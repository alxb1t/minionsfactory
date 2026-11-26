"""Unit cases of `skills/mflib/marks.py`, each on a planted change folder.

Each holds the behaviour of the copy the function replaces. Why: 0154-marks design D3.
"""

import errno
import os
import stat
from pathlib import Path

import pytest
from mflib import layout, marks

_CHANGE = "0001-todo"
_SHA = "a" * 40


def _folder(primary: Path) -> Path:
    """Return the change's folder under `primary`, made."""
    folder = layout.change_dir(primary, _CHANGE)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _plant(primary: Path, name: str, shape: str, text: str = "") -> Path:
    """Make the mark `name` a `shape` holding `text`; return its path."""
    path = _folder(primary) / name
    other = primary / f".other-{name}"
    if shape == "file":
        path.write_text(text)
    elif shape == "binary":
        path.write_bytes(text.encode() + b"\xff\xfe\n")
    elif shape == "link":
        other.write_text(text)
        path.symlink_to(other)
    elif shape == "dangling":
        path.symlink_to(primary / ".nowhere")
    elif shape == "hard":
        other.write_text(text)
        os.link(other, path)
    else:
        assert shape == "folder", shape
        path.mkdir()
    return path


def _link_folder(primary: Path) -> None:
    """Make the change's folder a link to another folder."""
    elsewhere = primary / "elsewhere"
    elsewhere.mkdir()
    changes = layout.run_dir(primary) / layout.CHANGES
    changes.mkdir(parents=True)
    (changes / _CHANGE).symlink_to(elsewhere)


def test_names_are_the_files() -> None:
    assert (marks.BUILD_DONE, marks.BUILD_HALT, marks.BUILD_CLOSING) == (
        "build.done",
        "build.halt",
        "build.closing",
    )
    assert (marks.BUILD_SIMPLIFIED, marks.BUILD_NOTES, marks.STACKED_ON) == (
        "build.simplified",
        "build-notes.md",
        "stacked-on",
    )
    assert (marks.CUT_HALT, marks.CUT_RED, marks.INTEGRATE_MD) == (
        "cut.halt",
        "cut.red",
        "integrate.md",
    )
    assert (
        marks.INTEGRATE_RED,
        marks.INTEGRATE_SETTLED,
        marks.INTEGRATE_RESOLVED,
    ) == ("integrate.red", "integrate.settled", "integrate.resolved")
    assert (marks.RELEASE_HELD, marks.RELEASE_FLAG, marks.RELEASE_PRE) == (
        "release.held",
        "release.flag",
        "release.pre",
    )
    assert (marks.RESCUE, marks.REPLAN, marks.PLAN_CHECK, marks.GATE_RED) == (
        "rescue.md",
        "replan.mark",
        "plan-check.txt",
        "gate.red",
    )
    assert (marks.BOUND, marks.NOTES_BOUND) == (65536, 1048576)
    assert marks.discarded(2) == "release.discarded.2.patch"


def test_done_head_reads_the_first_head_across_a_line_end(tmp_path: Path) -> None:
    assert marks.done_head(tmp_path, _CHANGE) is None
    _plant(tmp_path, marks.BUILD_DONE, "file", "x\nhead:\n  abc1234\nhead: def\n")
    assert marks.done_head(tmp_path, _CHANGE) == "abc1234"


@pytest.mark.parametrize(
    ("shape", "head"),
    [("link", "HEAD"), ("hard", "HEAD"), ("binary", None), ("folder", None)],
)
def test_done_head_follows_a_link_and_reads_no_bad_byte(
    tmp_path: Path, shape: str, head: str | None
) -> None:
    _plant(tmp_path, marks.BUILD_DONE, shape, "head: HEAD\n")
    assert marks.done_head(tmp_path, _CHANGE) == head


def test_simplified_head_reads_the_first_head(tmp_path: Path) -> None:
    assert marks.simplified_head(tmp_path, _CHANGE) is None
    _plant(tmp_path, marks.BUILD_SIMPLIFIED, "link", "head:\n\nhead: z\n")
    assert marks.simplified_head(tmp_path, _CHANGE) == "head:"


