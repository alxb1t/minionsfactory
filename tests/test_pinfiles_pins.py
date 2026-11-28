"""Pins of the pin's files and `ship.toml` as `pin.py` and the conductor keep them.

Each case reaches the code through a caller that stays, on the side its reading
settles. Why: 0160-pins design D5, The readings, The cases.
"""

import contextlib
import os
import re
import stat
import subprocess
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, NamedTuple

import pytest
import test_conduct
from conduct_load import conduct as _conduct
from fake_worker import _commit, _git
from mflib import kept, layout
from test_conduct import (
    _idle_machine,  # noqa: F401
    _no_codex_sessions,  # noqa: F401
    _offline_retries,
    _sandbox,  # noqa: F401
    _uv_sync,  # noqa: F401
    cut_check,  # noqa: F401
    ps,  # noqa: F401
)
from test_conduct import fake as _fake  # noqa: F401
from test_pin import _into, _keep, _links, _mark, _mf, _pin

_SCRIPT = (
    Path(__file__).resolve().parent.parent / "skills" / "mf-ship" / "scripts" / "pin.py"
)
_SK = " · skipped v0.2.0: not on origin"
_PENDING = " · pending v0.2.0"
_BAD = b"\xff\xfe"
_NOT_A_FILE = "it is not a file"
_NOT_TEXT = "it is not text"
_OVER = "it is over 65536 bytes"
_FILES: dict[str, Callable[[], Path]] = {
    "source": layout.pin_source,
    "pending": layout.pin_pending,
    "hold": layout.pin_hold,
    "checkout": layout.pin_checkout,
}
_DESCRIBE_CHILD = (
    "import runpy, sys\n"
    "try:\n"
    "    said = repr(runpy.run_path(sys.argv[1])['describe']())\n"
    "except OSError as error:\n"
    "    said = str(error)\n"
    "print(said)\n"
)


def _named(name: str, phrase: str) -> str:
    """Return the text of a pin file `name` that cannot be read, for `phrase`."""
    return f"~/.mf-ship-origin/{name} cannot be read: {phrase}"


def _moved(name: str, phrase: str) -> str:
    """Return what `move` says for a pin file `name` that cannot be read."""
    return f"pin: cannot move — {_named(name, phrase)}"


@pytest.fixture
def fake(request: pytest.FixtureRequest) -> Callable[..., Path]:
    """Return the setter of the fake worker's modes, which also moves the home."""
    setter: Callable[..., Path] = request.getfixturevalue("_fake")
    return setter


def _world(tmp_path: Path) -> tuple[dict[str, Any], Path]:
    """Return the pin and an MF checkout tagged `v0.1.0` and `v0.2.0`.

    Its origin holds `v0.1.0` alone, and the origin URL is kept.
    """
    pin = _pin()
    root = _mf(tmp_path, pushed=("v0.1.0",))
    _keep(pin, root, (tmp_path / "origin.git").as_uri())
    return pin, root


def _put(name: str, content: str | bytes) -> Path:
    """Write the pin file `name`, its kept folder made; return its path."""
    path = _FILES[name]()
    path.parent.mkdir(mode=0o700, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content)
    return path


def _text(name: str, root: Path) -> str:
    """Return a good line for the pin file `name`, the checkout `root`."""
    return {
        "source": str(root),
        "pending": "v0.2.0",
        "hold": "v0.1.0",
        "checkout": str(root),
    }[name]


def _plant(name: str, shape: str, root: Path, tmp_path: Path) -> Path:
    """Make the pin file `name` a `shape` of file, a good line its text."""
    path = _FILES[name]()
    path.parent.mkdir(mode=0o700, exist_ok=True)
    text = _text(name, root)
    if shape == "link":
        target = tmp_path / f"target-{name}"
        target.write_text(f"{text}\n")
        path.symlink_to(target)
    elif shape == "dangling":
        path.symlink_to(tmp_path / "nowhere")
    elif shape == "folder":
        path.mkdir()
    elif shape == "empty":
        path.write_text("")
    elif shape == "binary":
        path.write_bytes(_BAD)
    elif shape == "big":
        path.write_text(f"{text}\n{'x' * 70000}")
    else:
        assert shape == "pipe", shape
        os.mkfifo(path)
    return path


def _described(shape: str, name: str, tmp_path: Path) -> str:
    """Return `describe()` with the pin file `name` a `shape`, the world around it."""
    pin, root = _world(tmp_path)
    if name != "source":
        _put("source", str(root))
    _plant(name, shape, root, tmp_path)
    described: str = pin["describe"]()
    return described


class _Broke(NamedTuple):
    """Say `describe` stops on the pin file, naming it with `phrase`."""

    phrase: str


_LINK = _Broke(_NOT_A_FILE)
_ROWS: dict[str, tuple[str | _Broke, ...]] = {
    "link": ("source", _LINK, _LINK, _LINK, _SK),
    "dangling": ("source", _LINK, _LINK, _LINK, _SK),
    "folder": ("source", _LINK, _LINK, _LINK, _SK),
    "empty": ("source", "", _SK, _SK, _SK),
    "big": ("source", _Broke(_OVER), _Broke(_OVER), _Broke(_OVER), _SK),
}
_NAMES = ("source", "pending", "hold", "checkout")


@pytest.mark.parametrize("name", _NAMES)
@pytest.mark.parametrize("shape", sorted(_ROWS))
def test_r_a_shape_at_a_pin_file_reads_as_its_row(
    tmp_path: Path, shape: str, name: str
) -> None:
    expected = _ROWS[shape][1 + _NAMES.index(name)]

    if isinstance(expected, _Broke):
        with pytest.raises(kept.Broken) as broken:
            _described(shape, name, tmp_path)
        assert str(broken.value) == _named(name, expected.phrase)
    else:
        assert _described(shape, name, tmp_path) == expected


@pytest.mark.parametrize("name", ["source", "pending", "hold"])
def test_r_a_bad_byte_in_a_pin_file_stops_describe_naming_it(
    tmp_path: Path, name: str
) -> None:
    with pytest.raises(kept.Broken) as broken:
        _described("binary", name, tmp_path)

    assert str(broken.value) == _named(name, _NOT_TEXT)


def test_r_a_bad_byte_in_checkout_is_not_read_by_describe(tmp_path: Path) -> None:
    assert _described("binary", "checkout", tmp_path) == _SK


@pytest.mark.slow
@pytest.mark.parametrize("name", _NAMES)
def test_r_a_pipe_at_a_pin_file_is_read_at_once(tmp_path: Path, name: str) -> None:
    _, root = _world(tmp_path)
    if name != "source":
        _put("source", str(root))
    _plant(name, "pipe", root, tmp_path)

    done = subprocess.run(
        [sys.executable, "-c", _DESCRIBE_CHILD, str(_SCRIPT)],
        capture_output=True,
        text=True,
        timeout=30,
    )

    expected = repr(_SK) if name == "checkout" else _named(name, _NOT_A_FILE)
    assert (done.returncode, done.stdout, done.stderr) == (0, f"{expected}\n", "")


