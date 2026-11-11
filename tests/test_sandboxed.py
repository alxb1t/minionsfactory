"""`sandboxed()` under Seatbelt: a fake `sandbox-exec`, and the real one where it nests.

Why: 0107-sandbox-runner design D5.
"""

import io
import json
import os
import runpy
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
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


def test_a_profile_may_open_the_network(tmp_path: Path) -> None:
    profile = _conduct()["_profile"]
    home = tmp_path / "home"
    trees = [tmp_path]

    closed = profile(trees, home)
    assert profile(trees, home, network=False) == closed
    assert "(deny network*)" in closed.splitlines()

    opened = profile(trees, home, network=True)
    assert "network" not in opened
    assert opened.splitlines() == closed.splitlines()[:-1]
    assert opened.splitlines()[-1].startswith("(deny file-read* file-write* ")


def test_a_command_runs_under_sandbox_exec_with_a_scrubbed_environment(
    tmp_path: Path,
    fake_sandbox_exec: Path,
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
    temp = Path(env["TMPDIR"])
    assert temp.parent == Path(os.environ["TMPDIR"]).resolve()
    assert temp.name.startswith("mf-sandbox-")
    assert not temp.exists()
    assert not (trees[0] / ".minions" / "tmp").exists()
    for pair in conduct["HOOKS_OFF"]:
        key, value = pair.split("=", 1)
        assert env[key] == value
    assert fake_sandbox_exec.read_text() == conduct["_profile"](
        [*trees, Path(env["TMPDIR"])], Path.home()
    )

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
    tmp_path: Path, fake_sandbox_exec: Path, code: str, exit_code: int
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
    fake_sandbox_exec: Path,
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


def test_the_output_goes_to_the_file_given(
    tmp_path: Path, fake_sandbox_exec: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    trees = _trees(tmp_path)
    command = _python(
        "import sys; print('one', flush=True);"
        " print('touch: x: Operation not permitted',"
        " file=sys.stderr); sys.exit(1)"
    )
    out = io.StringIO()

    code = _conduct()["sandboxed"](command, trees[0], trees, out)

    seen = capsys.readouterr()
    assert code == 1
    assert out.getvalue().splitlines() == [
        "one",
        "touch: x: Operation not permitted",
        _DENIAL,
    ]
    assert seen.out == ""
    assert seen.err == ""
    assert _conduct()["sandboxed"](_python("print('two')"), trees[0], trees) == 0
    assert capsys.readouterr().out == "two\n"


_SPAWN = (
    "import subprocess, sys, time;"
    " child = subprocess.Popen(['sleep', '60']);"
    " open(sys.argv[1], 'w').write(str(child.pid));"
    " time.sleep(60)"
)
_DEAF = (
    "import signal, sys, time;"
    " signal.signal(signal.SIGTERM, signal.SIG_IGN);"
    " print('ready', flush=True);"
    " time.sleep(60)"
)


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def _gone(pid: int) -> bool:
    for _ in range(100):
        if not _alive(pid):
            return True
        time.sleep(0.05)
    return False


def test_a_command_past_its_deadline_is_killed_with_its_group(
    tmp_path: Path, fake_sandbox_exec: Path
) -> None:
    sandboxed = _conduct()["sandboxed"]
    trees = _trees(tmp_path)
    child = tmp_path / "child.pid"
    out = io.StringIO()

    assert sandboxed(_python("print('quick')"), trees[0], trees, out, timeout=30) == 0
    assert out.getvalue() == "quick\n"

    out = io.StringIO()
    code = sandboxed(
        [*_python(_SPAWN), str(child)], trees[0], trees, out, timeout=1, grace=30
    )

    assert code == 124
    assert out.getvalue() == "sandboxed: timed out — killed after 1 s\n"
    assert _gone(int(child.read_text()))

    out = io.StringIO()
    assert sandboxed(_python("print('x')"), trees[0], trees, out, timeout=0) == 124
    assert out.getvalue().endswith("sandboxed: timed out — killed after 0 s\n")


def test_a_command_that_ignores_sigterm_is_killed_after_the_grace(
    tmp_path: Path, fake_sandbox_exec: Path
) -> None:
    trees = _trees(tmp_path)
    out = io.StringIO()
    started = time.monotonic()

    code = _conduct()["sandboxed"](
        _python(_DEAF), trees[0], trees, out, timeout=1, grace=0.5
    )

    assert code == 124
    assert out.getvalue().splitlines() == [
        "ready",
        "sandboxed: timed out — killed after 1 s",
    ]
    assert time.monotonic() - started < 30


_ORPHAN = (
    "import subprocess, sys, time;"
    " code = 'import signal, time;"
    " signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)';"
    " child = subprocess.Popen([sys.executable, '-c', code],"
    " stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL);"
    " open(sys.argv[1], 'w').write(str(child.pid));"
    " time.sleep(60)"
)


def test_a_child_that_outlives_its_parent_is_killed_after_the_grace(
    tmp_path: Path, fake_sandbox_exec: Path
) -> None:
    trees = _trees(tmp_path)
    child = tmp_path / "orphan.pid"
    out = io.StringIO()

    code = _conduct()["sandboxed"](
        [*_python(_ORPHAN), str(child)], trees[0], trees, out, timeout=1, grace=0.5
    )

    assert code == 124
    assert _gone(int(child.read_text()))


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
    fake_sandbox_exec: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    conduct = _conduct()
    repo = _repo(tmp_path)
    monkeypatch.chdir(repo)

    shown = conduct["main"](
        [
            *("sandboxed", "--"),
            *_python("import os; print(os.getcwd()); print(os.environ['TMPDIR'])"),
        ]
    )

    seen = capsys.readouterr()
    cwd, temp = seen.out.splitlines()
    assert shown == 0
    assert Path(cwd).resolve() == repo
    assert fake_sandbox_exec.read_text() == conduct["_profile"](
        [repo, Path(temp)], Path.home()
    )
    assert conduct["main"](["sandboxed", "--", *_python("raise SystemExit(3)")]) == 3
    for argv in (["sandboxed"], ["sandboxed", "--"]):
        assert conduct["main"](argv) == 2
        assert "sandboxed: cannot run — no command" in capsys.readouterr().out


_TEMP_PROBE = (
    "import json, os, subprocess; tmp = os.environ['TMPDIR'];"
    " git = subprocess.run(['git', 'rev-parse', '--git-dir'], cwd=tmp,"
    " capture_output=True);"
    " open(os.path.join(tmp, 'x'), 'w').close();"
    " print(json.dumps({'tmp': tmp, 'git': git.returncode,"
    " 'wrote': os.path.isfile(os.path.join(tmp, 'x'))}))"
)


def test_a_command_gets_a_fresh_tmpdir_outside_every_repository(
    tmp_path: Path, fake_sandbox_exec: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    sandboxed = _conduct()["sandboxed"]
    trees = _trees(tmp_path)
    seen = []

    for _ in range(2):
        assert sandboxed(_python(_TEMP_PROBE), trees[0], trees) == 0
        seen.append(json.loads(capsys.readouterr().out))

    first, second = seen
    assert first["git"] != 0
    assert first["wrote"]
    assert not Path(first["tmp"]).exists()
    assert second["tmp"] != first["tmp"]
    assert not Path(second["tmp"]).exists()


def test_a_tmpdir_in_a_repository_runs_nothing(
    tmp_path: Path, fake_sandbox_exec: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    conduct = _conduct()
    trees = _trees(tmp_path)
    repo = _repo(tmp_path)
    marker = tmp_path / "ran.txt"
    command = _python(f"open({str(marker)!r}, 'w').close()")

    for folder in (repo, tmp_path / "missing"):
        monkeypatch.setenv("TMPDIR", str(folder))
        with pytest.raises(conduct["Stop"]) as stop:
            conduct["sandboxed"](command, trees[0], trees)
        assert stop.value.code == 2
        assert f"TMPDIR {folder}" in str(stop.value)
        assert not marker.exists()


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

    beside = (
        "import os, pathlib; tmp = pathlib.Path(os.environ['TMPDIR']);"
        " (tmp / 'in').touch(); print('in', flush=True);"
        " (tmp.parent / 'beside').touch()"
    )
    code = conduct["sandboxed"](_python(beside), trees[0], trees)
    seen = capsys.readouterr()
    assert code != 0
    assert seen.out.splitlines()[0] == "in"
    assert not (Path(os.environ["TMPDIR"]) / "beside").exists()
    assert _DENIAL in seen.err


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


@pytest.mark.parametrize("error", [ProcessLookupError, PermissionError])
def test_the_watch_ends_on_a_group_gone_or_not_its_to_signal(
    monkeypatch: pytest.MonkeyPatch, error: type[OSError]
) -> None:
    """A probe that finds the group gone, or may not signal it, ends the watch.

    Why: 0114-faster-plan-check design D5; a sandbox that refuses `killpg` covers it.
    """
    sent: list[int] = []

    def killpg(_: int, sig: int) -> None:
        sent.append(sig)
        if sig == 0:
            raise error(1, "probe")

    monkeypatch.setattr(os, "killpg", killpg)
    done, expired = threading.Event(), threading.Event()
    _conduct()["_watch"](4242, 0, 5.0, done, expired)
    assert expired.is_set()
    assert sent == [signal.SIGTERM, 0]
