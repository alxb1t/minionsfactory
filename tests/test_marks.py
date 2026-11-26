"""Unit cases of `skills/mflib/marks.py`, each on a planted change folder.

Why: 0154-marks design D2, D4, D5 and D6.
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
    elif shape == "pipe":
        os.mkfifo(path)
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


def test_read_takes_a_regular_file_of_utf8_within_its_bound(tmp_path: Path) -> None:
    assert marks.read(tmp_path, _CHANGE, marks.GATE_RED) is None
    _folder(tmp_path)
    assert marks.read(tmp_path, _CHANGE, marks.GATE_RED) is None
    path = _plant(tmp_path, marks.GATE_RED, "file", "a" * 8)
    assert marks.read(tmp_path, _CHANGE, marks.GATE_RED, 8) == "a" * 8
    path.unlink()
    _plant(tmp_path, marks.GATE_RED, "hard", "kept\n")
    assert marks.read(tmp_path, _CHANGE, marks.GATE_RED) == "kept\n"


@pytest.mark.parametrize(
    ("shape", "text", "said"),
    [
        ("link", "x", "it is a link"),
        ("dangling", "", "it is a link"),
        ("folder", "", "it is not a regular file"),
        ("pipe", "", "it is not a regular file"),
        ("file", "a" * 9, "it is over 8 bytes"),
        ("binary", "x", "it is not UTF-8"),
    ],
)
def test_read_breaks_on_what_it_does_not_take(
    tmp_path: Path, shape: str, text: str, said: str
) -> None:
    _plant(tmp_path, marks.GATE_RED, shape, text)
    with pytest.raises(marks.Broken, match=f"^gate.red cannot be read: {said}$"):
        marks.read(tmp_path, _CHANGE, marks.GATE_RED, 8)


def test_read_breaks_on_a_linked_change_folder(tmp_path: Path) -> None:
    _link_folder(tmp_path)
    (tmp_path / "elsewhere" / marks.GATE_RED).write_text("x\n")
    with pytest.raises(marks.Broken, match=r"^gate\.red cannot be read: its folder "):
        marks.read(tmp_path, _CHANGE, marks.GATE_RED)


@pytest.mark.parametrize(
    ("text", "head"),
    [
        ("head: abc1234\n", "abc1234"),
        (f"x\nhead:\t{_SHA} \r\n", _SHA),
        ("head: abc123\n", None),
        (f"head: {_SHA}0\n", None),
        ("head: ABC1234\n", None),
        ("head: HEAD\n", None),
        ("head: abc1234 x\n", None),
        (" head: abc1234\n", None),
        ("", None),
    ],
)
def test_head_of_takes_7_to_40_hex_digits(text: str, head: str | None) -> None:
    assert marks.head_of(text) == head


def test_done_head_reads_one_head_on_its_line(tmp_path: Path) -> None:
    assert marks.done_head(tmp_path, _CHANGE) is None
    path = _plant(tmp_path, marks.BUILD_DONE, "file", "head: abc1234\nsimplify: x\n")
    assert marks.done_head(tmp_path, _CHANGE) == "abc1234"
    for text in ("head:\n", "head: abc1234\nhead: def5678\n", "head:\n  abc1234\n"):
        path.write_text(text)
        assert marks.done_head(tmp_path, _CHANGE) is None, text


@pytest.mark.parametrize(
    ("shape", "head"),
    [("link", None), ("hard", "abc1234"), ("binary", None), ("folder", None)],
)
def test_done_head_reads_through_no_link_and_no_bad_byte(
    tmp_path: Path, shape: str, head: str | None
) -> None:
    _plant(tmp_path, marks.BUILD_DONE, shape, "head: abc1234\n")
    assert marks.done_head(tmp_path, _CHANGE) == head


def test_simplified_head_reads_one_head_through_no_link(tmp_path: Path) -> None:
    assert marks.simplified_head(tmp_path, _CHANGE) is None
    path = _plant(tmp_path, marks.BUILD_SIMPLIFIED, "file", "head: abc1234\n")
    assert marks.simplified_head(tmp_path, _CHANGE) == "abc1234"
    path.unlink()
    _plant(tmp_path, marks.BUILD_SIMPLIFIED, "link", "head: abc1234\n")
    assert marks.simplified_head(tmp_path, _CHANGE) is None


def test_red_head_reads_one_head_and_breaks_on_a_link(tmp_path: Path) -> None:
    assert marks.red_head(tmp_path, _CHANGE) is None
    path = _plant(tmp_path, marks.INTEGRATE_RED, "file", "gate red\nhead:\nabc\n")
    assert marks.red_head(tmp_path, _CHANGE) is None
    path.write_text("head: \tabc1234\r\n")
    assert marks.red_head(tmp_path, _CHANGE) == "abc1234"
    path.write_text("head: abc1234\nhead: def5678\n")
    assert marks.red_head(tmp_path, _CHANGE) is None
    path.unlink()
    _plant(tmp_path, marks.INTEGRATE_RED, "link", "head: abc1234\n")
    with pytest.raises(marks.Broken, match=r"^integrate\.red cannot be read: "):
        marks.red_head(tmp_path, _CHANGE)


def test_build_halt_reads_its_keys_the_last_of_each(tmp_path: Path) -> None:
    assert marks.build_halt(tmp_path, _CHANGE) is None
    text = "sub-task: 1.2  a\nstop: 3\nstop: 4\nhead: abc1234 \nevidence: x\n"
    path = _plant(tmp_path, marks.BUILD_HALT, "file", text)
    assert marks.build_halt(tmp_path, _CHANGE) == ("1.2  a", "4", "abc1234")
    path.write_text("sub-task: 1.2\nstop:\nhead: abc1234\n")
    assert marks.build_halt(tmp_path, _CHANGE) is None
    path.write_text("sub-task: 1.2\nstop: 3\nhead: old\nhead: abc1234\n")
    assert marks.build_halt(tmp_path, _CHANGE) is None


def test_build_halt_breaks_on_a_bad_byte(tmp_path: Path) -> None:
    _plant(tmp_path, marks.BUILD_HALT, "binary", "sub-task: 1\nstop: 3\nhead: a\n")
    with pytest.raises(marks.Broken, match=r"^build\.halt cannot be read: "):
        marks.build_halt(tmp_path, _CHANGE)


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
    path.write_text("")
    assert marks.cutter_halt(tmp_path, _CHANGE) == ""


@pytest.mark.parametrize("shape", ["link", "binary", "folder"])
def test_cutter_halt_breaks_on_a_mark_it_cannot_read(
    tmp_path: Path, shape: str
) -> None:
    _plant(tmp_path, marks.CUT_HALT, shape, "a halt\n")
    with pytest.raises(marks.Broken, match=r"^cut\.halt cannot be read: "):
        marks.cutter_halt(tmp_path, _CHANGE)


def test_plan_check_text_reads_up_to_the_notes_bound(tmp_path: Path) -> None:
    assert marks.plan_check_text(tmp_path, _CHANGE) is None
    path = _plant(tmp_path, marks.PLAN_CHECK, "file", "x" * marks.NOTES_BOUND)
    assert marks.plan_check_text(tmp_path, _CHANGE) == "x" * marks.NOTES_BOUND
    path.write_text("x" * (marks.NOTES_BOUND + 1))
    assert marks.plan_check_text(tmp_path, _CHANGE) is None


@pytest.mark.parametrize("shape", ["link", "folder", "binary"])
def test_plan_check_text_is_none_for_a_mark_it_cannot_read(
    tmp_path: Path, shape: str
) -> None:
    _plant(tmp_path, marks.PLAN_CHECK, shape, "base: a\n")
    assert marks.plan_check_text(tmp_path, _CHANGE) is None


def test_release_pre_reads_its_keys(tmp_path: Path) -> None:
    assert marks.release_pre(tmp_path, _CHANGE) is None
    text = "tag : v1.2.0\nversion: v1\nversion: v1.2\ngate: 9\nhead: abc1234\nnote\n"
    _plant(tmp_path, marks.RELEASE_PRE, "file", text)
    assert marks.release_pre(tmp_path, _CHANGE) == {
        "tag": "v1.2.0",
        "version": "v1.2",
        "gate": "9",
        "head": "abc1234",
    }


@pytest.mark.parametrize(
    ("text", "key"),
    [
        ("tag: v1.2.0\nversion:\n", "version"),
        ("tag: v1\nversion: v1\ngate: 9\nhead: abc1234\nhead: def5678\n", "head"),
        ("tag: v1\nversion: v1\ngate: 9\nhead: a:b\n", "head"),
    ],
)
def test_release_pre_without_a_key_is_broken(
    tmp_path: Path, text: str, key: str
) -> None:
    _plant(tmp_path, marks.RELEASE_PRE, "file", text)
    with pytest.raises(marks.Broken, match=rf"^release\.pre has no {key}:$"):
        marks.release_pre(tmp_path, _CHANGE)


def test_release_pre_that_cannot_be_read_is_broken(tmp_path: Path) -> None:
    _plant(tmp_path, marks.RELEASE_PRE, "link", "tag: v1.2.0\n")
    with pytest.raises(marks.Broken, match=r"^release\.pre cannot be read: "):
        marks.release_pre(tmp_path, _CHANGE)


@pytest.mark.parametrize(
    ("shape", "standing", "there"),
    [
        ("file", True, True),
        ("hard", True, True),
        ("link", False, True),
        ("dangling", False, True),
        ("folder", False, True),
        ("pipe", False, True),
    ],
)
def test_stands_follows_no_link_and_present_takes_anything(
    tmp_path: Path, shape: str, standing: bool, there: bool
) -> None:
    assert not marks.stands(tmp_path, _CHANGE, marks.RELEASE_HELD)
    assert not marks.present(tmp_path, _CHANGE, marks.RELEASE_FLAG)
    _plant(tmp_path, marks.RELEASE_HELD, shape)
    _plant(tmp_path, marks.RELEASE_FLAG, shape)
    assert marks.stands(tmp_path, _CHANGE, marks.RELEASE_HELD) is standing
    assert marks.present(tmp_path, _CHANGE, marks.RELEASE_FLAG) is there


@pytest.mark.parametrize("shape", ["link", "dangling", "folder", "pipe"])
def test_standing_breaks_on_a_stop_mark_it_cannot_read(
    tmp_path: Path, shape: str
) -> None:
    assert not marks.standing(tmp_path, _CHANGE, marks.INTEGRATE_MD)
    _plant(tmp_path, marks.INTEGRATE_MD, "file", "a note\n")
    assert marks.standing(tmp_path, _CHANGE, marks.INTEGRATE_MD)
    _plant(tmp_path, marks.RELEASE_HELD, shape, "no\n")
    with pytest.raises(marks.Broken, match=r"^release\.held cannot be read: "):
        marks.standing(tmp_path, _CHANGE, marks.RELEASE_HELD)


def test_mtime_is_of_a_regular_file_by_lstat(tmp_path: Path) -> None:
    assert marks.mtime(tmp_path, _CHANGE, marks.RESCUE) is None
    path = _plant(tmp_path, marks.RESCUE, "file", "x")
    assert marks.mtime(tmp_path, _CHANGE, marks.RESCUE) == path.lstat().st_mtime_ns
    _plant(tmp_path, marks.INTEGRATE_SETTLED, "link", "x")
    assert marks.mtime(tmp_path, _CHANGE, marks.INTEGRATE_SETTLED) is None


def test_gate_red_text_reads_back_or_nothing(tmp_path: Path) -> None:
    assert marks.gate_red_text(tmp_path, _CHANGE) == ""
    path = _plant(tmp_path, marks.GATE_RED, "file", "past its limit\n")
    assert marks.gate_red_text(tmp_path, _CHANGE) == "past its limit\n"
    path.unlink()
    _plant(tmp_path, marks.GATE_RED, "link", "past its limit\n")
    assert marks.gate_red_text(tmp_path, _CHANGE) == ""
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


def test_open_notes_breaks_on_a_file_over_the_notes_bound(tmp_path: Path) -> None:
    path = _plant(tmp_path, marks.BUILD_NOTES, "file", "x" * marks.NOTES_BOUND)
    fd = marks.open_notes(tmp_path, _CHANGE, os.O_RDONLY)
    assert fd is not None
    os.close(fd)
    path.write_text("x" * (marks.NOTES_BOUND + 1))
    with pytest.raises(marks.Broken, match=r"^build-notes\.md is over 1048576 bytes$"):
        marks.open_notes(tmp_path, _CHANGE, os.O_RDONLY)


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


def test_write_replaces_the_mark_and_keeps_a_hard_links_other_name(
    tmp_path: Path,
) -> None:
    marks.write(tmp_path, _CHANGE, marks.RESCUE, "a long first text\n")
    marks.write(tmp_path, _CHANGE, marks.RESCUE, "short\n")
    path = layout.change_dir(tmp_path, _CHANGE) / marks.RESCUE
    assert path.read_text() == "short\n"
    assert stat.S_IMODE(path.stat().st_mode) == 0o644 & ~_umask()
    _plant(tmp_path, marks.STACKED_ON, "hard", "old\n")
    marks.write(tmp_path, _CHANGE, marks.STACKED_ON, f"{_SHA}\n")
    assert (tmp_path / f".other-{marks.STACKED_ON}").read_text() == "old\n"
    assert (path.parent / marks.STACKED_ON).read_text() == f"{_SHA}\n"


def test_write_refuses_a_folder_at_the_mark(tmp_path: Path) -> None:
    _plant(tmp_path, marks.INTEGRATE_MD, "folder")
    with pytest.raises(marks.Unwritten, match=r"^integrate\.md cannot be written: "):
        marks.write(tmp_path, _CHANGE, marks.INTEGRATE_MD, "new\n")


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
