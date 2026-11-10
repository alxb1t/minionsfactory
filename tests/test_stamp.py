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


def _ended(event: str) -> str:
    head, rest = _RUN_1.split("\n", 1)
    return f"{head}\n09:00:09 · round 1 · {event}\n{rest}"


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

    # Several events in one call: each printed, the last given on top.
    # Why: 0100-worker-diet design D9.
    log.write_text(f"{_TITLE}\n{_RUN_1}")
    roles = ("conformance", "adversarial")
    assert stamp.main([str(log), *(f"round 1 · verdicts — {r}" for r in roles)]) == 0
    first, second = (f"10:02:03 · round 1 · verdicts — {r}" for r in roles)
    assert capsys.readouterr().out == f"{first}\n{second}\n"
    head, rest = _RUN_1.split("\n", 1)
    assert log.read_text() == f"{_TITLE}\n{head}\n{second}\n{first}\n{rest}"

    # `done` goes last in a call, so it is on top; a run ends on its `done` or `halt`,
    # save a `halt` naming a lock, under which converge resumes.
    # Why: 0109-converge-done-order design D1.
    log.write_text(f"{_TITLE}\n{_RUN_1}")
    debt, done = (f"10:02:03 · round 1 · {e} — x" for e in ("debt", "done"))
    assert stamp.main([str(log), "round 1 · debt — x", "round 1 · done — x"]) == 0
    assert capsys.readouterr().out == f"{debt}\n{done}\n"
    assert log.read_text() == f"{_TITLE}\n{head}\n{done}\n{debt}\n{rest}"
    for lock in (".minions/debt.lock", ".minions/backlog.lock"):
        log.write_text(f"{_TITLE}\n{_ended(f'halt — {lock} not taken')}")
        assert stamp.main([str(log), "round 1 · debt — x"]) == 0
        assert capsys.readouterr().out == f"{debt}\n"
        assert log.read_text().splitlines()[3] == debt
    log.write_text(f"{_TITLE}\n{_ended('done — clean')}")
    assert stamp.main([str(log), "--run", "2"]) == 0
    assert capsys.readouterr().out == "## Run 2 — 2026-11-07 10:02\n"
    assert log.read_text().splitlines()[2] == "## Run 2 — 2026-11-07 10:02"


def test_a_log_out_of_shape_is_not_stamped(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    missing = tmp_path / "missing.md"
    assert stamp.main([str(missing), "round 1 · start — base a"]) == 2
    assert capsys.readouterr().out == (
        f"stamp: cannot stamp — {missing}: No such file or directory\n"
    )
    assert not missing.exists()

    usage = "give events, or --run with an optional --mark\n"

    def last(event: str) -> str:
        return f"{event} goes last in a call\n"

    def ends(event: str) -> str:
        return f"the run ends on {event}: open a ## Run for a new event\n"

    log = tmp_path / "status_log.md"
    for text, argv, said in (
        (_TITLE, ["round 1 · start — base a"], "no ## Run heading\n"),
        (_RUN_1, ["--run", "2"], "no # title\n"),
        (_TITLE + _RUN_1, ["round 1 · x", "--run", "2"], usage),
        (_TITLE + _RUN_1, ["round 1 · x", "round 1 · y", "--run", "2"], usage),
        (_TITLE + _RUN_1, [], usage),
        (_TITLE + _RUN_1, ["round 1 · x", "--mark", "catch-up"], usage),
        (_TITLE + _RUN_1, ["round 1 · done — x", "round 1 · debt — x"], last("done")),
        (_TITLE + _RUN_1, ["round 1 · halt — x", "round 1 · debt — x"], last("halt")),
        (_TITLE + _ended("done — x"), ["round 1 · debt — x"], ends("done")),
        (_TITLE + _ended("halt — red"), ["round 1 · debt — x"], ends("halt")),
    ):
        log.write_text(text)
        assert stamp.main([str(log), *argv]) == 2
        assert capsys.readouterr().out == f"stamp: cannot stamp — {said}"
        assert log.read_text() == text

    # A worker can write the run directory: no stamp is written through a link.
    note = tmp_path / "note.md"
    note.write_text(_TITLE)
    log.unlink()
    log.symlink_to(note)
    assert stamp.main([str(log), "--run", "2"]) == 2
    assert capsys.readouterr().out == f"stamp: cannot stamp — {log} is a link\n"
    assert note.read_text() == _TITLE
    log.unlink()
    log.write_text(_TITLE + _RUN_1)
    staged = tmp_path / "status_log.md.tmp"
    staged.mkdir()
    assert stamp.main([str(log), "round 1 · x"]) == 2
    assert capsys.readouterr().out == (
        "stamp: cannot stamp — status_log.md.tmp could not be created\n"
    )
    assert log.read_text() == _TITLE + _RUN_1
    staged.rmdir()

    # A link swapped in after any check by name is still refused by the read itself.
    log.unlink()
    log.symlink_to(note)
    with monkeypatch.context() as patch:
        patch.setattr(Path, "is_symlink", lambda _: False)
        assert stamp.main([str(log), "--run", "2"]) == 2
    assert capsys.readouterr().out == f"stamp: cannot stamp — {log} is a link\n"
    assert note.read_text() == _TITLE
    log.unlink()

    # A log swapped for a folder between the read and the rename: exit 2, no `.tmp`.
    log.write_text(_TITLE + _RUN_1)
    real = stamp.stamp

    def swapped(*args: object) -> tuple[list[str], str]:
        log.unlink()
        log.mkdir()
        (log / "kept.md").write_text(_TITLE)
        return real(*args)

    monkeypatch.setattr(stamp, "stamp", swapped)
    assert stamp.main([str(log), "round 1 · x"]) == 2
    assert capsys.readouterr().out == (
        "stamp: cannot stamp — status_log.md could not be replaced\n"
    )
    assert (log / "kept.md").read_text() == _TITLE
    assert not staged.exists()
