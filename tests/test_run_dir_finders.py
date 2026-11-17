"""Each script's run-directory finder gives the primary's `.minions/` from any worktree.

Real git in a scratch repository with a linked worktree.
Why: 0134-run-layout design D3, D11.
"""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
from fake_worker import _commit, _git

_REPO = Path(__file__).resolve().parent.parent


def _load(name: str, path: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, _REPO / path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


integrate = _load("integrate", "skills/mf-integrate/scripts/integrate.py")
cut_pre = _load("cut_pre", "skills/mf-cut-change/scripts/cut_pre.py")
metrics = _load("metrics", "skills/mf-build/scripts/metrics.py")
awake = _load("awake", "skills/mf-cut-change/scripts/awake.py")
run = _load("run", "scripts/metrics/run.py")


def _found(cwd: Path) -> dict[str, Path]:
    """Return what each finder gives, run in `cwd`."""
    return {
        "integrate._run_dir": integrate._run_dir(cwd),
        "cut_pre.run_directory": cut_pre.run_directory(),
        "metrics.run_directory": metrics.run_directory(cwd),
        "awake._record": awake._record("0001-a").parent.parent,
        "run.Version": run.Version(cwd, "0001-a", "base", "head").minions,
    }


@pytest.mark.parametrize("where", ["primary", "linked"])
def test_each_finder_gives_the_primarys_run_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, where: str
) -> None:
    primary = tmp_path / "main"
    primary.mkdir()
    _git(primary, "init", "-q", "-b", "main")
    _commit(primary, {".gitignore": ".minions/\n"}, "base")
    linked = tmp_path / "0001-a"
    _git(primary, "worktree", "add", "-q", "-b", "0001-a", str(linked))
    cwd = (primary if where == "primary" else linked).resolve()
    monkeypatch.chdir(cwd)

    found = _found(cwd)

    minions = primary.resolve() / ".minions"
    assert found == dict.fromkeys(found, minions)
