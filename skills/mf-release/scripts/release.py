# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Check a release before the worker's fold, and cut it after, by fixed rules.

    release.py pre|finish <change-id> [--run] | findings <file>
Why: 0152-release-script design D1 and D2.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import mflib.debtfile
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
METRICS = Path(__file__).resolve().parents[2] / "mf-build" / "scripts" / "metrics.py"
UV = ("uv",)
GH = ("gh",)
DEBT_WAIT = 600
PREVIOUS = re.compile(r"^## \[([^\]]+)\][^\n]*\n(.*?)(?=^## |\Z)", re.M | re.S)
PRIOR_GATE = re.compile(r"^Gate: (.*?)(?: · \d[\w.-]*: .*)?$", re.M)
PROJECT = re.compile(r"^\[project\][ \t]*\n(.*?)(?=^\[|\Z)", re.M | re.S)
PROJECT_VERSION = re.compile(r'^version\s*=\s*"[^"]*"', re.M)
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


def _gate(git: Git, fresh: bool = False) -> int:
    """Return the seconds the gate took, green through `gate_run.py`; red halts."""
    argv = [sys.executable, str(GATE_RUN), *(["--fresh"] if fresh else [])]
    done = _exec(argv, git.cwd, "gate_run.py", GATE_SECONDS)
    if done.returncode != 0:
        raise halt(_last(done) + (" — nothing is committed" if fresh else ""))
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


def _converge_skip(primary: Path, change: str) -> str:
    """Return the line of a converge that left no findings file; a broken plan halts.

    e.g. "converge: skipped — by plan"
    """
    try:
        data = mflib.modelsfile.read(primary, change)
    except mflib.modelsfile.Broken as error:
        raise halt(f"models.toml: {error}") from None
    planned = mflib.modelsfile.skipping(data, ("converge",))
    return "converge: skipped — " + ("by plan" if planned else "no findings files")


def _skips(primary: Path, change: str) -> list[str]:
    """Return the skip lines the release commit states, none when converge ran whole.

    e.g. ["adversarial: skipped"]
    """
    paths = {role: mflib.layout.findings_file(primary, change, role) for role in ROLES}
    held = [role for role in ROLES if os.path.lexists(paths[role])]
    if not held:
        return [_converge_skip(primary, change)]
    found = [(role, read_findings(paths[role])) for role in held]
    return [f"{role}: skipped" for role, read in found if read.mode == "skipped"]


def _converge(primary: Path, change: str, head: str) -> None:
    """Check that converge ran clean at `head`, or was skipped; else halt."""
    folder = mflib.layout.change_dir(primary, change)
    paths = {role: mflib.layout.findings_file(primary, change, role) for role in ROLES}
    held = [role for role in ROLES if os.path.lexists(paths[role])]
    if not held:
        if os.path.lexists(folder / PATCH):
            raise halt("converge froze its diff and stopped: run /mf-converge")
        _ok(_converge_skip(primary, change))
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


def _opened(cwd: Path, change: str, run: bool) -> tuple[Git, Path]:
    """Return git at the checkout's top and the primary; a bad change id stops."""
    if not CHANGE_ID.fullmatch(change):
        raise cannot(f"{change} is no change id")
    top = Git(cwd).out("rev-parse", "--show-toplevel")
    git = Git(Path(top.strip()), run)
    return git, _primary(git)


def pre(cwd: Path, change: str, run: bool) -> str:
    """Check every precondition, write the mark, and return the line for the tag.

    Why: 0152-release-script design D2 and D4.
    """
    git, primary = _opened(cwd, change, run)
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


def _mark(primary: Path, change: str, head: str) -> dict[str, str]:
    """Return `release.pre`'s keys; a missing mark, or one of another head, halts.

    Why: 0152-release-script design D4.
    """
    path = mflib.layout.change_dir(primary, change) / MARK
    try:
        text = mflib.statefile.read(path)
    except FileNotFoundError:
        raise halt(f"{MARK} is missing — run release.py pre {change}") from None
    except OSError as error:
        raise cannot(f"{MARK} cannot be read: {error.strerror}") from None
    pairs = (line.partition(":") for line in text.splitlines())
    keys = {key.strip(): value.strip() for key, colon, value in pairs if colon}
    for key in ("tag", "version", "gate", "head"):
        if not keys.get(key):
            raise cannot(f"{MARK} has no {key}:")
    if not TAG.fullmatch(keys["tag"]) or not keys["gate"].isdigit():
        raise cannot(f"{MARK} holds no tag or gate seconds")
    if keys["head"] != head:
        raise halt(
            f"{MARK}: head {keys['head'][:8]} is not HEAD {head[:8]}"
            f" — run release.py pre {change}"
        )
    return keys


