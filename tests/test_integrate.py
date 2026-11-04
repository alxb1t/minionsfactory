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


def test_next_picks_the_named_or_the_lowest_ready_id(tmp_path: Path) -> None:
    root = _primary(tmp_path, {"README.md": "x\n"})
    # `0010` sorts before `009` as text: the queue is the change id's number.
    later = _version(root, "0010-later")
    early = _version(root, "009-early", ticked=False)
    stray = root.parent / "7-fix-login"
    _git(root, "worktree", "add", "-q", "-b", "7-fix-login", str(stray))
    _commit(stray, {"login.txt": "x\n"}, "not a version")
    _git(root, "worktree", "remove", str(stray))

    result = _run(root, "next")
    assert result.returncode == 0
    assert result.stdout.startswith("next: 0010-later · ")
    assert result.stdout.endswith(" · ready\n")

    forged = tmp_path / "zz-forged"
    forged.mkdir()
    entry = root / ".git" / "worktrees" / "zz-forged"
    entry.mkdir()
    (entry / "HEAD").write_text("ref: refs/heads/0010-later\n")
    (entry / "commondir").write_text("../..\n")
    (entry / "gitdir").write_text(f"{forged}/.git\n")
    assert f"worktree {forged.resolve()}\n" in _git(
        root, "worktree", "list", "--porcelain"
    )
    result = _run(root, "next", "0010-later")
    assert f" · {later.resolve()} · " in result.stdout
    (forged / ".git").mkdir()
    assert f" · {later.resolve()} · " in _run(root, "next", "0010-later").stdout
    (forged / ".git").rmdir()
    (forged / ".git").write_text(f"gitdir: {tmp_path}/other/.git/worktrees/x\n")
    assert f" · {later.resolve()} · " in _run(root, "next", "0010-later").stdout

    pointer = later / ".git"
    absolute = pointer.read_text()
    pointer.write_text("gitdir: ../main/.git/worktrees/0010-later\n")
    assert f" · {later.resolve()} · " in _run(root, "next", "0010-later").stdout
    pointer.write_text(absolute)

    result = _run(root, "next", "009-early")
    assert result.returncode == 1
    assert "next: 009-early · " in result.stdout
    assert "not ready — phase 1 unticked" in result.stdout

    result = _run(root, "next", "7-fix-login")
    assert (result.returncode, result.stdout) == (1, "next: 7-fix-login · not open\n")

    _commit(root, {"moved.txt": "x\n"}, "main moves")
    _git(early, "merge", "-q", "--no-ff", "--no-commit", "main")
    note = root / ".minions" / "integrate" / "009-early.md"
    note.parent.mkdir(parents=True)
    note.write_text("note\n")
    result = _run(root, "next", "009-early")
    assert (result.returncode, result.stdout.split(" · ")[-1]) == (0, "ready\n")
    assert _run(root, "next").stdout.startswith("next: 0010-later · ")
    note.unlink()
    assert _run(root, "next", "009-early").returncode == 1
    _git(early, "merge", "--abort")

    _commit(
        early,
        {"openspec/changes/009-early/tasks.md": "## Progress\n\n- [x] 1 — One\n"},
        "tick",
    )
    result = _run(root, "next")
    assert (result.returncode, result.stdout.split(" · ")[-1]) == (0, "ready\n")
    assert f" · {early.resolve()} · " in result.stdout

    findings = root / ".minions" / "findings"
    findings.mkdir(parents=True)
    (findings / "009-early_review.md").write_text("---\nverdict: clean\n---\n")
    result = _run(root, "next", "009-early")
    assert result.returncode == 1
    assert "not ready — converge ran, and a findings file is missing" in result.stdout

    (findings / "009-early_security.md").write_text("---\nverdict: clean\n---\n")
    assert _run(root, "next", "009-early").returncode == 0

    proposal = "---\nbump: minor\nafter: [009-early]\n---\n"
    _commit(later, {"openspec/changes/0010-later/proposal.md": proposal}, "after")
    result = _run(root, "next", "0010-later")
    assert result.returncode == 1
    assert "not ready — after 009-early" in result.stdout

    (early / "openspec/changes/archive").mkdir()
    folder = "openspec/changes/009-early"
    _git(early, "mv", folder, "openspec/changes/archive/009-early")
    _git(early, "commit", "-q", "-m", "chore(release): v0.1.0")
    result = _run(root, "next")
    assert result.returncode == 1
    assert "next: 009-early · " in result.stdout

    _git(later, "merge", "-q", "--no-ff", "-m", "bring it in", "009-early")
    result = _run(root, "next")
    assert result.returncode == 0
    assert result.stdout.startswith("next: 0010-later · ")


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


