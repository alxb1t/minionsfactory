"""Unit cases of `skills/mflib/kept.py`, each in the isolated home folder.

Why: 0159-kept design D2 and D5.
"""

import contextlib
import errno
import json
import os
import stat
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest
from mflib import kept, layout

_H = "0123456789abcdef0123456789abcdef01234567"
_S = "89abcdef0123456789abcdef0123456789abcdef"
_URLS: kept.Urls = (
    ["https://example.invalid/a.git"],
    ["https://example.invalid/b.git"],
)


@pytest.fixture
def p(tmp_path: Path) -> Path:
    """Return a primary checkout's path, made."""
    primary = tmp_path / "primary"
    primary.mkdir()
    return primary


def _kept() -> Path:
    """Return the home's kept folder, made at 0700."""
    folder = layout.kept_dir()
    folder.mkdir(mode=0o700, exist_ok=True)
    return folder


def _modes(path: Path) -> int:
    """Return the permission bits of `path`."""
    return stat.S_IMODE(path.stat().st_mode)


@contextlib.contextmanager
def _readonly(folder: Path) -> Iterator[None]:
    """Hold `folder` at mode 0500."""
    before = _modes(folder)
    folder.chmod(0o500)
    try:
        yield
    finally:
        folder.chmod(before)


@contextlib.contextmanager
def _other_process() -> Iterator[int]:
    """Yield the pid of a live process that is neither this one nor its parent."""
    child = subprocess.Popen(["sleep", "30"])
    try:
        yield child.pid
    finally:
        child.kill()
        child.wait()


def _file_at_kept_folder() -> None:
    """Plant a regular file where the kept folder would stand."""
    layout.kept_dir().write_text("x\n")


# --- the kept origin and `.default`


def test_origin_reads_none_before_a_run_kept_it(p: Path) -> None:
    assert kept.origin(p) is None
    assert not kept.origin_stands(p)


def test_origin_reads_the_pair_of_lists_kept(p: Path) -> None:
    _kept()
    layout.kept_file(p).write_text('[["u1"], ["u2", "u3"]]')

    assert kept.origin(p) == (["u1"], ["u2", "u3"])
    assert kept.origin_stands(p)


def test_origin_stops_on_a_folder_at_its_name(p: Path) -> None:
    _kept()
    layout.kept_file(p).mkdir()

    with pytest.raises(kept.Broken):
        kept.origin(p)
    with pytest.raises(kept.Broken):
        kept.origin_stands(p)


def test_origin_keep_writes_the_urls_at_0600_in_a_folder_of_0700(p: Path) -> None:
    kept.keep_origin(p, _URLS)

    file = layout.kept_file(p)
    assert _modes(file.parent) == 0o700
    assert _modes(file) == 0o600
    assert json.loads(file.read_text()) == [list(_URLS[0]), list(_URLS[1])]


def test_origin_keep_leaves_an_origin_that_stands(p: Path) -> None:
    _kept()
    layout.kept_file(p).write_text('[["old"], ["old"]]')

    kept.keep_origin(p, _URLS)

    assert kept.origin(p) == (["old"], ["old"])


def test_origin_keep_with_a_file_at_the_kept_folder_writes_nothing(p: Path) -> None:
    _file_at_kept_folder()

    kept.keep_origin(p, _URLS)

    assert layout.kept_dir().read_text() == "x\n"


def test_origin_keep_in_a_folder_it_cannot_write_raises_unwritten(p: Path) -> None:
    folder = _kept()

    with _readonly(folder), pytest.raises(kept.Unwritten) as raised:
        kept.keep_origin(p, _URLS)

    assert raised.value.strerror == "Permission denied"
    assert raised.value.filename == str(layout.kept_file(p))
    assert isinstance(raised.value.cause, PermissionError)


def test_origin_keep_in_a_home_it_cannot_write_raises_refused(
    p: Path, isolated_home: Path
) -> None:
    with _readonly(isolated_home), pytest.raises(kept.Refused) as raised:
        kept.keep_origin(p, _URLS)

    assert raised.value.strerror == "Permission denied"
    assert isinstance(raised.value.cause, PermissionError)


def test_origin_default_reads_none_before_a_run_kept_it(p: Path) -> None:
    assert kept.default(p) is None
    assert not kept.default_stands(p)


def test_origin_default_reads_its_text_stripped(p: Path) -> None:
    _kept()
    layout.default_file(p).write_text("dev\n")

    assert kept.default(p) == "dev"
    assert kept.default_stands(p)


def test_origin_default_stops_on_a_folder_at_its_name(p: Path) -> None:
    _kept()
    layout.default_file(p).mkdir()

    with pytest.raises(kept.Broken):
        kept.default(p)
    assert kept.default_stands(p)


def test_origin_default_stands_for_a_dangling_link(p: Path) -> None:
    _kept()
    layout.default_file(p).symlink_to(layout.kept_dir() / "nowhere")

    assert kept.default_stands(p)


