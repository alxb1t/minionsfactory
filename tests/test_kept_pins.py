"""Pins of the kept files as the conductor, `pin.py` and `gate_check.py` keep them.

Each case holds today's side and starts no worker. Why: 0159-kept design D4, D5.
"""

import contextlib
import errno
import importlib.util
import json
import os
import runpy
import stat
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import mflib.kept
import pytest
import test_conduct
from conduct_load import conduct as _conduct
from fake_worker import _commit, _git
from mflib import layout, platform
from test_conduct import (
    _idle_machine,  # noqa: F401
    _no_codex_sessions,  # noqa: F401
    _offline_retries,
    _primary,
    _released,
    _sandbox,  # noqa: F401
    _unmerged_release,
    _uv_sync,  # noqa: F401
    _version,
    cut_check,  # noqa: F401
    ps,  # noqa: F401
)
from test_conduct import fake as _fake  # noqa: F401

_H = "0123456789abcdef0123456789abcdef01234567"
_S = "89abcdef0123456789abcdef0123456789abcdef"
_BOUND = 65536
_REPOS_BOUND = 262144
_SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "mf-ship"
    / "scripts"
    / "conduct.py"
)
_GATE_CHECK = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "mf-converge"
    / "scripts"
    / "gate_check.py"
)
_VIEWER = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "mf-ui"
    / "scripts"
    / "viewer.py"
)
_METRICS = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "mf-review-metrics"
    / "scripts"
    / "review_metrics.py"
)
_CHILD = (
    "import json, runpy, sys\n"
    "from pathlib import Path\n"
    "names = runpy.run_path(sys.argv[1])\n"
    "read = names[sys.argv[2]]\n"
    "args = [Path(a) if a.startswith('/') else a for a in sys.argv[3:]]\n"
    "print(json.dumps(read(*args)))\n"
)
_HOLDER_CHILD = (
    "import json, runpy, sys\n"
    "from pathlib import Path\n"
    "names = runpy.run_path(sys.argv[1])\n"
    "print(json.dumps(names['_pin']()['holder'](Path(sys.argv[2]))))\n"
)
_APPROVAL_CHILD = (
    "import json, runpy, sys\n"
    "from pathlib import Path\n"
    "names = runpy.run_path(sys.argv[1])\n"
    "names['approval'].__globals__['_primary'] = lambda: Path(sys.argv[2])\n"
    "print(json.dumps(names['approval'](sys.argv[3])))\n"
)


@pytest.fixture
def c() -> dict[str, Any]:
    """Return a fresh run of the conductor script's names."""
    return _conduct()


@pytest.fixture
def p(tmp_path: Path) -> Path:
    """Return a primary checkout on `main`."""
    return _primary(tmp_path)


@pytest.fixture
def home(isolated_home: Path) -> Path:
    """Return the isolated home folder this test runs with."""
    return isolated_home


@pytest.fixture
def fake(request: pytest.FixtureRequest) -> Callable[..., Path]:
    """Return the setter of the fake worker's modes, which also moves the home."""
    setter: Callable[..., Path] = request.getfixturevalue("_fake")
    return setter


def _kept() -> Path:
    """Return the home's kept folder, made."""
    folder = layout.kept_dir()
    folder.mkdir(mode=0o700, exist_ok=True)
    return folder


def _modes(path: Path) -> int:
    """Return the permission bits of `path`."""
    return stat.S_IMODE(path.stat().st_mode)


def _plant(path: Path, shape: str, text: str = "x\n", bound: int = _BOUND) -> None:
    """Make `path` a `shape`: a file, an empty file, a link, a folder and so on."""
    other = path.parent.parent / f".other-{path.name}"
    if shape == "file":
        path.write_text(text)
    elif shape == "empty":
        path.write_text("")
    elif shape == "binary":
        path.write_bytes(b"\xff\xfe" + text.encode())
    elif shape == "big":
        path.write_text(text + " " * (bound + 4096))
    elif shape == "link":
        other.write_text(text)
        path.symlink_to(other)
    elif shape == "dangling":
        path.symlink_to(path.parent.parent / ".nowhere")
    elif shape == "folder":
        path.mkdir()
    else:
        assert shape == "pipe", shape
        os.mkfifo(path)


@contextlib.contextmanager
def _umask(mask: int) -> Iterator[None]:
    """Hold the process's umask at `mask`."""
    before = os.umask(mask)
    try:
        yield
    finally:
        os.umask(before)


def _conductor(name: str, *args: str) -> tuple[str, ...]:
    """Return the child's code and arguments that call the conductor's `name`."""
    return _CHILD, str(_SCRIPT), name, *args


def _ask(code: str, *args: str) -> object:
    """Run `code` in a child with `args`; return what it prints, read as JSON."""
    command = [sys.executable, "-c", code, *args]
    done = subprocess.run(
        command, capture_output=True, text=True, timeout=30, check=True
    )
    return json.loads(done.stdout)


def _hangs(code: str, *args: str) -> bool:
    """Return whether `code` in a child is still running after 4 s, and kill it."""
    command = [sys.executable, "-c", code, *args]
    try:
        subprocess.run(command, capture_output=True, text=True, timeout=4, check=True)
    except subprocess.TimeoutExpired:
        return True
    return False


def test_the_kept_folder_lies_under_the_home(home: Path) -> None:
    assert layout.kept_dir() == home / ".mf-ship-origin"
    assert layout.kept_dir().is_relative_to(home)


def test_ledger_records_one_entry_in_a_folder_of_0700(
    c: dict[str, Any], p: Path, home: Path
) -> None:
    with _umask(0o022):
        c["_record_release"](p, "0001-a", _H)

    folder = layout.released_dir(p)
    assert _modes(home / ".mf-ship-origin") == 0o755
    assert _modes(folder) == 0o700
    assert [entry.name for entry in folder.iterdir()] == ["0001-a"]
    assert _modes(folder / "0001-a") == 0o600
    assert (folder / "0001-a").read_text() == f"{_H}\n"


def test_ledger_keeps_one_entry_a_change_and_the_newest_head(
    c: dict[str, Any], p: Path
) -> None:
    newer = _S
    c["_record_release"](p, "0001-a", _H)
    c["_record_release"](p, "0002-b", _H)
    c["_record_release"](p, "0001-a", newer)

    folder = layout.released_dir(p)
    assert sorted(entry.name for entry in folder.iterdir()) == ["0001-a", "0002-b"]
    assert (folder / "0001-a").read_text() == f"{newer}\n"
    assert (folder / "0002-b").read_text() == f"{_H}\n"


