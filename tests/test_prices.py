"""The price table's reader in the home, each case a form of the file.

Why: 0162-metric-scripts design D4.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from mflib import prices

_GOOD = (
    "[models]\n"
    '"m" = { input = 2.0, cached_input = 0.1, output = 10.0 }\n'
    '"n" = { input = 4, output = 20 }\n'
)
_ROWS = {
    "m": {"input": 2.0, "cached_input": 0.1, "output": 10.0},
    "n": {"input": 4, "output": 20},
}


def _unread(path: Path) -> str:
    """Return the reason `rows` refuses `path`."""
    with pytest.raises(prices.Unreadable) as refused:
        prices.rows(path)
    return refused.value.reason


def test_rows_read_the_models_table(tmp_path: Path) -> None:
    path = tmp_path / "prices.toml"
    path.write_text(_GOOD)

    assert prices.rows(path) == _ROWS
    path.write_bytes(_GOOD.replace("\n", "\r\n").encode())
    assert prices.rows(path) == _ROWS
    path.write_text("[models]\n")
    assert prices.rows(path) == {}


def test_a_row_with_a_string_price_or_a_bool_is_left_out(tmp_path: Path) -> None:
    path = tmp_path / "prices.toml"
    path.write_text(
        "[models]\n"
        '"a" = { input = "2.0", output = 1 }\n'
        '"b" = { input = true, output = 1 }\n'
        '"c" = 5\n'
        '"d" = [1, 2]\n'
        '"e" = { input = 1, nested = { x = 1 } }\n'
        '"f" = { input = 1.5, output = 2 }\n'
    )

    assert prices.rows(path) == {"f": {"input": 1.5, "output": 2}}


def test_a_link_is_unreadable_a_dangling_one_too(tmp_path: Path) -> None:
    target = tmp_path / "target.toml"
    target.write_text(_GOOD)
    link = tmp_path / "prices.toml"
    link.symlink_to(target)

    assert _unread(link) == "it is a link"
    target.unlink()
    assert _unread(link) == "it is a link"


def test_a_missing_file_gives_the_systems_text(tmp_path: Path) -> None:
    assert _unread(tmp_path / "prices.toml") == "No such file or directory"


def test_a_folder_is_no_file(tmp_path: Path) -> None:
    folder = tmp_path / "prices.toml"
    folder.mkdir()

    assert _unread(folder) == "it is not a file"


def test_a_file_over_the_bound_is_unreadable_and_one_at_it_is_read(
    tmp_path: Path,
) -> None:
    path = tmp_path / "prices.toml"
    pad = prices.BOUND - len(_GOOD.encode())
    path.write_bytes(_GOOD.encode() + b"#" * (pad - 1) + b"\n")
    assert path.stat().st_size == 262144
    assert prices.rows(path) == _ROWS

    path.write_bytes(_GOOD.encode() + b"#" * pad + b"\n")

    assert _unread(path) == "it is over 262144 bytes"


def test_text_that_is_no_toml_gives_the_parsers_text(tmp_path: Path) -> None:
    path = tmp_path / "prices.toml"
    path.write_text("not = = toml\n")

    assert _unread(path) == "Invalid value (at line 1, column 7)"


def test_a_bad_byte_gives_the_decoders_text(tmp_path: Path) -> None:
    path = tmp_path / "prices.toml"
    path.write_bytes(b"\xff\xfe")

    assert _unread(path) == (
        "'utf-8' codec can't decode byte 0xff in position 0: invalid start byte"
    )


def test_a_models_that_is_missing_or_no_table_is_unreadable(tmp_path: Path) -> None:
    path = tmp_path / "prices.toml"
    for text in ("", "[other]\nx = 1\n", "models = 5\n", 'models = "x"\n'):
        path.write_text(text)
        assert _unread(path) == "no models table", text


@pytest.mark.slow
def test_a_pipe_is_unreadable_and_blocks_nothing(tmp_path: Path) -> None:
    pipe = tmp_path / "prices.toml"
    os.mkfifo(pipe)
    home = Path(prices.__file__).resolve().parents[1]
    code = (
        "import sys\n"
        "sys.path.insert(0, sys.argv[1])\n"
        "from mflib import prices\n"
        "try:\n"
        "    prices.rows(__import__('pathlib').Path(sys.argv[2]))\n"
        "except prices.Unreadable as refused:\n"
        "    print(refused.reason)\n"
    )

    done = subprocess.run(
        [sys.executable, "-c", code, str(home), str(pipe)],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert done.stdout == "it is not a file\n"
