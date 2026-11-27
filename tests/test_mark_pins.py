"""Pins of the marks as the conductor and `release.py` read, write and remove them.

Each case holds the one side and starts no worker. Why: 0154-marks design D8, D11.
"""

import errno
import os
import runpy
import threading
import types
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from conduct_load import conduct as _conduct
from conduct_load import halting
from fake_worker import _commit, _git
from mflib import layout
from test_release import Repo, _cut_release, _forged, _merge, _moved
from test_release import repo as _release_repo  # noqa: F401

_CHANGE = "0001-todo"
_WORKTREES = (
    "- **Worktrees:** `../` — a version's worktree is `<this path>/<branch>`.\n"
)
_BOUND = 65536
_AMEND = f"docs({_CHANGE}): amend the change directory"
_PROPOSAL = f"openspec/changes/{_CHANGE}/proposal.md"


@pytest.fixture(autouse=True)
def _idle_machine(monkeypatch: pytest.MonkeyPatch) -> None:
    """Read a load of 0, so no red gate of a case waits for the machine."""
    monkeypatch.setattr(os, "getloadavg", lambda: (0.0, 0.0, 0.0))


def _primary(tmp_path: Path) -> Path:
    """Return a primary checkout on `main` with a green gate."""
    root = tmp_path / "main"
    root.mkdir(parents=True)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.name", "mf")
    _git(root, "config", "user.email", "mf@example.invalid")
    _git(root, "config", "commit.gpgsign", "false")
    files = {
        ".gitignore": ".minions/\n",
        "AGENTS.md": _WORKTREES,
        "Makefile": "gate:\n\ttrue\n",
    }
    _commit(root, files, "base")
    return root.resolve()


def _version(root: Path, change: str, progress: str) -> Path:
    """Cut `change` on a branch of that name, linked, `progress` its list."""
    tree = root.parent / change
    _git(root, "worktree", "add", "-q", "-b", change, str(tree))
    folder = f"openspec/changes/{change}"
    files = {
        f"{folder}/proposal.md": "---\nbump: minor\n---\n",
        f"{folder}/design.md": f"# {change} — design\n",
        f"{folder}/tasks.md": f"## Progress\n\n{progress}",
    }
    _commit(tree, files, f"cut {change}")
    return tree.resolve()


def _folder(root: Path, change: str = _CHANGE) -> Path:
    """Return the change's mark folder under `root`, made."""
    folder = root / ".minions" / "changes" / change
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _plant(path: Path, shape: str, text: str = "head: abc1234\n") -> None:
    """Make `path` a `shape`: a file, an empty file, a link, a hard link and so on."""
    other = path.parent.parent / f".other-{path.name}"
    if shape == "file":
        path.write_text(text)
    elif shape == "empty":
        path.write_text("")
    elif shape == "binary":
        path.write_bytes(b"head: abc1234\n\xff\xfe\n")
    elif shape == "big":
        path.write_text(text + "z" * (_BOUND + 4096) + "\n")
    elif shape == "link":
        other.write_text(text)
        path.symlink_to(other)
    elif shape == "dangling":
        path.symlink_to(path.parent.parent / ".nowhere")
    elif shape == "hard":
        other.write_text(text)
        os.link(other, path)
    elif shape == "folder":
        path.mkdir()
    else:
        assert shape == "pipe", shape
        os.mkfifo(path)


def _within(call: Callable[[], Any], seconds: float = 5.0) -> Any:  # noqa: ANN401
    """Return what `call` returns, raise what it raises, and fail if it blocks."""
    done: list[Any] = []
    failed: list[BaseException] = []

    def run() -> None:
        try:
            done.append(call())
        # why: the thread carries any failure of the call back to the test
        except BaseException as error:  # noqa: BLE001
            failed.append(error)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    thread.join(seconds)
    assert not thread.is_alive(), "the call blocked"
    if failed:
        raise failed[0]
    return done[0]


def test_case_c_cut_halt(tmp_path: Path) -> None:
    conduct = _conduct()
    marks = conduct["mflib"].marks
    halt = marks.cutter_halt
    mark = _folder(tmp_path) / "cut.halt"
    assert halt(tmp_path, _CHANGE) is None

    mark.write_text("  the cutter stopped  \nsecond line\n")
    assert halt(tmp_path, _CHANGE) == "the cutter stopped"
    mark.write_text("x" * 400 + "\n")
    assert halt(tmp_path, _CHANGE) == "x" * 300
    mark.write_text("   " + "y" * 310 + "\n")
    assert halt(tmp_path, _CHANGE) == "y" * 300
    mark.write_bytes(b"a\xffb\n")
    with pytest.raises(marks.Broken):
        halt(tmp_path, _CHANGE)
    said = f".minions/changes/{_CHANGE}/cut.halt cannot be read: it is not UTF-8"
    assert conduct["_check_cut"](tmp_path, _CHANGE, tmp_path) == said

    mark.write_text("")
    assert halt(tmp_path, _CHANGE) == ""
    assert conduct["_check_cut"](tmp_path, _CHANGE, tmp_path) == ""

    mark.unlink()
    _plant(mark, "link", "a halt\n")
    with pytest.raises(marks.Broken, match=r"^cut\.halt cannot be read: it is a link$"):
        halt(tmp_path, _CHANGE)


def _closed_at(root: Path, tree: Path, text: str) -> bool:
    """Plant `text` as `build.done` and return `_closed` on `tree`."""
    (_folder(root) / "build.done").write_text(text)
    return _conduct()["_closed"](root / ".minions", tree, _CHANGE)


def test_case_d_build_done_head(tmp_path: Path) -> None:
    conduct = _conduct()
    head = conduct["mflib"].marks.done_head
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    mark = _folder(root) / "build.done"
    assert head(root, _CHANGE) is None

    mark.write_text("head: abc1234\n")
    assert head(root, _CHANGE) == "abc1234"
    mark.write_text("head:\nabc1234\n")
    assert head(root, _CHANGE) is None
    mark.write_text("head:   \n\n  abc1234 x\n")
    assert head(root, _CHANGE) is None
    mark.unlink()
    for shape in ("pipe", "binary", "dangling", "folder"):
        _plant(mark, shape)
        assert _within(lambda: head(root, _CHANGE)) is None, shape
        if shape == "folder":
            mark.rmdir()
        else:
            mark.unlink()

    # A full sha and its short form close the build; `HEAD`, a branch and a tag do not.
    _git(tree, "tag", "-a", "-m", "built", "built-tag")
    sha = _git(tree, "rev-parse", "HEAD")
    for word in (sha, sha[:7]):
        assert _closed_at(root, tree, f"head: {word}\n"), word
    for word in ("HEAD", _CHANGE, "built-tag", "main"):
        assert not _closed_at(root, tree, f"head: {word}\n"), word
    assert not _closed_at(root, tree, "simplify: none\n")


def _built(root: Path, change: str = _CHANGE) -> str | None:
    """Return `_built_head` for `change`."""
    return _conduct()["_built_head"](root, change)


