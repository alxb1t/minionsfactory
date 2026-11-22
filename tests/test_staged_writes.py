"""The staged writes, pinned as the code stands: a table of each script's writer.

Cases A–D of 0136-status-log design's pin, each over every row, under `tmp_path`.
"""

import errno
import hashlib
import importlib.util
import json
import os
import stat
from collections.abc import Callable
from datetime import datetime, tzinfo
from pathlib import Path
from types import ModuleType
from typing import Any, NamedTuple
from unittest import mock

import pytest
from mflib import statuslog

_SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "mf-converge" / "scripts"
_TEXT = "the new text\n"
# A skip stub's own check passes over a file of `mode: skipped`.
_OLD = "---\nmode: skipped\n---\n"
_DATE = "2026-11-19T09:00:00+00:00"
_KEY = "key"


def _load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"staged_{name}", _SCRIPTS / name)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bundle, debt_match, open_cards, skip_stub, gate_run, plan_check = (
    _load(f"{name}.py")
    for name in (
        "bundle",
        "debt_match",
        "open_cards",
        "skip_stub",
        "gate_run",
        "plan_check",
    )
)


class _Clock:
    @staticmethod
    def now(tz: tzinfo) -> datetime:
        return datetime(2026, 11, 19, 9, 0, tzinfo=tz)


@pytest.fixture(autouse=True)
def _fixed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fix the gate record's date, and make the plan check's store the folder named."""
    monkeypatch.setattr(gate_run, "datetime", _Clock)
    monkeypatch.setattr(plan_check, "store", Path)


def _stopped(
    module: ModuleType, write: Callable[..., Any]
) -> Callable[..., str | None]:
    """Return a writer that answers the module's `Stop` as its text, else None."""

    def call(path: Path, text: str) -> str | None:
        try:
            write(path, text)
        except module.Stop as stop:
            return str(stop)
        return None

    return call


def _stamp(path: Path, text: str) -> str | None:
    """Return the stamp's refusal to write `text`, its read and insert set aside."""
    lines = (text.splitlines(), [])
    with (
        mock.patch.object(statuslog, "_read_held", return_value=""),
        mock.patch.object(statuslog, "insert", return_value=lines),
    ):
        try:
            statuslog.stamp(path, [], None, None)
        except statuslog.Refused as refused:
            return str(refused)
    return None


def _keep(path: Path, text: str) -> str | None:
    plan_check.keep(str(path.parent), _KEY, plan_check.Result(0, text))
    return None


class Row(NamedTuple):
    """A staged write: its script, the file it writes, its call, and what it writes."""

    name: str
    target: str
    write: Callable[[Path, str], str | None]
    holds: Callable[[str], str]


def _same(text: str) -> str:
    return text


ROWS = (
    Row("stamp.py", "status_log.md", _stamp, _same),
    Row("bundle.py", "bundle.md", _stopped(bundle, bundle.write), _same),
    Row(
        "debt_match.py", "debt-cards.md", _stopped(debt_match, debt_match.write), _same
    ),
    Row("open_cards.py", "open.md", _stopped(open_cards, open_cards.write), _same),
    Row("skip_stub.py", "adversarial.md", _stopped(skip_stub, skip_stub.write), _same),
    Row(
        "gate_run.py",
        "tree",
        lambda path, text: gate_run.write_record(path, text, 1),
        lambda text: f"dry: {text}\ndate: {_DATE}\nseconds: 1\n",
    ),
    Row(
        "plan_check.py",
        hashlib.sha256(_KEY.encode()).hexdigest(),
        _keep,
        lambda text: json.dumps({"exit": 0, "output": text, "stderr": ""}),
    ),
)
_IDS = [row.name for row in ROWS]
# The change-folder writers refuse a link at the target; the stores replace it.
_REFUSES_LINK = {
    "stamp.py",
    "bundle.py",
    "debt_match.py",
    "open_cards.py",
    "skip_stub.py",
}


def _target(tmp_path: Path, row: Row) -> Path:
    folder = tmp_path / "folder"
    folder.mkdir()
    return folder / row.target


def _staged(target: Path) -> Path:
    return target.with_name(f"{target.name}.tmp")