def test_red_head_reads_on_its_line_alone(tmp_path: Path) -> None:
    assert marks.red_head(tmp_path, _CHANGE) is None
    path = _plant(tmp_path, marks.INTEGRATE_RED, "file", "gate red\nhead:\nabc\n")
    assert marks.red_head(tmp_path, _CHANGE) is None
    path.write_text("head: \tabc1234\nhead: def5678\n")
    assert marks.red_head(tmp_path, _CHANGE) == "abc1234"


def test_build_halt_reads_its_keys_the_last_of_each(tmp_path: Path) -> None:
    assert marks.build_halt(tmp_path, _CHANGE) is None
    text = "sub-task: 1.2  a\nstop: 3\nhead: old\nhead: abc1234 \nevidence: x\n"
    path = _plant(tmp_path, marks.BUILD_HALT, "file", text)
    assert marks.build_halt(tmp_path, _CHANGE) == ("1.2  a", "3", "abc1234")
    path.write_text("sub-task: 1.2\nstop:\nhead: abc1234\n")
    assert marks.build_halt(tmp_path, _CHANGE) is None


def test_build_halt_reads_no_bad_byte(tmp_path: Path) -> None:
    _plant(tmp_path, marks.BUILD_HALT, "binary", "sub-task: 1\nstop: 3\nhead: a\n")
    assert marks.build_halt(tmp_path, _CHANGE) is None


def test_stacked_head_takes_a_full_sha_alone(tmp_path: Path) -> None:
    assert marks.stacked_head(tmp_path, _CHANGE) is None
    path = _plant(tmp_path, marks.STACKED_ON, "file", f"{_SHA} more\n")
    assert marks.stacked_head(tmp_path, _CHANGE) == _SHA
    path.write_text("abc1234\n")
    assert marks.stacked_head(tmp_path, _CHANGE) is None
    path.write_text("")
    assert marks.stacked_head(tmp_path, _CHANGE) is None


def test_cutter_halt_strips_and_cuts_its_first_line(tmp_path: Path) -> None:
    assert marks.cutter_halt(tmp_path, _CHANGE) is None
    path = _plant(tmp_path, marks.CUT_HALT, "file", f"  {'w' * 400}  \nnext\n")
    assert marks.cutter_halt(tmp_path, _CHANGE) == "w" * 300
    path.write_bytes(b"bad \xff byte\n")
    assert marks.cutter_halt(tmp_path, _CHANGE) == "bad � byte"
    path.write_text("")
    assert marks.cutter_halt(tmp_path, _CHANGE) == ""


def test_cutter_halt_reads_no_link(tmp_path: Path) -> None:
    _plant(tmp_path, marks.CUT_HALT, "link", "a halt\n")
    assert marks.cutter_halt(tmp_path, _CHANGE) is None


def test_done_lines_read_through_no_link(tmp_path: Path) -> None:
    assert marks.done_lines(tmp_path, _CHANGE) == []
    path = _plant(tmp_path, marks.BUILD_DONE, "file", "head: a\nsimplify: none\n")
    assert marks.done_lines(tmp_path, _CHANGE) == ["head: a", "simplify: none"]
    path.unlink()
    _plant(tmp_path, marks.BUILD_DONE, "link", "head: a\n")
    assert marks.done_lines(tmp_path, _CHANGE) == []


def test_plan_check_text_replaces_a_bad_byte(tmp_path: Path) -> None:
    assert marks.plan_check_text(tmp_path, _CHANGE) is None
    _plant(tmp_path, marks.PLAN_CHECK, "binary", "base: a\nok\n")
    assert marks.plan_check_text(tmp_path, _CHANGE) == "base: a\nok\n��\n"


@pytest.mark.parametrize(("shape", "code"), [("link", errno.ELOOP), ("folder", None)])
def test_plan_check_text_raises_on_no_regular_file(
    tmp_path: Path, shape: str, code: int | None
) -> None:
    _plant(tmp_path, marks.PLAN_CHECK, shape, "base: a\n")
    with pytest.raises(OSError) as raised:  # noqa: PT011
        marks.plan_check_text(tmp_path, _CHANGE)
    assert raised.value.errno == (code or errno.EINVAL)


def test_release_pre_reads_its_keys(tmp_path: Path) -> None:
    assert marks.release_pre(tmp_path, _CHANGE) is None
    text = "tag : v1.2.0\nversion: v1.2\ngate: 9\nhead: old\nhead: a:b\nno colon\n"
    _plant(tmp_path, marks.RELEASE_PRE, "file", text)
    assert marks.release_pre(tmp_path, _CHANGE) == {
        "tag": "v1.2.0",
        "version": "v1.2",
        "gate": "9",
        "head": "a:b",
    }


