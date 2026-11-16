"""Reach the operating system through one port: every OS call a script makes.

Why: 0128-platform-port design D1 and D4.
"""

import functools
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

TIMEOUT = 60
SANDBOX = "sandbox-exec"
BWRAP = "bwrap"
PRIVATE = ("/run", "/tmp")  # noqa: S108
RESOLVER = "/etc/resolv.conf"
CAFFEINATE = "caffeinate"
REFUSALS = {"macos": "Operation not permitted", "linux": "Read-only file system"}
DEVICES = (
    *("/dev/null", "/dev/tty", "/dev/dtracehelper", "/dev/autofs_nowait"),
    *("/dev/stdout", "/dev/stderr"),
)
MARKS = (
    *(".bash_profile", ".bashrc", ".claude", ".gitconfig", ".gitmodules"),
    *(".idea", ".mcp.json", ".profile", ".ripgreprc", ".vscode"),
    *(".zprofile", ".zshrc"),
)


def side(system: str) -> str:
    """Return the port's side for an OS name: `linux`, else `macos`.

    e.g. "linux2" → "linux", "darwin" → "macos"
    Why: 0131-linux-runner design D7.
    """
    return "linux" if system.startswith("linux") else "macos"


OS = side(sys.platform)


class Policy(NamedTuple):
    """What a confined command may write, may not touch, and may reach."""

    writes: tuple[Path, ...]  # writable roots, in order
    denied: tuple[Path, ...]  # paths neither read nor written
    network: bool = False  # True leaves the network open
    tmp: Path | None = None  # the command's temporary folder: writable, after `writes`


def profile(policy: Policy) -> str:
    """Return the Seatbelt profile that renders `policy`.

    Why: 0107-sandbox-runner D1; 0121-ui-prepare D3; 0128-platform-port D3 and D11.
    """

    def quoted(path: Path) -> str:
        escaped = str(path.resolve()).replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    roots = policy.writes if policy.tmp is None else (*policy.writes, policy.tmp)
    writes = " ".join(f"(subpath {quoted(root)})" for root in roots)
    devices = " ".join(f'(literal "{device}")' for device in DEVICES)
    denied = " ".join(f"(subpath {quoted(path)})" for path in policy.denied)
    # A later rule beats an earlier one, so the denied paths stay denied inside a root.
    lines = (
        "(version 1)",
        "(allow default)",
        "(deny file-write*)",
        f"(allow file-write* {writes} {devices})",
        "(deny signal)",
        "(allow signal (target same-sandbox))",
        f"(deny file-read* file-write* {denied})",
    )
    return "\n".join(lines if policy.network else (*lines, "(deny network*)"))


def _bwrap(policy: Policy, tool: str) -> list[str]:
    """Return the `bwrap` prefix that renders `policy`; the caller appends the command.

    Why: 0131-linux-runner design D3 and D21.
    """
    named = policy.writes if policy.tmp is None else (*policy.writes, policy.tmp)
    roots = [root.resolve() for root in named]
    private = [
        folder
        for folder in (Path(name).resolve() for name in PRIVATE)
        if folder.is_dir() and folder not in roots
    ]
    resolver = Path(RESOLVER).resolve()
    hidden = resolver.is_file() and any(map(resolver.is_relative_to, private))
    command = [tool, "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc"]
    for folder in private:
        command += ["--tmpfs", str(folder)]
    if policy.network and hidden:
        command += ["--ro-bind", str(resolver), str(resolver)]
    for root in roots:
        if root.exists():
            command += ["--bind", str(root), str(root)]
    for path in (path.resolve() for path in policy.denied):
        if path.is_dir():
            command += ["--tmpfs", str(path)]
        elif path.exists():
            command += ["--ro-bind", "/dev/null", str(path)]
    for folder in private:
        command += ["--remount-ro", str(folder)]
    shut = [] if policy.network else ["--unshare-net"]
    command += ["--unshare-pid", *shut, "--die-with-parent", "--new-session", "--"]
    return command


