"""The scripts' OS calls: the side, the sandbox, the architecture, `ps`, the hold.

Fakes of `bwrap`, `sysctl`, `ps` and `caffeinate` first on `PATH`.
Why: 0128-platform-port design D7, 0131-linux-runner design D7.
"""

import os
import shlex
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


def test_the_side_names_linux_and_else_macos() -> None:
    names = ("linux", "linux2", "darwin", "freebsd")

    assert [platform.side(name) for name in names] == [
        "linux",
        "linux",
        "macos",
        "macos",
    ]


def test_a_refusal_is_read_on_its_own_side(monkeypatch: pytest.MonkeyPatch) -> None:
    mac = "touch: x: Operation not permitted"
    linux = "touch: x: Read-only file system"

    for side, own, other in (("macos", mac, linux), ("linux", linux, mac)):
        monkeypatch.setattr(platform, "OS", side)
        assert platform.refused(own)
        assert not platform.refused(other)


def test_the_bwrap_command_follows_the_policy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(platform, "OS", "linux")
    empty = tmp_path / "empty-bin"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))
    a, b, temp, folder = (tmp_path / name for name in ("a", "b", "temp", "folder"))
    for made in (a, b, temp, folder):
        made.mkdir()
    secret = tmp_path / "secret"
    secret.write_text("key")
    absent = tmp_path / "absent"
    link = tmp_path / "link"
    link.symlink_to(a)

    def bind(path: Path) -> list[str]:
        return ["--bind", str(path.resolve()), str(path.resolve())]

    head = ["bwrap", "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc"]
    masks = [
        *("--tmpfs", str(folder.resolve())),
        *("--ro-bind", "/dev/null", str(secret.resolve())),
    ]
    end = ["--die-with-parent", "--new-session", "--"]
    shut = ["--unshare-pid", "--unshare-net", *end]
    opened = ["--unshare-pid", *end]
    denied = (folder, secret, absent)

    assert platform.confine(platform.Policy((link, b), denied, tmp=temp)) == [
        *head,
        *bind(a),
        *bind(b),
        *bind(temp),
        *masks,
        *shut,
    ]
    assert platform.confine(
        platform.Policy((a, b), denied, network=True, tmp=temp)
    ) == [*head, *bind(a), *bind(b), *bind(temp), *masks, *opened]
    assert platform.confine(platform.Policy((a, b), denied)) == [
        *head,
        *bind(a),
        *bind(b),
        *masks,
        *shut,
    ]
    assert platform.confine(platform.Policy((absent, b), ())) == [
        *head,
        *bind(b),
        *shut,
    ]


def test_the_sandbox_stands_on_linux_when_bwrap_applies_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(platform, "OS", "linux")
    empty = tmp_path / "empty-bin"
    empty.mkdir()

    with monkeypatch.context() as bare:
        bare.setenv("PATH", str(empty))
        assert not platform.has_sandbox()

    def bwrap(label: str, text: str) -> Path:
        (tmp_path / label).mkdir()
        return _tool(tmp_path / label, "bwrap", text)

    for label, text in (
        ("failing", "#!/bin/sh\nexit 1\n"),
        ("broken", f"#!{tmp_path / 'no-such-shell'}\n"),
    ):
        with monkeypatch.context() as tried:
            tried.setenv("PATH", str(bwrap(label, text)), prepend=os.pathsep)
            assert not platform.has_sandbox()

    with monkeypatch.context() as stalled:
        stalled.setenv("PATH", str(bwrap("slow", "#!/bin/sh\n")), prepend=os.pathsep)
        stalled.setattr(subprocess, "run", _timeout)
        assert not platform.has_sandbox()

    calls = tmp_path / "calls.txt"
    passing = bwrap("passing", f"#!/bin/sh\necho call >> {shlex.quote(str(calls))}\n")
    monkeypatch.setenv("PATH", str(passing), prepend=os.pathsep)
    assert [platform.has_sandbox() for _ in range(3)] == [True, True, True]
    assert calls.read_text() == "call\n"


def test_the_reasons_are_the_ports(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    empty = tmp_path / "empty-bin"
    empty.mkdir()

    with monkeypatch.context() as bare:
        bare.setattr(platform, "SANDBOX", "sandbox-exec-absent")
        bare.setattr(platform, "CAFFEINATE", "caffeinate-absent")
        bare.setenv("PATH", str(empty))
        assert platform.no_sandbox() == "sandbox-exec is not on PATH"
        assert platform.no_hold() == "caffeinate not on PATH"
        bare.setattr(platform, "OS", "linux")
        assert platform.no_sandbox() == "bwrap is not on PATH"
        assert platform.no_hold() == "no hold on Linux"

    failing = _tool(tmp_path, "bwrap", "#!/bin/sh\nexit 1\n")
    with monkeypatch.context() as tried:
        tried.setattr(platform, "OS", "linux")
        tried.setenv("PATH", str(failing), prepend=os.pathsep)
        assert platform.no_sandbox() == "bwrap cannot apply a sandbox here"

    caffeinate = _tool(tmp_path, "caffeinate", "#!/bin/sh\n")
    monkeypatch.setenv("PATH", str(caffeinate), prepend=os.pathsep)
    assert platform.has_hold()
    monkeypatch.setattr(platform, "OS", "linux")
    assert not platform.has_hold()


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
    empty = tmp_path / "empty-bin"
    empty.mkdir()

    with monkeypatch.context() as bare:
        bare.setenv("PATH", str(empty))
        assert platform.process(os.getpid(), "lstart") == ""

    failing = _tool(tmp_path, "ps", "#!/bin/sh\necho partial-field\nexit 1\n")
    with monkeypatch.context() as failed:
        failed.setenv("PATH", str(failing), prepend=os.pathsep)
        assert platform.process(os.getpid(), "lstart") == ""

    monkeypatch.setattr(subprocess, "run", _timeout)
    assert platform.process(os.getpid(), "lstart") == ""


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
