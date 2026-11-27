"""Unit cases of `skills/mflib/queue.py`, each on a planted home queue.

Why: 0156-queue design D1, D2, D5 and D7.
"""

import errno
import json
import os
import stat
import threading
from pathlib import Path
from unittest import mock

import pytest
from mflib import layout, queue

_CHANGE = "0001-a"
_ENTRY: queue.Entry = {
    "bump": "minor",
    "brief": "/b/brief.md",
    "executor": "claude",
    "after": [],
    "halt": None,
    "model": None,
    "effort": None,
    "dependencies": [["pypi", "rich", ">=13", "the page"]],
    "models": None,
    "beside": ["0002-b"],
    "waits": "the cap",
}
_REQUIRED = {"bump", "brief", "executor", "after", "halt", "model", "effort"}
_MERGE = "a" * 40


def _primary(tmp_path: Path) -> Path:
    """Return a primary checkout's path, made."""
    primary = tmp_path / "primary"
    primary.mkdir()
    return primary


def _cuts(primary: Path) -> Path:
    """Return the queue's `cuts` folder, made."""
    folder = layout.queue_cuts(primary)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _modes(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def test_a_record_written_reads_back_whole(tmp_path: Path) -> None:
    primary = _primary(tmp_path)
    layout.queue_dir(primary).mkdir(parents=True)

    queue.write(primary, _CHANGE, _ENTRY)

    assert queue.entries(primary) == {_CHANGE: _ENTRY}


def test_the_required_keys_are_named_once_in_the_record() -> None:
    assert queue.REQUIRED == _REQUIRED
    assert set(queue.Entry.__optional_keys__) == {
        "dependencies",
        "models",
        "beside",
        "waits",
    }


def test_the_unreadable_entry_holds_its_halt_alone() -> None:
    assert queue.UNREADABLE == {"halt": "the queue entry is unreadable"}


def test_the_halt_text_names_the_cut_waited_on() -> None:
    assert queue.halted_text(_CHANGE) == "after 0001-a is cut-halted"


@pytest.mark.parametrize("name", ["0001-a", "12-two-words", "0003-a1-b2"])
def test_the_change_id_pattern_takes_an_id(name: str) -> None:
    assert queue.CHANGE_ID.fullmatch(name)


@pytest.mark.parametrize("name", ["a-0001", "0001", "0001-A", "0001-a-", ".0001-a"])
def test_the_change_id_pattern_refuses_what_is_no_id(name: str) -> None:
    assert not queue.CHANGE_ID.fullmatch(name)


def test_the_lock_blocks_a_second_taker(tmp_path: Path) -> None:
    primary = _primary(tmp_path)
    second = threading.Event()

    def take() -> None:
        with queue.lock(primary):
            second.set()

    with queue.lock(primary):
        thread = threading.Thread(target=take, daemon=True)
        thread.start()
        assert not second.wait(0.3)
    thread.join(10)

    assert second.is_set()


def test_the_lock_makes_its_folders_0700_and_its_file_0600(tmp_path: Path) -> None:
    primary = _primary(tmp_path)
    umask = os.umask(0o022)
    try:
        with queue.lock(primary):
            pass
    finally:
        os.umask(umask)
    lock = layout.queue_lock(primary)

    assert _modes(lock) == 0o600
    assert _modes(lock.parent) == 0o700
    assert _modes(lock.parent.parent) == 0o700


def test_the_lock_makes_no_parent_of_the_kept_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    primary = _primary(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path / "no" / "home"))

    with pytest.raises(queue.Refused) as refused, queue.lock(primary):
        pass

    assert refused.value.errno == errno.ENOENT
    assert refused.value.strerror == os.strerror(errno.ENOENT)
    assert isinstance(refused.value, OSError)
    assert not (tmp_path / "no").exists()


def test_the_lock_refuses_a_link_at_its_file(tmp_path: Path) -> None:
    primary = _primary(tmp_path)
    lock = layout.queue_lock(primary)
    lock.parent.mkdir(parents=True)
    outside = tmp_path / "outside"
    lock.symlink_to(outside)

    with pytest.raises(queue.Refused) as refused, queue.lock(primary):
        pass

    assert refused.value.errno == errno.ELOOP
    assert not outside.exists()


def test_the_lock_closes_its_descriptor_when_the_body_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    primary = _primary(tmp_path)
    closes = mock.Mock(wraps=os.close)
    monkeypatch.setattr(queue.os, "close", closes)

    with pytest.raises(KeyError), queue.lock(primary):
        raise KeyError

    assert closes.call_count == 1


def test_entries_skips_a_name_that_is_no_change_id(tmp_path: Path) -> None:
    primary = _primary(tmp_path)
    folder = _cuts(primary)
    for name in ("notes", ".0002-b", "0003-c.tmp"):
        (folder / name).write_text(json.dumps(_ENTRY))
    (folder / _CHANGE).write_text(json.dumps(_ENTRY))

    assert list(queue.entries(primary)) == [_CHANGE]