@functools.cache
def _applies(tool: str) -> bool:
    """Return whether `tool` applies an empty `bwrap` sandbox here; probed once a path.

    Why: 0131-linux-runner design D8.
    """
    try:
        done = subprocess.run(
            [*_bwrap(Policy((), ()), tool), "true"],
            capture_output=True,
            timeout=TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return done.returncode == 0


def has_sandbox() -> bool:
    """Return whether the OS sandbox stands here.

    On macOS `sandbox-exec` is on `PATH`; on Linux a `bwrap` there applies one.
    Why: 0131-linux-runner design D8.
    """
    if OS == "linux":
        tool = shutil.which(BWRAP)
        return tool is not None and _applies(tool)
    return shutil.which(SANDBOX) is not None


def no_sandbox() -> str:
    """Return why the OS sandbox does not stand here, as a stop names it.

    e.g. on Linux with no `bwrap` → "bwrap is not on PATH"
    Why: 0131-linux-runner design D8.
    """
    if OS == "linux":
        if shutil.which(BWRAP) is None:
            return "bwrap is not on PATH"
        return "bwrap cannot apply a sandbox here"
    return "sandbox-exec is not on PATH"


def confine(policy: Policy) -> list[str]:
    """Return the prefix that runs a command under `policy`.

    The tool's full path, since a caller's own `env` may hold another `PATH`.
    """
    if OS == "linux":
        return _bwrap(policy, shutil.which(BWRAP) or BWRAP)
    return [shutil.which(SANDBOX) or SANDBOX, "-p", profile(policy)]


def refused(text: str) -> bool:
    """Return whether `text` holds the OS sandbox's refusal on this side.

    Why: 0131-linux-runner design D9.
    """
    return REFUSALS[OS] in text


def arch() -> str:
    """Return the host's native architecture, read past a translated process.

    e.g. an `x86_64` Python under Rosetta on Apple silicon → "arm64"
    Why: 0057-run-fixes design D1.
    """
    try:
        done = subprocess.run(
            ["sysctl", "-n", "hw.optional.arm64"],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired):
        return os.uname().machine
    return "arm64" if done.stdout.strip() == "1" else os.uname().machine


def process(pid: int, field: str) -> str:
    """Return the `ps` field for `pid`, or "" when it cannot.

    e.g. `process(pid, "lstart")` → "Mon Nov 16 14:35:00 2026"
    """
    try:
        done = subprocess.run(
            ["ps", "-o", f"{field}=", "-p", str(pid)],
            capture_output=True,
            encoding="utf-8",
            env={**os.environ, "LC_ALL": "C", "TZ": "UTC0"},
            errors="replace",
            timeout=TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return done.stdout.strip() if done.returncode == 0 else ""


def has_hold() -> bool:
    """Return whether the awake hold's tool is on `PATH`; never on Linux.

    Why: 0131-linux-runner design D4.
    """
    return OS != "linux" and shutil.which(CAFFEINATE) is not None


def no_hold() -> str:
    """Return why the machine is not held awake, as the `awake:` line names it.

    e.g. on Linux → "no hold on Linux"
    Why: 0131-linux-runner design D4.
    """
    return "no hold on Linux" if OS == "linux" else "caffeinate not on PATH"


def hold_awake(pid: int, seconds: int | None = None) -> subprocess.Popen[bytes]:
    """Hold the machine awake until `pid` exits, or `seconds` pass; return the hold.

    It runs in a session of its own, its streams closed.
    """
    bound = [] if seconds is None else ["-t", str(seconds)]
    return subprocess.Popen(
        [shutil.which(CAFFEINATE) or CAFFEINATE, "-is", *bound, "-w", str(pid)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def marks() -> tuple[str, ...]:
    """Return the names Claude Code's sandbox mounts into a worktree on this side.

    e.g. on macOS → ()
    Why: 0131-linux-runner design D2.
    """
    return MARKS if OS == "linux" else ()