@pytest.mark.parametrize("name", _NAMES)
def test_r_a_kept_folder_of_mode_0500_still_reads(tmp_path: Path, name: str) -> None:
    pin, root = _world(tmp_path)
    if name != "source":
        _put("source", str(root))
    _put(name, f"{_text(name, root)}\n")
    kept = layout.kept_dir()
    kept.chmod(0o500)
    try:
        described = pin["describe"]()
    finally:
        kept.chmod(0o700)

    assert described == {"pending": _PENDING, "hold": ""}.get(name, _SK)


def test_r_no_kept_folder_describes_nothing() -> None:
    assert _pin()["describe"]() == ""


def test_r_pending_and_hold_are_stripped_and_blank_ones_are_none(
    tmp_path: Path,
) -> None:
    pin, root = _world(tmp_path)
    _put("source", str(root))
    _put("pending", "  v0.2.0 \t\r\n")

    assert pin["describe"]() == _PENDING

    _put("pending", " \n")
    assert pin["describe"]() == _SK
    layout.pin_pending().unlink()
    _put("hold", "   \n")
    assert pin["describe"]() == _SK


def test_r_a_pending_of_several_lines_keeps_every_line(tmp_path: Path) -> None:
    pin, root = _world(tmp_path)
    _put("source", str(root))
    _put("pending", "v0.2.0\nsecond line\n")

    assert pin["describe"]() == f"{_PENDING}\nsecond line"


@pytest.mark.parametrize("name", ["pending", "hold"])
def test_r_a_folder_at_pending_or_hold_stops_describe_naming_it(
    tmp_path: Path, name: str
) -> None:
    pin, root = _world(tmp_path)
    _put("source", str(root))
    _FILES[name]().mkdir()

    with pytest.raises(kept.Broken, match=re.escape(_named(name, _NOT_A_FILE))):
        pin["describe"]()


def test_r_a_folder_at_source_stops_describe_naming_it(tmp_path: Path) -> None:
    pin, _ = _world(tmp_path)
    layout.pin_source().parent.mkdir(exist_ok=True)
    layout.pin_source().mkdir()

    with pytest.raises(kept.Broken, match=re.escape(_named("source", _NOT_A_FILE))):
        pin["describe"]()


def test_r_empty_pending_and_hold_leave_the_skipped_note(tmp_path: Path) -> None:
    pin, root = _world(tmp_path)
    _put("source", str(root))
    _put("pending", "")
    _put("hold", "")

    assert pin["describe"]() == _SK
    _put("source", "")
    assert pin["describe"]() == ""


@pytest.mark.parametrize("text", ["", "  \n"])
def test_r_an_empty_source_moves_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_home: Path, text: str
) -> None:
    pin = _pin()
    root = _mf(tmp_path)
    _keep(pin, root, (tmp_path / "origin.git").as_uri())
    _put("source", text)
    monkeypatch.chdir(root)

    assert pin["move"]() is None
    assert _links(isolated_home) == {}


def test_r_no_source_moves_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_home: Path
) -> None:
    pin = _pin()
    root = _mf(tmp_path)
    _keep(pin, root, (tmp_path / "origin.git").as_uri())
    monkeypatch.chdir(root)

    assert pin["move"]() is None
    assert _links(isolated_home) == {}


def _tree(tmp_path: Path, home: Path, tag: str, host: str, version: bool) -> Path:
    """Link `mf-build` on `host` into a tree named `tag`; return the tree's root."""
    root = home / ".local/share/minionsfactory" / tag
    skill = root / "skills" / "mf-build"
    skill.mkdir(parents=True, exist_ok=True)
    if version:
        (root / "VERSION").write_text(f"{tag}\n")
    link = home / host / "mf-build"
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(skill)
    return root


def test_r_links_into_two_trees_describe_no_release(
    tmp_path: Path, isolated_home: Path
) -> None:
    pin = _pin()
    _tree(tmp_path, isolated_home, "v0.1.0", ".claude/skills", True)

    assert pin["describe"]() == " · mf v0.1.0"
    _tree(tmp_path, isolated_home, "v0.2.0", ".agents/skills", True)
    assert pin["describe"]() == ""


@pytest.mark.parametrize("version", ["missing", "folder"])
def test_r_a_tree_that_is_no_repo_reads_live_unknown(
    tmp_path: Path, isolated_home: Path, version: str
) -> None:
    pin = _pin()
    root = _tree(tmp_path, isolated_home, "v0.3.0", ".claude/skills", False)
    if version == "folder":
        (root / "VERSION").mkdir()

    assert pin["describe"]() == " · mf live unknown"


def test_r_a_tree_that_is_a_repo_reads_live_by_its_hash_or_its_tag(
    tmp_path: Path, isolated_home: Path
) -> None:
    pin = _pin()
    root = _tree(tmp_path, isolated_home, "v0.3.0", ".claude/skills", False)
    _git(root, "init", "-q", "-b", "main")
    _commit(root, {"skills/mf-build/SKILL.md": "build\n"}, "one")

    short = _git(root, "rev-parse", "--short", "HEAD")
    assert pin["describe"]() == f" · mf live {short}"
    _git(root, "tag", "v7.7.7")
    assert pin["describe"]() == " · mf live v7.7.7"


def test_r_describe_follows_source_pending_and_hold(tmp_path: Path) -> None:
    pin, root = _world(tmp_path)
    _put("source", str(root))

    assert pin["describe"]() == _SK
    _put("hold", "v0.1.0\n")
    assert pin["describe"]() == ""
    layout.pin_hold().unlink()
    _put("pending", "v0.2.0\n")
    assert pin["describe"]() == _PENDING
    _put("hold", "v0.1.0\n")
    assert pin["describe"]() == _PENDING


def test_r_a_linked_release_is_not_skipped(tmp_path: Path, isolated_home: Path) -> None:
    pin, root = _world(tmp_path)
    _tree(tmp_path, isolated_home, "v0.2.0", ".claude/skills", True)
    _put("source", str(root))

    assert pin["describe"]() == " · mf v0.2.0"


def test_r_a_source_that_is_no_repo_or_is_missing_describes_nothing(
    tmp_path: Path,
) -> None:
    pin = _pin()
    folder = tmp_path / "plain"
    folder.mkdir()
    _put("source", str(folder))

    assert pin["describe"]() == ""
    _put("source", str(tmp_path / "gone"))
    assert pin["describe"]() == ""


def _halts(lines: list[str]) -> list[str]:
    """Return the run's halt lines among the run log's `lines`."""
    return [line for line in lines if line.startswith("run · halt — ")]


@pytest.mark.slow
@pytest.mark.parametrize(
    ("name", "code"), [("source", 2), ("pending", 2), ("checkout", 0)]
)
def test_r_a_run_logs_a_bad_byte_in_a_pin_file_as_its_halt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake: Callable[..., Path],
    name: str,
    code: int,
) -> None:
    fake()
    conduct = test_conduct._conduct()
    root, _, run = _offline_retries(tmp_path, conduct, monkeypatch)
    if name != "source":
        _put("source", str(root))
    _put(name, _BAD)

    halts = _halts(run(code))

    if name == "checkout":
        assert not halts
        return
    assert halts == [
        f"run · halt — conduct.py failed: {_named(name, _NOT_TEXT)} · cause run"
    ]


