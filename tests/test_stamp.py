"""Converge's status-log stamp: each event and run heading takes the clock's time.

Each log written under `tmp_path`. Why: 0088-paydown-2 design D7.
"""

import importlib.util
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from types import ModuleType

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-converge" / "scripts" / "stamp.py"


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("stamp", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


stamp = _load(_SCRIPT)

_TITLE = "# 0001-a — converge status\n"
_RUN_1 = "## Run 1 — 2026-11-06 09:00\n09:00:01 · round 1 · start — base x\n"


def test_a_stamp_writes_the_clock_time_under_the_latest_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(stamp, "_now", lambda: datetime(2026, 11, 7, 10, 2, 3))
    log = tmp_path / "status_log.md"
    log.write_text(f"{_TITLE}\n{_RUN_1}")
    run_2 = "## Run 2 — 2026-11-07 10:02 · catch-up"
    assert stamp.main([str(log), "--run", "2", "--mark", "catch-up"]) == 0
    assert capsys.readouterr().out == f"{run_2}\n"
    assert log.read_text() == f"{_TITLE}\n{run_2}\n\n{_RUN_1}"

    event = "10:02:03 · round 1 · start — base a"
    assert stamp.main([str(log), "round 1 · start — base a"]) == 0
    assert capsys.readouterr().out == f"{event}\n"
    assert log.read_text() == f"{_TITLE}\n{run_2}\n{event}\n\n{_RUN_1}"

    done = subprocess.run(
        [sys.executable, str(_SCRIPT), str(log), "round 1 · done — clean"],
        capture_output=True,
        text=True,
    )
    line = done.stdout.strip()
    assert done.returncode == 0
    assert re.fullmatch(r"\d\d:\d\d:\d\d · round 1 · done — clean", line)
    assert log.read_text() == f"{_TITLE}\n{run_2}\n{line}\n{event}\n\n{_RUN_1}"


def test_a_log_out_of_shape_is_not_stamped(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_path / "missing.md"
    assert stamp.main([str(missing), "round 1 · start — base a"]) == 2
    assert capsys.readouterr().out == (
        f"stamp: cannot stamp — {missing}: No such file or directory\n"
    )
    assert not missing.exists()

    usage = "give one event, or --run with an optional --mark\n"
    log = tmp_path / "status_log.md"
    for text, argv, said in (
        (_TITLE, ["round 1 · start — base a"], "no ## Run heading\n"),
        (_RUN_1, ["--run", "2"], "no # title\n"),
        (_TITLE + _RUN_1, ["round 1 · x", "--run", "2"], usage),
        (_TITLE + _RUN_1, [], usage),
        (_TITLE + _RUN_1, ["round 1 · x", "--mark", "catch-up"], usage),
    ):
        log.write_text(text)
        assert stamp.main([str(log), *argv]) == 2
        assert capsys.readouterr().out == f"stamp: cannot stamp — {said}"
        assert log.read_text() == text
