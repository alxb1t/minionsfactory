# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Check a release before the worker's fold, by fixed rules.

    release.py pre <change-id> [--run] | findings <file>
Why: 0152-release-script design D1 and D2.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import mflib.findings
import mflib.layout
import mflib.modelsfile
import mflib.statefile

TIMEOUT_SECONDS = 60
GATE_SECONDS = 3700
CHANGE_ID = re.compile(r"\d+-[a-z0-9]+(?:-[a-z0-9]+)*")
TAG = re.compile(r"v\d+\.\d+\.\d+")
GATE_TIME = re.compile(r"^gate: (?:green|reused) — .*? · (\d+)s", re.MULTILINE)
UNRELEASED = re.compile(r"^## \[Unreleased\][ \t]*\n(.*?)(?=^## |\Z)", re.M | re.S)
GATE_RUN = (
    Path(__file__).resolve().parents[2] / "mf-converge" / "scripts" / "gate_run.py"
)
GATE_CHECK = GATE_RUN.with_name("gate_check.py")
NEXT_TAG = Path(__file__).with_name("next_tag.py")
# The git options of a run: the conductor's sandbox reaches no signer, and no hook runs.
# Why: 0152-release-script design D7.
RUN_OPTIONS = (
    *("-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false"),
    *("-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false"),
)
ROLES = ("conformance", "adversarial")
SETTLED = ("verified", "accepted")
PATCH = "diff.patch"
MARK = "release.pre"
FLAG = "release.flag"
VERSION_FILES = ("pyproject.toml", "uv.lock", "package.json", "package-lock.json")


class Stop(Exception):
    """End the command with `code`; the message is the line it prints."""

    def __init__(self, code: int, message: str) -> None:
        """Keep the exit code beside the message."""
        super().__init__(message)
        self.code = code


def halt(why: str) -> Stop:
    """Return the stop for a halt the plan or a person answers: exit 1."""
    return Stop(1, f"release: halt — {why}")


def cannot(why: str) -> Stop:
    """Return the stop for a script that could not run: exit 2."""
    return Stop(2, f"release: cannot run — {why}")


def _ok(what: str) -> None:
    """Print the line of a check that held."""
    print(f"release: ok — {what}")