def _changelog_merge(base: Path) -> tuple[Path, Path]:
    """Return a primary and a version whose merge of `main` conflicts in CHANGELOG.md.

    The merge is left open; `changelog` has settled and staged it.
    """
    base.mkdir()
    root = _primary(base, {"CHANGELOG.md": f"{_HEAD}\n{_OLD}", "README.md": "x\n"})
    tree = _version(root, "0003-b")
    _commit(tree, {"CHANGELOG.md": f"{_HEAD}\n- Branch.\n\n{_OLD}"}, "phase")
    released = "## [0.2.0] - 2026-02-02\n\n- Main.\n"
    _commit(root, {"CHANGELOG.md": f"{_HEAD}\n{released}\n{_OLD}"}, "release")
    _git(tree, "merge", "-q", "--no-ff", "--no-commit", "main", check=False)
    assert _run(root, "changelog", str(tree)).returncode == 0
    return root, tree


def _scratch_gone(root: Path) -> bool:
    replays = root / ".minions" / "replay"
    listed = _git(root, "worktree", "list", "--porcelain").count("worktree ")
    return listed == 2 and not (replays.exists() and any(replays.iterdir()))


def test_replay_reproduces_a_rule_settled_merge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, tree = _changelog_merge(tmp_path / "changelog")
    _git(tree, "commit", "-q", "-m", "chore(integrate): merge main into 0003-b")

    result = _run(tree, "replay", "HEAD")

    assert (result.returncode, result.stdout) == (0, "replay: by rule — CHANGELOG.md\n")
    assert _scratch_gone(root)

    # A merge git settles alone is the rules' too.
    clean = tmp_path / "clean"
    clean.mkdir()
    root = _primary(clean, {"README.md": "x\n"})
    tree = _version(root, "0004-c")
    _commit(root, {"main.txt": "x\n"}, "main moves")
    _git(tree, "merge", "-q", "--no-ff", "-m", "chore(integrate): merge", "main")
    result = _run(root, "replay", _git(tree, "rev-parse", "HEAD"))
    assert (result.returncode, result.stdout) == (0, "replay: by rule — no conflict\n")
    assert _scratch_gone(root)

    # A hook a worker planted in the common directory runs nowhere in a replay,
    # though a plain checkout runs it.
    monkeypatch.delenv("GIT_CONFIG_COUNT", raising=False)
    marker = tmp_path / "hook-ran"
    hook = root / ".git" / "hooks" / "post-checkout"
    hook.write_text(f"#!/bin/sh\ntouch '{marker}'\n")
    hook.chmod(0o755)
    _git(root, "checkout", "-q", "main")
    assert marker.exists()
    marker.unlink()
    result = _run(root, "replay", _git(tree, "rev-parse", "HEAD"))
    assert (result.returncode, result.stdout) == (0, "replay: by rule — no conflict\n")
    assert not marker.exists()
    assert _scratch_gone(root)

    # A planted promisor holds a blob the replay needs: no git of it fetches one.
    holder = tmp_path / "holder.git"
    _git(tmp_path, "clone", "-q", "--bare", str(root), str(holder))
    _git(root, "config", "remote.x.url", str(holder))
    _git(root, "config", "remote.x.promisor", "true")
    blob = _git(root, "rev-parse", "main:main.txt")
    (root / ".git" / "objects" / blob[:2] / blob[2:]).unlink()
    result = _run(root, "replay", _git(tree, "rev-parse", "HEAD"))
    assert result.returncode == 2, result.stdout
    assert not list((root / ".git" / "objects" / "pack").glob("*.promisor"))
    assert _scratch_gone(root)


