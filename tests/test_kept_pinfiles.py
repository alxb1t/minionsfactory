"""Unit and round-trip cases of the pin's files and `ship.toml` in `kept.py`.

Each case holds today's side, as `pin.py` and the conductor keep these files.
Why: 0160-pins design D1 and D5.
"""

import stat
import tomllib
from collections.abc import Callable
from pathlib import Path
from typing import Any

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
def test_pin_read_strips_the_white_space_around_the_text(name: str) -> None:
    path = _PATHS[name]()
    path.parent.mkdir()
    path.write_text("  v0.2.0 \t\r\n")

    assert _READERS[name]() == "v0.2.0"


def test_pin_read_keeps_the_inner_newlines_of_a_pending_of_several_lines() -> None:
    kept.keep_pending("v0.2.0\nsecond line")

    assert kept.pending() == "v0.2.0\nsecond line"


@pytest.mark.parametrize("name", _NAMES)
def test_pin_read_an_empty_file_is_empty_text(name: str) -> None:
    path = _PATHS[name]()
    path.parent.mkdir()
    path.write_text("")

    assert _READERS[name]() == ""


@pytest.mark.parametrize("name", _NAMES)
def test_pin_read_a_folder_at_the_name_is_none(name: str) -> None:
    path = _PATHS[name]()
    path.mkdir(parents=True)

    assert _READERS[name]() is None


@pytest.mark.parametrize("name", _NAMES)
def test_pin_read_follows_a_link_to_a_file(name: str, tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.write_text("v0.1.0\n")
    path = _PATHS[name]()
    path.parent.mkdir()
    path.symlink_to(target)

    assert _READERS[name]() == "v0.1.0"


@pytest.mark.parametrize("name", _NAMES)
def test_pin_read_a_bad_byte_raises_the_decode_error(name: str) -> None:
    path = _PATHS[name]()
    path.parent.mkdir()
    path.write_bytes(b"\xff\xfe")

    with pytest.raises(UnicodeDecodeError):
        _READERS[name]()


@pytest.mark.parametrize("name", _NAMES)
def test_pin_read_a_file_over_the_bound_is_read_whole(name: str) -> None:
    path = _PATHS[name]()
    path.parent.mkdir()
    path.write_text("x" * (kept.BOUND + 100))

    assert _READERS[name]() == "x" * (kept.BOUND + 100)


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


def test_pin_keep_over_a_folder_raises_the_system_error() -> None:
    layout.pin_hold().mkdir(parents=True)

    with pytest.raises(IsADirectoryError):
        kept.keep_hold("live")


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


def test_ship_data_a_folder_raises_the_error_read_text_raises() -> None:
    layout.ship_file().mkdir(parents=True)

    with pytest.raises(IsADirectoryError):
        kept.ship_data()


def test_ship_data_under_a_file_at_the_config_folder_raises_not_a_directory() -> None:
    layout.config_dir().parent.mkdir(parents=True)
    layout.config_dir().write_text("x\n")

    with pytest.raises(NotADirectoryError):
        kept.ship_data()


def test_ship_data_a_bad_byte_raises_the_decode_error() -> None:
    _ship(b"\xff\xfe")

    with pytest.raises(UnicodeDecodeError):
        kept.ship_data()


def test_ship_data_a_toml_error_raises_the_parser_error() -> None:
    _ship("[queue")

    with pytest.raises(tomllib.TOMLDecodeError):
        kept.ship_data()


def test_ship_data_follows_a_link_to_a_file(tmp_path: Path) -> None:
    target = tmp_path / "target.toml"
    target.write_text("[queue]\nin_flight = 2\n")
    layout.ship_file().parent.mkdir(parents=True)
    layout.ship_file().symlink_to(target)

    assert kept.ship_data() == {"queue": {"in_flight": 2}}


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
