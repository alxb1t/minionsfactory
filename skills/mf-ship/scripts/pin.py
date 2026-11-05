# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Install one pinned MF release on both hosts, and move it only at a quiet moment.

    pin.py install [<tag>|live]
    pin.py uninstall

Exit 0 done · 2 cannot. The conductor loads `move`, `describe`, `trees` and `holder`.
Why: 0068-pinned-release design D1, D2 and D3.
"""

import argparse
import contextlib
import functools
import os
import re
import runpy
import subprocess
import sys
import tarfile
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

HOSTS = (".claude/skills", ".agents/skills")
KEPT = ".mf-ship-origin"
CONDUCT = Path(__file__).resolve().with_name("conduct.py")
TAG = re.compile(r"v(\d+)\.(\d+)\.(\d+)")
NO_HOOKS = ("-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null")
NO_ORIGIN = (
    "no run kept origin's URLs: run /mf-ship once, or make install-skills TAG=<tag>"
)
FAILURES = (OSError, subprocess.SubprocessError)


class Refused(Exception):
    """An install or a move that cannot go on; its message says why."""


@functools.cache
def _conduct() -> dict[str, Any]:
    """Return the conductor's namespace: its kept URLs and its remote call options."""
    return runpy.run_path(str(CONDUCT))


def data() -> Path:
    """Return the data folder every release is exported into."""
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "minionsfactory"


def _kept(name: str) -> Path:
    """Return the file `name` in the conductor's folder in the home folder."""
    return Path.home() / KEPT / name


def _read(name: str) -> str | None:
    """Return what the kept file `name` holds, or None when it is absent."""
    file = _kept(name)
    return file.read_text().strip() if file.is_file() else None


def _write(name: str, text: str | None) -> None:
    """Write `text` to the kept file `name`; None removes it."""
    file = _kept(name)
    if text is None:
        file.unlink(missing_ok=True)
        return
    file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    file.write_text(f"{text}\n")


def holder(mark: Path) -> int | None:
    """Return the pid a live mark holds while that process runs, else None."""
    try:
        pid = int(mark.read_text())
    except (OSError, ValueError):
        return None
    if pid <= 1:
        return None
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, OverflowError):
        return None
    except PermissionError:
        pass
    return pid


def live(mine: Path | None = None) -> list[str]:
    """Return the live marks standing, `mine` aside; one whose pid is gone is none."""
    folder = _kept("live")
    marks = sorted(folder.iterdir()) if folder.is_dir() else []
    return [mark.name for mark in marks if mark != mine and holder(mark)]


def _version(tag: str) -> tuple[int, ...]:
    """Return a version tag's numbers, or none for another name.

    e.g. "v0.55.0" → (0, 55, 0)
    """
    match = TAG.fullmatch(tag)
    return tuple(int(part) for part in match.groups()) if match else ()


def _newest(tags: list[str]) -> str | None:
    """Return the highest version tag in `tags`, or None."""
    return max((tag for tag in tags if _version(tag)), key=_version, default=None)


def _why(done: subprocess.CompletedProcess[str]) -> str:
    """Return a failed call's last stderr line, or its exit."""
    lines = [line for line in done.stderr.splitlines() if line.strip()]
    return lines[-1].strip() if lines else f"exit {done.returncode}"


def _git(
    cwd: Path, *args: str, env: dict[str, str] | None = None, timeout: int | None = None
) -> subprocess.CompletedProcess[str]:
    """Return a finished git command in `cwd`: no hook, replace ref or lazy fetch."""
    quiet = {"GIT_NO_REPLACE_OBJECTS": "1", "GIT_NO_LAZY_FETCH": "1"}
    return subprocess.run(
        ["git", *NO_HOOKS, *args],
        cwd=cwd,
        capture_output=True,
        encoding="utf-8",
        env={**(os.environ if env is None else env), **quiet},
        errors="replace",
        timeout=timeout,
    )


def _out(cwd: Path, *args: str) -> str:
    """Return a local git command's stdout; a failure is refused."""
    done = _git(cwd, *args)
    if done.returncode != 0:
        raise Refused(f"git {args[0]} failed: {_why(done)}")
    return done.stdout.strip()


@contextlib.contextmanager
def _scratch() -> Iterator[Path]:
    """Yield an empty bare repo in the conductor's scratch folder, for remote calls.

    Taken as `GIT_DIR`, it stops git finding a repo a worker planted above the folder.
    Why: 0052-security-hardening design D9.
    """
    with _conduct()["_scratch"]() as scratch:
        _out(Path(scratch), "init", "-q", "--bare", "--template=")
        yield Path(scratch)