def test_entries_come_in_id_order(tmp_path: Path) -> None:
    primary = _primary(tmp_path)
    folder = _cuts(primary)
    for name in ("0003-c", "0001-a", "0002-b"):
        (folder / name).write_text(json.dumps(_ENTRY))

    assert list(queue.entries(primary)) == ["0001-a", "0002-b", "0003-c"]


@pytest.mark.parametrize(
    "data",
    [
        b"not json",
        b"[1, 2]",
        b'"text"',
        json.dumps({k: v for k, v in _ENTRY.items() if k != "after"}).encode(),
        b'{"bump": "minor", "brief": "\xff"}',
    ],
    ids=["no-json", "list", "string", "missing-key", "bad-byte"],
)
def test_entries_map_a_broken_entry_to_the_unreadable_one(
    tmp_path: Path, data: bytes
) -> None:
    primary = _primary(tmp_path)
    (_cuts(primary) / _CHANGE).write_bytes(data)

    found = queue.entries(primary)

    assert found == {_CHANGE: queue.UNREADABLE}
    assert found[_CHANGE] is not queue.UNREADABLE


def test_entries_map_a_folder_at_an_entry_to_the_unreadable_one(tmp_path: Path) -> None:
    primary = _primary(tmp_path)
    (_cuts(primary) / _CHANGE).mkdir()

    assert queue.entries(primary) == {_CHANGE: queue.UNREADABLE}


def test_entries_follow_a_link_at_an_entry(tmp_path: Path) -> None:
    primary = _primary(tmp_path)
    outside = tmp_path / "outside"
    outside.write_text(json.dumps(_ENTRY))
    (_cuts(primary) / _CHANGE).symlink_to(outside)

    assert queue.entries(primary) == {_CHANGE: _ENTRY}


def test_entries_keep_a_value_of_the_wrong_type(tmp_path: Path) -> None:
    primary = _primary(tmp_path)
    wrong = {**_ENTRY, "after": "0002-b", "waits": None}
    (_cuts(primary) / _CHANGE).write_text(json.dumps(wrong))

    assert queue.entries(primary) == {_CHANGE: wrong}


def test_entries_list_nothing_of_a_linked_missing_or_file_shaped_folder(
    tmp_path: Path,
) -> None:
    primary = _primary(tmp_path)
    assert queue.entries(primary) == {}
    real = tmp_path / "real"
    real.mkdir()
    (real / _CHANGE).write_text(json.dumps(_ENTRY))
    cuts = layout.queue_cuts(primary)
    cuts.parent.mkdir(parents=True)
    cuts.symlink_to(real)
    assert queue.entries(primary) == {}
    cuts.unlink()
    cuts.write_text("a file")

    assert queue.entries(primary) == {}


def test_entries_list_nothing_when_the_folder_cannot_be_listed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    primary = _primary(tmp_path)
    (_cuts(primary) / _CHANGE).write_text(json.dumps(_ENTRY))

    def refusing(path: object) -> list[str]:
        raise PermissionError(errno.EACCES, "denied")

    monkeypatch.setattr(queue.os, "listdir", refusing)

    assert queue.entries(primary) == {}


def test_a_write_makes_cuts_0700_and_its_entry_0600_in_compact_order(
    tmp_path: Path,
) -> None:
    primary = _primary(tmp_path)
    layout.queue_dir(primary).mkdir(parents=True)
    umask = os.umask(0o022)
    try:
        queue.write(primary, _CHANGE, {"halt": None, "bump": "minor"})
    finally:
        os.umask(umask)
    cuts = layout.queue_cuts(primary)

    assert _modes(cuts) == 0o700
    assert _modes(cuts / _CHANGE) == 0o600
    assert (cuts / _CHANGE).read_text() == '{"halt": null, "bump": "minor"}'
    assert os.listdir(cuts) == [_CHANGE]


def test_a_write_makes_no_parent_of_cuts(tmp_path: Path) -> None:
    primary = _primary(tmp_path)

    with pytest.raises(FileNotFoundError):
        queue.write(primary, _CHANGE, _ENTRY)

    assert not layout.queue_dir(primary).exists()


def test_a_write_replaces_a_link_at_the_entry_and_leaves_its_target(
    tmp_path: Path,
) -> None:
    primary = _primary(tmp_path)
    outside = tmp_path / "outside"
    outside.write_text("held")
    (_cuts(primary) / _CHANGE).symlink_to(outside)

    queue.write(primary, _CHANGE, _ENTRY)

    entry = layout.queue_cuts(primary) / _CHANGE
    assert not entry.is_symlink()
    assert json.loads(entry.read_text()) == _ENTRY
    assert outside.read_text() == "held"


