"""The no-follow reads, pinned as the code stands: a bad byte, the bounds, a FIFO.

Cases H and I of 0136-status-log design's pin, and a FIFO at each non-blocking read.
"""

import importlib.util
import os
import runpy
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from conduct_load import conduct as _conduct

_SKILLS = Path(__file__).resolve().parent.parent / "skills"
_CHANGE = "0001-a"
_SPEC = importlib.util.spec_from_file_location(
    "log_reads_stamp", _SKILLS / "mf-converge" / "scripts" / "stamp.py"
)
assert _SPEC and _SPEC.loader
stamp = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(stamp)
converge = runpy.run_path(str(_SKILLS / "mf-converge" / "scripts" / "converge.py"))
viewer = runpy.run_path(str(_SKILLS / "mf-ui" / "scripts" / "viewer.py"))
conduct = _conduct()


def _log(tmp_path: Path, data: bytes) -> Path:
    """Write the change's status log under `tmp_path` as a primary checkout."""
    log = tmp_path / ".minions" / "changes" / _CHANGE / "status_log.md"
    log.parent.mkdir(parents=True)
    log.write_bytes(data)
    return log


def _run_end(tmp_path: Path) -> str | None:
    return conduct["_run_end"](tmp_path / ".minions", _CHANGE)


def test_case_h_a_bad_byte_raises_in_the_stamp_and_run_end_and_is_replaced_else(
    tmp_path: Path,
) -> None:
    log = _log(tmp_path, b"# t\n\n## Run 1 \xff\n10:00:00 \xff\n")

    with pytest.raises(UnicodeDecodeError):
        stamp.read(log)
    with pytest.raises(UnicodeDecodeError):
        _run_end(tmp_path)
    for read in (converge["_text"], conduct["_bounded"], viewer["read_part"]):
        assert read(log) == "# t\n\n## Run 1 �\n10:00:00 �\n", read


def test_case_i_the_bounds_of_each_read_as_literals(tmp_path: Path) -> None:
    long = "a" * 300_000
    log = _log(tmp_path, f"# t\n\n## Run 1 — d\n{long}\n".encode())
    for read in (stamp.read, converge["_text"]):
        assert read(log) == f"# t\n\n## Run 1 — d\n{long}\n", read
    assert _run_end(tmp_path) == long

    bounded, read_part = conduct["_bounded"], viewer["read_part"]
    sized = tmp_path / "sized"
    sized.write_text("b" * 65_536)
    assert bounded(sized) == "b" * 65_536
    sized.write_text("b" * 65_537)
    assert bounded(sized) is None

    sized.write_text("c" * 100_000)
    assert read_part(sized) == "c" * 100_000
    sized.write_text("d" + "e" * 262_143 + "f")
    assert read_part(sized) == "d" + "e" * 262_143
    assert read_part(sized, tail=True) == "e" * 262_143 + "f"


def _in_thread(read: Callable[[Path], Any], path: Path) -> list[Any]:
    """Return what `read(path)` returned or raised, run in a thread joined for 10 s."""
    said: list[Any] = []

    def run() -> None:
        try:
            said.append(read(path))
        except OSError as error:
            said.append(error)

    reader = threading.Thread(target=run, daemon=True)
    reader.start()
    # A FIFO opened blocking waits for a writer: the join bounds a red run.
    reader.join(timeout=10)
    assert not reader.is_alive()
    return said


def test_converge_text_refuses_a_fifo_inside_ten_seconds(tmp_path: Path) -> None:
    pipe = tmp_path / "pipe"
    os.mkfifo(pipe)

    [said] = _in_thread(converge["_text"], pipe)

    assert isinstance(said, OSError)


def test_viewer_read_part_gives_none_on_a_fifo_inside_ten_seconds(
    tmp_path: Path,
) -> None:
    pipe = tmp_path / "pipe"
    os.mkfifo(pipe)

    assert _in_thread(viewer["read_part"], pipe) == [None]
