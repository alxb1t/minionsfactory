"""Pins of the queue as the conductor locks, lists, reads, writes and requests it.

Each case holds the one side and starts no worker. A comment `# mutant:` names the
change to the source that turns a case red. Why: 0156-queue design D9.
"""

import contextlib
import json
import os
import stat
import subprocess
import sys
import threading
import types
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from conduct_load import conduct as _conduct
from fake_worker import _commit, _git
from mflib import layout
from test_conduct import (
    _MODELS,
    _claimed,
    _idle_machine,  # noqa: F401
    _items,
    _no_codex_sessions,  # noqa: F401
    _primary,
    _swap_runner,
    _version,
    ps,  # noqa: F401
)

_BOUND = 262144
_UNREADABLE = {"halt": "the queue entry is unreadable"}
_REFUSED = "conduct: cannot run — the home folder refuses the queue: "
_SANDBOX = "; run it outside a sandbox"
_SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "mf-ship"
    / "scripts"
    / "conduct.py"
)
_CHILD = (
    "import json, runpy, sys\n"
    "from pathlib import Path\n"
    "names = runpy.run_path(sys.argv[1])\n"
    "print(json.dumps(names[sys.argv[3]](Path(sys.argv[2]), *sys.argv[4:])))\n"
)


def _entry(brief: Path, **more: object) -> dict[str, Any]:
    """Return a queued cut's entry for `brief`, `more` overriding or adding keys."""
    entry = {
        "bump": "minor",
        "brief": str(brief),
        "after": [],
        "executor": "claude",
        "model": None,
        "effort": None,
        "halt": None,
        "dependencies": [],
    }
    return {**entry, **more}


def _cuts(root: Path) -> dict[str, dict[str, Any]]:
    """Return the conductor's list of the queued entries."""
    return _conduct()["_cuts"](root)


def _write(root: Path, change: str, entry: dict[str, Any]) -> None:
    """Write `entry` as the conductor writes a queued cut's."""
    _conduct()["_write_cut"](root, change, entry)


def _folder(root: Path, name: str) -> Path:
    """Return the queue's folder `name` under `root`, made."""
    folder = layout.queue_dir(root) / name
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _plant(path: Path, shape: str, text: str = "x\n") -> None:
    """Make `path` a `shape`: a file, an empty file, a link, a hard link and so on."""
    other = path.parent.parent / f".other-{path.name}"
    if shape == "file":
        path.write_text(text)
    elif shape == "empty":
        path.write_text("")
    elif shape == "binary":
        path.write_bytes(b"\xff\xfe" + text.encode())
    elif shape == "big":
        path.write_text(text + " " * (_BOUND + 4096))
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


def _clear(path: Path) -> None:
    """Remove what stands at `path`: a file, a link, a pipe or an empty folder."""
    if path.is_dir() and not path.is_symlink():
        path.rmdir()
    else:
        path.unlink(missing_ok=True)


def _descriptors() -> int:
    """Return how many descriptors this process holds open."""
    return len(os.listdir("/dev/fd"))


def _modes(path: Path) -> int:
    """Return the permission bits of `path`."""
    return stat.S_IMODE(path.stat().st_mode)


def _lock(root: Path) -> contextlib.AbstractContextManager[None]:
    """Return the conductor's queue lock over `root`, a context manager."""
    return _conduct()["_queue_lock"](root)


def _child(root: Path, name: str, *args: str, seconds: float = 20) -> object:
    """Run the conductor's function `name` in a child over `root`; return its answer."""
    command = [sys.executable, "-c", _CHILD, str(_SCRIPT), str(root), name, *args]
    done = subprocess.run(
        command, capture_output=True, text=True, timeout=seconds, check=True
    )
    return json.loads(done.stdout)


