"""The cut's search script: each search run at HEAD as argv, and `I19`'s shape.

Real git and grep in a scratch repository. Why: 0066-plan-halts design D1.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-cut-change" / "scripts" / "verify_check.py"


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("verify_check", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


verify_check = _load(_SCRIPT)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=mf", "-c", "user.email=mf@example.invalid"]
        + ["-c", "commit.gpgsign=false", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _repo(root: Path, files: dict[str, str]) -> Path:
    """Commit `files` in a new repository at `root`; return it."""
    root.mkdir(exist_ok=True)
    _git(root, "init", "-q")
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text)
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "base")
    return root


def _tasks(*subtasks: str) -> str:
    body = "".join(f"- [ ] {task}\n" for task in subtasks)
    return f"## Progress\n\n- [ ] 1 — One\n\n## 1 — One\n\n{body}"


def _run(
    root: Path,
    tasks: str,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[int, str]:
    """Write `tasks` beside the repository, untracked; return the exit and stdout."""
    path = root / "openspec" / "changes" / "0002-x" / "tasks.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tasks)
    monkeypatch.chdir(root)
    code = verify_check.main([str(path.relative_to(root))])
    return code, capsys.readouterr().out


def test_a_search_prints_the_lines_it_matches_at_head(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _repo(
        tmp_path / "repo",
        {
            "app/drawer.css": ".drawer {\n  width: 720px;\n}\n",
            "app/page.css": ".page { max-width: 720px; }\n",
            "app/states.py": 'STATES = ["ready", "stock_wait"]\n',
            "app/schema.json": '{"$schema": "a|b"}\n',
            "docs/decisions.md": "## D24\n\nSee (D25).\n\n## D25\n",
        },
    )
    # The working tree's edit is not HEAD's, and an untracked file is not in HEAD.
    (root / "app" / "page.css").write_text(".page { max-width: 640px; }\n")
    (root / "notes.md").write_text("720px\n")
    tasks = _tasks(
        "1.1 Set the drawer to `480px`.\n"
        "  Verify: `grep -c '720px' app/drawer.css app/page.css` prints `1`.",
        "1.2 Drop the state.\n"
        "  Verify: `git grep -n '\"stock_wait\"' -- app/` prints nothing.",
        "1.3 Cite D25.\n  Verify: `grep -rn '(D25)' docs` prints a line.",
    )
    code, out = _run(root, tasks, capsys, monkeypatch)
    assert code == 1, out
    assert out.splitlines() == [
        "1.1: app/drawer.css:2:   width: 720px;",
        "1.1: app/page.css:1: .page { max-width: 720px; }",
        "1.1: I19 — an exact count `1` beside 2 matches: "
        "`grep -c '720px' app/drawer.css app/page.css`",
        '1.2: app/states.py:1: STATES = ["ready", "stock_wait"]',
        "1.3: docs/decisions.md:3: See (D25).",
        "verify: halt — I19: 1.1",
    ]

    # The count is the point when it holds: no break, the matches still printed.
    fits = _tasks(
        "1.1 x\n  Verify: `grep --count '720px' app/drawer.css` reports `1`.",
        "1.2 A sub-task with no check is not the script's to read.",
        "1.3 Run it before the first `Verify:` in `a.md`.\n"
        "  Verify: `grep -n 'first' app/states.py` prints nothing.",
        # A revision before `--` is searched there, its name before each path.
        "1.4 x\n  Verify: `git grep -c 'stock_wait' HEAD -- app/` prints `1`.",
        # A quoted `$` or operator is the pattern's, not the shell's.
        "1.5 x\n  Verify: `grep -nF '$schema' app/schema.json` prints a line.",
        "1.6 x\n  Verify: `grep -n '|' app/schema.json` prints a line.",
        # A revision with no `--` after it is searched there too.
        "1.7 x\n  Verify: `git grep -c 'stock_wait' HEAD` prints `1`.",
        # An escaped `$` is the pattern's too.
        "1.8 x\n  Verify: `grep -nF \\$schema app/schema.json` prints a line.",
    )
    code, out = _run(root, fits, capsys, monkeypatch)
    assert code == 0, out
    assert out.splitlines() == [
        "1.1: app/drawer.css:2:   width: 720px;",
        '1.4: HEAD:app/states.py:1: STATES = ["ready", "stock_wait"]',
        '1.5: app/schema.json:1: {"$schema": "a|b"}',
        '1.6: app/schema.json:1: {"$schema": "a|b"}',
        '1.7: HEAD:app/states.py:1: STATES = ["ready", "stock_wait"]',
        '1.8: app/schema.json:1: {"$schema": "a|b"}',
        "verify: every check is one plain command",
    ]


def test_a_check_out_of_shape_breaks_and_is_not_run(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _repo(tmp_path / "repo", {"a.md": "x\n"})
    # A file outside the repository, named whole or climbed to from the tree.
    secret = tmp_path / "secret.md"
    secret.write_text("x\n")
    climb = "../" * 40 + str(secret).lstrip("/")
    tasks = _tasks(
        "1.1 x\n  Verify: `for i in $(seq 20); do make check; done` exits 0.",
        "1.2 x\n  Verify: `while true; do grep -n x a.md; done` prints `x`.",
        "1.3 x\n  Verify: `cd docs && grep -n x a.md` prints a line.",
        "1.4 x\n  Verify: `LIMIT=3 make check` exits 0, and `grep -n $HOME a.md` "
        "prints nothing.",
        "1.5 x\n  Verify: `` grep -n `x` a.md `` prints a line.",
        '1.6 x\n  Verify: `grep -n "$(touch pwned)" a.md` prints nothing.',
        # An option outside the search's list may run a program: a pager, here.
        "1.7 x\n  Verify: `git grep --no-cached '--open-files-in-pager=touch pwned' "
        "-e x -- a.md` prints a line.",
        f"1.8 x\n  Verify: `grep -n x {secret}` prints a line.",
        f"1.9 x\n  Verify: `grep -rn x {climb}` prints a line.",
    )
    code, out = _run(root, tasks, capsys, monkeypatch)
    assert code == 1, out
    assert out.splitlines() == [
        "1.1: I19 — `$(…)` · a loop: `for i in $(seq 20); do make check; done`",
        "1.2: I19 — a loop: `while true; do grep -n x a.md; done`",
        "1.3: I19 — `cd`: `cd docs && grep -n x a.md`",
        "1.4: I19 — a shell variable: `LIMIT=3 make check`",
        "1.4: I19 — a shell variable: `grep -n $HOME a.md`",
        "1.5: I19 — a backtick: `grep -n `x` a.md`",
        '1.6: I19 — `$(…)`: `grep -n "$(touch pwned)" a.md`',
        "1.7: I19 — an option the search does not run: --no-cached · "
        "--open-files-in-pager=touch pwned: `git grep --no-cached "
        "'--open-files-in-pager=touch pwned' -e x -- a.md`",
        f"1.8: I19 — a path outside the repository: {secret}: `grep -n x {secret}`",
        f"1.9: I19 — a path outside the repository: {climb}: `grep -rn x {climb}`",
        "verify: halt — I19: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9",
    ]
    assert not (root / "pwned").exists()


def test_a_search_runs_with_no_shell(tmp_path: Path) -> None:
    root = _repo(tmp_path / "repo", {"a.md": "one\n"})
    tasks = root / "tasks.md"
    tasks.write_text(
        _tasks(
            "1.1 x\n  Verify: `grep -n one a.md > out.txt; touch pwned` prints x.",
            "1.2 x\n  Verify: `grep -n one missing.md` prints a line, and `uv run "
            "pytest -q` reports `3 passed`; `a.md` holds `$HOME` and `$PATH`.",
        )
    )
    result = subprocess.run(
        [sys.executable, str(_SCRIPT), "tasks.md"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout
    assert result.stdout.splitlines() == [
        "1.1: a.md:1: one",
        "1.2: grep: missing.md: No such file or directory",
        "verify: every check is one plain command",
    ]
    assert not (root / "out.txt").exists() and not (root / "pwned").exists()


@pytest.mark.parametrize(
    "verify",
    [
        "`grep -n 'one a.md` prints a line.",
        "`grep -n one a.md prints a line.",
    ],
)
def test_an_unparsable_check_exits_2(
    verify: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _repo(tmp_path / "repo", {"a.md": "one\n"})
    code, out = _run(root, _tasks(f"1.1 x\n  Verify: {verify}"), capsys, monkeypatch)
    assert code == 2, out
    assert out.startswith("verify: cannot check — 1.1: "), out


def test_what_cannot_run_exits_2(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    assert verify_check.main(["missing.md"]) == 2
    assert capsys.readouterr().out.startswith("verify: cannot check — missing.md: ")

    # No repository: HEAD's export fails.
    bare = tmp_path / "bare"
    bare.mkdir()
    search = _tasks("1.1 x\n  Verify: `grep -n one a.md` prints a line.")
    code, out = _run(bare, search, capsys, monkeypatch)
    assert code == 2, out
    assert out.startswith("verify: cannot check — git archive failed: "), out

    root = _repo(tmp_path / "repo", {"a.md": "one\n"})
    # A `git grep` git refuses ran nothing: a revision it cannot read.
    tree = _tasks("1.1 x\n  Verify: `git grep -n one nosuch -- a.md` prints a line.")
    code, out = _run(root, tree, capsys, monkeypatch)
    assert code == 2, out
    assert out.startswith("verify: cannot check — 1.1: git grep failed: fatal: "), out

    def missing(*_: object, **__: object) -> None:
        raise FileNotFoundError

    monkeypatch.setattr(verify_check.subprocess, "run", missing)
    code, out = _run(root, search, capsys, monkeypatch)
    assert (code, out) == (2, "verify: cannot check — git is missing\n")

    def slow(*_: object, **__: object) -> None:
        raise subprocess.TimeoutExpired("git", 1)

    monkeypatch.setattr(verify_check.subprocess, "run", slow)
    code, out = _run(root, search, capsys, monkeypatch)
    assert (code, out) == (2, "verify: cannot check — git archive timed out\n")