@pytest.mark.slow
def test_case_d_the_built_head_refuses_what_it_does_not_hold(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    built = _git(tree, "rev-parse", "HEAD")
    mark = _folder(root) / "build.done"
    mark.write_text(f"head: {built}\nsimplify: none\n")
    assert _built(root) == built

    # A head off the branch.
    _commit(root, {"main.txt": "x\n"}, "main moves")
    mark.write_text(f"head: {_git(root, 'rev-parse', 'main')}\n")
    assert _built(root) is None
    mark.write_text(f"head: {built}\n")
    assert _built(root) == built

    # A change with no box, then one with an open box.
    tasks = f"openspec/changes/{_CHANGE}/tasks.md"
    _commit(tree, {tasks: "## Progress\n\nno boxes\n"}, "no box")
    mark.write_text(f"head: {_git(tree, 'rev-parse', 'HEAD')}\n")
    assert _built(root) is None
    _commit(tree, {tasks: "## Progress\n\n- [ ] 1 — One\n"}, "open box")
    mark.write_text(f"head: {_git(tree, 'rev-parse', 'HEAD')}\n")
    assert _built(root) is None
    _commit(tree, {tasks: "## Progress\n\n- [x] 1 — One\n"}, "ticked")
    ticked = _git(tree, "rev-parse", "HEAD")
    mark.write_text(f"head: {ticked}\n")
    assert _built(root) == ticked

    # A re-planned change: an amend of the proposal past the head.
    _commit(tree, {_PROPOSAL: "---\nbump: patch\n---\n"}, _AMEND)
    assert _built(root) is None


def _side(tree: Path, name: str, path: str) -> str:
    """Commit an amend of `path` on a side branch of `tree`; return the branch name."""
    _git(tree, "switch", "-q", "-c", name)
    _commit(tree, {path: f"---\nbump: patch\n---\n{name}\n"}, _AMEND)
    _git(tree, "switch", "-q", _CHANGE)
    return name


@pytest.mark.slow
def test_case_d_a_side_merge_and_an_octopus_merge_refuse_the_built_head(
    tmp_path: Path,
) -> None:
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    built = _git(tree, "rev-parse", "HEAD")
    (_folder(root) / "build.done").write_text(f"head: {built}\n")
    notes = f"openspec/changes/{_CHANGE}/notes.md"
    first = _side(tree, "side-one", _PROPOSAL)
    second = _side(tree, "side-two", notes)
    _git(tree, "merge", "-q", "--no-ff", "-m", "side", first)
    assert _built(root) is None

    _git(tree, "reset", "-q", "--hard", built)
    assert _built(root) == built
    _git(tree, "merge", "-q", "--no-ff", "-m", "octopus", first, second)
    assert _built(root) is None


def test_case_d_a_merged_back_build_passes_stage_of(tmp_path: Path) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    built = _git(tree, "rev-parse", "HEAD")
    (_folder(root) / "build.done").write_text(f"head: {built}\n")
    version = conduct["Version"](_CHANGE, tree)
    _commit(root, {"main.txt": "x\n"}, "main moves")
    _git(tree, "merge", "-q", "--no-ff", "-m", "merge main", "main")
    assert not conduct["_closed"](root / ".minions", tree, _CHANGE)
    assert conduct["_merged_back"](tree, built, "main")
    assert conduct["stage_of"](root, version)[0] != "build"


def test_case_g_diagnose_writes_the_exact_text_and_halts_once(tmp_path: Path) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    run = conduct["Run"](root, "claude")
    run.diagnose(_CHANGE, "a halt")
    name = f".minions/changes/{_CHANGE}/rescue.md"
    assert (root / name).read_text() == (
        f"# {_CHANGE} — rescue diagnosis\n\nhalt: a halt\nsub-task: none\n"
        "cause: a Verify: changed since the cut\n"
        f"proposal: commit docs({_CHANGE}): amend the change directory, then"
        f" conduct.py rejoin {_CHANGE}, or /mf-ship with no run live\n"
    )
    assert run.halts == [(_CHANGE, f"rescue diagnosed — {name}")]
    assert run.diagnosed == {_CHANGE}


def test_case_g_a_failed_write_halts_the_version_and_leaves_it_undiagnosed(
    tmp_path: Path,
) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    run = conduct["Run"](root, "claude")
    mark = _folder(root) / "rescue.md"
    outside = tmp_path / "person.md"
    outside.write_text("the person's\n")
    mark.symlink_to(outside)
    run.diagnose(_CHANGE, "a halt")
    assert outside.read_text() == "the person's\n"
    [(who, why)] = run.halts
    assert who == _CHANGE
    assert why.startswith(
        f"rescue: cannot write .minions/changes/{_CHANGE}/rescue.md — "
    )
    assert run.diagnosed == set()


def test_case_g_release_held_stands_as_a_file_or_a_link_to_one(tmp_path: Path) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    mark = _folder(root) / "release.held"
    tip = conduct["_release_tip"]
    held = (
        f"v1.0.0: .minions/changes/{_CHANGE}/release.held holds a person's no:"
        f" /mf-release {_CHANGE} merges it on their yes"
    )
    assert tip(root, tree, _CHANGE, "v1.0.0") != ("released", held)
    _plant(mark, "file", "no\n")
    assert tip(root, tree, _CHANGE, "v1.0.0") == ("released", held)
    mark.unlink()
    _plant(mark, "link", "no\n")
    said = f"conduct: halt — .minions/changes/{_CHANGE}/release.held cannot be read: "
    with pytest.raises(conduct["Stop"]) as stopped:
        tip(root, tree, _CHANGE, "v1.0.0")
    assert str(stopped.value).startswith(said)


def _halted(root: Path, tree: Path, text: str) -> Any:  # noqa: ANN401
    """Plant `build.halt` as `text`, `{head}` the tree's `HEAD`; return its reading."""
    head = _git(tree, "rev-parse", "HEAD")
    (_folder(root) / "build.halt").write_text(text.format(head=head))
    return _conduct()["_build_halt"](root / ".minions", tree, _CHANGE)


def test_case_h_build_halt_keys(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [ ] 1 — One\n")
    head = _git(tree, "rev-parse", "HEAD")
    assert _conduct()["_build_halt"](root / ".minions", tree, _CHANGE) is None

    whole = "sub-task: {sub}\nstop: 3\nevidence: x\nhead: {{head}}\n"
    assert _halted(root, tree, whole.format(sub="1.2")) == ("1.2", "3")
    # A value keeps its inner spaces and loses the outer ones.
    spaced = whole.format(sub="  1.2  and   more \t")
    assert _halted(root, tree, spaced) == ("1.2  and   more", "3")

    # Two `head:` lines hold no head.
    late = "sub-task: 1.2\nstop: 3\nhead: deadbeef\nhead: {head}\n"
    assert _halted(root, tree, late) is None
    early = "sub-task: 1.2\nstop: 3\nhead: {head}\nhead: deadbeef\n"
    assert _halted(root, tree, early) is None

    # A key with no value on its line, or in mid-line, is not read.
    bare = "sub-task: 1.2\nstop:\n3\nhead: {head}\n"
    assert _halted(root, tree, bare) is None
    mid = "sub-task: 1.2\nsee stop: 3\nhead: {head}\n"
    assert _halted(root, tree, mid) is None
    # A head with more after it is stale.
    assert _halted(root, tree, "sub-task: 1.2\nstop: 3\nhead: {head} x\n") is None
    assert _halted(root, tree, "sub-task: 1.2\nstop: 3\n") is None
    assert head


@pytest.mark.slow
def test_case_h_the_checks_and_held_name_the_sub_task(tmp_path: Path) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [ ] 1 — One\n")
    version = conduct["Version"](_CHANGE, tree)
    run = conduct["Run"](root, "claude")
    plain = "phase 1 unticked"
    assert conduct["_check_simplified"](root, version, tree) == plain
    assert conduct["_check_phase"](root, version, tree, "1") == plain
    assert run.held(version, "build", tree) == "build"

    _halted(root, tree, "sub-task: 1.2\nstop: 3\nhead: {head}\n")
    named = f"{plain} · 1.2: 3"
    assert conduct["_check_simplified"](root, version, tree) == named
    assert conduct["_check_phase"](root, version, tree, "1") == named
    assert run.held(version, "build", tree) == "1.2"

    _halted(root, tree, "sub-task: 1.2\nstop: 3\nhead: deadbeef\n")
    assert conduct["_check_phase"](root, version, tree, "1") == plain
    assert run.held(version, "build", tree) == "build"


class _Moved(Exception):
    """A `delta` failure that names a requirement the default branch changed."""

    code = 1


def _merging(conduct: dict[str, Any], tmp_path: Path) -> tuple[Path, Path, Any, str]:
    """Return a primary, a version `main` moved past, its `Run` and the moved line."""
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [ ] 1 — One\n")
    _commit(root, {"main.txt": "x\n"}, "main moves")
    run = conduct["Run"](root, "claude")
    moved = f"{conduct['MOVED']}sdd: First"

    def delta(_: Path) -> str:
        raise _Moved(moved)

    run.delta = delta
    return root, tree, run, moved


_NOTE = (
    "## sdd: First\n\n"
    f"- **The branch:** `openspec/changes/{_CHANGE}/design.md`\n"
    "- **The default branch:** no `Change:` trailer\n"
    "- **Proposed:** rewrite the delta's requirement over the default"
    " branch's text, keeping both edits.\n"
)


@pytest.mark.slow
def test_case_m_merge_in_writes_the_note_and_leaves_the_merge_open(
    tmp_path: Path,
) -> None:
    conduct = _conduct()
    root, tree, run, moved = _merging(conduct, tmp_path)
    head = _git(tree, "rev-parse", "HEAD")
    note = _folder(root) / "integrate.md"

    run.merge_in(tree, _CHANGE, "main")
    assert note.read_text() == _NOTE
    assert conduct["_merge_open"](tree)
    assert _git(tree, "rev-parse", "HEAD") == head
    assert conduct["_note"](tree, _CHANGE, [moved]) == _NOTE

    # An open merge with a note commits nothing and rewrites nothing.
    note.write_text("a person's edit\n")
    run.merge_in(tree, _CHANGE, "main")
    assert note.read_text() == "a person's edit\n"
    assert conduct["_merge_open"](tree)
    assert _git(tree, "rev-parse", "HEAD") == head


@pytest.mark.slow
def test_case_m_the_note_stays_under_the_bound_its_reader_holds(tmp_path: Path) -> None:
    conduct = _conduct()
    _, tree, run, moved = _merging(conduct, tmp_path)
    run.merge_in(tree, _CHANGE, "main")
    assert conduct["NOTE_BOUND"] < conduct["mflib"].marks.BOUND
    bound = 3 * len(_NOTE)

    note = conduct["_note"](tree, _CHANGE, [moved] * 5, bound)
    assert note.startswith(_NOTE)
    assert len(note.encode()) <= bound + 200
    assert note.count("## sdd: First") == 2
    assert note.endswith("more requirements moved: read the merge's diff.\n")


@pytest.mark.slow
def test_case_m_a_failed_write_stops_the_version_with_code_1(tmp_path: Path) -> None:
    conduct = _conduct()
    root, tree, run, _ = _merging(conduct, tmp_path)
    run.merge_in(tree, _CHANGE, "main")
    note = _folder(root) / "integrate.md"
    note.unlink()
    note.symlink_to(tmp_path / "gone.md")
    name = f".minions/changes/{_CHANGE}/integrate.md"

    # In the open merge the note's stand test meets the link first.
    with pytest.raises(conduct["Stop"]) as stopped:
        run.merge_in(tree, _CHANGE, "main")
    assert str(stopped.value) == f"conduct: halt — {name} cannot be read: it is a link"
    _git(tree, "merge", "--abort")
    with pytest.raises(conduct["Stop"]) as stopped:
        run.merge_in(tree, _CHANGE, "main")
    assert stopped.value.code == 1
    assert str(stopped.value).startswith(f"conduct: halt — cannot write {name} — ")
    assert not (tmp_path / "gone.md").exists()
    assert conduct["_merge_open"](tree)


_INTEGRATE = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "mf-integrate"
    / "scripts"
    / "integrate.py"
)


@pytest.mark.slow
def test_case_m_the_settling_tests_stand_the_note_by_is_file(tmp_path: Path) -> None:
    conduct = _conduct()
    root, tree, run, _ = _merging(conduct, tmp_path)
    run.merge_in(tree, _CHANGE, "main")
    note = _folder(root) / "integrate.md"
    note.unlink()
    opened = conduct["_opened"](root, tree, _CHANGE)
    integrate = runpy.run_path(str(_INTEGRATE))
    settling = integrate["_settling"]
    nothing = (None, f"supervisor removed .minions/changes/{_CHANGE}/integrate.md")
    assert not settling(root, _CHANGE, tree)
    assert conduct["_settled"](root, tree, _CHANGE, opened) == nothing
    said = f".minions/changes/{_CHANGE}/integrate.md cannot be read: "
    for shape, stands in (
        ("file", True),
        ("empty", True),
        ("link", False),
        ("hard", True),
        ("dangling", False),
        ("folder", False),
        ("pipe", False),
    ):
        _plant(note, shape, "note\n")
        if stands:
            assert settling(root, _CHANGE, tree), shape
            reading = _within(lambda: conduct["_settled"](root, tree, _CHANGE, opened))
            assert reading == (None, ""), shape
        else:
            with pytest.raises(integrate["Stop"]) as halted:
                settling(root, _CHANGE, tree)
            assert halted.value.code == 1, shape
            assert str(halted.value).startswith(f"next: halt — {said}"), shape
            with pytest.raises(conduct["Stop"]) as stopped:
                _within(lambda: conduct["_settled"](root, tree, _CHANGE, opened))
            assert str(stopped.value).startswith(f"conduct: halt — {said}"), shape
        _clear(note)
    assert not settling(root, _CHANGE, None)


def test_case_n_build_notes_stop_the_version_on_a_wrong_shape(tmp_path: Path) -> None:
    conduct = _conduct()
    lines = halting(conduct, conduct["mflib"].marks.note_lines)
    mark = _folder(tmp_path) / "build-notes.md"
    plain = f".minions/changes/{_CHANGE}/build-notes.md"
    for shape, said in (
        ("link", "is a link"),
        ("dangling", "is a link"),
        ("hard", "is not a regular file of one name"),
        ("folder", "is not a regular file of one name"),
        ("pipe", "is not a regular file of one name"),
    ):
        _plant(mark, shape, "a\n")
        with pytest.raises(conduct["Stop"]) as stopped:
            _within(lambda: lines(tmp_path, _CHANGE))
        assert str(stopped.value) == f"conduct: halt — {plain} {said}", shape
        assert stopped.value.code == 1
        if shape == "folder":
            mark.rmdir()
        else:
            mark.unlink()


def test_case_n_build_notes_lines_are_counted_whole(tmp_path: Path) -> None:
    lines = _conduct()["mflib"].marks.note_lines
    assert lines(tmp_path, _CHANGE) == 0
    assert (tmp_path / ".minions" / "changes" / _CHANGE).is_dir()
    mark = _folder(tmp_path) / "build-notes.md"
    for text, count in (("", 0), ("one\ntwo", 2), ("one\r\ntwo\n\n", 3)):
        mark.write_text(text)
        assert lines(tmp_path, _CHANGE) == count, text
    mark.write_text("x\n" * (_BOUND * 2))
    assert lines(tmp_path, _CHANGE) == _BOUND * 2


def test_case_n_the_trim_keeps_the_lines_before_the_phase_and_its_allowance(
    tmp_path: Path,
) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    run = conduct["Run"](root, "claude")
    allowance = conduct["NOTES"]
    mark = _folder(root) / "build-notes.md"
    earlier = [f"earlier {n}\n" for n in range(5)]
    added = [f"added {n}\n" for n in range(allowance + 7)]
    mark.write_text("".join(earlier + added))

    run.trim_notes(_CHANGE, "2", len(earlier))
    kept = mark.read_text().splitlines(keepends=True)
    assert kept == earlier + added[:allowance]
    said = f"phase 2: kept {allowance} of {len(added)} lines"
    log = conduct["last_log"](root / ".minions" / "runs").read_text()
    assert f" · {_CHANGE} · notes — {said}" in log

    # Within the allowance, nothing is cut and nothing logged.
    run.trim_notes(_CHANGE, "3", len(earlier))
    assert mark.read_text().splitlines(keepends=True) == kept
    assert log == conduct["last_log"](root / ".minions" / "runs").read_text()

    # No file, no trim; a link stops the version.
    mark.unlink()
    run.trim_notes(_CHANGE, "3", 0)
    mark.symlink_to(tmp_path / "elsewhere.md")
    with pytest.raises(conduct["Stop"], match="is a link"):
        run.trim_notes(_CHANGE, "3", 0)


def _open_merge(root: Path, tree: Path) -> None:
    """Leave `main`'s move merged into `tree`, uncommitted."""
    _commit(root, {"main.txt": "x\n"}, "main moves")
    _git(tree, "merge", "-q", "--no-ff", "--no-commit", "main")


def test_case_r_the_red_head_is_the_first_on_a_line(tmp_path: Path) -> None:
    conduct = _conduct()
    red = conduct["_red"]
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    head = _git(tree, "rev-parse", "HEAD")
    mark = _folder(root) / "integrate.red"
    assert red(root, tree, _CHANGE) is None

    mark.write_text(f"gate red\n2026-11-05\nhead: {head[:7]}\n")
    assert red(root, tree, _CHANGE) == head
    mark.write_text(f"gate red\n2026-11-05\nhead: {head[:7]}\nhead: deadbeef\n")
    assert red(root, tree, _CHANGE) is None
    mark.write_text("head: abcdef1\n")
    assert red(root, tree, _CHANGE) == "abcdef1"
    mark.write_text("head: nocommit\n")
    assert red(root, tree, _CHANGE) is None
    mark.write_text("gate red\nno head here\n")
    assert red(root, tree, _CHANGE) is None
    mark.write_text(f"head:\n{head}\n")
    assert red(root, tree, _CHANGE) is None


def test_case_r_stage_of_reads_the_red_by_its_head(tmp_path: Path) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    head = _git(tree, "rev-parse", "HEAD")
    version = conduct["Version"](_CHANGE, tree)
    mark = _folder(root) / "integrate.red"
    note = f".minions/changes/{_CHANGE}/integrate"

    other = ("integrate", "red gate on another head: integrate gates again")
    mark.write_text(f"head: {head}\n")
    assert conduct["stage_of"](root, version) == (
        "integrating",
        f"red gate: {note}.red",
    )
    mark.write_text("head: abcdef1\n")
    assert conduct["stage_of"](root, version) == other
    # Outside a merge a red with no head is a red gate on another head.
    mark.write_text("gate red\n")
    assert conduct["stage_of"](root, version) == other

    # In an open merge a headed red is stale, a headless one is the merge's red gate,
    # and a folder halts the version.
    _open_merge(root, tree)
    resumes = (
        "integrate",
        "a merge is open and staged, with no note: integrate resumes",
    )
    mark.write_text(f"head: {head}\n")
    assert conduct["stage_of"](root, version) == resumes
    mark.write_text("gate red\n")
    assert conduct["stage_of"](root, version) == (
        "integrating",
        f"red gate: {note}.red",
    )
    mark.unlink()
    mark.mkdir()
    with pytest.raises(conduct["Stop"], match=r"integrate\.red cannot be read: "):
        conduct["stage_of"](root, version)


def test_case_s_stacked_on_names_a_full_head_alone(tmp_path: Path) -> None:
    standing = _conduct()["_stacked_on"]
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    head = _git(tree, "rev-parse", "HEAD")
    mark = _folder(root) / "stacked-on"

    def read(text: str, unreleased: tuple[str, ...] = ()) -> str | None:
        mark.write_text(text)
        return standing(root, _CHANGE, tree, list(unreleased))

    assert standing(root, _CHANGE, tree, []) is None
    assert read(f"{head}\n") == head
    assert read(f"{head} and more\nlines\n") == head
    for refused in ("", "\n", head[:7], head[:39], head.upper(), f"x{head}", "0" * 40):
        assert read(refused) is None, refused

    # An ancestor of `HEAD` alone, holding each unreleased dependency's tasks file.
    _commit(root, {"main.txt": "x\n"}, "main moves")
    assert read(f"{_git(root, 'rev-parse', 'main')}\n") is None
    assert read(f"{head}\n", (_CHANGE,)) == head
    assert read(f"{head}\n", ("0009-gone",)) is None


def test_case_s_unstack_removes_what_stands_at_the_name(tmp_path: Path) -> None:
    unstack = _conduct()["_unstack"]
    mark = _folder(tmp_path) / "stacked-on"
    unstack(tmp_path, _CHANGE)
    for shape in ("dangling", "file", "link", "hard", "pipe"):
        _plant(mark, shape, "x\n")
        unstack(tmp_path, _CHANGE)
        assert not os.path.lexists(mark), shape


def test_case_s_stack_writes_the_head_and_a_newline_before_it_merges(
    tmp_path: Path,
) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    run = conduct["Run"](root, "claude")
    mark = _folder(root) / "stacked-on"
    seen: list[tuple[str, tuple[Any, ...]]] = []

    def merge_in(*given: Any) -> None:  # noqa: ANN401
        seen.append((mark.read_text(), given))

    run.merge_in = merge_in
    _git(root, "switch", "-q", "-c", "dependency")
    _commit(root, {"dependency.txt": "x\n"}, "the dependency's build")
    head = _git(root, "rev-parse", "HEAD")
    _git(root, "switch", "-q", "main")

    run.stack(tree, _CHANGE, "0000-dep", head)
    assert seen == [(f"{head}\n", (tree, _CHANGE, head, "0000-dep"))]
    log = conduct["last_log"](root / ".minions" / "runs").read_text()
    assert f" · {_CHANGE} · stacked — on 0000-dep at {head[:7]}" in log

    # A head already in `HEAD` is written and merges nothing.
    built = _git(tree, "rev-parse", "HEAD")
    run.stack(tree, _CHANGE, "0000-dep", built)
    assert mark.read_text() == f"{built}\n"
    assert len(seen) == 1


def test_case_s_catch_up_passes_a_stacked_version(tmp_path: Path) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    built = _git(tree, "rev-parse", "HEAD")
    _commit(root, {"main.txt": "x\n"}, "main moves")
    run = conduct["Run"](root, "claude")
    merged: list[tuple[Any, ...]] = []

    def merge_in(*given: Any) -> None:  # noqa: ANN401
        merged.append(given)

    run.merge_in = merge_in
    version = conduct["Version"](_CHANGE, tree)
    mark = _folder(root) / "stacked-on"
    mark.write_text(f"{built}\n")
    run.catch_up(version)
    assert merged == []
    mark.unlink()
    run.catch_up(version)
    assert merged == [(tree, _CHANGE, "main")]


def test_case_t_mtime_is_the_lstat_time_of_a_regular_file_alone(
    tmp_path: Path,
) -> None:
    marks = _conduct()["mflib"].marks

    def mtime(path: Path) -> int | None:
        return marks.mtime(tmp_path, _CHANGE, path.name)

    mark = _folder(tmp_path) / "integrate.settled"
    assert mtime(mark) is None
    for shape in ("file", "empty", "hard"):
        _plant(mark, shape, "x\n")
        assert mtime(mark) == mark.lstat().st_mtime_ns, shape
        mark.unlink()
    for shape in ("link", "dangling", "pipe", "folder"):
        _plant(mark, shape, "x\n")
        assert _within(lambda: mtime(mark)) is None, shape
        if shape == "folder":
            mark.rmdir()
        else:
            mark.unlink()


@pytest.mark.slow
def test_case_t_opened_keeps_the_settled_time_and_settled_passes_a_new_one(
    tmp_path: Path,
) -> None:
    conduct = _conduct()
    root, tree, run, _ = _merging(conduct, tmp_path)
    run.merge_in(tree, _CHANGE, "main")
    marks = _folder(root)
    settled = marks / "integrate.settled"

    opened = conduct["_opened"](root, tree, _CHANGE)
    assert opened.written is None
    assert opened.head == _git(tree, "rev-parse", "HEAD")
    assert conduct["_settled"](root, tree, _CHANGE, opened) == (None, "")

    settled.write_text("settled\n")
    before = settled.lstat().st_mtime_ns
    held = conduct["_opened"](root, tree, _CHANGE)
    assert held.written == before
    assert conduct["_settled"](root, tree, _CHANGE, held) == (None, "")
    os.utime(settled, ns=(before + 10**9, before + 10**9))
    staged = _git(tree, "write-tree")
    assert conduct["_settled"](root, tree, _CHANGE, held) == (staged, "")

    # A link at the mark has no time, so no settle.
    settled.unlink()
    _plant(settled, "link", "settled\n")
    assert conduct["_settled"](root, tree, _CHANGE, held) == (None, "")


def _rescued(tmp_path: Path, plant: Callable[[Path], None], after: str) -> Any:  # noqa: ANN401
    """Run a rescue whose worker does `after` to `rescue.md`; return the `Run`."""
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [ ] 1 — One\n")
    run = conduct["Run"](root, "claude")
    mark = _folder(root) / "rescue.md"
    plant(mark)
    written = mark.lstat().st_mtime_ns if mark.is_file() else 0

    def spawn(*_: Any, **__: Any) -> list[str]:  # noqa: ANN401
        if after == "rewrite":
            mark.write_text("a diagnosis\n")
            os.utime(mark, ns=(written + 10**9, written + 10**9))
        return []

    run.planned_models = lambda change, station: ("model", None, None)
    run.spawn = spawn
    run.rescue(conduct["Version"](_CHANGE, tree), "integrating", ())
    return run


@pytest.mark.slow
def test_case_t_the_rescue_compares_the_time_of_rescue_md(tmp_path: Path) -> None:
    name = f".minions/changes/{_CHANGE}/rescue.md"

    def old(mark: Path) -> None:
        mark.write_text("an older diagnosis\n")

    def none(mark: Path) -> None:
        return None

    for plant in (old, none):
        run = _rescued(tmp_path / plant.__name__, plant, "rewrite")
        assert run.halts[0] == (_CHANGE, f"rescue diagnosed — {name}")
        assert run.diagnosed == {_CHANGE}
    run = _rescued(tmp_path / "left", old, "leave")
    assert run.halts[0] == (_CHANGE, "rescue wrote no amend and no diagnosis")
    assert run.diagnosed == set()

    def link(mark: Path) -> None:
        _plant(mark, "link", "a diagnosis\n")

    run = _rescued(tmp_path / "linked", link, "leave")
    assert run.halts[0] == (_CHANGE, "rescue wrote no amend and no diagnosis")


def test_case_w_the_in_place_write_truncates_and_makes_the_folder(
    tmp_path: Path,
) -> None:
    write = _conduct()["mflib"].marks.write
    umask = os.umask(0o022)
    try:
        write(tmp_path, _CHANGE, "mark", "a longer first text\n")
    finally:
        os.umask(umask)
    mark = tmp_path / ".minions" / "changes" / _CHANGE / "mark"
    assert mark.read_text() == "a longer first text\n"
    assert mark.stat().st_mode & 0o777 == 0o644
    write(tmp_path, _CHANGE, "mark", "short\n")
    assert mark.read_text() == "short\n"


def test_case_w_the_in_place_write_refuses_a_link_and_a_folder(tmp_path: Path) -> None:
    marks = _conduct()["mflib"].marks
    write = marks.write
    mark = _folder(tmp_path) / "mark"
    outside = tmp_path / "outside"
    outside.write_text("the person's\n")
    mark.symlink_to(outside)
    with pytest.raises(marks.Unwritten, match="symbolic links") as linked:
        write(tmp_path, _CHANGE, "mark", "x\n")
    assert linked.value.cause.errno == errno.ELOOP
    assert outside.read_text() == "the person's\n"
    mark.unlink()
    mark.mkdir()
    with pytest.raises(marks.Unwritten, match=r"^mark cannot be written: "):
        write(tmp_path, _CHANGE, "mark", "x\n")
    assert mark.is_dir()

    # A link at the change's folder is refused as well.
    other = tmp_path / "other"
    (other / ".minions" / "changes").mkdir(parents=True)
    aside = other / ".minions" / "changes" / "0002-aside"
    aside.mkdir()
    (other / ".minions" / "changes" / "0003-linked").symlink_to(aside)
    with pytest.raises(marks.Unwritten) as refused:
        write(other, "0003-linked", "mark", "x\n")
    assert refused.value.cause.errno in (errno.ELOOP, errno.ENOTDIR)
    assert not (aside / "mark").exists()


def test_case_w_unstack_raises_on_a_folder(tmp_path: Path) -> None:
    (_folder(tmp_path) / "stacked-on").mkdir()
    with pytest.raises(OSError):  # noqa: PT011
        _conduct()["_unstack"](tmp_path, _CHANGE)


def _simplified(tmp_path: Path, shape: str, text: str = "head: abc1234\n") -> Any:  # noqa: ANN401
    """Plant `build.simplified` as `shape`; return `simplified_head`, none blocking."""
    mark = _folder(tmp_path) / "build.simplified"
    if mark.is_dir() and not mark.is_symlink():
        mark.rmdir()
    else:
        mark.unlink(missing_ok=True)
    _plant(mark, shape, text)
    reader = _conduct()["mflib"].marks.simplified_head
    return _within(lambda: reader(tmp_path, _CHANGE))


def test_case_x_the_simplified_head_is_the_first_word_after_a_head_key(
    tmp_path: Path,
) -> None:
    assert _simplified(tmp_path, "file") == "abc1234"
    assert _simplified(tmp_path, "file", "note\nhead: abc1234\n") == "abc1234"
    assert _simplified(tmp_path, "file", "note\nhead: abc1234\nhead: z\n") is None
    assert _simplified(tmp_path, "file", "head:\nabc1234\n") is None
    assert _simplified(tmp_path, "file", "head:\n\nhead: z\n") is None
    for text in ("head:\n", "head:   \n", "note\n", ""):
        assert _simplified(tmp_path, "file", text) is None, text
    assert _simplified(tmp_path, "empty") is None
    assert _simplified(tmp_path, "binary") is None


def test_case_x_the_simplified_reader_follows_a_link_and_reads_a_file_whole(
    tmp_path: Path,
) -> None:
    assert _simplified(tmp_path, "hard") == "abc1234"
    for shape in ("link", "dangling", "folder", "pipe"):
        assert _simplified(tmp_path, shape) is None, shape
    assert _simplified(tmp_path, "file", "z\n" * _BOUND + "head: abc1234\n") is None


def test_case_x_the_simplified_writer_writes_a_head_and_a_newline_alone(
    tmp_path: Path,
) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    mark = _folder(root) / "build.simplified"
    conduct["_mark_simplified"](root, _CHANGE, tree)
    assert mark.read_text() == f"head: {_git(tree, 'rev-parse', 'HEAD')}\n"

    for shape in ("link", "folder"):
        mark.unlink() if mark.is_file() or mark.is_symlink() else mark.rmdir()
        _plant(mark, shape)
        with pytest.raises(conduct["Stop"]) as stopped:
            conduct["_mark_simplified"](root, _CHANGE, tree)
        assert stopped.value.code == 1, shape
        said = f"conduct: halt — .minions/changes/{_CHANGE}/build.simplified cannot be"
        assert str(stopped.value).startswith(said), shape


def _amends(root: Path, tree: Path, text: str) -> bool:
    """Plant `build.simplified` as `text`; return `_amended_since_simplify`."""
    (_folder(root) / "build.simplified").write_text(text)
    return _conduct()["_amended_since_simplify"](root, _CHANGE, tree)


@pytest.mark.slow
def test_case_x_the_amends_test_passes_amends_of_the_change_directory_alone(
    tmp_path: Path,
) -> None:
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    head = _git(tree, "rev-parse", "HEAD")
    folder = f"openspec/changes/{_CHANGE}"
    note = {f"{folder}/tasks.md": "## Progress\n\n- [x] 1 — One\n\nA note.\n"}
    assert _amends(root, tree, f"head: {head}\n")

    # An amend passes; the subject that only begins as it, a folder that only begins
    # as the change's and a path outside the folder each fail.
    for files, subject, passes in (
        (note, _AMEND, True),
        (note, f"{_AMEND} and more", False),
        ({f"{folder}-extra/a.md": "x\n"}, _AMEND, False),
        ({"x.txt": "x\n"}, _AMEND, False),
        ({**note, "x.txt": "x\n"}, _AMEND, False),
    ):
        _commit(tree, files, subject)
        assert _amends(root, tree, f"head: {head}\n") is passes, (files, subject)
        _git(tree, "reset", "-q", "--hard", head)

    # A merge or an octopus whose own subject is the amend subject fails.
    first = _side(tree, "side-one", f"{folder}/design.md")
    second = _side(tree, "side-two", f"{folder}/tasks.md")
    _git(tree, "merge", "-q", "--no-ff", "-m", _AMEND, first)
    assert not _amends(root, tree, f"head: {head}\n")
    _git(tree, "reset", "-q", "--hard", head)
    _git(tree, "merge", "-q", "--no-ff", "-m", _AMEND, first, second)
    assert not _amends(root, tree, f"head: {head}\n")


@pytest.mark.slow
def test_case_x_the_amends_test_resolves_the_head_it_names(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    _git(tree, "tag", "-a", "-m", "simplified", "simplified-tag")
    _commit(root, {"main.txt": "x\n"}, "main moves")
    off_branch = _git(root, "rev-parse", "main")
    short = _git(tree, "rev-parse", "HEAD")[:7]
    assert _amends(root, tree, f"head: {short}\n")
    for word in ("HEAD", _CHANGE, "simplified-tag"):
        assert not _amends(root, tree, f"head: {word}\n"), word
    for word in ("main", off_branch, "nocommit", ""):
        assert not _amends(root, tree, f"head: {word}\n"), word


_CONVERGE = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "mf-converge"
    / "scripts"
    / "converge.py"
)
_KEPT = "base: base1\nout line\n"
_H1 = "abc1234"


def _planned(
    tmp_path: Path, plan: Callable[[Path], None], done: str | None = None
) -> str:
    """Return converge's plan output for `HEAD` `_H1`, `plan` planting the kept file."""
    converge = runpy.run_path(str(_CONVERGE))
    fresh = lambda context, argv: (0, "fresh run\n")  # noqa: E731
    converge["_plan_output"].__globals__["_captured"] = fresh
    host = types.SimpleNamespace(primary=str(tmp_path))
    context = converge["Context"](host, _CHANGE, tmp_path, {}, 1e12)
    context.base = "base1"
    folder = _folder(tmp_path)
    (folder / "build.done").write_text(done or f"head: {_H1}\nsimplify: none\n")
    plan(folder / "plan-check.txt")
    return _within(lambda: converge["_plan_output"](context, _H1))


def test_case_p_converge_keeps_the_close_s_plan_check_of_a_regular_file(
    tmp_path: Path,
) -> None:
    for shape in ("file", "hard"):
        kept = _planned(tmp_path / shape, lambda mark, s=shape: _plant(mark, s, _KEPT))
        assert kept == "out line\n", shape
    for shape in ("link", "dangling", "folder", "pipe"):
        fresh = _planned(tmp_path / shape, lambda mark, s=shape: _plant(mark, s, _KEPT))
        assert fresh == "fresh run\n", shape

    def bad(mark: Path) -> None:
        mark.write_bytes(b"base: base1\nout \xff\n")

    assert _planned(tmp_path / "bad", bad) == "fresh run\n"
    big = "x" * (_BOUND + 10)
    whole = _planned(
        tmp_path / "big", lambda mark: _plant(mark, "file", f"base: base1\n{big}\n")
    )
    assert whole == f"{big}\n"
    over = "x" * (1048576 + 10)
    fresh = _planned(
        tmp_path / "over", lambda mark: _plant(mark, "file", f"base: base1\n{over}\n")
    )
    assert fresh == "fresh run\n"


def test_case_p_converge_reads_build_done_for_a_head_line(tmp_path: Path) -> None:
    def kept(mark: Path) -> None:
        _plant(mark, "file", _KEPT)

    heads = (
        (f"head: other\nhead: {_H1}\n", "fresh run\n"),
        (f"head: {_H1} \n", "out line\n"),
        (f"head: {_H1}\n\xff\n", "out line\n"),
        ("simplify: none\n", "fresh run\n"),
    )
    for n, (text, expected) in enumerate(heads):
        assert _planned(tmp_path / str(n), kept, text) == expected, text

    # A `build.done` that is a link names no head.
    folder = _folder(tmp_path / "linked")
    other = folder.parent / ".other"
    other.write_text("head: H1\n")
    converge = runpy.run_path(str(_CONVERGE))
    for shape in ("link", "folder", "pipe"):
        mark = folder / "build.done"
        mark.unlink(missing_ok=True)
        _plant(mark, shape, "head: H1\n")
        assert _within(lambda m=mark: converge["_read"](m)) == "", shape
        if shape == "folder":
            mark.rmdir()


def test_case_p_the_converge_text_reader_refuses_a_link_a_folder_and_a_pipe(
    tmp_path: Path,
) -> None:
    text = runpy.run_path(str(_CONVERGE))["_text"]
    mark = _folder(tmp_path) / "plan-check.txt"
    assert text(mark) is None
    mark.write_bytes(b"a\xffb\n")
    assert text(mark) == "a�b\n"
    mark.unlink()
    for shape, code in (
        ("link", errno.ELOOP),
        ("folder", errno.EINVAL),
        ("pipe", errno.EINVAL),
    ):
        _plant(mark, shape, "x\n")
        with pytest.raises(OSError) as refused:  # noqa: PT011
            _within(lambda: text(mark))
        assert refused.value.errno == code, shape
        if shape == "folder":
            mark.rmdir()
        else:
            mark.unlink()


def _gated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    plant: Callable[[Path], None] | None,
) -> tuple[str | None, bool, int]:
    """Run `_close_gate` over a simplify commit; return its evidence, drop and runs.

    The gate's first run is red and plants `gate.red` as `plant` says; `None` is green.
    """
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    simplify = f"refactor({_CHANGE}): simplify"
    _commit(tree, {"simplified.txt": "x\n"}, simplify)
    tip = _git(tree, "rev-parse", "HEAD")
    mark = _folder(root) / "gate.red"
    runs: list[int] = []

    def gate(
        _: Path, __: str, ___: Path, ____: Callable[[str], None] = print
    ) -> str | None:
        runs.append(1)
        mark.unlink(missing_ok=True)
        if len(runs) == 1 and plant is not None:
            plant(mark)
            return "red"
        return None

    monkeypatch.setitem(conduct["_close_gate"].__globals__, "_run_gate", gate)
    said: list[str] = []
    evidence = conduct["_close_gate"](root, _CHANGE, tree, said.append)
    dropped = _git(tree, "rev-parse", "HEAD") != tip
    assert dropped == ("reset — simplify dropped" in said)
    return evidence, dropped, len(runs)


