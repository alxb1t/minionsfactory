"""The bundled gate check: fresh exports, gate makefiles, planned changes, ignore marks.

Real git and make in a scratch repository: the routes are make's own behaviour.
Why: 0034-gate-recipe-hardening design D1…D4.
"""

import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-converge" / "scripts" / "gate_check.py"
_CHANGE = "0002-x"
_UNPLANNED = (
    "## Progress\n\n- [ ] 1 — One\n\n## 1 — One\n\n- [ ] 1.1 Edit `README.md`.\n"
)
_GATE = "gate:\n\techo a\n\techo b\n"


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=mf", "-c", "user.email=mf@example.invalid"]
        + ["-c", "commit.gpgsign=false", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _commit(root: Path, files: dict[str, str], message: str) -> str:
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text)
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", message)
    return _git(root, "rev-parse", "HEAD")


def _branch(
    root: Path, base: dict[str, str], tasks: str, branch: dict[str, str]
) -> str:
    """Commit `base`, then the cut with `tasks`, then `branch`; return the base."""
    _git(root, "init", "-q")
    first = _commit(root, {".gitignore": ".minions/\n.env\n", **base}, "base")
    change = f"openspec/changes/{_CHANGE}"
    _commit(root, {f"{change}/design.md": "# X\n", f"{change}/tasks.md": tasks}, "cut")
    _commit(root, branch, "build")
    return first


def _check(
    root: Path, base: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), "--change", _CHANGE, "--base", base],
        cwd=root,
        env={**os.environ, **(env or {})},
        capture_output=True,
        text=True,
    )


def _planned(quote: str = "") -> str:
    return f"## 1 — One\n\n- [ ] 1.1 Change the `gate` recipe in `Makefile`.{quote}\n"


def test_an_unchanged_gate_passes(tmp_path: Path) -> None:
    base = _branch(tmp_path, {"Makefile": _GATE}, _UNPLANNED, {"README.md": "x\n"})
    # A calling make's `-q` would fail both dry runs unless the check clears it.
    result = _check(tmp_path, base, {"MAKEFLAGS": "q"})
    assert (result.returncode, result.stdout) == (0, "gate: the base's\n")
    exports = tmp_path / ".minions" / "gate-check"
    assert not exports.exists() or not any(exports.iterdir())


def test_an_include_changed_on_the_branch_halts(tmp_path: Path) -> None:
    files = {
        "Makefile": "include gate.mk\ngate:\n\t$(CHECK)\n",
        "gate.mk": "CHECK = false\n",
    }
    base = _branch(tmp_path, files, _UNPLANNED, {"gate.mk": "CHECK = true\n"})
    result = _check(tmp_path, base)
    assert result.returncode == 1
    assert result.stdout.endswith("names `Makefile` and `gate`:\n  gate.mk\n")


def test_a_sub_make_weakened_on_the_branch_halts(tmp_path: Path) -> None:
    files = {"Makefile": "gate:\n\t$(MAKE) -C checks check\n"}
    files["checks/Makefile"] = "check:\n\tuv run pytest -q\n"
    weakened = {"checks/Makefile": "check:\n\tuv run pytest -q || true\n"}
    base = _branch(tmp_path, files, _UNPLANNED, weakened)
    result = _check(tmp_path, base)
    assert result.returncode == 1
    assert result.stdout.endswith(":\n  checks/Makefile\n")


def test_a_dash_prefix_halts(tmp_path: Path) -> None:
    files = {"Makefile": "gate:\n\tfalse\n"}
    base = _branch(tmp_path, files, _UNPLANNED, {"Makefile": "gate:\n\t-false\n"})
    result = _check(tmp_path, base)
    assert result.returncode == 1
    assert result.stdout.endswith(":\n  Makefile\n")


def test_an_ignore_target_halts(tmp_path: Path) -> None:
    branch = {"Makefile": f".IGNORE:\n{_GATE}"}
    base = _branch(tmp_path, {"Makefile": _GATE}, _UNPLANNED, branch)
    result = _check(tmp_path, base)
    assert result.returncode == 1
    assert result.stdout.endswith(":\n  Makefile\n")


def test_makeflags_ignore_halts(tmp_path: Path) -> None:
    branch = {"Makefile": f"MAKEFLAGS += -i\n{_GATE}"}
    base = _branch(tmp_path, {"Makefile": _GATE}, _UNPLANNED, branch)
    result = _check(tmp_path, base)
    assert result.returncode == 1
    assert result.stdout.endswith(":\n  Makefile\n")


def test_a_planned_change_that_drops_a_line_halts(tmp_path: Path) -> None:
    branch = {"Makefile": "gate:\n\techo a\n"}
    base = _branch(tmp_path, {"Makefile": _GATE}, _planned(), branch)
    result = _check(tmp_path, base)
    assert result.returncode == 1
    assert "\n  dropped: echo b\n" in result.stdout
    assert "\n-echo b" in result.stdout


def test_a_planned_dash_the_task_does_not_quote_halts(tmp_path: Path) -> None:
    branch = {"Makefile": "gate:\n\techo a\n\t-echo b\n"}
    base = _branch(tmp_path, {"Makefile": _GATE}, _planned(), branch)
    result = _check(tmp_path, base)
    assert result.returncode == 1
    assert "\n  ignore mark: Makefile: -echo b\n" in result.stdout
    assert "dropped" not in result.stdout


def test_a_planned_change_the_task_quotes_passes(tmp_path: Path) -> None:
    branch = {"Makefile": "gate:\n\techo a\n\t-echo c\n"}
    tasks = _planned("\n  It drops `echo b` and adds `-echo c`.")
    base = _branch(tmp_path, {"Makefile": _GATE}, tasks, branch)
    result = _check(tmp_path, base)
    assert result.returncode == 0, result.stdout
    assert result.stdout.startswith("gate: planned — 1.1 Change the `gate` recipe")
    assert "\n-echo b\n+echo c\n" in result.stdout


def test_a_dry_run_failing_in_an_export_exits_2(tmp_path: Path) -> None:
    files = {"Makefile": f"include .env\n{_GATE}", ".env": "KEY = x\n"}
    base = _branch(tmp_path, files, _UNPLANNED, {"README.md": "x\n"})
    result = _check(tmp_path, base)
    assert result.returncode == 2
    assert result.stdout.startswith("gate: cannot check — the base's make database")
    assert ".env" in result.stdout
    assert not (tmp_path / ".minions" / "gate-check" / _CHANGE).exists()


def test_no_single_cut_commit_halts(tmp_path: Path) -> None:
    base = _branch(tmp_path, {"Makefile": _GATE}, _UNPLANNED, {"README.md": "x\n"})
    design = tmp_path / "openspec" / "changes" / _CHANGE / "design.md"
    _git(tmp_path, "rm", "-q", str(design))
    _git(tmp_path, "commit", "-q", "-m", "drop")
    _commit(tmp_path, {str(design.relative_to(tmp_path)): "# X\n"}, "again")
    result = _check(tmp_path, base)
    assert result.returncode == 1
    assert result.stdout.startswith("gate: halt — no single cut commit")
