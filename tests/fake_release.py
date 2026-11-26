"""The stand-in for `release.py` the conductor's tests run: `pre`, `finish`, `merge`.

It makes the commit, the tag and the merge as `FAKE_MODE` says, a death among them.
Why: 0152-release-script design *Tests*.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

from fake_worker import _git

_DIED = 137


def _primary(here: Path) -> Path:
    common = _git(here, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(common).parent


def _marks(here: Path, change: str) -> Path:
    return _primary(here) / ".minions" / "changes" / change


def _released(here: Path) -> str | None:
    """Return the tag `HEAD`'s release subject names, or None."""
    subject = _git(here, "log", "-1", "--format=%s")
    named = subject.removeprefix("chore(release): ")
    return named if named != subject else None


def _pre(here: Path, change: str, origin: str | None) -> str:
    """Drop a stranded release, resume a release commit, or restore and give a tag."""
    marks = _marks(here, change)
    if tag := _released(here):
        if not _git(here, "rev-list", "-n", "1", "HEAD..main"):
            return f"release: resume — {tag}"
        if origin == "held":
            print(
                f"release: halt — drop: origin holds {tag} or HEAD — nothing is dropped"
            )
            sys.exit(1)
        if _git(here, "tag", "-l", tag):
            _git(here, "tag", "-d", tag)
        _git(here, "reset", "-q", "--hard", "HEAD~1")
        for name in ("release.pre", "release.flag"):
            (marks / name).unlink(missing_ok=True)
        return f"release: drop — {tag} and its commit"
    _git(here, "restore", "--source=HEAD", "--staged", "--worktree", "--", ".")
    _git(here, "clean", "-q", "-f", "-d", "--", "openspec")
    shutil.rmtree(
        here / "openspec" / "changes" / "archive" / change, ignore_errors=True
    )
    tag = f"v0.{len(_git(here, 'tag', '-l').split()) + 1}.0"
    marks.mkdir(parents=True, exist_ok=True)
    head = _git(here, "rev-parse", "HEAD")
    version = tag.removesuffix(".0")
    mark = f"tag: {tag}\nversion: {version}\ngate: 1\nhead: {head}\n"
    (marks / "release.pre").write_text(mark)
    return f"release: tag — {tag}"


def _finish(here: Path, change: str, modes: set[str]) -> str:
    """Archive, commit and tag, dying where `modes` say; at a release commit, tag it."""
    if tag := _released(here):
        if not _git(here, "tag", "-l", tag):
            _git(here, "tag", tag)
        return f"release: ok — {tag} committed and tagged"
    mark = (_marks(here, change) / "release.pre").read_text()
    tag = mark.split("\n")[0].removeprefix("tag: ")
    (here / "openspec" / "changes" / "archive").mkdir(exist_ok=True)
    _git(here, "mv", f"openspec/changes/{change}", f"openspec/changes/archive/{change}")
    if "dies-release-fold" in modes:
        sys.exit(_DIED)
    _git(here, "add", "-A")
    _git(here, "commit", "-q", "-m", f"chore(release): {tag}\n\nChange: {change}")
    if "dies-release-commit" in modes:
        sys.exit(_DIED)
    _git(here, "tag", tag)
    if "dies-release-tag" in modes:
        sys.exit(_DIED)
    return f"release: ok — {tag} committed and tagged"


def _merge(here: Path, modes: set[str]) -> str:
    """Merge the branch into `main` in the primary; `stops-release-tag` does not."""
    if "stops-release-tag" in modes:
        return "release: ok — stopped before the merge"
    branch = _git(here, "branch", "--show-current")
    message = f"Merge branch '{branch}'"
    _git(_primary(here), "merge", "-q", "--no-ff", "-m", message, branch)
    return f"release: ok — {branch} merged into main"


def main() -> int:
    """Run one step as `FAKE_MODE` says; print its line."""
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("pre", "finish", "merge"))
    parser.add_argument("change")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--origin", choices=("held", "free"))
    args = parser.parse_args()
    modes = set(os.environ.get("FAKE_MODE", "").split(","))
    here = Path.cwd()
    calls = os.environ.get("FAKE_RELEASE_CALLS")
    if calls:
        with open(calls, "a") as file:
            origin = args.origin or "none"
            file.write(f"{args.step} {args.change} run={args.run} origin={origin}\n")
    if args.step == "pre":
        print(_pre(here, args.change, args.origin))
    elif args.step == "finish":
        print(_finish(here, args.change, modes))
    else:
        print(_merge(here, modes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
