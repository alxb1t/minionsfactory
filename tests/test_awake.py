"""The cut's hold on the machine: `start` and `stop` by change id, in a scratch repo.

A fake `ps` and a fake `caffeinate` first on `PATH`; CI has no real `caffeinate`.
Why: 0081-cut-awake design Tests.
"""

import importlib.util
import os
import shlex
import signal
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-cut-change" / "scripts" / "awake.py"


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("awake", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


awake = _load(_SCRIPT)

_FAKE_PS = """
import os
import sys
from pathlib import Path

_, field, _, pid = sys.argv[1:]
known = Path(os.environ["FAKE_PS_REGISTRY"], f"{pid}.{field.rstrip('=')}")
if known.is_file():
    print(known.read_text())
"""


@pytest.fixture(autouse=True)
def ps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Put a fake `ps` first on `PATH`; return the registry it reads."""
    folder = tmp_path / "ps-bin"
    folder.mkdir()
    fake = folder / "ps"
    fake.write_text(f"#!{sys.executable} -S{_FAKE_PS}")
    fake.chmod(0o755)
    registry = tmp_path / "ps-registry"
    registry.mkdir()
    monkeypatch.setenv("PATH", str(folder), prepend=os.pathsep)
    monkeypatch.setenv("FAKE_PS_REGISTRY", str(registry))
    return registry


def _register(pid: int, comm: str, ppid: int | None = None) -> None:
    """Have the fake `ps` answer `comm`, and `ppid` when given, for `pid`."""
    registry = Path(os.environ["FAKE_PS_REGISTRY"])
    (registry / f"{pid}.comm").write_text(comm)
    if ppid is not None:
        (registry / f"{pid}.ppid").write_text(str(ppid))


def _ancestors(
    monkeypatch: pytest.MonkeyPatch, chain: list[tuple[int, str]], top: int | None
) -> None:
    """Make the first of `chain` the script's parent, each the child of the next."""
    for index, (pid, comm) in enumerate(chain):
        above = chain[index + 1][0] if index + 1 < len(chain) else top
        _register(pid, comm, above)
    monkeypatch.setattr(os, "getppid", lambda: chain[0][0])


def _repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Make a scratch repository under `tmp_path`, enter it, and return it."""
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    monkeypatch.chdir(root)
    return root


def _fake_caffeinate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path]:
    """Put a fake `caffeinate` first on `PATH`; return its argv file and term file."""
    folder = tmp_path / "caffeinate-bin"
    folder.mkdir()
    argv = tmp_path / "caffeinate-argv.txt"
    term = tmp_path / "caffeinate-term.txt"
    tool = folder / "caffeinate"
    tool.write_text(
        f"#!/bin/sh\n"
        f"trap 'echo TERM >> {shlex.quote(str(term))}; kill $!; exit 0' TERM\n"
        f'echo "$@" >> {shlex.quote(str(argv))}\n'
        f"sleep 60 &\nwait\n"
    )
    tool.chmod(0o755)
    monkeypatch.setenv("PATH", str(folder), prepend=os.pathsep)
    return argv, term


def _lines(path: Path) -> list[str]:
    return path.read_text().splitlines() if path.is_file() else []


def _wait(done: Callable[[], bool]) -> None:
    deadline = time.monotonic() + 10
    while not done() and time.monotonic() < deadline:
        time.sleep(0.05)
    assert done()


def test_a_cut_holds_the_machine_awake_by_change_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _repo(tmp_path, monkeypatch)
    argv, term = _fake_caffeinate(tmp_path, monkeypatch)
    _ancestors(
        monkeypatch,
        [(9001, "-zsh"), (9002, "/bin/zsh"), (9003, "uv"), (9004, "claude")],
        None,
    )

    assert awake.main(["start", "0001-a"]) == 0
    assert capsys.readouterr().out == "awake: held (2 h at most)\n"
    first = int((root / ".minions" / "awake" / "0001-a").read_text())
    _register(first, "caffeinate")
    _wait(lambda: len(_lines(argv)) == 1)
    assert _lines(argv) == ["-is -t 7200 -w 9004"]

    assert awake.main(["start", "0002-b"]) == 0
    capsys.readouterr()
    second = int((root / ".minions" / "awake" / "0002-b").read_text())
    _register(second, "caffeinate")
    assert second != first
    _wait(lambda: len(_lines(argv)) == 2)

    assert awake.main(["stop", "0001-a"]) == 0
    assert capsys.readouterr().out == "awake: released\n"
    _wait(lambda: _lines(term) == ["TERM"])
    assert not (root / ".minions" / "awake" / "0001-a").exists()
    assert (root / ".minions" / "awake" / "0002-b").read_text() == f"{second}\n"

    assert awake.main(["start", "0002-b"]) == 0
    capsys.readouterr()
    _wait(lambda: _lines(term) == ["TERM", "TERM"])
    third = int((root / ".minions" / "awake" / "0002-b").read_text())
    assert third != second
    _register(third, "caffeinate")
    _wait(lambda: len(_lines(argv)) == 3)

    assert awake.main(["stop", "0002-b"]) == 0
    _wait(lambda: _lines(term) == ["TERM"] * 3)


def test_no_hold_starts_without_caffeinate_or_a_host(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _repo(tmp_path, monkeypatch)
    argv, _ = _fake_caffeinate(tmp_path, monkeypatch)
    _ancestors(monkeypatch, [(9001, "zsh"), (9002, "claude")], None)

    with monkeypatch.context() as absent:
        absent.setitem(vars(awake), "CAFFEINATE", "caffeinate-absent")
        assert awake.main(["start", "0001-a"]) == 0
    assert capsys.readouterr().out == "awake: not held — caffeinate not on PATH\n"

    shells = [(9011, "zsh"), (9012, "uv")]
    for chain, top in ((shells, 1), ([(9021, "zsh")], None), ([(9031, "")], None)):
        _ancestors(monkeypatch, chain, top)
        assert awake.main(["start", "0001-a"]) == 0
        assert capsys.readouterr().out == "awake: not held — no host process\n"
    monkeypatch.setattr(os, "getppid", lambda: 9999)
    assert awake.main(["start", "0001-a"]) == 0
    assert capsys.readouterr().out == "awake: not held — no host process\n"

    assert not (root / ".minions" / "awake").exists()
    assert _lines(argv) == []


def test_stop_kills_only_a_recorded_caffeinate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _repo(tmp_path, monkeypatch)
    kills: list[tuple[int, int]] = []
    monkeypatch.setattr(os, "kill", lambda pid, sig: kills.append((pid, sig)))
    record = root / ".minions" / "awake" / "0001-a"
    record.parent.mkdir(parents=True)

    for text, comm, kept in (
        ("7777", "sleep", []),
        ("x", "caffeinate", []),
        ("1", "caffeinate", []),
        ("7778", "caffeinate", [(7778, signal.SIGTERM)]),
    ):
        _register(int(text) if text.isdigit() else 0, comm)
        record.write_text(f"{text}\n")
        assert awake.main(["stop", "0001-a"]) == 0
        released = "released" if kept else "none held"
        assert capsys.readouterr().out == f"awake: {released}\n"
        assert kills == kept
        assert not record.exists()
        kills.clear()

    assert awake.main(["stop", "0001-a"]) == 0
    assert capsys.readouterr().out == "awake: none held\n"
    assert awake.main(["stop", "../x"]) == 2
    assert capsys.readouterr().out == "awake: cannot run — not a change id: ../x\n"

    outside = tmp_path / "outside"
    outside.mkdir()
    monkeypatch.chdir(outside)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    assert awake.main(["stop", "0001-a"]) == 2
    assert capsys.readouterr().out == "awake: cannot run — not in a git repository\n"

    monkeypatch.chdir(root)
    done = subprocess.run(
        [sys.executable, str(_SCRIPT), "stop", "0001-a"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert (done.returncode, done.stdout) == (0, "awake: none held\n")