def test_a_write_goes_through_a_linked_cuts_folder(tmp_path: Path) -> None:
    primary = _primary(tmp_path)
    real = tmp_path / "real"
    real.mkdir()
    cuts = layout.queue_cuts(primary)
    cuts.parent.mkdir(parents=True)
    cuts.symlink_to(real)

    queue.write(primary, _CHANGE, _ENTRY)

    assert json.loads((real / _CHANGE).read_text()) == _ENTRY


def test_a_failed_write_raises_its_os_error_and_leaves_the_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    primary = _primary(tmp_path)
    (_cuts(primary) / _CHANGE).write_text("held")

    def full(source: object, target: object) -> None:
        raise OSError(errno.ENOSPC, os.strerror(errno.ENOSPC))

    monkeypatch.setattr(queue.os, "replace", full)

    with pytest.raises(OSError, match="No space left") as raised:
        queue.write(primary, _CHANGE, _ENTRY)

    assert raised.value.errno == errno.ENOSPC
    assert not isinstance(raised.value, queue.Unwritten)
    assert (layout.queue_cuts(primary) / _CHANGE).read_text() == "held"


def test_unwritten_is_an_os_error_that_names_its_file(tmp_path: Path) -> None:
    cause = OSError(errno.ENOSPC, os.strerror(errno.ENOSPC))
    path = tmp_path / "cuts" / _CHANGE

    unwritten = queue.Unwritten(path, cause)

    assert isinstance(unwritten, OSError)
    assert unwritten.filename == str(path)
    assert unwritten.errno == errno.ENOSPC
    assert unwritten.strerror == os.strerror(errno.ENOSPC)
    assert unwritten.cause is cause
    assert str(path) in str(unwritten)


def test_remove_removes_the_entry_and_a_missing_one_raises(tmp_path: Path) -> None:
    primary = _primary(tmp_path)
    (_cuts(primary) / _CHANGE).write_text(json.dumps(_ENTRY))
    (_cuts(primary) / "0002-b").write_text(json.dumps(_ENTRY))

    queue.remove(primary, _CHANGE)

    assert list(queue.entries(primary)) == ["0002-b"]
    with pytest.raises(FileNotFoundError):
        queue.remove(primary, _CHANGE)


def test_requests_returns_the_names_it_unlinks(tmp_path: Path) -> None:
    primary = _primary(tmp_path)
    queue.request(primary, _CHANGE)
    queue.request(primary, "all")
    folder = layout.queue_rejoin(primary)

    assert queue.requests(layout.queue_dir(primary)) == {_CHANGE, "all"}
    assert os.listdir(folder) == []
    assert queue.requests(layout.queue_dir(primary)) == set()


def test_requests_unlink_a_link_and_a_stray_name_and_leave_a_subfolder(
    tmp_path: Path,
) -> None:
    primary = _primary(tmp_path)
    folder = layout.queue_rejoin(primary)
    folder.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.write_text("held")
    (folder / "0002-b").symlink_to(outside)
    (folder / "stray.tmp").write_text("")
    (folder / "0003-c").mkdir()

    assert queue.requests(layout.queue_dir(primary)) == {"0002-b", "stray.tmp"}
    assert os.listdir(folder) == ["0003-c"]
    assert outside.read_text() == "held"


def test_requests_take_nothing_from_a_linked_or_missing_folder(tmp_path: Path) -> None:
    primary = _primary(tmp_path)
    home = layout.queue_dir(primary)
    assert queue.requests(home) == set()
    real = tmp_path / "real"
    real.mkdir()
    (real / _CHANGE).write_text("")
    home.mkdir(parents=True)
    layout.queue_rejoin(primary).symlink_to(real)

    assert queue.requests(home) == set()
    assert os.listdir(real) == [_CHANGE]


def test_a_request_makes_its_folder_with_parents_0700(tmp_path: Path) -> None:
    primary = _primary(tmp_path)
    umask = os.umask(0o022)
    try:
        queue.request(primary, _CHANGE)
    finally:
        os.umask(umask)
    folder = layout.queue_rejoin(primary)

    assert _modes(folder) == 0o700
    assert (folder / _CHANGE).read_bytes() == b""


def test_a_request_leaves_one_that_stands(tmp_path: Path) -> None:
    primary = _primary(tmp_path)
    folder = layout.queue_rejoin(primary)
    folder.mkdir(parents=True)
    (folder / _CHANGE).write_text("held")

    queue.request(primary, _CHANGE)

    assert (folder / _CHANGE).read_text() == "held"


def test_a_request_goes_through_a_link_at_its_name(tmp_path: Path) -> None:
    primary = _primary(tmp_path)
    folder = layout.queue_rejoin(primary)
    folder.mkdir(parents=True)
    outside = tmp_path / "outside"
    (folder / _CHANGE).symlink_to(outside)

    queue.request(primary, _CHANGE)

    assert outside.is_file()


