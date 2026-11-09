"""`sandboxed()` under Seatbelt: a fake `sandbox-exec`, and the real one where it nests.

Why: 0107-sandbox-runner design D5.
"""

import json
import os
import runpy
import shlex
import shutil
import signal
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

_SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "mf-ship"
    / "scripts"
    / "conduct.py"
)
_DENIAL = (
    "sandboxed: denied — the OS sandbox refused a call:"
    " writes stay in the trees, no network"
)
_DUMP = (
    "import json, os, sys;"
    " print(json.dumps({'env': dict(os.environ), 'cwd': os.getcwd(),"
    " 'stdin': sys.stdin.read()}))"
)


def _conduct() -> dict[str, Any]:
    return runpy.run_path(str(_SCRIPT))


def _python(code: str) -> list[str]:
    return [sys.executable, "-c", code]


@pytest.fixture
def fake_sandbox(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Put a fake `sandbox-exec` first on `PATH`; return the file its profile lands in.

    The fake writes its profile argument, then runs the rest of its arguments.
    """
    folder = tmp_path / "fake-bin"
    folder.mkdir()
    profile = tmp_path / "profile.sb"
    fake = folder / "sandbox-exec"
    target = shlex.quote(str(profile))
    fake.write_text(f'#!/bin/sh\nprintf \'%s\' "$2" > {target}\nshift 2\nexec "$@"\n')
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", str(folder), prepend=os.pathsep)
    return profile


def _trees(tmp_path: Path) -> list[Path]:
    primary = tmp_path / "primary"
    version = tmp_path / "version"
    primary.mkdir()
    version.mkdir()
    return [primary.resolve(), version.resolve()]


def test_the_profile_confines_writes_reads_and_network(tmp_path: Path) -> None:
    conduct = _conduct()
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real)
    quoted = tmp_path / 'a"b\\c'
    home = tmp_path / "home"

    profile = conduct["_profile"]([link, quoted], home)

    lines = profile.splitlines()
    assert lines[:3] == ["(version 1)", "(allow default)", "(deny file-write*)"]
    assert lines[-1] == "(deny network*)"
    allow = next(line for line in lines if line.startswith("(allow file-write*"))
    assert f'(subpath "{real.resolve()}")' in allow
    assert str(link) not in profile
    escaped = str(quoted.resolve()).replace("\\", "\\\\").replace('"', '\\"')
    assert f'(subpath "{escaped}")' in allow
    assert allow.index(str(real.resolve())) < allow.index(escaped)
    for device in (
        *("/dev/null", "/dev/tty", "/dev/dtracehelper", "/dev/autofs_nowait"),
        *("/dev/stdout", "/dev/stderr"),
    ):
        assert f'(literal "{device}")' in allow
    deny = next(line for line in lines if line.startswith("(deny file-read*"))
    assert deny.startswith("(deny file-read* file-write* ")
    for secret in conduct["SECRETS"]:
        assert f'(subpath "{(home / secret.removeprefix("~/")).resolve()}")' in deny
    assert "~" not in deny
    assert lines.index(allow) < lines.index(deny) < len(lines) - 1


def test_a_command_runs_under_sandbox_exec_with_a_scrubbed_environment(
    tmp_path: Path,
    fake_sandbox: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    conduct = _conduct()
    trees = _trees(tmp_path)
    cwd = trees[1]
    for name in conduct["TOKENS"]:
        monkeypatch.setenv(name, "secret")
    monkeypatch.setenv("VIRTUAL_ENV", "/somewhere/venv")
    monkeypatch.setenv("KEPT", "yes")

    code = conduct["sandboxed"](_python(_DUMP), cwd, trees)

    seen = json.loads(capsys.readouterr().out)
    env = seen["env"]
    assert code == 0
    assert Path(seen["cwd"]).resolve() == cwd
    assert seen["stdin"] == ""
    assert not set(conduct["TOKENS"]) & set(env)
    assert "VIRTUAL_ENV" not in env
    assert env["KEPT"] == "yes"
    assert env["UV_OFFLINE"] == "1"
    assert env["UV_CACHE_DIR"] == str(trees[0] / ".minions" / "uv-cache")
    assert env["TMPDIR"] == str(trees[0] / ".minions" / "tmp")
    assert (trees[0] / ".minions" / "tmp").is_dir()
    for pair in conduct["HOOKS_OFF"]:
        key, value = pair.split("=", 1)
        assert env[key] == value
    assert fake_sandbox.read_text() == conduct["_profile"](trees, Path.home())

    outside = tmp_path / "outside"
    outside.mkdir()
    planted = tmp_path / "planted"
    planted.mkdir()
    (planted / ".minions").symlink_to(outside)
    with pytest.raises(conduct["Stop"]) as stop:
        conduct["sandboxed"](_python("pass"), planted, [planted.resolve()])
    assert stop.value.code == 2
    assert not (outside / "tmp").exists()


@pytest.mark.parametrize(
    ("code", "exit_code"),
    [
        ("pass", 0),
        ("sys.exit(3)", 3),
        ("os.kill(os.getpid(), signal.SIGKILL)", 128 + signal.SIGKILL),
        ("os.kill(os.getpid(), signal.SIGTERM)", 128 + signal.SIGTERM),
    ],
)
def test_the_exit_passes_through(
    tmp_path: Path, fake_sandbox: Path, code: str, exit_code: int
) -> None:
    trees = _trees(tmp_path)
    command = _python(f"import os, signal, sys; {code}")

    assert _conduct()["sandboxed"](command, trees[0], trees) == exit_code


def test_no_sandbox_exec_stops_with_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    conduct = _conduct()
    trees = _trees(tmp_path)
    empty = tmp_path / "empty-bin"
    empty.mkdir()
    marker = tmp_path / "ran.txt"
    monkeypatch.setenv("PATH", str(empty))

    with pytest.raises(conduct["Stop"]) as stop:
        conduct["sandboxed"](
            _python(f"open({str(marker)!r}, 'w').close()"), trees[0], trees
        )

    assert stop.value.code == 2
    assert "no OS sandbox" in str(stop.value)
    assert not marker.exists()


@pytest.mark.parametrize(
    ("exit_code", "text", "denied"),
    [
        (1, "touch: x: Operation not permitted", True),
        (0, "touch: x: Operation not permitted", False),
        (1, "an ordinary failure", False),
    ],
)
def test_a_denial_in_the_output_gets_a_line(
    tmp_path: Path,
    fake_sandbox: Path,
    capsys: pytest.CaptureFixture[str],
    exit_code: int,
    text: str,
    denied: bool,
) -> None:
    trees = _trees(tmp_path)
    command = _python(
        f"import sys; print({text!r}, file=sys.stderr); sys.exit({exit_code})"
    )

    code = _conduct()["sandboxed"](command, trees[0], trees)

    seen = capsys.readouterr()
    assert code == exit_code
    assert text in seen.out
    assert (_DENIAL in seen.err) is denied


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    identity = ["-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=0"]
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(
        ["git", *identity, "commit", "-q", "--allow-empty", "-m", "base"],
        cwd=repo,
        check=True,
    )
    return repo.resolve()


def test_the_command_runs_a_command_in_the_cwd(
    tmp_path: Path,
    fake_sandbox: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    conduct = _conduct()
    repo = _repo(tmp_path)
    monkeypatch.chdir(repo)

    shown = conduct["main"](
        ["sandboxed", "--", *_python("import os; print(os.getcwd())")]
    )

    seen = capsys.readouterr()
    assert shown == 0
    assert Path(seen.out.strip()).resolve() == repo
    assert fake_sandbox.read_text() == conduct["_profile"]([repo], Path.home())
    assert conduct["main"](["sandboxed", "--", *_python("raise SystemExit(3)")]) == 3
    for argv in (["sandboxed"], ["sandboxed", "--"]):
        assert conduct["main"](argv) == 2
        assert "sandboxed: cannot run — no command" in capsys.readouterr().out


def test_the_command_exits_2_with_no_os_sandbox(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    conduct = _conduct()
    repo = _repo(tmp_path)
    git = shutil.which("git")
    assert git is not None
    bare = tmp_path / "git-only"
    bare.mkdir()
    (bare / "git").symlink_to(git)
    monkeypatch.chdir(repo)
    monkeypatch.setenv("PATH", str(bare))

    code = conduct["main"](["sandboxed", "--", "/usr/bin/true"])

    assert code == 2
    assert "no OS sandbox" in capsys.readouterr().out


def _seatbelt() -> bool:
    """Return whether the real `sandbox-exec` applies a trivial profile here.

    A worker's own sandbox refuses it, so a gate run there skips the tests below.
    """
    found = shutil.which("sandbox-exec")
    if found is None:
        return False
    probe = [found, "-p", "(version 1)(allow default)", "/usr/bin/true"]
    return subprocess.run(probe, capture_output=True).returncode == 0


@pytest.fixture
def real_sandbox() -> None:
    """Skip the test where the real `sandbox-exec` cannot apply a profile."""
    if not _seatbelt():
        pytest.skip("sandbox-exec cannot apply a profile here")


def test_a_write_outside_the_trees_is_denied(
    tmp_path: Path, real_sandbox: None, capsys: pytest.CaptureFixture[str]
) -> None:
    conduct = _conduct()
    trees = _trees(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()

    def write(folder: Path) -> int:
        code = f"open({str(folder / 'x')!r}, 'w').close()"
        return conduct["sandboxed"](_python(code), trees[0], trees)

    assert write(trees[1]) == 0
    assert (trees[1] / "x").is_file()
    assert write(outside) != 0
    assert not (outside / "x").exists()
    assert _DENIAL in capsys.readouterr().err


def test_a_secret_read_is_denied(
    tmp_path: Path, real_sandbox: None, isolated_home: Path
) -> None:
    trees = _trees(tmp_path)
    secret = isolated_home / ".ssh" / "id_test"
    secret.parent.mkdir()
    secret.write_text("key")
    plain = isolated_home / "notes.txt"
    plain.write_text("note")

    def read(path: Path) -> int:
        command = _python(f"print(open({str(path.resolve())!r}).read())")
        return _conduct()["sandboxed"](command, trees[0], trees)

    assert read(plain) == 0
    assert read(secret) != 0


def test_a_network_connect_is_denied(tmp_path: Path, real_sandbox: None) -> None:
    trees = _trees(tmp_path)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        listener.settimeout(1)
        address = listener.getsockname()
        socket.create_connection(address).close()
        listener.accept()[0].close()

        code = _conduct()["sandboxed"](
            _python(f"import socket; socket.create_connection({address!r}, timeout=2)"),
            trees[0],
            trees,
        )

        assert code != 0
        with pytest.raises(TimeoutError):
            listener.accept()