@pytest.mark.slow
def test_case_a_a_red_gate_drops_the_simplify_commit_but_for_a_fault_not_its_own(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def text(says: str) -> Callable[[Path], None]:
        def plant(mark: Path) -> None:
            mark.write_text(says)

        return plant

    def binary(mark: Path) -> None:
        mark.write_bytes(b"past its limit \xff\n")

    def link(mark: Path) -> None:
        _plant(mark, "link", "past its limit\n")

    def big(mark: Path) -> None:
        mark.write_text("z" * (1048576 + 10) + "\npast its limit\n")

    cases = (
        ("limit", text("boom — past its limit\n"), True),
        ("sandbox", text("git: sandboxed: denied\n"), True),
        ("near", text("past it limit\nsandbox: denied\n"), False),
        ("bad byte", binary, False),
        ("link", link, False),
        ("big", big, False),
        ("dangling", lambda mark: _plant(mark, "dangling"), False),
    )
    for name, plant, kept in cases:
        evidence, dropped, runs = _gated(tmp_path / name, monkeypatch, plant)
        assert dropped is not kept, name
        assert (evidence, runs) == (("red", 1) if kept else (None, 2)), name
    assert _gated(tmp_path / "green", monkeypatch, None) == (None, False, 1)


def test_case_a_a_red_gate_keeps_the_whole_output_and_a_green_one_removes_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    mark = _folder(root) / "gate.red"
    codes = iter([2, 0])
    output = "x" * 200000 + "\nthe last line\n"

    def boxed(primary: Path, where: Path, argv_: list[str]) -> tuple[int, str]:
        return next(codes), output

    monkeypatch.setitem(conduct["_run_gate"].__globals__, "_boxed", boxed)
    red = conduct["_run_gate"](root, _CHANGE, tree, lambda line: None)
    assert red == f"red · gate_run.py exit 2 · .minions/changes/{_CHANGE}/gate.red"
    assert mark.read_text() == output
    assert conduct["_run_gate"](root, _CHANGE, tree, lambda line: None) is None
    assert not mark.exists()


def _supervised(
    tmp_path: Path, plant: Callable[[Path], None] | None, design: bool
) -> list[str]:
    """Return the prompts of the supervisor a capped halt starts, `plant` the mark."""
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    run = conduct["Run"](root, "claude")
    prompts: list[str] = []

    def spawn(
        change: str, station: str, where: Path, prompt: str, models: object, **_: object
    ) -> None:
        prompts.append(prompt)

    conduct["_security_held"].__globals__["_read_cards"] = lambda *_: []
    run.decides.add(_CHANGE)
    run.design_cap = lambda change, halt: design
    run.planned_models = lambda change, station: ("model", None, None)
    run.spawn = spawn
    if plant is not None:
        plant(_folder(root) / "replan.mark")
    run.supervise(conduct["Version"](_CHANGE, tree), "converge-halted", True)
    return prompts


@pytest.mark.slow
def test_case_l_a_standing_replan_mark_stops_a_design_cap_alone(tmp_path: Path) -> None:
    [prompt] = _supervised(tmp_path / "none", None, True)
    assert "replan=yes" in prompt
    for shape in ("file", "empty", "link", "dangling", "folder", "pipe"):
        prompts = _supervised(
            tmp_path / shape, lambda mark, s=shape: _plant(mark, s, "head: abc\n"), True
        )
        assert prompts == [], shape

    # A cap that is no design cap is no cap of the mark's.
    [plain] = _supervised(
        tmp_path / "plain", lambda mark: _plant(mark, "file", "head: abc\n"), False
    )
    assert "replan=yes" not in plain


def _descriptors() -> int:
    """Return how many descriptors this process holds open."""
    return len(os.listdir("/dev/fd"))


def test_case_b_the_in_place_write_goes_through_a_hard_link(tmp_path: Path) -> None:
    marks = _conduct()["mflib"].marks
    write = marks.write
    mark = _folder(tmp_path) / "mark"
    _plant(mark, "hard", "first, and longer\n")
    other = mark.parent.parent / ".other-mark"
    held = _descriptors()
    write(tmp_path, _CHANGE, "mark", "second\n")
    assert other.read_text() == "first, and longer\n"
    assert mark.read_text() == "second\n"
    assert _descriptors() == held

    # A refused write leaves no descriptor open either; a folder is the caller's stop.
    mark.unlink()
    _plant(mark, "link")
    with pytest.raises(marks.Unwritten):
        write(tmp_path, _CHANGE, "mark", "x\n")
    mark.unlink()
    mark.mkdir()
    with pytest.raises(marks.Unwritten):
        write(tmp_path, _CHANGE, "mark", "x\n")
    assert _descriptors() == held


def test_case_b_the_remover_takes_a_name_and_nothing_else(tmp_path: Path) -> None:
    remove = _conduct()["_remove_in"]
    runs = tmp_path / ".minions"
    mark = _folder(tmp_path) / "mark"
    remove(runs, layout.CHANGES, _CHANGE, name="mark")
    for shape in ("file", "link", "hard", "pipe", "dangling"):
        _plant(mark, shape, "kept\n")
        remove(runs, layout.CHANGES, _CHANGE, name="mark")
        assert not os.path.lexists(mark), shape
    other = mark.parent.parent / ".other-mark"
    assert other.read_text() == "kept\n"

    mark.mkdir()
    with pytest.raises(OSError):  # noqa: PT011
        remove(runs, layout.CHANGES, _CHANGE, name="mark")
    aside = tmp_path / "aside"
    aside.mkdir()
    (aside / "mark").write_text("kept\n")
    (runs / layout.CHANGES / "0003-linked").symlink_to(aside)
    with pytest.raises(OSError):  # noqa: PT011
        remove(runs, layout.CHANGES, "0003-linked", name="mark")
    assert (aside / "mark").read_text() == "kept\n"


def test_case_b_write_state_stages_a_file_and_stops_with_code_1(tmp_path: Path) -> None:
    conduct = _conduct()
    write = conduct["_write_state"]
    marks = _folder(tmp_path)
    umask = os.umask(0o022)
    try:
        write(tmp_path, _CHANGE, "mark", "text\n")
    finally:
        os.umask(umask)
    assert (marks / "mark").read_text() == "text\n"
    assert (marks / "mark").stat().st_mode & 0o777 == 0o644
    assert sorted(path.name for path in marks.iterdir()) == ["mark"]

    # A hard link at the name keeps the other name's text.
    (marks / "mark").unlink()
    _plant(marks / "mark", "hard", "the other's\n")
    write(tmp_path, _CHANGE, "mark", "new\n")
    assert (marks.parent / ".other-mark").read_text() == "the other's\n"
    assert (marks / "mark").read_text() == "new\n"

    aside = tmp_path / "aside"
    aside.mkdir()
    (marks.parent / "0003-linked").symlink_to(aside)
    for change, shape in ((_CHANGE, "link"), (_CHANGE, "folder"), ("0003-linked", "")):
        if shape:
            (marks / "mark").unlink()
            _plant(marks / "mark", shape)
        with pytest.raises(conduct["Stop"]) as stopped:
            write(tmp_path, change, "mark", "x\n")
        assert stopped.value.code == 1, (change, shape)
        said = f"conduct: halt — .minions/changes/{change}/mark cannot be written: "
        assert str(stopped.value).startswith(said), (change, shape)
        if shape == "folder":
            (marks / "mark").rmdir()
    assert not (aside / "mark").exists()
    assert not (aside / "mark.tmp").exists()


def _driven(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    progress: str,
    stages: list[tuple[str, str]],
    stop_at: tuple[str, ...],
    spawned: Callable[[Path, Path, str, str | None], None] | None = None,
    before: Callable[[Path, Path], None] | None = None,
) -> tuple[Path, Path, list[str], str | None]:
    """Run `advance` over scripted stages with no worker; return what it did.

    Return the primary, the tree, the calls in order and `advance`'s answer. A spawn
    runs `spawned(root, tree, stage, phase)`; every call notes `stacked-on`.
    """
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, progress)
    marks = _folder(root)
    (marks / "stacked-on").write_text(f"{_git(tree, 'rev-parse', 'HEAD')}\n")
    if before is not None:
        before(root, tree)
    run = conduct["Run"](root, "claude")
    calls: list[str] = []
    script = iter(stages)

    def note(what: str) -> None:
        stacked = "stacked" if (marks / "stacked-on").exists() else "unstacked"
        calls.append(f"{what} · {stacked}")

    def spawn(
        change: str,
        stage: str,
        where: Path,
        prompt: str,
        models: object,
        phase: str | None = None,
    ) -> list[str]:
        note(f"spawn {stage} {phase}")
        if spawned is not None:
            spawned(root, tree, stage, phase)
        return []

    def conducted(*_: Any) -> list[str]:  # noqa: ANN401
        note("conducted")
        return []

    def released_by(*_: Any) -> str:  # noqa: ANN401
        note("released_by")
        return ""

    def close_build(*_: Any, **__: Any) -> None:  # noqa: ANN401
        note("close")

    monkeypatch.setitem(
        conduct["Run"].advance.__globals__, "check", lambda *_, **__: None
    )
    run.stage = lambda version: next(script)
    run.planned_models = lambda change, station: ("model", None, None)
    run.workers = lambda change: {}
    run.spawn = spawn
    run.conducted = conducted
    run.released_by = released_by
    run.gate_built = lambda version, where, models: (True, None)
    run.quick_built = lambda version, where, phase: None
    run.close_build = close_build
    answer = run.advance(conduct["Version"](_CHANGE, tree), stop_at)
    assert run.halts == [], run.halts
    return root, tree, calls, answer