def test_release_pre_without_a_key_is_broken(tmp_path: Path) -> None:
    _plant(tmp_path, marks.RELEASE_PRE, "file", "tag: v1.2.0\nversion:\n")
    with pytest.raises(marks.Broken, match=r"^release\.pre has no version:$"):
        marks.release_pre(tmp_path, _CHANGE)


def test_release_pre_that_cannot_be_read_is_broken(tmp_path: Path) -> None:
    _plant(tmp_path, marks.RELEASE_PRE, "link", "tag: v1.2.0\n")
    with pytest.raises(marks.Broken, match=r"^release\.pre cannot be read: "):
        marks.release_pre(tmp_path, _CHANGE)


@pytest.mark.parametrize(
    ("shape", "standing", "there"),
    [
        ("file", True, True),
        ("link", True, True),
        ("dangling", False, True),
        ("folder", False, True),
    ],
)
def test_stands_follows_a_link_and_present_does_not(
    tmp_path: Path, shape: str, standing: bool, there: bool
) -> None:
    assert not marks.stands(tmp_path, _CHANGE, marks.RELEASE_HELD)
    assert not marks.present(tmp_path, _CHANGE, marks.RELEASE_FLAG)
    _plant(tmp_path, marks.RELEASE_HELD, shape)
    _plant(tmp_path, marks.RELEASE_FLAG, shape)
    assert marks.stands(tmp_path, _CHANGE, marks.RELEASE_HELD) is standing
    assert marks.present(tmp_path, _CHANGE, marks.RELEASE_FLAG) is there


def test_mtime_is_of_a_regular_file_by_lstat(tmp_path: Path) -> None:
    assert marks.mtime(tmp_path, _CHANGE, marks.RESCUE) is None
    path = _plant(tmp_path, marks.RESCUE, "file", "x")
    assert marks.mtime(tmp_path, _CHANGE, marks.RESCUE) == path.lstat().st_mtime_ns
    _plant(tmp_path, marks.INTEGRATE_SETTLED, "link", "x")
    assert marks.mtime(tmp_path, _CHANGE, marks.INTEGRATE_SETTLED) is None


def test_gate_red_text_reads_back_or_nothing(tmp_path: Path) -> None:
    assert marks.gate_red_text(tmp_path, _CHANGE) == ""
    path = _plant(tmp_path, marks.GATE_RED, "link", "past its limit\n")
    assert marks.gate_red_text(tmp_path, _CHANGE) == "past its limit\n"
    path.unlink()
    _plant(tmp_path, marks.GATE_RED, "binary", "past its limit\n")
    assert marks.gate_red_text(tmp_path, _CHANGE) == ""


def test_open_notes_opens_a_file_of_one_name(tmp_path: Path) -> None:
    assert marks.open_notes(tmp_path, _CHANGE, os.O_RDONLY) is None
    _plant(tmp_path, marks.BUILD_NOTES, "file", "a\nb\n")
    fd = marks.open_notes(tmp_path, _CHANGE, os.O_RDONLY)
    assert fd is not None
    with os.fdopen(fd, "rb") as notes:
        assert notes.read() == b"a\nb\n"


@pytest.mark.parametrize(
    ("shape", "flags", "said"),
    [
        ("link", os.O_RDONLY, "is a link"),
        ("hard", os.O_RDONLY, "is not a regular file of one name"),
        ("folder", os.O_RDONLY, "is not a regular file of one name"),
        ("folder", os.O_RDWR, "cannot be opened — "),
    ],
)
def test_open_notes_breaks_on_no_file_of_one_name(
    tmp_path: Path, shape: str, flags: int, said: str
) -> None:
    _plant(tmp_path, marks.BUILD_NOTES, shape, "a\n")
    with pytest.raises(marks.Broken, match=f"^build-notes.md {said}"):
        marks.open_notes(tmp_path, _CHANGE, flags)


def test_note_lines_counts_whole_lines(tmp_path: Path) -> None:
    assert marks.note_lines(tmp_path, _CHANGE) == 0
    _plant(tmp_path, marks.BUILD_NOTES, "file", "a\nb\nc")
    assert marks.note_lines(tmp_path, _CHANGE) == 3