def test_ledger_replaces_a_link_at_an_entry_and_leaves_its_target(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    folder = layout.released_dir(p)
    folder.mkdir(parents=True)
    target = tmp_path / "target"
    target.write_text("the person's\n")
    (folder / "0001-a").symlink_to(target)

    c["_record_release"](p, "0001-a", _H)

    assert not (folder / "0001-a").is_symlink()
    assert (folder / "0001-a").read_text() == f"{_H}\n"
    assert target.read_text() == "the person's\n"


def test_ledger_entries_lists_every_name_of_the_folder(
    c: dict[str, Any], p: Path
) -> None:
    folder = layout.released_dir(p)
    assert mflib.kept.release_entries(p) == []
    folder.parent.mkdir(parents=True, exist_ok=True)
    folder.write_text("a file, no folder\n")
    assert mflib.kept.release_entries(p) == []
    folder.unlink()
    folder.mkdir()
    for name in ("0001-a", "0002-b", ".hidden"):
        (folder / name).write_text(f"{_H}\n")

    assert sorted(entry.name for entry in mflib.kept.release_entries(p)) == [
        ".hidden",
        "0001-a",
        "0002-b",
    ]


def test_ledger_heads_are_each_entrys_first_line(c: dict[str, Any], p: Path) -> None:
    assert c["_ledger_heads"](p) == set()
    folder = layout.released_dir(p)
    folder.mkdir(parents=True)
    for name, text in (
        ("e1", "h1\nh1b\n"),
        ("e2", "h2 \n"),
        ("e3", "h3"),
        ("e4", ""),
    ):
        (folder / name).write_text(text)

    assert c["_ledger_heads"](p) == {"h1", "h2 ", "h3", ""}


@pytest.mark.slow
def test_ledger_close_removes_the_entries_that_landed(
    c: dict[str, Any], p: Path
) -> None:
    _released(p, "v0.1.0")
    _released(p, "v0.2.0")
    unlanded, _ = _unmerged_release(p, "v0.3.0")
    folder = layout.released_dir(p)
    kept = (folder / "release-v0.3.0").read_text()
    main = _git(p, "rev-parse", "main").strip()

    c["_close_releases"](p, main)

    assert [entry.name for entry in folder.iterdir()] == ["release-v0.3.0"]
    assert (folder / "release-v0.3.0").read_text() == kept == f"{unlanded}\n"
    c["_close_releases"](p, main)
    assert [entry.name for entry in folder.iterdir()] == ["release-v0.3.0"]
    assert (folder / "release-v0.3.0").read_text() == kept


def test_ledger_close_reads_the_first_line_of_an_entry(
    c: dict[str, Any], p: Path
) -> None:
    _released(p, "v0.1.0")
    folder = layout.released_dir(p)
    head = (folder / "release-v0.1.0").read_text().strip()
    (folder / "release-v0.1.0").write_text(f"{head}\nsecond line\n")

    c["_close_releases"](p, _git(p, "rev-parse", "main").strip())

    assert list(folder.iterdir()) == []


def test_ledger_close_leaves_a_head_the_base_does_not_hold(
    c: dict[str, Any], p: Path
) -> None:
    _released(p, "v0.1.0")
    before = _git(p, "rev-parse", "main^1").strip()

    c["_close_releases"](p, before)

    assert [entry.name for entry in layout.released_dir(p).iterdir()] == [
        "release-v0.1.0"
    ]


def test_ledger_close_with_no_folder_is_quiet(c: dict[str, Any], p: Path) -> None:
    c["_close_releases"](p, _git(p, "rev-parse", "main").strip())

    assert not layout.released_dir(p).exists()


def _bare(tmp_path: Path, name: str = "origin.git") -> Path:
    """Return a bare repo holding no branch."""
    origin = tmp_path / name
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    return origin


def _with_origin(tmp_path: Path, p: Path) -> Path:
    """Add a bare `origin` holding `p`'s `main` to `p`; return it."""
    origin = _bare(tmp_path)
    _git(p, "remote", "add", "origin", str(origin))
    _git(p, "push", "-q", "origin", "main")
    return origin


@contextlib.contextmanager
def _readonly(folder: Path) -> Iterator[None]:
    """Hold `folder` at mode 0500."""
    before = _modes(folder)
    folder.chmod(0o500)
    try:
        yield
    finally:
        folder.chmod(before)


def _failing(monkeypatch: pytest.MonkeyPatch, target: Path) -> None:
    """Make `os.open` of `target` raise a bare `OSError()`."""
    opened = os.open

    def refuse(path: Any, *args: Any, **more: Any) -> int:  # noqa: ANN401
        if str(path) == str(target):
            raise OSError
        return opened(path, *args, **more)

    monkeypatch.setattr(os, "open", refuse)


def test_origin_kept_reads_none_before_a_run_kept_it(
    c: dict[str, Any], p: Path
) -> None:
    assert c["_kept_origin"](p) is None


def test_origin_kept_reads_the_two_lists(c: dict[str, Any], p: Path) -> None:
    _kept()
    layout.kept_file(p).write_text('[["u1"], ["u2", "u3"]]')

    assert c["_kept_origin"](p) == (["u1"], ["u2", "u3"])


def test_origin_kept_reads_none_for_a_folder_at_its_name(
    c: dict[str, Any], p: Path
) -> None:
    _kept()
    layout.kept_file(p).mkdir()

    assert c["_kept_origin"](p) is None


def test_origin_keep_writes_the_urls_and_the_default_branch(
    c: dict[str, Any], p: Path, tmp_path: Path, home: Path
) -> None:
    origin = _with_origin(tmp_path, p)
    pushed = "ssh://example.invalid/b.git"
    _git(p, "config", "--global", "remote.origin.pushurl", pushed)

    with _umask(0o022):
        assert c["_keep_origin"](p) is None

    kept = layout.kept_file(p)
    assert _modes(kept.parent) == 0o700
    assert _modes(kept) == 0o600
    assert json.loads(kept.read_text()) == [[str(origin)], [pushed]]
    named = layout.default_file(p)
    assert _modes(named) == 0o600
    assert named.read_text() == "main"


def test_origin_keep_leaves_a_standing_file_and_a_standing_default(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    _with_origin(tmp_path, p)
    _kept()
    layout.kept_file(p).write_text('[["old"], ["old"]]')
    layout.default_file(p).write_text("dev")

    assert c["_keep_origin"](p) is None

    assert layout.kept_file(p).read_text() == '[["old"], ["old"]]'
    assert layout.default_file(p).read_text() == "dev"


def test_origin_keep_writes_a_default_that_was_removed(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    _with_origin(tmp_path, p)
    c["_keep_origin"](p)
    layout.default_file(p).unlink()

    assert c["_keep_origin"](p) is None

    assert layout.default_file(p).read_text() == "main"


def test_origin_keep_with_no_origin_keeps_two_empty_lists(
    c: dict[str, Any], p: Path
) -> None:
    assert c["_keep_origin"](p) is None

    assert json.loads(layout.kept_file(p).read_text()) == [[], []]
    assert not layout.default_file(p).exists()


def test_origin_keep_of_an_origin_that_is_gone_keeps_no_default(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    gone = str(tmp_path / "gone.git")
    _git(p, "remote", "add", "origin", gone)

    assert c["_keep_origin"](p) is None

    assert json.loads(layout.kept_file(p).read_text()) == [[gone], [gone]]
    assert not layout.default_file(p).exists()


def test_origin_keep_of_an_origin_with_a_detached_head_keeps_no_default(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    origin = _with_origin(tmp_path, p)
    tip = _git(origin, "rev-parse", "main").strip()
    _git(origin, "update-ref", "--no-deref", "HEAD", tip)

    assert c["_keep_origin"](p) is None

    assert layout.kept_file(p).is_file()
    assert not layout.default_file(p).exists()


@pytest.mark.parametrize("shape", ["dangling", "folder"])
def test_origin_keep_leaves_what_stands_at_the_default(
    c: dict[str, Any], p: Path, tmp_path: Path, shape: str
) -> None:
    _with_origin(tmp_path, p)
    c["_keep_origin"](p)
    named = layout.default_file(p)
    named.unlink()
    _plant(named, shape)

    assert c["_keep_origin"](p) is None

    assert named.is_symlink() == (shape == "dangling")
    assert named.is_dir() == (shape == "folder")


def test_origin_keep_names_why_a_refused_folder_cannot_be_written(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    _with_origin(tmp_path, p)
    kept = _kept()

    with _readonly(kept):
        assert c["_keep_origin"](p) == "Permission denied"
    assert not layout.kept_file(p).exists()


def test_origin_keep_names_why_only_the_default_cannot_be_written(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    _with_origin(tmp_path, p)
    c["_keep_origin"](p)
    layout.default_file(p).unlink()

    with _readonly(layout.kept_dir()):
        assert c["_keep_origin"](p) == "Permission denied"


def test_origin_keep_names_a_bare_oserror_by_its_type(
    c: dict[str, Any], p: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _with_origin(tmp_path, p)
    _failing(monkeypatch, layout.kept_file(p))
    assert c["_keep_origin"](p) == "OSError"


def test_origin_keep_names_a_bare_oserror_of_the_default_by_its_type(
    c: dict[str, Any], p: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _with_origin(tmp_path, p)
    _failing(monkeypatch, layout.default_file(p))
    assert c["_keep_origin"](p) == "OSError"


def test_origin_default_is_the_name_git_gives_with_no_file(
    c: dict[str, Any], p: Path
) -> None:
    assert c["_kept_default"](p) == "main"
    _git(p, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk")

    assert c["_kept_default"](p) == "trunk"


@pytest.mark.parametrize("text", ["dev\n", "dev"])
def test_origin_default_reads_the_file_unstripped(
    c: dict[str, Any], p: Path, text: str
) -> None:
    _kept()
    layout.default_file(p).write_text(text)

    assert c["_kept_default"](p) == text


def test_origin_default_reads_git_name_for_a_folder_at_its_name(
    c: dict[str, Any], p: Path
) -> None:
    _git(p, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk")
    _kept()
    layout.default_file(p).mkdir()

    assert c["_kept_default"](p) == "trunk"


def test_base_keep_writes_the_sha_at_0600_in_a_folder_of_0700(
    c: dict[str, Any], p: Path
) -> None:
    with _umask(0o022):
        assert c["_keep_base"](p, _S) is None

    file = layout.pushed_file(p)
    assert _modes(file.parent) == 0o700
    assert _modes(file) == 0o600
    assert file.read_text() == f"{_S}\n"
    assert [entry.name for entry in file.parent.iterdir()] == [file.name]


def test_base_keep_replaces_an_older_base_and_leaves_the_folder_mode(
    c: dict[str, Any], p: Path
) -> None:
    kept = _kept()
    kept.chmod(0o755)
    assert c["_keep_base"](p, _H) is None

    assert c["_keep_base"](p, _S) is None

    file = layout.pushed_file(p)
    assert file.read_text() == f"{_S}\n"
    assert _modes(kept) == 0o755
    assert [entry.name for entry in kept.iterdir()] == [file.name]


def test_base_keep_with_a_full_folder_at_its_name_leaves_its_temp_file(
    c: dict[str, Any], p: Path
) -> None:
    file = layout.pushed_file(p)
    _kept()
    file.mkdir()
    (file / "held").write_text("x\n")

    why = c["_keep_base"](p, _S)

    assert why in {"Is a directory", "File exists", "Directory not empty"}
    left = [entry.name for entry in file.parent.iterdir() if entry != file]
    assert len(left) == 1
    assert left[0].startswith(f".{file.name}-")


def test_base_keep_names_why_a_refused_folder_cannot_be_written(
    c: dict[str, Any], p: Path
) -> None:
    with _readonly(_kept()):
        assert c["_keep_base"](p, _S) == "Permission denied"


def test_base_keep_with_a_file_at_the_kept_folder_names_it(
    c: dict[str, Any], p: Path
) -> None:
    layout.kept_dir().write_text("a file\n")

    assert c["_keep_base"](p, _S) == "File exists"


def test_base_keep_names_a_bare_oserror_by_its_type(
    c: dict[str, Any], p: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse(*_: object, **__: object) -> tuple[int, str]:
        raise OSError

    monkeypatch.setattr(tempfile, "mkstemp", refuse)

    assert c["_keep_base"](p, _S) == "OSError"


def test_base_offline_reads_none_with_no_file(c: dict[str, Any], p: Path) -> None:
    assert c["_offline_base"](p) is None


@pytest.mark.parametrize(
    ("text", "base"),
    [
        (f"{_S}\n", _S),
        (f"  {_S}  \n\n", _S),
        ("abc\ndef\n", "abc\ndef"),
        ("", None),
        ("  \n\t\n", None),
    ],
)
def test_base_offline_reads_the_stripped_text(
    c: dict[str, Any], p: Path, text: str, base: str | None
) -> None:
    _kept()
    layout.pushed_file(p).write_text(text)

    assert c["_offline_base"](p) == base


def test_base_offline_reads_none_for_a_folder_at_its_name(
    c: dict[str, Any], p: Path
) -> None:
    _kept()
    layout.pushed_file(p).mkdir()

    assert c["_offline_base"](p) is None


def _stop(c: dict[str, Any], call: Callable[[], object]) -> tuple[int, str]:
    """Return the exit and the text of the conductor's `Stop` that `call` raises."""
    with pytest.raises(c["Stop"]) as stopped:
        call()
    return stopped.value.code, str(stopped.value)


def _remedy(p: Path, name: str) -> str:
    """Return the words after which a halt names the kept file of `name`."""
    return f"a person decides, then removes ~/.mf-ship-origin/{name}"


def test_remote_push_default_is_the_branch_origin_names(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    origin = _with_origin(tmp_path, p)

    assert c["_push_default"](p, str(origin)) == "main"
    _kept()
    layout.default_file(p).write_text("main")
    assert c["_push_default"](p, str(origin)) == "main"


@pytest.mark.parametrize("kept", ["", "dev", "main\n"])
def test_remote_push_default_halts_on_a_kept_name_that_differs(
    c: dict[str, Any], p: Path, tmp_path: Path, kept: str
) -> None:
    origin = _with_origin(tmp_path, p)
    _kept()
    layout.default_file(p).write_text(kept)
    named = layout.default_file(p).name

    code, text = _stop(c, lambda: c["_push_default"](p, str(origin)))

    assert code == 1
    assert text == (
        f"conduct: halt — origin's HEAD names main, and the run kept {kept}:"
        f" {_remedy(p, named)}"
    )


def test_remote_push_default_halts_when_origin_names_no_branch(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    origin = _with_origin(tmp_path, p)
    tip = _git(origin, "rev-parse", "main").strip()
    _git(origin, "update-ref", "--no-deref", "HEAD", tip)

    code, text = _stop(c, lambda: c["_push_default"](p, str(origin)))

    assert code == 1
    assert text == (
        "conduct: halt — origin's HEAD names no branch: a person pushes the default"
        " branch, or points origin's HEAD at it"
    )
    _kept()
    layout.default_file(p).write_text("main")
    code, text = _stop(c, lambda: c["_push_default"](p, str(origin)))
    assert code == 1
    assert text == (
        "conduct: halt — origin's HEAD names no branch, and the run kept main:"
        f" {_remedy(p, layout.default_file(p).name)}"
    )


def test_remote_push_default_reads_a_folder_at_the_default_as_none_kept(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    origin = _with_origin(tmp_path, p)
    _kept()
    layout.default_file(p).mkdir()

    assert c["_push_default"](p, str(origin)) == "main"


_FETCH = "https://example.invalid/a.git"
_PUSH = "https://example.invalid/b.git"


def _network(p: Path, push: str | None = _PUSH, fetch: str = _FETCH) -> None:
    """Point `p`'s `origin` at `fetch`, its push URL in the global config."""
    _git(p, "remote", "add", "origin", fetch)
    if push:
        _git(p, "config", "--global", "remote.origin.pushurl", push)


def _keep(p: Path, fetch: list[str], push: list[str]) -> None:
    """Write the kept origin file as a run does."""
    _kept()
    layout.kept_file(p).write_text(json.dumps([fetch, push]))


def test_remote_refuse_origin_returns_the_urls_with_no_kept_file_and_with_an_equal_one(
    c: dict[str, Any], p: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MF_SHIP_AGENT", raising=False)
    _network(p)
    assert c["_refuse_origin"](p) == ([_FETCH], [_PUSH])

    _keep(p, [_FETCH], [_PUSH])

    assert c["_refuse_origin"](p) == ([_FETCH], [_PUSH])


def test_remote_refuse_origin_halts_on_a_changed_origin(
    c: dict[str, Any], p: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MF_SHIP_AGENT", raising=False)
    _network(p)
    name = layout.kept_file(p).name
    away = (
        "conduct: halt — the repo's git config points origin away from the URLs a run"
        " kept: read `git remote -v`, then repoint it, or remove"
        f" ~/.mf-ship-origin/{name} to keep what it reads now"
    )

    _keep(p, [_FETCH], [_FETCH])
    assert _stop(c, lambda: c["_refuse_origin"](p)) == (1, away)
    _keep(p, ["https://example.invalid/other.git"], [_PUSH])
    assert _stop(c, lambda: c["_refuse_origin"](p)) == (1, away)


def test_remote_refuse_origin_with_no_origin_is_two_empty_lists(
    c: dict[str, Any], p: Path
) -> None:
    assert c["_refuse_origin"](p) == ([], [])


_LOCAL = (
    "conduct: halt — the repo's git config points origin at a local repo, whose hooks"
    " would run on a push; repoint it"
)


def test_remote_refuse_origin_halts_on_a_local_path_unless_the_agent_is_set(
    c: dict[str, Any], p: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    here = str(_bare(tmp_path, "here.git"))
    _git(p, "remote", "add", "origin", here)
    monkeypatch.delenv("MF_SHIP_AGENT", raising=False)

    assert _stop(c, lambda: c["_refuse_origin"](p)) == (1, _LOCAL)
    monkeypatch.setenv("MF_SHIP_AGENT", "a fake worker")
    assert c["_refuse_origin"](p) == ([here], [here])


def test_remote_refuse_origin_halts_on_a_local_push_url_alone(
    c: dict[str, Any], p: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MF_SHIP_AGENT", raising=False)
    _network(p, push=str(_bare(tmp_path, "push.git")))

    assert _stop(c, lambda: c["_refuse_origin"](p)) == (1, _LOCAL)


@pytest.mark.parametrize("url", ["/x/a:b/c", "x/a:b"])
def test_remote_refuse_origin_halts_on_a_path_with_a_colon(
    c: dict[str, Any], p: Path, monkeypatch: pytest.MonkeyPatch, url: str
) -> None:
    monkeypatch.delenv("MF_SHIP_AGENT", raising=False)
    _git(p, "remote", "add", "origin", url)

    assert _stop(c, lambda: c["_refuse_origin"](p)) == (1, _LOCAL)


def test_remote_refuse_origin_accepts_a_host_and_a_path(
    c: dict[str, Any], p: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MF_SHIP_AGENT", raising=False)
    _git(p, "remote", "add", "origin", "host:path")

    assert c["_refuse_origin"](p) == (["host:path"], ["host:path"])


def test_remote_refuse_origin_with_the_agent_returns_fetch_then_push(
    c: dict[str, Any], p: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MF_SHIP_AGENT", "a fake worker")
    _network(p, push="/local/push.git", fetch="/local/fetch.git")

    assert c["_refuse_origin"](p) == (["/local/fetch.git"], ["/local/push.git"])


def test_remote_refuse_origin_halts_on_a_key_that_could_name_a_program(
    c: dict[str, Any], p: Path
) -> None:
    _git(p, "config", "core.sshCommand", "ssh -v")

    code, text = _stop(c, lambda: c["_refuse_origin"](p))

    assert code == 1
    assert text == (
        "conduct: halt — the repo's git config holds a key that could name a program:"
        " core.sshcommand; move it to the global config or remove it"
    )


def test_remote_read_url_goes_to_the_kept_origin_only_after_a_first_read(
    c: dict[str, Any], p: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MF_SHIP_AGENT", raising=False)
    _network(p)

    assert c["_read_url"](p, True) == _FETCH
    assert c["_read_url"](p, False) is None
    _keep(p, [_FETCH], [_PUSH])
    assert c["_read_url"](p, False) == _FETCH


def test_remote_read_url_reads_none_for_a_folder_at_the_kept_name(
    c: dict[str, Any], p: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MF_SHIP_AGENT", raising=False)
    _network(p)
    _kept()
    layout.kept_file(p).mkdir()

    assert c["_read_url"](p, False) is None
    assert c["_read_url"](p, True) == _FETCH


def test_remote_read_url_with_no_origin_is_none(c: dict[str, Any], p: Path) -> None:
    assert c["_read_url"](p, True) is None
    assert c["_read_url"](p, False) is None


def test_remote_read_url_takes_the_first_fetch_url(
    c: dict[str, Any], p: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MF_SHIP_AGENT", raising=False)
    _network(p, push=None)
    second = "https://example.invalid/second.git"
    _git(p, "remote", "set-url", "--add", "origin", second)

    assert c["_read_url"](p, True) == _FETCH


def _probed(p: Path, text: str | None = "ok\n", gated: str | None = "file") -> Path:
    """Make `p` a probe's scratch repo: `probe.txt` at `HEAD`, `.gated` as given."""
    if text is not None:
        _commit(p, {"probe.txt": text}, "probe")
    if gated == "file":
        (p / ".gated").write_text("")
    elif gated == "folder":
        (p / ".gated").mkdir()
    return p


_ESCAPED = "codex wrote outside its reach: it runs unsandboxed"


def test_probe_check_passes_with_no_mark_and_with_an_empty_one(
    c: dict[str, Any], p: Path
) -> None:
    _probed(p)
    mark = layout.probe_mark("codex", 41)
    _kept()
    mark.write_text("")

    assert c["check_probe"](p, None) is None
    assert c["check_probe"](p, mark) is None


@pytest.mark.parametrize("shape", ["one byte", "eight bytes", "gone", "folder"])
def test_probe_check_fails_a_mark_that_is_written_gone_or_no_file(
    c: dict[str, Any], p: Path, shape: str
) -> None:
    _probed(p)
    mark = layout.probe_mark("codex", 41)
    _kept()
    if shape == "one byte":
        mark.write_text("x")
    elif shape == "eight bytes":
        mark.write_text("escaped\n")
    elif shape == "folder":
        mark.mkdir()

    assert c["check_probe"](p, mark) == _ESCAPED


def test_probe_check_names_the_executor_of_the_mark(c: dict[str, Any], p: Path) -> None:
    _probed(p)

    gone = layout.probe_mark("claude", 7)

    assert c["check_probe"](p, gone) == (
        "claude wrote outside its reach: it runs unsandboxed"
    )
    assert gone.name == "probe-claude-7"


def test_probe_check_reads_a_dangling_arch_as_unreadable(
    c: dict[str, Any], p: Path
) -> None:
    _probed(p)
    (p / ".arch").symlink_to(p / ".nowhere")

    assert c["check_probe"](p, None) == (
        f"the worker's shell runs an unreadable .arch on a {platform.arch()} host"
    )


@pytest.mark.parametrize(
    ("text", "named"),
    [("a" * 16, True), ("a" * 17, False), ("a" * 20, False)],
)
def test_probe_check_names_a_short_arch_and_not_a_long_one(
    c: dict[str, Any], p: Path, text: str, named: bool
) -> None:
    _probed(p)
    (p / ".arch").write_text(text)
    native = platform.arch()

    expected = (
        f"the worker's shell runs as {text} on a {native} host"
        if named
        else f"the worker's shell runs an unreadable .arch on a {native} host"
    )
    assert c["check_probe"](p, None) == expected


def test_probe_check_reads_the_native_arch_in_upper_case_as_another_shell(
    c: dict[str, Any], p: Path
) -> None:
    _probed(p)
    native = platform.arch()
    (p / ".arch").write_text(native.upper())

    assert c["check_probe"](p, None) == (
        f"the worker's shell runs as {native.upper()} on a {native} host"
    )
    (p / ".arch").write_text(native)
    assert c["check_probe"](p, None) is None


def test_probe_check_reads_a_link_at_arch_as_unreadable(
    c: dict[str, Any], p: Path
) -> None:
    _probed(p)
    native = platform.arch()
    (p.parent / "arch").write_text(native)
    (p / ".arch").symlink_to(p.parent / "arch")

    assert c["check_probe"](p, None) == (
        f"the worker's shell runs an unreadable .arch on a {native} host"
    )


@pytest.mark.parametrize(
    ("text", "said"),
    [
        (None, "HEAD holds no probe.txt"),
        ("no\n", "probe.txt reads 'no'"),
        ("ok", None),
        ("  ok \n", None),
    ],
)
def test_probe_check_reads_probe_txt_at_head(
    c: dict[str, Any], p: Path, text: str | None, said: str | None
) -> None:
    _probed(p, text)

    assert c["check_probe"](p, None) == said


@pytest.mark.parametrize("gated", [None, "folder"])
def test_probe_check_wants_a_gated_file(
    c: dict[str, Any], p: Path, gated: str | None
) -> None:
    _probed(p, gated=gated)

    assert c["check_probe"](p, None) == "make gate left no .gated"


def _run_of(c: dict[str, Any], tmp_path: Path) -> Any:  # noqa: ANN401
    """Return a conductor `Run` over a primary, its run's claim folder made."""
    root = _primary(tmp_path)
    (root / ".minions" / "runs" / "active").mkdir(parents=True)
    return c["Run"](root, "claude")


def _spied(conductor: Any) -> list[dict[str, Any]]:  # noqa: ANN401
    """Return what each spawn of `conductor` finds on disk, as it starts."""
    seen: list[dict[str, Any]] = []
    spawn = conductor.spawn

    def wrapper(*args: Any, **more: Any) -> Any:  # noqa: ANN401
        scratch = Path(args[2])
        marks = sorted(layout.kept_dir().glob("probe-*"))
        seen.append(
            {
                "args": args,
                "more": more,
                "marks": [(m.name, m.stat().st_size, _modes(m)) for m in marks],
                "folder": _modes(layout.kept_dir()),
                "ignore": (scratch / ".gitignore").read_text(),
                "tree": (scratch / "tree").exists(),
                "scratch": scratch,
            }
        )
        return spawn(*args, **more)

    conductor.spawn = wrapper
    return seen


def _halted(conductor: Any) -> list[str]:  # noqa: ANN401
    """Return the reason of each halt `conductor` holds."""
    return [reason for _, reason in conductor.halts]


@pytest.mark.slow
def test_probe_run_writes_an_empty_mark_and_removes_it(
    c: dict[str, Any], tmp_path: Path, fake: Callable[..., Path]
) -> None:
    fake("first-turn")
    conductor = _run_of(c, tmp_path)
    seen = _spied(conductor)
    deadline = time.monotonic() + 600

    conductor.probe("claude", deadline=deadline)

    (spawned,) = seen
    assert spawned["marks"] == [(f"probe-claude-{os.getpid()}", 0, 0o600)]
    assert spawned["folder"] == 0o700
    assert spawned["more"]["limits"] is True
    assert spawned["more"]["deadline"] == deadline
    assert spawned["ignore"] == ".gated\n.arch\n"
    assert spawned["tree"] is False
    assert not spawned["scratch"].exists()
    assert list(layout.kept_dir().glob("probe-*")) == []
    assert "claude" in conductor.probed
    assert conductor.halts == []
    assert " · run · check — probe · pass" in conductor.log.path.read_text()


@pytest.mark.slow
def test_probe_run_makes_a_stale_mark_empty_and_leaves_the_folder_mode(
    c: dict[str, Any], tmp_path: Path, fake: Callable[..., Path]
) -> None:
    fake("first-turn")
    conductor = _run_of(c, tmp_path)
    kept = _kept()
    kept.chmod(0o755)
    (kept / f"probe-claude-{os.getpid()}").write_text("junk")
    seen = _spied(conductor)

    conductor.probe("claude")

    assert seen[0]["marks"] == [(f"probe-claude-{os.getpid()}", 0, 0o600)]
    assert _modes(kept) == 0o755


def test_probe_run_halts_on_a_folder_that_refuses_the_mark(
    c: dict[str, Any], tmp_path: Path, fake: Callable[..., Path]
) -> None:
    fake("first-turn")
    conductor = _run_of(c, tmp_path)
    seen = _spied(conductor)

    with _readonly(_kept()):
        conductor.probe("claude")

    assert seen == []
    assert _halted(conductor) == [
        "probe — cannot write the probe mark: Permission denied"
    ]


def test_probe_run_with_a_file_at_the_kept_folder_halts_and_raises(
    c: dict[str, Any], tmp_path: Path, fake: Callable[..., Path]
) -> None:
    fake("first-turn")
    conductor = _run_of(c, tmp_path)
    seen = _spied(conductor)
    layout.kept_dir().write_text("a file\n")

    with pytest.raises(NotADirectoryError):
        conductor.probe("claude")

    assert seen == []
    assert _halted(conductor) == ["probe — cannot write the probe mark: File exists"]


def test_probe_run_halts_once_when_the_executor_is_not_on_path(
    c: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    conductor = _run_of(c, tmp_path)
    seen = _spied(conductor)
    monkeypatch.delenv("MF_SHIP_AGENT", raising=False)
    monkeypatch.setenv("PATH", "")

    conductor.probe("nosuchexec")
    conductor.probe("claude")

    assert seen == []
    assert _halted(conductor) == [
        "probe-nosuchexec — nosuchexec is not on PATH",
        "probe — claude is not on PATH",
    ]


def test_probe_run_halts_when_a_skill_is_not_linked(
    c: dict[str, Any], tmp_path: Path, fake: Callable[..., Path]
) -> None:
    fake("first-turn")
    conductor = _run_of(c, tmp_path)
    seen = _spied(conductor)

    def unlinked(_: str) -> None:
        raise c["Stop"](2, "skill not linked")

    c["main"].__globals__["_unlinked"] = unlinked

    conductor.probe("claude")

    assert seen == []
    assert _halted(conductor) == ["probe — skill not linked"]


@pytest.mark.slow
def test_probe_run_halts_on_a_worker_that_wrote_out(
    c: dict[str, Any], tmp_path: Path, fake: Callable[..., Path]
) -> None:
    fake("unsandboxed")
    conductor = _run_of(c, tmp_path)

    conductor.probe("claude")

    assert _halted(conductor) == [
        "probe check fail — claude wrote outside its reach: it runs unsandboxed"
    ]
    assert list(layout.kept_dir().glob("probe-*")) == []
    assert "claude" not in conductor.probed


@contextlib.contextmanager
def _other_process() -> Iterator[int]:
    """Yield the pid of a live process that is neither this one nor its parent."""
    child = subprocess.Popen(["sleep", "30"])
    try:
        yield child.pid
    finally:
        child.kill()
        child.wait()


def _marked(p: Path, text: str) -> Path:
    """Write the live mark of `p`, holding `text`; return it."""
    mark = layout.live_mark(p)
    mark.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    mark.write_text(text)
    return mark


def test_live_mark_holds_this_pid_in_folders_of_0700(
    c: dict[str, Any], p: Path
) -> None:
    with _umask(0o022):
        mark = mflib.kept.mark_live(p, os.getpid(), os.getppid())

    assert mark == layout.live_dir() / layout.digest(p)
    assert mark.read_text() == f"{os.getpid()}\n"
    assert _modes(layout.kept_dir()) == 0o700
    assert _modes(layout.live_dir()) == 0o700
    assert mflib.kept.mark_live(p, os.getpid(), os.getppid()) == mark
    assert mark.read_text() == f"{os.getpid()}\n"


@pytest.mark.parametrize("held", ["parent", "own", "3999999", "junk", ""])
def test_live_mark_takes_over_a_mark_that_holds_no_other_live_process(
    c: dict[str, Any], p: Path, held: str
) -> None:
    text = {"parent": f"{os.getppid()}\n", "own": f"{os.getpid()}\n"}.get(held, held)
    mark = _marked(p, text)

    assert mflib.kept.mark_live(p, os.getpid(), os.getppid()) == mark

    assert mark.read_text() == f"{os.getpid()}\n"


def test_live_mark_leaves_the_mark_of_another_live_process(
    c: dict[str, Any], p: Path
) -> None:
    with _other_process() as other:
        mark = _marked(p, f"{other}\n")

        assert mflib.kept.mark_live(p, os.getpid(), os.getppid()) is None

        assert mark.read_text() == f"{other}\n"


def test_live_mark_is_none_where_the_home_refuses_it(
    c: dict[str, Any], p: Path
) -> None:
    with _readonly(_kept()):
        assert mflib.kept.mark_live(p, os.getpid(), os.getppid()) is None
    layout.kept_dir().rmdir()
    layout.kept_dir().write_text("a file\n")

    assert mflib.kept.mark_live(p, os.getpid(), os.getppid()) is None


def test_live_mark_is_none_for_a_folder_at_its_name(c: dict[str, Any], p: Path) -> None:
    layout.live_dir().mkdir(parents=True)
    layout.live_mark(p).mkdir()

    assert mflib.kept.mark_live(p, os.getpid(), os.getppid()) is None


def test_live_unmark_removes_the_mark_that_holds_this_pid(
    c: dict[str, Any], p: Path
) -> None:
    mark = _marked(p, f"{os.getpid()}\n")

    mflib.kept.unmark(mark, os.getpid())

    assert not mark.exists()


def test_live_unmark_of_none_is_quiet(c: dict[str, Any]) -> None:
    mflib.kept.unmark(None, os.getpid())


@pytest.mark.parametrize("held", ["parent", "3999999", "junk"])
def test_live_unmark_leaves_a_mark_that_holds_another_pid(
    c: dict[str, Any], p: Path, held: str
) -> None:
    text = f"{os.getppid()}\n" if held == "parent" else held
    mark = _marked(p, text)

    mflib.kept.unmark(mark, os.getpid())

    assert mark.read_text() == text


def test_repos_records_the_resolved_primary_once(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    link = tmp_path / "link"
    link.symlink_to(p)

    with _umask(0o022):
        c["_record_repo"](link)
    c["_record_repo"](p)

    repos = layout.repos_file()
    assert _modes(repos.parent) == 0o700
    assert _modes(repos) == 0o600
    assert repos.read_text() == f"{p.resolve()}\n"


def test_repos_records_each_repo_a_line(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    other = tmp_path / "other"
    other.mkdir()

    c["_record_repo"](p)
    c["_record_repo"](other)

    assert layout.repos_file().read_text() == f"{p.resolve()}\n{other.resolve()}\n"


def test_repos_records_a_primary_a_longer_line_starts_with(
    c: dict[str, Any], p: Path
) -> None:
    _kept()
    layout.repos_file().write_text(f"{p.resolve()}x\n")

    c["_record_repo"](p)

    assert layout.repos_file().read_text() == f"{p.resolve()}x\n{p.resolve()}\n"


def test_repos_appends_to_a_list_with_a_bad_byte(c: dict[str, Any], p: Path) -> None:
    _kept()
    layout.repos_file().write_bytes(b"\xff\xfe\n")

    c["_record_repo"](p)

    assert (
        layout.repos_file().read_bytes() == b"\xff\xfe\n" + f"{p.resolve()}\n".encode()
    )


def test_repos_writes_nothing_through_a_dangling_link(
    c: dict[str, Any], p: Path
) -> None:
    _kept()
    layout.repos_file().symlink_to(layout.kept_dir() / ".nowhere")

    c["_record_repo"](p)

    assert not (layout.kept_dir() / ".nowhere").exists()


def test_repos_writes_nothing_through_a_link_to_a_file(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    target = tmp_path / "target"
    target.write_text("the person's\n")
    _kept()
    layout.repos_file().symlink_to(target)

    c["_record_repo"](p)

    assert target.read_text() == "the person's\n"


def test_repos_records_nothing_where_the_home_refuses_it(
    c: dict[str, Any], p: Path
) -> None:
    kept = _kept()
    with _readonly(kept):
        c["_record_repo"](p)
    assert not layout.repos_file().exists()
    kept.rmdir()
    kept.write_text("a file\n")

    c["_record_repo"](p)

    assert kept.read_text() == "a file\n"


def test_repos_leaves_a_list_it_cannot_read(c: dict[str, Any], p: Path) -> None:
    _kept()
    repos = layout.repos_file()
    repos.write_text("/elsewhere\n")
    repos.chmod(0)
    try:
        c["_record_repo"](p)
    finally:
        repos.chmod(0o600)

    assert repos.read_text() == "/elsewhere\n"


_CHANGE = "0002-gate"
_HASH = "ab" * 32
_OTHER = "cd" * 32
_SANDBOX = "; a sandbox refuses the home folder: run it outside one"


def _approved(p: Path) -> Path:
    """Cut `_CHANGE` beside `p`; return the folder `approve_gate` keeps entries in."""
    _version(p, _CHANGE, "- [ ] 1 — One\n")
    return layout.gate_approval(p, _CHANGE).parent


def test_approval_records_the_hash_at_0600_in_a_folder_of_0700(
    c: dict[str, Any], p: Path
) -> None:
    folder = _approved(p)

    said = c["approve_gate"](p, _CHANGE, _HASH)

    assert said == f"approve-gate: approved — {_HASH} · {_CHANGE}"
    assert _modes(folder) == 0o700
    assert _modes(folder / _CHANGE) == 0o600
    assert (folder / _CHANGE).read_text() == f"{_HASH}\n"


def test_approval_of_a_second_hash_replaces_the_first(
    c: dict[str, Any], p: Path
) -> None:
    folder = _approved(p)
    c["approve_gate"](p, _CHANGE, _HASH)

    c["approve_gate"](p, _CHANGE, _OTHER)

    assert (folder / _CHANGE).read_text() == f"{_OTHER}\n"


def test_approval_replaces_a_link_at_the_entry_and_leaves_its_target(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    folder = _approved(p)
    folder.mkdir(parents=True)
    target = tmp_path / "target"
    target.write_text("the person's\n")
    (folder / _CHANGE).symlink_to(target)

    c["approve_gate"](p, _CHANGE, _HASH)

    assert not (folder / _CHANGE).is_symlink()
    assert (folder / _CHANGE).read_text() == f"{_HASH}\n"
    assert target.read_text() == "the person's\n"


@pytest.mark.parametrize("change", ["0009-unknown", "0003-no-worktree"])
def test_approval_needs_a_version_worktree(
    c: dict[str, Any], p: Path, change: str
) -> None:
    _git(p, "branch", "0003-no-worktree")

    assert _stop(c, lambda: c["approve_gate"](p, change, _HASH)) == (
        2,
        f"approve-gate: cannot run — no version worktree holds {change}",
    )


@pytest.mark.parametrize(
    "hashed", [_HASH + "0", _HASH[:-1], _HASH.upper(), "x" + _HASH, "not-a-hash", ""]
)
def test_approval_refuses_what_is_no_hash_and_writes_nothing(
    c: dict[str, Any], p: Path, hashed: str
) -> None:
    folder = _approved(p)

    assert _stop(c, lambda: c["approve_gate"](p, _CHANGE, hashed)) == (
        1,
        f"approve-gate: refused — not the hash a halt names: {hashed}",
    )
    assert not folder.exists()


def test_approval_words_why_the_home_cannot_be_written(
    c: dict[str, Any], p: Path
) -> None:
    _approved(p)
    refused = "approve-gate: cannot write the approval — "
    with _readonly(_kept()):
        assert _stop(c, lambda: c["approve_gate"](p, _CHANGE, _HASH)) == (
            2,
            f"{refused}Permission denied{_SANDBOX}",
        )
    layout.kept_dir().rmdir()
    layout.kept_dir().write_text("a file\n")

    assert _stop(c, lambda: c["approve_gate"](p, _CHANGE, _HASH)) == (
        2,
        f"{refused}Not a directory{_SANDBOX}",
    )


def _anchored(tmp_path: Path, p: Path) -> str:
    """Give `p` an origin holding a release `v0.1.0`; return the sha it tracks."""
    _with_origin(tmp_path, p)
    _released(p, "v0.1.0")
    _git(p, "push", "-q", "origin", "main")
    return _git(p, "rev-parse", "origin/main").strip()


def _anchor(c: dict[str, Any], p: Path, yes: str | None) -> tuple[int, str]:
    """Return the exit and the text of an `anchor` that stops."""
    return _stop(c, lambda: c["anchor"](p, yes))


@pytest.mark.slow
def test_anchor_writes_the_base_the_person_named(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    tracked = _anchored(tmp_path, p)

    said = c["anchor"](p, tracked)

    assert said == f"anchor: {tracked} · Merge branch 'release-v0.1.0'"
    assert layout.pushed_file(p).read_text() == f"{tracked}\n"
    assert _modes(layout.pushed_file(p)) == 0o600


@pytest.mark.parametrize("cut", [8, -1, 0])
@pytest.mark.slow
def test_anchor_refuses_a_name_that_is_not_the_sha(
    c: dict[str, Any], p: Path, tmp_path: Path, cut: int
) -> None:
    tracked = _anchored(tmp_path, p)
    yes = tracked[:cut] if cut else ""

    assert _anchor(c, p, yes) == (
        2,
        f"anchor: cannot run — origin/main is {tracked}, not {yes}",
    )
    assert not layout.pushed_file(p).exists()


@pytest.mark.slow
def test_anchor_without_a_name_shows_the_sha_to_check(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    tracked = _anchored(tmp_path, p)

    assert _anchor(c, p, None) == (
        1,
        f"anchor: check {tracked} · Merge branch 'release-v0.1.0' against origin's"
        f" main, then run conduct.py anchor --yes {tracked}",
    )


def test_anchor_reads_the_kept_default_branch(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    tracked = _anchored(tmp_path, p)
    _kept()
    layout.default_file(p).write_text("trunk")

    assert _anchor(c, p, tracked) == (2, "anchor: cannot run — origin/trunk is missing")


def test_anchor_refuses_a_key_that_could_name_a_program(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    tracked = _anchored(tmp_path, p)
    _git(p, "config", "core.sshCommand", "ssh -v")

    code, text = _anchor(c, p, tracked)

    assert code == 1
    assert "could name a program" in text


def test_anchor_words_why_the_home_cannot_be_written(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    tracked = _anchored(tmp_path, p)
    refused = "anchor: cannot write the offline base — "
    with _readonly(_kept()):
        assert _anchor(c, p, tracked) == (2, f"{refused}Permission denied{_SANDBOX}")


@pytest.mark.slow
def test_anchor_stops_on_a_folder_at_the_base(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    tracked = _anchored(tmp_path, p)
    _kept()
    layout.pushed_file(p).mkdir()

    code, text = _anchor(c, p, tracked)

    assert code == 2
    assert text.startswith("anchor: cannot write the offline base — ")


def test_anchor_stops_where_a_base_stands(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    tracked = _anchored(tmp_path, p)
    c["_keep_base"](p, _S)

    assert _anchor(c, p, tracked) == (
        2,
        "anchor: cannot run — an offline base stands:"
        f" ~/.mf-ship-origin/{layout.pushed_file(p).name}",
    )


def test_anchor_stops_on_an_origin_with_no_release_merge(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    _with_origin(tmp_path, p)

    assert _anchor(c, p, None) == (
        2,
        "anchor: cannot run — origin/main is no release merge",
    )


def test_anchor_stops_on_a_tracking_ref_off_the_branch(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    _anchored(tmp_path, p)
    off = _git(p, "commit-tree", "-p", "main", "-m", "off", "main^{tree}").strip()
    _git(p, "update-ref", "refs/remotes/origin/main", off)

    assert _anchor(c, p, None) == (2, "anchor: cannot run — origin/main is not on main")


@pytest.fixture
def gate_check(p: Path, monkeypatch: pytest.MonkeyPatch) -> Callable[[str], str | None]:
    """Return `gate_check.py`'s `approval`, its `_primary` the fixture's repo."""
    monkeypatch.setattr(sys, "path", list(sys.path))
    script = (
        Path(__file__).resolve().parent.parent
        / "skills"
        / "mf-converge"
        / "scripts"
        / "gate_check.py"
    )
    spec = importlib.util.spec_from_file_location("gate_check_pins", script)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "_primary", lambda: p)
    return module.approval


def _entry(p: Path, change: str = _CHANGE) -> Path:
    """Return the approval entry of `change`, its folder made."""
    entry = layout.gate_approval(p, change)
    entry.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    return entry


def test_approval_reads_none_with_no_entry_and_for_another_change(
    gate_check: Callable[[str], str | None], p: Path
) -> None:
    assert gate_check(_CHANGE) is None
    _entry(p).write_text(f"{_HASH}\n")

    assert gate_check("0003-other") is None


@pytest.mark.parametrize(
    ("text", "read"),
    [(f"{_HASH}\nsecond\n", _HASH), (f"{_HASH} \n", f"{_HASH} "), ("", "")],
)
def test_approval_reads_the_first_line_unstripped(
    gate_check: Callable[[str], str | None], p: Path, text: str, read: str
) -> None:
    _entry(p).write_text(text)

    assert gate_check(_CHANGE) == read


def test_approval_reads_none_for_a_folder_at_the_entry(
    gate_check: Callable[[str], str | None], p: Path
) -> None:
    _entry(p).mkdir()

    assert gate_check(_CHANGE) is None


def test_approval_reads_none_for_an_entry_it_cannot_open(
    gate_check: Callable[[str], str | None], p: Path
) -> None:
    entry = _entry(p)
    entry.write_text(f"{_HASH}\n")
    entry.chmod(0)
    try:
        assert gate_check(_CHANGE) is None
    finally:
        entry.chmod(0o600)


def test_approval_raises_on_a_bad_byte(
    gate_check: Callable[[str], str | None], p: Path
) -> None:
    _entry(p).write_bytes(b"\xff\xfe\n")

    with pytest.raises(UnicodeDecodeError):
        gate_check(_CHANGE)


def test_mixed_primary_of_a_tree_outside_the_primary_needs_a_kept_origin(
    c: dict[str, Any], p: Path
) -> None:
    tree = _version(p, "0001-a", "- [ ] 1 — A\n")

    code, text = _stop(c, lambda: c["primary_of"](tree))

    assert code == 1
    assert "no run kept its URLs" in text
    _kept()
    layout.kept_file(p).mkdir()
    assert _stop(c, lambda: c["primary_of"](tree)) == (code, text)
    layout.kept_file(p).rmdir()
    layout.kept_file(p).write_text("[[], []]")

    assert c["primary_of"](tree) == p


def test_mixed_unread_waits_on_a_merged_tag_and_a_kept_file(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    _with_origin(tmp_path, p)
    assert c["_unread"](p) is False
    _released(p, "v0.1.0")

    assert c["_unread"](p) is True
    _kept()
    layout.kept_file(p).mkdir()
    assert c["_unread"](p) is True
    layout.kept_file(p).rmdir()
    layout.kept_file(p).write_text("[[], []]")
    assert c["_unread"](p) is False


def test_mixed_run_pushes_to_the_origin_or_to_the_kept_push_list(
    c: dict[str, Any], p: Path
) -> None:
    _git(p, "remote", "add", "origin", "/a.git")
    assert c["Run"](p, "claude").pushes == ["/a.git"]

    _keep(p, ["/f.git"], ["/p1.git", "/p2.git"])

    assert c["Run"](p, "claude").pushes == ["/p1.git", "/p2.git"]


@pytest.mark.slow
def test_mixed_run_names_what_is_unpushed_only_while_offline(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    _with_origin(tmp_path, p)
    c["_keep_base"](p, _git(p, "rev-parse", "main").strip())
    _released(p, "v0.2.0")
    _kept()
    layout.default_file(p).write_text("main")
    _git(p, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk")
    conductor = c["Run"](p, "claude")

    conductor.offline = True
    assert conductor.unpushed() == " · unpushed main v0.2.0"
    conductor.offline = False
    assert conductor.unpushed() == ""


def _gone_origin(p: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point `p`'s `origin` at a repo that is gone, its URLs kept, a worker set."""
    monkeypatch.setenv("MF_SHIP_AGENT", "a fake worker")
    gone = str(tmp_path / "gone.git")
    _git(p, "remote", "add", "origin", gone)
    _keep(p, [gone], [gone])


def test_mixed_unpushed_halts_where_origin_has_no_default_and_keeps_no_base(
    c: dict[str, Any], p: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _gone_origin(p, tmp_path, monkeypatch)
    _git(p, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk")

    assert _stop(c, lambda: c["_unpushed"](p, first_read=False)) == (
        1,
        "conduct: halt — origin has no trunk: push it by hand",
    )
    assert not layout.pushed_file(p).exists()


@pytest.mark.slow
def test_mixed_unpushed_first_read_keeps_the_base_and_closes_the_ledger(
    c: dict[str, Any], p: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MF_SHIP_AGENT", "a fake worker")
    origin = _with_origin(tmp_path, p)
    _released(p, "v0.1.0")
    _git(p, "push", "-q", "origin", "main", "v0.1.0")
    assert c["_ledger_heads"](p) != set()

    assert c["_unpushed"](p, first_read=True, start=False) == []

    tip = _git(origin, "rev-parse", "main").strip()
    assert layout.pushed_file(p).read_text() == f"{tip}\n"
    assert c["_ledger_heads"](p) == set()


def _run_by_main(c: dict[str, Any], p: Path, monkeypatch: pytest.MonkeyPatch) -> int:
    """Return the exit of the conductor's `run` command in `p`."""
    monkeypatch.chdir(p)
    return int(c["main"](["run", "--executor", "claude"]))


def test_mixed_run_stops_and_leaves_no_live_mark_where_the_claim_is_refused(
    c: dict[str, Any],
    p: Path,
    fake: Callable[..., Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake()

    def refuse(_: Path) -> None:
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(c["mflib"].claim, "take", refuse)
    monkeypatch.setattr(c["Run"], "ship", lambda _: 0)

    assert _run_by_main(c, p, monkeypatch) == 2

    assert not layout.live_mark(p).exists()


def test_mixed_run_leaves_no_live_mark_where_the_close_raises(
    c: dict[str, Any],
    p: Path,
    fake: Callable[..., Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake()

    def fail(*_: object) -> None:
        raise RuntimeError("the close failed")

    monkeypatch.setitem(c["main"].__globals__, "_close", fail)
    monkeypatch.setattr(c["Run"], "ship", lambda _: 0)

    with pytest.raises(RuntimeError, match="the close failed"):
        _run_by_main(c, p, monkeypatch)

    assert not layout.live_mark(p).exists()
    assert (p / ".minions" / "runs" / "active").exists()


def _offline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict[str, Any], Path, Callable[..., list[str]]]:
    """Return the conductor, a primary and a run, `origin` gone and the base kept."""
    conduct = test_conduct._conduct()
    root, origin, run = _offline_retries(tmp_path, conduct, monkeypatch)
    _version(root, "0001-todo", "- [ ] 1 — Todo\n")
    origin.rename(tmp_path / "origin.away")
    conduct["_keep_base"](root, _git(root, "rev-parse", "main").strip())
    return conduct, root, run


@pytest.mark.slow
def test_mixed_offline_run_logs_the_release_it_ledgers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    fake()
    conduct, root, run = _offline(tmp_path, monkeypatch)

    lines = run(0)

    (head,) = conduct["_ledger_heads"](root)
    assert f"0001-todo · ledger — 0001-todo {head}" in lines


@pytest.mark.slow
def test_mixed_offline_run_halts_on_a_kept_default_git_does_not_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    fake()
    conduct, root, run = _offline(tmp_path, monkeypatch)
    _kept()
    layout.default_file(root).write_text("trunk")

    lines = run(1)

    halts = [line for line in lines if line.startswith("run · halt — conduct: ")]
    assert len(halts) == 1
    assert "trunk" in halts[0]
    assert not any(" ledger — " in line for line in lines)
    assert conduct["_ledger_heads"](root) == set()


_OCTOPUS = ("-q", "--no-ff", "-m", "an octopus", "side-a", "side-b")


@pytest.mark.slow
def test_mixed_push_goes_past_an_octopus_merge_before_the_kept_base(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    origin = _with_origin(tmp_path, p)
    for side in ("side-a", "side-b"):
        _git(p, "switch", "-q", "-c", side)
        _git(p, "commit", "-q", "--allow-empty", "-m", side)
        _git(p, "switch", "-q", "main")
    _git(p, "merge", *_OCTOPUS)
    c["_keep_base"](p, _git(p, "rev-parse", "main").strip())
    _commit(p, {"next.txt": "x\n"}, "next")
    new = _git(p, "rev-parse", "main").strip()
    conductor = c["Run"](p, "claude")

    assert conductor.push([("refs/heads/main", new)]) is True

    assert conductor.halts == []
    assert layout.pushed_file(p).read_text() == f"{new}\n"
    assert _git(origin, "rev-parse", "main").strip() == new


def _reads(call: Callable[[], object], outcome: object) -> None:
    """Assert `call` returns `outcome`, or raises it when `outcome` is an exception."""
    if isinstance(outcome, type) and issubclass(outcome, Exception):
        with pytest.raises(outcome):
            call()
    else:
        assert call() == outcome


_URLS = '[["u1"], ["u2"]]'
_PAIR = (["u1"], ["u2"])


@pytest.mark.parametrize(
    ("shape", "outcome"),
    [
        ("link", _PAIR),
        ("folder", None),
        ("binary", UnicodeDecodeError),
        ("empty", json.JSONDecodeError),
        ("big", _PAIR),
    ],
)
def test_shape_kept_origin_as_it_reads(
    c: dict[str, Any], p: Path, shape: str, outcome: object
) -> None:
    _kept()
    _plant(layout.kept_file(p), shape, _URLS)

    _reads(lambda: c["_kept_origin"](p), outcome)


@pytest.mark.parametrize(
    ("shape", "outcome"),
    [
        ("link", "dev"),
        ("folder", "main"),
        ("binary", UnicodeDecodeError),
        ("empty", ""),
    ],
)
def test_shape_default_as_it_reads(
    c: dict[str, Any], p: Path, shape: str, outcome: object
) -> None:
    _kept()
    _plant(layout.default_file(p), shape, "dev")

    _reads(lambda: c["_kept_default"](p), outcome)


def test_shape_default_over_its_bound_is_read_whole(c: dict[str, Any], p: Path) -> None:
    _kept()
    _plant(layout.default_file(p), "big", "dev")

    read = c["_kept_default"](p)

    assert read.startswith("dev")
    assert len(read) > _BOUND


@pytest.mark.parametrize(
    ("shape", "outcome"),
    [
        ("link", _S),
        ("folder", None),
        ("binary", UnicodeDecodeError),
        ("empty", None),
        ("big", _S),
    ],
)
def test_shape_offline_base_as_it_reads(
    c: dict[str, Any], p: Path, shape: str, outcome: object
) -> None:
    _kept()
    _plant(layout.pushed_file(p), shape, f"{_S}\n")

    _reads(lambda: c["_offline_base"](p), outcome)


@pytest.mark.parametrize(
    ("shape", "outcome"),
    [
        ("link", {_H}),
        ("folder", IsADirectoryError),
        ("binary", UnicodeDecodeError),
        ("empty", {""}),
        ("big", {_H}),
    ],
)
def test_shape_ledger_entry_as_it_reads(
    c: dict[str, Any], p: Path, shape: str, outcome: object
) -> None:
    folder = layout.released_dir(p)
    folder.mkdir(parents=True)
    _plant(folder / "0001-a", shape, f"{_H}\n")

    _reads(lambda: c["_ledger_heads"](p), outcome)


@pytest.mark.slow
@pytest.mark.parametrize(
    ("name", "where", "outcome"),
    [
        ("_kept_origin", layout.kept_file, None),
        ("_kept_default", layout.default_file, "main"),
        ("_offline_base", layout.pushed_file, None),
    ],
)
def test_shape_a_pipe_reads_as_no_file(
    p: Path, name: str, where: Callable[[Path], Path], outcome: object
) -> None:
    _kept()
    os.mkfifo(where(p))

    assert _ask(*_conductor(name, str(p))) == outcome


@pytest.mark.slow
def test_shape_a_pipe_at_a_ledger_entry_blocks_the_read(p: Path) -> None:
    folder = layout.released_dir(p)
    folder.mkdir(parents=True)
    os.mkfifo(folder / "0001-a")

    assert _hangs(*_conductor("_ledger_heads", str(p))) is True


@pytest.mark.parametrize(
    ("shape", "outcome"),
    [
        ("link", _HASH),
        ("folder", None),
        ("binary", UnicodeDecodeError),
        ("empty", ""),
        ("big", _HASH),
    ],
)
def test_odd_approval_as_it_reads(
    gate_check: Callable[[str], str | None],
    p: Path,
    shape: str,
    outcome: object,
) -> None:
    folder = layout.gate_approval(p, _CHANGE).parent
    folder.mkdir(parents=True)
    _plant(folder / _CHANGE, shape, f"{_HASH}\n")

    _reads(lambda: gate_check(_CHANGE), outcome)


@pytest.mark.slow
def test_odd_a_pipe_at_the_approval_blocks_the_read(p: Path) -> None:
    folder = layout.gate_approval(p, _CHANGE).parent
    folder.mkdir(parents=True)
    os.mkfifo(folder / _CHANGE)

    assert _hangs(_APPROVAL_CHILD, str(_GATE_CHECK), str(p), _CHANGE) is True


@pytest.mark.parametrize(
    ("shape", "outcome"),
    [
        ("link", "this pid"),
        ("folder", None),
        ("binary", None),
        ("empty", None),
        ("big", "this pid"),
    ],
)
def test_odd_live_mark_as_it_reads(
    c: dict[str, Any], p: Path, shape: str, outcome: str | None
) -> None:
    layout.live_dir().mkdir(parents=True)
    mark = layout.live_mark(p)
    _plant(mark, shape, f"{os.getpid()}\n")

    assert c["_pin"]()["holder"](mark) == (os.getpid() if outcome else None)


@pytest.mark.slow
def test_odd_a_pipe_at_the_live_mark_blocks_the_read(p: Path) -> None:
    layout.live_dir().mkdir(parents=True)
    mark = layout.live_mark(p)
    os.mkfifo(mark)

    assert _hangs(_HOLDER_CHILD, str(_SCRIPT), str(mark)) is True


def _listed(p: Path, shape: str) -> Path:
    """Plant `shape` at the list of repos, holding `/elsewhere`; return its path."""
    _kept()
    repos = layout.repos_file()
    _plant(repos, shape, "/elsewhere\n", bound=_REPOS_BOUND)
    return repos


def test_odd_repos_leaves_a_link_to_a_file_as_it_was(
    c: dict[str, Any], p: Path
) -> None:
    repos = _listed(p, "link")

    c["_record_repo"](p)

    assert repos.read_text() == "/elsewhere\n"


def test_odd_repos_records_nothing_for_a_folder_and_raises_nothing(
    c: dict[str, Any], p: Path
) -> None:
    repos = _listed(p, "folder")

    c["_record_repo"](p)

    assert repos.is_dir()


def test_odd_repos_appends_to_a_list_with_a_bad_byte(
    c: dict[str, Any], p: Path
) -> None:
    repos = _listed(p, "binary")

    c["_record_repo"](p)

    assert repos.read_bytes() == b"\xff\xfe/elsewhere\n" + f"{p.resolve()}\n".encode()


def test_odd_repos_appends_to_an_empty_list(c: dict[str, Any], p: Path) -> None:
    repos = _listed(p, "empty")

    c["_record_repo"](p)

    assert repos.read_text() == f"{p.resolve()}\n"


def test_odd_repos_appends_to_a_list_over_its_bound(c: dict[str, Any], p: Path) -> None:
    repos = _listed(p, "big")

    c["_record_repo"](p)

    text = repos.read_text()
    assert len(text) > _REPOS_BOUND
    assert text.startswith("/elsewhere")
    assert text.endswith(f"{p.resolve()}\n")


@pytest.mark.slow
def test_odd_a_pipe_at_repos_blocks_the_append(p: Path) -> None:
    _listed(p, "pipe")

    assert _hangs(*_conductor("_record_repo", str(p))) is True


_FULL = OSError(errno.ENOSPC, "No space left on device")


def test_write_a_failed_origin_write_leaves_a_half_written_file(
    c: dict[str, Any], p: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _with_origin(tmp_path, p)

    def full(*_: object, **__: object) -> None:
        raise _FULL

    monkeypatch.setattr(json, "dump", full)

    assert c["_keep_origin"](p) == "No space left on device"

    assert layout.kept_file(p).is_file()
    assert layout.kept_file(p).read_text() == ""


class _Full:
    """A file whose write fails with a full disk, the descriptor closed on exit."""

    def __init__(self, fd: int) -> None:
        self.fd = fd

    def __enter__(self) -> "_Full":
        return self

    def __exit__(self, *_: object) -> None:
        os.close(self.fd)

    def write(self, _: str) -> None:
        raise _FULL


def test_write_a_failed_default_write_leaves_its_file(
    c: dict[str, Any], p: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _with_origin(tmp_path, p)
    opened = os.fdopen
    calls: list[int] = []

    def second_is_full(fd: int, *args: Any, **more: Any) -> Any:  # noqa: ANN401
        calls.append(fd)
        return _Full(fd) if len(calls) == 2 else opened(fd, *args, **more)

    monkeypatch.setattr(os, "fdopen", second_is_full)

    assert c["_keep_origin"](p) == "No space left on device"

    assert layout.default_file(p).is_file()
    assert layout.default_file(p).read_text() == ""


def test_write_a_failed_base_write_leaves_its_temp_file(
    c: dict[str, Any], p: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def full(*_: object) -> None:
        raise _FULL

    monkeypatch.setattr(os, "replace", full)

    assert c["_keep_base"](p, _S) == "No space left on device"

    file = layout.pushed_file(p)
    assert not file.exists()
    (left,) = file.parent.iterdir()
    assert left.name.startswith(f".{file.name}-")


def test_write_a_live_link_at_the_default_skips_the_write(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    _with_origin(tmp_path, p)
    c["_keep_origin"](p)
    named = layout.default_file(p)
    named.unlink()
    _plant(named, "link", "dev")

    assert c["_keep_origin"](p) is None

    assert named.is_symlink()
    assert named.read_text() == "dev"


def test_write_a_dangling_link_at_the_default_is_refused_and_not_followed(
    c: dict[str, Any], p: Path, tmp_path: Path, home: Path
) -> None:
    _with_origin(tmp_path, p)
    c["_keep_origin"](p)
    named = layout.default_file(p)
    named.unlink()
    _plant(named, "dangling")

    assert c["_keep_origin"](p) is None

    assert named.is_symlink()
    assert not (home / ".nowhere").exists()


def test_write_the_default_has_no_newline(
    c: dict[str, Any], p: Path, tmp_path: Path
) -> None:
    _with_origin(tmp_path, p)

    c["_keep_origin"](p)

    assert layout.default_file(p).read_bytes() == b"main"


def _viewer_lists(p: Path) -> list[Path]:
    """Return the repos the viewer's `projects` reads from the list."""
    names = runpy.run_path(str(_VIEWER))
    return [entry.path for entry in names["projects"](layout.repos_file(), [])]


def _metrics_lists(p: Path) -> list[Path]:
    """Return the repos the metrics script's `_recorded_repos` reads."""
    spec = importlib.util.spec_from_file_location("review_metrics_pins", _METRICS)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return list(module._recorded_repos())


@pytest.mark.parametrize("reader", [_viewer_lists, _metrics_lists])
def test_write_the_readers_of_repos_take_a_list_with_a_bad_byte(
    p: Path, reader: Callable[[Path], list[Path]]
) -> None:
    (p / ".minions").mkdir()
    _kept()
    layout.repos_file().write_bytes(b"\xff\xfe\n" + f"{p}\n".encode())

    assert reader(p) == [p.resolve()]


@pytest.mark.parametrize("reader", [_viewer_lists, _metrics_lists])
def test_write_the_readers_of_repos_read_a_list_of_mode_0_as_none(
    p: Path, reader: Callable[[Path], list[Path]]
) -> None:
    (p / ".minions").mkdir()
    _kept()
    repos = layout.repos_file()
    repos.write_text(f"{p}\n")
    repos.chmod(0)
    try:
        assert reader(p) == []
    finally:
        repos.chmod(0o600)
