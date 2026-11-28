"""Unit and round-trip cases of the pin's files and `ship.toml` in `kept.py`.

Each case holds the side its reading settles.
Why: 0160-pins design D1, D3, D4, D7 and D8, The readings.
"""

import errno
import os
import stat
import tomllib
from collections.abc import Callable
from pathlib import Path
from typing import IO, Any

import pytest
from mflib import kept, layout

_READERS: dict[str, Callable[[], str | None]] = {
    "source": kept.source,
    "pending": kept.pending,
    "hold": kept.hold,
    "checkout": kept.checkout,
}
_KEEPERS: dict[str, Callable[[str], None]] = {
    "source": kept.keep_source,
    "pending": kept.keep_pending,
    "hold": kept.keep_hold,
    "checkout": kept.keep_checkout,
}
_PATHS: dict[str, Callable[[], Path]] = {
    "source": layout.pin_source,
    "pending": layout.pin_pending,
    "hold": layout.pin_hold,
    "checkout": layout.pin_checkout,
}
_NAMES = list(_READERS)


def _ship(content: str | bytes) -> Path:
    """Write the operator's `ship.toml`, its folder made; return its path."""
    path = layout.ship_file()
    path.parent.mkdir(parents=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content)
    return path


# --- Broken names a path outside the kept folder


def test_broken_under_the_kept_folder_keeps_its_frame() -> None:
    path = layout.kept_dir() / "source"

    error = kept.Broken(path, "it is not text")

    assert str(error) == "~/.mf-ship-origin/source cannot be read: it is not text"


def test_broken_outside_the_kept_folder_names_the_path_and_the_phrase() -> None:
    path = layout.ship_file()

    error = kept.Broken(path, "it is not text")

    assert str(error) == f"{path}: it is not text"
    assert error.filename == str(path)


@pytest.mark.parametrize("where", ["kept", "outside"])
def test_broken_holds_its_path_and_phrase(where: str) -> None:
    path = layout.kept_dir() / "hold" if where == "kept" else layout.ship_file()

    error = kept.Broken(path, "it is not text")

    assert error.path == path
    assert error.phrase == "it is not text"
    assert isinstance(error, OSError)


# --- the pin's files


@pytest.mark.parametrize("name", _NAMES)
def test_pin_a_file_that_stands_not_reads_none(name: str) -> None:
    assert _READERS[name]() is None


@pytest.mark.parametrize("name", _NAMES)
def test_pin_keep_then_read_round_trips_the_text(name: str) -> None:
    _KEEPERS[name]("v0.1.0")

    assert _READERS[name]() == "v0.1.0"
    assert _PATHS[name]().read_text() == "v0.1.0\n"


