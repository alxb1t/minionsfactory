"""Hold every test's home, global git config and XDG folders under its own `tmp_path`.

Why: the suite runs on every core, so no test may share the operator's home or another
test's state — 0065-gate-hardening design D1.
"""

import os
import shlex
from pathlib import Path

import pytest
from mflib import platform

HOST = platform.OS

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
    # Why: 0123-linux-ci-green design D3 — a missing identity fails here as on Linux.
    (home / ".gitconfig").write_text("[user]\n\tuseConfigOnly = true\n")
    for name, folder in ISOLATED.items():
        monkeypatch.setenv(name, str(home / folder))
    # Why: 0100-worker-diet design D2 — `_plugins_off` reads the operator's otherwise.
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    return home


@pytest.fixture(scope="session")
def host() -> str:
    """Return the host's side, read at import, before any test sets `platform.OS`."""
    return HOST


@pytest.fixture(autouse=True)
def macos_side(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run the test on the port's macOS side; a test of the Linux side sets `linux`.

    Why: 0131-linux-runner design D7.
    """
    monkeypatch.setattr(platform, "OS", "macos")


@pytest.fixture
def fake_sandbox_exec(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Put a fake `sandbox-exec` first on `PATH`; return the file its profile lands in.

    It refuses a first word but `-p`, then writes the profile and runs the rest
    unconfined (no Seatbelt nests). Why: 0108-converge-script C5, 0128 design D8.
    """
    folder = tmp_path / "fake-bin"
    folder.mkdir()
    profile = tmp_path / "profile.sb"
    fake = folder / "sandbox-exec"
    target = shlex.quote(str(profile))
    fake.write_text(
        "#!/bin/sh\n"
        'if [ "$1" != "-p" ]; then\n'
        '  echo "sandbox-exec: want -p, got $1" >&2\n'
        "  exit 64\n"
        "fi\n"
        f"printf '%s' \"$2\" > {target}\n"
        "shift 2\n"
        'exec "$@"\n'
    )
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", str(folder), prepend=os.pathsep)
    return profile
