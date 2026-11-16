"""The scripts' calls on the OS: the native architecture, `ps`, the conductor's hold.

Fakes of `sysctl`, `ps` and `caffeinate` first on `PATH`. Why: 0128-platform-port
design D7.
"""

import os
import subprocess
import sys
import time
import types
from pathlib import Path

import pytest
from conduct_load import conduct as _conduct
from mflib import platform


def _tool(tmp_path: Path, name: str, text: str) -> Path:
    """Write the executable `name` holding `text` into a folder; return the folder."""
    folder = tmp_path / f"{name}-bin"
    folder.mkdir(exist_ok=True)
    tool = folder / name
    tool.write_text(text)
    tool.chmod(0o755)
    return folder


def _uname(monkeypatch: pytest.MonkeyPatch, machine: str) -> None:
    monkeypatch.setattr(os, "uname", lambda: types.SimpleNamespace(machine=machine))


def _timeout(*args: object, **kwargs: object) -> None:
    raise subprocess.TimeoutExpired("tool", 60)


def test_the_native_architecture_reads_sysctl_past_a_translated_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _uname(monkeypatch, "x86_64")

    for printed, expected in (("1", "arm64"), ("0", "x86_64")):
        folder = _tool(tmp_path, "sysctl", f"#!/bin/sh\necho {printed}\n")
        monkeypatch.setenv("PATH", str(folder), prepend=os.pathsep)
        assert platform.arch() == expected


def test_the_native_architecture_falls_back_to_uname(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _uname(monkeypatch, "x86_64")
    empty = tmp_path / "empty-bin"
    empty.mkdir()

    with monkeypatch.context() as bare:
        bare.setenv("PATH", str(empty))
        assert platform.arch() == "x86_64"

    folder = _tool(tmp_path, "sysctl", "#!/bin/sh\necho 1\n")
    monkeypatch.setenv("PATH", str(folder), prepend=os.pathsep)
    monkeypatch.setattr(subprocess, "run", _timeout)
    assert platform.arch() == "x86_64"


def test_ps_reads_nothing_when_it_cannot_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ps = _conduct()["_ps"]
    empty = tmp_path / "empty-bin"
    empty.mkdir()

    with monkeypatch.context() as bare:
        bare.setenv("PATH", str(empty))
        assert ps(os.getpid(), "lstart=") == ""

    monkeypatch.setattr(subprocess, "run", _timeout)
    assert ps(os.getpid(), "lstart=") == ""


_RECORD_SESSION = """
import os
import sys

record = os.environ["FAKE_SESSION_RECORD"]
with open(record + ".tmp", "w") as out:
    out.write(f"{os.getsid(0)} {os.getpid()}")
os.replace(record + ".tmp", record)
"""


def test_the_conductors_hold_runs_in_a_session_of_its_own(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = tmp_path / "session.txt"
    folder = _tool(tmp_path, "caffeinate", f"#!{sys.executable} -S{_RECORD_SESSION}")
    monkeypatch.setenv("PATH", str(folder), prepend=os.pathsep)
    monkeypatch.setenv("FAKE_SESSION_RECORD", str(record))

    assert _conduct()["_hold_awake"](4242) == "awake: held"

    deadline = time.monotonic() + 10
    while not record.is_file() and time.monotonic() < deadline:
        time.sleep(0.05)
    session, pid = (int(word) for word in record.read_text().split())
    assert session == pid
    assert session != os.getsid(0)