@pytest.mark.parametrize("name", _NAMES)
def test_pin_keep_writes_utf_8_whatever_the_locale(
    name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened = os.fdopen

    def latin_1(fd: int, mode: str, encoding: str | None = None) -> IO[str]:
        if "b" in mode:
            return opened(fd, mode)
        return opened(fd, mode, encoding=encoding or "latin-1")

    monkeypatch.setattr(os, "fdopen", latin_1)

    _KEEPERS[name]("Müller")

    assert _PATHS[name]().read_bytes() == "Müller\n".encode()
    assert _READERS[name]() == "Müller"


@pytest.mark.parametrize("name", _NAMES)
def test_pin_read_strips_the_white_space_around_the_text(name: str) -> None:
    path = _PATHS[name]()
    path.parent.mkdir()
    path.write_text("  v0.2.0 \t\r\n")

    assert _READERS[name]() == "v0.2.0"


def test_pin_read_keeps_the_inner_newlines_of_a_pending_of_several_lines() -> None:
    kept.keep_pending("v0.2.0\nsecond line")

    assert kept.pending() == "v0.2.0\nsecond line"


def _broken(name: str, phrase: str) -> None:
    """Assert the pin file `name`'s reader raises `Broken` naming it with `phrase`."""
    with pytest.raises(kept.Broken) as raised:
        _READERS[name]()
    assert raised.value.path == _PATHS[name]()
    assert str(raised.value) == f"~/.mf-ship-origin/{name} cannot be read: {phrase}"


@pytest.mark.parametrize("text", ["", " \t\n"])
@pytest.mark.parametrize("name", _NAMES)
def test_pin_read_an_empty_file_is_empty_text_and_source_none(
    name: str, text: str
) -> None:
    path = _PATHS[name]()
    path.parent.mkdir()
    path.write_text(text)

    assert _READERS[name]() == (None if name == "source" else "")


@pytest.mark.parametrize("name", _NAMES)
def test_pin_read_a_folder_at_the_name_is_broken(name: str) -> None:
    path = _PATHS[name]()
    path.mkdir(parents=True)

    _broken(name, "it is not a file")


@pytest.mark.parametrize("kind", ["file", "dangling"])
@pytest.mark.parametrize("name", _NAMES)
def test_pin_read_a_link_is_broken(name: str, kind: str, tmp_path: Path) -> None:
    target = tmp_path / "target"
    if kind == "file":
        target.write_text("v0.1.0\n")
    path = _PATHS[name]()
    path.parent.mkdir()
    path.symlink_to(target)

    _broken(name, "it is not a file")


@pytest.mark.parametrize("name", _NAMES)
def test_pin_read_a_pipe_is_broken_at_once(name: str) -> None:
    path = _PATHS[name]()
    path.parent.mkdir()
    os.mkfifo(path)

    _broken(name, "it is not a file")


@pytest.mark.parametrize("name", _NAMES)
def test_pin_read_a_bad_byte_is_broken(name: str) -> None:
    path = _PATHS[name]()
    path.parent.mkdir()
    path.write_bytes(b"\xff\xfe")

    _broken(name, "it is not text")


@pytest.mark.parametrize("name", _NAMES)
def test_pin_read_a_file_over_the_bound_is_broken(name: str) -> None:
    path = _PATHS[name]()
    path.parent.mkdir()
    path.write_text("x" * kept.BOUND)
    assert _READERS[name]() == "x" * kept.BOUND

    path.write_text("x" * (kept.BOUND + 1))

    _broken(name, f"it is over {kept.BOUND} bytes")


def test_pin_keep_makes_the_kept_folder_at_0700() -> None:
    kept.keep_source("/primary")

    assert stat.S_IMODE(layout.kept_dir().stat().st_mode) == 0o700


def test_pin_keep_leaves_the_mode_of_a_folder_that_stands() -> None:
    layout.kept_dir().mkdir(mode=0o755)
    layout.kept_dir().chmod(0o755)

    kept.keep_hold("live")

    assert stat.S_IMODE(layout.kept_dir().stat().st_mode) == 0o755


def test_pin_keep_replaces_the_text_whole() -> None:
    kept.keep_pending("v0.1.0")

    kept.keep_pending("v0.2.0")

    assert layout.pin_pending().read_text() == "v0.2.0\n"


def test_pin_keep_in_a_home_that_stands_not_makes_it(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "no" / "such" / "home"))

    kept.keep_source("/primary")

    assert layout.pin_source().read_text() == "/primary\n"
    assert stat.S_IMODE(layout.kept_dir().stat().st_mode) == 0o700


def test_pin_keep_over_a_folder_is_unwritten_naming_the_file() -> None:
    layout.pin_hold().mkdir(parents=True)

    with pytest.raises(kept.Unwritten) as raised:
        kept.keep_hold("live")

    assert raised.value.errno == errno.EISDIR
    assert raised.value.filename == str(layout.pin_hold())
    assert not layout.pin_hold().with_name("hold.tmp").exists()


@pytest.mark.parametrize("name", _NAMES)
def test_pin_keep_writes_the_file_0600_whatever_the_umask(name: str) -> None:
    before = os.umask(0o022)
    try:
        _KEEPERS[name]("v0.1.0")
    finally:
        os.umask(before)

    assert stat.S_IMODE(_PATHS[name]().stat().st_mode) == 0o600
    assert sorted(entry.name for entry in layout.kept_dir().iterdir()) == [name]