def test_origin_keep_default_writes_the_name_and_a_newline(p: Path) -> None:
    _kept()

    kept.keep_default(p, "main")

    file = layout.default_file(p)
    assert file.read_text() == "main\n"
    assert _modes(file) == 0o600


def test_origin_keep_default_leaves_a_name_that_stands(p: Path) -> None:
    _kept()
    layout.default_file(p).write_text("dev")

    kept.keep_default(p, "main")

    assert kept.default(p) == "dev"


def test_origin_keep_default_in_a_folder_it_cannot_write_raises_unwritten(
    p: Path,
) -> None:
    folder = _kept()

    with _readonly(folder), pytest.raises(kept.Unwritten) as raised:
        kept.keep_default(p, "main")

    assert raised.value.strerror == "Permission denied"
    assert raised.value.filename == str(layout.default_file(p))


# --- the offline base


def test_base_reads_none_before_a_run_kept_it(p: Path) -> None:
    assert kept.base(p) is None
    assert not kept.base_stands(p)


@pytest.mark.parametrize(
    ("text", "read"),
    [
        (f"{_S}\n", _S),
        (f"  {_S}  \n\n", _S),
        ("", None),
        (" \n\t\n", None),
    ],
)
def test_base_reads_its_text_stripped(p: Path, text: str, read: str | None) -> None:
    _kept()
    layout.pushed_file(p).write_text(text)

    assert kept.base(p) == read
    assert kept.base_stands(p)


def test_base_stops_on_a_folder_at_its_name(p: Path) -> None:
    _kept()
    layout.pushed_file(p).mkdir()

    with pytest.raises(kept.Broken):
        kept.base(p)
    with pytest.raises(kept.Broken):
        kept.base_stands(p)


def test_base_keep_writes_the_sha_at_0600_in_a_folder_of_0700(p: Path) -> None:
    kept.keep_base(p, _S)

    file = layout.pushed_file(p)
    assert _modes(file.parent) == 0o700
    assert _modes(file) == 0o600
    assert file.read_text() == f"{_S}\n"
    assert [path.name for path in file.parent.iterdir()] == [file.name]


def test_base_keep_replaces_a_base_that_stands(p: Path) -> None:
    kept.keep_base(p, _S)

    kept.keep_base(p, _H)

    assert kept.base(p) == _H


def test_base_keep_in_a_folder_it_cannot_write_raises_unwritten(p: Path) -> None:
    folder = _kept()

    with _readonly(folder), pytest.raises(kept.Unwritten) as raised:
        kept.keep_base(p, _S)

    assert raised.value.strerror == "Permission denied"
    assert raised.value.filename == str(layout.pushed_file(p))


def test_base_keep_with_a_file_at_the_kept_folder_raises_refused(p: Path) -> None:
    _file_at_kept_folder()

    with pytest.raises(kept.Refused) as raised:
        kept.keep_base(p, _S)

    assert raised.value.errno == errno.EEXIST


# --- the release ledger


def test_ledger_records_an_entry_at_0600_in_a_folder_of_0700(p: Path) -> None:
    kept.record_release(p, "0001-a", _H)

    entry = layout.released_dir(p) / "0001-a"
    assert _modes(entry.parent) == 0o700
    assert _modes(entry) == 0o600
    assert entry.read_text() == f"{_H}\n"


def test_ledger_records_a_change_again_over_its_entry(p: Path) -> None:
    kept.record_release(p, "0001-a", _S)
    kept.record_release(p, "0002-b", _S)

    kept.record_release(p, "0001-a", _H)

    assert sorted(path.name for path in kept.release_entries(p)) == [
        "0001-a",
        "0002-b",
    ]
    assert (layout.released_dir(p) / "0001-a").read_text() == f"{_H}\n"


def test_ledger_a_folder_at_an_entry_raises_unwritten_naming_it(p: Path) -> None:
    entry = layout.released_dir(p) / "0001-a"
    (entry / "inner").mkdir(parents=True)

    with pytest.raises(kept.Unwritten) as raised:
        kept.record_release(p, "0001-a", _H)

    assert raised.value.filename == str(entry)


def test_ledger_with_a_file_at_the_kept_folder_raises_refused(p: Path) -> None:
    _file_at_kept_folder()

    with pytest.raises(kept.Refused):
        kept.record_release(p, "0001-a", _H)


def test_ledger_entries_are_none_with_no_folder(p: Path) -> None:
    assert kept.release_entries(p) == []


def test_ledger_entries_are_none_with_a_file_at_the_folder(p: Path) -> None:
    _kept()
    layout.released_dir(p).write_text("x\n")

    assert kept.release_entries(p) == []


