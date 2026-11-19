"""The staged write and the no-follow read of the home, each argument value a case.

Why: 0136-status-log design D3, D4 and D5, and its differences.
"""

import errno
import os
import stat
import threading
from pathlib import Path

import pytest
from mflib import statefile

_OLD = "the old text\n"
_TEXT = "the new text\n"


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
        statefile.write(target, _TEXT, remove="any")
    finally:
        os.umask(umask)

    assert target.read_text() == _TEXT
    assert stat.S_IMODE(target.stat().st_mode) == 0o644
    assert hard.read_text() == _OLD
    assert not os.path.lexists(_staged(target))


def test_a_write_takes_the_mode_it_is_given(tmp_path: Path) -> None:
    target = tmp_path / "state.md"

    statefile.write(target, _TEXT, remove="any", mode=0o600)

    assert stat.S_IMODE(target.stat().st_mode) == 0o600


def test_a_write_clears_a_stale_tmp_that_links_outside(tmp_path: Path) -> None:
    target = tmp_path / "state.md"
    outside = tmp_path / "outside"
    outside.write_text(_OLD)
    _staged(target).symlink_to(outside)

    statefile.write(target, _TEXT, remove="never")

    assert target.read_text() == _TEXT
    assert outside.read_text() == _OLD


def test_refuse_link_true_refuses_a_link_at_the_target(tmp_path: Path) -> None:
    target = tmp_path / "state.md"
    outside = tmp_path / "outside"
    outside.write_text(_OLD)
    target.symlink_to(outside)

    with pytest.raises(statefile.WriteFailed) as failed:
        statefile.write(target, _TEXT, refuse_link=True, remove="any")

    assert failed.value.step == "replace"
    assert failed.value.error.errno == errno.ELOOP
    assert target.is_symlink()
    assert outside.read_text() == _OLD
    assert not os.path.lexists(_staged(target))


def test_refuse_link_true_writes_a_missing_target(tmp_path: Path) -> None:
    target = tmp_path / "state.md"

    statefile.write(target, _TEXT, refuse_link=True, remove="any")

    assert target.read_text() == _TEXT


def test_refuse_link_false_replaces_a_link_at_the_target(tmp_path: Path) -> None:
    target = tmp_path / "state.md"
    outside = tmp_path / "outside"
    outside.write_text(_OLD)
    target.symlink_to(outside)

    statefile.write(target, _TEXT, refuse_link=False, remove="any")

    assert not target.is_symlink()
    assert target.read_text() == _TEXT
    assert outside.read_text() == _OLD


@pytest.mark.parametrize(
    ("remove", "leaves"), [("any", False), ("rename", True), ("never", True)]
)
def test_a_file_made_at_the_tmp_between_the_clear_and_the_create_is_refused(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    remove: statefile.Removal,
    leaves: bool,
) -> None:
    target = tmp_path / "state.md"
    target.write_text(_OLD)
    _plant_at_create(monkeypatch)

    with pytest.raises(statefile.WriteFailed) as failed:
        statefile.write(target, _TEXT, remove=remove)

    monkeypatch.undo()
    assert failed.value.step == "create"
    assert failed.value.error.errno == errno.EEXIST
    assert target.read_text() == _OLD
    assert os.path.lexists(_staged(target)) == leaves


@pytest.mark.parametrize(
    ("remove", "leaves"), [("any", False), ("rename", False), ("never", True)]
)
def test_a_failed_rename_is_a_replace_failure(
    tmp_path: Path, remove: statefile.Removal, leaves: bool
) -> None:
    target = tmp_path / "state.md"
    target.mkdir()
    (target / "kept").write_text("kept\n")

    with pytest.raises(statefile.WriteFailed) as failed:
        statefile.write(target, _TEXT, remove=remove)

    assert failed.value.step == "replace"
    assert isinstance(failed.value.error, IsADirectoryError)
    assert (target / "kept").read_text() == "kept\n"
    assert os.path.lexists(_staged(target)) == leaves


def test_a_write_and_a_read_go_through_the_folder_given(tmp_path: Path) -> None:
    held = tmp_path / "held"
    held.mkdir()
    fd = os.open(held, os.O_RDONLY | os.O_DIRECTORY)
    try:
        statefile.write(Path("state.md"), _TEXT, remove="any", folder=fd)
        assert statefile.read("state.md", folder=fd) == _TEXT
        (held / "link").symlink_to(held / "state.md")
        with pytest.raises(statefile.WriteFailed):
            statefile.write(
                Path("link"), _TEXT, refuse_link=True, remove="any", folder=fd
            )
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


@pytest.mark.parametrize("guard", [True, False])
def test_a_link_at_a_read_raises_eloop(tmp_path: Path, guard: bool) -> None:
    path = tmp_path / "state.md"
    outside = tmp_path / "outside"
    outside.write_text(_OLD)
    path.symlink_to(outside)

    with pytest.raises(OSError, match="symbolic links") as raised:
        statefile.read(path, guard=guard)

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


@pytest.mark.parametrize(("guard", "takes"), [(True, False), (False, True)])
def test_guard_decides_whether_a_file_that_is_no_regular_file_is_read(
    guard: bool, takes: bool
) -> None:
    if takes:
        assert statefile.read_bytes(os.devnull, guard=guard) == b""
    else:
        with pytest.raises(OSError, match="not a file"):
            statefile.read_bytes(os.devnull, guard=guard)


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
