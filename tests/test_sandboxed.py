"""`sandboxed()` under a fake `sandbox-exec` or `bwrap`, and the real OS sandbox.

The real one runs where it nests.
Why: 0107-sandbox-runner design D5, 0131-linux-runner design D7.
"""

import contextlib
import io
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from conduct_load import conduct as _conduct
from mflib import platform

_DENIAL = (
    "sandboxed: denied — the OS sandbox refused a call:"
    " writes stay in the trees, no network"
)
_DUMP = (
    "import json, os, sys;"
    " print(json.dumps({'env': dict(os.environ), 'cwd': os.getcwd(),"
    " 'stdin': sys.stdin.read()}))"
)


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

    profile = platform.profile(conduct["_policy"]([link, quoted], home))

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
    policy = _conduct()["_policy"]
    home = tmp_path / "home"
    trees = [tmp_path]

    closed = platform.profile(policy(trees, home))
    assert platform.profile(policy(trees, home, network=False)) == closed
    assert "(deny network*)" in closed.splitlines()

    opened = platform.profile(policy(trees, home, network=True))
    assert "network" not in opened
    assert opened.splitlines() == closed.splitlines()[:-1]
    assert opened.splitlines()[-1].startswith("(deny file-read* file-write* ")


_CLOSED_PROFILE = (
    "(version 1)\n"
    "(allow default)\n"
    "(deny file-write*)\n"
    '(allow file-write* (subpath "{a}") (subpath "{b}")'
    ' (literal "/dev/null") (literal "/dev/tty") (literal "/dev/dtracehelper")'
    ' (literal "/dev/autofs_nowait") (literal "/dev/stdout")'
    ' (literal "/dev/stderr"))\n'
    "(deny signal)\n"
    "(allow signal (target same-sandbox))\n"
    '(deny file-read* file-write* (subpath "{home}/.ssh") (subpath "{home}/.aws")'
    ' (subpath "{home}/.config/gh") (subpath "{home}/.netrc")'
    ' (subpath "{home}/.gnupg") (subpath "{home}/.kube")'
    ' (subpath "{home}/.docker/config.json") (subpath "{home}/.git-credentials")'
    ' (subpath "{home}/.config/git/credentials") (subpath "{home}/.npmrc")'
    ' (subpath "{home}/.pypirc") (subpath "{home}/.codex/auth.json")'
    ' (subpath "{home}/.claude/.credentials.json"))\n'
    "(deny network*)"
)
_OPEN_PROFILE = (
    "(version 1)\n"
    "(allow default)\n"
    "(deny file-write*)\n"
    '(allow file-write* (subpath "{a}") (subpath "{b}")'
    ' (literal "/dev/null") (literal "/dev/tty") (literal "/dev/dtracehelper")'
    ' (literal "/dev/autofs_nowait") (literal "/dev/stdout")'
    ' (literal "/dev/stderr"))\n'
    "(deny signal)\n"
    "(allow signal (target same-sandbox))\n"
    '(deny file-read* file-write* (subpath "{home}/.ssh") (subpath "{home}/.aws")'
    ' (subpath "{home}/.config/gh") (subpath "{home}/.netrc")'
    ' (subpath "{home}/.gnupg") (subpath "{home}/.kube")'
    ' (subpath "{home}/.docker/config.json") (subpath "{home}/.git-credentials")'
    ' (subpath "{home}/.config/git/credentials") (subpath "{home}/.npmrc")'
    ' (subpath "{home}/.pypirc") (subpath "{home}/.codex/auth.json")'
    ' (subpath "{home}/.claude/.credentials.json"))'
)


def test_the_profile_text_is_held_byte_for_byte(tmp_path: Path) -> None:
    policy = _conduct()["_policy"]
    a, b = _trees(tmp_path)
    home = tmp_path / "home"
    paths = {"a": a, "b": b, "home": home.resolve()}

    assert platform.profile(policy([a, b], home)) == _CLOSED_PROFILE.format(**paths)
    assert platform.profile(policy([a, b], home, network=True)) == (
        _OPEN_PROFILE.format(**paths)
    )