@pytest.mark.parametrize("kind", ["file", "dangling"])
@pytest.mark.parametrize("name", _NAMES)
def test_pin_keep_replaces_a_link_and_leaves_its_target(
    name: str, kind: str, tmp_path: Path
) -> None:
    target = tmp_path / "target"
    if kind == "file":
        target.write_text("orig\n")
    path = _PATHS[name]()
    path.parent.mkdir()
    path.symlink_to(target)

    _KEEPERS[name]("v0.1.0")

    assert not path.is_symlink()
    assert path.read_text() == "v0.1.0\n"
    if kind == "file":
        assert target.read_text() == "orig\n"
    else:
        assert not target.exists()


@pytest.mark.parametrize("name", _NAMES)
def test_pin_keep_replaces_a_pipe_without_blocking(name: str) -> None:
    path = _PATHS[name]()
    path.parent.mkdir()
    os.mkfifo(path)

    _KEEPERS[name]("v0.1.0")

    assert stat.S_ISREG(path.lstat().st_mode)
    assert path.read_text() == "v0.1.0\n"


@pytest.mark.parametrize("name", ["pending", "hold"])
def test_pin_clear_removes_a_link_and_leaves_its_target(
    name: str, tmp_path: Path
) -> None:
    target = tmp_path / "target"
    target.write_text("orig\n")
    path = _PATHS[name]()
    path.parent.mkdir()
    path.symlink_to(target)

    {"pending": kept.clear_pending, "hold": kept.clear_hold}[name]()

    assert not os.path.lexists(path)
    assert target.read_text() == "orig\n"


@pytest.mark.parametrize("name", ["pending", "hold"])
def test_pin_clear_removes_the_file(name: str) -> None:
    _KEEPERS[name]("v0.1.0")

    {"pending": kept.clear_pending, "hold": kept.clear_hold}[name]()

    assert not _PATHS[name]().exists()


@pytest.mark.parametrize("clear", [kept.clear_pending, kept.clear_hold])
def test_pin_clear_of_a_gone_file_is_quiet(clear: Callable[[], None]) -> None:
    clear()

    layout.kept_dir().mkdir()
    clear()


def test_pin_clear_leaves_the_other_files() -> None:
    kept.keep_pending("v0.1.0")
    kept.keep_hold("v0.1.0")
    kept.keep_source("/primary")

    kept.clear_pending()

    assert kept.hold() == "v0.1.0"
    assert kept.source() == "/primary"


# --- ship.toml


def test_ship_data_for_no_file_is_empty() -> None:
    assert kept.ship_data() == {}


def test_ship_data_for_an_empty_file_is_empty() -> None:
    _ship("")

    assert kept.ship_data() == {}


def test_ship_data_returns_the_parsed_tables() -> None:
    _ship("[queue]\nin_flight = 2\n[push]\ntags = false\n")

    assert kept.ship_data() == {"queue": {"in_flight": 2}, "push": {"tags": False}}


def test_ship_data_reads_at_each_call() -> None:
    path = _ship("[queue]\nin_flight = 2\n")
    assert kept.ship_data() == {"queue": {"in_flight": 2}}

    path.write_text("[queue]\nin_flight = 3\n")

    assert kept.ship_data() == {"queue": {"in_flight": 3}}


def _ship_broken(phrase: str) -> None:
    """Assert `ship_data` raises `Broken` naming `ship.toml` with `phrase`."""
    with pytest.raises(kept.Broken) as raised:
        kept.ship_data()
    assert raised.value.path == layout.ship_file()
    assert raised.value.phrase == phrase
    assert str(raised.value) == f"{layout.ship_file()}: {phrase}"


def test_ship_data_a_folder_is_broken() -> None:
    layout.ship_file().mkdir(parents=True)

    _ship_broken("it is not a file")


def test_ship_data_under_a_file_at_the_config_folder_is_broken() -> None:
    layout.config_dir().parent.mkdir(parents=True)
    layout.config_dir().write_text("x\n")

    _ship_broken("Not a directory")