def _workers(git: Git) -> list[str]:
    """Return the worker's paths: those under `openspec/specs/` and Markdown files.

    Any other path, and a rename, halts naming it. Why: 0152-release-script design D5.
    """
    status = git.out("status", "--porcelain", "-z", "--untracked-files=all")
    fields = iter(status.split("\0"))
    paths = []
    for entry in fields:
        if not entry:
            continue
        code, path = entry[:2], entry[3:]
        if "R" in code or "C" in code:
            raise halt(f"paths: {next(fields, '')} → {path} is a rename")
        if not (path.startswith("openspec/specs/") or path.endswith(".md")):
            raise halt(f"paths: {path} is no spec and no Markdown file")
        paths.append(path)
    _ok("paths · " + (", ".join(paths) or "none"))
    return paths


def _text(path: Path) -> str:
    """Return a tracked file's text, read through no link; an unreadable one stops."""
    try:
        return mflib.statefile.read(path)
    except OSError as error:
        raise cannot(f"{path.name} cannot be read: {error.strerror}") from None


def _put(path: Path, text: str) -> None:
    """Replace a tracked file with `text`, a link replaced rather than followed."""
    try:
        mflib.statefile.write(path, text)
    except mflib.statefile.WriteFailed as failed:
        raise cannot(
            f"{path.name} could not be written: {failed.error.strerror}"
        ) from None


def _archive(git: Git, change: str, version: str) -> str:
    """Write `version:` below `bump:`, then archive the change; return its new path."""
    proposal = git.cwd / "openspec" / "changes" / change / "proposal.md"
    text, found = re.subn(
        r"^bump:.*\n",
        lambda bump: f"{bump[0]}version: {version}\n",
        _text(proposal),
        count=1,
        flags=re.M,
    )
    if not found:
        raise halt("proposal.md: no bump: line to write version: below")
    _put(proposal, text)
    archived = f"openspec/changes/archive/{change}"
    (git.cwd / archived).parent.mkdir(parents=True, exist_ok=True)
    git.out("mv", f"openspec/changes/{change}", archived)
    _ok(f"archive · {archived} · version: {version}")
    return archived


def _clock(seconds: int) -> str:
    """Return seconds as minutes and seconds.

    e.g. 479 → "7m59s"
    """
    return f"{seconds // 60}m{seconds % 60}s"


def _latest_runs(text: str) -> list[tuple[int, str, str]]:
    """Return each workflow's latest run as seconds, name and short sha; junk is none.

    `gh run list` prints the newest run first. Why: 0152-release-script design D7.
    """
    try:
        latest: dict[str, dict[str, str]] = {}
        for run in json.loads(text):
            latest.setdefault(run["workflowName"], run)
        return [
            (
                round(
                    (
                        datetime.fromisoformat(run["updatedAt"])
                        - datetime.fromisoformat(run["startedAt"])
                    ).total_seconds()
                ),
                name,
                run["headSha"][:7],
            )
            for name, run in latest.items()
        ]
    except (ValueError, TypeError, KeyError, AttributeError):
        return []


def _ci(git: Git, default: str, run: bool) -> str:
    """Return the `Gate:` line's CI part: the longest latest successful run, or none.

    e.g. "CI 0m12s (CI at d5162e4)". Why: 0152-release-script design D7.
    """
    if run:
        return "CI not read under mf-ship"
    if not git.ok("remote", "get-url", "origin"):
        return "CI none"
    argv = [*GH, "run", "list", "--branch", default, "--status", "success"]
    argv += ["--limit", "50", "--json", "workflowName,headSha,startedAt,updatedAt"]
    try:
        done = _exec(argv, git.cwd, "gh")
    except Stop:
        return "CI none"
    runs = _latest_runs(done.stdout) if done.returncode == 0 else []
    if not runs:
        return "CI none"
    seconds, name, sha = max(runs)
    return f"CI {_clock(seconds)} ({name} at {sha})"


