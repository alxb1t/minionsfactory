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
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, NamedTuple, Protocol, TextIO

import pytest

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
    fallback: bool
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

    debt.unlink()
    debt.mkdir()
    converge["freeze"](context, base, head)

    assert (folder / "debt-cards.md").read_text() == (
        "# Debt cards on the diff's files\n\nNone.\n"
    )

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
    frozen = converge["Freeze"]("b" * 40, head, 2, 3)
    folder = host.folder()
    folder.mkdir(parents=True)

    def read(role: str, **keys: object) -> Read:
        (folder / f"{role}.md").write_text(findings(role, head, **keys))
        return converge["read_findings"](folder / f"{role}.md", role, frozen)

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
        ({"files": 2, "commits": 2}, "scope resolved 2 files and 2 commits"),
        ({"files": 3, "commits": 1}, "scope resolved 3 files and 1 commit"),
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
    assert converge["read_findings"](folder / "gone.md", "conformance", frozen) is None
    (folder / "linked.md").symlink_to(folder / "conformance.md")
    linked = converge["read_findings"](folder / "linked.md", "conformance", frozen)
    assert linked.malformed == "linked.md is malformed: it is a link"
    os.mkfifo(folder / "piped.md")
    piped = converge["read_findings"](folder / "piped.md", "conformance", frozen)
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

    read = converge["read_verdicts"](context, frozen, checked)

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
    narrow.write_text(findings("conformance", head, files=0, commits=0))
    small = converge["read_findings"](narrow, "conformance", frozen)
    with pytest.raises(halt, match="scope resolved 0 files"):
        converge["held"](context, read | {"conformance": small}, frozen)


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
        assert f"`head: {head}` and `mode: parallel`" in text
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
        ("no card", "changes requested with no blocking card open"),
        ("status", "open cards: cannot read — card R1: Status maybe"),
    ):
        card = _card("R1 blocking", status="maybe" if case == "status" else "open")
        host.answers["converge-conformance-r1"] = (
            answer(host, "conformance", verdict="changes-requested")
            if case == "no card"
            else answer(host, "conformance", card, blocking=1)
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


def test_a_catch_up_runs_the_changed_verifies_in_one_plan_check(host: Host) -> None:
    assert run(host) == 0
    tasks = (
        _TASKS
        + "\n- [x] 1.1 One.\n  Verify: `git grep -n nope` prints a line.\n"
        + "- [x] 1.2 Two.\n  Verify: `true`.\n"
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
        "round 1 · halt — .minions/debt.md cannot be read: it is a link"
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
    gone = _filed(_card("R1 nit", still="`true`"), "0000")
    kept = _filed(_card("R2 nit", still="`false`"), "0000")
    debt = _debt(host)
    debt.write_text(
        f"# Debt\n\n*Deferred.*\n\n## 0000-y\n\n{gone}\n## 0000-z\n\n{kept}"
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

    assert debt.read_text() == f"# Debt\n\n*Deferred.*\n\n## 0000-z\n\n{kept}"
    assert events(host)[-2] == "round 1 · debt — cleared 0000·R1"
    assert "; cleared 0000·R1 (`true` exited 1); " in capsys.readouterr().out


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

    limit = "codex usage limit — the fixer · resets 5:50 PM"
    host.fixes = [Checked(1, False, codex, limit, False, None)]

    assert run(host, workers) == 1

    assert len(host.codexed) == 2
    assert events(host)[-1] == f"round 1 · halt — {limit} · head {_head(host)}"

    host.fixes = [Checked(1, False, codex, "", False, None)]

    assert run(host, workers) == 0

    assert len(host.codexed) == 4
    assert host.fixed == []


def test_a_codex_fixers_prompt_names_its_attribution(host: Host) -> None:
    codex = ("codex", "gpt-6.1-sol", "medium")
    host.answers["converge-conformance-r1"] = answer(
        host, "conformance", _card("R1 blocking"), blocking=1
    )

    assert run(host, {**_WORKERS, "fix": codex}) == 0

    assert (
        "Co-Authored-By: Codex gpt-6.1-sol <noreply@openai.com>" in host.codexed[0][2]
    )
    assert host.fixed == []

    assert run(host, _WORKERS) == 0

    assert "the attribution line your session names" in host.fixed[0][2]
    assert len(host.codexed) == 1


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
    broken = answer(host, "conformance", files=None)
    host.answers["converge-conformance-r1"] = _twice(
        broken, answer(host, "conformance")
    )

    assert run(host) == 0

    why = "conformance.md is malformed: files is missing"
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
        host, "conformance", _card("R1 blocking"), blocking=1, files=None
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

    def noting(host: Host) -> None:
        design = "# A — design\n\n### D1 · One rule\n\nIt holds.\n"
        note = "Fix note (2026-11-09, R1): the rule holds at the call.\n"
        _commit(
            host.tree,
            {f"openspec/changes/{_CHANGE}/design.md": design + note},
            "fix(0001-a): it",
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
