"""The bundled integration script: the queue, the CHANGELOG, decision ids, the delta.

Real git in a scratch repository with linked worktrees and real merges.
Why: 0037-serial-integration design D2.
"""

import runpy
import subprocess
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-integrate" / "scripts" / "integrate.py"


def _git(root: Path, *args: str, check: bool = True) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=mf", "-c", "user.email=mf@example.invalid"]
        + ["-c", "commit.gpgsign=false", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=check,
    ).stdout.strip()


def _commit(root: Path, files: dict[str, str], message: str) -> None:
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text)
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", message)


def _primary(tmp_path: Path, files: dict[str, str]) -> Path:
    """Return a primary checkout on `main` holding `files`."""
    root = tmp_path / "main"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    _commit(root, {".gitignore": ".minions/\n", **files}, "base")
    return root


def _version(root: Path, change: str, ticked: bool = True) -> Path:
    """Cut `change` on a branch of that name, in a linked worktree; return it."""
    tree = root.parent / change
    _git(root, "worktree", "add", "-q", "-b", change, str(tree))
    box = "x" if ticked else " "
    folder = f"openspec/changes/{change}"
    files = {
        f"{folder}/proposal.md": "---\nbump: minor\n---\n",
        f"{folder}/tasks.md": f"## Progress\n\n- [{box}] 1 — One\n",
    }
    _commit(tree, files, f"cut {change}")
    return tree


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *args], cwd=cwd, capture_output=True, text=True
    )


def test_next_picks_the_lowest_open_id_and_halts_on_an_unready_one(
    tmp_path: Path,
) -> None:
    root = _primary(tmp_path, {"README.md": "x\n"})
    _version(root, "0010-later")
    early = _version(root, "0009-early", ticked=False)
    stray = root.parent / "7-fix-login"
    _git(root, "worktree", "add", "-q", "-b", "7-fix-login", str(stray))
    _commit(stray, {"login.txt": "x\n"}, "not a version")
    _git(root, "worktree", "remove", str(stray))

    result = _run(root, "next")
    assert result.returncode == 1
    assert "next: 0009-early · " in result.stdout
    assert "not ready — phase 1 unticked" in result.stdout

    _commit(
        early,
        {"openspec/changes/0009-early/tasks.md": "## Progress\n\n- [x] 1 — One\n"},
        "tick",
    )
    result = _run(root, "next")
    assert (result.returncode, result.stdout.split(" · ")[-1]) == (0, "ready\n")
    assert f" · {early.resolve()} · " in result.stdout

    findings = root / ".minions" / "findings"
    findings.mkdir(parents=True)
    (findings / "0009-early_review.md").write_text("---\nverdict: clean\n---\n")
    result = _run(root, "next")
    assert result.returncode == 1
    assert "not ready — converge ran, and a findings file is missing" in result.stdout

    (findings / "0009-early_security.md").write_text("---\nverdict: clean\n---\n")
    assert _run(root, "next").returncode == 0

    (early / "openspec/changes/archive").mkdir()
    folder = "openspec/changes/0009-early"
    _git(early, "mv", folder, "openspec/changes/archive/0009-early")
    _git(early, "commit", "-q", "-m", "chore(release): v0.1.0")
    result = _run(root, "next")
    assert result.returncode == 1
    assert "next: 0009-early · " in result.stdout


_HEAD = "# Changelog\n\n## [Unreleased]\n"
_OLD = "## [0.1.0] - 2026-01-01\n\n- First.\n"


def test_changelog_keeps_the_branch_entries_above_the_released_sections(
    tmp_path: Path,
) -> None:
    root = _primary(tmp_path, {"CHANGELOG.md": f"{_HEAD}\n{_OLD}"})
    tree = _version(root, "0003-b")
    entries = "- Branch one.\n\n- Branch two,\n  wrapped.\n"
    _commit(tree, {"CHANGELOG.md": f"{_HEAD}\n{entries}\n{_OLD}"}, "phase")
    released = (
        "## [0.2.0] - 2026-02-02\n\nGate: local 0m1s\n\n- Main one.\n\n- Main two.\n"
    )
    _commit(root, {"CHANGELOG.md": f"{_HEAD}\n{released}\n{_OLD}"}, "release")
    _git(tree, "merge", "-q", "main", check=False)
    assert _git(tree, "diff", "--name-only", "--diff-filter=U") == "CHANGELOG.md"

    result = _run(root, "changelog", str(tree))

    assert result.returncode == 0, result.stdout
    expected = f"{_HEAD}\n{entries}\n{released}\n{_OLD}"
    assert (tree / "CHANGELOG.md").read_text() == expected
    assert _git(tree, "diff", "--name-only", "--diff-filter=U") == ""