@pytest.mark.slow
def test_r_a_bad_byte_at_hold_halts_run_and_takes_the_live_mark(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., Path]
) -> None:
    fake()
    conduct = test_conduct._conduct()
    root, _, run = _offline_retries(tmp_path, conduct, monkeypatch)
    _put("source", str(root))
    _put("hold", _BAD)
    layout.released_dir(root).mkdir(parents=True)
    (layout.released_dir(root) / "0001-a").write_text("abc\n")

    lines = run(2)

    halts = _halts(lines)
    assert halts == [
        f"run · halt — conduct.py failed: {_named('hold', _NOT_TEXT)} · cause run"
    ]
    said = "run · ledger — 0001-a is no commit id: skipped"
    assert said in lines
    assert lines.index(said) < lines.index(halts[0])
    assert not layout.live_mark(root).exists()
    assert _raw()["hold"] == _BAD


@contextlib.contextmanager
def _umask(mask: int) -> Iterator[None]:
    """Hold the process's umask at `mask`."""
    before = os.umask(mask)
    try:
        yield
    finally:
        os.umask(before)


def _modes(path: Path) -> int:
    """Return the permission bits of `path`."""
    return stat.S_IMODE(path.stat().st_mode)


def _state() -> dict[str, str]:
    """Return the text of each pin file that reads as a file."""
    return {
        name: where().read_text() for name, where in _FILES.items() if where().is_file()
    }


def _raw() -> dict[str, bytes]:
    """Return the bytes of each pin file that reads as a file."""
    return {
        name: where().read_bytes()
        for name, where in _FILES.items()
        if where().is_file()
    }


def _said(pin: dict[str, Any], capsys: pytest.CaptureFixture[str], *args: str) -> str:
    """Return what `pin.py` prints for `args`, after it exits 2."""
    capsys.readouterr()
    assert pin["main"](list(args)) == 2
    return capsys.readouterr().out.strip()


@contextlib.contextmanager
def _hold_k(mode: int) -> Iterator[Path]:
    """Yield the kept folder, made empty at `mode`, and restore its mode after."""
    kept = layout.kept_dir()
    kept.mkdir(mode=0o700)
    kept.chmod(mode)
    try:
        yield kept
    finally:
        kept.chmod(0o700)