def test_ship_data_a_bad_byte_is_broken() -> None:
    _ship(b"\xff\xfe")

    _ship_broken("it is not text")


def test_ship_data_a_toml_error_is_broken_in_the_parsers_words() -> None:
    _ship("[queue")

    with pytest.raises(tomllib.TOMLDecodeError) as parsed:
        tomllib.loads("[queue")
    _ship_broken(str(parsed.value))


@pytest.mark.parametrize("kind", ["file", "dangling"])
def test_ship_data_a_link_is_broken(kind: str, tmp_path: Path) -> None:
    target = tmp_path / "target.toml"
    if kind == "file":
        target.write_text("[queue]\nin_flight = 2\n")
    layout.ship_file().parent.mkdir(parents=True)
    layout.ship_file().symlink_to(target)

    _ship_broken("it is not a file")


def test_ship_data_a_pipe_is_broken_at_once() -> None:
    layout.ship_file().parent.mkdir(parents=True)
    os.mkfifo(layout.ship_file())

    _ship_broken("it is not a file")


def test_ship_data_a_file_over_the_bound_is_broken() -> None:
    path = _ship("# " + "x" * (kept.BOUND - 3) + "\n")
    assert kept.ship_data() == {}

    path.write_text("# " + "x" * (kept.BOUND - 2) + "\n")

    _ship_broken(f"it is over {kept.BOUND} bytes")


@pytest.mark.parametrize(
    "text",
    ["a = " + "[" * 1000 + "]" * 1000 + "\n", "a = " + "{b = " * 400 + "1" + "}" * 400],
)
def test_ship_data_a_file_nested_too_deep_is_broken(text: str) -> None:
    _ship(text)

    _ship_broken("it is nested too deep")


def test_ship_data_an_integer_past_the_digit_limit_is_broken() -> None:
    _ship("in_flight = " + "1" * 5000 + "\n")

    with pytest.raises(ValueError, match="Exceeds the limit") as parsed:
        tomllib.loads("in_flight = " + "1" * 5000)
    _ship_broken(str(parsed.value))


@pytest.mark.parametrize(
    ("data", "cap"),
    [
        ({}, None),
        ({"queue": 3}, None),
        ({"queue": {}}, None),
        ({"queue": {"in_flight": 1}}, 1),
        ({"queue": {"in_flight": 2}, "push": {"tags": False}}, 2),
    ],
)
def test_ship_cap_returns_in_flight_or_none(
    data: dict[str, Any], cap: int | None
) -> None:
    assert kept.ship_cap(data) == cap


@pytest.mark.parametrize("value", [0, -1, 1.5, 2.0, "2", True, False, [2], {"a": 1}])
def test_ship_cap_a_value_that_is_no_whole_number_above_0_is_broken(
    value: object,
) -> None:
    with pytest.raises(kept.Broken) as raised:
        kept.ship_cap({"queue": {"in_flight": value}})

    assert raised.value.path == layout.ship_file()
    assert raised.value.phrase == "`in_flight` is not a whole number above 0"
    assert str(raised.value) == (
        f"{layout.ship_file()}: `in_flight` is not a whole number above 0"
    )


@pytest.mark.parametrize(
    ("data", "tags"),
    [
        ({}, True),
        ({"push": 1}, True),
        ({"push": {}}, True),
        ({"push": {"tags": True}}, True),
        ({"push": {"tags": False}}, False),
    ],
)
def test_ship_tags_returns_tags_or_true(data: dict[str, Any], tags: bool) -> None:
    assert kept.ship_tags(data) is tags


@pytest.mark.parametrize("value", ["true", "yes", 1, 0, 1.0, [True], {"a": 1}])
def test_ship_tags_a_value_that_is_no_boolean_is_broken(value: object) -> None:
    with pytest.raises(kept.Broken) as raised:
        kept.ship_tags({"push": {"tags": value}})

    assert raised.value.path == layout.ship_file()
    assert raised.value.phrase == "`tags` is not true or false"
    assert str(raised.value) == f"{layout.ship_file()}: `tags` is not true or false"