def _remote(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Return a remote git call with `cwd`, a `_scratch` repo, as its `GIT_DIR`.

    It reads the operator's config and no repo's above `cwd`. It takes the conductor's
    timeout and, with no ssh command the operator set, its ssh options.
    """
    conduct = _conduct()
    env = {**os.environ, "GIT_DIR": str(cwd)}
    named = _git(cwd, "config", "--get", "core.sshCommand", env=env).stdout.strip()
    if not named and not any(env.get(name) for name in ("GIT_SSH_COMMAND", "GIT_SSH")):
        env["GIT_SSH_COMMAND"] = conduct["SSH_COMMAND"]
    return _git(cwd, *args, env=env, timeout=conduct["GIT_TIMEOUT"])


def _origin(primary: Path) -> str | None:
    """Return the fetch URL a run kept for `primary`'s `origin`, or None before one."""
    kept = _conduct()["_kept_origin"](primary)
    return kept[0][0] if kept and kept[0] else None


def _held(url: str) -> list[str] | None:
    """Return the tags `url` lists, or None when it cannot be read."""
    with _scratch() as scratch:
        done = _remote(scratch, "ls-remote", "--tags", "--refs", "--", url)
    if done.returncode != 0:
        return None
    return [line.partition("\trefs/tags/")[2] for line in done.stdout.splitlines()]


def _export(repo: Path, tag: str) -> Path:
    """Return the skills tree `tag` is exported to from `repo`; one that stands is kept.

    The tree's root holds `VERSION`, naming the tag. e.g. "v0.55.0" →
    `<data>/v0.55.0/skills`
    """
    root = data() / tag
    if not root.is_dir():
        data().mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=data(), prefix=f".{tag}-") as scratch:
            archive = Path(scratch) / "skills.tar"
            ref = f"refs/tags/{tag}"
            done = _git(
                repo, "archive", "--format=tar", "-o", str(archive), ref, "skills"
            )
            if done.returncode != 0:
                raise Refused(f"cannot export {tag}: {_why(done)}")
            tree = Path(scratch) / tag
            with tarfile.open(archive) as tar:
                tar.extractall(tree, filter="data")
            (tree / "VERSION").write_text(f"{tag}\n")
            tree.rename(root)
    return root / "skills"


def _fetch(url: str, tag: str) -> Path:
    """Return `tag`'s skills tree, exported from a fresh scratch clone of `url`.

    The clone shares no object with any local repo, so nothing planted there reaches
    the export.
    """
    if (data() / tag).is_dir():
        return data() / tag / "skills"
    with _scratch() as scratch:
        clone = scratch / "clone"
        done = _remote(
            scratch,
            *("clone", "-q", "--bare", "--depth", "1", "--branch", tag, "--template="),
            *("--", url, str(clone)),
        )
        if done.returncode != 0:
            raise Refused(f"cannot clone {tag} from origin: {_why(done)}")
        return _export(clone, tag)


def _link(skills: Path) -> None:
    """Point every `mf-*` on both hosts into `skills`; a non-link stops it, untouched.

    Each link is made at a temp name and moved over the old one, so no moment lacks
    it; a link to a skill `skills` lacks goes.
    """
    names = sorted(skill.name for skill in skills.glob("mf-*") if skill.is_dir())
    if not names:
        raise Refused(f"{skills} holds no mf-* skill")
    for host in HOSTS:
        for name in names:
            if (dest := Path.home() / host / name).exists() and not dest.is_symlink():
                raise Refused(f"~/{host}/{name} exists and is not a link")
    for host in HOSTS:
        folder = Path.home() / host
        folder.mkdir(parents=True, exist_ok=True)
        for name in names:
            temp = folder / f".{name}.pin-{os.getpid()}"
            temp.unlink(missing_ok=True)
            temp.symlink_to(skills / name)
            temp.replace(folder / name)
        for link in folder.glob("mf-*"):
            if link.is_symlink() and link.name not in names:
                link.unlink()


def trees() -> dict[Path, list[str]]:
    """Return each skills folder the `mf-*` links on both hosts point into, with them.

    e.g. {Path("<data>/v0.55.0/skills"): ["~/.claude/skills/mf-build", …]}
    """
    found: dict[Path, list[str]] = {}
    for host in HOSTS:
        for link in sorted((Path.home() / host).glob("mf-*")):
            if link.is_symlink():
                links = found.setdefault(link.resolve().parent, [])
                links.append(f"~/{host}/{link.name}")
    return found


def _linked() -> str | None:
    """Return the tag the links hold, when they all point into one exported tree."""
    found = list(trees())
    version = found[0].parent / "VERSION" if len(found) == 1 else None
    return version.read_text().strip() if version and version.is_file() else None


