"""The pin: one exported MF release per machine, linked on both hosts, moved when quiet.

Real git: an MF checkout with `skills/mf-*`, its bare `origin` read by a `file://` URL,
under the autouse `isolated_home`. Why: 0068-pinned-release design D1, D2 and D3.
"""

import json
import os
import runpy
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest
from fake_worker import _commit, _git

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-ship" / "scripts" / "pin.py"
_HOSTS = (".claude/skills", ".agents/skills")


def _pin() -> dict[str, Any]:
    return runpy.run_path(str(_SCRIPT))


def _mf(tmp_path: Path, pushed: tuple[str, ...] = ("v0.1.0", "v0.2.0")) -> Path:
    """Return an MF checkout tagged `v0.1.0` and `v0.2.0`, `pushed` on its origin.

    `v0.1.0` holds `mf-build`, `mf-old` and `mf-ship`; `v0.2.0` drops `mf-old`.
    """
    origin = tmp_path / "origin.git"
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    root = tmp_path / "mf"
    _git(tmp_path, "init", "-q", "-b", "main", str(root))
    _git(root, "remote", "add", "origin", origin.as_uri())
    files = {f"skills/mf-{name}/SKILL.md": f"{name} 1\n" for name in ("build", "old")}
    _commit(root, files | {"skills/mf-ship/SKILL.md": "ship 1\n"}, "v1")
    _git(root, "tag", "-a", "-m", "v0.1.0", "v0.1.0")
    _git(root, "rm", "-q", "-r", "skills/mf-old")
    _commit(root, {"skills/mf-build/SKILL.md": "build 2\n"}, "v2")
    _git(root, "tag", "-a", "-m", "v0.2.0", "v0.2.0")
    _git(root, "push", "-q", "origin", "main", *pushed)
    return root.resolve()


def _keep(pin: dict[str, Any], root: Path, url: str) -> None:
    """Keep `url` as `root`'s origin, as a run's first read does."""
    file = pin["_conduct"]()["_kept_file"](root)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps([[url], [url]]))


def _links(home: Path) -> dict[str, str]:
    """Return every `mf-*` link on both hosts and where it points."""
    return {
        f"{host}/{link.name}": os.readlink(link)
        for host in _HOSTS
        for link in sorted((home / host).glob("mf-*"))
        if link.is_symlink()
    }


def _into(home: Path, skills: Path, names: tuple[str, ...]) -> dict[str, str]:
    """Return the links `_links` reads when both hosts point `names` into `skills`."""
    return {
        f"{host}/mf-{name}": str(skills / f"mf-{name}")
        for host in _HOSTS
        for name in names
    }


def _mark(home: Path, name: str, pid: int | str) -> Path:
    """Write a live mark `name` holding `pid`; return it."""
    mark = home / ".mf-ship-origin" / "live" / name
    mark.parent.mkdir(parents=True, exist_ok=True)
    mark.write_text(f"{pid}\n")
    return mark


def test_a_bare_install_links_the_newest_tag_origin_holds(
    tmp_path: Path, isolated_home: Path
) -> None:
    pin = _pin()
    root = _mf(tmp_path)
    _git(root, "tag", "-a", "-m", "v0.3.0", "v0.3.0")
    _keep(pin, root, (tmp_path / "origin.git").as_uri())
    stale = isolated_home / ".claude/skills/mf-gone"
    stale.parent.mkdir(parents=True)
    stale.symlink_to(tmp_path / "elsewhere")
    hold = isolated_home / ".mf-ship-origin" / "hold"
    hold.write_text("v0.1.0\n")

    assert pin["install"](root, None) == (
        "pin: linked v0.2.0 · skipped v0.3.0: not on origin"
    )

    tree = isolated_home / ".local/share/minionsfactory/v0.2.0"
    assert _links(isolated_home) == _into(
        isolated_home, tree / "skills", ("build", "ship")
    )
    assert (tree / "VERSION").read_text() == "v0.2.0\n"
    assert (tree / "skills/mf-build/SKILL.md").read_text() == "build 2\n"
    assert not hold.exists()
    assert (isolated_home / ".mf-ship-origin/source").read_text() == f"{root}\n"
    assert pin["describe"]() == " · mf v0.2.0 · skipped v0.3.0: not on origin"

    (tree / "skills/mf-build/SKILL.md").write_text("kept\n")
    assert pin["install"](root, None).startswith("pin: linked v0.2.0")
    assert (tree / "skills/mf-build/SKILL.md").read_text() == "kept\n"