def _changelog(git: Git, tag: str, gate: int, ci: str) -> None:
    """Rename `## [Unreleased]` to the release, seed an empty one, write `Gate:`.

    Why: 0152-release-script design D7.
    """
    path = git.cwd / "CHANGELOG.md"
    text = _text(path)
    found = UNRELEASED.search(text)
    if found is None:
        raise halt("CHANGELOG.md: no ## [Unreleased] heading")
    after = text[found.end() :]
    line = f"Gate: local {_clock(gate)} · {ci}"
    if prior := PREVIOUS.search(after):
        times = PRIOR_GATE.search(prior[2])
        line += f" · {prior[1]}: {times[1] if times else 'none'}"
    heading = f"## [{tag.removeprefix('v')}] - {date.today().isoformat()}"
    cut = f"## [Unreleased]\n\n{heading}\n\n{line}\n\n{found[1].strip()}\n"
    _put(path, text[: found.start()] + cut + (f"\n{after}" if after else ""))
    _ok(f"changelog · {heading} · {line}")


def _pyproject(git: Git, number: str) -> list[str]:
    """Set `[project]`'s first `version` and lock it; return the files bumped.

    Why: 0152-release-script design D6.
    """
    path = git.cwd / "pyproject.toml"
    if not path.is_file():
        return []
    text = _text(path)
    section = PROJECT.search(text)
    line = PROJECT_VERSION.search(section[1]) if section else None
    if section is None or line is None:
        return []
    at = section.start(1)
    _put(
        path,
        f'{text[: at + line.start()]}version = "{number}"{text[at + line.end() :]}',
    )
    if not (git.cwd / "uv.lock").is_file():
        return [path.name]
    done = _exec([*UV, "lock", "--offline"], git.cwd, "uv lock")
    if done.returncode != 0:
        raise halt(f"uv lock: {_last(done)}")
    return [path.name, "uv.lock"]


def _json(path: Path) -> dict[str, object]:
    """Return a JSON file's object; one that is no object halts naming it."""
    try:
        data = json.loads(_text(path))
    except ValueError:
        data = None
    if not isinstance(data, dict):
        raise halt(f"{path.name}: no JSON object")
    return data


def _dumped(data: dict[str, object]) -> str:
    """Return JSON as npm writes it: two spaces, a newline at the end."""
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def _package(git: Git, number: str) -> list[str]:
    """Set `package.json`'s version and its lock's own; return the files bumped.

    A lock of another shape halts naming it. Why: 0152-release-script design D6.
    """
    path = git.cwd / "package.json"
    if not path.is_file():
        return []
    package = _json(path)
    lock_path = git.cwd / "package-lock.json"
    lock = _json(lock_path) if lock_path.is_file() else None
    if lock is not None:
        packages = lock.get("packages")
        root = packages.get("") if isinstance(packages, dict) else None
        level = lock.get("lockfileVersion")
        if (
            type(level) is not int
            or "version" not in lock
            or not isinstance(root, dict)
        ):
            raise halt(f"{lock_path.name}: a lock of another shape")
        lock["version"] = root["version"] = number
    package["version"] = number
    _put(path, _dumped(package))
    if lock is None:
        return [path.name]
    _put(lock_path, _dumped(lock))
    return [path.name, lock_path.name]


def _metrics(git: Git, change: str, default: str, version: str, gate: str) -> list[str]:
    """Collect the change's data file; return its path, none with no catalogue.

    A data file of another version halts. Why: 0152-release-script design D7.
    """
    if not (git.cwd / "metrics" / "catalogue.toml").is_file():
        _ok("metrics: none — no catalogue")
        return []
    out = f"metrics/changes/{change}.json"
    base = git.out("merge-base", default, "HEAD").strip()
    argv = [sys.executable, str(METRICS), "collect", "--change", change]
    argv += ["--base", base, "--out", out, "--value", f"gate-seconds={gate}"]
    done = _exec(
        [*argv, "--model", "unidentified"], git.cwd, "metrics.py", GATE_SECONDS
    )
    if done.returncode != 0:
        raise halt(f"metrics: {_last(done)}")
    try:
        found = json.loads(_text(git.cwd / out)).get("version")
    except (ValueError, AttributeError):
        raise cannot(f"{out} holds no JSON object") from None
    if found != version:
        raise halt(f"metrics: {out} says version {found}, not {version}")
    _ok(f"metrics · {out}")
    return [out]


def _committed(
    git: Git, paths: list[str], change: str, tag: str, skips: list[str]
) -> None:
    """Stage by name, gate fresh, then commit once; a tree the gate did not judge halts.

    Why: 0152-release-script design D7.
    """
    git.out("add", "--", *paths)
    _gate(git, fresh=True)
    unstaged = [
        path for path in git.out("diff", "--name-only", "-z").split("\0") if path
    ]
    if unstaged:
        raise halt(f"tree: {unstaged[0]} changed after staging — nothing is committed")
    left = git.out("ls-files", "--others", "--exclude-standard", "-z").split("\0")
    if untracked := [path for path in left if path]:
        raise halt(f"tree: {untracked[0]} is untracked — nothing is committed")
    body = "".join(f"{line}\n" for line in skips)
    message = f"chore(release): {tag}\n\n" + (f"{body}\n" if body else "")
    git.out("commit", "-q", "-m", f"{message}Change: {change}")
    if dirty := git.out("status", "--porcelain"):
        raise halt(f"tree: dirty after the commit — {dirty.splitlines()[0].strip()}")
    _ok(f"commit · chore(release): {tag}")