def test_the_profile_denies_a_signal_outside_the_sandbox(tmp_path: Path) -> None:
    policy = _conduct()["_policy"]
    home = tmp_path / "home"

    for network in (False, True):
        lines = platform.profile(policy([tmp_path], home, network=network)).splitlines()
        allow = next(
            index
            for index, line in enumerate(lines)
            if line.startswith("(allow file-write* ")
        )
        assert lines[allow + 1 : allow + 3] == [
            "(deny signal)",
            "(allow signal (target same-sandbox))",
        ]
        assert lines[allow + 3].startswith("(deny file-read* file-write* ")


def test_the_deny_lists_are_literals() -> None:
    conduct = _conduct()

    assert conduct["SECRETS"] == (
        "~/.ssh",
        "~/.aws",
        "~/.config/gh",
        "~/.netrc",
        "~/.gnupg",
        "~/.kube",
        "~/.docker/config.json",
        "~/.git-credentials",
        "~/.config/git/credentials",
        "~/.npmrc",
        "~/.pypirc",
        "~/.codex/auth.json",
        "~/.claude/.credentials.json",
    )
    assert conduct["TOKENS"] == (
        "GITHUB_TOKEN",
        "GH_TOKEN",
        "NPM_TOKEN",
        "NODE_AUTH_TOKEN",
        "UV_PUBLISH_TOKEN",
        "TWINE_PASSWORD",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "ANTHROPIC_API_KEY",
        "CLAUDE_CODE_OAUTH_TOKEN",
        "OPENAI_API_KEY",
    )
    assert conduct["NETWORK"] == ("pypi.org", "files.pythonhosted.org")
    assert conduct["HOOKS_OFF"] == (
        "GIT_CONFIG_COUNT=2",
        "GIT_CONFIG_KEY_0=core.hooksPath",
        "GIT_CONFIG_VALUE_0=/dev/null",
        "GIT_CONFIG_KEY_1=core.fsmonitor",
        "GIT_CONFIG_VALUE_1=false",
    )


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
    assert fake_sandbox_exec.read_text() == platform.profile(
        conduct["_policy"]([*trees, Path(env["TMPDIR"])], Path.home())
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


def test_a_sandboxed_command_has_npm_offline_with_scripts_off(
    tmp_path: Path,
    fake_sandbox_exec: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    conduct = _conduct()
    trees = _trees(tmp_path)
    monkeypatch.setenv("npm_config_offline", "false")
    monkeypatch.setenv("npm_config_ignore_scripts", "false")
    monkeypatch.setenv("npm_config_cache", str(tmp_path / "other-cache"))

    code = conduct["sandboxed"](_python(_DUMP), trees[1], trees)

    env = json.loads(capsys.readouterr().out)["env"]
    assert code == 0
    assert env["npm_config_cache"] == str(trees[0] / ".minions" / "npm-cache")
    assert env["npm_config_offline"] == "true"
    assert env["npm_config_ignore_scripts"] == "true"


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


def test_a_command_runs_under_bwrap_on_linux(
    tmp_path: Path,
    fake_bwrap: Path,
    isolated_home: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(platform, "OS", "linux")
    trees = _trees(tmp_path)
    private = tmp_path / "private"
    private.mkdir()
    monkeypatch.setattr(platform, "PRIVATE", (str(private),))
    keys = isolated_home / ".ssh"
    keys.mkdir()
    command = _python("import os; print(os.environ['TMPDIR'])")

    code = _conduct()["sandboxed"](command, trees[0], trees)

    temp = str(Path(capsys.readouterr().out.strip()).resolve())
    assert code == 0
    assert fake_bwrap.read_text().splitlines() == [
        *("--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc"),
        *("--tmpfs", str(private.resolve())),
        *("--bind", str(trees[0]), str(trees[0])),
        *("--bind", str(trees[1]), str(trees[1])),
        *("--bind", temp, temp),
        *("--tmpfs", str(keys.resolve())),
        *("--remount-ro", str(private.resolve())),
        *("--unshare-pid", "--unshare-net", "--die-with-parent", "--new-session"),
        "--",
        *command,
    ]


def test_a_linux_denial_gets_the_line(
    tmp_path: Path,
    fake_bwrap: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(platform, "OS", "linux")
    trees = _trees(tmp_path)
    sandboxed = _conduct()["sandboxed"]

    for text, denied in (
        ("touch: x: Read-only file system", True),
        ("touch: x: Operation not permitted", False),
    ):
        command = _python(f"import sys; print({text!r}, file=sys.stderr); sys.exit(1)")
        assert sandboxed(command, trees[0], trees) == 1
        seen = capsys.readouterr()
        assert text in seen.out
        assert (_DENIAL in seen.err) is denied


def test_no_bwrap_stops_with_2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(platform, "OS", "linux")
    conduct = _conduct()
    trees = _trees(tmp_path)
    marker = tmp_path / "ran.txt"
    empty = tmp_path / "empty-bin"
    empty.mkdir()
    failing = tmp_path / "failing-bin"
    failing.mkdir()
    (failing / "bwrap").write_text("#!/bin/sh\nexit 1\n")
    (failing / "bwrap").chmod(0o755)

    for folder, why in ((empty, "is not on PATH"), (failing, "cannot apply")):
        monkeypatch.setenv("PATH", str(folder))
        with pytest.raises(conduct["Stop"]) as stop:
            conduct["sandboxed"](
                _python(f"open({str(marker)!r}, 'w').close()"), trees[0], trees
            )
        assert stop.value.code == 2
        assert "no OS sandbox: bwrap" in str(stop.value)
        assert why in str(stop.value)
        assert not marker.exists()


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


def _gone(pid: int, seconds: float = 5) -> bool:
    for _ in range(int(seconds / 0.05)):
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
    assert fake_sandbox_exec.read_text() == platform.profile(
        conduct["_policy"]([repo, Path(temp)], Path.home())
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


def _require_sandbox(host: str, tmp_path: Path) -> None:
    """Pass where the host's real OS sandbox applies; else fail or skip.

    `MF_REQUIRE_SANDBOX` set fails it: CI's macOS and Linux jobs.
    Why: 0128-platform-port D12, 0131-linux-runner design D5 and D21.
    """
    if host == "linux":
        stands, reason = platform.has_sandbox(), "bwrap cannot apply a sandbox here"
        folders = [Path(name).resolve() for name in platform.PRIVATE]
        if stands and any(map(tmp_path.resolve().is_relative_to, folders)):
            stands = False
            reason = "the test folder is in a private folder: set TMPDIR outside /tmp"
    else:
        stands, reason = _seatbelt(), "sandbox-exec cannot apply a profile here"
    if stands:
        return
    if os.environ.get("MF_REQUIRE_SANDBOX"):
        pytest.fail(reason)
    pytest.skip(reason)


def _clear_coverage(monkeypatch: pytest.MonkeyPatch) -> None:
    """Drop the variables that start coverage in a child of the test.

    Why: 0133-host-free-tests design D1.
    """
    for name in ("COVERAGE_PROCESS_START", "COVERAGE_PROCESS_CONFIG"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def real_sandbox(
    host: str, tmp_path: Path, macos_side: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run the test on the host's side; skip or fail it as `_require_sandbox` says.

    Why: 0131-linux-runner design D7.
    """
    monkeypatch.setattr(platform, "OS", host)
    _clear_coverage(monkeypatch)
    _require_sandbox(host, tmp_path)


@pytest.mark.parametrize("name", ["COVERAGE_PROCESS_START", "COVERAGE_PROCESS_CONFIG"])
def test_a_real_sandbox_child_starts_no_coverage(
    name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(name, "coveragerc")
    monkeypatch.setenv("COVERAGE_FILE", "data")

    _clear_coverage(monkeypatch)

    assert name not in os.environ
    assert "COVERAGE_FILE" in os.environ


def test_a_required_sandbox_that_cannot_apply_fails_and_else_skips(
    tmp_path: Path, fake_sandbox_exec: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MF_REQUIRE_SANDBOX", "1")
    _require_sandbox("macos", tmp_path)

    empty = tmp_path / "empty-bin"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))
    outcomes = (pytest.fail.Exception, pytest.skip.Exception)
    with pytest.raises(outcomes, match="cannot apply a profile") as required:
        _require_sandbox("macos", tmp_path)
    assert required.type is pytest.fail.Exception
    monkeypatch.delenv("MF_REQUIRE_SANDBOX")
    with pytest.raises(outcomes, match="cannot apply a profile") as optional:
        _require_sandbox("macos", tmp_path)
    assert optional.type is pytest.skip.Exception

    for name, code in (("failing", 1), ("passing", 0)):
        (tmp_path / f"{name}-bin").mkdir()
        (tmp_path / f"{name}-bin" / "bwrap").write_text(f"#!/bin/sh\nexit {code}\n")
        (tmp_path / f"{name}-bin" / "bwrap").chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path / "failing-bin"))
    monkeypatch.setenv("MF_REQUIRE_SANDBOX", "1")
    monkeypatch.setattr(platform, "OS", "linux")
    monkeypatch.setattr(platform, "PRIVATE", ())
    with pytest.raises(outcomes, match="bwrap cannot apply a sandbox") as required:
        _require_sandbox("linux", tmp_path)
    assert required.type is pytest.fail.Exception
    monkeypatch.delenv("MF_REQUIRE_SANDBOX")
    monkeypatch.setattr(platform, "OS", "linux")
    monkeypatch.setattr(platform, "PRIVATE", ())
    with pytest.raises(outcomes, match="bwrap cannot apply a sandbox") as optional:
        _require_sandbox("linux", tmp_path)
    assert optional.type is pytest.skip.Exception
    monkeypatch.setenv("PATH", str(tmp_path / "passing-bin"))
    monkeypatch.setattr(platform, "OS", "linux")
    monkeypatch.setattr(platform, "PRIVATE", ())
    _require_sandbox("linux", tmp_path)

    monkeypatch.setattr(platform, "PRIVATE", (str(tmp_path.parent),))
    monkeypatch.setenv("MF_REQUIRE_SANDBOX", "1")
    with pytest.raises(outcomes, match="in a private folder") as required:
        _require_sandbox("linux", tmp_path)
    assert required.type is pytest.fail.Exception
    monkeypatch.delenv("MF_REQUIRE_SANDBOX")
    with pytest.raises(outcomes, match="in a private folder") as optional:
        _require_sandbox("linux", tmp_path)
    assert optional.type is pytest.skip.Exception


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
    netrc = isolated_home / ".netrc"
    netrc.write_text("machine x")
    plain = isolated_home / "notes.txt"
    plain.write_text("note")

    def read(path: Path) -> tuple[int, str]:
        out = io.StringIO()
        command = _python(f"print(open({str(path.resolve())!r}).read())")
        return _conduct()["sandboxed"](command, trees[0], trees, out), out.getvalue()

    assert read(plain) == (0, "note\n")
    code, seen = read(secret)
    assert code != 0
    for text in (seen, read(netrc)[1]):
        assert "key" not in text
        assert "machine" not in text


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


_UNIX_CONNECT = (
    "import socket, sys;"
    " client = socket.socket(socket.AF_UNIX); client.settimeout(2);"
    " client.connect(sys.argv[1])"
)


@contextlib.contextmanager
def _host_socket() -> Iterator[tuple[socket.socket, str]]:
    """Yield a Unix listener the host holds under `/tmp`, and its path."""
    folder = tempfile.mkdtemp(dir="/tmp")
    path = os.path.join(folder, "host.sock")
    try:
        with socket.socket(socket.AF_UNIX) as listener:
            listener.bind(path)
            listener.listen()
            listener.settimeout(1)
            yield listener, path
    finally:
        shutil.rmtree(folder)


def test_a_host_socket_is_out_of_reach(tmp_path: Path, real_sandbox: None) -> None:
    trees = _trees(tmp_path)
    out = io.StringIO()
    with _host_socket() as (listener, path):
        code = _conduct()["sandboxed"](
            [*_python(_UNIX_CONNECT), path], trees[0], trees, out
        )

        assert code != 0
        with pytest.raises(TimeoutError):
            listener.accept()


def test_the_private_folders_are_the_commands_own(
    tmp_path: Path, real_sandbox: None
) -> None:
    if platform.OS == "macos":
        pytest.skip("the private folders are bubblewrap's")
    trees = _trees(tmp_path)
    sandboxed = _conduct()["sandboxed"]

    out = io.StringIO()
    listing = _python("import os; print(os.listdir('/run'))")
    assert sandboxed(listing, trees[0], trees, out) == 0
    assert out.getvalue() == "[]\n"
    out = io.StringIO()
    write = f"open('/tmp/mf-{tmp_path.name}', 'w').close()"
    assert sandboxed(_python(write), trees[0], trees, out) != 0
    assert "Read-only file system" in out.getvalue()

    prefix = platform.confine(platform.Policy((trees[0],), (), network=True))
    read = "print(open('/etc/resolv.conf').read(), end='')"
    shown = subprocess.run(
        [*prefix, *_python(read)], capture_output=True, text=True, timeout=60
    )
    assert shown.returncode == 0
    assert shown.stdout == Path("/etc/resolv.conf").read_text()
    with _host_socket() as (listener, path):
        reached = subprocess.run(
            [*prefix, *_python(_UNIX_CONNECT), path], capture_output=True, timeout=60
        )
        assert reached.returncode != 0
        with pytest.raises(TimeoutError):
            listener.accept()


_SIGNAL_OUT = (
    "import os, signal, sys\n"
    "for sig in (signal.SIGTERM, 0):\n"
    "    try:\n"
    "        os.kill(int(sys.argv[1]), sig)\n"
    "    except OSError as error:\n"
    "        print(int(sig), error.strerror)\n"
    "    else:\n"
    "        print(int(sig), 'sent')\n"
)
_SIGNAL_CHILD = (
    "import signal, subprocess, sys;"
    " child = subprocess.Popen(['sleep', '60']);"
    " child.send_signal(signal.SIGTERM);"
    " sys.exit(0 if child.wait(timeout=10) == -signal.SIGTERM else 1)"
)
_STARTER = (
    "import subprocess;"
    " quiet = subprocess.DEVNULL;"
    " sleeper = subprocess.Popen(['sleep', '60'], start_new_session=True,"
    " stdin=quiet, stdout=quiet, stderr=quiet);"
    " print(sleeper.pid, flush=True)"
)
# The PID is the sandbox's own; on Linux the host's numbers differ, so it is read here.
_SIGNALLER = (
    "import os, signal, sys, time\n"
    "pid = int(sys.argv[1])\n"
    "try:\n"
    "    os.kill(pid, signal.SIGTERM)\n"
    "    for _ in range(200):\n"
    "        os.kill(pid, 0)\n"
    "        time.sleep(0.05)\n"
    "except ProcessLookupError:\n"
    "    print('gone', flush=True)\n"
    "else:\n"
    "    os.kill(pid, signal.SIGKILL)\n"
    "    sys.exit('alive')\n"
)
_SIBLINGS = (
    "import subprocess, sys;"
    " first = subprocess.run([sys.executable, '-c', sys.argv[1]],"
    " capture_output=True, text=True, check=True);"
    " print(first.stdout, end='', flush=True);"
    " subprocess.run([sys.executable, '-c', sys.argv[2], first.stdout.strip()],"
    " check=True)"
)


def test_a_signal_to_a_process_outside_is_denied(
    tmp_path: Path, real_sandbox: None
) -> None:
    trees = _trees(tmp_path)
    outside = subprocess.Popen(["sleep", "60"])
    out = io.StringIO()
    error = {"macos": "Operation not permitted", "linux": "No such process"}
    try:
        code = _conduct()["sandboxed"](
            [*_python(_SIGNAL_OUT), str(outside.pid)], trees[0], trees, out
        )

        assert code == 0
        assert out.getvalue().splitlines() == [
            f"{int(signal.SIGTERM)} {error[platform.OS]}",
            f"0 {error[platform.OS]}",
        ]
        assert outside.poll() is None
    finally:
        outside.kill()
        outside.wait()


def test_a_signal_to_the_commands_own_child_is_delivered(
    tmp_path: Path, real_sandbox: None
) -> None:
    trees = _trees(tmp_path)

    assert _conduct()["sandboxed"](_python(_SIGNAL_CHILD), trees[0], trees) == 0


def test_a_signal_between_siblings_is_delivered(
    tmp_path: Path, real_sandbox: None
) -> None:
    trees = _trees(tmp_path)
    out = io.StringIO()

    code = _conduct()["sandboxed"](
        [*_python(_SIBLINGS), _STARTER, _SIGNALLER], trees[0], trees, out
    )

    assert code == 0
    assert out.getvalue().splitlines()[1:] == ["gone"]


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
