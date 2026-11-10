"""Hold every test's home, global git config and XDG folders under its own `tmp_path`.

Why: the suite runs on every core, so no test may share the operator's home or another
test's state — 0065-gate-hardening design D1.
"""

import os
import shlex
from pathlib import Path

import pytest

ISOLATED = {
    "XDG_CONFIG_HOME": ".config",
    "XDG_DATA_HOME": ".local/share",
    "XDG_CACHE_HOME": ".cache",
}


@pytest.fixture(autouse=True)
def isolated_home(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path_factory: pytest.TempPathFactory,
) -> Path:
    """Return the home folder this test runs with, under its `tmp_path`."""
    home = tmp_path / "isolated-home"
    home.mkdir()
    # Why: 0111-sandbox-tmp design D1
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path_factory.getbasetemp()))
    monkeypatch.setenv("TMPDIR", str(tmp_path_factory.mktemp("tmp")))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(home / ".gitconfig"))
    for name, folder in ISOLATED.items():
        monkeypatch.setenv(name, str(home / folder))
    # Why: 0100-worker-diet design D2 — `_plugins_off` reads the operator's otherwise.
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    return home


@pytest.fixture
def fake_sandbox_exec(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Put a fake `sandbox-exec` first on `PATH`; return the file its profile lands in.

    The fake writes its profile argument, then runs the rest of its arguments
    unconfined: a nested Seatbelt cannot apply one. Why: 0108-converge-script C5.
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