def _exec(
    argv: list[str], cwd: Path, what: str, timeout: int = TIMEOUT_SECONDS
) -> subprocess.CompletedProcess[str]:
    """Return a finished command; a command that cannot start or runs long stops."""
    try:
        return subprocess.run(
            argv,
            cwd=cwd,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise cannot(f"{what} timed out") from None
    except OSError as error:
        raise cannot(f"{what} could not run: {error.strerror}") from None


def _last(done: subprocess.CompletedProcess[str]) -> str:
    """Return the last line a command printed, else its exit code."""
    lines = [line for line in (done.stdout + done.stderr).splitlines() if line.strip()]
    return lines[-1] if lines else f"exit {done.returncode}"


class Git:
    """Run git in one folder, with the run's options under `--run`."""

    def __init__(self, cwd: Path, run: bool = False) -> None:
        """Keep the folder and whether the options of a run apply."""
        self.cwd = cwd
        self.run = run

    def argv(self, *args: str) -> list[str]:
        """Return the command line of a git call.

        e.g. under a run, "status" → git -c commit.gpgsign=false … status
        """
        return ["git", *(RUN_OPTIONS if self.run else ()), *args]

    def result(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Return a finished git call, whatever its exit."""
        return _exec(self.argv(*args), self.cwd, f"git {args[0]}")

    def out(self, *args: str) -> str:
        """Return a git call's stdout; a failure stops with exit 2."""
        done = self.result(*args)
        if done.returncode != 0:
            raise cannot(f"git {args[0]} failed: {_last(done)}")
        return done.stdout

    def ok(self, *args: str) -> bool:
        """Return whether a git call exits 0."""
        return self.result(*args).returncode == 0


@dataclass(frozen=True)
class Findings:
    """A findings file's role, verdict, head, mode and cards."""

    role: str
    verdict: str
    head: str
    mode: str
    cards: list[mflib.findings.Card]


def read_findings(path: Path) -> Findings:
    """Return a findings file's role, verdict and head; a file it cannot parse stops.

    Why: 0152-release-script design D14.
    """
    try:
        text = mflib.findings.read(path)
    except OSError as error:
        raise cannot(f"{path.name} cannot be read: {error.strerror}") from None
    if text is None:
        raise cannot(f"{path.name} is missing")
    keys, body = mflib.findings.front(text)
    for key in ("type", "head"):
        if not keys.get(key):
            raise cannot(f"{path.name} has no {key}:")
    if keys.get("verdict") not in mflib.findings.VERDICTS:
        raise cannot(f"{path.name} has no verdict of clean or changes-requested")
    role = keys["type"]
    mode = keys.get("mode", "")
    cards = mflib.findings.cards(body, role)
    return Findings(role, keys["verdict"], keys["head"], mode, cards)


def findings(path: Path) -> str:
    """Return the line that says a findings file's role, verdict and head.

    e.g. "release: ok — conformance verdict clean head 81d2d09d"
    """
    found = read_findings(path)
    return f"release: ok — {found.role} verdict {found.verdict} head {found.head}"


def default_branch(git: Git) -> str:
    """Return the branch `origin/HEAD` names, else `main`."""
    named = git.result("symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    return named.stdout.strip().removeprefix("origin/") or "main"


def _primary(git: Git) -> Path:
    """Return the primary checkout, from any worktree."""
    common = git.out("rev-parse", "--path-format=absolute", "--git-common-dir")
    return mflib.layout.primary_of(common.strip())


def _dirty(git: Git) -> list[str]:
    """Return the changed and untracked paths of the tree, sorted."""
    changed = git.out("diff", "--no-renames", "--name-only", "-z", "HEAD")
    untracked = git.out("ls-files", "--others", "--exclude-standard", "-z")
    found = {*changed.split("\0"), *untracked.split("\0")}
    return sorted(path for path in found if path)


def _derived(path: str, change: str) -> bool:
    """Return whether a path is one a release's own work writes.

    Why: 0152-release-script design D5 and D8.
    """
    return (
        path.startswith(("openspec/specs/", "openspec/changes/"))
        or path.endswith(".md")
        or path in VERSION_FILES
        or path == f"metrics/changes/{change}.json"
    )


def _restore(git: Git, primary: Path, change: str) -> None:
    """Put a dead release's derived work back to `HEAD`, and remove its marks.

    A dirty path outside the derived set leaves the tree as it is.
    Why: 0152-release-script design D8.
    """
    paths = _dirty(git)
    if paths and all(_derived(path, change) for path in paths):
        git.out("restore", "--source=HEAD", "--staged", "--worktree", "--", ".")
        left = git.out("ls-files", "--others", "--exclude-standard", "-z")
        for path in (p for p in left.split("\0") if p and _derived(p, change)):
            (git.cwd / path).unlink(missing_ok=True)
        archived = git.cwd / "openspec" / "changes" / "archive" / change
        shutil.rmtree(archived, ignore_errors=True)
        (git.cwd / "metrics" / "changes" / f"{change}.json").unlink(missing_ok=True)
        _ok("restore — a dead release's derived work is back at HEAD")
    folder = mflib.layout.change_dir(primary, change)
    for name in (FLAG, MARK):
        (folder / name).unlink(missing_ok=True)


def _gate(git: Git) -> int:
    """Return the seconds the gate took, green through `gate_run.py`; red halts."""
    done = _exec([sys.executable, str(GATE_RUN)], git.cwd, "gate_run.py", GATE_SECONDS)
    if done.returncode != 0:
        raise halt(_last(done))
    found = GATE_TIME.search(done.stdout)
    if found is None:
        raise cannot("gate_run.py printed no time")
    _ok(f"gate · {found[1]}s")
    return int(found[1])


def _checked(role: str, path: Path) -> Findings:
    """Return a findings file that is clean, every blocking card settled; else halt."""
    found = read_findings(path)
    if found.role != role:
        raise halt(f"{path.name}: its type is {found.role}, not {role}")
    if found.verdict != "clean":
        raise halt(f"{role}: verdict {found.verdict}")
    for card in found.cards:
        if card.blocking and card.status not in SETTLED:
            state = card.status or "unmarked"
            raise halt(f"{role}: {card.id} is {state}, not verified or accepted")
    return found


def _converge(primary: Path, change: str, head: str) -> None:
    """Check that converge ran clean at `head`, or was skipped; else halt."""
    folder = mflib.layout.change_dir(primary, change)
    paths = {role: mflib.layout.findings_file(primary, change, role) for role in ROLES}
    held = [role for role in ROLES if os.path.lexists(paths[role])]
    if not held:
        if os.path.lexists(folder / PATCH):
            raise halt("converge froze its diff and stopped: run /mf-converge")
        try:
            data = mflib.modelsfile.read(primary, change)
        except mflib.modelsfile.Broken as error:
            raise halt(f"models.toml: {error}") from None
        planned = mflib.modelsfile.skipping(data, ("converge",))
        _ok("converge: skipped — " + ("by plan" if planned else "no findings files"))
        return
    for role in ROLES:
        if role not in held:
            raise halt(f"converge ran, and {paths[role].name} is missing")
    judged = []
    for role in ROLES:
        found = _checked(role, paths[role])
        _ok(f"{role}: " + ("skipped" if found.mode == "skipped" else "clean"))
        judged.append((role, found))
    _ok("converge: ran")
    for role, found in judged:
        if found.head != head:
            raise halt(
                f"{role}: head {found.head[:8]} is not HEAD {head[:8]}"
                f" — run /mf-converge: its catch-up round judges {found.head[:8]}..HEAD"
            )
    _ok(f"head · {head[:8]}")


def _proposal(git: Git, change: str) -> dict[str, str]:
    """Return the leading frontmatter of the change's `proposal.md`."""
    path = git.cwd / "openspec" / "changes" / change / "proposal.md"
    try:
        return mflib.findings.front(mflib.statefile.read(path))[0]
    except OSError as error:
        raise cannot(f"proposal.md cannot be read: {error.strerror}") from None


def _tag(git: Git, keys: dict[str, str]) -> str:
    """Return the tag the release takes from its `bump:`; one that stands halts."""
    bump = keys.get("bump", "")
    if bump not in ("minor", "patch"):
        raise halt(f"proposal.md: bump is {bump or 'missing'}, not minor or patch")
    done = _exec([sys.executable, str(NEXT_TAG), bump], git.cwd, "next_tag.py")
    tag = done.stdout.strip()
    if done.returncode != 0 or not TAG.fullmatch(tag):
        raise cannot(f"next_tag.py: {_last(done)}")
    _ok(f"bump · {bump}")
    if git.out("tag", "--list", tag).strip():
        raise halt(f"tag: {tag} already exists")
    _ok(f"tag · {tag} is free")
    return tag


def _entries(git: Git) -> None:
    """Halt unless `CHANGELOG.md`'s `## [Unreleased]` holds entries."""
    try:
        text = mflib.statefile.read(git.cwd / "CHANGELOG.md")
    except OSError:
        text = ""
    found = UNRELEASED.search(text)
    if found is None or not found[1].strip():
        raise halt("CHANGELOG.md: ## [Unreleased] holds no entries")
    _ok("changelog · Unreleased holds entries")


def _planned(git: Git, change: str, default: str) -> None:
    """Halt unless the gate changed only as the cut planned."""
    base = git.out("merge-base", default, "HEAD").strip()
    argv = [sys.executable, str(GATE_CHECK), "--change", change, "--base", base]
    done = _exec(argv, git.cwd, "gate_check.py")
    if done.returncode == 1:
        raise halt("gate check — " + done.stdout.strip())
    if done.returncode != 0:
        raise cannot(f"gate_check.py: {_last(done)}")
    _ok("gate check · no unplanned change")


def _shipped(git: Git, change: str, keys: dict[str, str], default: str) -> None:
    """Halt unless the default branch is merged in and each `after:` id is archived."""
    if not git.ok("merge-base", "--is-ancestor", default, "HEAD"):
        raise halt(
            f"base: {default} is not an ancestor of HEAD — run /mf-integrate {change}"
        )
    _ok(f"base · {default} is merged in")
    for named in mflib.findings.listed(keys.get("after", "[]")):
        if not git.ok("cat-file", "-e", f"HEAD:openspec/changes/archive/{named}"):
            raise halt(f"after: {named} is not archived at HEAD")
    _ok("after · each dependency is archived")


def pre(cwd: Path, change: str, run: bool) -> str:
    """Check every precondition, write the mark, and return the line for the tag.

    Why: 0152-release-script design D2 and D4.
    """
    if not CHANGE_ID.fullmatch(change):
        raise cannot(f"{change} is no change id")
    top = Git(cwd).out("rev-parse", "--show-toplevel")
    git = Git(Path(top.strip()), run)
    primary = _primary(git)
    if old := mflib.layout.old_layout(primary, change):
        raise halt(f"{old} is the old layout: /mf-ship moves it")
    _ok("old layout")
    if run:
        _restore(git, primary, change)
    if dirty := _dirty(git):
        raise halt(f"tree: dirty at {dirty[0]}")
    _ok("tree · clean")
    seconds = _gate(git)
    head = git.out("rev-parse", "HEAD").strip()
    _converge(primary, change, head)
    keys = _proposal(git, change)
    tag = _tag(git, keys)
    default = default_branch(git)
    _entries(git)
    _planned(git, change, default)
    _shipped(git, change, keys, default)
    folder = mflib.layout.change_dir(primary, change)
    folder.mkdir(parents=True, exist_ok=True)
    version = tag.removesuffix(".0")
    mark = f"tag: {tag}\nversion: {version}\ngate: {seconds}\nhead: {head}\n"
    try:
        mflib.statefile.write(folder / MARK, mark)
    except mflib.statefile.WriteFailed as failed:
        raise cannot(f"{MARK} could not be written: {failed.error.strerror}") from None
    return f"release: tag — {tag}"


def main(argv: list[str] | None = None) -> int:
    """Run one subcommand; return 0 for ok, 1 for a halt, 2 for a script that cannot."""
    parser = argparse.ArgumentParser(
        description="Check and cut a release by fixed rules."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    checking = commands.add_parser("pre", help="check the preconditions, print the tag")
    checking.add_argument("change", metavar="change-id")
    checking.add_argument(
        "--run", action="store_true", help="a run of mf-ship: restore, unsigned git"
    )
    commands.add_parser(
        "findings", help="print a findings file's verdict"
    ).add_argument("file", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "findings":
            print(findings(args.file))
        else:
            print(pre(Path.cwd(), args.change, args.run))
    except Stop as stop:
        print(stop)
        return stop.code
    return 0


if __name__ == "__main__":
    sys.exit(main())