def test_queue_lock_blocks_a_second_taker(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    second = threading.Event()

    def take() -> None:
        with _lock(root):
            second.set()

    with _lock(root):
        thread = threading.Thread(target=take, daemon=True)
        thread.start()
        # mutant: `fcntl.LOCK_EX` → `fcntl.LOCK_SH`
        assert not second.wait(0.3)
    thread.join(10)
    assert second.is_set()


def test_the_lock_makes_its_folders_0700_and_its_file_0600(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    umask = os.umask(0o022)
    try:
        with _lock(root):
            pass
    finally:
        os.umask(umask)
    lock = layout.queue_lock(root)
    # mutant: `mode=0o700` → `mode=0o777` in either `mkdir`; `0o600` → `0o644`
    assert _modes(lock) == 0o600
    assert _modes(lock.parent) == 0o700
    assert _modes(lock.parent.parent) == 0o700


def test_the_lock_makes_no_parent_of_the_kept_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _primary(tmp_path)
    conduct = _conduct()
    monkeypatch.setenv("HOME", str(tmp_path / "no" / "home"))
    with pytest.raises(conduct["Stop"]) as refused:
        # mutant: `mkdir(mode=0o700, exist_ok=True)` → `parents=True` as well
        conduct["_queue_lock"](root).__enter__()
    assert refused.value.code == 2
    assert str(refused.value) == f"{_REFUSED}No such file or directory{_SANDBOX}"
    assert not (tmp_path / "no").exists()


def test_the_lock_refuses_a_link_and_a_folder_at_its_name(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    conduct = _conduct()
    with conduct["_queue_lock"](root):
        pass
    lock = layout.queue_lock(root)
    outside = tmp_path / "outside"
    outside.write_text("the person's\n")
    for shape in ("link", "folder"):
        lock.unlink() if lock.is_file() or lock.is_symlink() else lock.rmdir()
        if shape == "link":
            lock.symlink_to(outside)
        else:
            lock.mkdir()
        with pytest.raises(conduct["Stop"]) as refused:
            # mutant: drop `os.O_NOFOLLOW` from the lock's open
            conduct["_queue_lock"](root).__enter__()
        assert refused.value.code == 2, shape
        assert str(refused.value).startswith(_REFUSED), shape
        assert str(refused.value).endswith(_SANDBOX), shape
    assert outside.read_text() == "the person's\n"


def _locked_and_raised(root: Path) -> None:
    """Raise inside the lock."""
    with _lock(root):
        raise RuntimeError("boom")


def test_the_lock_closes_its_descriptor_when_its_body_raises(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    with _lock(root):
        pass
    held = _descriptors()
    with _lock(root):
        pass
    assert _descriptors() == held
    with pytest.raises(RuntimeError):
        # mutant: drop `os.close(fd)` from the `finally`
        _locked_and_raised(root)
    assert _descriptors() == held


def _queued(root: Path, *changes: str) -> Path:
    """Write an entry for each of `changes`, a brief beside `root`; return the brief."""
    brief = root.parent / "brief.md"
    brief.write_text("# brief\n")
    _folder(root, "cuts")
    for change in changes:
        _write(root, change, _entry(brief))
    return brief


def test_cuts_lists_the_entries_by_id_and_skips_a_name_that_is_no_change_id(
    tmp_path: Path,
) -> None:
    root = _primary(tmp_path)
    brief = _queued(root, "0010-c", "0002-b", "0001-a")
    folder = layout.queue_cuts(root)
    for stray in (".partial", "notes", "0003-a.tmp", "A-b", "0004-", "-a"):
        (folder / stray).write_text(json.dumps(_entry(brief)))
    # mutant: drop the `CHANGE_ID.fullmatch` test of `_cuts`
    assert list(_cuts(root)) == ["0001-a", "0002-b", "0010-c"]
    assert _cuts(root)["0002-b"] == _entry(brief)


def test_cuts_lists_nothing_for_no_folder_and_a_folder_with_no_entry(
    tmp_path: Path,
) -> None:
    root = _primary(tmp_path)
    assert _cuts(root) == {}
    _folder(root, "cuts")
    assert _cuts(root) == {}


def test_cuts_returns_each_key_the_entry_holds(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    brief = _queued(root)
    more = {"beside": ["0009-z"], "models": "[build]\n", "waits": "1 in flight, cap 1"}
    entry = _entry(brief, after=["0001-a"], halt="x", model="opus", **more)
    _write(root, "0002-b", entry)
    # mutant: return `{key: entry[key] for key in CUT_KEYS}`
    assert _cuts(root) == {"0002-b": entry}


def test_cuts_reads_a_broken_entry_as_the_unreadable_one(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    brief = _queued(root)
    path = layout.queue_cuts(root) / "0001-a"
    whole = _entry(brief)
    keys = ("bump", "brief", "after", "executor", "model", "effort", "halt")
    broken = ["", "{", "[]", "null", '"x"', "7", "true", '{"halt": null}']
    broken += [json.dumps({k: v for k, v in whole.items() if k != key}) for key in keys]
    for text in broken:
        path.write_text(text)
        # mutant: drop a key of `CUT_KEYS`; drop the `isinstance(entry, dict)` test
        assert _cuts(root) == {"0001-a": _UNREADABLE}, text
    path.write_bytes(b'{"halt": null, "bump": "\xff"}')
    assert _cuts(root) == {"0001-a": _UNREADABLE}


def test_cuts_reads_a_file_an_empty_file_a_bad_byte_and_a_big_file(
    tmp_path: Path,
) -> None:
    root = _primary(tmp_path)
    brief = _queued(root)
    path = layout.queue_cuts(root) / "0001-a"
    text = json.dumps(_entry(brief))
    for shape, expected in (
        ("file", _entry(brief)),
        ("empty", _UNREADABLE),
        ("binary", _UNREADABLE),
        ("big", _entry(brief)),
    ):
        path.unlink(missing_ok=True)
        _plant(path, shape, text)
        assert _cuts(root) == {"0001-a": expected}, shape


def test_cuts_follows_a_link_and_reads_a_dangling_link_and_a_folder_as_unreadable(
    tmp_path: Path,
) -> None:
    root = _primary(tmp_path)
    brief = _queued(root)
    path = layout.queue_cuts(root) / "0001-a"
    text = json.dumps(_entry(brief))
    for shape, expected in (
        ("link", _entry(brief)),
        ("dangling", _UNREADABLE),
        ("hard", _entry(brief)),
        ("folder", _UNREADABLE),
    ):
        _clear(path)
        _plant(path, shape, text)
        # mutant: read the entry with `os.lstat` first, refusing a link
        assert _cuts(root) == {"0001-a": expected}, shape


def test_cuts_lists_nothing_through_a_link_or_a_file_at_the_folder(
    tmp_path: Path,
) -> None:
    root = _primary(tmp_path)
    brief = _queued(root, "0001-a")
    folder = layout.queue_cuts(root)
    aside = layout.queue_dir(root) / "aside"
    folder.rename(aside)
    folder.symlink_to(aside)
    # mutant: drop `os.O_NOFOLLOW` from `_entries`
    assert _cuts(root) == {}
    assert (aside / "0001-a").is_file()
    folder.unlink()
    folder.write_text("a file")
    assert _cuts(root) == {}
    assert brief.is_file()


def test_write_cut_writes_the_entry_whole_in_key_order_and_leaves_no_temp(
    tmp_path: Path,
) -> None:
    root = _primary(tmp_path)
    brief = _queued(root)
    entry = _entry(brief, after=["0001-a"], beside=["0009-z"])
    entry["models"] = None
    _write(root, "0002-b", entry)
    path = layout.queue_cuts(root) / "0002-b"
    # mutant: `json.dump(entry, file)` → `json.dump(entry, file, sort_keys=True)`
    assert path.read_text() == json.dumps(entry)
    assert list(json.loads(path.read_text())) == list(entry)
    assert sorted(os.listdir(path.parent)) == ["0002-b"]

    # A longer entry first, then a shorter one: the new text leaves no tail.
    _write(root, "0002-b", {**entry, "halt": "x" * 400})
    _write(root, "0002-b", entry)
    assert path.read_text() == json.dumps(entry)
    assert sorted(os.listdir(path.parent)) == ["0002-b"]


def test_write_cut_makes_the_entry_0600_and_its_folder_0700_with_no_parent(
    tmp_path: Path,
) -> None:
    root = _primary(tmp_path)
    brief = tmp_path / "brief.md"
    brief.write_text("# brief\n")
    with pytest.raises(FileNotFoundError):
        # mutant: `folder.mkdir(mode=0o700, exist_ok=True)` → `parents=True` as well
        _write(root, "0001-a", _entry(brief))
    layout.queue_dir(root).mkdir(parents=True)
    umask = os.umask(0o022)
    try:
        _write(root, "0001-a", _entry(brief))
    finally:
        os.umask(umask)
    folder = layout.queue_cuts(root)
    assert _modes(folder) == 0o700
    assert _modes(folder / "0001-a") == 0o600


def test_write_cut_replaces_a_link_a_dangling_link_and_a_pipe_at_the_name(
    tmp_path: Path,
) -> None:
    root = _primary(tmp_path)
    brief = _queued(root)
    path = layout.queue_cuts(root) / "0001-a"
    entry = _entry(brief)
    for shape in ("link", "dangling", "pipe", "hard"):
        _clear(path)
        _plant(path, shape, "the target's\n")
        _write(root, "0001-a", entry)
        # mutant: write the entry in place, `open(path, "w")`
        assert path.is_file() and not path.is_symlink(), shape
        assert path.read_text() == json.dumps(entry), shape
        assert _cuts(root) == {"0001-a": entry}, shape
    other = layout.queue_dir(root) / ".other-0001-a"
    assert other.read_text() == "the target's\n"


def test_write_cut_fails_on_a_folder_at_the_name_and_lists_no_stray(
    tmp_path: Path,
) -> None:
    root = _primary(tmp_path)
    brief = _queued(root)
    path = layout.queue_cuts(root) / "0001-a"
    path.mkdir()
    with pytest.raises(OSError):  # noqa: PT011
        _write(root, "0001-a", _entry(brief))
    assert path.is_dir()
    assert _cuts(root) == {"0001-a": _UNREADABLE}


def test_a_record_is_stripped_and_a_prefix_is_no_try(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    tried = _conduct()["_merge_tried"]
    record = _folder(root, "supervised") / "0001-a"
    assert not tried(root, "0001-a", "abc")
    record.write_text("abc\n")
    assert tried(root, "0001-a", "abc")
    # mutant: drop `.strip()` from `_merge_tried`
    record.write_text("  abc \n\n")
    assert tried(root, "0001-a", "abc")
    # mutant: `==` → `startswith` in `_merge_tried`
    for text in ("ab\n", "abcd\n", "abc d\n", "abc\nabc\n", "", "\n"):
        record.write_text(text)
        assert not tried(root, "0001-a", "abc"), text
    record.write_bytes(b"abc\xff\n")
    assert not tried(root, "0001-a", "abc")
    assert not tried(root, "0002-b", "abc")


def test_an_empty_record_reads_as_none_and_a_brief_record_names_a_file(
    tmp_path: Path,
) -> None:
    root = _primary(tmp_path)
    brief_of = _conduct()["_brief_of"]
    record = _folder(root, "briefs") / "0001-a"
    brief = tmp_path / "brief.md"
    brief.write_text("# brief\n")
    assert brief_of(root, "0001-a") is None
    record.write_text(f"{brief}\n")
    assert brief_of(root, "0001-a") == str(brief)
    record.write_text(f"  {brief} \n\n")
    assert brief_of(root, "0001-a") == str(brief)
    for text in ("", "\n", "  \n", f"{tmp_path}\n", f"{tmp_path}/gone.md\n"):
        record.write_text(text)
        # mutant: `Path(named).is_file()` → `Path(named).exists()`
        assert brief_of(root, "0001-a") is None, text
    record.write_bytes(b"\xff\n")
    assert brief_of(root, "0001-a") is None


def _cutter(tmp_path: Path) -> tuple[dict[str, Any], Path, Any, Path]:
    """Return a conductor, a primary, a `Run` whose cutter and check pass, a brief.

    `0001-a` is queued with its reservation; the run starts no worker.
    """
    conduct = _conduct()
    root = _primary(tmp_path)
    brief = _queued(root, "0001-a")
    reserved = root / ".minions" / "cuts" / "0001-a"
    reserved.parent.mkdir(parents=True)
    reserved.touch()
    run = conduct["Run"](root, "claude")
    run.run_cutter = lambda *_, **__: None
    run.checked_cut = lambda *_: (None, None)
    return conduct, root, run, brief


def test_cutting_writes_the_brief_record_under_the_lock_then_takes_the_entry(
    tmp_path: Path,
) -> None:
    conduct, root, run, brief = _cutter(tmp_path)
    record = layout.queue_dir(root) / "briefs" / "0001-a"
    names = conduct["main"].__globals__
    real = names["_queue_lock"]
    seen: list[tuple[str, bool]] = []

    @contextlib.contextmanager
    def watched(primary: Path) -> Iterator[None]:
        seen.append(("in", record.exists()))
        with real(primary):
            yield
        seen.append(("out", record.exists()))

    names["_queue_lock"] = watched
    umask = os.umask(0o022)
    try:
        assert run.cutting("0001-a") is None
    finally:
        os.umask(umask)
    # mutant: write the record after the `with _queue_lock(primary)` block
    assert seen == [("in", False), ("out", True)]
    # mutant: write `entry['brief']` with no newline
    assert record.read_text() == f"{brief}\n"
    assert _modes(record.parent) == 0o700
    assert _cuts(root) == {}
    assert not (root / ".minions" / "cuts" / "0001-a").exists()


def _supervising(tmp_path: Path) -> tuple[dict[str, Any], Path, Any, Any, str]:
    """Return a conductor, a primary, an open merge's `Run` and version, its merge.

    The run's stage reads a semantic conflict, and its supervisor spawns nothing.
    """
    conduct = _conduct()
    root = _primary(tmp_path)
    tree = _version(root, "0001-a", "- [ ] 1 — One\n")
    _commit(root, {"main.txt": "x\n"}, "main moves")
    _git(tree, "merge", "-q", "--no-ff", "--no-commit", "main")
    run = conduct["Run"](root, "claude")
    run.decides.add("0001-a")
    run.diagnosed.add("0001-a")
    run.planned_models = lambda change, station: ("model", None, None)
    run.spawn = lambda *_, **__: None
    stage = ("integrating", "semantic conflict: x")
    conduct["main"].__globals__["stage_of"] = lambda *_, **__: stage
    version = conduct["Version"]("0001-a", tree)
    return conduct, root, run, version, _git(tree, "rev-parse", "MERGE_HEAD")


def test_supervise_writes_the_merge_it_tries_under_the_lock(tmp_path: Path) -> None:
    conduct, root, run, version, merge = _supervising(tmp_path)
    record = layout.queue_dir(root) / "supervised" / "0001-a"
    names = conduct["main"].__globals__
    real = names["_queue_lock"]
    seen: list[tuple[str, bool]] = []

    @contextlib.contextmanager
    def watched(primary: Path) -> Iterator[None]:
        seen.append(("in", record.exists()))
        with real(primary):
            yield
        seen.append(("out", record.exists()))

    names["_queue_lock"] = watched
    umask = os.umask(0o022)
    try:
        assert not run.supervise(version, "integrating", True)
    finally:
        os.umask(umask)
    # mutant: write the record after the `with _queue_lock(self.primary)` block
    assert seen == [("in", False), ("out", True)]
    # mutant: write `start.merge` with no newline
    assert record.read_text() == f"{merge}\n"
    assert _modes(record.parent) == 0o700
    assert len(run.supervisions["0001-a"]) == 1


def test_supervise_skips_an_open_merge_it_tried_before(tmp_path: Path) -> None:
    _, root, run, version, merge = _supervising(tmp_path)
    record = _folder(root, "supervised") / "0001-a"
    record.write_text(f"{merge}\n")
    spawned: list[str] = []
    run.spawn = lambda *args, **_: spawned.append(args[1])
    # mutant: drop the `_merge_tried` test of `supervise`
    assert not run.supervise(version, "integrating", True)
    assert spawned == []
    assert "0001-a" not in run.supervisions

    # A record of another merge is no try.
    record.write_text("deadbeef\n")
    assert not run.supervise(version, "integrating", True)
    assert spawned == ["supervise"]
    assert record.read_text() == f"{merge}\n"


def test_requests_unlinks_a_link_and_leaves_its_target(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    queue = layout.queue_dir(root)
    folder = _folder(root, "rejoin")
    outside = tmp_path / "outside"
    outside.write_text("the person's\n")
    (folder / "0001-a").write_text("")
    (folder / "0002-b").symlink_to(outside)
    (folder / "0003-c").symlink_to(tmp_path / "gone")
    os.mkfifo(folder / "0004-d")
    (folder / "all").touch()
    (folder / "0005-e").mkdir()
    taken = _conduct()["_requests"](queue)
    # mutant: unlink the target of a link, `os.unlink(os.path.realpath(...))`
    assert outside.read_text() == "the person's\n"
    assert isinstance(taken, set)
    assert taken == {"0001-a", "0002-b", "0003-c", "0004-d", "all"}
    # mutant: drop the `continue` of a failed unlink, or count a folder's name
    assert os.listdir(folder) == ["0005-e"]
    assert _conduct()["_requests"](queue) == set()


def test_requests_takes_a_stray_name_today_and_reads_a_missing_folder_as_none(
    tmp_path: Path,
) -> None:
    root = _primary(tmp_path)
    queue = layout.queue_dir(root)
    requests = _conduct()["_requests"]
    assert requests(queue) == set()
    folder = _folder(root, "rejoin")
    for stray in ("0001-a.tmp", ".hidden", "notes"):
        (folder / stray).touch()
    assert requests(queue) == {"0001-a.tmp", ".hidden", "notes"}
    assert os.listdir(folder) == []


def test_requests_reads_a_linked_folder_as_none_and_leaves_its_files(
    tmp_path: Path,
) -> None:
    root = _primary(tmp_path)
    queue = layout.queue_dir(root)
    folder = _folder(root, "rejoin")
    folder.rmdir()
    aside = tmp_path / "aside"
    aside.mkdir()
    (aside / "0001-a").touch()
    folder.symlink_to(aside)
    conduct = _conduct()
    # mutant: drop `os.O_NOFOLLOW` from `_entries`
    assert conduct["_requests"](queue) == set()
    assert not conduct["_requested"](queue)
    assert os.listdir(aside) == ["0001-a"]
    folder.unlink()
    folder.write_text("a file")
    assert conduct["_requests"](queue) == set()
    assert not conduct["_requested"](queue)


def test_requested_counts_a_regular_file_alone_and_unlinks_nothing(
    tmp_path: Path,
) -> None:
    root = _primary(tmp_path)
    queue = layout.queue_dir(root)
    requested = _conduct()["_requested"]
    assert not requested(queue)
    folder = _folder(root, "rejoin")
    assert not requested(queue)
    outside = tmp_path / "outside"
    outside.write_text("x\n")
    (folder / "0001-a").symlink_to(outside)
    (folder / "0002-b").symlink_to(tmp_path / "gone")
    os.mkfifo(folder / "0003-c")
    (folder / "0004-d").mkdir()
    # mutant: `os.lstat` → `os.stat`, or `stat.S_ISREG` → `os.path.exists`
    assert not requested(queue)
    (folder / "0005-e").touch()
    assert requested(queue)
    assert requested(queue)
    assert sorted(os.listdir(folder)) == [
        "0001-a",
        "0002-b",
        "0003-c",
        "0004-d",
        "0005-e",
    ]


def test_request_makes_the_folder_with_its_parents_and_the_file_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _primary(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path / "no" / "home"))
    umask = os.umask(0o022)
    try:
        # mutant: `parents=True` → `parents=False` in `_request`
        _conduct()["_request"](root, "0001-a")
    finally:
        os.umask(umask)
    folder = layout.queue_rejoin(root)
    assert _modes(folder) == 0o700
    assert (folder / "0001-a").read_bytes() == b""
    assert _modes(folder / "0001-a") == 0o644
    _conduct()["_request"](root, "0001-a")
    _conduct()["_request"](root, "all")
    assert sorted(os.listdir(folder)) == ["0001-a", "all"]
    assert _conduct()["_requests"](layout.queue_dir(root)) == {"0001-a", "all"}


def _traced(
    conduct: dict[str, Any], *wrapped: str
) -> list[tuple[str, tuple[Any, ...], bool]]:
    """Wrap the conductor's functions `wrapped` and its queue lock; return the log.

    A call logs its name, its arguments and whether the queue lock was held.
    """
    names = conduct["main"].__globals__
    held = [0]
    log: list[tuple[str, tuple[Any, ...], bool]] = []
    real_lock = names["_queue_lock"]

    @contextlib.contextmanager
    def lock(primary: Path) -> Iterator[None]:
        with real_lock(primary):
            held[0] += 1
            try:
                yield
            finally:
                held[0] -= 1

    def wrap(name: str) -> None:
        real = names[name]

        def call(*args: object, **kwargs: object) -> object:
            log.append((name, args, held[0] > 0))
            return real(*args, **kwargs)

        names[name] = call

    names["_queue_lock"] = lock
    for name in wrapped:
        wrap(name)
    return log


def test_cut_line_shows_the_halt_before_the_wait_before_nothing() -> None:
    line = _conduct()["_cut_line"]
    whole = _entry(Path("brief.md"))
    assert line("0003-a", whole) == "0003-a · cut"
    assert line("0003-a", {**whole, "waits": "1 in flight, cap 1"}) == (
        "0003-a · cut — waits: 1 in flight, cap 1"
    )
    assert line("0003-a", {**whole, "halt": "x"}) == "0003-a · cut-halted — x"
    both = {**whole, "halt": "x", "waits": "1 in flight, cap 1"}
    assert line("0003-a", both) == "0003-a · cut-halted — x"
    assert line("0003-a", _UNREADABLE) == (
        "0003-a · cut-halted — the queue entry is unreadable"
    )


def test_halted_after_follows_the_chain_and_matches_the_text_whole() -> None:
    halted = _conduct()["_halted_after"]
    brief = Path("brief.md")

    def cuts(**halts: str | None) -> dict[str, dict[str, Any]]:
        return {name: _entry(brief, halt=halt) for name, halt in halts.items()}

    chain = cuts(
        **{
            "0001-a": "x",
            "0002-b": "after 0001-a is cut-halted",
            "0003-c": "after 0002-b is cut-halted",
            "0004-d": "after 0001-a is cut-halted",
            "0005-e": "after 0009-z is cut-halted",
            "0006-f": None,
        }
    )
    assert halted(chain, "0001-a") == ["0002-b", "0003-c", "0004-d"]
    assert halted(chain, "0002-b") == ["0003-c"]
    assert halted(chain, "0003-c") == []
    assert halted(chain, "0009-z") == ["0005-e"]
    # mutant: `==` → `startswith` or `in` in the halt's match
    near = cuts(
        **{
            "0002-b": "after 0001-a is cut-halted.",
            "0003-c": "after 0001-a is cut-halted and more",
            "0004-d": "x after 0001-a is cut-halted",
            "0005-e": "after 0001-ab is cut-halted",
        }
    )
    assert halted(near, "0001-a") == []
    # A cycle ends and the change names itself not.
    loop = cuts(
        **{
            "0001-a": "after 0002-b is cut-halted",
            "0002-b": "after 0001-a is cut-halted",
        }
    )
    assert halted(loop, "0001-a") == ["0002-b"]


def test_next_id_is_one_above_every_number_the_repo_its_branches_and_the_queue_hold(
    tmp_path: Path,
) -> None:
    root = _primary(tmp_path)
    conduct = _conduct()
    assert conduct["_next_id"](root) == 1
    brief = _queued(root, "0009-q")
    # mutant: drop `names += _cuts(primary)` from `_next_id`
    assert conduct["_next_id"](root) == 10
    _git(root, "branch", "0011-b")
    assert conduct["_next_id"](root) == 12
    (root / ".minions" / "cuts").mkdir(parents=True)
    (root / ".minions" / "cuts" / "0013-r").touch()
    assert conduct["_next_id"](root) == 14
    _commit(root, {"openspec/changes/archive/0020-z/proposal.md": ""}, "ship 0020-z")
    assert conduct["_next_id"](root) == 21
    # A name in the queue that is no change id holds no number.
    (layout.queue_cuts(root) / "0099-").write_text(json.dumps(_entry(brief)))
    (layout.queue_cuts(root) / "0098-x.tmp").write_text("{}")
    assert conduct["_next_id"](root) == 21


def _briefed(tmp_path: Path, *slugs: str) -> tuple[dict[str, Any], Path, Path]:
    """Return a conductor, a primary with a live claim, and a brief for `slugs`."""
    conduct = _conduct()
    root = _primary(tmp_path)
    _claimed(conduct, root)
    _swap_runner(conduct)
    brief = tmp_path / "brief.md"
    brief.write_text(f"# brief\n\n{_items(*slugs)}")
    return conduct, root, brief


def test_cut_reserves_the_id_then_writes_its_entry_under_the_lock(
    tmp_path: Path,
) -> None:
    conduct, root, brief = _briefed(tmp_path, "a", "b")
    log = _traced(conduct, "_write_cut")
    umask = os.umask(0o022)
    try:
        said = conduct["cut"](
            root, "a", "minor", f"brief={brief}", [], "claude", "opus", None
        )
    finally:
        os.umask(umask)
    assert said == "cut: queued 0001-a · the live run takes it"
    assert [(name, args[1], held) for name, args, held in log] == [
        ("_write_cut", "0001-a", True)
    ]
    # mutant: reorder the keys of the entry, or write `beside` for no link
    entry = _cuts(root)["0001-a"]
    assert list(entry) == [
        "bump",
        "brief",
        "after",
        "executor",
        "model",
        "effort",
        "halt",
        "dependencies",
        "models",
    ]
    assert entry == _entry(
        brief.resolve(), model="opus", dependencies=[], models=_MODELS
    )
    reserved = root / ".minions" / "cuts" / "0001-a"
    assert reserved.read_bytes() == b""
    assert _modes(reserved) == 0o644

    # The next cut takes the next number, and may wait on, and sit beside, the first.
    links = ["after=0001-a", "beside=0001-a"]
    given = (root, "b", "patch", f"brief={brief}", links, "claude", None, "low")
    assert conduct["cut"](*given) == "cut: queued 0002-b · the live run takes it"
    second = _cuts(root)["0002-b"]
    assert second["after"] == ["0001-a"]
    assert list(second)[-1] == "beside"
    assert second["beside"] == ["0001-a"]
    assert (second["bump"], second["model"], second["effort"]) == ("patch", None, "low")


def test_cut_refuses_an_after_that_names_no_open_version_or_queued_cut(
    tmp_path: Path,
) -> None:
    conduct, root, brief = _briefed(tmp_path, "a")
    with pytest.raises(conduct["Stop"]) as refused:
        conduct["cut"](
            root, "a", "minor", f"brief={brief}", ["after=0009-x"], "claude", None, None
        )
    assert refused.value.code == 2
    assert str(refused.value) == (
        "cut: cannot run — after=0009-x names no open version or queued cut"
    )
    assert _cuts(root) == {}
    assert not (root / ".minions" / "cuts").exists()


def test_rejoin_clears_the_chain_in_name_order(tmp_path: Path) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    brief = _queued(root)
    halts = {
        "0001-a": "x",
        "0002-b": "after 0001-a is cut-halted",
        "0003-c": "after 0002-b is cut-halted",
        "0004-d": "after 0001-a is cut-halted",
        "0005-e": "after 0009-z is cut-halted",
    }
    entries = {
        name: _entry(brief, halt=halt, waits="1 in flight, cap 1")
        for name, halt in halts.items()
    }
    for name, entry in entries.items():
        _write(root, name, entry)
    _claimed(conduct, root)
    log = _traced(conduct, "_write_cut", "_request")

    said = conduct["rejoin"](root, "0001-a")

    assert said == "rejoin: requested 0001-a, 0002-b, 0003-c, 0004-d"
    # mutant: `sorted(found[1:])` → `found[1:]` in `_halted_after`
    names = ["0001-a", "0002-b", "0003-c", "0004-d"]
    assert [(n, a[1], held) for n, a, held in log if n == "_write_cut"] == [
        ("_write_cut", name, True) for name in names
    ]
    assert [(n, a[1], held) for n, a, held in log if n == "_request"] == [
        ("_request", name, True) for name in names
    ]
    cuts = _cuts(root)
    for name in names:
        # The entry's key order stays, `halt` cleared, `waits` kept.
        assert list(cuts[name]) == list(entries[name]), name
        assert cuts[name] == {**entries[name], "halt": None}, name
    assert cuts["0005-e"] == entries["0005-e"]
    asked = sorted(os.listdir(layout.queue_rejoin(root)))
    assert asked == names


def test_rejoin_refuses_an_unreadable_entry_and_leaves_it(tmp_path: Path) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    _queued(root)
    _claimed(conduct, root)
    entry = layout.queue_cuts(root) / "0003-c"
    said = (
        f"rejoin: cannot run — the queue entry {entry} is unreadable: remove it,"
        " then queue the cut again"
    )
    for text in ("{", '{"halt": null}', "[]", ""):
        entry.write_text(text)
        with pytest.raises(conduct["Stop"]) as refused:
            conduct["rejoin"](root, "0003-c")
        assert refused.value.code == 2, text
        assert str(refused.value) == said, text
        assert entry.read_text() == text
    assert not layout.queue_rejoin(root).exists()


def test_rejoin_asks_all_when_no_change_is_named_and_names_what_it_cannot(
    tmp_path: Path,
) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    stop = conduct["Stop"]
    with pytest.raises(stop, match="rejoin: no run is live — run /mf-ship"):
        conduct["rejoin"](root, None)
    _claimed(conduct, root)
    log = _traced(conduct, "_request")
    assert conduct["rejoin"](root, None) == "rejoin: requested every halted version"
    assert [(args[1], held) for _, args, held in log] == [("all", True)]
    assert os.listdir(layout.queue_rejoin(root)) == ["all"]
    with pytest.raises(stop, match="no open version holds 0009-x") as refused:
        conduct["rejoin"](root, "0009-x")
    assert refused.value.code == 2
    with pytest.raises(stop, match="--yes answers a queued cut's packages"):
        conduct["rejoin"](root, "0009-x", "abc")
    assert os.listdir(layout.queue_rejoin(root)) == ["all"]


def test_grant_writes_a_request_under_the_lock_when_a_run_is_live(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    _version(root, "0001-a", "- [x] 1 — One\n")
    _claimed(conduct, root)
    names = conduct["main"].__globals__
    stage = ("converge-halted", "cap reached: x")
    names["stage_of"] = lambda *_, **__: stage
    log = _traced(conduct, "_request")
    started: list[Path] = []
    names["_start_run"] = lambda primary, executor: started.append(primary) or 4242

    assert conduct["grant"](root, "0001-a", "claude") == 0

    assert [(args[1], held) for _, args, held in log] == [("0001-a", True)]
    assert os.listdir(layout.queue_rejoin(root)) == ["0001-a"]
    assert started == []
    assert (root / ".minions" / "grants" / "0001-a").is_file()
    out = capsys.readouterr().out
    assert out == "grant: recorded — the live run takes 0001-a back\n"

    # With no run live the grant starts one and writes no request.
    shutil_claim = root / ".minions" / "runs" / "active"
    for name in ("pid", "start"):
        (shutil_claim / name).unlink()
    shutil_claim.rmdir()
    names["preconditions"] = lambda cwd, executor: None
    conduct["_requests"](layout.queue_dir(root))
    assert conduct["grant"](root, "0001-a", "claude") == 0
    assert started == [root]
    assert os.listdir(layout.queue_rejoin(root)) == []


def _polling(tmp_path: Path, *changes: str) -> tuple[dict[str, Any], Path, Any, Path]:
    """Return a conductor, a primary, a `Run` that took nothing, and a brief.

    `changes` are queued; the run has read the queue, and its `take_cut` records.
    """
    conduct = _conduct()
    root = _primary(tmp_path)
    brief = _queued(root, *changes)
    run = conduct["Run"](root, "claude")
    run.seen = set()
    run.taken = []
    run.take_cut = lambda change, entry, threads: run.taken.append(change) or True
    return conduct, root, run, brief


def _halt_entry(root: Path, change: str, halt: str | None) -> None:
    """Rewrite the queued entry `change` with `halt`."""
    entry = _cuts(root)[change]
    _write(root, change, {**entry, "halt": halt})


def test_take_requests_reads_the_entries_again_when_a_request_stands(
    tmp_path: Path,
) -> None:
    conduct, root, run, _ = _polling(tmp_path, "0003-a")
    _halt_entry(root, "0003-a", "x")
    names = conduct["main"].__globals__
    reads: list[int] = []
    real = names["_cuts"]

    def counted(primary: Path) -> dict[str, dict[str, Any]]:
        reads.append(1)
        return real(primary)

    names["_cuts"] = counted
    assert not run.take_requests({})
    assert len(reads) == 1
    conduct["_request"](root, "0009-x")
    reads.clear()
    # mutant: drop the second `_cuts` read of `take_requests`
    assert not run.take_requests({})
    assert len(reads) == 2
    assert run.taken == []


def test_take_requests_takes_a_cut_whose_halt_a_rejoin_cleared_after_the_first_read(
    tmp_path: Path,
) -> None:
    conduct, root, run, _ = _polling(tmp_path, "0003-a")
    _halt_entry(root, "0003-a", "x")
    names = conduct["main"].__globals__
    requests = names["_requests"]

    def raced(queue: Path) -> set[str]:
        _halt_entry(root, "0003-a", None)
        return requests(queue)

    names["_requests"] = raced
    conduct["_request"](root, "0003-a")
    assert run.take_requests({})
    assert run.taken == ["0003-a"]


def test_take_requests_skips_a_halted_a_seen_and_a_running_cut_and_takes_a_request(
    tmp_path: Path,
) -> None:
    conduct, root, run, _ = _polling(tmp_path, "0001-a", "0002-b", "0003-c", "0004-d")
    _halt_entry(root, "0001-a", "x")
    run.seen = {"0002-b", "0004-d"}
    gate = threading.Event()
    running = threading.Thread(target=gate.wait, daemon=True)
    running.start()
    assert run.take_requests({"0003-c": running}) is False
    assert run.taken == []
    conduct["_request"](root, "0004-d")
    # A request takes a seen cut back; it takes no halted one, and none a thread runs.
    assert run.take_requests({"0003-c": running})
    assert run.taken == ["0004-d"]
    gate.set()
    running.join()


def test_take_requests_holds_a_cut_the_cap_leaves_no_room_for(tmp_path: Path) -> None:
    conduct, root, run, _ = _polling(tmp_path, "0003-a", "0004-b")
    gate = threading.Event()
    threads = {"0002-v": threading.Thread(target=gate.wait, daemon=True)}
    threads["0002-v"].start()
    run.cap = 1
    waited: list[str] = []
    run.wait_cut = lambda change, threads: waited.append(change)
    assert not run.take_requests(threads)
    assert waited == ["0003-a", "0004-b"]
    assert run.taken == []
    # A request is no waiter: the cap does not hold it.
    conduct["_request"](root, "0004-b")
    waited.clear()
    assert run.take_requests(threads)
    assert (waited, run.taken) == (["0003-a"], ["0004-b"])
    gate.set()
    threads["0002-v"].join()


def test_wait_cut_writes_its_reason_last_under_the_lock_and_skips_what_it_must(
    tmp_path: Path,
) -> None:
    conduct, root, run, _ = _polling(tmp_path, "0003-a", "0004-b")
    _halt_entry(root, "0004-b", "a halt")
    run.cap = 1
    gate = threading.Event()
    threads = {"0002-v": threading.Thread(target=gate.wait, daemon=True)}
    threads["0002-v"].start()
    log = _traced(conduct, "_write_cut")

    run.wait_cut("0003-a", threads)
    run.wait_cut("0003-a", threads)
    entry = _cuts(root)["0003-a"]
    assert entry["waits"] == "1 in flight, cap 1"
    # mutant: write `waits` ahead of the entry's keys, `{"waits": reason, **current}`
    assert list(entry)[-1] == "waits"
    assert [(args[1], held) for _, args, held in log] == [("0003-a", True)]

    # A halted entry and a vanished one are left as they are.
    run.wait_cut("0004-b", threads)
    run.wait_cut("0005-gone", threads)
    assert "waits" not in _cuts(root)["0004-b"]
    assert "0005-gone" not in _cuts(root)
    assert len(log) == 1
    assert run.waiting["0005-gone"] == "1 in flight, cap 1"
    gate.set()
    threads["0002-v"].join()


def test_unwait_drops_the_reason_in_place_and_takes_no_lock_for_none(
    tmp_path: Path,
) -> None:
    conduct, root, run, _ = _polling(tmp_path, "0003-a", "0004-b")
    waits = {"waits": "1 in flight, cap 1"}
    held = {**_cuts(root)["0003-a"], **waits}
    _write(root, "0003-a", held)
    run.waiting["0003-a"] = "1 in flight, cap 1"
    log = _traced(conduct, "_write_cut")

    run.unwait("0003-a", held)
    kept = {key: value for key, value in held.items() if key != "waits"}
    assert _cuts(root)["0003-a"] == kept
    assert list(_cuts(root)["0003-a"]) == list(kept)
    assert [(args[1], held_) for _, args, held_ in log] == [("0003-a", True)]
    assert "0003-a" not in run.waiting

    # An entry that holds no reason is not written, nor read under a lock.
    names = conduct["main"].__globals__

    def locked(primary: Path) -> None:
        raise AssertionError("locked")

    names["_queue_lock"] = locked
    run.waiting["0004-b"] = "x"
    run.unwait("0004-b", _cuts(root)["0004-b"])
    assert "0004-b" not in run.waiting
    assert len(log) == 1


def test_unwait_writes_nothing_for_an_entry_gone_or_one_that_lost_its_reason(
    tmp_path: Path,
) -> None:
    conduct, root, run, _ = _polling(tmp_path, "0003-a")
    held = {**_cuts(root)["0003-a"], "waits": "x"}
    log = _traced(conduct, "_write_cut")
    run.unwait("0003-a", held)
    assert log == []
    (layout.queue_cuts(root) / "0003-a").unlink()
    run.unwait("0003-a", held)
    assert log == []
    assert _cuts(root) == {}


def test_cut_halted_writes_the_halt_under_the_lock_and_logs_it_unless_spawn_did(
    tmp_path: Path,
) -> None:
    conduct, root, run, _ = _polling(tmp_path, "0003-a")
    before = _cuts(root)["0003-a"]
    log = _traced(conduct, "_write_cut")

    run.cut_halted("0003-a", "the cutter died", True)
    entry = _cuts(root)["0003-a"]
    assert entry == {**before, "halt": "the cutter died"}
    assert list(entry) == list(before)
    assert [(args[1], held) for _, args, held in log] == [("0003-a", True)]
    assert run.halts == []

    run.cut_halted("0003-a", "again", False)
    assert _cuts(root)["0003-a"]["halt"] == "again"
    assert run.halts == [("0003-a", "cut-halted — again")]

    # An entry gone stays gone: one written with no fields would halt every run.
    run.cut_halted("0009-gone", "x", True)
    assert "0009-gone" not in _cuts(root)
    assert len(log) == 2


def test_cutting_halts_on_a_queued_dependency_that_is_halted_or_stopped(
    tmp_path: Path,
) -> None:
    _, root, run, brief = _polling(tmp_path, "0001-a", "0002-b")
    _write(root, "0002-b", _entry(brief, after=["0001-a"]))
    _halt_entry(root, "0001-a", "x")
    assert run.cutting("0002-b") == ("after 0001-a is cut-halted", False)
    _halt_entry(root, "0001-a", None)
    run.halts.append(("0001-a", "a halt"))
    assert run.cutting("0002-b") == ("after 0001-a is cut-halted", False)
    assert not (root.parent / "0002-b").exists()


def test_in_flight_counts_a_queued_cut_by_its_entry_s_after(tmp_path: Path) -> None:
    _, root, run, brief = _polling(tmp_path, "0006-cut", "0007-cut")
    _commit(root, {"openspec/changes/archive/0001-s/proposal.md": ""}, "ship 0001-s")
    _write(root, "0006-cut", _entry(brief, after=["0009-x"]))
    _write(root, "0007-cut", _entry(brief, after=["0001-s"]))
    (layout.queue_cuts(root) / "0008-bad").write_text("{")
    gate = threading.Event()
    threads = {}
    for name in ("0006-cut", "0007-cut", "0008-bad"):
        threads[name] = threading.Thread(target=gate.wait, daemon=True)
        threads[name].start()
    # mutant: read `after` from `_dependencies` for a queued cut, or drop `.get`
    assert run.in_flight(threads) == 2
    del threads["0007-cut"]
    assert run.in_flight(threads) == 1
    gate.set()


def _closing(tmp_path: Path) -> tuple[dict[str, Any], Path, Path]:
    """Return a conductor, a primary and its claim holding one entry."""
    conduct = _conduct()
    root = _primary(tmp_path)
    active = root / ".minions" / "runs" / "active"
    active.mkdir(parents=True)
    (active / "pid").write_text("4242")
    return conduct, root, active


def test_close_starts_a_run_for_an_unread_cut_or_a_request_and_none_else(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    conduct, root, active = _closing(tmp_path)
    brief = _queued(root)
    conduct["main"].__globals__["_start_run"] = lambda primary, executor: 4242
    log = _traced(conduct, "_start_run")

    def closed(seen: set[str] | None) -> str:
        active.mkdir(exist_ok=True)
        conduct["_close"](root, active, "claude", seen)
        assert not active.exists()
        return capsys.readouterr().out

    started = "run: next started · pid 4242\n"
    assert closed(set()) == ""
    _write(root, "0003-a", _entry(brief))
    assert closed(None) == ""
    assert closed({"0003-a"}) == ""
    assert closed(set()) == started
    # A halted entry and an unreadable one: the unreadable halts, so it starts none.
    _halt_entry(root, "0003-a", "x")
    (layout.queue_cuts(root) / "0004-b").write_text("{")
    assert closed(set()) == ""
    (layout.queue_cuts(root) / "0003-a").unlink()
    (layout.queue_cuts(root) / "0004-b").unlink()

    # A request starts a run: a file, not a link or a folder.
    rejoin = _folder(root, "rejoin")
    (rejoin / "0009-x").symlink_to(brief)
    (rejoin / "0008-y").mkdir()
    assert closed(set()) == ""
    (rejoin / "0007-z").touch()
    assert closed(set()) == started
    assert (rejoin / "0007-z").is_file()
    assert len(log) == 2


@pytest.mark.slow
def test_a_fifo_at_an_entry_reads_in_a_child(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    brief = _queued(root, "0001-a")
    record = brief.parent / "record"
    record.write_text("abc\n")
    for folder in ("briefs", "supervised"):
        (_folder(root, folder) / "0001-a").write_text(f"{brief}\n")
    reads = (
        ("_cuts", layout.queue_cuts(root) / "0001-a", ()),
        ("_brief_of", layout.queue_briefs(root) / "0001-a", ("0001-a",)),
        ("_merge_tried", layout.queue_supervised(root) / "0001-a", ("0001-a", "abc")),
    )
    for name, path, args in reads:
        # The read of a record no pipe stands at answers, in the child.
        assert _child(root, name, *args) is not None
        held = path.read_bytes()
        path.unlink()
        os.mkfifo(path)
        # mutant: open the entry with `os.O_NONBLOCK`, or read it through `lstat` first
        with pytest.raises(subprocess.TimeoutExpired):
            _child(root, name, *args, seconds=3)
        path.unlink()
        path.write_bytes(held)


def test_a_deep_json_at_an_entry_raises_out_of_the_list(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    _queued(root, "0001-a")
    entry = layout.queue_cuts(root) / "0001-a"
    for text in ("[" * 100000, '{"a":' * 100000):
        entry.write_text(text)
        # mutant: add `RecursionError` to the `except` of `_cuts`
        with pytest.raises(RecursionError):
            _cuts(root)


def test_a_wrong_type_at_an_entry_is_kept_as_written(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    brief = _queued(root)
    entry = layout.queue_cuts(root) / "0001-a"
    whole = _entry(brief)
    for key, value in (
        ("bump", 5),
        ("brief", None),
        ("after", "0001-a"),
        ("executor", ["claude"]),
        ("model", 3),
        ("halt", 3),
        ("dependencies", "x"),
        ("waits", None),
        ("waits", ""),
        ("waits", 7),
    ):
        wrong = {**whole, key: value}
        entry.write_text(json.dumps(wrong))
        # mutant: map a value of the wrong type to the unreadable entry
        assert _cuts(root) == {"0001-a": wrong}, (key, value)


def test_a_record_is_read_by_its_path_whatever_stands_there(tmp_path: Path) -> None:
    root = _primary(tmp_path)
    brief = tmp_path / "brief.md"
    brief.write_text("# brief\n")
    conduct = _conduct()
    for folder, text, read, expected in (
        ("briefs", f"{brief}\n", conduct["_brief_of"], (str(brief), None)),
        ("supervised", "abc\n", conduct["_merge_tried"], (True, False)),
    ):
        path = _folder(root, folder) / "0001-a"
        args = ("abc",) if folder == "supervised" else ()
        followed, refused = expected
        for shape, expect in (
            ("file", followed),
            ("link", followed),
            ("hard", followed),
            ("big", followed),
            ("empty", refused),
            ("binary", refused),
            ("dangling", refused),
            ("folder", refused),
        ):
            _clear(path)
            _plant(path, shape, text)
            # mutant: read the record through `statefile.read_bytes`, refusing a link
            assert read(root, "0001-a", *args) == expect, (folder, shape)


def test_a_request_is_made_through_a_link_at_its_name_and_a_pipe_blocks_none(
    tmp_path: Path,
) -> None:
    root = _primary(tmp_path)
    request = _conduct()["_request"]
    folder = _folder(root, "rejoin")
    outside = tmp_path / "outside"
    outside.write_text("the person's\n")
    (folder / "0001-a").symlink_to(outside)
    (folder / "0002-b").symlink_to(tmp_path / "gone")
    os.mkfifo(folder / "0003-c")
    (folder / "0004-d").mkdir()
    for name in ("0001-a", "0002-b", "0003-c", "0004-d"):
        # mutant: `touch` → create the name with `O_NOFOLLOW`, which refuses a link
        request(root, name)
    assert outside.read_text() == "the person's\n"
    assert (tmp_path / "gone").read_bytes() == b""
    assert (folder / "0001-a").is_symlink()
    assert stat.S_ISFIFO((folder / "0003-c").lstat().st_mode)
    assert (folder / "0004-d").is_dir()


def test_a_hard_link_is_a_request_and_unlinking_it_leaves_the_other_name(
    tmp_path: Path,
) -> None:
    root = _primary(tmp_path)
    queue = layout.queue_dir(root)
    folder = _folder(root, "rejoin")
    other = tmp_path / "other"
    other.write_text("x\n")
    os.link(other, folder / "0001-a")
    conduct = _conduct()
    assert conduct["_requested"](queue)
    assert conduct["_requests"](queue) == {"0001-a"}
    assert other.read_text() == "x\n"


def test_a_link_at_the_cuts_folder_and_at_the_rejoin_folder_is_written_through(
    tmp_path: Path,
) -> None:
    root = _primary(tmp_path)
    brief = _queued(root)
    queue = layout.queue_dir(root)
    for name in ("cuts", "rejoin"):
        aside = tmp_path / f"aside-{name}"
        aside.mkdir()
        folder = _folder(root, name)
        folder.rmdir()
        folder.symlink_to(aside)
    _write(root, "0001-a", _entry(brief))
    # mutant: open the folder with `statefile.open_folder`, which refuses a link
    assert os.listdir(tmp_path / "aside-cuts") == ["0001-a"]
    assert _cuts(root) == {}
    _conduct()["_request"](root, "0001-a")
    assert os.listdir(tmp_path / "aside-rejoin") == ["0001-a"]
    assert _conduct()["_requests"](queue) == set()

    # A link to a file at the rejoin folder fails the request.
    (queue / "rejoin").unlink()
    (queue / "rejoin").symlink_to(brief)
    with pytest.raises(FileExistsError):
        _conduct()["_request"](root, "0001-a")


def _refusing_entries(
    root: Path, monkeypatch: pytest.MonkeyPatch, after: int = 0
) -> types.SimpleNamespace:
    """Make the write of an entry fail with `ENOSPC`, once `after` writes went in.

    Return a handle: `asked` lists the names the write was asked for, `on` ends it.
    """
    real = os.replace
    handle = types.SimpleNamespace(asked=[], on=True)

    def replace(
        src: str | Path,
        dst: str | Path,
        *,
        src_dir_fd: int | None = None,
        dst_dir_fd: int | None = None,
    ) -> None:
        if handle.on and Path(dst).parent == layout.queue_cuts(root):
            handle.asked.append(Path(dst))
            if len(handle.asked) > after:
                raise OSError(28, "No space left on device")
        real(src, dst, src_dir_fd=src_dir_fd, dst_dir_fd=dst_dir_fd)

    monkeypatch.setattr(os, "replace", replace)
    return handle


def _lock_is_free(conduct: dict[str, Any], root: Path) -> bool:
    """Return whether another taker gets the queue lock at once."""
    taken = threading.Event()

    def take() -> None:
        with conduct["_queue_lock"](root):
            taken.set()

    threading.Thread(target=take, daemon=True).start()
    return taken.wait(5)


def test_a_failed_entry_write_in_cut_leaves_the_reservation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    conduct, root, brief = _briefed(tmp_path, "a")
    _folder(root, "cuts")
    refusing = _refusing_entries(root, monkeypatch)
    with pytest.raises(OSError, match="No space left on device"):
        conduct["cut"](root, "a", "minor", f"brief={brief}", [], "claude", None, None)
    assert refusing.asked == [layout.queue_cuts(root) / "0001-a"]
    # mutant: remove the reservation through `_remove_in` before the raise
    assert (root / ".minions" / "cuts" / "0001-a").is_file()
    assert _cuts(root) == {}
    assert _lock_is_free(conduct, root)


def test_a_failed_entry_write_in_rejoin_leaves_the_entries_already_cleared(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    brief = _queued(root)
    halts = {
        "0001-a": "x",
        "0002-b": "after 0001-a is cut-halted",
        "0003-c": "after 0002-b is cut-halted",
    }
    for name, halt in halts.items():
        _write(root, name, _entry(brief, halt=halt))
    _claimed(conduct, root)
    refusing = _refusing_entries(root, monkeypatch, after=1)
    with pytest.raises(OSError, match="No space left on device"):
        conduct["rejoin"](root, "0001-a")
    assert [path.name for path in refusing.asked] == ["0001-a", "0002-b"]
    refusing.on = False
    halted = {name: entry["halt"] for name, entry in _cuts(root).items()}
    assert halted == {**halts, "0001-a": None}
    assert not layout.queue_rejoin(root).exists()
    assert _lock_is_free(conduct, root)


def test_a_failed_request_write_in_rejoin_leaves_the_entry_cleared(
    tmp_path: Path,
) -> None:
    conduct = _conduct()
    root = _primary(tmp_path)
    brief = _queued(root)
    _write(root, "0001-a", _entry(brief, halt="x"))
    _claimed(conduct, root)
    layout.queue_rejoin(root).write_text("a file")
    with pytest.raises(FileExistsError):
        conduct["rejoin"](root, "0001-a")
    assert _cuts(root)["0001-a"]["halt"] is None
    assert _lock_is_free(conduct, root)


def test_a_failed_entry_write_in_a_run_rises_as_an_oserror_and_keeps_its_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    conduct, root, run, _ = _polling(tmp_path, "0003-a", "0004-b")
    held = {**_cuts(root)["0004-b"], "waits": "x"}
    _write(root, "0004-b", held)
    run.cap = 1
    gate = threading.Event()
    threads = {"0002-v": threading.Thread(target=gate.wait, daemon=True)}
    threads["0002-v"].start()
    refusing = _refusing_entries(root, monkeypatch)
    failed = pytest.raises(OSError, match="No space left on device")

    with failed:
        run.cut_halted("0003-a", "x", False)
    assert run.halts == []
    with failed:
        run.wait_cut("0003-a", threads)
    assert run.waiting == {"0003-a": "1 in flight, cap 1"}
    with failed:
        run.unwait("0004-b", held)
    assert "0004-b" not in run.waiting
    assert [path.name for path in refusing.asked] == ["0003-a", "0003-a", "0004-b"]
    refusing.on = False
    assert _cuts(root)["0003-a"]["halt"] is None
    assert "waits" not in _cuts(root)["0003-a"]
    assert _cuts(root)["0004-b"] == held
    assert _lock_is_free(conduct, root)
    gate.set()
    threads["0002-v"].join()


def test_a_failed_briefs_write_in_cutting_keeps_the_entry_and_the_reservation(
    tmp_path: Path,
) -> None:
    conduct, root, run, _ = _cutter(tmp_path)
    layout.queue_briefs(root).write_text("a file")
    with pytest.raises(FileExistsError):
        run.cutting("0001-a")
    assert (root / ".minions" / "cuts" / "0001-a").is_file()
    assert set(_cuts(root)) == {"0001-a"}
    assert _lock_is_free(conduct, root)


def test_a_failed_supervised_write_in_supervise_rises_and_counts_the_try(
    tmp_path: Path,
) -> None:
    conduct, root, run, version, merge = _supervising(tmp_path)
    layout.queue_supervised(root).parent.mkdir(parents=True, exist_ok=True)
    layout.queue_supervised(root).write_text("a file")
    spawned: list[str] = []
    run.spawn = lambda *args, **_: spawned.append(args[1])
    with pytest.raises(FileExistsError):
        run.supervise(version, "integrating", True)
    assert spawned == []
    assert len(run.supervisions["0001-a"]) == 1
    assert merge
    assert _lock_is_free(conduct, root)


def test_each_form_of_waits_reads_as_a_wait_to_the_line_and_unwait(
    tmp_path: Path,
) -> None:
    conduct, root, run, brief = _polling(tmp_path, "0003-a")
    line = conduct["_cut_line"]
    for waits, said in ((None, "None"), ("", ""), ("text", "text")):
        entry = _entry(brief, waits=waits)
        # mutant: read `entry.get("waits")` as a wait only when it is a string
        assert line("0003-a", entry) == f"0003-a · cut — waits: {said}", repr(waits)
        _write(root, "0003-a", entry)
        run.unwait("0003-a", entry)
        assert _cuts(root)["0003-a"] == _entry(brief), repr(waits)


def test_the_cut_halt_s_text_is_written_by_cutting_and_matched_by_halted_after(
    tmp_path: Path,
) -> None:
    conduct, root, run, brief = _polling(tmp_path, "0001-a", "0002-b", "0003-c")
    _write(root, "0002-b", _entry(brief, after=["0001-a"]))
    _write(root, "0003-c", _entry(brief, after=["0002-b"]))
    _halt_entry(root, "0001-a", "x")
    for change, named in (("0002-b", "0001-a"), ("0003-c", "0002-b")):
        failed = run.cutting(change)
        assert failed == (f"after {named} is cut-halted", False)
        run.cut_halted(change, *failed)
        # mutant: write `after {named} is cut-halted.`, or match it by `in`
        assert _cuts(root)[change]["halt"] == f"after {named} is cut-halted"
    assert conduct["_halted_after"](_cuts(root), "0001-a") == ["0002-b", "0003-c"]
