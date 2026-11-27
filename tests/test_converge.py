"""`converge.py`, the converge conductor, driven over a fake host.

Why: 0108-converge-script design D1, its `## Tests` table.
"""

import ast
import io
import os
import re
import runpy
import subprocess
import sys
import threading
import time
import types
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, NamedTuple, Protocol, TextIO

import mflib.findings
import pytest
from mflib import debtfile, statuslog
from old_layout import ENTRIES, LOG, ROLES, plant

_SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "mf-converge" / "scripts"
_CHANGE = "0001-a"
_TASKS = "# Tasks\n\n## Progress\n\n- [x] 1 — One · moderate\n\n## 1 — One\n"
_WORKERS = {
    "conformance": ("claude", "claude-opus-5-5", "high"),
    "adversarial": ("claude", None, None),
    "fix": ("claude", "claude-sonnet-5-5", "medium"),
}
# A fake checker's scope: as wide as any freeze a test makes.
_WIDE = {"files": 99, "commits": 99}


def _converge() -> dict[str, Any]:
    return runpy.run_path(str(_SCRIPTS / "converge.py"))


def _git(cwd: Path, *args: str) -> str:
    identity = ["-c", "user.name=mf", "-c", "user.email=mf@example.invalid"]
    return subprocess.run(
        ["git", *identity, "-c", "commit.gpgsign=false", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _commit(cwd: Path, files: dict[str, str], message: str) -> str:
    for name, text in files.items():
        path = cwd / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    _git(cwd, "add", *files)
    _git(cwd, "commit", "-q", "-m", message)
    return _git(cwd, "rev-parse", "HEAD")


class Checked(NamedTuple):
    code: int
    killed: bool
    models: tuple[str, str | None, str | None]
    limit: str
    fallback: bool | str
    tokens: int | None


class NoSandbox(Exception):
    code = 2


class Read(Protocol):
    """The fields of `converge.py`'s `Verdict` a test reads."""

    verdict: str
    head: str
    round: int
    open_blocking: int
    stub: bool
    inconclusive: tuple[str, ...]
    cards: tuple[Any, ...]
    malformed: str | None
    unclean: str | None


def findings(role: str, head: str, **keys: object) -> str:
    """Return a findings file of `role` at `head`, clean; `keys` change or drop keys.

    A key given None is dropped; `body` is the text below the frontmatter.
    """
    front: dict[str, object] = {
        "type": role,
        "plan": _CHANGE,
        "project": "primary",
        "branch": _CHANGE,
        "head": head,
        "reviewed": "2026-11-09",
        "round": 1,
        "open_blocking": 0,
        "verdict": "clean",
        "mode": "parallel",
        "workers": 1,
        "files": 1,
        "commits": 1,
        "passes": "[stale-claim, test-cost, no-removed-test]",
        "inconclusive": "[]",
        "model": "claude-opus-5-5",
        "executor": "claude",
        "packet": "diff.patch",
    }
    if role != "conformance":
        del front["passes"]
    body = str(keys.pop("body", "## Summary\n\nClean.\n"))
    front.update(keys)
    lines = "".join(f"{k}: {v}\n" for k, v in front.items() if v is not None)
    return f"---\n{lines}---\n\n{body}\n## Resolution log\n"


def _round_of(station: str) -> int:
    """Return the round a station's name ends on, e.g. "converge-fix-r2" → 2."""
    return int(station.rpartition("-r")[2])


class Host:
    """A fake of the run `converge` is handed: its sandbox and its workers."""

    def __init__(self, primary: Path, tree: Path) -> None:
        self.primary = primary
        self.tree = tree
        self.plan: dict[tuple[str, str], tuple[str, str | None, str | None]] = {}
        self.exits: dict[str, int | list[int]] = {}
        self.printed = {"make": "uv run ruff check .\n"}
        self.ran: list[list[str]] = []
        self.timeouts: list[float | None] = []
        self.checks: list[tuple[str, str, str | None, str]] = []
        self.answers: dict[str, Callable[[str], None]] = {}
        self.results: dict[str, Checked | list[Checked]] = {}
        self.fixers: list[Callable[[Host], int | None]] = []
        self.fixed: list[tuple[str, tuple[str, str | None, str | None], str]] = []
        # A Codex fixer starts through `fix`: its calls, and the results it returns.
        self.codexed: list[tuple[str, tuple[str, str | None, str | None], str]] = []
        self.fixes: list[Checked] = []
        # The tools a station's log shows it asked for and lacks, by station.
        self.lacking: dict[str, list[str]] = {}
        # False is no OS sandbox; an exception is a runner that breaks.
        self.sandbox: bool | Exception = True
        # The run-log lines converge writes through `logged`: change, event, detail.
        self.logs: list[tuple[str, str, str]] = []

    def logged(self, change: str, event: str, detail: str) -> None:
        self.logs.append((change, event, detail))

    def folder(self) -> Path:
        return self.primary / ".minions" / "changes" / _CHANGE

    def write(self, role: str, text: str) -> None:
        self.folder().mkdir(parents=True, exist_ok=True)
        (self.folder() / f"{role}.md").write_text(text)

    def trees(self) -> list[Path]:
        return [self.primary, self.tree]

    def sandboxed(
        self,
        argv: list[str],
        cwd: Path,
        trees: list[Path],
        out: TextIO | None = None,
        timeout: float | None = None,
    ) -> int:
        self.timeouts.append(timeout)
        if isinstance(self.sandbox, Exception):
            raise self.sandbox
        if not self.sandbox:
            raise NoSandbox("conduct: cannot run — no OS sandbox")
        assert cwd == self.tree
        assert trees == self.trees()
        self.ran.append(argv)
        name = Path(argv[1]).name if argv[0] == sys.executable else argv[0]
        print(self.printed.get(name, ""), end="", file=out)
        code = self.exits.get(name, 0)
        if isinstance(code, list):
            return code.pop(0) if len(code) > 1 else code[0]
        return code

    def checker(
        self,
        change: str,
        station: str,
        table: str,
        cwd: Path,
        prompt: str,
        deadline: float,
        effort: str | None = None,
    ) -> Checked:
        assert (change, cwd) == (_CHANGE, self.tree)
        assert deadline > time.monotonic()
        self.checks.append((station, table, effort, prompt))
        head = _git(self.tree, "rev-parse", "HEAD")
        if answer := self.answers.get(station):
            answer(head)
        else:
            self.write(table, findings(table, head, round=_round_of(station), **_WIDE))
        models = _WORKERS.get(table.removeprefix("shadow-"), ("codex", None, None))
        result = self.results.get(station, Checked(0, False, models, "", False, 1200))
        if isinstance(result, list):
            return result.pop(0) if len(result) > 1 else result[0]
        return result

    def lacks(self, who: str, station: str) -> list[str]:
        assert who == _CHANGE
        return self.lacking.get(station, [])

    def worker(
        self,
        who: str,
        station: str,
        cwd: Path,
        prompt: str,
        models: tuple[str, str | None, str | None],
        timeout: float | None = None,
    ) -> tuple[int, bool, Path, list[str]]:
        assert (who, cwd) == (_CHANGE, self.tree)
        assert timeout is not None and timeout > 0
        self.fixed.append((station, models, prompt))
        code = (self.fixers.pop(0) if self.fixers else fixing)(self)
        return code or 0, False, self.folder() / "logs" / f"x-{station}.log", []

    def fix(
        self,
        change: str,
        station: str,
        cwd: Path,
        prompt: str,
        models: tuple[str, str | None, str | None],
        deadline: float,
    ) -> Checked:
        assert (change, cwd) == (_CHANGE, self.tree)
        assert deadline > time.monotonic()
        self.codexed.append((station, models, prompt))
        result = (
            self.fixes.pop(0)
            if self.fixes
            else Checked(0, False, models, "", False, None)
        )
        if result.code == 0:
            (self.fixers.pop(0) if self.fixers else fixing)(self)
        return result


def fixing(host: Host, left: str = "none") -> None:
    """Commit one fix and write the fixer's report, `plan check left: <left>`."""
    count = len(host.fixed) + len(host.codexed)
    _commit(host.tree, {f"src/fix{count}.py": f"F = {count}\n"}, "fix(0001-a): it")
    (host.folder() / "fix.md").write_text(
        f"fixed: R1\nwontfix: none\ncommit: x\nplan check left: {left}\n"
    )


def idle(host: Host) -> None:
    """Commit nothing: every card the fixer took is `wontfix`."""
    (host.folder() / "fix.md").write_text(
        "fixed: none\nwontfix: R2\ncommit: nothing committed\nplan check left: none\n"
    )


@pytest.fixture
def host(tmp_path: Path) -> Host:
    """Return a fake host over a primary checkout and its version's worktree.

    `main` holds the change directory; the version adds one commit on it.
    """
    primary = tmp_path / "primary"
    primary.mkdir()
    _git(primary, "init", "-q", "-b", "main")
    folder = f"openspec/changes/{_CHANGE}"
    _commit(
        primary,
        {
            ".gitignore": ".minions/\n",
            "Makefile": "gate:\n\ttrue\n",
            "docs/decisions.md": "# Decisions\n\n### D1 · One rule\n\nIt holds.\n",
            f"{folder}/proposal.md": "---\nbump: minor\n---\n\n# A\n",
            f"{folder}/design.md": "# A — design\n\nPer D1 · One rule.\n",
            f"{folder}/tasks.md": _TASKS,
        },
        "base",
    )
    tree = tmp_path / _CHANGE
    _git(primary, "worktree", "add", "-q", "-b", _CHANGE, str(tree))
    _commit(tree, {"src/a.py": "A = 1\n"}, "feat(0001-a): one")
    return Host(primary.resolve(), tree.resolve())


def run(
    host: Host,
    workers: Mapping[str, object] | None = None,
    *,
    grant: bool = False,
    module: dict[str, Any] | None = None,
) -> int:
    """Return `converge`'s exit over the fake host, on `_WORKERS` unless given."""
    deadline = time.monotonic() + 3600
    return (module or _converge())["converge"](
        host,
        _CHANGE,
        host.tree,
        workers=workers or _WORKERS,
        grant=grant,
        deadline=deadline,
    )


def events(host: Host) -> list[str]:
    """Return the newest run's events, oldest first, each without its time."""
    log = (host.folder() / "status_log.md").read_text().splitlines()
    heading = next(i for i, line in enumerate(log) if line.startswith("## Run"))
    run_lines = []
    for line in log[heading + 1 :]:
        if not line.strip() or line.startswith("## Run"):
            break
        run_lines.append(line.split(" · ", 1)[1])
    return run_lines[::-1]


def _dirty(host: Host) -> None:
    (host.tree / "stray.txt").write_text("x\n")


def _unticked(host: Host) -> None:
    tasks = _TASKS.replace("- [x] 1", "- [x] 1 — One\n- [ ] 2")
    _commit(host.tree, {f"openspec/changes/{_CHANGE}/tasks.md": tasks}, "a phase")


def _no_progress(host: Host) -> None:
    tasks = "# Tasks\n\n## 1 — One\n\n- [x] 1.1 One.\n"
    _commit(host.tree, {f"openspec/changes/{_CHANGE}/tasks.md": tasks}, "no progress")


def _upper_tick(host: Host) -> None:
    tasks = _TASKS.replace("- [x] 1", "- [X] 1")
    _commit(host.tree, {f"openspec/changes/{_CHANGE}/tasks.md": tasks}, "a capital")


def _empty(host: Host) -> None:
    _git(host.tree, "reset", "-q", "--hard", "main")


def _no_gate(host: Host) -> None:
    host.printed["make"] = "make: Nothing to be done for `gate'.\n"


def _red(host: Host) -> None:
    host.exits["gate_run.py"] = 2


def _changed(host: Host) -> None:
    host.exits["gate_check.py"] = 1
    host.printed["gate_check.py"] = "gate: halt — the gate changed\n  approve abc123\n"


def _verify(host: Host) -> None:
    host.exits["gate_check.py"] = 1
    # `gate_check.py` prints its gate line first.
    host.printed["gate_check.py"] = (
        "gate: no unplanned change\n"
        "verify: halt — a `Verify:` differs from the plan at 1a2b3c4; the build never"
        " amends one:\n  1.2\n  - a\n  + b\n  2.1 · uncommitted\n  - c\n  + d\n"
    )


def _old(host: Host) -> None:
    old = host.primary / ".minions" / "findings" / f"{_CHANGE}_review.md"
    old.parent.mkdir(parents=True)
    old.write_text("old\n")


def _no_sandbox(host: Host) -> None:
    host.sandbox = False


def _unrelated(host: Host) -> None:
    _git(host.tree, "checkout", "-q", "--orphan", "lone")
    _git(host.tree, "commit", "-q", "-m", "a root of its own")


def _unreadable(host: Host) -> None:
    tasks = host.tree / "openspec" / "changes" / _CHANGE / "tasks.md"
    tasks.unlink()
    tasks.symlink_to("gone.md")
    _git(host.tree, "add", str(tasks))
    _git(host.tree, "commit", "-q", "-m", "tasks.md is a link")


def _linked_commands(host: Host) -> None:
    host.folder().mkdir(parents=True)
    (host.folder() / "commands-r1.log").symlink_to(host.primary / "elsewhere.log")


def _unstamped(host: Host) -> None:
    host.folder().mkdir(parents=True)
    (host.folder() / "status_log.md").write_text("no title\n")


_REFUSED: dict[str, tuple[Callable[[Host], None], int, str | None]] = {
    "dirty": (_dirty, 1, "the tree is dirty: stray.txt"),
    "unticked": (_unticked, 1, "phase 2 of tasks.md is unticked: mf-build owns it"),
    "no progress": (_no_progress, 1, "tasks.md has no ## Progress list"),
    "upper-case tick": (_upper_tick, 1, "tasks.md has no ## Progress list"),
    "unrelated": (_unrelated, 1, "git merge-base failed: "),
    "unreadable": (
        _unreadable,
        1,
        "tasks.md cannot be read: No such file or directory",
    ),
    "linked commands": (
        _linked_commands,
        1,
        "commands-r1.log cannot be opened: Too many levels of symbolic links",
    ),
    "empty": (_empty, 1, "the range is empty: base is HEAD"),
    "no gate": (_no_gate, 1, "the root Makefile's gate runs no command"),
    "red": (_red, 1, "the gate is red before round 1: gate_run.py exit 2"),
    "changed": (
        _changed,
        1,
        "gate check: gate: halt — the gate changed · approve abc123",
    ),
    "verify": (_verify, 1, "verify: halt — 1.2, 2.1"),
    "old layout": (_old, 1, None),
    "no sandbox": (_no_sandbox, 2, None),
    "unstamped": (_unstamped, 2, None),
}


def test_a_converge_script_runs_by_the_conductors_python() -> None:
    argv = _converge()["script"]("gate_check.py", "--change", "x")

    assert argv == [sys.executable, str(_SCRIPTS / "gate_check.py"), "--change", "x"]
    assert "uv" not in argv


def _scripts_converge_starts() -> list[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse((_SCRIPTS / "converge.py").read_text())):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "script"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            names.add(node.args[0].value)
    return sorted(names)


def test_each_script_converge_starts_declares_no_dependencies() -> None:
    names = _scripts_converge_starts()

    assert {"gate_run.py", "gate_check.py", "plan_check.py"} <= set(names)
    for name in names:
        header = re.search(
            r"^# /// script\n(.*?)^# ///$",
            (_SCRIPTS / name).read_text(),
            re.DOTALL | re.MULTILINE,
        )
        assert header, name
        assert "# dependencies = []\n" in header.group(1), name


def test_two_converges_start_gate_check_at_once(tmp_path: Path) -> None:
    cache = tmp_path / "uv-cache"
    cache.mkdir()
    env = {**os.environ, "UV_CACHE_DIR": str(cache)}
    argv = _converge()["script"]("gate_check.py", "--help")
    barrier = threading.Barrier(2)

    def start() -> int:
        barrier.wait()
        return subprocess.run(
            argv, env=env, capture_output=True, check=False
        ).returncode

    with ThreadPoolExecutor(2) as pool:
        codes = [future.result() for future in [pool.submit(start), pool.submit(start)]]

    assert codes == [0, 0]
    assert not (cache / "environments-v2").exists()


@pytest.mark.parametrize("case", list(_REFUSED))
def test_a_converge_refuses_what_it_cannot_start(
    host: Host, case: str, capsys: pytest.CaptureFixture[str]
) -> None:
    setup, code, reason = _REFUSED[case]
    setup(host)
    head = _git(host.tree, "rev-parse", "HEAD")

    assert run(host) == code

    assert host.checks == []
    printed = capsys.readouterr().out
    log = host.folder() / "status_log.md"
    if case == "old layout":
        assert not log.exists()
        assert f".minions/findings/{_CHANGE}_review.md" in printed
        assert "/mf-ship" in printed
        return
    if case == "unstamped":
        # A log that takes no run takes no halt either: exit 2, the log as it stood.
        assert "status_log.md cannot be stamped" in printed
        assert log.read_text() == "no title\n"
        return
    written = events(host)
    assert not any(line.startswith("round 1 · start") for line in written)
    if case == "no sandbox":
        assert "no OS sandbox" in printed
        reason = "conduct: cannot run — no OS sandbox"
    assert written[-1] == f"round 1 · halt — {reason} · head {head}"
    if case == "no sandbox":
        # Any other failure of the runner is no "cannot run": it propagates.
        host.sandbox = RuntimeError("the runner broke")
        with pytest.raises(RuntimeError, match="the runner broke"):
            run(host)


def test_converge_halts_on_each_old_entry_alone(
    host: Host, capsys: pytest.CaptureFixture[str]
) -> None:
    module = _converge()
    for old in {**ENTRIES, **ROLES, **LOG}:
        planted = plant(host.primary / ".minions", _CHANGE, old)
        assert run(host, module=module) == 1, old
        assert host.checks == [], old
        printed = capsys.readouterr().out
        assert f".minions/{old.format(_CHANGE)} is at an old path" in printed, old
        assert not (host.folder() / "status_log.md").exists(), old
        planted.unlink()


def test_a_halt_names_the_first_sorted_path(
    host: Host, capsys: pytest.CaptureFixture[str]
) -> None:
    for old in ("build/{}.done", "findings/{}_review.md"):
        plant(host.primary / ".minions", _CHANGE, old)

    assert run(host) == 1

    printed = capsys.readouterr().out
    assert f".minions/build/{_CHANGE}.done is at an old path" in printed


def test_a_freeze_reads_the_cards_of_a_lone_backlog(host: Host) -> None:
    converge = _converge()
    old = host.primary / ".minions" / "backlog.md"
    old.parent.mkdir(parents=True)
    old.write_text(
        "# Backlog\n\n## 0000-z\n\n- **0000·R1 — A stays one**\n"
        "  - **What it affects:** `src/a.py:1`\n"
    )
    base = _git(host.tree, "merge-base", "main", "HEAD")
    head = _git(host.tree, "rev-parse", "HEAD")
    context = converge["Context"](host, _CHANGE, host.tree, _WORKERS, 1e12)
    converge["open_run"](context)

    converge["freeze"](context, base, head)

    cards = host.folder() / "debt-cards.md"
    assert "0000·R1" in cards.read_text()
    assert not (host.primary / ".minions" / "debt.md").exists()
    # Twin: a debt file beside it is read in its place.
    (host.primary / ".minions" / "debt.md").write_text("# Debt\n")
    converge["freeze"](context, base, head)
    assert "0000·R1" not in cards.read_text()


def test_the_freeze_writes_the_patch_the_bundle_and_the_debt_cards(host: Host) -> None:
    converge = _converge()
    debt = host.primary / ".minions" / "debt.md"
    debt.parent.mkdir(parents=True)
    debt.write_text(
        "# Debt\n\n## 0000-z\n\n- **0000·R1 — A stays one**\n"
        "  - **What it affects:** `src/a.py:1`\n- **0000·R2 — B**\n"
        "  - **What it affects:** `src/b.py`\n"
    )
    _commit(host.tree, {"src/b.txt": "b\n"}, "feat(0001-a): two")
    base = _git(host.tree, "merge-base", "main", "HEAD")
    head = _git(host.tree, "rev-parse", "HEAD")
    context = converge["Context"](host, _CHANGE, host.tree, _WORKERS, 1e12)
    converge["open_run"](context)

    frozen = converge["freeze"](context, base, head)

    folder = host.folder()
    assert (frozen.base, frozen.head, frozen.commits, frozen.files) == (
        base,
        head,
        2,
        2,
    )
    patch = (folder / "diff.patch").read_text()
    assert patch == _git(host.tree, "diff", "--binary", base, head) + "\n"
    bundle = (folder / "bundle.md").read_text()
    assert bundle.startswith(f"# {_CHANGE} — bundle")
    assert "### D1 · One rule" in bundle
    cards = (folder / "debt-cards.md").read_text()
    assert "0000·R1" in cards
    assert "0000·R2" not in cards
    assert events(host)[-1] == (
        f"round 1 · freeze — {base[:7]}..{head[:7]} · 2 commits · 2 files"
    )

    # A debt it may not read halts the freeze, and the cards file stands.
    debt.unlink()
    debt.mkdir()
    with pytest.raises(converge["Halt"], match=r"^debt_match\.py exited 2 — "):
        converge["freeze"](context, base, head)

    assert (folder / "debt-cards.md").read_text() == cards
    debt.rmdir()

    # A planted link takes no patch and no bundle: the freeze halts naming it.
    for name, said in (
        ("diff.patch", "the patch cannot be written"),
        ("bundle.md", "bundle: cannot bundle"),
        ("evidence.md", "evidence: cannot write"),
    ):
        (folder / name).unlink()
        (folder / name).symlink_to(host.primary / "elsewhere")
        with pytest.raises(converge["Halt"], match=said):
            converge["freeze"](context, base, head)
        (folder / name).unlink()

    # The evidence stands after the freeze: its plan check is the host's output, and a
    # patch that removes a name runs one `git grep` for it.
    host.printed["plan_check.py"] = "plan: clean\n"
    host.printed["git"] = "docs/guide.md:41:call A to start\nsrc/a.py:1:B = 1\n"
    (host.tree / ".minions").mkdir()
    (host.tree / ".minions" / "test-report.xml").write_text(
        '<testsuites><testcase classname="tests.test_x" name="test_x"'
        ' time="0.25"/></testsuites>'
    )
    context.base = base
    fixed = _commit(
        host.tree,
        {
            "src/a.py": "B = 1  # noqa: X\n",
            "tests/test_x.py": "def test_x():\n    pass\n",
        },
        "fix(0001-a): it",
    )
    host.ran.clear()

    converge["freeze"](context, head, fixed)

    assert (folder / "evidence.md").read_text() == (
        f"# Evidence — {_CHANGE} · {head[:7]}..{fixed[:7]}\n\n"
        "Facts a tool found, not verdicts. Start from them; judge them.\n\n"
        "## Gate integrity\nnoqa · src/a.py:1 · B = 1  # noqa: X\n\n"
        "## Plan check\nplan: clean\n\n"
        "## Stale-claim candidates\nA · docs/guide.md:41: call A to start\n\n"
        "## Test cost\nadded · tests/test_x.py:1 · test_x · 0.25 s\n"
    )
    assert _ran(host) == ["plan_check.py", "git"]
    assert host.ran[0][-4:] == ["--change", _CHANGE, "--base", base]
    assert host.ran[1] == ["git", "grep", "-n", "-w", "-F", "-e", "A"]

    # With no name to look for no `git grep` runs, and the section reads `None.`.
    host.ran.clear()
    converge["freeze"](context, base, head)

    assert _ran(host) == ["plan_check.py"]
    assert "## Stale-claim candidates\nNone.\n" in (folder / "evidence.md").read_text()


def _plan_check_section(folder: Path) -> str:
    text = (folder / "evidence.md").read_text()
    return text.split("## Plan check\n")[1].split("\n\n## ")[0]


def test_a_freeze_at_the_head_build_done_names_runs_no_plan_check(host: Host) -> None:
    converge = _converge()
    base = _git(host.tree, "merge-base", "main", "HEAD")
    head = _git(host.tree, "rev-parse", "HEAD")
    context = converge["Context"](host, _CHANGE, host.tree, _WORKERS, 1e12)
    context.base = base
    converge["open_run"](context)
    folder = host.folder()
    (folder / "build.done").write_text(f"head: {head}\nsimplify: none\n")
    kept = "1.1 failed: x\ntimed out: 1.2\n"
    (folder / "plan-check.txt").write_text(f"base: {base}\n{kept}")
    host.printed["plan_check.py"] = "plan: a run's line\n"
    host.ran.clear()

    converge["freeze"](context, base, head)

    assert _plan_check_section(folder) == "1.1 failed: x\ntimed out: 1.2"
    assert "plan_check.py" not in _ran(host)

    # A check the close ran from another base, a stacked one's, is no check here.
    (folder / "plan-check.txt").write_text(f"base: {head}\n{kept}")
    host.ran.clear()
    converge["freeze"](context, base, head)

    assert _plan_check_section(folder) == "plan: a run's line"
    assert "plan_check.py" in _ran(host)


def test_a_freeze_at_another_head_runs_the_plan_check(host: Host) -> None:
    converge = _converge()
    base = _git(host.tree, "merge-base", "main", "HEAD")
    head = _git(host.tree, "rev-parse", "HEAD")
    context = converge["Context"](host, _CHANGE, host.tree, _WORKERS, 1e12)
    context.base = base
    converge["open_run"](context)
    folder = host.folder()
    (folder / "plan-check.txt").write_text(f"base: {base}\n1.1 failed: x\n")
    host.printed["plan_check.py"] = "plan: a run's line\n"

    # Twin of each conjunct: a head `build.done` names no longer, then no file kept.
    (folder / "build.done").write_text(f"head: {base}\nsimplify: none\n")
    host.ran.clear()
    converge["freeze"](context, base, head)

    assert _plan_check_section(folder) == "plan: a run's line"
    assert "plan_check.py" in _ran(host)

    (folder / "build.done").write_text(f"head: {head}\nsimplify: none\n")
    (folder / "plan-check.txt").unlink()
    host.ran.clear()
    converge["freeze"](context, base, head)

    assert _plan_check_section(folder) == "plan: a run's line"
    assert "plan_check.py" in _ran(host)


_REFERENCES = (
    "generic-conformance.md",
    "generic-adversarial.md",
    "verify.md",
    "fix.md",
)


def test_each_worker_prompt_is_filled_from_its_reference(tmp_path: Path) -> None:
    converge = _converge()
    names = converge["PLACEHOLDERS"]
    values = {name: f"<{name} value>" for name in names}

    for reference in _REFERENCES:
        filled = converge["prompt"](reference, **values)

        template = (_SCRIPTS.parent / "references" / reference).read_text()
        assert filled.startswith("role: <role value>\nchange: <change value>\n")
        assert "{" not in filled
        for name in names:
            assert (f"<{name} value>" in filled) is (f"{{{name}}}" in template)

    with pytest.raises(ValueError, match="unknown placeholder: colour"):
        converge["prompt"]("verify.md", colour="red", **values)
    del values["findings"]
    with pytest.raises(ValueError, match=r"verify\.md: findings is not filled"):
        converge["prompt"]("verify.md", **values)
    # A reference with no `## Prompt`, or one naming no placeholder, is refused.
    with pytest.raises(ValueError, match=r"worker\.md has no ## Prompt block"):
        converge["prompt"]("worker.md", **values)
    odd = tmp_path / "odd.md"
    odd.write_text("## Prompt\n\n```text\nrole: {colour}\n```\n")
    with pytest.raises(ValueError, match=r"\{colour\} is no placeholder"):
        converge["prompt"](str(odd), **values)


def _card(
    card: str,
    *,
    amend: str | None = "no",
    status: str = "open",
    size: str = "one line",
    category: str = "functional correctness",
    still: str = "`grep -n A src/a.py`",
    related: str = "none.",
) -> str:
    """Return a card `<id> <severity>`, e.g. "R1 blocking", with its fields."""
    ident, severity = card.split()
    role = "conformance" if ident.startswith("R") else "adversarial"
    fields = [
        ("Why it's a problem:", "it breaks."),
        ("What it affects:", "`src/a.py:1`."),
        ("Priority:", f"{severity} · {role} · {category} — it breaks."),
        ("Round:", "1"),
        ("Fix:", f"fix it · size: {size}."),
        ("Amend:", amend),
        ("Still true?", still),
        ("Related:", related),
        ("Status:", status),
    ]
    lines = [f"  - **{name}** {value}" for name, value in fields if value is not None]
    return "\n".join([f"- **{ident} — It breaks**", *lines]) + "\n"


def test_a_findings_file_is_read_by_its_fields(host: Host) -> None:
    converge = _converge()
    head = _git(host.tree, "rev-parse", "HEAD")
    folder = host.folder()
    folder.mkdir(parents=True)

    def read(role: str, **keys: object) -> Read:
        (folder / f"{role}.md").write_text(findings(role, head, **keys))
        return converge["read_findings"](folder / f"{role}.md", role)

    clean = read("conformance", files=3, commits=2, inconclusive="[design.md]")
    assert (clean.verdict, clean.head, clean.round, clean.open_blocking) == (
        "clean",
        head,
        1,
        0,
    )
    assert clean.inconclusive == ("design.md",)
    assert (clean.malformed, clean.unclean, clean.stub) == (None, None, False)
    cards = _card("S1 high") + _card("S2 medium", amend="yes", status="wontfix")
    blocked = read(
        "adversarial", files=3, commits=2, verdict="changes-requested", body=cards
    )
    assert [(c.id, c.blocking, c.status, c.amend) for c in blocked.cards] == [
        ("S1", True, "open", False),
        ("S2", False, "wontfix", True),
    ]
    assert blocked.cards[1].fields["Still true?"] == "`grep -n A src/a.py`"
    passes = "[stale-claim, test-cost, coverage-trace]"
    assert read("conformance", files=3, commits=2, passes=passes).unclean is None

    for keys, why in (
        ({"passes": "[stale-claim, no-removed-test]"}, "lacks test-cost"),
        ({"passes": "[stale-claim, test-cost]"}, "lacks coverage-trace"),
    ):
        unclean = read("conformance", **{"files": 3, "commits": 2, **keys}).unclean
        assert unclean is not None
        assert why in unclean

    for keys, why in (
        ({"files": None}, "files is missing"),
        ({"commits": "many"}, "commits is not an integer"),
        ({"passes": "stale-claim"}, "passes is not a list"),
        ({"verdict": "fine"}, "verdict is neither clean nor changes-requested"),
        ({"body": _card("R1 drift", amend=None)}, "card R1 has no Amend line"),
        ({"body": _card("R1 drift", amend="maybe")}, "card R1 has no Amend line"),
    ):
        assert read("conformance", **{"files": 3, "commits": 2, **keys}).malformed == (
            f"conformance.md is malformed: {why}"
        )

    stub = read(
        "adversarial",
        mode="skipped",
        files=None,
        commits=None,
        inconclusive=None,
        workers=0,
    )
    assert (stub.stub, stub.malformed, stub.unclean, stub.verdict) == (
        True,
        None,
        None,
        "clean",
    )
    assert converge["read_findings"](folder / "gone.md", "conformance") is None
    (folder / "linked.md").symlink_to(folder / "conformance.md")
    linked = converge["read_findings"](folder / "linked.md", "conformance")
    assert linked.malformed == "linked.md is malformed: it is a link"
    os.mkfifo(folder / "piped.md")
    piped = converge["read_findings"](folder / "piped.md", "conformance")
    assert piped.malformed == "piped.md is malformed: it is not a file"

    frozen = converge["Freeze"]("b" * 40, head, 1, 1)
    context = converge["Context"](host, _CHANGE, host.tree, _WORKERS, 1e12)
    converge["open_run"](context)
    for role in ("conformance", "adversarial"):
        (folder / f"{role}.md").write_text(findings(role, head))
    checked = {
        "conformance": Checked(0, False, _WORKERS["conformance"], "", False, 97960),
        "adversarial": Checked(0, False, ("claude", None, None), "", True, None),
    }

    read = converge["read_verdicts"](context, checked)

    assert set(read) == {"conformance", "adversarial"}
    assert events(host) == [
        "round 1 · verdicts — conformance clean · open_blocking 0 · executor claude"
        " · model claude-opus-5-5 · effort high · tokens 97960",
        "round 1 · verdicts — adversarial clean · open_blocking 0 · executor claude"
        " · model default · effort default · tokens unavailable"
        " · fallback: codex usage limit",
    ]
    # A file missing, or one not clean, halts the round naming it.
    halt = converge["Halt"]
    with pytest.raises(halt, match=r"conformance\.md is missing: its checker left no"):
        converge["held"](context, read | {"conformance": None}, frozen)
    narrow = folder / "conformance.md"
    narrow.write_text(findings("conformance", head, passes="[stale-claim]"))
    short = converge["read_findings"](narrow, "conformance")
    with pytest.raises(halt, match="lacks test-cost"):
        converge["held"](context, read | {"conformance": short}, frozen)
    # A file with no open card is judged on its passes first, so it never reads clean.
    narrow.write_text(
        findings(
            "conformance", head, passes="[stale-claim]", verdict="changes-requested"
        )
    )
    short = converge["read_findings"](narrow, "conformance")
    assert short.malformed is None
    assert "lacks test-cost" in short.unclean


def _front_holds(host: Host, role: str, **keys: object) -> None:
    """Assert `role`'s findings file holds each key in its frontmatter."""
    front = mflib.findings.front((host.folder() / f"{role}.md").read_text())[0]
    assert {key: front.get(key) for key in keys} == {
        key: str(value) for key, value in keys.items()
    }


def test_a_miscounted_file_is_stamped_clean(host: Host) -> None:
    more = {f"src/b{n}.py": f"B = {n}\n" for n in range(3)}
    _commit(host.tree, more, "feat(0001-a): more")

    def miscounted(head: str) -> None:
        host.write("conformance", findings("conformance", head, files=3, commits=1))

    host.answers["converge-conformance-r1"] = miscounted

    assert run(host) == 0

    _front_holds(host, "conformance", head=_head(host), round=1, files=4, commits=2)
    assert [station for station, *_ in host.checks] == [
        "converge-conformance-r1",
        "converge-adversarial-r1",
    ]
    assert events(host)[3] == _verdicts("conformance")


def test_a_file_with_no_count_keys_is_stamped(host: Host) -> None:
    def bare(head: str) -> None:
        text = findings("adversarial", head, round=None, files=None, commits=None)
        host.write("adversarial", text.replace(f"head: {head}\n", ""))

    host.answers["converge-adversarial-r1"] = bare

    assert run(host) == 0

    _front_holds(host, "adversarial", head=_head(host), round=1, files=1, commits=1)
    assert events(host)[4] == _verdicts("adversarial")


def test_a_verify_round_is_stamped_with_the_fixs_head_and_the_round(
    host: Host,
) -> None:
    first = _head(host)
    host.answers["converge-conformance-r1"] = answer(
        host, "conformance", _card("R1 blocking"), blocking=1
    )

    def stale(now: str) -> None:
        verified = _card("R1 blocking", status="verified")
        text = findings("conformance", first, files=0, commits=0, body=verified)
        host.write("conformance", text)

    host.answers["converge-verify-conformance-r2"] = stale

    assert run(host) == 0

    # The whole range is 2 commits and 2 files; the fix diff is 1 and 1.
    _front_holds(host, "conformance", head=_head(host), round=2, files=1, commits=1)
    assert events(host)[-1] == (
        "round 2 · done — converged in 2 rounds · 0 cards to debt"
    )


def test_a_pickup_check_is_stamped_and_keeps_its_round(host: Host) -> None:
    first = _head(host)
    host.answers["converge-conformance-r1"] = answer(
        host, "conformance", _card("R2 nit")
    )

    def stale(now: str) -> None:
        # A round converge never counts: the stamp leaves it as written.
        verified = _card("R2 nit", status="verified")
        text = findings("conformance", first, round=7, files=0, body=verified)
        host.write("conformance", text)
        host.write("adversarial", findings("adversarial", first, round=7, commits=0))

    host.answers["converge-verify-pickup-r1"] = stale

    assert run(host) == 0

    assert host.checks[-1][0] == "converge-verify-pickup-r1"
    for role in ("conformance", "adversarial"):
        _front_holds(host, role, head=_head(host), round=7, files=1, commits=1)


def test_a_checker_that_writes_nothing_leaves_no_stamp_on_a_stale_file(
    host: Host,
) -> None:
    host.write("adversarial", findings("adversarial", "a" * 40, round=1))
    stale = (host.folder() / "adversarial.md").read_text()
    host.answers["converge-adversarial-r1"] = lambda head: None

    assert run(host) == 1

    assert (host.folder() / "adversarial.md").read_text() == stale
    assert events(host)[-1].startswith(
        "round 1 · halt — adversarial.md is unchanged: its checker wrote no findings"
    )
    told = [station for station, *_ in host.checks]
    assert told.count("converge-adversarial-r1") == 2


def test_a_stamp_that_fails_halts_naming_the_file(host: Host) -> None:
    def blocked(head: str) -> None:
        host.write("conformance", findings("conformance", head, **_WIDE))
        planted = host.folder() / "conformance.md.tmp"
        planted.mkdir()
        (planted / "held").write_text("x")

    host.answers["converge-conformance-r1"] = blocked

    assert run(host) == 1

    assert events(host)[-1].startswith(
        "round 1 · halt — conformance.md could not be stamped: the write failed"
    )


def test_a_stub_and_a_by_rule_file_are_not_stamped(host: Host) -> None:
    converge = _converge()
    context = converge["Context"](host, _CHANGE, host.tree, _WORKERS, 1e12)
    context.round = 2
    frozen = converge["Freeze"]("b" * 40, "c" * 40, 3, 5)
    texts = {
        "adversarial": mflib.findings.stub(
            "adversarial", _CHANGE, "primary", _CHANGE, "a" * 40, "2026-11-09", 1
        ),
        "conformance": findings("conformance", "a" * 40, mode="by-rule", workers=0),
    }
    for role, text in texts.items():
        host.write(role, text)

    converge["counted"](context, frozen, list(texts))
    converge["counted"](context, frozen, list(texts), pickup=True)

    for role, text in texts.items():
        assert (host.folder() / f"{role}.md").read_text() == text
    # A worker's file beside them is stamped.
    host.write("conformance", findings("conformance", "a" * 40))
    converge["counted"](context, frozen, ["conformance"])
    _front_holds(host, "conformance", head="c" * 40, round=2, files=5, commits=3)


def test_a_codex_failure_fallback_is_named_in_the_verdicts_line(host: Host) -> None:
    converge = _converge()
    head = _git(host.tree, "rev-parse", "HEAD")
    folder = host.folder()
    folder.mkdir(parents=True)
    context = converge["Context"](host, _CHANGE, host.tree, _WORKERS, 1e12)
    converge["open_run"](context)
    (folder / "conformance.md").write_text(findings("conformance", head))
    claude = ("claude", None, None)
    failed = Checked(0, False, claude, "", "codex failed", None)

    converge["read_verdicts"](context, {"conformance": failed})

    assert events(host) == [
        "round 1 · verdicts — conformance clean · open_blocking 0 · executor claude"
        " · model default · effort default · tokens unavailable"
        " · fallback: codex failed",
    ]


def test_a_bold_bullet_is_no_card(host: Host) -> None:
    converge = _converge()
    head = _git(host.tree, "rev-parse", "HEAD")
    folder = host.folder()
    folder.mkdir(parents=True)
    body = (
        "## Passes\n\n- **stale-claim** — ran.\n\n"
        "## Summary\n\n- **Spec** — none.\n\n" + _card("R1 drift")
    )
    (folder / "conformance.md").write_text(
        findings("conformance", head, files=3, commits=2, body=body)
    )

    read = converge["read_findings"](folder / "conformance.md", "conformance")

    assert read.malformed is None
    assert [card.id for card in read.cards] == ["R1"]
    debt = body.replace(_card("R1 drift"), _filed(_card("R1 drift")))
    assert debtfile.TITLE.findall(debt) == ["0001·R1"]


def _verdicts(
    role: str, round_: int = 1, verdict: str = "clean", blocking: int = 0
) -> str:
    executor, model, effort = _WORKERS[role]
    return (
        f"round {round_} · verdicts — {role} {verdict} · open_blocking {blocking}"
        f" · executor {executor} · model {model or 'default'}"
        f" · effort {effort or 'default'} · tokens 1200"
    )


def test_a_clean_round_converges_with_no_fix(host: Host) -> None:
    base = _git(host.tree, "merge-base", "main", "HEAD")
    head = _git(host.tree, "rev-parse", "HEAD")
    span = f"{base[:7]}..{head[:7]}"

    assert run(host) == 0

    assert events(host) == [
        f"round 1 · start — base {base[:7]} · head {head[:7]} · 1 commit · 1 file",
        f"round 1 · freeze — {span} · 1 commit · 1 file",
        f"round 1 · fan-out — conformance and adversarial dispatched · {span}"
        " · 2 workers",
        _verdicts("conformance"),
        _verdicts("adversarial"),
        "round 1 · debt — none",
        "round 1 · done — converged in 1 round · 0 cards to debt",
    ]
    assert [(station, table, effort) for station, table, effort, _ in host.checks] == [
        ("converge-conformance-r1", "conformance", None),
        ("converge-adversarial-r1", "adversarial", None),
    ]
    for _, role, _, text in host.checks:
        assert text.startswith(f"role: {role}\nchange: {_CHANGE}\nround: 1\n")
        assert "`mode: parallel`" in text
        assert "head" not in text
        assert str(host.folder() / f"{role}.md") in text
    assert [
        Path(argv[1]).name if argv[0] == sys.executable else argv[0]
        for argv in host.ran
    ] == [
        "make",
        "gate_run.py",
        "gate_check.py",
        "plan_check.py",
        "gate_run.py",
    ]


def test_a_skipped_checker_is_a_stub(host: Host) -> None:
    head = _git(host.tree, "rev-parse", "HEAD")
    skips = {**_WORKERS, "adversarial": "skip"}

    assert run(host, workers=skips) == 0

    stub = (host.folder() / "adversarial.md").read_text()
    assert f"head: {head}\n" in stub
    assert "mode: skipped\n" in stub
    assert [station for station, *_ in host.checks] == ["converge-conformance-r1"]
    written = events(host)
    assert written[2].startswith("round 1 · fan-out — conformance dispatched · ")
    assert written[2].endswith(" · 1 worker")
    assert written[3:] == [
        _verdicts("conformance"),
        "round 1 · debt — none",
        "round 1 · done — converged in 1 round · 0 cards to debt",
    ]

    (host.folder() / "adversarial.md").write_text(
        findings(
            "adversarial", head, verdict="changes-requested", body=_card("S1 high")
        )
    )
    assert run(host, workers=skips) == 1
    assert events(host)[-1].startswith(
        "round 1 · halt — skip_stub: cannot stub — "
        f"{host.folder() / 'adversarial.md'} holds a checker's round not cleared"
    )

    both = {**skips, "conformance": "skip"}
    assert run(host, workers=both) == 1
    assert events(host) == [
        "round 1 · halt — both checkers are skipped: a plan that skips both runs no"
        f" converge · head {head}"
    ]


def answer(
    host: Host, role: str, *cards: str, blocking: int = 0, **keys: object
) -> Callable[[str], None]:
    """Return a checker's answer: `role`'s file at the head given, with `cards`."""

    def write(head: str) -> None:
        verdict = "changes-requested" if blocking else "clean"
        body = "## Summary\n\nJudged.\n\n" + "".join(cards)
        fields = {"verdict": verdict, "open_blocking": blocking, **_WIDE, **keys}
        host.write(role, findings(role, head, body=body, **fields))

    return write


def _head(host: Host) -> str:
    return _git(host.tree, "rev-parse", "HEAD")


def _ran(host: Host) -> list[str]:
    return [
        Path(argv[1]).name if argv[0] == sys.executable else argv[0]
        for argv in host.ran
    ]


def _stations(host: Host) -> list[tuple[str, str, str | None]]:
    return sorted((station, table, effort) for station, table, effort, _ in host.checks)


def _fan_out(round_: int, span: str) -> str:
    return (
        f"round {round_} · fan-out — conformance and adversarial dispatched · {span}"
        " · 2 workers"
    )


def heading(host: Host) -> str:
    log = (host.folder() / "status_log.md").read_text().splitlines()
    return next(line for line in log if line.startswith("## Run"))


@pytest.mark.slow
def test_a_blocker_is_fixed_verified_and_cleared(host: Host) -> None:
    base = _git(host.tree, "merge-base", "main", "HEAD")
    first = _head(host)
    host.answers["converge-conformance-r1"] = answer(
        host, "conformance", _card("R1 blocking"), blocking=1
    )
    workers = {**_WORKERS, "fix": ("claude", "claude-sonnet-5-5", None)}

    assert run(host, workers) == 0

    fixed = _head(host)
    span = f"{first[:7]}..{fixed[:7]}"
    assert [(station, models) for station, models, _ in host.fixed] == [
        ("converge-fix-r1", ("claude", "claude-sonnet-5-5", "medium"))
    ]
    told = host.fixed[0][2]
    assert told.startswith(f"role: fix\nchange: {_CHANGE}\nround: 1\n")
    assert "- The cards to clear, by id: R1\n" in told
    assert f"- The base for the plan check: {base}\n" in told
    assert events(host)[3:] == [
        _verdicts("conformance", verdict="changes-requested", blocking=1),
        _verdicts("adversarial"),
        "round 1 · fix — sent R1",
        f"round 1 · fix — commit {fixed[:7]} · gate green",
        f"round 1 · freeze — {span} · 1 commit · 1 file",
        f"round 1 · verify — round 2 · {span} · gate green",
        _fan_out(2, span),
        _verdicts("conformance", 2),
        _verdicts("adversarial", 2),
        "round 2 · debt — none",
        "round 2 · done — converged in 2 rounds · 0 cards to debt",
    ]
    assert _stations(host)[2:] == [
        ("converge-verify-adversarial-r2", "adversarial", "medium"),
        ("converge-verify-conformance-r2", "conformance", "medium"),
    ]
    verify = next(text for station, _, _, text in host.checks if "verify-c" in station)
    assert verify.startswith(f"role: conformance\nchange: {_CHANGE}\nround: 2\n")
    assert f"{first}..{fixed}: {host.folder() / 'diff.patch'}" in verify
    assert str(host.folder() / "conformance.open.md") in verify
    assert "- **R1 — It breaks**" in (host.folder() / "conformance.open.md").read_text()
    # The re-freeze rewrote the evidence for the fix range, and each prompt names it.
    evidence = host.folder() / "evidence.md"
    assert evidence.read_text().startswith(f"# Evidence — {_CHANGE} · {span}\n")
    assert all(str(evidence) in prompt for *_, prompt in host.checks)
    assert str(evidence) in told
    assert _ran(host) == [
        *("make", "gate_run.py", "gate_check.py", "plan_check.py"),
        *("gate_run.py", "plan_check.py", "gate_run.py", "gate_check.py"),
        *("plan_check.py", "gate_run.py"),
    ]

    for case, why in (
        ("failed", "converge-fix-r1 worker exit 1"),
        ("status", "open cards: cannot read — card R1: Status maybe"),
    ):
        card = _card("R1 blocking", status="maybe" if case == "status" else "open")
        host.answers["converge-conformance-r1"] = answer(
            host, "conformance", card, blocking=1
        )
        host.fixers = [lambda host: 1] * 2 if case == "failed" else []

        assert run(host) == 1

        assert events(host)[-1].endswith(f" · halt — {why} · head {_head(host)}")

    host.answers.clear()
    host.results["converge-conformance-r1"] = Checked(
        0, True, _WORKERS["conformance"], "", False, None
    )

    assert run(host) == 1

    last = events(host)[-1]
    assert last.startswith("round 1 · halt — converge-conformance-r1 timed out after ")
    assert last.endswith(f"s; its group was killed · head {_head(host)}")


def test_a_red_gate_after_a_fix_gets_one_more_pass_then_the_cap(host: Host) -> None:
    host.answers["converge-conformance-r1"] = answer(
        host, "conformance", _card("R1 blocking"), blocking=1
    )
    host.exits["gate_run.py"] = [0, 2, 0]
    host.printed["gate_run.py"] = "FAILED tests/test_a.py::test_one\n"

    assert run(host) == 0

    assert [station for station, *_ in host.fixed] == ["converge-fix-r1"] * 2
    assert host.fixed[1][2].count(
        "R1; and the gate is red, exit 2: FAILED tests/test_a.py::test_one"
    )
    written = events(host)
    sent = written.index("round 1 · fix — sent R1")
    assert written[sent + 1].endswith(" · the gate is red, exit 2")
    assert written[sent + 2] == "round 1 · fix — sent R1 · one more pass"
    assert written[sent + 3].endswith(" · gate green")
    assert written[-1] == "round 2 · done — converged in 2 rounds · 0 cards to debt"

    def dirty(host: Host) -> None:
        fixing(host)
        (host.tree / "stray.txt").write_text("x\n")

    host.fixers = [dirty, dirty]

    assert run(host) == 1

    assert events(host)[-1] == (
        "round 1 · halt — cap reached — the tree is dirty: stray.txt after one more"
        f" fix pass · head {_head(host)}"
    )


def test_converge_logs_each_gate_with_its_seconds(host: Host) -> None:
    # Why: 0148-run-fields design D4.
    host.answers["converge-conformance-r1"] = answer(
        host, "conformance", _card("R1 blocking"), blocking=1
    )
    host.exits["gate_run.py"] = [0, 2, 0]

    assert run(host) == 0

    assert {(change, event) for change, event, _ in host.logs} == {(_CHANGE, "check")}
    shown = [re.sub(r"\d+s$", "Ns", detail) for *_, detail in host.logs]
    assert shown[:3] == [
        "gate · pass · Ns",
        "gate · fail — red · Ns",
        "gate · pass · Ns",
    ]
    assert set(shown) == {"gate · pass · Ns", "gate · fail — red · Ns"}
    assert len(shown) == _ran(host).count("gate_run.py")

    host.logs.clear()
    host.exits["gate_run.py"] = 2

    assert run(host) == 1

    (_, _, detail), *rest = host.logs
    assert re.fullmatch(r"gate · fail — red · \d+s", detail)
    assert rest == []


def test_a_reused_gate_record_is_logged_as_a_pass(host: Host) -> None:
    # Why: 0148-run-fields design D4.
    host.printed["gate_run.py"] = "gate: green — the record of this tree is reused\n"

    assert run(host) == 0

    details = [detail for *_, detail in host.logs]
    assert details
    assert all(re.fullmatch(r"gate · pass · \d+s", detail) for detail in details)
    assert not any("start" in detail for detail in details)


def test_the_cap_halts_with_the_open_blockers(host: Host) -> None:
    security = _card("S1 high", category="security")
    for station in (
        "converge-conformance-r1",
        *(f"converge-verify-conformance-r{n}" for n in (2, 3)),
    ):
        host.answers[station] = answer(
            host,
            "conformance",
            _card("R1 blocking"),
            blocking=1,
            round=_round_of(station),
        )
    for station in (
        "converge-adversarial-r1",
        *(f"converge-verify-adversarial-r{n}" for n in (2, 3)),
    ):
        host.answers[station] = answer(
            host, "adversarial", security, blocking=1, round=_round_of(station)
        )
    host.answers["converge-conformance-r1"] = answer(
        host, "conformance", _card("R1 blocking"), _card("R2 nit"), blocking=1
    )

    assert run(host) == 1

    assert [station for station, *_ in host.fixed] == [
        "converge-fix-r1",
        "converge-fix-r2",
    ]
    assert "by id: R1, S1, R2\n" in host.fixed[0][2]
    assert "by id: R1, S1\n" in host.fixed[1][2]
    written = events(host)
    assert "round 1 · pickup — R2 · with the fix" in written
    assert written[-1] == (
        f"round 3 · halt — cap reached, R1, S1 open · security S1 · pickup R2"
        f" · head {_head(host)}"
    )
    assert not any(" · done — " in line for line in written)
    assert "round: 3\n" in (host.folder() / "conformance.md").read_text()

    spent = (len(host.checks), len(host.fixed))
    log = (host.folder() / "status_log.md").read_text()

    assert run(host) == 1

    assert (len(host.checks), len(host.fixed)) == spent
    assert (host.folder() / "status_log.md").read_text().count("## Run") == (
        log.count("## Run")
    )
    assert events(host)[-1] == written[-1]


def test_an_accepted_blocker_converges_and_a_critical_one_blocks(host: Host) -> None:
    host.answers["converge-conformance-r1"] = answer(
        host, "conformance", _card("R1 blocking", status="accepted")
    )

    assert run(host) == 0

    assert host.fixed == []
    assert events(host)[-1].startswith("round 1 · done — converged in 1 round")

    host.answers = {
        "converge-adversarial-r1": answer(
            host, "adversarial", _card("S1 critical"), blocking=1
        )
    }

    assert run(host) == 0

    assert "by id: S1\n" in host.fixed[0][2]
    assert (
        events(host)[-1] == "round 2 · done — converged in 2 rounds · 0 cards to debt"
    )


@pytest.mark.slow
def test_plan_check_left_halts_amend_needed(host: Host) -> None:
    host.answers["converge-conformance-r1"] = answer(
        host, "conformance", _card("R1 blocking"), blocking=1
    )
    host.fixers = [lambda host: fixing(host, left="2.3")]
    host.exits["plan_check.py"] = 1
    host.printed["plan_check.py"] = "plan: 2.3 — `git grep -n x` exited 1\n  | x\n"

    assert run(host) == 1

    written = events(host)
    assert written[-2].startswith("round 1 · verify — round 2 · ")
    assert written[-1] == (
        f"round 1 · halt — amend needed — plan check: 2.3 · head {_head(host)}"
    )
    assert not any("-r2" in station for station, *_ in host.checks)

    host.fixers = [fixing, fixing]
    host.printed["plan_check.py"] = (
        "plan: tests/test_a.py:4 names gone, which the diff removes\n"
    )

    assert run(host) == 1

    assert "by id: plan check: tests/test_a.py:4\n" in host.fixed[-1][2]
    written = events(host)
    assert "round 1 · fix — sent plan check: tests/test_a.py:4" in written
    assert written[-1] == (
        "round 1 · halt — amend needed — plan check: tests/test_a.py:4"
        f" · head {_head(host)}"
    )

    def amending(host: Host) -> None:
        card = _card("R1 blocking", amend="yes", status="wontfix")
        answer(host, "conformance", card, blocking=1)(_head(host))
        idle(host)

    host.fixers = [amending]
    host.exits["plan_check.py"] = 0

    assert run(host) == 1

    written = events(host)
    assert written[-2] == "round 1 · fix — nothing committed · gate green"
    assert written[-1] == f"round 1 · halt — amend needed — R1 · head {_head(host)}"

    _amend(host)

    assert run(host) == 0

    assert heading(host).endswith(" · amend")
    assert (
        events(host)[-1] == "round 2 · done — converged in 2 rounds · 0 cards to debt"
    )

    host.exits["plan_check.py"] = 2
    host.printed["plan_check.py"] = "plan: cannot check — tasks.md: gone\n"
    host.fixers = []

    assert run(host) == 1

    assert events(host)[-1] == (
        "round 1 · halt — plan check: cannot check — tasks.md: gone"
        f" · head {_head(host)}"
    )


def test_a_timeout_alone_sends_nothing_back(host: Host) -> None:
    host.answers["converge-conformance-r1"] = answer(
        host, "conformance", _card("R1 blocking"), blocking=1
    )
    host.fixers = [fixing, fixing]
    host.exits["plan_check.py"] = 1
    host.printed["plan_check.py"] = (
        "plan: 1.1 — `sleep 5` timed out\nplan: 2.3 — `git grep x` exited 1\n  | x\n"
    )

    assert run(host) == 1

    # A failure beside a timeout is sent back, and the timeout is not.
    written = events(host)
    assert "round 1 · fix — sent plan check: 2.3" in written
    assert not any("timed out" in line for line in written)

    host.exits["plan_check.py"] = 1
    host.printed["plan_check.py"] = "plan: 1.1 — `sleep 5` timed out\n"
    host.fixers = [fixing]

    assert run(host) == 0

    written = events(host)
    assert "round 1 · plan check — timed out: 1.1" in written
    assert "round 1 · fix — sent plan check: 1.1" not in written
    assert written[-1].startswith("round 2 · done — converged in 2 rounds")


def test_round_one_pickup_rides_with_the_fix(host: Host) -> None:
    host.answers["converge-conformance-r1"] = answer(
        host,
        "conformance",
        _card("R1 blocking"),
        _card("R2 nit"),
        _card("R3 drift", size="a design change"),
        _card("R4 nit", size="a design change"),
        _card("R5 nit", status="fixed"),
        blocking=1,
    )
    host.answers["converge-adversarial-r1"] = answer(
        host,
        "adversarial",
        _card("S1 low", size="a test"),
        _card("S2 medium", size="a design change"),
    )

    assert run(host) == 0

    assert "by id: R1, R2, R3, S1\n" in host.fixed[0][2]
    written = events(host)
    assert written[5:7] == [
        "round 1 · pickup — R2, R3, S1 · with the fix",
        "round 1 · fix — sent R1, R2, R3, S1",
    ]
    assert written[-1] == "round 2 · done — converged in 2 rounds · 0 cards to debt"
    assert not any("pickup" in station for station, *_ in host.checks)

    host.answers = {
        "converge-conformance-r1": answer(host, "conformance", _card("R2 nit"))
    }
    host.fixers = [idle]
    host.ran.clear()

    assert run(host) == 0

    assert events(host)[5:] == [
        "round 1 · pickup — R2",
        "round 1 · fix — sent R2",
        "round 1 · fix — nothing committed · gate green",
        "round 1 · pickup — checked — nothing committed",
        "round 1 · debt — written 0001·R2",
        "round 1 · done — converged in 1 round · 1 card to debt",
    ]
    assert _ran(host)[3:] == ["plan_check.py", "gate_run.py", "grep", "gate_run.py"]


@pytest.mark.slow
def test_a_pickup_check_runs_on_the_needed_role(host: Host) -> None:
    first = _head(host)
    host.answers["converge-conformance-r1"] = answer(
        host, "conformance", _card("R2 nit")
    )

    assert run(host) == 0

    fixed = _head(host)
    span = f"{first[:7]}..{fixed[:7]}"
    assert events(host)[5:] == [
        "round 1 · pickup — R2",
        "round 1 · fix — sent R2",
        f"round 1 · fix — commit {fixed[:7]} · gate green",
        f"round 1 · freeze — {span} · 1 commit · 1 file",
        f"round 1 · verify — pickup check · {span} · gate green",
        "round 1 · pickup — checked · conformance clean · open_blocking 0"
        " · adversarial clean · open_blocking 0 · executor claude"
        " · model claude-opus-5-5 · effort high · tokens 1200",
        "round 1 · debt — none",
        "round 1 · done — converged in 1 round · 0 cards to debt",
    ]
    station, table, effort, told = host.checks[-1]
    assert (station, table, effort) == (
        "converge-verify-pickup-r1",
        "conformance",
        "medium",
    )
    assert told.startswith(f"role: pickup\nchange: {_CHANGE}\nround: 1\n")
    for role in ("conformance", "adversarial"):
        assert str(host.folder() / f"{role}.open.md") in told
    assert _ran(host)[3:] == [
        *("plan_check.py", "gate_run.py", "plan_check.py"),
        *("gate_run.py", "gate_check.py", "gate_run.py"),
    ]

    host.answers = {
        "converge-adversarial-r1": answer(
            host, "adversarial", _card("S1 low", size="a test")
        )
    }

    assert run(host) == 0

    assert host.checks[-1][:2] == ("converge-verify-pickup-r1", "adversarial")

    host.answers = {
        "converge-conformance-r1": answer(host, "conformance", _card("R2 nit")),
        "converge-verify-pickup-r1": answer(
            host, "conformance", _card("R5 blocking"), blocking=1
        ),
    }

    assert run(host) == 0

    written = events(host)
    checked = next(i for i, line in enumerate(written) if "pickup — checked" in line)
    assert " · conformance changes-requested · open_blocking 1 · " in written[checked]
    assert written[checked + 1] == "round 1 · fix — sent R5"
    assert written[-1] == "round 2 · done — converged in 2 rounds · 0 cards to debt"
    assert sum("pickup — " in line for line in written) == 2

    host.answers = {
        "converge-conformance-r1": answer(host, "conformance", _card("R2 nit"))
    }
    host.results["converge-verify-pickup-r1"] = Checked(
        1, False, _WORKERS["conformance"], "", False, None
    )

    assert run(host) == 1

    assert events(host)[-1] == (
        f"round 1 · halt — converge-verify-pickup-r1 worker exit 1 · head {_head(host)}"
    )


@pytest.mark.parametrize(
    ("mark", "events", "before"),
    [
        (None, ["halt — gate red · head a", "freeze — a..b"], True),
        (None, ["halt — converge-conformance-r1 worker exit 1", "start — b"], True),
        (None, ["halt — converge-fix-r1 timed out after 9s", "start — b"], True),
        (None, ["halt — red · head a", "start — b"], False),
        (
            None,
            ["halt — converge-fix-r1 worker exit 1", "verdicts — c", "start"],
            False,
        ),
        ("grant", ["halt — converge-fix-r3 worker exit 1", "fix — sent R1"], False),
        (None, ["halt — verify: halt · converge-fix-r1 worker exit 1", "start"], False),
        (
            None,
            ["halt — c-r1 worker exit 1 · stopped by a usage limit", "start"],
            False,
        ),
    ],
    ids=[
        "no-start",
        "exit",
        "timeout",
        "other",
        "verdicts",
        "grant",
        "verify",
        "limit",
    ],
)
def test_a_worker_halt_with_no_verdict_is_a_halt_before_round_1(
    mark: str | None, events: list[str], before: bool
) -> None:
    parsed = [statuslog.parse_event(f"10:00:00 · round 1 · {e}") for e in events]
    run = statuslog.Run(mark, [event for event in parsed if event])
    assert _converge()["before_round"](run) == before


def _plant(host: Host, *lines: str, mark: str | None = None) -> None:
    """Write a status log whose one run holds `lines`, oldest first."""
    title = f"## Run 1 — 2026-11-09 10:00{f' · {mark}' if mark else ''}"
    stamped = [f"10:00:{n:02d} · {line}" for n, line in enumerate(lines)]
    host.folder().mkdir(parents=True, exist_ok=True)
    (host.folder() / "status_log.md").write_text(
        f"# {_CHANGE} — converge status\n\n{title}\n" + "\n".join(stamped[::-1]) + "\n"
    )


def test_a_granted_round_goes_one_past_the_cap(host: Host) -> None:
    first = _head(host)
    blocker = answer(host, "conformance", _card("R1 blocking"), blocking=1, round=3)
    blocker(first)
    answer(host, "adversarial", round=3)(first)
    _plant(host, f"round 3 · halt — cap reached, R1 open · head {first}")
    host.answers["converge-verify-conformance-r4"] = answer(
        host, "conformance", _card("R9 nit"), round=4
    )

    assert run(host, grant=True) == 0

    fixed = _head(host)
    span = f"{first[:7]}..{fixed[:7]}"
    assert heading(host).endswith(" · grant")
    assert [station for station, *_ in host.fixed] == ["converge-fix-r3"]
    assert events(host) == [
        "round 3 · fix — sent R1 · grant",
        f"round 3 · fix — commit {fixed[:7]} · gate green",
        f"round 3 · freeze — {span} · 1 commit · 1 file",
        f"round 3 · verify — round 4 · {span} · gate green",
        _fan_out(4, span),
        _verdicts("conformance", 4),
        _verdicts("adversarial", 4),
        "round 4 · debt — written 0001·R9",
        "round 4 · done — converged in 4 rounds · 1 card to debt",
    ]

    answer(host, "conformance", _card("R1 blocking"), blocking=1, round=4)(fixed)
    host.answers["converge-verify-conformance-r5"] = answer(
        host, "conformance", _card("R1 blocking"), blocking=1, round=5
    )

    assert run(host, grant=True) == 1

    assert (
        events(host)[-1]
        == f"round 5 · halt — cap reached, R1 open · head {_head(host)}"
    )

    answer(host, "conformance", round=5)(_head(host))

    assert run(host, grant=True) == 1

    assert events(host)[-1].endswith(
        f" · halt — a granted round needs a blocking card open · head {_head(host)}"
    )


def test_round_three_is_the_cap_of_a_pickup_and_a_catch_up(host: Host) -> None:
    head = _head(host)
    answer(host, "conformance", _card("R2 nit"), round=3)(head)
    answer(host, "adversarial", round=3)(head)
    _plant(host, _verdicts("conformance", 3))

    assert run(host) == 0

    written = events(host)
    assert not any(" · pickup — " in line for line in written)
    assert host.fixed == []
    assert written[-1] == "round 3 · done — converged in 3 rounds · 1 card to debt"

    _commit(host.tree, {"src/late.py": "L = 1\n"}, "feat(0001-a): late")

    assert run(host) == 1

    assert events(host)[-1] == (
        "round 3 · halt — the files judged round 3, the cap: revert the late commits,"
        f" or re-converge from round 1 · head {_head(host)}"
    )


def test_a_resumed_counted_catch_up_halts_at_round_three(host: Host) -> None:
    head = _head(host)
    answer(host, "conformance", _card("R1 blocking"), blocking=1, round=3)(head)
    answer(host, "adversarial", round=3)(head)
    _plant(
        host,
        f"round 2 · catch-up — judged head {head[:7]} · HEAD {head[:7]} · counted",
        _verdicts("conformance", 3, "changes-requested", 1),
        mark="catch-up",
    )

    assert run(host) == 1

    assert events(host)[-1] == f"round 3 · halt — cap reached, R1 open · head {head}"
    assert host.fixed == []


def test_a_sandboxed_command_gets_the_converge_deadline(host: Host) -> None:
    converge = _converge()
    context = converge["Context"](
        host, _CHANGE, host.tree, _WORKERS, time.monotonic() + 100
    )
    out = io.StringIO()

    converge["sandboxed"](context, ["true"], out)

    assert host.timeouts[0] is not None
    assert 0 < host.timeouts[0] <= 100
    context.deadline = time.monotonic() - 5

    converge["sandboxed"](context, ["true"], out)

    assert host.timeouts[1] == 0


@pytest.mark.slow
def test_a_catch_up_runs_the_changed_verifies_in_one_plan_check(host: Host) -> None:
    assert run(host) == 0
    tasks = (
        _TASKS
        + "\n- [x] 1.1 One.\n  Verify: `git grep -n nope` prints a line.\n"
        + "- [x] 1.2 Two.\n  Verify: `true`.\n"
        + "- [x] 1.3 **HALT CHECK** Three.\n"
        + "  Verify: `git grep -n gone` prints a line.\n"
    )
    _commit(
        host.tree,
        {f"openspec/changes/{_CHANGE}/tasks.md": tasks},
        f"docs({_CHANGE}): amend the change directory",
    )
    host.ran.clear()
    host.exits["plan_check.py"] = 1
    host.printed["plan_check.py"] = (
        "plan: 1.2 — `true` exited 1\n  | out\nplan: 1.1 — `x` exited 1\n"
        "plan: 1.2 — `true` printed other\n"
    )

    assert run(host) == 1

    plans = [argv for argv in host.ran if Path(argv[1]).name == "plan_check.py"]
    assert len(plans) == 1
    assert plans[0][plans[0].index("--only") :] == ["--only", "1.1", "1.2"]
    assert ["git", "grep", "-n", "nope"] not in host.ran
    assert events(host)[-1].endswith(
        f" · halt — verify failed — 1.2, 1.1 · head {_head(host)}"
    )

    host.exits["plan_check.py"] = 2
    host.printed["plan_check.py"] = "plan: cannot check — git is missing\n"

    assert run(host) == 1

    assert events(host)[-1].endswith(
        f" · halt — plan check: cannot check — git is missing · head {_head(host)}"
    )

    host.exits["plan_check.py"] = 1
    host.printed["plan_check.py"] = "plan: tasks.md names nothing here\n"

    assert run(host) == 1

    assert events(host)[-1].endswith(
        f" · halt — plan check: tasks.md names nothing here · head {_head(host)}"
    )

    host.exits["plan_check.py"] = 0

    assert run(host) == 0


def _amend(host: Host, text: str = "# A — design, amended\n") -> str:
    return _commit(
        host.tree,
        {f"openspec/changes/{_CHANGE}/design.md": text},
        f"docs({_CHANGE}): amend the change directory",
    )


def _merge_main(host: Host, name: str) -> str:
    _commit(host.primary, {f"src/{name}.txt": f"{name}\n"}, f"main: {name}")
    _git(host.tree, "merge", "-q", "--no-ff", "-m", f"Merge main: {name}", "main")
    return _head(host)


@pytest.mark.slow
def test_a_catch_up_judges_the_new_commits(host: Host) -> None:
    base = _git(host.tree, "merge-base", "main", "HEAD")
    assert run(host) == 0
    judged = _head(host)
    late = _commit(host.tree, {"src/late.py": "L = 1\n"}, "feat(0001-a): late")
    host.answers["converge-adversarial-r2"] = answer(
        host, "adversarial", _card("S1 low", size="a test"), round=2
    )
    host.checks.clear()

    assert run(host) == 0

    span = f"{judged[:7]}..{late[:7]}"
    assert heading(host).endswith(" · catch-up")
    assert events(host) == [
        f"round 1 · catch-up — judged head {judged[:7]} · HEAD {late[:7]} · counted",
        f"round 1 · start — base {base[:7]} · head {late[:7]} · 2 commits · 2 files",
        f"round 1 · freeze — {span} · 1 commit · 1 file",
        f"round 1 · verify — round 2 · {span} · gate green",
        _fan_out(2, span),
        _verdicts("conformance", 2),
        _verdicts("adversarial", 2),
        "round 2 · debt — written 0001·S1",
        "round 2 · done — converged in 2 rounds · 1 card to debt",
    ]
    assert _stations(host) == [
        ("converge-adversarial-r2", "adversarial", None),
        ("converge-conformance-r2", "conformance", None),
    ]
    assert f"{judged}..{late}" in host.checks[0][3]
    assert (
        f"The scope: a catch-up round of 1 commit and 1 file.\n- {late} (parents"
        f" {judged}): ordinary diff\n"
    ) in host.checks[0][3]

    tasks = _TASKS + "\n- [x] 1.1 One.\n  Verify: `git grep -n nope` prints a line.\n"
    _commit(
        host.tree,
        {f"openspec/changes/{_CHANGE}/tasks.md": tasks},
        f"docs({_CHANGE}): amend the change directory",
    )
    host.exits["plan_check.py"] = 1
    host.printed["plan_check.py"] = "plan: 1.1 — `git grep -n nope` exited 1\n"

    assert run(host) == 1

    assert (
        events(host)[-1] == f"round 2 · halt — verify failed — 1.1 · head {_head(host)}"
    )

    host.exits["plan_check.py"] = [0, 0, 1, 0]

    assert run(host) == 0

    written = events(host)
    assert written[0].endswith(" · its own count")
    assert "round 2 · fix — sent plan check: 1.1" in written
    assert written[-1] == "round 3 · done — converged in 3 rounds · 0 cards to debt"

    merged = _merge_main(host, "moved")
    amended = _amend(host)
    host.checks.clear()

    assert run(host) == 0

    patch = (host.folder() / "diff.patch").read_text()
    assert patch.startswith(f"commit {merged}\nMerge: ")
    assert f"commit {amended}\n" in patch
    assert "src/moved.txt" not in patch
    parents = _git(host.tree, "rev-list", "--parents", "-n", "1", merged).split()[1:]
    assert len(host.checks) == 2
    for _, _, _, text in host.checks:
        assert (
            "The scope: a catch-up round of 2 commits and 1 file.\n"
            f"- {merged} (parents {' '.join(parents)}): remerge-diff\n"
            f"- {amended} (parents {merged}): ordinary diff\n"
        ) in text
        assert "src/moved.txt" not in text
    written = events(host)
    assert written[0].endswith(f"HEAD {amended[:7]} · its own count")
    assert written[2].endswith(" · 2 commits · 1 file")
    assert written[-1] == "round 4 · done — converged in 4 rounds · 0 cards to debt"

    _commit(host.tree, {"src/later.py": "L = 2\n"}, "feat(0001-a): later")

    assert run(host) == 1

    assert events(host)[-1] == (
        "round 4 · halt — the files judged round 4, the cap: revert the late commits,"
        f" or re-converge from round 1 · head {_head(host)}"
    )

    _git(host.tree, "checkout", "-q", "-b", "side", "main")
    _commit(host.tree, {"src/side.py": "S = 1\n"}, "side")
    _git(host.tree, "checkout", "-q", _CHANGE)
    _git(host.tree, "merge", "-q", "--no-ff", "-m", "Merge side", "side")

    assert run(host) == 1

    assert events(host)[-1] == (
        f"round 4 · halt — {_head(host)[:7]} is no merge of main: catch-up scope"
        f" cannot judge it · head {_head(host)}"
    )

    _git(host.tree, "reset", "-q", "--hard", "main")
    _commit(host.tree, {"src/b.py": "B = 1\n"}, "feat(0001-a): again")

    assert run(host) == 1

    assert events(host)[-1] == (
        f"round 4 · halt — history rewritten: {amended[:7]} is not on HEAD's"
        f" first-parent chain — re-converge from round 1 · head {_head(host)}"
    )


@pytest.mark.slow
def test_a_merge_only_catch_up_is_by_rule(host: Host) -> None:
    assert run(host) == 0
    judged = _head(host)
    merged = _merge_main(host, "moved")
    parents = _git(host.tree, "rev-list", "--parents", "-n", "1", merged).split()[1:]
    host.checks.clear()

    assert run(host) == 0

    assert events(host)[2:] == [
        "round 2 · by rule — clean, no conflict",
        "round 2 · debt — none",
        "round 2 · done — converged in 2 rounds · 0 cards to debt",
    ]
    assert events(host)[0] == (
        f"round 1 · catch-up — judged head {judged[:7]} · HEAD {merged[:7]}"
        " · its own count"
    )
    assert host.checks == []
    today = time.strftime("%Y-%m-%d")
    for role in ("conformance", "adversarial"):
        text = (host.folder() / f"{role}.md").read_text()
        for line in (f"head: {merged}", "round: 2", f"reviewed: {today}"):
            assert f"\n{line}\n" in text
        for line in ("mode: by-rule", "workers: 0", "verdict: clean"):
            assert f"\n{line}\n" in text
        assert (
            f"## By rule\n\n- {merged} ({' '.join(parents)}): no conflict\n\n"
            "## Resolution log\n"
        ) in text
        assert text.endswith(f"\n{today} · round 2 · by rule — clean\n")

    module = _converge()
    stop = module["INTEGRATE"]["Stop"]

    def refuse(cwd: Path, merge: str) -> str:
        raise stop(2, "integrate: cannot run — git merge failed")

    module["INTEGRATE"]["replay"] = refuse
    _merge_main(host, "again")

    assert run(host, module=module) == 0

    written = events(host)
    assert not any(" · by rule — " in line for line in written)
    assert written[3].startswith("round 2 · verify — round 3 · ")
    assert _stations(host) == [
        ("converge-adversarial-r3", "adversarial", None),
        ("converge-conformance-r3", "conformance", None),
    ]


@pytest.mark.slow
def test_a_shadow_round_runs_the_other_host_and_drives_nothing(host: Host) -> None:
    shadowed = {**_WORKERS, "shadow": True}
    host.answers["converge-shadow-conformance-r1"] = answer(
        host, "shadow-conformance", _card("R1 blocking"), blocking=1
    )

    assert run(host, shadowed) == 0

    assert _stations(host) == [
        ("converge-adversarial-r1", "adversarial", None),
        ("converge-conformance-r1", "conformance", None),
        ("converge-shadow-adversarial-r1", "shadow-adversarial", None),
        ("converge-shadow-conformance-r1", "shadow-conformance", None),
    ]
    assert events(host)[5:] == [
        "round 1 · shadow — conformance shared 0 · primary (claude) alone 0"
        " · shadow (claude) alone 1 · blockers shared 0 · primary 0 · shadow 1;"
        " adversarial shared 0 · primary (claude) alone 0 · shadow (claude) alone 0"
        " · blockers shared 0 · primary 0 · shadow 0",
        "round 1 · debt — none",
        "round 1 · done — converged in 1 round · 0 cards to debt",
    ]
    assert host.fixed == []

    host.checks.clear()
    host.results["converge-shadow-adversarial-r1"] = Checked(
        1, False, ("codex", None, None), "", False, None
    )
    host.answers["converge-conformance-r1"] = answer(
        host, "conformance", _card("R1 blocking"), blocking=1
    )

    assert run(host, shadowed) == 0

    written = events(host)
    assert (
        written[5] == "round 1 · shadow — converge-shadow-adversarial-r1 worker exit 1"
    )
    assert written[-1] == "round 2 · done — converged in 2 rounds · 0 cards to debt"
    assert sorted(station for station, *_ in host.checks if "shadow" in station) == [
        "converge-shadow-adversarial-r1",
        "converge-shadow-conformance-r1",
    ]

    assert run(host, {**shadowed, "adversarial": "skip"}) == 1

    assert events(host)[-1].startswith(
        "round 1 · halt — a shadow round beside a skipped checker"
    )

    gone = host.folder() / "shadow-conformance.md"
    host.results.clear()
    host.answers = {"converge-shadow-conformance-r1": lambda head: gone.unlink()}

    assert run(host, shadowed) == 0

    assert events(host)[5] == f"round 1 · shadow — overlap: cannot read — {gone}"


def _resumed(host: Host, case: str) -> list[str]:
    """Plant a run whose newest event is `case`'s; return the events planted."""
    base = _git(host.tree, "merge-base", "main", "HEAD")
    head = _head(host)
    span = f"{base[:7]}..{head[:7]}"
    start = f"round 1 · start — base {base[:7]} · head {head[:7]} · 1 commit · 1 file"
    frozen = f"round 1 · freeze — {span} · 1 commit · 1 file"
    fanned = _fan_out(1, span)
    judged = [start, frozen, fanned, _verdicts("conformance"), _verdicts("adversarial")]
    blocker, nit = _card("R1 blocking"), _card("R2 nit")
    cards = {
        "fix, a commit since": (blocker,),
        "fix, none since": (blocker,),
        "verify": (blocker,),
        "pickup with the fix": (blocker, nit),
        "pickup ids": (nit,),
        "pickup checked": (nit,),
        "pickup fix": (nit,),
        "pickup verify": (nit,),
    }.get(case, ())
    if case not in ("start", "freeze"):
        answer(host, "conformance", *cards, blocking=int(blocker in cards))(head)
        if case != "fan-out":
            answer(host, "adversarial")(head)
    planted = {
        "start": [start],
        "freeze": [start, frozen],
        "fan-out": [start, frozen, fanned],
        "verdicts": judged,
        "shadow": [*judged, "round 1 · shadow — conformance shared 0"],
        "fix, a commit since": [*judged, "round 1 · fix — sent R1"],
        "fix, none since": [*judged, "round 1 · fix — sent R1"],
        "pickup none": [*judged, "round 1 · pickup — none"],
        "pickup ids": [*judged, "round 1 · pickup — R2"],
        "pickup checked": [
            *judged,
            "round 1 · pickup — R2",
            "round 1 · pickup — checked",
        ],
        "pickup with the fix": [*judged, "round 1 · pickup — R2 · with the fix"],
        "debt": [*judged, "round 1 · debt — none"],
        "pickup fix": [*judged, "round 1 · pickup — R2", "round 1 · fix — sent R2"],
    }
    if case in ("verify", "pickup verify"):
        fixed = _commit(host.tree, {"src/fix.py": "F = 1\n"}, "fix(0001-a): it")
        span = f"{head[:7]}..{fixed[:7]}"
        picked = case == "pickup verify"
        lines = [
            *judged,
            *(["round 1 · pickup — R2"] if picked else []),
            f"round 1 · fix — sent {'R2' if picked else 'R1'}",
            f"round 1 · fix — commit {fixed[:7]} · gate green",
            f"round 1 · freeze — {span} · 1 commit · 1 file",
            f"round 1 · verify — {'pickup check' if picked else 'round 2'} · {span}"
            " · gate green",
        ]
        _plant(host, *lines)
        return lines
    if case in ("fix, a commit since", "grant", "pickup fix"):
        _commit(host.tree, {"src/fix.py": "F = 1\n"}, "fix(0001-a): it")
    if case == "grant":
        answer(host, "conformance", blocker, blocking=1, round=3)(head)
        answer(host, "adversarial", round=3)(head)
        _plant(host, "round 3 · fix — sent R1 · grant", mark="grant")
        return ["round 3 · fix — sent R1 · grant"]
    if case == "catch-up at round three":
        amended = _amend(host)
        answer(host, "conformance", blocker, blocking=1, round=4)(amended)
        answer(host, "adversarial", round=4)(amended)
        span = f"{head[:7]}..{amended[:7]}"
        lines = [
            f"round 3 · catch-up — judged head {head[:7]} · HEAD {amended[:7]}"
            " · its own count",
            f"round 3 · start — base {base[:7]} · head {amended[:7]} · 2 commits",
            f"round 3 · freeze — {span} · 1 commit · 1 file",
            _verdicts("conformance", 4, "changes-requested", 1),
        ]
        _plant(host, *lines, mark="catch-up")
        return lines
    if case in ("catch-up", "by rule"):
        moved = _merge_main(host, "moved")
        lines = [
            f"round 1 · catch-up — judged head {head[:7]} · HEAD {moved[:7]}"
            " · its own count"
        ]
        if case == "by rule":
            lines += [
                f"round 1 · start — base {base[:7]} · head {moved[:7]}",
                "round 2 · by rule — clean, no conflict",
            ]
        _plant(host, *lines, mark="catch-up")
        return lines
    _plant(host, *planted[case])
    return planted[case]


_RESUMED: dict[str, tuple[list[str], list[str]]] = {
    "start": (
        ["freeze", "fan-out", "verdicts", "verdicts", "debt", "done"],
        ["conformance-r1", "adversarial-r1"],
    ),
    "freeze": (
        ["fan-out", "verdicts", "verdicts", "debt", "done"],
        ["conformance-r1", "adversarial-r1"],
    ),
    "fan-out": (["fan-out", "verdicts", "debt", "done"], ["adversarial-r1"]),
    "verdicts": (["debt", "done"], []),
    "shadow": (["debt", "done"], []),
    "fix, a commit since": (
        ["freeze", "verify", "fan-out", "verdicts", "verdicts", "debt", "done"],
        ["verify-conformance-r2", "verify-adversarial-r2"],
    ),
    "fix, none since": (
        [
            *("fix", "fix", "freeze", "verify", "fan-out"),
            *("verdicts", "verdicts", "debt", "done"),
        ],
        ["verify-conformance-r2", "verify-adversarial-r2"],
    ),
    "verify": (
        ["verify", "fan-out", "verdicts", "verdicts", "debt", "done"],
        ["verify-conformance-r2", "verify-adversarial-r2"],
    ),
    "pickup none": (["debt", "done"], []),
    "pickup ids": (
        ["fix", "fix", "freeze", "verify", "pickup", "debt", "done"],
        ["verify-pickup-r1"],
    ),
    "pickup checked": (["debt", "done"], []),
    "pickup fix": (
        ["freeze", "verify", "pickup", "debt", "done"],
        ["verify-pickup-r1"],
    ),
    "pickup verify": (["verify", "pickup", "debt", "done"], ["verify-pickup-r1"]),
    "pickup with the fix": (
        [
            *("fix", "fix", "freeze", "verify", "fan-out"),
            *("verdicts", "verdicts", "debt", "done"),
        ],
        ["verify-conformance-r2", "verify-adversarial-r2"],
    ),
    "debt": (["done"], []),
    "catch-up": (
        ["catch-up", "start", "by rule", "debt", "done"],
        [],
    ),
    "by rule": (["debt", "done"], []),
    "catch-up at round three": (
        [
            *("fix", "fix", "freeze", "verify", "fan-out", "verdicts"),
            *("verdicts", "debt", "done"),
        ],
        ["verify-conformance-r5", "verify-adversarial-r5"],
    ),
    "grant": (
        ["freeze", "verify", "fan-out", "verdicts", "verdicts", "debt", "done"],
        ["verify-conformance-r4", "verify-adversarial-r4"],
    ),
}


@pytest.mark.parametrize("case", list(_RESUMED))
def test_a_run_resumes_from_its_status_log(host: Host, case: str) -> None:
    planted = _resumed(host, case)
    names, stations = _RESUMED[case]

    assert run(host) == 0

    log = (host.folder() / "status_log.md").read_text()
    assert log.count("\n## Run") == 1
    written = events(host)
    assert written[: len(planted)] == planted
    new = written[len(planted) :]
    assert [line.split(" · ", 1)[1].split(" — ")[0] for line in new] == names
    assert sorted(
        station.removeprefix("converge-") for station, *_ in host.checks
    ) == sorted(stations)
    if case == "fix, none since":
        assert "by id: R1\n" in host.fixed[0][2]
    if case == "pickup with the fix":
        assert "by id: R1, R2\n" in host.fixed[0][2]
    if case == "pickup ids":
        assert "by id: R2\n" in host.fixed[0][2]


_DESIGN = "a design change"


def _filed(card: str, number: str = "0001") -> str:
    """Return a card as the debt holds it: its id qualified by `number`."""
    ident = card.split()[1].removeprefix("**")
    return card.replace(f"- **{ident} — ", f"- **{number}·{ident} — ", 1)


def _debt(host: Host) -> Path:
    path = host.primary / ".minions" / "debt.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@pytest.mark.slow
def test_the_debt_is_written_once_under_its_lock(
    host: Host, monkeypatch: pytest.MonkeyPatch
) -> None:
    debt = _debt(host)
    held = _filed(_card("R3 nit", size=_DESIGN))
    other = _filed(_card("R1 nit"), "0000")
    debt.write_text(f"# Debt\n\n*Deferred.*\n\n## 0001-a\n\n{held}## 0000-z\n\n{other}")
    cards = [_card("R2 nit", size=_DESIGN), _card("R3 nit", size=_DESIGN)]
    host.answers["converge-conformance-r1"] = answer(host, "conformance", *cards)
    host.answers["converge-adversarial-r1"] = answer(
        host, "adversarial", _card("S1 low", size=_DESIGN)
    )
    lock = host.primary / ".minions" / "debt.lock"

    assert run(host) == 0

    added = _filed(cards[0]) + _filed(_card("S1 low", size=_DESIGN))
    text = debt.read_text()
    assert text == (
        f"# Debt\n\n*Deferred.*\n\n## 0001-a\n\n{held}{added}\n## 0000-z\n\n{other}"
    )
    assert events(host)[-2:] == [
        "round 1 · debt — written 0001·R2, 0001·S1",
        "round 1 · done — converged in 1 round · 2 cards to debt",
    ]
    assert not lock.exists()

    assert run(host) == 0

    assert debt.read_text() == text
    assert events(host)[-2] == "round 1 · debt — none"

    old = host.primary / ".minions" / "backlog.md"
    old.write_text("# Backlog\n")
    late = _card("R4 nit", size=_DESIGN)
    host.answers["converge-conformance-r1"] = answer(host, "conformance", *cards, late)

    assert run(host) == 1

    assert events(host)[-1] == (
        "round 1 · halt — .minions/debt.lock not taken — an old .minions/backlog.md"
        f" stands; /mf-ship moves it at a run's start · head {_head(host)}"
    )
    assert not lock.exists()
    assert debt.read_text() == text
    runs = (host.folder() / "status_log.md").read_text().count("\n## Run")
    old.unlink()

    assert run(host) == 0

    assert (host.folder() / "status_log.md").read_text().count("\n## Run") == runs
    assert events(host)[-2] == "round 1 · debt — written 0001·R4"
    assert _filed(late) in debt.read_text()

    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", sleeps.append)
    lock.mkdir()
    host.answers["converge-conformance-r1"] = answer(
        host, "conformance", _card("R5 nit", size=_DESIGN)
    )

    assert run(host) == 1

    assert events(host)[-1] == (
        f"round 1 · halt — .minions/debt.lock held for 10 minutes · head {_head(host)}"
    )
    # A timed `subprocess` wait sleeps too: count the lock's naps alone.
    assert [nap for nap in sleeps if nap == 5] == [5] * 120
    assert lock.is_dir()
    assert "0001·R5" not in debt.read_text()
    _commit(host.tree, {"src/late.py": "L = 1\n"}, "feat(0001-a): late")

    assert run(host) == 1

    assert events(host)[-1] == (
        "round 1 · halt — conformance.md is not clean at HEAD: the debt write cannot"
        f" go on · head {_head(host)}"
    )

    lock.rmdir()
    (lock.parent / "debt.md.tmp").mkdir()

    assert run(host) == 1

    assert events(host)[-1].startswith("round 2 · halt — .minions/debt.md cannot be")
    assert not lock.exists()

    debt.unlink()
    debt.symlink_to(debt.with_name("debt.md.tmp"))

    assert run(host) == 1

    assert events(host)[-1] == (
        "round 1 · halt — debt_match.py exited 2 — the debt cannot be matched"
        f" · head {_head(host)}"
    )


def test_a_still_true_command_runs_sandboxed_and_a_prose_card_goes_unchecked(
    host: Host, capsys: pytest.CaptureFixture[str]
) -> None:
    host.exits.update({"false": 0, "true": 1, "ls": 2})
    cards = {
        "R2": _card("R2 nit", size=_DESIGN, still="`false` prints the line"),
        "R3": _card("R3 nit", size=_DESIGN, still="`true -x 'a b'`"),
        "R4": _card("R4 nit", size=_DESIGN, still="`ls src`"),
        "R5": _card("R5 nit", size=_DESIGN, still="read `src/a.py` and its caller"),
        "R6": _card("R6 nit", size=_DESIGN, still="`'unbalanced`"),
        "R7": _card(
            "R7 nit",
            amend="yes",
            status="wontfix",
            size=_DESIGN,
            still="read `src/a.py` and its caller",
        ),
    }
    host.answers["converge-conformance-r1"] = answer(
        host, "conformance", *cards.values()
    )

    assert run(host) == 0

    text = _debt(host).read_text()
    for ident in ("R2", "R4", "R5", "R6", "R7"):
        assert _filed(cards[ident]) in text
    assert "R3" not in text
    assert events(host)[-2] == (
        "round 1 · debt — written 0001·R2, 0001·R4, 0001·R5, 0001·R6, 0001·R7 · moot R3"
    )
    assert [argv for argv in host.ran if argv[0] in ("false", "true", "ls")] == [
        ["false"],
        ["true", "-x", "a b"],
        ["ls", "src"],
    ]
    assert "; moot R3 (`true -x 'a b'` exited 1); " in capsys.readouterr().out


@pytest.mark.slow
def test_an_amend_card_halts_the_debt(host: Host) -> None:
    amend = _card(
        "R2 nit", amend="yes", status="wontfix", size=_DESIGN, still="`false`"
    )
    host.answers["converge-conformance-r1"] = answer(host, "conformance", amend)
    host.exits["false"] = 0
    debt = _debt(host)

    assert run(host) == 1

    written = events(host)
    assert written[-1] == f"round 1 · halt — amend needed — R2 · head {_head(host)}"
    assert not any(" · debt — " in line for line in written)
    assert not debt.exists()

    host.exits["false"] = 1

    assert run(host) == 0

    assert events(host)[-2] == "round 1 · debt — moot R2"
    assert "0001·R2" not in debt.read_text()

    host.exits["false"] = 0

    assert run(host) == 1

    _amend(host)
    host.answers["converge-conformance-r2"] = answer(
        host, "conformance", amend, round=2
    )

    assert run(host) == 0

    assert heading(host).endswith(" · amend")
    assert events(host)[-2] == "round 2 · debt — written 0001·R2"
    assert _filed(amend) in debt.read_text()

    assert run(host) == 0

    assert events(host)[-2] == "round 1 · debt — none"


def test_a_fixed_repeats_old_card_is_cleared(
    host: Host, capsys: pytest.CaptureFixture[str]
) -> None:
    # A blank line inside the paid card does not end it: its later fields go too.
    gone = _filed(_card("R1 nit", still="`true`"), "0000").replace(
        "  - **Still true?**", "\n  - **Still true?**"
    )
    kept = _filed(_card("R2 nit", still="`false`"), "0000")
    sibling = _filed(_card("R6 nit", still="`false`"), "0000")
    debt = _debt(host)
    debt.write_text(
        f"# Debt\n\n*Deferred.*\n\n## 0000-y\n\n{gone}{sibling}\n## 0000-z\n\n{kept}"
    )
    host.exits.update({"true": 1, "false": 0})
    host.answers["converge-conformance-r1"] = answer(
        host,
        "conformance",
        _card("R3 nit", status="verified", related="repeat of `0000·R1`."),
        _card("R4 nit", status="verified", related="repeat of 0000·R2, one level up."),
        _card("R5 nit", status="verified", related="repeat of 0000·R9."),
    )

    assert run(host) == 0

    assert debt.read_text() == (
        f"# Debt\n\n*Deferred.*\n\n## 0000-y\n\n{sibling}\n## 0000-z\n\n{kept}"
    )
    assert events(host)[-2] == "round 1 · debt — cleared 0000·R1"
    assert "; cleared 0000·R1 (`true` exited 1); " in capsys.readouterr().out


@pytest.mark.slow
def test_a_failed_worker_gets_one_retry(host: Host) -> None:
    models = _WORKERS["conformance"]
    host.results["converge-conformance-r1"] = [
        Checked(1, False, models, "", False, None),
        Checked(0, False, models, "", False, 1200),
    ]

    assert run(host) == 0

    written = events(host)
    assert written[3] == (
        "round 1 · fan-out — retry — conformance: converge-conformance-r1 worker exit 1"
    )
    assert written[-1] == "round 1 · done — converged in 1 round · 0 cards to debt"
    told = [text for station, _, _, text in host.checks if station.endswith("ce-r1")]
    assert len(told) == 2
    assert told[0] == told[1]

    (host.folder() / "adversarial.md").unlink()
    calls: list[str] = []

    def late(head: str) -> None:
        calls.append(head)
        if len(calls) > 1:
            answer(host, "adversarial")(head)

    host.answers["converge-adversarial-r1"] = late

    assert run(host) == 0

    assert events(host)[3] == (
        "round 1 · fan-out — retry — adversarial: adversarial.md is missing: its"
        " checker left no findings file"
    )

    host.results["converge-conformance-r1"] = Checked(1, False, models, "", False, None)
    host.checks.clear()

    assert run(host) == 1

    written = events(host)
    assert written[-2] == (
        "round 1 · fan-out — retry — conformance: converge-conformance-r1 worker exit 1"
    )
    assert written[-1] == (
        f"round 1 · halt — converge-conformance-r1 worker exit 1 · head {_head(host)}"
    )

    host.results["converge-conformance-r1"] = Checked(0, True, models, "", False, None)
    host.checks.clear()

    assert run(host) == 1

    assert [station for station, *_ in host.checks].count(
        "converge-conformance-r1"
    ) == 1
    assert " · halt — converge-conformance-r1 timed out after " in events(host)[-1]

    host.results.clear()
    host.answers = {
        "converge-conformance-r1": answer(
            host, "conformance", _card("R1 blocking"), blocking=1
        )
    }
    host.fixers = [lambda host: 1, fixing]

    assert run(host) == 0

    written = events(host)
    sent = written.index("round 1 · fix — sent R1")
    assert written[sent + 1] == (
        "round 1 · fan-out — retry — fix: converge-fix-r1 worker exit 1"
    )
    assert [station for station, *_ in host.fixed] == ["converge-fix-r1"] * 2

    # A zero exit does not excuse a call to a tool the station lacks.
    host.fixers = [fixing]
    host.lacking["converge-fix-r1"] = ["Agent", "Task"]

    assert run(host) == 1

    assert events(host)[-1] == (
        "round 1 · halt — converge-fix-r1 asked for a tool its station lacks:"
        f" Agent, Task · head {_head(host)}"
    )

    host.answers.clear()
    host.lacking = {"converge-conformance-r1": ["Agent"]}

    assert run(host) == 1

    assert events(host)[-1] == (
        "round 1 · halt — converge-conformance-r1 asked for a tool its station"
        f" lacks: Agent · head {_head(host)}"
    )


@pytest.mark.slow
def test_a_codex_fixer_runs_through_host_fix_and_halts_at_a_limit(host: Host) -> None:
    codex = ("codex", "gpt-6.1-sol", "medium")
    workers = {**_WORKERS, "fix": codex}
    host.answers["converge-conformance-r1"] = answer(
        host, "conformance", _card("R1 blocking"), blocking=1
    )

    assert run(host, workers) == 0

    assert host.fixed == []
    assert [(station, models) for station, models, _ in host.codexed] == [
        ("converge-fix-r1", codex)
    ]
    assert (
        "Co-Authored-By: Codex gpt-6.1-sol <noreply@openai.com>" in host.codexed[0][2]
    )

    limit = "codex usage limit — the fixer · resets 5:50 PM"
    host.fixes = [Checked(1, False, codex, limit, False, None)]

    assert run(host, workers) == 1

    assert len(host.codexed) == 2
    assert events(host)[-1] == f"round 1 · halt — {limit} · head {_head(host)}"

    host.fixes = [Checked(1, False, codex, "", False, None)]

    assert run(host, workers) == 0

    assert len(host.codexed) == 4
    assert host.fixed == []


def test_a_claude_fixers_prompt_names_its_attribution(host: Host) -> None:
    host.answers["converge-conformance-r1"] = answer(
        host, "conformance", _card("R1 blocking"), blocking=1
    )

    assert run(host, _WORKERS) == 0

    assert "the attribution line your session names" in host.fixed[0][2]
    assert host.codexed == []


_FOLDER = f"openspec/changes/{_CHANGE}"
_DESIGN_MD = f"{_FOLDER}/design.md"
_DELTA = f"{_FOLDER}/specs/sdd/spec.md"
_DECIDED = (
    "# A — design\n\nProse.\n\n## Decisions\n\n| id | decision |\n|---|---|\n"
    "| D1 | One rule |\n\n### D1\n\nIt holds.\n\n## Tests\n\nNone.\n"
)
_PLAN_TEXT = "fix(0001-a): it\n\nPlan-text: R1\nChange: 0001-a"
_NO_TRAILER = "fix(0001-a): it\n\nChange: 0001-a"


def _plan_text(host: Host, files: dict[str, str], message: str) -> str | None:
    """Commit `files` as one fix; return the halt `plan_text` raises on it, or None."""
    converge = _converge()
    context = converge["Context"](host, _CHANGE, host.tree, _WORKERS, 1e12)
    before = _head(host)
    _commit(host.tree, files, message)
    try:
        converge["plan_text"](context, before, _head(host))
    except converge["Halt"] as halt:
        return str(halt)
    return None


def _seeded(host: Host) -> None:
    """Commit a design with a decisions table, `### D1` and a delta, as a build did."""
    _commit(host.tree, {_DESIGN_MD: _DECIDED, _DELTA: "## ADDED\n"}, "feat: seed")


def test_a_fix_commit_editing_tasks_md_halts(host: Host) -> None:
    for at, message in enumerate((_NO_TRAILER, _PLAN_TEXT)):
        said = _plan_text(host, {f"{_FOLDER}/tasks.md": f"{_TASKS}{at}\n"}, message)

        assert said == (
            f"plan edit refused — {_head(host)[:7]} edits {_FOLDER}/tasks.md"
        )


def test_a_fix_commit_editing_proposal_md_halts(host: Host) -> None:
    for at, message in enumerate((_NO_TRAILER, _PLAN_TEXT)):
        proposal = {f"{_FOLDER}/proposal.md": f"---\nbump: minor\n---\n\n# A{at}\n"}
        said = _plan_text(host, proposal, message)

        assert said == (
            f"plan edit refused — {_head(host)[:7]} edits {_FOLDER}/proposal.md"
        )


def _found_r1(host: Host) -> None:
    """Write a conformance file holding card R1 at the head."""
    answer(host, "conformance", _card("R1 blocking"), blocking=1)(_head(host))


def test_a_trailer_naming_no_card_of_the_findings_is_refused(host: Host) -> None:
    _seeded(host)
    _found_r1(host)
    for at, trailer in enumerate(("none", "R9", "misnamed")):
        message = _PLAN_TEXT.replace("Plan-text: R1", f"Plan-text: {trailer}")

        said = _plan_text(host, {_DELTA: f"## ADDED\n\nWorded {at}.\n"}, message)

        assert said == (
            f"plan edit refused — {_head(host)[:7]} names no card of the findings"
            " under Plan-text:"
        )


def test_a_trailer_with_prose_beside_a_card_id_passes(host: Host) -> None:
    _seeded(host)
    _found_r1(host)
    message = _PLAN_TEXT.replace("Plan-text: R1", "Plan-text: R1, the delta words it")

    assert _plan_text(host, {_DELTA: "## ADDED\n\nWorded.\n"}, message) is None


def test_a_fix_commit_may_edit_the_delta_with_the_trailer(host: Host) -> None:
    _seeded(host)
    _found_r1(host)
    edited = {_DELTA: "## ADDED\n\nWorded.\n", "src/a.py": "A = 2\n"}

    assert _plan_text(host, edited, _PLAN_TEXT) is None


def test_a_fix_commit_editing_the_delta_without_the_trailer_halts(host: Host) -> None:
    _seeded(host)

    said = _plan_text(host, {_DELTA: "## ADDED\n\nWorded.\n"}, _NO_TRAILER)

    assert said == (
        f"plan edit refused — {_head(host)[:7]} edits {_DELTA}"
        " with no Plan-text: trailer"
    )


def test_a_fix_commit_editing_a_decisions_body_is_taken(host: Host) -> None:
    _seeded(host)
    _found_r1(host)
    reworded: dict[str, str] = {
        _DESIGN_MD: _DECIDED.replace("It holds.", "It holds at the call.")
    }

    assert _plan_text(host, reworded, _PLAN_TEXT) is None

    # Twin: the same rewording with no trailer halts.
    again: dict[str, str] = {
        _DESIGN_MD: _DECIDED.replace("It holds.", "It holds at each call.")
    }
    said = _plan_text(host, again, _NO_TRAILER)

    assert said == (
        f"plan edit refused — {_head(host)[:7]} edits {_DESIGN_MD}"
        " with no Plan-text: trailer"
    )


def test_a_fix_commit_editing_the_decisions_table_halts(host: Host) -> None:
    _seeded(host)
    for edited, what in (
        (_DECIDED.replace("| One rule |", "| Two rules |"), "the decisions table"),
        (_DECIDED.replace("### D1\n", "### D1\n\nOne.\n\n### D2\n"), "a heading"),
        (_DECIDED.replace("## Tests\n", "## Checks\n"), "a heading"),
    ):
        said = _plan_text(host, {_DESIGN_MD: edited}, _PLAN_TEXT)

        assert said is not None
        assert said.startswith(f"plan edit refused — {_head(host)[:7]} changes {what}")
        _git(host.tree, "reset", "-q", "--hard", "HEAD^")


def test_a_fix_note_alone_needs_no_trailer(host: Host) -> None:
    _seeded(host)
    note = "It holds.\nFix note (2026-11-09, R1): the rule holds at the call.\n"
    for edited in (
        _DECIDED.replace("It holds.\n", note),
        _DECIDED.replace("Prose.", "Prose, corrected."),
        _DECIDED.replace("None.", "One test."),
    ):
        assert _plan_text(host, {_DESIGN_MD: edited}, _NO_TRAILER) is None

    assert _plan_text(host, {"src/a.py": "A = 3\n"}, _NO_TRAILER) is None


def test_a_security_card_of_high_is_left_to_the_halt(host: Host) -> None:
    _seeded(host)
    message = _PLAN_TEXT.replace("Plan-text: R1", "Plan-text: R1, S1")
    for at, (card, blocking, refused) in enumerate(
        (
            (_card("S1 high", category="security"), 1, True),
            (_card("S1 critical", category="security"), 1, True),
            (_card("S1 high", category="stability"), 1, False),
            (_card("S1 medium", category="security"), 0, False),
        )
    ):
        answer(host, "adversarial", card, blocking=blocking)(_head(host))
        said = _plan_text(host, {_DELTA: f"## ADDED\n\nWorded {at}.\n"}, message)

        assert said == (
            f"plan edit refused — {_head(host)[:7]} names security card S1"
            " under Plan-text:"
            if refused
            else None
        )


def test_the_fix_pass_runs_the_plan_text_check(host: Host) -> None:
    host.answers["converge-conformance-r1"] = answer(
        host, "conformance", _card("R1 blocking"), blocking=1
    )

    def planning(host: Host) -> None:
        _commit(host.tree, {f"{_FOLDER}/tasks.md": f"{_TASKS}x\n"}, _PLAN_TEXT)

    host.fixers = [planning]

    assert run(host) == 1

    sha = _head(host)
    assert events(host)[-2:] == [
        "round 1 · fix — sent R1",
        f"round 1 · halt — plan edit refused — {sha[:7]} edits {_FOLDER}/tasks.md"
        f" · head {sha}",
    ]
    assert _ran(host) == ["make", "gate_run.py", "gate_check.py", "plan_check.py"]


def test_a_fix_commit_under_a_name_git_quotes_is_read(host: Host) -> None:
    # Why: 0147-amends-alone design D3.
    odd = f"{_FOLDER}/specs/é/spec.md"

    said = _plan_text(host, {odd: "## ADDED\n"}, _NO_TRAILER)

    assert said == (
        f"plan edit refused — {_head(host)[:7]} edits {odd} with no Plan-text: trailer"
    )
    assert _plan_text(host, {f"{_FOLDER}/é.md": "x\n"}, _PLAN_TEXT) == (
        f"plan edit refused — {_head(host)[:7]} edits {_FOLDER}/é.md"
    )


def test_a_merge_in_a_fix_pass_halts(host: Host) -> None:
    # A merge's own edits show in no listed commit. Why: 0147-amends-alone design D3.
    base = _head(host)
    _git(host.tree, "checkout", "-q", "-b", "side")
    _commit(host.tree, {"src/side.py": "S = 1\n"}, "fix(0001-a): side")
    _git(host.tree, "checkout", "-q", "-")
    converge = _converge()
    context = converge["Context"](host, _CHANGE, host.tree, _WORKERS, 1e12)
    _git(host.tree, "merge", "-q", "--no-ff", "--no-commit", "side")
    tasks = host.tree / _FOLDER / "tasks.md"
    tasks.parent.mkdir(parents=True, exist_ok=True)
    tasks.write_text(f"{_TASKS}merged\n")
    _git(host.tree, "add", str(tasks))
    _git(host.tree, "commit", "-q", "-m", _PLAN_TEXT)

    with pytest.raises(converge["Halt"]) as halt:
        converge["plan_text"](context, base, _head(host))

    assert str(halt.value) == (
        f"plan edit refused — {_head(host)[:7]} is a merge in a fix pass"
    )


def test_a_killed_fixers_commit_is_read_on_the_resume(host: Host) -> None:
    # The commit stays when the fixer is killed before `fix` reads it.
    # Why: 0147-amends-alone design D3.
    planted = _resumed(host, "fix, a commit since")
    _commit(host.tree, {f"{_FOLDER}/tasks.md": f"{_TASKS}x\n"}, _PLAN_TEXT)

    assert run(host) == 1

    sha = _head(host)
    assert events(host)[len(planted)] == (
        f"round 1 · halt — plan edit refused — {sha[:7]} edits {_FOLDER}/tasks.md"
        f" · head {sha}"
    )


def test_a_verify_round_reads_a_plan_text_edit(host: Host) -> None:
    _seeded(host)
    host.answers["converge-conformance-r1"] = answer(
        host, "conformance", _card("R1 blocking"), blocking=1
    )

    def wording(host: Host) -> None:
        edited = {_DELTA: "## ADDED\n\nThe rule holds at the call.\n", "src/a.py": "2"}
        _commit(host.tree, edited, _PLAN_TEXT)
        (host.folder() / "fix.md").write_text("fixed: R1\nplan check left: none\n")

    host.fixers = [wording]

    assert run(host) == 0

    patch = (host.folder() / "diff.patch").read_text()
    assert f"+++ b/{_DELTA}" in patch
    assert "+The rule holds at the call." in patch
    told = next(text for station, _, _, text in host.checks if "verify-c" in station)
    assert "- A plan-text edit in the fix diff, its commit under a `Plan-text:`" in told


def _twice(
    first: Callable[[str], None], then: Callable[[str], None]
) -> Callable[[str], None]:
    """Return a checker's answer: `first` on its first call, `then` after."""
    calls: list[str] = []

    def write(head: str) -> None:
        calls.append(head)
        (first if len(calls) == 1 else then)(head)

    return write


def test_a_malformed_file_gets_a_rewrite_then_a_debt_card(host: Host) -> None:
    broken = answer(host, "conformance", inconclusive=None)
    host.answers["converge-conformance-r1"] = _twice(
        broken, answer(host, "conformance")
    )

    assert run(host) == 0

    why = "conformance.md is malformed: inconclusive is missing"
    written = events(host)
    assert written[3:] == [
        _verdicts("adversarial"),
        f"round 1 · fan-out — rewrite — conformance: {why}",
        "round 1 · debt — none",
        "round 1 · done — converged in 1 round · 0 cards to debt",
    ]
    station, table, effort, told = host.checks[-1]
    assert (station, table, effort) == ("converge-conformance-r1", "conformance", None)
    assert told.startswith(f"role: conformance\nchange: {_CHANGE}\nround: 1\n")
    assert f"{host.folder() / 'conformance.md'} breaks the findings file" in told
    assert f": {why}.\n" in told

    host.answers["converge-conformance-r1"] = answer(
        host, "conformance", _card("R1 blocking"), blocking=1, inconclusive=None
    )

    assert run(host) == 0

    assert events(host)[-2:] == [
        "round 1 · debt — written 0001·M1",
        "round 1 · done — converged in 1 round · 1 card to debt",
    ]
    text = _debt(host).read_text()
    assert (
        "- **0001·M1 — conformance's findings file was malformed after a rewrite**\n"
    ) in text
    assert f"  - **Evidence:** {why} · read.\n" in text
    assert host.fixed == []

    models = _WORKERS["conformance"]
    host.results["converge-conformance-r1"] = [
        Checked(0, False, models, "", False, None),
        Checked(0, True, models, "", False, None),
    ]

    assert run(host) == 1

    assert " · halt — converge-conformance-r1 timed out after " in events(host)[-1]


def test_changes_requested_with_nits_alone_counts_clean(host: Host) -> None:
    nit = _card("R1 nit", size="a module")
    host.answers["converge-conformance-r1"] = answer(
        host, "conformance", nit, verdict="changes-requested"
    )

    assert run(host) == 0

    assert host.fixed == []
    assert [station for station, *_ in host.checks].count(
        "converge-conformance-r1"
    ) == 1
    text = (host.folder() / "conformance.md").read_text()
    assert "verdict: clean\n" in text
    assert "open_blocking: 0\n" in text
    assert "changes-requested" not in text
    assert events(host)[3] == _verdicts("conformance", verdict="changes-requested")


def test_changes_requested_with_no_card_gets_a_rewrite(host: Host) -> None:
    host.answers["converge-conformance-r1"] = answer(
        host, "conformance", verdict="changes-requested"
    )

    assert run(host) == 0

    why = "conformance.md is malformed: verdict is changes-requested with no open card"
    assert f"round 1 · fan-out — rewrite — conformance: {why}" in events(host)
    assert [station for station, *_ in host.checks].count(
        "converge-conformance-r1"
    ) == 2
    text = (host.folder() / "conformance.md").read_text()
    assert "verdict: clean\n" in text
    assert "changes-requested" not in text
    assert events(host)[-2:] == [
        "round 1 · debt — none",
        "round 1 · done — converged in 1 round · 0 cards to debt",
    ]


def test_the_report_names_the_verdicts(
    host: Host, capsys: pytest.CaptureFixture[str]
) -> None:
    _debt(host).write_text(
        f"# Debt\n\n*Deferred.*\n\n## 0000-z\n\n{_filed(_card('R1 nit'), '0000')}"
    )
    host.answers["converge-conformance-r1"] = answer(
        host,
        "conformance",
        _card("R1 blocking"),
        blocking=1,
        inconclusive="[design.md]",
    )
    host.answers["converge-verify-conformance-r2"] = answer(
        host,
        "conformance",
        _card("R1 blocking", status="verified"),
        _card("R2 nit", size=_DESIGN),
        round=2,
        inconclusive="[design.md]",
    )

    design = f"openspec/changes/{_CHANGE}/design.md"
    decided = "# A — design\n\n## Decisions\n\n### D1 · One rule\n\nIt holds.\n"
    _commit(host.tree, {design: decided}, "docs(0001-a): decide D1")

    def noting(host: Host) -> None:
        worded = decided.replace("It holds.", "It holds at the call.")
        note = "Fix note (2026-11-09, R1): the rule holds at the call.\n"
        _commit(
            host.tree,
            {design: worded + note},
            "fix(0001-a): it\n\nPlan-text: R1\nChange: 0001-a",
        )
        (host.folder() / "fix.md").write_text("fixed: R1\nplan check left: none\n")

    host.fixers = [noting]
    workers = {**_WORKERS, "adversarial": "skip"}

    assert run(host, workers) == 0

    assert capsys.readouterr().out.endswith(
        f"Converged in 2 rounds at {_head(host)[:7]}: conformance clean, adversarial"
        " skipped, the loop judged without it.\n"
        "Blocking R1 verified; inconclusive: conformance design.md; fix notes to"
        " read: D1 (R1).\n"
        "To the debt 0001·R2; the debt holds 2 cards; the gate exits 0.\n"
        "Next: /mf-release, in a fresh session.\n"
    )

    host.answers.clear()
    host.fixers.clear()
    host.exits["gate_run.py"] = [0, 3]

    assert run(host, workers) == 1

    assert events(host)[-1] == (
        f"round 1 · halt — the gate is red at the close: gate_run.py exit 3"
        f" · head {_head(host)}"
    )
    assert " · done — " not in "".join(events(host))
    assert "Next: /mf-release" not in capsys.readouterr().out

    host.exits["gate_run.py"] = 2

    assert run(host) == 1

    assert capsys.readouterr().out.endswith(
        "converge: halt — the gate is red before round 1: gate_run.py exit 2\n"
    )


def test_a_halt_on_an_ended_log_is_printed_not_stamped(host: Host) -> None:
    converge = _converge()
    context = converge["Context"](host, _CHANGE, host.tree, _WORKERS, 1e12)
    converge["open_run"](context)
    converge["stamp"](context, "done — converged in 1 round · 0 cards to debt")
    ended = context.log.read_bytes()

    converge["halt"](context, "git failed")

    assert context.log.read_bytes() == ended
    # Twin: a halt on an open run stamps as before.
    converge["open_run"](context)
    converge["halt"](context, "git failed")
    assert events(host)[-1] == f"round 1 · halt — git failed · head {_head(host)}"


class Logged(Protocol):
    """The fields of `converge.py`'s `Context` a status-log test reads."""

    @property
    def folder(self) -> Path: ...

    @property
    def log(self) -> Path: ...


def _bare(converge: dict[str, Any], primary: Path) -> Logged:
    """Return a converge `Context` over `primary`, its change folder made."""
    host = types.SimpleNamespace(primary=primary)
    context = converge["Context"](host, _CHANGE, primary, _WORKERS, 1e12)
    context.folder.mkdir(parents=True)
    return context


def test_case_m_latest_reads_the_newest_run_to_a_blank_line_or_a_heading(
    tmp_path: Path,
) -> None:
    # Why: 0136-status-log design, the pin.
    converge = _converge()
    latest, event = converge["latest"], statuslog.Event
    context = _bare(converge, tmp_path)
    context.log.write_text(
        "# t\n\n## Run 3 — d\n10:00:02 · round 12 · verify — \n"
        "10:00:01 · round 12 · start — base a\n\n10:00:00 · round 1 · halt — old\n"
    )
    assert latest(context) == (
        None,
        [
            event(12, "verify", ""),
            event(12, "start", "base a"),
            event(1, "halt", "old"),
        ],
    )
    context.log.write_text(
        "# t\n\n## Run 3 — d · catch-up\n10:00:01 · round 2 · fix — R1\n"
        "## Run 2 — d\n10:00:00 · round 1 · halt — old\n"
    )
    assert latest(context) == ("catch-up", [event(2, "fix", "R1")])

    context.log.unlink()
    context.log.symlink_to(tmp_path / "gone.md")
    with pytest.raises(statuslog.Refused):
        latest(context)


def test_case_n_halted_is_anchored_at_the_end_and_locked_needs_the_run_folder() -> None:
    # Why: 0136-status-log design, the pin.
    converge = _converge()
    halted, locked = converge["HALTED"], statuslog.names_lock
    assert halted.sub("", "red · head abc123") == "red"
    assert halted.sub("", "red · head abc123 · more") == "red · head abc123 · more"
    assert locked("waited 2 minutes for .minions/debt.lock")
    assert locked("waited 2 minutes for .minions/backlog.lock")
    assert not locked("waited 2 minutes for debt.lock")


def test_case_p_a_refused_stamp_is_cannot_and_runs_are_counted_by_heading(
    tmp_path: Path,
) -> None:
    # Why: 0136-status-log design, the pin.
    converge = _converge()
    context = _bare(converge, tmp_path)
    cannot = f"converge: cannot run — {context.log} cannot be stamped"
    context.log.write_text("# t\n")
    with pytest.raises(converge["Cannot"]) as refused:
        converge["stamp"](context, "start — base a")
    assert str(refused.value) == cannot

    context.log.write_text(
        "# t\n\n## Run 1 — d\n10:00:00 · round 1 · halt — x ## Run 7\n"
    )
    converge["open_run"](context)
    assert context.log.read_text().splitlines()[2].startswith("## Run 2 — ")

    outside = tmp_path / "outside.md"
    outside.write_text("# t\n\n## Run 1 — d\n")
    context.log.unlink()
    context.log.symlink_to(outside)
    with pytest.raises(statuslog.Refused):
        converge["open_run"](context)
    with pytest.raises(converge["Cannot"]) as linked:
        converge["stamp"](context, "start — base a")
    assert str(linked.value) == cannot
    assert outside.read_text() == "# t\n\n## Run 1 — d\n"


def test_a_change_folder_that_is_a_link_cannot_be_stamped(tmp_path: Path) -> None:
    # Why: card 0109·S1; 0136-status-log design D7.
    converge = _converge()
    context = _bare(converge, tmp_path)
    cannot = f"converge: cannot run — {context.log} cannot be stamped"
    outside = tmp_path / "outside"
    outside.mkdir()
    context.folder.rmdir()
    context.folder.symlink_to(outside)
    for act in (converge["open_run"], converge["stamp"]):
        with pytest.raises(converge["Cannot"]) as refused:
            act(context)
        assert str(refused.value) == cannot
    assert list(outside.iterdir()) == []


def test_a_change_folder_is_refused_at_a_link_at_minions(tmp_path: Path) -> None:
    converge = _converge()
    primary, outside = tmp_path / "primary", tmp_path / "outside"
    primary.mkdir()
    outside.mkdir()
    (primary / ".minions").symlink_to(outside)
    context = _bare(converge, primary)
    context.log.write_text("# t\n")
    cannot = f"converge: cannot run — {context.log} cannot be stamped"

    with pytest.raises(converge["Cannot"]) as refused:
        converge["open_run"](context)

    assert str(refused.value) == cannot
    assert (outside / "changes" / _CHANGE / "status_log.md").read_text() == "# t\n"


# The pin: converge's copy of the findings format, as it stands.
# Why: 0138-findings design D2, its cases a, b, c, d, f and g.


def _pin_read(converge: dict[str, Any], path: Path, text: str) -> Read:
    path.write_text(text)
    return converge["read_findings"](path, path.stem)


def _pin_context(converge: dict[str, Any], host: Host, **workers: object) -> Logged:
    host.folder().mkdir(parents=True, exist_ok=True)
    context = converge["Context"](
        host, _CHANGE, host.tree, {**_WORKERS, **workers}, 1e12
    )
    converge["open_run"](context)
    return context


def test_pin_a_card_word_drops_marks_and_folds_case() -> None:
    card = mflib.findings.Card
    for value, word in (
        ("`**Fixed**` — a note", "fixed"),
        ("verified held", "verified"),
        ("open.", "open"),
        ("open,", "open"),
        ("open;", "open"),
        ("open:", "open"),
        ("OPEN", "open"),
        ("", ""),
    ):
        assert card("R1", "conformance", {"Status": value}).word("Status") == word
    assert card("R1", "conformance", {}).word("Status") == ""
    assert card("R1", "conformance", {"Amend": "`Yes`."}).amend


def test_pin_b_converge_reads_each_field_line() -> None:
    body = (
        "- **R1 — a title**\n"
        "  - **Priority**: blocking · conformance · stability — why.\n"
        "  - **Fix:**   a fix · size: one line.   \n"
        "  - **Still true?** `true`\n"
        "\t- **Round:** 1\n"
        "    - **Amend:** no\n"
        "  - **Status:** open\n"
        "  - **Status:** verified\n"
    )

    (card,) = mflib.findings.cards(body, "conformance")

    assert card.fields == {
        "Priority": "blocking · conformance · stability — why.",
        "Fix": "a fix · size: one line.",
        "Still true?": "`true`",
        "Round": "1",
        "Amend": "no",
        "Status": "open",
    }


def test_pin_b_converge_reads_no_title_off_the_form() -> None:
    cards = mflib.findings.cards
    for title in (
        "  - **R1 — nested**",
        "- **R 1 — spaced**",
        "- **R1 – en dash**",
        "- **R1 - hyphen**",
        "- **R1 no dash**",
    ):
        assert cards(f"{title}\n  - **Status:** open\n", "conformance") == [], title


def _pin_extent(between: str) -> dict[str, dict[str, str]]:
    body = (
        "- **R1 — a title**\n  - **Status:** open\n"
        f"{between}  - **Fix:** a fix · size: one line.\n"
    )
    return {card.id: card.fields for card in mflib.findings.cards(body, "conformance")}


def test_pin_extent_converge_an_unindented_line_ends_a_card() -> None:
    assert _pin_extent("a line\n") == {"R1": {"Status": "open"}}


def test_pin_extent_converge_the_next_title_ends_a_card() -> None:
    assert _pin_extent("- **R2 — next**\n") == {
        "R1": {"Status": "open"},
        "R2": {"Fix": "a fix · size: one line."},
    }


def test_pin_extent_converge_a_refuted_heading_ends_a_card() -> None:
    assert _pin_extent("## Refuted\n") == {"R1": {"Status": "open"}}


def test_pin_c_converge_reads_the_frontmatter_block(tmp_path: Path) -> None:
    converge = _converge()
    path = tmp_path / "conformance.md"
    clean = findings("conformance", "h")

    # A block at the start alone, ended by its first `---` line.
    late = _pin_read(converge, path, "\n" + clean)
    assert late.malformed == "conformance.md is malformed: head is missing"
    body = "---\nverdict: changes-requested\n---\n"
    ruled_in_body = _pin_read(converge, path, findings("conformance", "h", body=body))
    assert ruled_in_body.verdict == "clean"
    # Keys and values stripped, a bare key ignored, a value keeping its colons.
    spaced = clean.replace("\nverdict: clean\n", "\n verdict :  clean  \nnotes\n")
    read = _pin_read(converge, path, spaced.replace("head: h\n", "head: a:b\n"))
    assert (read.malformed, read.verdict, read.head) == (None, "clean", "a:b")
    # `mode: skipped` alone is a stub.
    for mode, stub in (("skipped", True), ("Skipped", False), ("skipped-ish", False)):
        keys = {"mode": mode, "files": None, "commits": None, "inconclusive": None}
        read = _pin_read(converge, path, findings("conformance", "h", **keys))
        assert read.stub is stub, mode
        assert read.malformed == (
            None if stub else "conformance.md is malformed: files is missing"
        )


def test_pin_c_converge_names_each_fault(tmp_path: Path) -> None:
    converge = _converge()
    path = tmp_path / "conformance.md"
    headless = findings("conformance", "h").replace("head: h\n", "")
    assert _pin_read(converge, path, headless).malformed == (
        "conformance.md is malformed: head is missing"
    )
    for keys, why in (
        ({"round": "1.0"}, "round is not an integer"),
        ({"open_blocking": None}, "open_blocking is missing"),
        ({"files": "\N{FULLWIDTH DIGIT ONE}"}, "files is not an integer"),
        ({"inconclusive": "none"}, "inconclusive is not a list"),
        ({"verdict": "Clean"}, "verdict is neither clean nor changes-requested"),
        # A key's fault is named before a card's.
        ({"files": None, "body": _card("R1 drift", amend=None)}, "files is missing"),
    ):
        read = _pin_read(converge, path, findings("conformance", "h", **keys))
        assert read.malformed == f"conformance.md is malformed: {why}"


def test_pin_f_a_rewrite_keeps_a_good_files_cards(host: Host) -> None:
    converge = _converge()
    context = _pin_context(converge, host)
    frozen = converge["Freeze"]("b" * 40, _head(host), 1, 1)
    host.answers["converge-conformance-r1"] = answer(
        host, "conformance", _card("R1 blocking"), blocking=1
    )

    read = converge["rewrite"](context, "conformance", frozen, "files is missing")

    assert (read.malformed, [card.id for card in read.cards]) == (None, ["R1"])


def test_pin_f_a_spoiled_card_is_open_for_each_dispatched_role(host: Host) -> None:
    converge = _converge()
    context = _pin_context(converge, host, adversarial="skip")
    for role in ("conformance", "adversarial"):
        host.write(role, findings(role, _head(host), files=None))

    (spoiled,) = converge["spoiled"](context)

    (card,) = mflib.findings.cards(spoiled, "conformance")
    assert spoiled.startswith("- **0001·M1 — conformance's findings file was malformed")
    assert (card.status, card.word("Amend"), card.amend) == ("open", "no", False)


def test_pin_f_ruled_edits_the_frontmatter_and_keeps_the_log(tmp_path: Path) -> None:
    converge = _converge()
    path = tmp_path / "conformance.md"
    path.write_text(
        "---\nhead: a\nround: 1\nreviewed: d\nmode: parallel\nworkers: 1\n---\n\n"
        "round: 7\n## Resolution log\n- d · round 1 · R1 fixed\n"
    )

    converge["ruled"](path, "b" * 40, 2, "2026-11-19", "- a rule.\n")

    assert path.read_text() == (
        f"---\nhead: {'b' * 40}\nround: 2\nreviewed: 2026-11-19\nmode: by-rule\n"
        "workers: 0\n---\n\nround: 7\n## By rule\n\n- a rule.\n\n## Resolution log\n"
        "- d · round 1 · R1 fixed\n2026-11-19 · round 2 · by rule — clean\n"
    )
    target = tmp_path / "target.md"
    target.write_text("---\nhead: a\n---\n")
    linked = tmp_path / "adversarial.md"
    linked.symlink_to(target)
    with pytest.raises(OSError, match="Too many levels of symbolic links"):
        converge["ruled"](linked, "b" * 40, 2, "2026-11-19", "- a rule.\n")
    assert target.read_text() == "---\nhead: a\n---\n"


def test_pin_f_stubs_halt_on_a_link(host: Host, tmp_path: Path) -> None:
    converge = _converge()
    context = _pin_context(converge, host, adversarial="skip")
    target = tmp_path / "target.md"
    target.write_text("kept\n")
    (host.folder() / "adversarial.md").symlink_to(target)

    with pytest.raises(converge["Halt"], match=r"^skip_stub: cannot stub — .* link$"):
        converge["stubs"](context)

    assert target.read_text() == "kept\n"


def test_pin_g_converge_reads_the_fix_size() -> None:
    card = mflib.findings.Card

    def small(fix: str) -> bool:
        return card("R1", "conformance", {"Fix": fix}).small

    for fix in (
        "a fix · size: one line.",
        "a fix · size: `a test`.",
        "a fix · size: one line and a test",
        "a size: big · size: a test.",
    ):
        assert small(fix), fix
    for fix in ("a fix · size: a design change.", "a fix · size: a test. note: x", ""):
        assert not small(fix), fix


def test_pin_g_converge_counts_an_open_blocker() -> None:
    converge = _converge()

    def counted(status: str, grade: str = "blocking") -> bool:
        priority = f"{grade} · conformance · stability — why."
        held = mflib.findings.Card(
            "R1", "conformance", {"Priority": priority, "Status": status}
        )
        read = converge["Verdict"]("conformance", cards=(held,))
        return converge["blockers"]({"conformance": read}) == [held]

    for status in (
        "open",
        "`open` — x",
        "open, then fixed",
        "Open",
        "**open**",
        "opened",
        "fixed — was open",
    ):
        assert counted(status), status
    for status in ("verified — held", "accepted", "`Verified`"):
        assert not counted(status), status
    assert counted("open", "**blocking**")
    assert not counted("open", "nit")


def test_pin_amend_a_held_card_is_skipped_alone(host: Host) -> None:
    converge = _converge()
    context = _pin_context(converge, host)
    host.exits["false"] = 1
    body = _card(
        "R2 nit", amend="yes", status="wontfix", size=_DESIGN, still="`true`"
    ) + _card("R3 nit", amend="yes", status="wontfix", size=_DESIGN, still="`false`")
    cards = mflib.findings.cards(body, "conformance")

    assert converge["amends"](context, cards, {"0001·R2"}) == {"R3": "false"}

    assert [argv for argv in host.ran if argv[0] in ("true", "false")] == [["false"]]


def test_pin_amend_unlocked_halts_naming_the_role(host: Host) -> None:
    converge = _converge()
    context = _pin_context(converge, host)
    run_ = statuslog.Run(None, [statuslog.Event(1, "halt", "debt lock")])
    for role, other in (("adversarial", "conformance"), ("conformance", "adversarial")):
        host.write(other, findings(other, _head(host)))
        host.write(role, findings(role, "a" * 40))
        with pytest.raises(converge["Halt"]) as halted:
            converge["unlocked"](context, run_)
        assert str(halted.value) == (
            f"{role}.md is not clean at HEAD: the debt write cannot go on"
        )


def test_pin_link_converge_read_findings_refuses_a_link(tmp_path: Path) -> None:
    converge = _converge()
    target = tmp_path / "target.md"
    target.write_text(findings("conformance", "h"))
    linked = tmp_path / "conformance.md"
    linked.symlink_to(target)

    read = converge["read_findings"](linked, "conformance")

    assert read.malformed == "conformance.md is malformed: it is a link"


def test_pin_malformed_converge_reads_the_role_clean_at_head(host: Host) -> None:
    converge = _converge()
    context = _pin_context(converge, host)
    frozen = converge["Freeze"]("b" * 40, _head(host), 1, 1)
    host.answers["converge-conformance-r1"] = answer(
        host, "conformance", _card("R1 blocking"), blocking=1, inconclusive=None
    )

    read = converge["rewrite"](
        context, "conformance", frozen, "inconclusive is missing"
    )

    assert read == converge["Verdict"]("conformance", "clean", _head(host), 1)


# The fix: converge's reads on the module's one form.
# Why: 0138-findings design D4, D6, D7 and D8.


def test_fix_extent_converge_a_blank_line_does_not_end_a_card() -> None:
    assert _pin_extent("\n") == {
        "R1": {"Status": "open", "Fix": "a fix · size: one line."}
    }


def test_fix_security_converge_fails_closed_on_an_unread_category() -> None:
    card = mflib.findings.Card

    def security(role: str, priority: str) -> bool:
        return card("S1", role, {"Priority": priority}).security

    assert security("adversarial", "high · adversarial · security — why.")
    assert security("adversarial", "high · adversarial · Security — why.")
    assert security("adversarial", "high · adversarial")
    assert not security("adversarial", "high · adversarial · stability — why.")
    assert not security("conformance", "blocking · conformance · security — why.")


def test_fix_ids_converge_reads_a_card_off_the_ids_as_malformed(
    tmp_path: Path,
) -> None:
    converge = _converge()
    path = tmp_path / "adversarial.md"
    for title, why in (
        ("A6 blocking", "card A6 is not R<n> or S<n>"),
        ("S-1 blocking", "card S-1 is not R<n> or S<n>"),
    ):
        read = _pin_read(
            converge, path, findings("adversarial", "h", body=_card(title))
        )
        assert read.malformed == f"adversarial.md is malformed: {why}", title
    stray = "## Findings\n\n  - **Status:** open\n"
    read = _pin_read(converge, path, findings("adversarial", "h", body=stray))
    assert (
        read.malformed == "adversarial.md is malformed: a Status under no card: unnamed"
    )
    # Twin: the same card titled on the contract's ids is read.
    read = _pin_read(
        converge, path, findings("adversarial", "h", body=_card("S1 blocking"))
    )
    assert (read.malformed, [card.id for card in read.cards]) == (None, ["S1"])


def test_fix_frontmatter_converge_ruled_edits_the_block_alone(tmp_path: Path) -> None:
    converge = _converge()
    path = tmp_path / "conformance.md"
    path.write_text("---\n head : a\nmode: parallel\n---\n\nround: 7\nworkers: 3\n")

    converge["ruled"](path, "b" * 40, 2, "2026-11-19", "- a rule.\n")

    assert path.read_text() == (
        f"---\nhead: {'b' * 40}\nmode: by-rule\n---\n\nround: 7\nworkers: 3\n"
        "## By rule\n\n- a rule.\n2026-11-19 · round 2 · by rule — clean\n"
    )


# The pin: converge's copy of the debt file's rules, as it stands.
# Why: 0139-debt design D1.

_PREAMBLE = (
    "# Debt\n\n*Deferred work from converge, one heading per change; a paydown change"
    " lists the ids it closes under `debt:`.*"
)
_OLD_BACKLOG = (
    ".minions/debt.lock not taken — an old .minions/backlog.md stands;"
    " /mf-ship moves it at a run's start"
)


def test_debt_pin_still_true(host: Host) -> None:
    converge = _converge()
    context = _pin_context(converge, host)
    host.exits.update({"true": 1, "ls": 2})
    still = converge["still_true"]

    assert still(context, "  `true`  ") == (1, "true")
    assert still(context, "`ls src` then `true`") == (2, "ls src")
    assert still(context, "`true -x 'a b'`") == (1, "true -x 'a b'")
    assert still(context, "read `true` and its caller") == (None, "")
    assert still(context, "`'unbalanced`") == (None, "'unbalanced")
    assert still(context, "` `") == (None, " ")
    assert [argv for argv in host.ran if argv[0] in ("true", "ls")] == [
        ["true"],
        ["ls", "src"],
        ["true", "-x", "a b"],
    ]


def test_debt_pin_lock(host: Host, monkeypatch: pytest.MonkeyPatch) -> None:
    converge = _converge()
    lock, primary = _debt(host).with_name("debt.lock"), host.primary
    with converge["debt_lock"](primary):
        assert lock.is_dir()
    assert not lock.exists()
    with pytest.raises(ValueError, match="the body"), converge["debt_lock"](primary):
        raise ValueError("the body")
    assert not lock.exists()

    naps: list[float] = []
    monkeypatch.setattr(time, "sleep", naps.append)
    lock.mkdir()
    with pytest.raises(converge["Halt"]) as held, converge["debt_lock"](primary):
        pass
    assert str(held.value) == ".minions/debt.lock held for 10 minutes"
    poll, wait = debtfile.LOCK_POLL, converge["LOCK_WAIT"]
    assert naps == [poll] * (wait // poll)
    assert lock.is_dir()
    lock.rmdir()

    old = lock.with_name("backlog.md")
    old.symlink_to(lock.with_name("gone.md"))
    with pytest.raises(converge["Halt"]) as dangling, converge["debt_lock"](primary):
        pass
    assert str(dangling.value) == _OLD_BACKLOG
    assert not lock.exists()
    old.unlink()

    # The release leaves another holder's lock, and a lock gone is no error.
    with converge["debt_lock"](primary) as held:
        assert held.holds()
        (lock / "owner").unlink()
        lock.rmdir()
        lock.mkdir()
    assert lock.is_dir()
    lock.rmdir()
    with converge["debt_lock"](primary):
        (lock / "owner").unlink()
        lock.rmdir()
    assert not lock.exists()


def test_debt_pin_read(tmp_path: Path) -> None:
    converge = _converge()
    read, halt = converge["_debt_text"], converge["Halt"]
    debt = tmp_path / "debt.md"
    assert read(debt) == ""
    debt.write_bytes(b"# Debt\n\xff\n")
    assert read(debt) == "# Debt\n�\n"
    debt.unlink()
    target = tmp_path / "target.md"
    target.write_text("# Debt\n")
    debt.symlink_to(target)
    with pytest.raises(halt) as linked:
        read(debt)
    assert str(linked.value) == ".minions/debt.md cannot be read: it is a link"
    debt.unlink()
    debt.mkdir()
    with pytest.raises(halt) as folder:
        read(debt)
    # why: Linux opens a folder and the read names its kind; macOS refuses the open
    assert str(folder.value) in {
        ".minions/debt.md cannot be read: it is not a file",
        ".minions/debt.md cannot be read: Is a directory",
    }
    debt.rmdir()

    os.mkfifo(debt)
    said: list[str] = []

    def piped() -> None:
        try:
            read(debt)
        except halt as halted:
            said.append(str(halted))

    reader = threading.Thread(target=piped)
    reader.start()
    reader.join(10)
    assert not reader.is_alive()
    assert said == [".minions/debt.md cannot be read: it is not a file"]

    text = (
        "- **0001·R1 — a**\n- **R2 — b**\n  - **0001·R3 — c**\n"
        "-  **0001·R4 — d**\n- **0001·R5 —e**\n"
    )
    assert debtfile.TITLE.findall(text) == ["0001·R1"]


def test_debt_pin_filed() -> None:
    filed, unfiled = debtfile.filed, debtfile.unfiled
    card = "- **0001·R2 — new**\n  - **Status:** open\n"
    old = "- **0001·R1 — old**\n  - **Status:** open\n"
    assert filed("# Debt\n", _CHANGE, []) == "# Debt\n"
    assert filed("# Debt\n\n", _CHANGE, [card]) == f"# Debt\n\n## 0001-a\n\n{card}"
    # A heading with trailing blanks is found, and no second one is written.
    blank = f"# Debt\n\n## 0001-a  \n\n{old}"
    assert filed(blank, _CHANGE, [card]) == f"{blank}{card}"
    # A `### ` line or a `#` line is inside; the cards go after the last non-blank.
    inner = f"# Debt\n\n## 0001-a\n\n{old}### a note\n#no heading\n"
    other = "## 0000-z\n\n- **0000·R1 — z**\n"
    assert filed(f"{inner}\n\n{other}", _CHANGE, [card]) == (
        f"{inner}{card}\n\n{other}"
    )
    assert filed(f"{inner}{other}", _CHANGE, [card]) == f"{inner}{card}\n{other}"
    assert filed(inner, _CHANGE, [card]) == f"{inner}{card}"

    # A blank line inside the card does not end it; the id is matched whole.
    kept = "- **0001·R10 — kept**\n  - **Status:** open\n"
    paid = "- **0001·R1 — paid**\n  - **Fix:** x\n\n  - **Status:** open\n"
    debt = f"# Debt\n\n## 0001-a\n\n{paid}{kept}\n{other}"
    left = f"# Debt\n\n## 0001-a\n\n{kept}\n{other}"
    assert unfiled(debt, "0001·R1") == left
    assert unfiled(left, "0001·R10") == f"# Debt\n\n{other}"
    with pytest.raises(StopIteration):
        unfiled(debt, "0001·R9")


def test_debt_pin_write(host: Host, monkeypatch: pytest.MonkeyPatch) -> None:
    converge = _converge()
    context = _pin_context(converge, host)
    # The lock is renewed after each Still true? command it holds.
    renewed: list[Path] = []
    monkeypatch.setattr(
        debtfile.Holder, "renew", lambda held: renewed.append(held.path)
    )
    head = _head(host)
    filed = _card("R1 nit", size=_DESIGN)
    body = (
        filed
        + _card("R2 blocking", status="fixed")
        + _card("R3 nit", size=_DESIGN, status="verified")
    )
    host.write("conformance", findings("conformance", head, body=body))
    host.write("adversarial", findings("adversarial", head, files=None))
    debt = _debt(host)
    where = f".minions/changes/{_CHANGE}/adversarial.md"
    spoilt = (
        "- **0001·M1 — adversarial's findings file was malformed after a rewrite**\n"
        "  - **Why it's a problem:** converge read the role as clean at HEAD with"
        " no card, so a finding in the file went unjudged.\n"
        "  - **When you'd hit it:** the release reads the file's own verdict.\n"
        f"  - **What it affects:** `{where}`.\n"
        "  - **Evidence:** adversarial.md is malformed: files is missing · read.\n"
        "  - **Verdict:** confirmed.\n"
        "  - **Priority:** medium · conformance · maintainability — the role's"
        " verdict this run is the script's, not its checker's.\n"
        "  - **Round:** 1\n"
        "  - **Fix:** rewrite the file to the findings file contract, then converge"
        " again · size: a design change.\n"
        "  - **Amend:** no\n"
        f"  - **Trigger:** the release of {_CHANGE}.\n"
        f"  - **Still true?** read `{where}` against the contract.\n"
        "  - **Related:** none.\n"
        "  - **Status:** open\n"
    )

    assert converge["debt"](context) == (["0001·R1", "0001·M1"], [], [], 2, {})

    text = f"{_PREAMBLE}\n\n## 0001-a\n\n{_filed(filed)}{spoilt}"
    assert debt.read_text() == text

    assert converge["debt"](context) == ([], [], [], 2, {})

    assert debt.read_text() == text

    host.exits.update({"true": 1, "false": 0, "ls": 2})
    old = {
        n: _filed(_card(f"R{n} nit", still=f"`{command}`"), "0000")
        for n, command in ((1, "true"), (2, "false"), (3, "ls"))
    }
    # The total counts a qualified title alone.
    bare = _card("R9 nit")
    debt.write_text(f"{text}\n## 0000-z\n\n{''.join(old.values())}{bare}")
    repeats = "".join(
        _card(f"R{n + 3} nit", status="verified", related=f"repeat of `0000·R{n}`.")
        for n in old
    )
    host.write("conformance", findings("conformance", head, body=filed + repeats))

    assert converge["debt"](context) == ([], [], ["0000·R1"], 4, {"0000·R1": "true"})

    assert debt.read_text() == f"{text}\n## 0000-z\n\n{old[2]}{old[3]}{bare}"
    assert renewed == [debt.with_name("debt.lock")] * 4


def test_debt_pin_debted(host: Host) -> None:
    converge = _converge()
    context = _pin_context(converge, host)
    _debt(host).write_text(
        "# Debt\n\n## 0001-a\n\n- **0001·R1 — a**\n- **R2 — b**\n  - **0001·R3 — c**\n"
    )
    converge["stamp"](
        context, "debt — written 0001·R1, 0001·R2 · moot R3 · cleared 0000·R1"
    )

    assert converge["debted"](context) == (
        ["0001·R1", "0001·R2"],
        ["R3"],
        ["0000·R1"],
        1,
        {},
    )

    converge["stamp"](context, "debt — none")

    assert converge["debted"](context) == ([], [], [], 1, {})

    locked = statuslog.names_lock
    assert locked("halt — .minions/debt.lock held for 10 minutes")
    assert locked("halt — .minions/backlog.lock is held")
    assert not locked("halt — .minions/queue.lock is held")


def test_debt_pin_empty_page(host: Host) -> None:
    converge = _converge()
    debt = _debt(host)
    debt.symlink_to(debt.with_name("gone.md"))
    base = _git(host.tree, "merge-base", "main", "HEAD")
    context = converge["Context"](host, _CHANGE, host.tree, _WORKERS, 1e12)
    converge["open_run"](context)

    with pytest.raises(converge["Halt"]) as halted:
        converge["freeze"](context, base, _head(host))

    assert str(halted.value) == ("debt_match.py exited 2 — the debt cannot be matched")
    assert not (host.folder() / "debt-cards.md").exists()
    assert not any(" · freeze — " in event for event in events(host))


def test_debt_pin_backlog_no_file(host: Host) -> None:
    converge = _converge()
    old = _debt(host).with_name("backlog.md")
    old.symlink_to(old.with_name("gone.md"))
    with (
        pytest.raises(converge["Halt"]) as dangling,
        converge["debt_lock"](host.primary),
    ):
        pass
    assert str(dangling.value) == _OLD_BACKLOG
    old.unlink()
    old.write_text("# Backlog\n")
    with (
        pytest.raises(converge["Halt"]) as regular,
        converge["debt_lock"](host.primary),
    ):
        pass
    assert str(regular.value) == _OLD_BACKLOG
    assert not old.with_name("debt.lock").exists()


def test_debt_pin_folder(host: Host) -> None:
    converge = _converge()
    context = _pin_context(converge, host)
    head = _head(host)
    body = _card("R1 nit", size=_DESIGN)
    host.write("conformance", findings("conformance", head, body=body))
    host.write("adversarial", findings("adversarial", head))
    minions = _debt(host).parent
    elsewhere = minions.with_name("elsewhere")
    minions.rename(elsewhere)
    minions.symlink_to(elsewhere)

    with pytest.raises(converge["Halt"]) as refused:
        converge["debt"](context)

    assert str(refused.value).startswith(
        f".minions/debt.md cannot be written — {minions}: "
    )
    assert not (elsewhere / "debt.md").exists()
    assert not (elsewhere / "debt.lock").exists()

    # Twin: the same debt in a real folder is written.
    minions.unlink()
    elsewhere.rename(minions)

    assert converge["debt"](context).written == ["0001·R1"]

    assert _filed(body) in (minions / "debt.md").read_text()
