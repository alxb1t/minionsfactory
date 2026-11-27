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


def test_origin_reads_a_folder_at_its_name_as_none(p: Path) -> None:
    _kept()
    layout.kept_file(p).mkdir()

    assert kept.origin(p) is None
    assert not kept.origin_stands(p)


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


def test_origin_default_reads_its_text_unstripped(p: Path) -> None:
    _kept()
    layout.default_file(p).write_text("dev\n")

    assert kept.default(p) == "dev\n"
    assert kept.default_stands(p)


def test_origin_default_reads_a_folder_at_its_name_as_none(p: Path) -> None:
    _kept()
    layout.default_file(p).mkdir()

    assert kept.default(p) is None
    assert kept.default_stands(p)


def test_origin_default_stands_not_for_a_dangling_link(p: Path) -> None:
    _kept()
    layout.default_file(p).symlink_to(layout.kept_dir() / "nowhere")

    assert not kept.default_stands(p)


def test_origin_keep_default_writes_the_name_with_no_newline(p: Path) -> None:
    _kept()

    kept.keep_default(p, "main")

    file = layout.default_file(p)
    assert file.read_text() == "main"
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
        ("abc\ndef\n", "abc\ndef"),
        ("", None),
        (" \n\t\n", None),
    ],
)
def test_base_reads_its_text_stripped(p: Path, text: str, read: str | None) -> None:
    _kept()
    layout.pushed_file(p).write_text(text)

    assert kept.base(p) == read
    assert kept.base_stands(p)


def test_base_reads_a_folder_at_its_name_as_none(p: Path) -> None:
    _kept()
    layout.pushed_file(p).mkdir()

    assert kept.base(p) is None
    assert not kept.base_stands(p)


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


def test_ledger_heads_are_each_entry_s_first_line(p: Path) -> None:
    folder = layout.released_dir(p)
    folder.mkdir(parents=True)
    for name, text in (("a", "h1\nh1b\n"), ("b", "h2 \n"), ("c", "h3"), ("d", "")):
        (folder / name).write_text(text)

    assert kept.release_heads(p) == kept.Heads({"h1", "h2 ", "h3", ""}, [])


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

    assert raised.value.errno == errno.ENOTDIR


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