def _skipped(source: Path, linked: str | None, held: list[str] | None) -> str | None:
    """Return the source's newest local tag when past `linked` and origin lacks it.

    `held` is origin's tags when the caller has read them; else they are read here.
    """
    local = _newest(_out(source, "tag", "-l", "v*").split())
    if local is None or (linked and _version(local) <= _version(linked)):
        return None
    if held is None and (url := _origin(source)):
        held = _held(url)
    return local if held is not None and local not in held else None


def describe() -> str:
    """Return the `start` line's release: the linked one, then what waits or skipped.

    e.g. " · mf v0.55.0 · pending v0.56.0"
    """
    parts = []
    if len(found := list(trees())) == 1:
        root = found[0].parent
        if (version := root / "VERSION").is_file():
            parts.append(f"mf {version.read_text().strip()}")
        else:
            # No `--dirty`: its index refresh runs a clean filter the checkout names.
            done = _git(root, "describe", "--tags", "--always")
            parts.append(f"mf live {done.stdout.strip() or 'unknown'}")
    source = _read("source")
    if pending := _read("pending"):
        parts.append(f"pending {pending}")
    elif source and not _read("hold"):
        try:
            if skipped := _skipped(Path(source), _linked(), None):
                parts.append(f"skipped {skipped}: not on origin")
        except (Refused, *FAILURES):
            pass
    return "".join(f" · {part}" for part in parts)


def move(mine: Path | None = None) -> str | None:
    """Move the links to the pending release, or a newer one origin holds; say what.

    Nothing moves without `source`, while a run other than `mine` is live, or under a
    hold for a newer tag; `origin` that cannot be read moves nothing.
    """
    source = _read("source")
    if source is None or live(mine):
        return None
    try:
        target = _read("pending")
        if target == "live":
            skills = Path(_read("checkout") or source) / "skills"
        elif target:
            skills = data() / target / "skills"
        elif _read("hold") or not (url := _origin(Path(source))):
            return None
        else:
            linked = _linked()
            target = _newest(_held(url) or [])
            if target is None or (linked and _version(target) <= _version(linked)):
                return None
            skills = _fetch(url, target)
        if live(mine):
            return None
        _link(skills)
        _write("pending", None)
    except (Refused, *FAILURES) as error:
        return f"pin: cannot move — {error}"
    return f"pin: moved to {target}"


def install(cwd: Path, release: str | None) -> str:
    """Install `release`, a tag or `live`, or bare the newest origin holds; say what.

    Under a live run the tree is exported and left `pending` for the quiet move.
    """
    checkout = Path(_out(cwd, "rev-parse", "--show-toplevel")).resolve()
    common = _out(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")
    primary = Path(common).resolve().parent
    _write("source", str(primary))
    skipped = None
    if release is None:
        if not (url := _origin(primary)):
            raise Refused(NO_ORIGIN)
        if (held := _held(url)) is None:
            raise Refused("origin cannot be read: make install-skills TAG=<tag>")
        if not (target := _newest(held)):
            raise Refused("origin holds no version tag")
        skills = _fetch(url, target)
        _write("hold", None)
        skipped = _skipped(primary, target, held)
    elif release == "live":
        target, skills = release, checkout / "skills"
        _write("hold", release)
        _write("checkout", str(checkout))
    elif _version(release):
        target, skills = release, _export(checkout, release)
        _write("hold", release)
    else:
        raise Refused(f"{release} is not a version tag or live")
    if live():
        _write("pending", target)
        return f"pin: pending {target} — a run is live"
    _link(skills)
    _write("pending", None)
    note = f" · skipped {skipped}: not on origin" if skipped else ""
    return f"pin: linked {target}{note}"


def uninstall(cwd: Path) -> list[str]:
    """Remove each `mf-*` link on both hosts into the data folder or the checkout.

    Return the links removed; a link elsewhere, and anything not a link, stays.
    """
    checkout = Path(_out(cwd, "rev-parse", "--show-toplevel")).resolve()
    roots = (data().resolve(), checkout)
    removed = []
    for host in HOSTS:
        for link in sorted((Path.home() / host).glob("mf-*")):
            target = link.resolve()
            if link.is_symlink() and any(target.is_relative_to(r) for r in roots):
                link.unlink()
                removed.append(f"pin: removed ~/{host}/{link.name}")
    return removed


def main(argv: list[str] | None = None) -> int:
    """Run the command `argv` names; return its exit."""
    parser = argparse.ArgumentParser(prog="pin.py")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("install").add_argument("release", nargs="?")
    commands.add_parser("uninstall")
    args = parser.parse_args(argv)
    try:
        if args.command == "install":
            print(install(Path.cwd(), args.release))
        else:
            print("\n".join(uninstall(Path.cwd())) or "pin: no link to remove")
    except (Refused, *FAILURES) as error:
        print(f"pin: cannot {args.command} — {error}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