def test_ledger_entries_list_every_name_of_the_folder(p: Path) -> None:
    folder = layout.released_dir(p)
    folder.mkdir(parents=True)
    for name in ("0001-a", "0002-b", ".hidden"):
        (folder / name).write_text(f"{_H}\n")

    assert sorted(path.name for path in kept.release_entries(p)) == [
        ".hidden",
        "0001-a",
        "0002-b",
    ]


def test_ledger_heads_are_each_entry_s_commit_id(p: Path) -> None:
    folder = layout.released_dir(p)
    folder.mkdir(parents=True)
    (folder / "a").write_text(f"{_H}\n")
    (folder / "b").write_text(_S)

    assert kept.release_heads(p) == kept.Heads({_H, _S}, [])


def test_ledger_heads_are_none_with_no_folder(p: Path) -> None:
    assert kept.release_heads(p) == kept.Heads(set(), [])


def test_ledger_close_removes_each_entry_whose_head_landed(p: Path) -> None:
    kept.record_release(p, "0001-a", _H)
    kept.record_release(p, "0002-b", _S)
    asked: list[str] = []

    def landed(head: str) -> bool:
        asked.append(head)
        return head == _H

    kept.close_releases(p, landed)

    assert sorted(asked) == sorted([_H, _S])
    assert [path.name for path in kept.release_entries(p)] == ["0002-b"]


def test_ledger_close_with_no_folder_is_quiet(p: Path) -> None:
    kept.close_releases(p, lambda _: True)

    assert kept.release_entries(p) == []


# --- the gate approval


def test_approval_approve_writes_the_hash_at_0600_in_a_folder_of_0700(
    p: Path,
) -> None:
    kept.approve(p, "0002-gate", _H)

    entry = layout.gate_approval(p, "0002-gate")
    assert _modes(entry.parent) == 0o700
    assert _modes(entry) == 0o600
    assert entry.read_text() == f"{_H}\n"


def test_approval_approve_again_replaces_the_entry(p: Path) -> None:
    kept.approve(p, "0002-gate", _S)

    kept.approve(p, "0002-gate", _H)

    assert kept.approval(p, "0002-gate") == _H


def test_approval_approve_in_a_folder_it_cannot_write_raises_unwritten(
    p: Path,
) -> None:
    entry = layout.gate_approval(p, "0002-gate")
    entry.parent.mkdir(parents=True)

    with _readonly(entry.parent), pytest.raises(kept.Unwritten) as raised:
        kept.approve(p, "0002-gate", _H)

    assert raised.value.strerror == "Permission denied"
    assert raised.value.filename == str(entry)


def test_approval_approve_with_a_file_at_the_kept_folder_raises_refused(
    p: Path,
) -> None:
    _file_at_kept_folder()

    with pytest.raises(kept.Refused) as raised:
        kept.approve(p, "0002-gate", _H)

    assert raised.value.errno == errno.EEXIST


def test_approval_reads_none_with_no_entry(p: Path) -> None:
    kept.approve(p, "0002-gate", _H)

    assert kept.approval(p, "0003-other") is None


@pytest.mark.parametrize(
    ("text", "read"),
    [(f"{_H}\nsecond\n", _H), (f"{_H} \n", f"{_H} "), ("", "")],
)
def test_approval_reads_the_entry_s_first_line(p: Path, text: str, read: str) -> None:
    entry = layout.gate_approval(p, "0002-gate")
    entry.parent.mkdir(parents=True)
    entry.write_text(text)

    assert kept.approval(p, "0002-gate") == read


def test_approval_reads_a_folder_at_the_entry_as_none(p: Path) -> None:
    layout.gate_approval(p, "0002-gate").mkdir(parents=True)

    assert kept.approval(p, "0002-gate") is None


# --- the live mark


def test_live_holder_is_none_with_no_mark(p: Path) -> None:
    assert kept.holder(layout.live_mark(p)) is None


@pytest.mark.parametrize("text", ["junk", "", "1", "0", "-5", "3999999", "9" * 30])
def test_live_holder_is_none_for_a_mark_no_live_process_holds(
    p: Path, text: str
) -> None:
    mark = layout.live_mark(p)
    mark.parent.mkdir(parents=True)
    mark.write_text(f"{text}\n")

    assert kept.holder(mark) is None


def test_live_holder_is_the_pid_of_a_live_process(p: Path) -> None:
    mark = layout.live_mark(p)
    mark.parent.mkdir(parents=True)

    with _other_process() as pid:
        mark.write_text(f"{pid}\n")

        assert kept.holder(mark) == pid