_MAP = "Repo conventions D43, D44"


def _decision(number: int, title: str) -> str:
    return f"\n### D{number} · {title}\n\n**{title}.**\n\n- **Why:** because.\n"


def test_decisions_renumbers_a_colliding_decision_and_its_citations(
    tmp_path: Path,
) -> None:
    head = f"# Decisions\n\n```\n  {_MAP}\n```\n\n## Repo conventions\n"
    old = _decision(43, "Old") + _decision(44, "Older")
    root = _primary(
        tmp_path, {"docs/decisions.md": head + old, "docs/shared.md": "## Common\n"}
    )
    tree = _version(root, "0046-b")
    ours = head.replace("D44", "D44, D45") + old + _decision(45, "Branch")
    cite = "Per [D45](decisions.md#d45--branch), and D44 stays.\n"
    _commit(
        tree,
        {
            "docs/decisions.md": ours,
            "docs/guide.md": cite,
            "docs/shared.md": "## Branch\nPer D45.\n\n## Common\n",
        },
        "phase",
    )
    theirs = head.replace("D44", "D44, D45") + old + _decision(45, "Main")
    _commit(
        root,
        {
            "docs/decisions.md": theirs,
            "docs/shared.md": "## Common\n\n## Main\nPer D45.\n",
        },
        "release",
    )
    _git(tree, "merge", "-q", "main", check=False)
    assert _git(tree, "diff", "--name-only", "--diff-filter=U") == "docs/decisions.md"

    result = _run(root, "decisions", str(tree))

    assert result.returncode == 0, result.stdout
    assert result.stdout == "decisions: renumbered D45 → D46, citations with them\n"
    merged = head.replace("D44", "D44, D45, D46") + old
    merged += _decision(45, "Main") + _decision(46, "Branch")
    assert (tree / "docs/decisions.md").read_text() == merged
    guide = "Per [D46](decisions.md#d46--branch), and D44 stays.\n"
    assert (tree / "docs/guide.md").read_text() == guide
    assert (tree / "docs/shared.md").read_text() == (
        "## Branch\nPer D46.\n\n## Common\n\n## Main\nPer D45.\n"
    )
    assert _git(tree, "diff", "--name-only", "--diff-filter=U") == ""
    assert _git(tree, "diff", "--name-only") == ""
    helpers = runpy.run_path(str(_SCRIPT))
    with pytest.raises(helpers["Stop"], match="both sides changed"):
        helpers["merge3"](
            "The mode is enabled.\n",
            "The mode is never enabled.\n",
            "The mode is always enabled.\n",
            decision_map=True,
        )
    external = tmp_path / "external.md"
    external.write_text("Per D45.\n")
    (tree / "linked.md").symlink_to(external)
    (tree / "linked-dir").symlink_to(tmp_path, target_is_directory=True)
    for path in ("linked.md", "linked-dir/external.md", "../external.md"):
        with pytest.raises(helpers["Stop"], match="unsafe path"):
            helpers["_write"](tree, path, "replacement\n")
        assert external.read_text() == "Per D45.\n"
        with pytest.raises(helpers["Stop"], match="unsafe path"):
            helpers["_recite"](tree, path, {45: 46}, "HEAD")
        assert external.read_text() == "Per D45.\n"


def _spec(first: str) -> str:
    return (
        "# sdd\n\n## Requirements\n\n"
        f"### Requirement: First\n\n{first}\n\n"
        "### Requirement: Second\n\nThe second SHALL hold.\n"
    )


def test_delta_reports_a_requirement_main_changed(tmp_path: Path) -> None:
    root = _primary(tmp_path, {"openspec/specs/sdd/spec.md": _spec("It SHALL hold.")})
    tree = _version(root, "0005-b")
    delta = (
        "## MODIFIED Requirements\n\n### Requirement: First\n\nThe branch's.\n\n"
        "### Requirement: Second\n\nThe branch's.\n"
    )
    _commit(tree, {"openspec/changes/0005-b/specs/sdd/spec.md": delta}, "phase")
    _commit(root, {"openspec/specs/sdd/spec.md": _spec("Main's.")}, "release")
    _git(tree, "merge", "-q", "--no-commit", "main")

    result = _run(root, "delta", str(tree))

    assert result.returncode == 1
    assert result.stdout == "delta: changed on the default branch: sdd: First\n"