def test_requested_counts_a_regular_file_and_unlinks_nothing(tmp_path: Path) -> None:
    primary = _primary(tmp_path)
    home = layout.queue_dir(primary)
    folder = layout.queue_rejoin(primary)
    folder.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.write_text("")
    (folder / "0002-b").symlink_to(outside)
    (folder / "0003-c").mkdir()
    assert not queue.requested(home)
    (folder / _CHANGE).write_text("")

    assert queue.requested(home)
    assert sorted(os.listdir(folder)) == [_CHANGE, "0002-b", "0003-c"]


def test_requested_reads_no_linked_or_missing_folder(tmp_path: Path) -> None:
    primary = _primary(tmp_path)
    home = layout.queue_dir(primary)
    assert not queue.requested(home)
    real = tmp_path / "real"
    real.mkdir()
    (real / _CHANGE).write_text("")
    home.mkdir(parents=True)
    layout.queue_rejoin(primary).symlink_to(real)

    assert not queue.requested(home)


def test_requested_is_false_when_a_name_cannot_be_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    primary = _primary(tmp_path)
    queue.request(primary, _CHANGE)

    def refusing(name: str, **at: int) -> os.stat_result:
        raise PermissionError(errno.EACCES, "denied")

    monkeypatch.setattr(queue.os, "lstat", refusing)

    assert not queue.requested(layout.queue_dir(primary))


def test_a_prefix_of_the_merge_is_no_try(tmp_path: Path) -> None:
    primary = _primary(tmp_path)
    layout.queue_dir(primary).mkdir(parents=True)
    queue.write_supervised(primary, _CHANGE, _MERGE[:7])

    assert not queue.merge_tried(primary, _CHANGE, _MERGE)


def test_a_supervised_record_reads_back_as_a_try(tmp_path: Path) -> None:
    primary = _primary(tmp_path)
    layout.queue_dir(primary).mkdir(parents=True)
    umask = os.umask(0o022)
    try:
        queue.write_supervised(primary, _CHANGE, _MERGE)
    finally:
        os.umask(umask)
    folder = layout.queue_supervised(primary)

    assert queue.merge_tried(primary, _CHANGE, _MERGE)
    assert not queue.merge_tried(primary, "0002-b", _MERGE)
    assert (folder / _CHANGE).read_text() == f"{_MERGE}\n"
    assert _modes(folder) == 0o700


def test_a_supervised_record_is_read_stripped(tmp_path: Path) -> None:
    primary = _primary(tmp_path)
    folder = layout.queue_supervised(primary)
    folder.mkdir(parents=True)
    (folder / _CHANGE).write_text(f"  {_MERGE} \n\n")

    assert queue.merge_tried(primary, _CHANGE, _MERGE)


def test_a_supervised_record_of_a_bad_byte_is_no_try(tmp_path: Path) -> None:
    primary = _primary(tmp_path)
    folder = layout.queue_supervised(primary)
    folder.mkdir(parents=True)
    (folder / _CHANGE).write_bytes(_MERGE.encode() + b"\xff")

    assert not queue.merge_tried(primary, _CHANGE, _MERGE)


def test_a_brief_record_reads_back_stripped(tmp_path: Path) -> None:
    primary = _primary(tmp_path)
    layout.queue_dir(primary).mkdir(parents=True)
    umask = os.umask(0o022)
    try:
        queue.write_brief(primary, _CHANGE, "/b/brief.md")
    finally:
        os.umask(umask)
    folder = layout.queue_briefs(primary)

    assert queue.brief(primary, _CHANGE) == "/b/brief.md"
    assert (folder / _CHANGE).read_text() == "/b/brief.md\n"
    assert _modes(folder) == 0o700


@pytest.mark.parametrize("data", [b"", b"  \n", b"/b/\xff.md"], ids=str)
def test_an_empty_or_bad_brief_record_reads_as_none(
    tmp_path: Path, data: bytes
) -> None:
    primary = _primary(tmp_path)
    folder = layout.queue_briefs(primary)
    folder.mkdir(parents=True)
    (folder / _CHANGE).write_bytes(data)

    assert queue.brief(primary, _CHANGE) is None
    assert queue.brief(primary, "0002-b") is None


def test_a_record_write_makes_no_parent_of_its_folder(tmp_path: Path) -> None:
    primary = _primary(tmp_path)

    with pytest.raises(FileNotFoundError):
        queue.write_brief(primary, _CHANGE, "/b/brief.md")
    with pytest.raises(FileNotFoundError):
        queue.write_supervised(primary, _CHANGE, _MERGE)

    assert not layout.queue_dir(primary).exists()
