"""Reach the operating system through one port: every OS call a script makes.

Why: 0128-platform-port design D1 and D4.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import NamedTuple

TIMEOUT = 60
SANDBOX = "sandbox-exec"
CAFFEINATE = "caffeinate"
REFUSAL = "Operation not permitted"
DEVICES = (
    *("/dev/null", "/dev/tty", "/dev/dtracehelper", "/dev/autofs_nowait"),
    *("/dev/stdout", "/dev/stderr"),
)


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


def has_sandbox() -> bool:
    """Return whether the OS sandbox's tool is on `PATH`."""
    return shutil.which(SANDBOX) is not None


def confine(policy: Policy) -> list[str]:
    """Return the prefix that runs a command under `policy`.

    The tool's full path, since a caller's own `env` may hold another `PATH`.
    """
    return [shutil.which(SANDBOX) or SANDBOX, "-p", profile(policy)]


def refused(text: str) -> bool:
    """Return whether `text` holds the OS sandbox's refusal."""
    return REFUSAL in text


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
    """Return whether the awake hold's tool is on `PATH`."""
    return shutil.which(CAFFEINATE) is not None


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