@pytest.mark.parametrize("row", ROWS, ids=_IDS)
def test_case_a_a_stale_tmp_that_links_outside_is_cleared(
    tmp_path: Path, row: Row
) -> None:
    target = _target(tmp_path, row)
    outside = tmp_path / "outside"
    outside.write_text(_OLD)
    _staged(target).symlink_to(outside)

    assert row.write(target, _TEXT) is None

    assert target.read_text() == row.holds(_TEXT)
    assert outside.read_text() == _OLD
    assert not os.path.lexists(_staged(target))


@pytest.mark.parametrize("row", ROWS, ids=_IDS)
def test_case_a_a_link_at_the_target_is_refused_or_replaced(
    tmp_path: Path, row: Row
) -> None:
    target = _target(tmp_path, row)
    outside = tmp_path / "outside"
    outside.write_text(_OLD)
    target.symlink_to(outside)

    said = row.write(target, _TEXT)

    assert outside.read_text() == _OLD
    if row.name in _REFUSES_LINK:
        assert said == f"{target} is a link"
        assert target.is_symlink()
    else:
        assert said is None
        assert not target.is_symlink()
        assert target.read_text() == row.holds(_TEXT)


@pytest.mark.parametrize("row", ROWS, ids=_IDS)
def test_case_b_a_file_made_at_the_tmp_after_the_clear_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, row: Row
) -> None:
    target = _target(tmp_path, row)
    target.write_text(_OLD)
    real = os.open

    def planting(
        path: Path, flags: int, mode: int = 0o777, *, dir_fd: int | None = None
    ) -> int:
        if Path(path).name.endswith(".tmp") and flags & os.O_EXCL:
            made = real(path, os.O_WRONLY | os.O_CREAT, 0o644, dir_fd=dir_fd)
            os.write(made, b"planted\n")
            os.close(made)
        return real(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "open", planting)

    said = row.write(target, _TEXT)

    monkeypatch.undo()
    assert target.read_text() == _OLD
    assert (said is None) == (row.name == "plan_check.py")
    if os.path.lexists(_staged(target)):
        assert _staged(target).read_text() == "planted\n"


@pytest.mark.parametrize("row", ROWS, ids=_IDS)
def test_case_c_the_target_is_a_new_file_of_mode_0644(tmp_path: Path, row: Row) -> None:
    target = _target(tmp_path, row)
    target.write_text(_OLD)
    target.chmod(0o600)
    hard = tmp_path / "hard"
    os.link(target, hard)
    umask = os.umask(0o022)
    try:
        assert row.write(target, _TEXT) is None
    finally:
        os.umask(umask)

    assert stat.S_IMODE(target.stat().st_mode) == 0o644
    assert target.stat().st_ino != hard.stat().st_ino
    assert target.read_text() == row.holds(_TEXT)
    assert hard.read_text() == _OLD


# The converge writers that word a failed write as `<path>: <reason>`.
_WORDED = {"bundle.py", "debt_match.py", "open_cards.py"}
_ADAPTERS = [row for row in ROWS if row.name in _WORDED]


@pytest.mark.parametrize("row", _ADAPTERS, ids=[row.name for row in _ADAPTERS])
def test_a_parent_that_is_a_file_is_the_writers_own_refusal(
    tmp_path: Path, row: Row
) -> None:
    # Why: 0136-status-log converge card S1.
    parent = tmp_path / "parent"
    parent.write_text(_OLD)
    target = parent / row.target

    said = row.write(target, _TEXT)

    assert said == f"{target}: {os.strerror(errno.ENOTDIR)}"
    assert parent.read_text() == _OLD


@pytest.mark.parametrize("row", ROWS, ids=_IDS)
def test_case_d_a_failed_rename_ends_as_it_does_today(tmp_path: Path, row: Row) -> None:
    target = _target(tmp_path, row)
    target.mkdir()
    (target / "kept").write_text("kept\n")

    said = row.write(target, _TEXT)

    assert (said is None) == (row.name == "plan_check.py")
    assert (target / "kept").read_text() == "kept\n"
    assert not os.path.lexists(_staged(target))