def test_wi_a_first_install_makes_the_folder_0700_and_files_0600(
    tmp_path: Path, isolated_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pin = _pin()
    mf = _mf(tmp_path)
    for umask, mode, home in (
        (0o022, 0o600, isolated_home),
        (0o077, 0o600, tmp_path / "second-home"),
    ):
        home.mkdir(exist_ok=True)
        monkeypatch.setenv("HOME", str(home))
        with _umask(umask):
            assert pin["install"](mf, "live") == "pin: linked live"
            _mark(home, "mark", os.getpid())
            assert pin["install"](mf, "live") == "pin: pending live — a run is live"

        kept = layout.kept_dir()
        assert _modes(kept) == 0o700
        assert _state() == {
            "source": f"{mf}\n",
            "pending": "live\n",
            "hold": "live\n",
            "checkout": f"{mf}\n",
        }
        assert {_modes(where()) for where in _FILES.values()} == {mode}


def test_wi_a_home_that_does_not_stand_is_made(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pin = _pin()
    mf = _mf(tmp_path)
    home = tmp_path / "no" / "such" / "home"
    monkeypatch.setenv("HOME", str(home))

    assert pin["install"](mf, "v0.1.0") == "pin: linked v0.1.0"

    assert _modes(home / ".mf-ship-origin") == 0o700
    assert (home / ".mf-ship-origin" / "source").read_text() == f"{mf}\n"


def test_wi_a_worktree_installs_its_primary_as_source(
    tmp_path: Path, isolated_home: Path
) -> None:
    pin = _pin()
    mf = _mf(tmp_path)
    worktree = tmp_path / "worktree"
    _git(mf, "worktree", "add", "-q", str(worktree))

    assert pin["install"](worktree, "live") == "pin: linked live"

    assert _state()["source"] == f"{mf}\n"
    assert _state()["checkout"] == f"{worktree.resolve()}\n"
    assert _links(isolated_home) == _into(
        isolated_home, worktree.resolve() / "skills", ("build", "ship")
    )


def test_wi_a_link_to_the_checkout_installs_the_checkout(tmp_path: Path) -> None:
    pin = _pin()
    mf = _mf(tmp_path)
    link = tmp_path / "link"
    link.symlink_to(mf)
    both = {"source": f"{mf}\n", "checkout": f"{mf}\n"}

    for cwd in (link, mf / "skills"):
        assert pin["install"](cwd, "live") == "pin: linked live"
        assert {name: _state()[name] for name in both} == both

    def out(cwd: Path, *args: str) -> str:
        if "--show-toplevel" in args:
            return str(link)
        assert "--git-common-dir" in args
        return str(link / ".git")

    pin["install"].__globals__["_out"] = out
    assert pin["install"](mf, "live") == "pin: linked live"
    assert {name: _state()[name] for name in both} == both


@pytest.mark.slow
def test_wi_a_tag_origin_lost_locally_is_linked_with_no_note(
    tmp_path: Path,
) -> None:
    pin = _pin()
    mf = _mf(tmp_path, pushed=("v0.1.0",))
    _keep(pin, mf, (tmp_path / "origin.git").as_uri())
    _git(mf, "tag", "-a", "-m", "v0.3.0", "v0.3.0")
    _git(mf, "push", "-q", "origin", "v0.3.0")
    _git(mf, "tag", "-d", "v0.3.0")

    assert pin["install"](mf, None) == "pin: linked v0.3.0"


@pytest.mark.parametrize("release", ["next", "vnext", "v1.2", "v0.1.0-rc1", "LIVE"])
def test_wi_a_release_that_is_no_tag_is_refused_after_source_is_written(
    tmp_path: Path, release: str
) -> None:
    pin = _pin()
    mf = _mf(tmp_path)
    _put("pending", "v0.1.0\n")
    _put("hold", "v0.1.0\n")

    with pytest.raises(pin["Refused"]) as refused:
        pin["install"](mf, release)

    assert str(refused.value) == f"{release} is not a version tag or live"
    assert _state() == {
        "source": f"{mf}\n",
        "pending": "v0.1.0\n",
        "hold": "v0.1.0\n",
    }


def test_wi_a_bare_install_with_no_kept_origin_is_refused(tmp_path: Path) -> None:
    pin = _pin()
    mf = _mf(tmp_path)
    _put("hold", "v0.1.0\n")

    with pytest.raises(pin["Refused"], match="no run kept origin"):
        pin["install"](mf, None)

    assert _state() == {"hold": "v0.1.0\n", "source": f"{mf}\n"}


@pytest.mark.slow
def test_wi_a_bare_install_that_cannot_clone_leaves_the_hold(tmp_path: Path) -> None:
    pin = _pin()
    mf = _mf(tmp_path)
    _keep(pin, mf, (tmp_path / "origin.git").as_uri())
    _put("hold", "v0.1.0\n")
    remote = pin["_fetch"].__globals__["_remote"]

    def refusing(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        if args[0] == "clone":
            return subprocess.CompletedProcess(args, 128, "", "fatal: refused\n")
        done: subprocess.CompletedProcess[str] = remote(cwd, *args)
        return done

    pin["_fetch"].__globals__["_remote"] = refusing

    with pytest.raises(pin["Refused"]) as refused:
        pin["install"](mf, None)

    assert str(refused.value) == "cannot clone v0.2.0 from origin: fatal: refused"
    assert _state()["hold"] == "v0.1.0\n"


def test_wi_a_non_link_refuses_the_install_and_leaves_pending_and_hold(
    tmp_path: Path, isolated_home: Path
) -> None:
    pin = _pin()
    mf = _mf(tmp_path)
    real = isolated_home / ".agents/skills/mf-ship"
    real.mkdir(parents=True)
    _put("pending", "v0.9.0\n")

    with pytest.raises(pin["Refused"], match="exists and is not a link"):
        pin["install"](mf, "v0.1.0")

    assert _state() == {
        "source": f"{mf}\n",
        "pending": "v0.9.0\n",
        "hold": "v0.1.0\n",
    }
    assert _links(isolated_home) == {}


def test_wi_a_clean_install_clears_pending(tmp_path: Path) -> None:
    pin = _pin()
    mf = _mf(tmp_path)
    _put("pending", "v0.9.0\n")

    assert pin["install"](mf, "v0.1.0") == "pin: linked v0.1.0"

    assert "pending" not in _state()


def test_wi_a_second_install_replaces_source_whole_and_leaves_no_staged_file(
    tmp_path: Path,
) -> None:
    pin = _pin()
    mf = _mf(tmp_path)
    _put("source", f"{mf}/a/much/longer/path/than/the/checkout\n")

    pin["install"](mf, "v0.1.0")
    pin["install"](mf, "v0.1.0")

    assert _state()["source"] == f"{mf}\n"
    assert sorted(entry.name for entry in layout.kept_dir().iterdir()) == [
        "hold",
        "source",
    ]


def test_wi_a_folder_at_source_stops_install_and_exports_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    pin = _pin()
    mf = _mf(tmp_path)
    monkeypatch.chdir(mf)
    kept = layout.kept_dir()
    kept.mkdir(mode=0o700)
    layout.pin_source().mkdir()

    assert _said(pin, capsys, "install", "v0.1.0") == (
        f"pin: cannot install — [Errno 21] Is a directory: '{kept}/source'"
    )

    assert [entry.name for entry in kept.iterdir()] == ["source"]
    assert not (layout.data_dir() / "v0.1.0").exists()


def test_wi_a_kept_folder_of_mode_0500_stops_install(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    pin = _pin()
    mf = _mf(tmp_path)
    monkeypatch.chdir(mf)

    with _hold_k(0o500) as kept:
        assert _said(pin, capsys, "install", "v0.1.0") == (
            f"pin: cannot install — [Errno 13] Permission denied: '{kept}/source'"
        )
        assert list(kept.iterdir()) == []


def test_wi_a_file_at_the_kept_folder_stops_install(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    pin = _pin()
    mf = _mf(tmp_path)
    monkeypatch.chdir(mf)
    kept = layout.kept_dir()
    kept.write_text("mine\n")

    assert _said(pin, capsys, "install", "v0.1.0") == (
        "pin: cannot install — [Errno 17] File exists"
    )

    assert kept.read_text() == "mine\n"


def _folder_at(name: str) -> Path:
    """Make a folder at the pin file `name`, its kept folder made; return it."""
    path = _FILES[name]()
    path.parent.mkdir(mode=0o700, exist_ok=True)
    path.mkdir()
    return path


def test_wi_a_folder_at_hold_stops_a_tag_install_after_the_export(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    isolated_home: Path,
) -> None:
    pin = _pin()
    mf = _mf(tmp_path)
    monkeypatch.chdir(mf)
    hold = _folder_at("hold")
    _put("pending", "v0.9.0\n")

    assert _said(pin, capsys, "install", "v0.1.0") == (
        f"pin: cannot install — [Errno 21] Is a directory: '{hold}'"
    )

    assert _state() == {"source": f"{mf}\n", "pending": "v0.9.0\n"}
    assert (layout.data_dir() / "v0.1.0" / "VERSION").is_file()
    assert _links(isolated_home) == {}


def test_wi_a_folder_at_checkout_stops_a_live_install(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    isolated_home: Path,
) -> None:
    pin = _pin()
    mf = _mf(tmp_path)
    monkeypatch.chdir(mf)
    checkout = _folder_at("checkout")

    assert _said(pin, capsys, "install", "live") == (
        f"pin: cannot install — [Errno 21] Is a directory: '{checkout}'"
    )

    assert _state() == {"hold": "live\n", "source": f"{mf}\n"}
    assert _links(isolated_home) == {}


def test_wi_a_folder_at_pending_stops_an_install_under_a_live_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    isolated_home: Path,
) -> None:
    pin = _pin()
    mf = _mf(tmp_path)
    monkeypatch.chdir(mf)
    pending = _folder_at("pending")
    _mark(isolated_home, "mark", os.getpid())

    assert _said(pin, capsys, "install", "v0.1.0") == (
        f"pin: cannot install — [Errno 21] Is a directory: '{pending}'"
    )

    assert _state() == {"hold": "v0.1.0\n", "source": f"{mf}\n"}
    assert _links(isolated_home) == {}


def test_wi_a_folder_at_pending_stops_the_clearing_after_the_links(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    isolated_home: Path,
) -> None:
    pin = _pin()
    mf = _mf(tmp_path)
    monkeypatch.chdir(mf)
    pending = _folder_at("pending")

    said = _said(pin, capsys, "install", "v0.1.0")

    assert re.fullmatch(r"pin: cannot install — \[Errno (1|21)\] .*: 'pending'", said)
    assert pending.is_dir()
    assert _state() == {"hold": "v0.1.0\n", "source": f"{mf}\n"}
    assert _links(isolated_home)


@pytest.mark.slow
def test_wi_a_folder_at_hold_stops_a_bare_install_after_the_export(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    isolated_home: Path,
) -> None:
    pin, mf = _world(tmp_path)
    _git(mf, "push", "-q", "origin", "v0.2.0")
    monkeypatch.chdir(mf)
    hold = _folder_at("hold")

    said = _said(pin, capsys, "install")

    assert re.fullmatch(r"pin: cannot install — \[Errno (1|21)\] .*: 'hold'", said)
    assert hold.is_dir()
    assert (layout.data_dir() / "v0.2.0" / "VERSION").is_file()
    assert _links(isolated_home) == {}
    assert _state() == {"source": f"{mf}\n"}


_TARGETS = {
    "source": ("v0.1.0", None),
    "hold": ("v0.1.0", None),
    "checkout": ("live", None),
    "pending": ("v0.1.0", "mark"),
}


@pytest.mark.parametrize("kind", ["file", "dangling"])
@pytest.mark.parametrize("name", _NAMES)
def test_wi_a_write_replaces_a_link_at_a_pin_file_and_leaves_its_target(
    tmp_path: Path, isolated_home: Path, name: str, kind: str
) -> None:
    pin = _pin()
    mf = _mf(tmp_path)
    release, mark = _TARGETS[name]
    path = _FILES[name]()
    path.parent.mkdir(mode=0o700)
    target = tmp_path / "target"
    if kind == "file":
        target.write_text("orig\n")
    path.symlink_to(target)
    if mark:
        _mark(isolated_home, mark, os.getpid())

    pin["install"](mf, release)

    assert not path.is_symlink()
    assert path.read_text() == (
        {"source": f"{mf}\n", "checkout": f"{mf}\n"}.get(name, f"{release}\n")
    )
    if kind == "file":
        assert target.read_text() == "orig\n"
    else:
        assert not target.exists()


@pytest.mark.slow
@pytest.mark.parametrize("name", ["pending", "hold"])
def test_wi_the_removal_of_a_link_at_pending_or_hold_takes_the_link(
    tmp_path: Path, name: str
) -> None:
    pin, mf = _world(tmp_path)
    _git(mf, "push", "-q", "origin", "v0.2.0")
    path = _FILES[name]()
    path.parent.mkdir(mode=0o700, exist_ok=True)
    target = tmp_path / "target"
    target.write_text("orig\n")
    path.symlink_to(target)

    pin["install"](mf, "v0.1.0" if name == "pending" else None)

    assert not path.is_symlink()
    assert target.read_text() == "orig\n"


def test_wi_a_pipe_at_pending_is_removed_and_a_dangling_hold_is_replaced(
    tmp_path: Path,
) -> None:
    pin = _pin()
    mf = _mf(tmp_path)
    layout.kept_dir().mkdir(mode=0o700)
    os.mkfifo(layout.pin_pending())
    target = tmp_path / "target"
    layout.pin_hold().symlink_to(target)

    assert pin["install"](mf, "v0.1.0") == "pin: linked v0.1.0"

    assert not os.path.lexists(layout.pin_pending())
    assert not layout.pin_hold().is_symlink()
    assert layout.pin_hold().read_text() == "v0.1.0\n"
    assert not target.exists()


@pytest.mark.slow
@pytest.mark.parametrize("name", _NAMES)
def test_wi_a_pipe_with_no_reader_is_replaced_by_an_install(
    tmp_path: Path, isolated_home: Path, name: str
) -> None:
    mf = _mf(tmp_path)
    release, mark = _TARGETS[name]
    path = _FILES[name]()
    path.parent.mkdir(mode=0o700)
    os.mkfifo(path)
    if mark:
        _mark(isolated_home, mark, os.getpid())

    done = subprocess.run(
        [sys.executable, str(_SCRIPT), "install", release],
        cwd=mf,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert done.returncode == 0, done.stdout
    assert stat.S_ISREG(path.lstat().st_mode)


_MOVE_CHILD = "import runpy, sys\nprint(repr(runpy.run_path(sys.argv[1])['move']()))\n"


def _moving(
    tmp_path: Path, release: str | None = "v0.1.0"
) -> tuple[dict[str, Any], Path]:
    """Return the pin and an MF checkout named by `source`, `release` exported."""
    pin = _pin()
    mf = _mf(tmp_path)
    _put("source", str(mf))
    if release:
        pin["_export"](mf, release)
    return pin, mf


@pytest.mark.slow
def test_wm_a_live_run_other_than_mine_holds_the_move_before_any_fetch(
    tmp_path: Path, isolated_home: Path
) -> None:
    pin = _pin()
    mf = _mf(tmp_path, pushed=("v0.1.0",))
    _keep(pin, mf, (tmp_path / "origin.git").as_uri())
    pin["install"](mf, None)
    _git(mf, "push", "-q", "origin", "v0.2.0")
    _mark(isolated_home, "other", os.getpid())

    assert pin["move"]() is None
    pin["move"].__globals__["_fetch"] = _refusing_fetch(pin)

    assert pin["move"]() is None
    data = layout.data_dir()
    assert not (data / "v0.2.0").exists()
    assert not list(data.glob(".v0.2.0-*"))


def _refusing_fetch(pin: dict[str, Any]) -> Callable[[str, str], Path]:
    def fetch(url: str, tag: str) -> Path:
        raise pin["Refused"]("fetched")

    return fetch


def test_wm_pending_live_without_a_checkout_file_links_the_source(
    tmp_path: Path, isolated_home: Path
) -> None:
    pin, mf = _moving(tmp_path, None)
    _put("pending", "live\n")

    assert pin["move"]() == "pin: moved to live"

    assert _links(isolated_home) == _into(
        isolated_home, mf / "skills", ("build", "ship")
    )


@pytest.mark.parametrize("pending", ["", "\n", "  \n"])
def test_wm_a_blank_pending_moves_nothing_and_stays(
    tmp_path: Path, isolated_home: Path, pending: str
) -> None:
    pin, _ = _moving(tmp_path, None)
    _put("pending", pending)

    assert pin["move"]() is None

    assert _state()["pending"] == pending
    assert _links(isolated_home) == {}


def test_wm_a_pending_release_with_no_tree_is_refused_and_stays(
    tmp_path: Path, isolated_home: Path
) -> None:
    pin = _pin()
    mf = _mf(tmp_path)
    pin["install"](mf, "v0.1.0")
    held = _links(isolated_home)
    _put("pending", "v0.0.0\n")

    assert pin["move"]() == (
        f"pin: cannot move — {layout.data_dir()}/v0.0.0/skills holds no mf-* skill"
    )

    assert _links(isolated_home) == held
    assert _state()["pending"] == "v0.0.0\n"


def test_wm_a_non_link_stops_the_move_and_leaves_pending_and_source(
    tmp_path: Path, isolated_home: Path
) -> None:
    pin, mf = _moving(tmp_path)
    (isolated_home / ".agents/skills/mf-ship").mkdir(parents=True)
    _put("pending", "v0.1.0\n")

    assert pin["move"]() == (
        "pin: cannot move — ~/.agents/skills/mf-ship exists and is not a link"
    )

    assert _state() == {"source": str(mf), "pending": "v0.1.0\n"}


def test_wm_a_live_install_then_a_tag_then_a_pending_tag_moves_to_it(
    tmp_path: Path,
) -> None:
    pin = _pin()
    mf = _mf(tmp_path)
    pin["install"](mf, "live")
    pin["install"](mf, "v0.1.0")
    pin["_export"](mf, "v0.2.0")
    _put("pending", "v0.2.0\n")

    assert pin["move"]() == "pin: moved to v0.2.0"

    assert _state() == {
        "source": f"{mf}\n",
        "hold": "v0.1.0\n",
        "checkout": f"{mf}\n",
    }


def test_wm_a_skills_folder_of_mode_0500_is_named_and_pending_stays(
    tmp_path: Path, isolated_home: Path
) -> None:
    pin, _ = _moving(tmp_path)
    _put("pending", "v0.1.0\n")
    skills = isolated_home / ".claude/skills"
    skills.mkdir(parents=True)
    skills.chmod(0o500)
    try:
        said = pin["move"]()
    finally:
        skills.chmod(0o700)

    assert said.startswith("pin: cannot move — [Errno 13] Permission denied: ")
    assert _state()["pending"] == "v0.1.0\n"


@pytest.mark.parametrize("shape", ["link", "empty"])
def test_wm_source_a_link_is_named_and_an_empty_file_moves_nothing(
    tmp_path: Path, isolated_home: Path, shape: str
) -> None:
    pin, mf = _moving(tmp_path)
    layout.pin_source().unlink()
    _put("pending", "v0.1.0\n")
    _plant("source", shape, mf, tmp_path)

    said = pin["move"]()

    assert said == (_moved("source", _NOT_A_FILE) if shape == "link" else None)
    assert layout.pin_source().is_symlink() is (shape == "link")
    assert _links(isolated_home) == {}


@pytest.mark.parametrize("shape", ["dangling", "folder"])
def test_wm_source_a_dangling_link_or_a_folder_is_named_and_moves_nothing(
    tmp_path: Path, shape: str
) -> None:
    pin, mf = _moving(tmp_path)
    layout.pin_source().unlink()
    _put("pending", "v0.1.0\n")
    _plant("source", shape, mf, tmp_path)

    assert pin["move"]() == _moved("source", _NOT_A_FILE)

    assert _state()["pending"] == "v0.1.0\n"


@pytest.mark.parametrize("name", ["source", "pending", "checkout"])
def test_wm_a_bad_byte_is_named_and_moves_nothing(
    tmp_path: Path, isolated_home: Path, name: str
) -> None:
    pin, _ = _moving(tmp_path)
    _put("pending", "live\n" if name == "checkout" else "v0.1.0\n")
    _put(name, _BAD)
    before = _raw()

    assert pin["move"]() == _moved(name, _NOT_TEXT)

    assert _links(isolated_home) == {}
    assert _raw() == before


def test_wm_a_bad_byte_at_hold_is_named(tmp_path: Path) -> None:
    pin = _pin()
    mf = _mf(tmp_path)
    _keep(pin, mf, (tmp_path / "origin.git").as_uri())
    _put("source", str(mf))
    _put("hold", _BAD)

    assert pin["move"]() == _moved("hold", _NOT_TEXT)


def test_wm_pending_a_link_is_named_and_the_link_stays(
    tmp_path: Path, isolated_home: Path
) -> None:
    pin, _ = _moving(tmp_path)
    target = tmp_path / "target"
    target.write_text("v0.1.0\n")
    layout.pin_pending().symlink_to(target)

    assert pin["move"]() == _moved("pending", _NOT_A_FILE)

    assert layout.pin_pending().is_symlink()
    assert target.read_text() == "v0.1.0\n"
    assert _links(isolated_home) == {}


@pytest.mark.parametrize("shape", ["dangling", "folder"])
def test_wm_pending_a_dangling_link_or_a_folder_stays_and_is_named(
    tmp_path: Path, shape: str
) -> None:
    pin, mf = _moving(tmp_path)
    _plant("pending", shape, mf, tmp_path)

    assert pin["move"]() == _moved("pending", _NOT_A_FILE)

    assert os.path.lexists(layout.pin_pending())


@pytest.mark.parametrize("name", ["pending", "checkout"])
def test_wm_a_pending_or_checkout_of_70000_x_is_over_the_bound(
    tmp_path: Path, name: str
) -> None:
    pin, _ = _moving(tmp_path)
    pending = "x" * 70000 if name == "pending" else "live\n"
    _put("pending", pending)
    if name == "checkout":
        _put("checkout", "x" * 70000)

    assert pin["move"]() == _moved(name, _OVER)

    assert _state()["pending"] == pending


def test_wm_a_source_of_70000_x_is_over_the_bound(
    tmp_path: Path, isolated_home: Path
) -> None:
    pin, _ = _moving(tmp_path)
    _put("source", "x" * 70000)
    _put("pending", "v0.1.0\n")

    assert pin["move"]() == _moved("source", _OVER)

    assert _links(isolated_home) == {}


@pytest.mark.slow
@pytest.mark.parametrize("name", ["source", "pending", "checkout"])
def test_wm_a_pipe_at_a_file_move_reads_does_not_block(
    tmp_path: Path, name: str
) -> None:
    _moving(tmp_path, None)
    _put("pending", "live\n")
    if name != "checkout":
        _FILES[name]().unlink()
    os.mkfifo(_FILES[name]())

    done = subprocess.run(
        [sys.executable, "-c", _MOVE_CHILD, str(_SCRIPT)],
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert (done.returncode, done.stdout) == (0, f"{_moved(name, _NOT_A_FILE)!r}\n")
    assert os.path.lexists(layout.pin_pending())


_HOLDS = {
    "link": _NOT_A_FILE,
    "big": _OVER,
    "dangling": _NOT_A_FILE,
    "folder": _NOT_A_FILE,
    "pipe": _NOT_A_FILE,
}


@pytest.mark.slow
@pytest.mark.parametrize("shape", sorted(_HOLDS))
def test_wm_hold_of_any_shape_but_a_file_is_named_and_moves_nothing(
    tmp_path: Path, shape: str
) -> None:
    pin = _pin()
    mf = _mf(tmp_path)
    _keep(pin, mf, (tmp_path / "origin.git").as_uri())
    _put("source", str(mf))
    _plant("hold", shape, mf, tmp_path)
    if shape == "pipe":
        done = subprocess.run(
            [sys.executable, "-c", _MOVE_CHILD, str(_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        said = done.stdout.strip()
    else:
        said = repr(pin["move"]())

    assert said == repr(_moved("hold", _HOLDS[shape]))
    assert not (layout.data_dir() / "v0.2.0").exists()


def test_wb_source_broken_is_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_home: Path
) -> None:
    pin, _ = _moving(tmp_path)
    _put("pending", "v0.1.0\n")
    pinned = pin["mflib"].kept

    def broken() -> str | None:
        raise pinned.Broken(layout.pin_source(), "it is not text")

    monkeypatch.setattr(pinned, "source", broken)

    assert pin["move"]() == (
        "pin: cannot move — ~/.mf-ship-origin/source cannot be read: it is not text"
    )
    assert _links(isolated_home) == {}


_CAP_CHILD = (
    "import runpy, sys\n"
    "conduct = runpy.run_path(sys.argv[1])\n"
    "try:\n"
    "    said = repr(conduct['_cap']())\n"
    "except conduct['Stop'] as stop:\n"
    "    said = f'{stop.code} {stop}'\n"
    "print(said)\n"
)
_DEEP = "it is nested too deep"
_CONDUCT_SCRIPT = _SCRIPT.with_name("conduct.py")
_NESTED = {
    "arrays": ("a = " + "[" * 1000 + "]" * 1000 + "\n"),
    "tables": ("a = " + "{b = " * 400 + "1" + "}" * 400 + "\n"),
}
_CALLS = ("_ship_file", "_cap", "_pushes_tags")


def _toml(content: str | bytes) -> Path:
    """Write `ship.toml` in the config folder, made; return its path."""
    path = layout.ship_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content)
    return path


def _stopped_by(conduct: dict[str, Any], call: Callable[[], object], text: str) -> None:
    """Assert `call` stops with code 2 and exactly `text`."""
    with pytest.raises(conduct["Stop"]) as stopped:
        call()
    assert (stopped.value.code, str(stopped.value)) == (2, text)


def _stopped(conduct: dict[str, Any], call: str, text: str) -> None:
    """Assert the conductor's `call` stops with code 2 and exactly `text`."""
    _stopped_by(conduct, conduct[call], text)


def test_s_no_file_reads_as_empty_data_at_its_spelled_path() -> None:
    conduct = _conduct()
    path = layout.ship_file()

    assert conduct["_ship_file"]() == (path, {})
    _toml("")
    assert conduct["_ship_file"]() == (path, {})
    _toml("[queue]\nin_flight = 2\n")
    assert conduct["_ship_file"]() == (path, {"queue": {"in_flight": 2}})


def test_s_no_file_no_folder_or_an_empty_file_sets_nothing() -> None:
    conduct = _conduct()

    assert (conduct["_cap"](), conduct["_pushes_tags"]()) == (None, True)
    _toml("")
    assert (conduct["_cap"](), conduct["_pushes_tags"]()) == (None, True)


def test_s_the_whole_dict_is_returned_and_each_table_is_read() -> None:
    conduct = _conduct()
    path = _toml("[other]\nx = 1\n[queue]\nin_flight = 2\n[push]\ntags = false\n")

    assert conduct["_ship_file"]() == (
        path,
        {"other": {"x": 1}, "queue": {"in_flight": 2}, "push": {"tags": False}},
    )
    assert (conduct["_cap"](), conduct["_pushes_tags"]()) == (2, False)
    path = _toml("queue = 3\n[push]\ntags = false\n")
    assert conduct["_ship_file"]() == (path, {"queue": 3, "push": {"tags": False}})
    assert (conduct["_cap"](), conduct["_pushes_tags"]()) == (None, False)


@pytest.mark.parametrize("call", _CALLS)
def test_s_a_file_at_the_config_folder_stops_with_the_modules_phrase(
    call: str,
) -> None:
    conduct = _conduct()
    folder = layout.config_dir()
    folder.parent.mkdir(parents=True)
    folder.write_text("mine\n")

    _stopped(conduct, call, f"{layout.ship_file()}: Not a directory")


@pytest.mark.parametrize("content", [b"[queue]\nin_flight = 2\n# \xe9\n", b"\xff\xfe"])
@pytest.mark.parametrize("call", ["_cap", "_pushes_tags"])
def test_s_a_bad_byte_stops_as_no_text(call: str, content: bytes) -> None:
    conduct = _conduct()
    path = _toml(content)

    _stopped(conduct, call, f"{path}: {_NOT_TEXT}")


@pytest.mark.parametrize("call", _CALLS)
def test_s_a_link_to_a_valid_file_stops(call: str, tmp_path: Path) -> None:
    conduct = _conduct()
    target = tmp_path / "target.toml"
    target.write_text("[queue]\nin_flight = 2\n[push]\ntags = false\n")
    path = layout.ship_file()
    path.parent.mkdir(parents=True)
    path.symlink_to(target)

    _stopped(conduct, call, f"{path}: {_NOT_A_FILE}")


@pytest.mark.parametrize("call", _CALLS)
def test_s_a_dangling_link_stops(call: str, tmp_path: Path) -> None:
    conduct = _conduct()
    path = layout.ship_file()
    path.parent.mkdir(parents=True)
    path.symlink_to(tmp_path / "nowhere")

    _stopped(conduct, call, f"{path}: {_NOT_A_FILE}")


@pytest.mark.parametrize("call", _CALLS)
def test_s_a_folder_stops_as_no_file(call: str) -> None:
    conduct = _conduct()
    path = layout.ship_file()
    path.mkdir(parents=True)

    _stopped(conduct, call, f"{path}: {_NOT_A_FILE}")


def test_s_a_file_over_the_bound_stops() -> None:
    conduct = _conduct()
    path = _toml("[queue]\nin_flight = 2\n# " + "x" * 70000 + "\n")

    _stopped(conduct, "_cap", f"{path}: {_OVER}")


@pytest.mark.parametrize(
    ("content", "words"),
    [
        (
            "[queue",
            "Expected ']' at the end of a table declaration (at end of document)",
        ),
        (
            "[queue]\nin_flight = 2\nin_flight = 3\n",
            "Cannot overwrite a value (at line 3, column 14)",
        ),
        ("﻿[queue]\nin_flight = 2\n", "Invalid statement (at line 1, column 1)"),
    ],
)
def test_s_a_toml_error_stops_with_the_parsers_words(content: str, words: str) -> None:
    conduct = _conduct()
    path = _toml(content.encode())

    _stopped(conduct, "_cap", f"{path}: {words}")


def test_s_a_file_with_crlf_lines_reads() -> None:
    conduct = _conduct()
    _toml(b"[queue]\r\nin_flight = 2\r\n[push]\r\ntags = false\r\n")

    assert (conduct["_cap"](), conduct["_pushes_tags"]()) == (2, False)


@pytest.mark.parametrize("call", _CALLS)
@pytest.mark.parametrize("shape", sorted(_NESTED))
def test_s_a_deeply_nested_file_stops_naming_it(call: str, shape: str) -> None:
    conduct = _conduct()
    path = _toml(_NESTED[shape])

    _stopped(conduct, call, f"{path}: {_DEEP}")


def test_s_a_file_nested_a_hundred_deep_reads() -> None:
    conduct = _conduct()
    _toml("a = " + "[" * 100 + "]" * 100 + "\n")

    assert (conduct["_cap"](), conduct["_pushes_tags"]()) == (None, True)


@pytest.mark.slow
def test_s_a_pipe_stops_the_read_at_once() -> None:
    path = layout.ship_file()
    path.parent.mkdir(parents=True)
    os.mkfifo(path)

    done = subprocess.run(
        [sys.executable, "-c", _CAP_CHILD, str(_CONDUCT_SCRIPT)],
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert (done.returncode, done.stdout) == (0, f"2 {path}: {_NOT_A_FILE}\n")


def test_s_a_config_folder_of_mode_0500_reads_and_a_file_of_mode_0_stops() -> None:
    conduct = _conduct()
    path = _toml("[queue]\nin_flight = 2\n")
    folder = path.parent
    folder.chmod(0o500)
    try:
        assert conduct["_cap"]() == 2
    finally:
        folder.chmod(0o700)
    if os.geteuid() == 0:
        pytest.skip("root reads a file of mode 0")
    path.chmod(0)
    try:
        _stopped(conduct, "_cap", f"{path}: Permission denied")
    finally:
        path.chmod(0o600)


@pytest.mark.parametrize(
    "value", ["0", "-1", "1.5", "2.0", '"2"', "true", "false", "[2]", "{a = 1}"]
)
def test_s_an_in_flight_that_is_no_whole_number_above_0_stops(value: str) -> None:
    conduct = _conduct()
    path = _toml(f"[queue]\nin_flight = {value}\n")

    _stopped(conduct, "_cap", f"{path}: `in_flight` is not a whole number above 0")


@pytest.mark.parametrize(("value", "cap"), [("1_0", 10), ("0x10", 16), ("1", 1)])
def test_s_in_flight_takes_tomls_integer_spellings(value: str, cap: int) -> None:
    conduct = _conduct()
    _toml(f"[queue]\nin_flight = {value}\n")

    assert conduct["_cap"]() == cap


@pytest.mark.parametrize(
    "value", ['"true"', '"yes"', "1", "0", "1.0", "[true]", "{a = 1}"]
)
def test_s_a_tags_that_is_no_bool_stops(value: str) -> None:
    conduct = _conduct()
    path = _toml(f"[push]\ntags = {value}\n")

    _stopped(conduct, "_pushes_tags", f"{path}: `tags` is not true or false")


@pytest.mark.parametrize(
    "text",
    [
        "[zzz]\nx = 1\n",
        "extra = 1\n",
        "queue = 3\npush = 1\n",
        "[push]\n[queue]\n",
    ],
)
def test_s_an_unknown_key_a_scalar_for_a_table_or_a_missing_key_sets_nothing(
    text: str,
) -> None:
    conduct = _conduct()
    _toml(text)

    assert (conduct["_cap"](), conduct["_pushes_tags"]()) == (None, True)


def test_s_a_bad_value_stops_its_own_reader_alone() -> None:
    conduct = _conduct()
    path = _toml('[queue]\nin_flight = 2\n[push]\ntags = "yes"\n')

    assert conduct["_cap"]() == 2
    _stopped(conduct, "_pushes_tags", f"{path}: `tags` is not true or false")
    path = _toml("[queue]\nin_flight = 0\n[push]\ntags = false\n")
    assert conduct["_pushes_tags"]() is False
    _stopped(conduct, "_cap", f"{path}: `in_flight` is not a whole number above 0")


_UNCLOSED = "[queue\n"
_UNCLOSED_WORDS = "Expected ']' at the end of a table declaration (at line 1, column 7)"


def _counted(conduct: dict[str, Any]) -> list[int]:
    """Wrap the conductor's `_ship_file` to count its calls; return the count's list."""
    names = conduct["main"].__globals__
    real = names["_ship_file"]
    reads: list[int] = []

    def counting() -> tuple[Path, dict[str, Any]]:
        reads.append(1)
        found: tuple[Path, dict[str, Any]] = real()
        return found

    names["_ship_file"] = counting
    return reads


@pytest.mark.slow
def test_sc_status_reads_the_file_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    fake()
    root, _ = test_conduct._with_origin(tmp_path)
    conduct["_keep_origin"](root)
    test_conduct._released(root, "v0.1.0")
    _toml("[queue]\nin_flight = 2\n[push]\ntags = false\n")
    reads = _counted(conduct)

    said = test_conduct._status(conduct, root, capsys, monkeypatch)

    assert said == "run · unpushed main\nrun · tags — this machine pushes none"
    assert len(reads) == 1


def test_sc_status_stops_on_a_toml_error_and_on_a_deep_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    conduct = _conduct()
    root = test_conduct._primary(tmp_path)
    path = _toml(_UNCLOSED)

    said = test_conduct._status(conduct, root, capsys, monkeypatch, 2)

    assert said == f"{path}: {_UNCLOSED_WORDS}"
    _toml(_NESTED["arrays"])
    said = test_conduct._status(conduct, root, capsys, monkeypatch, 2)
    assert said == f"{path}: {_DEEP}"


@pytest.mark.slow
def test_sc_report_reads_the_file_once_and_stops_as_status_does(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    conduct, root, _ = test_conduct._released_on_origin(tmp_path, monkeypatch)
    reads = _counted(conduct)

    assert test_conduct._main(conduct, root, "report", monkeypatch=monkeypatch) == 0
    assert len(reads) == 1
    path = _toml(_UNCLOSED)
    capsys.readouterr()
    assert test_conduct._main(conduct, root, "report", monkeypatch=monkeypatch) == 2
    assert capsys.readouterr().out.strip() == f"{path}: {_UNCLOSED_WORDS}"
    _toml(_NESTED["arrays"])
    assert test_conduct._main(conduct, root, "report", monkeypatch=monkeypatch) == 2
    assert capsys.readouterr().out.strip() == f"{path}: {_DEEP}"


@pytest.mark.slow
def test_sc_run_reads_the_file_twice_and_a_deep_file_starts_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: Callable[..., Path],
) -> None:
    conduct = _conduct()
    fake()
    root = test_conduct._primary(tmp_path)
    _toml("[queue]\nin_flight = 2\n[push]\ntags = false\n")
    reads = _counted(conduct)

    assert test_conduct._run_claude(conduct, root, monkeypatch) == 0
    assert len(reads) == 2
    path = _toml(_NESTED["arrays"])
    capsys.readouterr()
    assert test_conduct._run_claude(conduct, root, monkeypatch) == 2
    assert capsys.readouterr().out.strip() == f"{path}: {_DEEP}"
    assert not (root / ".minions" / "runs" / "active").exists()


@pytest.mark.slow
def test_sc_cut_reads_the_file_once_and_reserves_nothing_for_a_deep_one(
    tmp_path: Path, fake: Callable[..., Path]
) -> None:
    conduct = _conduct()
    fake()
    names = conduct["main"].__globals__
    root = test_conduct._primary(tmp_path)
    test_conduct._swap_runner(conduct)
    names["_start_run"] = lambda primary, executor: 4242
    brief = tmp_path / "brief.md"
    brief.write_text(f"# brief\n\n{test_conduct._items('d', 'e')}")
    _toml("[queue]\nin_flight = 2\n")
    reads = _counted(conduct)

    def cut(slug: str) -> str:
        said: str = conduct["cut"](
            root, slug, "minor", f"brief={brief}", [], "claude", None, None
        )
        return said

    assert cut("d") == "cut: queued 0001-d · run started · pid 4242 · cap 2"
    assert len(reads) == 1
    path = _toml(_NESTED["arrays"])
    _stopped_by(conduct, lambda: cut("e"), f"{path}: {_DEEP}")
    assert os.listdir(root / ".minions" / "cuts") == ["0001-d"]