def test_replay_refuses_a_judged_merge(tmp_path: Path) -> None:
    # A union: both sides add a line to one file, resolved by hand.
    union = tmp_path / "union"
    union.mkdir()
    root = _primary(union, {"README.md": "x\n"})
    tree = _version(root, "0003-b")
    _commit(tree, {"README.md": "x\nbranch\n"}, "phase")
    _commit(root, {"README.md": "x\nmain\n"}, "main moves")
    _git(tree, "merge", "-q", "--no-ff", "--no-commit", "main", check=False)
    _commit(tree, {"README.md": "x\nbranch\nmain\n"}, "chore(integrate): merge")
    result = _run(tree, "replay", "HEAD")
    assert result.returncode == 1, result.stdout
    assert result.stdout == "replay: judged — the rules leave README.md unmerged\n"
    assert _scratch_gone(root)

    # A person's edit over the rule's resolution.
    root, tree = _changelog_merge(tmp_path / "person")
    changelog = (tree / "CHANGELOG.md").read_text()
    _commit(tree, {"CHANGELOG.md": changelog + "- A person's line.\n"}, "merge")
    result = _run(tree, "replay", "HEAD")
    assert result.returncode == 1, result.stdout
    assert result.stdout == (
        "replay: judged — the merge differs from the rules at CHANGELOG.md\n"
    )
    assert _scratch_gone(root)

    # A test git merged cleanly, edited before the commit.
    edited = tmp_path / "edited"
    edited.mkdir()
    root = _primary(edited, {"tests/test_x.py": "assert True\n"})
    tree = _version(root, "0003-b")
    _commit(root, {"tests/test_x.py": "assert 1\n"}, "main moves")
    _git(tree, "merge", "-q", "--no-ff", "--no-commit", "main")
    _commit(tree, {"tests/test_x.py": "assert 1 == 1\n"}, "chore(integrate): merge")
    result = _run(tree, "replay", "HEAD")
    assert result.returncode == 1, result.stdout
    assert "differs from the rules at tests/test_x.py" in result.stdout
    assert _scratch_gone(root)

    # A commit with one parent is no merge.
    result = _run(tree, "replay", "HEAD~1")
    assert result.returncode == 2, result.stdout
    assert result.stdout.startswith("integrate: cannot run — HEAD~1 is not a merge")
    assert _scratch_gone(root)

    # A clean merge of a commit the default branch does not hold is no catch-up.
    _git(root, "checkout", "-q", "-b", "side")
    _commit(root, {"side.txt": "x\n"}, "side work")
    _git(root, "checkout", "-q", "main")
    _git(tree, "merge", "-q", "--no-ff", "-m", "chore(integrate): merge", "side")
    result = _run(tree, "replay", "HEAD")
    assert result.returncode == 2, result.stdout
    assert result.stdout == (
        "integrate: cannot run — HEAD's second parent is not on main\n"
    )
    assert _scratch_gone(root)

    # A requirement both sides changed: `delta` halts, the person keeps the branch's.
    both = tmp_path / "delta"
    both.mkdir()
    root = _primary(both, {"openspec/specs/sdd/spec.md": _spec("It SHALL hold.")})
    tree = _version(root, "0005-b")
    edit = "## MODIFIED Requirements\n\n### Requirement: First\n\nThe branch's.\n"
    _commit(tree, {"openspec/changes/0005-b/specs/sdd/spec.md": edit}, "phase")
    _commit(root, {"openspec/specs/sdd/spec.md": _spec("Main's.")}, "release")
    _git(tree, "merge", "-q", "--no-ff", "-m", "chore(integrate): merge", "main")
    result = _run(tree, "replay", "HEAD")
    assert result.returncode == 1, result.stdout
    assert result.stdout == (
        "replay: judged — delta: changed on the default branch: sdd: First\n"
    )
    assert _scratch_gone(root)


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
