"""The plan check: a change's plan held to the tree built from it.

A repository under `tmp_path`, the check run in-process from inside it.
Why: 0103-fewer-rounds design D4.
"""

import importlib.util
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from types import ModuleType

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-converge" / "scripts" / "plan_check.py"
_CHANGE = "0002-x"
_FOLDER = f"openspec/changes/{_CHANGE}"
_SPEC = "openspec/specs/cap/spec.md"
_MOD = (
    "def _gone() -> None:\n    pass\n\n\ndef _kept() -> None:\n    pass\n\n\n"
    "class Old:\n    pass\n\n\nLIMIT = 1\nOTHER: int = 2\n"
)
_TESTS = (
    "def test_gone() -> None:\n    pass\n\n\nasync def test_async() -> None:\n"
    "    pass\n\n\nclass T:\n    def test_nested(self) -> None:\n        pass\n"
)
_DESIGN = "# D\n\n## Context\n\nNone.\n"
_ONE = "- [x] 1 — One\n"
_GONE = "plan: openspec/specs/cap/spec.md:1 names {}, which the diff removes"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("plan_check", _SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


plan_check = _load()


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=mf", "-c", "user.email=mf@example.invalid"]
        + ["-c", "commit.gpgsign=false", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _commit(root: Path, files: dict[str, str], message: str) -> None:
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text)
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", message)


def _repo(root: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """Commit a base, then a cut, in `root`; enter it and return the base."""
    root.mkdir()
    _git(root, "init", "-q")
    base = {
        ".gitignore": ".minions/\n",
        "src/mod.py": _MOD,
        "src/legacy.py": "LEGACY = 1\n",
        "tests/test_mod.py": _TESTS,
    }
    _commit(root, base, "base")
    first = _git(root, "rev-parse", "HEAD")
    cut = {f"{_FOLDER}/tasks.md": _ONE, f"{_FOLDER}/design.md": _DESIGN}
    _commit(root, cut, "cut")
    monkeypatch.chdir(root)
    return first


def _tasks(root: Path, progress: str, *tasks: str) -> None:
    text = f"## Progress\n\n{progress}\n## 1 — One\n\n{''.join(tasks)}"
    (root / _FOLDER / "tasks.md").write_text(text)


def test_a_plan_check_finds_what_the_plan_left(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "repo"
    base = _repo(root, monkeypatch)

    def check() -> tuple[int, list[str]]:
        code = plan_check.main(["--change", _CHANGE, "--base", base])
        return code, capsys.readouterr().out.splitlines()

    # A ticked `Verify:` that exits non-zero names itself and what it printed.
    refs = "git rev-parse --verify nonesuch"
    _tasks(root, _ONE, f"- [x] 1.1 Fails.\n  Verify: `{refs}`.\n")
    assert check() == (
        1,
        [
            f"plan: 1.1 — `{refs}` exited 128",
            "  | fatal: Needed a single revision",
        ],
    )
    # Its output is cut to the first lines.
    seq = 'sh -c "seq 1 9; exit 1"'
    _tasks(root, _ONE, f"- [x] 1.1 Noisy.\n  Verify: `{seq}`.\n")
    assert check() == (
        1,
        [f"plan: 1.1 — `{seq}` exited 1", *(f"  | {n}" for n in range(1, 6))],
    )

    # A search that finds nothing passes when its `Verify:` says it prints nothing.
    search = "git grep -n -e zzz -- src"
    _tasks(
        root,
        _ONE,
        f"- [x] 1.1 Absent.\n  Verify: `{search}` prints nothing.\n",
        f"- [x] 1.2 Counted.\n  Verify: `{search}` prints `0`.\n",
    )
    assert check() == (0, ["plan: clean"])
    _tasks(root, _ONE, f"- [x] 1.1 Absent.\n  Verify: `{search}` prints a line.\n")
    assert check() == (1, [f"plan: 1.1 — `{search}` exited 1"])

    # A command that exits 0 must print what its `Verify:` says: a `prints nothing`
    # search that finds a match fails, showing the match.
    found = "git grep -n -e Old -- src"
    other = "printed other than its Verify: says"
    _tasks(root, _ONE, f"- [x] 1.1 Present.\n  Verify: `{found}` prints nothing.\n")
    assert check() == (
        1,
        [f"plan: 1.1 — `{found}` {other}", "  | src/mod.py:9:class Old:"],
    )
    # Blank lines are output: a `prints nothing` search that finds them fails.
    blank = "grep ^$ src/mod.py"
    _tasks(root, _ONE, f"- [x] 1.1 Blank.\n  Verify: `{blank}` prints nothing.\n")
    assert check() == (1, [f"plan: 1.1 — `{blank}` {other}", *["  | "] * 5])
    # A count a `Verify:` names is the whole output: `printf 1` is not `2`, is `1`.
    _tasks(root, _ONE, "- [x] 1.1 Wrong.\n  Verify: `printf 1` prints `2`.\n")
    assert check() == (1, [f"plan: 1.1 — `printf 1` {other}", "  | 1"])
    _tasks(
        root,
        _ONE,
        "- [x] 1.1 Right.\n  Verify: `printf 1` prints `1`.\n",
        "- [x] 1.2 Reported.\n"
        "  Verify: `printf 1` prints `1`, then `printf 2` reports `1`.\n",
    )
    assert check() == (1, [f"plan: 1.2 — `printf 2` {other}", "  | 2"])
    # A `grep -c` that finds nothing exits 1 printing `0`, which `prints `0`` passes.
    counted = "grep -c zzz src/mod.py"
    _tasks(root, _ONE, f"- [x] 1.1 Zero.\n  Verify: `{counted}` prints `0`.\n")
    assert check() == (0, ["plan: clean"])
    _tasks(root, _ONE, f"- [x] 1.1 One.\n  Verify: `{counted}` prints `1`.\n")
    assert check() == (1, [f"plan: 1.1 — `{counted}` exited 1", "  | 0"])
    # Each command is held to the words after its own span.
    _tasks(
        root,
        _ONE,
        "- [x] 1.1 Both.\n"
        f"  Verify: `{search}` prints nothing, then `printf 1` prints `1`.\n",
        "- [x] 1.2 Order.\n"
        f"  Verify: `{found}` prints nothing, then `printf 1` prints `1`.\n",
    )
    assert check() == (
        1,
        [f"plan: 1.2 — `{found}` {other}", "  | src/mod.py:9:class Old:"],
    )

    # A HALT CHECK, a HUMAN phase's sub-task and a command naming `plan_check.py` are
    # not run.
    _tasks(
        root,
        f"{_ONE}- [x] 2 — Two **HUMAN**\n",
        "- [x] 1.1 **HALT CHECK** Confirm it.\n  Verify: `false`.\n",
        "- [x] 1.2 Run the guard.\n"
        "  Verify: `false plan_check.py` prints `plan: clean`.\n"
        "\n## 2 — Two\n\n- [x] 2.1 A person did it.\n  Verify: `false`.\n",
    )
    assert check() == (0, ["plan: clean"])

    # A span of double backticks, padded, holds the command inside.
    _tasks(root, _ONE, "- [x] 1.1 Padded.\n  Verify: `` true ``.\n")
    assert check() == (0, ["plan: clean"])

    # A command past the timeout, and one that cannot start, fail.
    monkeypatch.setattr(plan_check, "TIMEOUT_SECONDS", 0.5)
    _tasks(
        root,
        _ONE,
        "- [x] 1.1 Slow.\n  Verify: `sleep 5`.\n",
        "- [x] 1.2 Missing.\n  Verify: `nonesuch-program`.\n",
    )
    assert check() == (
        1,
        [
            "plan: 1.1 — `sleep 5` timed out",
            "plan: 1.2 — `nonesuch-program` exited 127",
            "  | No such file or directory",
        ],
    )

    # A box left unticked under a ticked phase; an unticked phase's are fine.
    _tasks(
        root,
        f"{_ONE}- [ ] 2 — Two\n",
        "- [x] 1.1 Done.\n  Verify: `true`.\n",
        "- [ ] 1.2 Left.\n  Verify: `false`.\n\n## 2 — Two\n\n- [ ] 2.1 Later.\n",
    )
    assert check() == (1, ["plan: 1.2 — unticked under the ticked phase 1"])

    # The build removes a function, a class, two constants and a file.
    (root / "src/mod.py").write_text("def _kept(x: int) -> None:\n    pass\n")
    (root / "src/legacy.py").unlink()
    spec = root / _SPEC
    spec.parent.mkdir(parents=True)
    spec.write_text("The `_gone` helper reads it.\nThe `_kept` helper reads it.\n")
    _tasks(root, _ONE, "- [x] 1.1 Read.\n  Verify: `true`.\n")
    assert check() == (1, [_GONE.format("_gone")])

    # A line saying it is removed names it without harm.
    spec.write_text(
        "The `_gone` helper is removed.\n`Old` → `New`\n"
        "**Reason**: `LIMIT` is not read.\n"
        "**Migration**: `OTHER` and `LEGACY` go; `legacy.py` too.\n"
    )
    assert check() == (0, ["plan: clean"])

    # Each removed name names itself, in the order the diff removes them.
    spec.write_text("`Old` `LIMIT` `OTHER` `LEGACY` `legacy.py` `_gone`\n")
    names = ["LEGACY", "_gone", "Old", "LIMIT", "OTHER", "legacy.py"]
    assert check() == (1, [_GONE.format(name) for name in names])

    # A line in a living requirement the delta removes names it without harm; the
    # same name in the next requirement, which the delta keeps, does not.
    spec.write_text(
        "## Requirements\n\n### Requirement: Capped reads\n\nIt holds `LIMIT`.\n\n"
        "### Requirement: Kept reads\n\nIt holds `LIMIT` too.\n"
    )
    held = f"plan: {_SPEC}:{{}} names LIMIT, which the diff removes"
    assert check() == (1, [held.format(5), held.format(9)])
    delta = root / _FOLDER / "specs/cap/spec.md"
    delta.parent.mkdir(parents=True)
    delta.write_text(
        "## MODIFIED Requirements\n\n### Requirement: Kept reads\n\nIt reads.\n\n"
        "## REMOVED Requirements\n\n### Requirement: Capped reads\n\n"
        "**Reason**: unread.\n"
    )
    assert check() == (1, [held.format(9)])
    delta.unlink()
    spec.write_text("The `_gone` helper is removed.\n")

    # The tasks never name a removed name to the plan's harm.
    _tasks(root, _ONE, "- [x] 1.1 Read `_gone`.\n  Verify: `true`.\n")
    assert check() == (0, ["plan: clean"])

    # The design's `## Tests` section may; the rest of it may not.
    design = root / _FOLDER / "design.md"
    outside = "# D\n\n## Context\n\nSee `_gone`.\n\n## Tests\n\nThe `_gone` helper.\n"
    design.write_text(f"{outside}\n## Risks\n\nNone.\n")
    assert check() == (
        1,
        [f"plan: {_FOLDER}/design.md:5 names _gone, which the diff removes"],
    )
    design.write_text(outside.replace("See `_gone`.", "None."))
    assert check() == (0, ["plan: clean"])

    # A test of the base gone from the tree, indented or async or not, is named,
    # unless the design's `## Tests` section names it as a word.
    spec.write_text("None.\n")
    (root / "tests/test_mod.py").write_text("# none\n")
    design.write_text(_DESIGN)
    assert check() == (
        1,
        [
            "plan: test_async is gone since the base",
            "plan: test_gone is gone since the base",
            "plan: test_nested is gone since the base",
        ],
    )
    planned = "`test_async` and `test_gone` go; `test_nested_more` is new."
    design.write_text(f"{_DESIGN}\n## Tests\n\n{planned}\n")
    assert check() == (1, ["plan: test_nested is gone since the base"])
    design.write_text(
        f"{_DESIGN}\n## Tests\n\n`test_async`, `test_gone` and `test_nested` go.\n"
    )
    assert check() == (0, ["plan: clean"])

    # A sub-task marked `**CORPUS**`, ticked or not, needs its case in the corpus.
    marked = "- [x] 1.1 Read run data. **CORPUS** `open-cards`\n  Verify: `true`.\n"
    _tasks(root, _ONE, marked)
    assert check() == (
        1,
        ["plan: 1.1 — no case open-cards in scripts/corpus.toml"],
    )
    (root / "scripts").mkdir()
    (root / "scripts/corpus.toml").write_text('[[case]]\nname = "open-cards"\n')
    assert check() == (0, ["plan: clean"])
    _tasks(
        root,
        f"{_ONE}- [ ] 2 — Two\n",
        marked,
        "\n## 2 — Two\n\n- [ ] 2.1 Read more. **CORPUS** `ghost`\n",
    )
    assert check() == (1, ["plan: 2.1 — no case ghost in scripts/corpus.toml"])


def _commit_tasks(root: Path, *tasks: str) -> None:
    """Write `tasks.md` and commit it, so the tree is settled."""
    _tasks(root, _ONE, *tasks)
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "tasks")


def test_a_command_named_twice_runs_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "repo"
    base = _repo(root, monkeypatch)
    ran = root / "ran.txt"
    command = 'sh -c "echo r >> ran.txt; printf 1"'
    _tasks(
        root,
        _ONE,
        f"- [x] 1.1 First.\n  Verify: `{command}` prints `1`.\n",
        f"- [x] 1.2 Second.\n  Verify: `{command}` prints `2`.\n",
        f"- [x] 1.3 Third.\n  Verify: `{command}`.\n",
    )
    code = plan_check.main(["--change", _CHANGE, "--base", base])
    other = "printed other than its Verify: says"
    assert (code, capsys.readouterr().out.splitlines()) == (
        1,
        [f"plan: 1.2 — `{command}` {other}", "  | 1"],
    )
    assert ran.read_text() == "r\n"


def test_a_green_gate_record_passes_a_bare_pytest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "repo"
    base = _repo(root, monkeypatch)
    stub = tmp_path / "bin"
    stub.mkdir()
    (stub / "pytest").write_text("#!/bin/sh\nexit 3\n")
    (stub / "pytest").chmod(0o755)
    monkeypatch.setenv("PATH", f"{stub}{os.pathsep}{os.environ['PATH']}")

    def check() -> tuple[int, list[str]]:
        code = plan_check.main(["--change", _CHANGE, "--base", base])
        return code, capsys.readouterr().out.splitlines()

    def record(dry: str | None = None) -> None:
        loaded = plan_check.gate()
        tree = loaded["settled_tree"]()
        dry = dry or loaded["dry_run"]()
        loaded["write_record"](loaded["records"]() / tree, dry, 1)

    bare = "- [x] 1.1 Suite.\n  Verify: `pytest -q`.\n"
    ran = ["plan: 1.1 — `pytest -q` exited 3"]
    # No `make gate` target to dry-run: no record can stand, and the pytest runs.
    _commit_tasks(root, bare)
    assert check() == (1, ran)
    # A green record for the tree and the dry run passes it unrun.
    _commit(root, {"Makefile": "gate:\n\t@true\n"}, "gate")
    record()
    assert check() == (0, ["plan: clean"])
    # A `Verify:` that names an output is no bare pytest: it runs.
    _commit_tasks(root, "- [x] 1.1 Suite.\n  Verify: `pytest -q` prints `1`.\n")
    record()
    assert check() == (1, ["plan: 1.1 — `pytest -q` exited 3"])
    # A record of another dry run stands for another gate: the pytest runs.
    _commit_tasks(root, bare)
    record("0" * 64)
    assert check() == (1, ran)
    # An unsettled tree has no record: the pytest runs.
    record()
    (root / "stray.txt").write_text("x\n")
    assert check() == (1, ran)


def test_a_command_naming_a_revision_is_keyed_by_head() -> None:
    for text in (
        "git rev-parse --verify HEAD",
        "git log -1",
        "git diff HEAD~1 --stat",
        "printf deadbeef",
        "git",
    ):
        assert plan_check.keyed(text, "abc") == f"{text}\nabc"
    for text in (
        "git grep -n x -- src",
        "git ls-files src",
        "printf 1",
        "ruff check .",
    ):
        assert plan_check.keyed(text, "abc") == text


def test_a_result_is_kept_by_tree_and_reused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "repo"
    base = _repo(root, monkeypatch)
    ran = tmp_path / "ran.txt"
    counted = f'sh -c "echo r >> {ran}; printf 1"'
    bare = "git rev-parse --verify HEAD"
    tasks = (
        f"- [x] 1.1 Counted.\n  Verify: `{counted}` prints `1`.\n",
        f"- [x] 1.2 Bare.\n  Verify: `{bare}`.\n",
    )
    _commit_tasks(root, *tasks)
    kept = root / ".minions" / "plan-check"

    def check() -> tuple[int, list[str], int]:
        code = plan_check.main(["--change", _CHANGE, "--base", base])
        out = capsys.readouterr().out.splitlines()
        return code, out, len(list(kept.glob("*/*")))

    def runs() -> int:
        return len(ran.read_text().splitlines())

    # A settled tree keeps a result for each command, and reads it again.
    assert check() == (0, ["plan: clean"], 2)
    assert (check(), runs()) == ((0, ["plan: clean"], 2), 1)
    # A new commit on the same tree runs the command naming `HEAD` again alone.
    _git(root, "commit", "-q", "--allow-empty", "-m", "empty")
    assert (check(), runs()) == ((0, ["plan: clean"], 3), 1)
    # Another tree has its own results, and a result is judged by the words that
    # name it.
    _commit_tasks(root, tasks[0].replace("prints `1`", "prints `2`"))
    other = "printed other than its Verify: says"
    out = [f"plan: 1.1 — `{counted}` {other}", "  | 1"]
    assert (check(), runs()) == ((1, out, 4), 2)
    assert (check(), runs()) == ((1, out, 4), 2)
    # An unsettled tree reads nothing and keeps nothing.
    (root / _FOLDER / "tasks.md").write_text(_ONE + tasks[0])
    assert (check(), runs()) == ((0, ["plan: clean"], 4), 3)
    # A timed-out command is never kept.
    monkeypatch.setattr(plan_check, "TIMEOUT_SECONDS", 0.5)
    _commit_tasks(root, "- [x] 1.1 Slow.\n  Verify: `sleep 5`.\n")
    assert check() == (1, ["plan: 1.1 — `sleep 5` timed out"], 4)
    # A store that is a link keeps nothing.
    monkeypatch.setattr(plan_check, "TIMEOUT_SECONDS", 600)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    shutil.rmtree(kept)
    kept.symlink_to(elsewhere)
    _commit_tasks(root, tasks[0])
    assert (check(), runs()) == ((0, ["plan: clean"], 0), 4)
    assert list(elsewhere.iterdir()) == []


def _gone(pid: int) -> bool:
    """Return whether a process is gone, waiting up to 5 s for it to be."""
    for _ in range(100):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.05)
    return False


def _pid(path: Path) -> int:
    """Return the pid a command wrote to `path`, waiting up to 10 s for it."""
    for _ in range(200):
        if path.exists() and path.read_text().strip():
            return int(path.read_text())
        time.sleep(0.05)
    raise AssertionError(f"{path} was never written")


def test_a_pytest_with_n_takes_every_slot(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(plan_check, "CPUS", 8)
    for argv in (
        ["pytest", "-n", "auto"],
        ["uv", "run", "pytest", "-q", "-nauto"],
        ["python", "-m", "pytest", "-n4", "tests"],
        ["pytest", "--numprocesses=2"],
        ["pytest", "--numprocesses", "2"],
    ):
        assert plan_check.weight(argv) == 8
    for argv in (
        ["pytest", "-q", "-p", "no:cacheprovider"],
        ["git", "grep", "-n", "pytest"],
        ["make", "-n", "gate"],
    ):
        assert plan_check.weight(argv) == 1


def test_a_timed_out_command_loses_its_process_group(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    _repo(root, monkeypatch)
    monkeypatch.setattr(plan_check, "TIMEOUT_SECONDS", 1.5)
    kid = tmp_path / "kid"
    command = f'sh -c "sleep 30 & echo $! > {kid}; wait"'
    assert plan_check.run(command, root) == plan_check.Result(-1, "", True)
    assert _gone(_pid(kid))
    assert not plan_check.RUNNING


def test_every_pytest_runs_without_the_cache_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    _repo(root, monkeypatch)
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)
    option = "-p no:cacheprovider\n"
    assert plan_check.run("printenv PYTEST_ADDOPTS", root) == (0, option, False)
    monkeypatch.setenv("PYTEST_ADDOPTS", "-q")
    assert plan_check.run("printenv PYTEST_ADDOPTS", root) == (0, f"-q {option}", False)


def test_commands_run_side_by_side_and_print_in_task_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "repo"
    base = _repo(root, monkeypatch)
    monkeypatch.setattr(plan_check, "CPUS", 4)
    monkeypatch.setattr(plan_check, "TIMEOUT_SECONDS", 30)
    left = 'sh -c "touch one; while [ ! -e two ]; do sleep 0.05; done; exit 3"'
    right = 'sh -c "touch two; while [ ! -e one ]; do sleep 0.05; done; exit 4"'
    last = 'sh -c "exit 5"'
    _tasks(
        root,
        _ONE,
        f"- [x] 1.1 Left.\n  Verify: `{left}`.\n",
        f"- [x] 1.2 Right.\n  Verify: `{right}`.\n",
        f"- [x] 1.3 Last.\n  Verify: `{last}`.\n",
    )
    code = plan_check.main(["--change", _CHANGE, "--base", base])
    assert (code, capsys.readouterr().out.splitlines()) == (
        1,
        [
            f"plan: 1.1 — `{left}` exited 3",
            f"plan: 1.2 — `{right}` exited 4",
            f"plan: 1.3 — `{last}` exited 5",
        ],
    )

    # A `pytest` with `-n` runs alone, and a `make` runs beside no other `make`.
    stub = tmp_path / "bin"
    stub.mkdir()
    for name in ("pytest", "make"):
        (stub / name).write_text(
            f'#!/bin/sh\necho "start {name} $*" >> "$STUB_LOG"\nsleep 0.3\n'
            f'echo "end {name} $*" >> "$STUB_LOG"\n'
        )
        (stub / name).chmod(0o755)
    log = tmp_path / "log"
    monkeypatch.setenv("STUB_LOG", str(log))
    monkeypatch.setenv("PATH", f"{stub}{os.pathsep}{os.environ['PATH']}")
    work = ["pytest -q", "make one", "make two", "pytest -n 2"]
    assert set(plan_check.schedule(work, root)) == set(work)
    lines = log.read_text().splitlines()
    assert sorted(lines[:2]) == ["start make one", "start pytest -q"]
    assert lines.index("start make two") > lines.index("end make one")
    assert lines[-2:] == ["start pytest -n 2", "end pytest -n 2"]


def test_sigterm_ends_the_commands_running(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    base = _repo(root, monkeypatch)
    pidfile = tmp_path / "pid"
    command = f'sh -c "echo $$ > {pidfile}; exec sleep 30"'
    _tasks(root, _ONE, f"- [x] 1.1 Wait.\n  Verify: `{command}`.\n")
    process = subprocess.Popen(
        [sys.executable, str(_SCRIPT), "--change", _CHANGE, "--base", base],
        cwd=root,
        stdout=subprocess.DEVNULL,
    )
    pid = _pid(pidfile)
    process.send_signal(signal.SIGTERM)
    assert process.wait(timeout=10) == 143
    assert _gone(pid)


def test_what_the_plan_check_cannot_read_exits_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "repo"
    base = _repo(root, monkeypatch)

    def check(*args: str) -> tuple[int, str]:
        code = plan_check.main(["--change", _CHANGE, "--base", base, *args])
        return code, capsys.readouterr().out.strip()

    def refused(change: str, rev: str) -> tuple[int, str]:
        code = plan_check.main(["--change", change, f"--base={rev}"])
        return code, capsys.readouterr().out.strip()

    # A base naming no commit.
    code, said = refused(_CHANGE, "nonesuch")
    assert code == 2
    assert said.startswith("plan: cannot check — git merge-base failed: fatal:")
    # A base or an id the check will not read.
    for change, rev in ((_CHANGE, "--all"), ("../x", base)):
        code, said = refused(change, rev)
        assert code == 2
        assert said.startswith("plan: cannot check — the change id or the base")

    # A span `tokens()` cannot split, and a stray backtick.
    _tasks(root, _ONE, '- [x] 1.1 Open.\n  Verify: `grep "x`.\n')
    code, said = check()
    assert (code, said.startswith("plan: cannot check — 1.1: ")) == (2, True)
    _tasks(root, _ONE, "- [x] 1.1 Stray.\n  Verify: `true` and `.\n")
    code, said = check()
    assert (code, said.startswith("plan: cannot check — 1.1: ")) == (2, True)

    # A corpus file that does not parse, for a sub-task marked `**CORPUS**`.
    marked = "- [x] 1.1 Read. **CORPUS** `open-cards`\n  Verify: `true`.\n"
    _tasks(root, _ONE, marked)
    (root / "scripts").mkdir()
    (root / "scripts/corpus.toml").write_text("[[case\n")
    code, said = check()
    assert (code, said.startswith("plan: cannot check — scripts/corpus.toml: ")) == (
        2,
        True,
    )

    # No `tasks.md`.
    (root / _FOLDER / "tasks.md").unlink()
    assert check() == (2, "plan: cannot check — tasks.md: No such file or directory")
    run = subprocess.run(
        [sys.executable, str(_SCRIPT), "--change", _CHANGE, "--base", base],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert (run.returncode, run.stdout.strip()) == (
        2,
        "plan: cannot check — tasks.md: No such file or directory",
    )

    # No git, and a directory that is no repository.
    path = os.environ["PATH"]
    monkeypatch.setenv("PATH", "")
    assert check() == (2, "plan: cannot check — git is missing")
    monkeypatch.setenv("PATH", path)
    elsewhere = tmp_path / "plain"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    code, said = check()
    assert code == 2
    assert said.startswith("plan: cannot check — git rev-parse failed: fatal:")