def test_live_holder_is_the_pid_of_a_process_it_may_not_signal(
    p: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mark = layout.live_mark(p)
    mark.parent.mkdir(parents=True)
    mark.write_text("4242\n")

    def refuse(*_: object) -> None:
        raise PermissionError(errno.EPERM, "Operation not permitted")

    monkeypatch.setattr(os, "kill", refuse)

    assert kept.holder(mark) == 4242


def test_live_lists_the_marks_a_live_process_holds_mine_aside() -> None:
    folder = layout.live_dir()
    folder.mkdir(parents=True)
    with _other_process() as pid:
        for name in ("a", "b"):
            (folder / name).write_text(f"{pid}\n")
        (folder / "c").write_text("junk\n")

        assert kept.live() == ["a", "b"]
        assert kept.live(folder / "a") == ["b"]


def test_live_lists_none_with_no_folder() -> None:
    assert kept.live() == []


def test_live_mark_writes_the_pid_in_folders_of_0700(p: Path) -> None:
    mark = kept.mark_live(p, 4242, 4241)

    assert mark == layout.live_mark(p)
    assert mark.read_text() == "4242\n"
    assert _modes(mark.parent) == 0o700
    assert _modes(mark.parent.parent) == 0o700


@pytest.mark.parametrize("held", ["own", "parent", "3999999", "junk"])
def test_live_mark_takes_over_a_mark_no_other_live_process_holds(
    p: Path, held: str
) -> None:
    own, parent = os.getpid(), os.getppid()
    text = {"own": str(own), "parent": str(parent)}.get(held, held)
    mark = layout.live_mark(p)
    mark.parent.mkdir(parents=True)
    mark.write_text(f"{text}\n")

    assert kept.mark_live(p, own, parent) == mark
    assert mark.read_text() == f"{own}\n"


def test_live_mark_leaves_a_mark_another_live_process_holds(p: Path) -> None:
    mark = layout.live_mark(p)
    mark.parent.mkdir(parents=True)

    with _other_process() as pid:
        mark.write_text(f"{pid}\n")

        assert kept.mark_live(p, os.getpid(), os.getppid()) is None
        assert mark.read_text() == f"{pid}\n"


def test_live_mark_with_a_file_at_the_kept_folder_is_none(p: Path) -> None:
    _file_at_kept_folder()

    assert kept.mark_live(p, os.getpid(), os.getppid()) is None


def test_live_unmark_removes_a_mark_holding_the_pid(p: Path) -> None:
    mark = kept.mark_live(p, os.getpid(), os.getppid())

    kept.unmark(mark, os.getpid())

    assert not layout.live_mark(p).exists()


def test_live_unmark_leaves_a_mark_holding_another_pid(p: Path) -> None:
    mark = kept.mark_live(p, os.getpid(), os.getppid())

    kept.unmark(mark, os.getppid())

    assert layout.live_mark(p).read_text() == f"{os.getpid()}\n"


def test_live_unmark_of_no_mark_is_quiet() -> None:
    kept.unmark(None, os.getpid())


# --- the list of repos


def test_repos_records_the_primary_resolved_at_0600(p: Path, tmp_path: Path) -> None:
    link = tmp_path / "link"
    link.symlink_to(p)

    kept.record_repo(link)

    file = layout.repos_file()
    assert file.read_text() == f"{p.resolve()}\n"
    assert _modes(file) == 0o600
    assert _modes(file.parent) == 0o700


def test_repos_records_a_primary_once(p: Path) -> None:
    kept.record_repo(p)

    kept.record_repo(p)

    assert layout.repos_file().read_text() == f"{p.resolve()}\n"


def test_repos_records_a_primary_a_longer_line_starts_with(p: Path) -> None:
    _kept()
    layout.repos_file().write_text(f"{p.resolve()}x\n")

    kept.record_repo(p)

    assert layout.repos_file().read_text().splitlines() == [
        f"{p.resolve()}x",
        str(p.resolve()),
    ]


def test_repos_with_a_file_at_the_kept_folder_records_nothing(p: Path) -> None:
    _file_at_kept_folder()

    kept.record_repo(p)

    assert layout.kept_dir().read_text() == "x\n"


# --- the probe mark


def test_probe_make_writes_an_empty_mark_at_0600_in_a_folder_of_0700() -> None:
    mark = kept.make_probe_mark("claude", 4242)

    assert mark == layout.probe_mark("claude", 4242)
    assert mark.read_bytes() == b""
    assert _modes(mark) == 0o600
    assert _modes(mark.parent) == 0o700


def test_probe_make_empties_a_stale_mark() -> None:
    stale = layout.probe_mark("claude", 4242)
    _kept()
    stale.write_text("junk")

    kept.make_probe_mark("claude", 4242)

    assert stale.read_bytes() == b""


def test_probe_make_in_a_folder_it_cannot_write_raises_unwritten() -> None:
    folder = _kept()

    with _readonly(folder), pytest.raises(kept.Unwritten) as raised:
        kept.make_probe_mark("claude", 4242)

    assert raised.value.strerror == "Permission denied"


def test_probe_make_with_a_file_at_the_kept_folder_raises_refused() -> None:
    _file_at_kept_folder()

    with pytest.raises(kept.Refused) as raised:
        kept.make_probe_mark("claude", 4242)

    assert raised.value.errno == errno.EEXIST


def test_probe_remove_removes_the_mark_and_a_gone_one_quietly() -> None:
    mark = kept.make_probe_mark("claude", 4242)

    kept.remove_probe_mark(mark)
    kept.remove_probe_mark(mark)

    assert not mark.exists()


def test_probe_executor_is_the_name_s_second_part() -> None:
    assert kept.probe_executor(layout.probe_mark("codex", 41)) == "codex"


def test_probe_untouched_holds_for_an_empty_mark_alone() -> None:
    mark = kept.make_probe_mark("claude", 4242)
    assert kept.probe_untouched(mark)

    mark.write_text("x")
    assert not kept.probe_untouched(mark)

    mark.unlink()
    assert not kept.probe_untouched(mark)

    mark.mkdir()
    assert not kept.probe_untouched(mark)


# --- each format, written by its writer and read by its reader


def test_roundtrip_the_kept_origin(p: Path) -> None:
    kept.keep_origin(p, _URLS)

    assert kept.origin(p) == _URLS


def test_roundtrip_the_default(p: Path) -> None:
    _kept()
    kept.keep_default(p, "trunk")

    assert kept.default(p) == "trunk"


def test_roundtrip_the_offline_base(p: Path) -> None:
    kept.keep_base(p, _S)

    assert kept.base(p) == _S


def test_roundtrip_a_ledger_entry(p: Path) -> None:
    kept.record_release(p, "0001-a", _H)

    assert kept.release_heads(p) == kept.Heads({_H}, [])


def test_roundtrip_an_approval(p: Path) -> None:
    kept.approve(p, "0002-gate", _H)

    assert kept.approval(p, "0002-gate") == _H


def test_roundtrip_a_live_mark(p: Path) -> None:
    mark = kept.mark_live(p, os.getpid(), os.getppid())

    assert mark is not None
    assert kept.holder(mark) == os.getpid()


def test_roundtrip_repos(p: Path) -> None:
    kept.record_repo(p)
    kept.record_repo(p)

    assert layout.repos_file().read_text().splitlines() == [str(p.resolve())]


# --- the one read and its failure


def _plant(path: Path, shape: str, text: str = "x\n", bound: int = kept.BOUND) -> None:
    """Make `path` a `shape`: a file, a link, a folder, a FIFO and so on."""
    if shape == "file":
        path.write_text(text)
    elif shape == "binary":
        path.write_bytes(b"\xff\xfe" + text.encode())
    elif shape == "big":
        path.write_text(text + " " * bound)
    elif shape == "unreadable":
        path.write_text(text)
        path.chmod(0)
    elif shape == "link":
        other = path.parent.parent / f".other-{path.name}"
        other.write_text(text)
        path.symlink_to(other)
    elif shape == "dangling":
        path.symlink_to(path.parent.parent / ".nowhere")
    elif shape == "folder":
        path.mkdir()
    else:
        assert shape == "pipe", shape
        os.mkfifo(path)


def test_read_a_missing_name_is_none(p: Path) -> None:
    assert kept._read(layout.kept_file(p)) is None


def test_read_a_file_at_its_bound_is_its_text(p: Path) -> None:
    _kept()
    file = layout.kept_file(p)
    file.write_text("a" * kept.BOUND)

    assert kept._read(file) == "a" * kept.BOUND


@pytest.mark.parametrize(
    ("shape", "phrase"),
    [
        ("link", "it is not a file"),
        ("dangling", "it is not a file"),
        ("folder", "it is not a file"),
        ("pipe", "it is not a file"),
        ("binary", "it is not text"),
        ("big", f"it is over {kept.BOUND} bytes"),
        ("unreadable", "Permission denied"),
    ],
)
def test_read_a_file_that_cannot_be_read_is_broken(
    p: Path, shape: str, phrase: str
) -> None:
    _kept()
    file = layout.kept_file(p)
    _plant(file, shape)

    with pytest.raises(kept.Broken) as raised:
        kept._read(file)

    said = f"~/.mf-ship-origin/{file.name} cannot be read: {phrase}"
    assert str(raised.value) == said
    assert raised.value.filename == str(file)
    assert isinstance(raised.value, OSError)


def test_read_names_a_ledger_entry_by_its_path_under_the_kept_folder(p: Path) -> None:
    entry = layout.released_dir(p) / "0001-a"
    entry.parent.mkdir(parents=True)
    entry.write_bytes(b"\xff\n")

    with pytest.raises(kept.Broken) as raised:
        kept._read(entry)

    assert str(raised.value) == (
        f"~/.mf-ship-origin/{entry.parent.name}/0001-a cannot be read: it is not text"
    )


def test_read_under_a_file_at_the_kept_folder_is_broken(p: Path) -> None:
    _file_at_kept_folder()

    with pytest.raises(kept.Broken, match="cannot be read: Not a directory"):
        kept._read(layout.kept_file(p))


# --- the kept origin, `.default` and the offline base stop on a broken file


@pytest.mark.parametrize(
    "text",
    ["", "not json", "{}", "[]", '[["u"]]', '[["u"], ["v"], []]', '[["u"], [1]]'],
)
def test_strict_origin_stops_on_what_is_no_pair_of_url_lists(
    p: Path, text: str
) -> None:
    _kept()
    layout.kept_file(p).write_text(text)

    with pytest.raises(kept.Broken, match=r"it is not a pair of URL lists$"):
        kept.origin(p)


def test_strict_origin_reads_a_pair_of_empty_lists(p: Path) -> None:
    _kept()
    layout.kept_file(p).write_text("[[], []]")

    assert kept.origin(p) == ([], [])


@pytest.mark.parametrize("shape", ["link", "folder", "pipe", "binary", "big"])
def test_strict_origin_stops_on_a_file_that_cannot_be_read(p: Path, shape: str) -> None:
    _kept()
    _plant(layout.kept_file(p), shape, "[[], []]")

    with pytest.raises(kept.Broken):
        kept.origin(p)


@pytest.mark.parametrize("shape", ["link", "dangling", "folder", "pipe"])
def test_strict_stands_stops_on_a_name_that_is_no_file(p: Path, shape: str) -> None:
    _kept()
    _plant(layout.kept_file(p), shape, "[[], []]")
    _plant(layout.pushed_file(p), shape, f"{_S}\n")

    with pytest.raises(kept.Broken, match=r"it is not a file$"):
        kept.origin_stands(p)
    with pytest.raises(kept.Broken, match=r"it is not a file$"):
        kept.base_stands(p)


def test_strict_stands_under_a_file_at_the_kept_folder_stops(p: Path) -> None:
    _file_at_kept_folder()

    with pytest.raises(kept.Broken, match=r"Not a directory$"):
        kept.origin_stands(p)


def test_strict_default_is_read_stripped(p: Path) -> None:
    _kept()
    layout.default_file(p).write_text(" trunk \n")

    assert kept.default(p) == "trunk"


@pytest.mark.parametrize("shape", ["link", "folder", "pipe", "binary", "big"])
def test_strict_default_stops_on_a_file_that_cannot_be_read(
    p: Path, shape: str
) -> None:
    _kept()
    _plant(layout.default_file(p), shape, "main\n")

    with pytest.raises(kept.Broken):
        kept.default(p)


@pytest.mark.parametrize(
    "text", ["abc\ndef\n", _S[:7], _S.upper(), f"{_S}\n{_H}\n", f"{_S}0"]
)
def test_strict_base_stops_on_what_is_no_commit_id(p: Path, text: str) -> None:
    _kept()
    layout.pushed_file(p).write_text(text)

    with pytest.raises(kept.Broken, match=r"it is not a commit id$"):
        kept.base(p)


@pytest.mark.parametrize("shape", ["link", "folder", "pipe", "binary", "big"])
def test_strict_base_stops_on_a_file_that_cannot_be_read(p: Path, shape: str) -> None:
    _kept()
    _plant(layout.pushed_file(p), shape, f"{_S}\n")

    with pytest.raises(kept.Broken):
        kept.base(p)


# --- an approval that cannot be read approves nothing


def test_bad_byte_approval_approves_nothing(p: Path) -> None:
    entry = layout.gate_approval(p, "0002-gate")
    entry.parent.mkdir(parents=True)
    entry.write_bytes(b"\xff\xfe\n")

    assert kept.approval(p, "0002-gate") is None
    entry.write_text(f"{_H}\n")
    assert kept.approval(p, "0002-gate") == _H


@pytest.mark.parametrize("shape", ["link", "pipe", "big", "unreadable"])
def test_bad_byte_approval_or_any_entry_that_cannot_be_read_approves_nothing(
    p: Path, shape: str
) -> None:
    entry = layout.gate_approval(p, "0002-gate")
    entry.parent.mkdir(parents=True)
    _plant(entry, shape, f"{_H}\n")

    assert kept.approval(p, "0002-gate") is None


# --- a ledger entry is one commit id


def _entries(p: Path, **texts: str) -> Path:
    """Write the ledger entries `texts`, by name; return the ledger's folder."""
    folder = layout.released_dir(p)
    folder.mkdir(parents=True, exist_ok=True)
    for name, text in texts.items():
        (folder / name).write_text(text)
    return folder


@pytest.mark.parametrize(
    "text",
    ["h1\nh1b\n", "h2 \n", "h3", "", f"{_H}\nsecond\n", _H[:7], _H.upper(), _H + _S],
)
def test_heads_an_entry_that_is_no_commit_id_is_named_bad(p: Path, text: str) -> None:
    _entries(p, a=text, b=f"{_S}\n")

    assert kept.release_heads(p) == kept.Heads({_S}, ["a"])


def test_heads_take_the_whole_text_stripped(p: Path) -> None:
    _entries(p, a=f"  {_S} \n\n")

    assert kept.release_heads(p) == kept.Heads({_S}, [])


def test_heads_name_each_bad_entry_in_order(p: Path) -> None:
    _entries(p, c="x", a="y", b=f"{_S}\n")

    assert kept.release_heads(p).bad == ["a", "c"]


@pytest.mark.parametrize("shape", ["link", "folder", "pipe", "binary", "big"])
def test_heads_an_entry_that_cannot_be_read_is_named_bad(p: Path, shape: str) -> None:
    folder = _entries(p)
    _plant(folder / "a", shape, f"{_H}\n")

    assert kept.release_heads(p) == kept.Heads(set(), ["a"])


def test_heads_close_leaves_an_entry_that_is_no_commit_id(p: Path) -> None:
    folder = _entries(p, a="abc\n", b=f"{_H}\n")
    asked: list[str] = []

    def landed(head: str) -> bool:
        asked.append(head)
        return True

    kept.close_releases(p, landed)

    assert asked == [_H]
    assert [entry.name for entry in folder.iterdir()] == ["a"]


# --- the kept origin and `.default` are written once


def _failing_replace(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make every `os.replace` fail with a full disk."""

    def full(*_: object, **__: object) -> None:
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(os, "replace", full)


def test_once_keep_origin_leaves_no_staged_file(p: Path) -> None:
    kept.keep_origin(p, _URLS)

    assert [path.name for path in layout.kept_dir().iterdir()] == [
        layout.kept_file(p).name
    ]


def test_once_keep_default_writes_a_newline_and_reads_stripped(p: Path) -> None:
    kept.keep_default(p, "main")

    assert layout.default_file(p).read_bytes() == b"main\n"
    assert kept.default(p) == "main"


@pytest.mark.parametrize("shape", ["file", "link", "dangling", "folder"])
def test_once_keep_leaves_a_name_that_stands(p: Path, shape: str) -> None:
    _kept()
    origin, named = layout.kept_file(p), layout.default_file(p)
    _plant(origin, shape, '[["old"], ["old"]]')
    _plant(named, shape, "dev\n")
    before = {path: os.lstat(path) for path in (origin, named)}

    kept.keep_origin(p, _URLS)
    kept.keep_default(p, "main")

    for path, held in before.items():
        now = os.lstat(path)
        assert (now.st_mode, now.st_ino, now.st_size) == (
            held.st_mode,
            held.st_ino,
            held.st_size,
        )
    assert not (layout.kept_dir().parent / ".nowhere").exists()


def test_once_a_failed_keep_raises_unwritten_and_leaves_nothing(
    p: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _kept()
    _failing_replace(monkeypatch)

    with pytest.raises(kept.Unwritten) as raised:
        kept.keep_origin(p, _URLS)
    with pytest.raises(kept.Unwritten):
        kept.keep_default(p, "main")

    assert raised.value.strerror == "No space left on device"
    assert raised.value.filename == str(layout.kept_file(p))
    assert list(layout.kept_dir().iterdir()) == []


# --- the offline base, a ledger entry, an approval and the live mark are staged


_STAGED = {
    "base": (lambda p: kept.keep_base(p, _S), layout.pushed_file),
    "ledger": (
        lambda p: kept.record_release(p, "0001-a", _H),
        lambda p: layout.released_dir(p) / "0001-a",
    ),
    "approval": (
        lambda p: kept.approve(p, "0002-gate", _H),
        lambda p: layout.gate_approval(p, "0002-gate"),
    ),
    "live": (
        lambda p: kept.mark_live(p, os.getpid(), os.getppid()),
        layout.live_mark,
    ),
}


@contextlib.contextmanager
def _umask(mask: int) -> Iterator[None]:
    """Hold the process's umask at `mask`."""
    before = os.umask(mask)
    try:
        yield
    finally:
        os.umask(before)


@pytest.mark.parametrize("name", list(_STAGED))
def test_staged_write_makes_each_folder_0700_and_the_file_0600(
    p: Path, name: str
) -> None:
    write, where = _STAGED[name]

    with _umask(0o022):
        write(p)

    file = where(p)
    assert _modes(file) == 0o600
    assert _modes(file.parent) == 0o700
    assert _modes(layout.kept_dir()) == 0o700
    assert [path.name for path in file.parent.iterdir()] == [file.name]


@pytest.mark.parametrize("name", list(_STAGED))
def test_staged_write_leaves_the_mode_of_the_kept_folder(p: Path, name: str) -> None:
    write, _ = _STAGED[name]
    _kept().chmod(0o755)

    write(p)

    assert _modes(layout.kept_dir()) == 0o755


@pytest.mark.parametrize("name", list(_STAGED))
def test_staged_write_that_fails_leaves_no_staged_file(
    p: Path, name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    write, where = _STAGED[name]
    folder = where(p).parent
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    _failing_replace(monkeypatch)

    with contextlib.suppress(kept.Unwritten):
        write(p)

    assert list(folder.iterdir()) == []


@pytest.mark.parametrize("name", list(_STAGED))
def test_staged_write_replaces_a_link_and_leaves_its_target(
    p: Path, name: str, tmp_path: Path
) -> None:
    write, where = _STAGED[name]
    file = where(p)
    file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    target = tmp_path / "target"
    target.write_text("the person's\n")
    file.symlink_to(target)

    write(p)

    assert not file.is_symlink()
    assert target.read_text() == "the person's\n"


@pytest.mark.parametrize("name", ["ledger", "approval", "live"])
def test_staged_write_refuses_a_link_at_its_folder(
    p: Path, name: str, tmp_path: Path
) -> None:
    write, where = _STAGED[name]
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    _kept()
    where(p).parent.symlink_to(elsewhere)

    with contextlib.suppress(kept.Refused):
        write(p)

    assert list(elsewhere.iterdir()) == []


# --- `repos`, the live mark: a file that cannot be read is none


@pytest.mark.parametrize(
    "shape", ["binary", "big", "link", "dangling", "folder", "pipe", "unreadable"]
)
def test_lenient_repos_that_cannot_be_read_takes_no_append(p: Path, shape: str) -> None:
    _kept()
    repos = layout.repos_file()
    _plant(repos, shape, "/elsewhere\n", bound=kept.REPOS_BOUND)
    other = repos.parent.parent / f".other-{repos.name}"
    held = os.lstat(repos)

    kept.record_repo(p)

    now = os.lstat(repos)
    assert (now.st_mode, now.st_size) == (held.st_mode, held.st_size)
    assert not other.exists() or other.read_text() == "/elsewhere\n"
    assert not (repos.parent.parent / ".nowhere").exists()


def test_lenient_repos_at_its_bound_takes_the_append(p: Path) -> None:
    _kept()
    repos = layout.repos_file()
    listed = "/elsewhere\n".ljust(kept.REPOS_BOUND)
    repos.write_text(listed)

    kept.record_repo(p)

    assert repos.read_text() == f"{listed}{p.resolve()}\n"


@pytest.mark.parametrize("shape", ["binary", "big", "link", "folder", "pipe"])
def test_lenient_holder_reads_a_mark_that_cannot_be_read_as_none(
    p: Path, shape: str
) -> None:
    mark = layout.live_mark(p)
    mark.parent.mkdir(parents=True)
    _plant(mark, shape, f"{os.getpid()}\n")

    assert kept.holder(mark) is None


def test_lenient_live_lists_none_through_a_link_at_its_folder(tmp_path: Path) -> None:
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / "a").write_text(f"{os.getpid()}\n")
    _kept()
    layout.live_dir().symlink_to(elsewhere)

    assert kept.live() == []


def test_lenient_live_lists_none_under_a_file_at_the_kept_folder() -> None:
    _file_at_kept_folder()

    assert kept.live() == []


# --- a removal is by name under its folder's descriptor


def test_unlink_close_through_a_link_at_its_folder_removes_nothing(
    p: Path, tmp_path: Path
) -> None:
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / "0001-a").write_text(f"{_H}\n")
    _kept()
    layout.released_dir(p).symlink_to(elsewhere)

    kept.close_releases(p, lambda _: True)

    assert [path.name for path in elsewhere.iterdir()] == ["0001-a"]


def test_unlink_unmark_through_a_link_at_its_folder_removes_nothing(
    p: Path, tmp_path: Path
) -> None:
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / layout.digest(p)).write_text(f"{os.getpid()}\n")
    _kept()
    layout.live_dir().symlink_to(elsewhere)

    kept.unmark(layout.live_mark(p), os.getpid())

    assert [path.name for path in elsewhere.iterdir()] == [layout.digest(p)]


def test_unlink_remove_probe_mark_under_a_file_at_the_kept_folder_is_quiet() -> None:
    _file_at_kept_folder()

    kept.remove_probe_mark(layout.probe_mark("claude", 4242))

    assert layout.kept_dir().read_text() == "x\n"


def test_unlink_make_probe_mark_unlinks_a_link_and_leaves_its_target(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target"
    target.write_text("the person's\n")
    _kept()
    stale = layout.probe_mark("claude", 4242)
    stale.symlink_to(target)

    mark = kept.make_probe_mark("claude", 4242)

    assert not mark.is_symlink()
    assert mark.read_bytes() == b""
    assert _modes(mark) == 0o600
    assert target.read_text() == "the person's\n"