def test_loop_advance_removes_stacked_on_before_converge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stages = [("converge", "unfinished"), ("release", "clean")]
    _, _, calls, answer = _driven(
        tmp_path, monkeypatch, "- [x] 1 — One\n", stages, ("release",)
    )
    assert answer == "release"
    assert calls == ["conducted · unstacked"]


def test_loop_advance_removes_stacked_on_before_the_release(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, _, calls, answer = _driven(
        tmp_path, monkeypatch, "- [x] 1 — One\n", [("release", "clean")], ()
    )
    assert answer is None
    assert calls == ["released_by · unstacked"]


def _ticked(root: Path, tree: Path, stage: str, phase: str | None, done: bool) -> None:
    """Tick the box on phase 1's spawn; a closed build also marks `build.done`."""
    if phase != "phase 1":
        return
    tasks = f"openspec/changes/{_CHANGE}/tasks.md"
    _commit(tree, {tasks: "## Progress\n\n- [x] 1 — One\n"}, "build: phase 1")
    if done:
        head = _git(tree, "rev-parse", "HEAD")
        (_folder(root) / "build.done").write_text(f"head: {head}\n")


@pytest.mark.slow
def test_loop_a_closed_build_is_not_closed_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stages = [("build", "phase 1 unticked"), ("converge", "unfinished")]

    def closed(root: Path, tree: Path, stage: str, phase: str | None) -> None:
        _ticked(root, tree, stage, phase, True)

    _, _, calls, answer = _driven(
        tmp_path / "closed",
        monkeypatch,
        "- [ ] 1 — One\n",
        stages,
        ("converge",),
        closed,
    )
    assert answer == "converge"
    assert calls == ["spawn build phase 1 · stacked"]


@pytest.mark.slow
def test_loop_an_open_build_is_closed_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stages = [("build", "phase 1 unticked"), ("converge", "unfinished")]

    def open_(root: Path, tree: Path, stage: str, phase: str | None) -> None:
        _ticked(root, tree, stage, phase, False)

    _, _, calls, answer = _driven(
        tmp_path / "open", monkeypatch, "- [ ] 1 — One\n", stages, ("converge",), open_
    )
    assert answer == "converge"
    assert calls == [
        "spawn build phase 1 · stacked",
        "spawn build close · stacked",
        "close · stacked",
    ]


def test_case_b_the_build_spawn_finds_the_last_builds_halt_gone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[bool] = []

    def before(root: Path, tree: Path) -> None:
        text = "sub-task: 1.1\nstop: 3\nhead: abc1234\n"
        (_folder(root) / "build.halt").write_text(text)

    def spawned(root: Path, tree: Path, stage: str, phase: str | None) -> None:
        seen.append((_folder(root) / "build.halt").exists())

    stages = [("build", "phase 1 unticked"), ("converge", "unfinished")]
    answer = _driven(
        tmp_path, monkeypatch, "- [ ] 1 — One\n", stages, ("converge",), spawned, before
    )[3]
    assert answer == "converge"
    assert seen == [False]


def test_case_b_the_repair_spawn_finds_the_last_builds_halt_gone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    marks = _folder(root)
    (marks / "build.halt").write_text("sub-task: close\nstop: gate\nhead: abc1234\n")
    run = conduct["Run"](root, "claude")
    seen: list[bool] = []
    reds = iter(["red", None])

    def spawn(*_: Any, **__: Any) -> list[str]:  # noqa: ANN401
        seen.append((marks / "build.halt").exists())
        return []

    monkeypatch.setitem(
        conduct["Run"].gate_built.__globals__, "_run_gate", lambda *_: next(reds)
    )
    run.spawn = spawn
    version = conduct["Version"](_CHANGE, tree)
    assert run.gate_built(version, tree, ("model", None, None)) == (True, None)
    assert seen == [False]
    assert not (marks / "build.halt").exists()


@pytest.fixture
def repo(request: pytest.FixtureRequest) -> Repo:
    """Return `test_release.py`'s project, a version branch and fake gates."""
    return request.getfixturevalue("_release_repo")


_WHOLE = "tag: v0.2.0\nversion: v0.2\ngate: 41\nhead: abc1234\n"
_KEYS = {"tag": "v0.2.0", "version": "v0.2", "gate": "41", "head": "abc1234"}


def _pre(repo: Repo) -> Path:
    """Return the release mark's path, its folder made."""
    repo.run_folder.mkdir(parents=True, exist_ok=True)
    return repo.run_folder / "release.pre"


def test_case_e_the_release_mark_reader_takes_keys_as_it_does(repo: Repo) -> None:
    read = repo.ns._read_mark
    mark = _pre(repo)
    mark.write_text(_WHOLE)
    assert read(repo.root, _CHANGE, "gone") == _KEYS

    # Key and value are stripped, the first colon splits, a colonless line is no key.
    mark.write_text(" tag : v0.2.0 \nversion: v0.2:x\ngate:41\nhead:abc1234 \nnote\n")
    assert read(repo.root, _CHANGE, "gone") == {**_KEYS, "version": "v0.2:x"}

    # Two heads, a bad byte and a mark over the bound are the caller's stop.
    cannot = "release: cannot run — release.pre "
    long = "a" * (_BOUND + 10)
    for text, said in (
        ((_WHOLE + "head: def5678\n").encode(), "has no head:"),
        (_WHOLE.encode() + b"a note \xff\n", "cannot be read: it is not UTF-8"),
        ((_WHOLE + f"note: {long}\n").encode(), "cannot be read: it is over 65536"),
    ):
        mark.write_bytes(text)
        with pytest.raises(repo.ns.Stop) as stopped:
            read(repo.root, _CHANGE, "gone")
        assert stopped.value.code == 2, said
        assert str(stopped.value).startswith(f"{cannot}{said}"), said


def test_case_e_a_missing_or_malformed_release_mark_is_a_stop(repo: Repo) -> None:
    read = repo.ns._read_mark
    mark = _pre(repo)
    with pytest.raises(repo.ns.Stop) as missing:
        read(repo.root, _CHANGE, "gone")
    assert (missing.value.code, str(missing.value)) == (1, "release: halt — gone")
    cannot = "release: cannot run — release.pre "
    for text, said in (
        ("", "has no tag:"),
        (_WHOLE.replace("tag: v0.2.0\n", "tag:\n"), "has no tag:"),
        (_WHOLE.replace("gate: 41\n", ""), "has no gate:"),
        (_WHOLE.replace("head: abc1234\n", "note\n"), "has no head:"),
        (_WHOLE.replace("v0.2.0", "2"), "holds no tag or gate seconds"),
        (_WHOLE.replace("41", "x"), "holds no tag or gate seconds"),
    ):
        mark.write_text(text)
        with pytest.raises(repo.ns.Stop) as stopped:
            read(repo.root, _CHANGE, "gone")
        assert stopped.value.code == 2, text
        assert str(stopped.value) == f"{cannot}{said}", text


def test_case_e_a_link_a_folder_and_a_pipe_cannot_be_read(repo: Repo) -> None:
    read = repo.ns._read_mark
    mark = _pre(repo)
    for shape in ("link", "folder", "pipe"):
        _plant(mark, shape, _WHOLE)
        with pytest.raises(repo.ns.Stop) as stopped:
            _within(lambda: read(repo.root, _CHANGE, "gone"))
        assert stopped.value.code == 2, shape
        assert str(stopped.value).startswith(
            "release: cannot run — release.pre cannot be read: "
        ), shape
        if shape == "folder":
            mark.rmdir()
        else:
            mark.unlink()


_FLAG = (
    f"release: halt — .minions/changes/{_CHANGE}/release.flag stands"
    " — read the prose it names, then merge"
)


@pytest.mark.slow
def test_case_e_finish_and_merge_halt_on_a_flag_of_any_shape(repo: Repo) -> None:
    _cut_release(repo)
    flag = repo.run_folder / "release.flag"
    before = repo.git("rev-parse", "main").strip()
    for shape in ("file", "empty", "link", "dangling", "folder", "pipe"):
        _plant(flag, shape, "README.md states v0.1\n")
        code, lines = repo.finish()
        assert (code, lines[-1]) == (1, _FLAG), shape
        assert _merge(repo)[1][-1] == _FLAG, shape
        assert repo.git("rev-parse", "main").strip() == before, shape
        if shape == "folder":
            flag.rmdir()
        else:
            flag.unlink()


@pytest.mark.slow
def test_case_e_a_release_subject_with_more_after_it_is_no_release_commit(
    repo: Repo,
) -> None:
    repo.ready()
    _forged(repo, "notes.md", "chore(release): v0.2.0 and more")
    code, lines = repo.finish()
    assert code == 1
    assert lines[-1].startswith("release: halt — release.pre: head ")
    assert repo.git("tag", "--list", "v0.2.0") == ""


@pytest.mark.slow
def test_case_e_a_drop_with_no_flag_removes_the_mark(repo: Repo) -> None:
    _cut_release(repo)
    _moved(repo)
    assert not (repo.run_folder / "release.flag").exists()
    code, lines = repo.pre("--origin", "free")
    assert (code, lines[-1]) == (0, "release: drop — v0.2.0 and its commit")
    assert not (repo.run_folder / "release.pre").exists()


@pytest.mark.slow
def test_case_e_a_restore_of_a_clean_tree_saves_no_patch(repo: Repo) -> None:
    repo.ready()
    flag = repo.run_folder / "release.flag"
    flag.write_text("README.md states v0.1\n")
    code, lines = repo.pre("--run")
    assert (code, lines[-1]) == (0, "release: tag — v0.2.0")
    assert not flag.exists()
    assert list(repo.run_folder.glob("release.discarded.*")) == []

    # A removal through a linked change folder is a stop.
    aside = repo.root.parent / "aside"
    repo.run_folder.rename(aside)
    repo.run_folder.symlink_to(aside)
    code, lines = repo.pre("--run")
    assert code == 1
    assert lines[-1].startswith("release: halt — release.flag cannot be removed: ")
    assert (aside / "release.pre").exists()


def _dirty(repo: Repo) -> None:
    """Leave a person's edit and a binary file the restore saves."""
    repo.put("README.md", "committed\n")
    repo.settle()
    repo.put("README.md", "edited by hand\n")
    (repo.root / "BIN.md").write_bytes(b"\x00\x01\xff\xfe binary\n")


@pytest.mark.slow
def test_case_e_save_numbers_past_a_folder_and_keeps_a_binary_file(
    repo: Repo,
) -> None:
    _dirty(repo)
    repo.run_folder.mkdir(parents=True, exist_ok=True)
    taken = repo.run_folder / "release.discarded.1.patch"
    taken.mkdir()
    code, _ = repo.pre("--run")
    assert code == 0
    assert taken.is_dir()
    patch = (repo.run_folder / "release.discarded.2.patch").read_text()
    assert "edited by hand" in patch
    assert "GIT binary patch" in patch


@pytest.mark.slow
def test_case_e_save_replaces_a_dangling_link(repo: Repo) -> None:
    _dirty(repo)
    repo.run_folder.mkdir(parents=True, exist_ok=True)
    taken = repo.run_folder / "release.discarded.1.patch"
    taken.symlink_to(repo.root.parent / "nowhere.patch")
    code, _ = repo.pre("--run")
    assert code == 0
    assert taken.is_symlink()
    saved = repo.run_folder / "release.discarded.2.patch"
    assert "edited by hand" in saved.read_text()
    assert not (repo.root.parent / "nowhere.patch").exists()


def _held(root: Path, tree: Path, tag: str = "v1.0.0") -> tuple[str, str]:
    """Return the conductor's reading of a release tip, in a fresh load."""
    return _conduct()["_release_tip"](root, tree, _CHANGE, tag)


def test_case_o_release_held_stands_as_a_file_an_empty_file_or_a_link_to_one(
    tmp_path: Path,
) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    mark = _folder(root) / "release.held"
    held = (
        f"v1.0.0: .minions/changes/{_CHANGE}/release.held holds a person's no:"
        f" /mf-release {_CHANGE} merges it on their yes"
    )
    said = f"conduct: halt — .minions/changes/{_CHANGE}/release.held cannot be read: "

    def tip() -> tuple[str, str]:
        return conduct["_release_tip"](root, tree, _CHANGE, "v1.0.0")

    for shape, stands in (
        ("file", True),
        ("empty", True),
        ("link", False),
        ("hard", True),
        ("dangling", False),
        ("folder", False),
        ("pipe", False),
    ):
        _plant(mark, shape, "no\n")
        if stands:
            assert _within(tip) == ("released", held), shape
        else:
            with pytest.raises(conduct["Stop"]) as stopped:
                _within(tip)
            assert str(stopped.value).startswith(said), shape
        _clear(mark)


@pytest.mark.slow
def test_case_o_release_flag_stands_in_every_shape(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    mark = _folder(root) / "release.flag"
    stands = (
        f"v1.0.0 is not tagged; .minions/changes/{_CHANGE}/release.flag stands:"
        f" a person reads the prose it names, then /mf-release {_CHANGE} merges it"
    )
    assert _held(root, tree) != ("released", stands)
    for shape in ("file", "empty", "link", "hard", "dangling", "folder", "pipe"):
        _plant(mark, shape, "README.md states v0.1\n")
        assert _within(lambda: _held(root, tree)) == ("released", stands), shape
        if shape == "folder":
            mark.rmdir()
        else:
            mark.unlink()


def test_case_o_a_stranded_tip_drops_only_under_a_release_pre_that_is_a_file(
    tmp_path: Path,
) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    mark = _folder(root) / "release.pre"
    missing = f".minions/changes/{_CHANGE}/release.pre is missing"
    undroppable = conduct["_undroppable"]
    assert undroppable(root, tree, _CHANGE, "main") == missing
    # The drop takes the mark only when it reads whole.
    whole = "tag: v1.0.0\nversion: v1.0\ngate: 1\nhead: abc1234\n"
    for shape, drops in (
        ("file", True),
        ("empty", False),
        ("link", False),
        ("hard", True),
        ("dangling", False),
        ("folder", False),
        ("pipe", False),
    ):
        _plant(mark, shape, whole)
        why = _within(lambda: undroppable(root, tree, _CHANGE, "main"))
        assert (why is None) is drops, shape
        if not drops:
            assert why.startswith(f".minions/changes/{_CHANGE}/release.pre "), shape
        _clear(mark)
    _plant(mark, "file", "tag: v1.0.0\n")
    said = f".minions/changes/{_CHANGE}/release.pre has no version:"
    assert undroppable(root, tree, _CHANGE, "main") == said


def _clear(mark: Path) -> None:
    """Remove whatever stands at `mark`: a folder, or a name of any other kind."""
    if mark.is_dir() and not mark.is_symlink():
        mark.rmdir()
    else:
        mark.unlink(missing_ok=True)


def test_pin_readers_follow_a_link_and_read_a_file_whole(tmp_path: Path) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    head = _git(tree, "rev-parse", "HEAD")
    marks = _folder(root)
    halt = f"sub-task: 1.2\nstop: 3\nhead: {head}\n"
    named = f"head: {head}\n"
    done = conduct["mflib"].marks.done_head
    simplified = conduct["mflib"].marks.simplified_head
    red, stacked, built = (
        conduct["_red"],
        conduct["_stacked_on"],
        conduct["_build_halt"],
    )
    readers: tuple[tuple[str, str, bool, Callable[[], Any], Any], ...] = (
        ("build.done", named, True, lambda: done(root, _CHANGE), head),
        ("build.simplified", named, True, lambda: simplified(root, _CHANGE), head),
        ("integrate.red", named, True, lambda: red(root, tree, _CHANGE), head),
        (
            "stacked-on",
            f"{head}\n",
            False,
            lambda: stacked(root, _CHANGE, tree, []),
            head,
        ),
        (
            "build.halt",
            halt,
            True,
            lambda: built(root / ".minions", tree, _CHANGE),
            ("1.2", "3"),
        ),
    )
    # A pass mark that cannot be read is absent, a stop mark halts its version, and
    # `build.halt` answers its name and why.
    phrases = {
        "link": "it is a link",
        "pipe": "it is not a regular file",
        "folder": "it is not a regular file",
        "dangling": "it is a link",
        "binary": "it is not UTF-8",
        "whole": f"it is over {_BOUND} bytes",
    }

    def reading(read: Callable[[], Any]) -> Any:  # noqa: ANN401
        try:
            return _within(read)
        except conduct["Stop"]:
            return "halt"

    for name, text, before, read, value in readers:
        mark = marks / name
        padding = "z\n" * _BOUND
        whole = padding + text if before else text + padding
        broken = {
            "integrate.red": lambda shape: "halt",
            "build.halt": lambda shape: (
                "build.halt",
                f"cannot be read: {phrases[shape]}",
            ),
        }.get(name, lambda shape: None)
        for shape in ("link", "hard", "pipe", "folder", "dangling", "binary", "whole"):
            if shape == "whole":
                mark.write_text(whole)
            else:
                _plant(mark, shape, text)
            expected = value if shape == "hard" else broken(shape)
            assert reading(read) == expected, (name, shape)
            _clear(mark)


@pytest.mark.slow
def test_pin_stands_of_the_stop_marks_are_is_file(tmp_path: Path) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    _open_merge(root, tree)
    version = conduct["Version"](_CHANGE, tree)
    note = f".minions/changes/{_CHANGE}/integrate"
    resumes = (
        "integrate",
        "a merge is open and staged, with no note: integrate resumes",
    )
    for name, standing in (
        ("integrate.md", ("integrating", f"semantic conflict: {note}.md")),
        ("integrate.red", ("integrating", f"red gate: {note}.red")),
    ):
        mark = _folder(root) / name
        assert conduct["stage_of"](root, version) == resumes
        said = f"conduct: halt — .minions/changes/{_CHANGE}/{name} cannot be read: "
        for shape, stands in (
            ("file", True),
            ("empty", True),
            ("link", False),
            ("hard", True),
            ("dangling", False),
            ("pipe", False),
            ("folder", False),
        ):
            _plant(mark, shape, "a note\n")
            if stands:
                reading = _within(lambda: conduct["stage_of"](root, version))
                assert reading == standing, (name, shape)
            else:
                with pytest.raises(conduct["Stop"]) as stopped:
                    _within(lambda: conduct["stage_of"](root, version))
                assert str(stopped.value).startswith(said), (name, shape)
                # `conduct.py status` names the mark on the version's line.
                line = conduct["_status_line"](root, version)
                halted = f"{_CHANGE} · halted — {said.removeprefix('conduct: halt — ')}"
                assert line.startswith(halted), (name, shape)
            _clear(mark)


def test_pin_notes_stop_the_version_and_read_with_no_bound(tmp_path: Path) -> None:
    conduct = _conduct()
    opened = halting(conduct, conduct["mflib"].marks.open_notes)
    assert opened(tmp_path, _CHANGE, os.O_RDONLY) is None
    mark = _folder(tmp_path) / "build-notes.md"
    mark.write_text("a\n")
    fd = opened(tmp_path, _CHANGE, os.O_RDONLY)
    assert fd is not None
    os.close(fd)
    mark.unlink()
    for shape in ("link", "hard", "folder", "pipe"):
        _plant(mark, shape, "a\n")
        with pytest.raises(conduct["Stop"]):
            _within(lambda: opened(tmp_path, _CHANGE, os.O_RDONLY))
        _clear(mark)
    mark.write_text("x" * 2**20)
    assert conduct["mflib"].marks.note_lines(tmp_path, _CHANGE) == 1
    mark.write_text("x\n" * (2**20 + 10))
    lines = halting(conduct, conduct["mflib"].marks.note_lines)
    with pytest.raises(conduct["Stop"], match=r"is over 1048576 bytes$"):
        lines(tmp_path, _CHANGE)


def test_pin_cut_halt_is_no_halt_through_a_link_and_blocks_on_a_pipe(
    tmp_path: Path,
) -> None:
    marks = _conduct()["mflib"].marks
    halt = marks.cutter_halt
    mark = _folder(tmp_path) / "cut.halt"
    for shape, said in (
        ("link", "it is a link"),
        ("folder", "it is not a regular file"),
        ("pipe", "it is not a regular file"),
    ):
        _plant(mark, shape, "a halt\n")
        with pytest.raises(marks.Broken, match=f"^cut.halt cannot be read: {said}$"):
            _within(lambda: halt(tmp_path, _CHANGE))
        _clear(mark)


def test_pin_writers_write_through_a_hard_link_and_refuse_or_block_elsewhere(
    tmp_path: Path,
) -> None:
    marks = _conduct()["mflib"].marks
    write = marks.write
    mark = _folder(tmp_path) / "mark"
    _plant(mark, "hard", "first\n")
    write(tmp_path, _CHANGE, "mark", "second\n")
    assert (mark.parent.parent / ".other-mark").read_text() == "first\n"
    assert mark.read_text() == "second\n"
    mark.unlink()
    _plant(mark, "link")
    with pytest.raises(marks.Unwritten) as linked:
        write(tmp_path, _CHANGE, "mark", "x\n")
    assert linked.value.cause.errno == errno.ELOOP
    mark.unlink()
    mark.mkdir()
    with pytest.raises(marks.Unwritten):
        write(tmp_path, _CHANGE, "mark", "x\n")
    mark.rmdir()
    # A pipe at the name is replaced, never written through.
    os.mkfifo(mark)
    _within(lambda: write(tmp_path, _CHANGE, "mark", "x\n"))
    assert mark.read_text() == "x\n"


def _dependency(root: Path) -> str:
    """Commit a dependency's build on its own branch of `root`; return its head."""
    _git(root, "switch", "-q", "-c", "dependency")
    _commit(root, {"dependency.txt": "x\n"}, "the dependency's build")
    head = _git(root, "rev-parse", "HEAD")
    _git(root, "switch", "-q", "main")
    return head


def test_pin_failed_write_of_stacked_on_halts_the_whole_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    head = _dependency(root)
    run = conduct["Run"](root, "claude")
    mark = _folder(root) / "stacked-on"
    mark.symlink_to(tmp_path / "gone")
    said = f"conduct: halt — .minions/changes/{_CHANGE}/stacked-on cannot be written: "
    with pytest.raises(conduct["Stop"]) as refused:
        run.stack(tree, _CHANGE, "0000-dep", head)
    assert refused.value.code == 1
    assert str(refused.value).startswith(said)

    # The version halts, not the run.
    monkeypatch.setitem(
        conduct["Run"].take.__globals__, "_models", lambda *_: ("model", None, None)
    )
    run.catch_up = lambda version: None
    run.ready = lambda version, threads: (
        run.stack(tree, _CHANGE, "0000-dep", head) is None
    )
    run.take(conduct["Version"](_CHANGE, tree), {})
    [(who, why)] = run.halts
    assert who == _CHANGE
    assert why.startswith(said)
    assert not (tmp_path / "gone").exists()


def test_pin_failed_write_of_the_close_stops_with_code_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    names = conduct["close"].__globals__
    for step in ("_close_gate", "_close_metrics", "_close_plan"):
        monkeypatch.setitem(names, step, lambda *_: None)
    (_folder(root) / "build.done").symlink_to(tmp_path / "gone")
    with pytest.raises(conduct["Stop"]) as stopped:
        conduct["close"](root, conduct["Version"](_CHANGE, tree), lambda line: None)
    assert stopped.value.code == 1
    said = f"conduct: halt — .minions/changes/{_CHANGE}/build.done cannot be written: "
    assert str(stopped.value).startswith(said)
    assert not (tmp_path / "gone").exists()


def test_pin_new_marks_cut_red_is_written_staged_and_refuses_a_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    run = conduct["Run"](root, "claude")
    names = conduct["Run"].checked_cut.__globals__
    monkeypatch.setitem(names, "_check_cut", lambda *_: None)
    monkeypatch.setitem(names, "_unapproved", lambda *_: None)
    monkeypatch.setitem(names, "_cut_checked", lambda *_: "line one\nline two\n")
    mark = _folder(root) / "cut.red"
    assert run.checked_cut(_CHANGE, {"bump": "minor"}, tree) == (None, "line one")
    assert mark.read_text() == "line one\nline two\n"
    mark.unlink()
    _plant(mark, "link")
    with pytest.raises(conduct["Stop"]) as stopped:
        run.checked_cut(_CHANGE, {"bump": "minor"}, tree)
    assert stopped.value.code == 1
    assert (mark.parent.parent / ".other-cut.red").read_text() == "head: abc1234\n"


# Each form of a `head:` value a mark can hold: its label, its text with `{head}` the
# tree's `HEAD`, `{short}` its first seven digits, and `{branch}` the change's branch.
_FORMS = (
    ("HEAD", "head: HEAD\n"),
    ("branch", "head: {branch}\n"),
    ("six digits", "head: 123456\n"),
    ("seven digits", "head: {short}\n"),
    ("forty zeros", "head: " + "0" * 40 + "\n"),
    ("next line", "head:\n{head}\n"),
    ("a second head line", "head: {head}\nhead: other\n"),
    ("the real head second", "head: other\nhead: {head}\n"),
    ("a word after it", "head: {head} x\n"),
    ("none", "simplify: none\n"),
)


def _formed(text: str, tree: Path) -> str:
    """Return a form's text with `HEAD`, its short form and the branch put in."""
    head = _git(tree, "rev-parse", "HEAD")
    return text.format(head=head, short=head[:7], branch=_CHANGE)


def test_pin_head_forms_of_build_done(tmp_path: Path) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    head = _git(tree, "rev-parse", "HEAD")
    answers = {
        "HEAD": (None, False),
        "branch": (None, False),
        "six digits": (None, False),
        "seven digits": (head[:7], True),
        "forty zeros": ("0" * 40, False),
        "next line": (None, False),
        "a second head line": (None, False),
        "the real head second": (None, False),
        "a word after it": (None, False),
        "none": (None, False),
    }
    for label, form in _FORMS:
        done, closed = answers[label]
        text = _formed(form, tree)
        assert _closed_at(root, tree, text) is closed, label
        assert conduct["mflib"].marks.done_head(root, _CHANGE) == done, label


@pytest.mark.slow
def test_pin_head_forms_of_build_simplified(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    head = _git(tree, "rev-parse", "HEAD")
    answers = {
        "HEAD": (None, False),
        "branch": (None, False),
        "six digits": (None, False),
        "seven digits": (head[:7], True),
        "forty zeros": ("0" * 40, False),
        "next line": (None, False),
        "a second head line": (None, False),
        "the real head second": (None, False),
        "a word after it": (None, False),
        "none": (None, False),
    }
    for label, form in _FORMS:
        word, amends = answers[label]
        text = _formed(form, tree)
        assert _amends(root, tree, text) is amends, label
        assert _conduct()["mflib"].marks.simplified_head(root, _CHANGE) == word, label


@pytest.mark.slow
def test_pin_head_forms_of_integrate_red(tmp_path: Path) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [x] 1 — One\n")
    head = _git(tree, "rev-parse", "HEAD")
    version = conduct["Version"](_CHANGE, tree)
    note = f".minions/changes/{_CHANGE}/integrate"
    own = ("integrating", f"red gate: {note}.red")
    other = ("integrate", "red gate on another head: integrate gates again")
    answers = {
        "HEAD": (None, other),
        "branch": (None, other),
        "six digits": (None, other),
        "seven digits": (head, own),
        "forty zeros": ("0" * 40, other),
        "next line": (None, other),
        "a second head line": (None, other),
        "the real head second": (None, other),
        "a word after it": (None, other),
        "none": (None, other),
    }
    mark = _folder(root) / "integrate.red"
    for label, text in _FORMS:
        named, staged = answers[label]
        mark.write_text(_formed(text, tree))
        assert conduct["_red"](root, tree, _CHANGE) == named, label
        assert conduct["stage_of"](root, version) == staged, label


def test_pin_head_forms_of_build_halt(tmp_path: Path) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, _CHANGE, "- [ ] 1 — One\n")
    mark = _folder(root) / "build.halt"
    read = ("1.2", "3")
    answers = {
        "HEAD": None,
        "branch": None,
        "six digits": None,
        "seven digits": read,
        "forty zeros": None,
        "next line": None,
        "a second head line": None,
        "the real head second": None,
        "a word after it": None,
        "none": None,
    }
    for label, text in _FORMS:
        mark.write_text(f"sub-task: 1.2\nstop: 3\n{_formed(text, tree)}")
        found = conduct["_build_halt"](root / ".minions", tree, _CHANGE)
        assert found == answers[label], label


def test_pin_head_forms_of_release_pre(repo: Repo) -> None:
    sha = repo.head
    mark = _pre(repo)
    head = {"head": sha, "short": sha[:7], "branch": _CHANGE}
    halts = {"seven digits": sha[:7], "forty zeros": "0" * 8}
    for label, text in _FORMS:
        formed = text.format(**head)
        body = _WHOLE.replace("head: abc1234\n", "") + formed
        mark.write_text(body)
        with pytest.raises(repo.ns.Stop) as stopped:
            repo.ns._mark(repo.root, _CHANGE, sha)
        if label in halts:
            assert stopped.value.code == 1, label
            at = f"release.pre: head {halts[label]} is not HEAD {sha[:8]}"
            said = f"release: halt — {at}"
            assert str(stopped.value).startswith(said), label
        else:
            assert stopped.value.code == 2, label
            no_head = "release: cannot run — release.pre has no head:"
            assert str(stopped.value) == no_head, label
    mark.write_text(_WHOLE.replace("abc1234", sha))
    assert repo.ns._mark(repo.root, _CHANGE, sha)["head"] == sha