def test_an_install_names_what_stops_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    pin = _pin()
    root = _mf(tmp_path)
    monkeypatch.chdir(root)

    def said(*args: str) -> str:
        assert pin["main"](list(args)) == 2
        return capsys.readouterr().out.strip()

    assert said("install") == (
        "pin: cannot install — no run kept origin's URLs: run /mf-ship once,"
        " or make install-skills TAG=<tag>"
    )
    _keep(pin, root, (tmp_path / "missing.git").as_uri())
    assert said("install") == (
        "pin: cannot install — origin cannot be read: make install-skills TAG=<tag>"
    )
    _git(tmp_path, "init", "-q", "--bare", str(tmp_path / "bare.git"))
    _keep(pin, root, (tmp_path / "bare.git").as_uri())
    assert said("install") == "pin: cannot install — origin holds no version tag"
    assert said("install", "next") == (
        "pin: cannot install — next is not a version tag or live"
    )
    assert said("install", "v9.9.9").startswith("pin: cannot install — cannot export")
    monkeypatch.chdir(tmp_path)
    assert said("uninstall").startswith("pin: cannot uninstall — git rev-parse failed")

    pin["_fetch"].__globals__["_remote"] = lambda cwd, *args: (
        subprocess.CompletedProcess(args, 128, "", "fatal: refused\n")
    )
    with pytest.raises(pin["Refused"], match=r"cannot clone v0\.2\.0 from origin"):
        pin["_fetch"]("file:///nowhere", "v0.2.0")

    done = subprocess.run(
        [sys.executable, str(_SCRIPT), "install", "next"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert done.returncode == 2
    assert "next is not a version tag or live" in done.stdout


def test_a_tag_or_live_holds_the_links(tmp_path: Path, isolated_home: Path) -> None:
    pin = _pin()
    root = _mf(tmp_path, pushed=("v0.1.0",))
    _keep(pin, root, (tmp_path / "origin.git").as_uri())
    hold = isolated_home / ".mf-ship-origin" / "hold"

    assert pin["install"](root, "v0.1.0") == "pin: linked v0.1.0"
    tree = isolated_home / ".local/share/minionsfactory/v0.1.0/skills"
    held = _into(isolated_home, tree, ("build", "old", "ship"))
    assert _links(isolated_home) == held
    assert hold.read_text() == "v0.1.0\n"
    _git(root, "push", "-q", "origin", "v0.2.0")
    assert pin["move"]() is None
    assert _links(isolated_home) == held

    assert pin["install"](root, "live") == "pin: linked live"
    assert _links(isolated_home) == _into(
        isolated_home, root / "skills", ("build", "ship")
    )
    assert hold.read_text() == "live\n"
    described = _git(root, "describe", "--tags", "--always")
    assert pin["describe"]() == f" · mf live {described}"
    ran = tmp_path / "ran"
    _git(root, "config", "filter.probe.clean", f"touch {shlex.quote(str(ran))}; cat")
    (root / ".git" / "info").mkdir(exist_ok=True)
    (root / ".git" / "info" / "attributes").write_text("* filter=probe\n")
    os.utime(root / "skills" / "mf-build" / "SKILL.md", (0, 0))
    assert pin["describe"]() == f" · mf live {described}"
    assert not ran.exists()

    assert pin["install"](root, None) == "pin: linked v0.2.0"
    assert not hold.exists()


def test_the_quiet_move_follows_origin(tmp_path: Path, isolated_home: Path) -> None:
    pin = _pin()
    assert pin["move"]() is None
    root = _mf(tmp_path, pushed=("v0.1.0",))
    origin = (tmp_path / "origin.git").as_uri()
    _keep(pin, root, origin)
    assert pin["install"](root, None) == (
        "pin: linked v0.1.0 · skipped v0.2.0: not on origin"
    )
    assert pin["move"]() is None

    _git(root, "push", "-q", "origin", "v0.2.0")
    fetch = pin["_fetch"]

    def started(url: str, tag: str) -> Path:
        _mark(isolated_home, "started", os.getpid())
        return fetch(url, tag)

    pin["move"].__globals__["_fetch"] = started
    assert pin["move"]() is None
    v1 = isolated_home / ".local/share/minionsfactory/v0.1.0/skills"
    assert _links(isolated_home) == _into(isolated_home, v1, ("build", "old", "ship"))
    (isolated_home / ".mf-ship-origin/live/started").unlink()
    pin["move"].__globals__["_fetch"] = fetch
    assert pin["move"]() == "pin: moved to v0.2.0"
    tree = isolated_home / ".local/share/minionsfactory/v0.2.0/skills"
    assert _links(isolated_home) == _into(isolated_home, tree, ("build", "ship"))

    _git(root, "tag", "-a", "-m", "v0.3.0", "v0.3.0")
    _keep(pin, root, (tmp_path / "missing.git").as_uri())
    assert pin["move"]() is None
    assert pin["describe"]() == " · mf v0.2.0"
    (isolated_home / ".mf-ship-origin/source").write_text(str(tmp_path / "gone"))
    assert pin["describe"]() == " · mf v0.2.0"
    assert pin["move"]() is None
    assert _links(isolated_home) == _into(isolated_home, tree, ("build", "ship"))


def test_a_remote_call_takes_the_conductors_ssh_options(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pin = _pin()
    printed = ("-c", "alias.env=!env", "env")
    monkeypatch.delenv("GIT_SSH", raising=False)
    monkeypatch.delenv("GIT_SSH_COMMAND", raising=False)
    ssh = pin["_conduct"]()["SSH_COMMAND"]
    with pin["_scratch"]() as scratch:
        assert f"GIT_SSH_COMMAND={ssh}" in pin["_remote"](scratch, *printed).stdout

        monkeypatch.setenv("GIT_SSH_COMMAND", "ssh -o mine")
        said = pin["_remote"](scratch, *printed).stdout
        assert "GIT_SSH_COMMAND=ssh -o mine" in said


def test_a_non_link_is_refused_and_left_untouched(
    tmp_path: Path, isolated_home: Path
) -> None:
    pin = _pin()
    root = _mf(tmp_path)
    real = isolated_home / ".agents/skills/mf-ship"
    real.mkdir(parents=True)
    (real / "SKILL.md").write_text("mine\n")

    with pytest.raises(pin["Refused"], match=r"~/\.agents/skills/mf-ship exists"):
        pin["install"](root, "v0.1.0")

    assert _links(isolated_home) == {}
    assert (real / "SKILL.md").read_text() == "mine\n"
    (isolated_home / ".mf-ship-origin/pending").write_text("v0.1.0\n")
    assert pin["move"]() == (
        "pin: cannot move — ~/.agents/skills/mf-ship exists and is not a link"
    )
    (isolated_home / ".mf-ship-origin/pending").write_text("v0.9.0\n")
    assert pin["move"]() == (
        "pin: cannot move — "
        f"{isolated_home}/.local/share/minionsfactory/v0.9.0/skills holds no mf-* skill"
    )


def test_a_live_run_leaves_the_install_pending(
    tmp_path: Path, isolated_home: Path
) -> None:
    pin = _pin()
    root = _mf(tmp_path)
    mine = _mark(isolated_home, "mine", os.getpid())
    pending = isolated_home / ".mf-ship-origin" / "pending"

    assert pin["install"](root, "v0.1.0") == "pin: pending v0.1.0 — a run is live"
    assert _links(isolated_home) == {}
    assert pending.read_text() == "v0.1.0\n"
    tree = isolated_home / ".local/share/minionsfactory/v0.1.0"
    assert (tree / "VERSION").read_text() == "v0.1.0\n"
    assert pin["describe"]() == " · pending v0.1.0"
    assert pin["move"]() is None

    other = _mark(isolated_home, "other", os.getpid())
    assert pin["move"](mine) is None
    other.unlink()
    assert pin["move"](mine) == "pin: moved to v0.1.0"
    held = _into(isolated_home, tree / "skills", ("build", "old", "ship"))
    assert _links(isolated_home) == held
    assert not pending.exists()

    assert pin["install"](root, "live") == "pin: pending live — a run is live"
    assert _links(isolated_home) == held
    assert pin["move"](mine) == "pin: moved to live"
    assert _links(isolated_home) == _into(
        isolated_home, root / "skills", ("build", "ship")
    )

    worktree = tmp_path / "worktree"
    _git(root, "worktree", "add", "-q", str(worktree))
    assert pin["install"](worktree, "live") == "pin: pending live — a run is live"
    assert pin["move"](mine) == "pin: moved to live"
    assert _links(isolated_home) == _into(
        isolated_home, worktree.resolve() / "skills", ("build", "ship")
    )


def test_a_stale_mark_is_ignored(
    tmp_path: Path, isolated_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pin = _pin()
    root = _mf(tmp_path)
    ended = subprocess.Popen([sys.executable, "-c", ""])
    ended.wait()
    for name, pid in {
        "ended": ended.pid,
        "init": 1,
        "huge": 10**30,
        "torn": "x",
    }.items():
        _mark(isolated_home, name, pid)

    assert pin["live"]() == []
    assert pin["install"](root, "v0.1.0") == "pin: linked v0.1.0"

    def refused(pid: int, signal: int) -> None:
        raise PermissionError

    monkeypatch.setattr(os, "kill", refused)
    assert pin["live"]() == ["ended", "huge"]


def test_a_planted_replace_ref_does_not_reach_the_export(
    tmp_path: Path, isolated_home: Path
) -> None:
    pin = _pin()
    root = _mf(tmp_path)
    _keep(pin, root, (tmp_path / "origin.git").as_uri())
    real = _git(root, "rev-parse", "v0.2.0:skills/mf-build/SKILL.md")
    planted = (tmp_path / "planted.md").resolve()
    planted.write_text("planted\n")
    forged = _git(root, "hash-object", "-w", str(planted))
    _git(root, "replace", real, forged)
    assert _git(root, "show", "v0.2.0:skills/mf-build/SKILL.md") == "planted"
    _commit(root, {"skills/mf-build/SKILL.md": "moved\n"}, "moved")
    _git(root, "tag", "-f", "-a", "-m", "v0.2.0", "v0.2.0")
    assert _git(root, "show", "v0.2.0:skills/mf-build/SKILL.md") == "moved"

    assert pin["install"](root, None) == "pin: linked v0.2.0"

    tree = isolated_home / ".local/share/minionsfactory/v0.2.0/skills"
    assert (tree / "mf-build/SKILL.md").read_text() == "build 2\n"


def test_a_repo_planted_above_the_scratch_supplies_no_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pin = _pin()
    root = _mf(tmp_path)
    origin = (tmp_path / "origin.git").as_uri()
    _keep(pin, root, origin)
    forged = tmp_path / "forged.git"
    _git(tmp_path, "init", "-q", "--bare", str(forged))
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", f"url.{forged.as_uri()}.insteadOf", origin)
    _git(tmp_path, "config", "core.sshCommand", "planted")
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    monkeypatch.delenv("GIT_SSH", raising=False)
    monkeypatch.delenv("GIT_SSH_COMMAND", raising=False)

    assert pin["install"](root, None) == "pin: linked v0.2.0"

    ssh = pin["_conduct"]()["SSH_COMMAND"]
    with pin["_scratch"]() as scratch:
        printed = pin["_remote"](scratch, "-c", "alias.env=!env", "env").stdout
    assert f"GIT_SSH_COMMAND={ssh}" in printed


def test_uninstall_removes_the_links_into_the_release_or_the_checkout(
    tmp_path: Path,
    isolated_home: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    pin = _pin()
    root = _mf(tmp_path)
    assert pin["install"](root, "v0.1.0") == "pin: linked v0.1.0"
    agents = isolated_home / ".agents/skills"
    (agents / "mf-extra").symlink_to(root / "skills" / "mf-build")
    (agents / "mf-foreign").symlink_to(tmp_path / "elsewhere" / "mf-foreign")
    (agents / "mf-real").mkdir()
    monkeypatch.chdir(root)

    assert pin["main"](["uninstall"]) == 0

    assert capsys.readouterr().out.splitlines() == [
        *(
            f"pin: removed ~/.claude/skills/mf-{name}"
            for name in ("build", "old", "ship")
        ),
        *(f"pin: removed ~/.agents/skills/mf-{name}" for name in ("build", "extra")),
        *(f"pin: removed ~/.agents/skills/mf-{name}" for name in ("old", "ship")),
    ]
    assert _links(isolated_home) == {
        ".agents/skills/mf-foreign": str(tmp_path / "elsewhere" / "mf-foreign")
    }
    assert (agents / "mf-real").is_dir()
    assert pin["main"](["uninstall"]) == 0
    assert capsys.readouterr().out.strip() == "pin: no link to remove"