def test_text_writers_give_each_mark_its_form() -> None:
    assert marks.done_text("abc", "none") == "head: abc\nsimplify: none\n"
    assert marks.halt_text("close", "gate", "red\n  x", "abc") == (
        "sub-task: close\nstop: gate\nevidence: red x\nhead: abc\n"
    )
    assert marks.diagnosis_text(_CHANGE, "verify: halt") == (
        f"# {_CHANGE} — rescue diagnosis\n\nhalt: verify: halt\nsub-task: none\n"
        "cause: a Verify: changed since the cut\n"
        f"proposal: commit docs({_CHANGE}): amend the change directory, then"
        f" conduct.py rejoin {_CHANGE}, or /mf-ship with no run live\n"
    )
    assert marks.head_text("abc") == "head: abc\n"
    assert marks.stacked_text("abc") == "abc\n"
    assert marks.plan_check_body("abc", "ok\n") == "base: abc\nok\n"


def test_write_stages_the_mark(tmp_path: Path) -> None:
    marks.write(tmp_path, _CHANGE, marks.BUILD_DONE, "head: a\n")
    folder = layout.change_dir(tmp_path, _CHANGE)
    assert (folder / marks.BUILD_DONE).read_text() == "head: a\n"
    assert sorted(path.name for path in folder.iterdir()) == [marks.BUILD_DONE]


def test_write_refuses_a_link_at_the_mark(tmp_path: Path) -> None:
    _plant(tmp_path, marks.GATE_RED, "link", "old\n")
    with pytest.raises(
        marks.Unwritten, match=r"^gate\.red cannot be written: "
    ) as raised:
        marks.write(tmp_path, _CHANGE, marks.GATE_RED, "new\n")
    assert raised.value.name == marks.GATE_RED
    assert raised.value.cause.errno == errno.ELOOP
    assert (tmp_path / f".other-{marks.GATE_RED}").read_text() == "old\n"


def test_write_refuses_a_linked_change_folder(tmp_path: Path) -> None:
    _link_folder(tmp_path)
    with pytest.raises(marks.Unwritten, match=r"^build\.halt cannot be written: "):
        marks.write(tmp_path, _CHANGE, marks.BUILD_HALT, "x\n")
    assert list((tmp_path / "elsewhere").iterdir()) == []


def test_write_in_place_truncates_through_a_hard_link(tmp_path: Path) -> None:
    marks.write_in_place(tmp_path, _CHANGE, marks.RESCUE, "a long first text\n")
    marks.write_in_place(tmp_path, _CHANGE, marks.RESCUE, "short\n")
    path = layout.change_dir(tmp_path, _CHANGE) / marks.RESCUE
    assert path.read_text() == "short\n"
    assert stat.S_IMODE(path.stat().st_mode) == 0o644 & ~_umask()
    _plant(tmp_path, marks.STACKED_ON, "hard", "old\n")
    marks.write_in_place(tmp_path, _CHANGE, marks.STACKED_ON, f"{_SHA}\n")
    assert (tmp_path / f".other-{marks.STACKED_ON}").read_text() == f"{_SHA}\n"


def test_write_in_place_refuses_a_link(tmp_path: Path) -> None:
    _plant(tmp_path, marks.INTEGRATE_MD, "link", "old\n")
    with pytest.raises(OSError) as raised:  # noqa: PT011
        marks.write_in_place(tmp_path, _CHANGE, marks.INTEGRATE_MD, "new\n")
    assert raised.value.errno == errno.ELOOP


def test_remove_unlinks_by_name(tmp_path: Path) -> None:
    marks.remove(tmp_path, _CHANGE, marks.GATE_RED)
    path = _plant(tmp_path, marks.GATE_RED, "link", "x")
    marks.remove(tmp_path, _CHANGE, marks.GATE_RED)
    assert not os.path.lexists(path)
    assert (tmp_path / f".other-{marks.GATE_RED}").exists()


def test_remove_raises_on_a_folder(tmp_path: Path) -> None:
    _plant(tmp_path, marks.BUILD_CLOSING, "folder")
    with pytest.raises(OSError):  # noqa: PT011
        marks.remove(tmp_path, _CHANGE, marks.BUILD_CLOSING)


def _umask() -> int:
    """Return the process's umask, left as it was."""
    mask = os.umask(0)
    os.umask(mask)
    return mask