def _debt(primary: Path, keys: dict[str, str]) -> None:
    """Clear the paid cards that `debt:`, else `backlog:`, names from the debt file.

    Why: 0152-release-script design D7; 0139-debt design D12.
    """
    named = keys["debt"] if "debt" in keys else keys.get("backlog")
    ids = list(dict.fromkeys(mflib.findings.listed(named or "[]")))
    if not ids:
        _ok("debt: none")
        return
    old = mflib.layout.backlog_file(primary)
    if os.path.lexists(old):
        raise halt(
            f"{old.relative_to(primary)} is the old debt file: /mf-ship moves it"
        )
    path, lock = mflib.layout.debt_file(primary), mflib.layout.debt_lock(primary)
    debt = path.relative_to(primary)
    try:
        with mflib.debtfile.lock(lock, DEBT_WAIT):
            text = mflib.debtfile.read(path)
            held = set(mflib.debtfile.ids(text))
            paid = [ident for ident in ids if ident in held]
            if paid:
                mflib.debtfile.write(path, mflib.debtfile.clear(text, paid))
    except mflib.debtfile.Held:
        waited = DEBT_WAIT // 60
        raise halt(f"{lock.relative_to(primary)} held for {waited} minutes") from None
    except mflib.debtfile.Unreadable as unread:
        raise halt(f"{debt} cannot be read: {unread.reason}") from None
    except mflib.statefile.WriteFailed as failed:
        why = failed.error.strerror
        raise cannot(f"{debt} could not be written: {why}") from None
    for ident in ids:
        _ok(f"debt: {ident} " + ("cleared" if ident in paid else "not found"))


def finish(cwd: Path, change: str, run: bool) -> str:
    """Archive, cut the changelog, bump, gate, commit once and tag; clear the debt.

    Why: 0152-release-script design D4, D5, D6 and D7.
    """
    git, primary = _opened(cwd, change, run)
    keys = _mark(primary, change, git.out("rev-parse", "HEAD").strip())
    tag, version, gate = keys["tag"], keys["version"], keys["gate"]
    workers = _workers(git)
    default = default_branch(git)
    archived = _archive(git, change, version)
    _changelog(git, tag, int(gate), _ci(git, default, run))
    number = tag.removeprefix("v")
    bumped = _pyproject(git, number) + _package(git, number)
    _ok("version file · " + ", ".join(bumped) if bumped else "version file: none")
    data = _metrics(git, change, default, version, gate)
    moved = f"openspec/changes/{change}/"
    kept = [path for path in workers if not path.startswith(moved)]
    paths = [*dict.fromkeys([*kept, archived, "CHANGELOG.md", *bumped, *data])]
    _committed(git, paths, change, tag, _skips(primary, change))
    git.out("tag", "-a", tag, "-m", tag)
    _ok(f"tag · {tag}")
    proposal = git.cwd / archived / "proposal.md"
    _debt(primary, mflib.findings.front(_text(proposal))[0])
    flag = mflib.layout.change_dir(primary, change) / FLAG
    if os.path.lexists(flag):
        raise halt(
            f"{flag.relative_to(primary)} stands — read the prose it names, then merge"
        )
    return f"release: ok — {tag} committed and tagged"


def main(argv: list[str] | None = None) -> int:
    """Run one subcommand; return 0 for ok, 1 for a halt, 2 for a script that cannot."""
    parser = argparse.ArgumentParser(
        description="Check and cut a release by fixed rules."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    steps = {"pre": pre, "finish": finish}
    helps = {
        "pre": "check the preconditions, print the tag",
        "finish": "archive, cut the changelog, gate, commit and tag",
    }
    for name, said in helps.items():
        step = commands.add_parser(name, help=said)
        step.add_argument("change", metavar="change-id")
        step.add_argument(
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
            print(steps[args.command](Path.cwd(), args.change, args.run))
    except Stop as stop:
        print(stop)
        return stop.code
    return 0


if __name__ == "__main__":
    sys.exit(main())
