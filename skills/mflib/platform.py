"""Reach the operating system through one port: every OS call a script makes.

Why: 0128-platform-port design D1 and D4.
"""

import os
import subprocess

TIMEOUT = 60


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
