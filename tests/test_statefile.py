"""The staged write and the no-follow read of the home, each argument value a case.

Why: 0136-status-log design D3, D4 and D5, and its differences.
"""

import errno
import os
import stat
import threading
from pathlib import Path
from unittest import mock

import pytest
from mflib import claim, findings, layout, marks, modelsfile, runlog, statefile

_OLD = "the old text\n"
_TEXT = "the new text\n"
_CHANGE = "0001-a"


def _staged(target: Path) -> Path:
    return target.with_name(f"{target.name}.tmp")


def _plant_at_create(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make a file at `.tmp` between the clear and the create, through the module."""
    real = os.open

    def planting(path: Path, flags: int, mode: int = 0o777, **at: int) -> int:
        if Path(path).name.endswith(".tmp") and flags & os.O_EXCL:
            Path(path).write_text("planted\n")
        return real(path, flags, mode, **at)

    monkeypatch.setattr(statefile.os, "open", planting)


def test_a_write_replaces_the_file_with_a_new_one_of_mode_0644(tmp_path: Path) -> None:
    target = tmp_path / "state.md"
    target.write_text(_OLD)
    hard = tmp_path / "hard"
    os.link(target, hard)
    umask = os.umask(0o022)
    try:
        statefile.write(target, _TEXT)
    finally:
        os.umask(umask)

    assert target.read_text() == _TEXT
    assert stat.S_IMODE(target.stat().st_mode) == 0o644
    assert hard.read_text() == _OLD
    assert not os.path.lexists(_staged(target))


def test_a_write_takes_the_mode_it_is_given(tmp_path: Path) -> None:
    target = tmp_path / "state.md"

    statefile.write(target, _TEXT, mode=0o600)

    assert stat.S_IMODE(target.stat().st_mode) == 0o600


def test_a_write_clears_a_stale_tmp_that_links_outside(tmp_path: Path) -> None:
    target = tmp_path / "state.md"
    outside = tmp_path / "outside"
    outside.write_text(_OLD)
    _staged(target).symlink_to(outside)

    statefile.write(target, _TEXT)

    assert target.read_text() == _TEXT
    assert outside.read_text() == _OLD


def test_refuse_link_true_refuses_a_link_at_the_target(tmp_path: Path) -> None:
    target = tmp_path / "state.md"
    outside = tmp_path / "outside"
    outside.write_text(_OLD)
    target.symlink_to(outside)

    with pytest.raises(statefile.WriteFailed) as failed:
        statefile.write(target, _TEXT, refuse_link=True)

    assert failed.value.step == "replace"
    assert failed.value.error.errno == errno.ELOOP
    assert target.is_symlink()
    assert outside.read_text() == _OLD
    assert not os.path.lexists(_staged(target))


@pytest.mark.parametrize("code", [errno.ENOTDIR, errno.EACCES])
def test_refuse_link_true_raises_a_failed_link_check_as_a_create_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, code: int
) -> None:
    # Why: 0136-status-log converge card S1: a parent a file, or one not searched.
    parent = tmp_path / "parent"
    parent.write_text(_OLD)
    if code == errno.EACCES:
        parent.unlink()
        parent.mkdir()
        denied = OSError(code, os.strerror(code))
        monkeypatch.setattr(statefile.os, "stat", mock.Mock(side_effect=denied))

    with pytest.raises(statefile.WriteFailed) as failed:
        statefile.write(parent / "state.md", _TEXT, refuse_link=True)

    assert failed.value.step == "create"
    assert failed.value.error.errno == code
    assert not os.path.lexists(parent / "state.md.tmp")


def test_refuse_link_true_writes_a_missing_target(tmp_path: Path) -> None:
    target = tmp_path / "state.md"

    statefile.write(target, _TEXT, refuse_link=True)

    assert target.read_text() == _TEXT


def test_write_or_say_writes_and_says_nothing(tmp_path: Path) -> None:
    target = tmp_path / "state.md"

    assert statefile.write_or_say(target, _TEXT) is None
    assert target.read_text() == _TEXT


def test_write_or_say_names_a_link(tmp_path: Path) -> None:
    target = tmp_path / "state.md"
    outside = tmp_path / "outside"
    outside.write_text(_OLD)
    target.symlink_to(outside)

    assert statefile.write_or_say(target, _TEXT) == f"{target} is a link"
    assert outside.read_text() == _OLD


def test_write_or_say_gives_another_failure_its_reason(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    parent.write_text(_OLD)

    said = statefile.write_or_say(parent / "state.md", _TEXT)

    assert said == f"{parent / 'state.md'}: {os.strerror(errno.ENOTDIR)}"


def test_refuse_link_false_replaces_a_link_at_the_target(tmp_path: Path) -> None:
    target = tmp_path / "state.md"
    outside = tmp_path / "outside"
    outside.write_text(_OLD)
    target.symlink_to(outside)

    statefile.write(target, _TEXT, refuse_link=False)

    assert not target.is_symlink()
    assert target.read_text() == _TEXT
    assert outside.read_text() == _OLD


def test_a_file_made_at_the_tmp_between_the_clear_and_the_create_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "state.md"
    target.write_text(_OLD)
    _plant_at_create(monkeypatch)

    with pytest.raises(statefile.WriteFailed) as failed:
        statefile.write(target, _TEXT)

    monkeypatch.undo()
    assert failed.value.step == "create"
    assert failed.value.error.errno == errno.EEXIST
    assert target.read_text() == _OLD
    assert not os.path.lexists(_staged(target))


def test_a_failed_rename_is_a_replace_failure(tmp_path: Path) -> None:
    target = tmp_path / "state.md"
    target.mkdir()
    (target / "kept").write_text("kept\n")

    with pytest.raises(statefile.WriteFailed) as failed:
        statefile.write(target, _TEXT)

    assert failed.value.step == "replace"
    assert isinstance(failed.value.error, IsADirectoryError)
    assert (target / "kept").read_text() == "kept\n"
    assert not os.path.lexists(_staged(target))


def test_a_write_and_a_read_go_through_the_folder_given(tmp_path: Path) -> None:
    held = tmp_path / "held"
    held.mkdir()
    fd = os.open(held, os.O_RDONLY | os.O_DIRECTORY)
    try:
        statefile.write(Path("state.md"), _TEXT, folder=fd)
        assert statefile.read("state.md", folder=fd) == _TEXT
        (held / "link").symlink_to(held / "state.md")
        with pytest.raises(statefile.WriteFailed):
            statefile.write(Path("link"), _TEXT, refuse_link=True, folder=fd)
    finally:
        os.close(fd)

    assert (held / "state.md").read_text() == _TEXT
    assert not (tmp_path / "state.md").exists()


def test_a_read_takes_a_limit_and_a_tail(tmp_path: Path) -> None:
    path = tmp_path / "state.md"
    path.write_bytes(b"abcdef")

    assert statefile.read_bytes(path) == b"abcdef"
    assert statefile.read_bytes(path, limit=4) == b"abcd"
    assert statefile.read_bytes(path, limit=4, tail=True) == b"cdef"
    assert statefile.read_bytes(path, limit=9, tail=True) == b"abcdef"


def test_a_read_replaces_a_bad_byte(tmp_path: Path) -> None:
    path = tmp_path / "state.md"
    path.write_bytes(b"a\xffb")

    assert statefile.read(path) == "a�b"


def test_a_link_at_a_read_raises_eloop(tmp_path: Path) -> None:
    path = tmp_path / "state.md"
    outside = tmp_path / "outside"
    outside.write_text(_OLD)
    path.symlink_to(outside)

    with pytest.raises(OSError, match="symbolic links") as raised:
        statefile.read(path)

    assert raised.value.errno == errno.ELOOP


def test_a_missing_file_raises_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        statefile.read_bytes(tmp_path / "gone")


def test_a_fifo_at_a_guarded_read_raises_inside_ten_seconds(tmp_path: Path) -> None:
    pipe = tmp_path / "pipe"
    os.mkfifo(pipe)
    said: list[object] = []

    def run() -> None:
        try:
            said.append(statefile.read(pipe))
        except OSError as error:
            said.append(error)

    reader = threading.Thread(target=run, daemon=True)
    reader.start()
    # A FIFO opened blocking waits for a writer: the join bounds a red run.
    reader.join(timeout=10)

    assert not reader.is_alive()
    [error] = said
    assert isinstance(error, OSError)
    assert error.errno == errno.EINVAL


def test_guard_decides_whether_a_file_that_is_no_regular_file_is_read() -> None:
    with pytest.raises(OSError, match="not a file"):
        statefile.read_bytes(os.devnull)


def test_a_read_takes_an_offset(tmp_path: Path) -> None:
    path = tmp_path / "state.md"
    path.write_bytes(b"abcdef")

    assert statefile.read_bytes(path, offset=2) == b"cdef"
    assert statefile.read_bytes(path, offset=2, limit=3) == b"cde"
    assert statefile.read_bytes(path, offset=4, limit=3, tail=True) == b"ef"
    assert statefile.read_bytes(path, offset=1, limit=3, tail=True) == b"def"
    assert statefile.read_bytes(path, offset=9) == b""
    assert statefile.read(path, offset=3) == "def"


def test_append_adds_its_text_at_the_end_in_one_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "state.md"
    path.write_text(_OLD)
    writes = mock.Mock(wraps=os.write)
    monkeypatch.setattr(statefile.os, "write", writes)

    statefile.append(path, _TEXT)

    assert path.read_text() == _OLD + _TEXT
    assert writes.call_count == 1


def test_append_makes_no_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        statefile.append(tmp_path / "gone", _TEXT)

    assert not (tmp_path / "gone").exists()


def test_append_refuses_a_link(tmp_path: Path) -> None:
    path = tmp_path / "state.md"
    outside = tmp_path / "outside"
    outside.write_text(_OLD)
    path.symlink_to(outside)

    with pytest.raises(OSError, match="symbolic links") as raised:
        statefile.append(path, _TEXT)

    assert raised.value.errno == errno.ELOOP
    assert outside.read_text() == _OLD


def test_append_refuses_a_pipe_inside_ten_seconds(tmp_path: Path) -> None:
    pipe = tmp_path / "pipe"
    os.mkfifo(pipe)
    reader = os.open(pipe, os.O_RDONLY | os.O_NONBLOCK)
    said: list[OSError] = []

    def run() -> None:
        try:
            statefile.append(pipe, _TEXT)
        except OSError as error:
            said.append(error)

    writer = threading.Thread(target=run, daemon=True)
    writer.start()
    writer.join(timeout=10)
    try:
        assert not writer.is_alive()
        [error] = said
        assert error.errno == errno.EINVAL
        assert os.read(reader, 64) == b""
    finally:
        os.close(reader)


def test_append_goes_through_the_folder_given(tmp_path: Path) -> None:
    held = tmp_path / "held"
    held.mkdir()
    (held / "state.md").write_text(_OLD)
    fd = os.open(held, os.O_RDONLY | os.O_DIRECTORY)
    try:
        statefile.append("state.md", _TEXT, folder=fd)
    finally:
        os.close(fd)

    assert (held / "state.md").read_text() == _OLD + _TEXT
    assert not (tmp_path / "state.md").exists()


def test_open_regular_returns_a_descriptor_on_the_file(tmp_path: Path) -> None:
    held = tmp_path / "held"
    held.mkdir()
    (held / "state.md").write_text(_OLD)
    folder = os.open(held, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fd = statefile.open_regular("state.md", folder=folder)
    finally:
        os.close(folder)
    try:
        assert os.pread(fd, 64, 0) == _OLD.encode()
    finally:
        os.close(fd)


def test_open_regular_refuses_a_link_and_a_pipe(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.write_text(_OLD)
    (tmp_path / "link").symlink_to(outside)
    os.mkfifo(tmp_path / "pipe")

    with pytest.raises(OSError, match="symbolic links") as linked:
        statefile.open_regular(tmp_path / "link")
    with pytest.raises(OSError, match="not a file") as piped:
        statefile.open_regular(tmp_path / "pipe")

    assert linked.value.errno == errno.ELOOP
    assert piped.value.errno == errno.EINVAL


def test_open_regular_and_append_refuse_a_second_name_when_asked(
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside"
    outside.write_text(_OLD)
    os.link(outside, tmp_path / "hard")

    for call in (
        lambda: statefile.open_regular(tmp_path / "hard", one_name=True),
        lambda: statefile.append(tmp_path / "hard", _TEXT, one_name=True),
    ):
        with pytest.raises(OSError, match="one name") as refused:
            call()
        assert refused.value.errno == errno.EINVAL
    assert outside.read_text() == _OLD
    os.close(statefile.open_regular(tmp_path / "hard"))


def test_open_regular_closes_the_descriptor_it_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    os.mkfifo(tmp_path / "pipe")
    closes = mock.Mock(wraps=os.close)
    monkeypatch.setattr(statefile.os, "close", closes)

    with pytest.raises(OSError, match="not a file"):
        statefile.open_regular(tmp_path / "pipe")

    assert closes.call_count == 1


def test_folder_makes_each_part_and_refuses_a_link(tmp_path: Path) -> None:
    root = tmp_path / "root"
    fd = statefile.folder(root, "a", "b")
    try:
        assert os.path.samestat(os.fstat(fd), (root / "a" / "b").stat())
    finally:
        os.close(fd)
    (root / "c").symlink_to(root / "a")

    with pytest.raises(OSError, match=r"symbolic links|Not a directory"):
        statefile.folder(root, "c")


def test_folder_follows_a_link_at_its_root(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    (tmp_path / "root").symlink_to(real)

    fd = statefile.folder(tmp_path / "root", "a")
    os.close(fd)

    assert (real / "a").is_dir()


def test_open_folder_returns_a_descriptor_on_the_folder(tmp_path: Path) -> None:
    (tmp_path / "a" / "b").mkdir(parents=True)
    fd = statefile.open_folder(tmp_path, "a", "b")
    try:
        assert os.path.samestat(os.fstat(fd), (tmp_path / "a" / "b").stat())
    finally:
        os.close(fd)


def test_open_folder_raises_file_not_found_on_a_missing_part_and_makes_nothing(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    (root / "a").mkdir(parents=True)

    with pytest.raises(FileNotFoundError):
        statefile.open_folder(root, "a", "b", "c")
    with pytest.raises(FileNotFoundError):
        statefile.open_folder(root / "gone", "a")

    assert sorted(root.rglob("*")) == [root / "a"]


def test_open_folder_raises_eloop_on_a_link_at_a_part(tmp_path: Path) -> None:
    (tmp_path / "real").mkdir()
    (tmp_path / "link").symlink_to(tmp_path / "real")

    with pytest.raises(OSError, match="symbolic links") as raised:
        statefile.open_folder(tmp_path, "link")

    assert raised.value.errno == errno.ELOOP


def test_open_folder_raises_not_a_directory_on_a_file_at_a_part(tmp_path: Path) -> None:
    (tmp_path / "file").write_text("x")

    with pytest.raises(NotADirectoryError):
        statefile.open_folder(tmp_path, "file")


def test_open_folder_follows_a_link_at_its_root(tmp_path: Path) -> None:
    (tmp_path / "real" / "a").mkdir(parents=True)
    (tmp_path / "root").symlink_to(tmp_path / "real")

    fd = statefile.open_folder(tmp_path / "root", "a")
    try:
        assert os.path.samestat(os.fstat(fd), (tmp_path / "real" / "a").stat())
    finally:
        os.close(fd)


def _linked_home(tmp_path: Path) -> tuple[Path, Path]:
    """Return a primary whose `.minions` is a link, and the folder outside it names."""
    primary, outside = tmp_path / "primary", tmp_path / "outside"
    primary.mkdir()
    outside.mkdir()
    (primary / layout.MINIONS).symlink_to(outside)
    return primary, outside


def test_marks_follows_a_link_at_minions(tmp_path: Path) -> None:
    primary, outside = _linked_home(tmp_path)

    marks.write(primary, _CHANGE, marks.BUILD_DONE, _TEXT)

    assert (outside / "changes" / _CHANGE / marks.BUILD_DONE).read_text() == _TEXT


def test_modelsfile_follows_a_link_at_minions(tmp_path: Path) -> None:
    primary, outside = _linked_home(tmp_path)

    modelsfile.write(primary, _CHANGE, _TEXT)

    assert (outside / "changes" / _CHANGE / layout.MODELS).read_text() == _TEXT


def test_findings_follows_a_link_at_minions(tmp_path: Path) -> None:
    primary, outside = _linked_home(tmp_path)
    held = outside / "changes" / _CHANGE
    held.mkdir(parents=True)
    (held / "conformance.md").write_text("---\nmodel: x\n---\nbody\n")

    findings.stamp(layout.change_dir(primary, _CHANGE), "conformance.md", "m", 5)

    stamped = (held / "conformance.md").read_text()
    assert stamped == "---\nmodel: m\ntokens: 5\n---\nbody\n"


def test_claim_follows_a_link_at_minions(tmp_path: Path) -> None:
    primary, outside = _linked_home(tmp_path)

    claim.take(layout.claim_file(primary))

    assert (outside / "runs" / "active").is_dir()


def test_runlog_follows_a_link_at_minions(tmp_path: Path) -> None:
    primary, outside = _linked_home(tmp_path)
    log = outside / "runs" / "20261101-100000.md"
    log.parent.mkdir()
    log.write_text(f"{runlog.title('20261101-100000')}\n\n")

    stopped = runlog.stop(layout.runs_dir(primary))

    assert stopped == layout.runs_dir(primary) / log.name
    assert log.read_text().endswith(f" · run · halt — {runlog.STOPPED}\n")
