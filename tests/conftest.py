"""Hold every test's home, global git config and XDG folders under its own `tmp_path`.

Why: the suite runs on every core, so no test may share the operator's home or another
test's state — 0065-gate-hardening design D1.
"""

from pathlib import Path

import pytest

ISOLATED = {
    "XDG_CONFIG_HOME": ".config",
    "XDG_DATA_HOME": ".local/share",
    "XDG_CACHE_HOME": ".cache",
}


@pytest.fixture(autouse=True)
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Return the home folder this test runs with, under its `tmp_path`."""
    home = tmp_path / "isolated-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(home / ".gitconfig"))
    for name, folder in ISOLATED.items():
        monkeypatch.setenv(name, str(home / folder))
    return home
