"""The plan check: a change's plan held to the tree built from it.

A repository under `tmp_path`, the check run in-process from inside it.
Why: 0103-fewer-rounds design D4.
"""

import importlib.util
import os
import subprocess
import sys
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
