# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Take every cut version to the default branch, one agent process per station.

    conduct.py status
    conduct.py check <stage> <change-id>
    conduct.py log --verify <run-log>
    conduct.py run --executor claude|codex [--detach]
    conduct.py stop
    conduct.py grant <change-id> --executor claude|codex
    conduct.py agent --executor claude|codex <prompt>
    conduct.py report

Exit 0 done · 1 halt · 2 cannot run. Every stage and check is read from git and
the run directory, so a re-run derives them again.
Why: 0040-mf-ship design D2.
"""

import argparse
import hashlib
import itertools
import json
import os
import re
import runpy
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

TIMEOUT = 10800
STAMP = "%Y%m%d-%H%M%S"
GIT_TIMEOUT = 60
PUSH_TIMEOUT = 1800
LOCK_SECONDS = 30
LOCK_STALE = 600
INTEGRATE = Path(__file__).resolve().parents[2] / "mf-integrate/scripts/integrate.py"
MOVED = "delta: changed on the default branch: "
CHANGE_ID = re.compile(r"(\d+)-([a-z0-9-]+)")
PROGRESS = re.compile(r"^- \[([ x])\] (\d+) — (.*)$", re.MULTILINE)
RELEASE = re.compile(r"chore\(release\): (\S+)")
EVENT = re.compile(r"^\d\d:\d\d:\d\d · (\S+) · (\S+) — ")
EVENTS = (
    *("start", "spawn", "finish", "check", "denied", "halt", "blocked", "done"),
    *("push", "ledger", "unlock", "unkept", "loopback"),
)
TAG = re.compile(r"v\d+\.\d+\.\d+")
HALTS = ("integrating", "released", "human", "converge-halted")
STUCK = (*HALTS, "waiting")
STATIONS = ("build", "converge", "integrate", "release")
ROLES = ("review", "security")
TIERS = ("standard", "high")
EXECUTORS = ("claude", "codex")
SKILLS = {"claude": ".claude/skills", "codex": ".agents/skills"}
STOPPED = "stopped by the person"
CONFIG_CHANGED = "the local git config changed during the run: {file} differs"
# Why: 0054-loopback design D2.
NEEDS_CLAUDE = (
    "conduct: halt — AGENTS.md: Ship loopback needs Claude workers: {} names codex"
)
GIT_FILES = (".git/config", ".git/info/attributes")
KEPT_ORIGINS = ".mf-ship-origin"
TOOLS = ("Read", "Glob", "Grep", "Agent", "Skill")
COMMANDS = (
    *("git", "uv", "make", "python3", "openspec", "gh", "grep", "sed", "awk"),
    *("head", "tail", "cat", "ls", "wc", "echo", "mkdir", "rmdir", "date", "test"),
    *("diff", "find", "sort", "mktemp", "cp", "mv", "touch", "basename", "dirname"),
    *("readlink", "tr", "cut", "rm"),
)
DENIED = (
    *("git push --force", "git push -f", "git reset --hard", "git clean"),
    *("git branch -D", "git tag -d", "git worktree remove --force"),
)
# Each (subcommand, flag) also denied as globs: a `:*` rule matches `<prefix> *`, so
# never `--force-with-lease`, `-fu`, `git -C <dir> …` or a trailing flag. `clean`'s
# flag `-` gets no trailing form: its `-*` would match any flag after the word.
FORCED = (
    *(("push", "--force"), ("push", "-f"), ("push", "+"), ("reset", "--hard")),
    *(("clean", "-"), ("branch", "-D"), ("tag", "-d"), ("worktree remove", "--force")),
    ("worktree remove", "-f"),
)
DENIALS = ("has been denied", "needs approval", "denied by your permission settings")
SECRETS = (
    "~/.ssh",
    "~/.aws",
    "~/.config/gh",
    "~/.netrc",
    "~/.gnupg",
    "~/.kube",
    "~/.docker/config.json",
    "~/.git-credentials",
    "~/.config/git/credentials",
    "~/.npmrc",
    "~/.pypirc",
    "~/.codex/auth.json",
    "~/.claude/.credentials.json",
)
# Unset before each sandboxed command: the host names no credential of its own.
TOKENS = (
    *("GITHUB_TOKEN", "GH_TOKEN", "NPM_TOKEN", "NODE_AUTH_TOKEN"),
    *("UV_PUBLISH_TOKEN", "TWINE_PASSWORD"),
    *("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"),
    *("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "OPENAI_API_KEY"),
)
# Read-only by host: `upload.pypi.org` takes a package, and it is not here.
NETWORK = ("pypi.org", "files.pythonhosted.org")
DOMAIN = re.compile(r"[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+")
PROMPTS = {
    "build": "Run the mf-build skill for change {change}.",
    "converge": "Run the mf-converge skill for change {change}{tier}.",
    "integrate": "Run the mf-integrate skill for change {change}.",
    "release": "Run the mf-release skill for change {change} with merge=yes.",
}
SHELL_RULES = (
    "Shell rules for this run: one command per Bash call; no `$(…)`, shell variables"
    " or loops — run the inner command first and use its output literally; use"
    " `git -C <dir>`, never `cd`; never retry a denied command in a rewritten form"
    " to get past the list. Give these rules, word for word,"
    " to every subagent you start."
)
PROBE = (
    "In this directory, write the word ok to probe.txt, commit it with the"
    " message probe, then run make gate."
)
SCRATCH_IDENTITY = (
    *("-c", "user.name=mf-ship", "-c", "user.email=mf-ship@example.invalid"),
    *("-c", "commit.gpgsign=false"),
)
# A worker can write the common directory, and the conductor runs outside its sandbox.
# These stop a directory's hooks only; `CONFIG_PLAIN` stops a `hook.*` key's.
NO_HOOKS = ("-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null")
# The same, for a worker's git: `make gate` is the one check in a run.
HOOKS_OFF = (
    "GIT_CONFIG_COUNT=2",
    *("GIT_CONFIG_KEY_0=core.hooksPath", "GIT_CONFIG_VALUE_0=/dev/null"),
    *("GIT_CONFIG_KEY_1=core.fsmonitor", "GIT_CONFIG_VALUE_1=false"),
)
# A primary checkout and its common directory, None outside a repo.
type Repo = tuple[Path, Path | None]
# The URLs git fetches `origin` from, then the ones it pushes to.
type Urls = tuple[list[str], list[str]]
# The only keys a repo's own config may hold: each starts no program under `NO_HOOKS`,
# and any other halts, so a key git adds later fails closed. `lfs.*` stays off: LFS
# uploads from a `pre-push` hook, and no hook runs in a run.
CONFIG_PLAIN = re.compile(
    r"core\.(repositoryformatversion|filemode|bare|logallrefupdates|ignorecase"
    r"|precomposeunicode|symlinks|hookspath)"
    r"|(user|author|committer)\.(name|email)|user\.signingkey|commit\.gpgsign"
    r"|protocol\.version|pull\.(rebase|ff)"
    r"|remote\..+\.(url|fetch|gh-resolved)"
    r"|branch\..+\.(remote|merge|rebase|description)"
)
# What `git lfs install` writes: under these names, any other value is a planted one.
LFS_CONFIG = {
    "lfs.repositoryformatversion": "0",
    "filter.lfs.clean": "git-lfs clean -- %f",
    "filter.lfs.smudge": "git-lfs smudge -- %f",
    "filter.lfs.process": "git-lfs filter-process",
    "filter.lfs.required": "true",
}
# A URL git reaches over a network. Any other form runs a program on this machine: a
# local path or `file://` runs that repo's hooks, and `<helper>::` runs the helper.
NETWORK_URL = re.compile(r"(https?|ssh|git)://.+|[^/:]+:(?!:|//).*")


class ShipLines(NamedTuple):
    """`AGENTS.md`'s `Ship tools:` and `Ship network:` values; `Ship loopback: yes`."""

    tools: list[str]
    network: list[str]
    loopback: bool


class Stop(Exception):
    """End the command with `code`; the message is what it prints."""

    def __init__(self, code: int, message: str) -> None:
        """Keep the exit code beside the message."""
        super().__init__(message)
        self.code = code


def _run(
    cwd: Path, *args: str, env: dict[str, str] | None = None, timeout: int = GIT_TIMEOUT
) -> subprocess.CompletedProcess[str]:
    """Return a finished git command run in `cwd`; a missing git stops with exit 2.

    No local git reaches a network: a missing object read here would otherwise fetch
    from a promisor remote a worker planted, past every refusal.
    Why: 0052-security-hardening design D9.
    """
    try:
        return subprocess.run(
            ["git", *NO_HOOKS, *args],
            cwd=cwd,
            capture_output=True,
            encoding="utf-8",
            env={**(os.environ if env is None else env), "GIT_NO_LAZY_FETCH": "1"},
            errors="replace",
            timeout=timeout,
        )
    except FileNotFoundError:
        raise Stop(2, "conduct: cannot run — git is missing") from None
    except subprocess.TimeoutExpired:
        raise Stop(2, f"conduct: cannot run — git {args[0]} timed out") from None


def _git(cwd: Path, *args: str) -> str:
    """Return a git command's stdout; a failure stops with exit 2."""
    done = _run(cwd, *args)
    if done.returncode != 0:
        lines = [line for line in done.stderr.splitlines() if line.strip()]
        first = lines[0] if lines else f"exit {done.returncode}"
        raise Stop(2, f"conduct: cannot run — git {args[0]} failed: {first}")
    return done.stdout


def _maybe(cwd: Path, *args: str) -> str | None:
    """Return a git command's stdout, or None when it exits non-zero."""
    done = _run(cwd, *args)
    return done.stdout if done.returncode == 0 else None


def _show(cwd: Path, rev: str, path: str) -> str | None:
    """Return the file at `path` in `rev`, or None when `rev` has none."""
    return _maybe(cwd, "show", f"{rev}:{path}")


def _ancestor(cwd: Path, older: str, newer: str) -> bool:
    """Return whether `older` is an ancestor of `newer`."""
    return _maybe(cwd, "merge-base", "--is-ancestor", older, newer) is not None


def _tagged(cwd: Path, tag: str) -> bool:
    """Return whether the tag exists."""
    return _maybe(cwd, "rev-parse", "-q", "--verify", f"refs/tags/{tag}") is not None


def _shipped(cwd: Path, rev: str, change: str) -> bool:
    """Return whether `rev` holds the change's archive folder."""
    path = f"{rev}:openspec/changes/archive/{change}"
    return _maybe(cwd, "cat-file", "-e", path) is not None


def _subject(cwd: Path, rev: str = "HEAD") -> str:
    """Return the subject line of `rev`."""
    return _git(cwd, "log", "-1", "--format=%s", rev).strip()


def default_branch(cwd: Path) -> str:
    """Return the branch `origin/HEAD` names, or `main`."""
    ref = _maybe(cwd, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    return ref.strip().removeprefix("origin/") if ref else "main"


def _common_dir(cwd: Path) -> Path | None:
    """Return git's common directory for `cwd`, or None outside a repo."""
    common = _maybe(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(common.strip()).resolve() if common else None


def primary_of(cwd: Path) -> Path:
    """Return the primary checkout of the repo holding `cwd`; outside one, exit 2.

    A worker can write `commondir` and `.git`, so git can name a repo `_refuse_origin`
    has no kept URLs for: past that repo's own folder, kept URLs must stand, or stop
    with 1. Why: 0052-security-hardening design D9.
    """
    if (common := _common_dir(cwd)) is None:
        raise Stop(2, "conduct: cannot run — not in a git repository")
    primary = common.parent
    if not cwd.resolve().is_relative_to(primary) and not _kept_file(primary).is_file():
        raise Stop(
            1,
            "conduct: halt — git names a repo outside this folder, and no run kept its"
            " URLs: run this in the primary, and if it halts there, remove the"
            " `commondir` file in `.git`, or restore `.git`",
        )
    return primary


def _repo(cwd: Path) -> Repo:
    """Return the primary checkout and common directory; outside a repo, `cwd`, None.

    Taken once, before the first worker: git's answer in a tree is worker-written.
    """
    common = _common_dir(cwd)
    return (common.parent, common) if common else (cwd.resolve(), None)


def _frontmatter(text: str, key: str) -> str | None:
    """Return a key's value in the text's leading `---` block.

    e.g. a findings file opening `verdict: clean` in its block, "verdict" → "clean"
    """
    if not text.startswith("---\n"):
        return None
    block = text[4:].split("\n---", 1)[0]
    found = re.search(rf"^{key}:\s*(\S+)", block, re.MULTILINE)
    return found[1] if found else None


def _after(text: str) -> list[str]:
    r"""Return the change ids a proposal's `after:` names.

    e.g. "---\nafter: [0047-x, 0048-y]\n---\n" → ["0047-x", "0048-y"]
    """
    found = re.search(r"^after:\s*\[(.*)\]", text.split("\n---", 1)[0], re.MULTILINE)
    return re.findall(r"[^,\s]+", found[1]) if found else []


def _agents_line(root: Path, key: str) -> str | None:
    """Return the text after `AGENTS.md`'s `**<key>:**`, or None."""
    path = root / "AGENTS.md"
    if not path.is_file():
        return None
    found = re.search(rf"\*\*{key}:\*\*(.*)", path.read_text())
    return found[1] if found else None


def _agents_values(root: Path, key: str) -> list[str] | None:
    """Return the backticked values of `AGENTS.md`'s `**<key>:**` line, or None.

    e.g. "- **Ship tools:** `npm`, `pnpm`", "Ship tools" → ["npm", "pnpm"]
    """
    line = _agents_line(root, key)
    return None if line is None else re.findall(r"`([^`]+)`", line)


def _agents_flag(root: Path, key: str) -> str | None:
    """Return `AGENTS.md`'s `**<key>:**` text up to an optional ` — `, or None.

    e.g. "- **Ship loopback:** yes — the gate serves", "Ship loopback" → "yes"
    """
    line = _agents_line(root, key)
    return None if line is None else line.split(" — ", 1)[0].strip()


@dataclass(frozen=True)
class Version:
    """A cut version: its change, which names its branch, and its worktree."""

    change: str
    tree: Path | None

    @property
    def number(self) -> int:
        """Return the change id's number."""
        return int(self.change.split("-")[0])


def _points_back(tree: Path, common: Path, branch: str) -> bool:
    """Return whether `tree`'s `.git` file names `common`'s entry holding `branch`.

    e.g. "gitdir: <common>/worktrees/0001-todo", its `HEAD` on 0001-todo → True
    """
    link = tree / ".git"
    text = link.read_text(errors="replace") if link.is_file() else ""
    found = re.fullmatch(r"gitdir: (.+)\n?", text)
    if found is None:
        return False
    entry = (tree / found[1]).resolve()
    head = entry / "HEAD"
    return (
        entry.parent == common / "worktrees"
        and head.is_file()
        and head.read_text(errors="replace").strip() == f"ref: refs/heads/{branch}"
    )


def _worktrees(primary: Path) -> dict[str, Path]:
    """Map each checked-out branch to its worktree."""
    found: dict[str, Path] = {}
    main = primary.resolve()
    path = None
    for line in _git(primary, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            path = Path(line.removeprefix("worktree ")).resolve()
        elif line.startswith("branch refs/heads/") and path:
            branch = line.removeprefix("branch refs/heads/")
            # Why: 0050-codex-review design D5.
            if path == main or _points_back(path, main / ".git", branch):
                found[branch] = path
    return found


def _tag_of(primary: Path, change: str) -> str | None:
    """Return the tag the branch's tip names, or None before a release."""
    found = RELEASE.fullmatch(_subject(primary, change))
    return found[1] if found else None


def _holds(primary: Path, change: str) -> bool:
    """Return whether a branch holds its change, active or just released."""
    folder = f"openspec/changes/{change}"
    active = _show(primary, change, f"{folder}/proposal.md") is not None
    return active or _tag_of(primary, change) is not None


def _dependencies(primary: Path, change: str) -> list[str]:
    """Return the ids the `after:` on the change's branch names; released, none."""
    proposal = _show(primary, change, f"openspec/changes/{change}/proposal.md")
    return _after(proposal or "")


def open_versions(primary: Path) -> list[Version]:
    """Return the open versions in change-id order.

    Open is a branch named by a change id, the default branch lacks, in a linked
    worktree, holding its change.
    """
    default = default_branch(primary)
    listing = _git(
        primary,
        *("branch", "--no-merged", default, "--list", "[0-9]*"),
        "--format=%(refname:short)",
    )
    trees = _worktrees(primary)
    found = []
    for change in listing.split():
        tree = trees.get(change)
        if tree is None or tree == primary.resolve():
            continue
        if CHANGE_ID.fullmatch(change) and _holds(primary, change):
            found.append(Version(change, tree))
    return sorted(found, key=lambda version: version.number)


def find_version(primary: Path, change: str) -> Version | None:
    """Return the version of a change, open or merged, or None."""
    ref = f"refs/heads/{change}"
    if not CHANGE_ID.fullmatch(change) or not _maybe(
        primary, "rev-parse", "-q", "--verify", ref
    ):
        return None
    return Version(change, _worktrees(primary).get(change))


def _progress(tree: Path, change: str) -> list[tuple[str, str, str]]:
    """Return the `## Progress` lines as (mark, number, title); none stops with 1."""
    tasks = _show(tree, "HEAD", f"openspec/changes/{change}/tasks.md") or ""
    boxes = PROGRESS.findall(tasks)
    if not boxes:
        raise Stop(1, f"conduct: halt — {change}: tasks.md has no ## Progress list")
    return boxes


def _unticked(tree: Path, change: str) -> tuple[str, str] | None:
    """Return the first unticked phase's number and title, or None."""
    for mark, number, title in _progress(tree, change):
        if mark != "x":
            return number, title
    return None


def _run_end(runs: Path, change: str) -> str | None:
    """Return the newest converge run's top event line, or None with no run."""
    log = runs / "findings" / f"{change}_status_log.md"
    lines = log.read_text().splitlines() if log.is_file() else []
    heading = next(
        (i for i, line in enumerate(lines) if line.startswith("## Run")), None
    )
    if heading is None:
        return None
    return next((line for line in lines[heading + 1 :] if line.strip()), "").strip()


def _is_event(line: str, event: str) -> bool:
    """Return whether a status-log line holds `event`, its detail aside.

    e.g. "10:00:00 · round 1 · done — ok", "done" → True
    """
    return line.split(" — ")[0].endswith(f" · {event}")


def _clear_stale_lock(primary: Path) -> int | None:
    """Remove a `backlog.lock` older than `LOCK_STALE`; return its age in seconds.

    A lock younger, or one `rmdir` refuses, stays. Why: 0053-sandbox-patch design D3.
    """
    lock = primary / ".minions" / "backlog.lock"
    if not lock.is_dir():
        return None
    age = round(time.time() - lock.stat().st_mtime)
    if age <= LOCK_STALE:
        return None
    try:
        lock.rmdir()
    except OSError:
        return None
    return age


def _converge_halt(runs: Path, change: str) -> str | None:
    """Return the newest converge run's top event when it is a halt, else None."""
    end = _run_end(runs, change)
    return end if end and _is_event(end, "halt") else None


def _converge_done(runs: Path, change: str) -> bool:
    """Return whether the newest converge run ends on `done`."""
    return _is_event(_run_end(runs, change) or "", "done")


def _unjudged(runs: Path, tree: Path, change: str, rev: str = "HEAD") -> str | None:
    """Return why converge is not clean at `rev`, or None when it is."""
    head = _git(tree, "rev-parse", rev).strip()
    for role in ROLES:
        file = runs / "findings" / f"{change}_{role}.md"
        if not file.is_file():
            return f"no {role} findings file"
        text = file.read_text()
        if (verdict := _frontmatter(text, "verdict")) != "clean":
            return f"{role}: verdict {verdict}"
        judged = _frontmatter(text, "head") or ""
        resolved = _maybe(tree, "rev-parse", "-q", "--verify", f"{judged}^{{commit}}")
        if not judged or (resolved or "").strip() != head:
            return f"{role}: judged {judged or 'no head'}, not {rev}"
    return None


def _merge_open(tree: Path) -> bool:
    """Return whether a merge is open in `tree`."""
    return _maybe(tree, "rev-parse", "-q", "--verify", "MERGE_HEAD") is not None


def _unmerged(tree: Path) -> bool:
    """Return whether an open merge leaves a path unmerged in `tree`.

    Past the refusal: a stat-dirty file makes `git diff` run a clean filter.
    """
    _refuse_config_commands(tree)
    return bool(_git(tree, "diff", "--name-only", "--diff-filter=U").strip())


def _dirty(tree: Path) -> bool:
    """Return whether `git status --porcelain` prints anything.

    Past the refusal: a stat-dirty file makes `git status` run a clean filter.
    """
    _refuse_config_commands(tree)
    return bool(_git(tree, "status", "--porcelain").strip())


def _delta(delta: Callable[[Path], str], tree: Path) -> list[str]:
    """Return the lines `integrate.py`'s `delta` names; a crash stops with exit 2."""
    try:
        delta(tree)
    except Exception as error:
        code = getattr(error, "code", None)
        said = str(error).splitlines() if code else [f"{type(error).__name__}: {error}"]
        moved = [line for line in said if line.startswith(MOVED)]
        if code == 1 and moved:
            return moved
        raise Stop(2, f"conduct: cannot run — integrate.py delta: {said[-1]}") from None
    return []


def _git_state(primary: Path) -> list[str]:
    """Return each of `GIT_FILES` under `primary`, or "" if none."""
    files = (primary / name for name in GIT_FILES)
    return [
        file.read_text(errors="replace") if file.is_file() else "" for file in files
    ]


def _config_changed(primary: Path, state: list[str]) -> Stop | None:
    """Return the halt naming the first of `GIT_FILES` that differs from `state`.

    It names no URL: one can hold a key. Why: 0053-sandbox-patch design D4.
    """
    for name, held, now in zip(GIT_FILES, state, _git_state(primary), strict=True):
        if held != now:
            return Stop(1, CONFIG_CHANGED.format(file=name))
    return None


def _note(tree: Path, change: str, moved: list[str]) -> str:
    """Return the integrate note for the requirements the default branch changed.

    e.g. "delta: changed on the default branch: sdd: First" → a `## sdd: First` section
    """
    base = _git(tree, "merge-base", "HEAD", "MERGE_HEAD").strip()
    sections = []
    for line in moved:
        heading = line.removeprefix(MOVED)
        trailers = _git(
            tree,
            *("log", "--format=%(trailers:key=Change,valueonly)"),
            *(f"{base}..MERGE_HEAD", "--"),
            f"openspec/specs/{heading.split(': ')[0]}/spec.md",
        )
        designs = ", ".join(
            f"`openspec/changes/archive/{name}/design.md`"
            for name in dict.fromkeys(trailers.split())
        )
        sections.append(
            f"## {heading}\n\n"
            f"- **The branch:** `openspec/changes/{change}/design.md`\n"
            f"- **The default branch:** {designs or 'no `Change:` trailer'}\n"
            "- **Proposed:** rewrite the delta's requirement over the default"
            " branch's text, keeping both edits.\n"
        )
    return "\n".join(sections)


def _release_died(runs: Path, change: str) -> bool:
    """Return whether the change's newest release worker ended any way but exit 0.

    A person's no ran no worker, and a release that stopped on purpose exits 0.
    """
    for log in sorted(runs.glob("*.md"), key=_log_order, reverse=True):
        for line in reversed(log.read_text().splitlines()):
            found = EVENT.match(line)
            detail = line[found.end() :] if found else ""
            if found and found[1] == change and detail.startswith("release · "):
                if found[2] == "spawn":
                    return True
                if found[2] == "finish":
                    return not detail.startswith("release · exit 0 · ")
    return False


def _release_tip(primary: Path, tree: Path, change: str, tag: str) -> tuple[str, str]:
    """Return the stage of a tip that says it is released; only a death re-enters.

    The re-entry merges unasked, so it takes no person's no, a tag on `HEAD`
    or none, the converge clean at the parent, an unmoved base and a release worker
    that died. Every other reason names the person's way out, per `mf-release` Step 5.1.
    """
    runs = primary / ".minions"
    if (runs / "release" / f"{change}.held").is_file():
        return "released", (
            f"{tag}: .minions/release/{change}.held holds a person's no:"
            f" /mf-release {change} merges it on their yes"
        )
    own = _maybe(tree, "rev-parse", "-q", "--verify", f"refs/tags/{tag}^{{commit}}")
    if own is not None and own != _git(tree, "rev-parse", "HEAD"):
        return "released", f"{tag} is tagged on another commit: a person reads this tip"
    stated = "is not tagged" if own is None else "is tagged"
    default = default_branch(primary)
    if not _ancestor(tree, default, "HEAD"):
        undo = "" if own is None else f"git tag -d {tag}, "
        return "released", (
            f"{tag} {stated}; {default} moved, so recover by hand: {undo}git reset"
            f" --hard HEAD~1, then /mf-integrate {change}, /mf-converge, /mf-release"
        )
    if why := _unjudged(runs, tree, change, "HEAD~1"):
        return "released", f"{tag} {stated}; {why}: a person reads this tip"
    if _release_died(runs / "runs", change):
        return "release", f"{tag} {stated}; the merge is left"
    return "released", (
        f"{tag} {stated}; the release stopped before its merge:"
        f" /mf-release {change} merges it on a person's yes"
    )


def stage_of(primary: Path, version: Version) -> tuple[str, str]:
    """Return a version's stage, read in its worktree, and why; the first match wins."""
    tree = version.tree
    change = version.change
    if tree is None:
        raise Stop(2, f"conduct: cannot run — {change} has no worktree")
    runs = primary / ".minions"
    if _merge_open(tree):
        marks = runs / "integrate"
        if (marks / f"{change}.red").is_file():
            return "integrating", f"red gate: .minions/integrate/{change}.red"
        if (marks / f"{change}.md").is_file():
            return "integrating", f"semantic conflict: .minions/integrate/{change}.md"
        if _unmerged(tree):
            return "integrate", "interrupted: a merge is open with no note"
        return (
            "integrate",
            "a merge is open and staged, with no note: integrate resumes",
        )
    tag = _tag_of(primary, change)
    default = default_branch(primary)
    if tag is not None:
        return _release_tip(primary, tree, version.change, tag)
    missing = [
        name
        for name in _dependencies(primary, change)
        if not _shipped(primary, default, name)
    ]
    if missing:
        return "waiting", f"after {' '.join(missing)}"
    if unticked := _unticked(tree, change):
        number, title = unticked
        if "**HUMAN" in title:
            return "human", f"phase {number} — {title}"
        return "build", f"phase {number} unticked"
    if halt := _converge_halt(runs, change):
        if "cap reached" in halt and (runs / "grants" / change).is_file():
            return "converge", "granted"
        if ".minions/backlog.lock" in halt:
            return "converge", "halted on the backlog lock: resumes at Step 9"
        return "converge-halted", halt
    end = _run_end(runs, change)
    if end is not None and not _converge_done(runs, change):
        return "converge", f"unfinished run: {end}"
    if why := _unjudged(runs, tree, change):
        return "converge", why
    if not _ancestor(tree, default, "HEAD"):
        return "integrate", f"{default} is not an ancestor of HEAD"
    return "release", f"converge clean at HEAD; {default} is an ancestor"


def _check_build(version: Version, tree: Path) -> str | None:
    """Return why the build check fails, or None."""
    if unticked := _unticked(tree, version.change):
        return f"phase {unticked[0]} unticked"
    return "the tree is not clean" if _dirty(tree) else None


def _check_converge(primary: Path, version: Version, tree: Path) -> str | None:
    """Return why the converge check fails, or None."""
    runs = primary / ".minions"
    if halt := _converge_halt(runs, version.change):
        return f"the status log halts: {halt}"
    if not _converge_done(runs, version.change):
        return "the status log has no done"
    if why := _unjudged(runs, tree, version.change):
        return why
    return "the tree is not clean" if _dirty(tree) else None


def _check_integrate(primary: Path, version: Version, tree: Path) -> str | None:
    """Return why the integrate check fails, or None; an open merge names its note."""
    if _merge_open(tree):
        note = f".minions/integrate/{version.change}"
        if (primary / f"{note}.red").is_file():
            return f"integrate halted — red gate, see {note}.red"
        if (primary / f"{note}.md").is_file():
            return f"integrate halted — semantic conflict, see {note}.md"
        return "a merge is still open"
    default = default_branch(primary)
    subject = _subject(tree)
    if subject != f"chore(integrate): merge {default} into {version.change}":
        return f"HEAD is not the integrate commit: {subject}"
    if not _ancestor(tree, default, "HEAD"):
        return f"{default} is not an ancestor of HEAD"
    return None


def _check_release(primary: Path, version: Version, first_read: bool) -> str | None:
    """Return why the release check fails, or None."""
    default = default_branch(primary)
    if not _ancestor(primary, version.change, default):
        return f"{default} does not contain {version.change}"
    tag = _tag_of(primary, version.change)
    if tag is None:
        return f"{version.change} has no release commit"
    if not _tagged(primary, tag):
        return f"{tag} does not exist"
    tip = _git(primary, "rev-parse", f"refs/heads/{version.change}")
    own = _maybe(primary, "rev-parse", "-q", "--verify", f"refs/tags/{tag}^{{commit}}")
    if own != tip:
        return f"{tag} is not the tip of {version.change}"
    if _pushed(primary, version.change, tag, first_read) is False:
        return f"{tag} is not on origin"
    return None


def _config_held(cwd: Path) -> list[str]:
    """Return the keys in the repo's own git config that `CONFIG_PLAIN` lacks."""
    listed = _git(cwd, "config", "--list", "--show-scope", "--name-only")
    return [
        name
        for scope, _, name in (line.partition("\t") for line in listed.splitlines())
        if scope in ("local", "worktree") and not CONFIG_PLAIN.fullmatch(name)
    ]


def _lfs_wrote(cwd: Path, name: str) -> bool:
    """Return whether `name` holds the value LFS writes for it, and no other."""
    return name in LFS_CONFIG and set(
        _git(cwd, "config", "--get-all", name).splitlines()
    ) == {LFS_CONFIG[name]}


def _refuse_config_commands(cwd: Path) -> None:
    """Stop with 1 when the repo's own git config holds a key `CONFIG_PLAIN` lacks.

    A worker can write that file, and the conductor runs outside its sandbox. An LFS
    key stays where it is: with it gone, a run's push would send pointers alone.
    """
    if held := _config_held(cwd):
        remedy = "move it to the global config or remove it"
        if all(_lfs_wrote(cwd, name) for name in held):
            remedy = (
                "a run cannot upload LFS objects: keep the key, and release this repo"
                " by hand"
            )
        raise Stop(
            1,
            "conduct: halt — the repo's git config holds a key that could name a"
            f" program: {' '.join(dict.fromkeys(held))}; {remedy}",
        )


def _urls(primary: Path) -> Urls:
    """Return the URLs git would fetch and push `origin` with; no `origin`, none."""
    if "origin" not in _git(primary, "remote").split():
        return [], []
    fetch = _git(primary, "remote", "get-url", "--all", "origin")
    push = _git(primary, "remote", "get-url", "--all", "--push", "origin")
    return fetch.splitlines(), push.splitlines()


def _kept_file(primary: Path) -> Path:
    """Return the file holding the URLs a run kept for `primary`, in the home folder.

    No worker can write there, and a repo's config lasts past the run that wrote it.
    Why: 0052-security-hardening design D9.
    """
    return Path.home() / KEPT_ORIGINS / _digest(primary)


def _digest(primary: Path) -> str:
    """Return the name `primary`'s files take in the home folder, from its path."""
    return hashlib.sha256(str(primary.resolve()).encode()).hexdigest()[:16]


def _ledger(primary: Path) -> Path:
    """Return the release ledger's folder: one file per change, holding its head.

    Why: 0053-sandbox-patch design D2.
    """
    return Path.home() / KEPT_ORIGINS / f"{_digest(primary)}.released"


def _record_release(primary: Path, change: str, head: str) -> None:
    """Record `head` as the change's in the release ledger, over an older entry."""
    folder = _ledger(primary)
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    entry = folder / change
    entry.unlink(missing_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    with os.fdopen(os.open(entry, flags, 0o600), "w") as file:
        file.write(f"{head}\n")


def _ledger_entries(primary: Path) -> list[Path]:
    """Return the release ledger's entry files."""
    folder = _ledger(primary)
    return list(folder.iterdir()) if folder.is_dir() else []


def _ledger_heads(primary: Path) -> set[str]:
    """Return the heads the release ledger holds: each entry's first line."""
    return {entry.read_text().partition("\n")[0] for entry in _ledger_entries(primary)}


def _close_releases(primary: Path, base: str) -> None:
    """Remove ledger entries whose heads have landed on `base`, origin's default.

    This is cleanup alone: the push check independently excludes landed heads.
    Read ancestry in the clean scratch repo. Why: 0053-sandbox-patch design D2.
    """
    for entry in _ledger_entries(primary):
        head = entry.read_text().partition("\n")[0]
        if _history_ancestor(primary, head, base):
            entry.unlink()


def _kept_origin(primary: Path) -> Urls | None:
    """Return the URLs a run kept for `primary`, or None before its first."""
    file = _kept_file(primary)
    if not file.is_file():
        return None
    fetch, push = json.loads(file.read_text())
    return fetch, push


def _keep_origin(primary: Path) -> str | None:
    """Keep `origin`'s URLs before a repo's first worker; return why it could not.

    A file that stands stays. Owner-only: a URL can hold a key. Where the home folder
    refuses it, this process is itself in a sandbox, and nothing is kept. Beside the
    URLs it keeps the branch origin's own HEAD names, once, read through a kept URL;
    a repo kept before gains it here. Why: 0053-sandbox-patch design D2.
    """
    file = _kept_file(primary)
    urls = _urls(primary)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        file.parent.mkdir(mode=0o700, exist_ok=True)
        with os.fdopen(os.open(file, flags, 0o600), "w") as kept:
            json.dump(urls, kept)
    except FileExistsError:
        pass
    except OSError as error:
        return error.strerror or type(error).__name__
    fetch = (_kept_origin(primary) or ([], []))[0]
    named = _default_file(primary)
    try:
        name = _origin_head(primary, fetch[0]) if fetch and not named.exists() else None
        if name is not None:
            with os.fdopen(os.open(named, flags, 0o600), "w") as kept:
                kept.write(name)
    except (FileExistsError, Stop):
        pass
    except OSError as error:
        return error.strerror or type(error).__name__
    return None


def _default_file(primary: Path) -> Path:
    """Return the file holding the default branch's name a run kept for `primary`."""
    return Path.home() / KEPT_ORIGINS / f"{_digest(primary)}.default"


def _origin_head(primary: Path, url: str) -> str | None:
    """Return the branch `url`'s own HEAD names, or None when it names none.

    A read that fails stops with 1, nothing pushed.
    """
    done = _outside(primary, "ls-remote", "--symref", "--", url, "HEAD")
    if done.returncode != 0:
        raise Stop(1, "conduct: halt — cannot read origin: nothing pushed")
    for line in done.stdout.splitlines():
        ref, _, name = line.partition("\t")
        if name == "HEAD" and ref.startswith("ref: refs/heads/"):
            return ref.removeprefix("ref: refs/heads/")
    return None


def _push_default(primary: Path, url: str) -> str:
    """Return the default branch a push judges and pushes: the one origin's HEAD names.

    Never the local `refs/remotes/origin/HEAD`, which a worker writes. Once a run kept
    the name, origin's HEAD naming another halts, for a person to decide.
    Why: 0053-sandbox-patch design D2.
    """
    name = _origin_head(primary, url)
    file = _default_file(primary)
    kept = file.read_text() if file.is_file() else None
    if kept is not None and name != kept:
        remedy = f"a person decides, then removes ~/{KEPT_ORIGINS}/{file.name}"
        raise Stop(
            1,
            f"conduct: halt — origin's HEAD names {name or 'no branch'}, and the run"
            f" kept {kept}: {remedy}",
        )
    if name is None:
        raise Stop(
            1,
            "conduct: halt — origin's HEAD names no branch: a person pushes the default"
            " branch, or points origin's HEAD at it",
        )
    return name


def _refuse_origin(primary: Path) -> Urls:
    """Return `_urls`; stop with 1 unless a remote call can run only its own git.

    The URLs returned are the ones a run kept, once a run has: the comparison is on
    the value the caller uses, so a worker's toggle steers nothing. A fake worker's
    fixtures use a local `origin`, and a worker cannot set the conductor's
    environment. A halt names no URL: it can hold a key.
    """
    _refuse_config_commands(primary)
    fetch, push = _urls(primary)
    if _kept_origin(primary) not in (None, (fetch, push)):
        raise Stop(
            1,
            "conduct: halt — the repo's git config points origin away from the URLs a"
            " run kept: read `git remote -v`, then repoint it, or remove"
            f" ~/{KEPT_ORIGINS}/{_kept_file(primary).name} to keep what it reads now",
        )
    if os.environ.get("MF_SHIP_AGENT"):
        return fetch, push
    for url in (*fetch, *push):
        if not NETWORK_URL.fullmatch(url):
            raise Stop(
                1,
                "conduct: halt — the repo's git config points origin at a local"
                " repo, whose hooks would run on a push; repoint it",
            )
    return fetch, push


def _read_url(primary: Path, first_read: bool) -> str | None:
    """Return the URL a remote read goes to; None with no `origin`, or none it may read.

    A first read is a run's alone: `status`, `check` and `report` take the repo from
    git, which a worker steers, and a repo it puts inside a worktree no run kept.
    Why: 0052-security-hardening design D9.
    """
    fetch, _ = _refuse_origin(primary)
    readable = first_read or _kept_file(primary).is_file()
    return fetch[0] if fetch and readable else None


def _scratch() -> tempfile.TemporaryDirectory[str]:
    """Return a scratch folder in the home folder, which no worker can write.

    Where the home folder refuses it, this process is itself in a sandbox, and the
    temp folder serves.
    """
    prefix = ".mf-ship-remote-"
    try:
        return tempfile.TemporaryDirectory(dir=Path.home(), prefix=prefix)
    except OSError:
        return tempfile.TemporaryDirectory(prefix=prefix)


def _outside(
    primary: Path, *args: str, timeout: int = GIT_TIMEOUT
) -> subprocess.CompletedProcess[str]:
    """Return a remote git call finished from a scratch repo with `primary`'s objects.

    It reads the operator's global config and no repo's, so a key a worker sets after
    the refusal starts nothing. The caller passes a URL, not a remote's name, behind
    `--`. Why: 0052-security-hardening design D9.
    """
    with _scratch() as scratch:
        root = Path(scratch)
        _git(root, "init", "-q", "--bare", "--template=")
        alternates = root / "objects" / "info" / "alternates"
        objects = _git(
            primary, "rev-parse", "--path-format=absolute", "--git-path", "objects"
        )
        alternates.write_text(objects)
        env = {**os.environ, "GIT_DIR": scratch, "GIT_NO_REPLACE_OBJECTS": "1"}
        return _run(root, *args, env=env, timeout=timeout)


def _listed(primary: Path, url: str, *refs: str) -> str | None:
    """Return what `url` lists of its tags and `refs`, or None if it cannot be read."""
    done = _outside(primary, "ls-remote", "--tags", "--", url, *refs)
    return done.stdout if done.returncode == 0 else None


def _pushed(
    primary: Path, change: str, tag: str, first_read: bool = False
) -> bool | None:
    """Return whether origin's tag is on the branch's tip, or None with no origin.

    An `origin` this may not read lacks the tag, as one that cannot be read does.
    """
    if "origin" not in _git(primary, "remote").split():
        return None
    url = _read_url(primary, first_read)
    ref = f"refs/tags/{tag}"
    # Origin lists an annotated tag's own id on `ref`, and its commit only on `^{}`.
    listed = _listed(primary, url, ref, f"{ref}^{{}}") if url else None
    tip = _git(primary, "rev-parse", f"refs/heads/{change}").strip()
    lines = (listed or "").splitlines()
    return f"{tip}\t{ref}" in lines or f"{tip}\t{ref}^{{}}" in lines


def _history(primary: Path, *args: str) -> str:
    """Read raw object history in the conductor's clean scratch repo.

    Only alternates reach the primary: no ref, graft or shallow file does, and
    replacement is disabled. Why: 0053-sandbox-patch design D2.
    """
    done = _outside(primary, *args)
    if done.returncode != 0:
        raise Stop(2, f"conduct: cannot read release history: git {args[0]} failed")
    return done.stdout.strip()


def _history_ancestor(primary: Path, older: str, newer: str) -> bool:
    """Return whether raw object history places `older` at or before `newer`."""
    done = _outside(primary, "merge-base", "--is-ancestor", older, newer)
    if done.returncode not in (0, 1):
        raise Stop(2, "conduct: cannot read release history: git merge-base failed")
    return done.returncode == 0


def _release_tags(primary: Path) -> dict[str, tuple[str, str]]:
    """Snapshot version tags as `(ref sha, commit sha)`, peeling in scratch."""
    refs = _git(
        primary,
        "for-each-ref",
        "--format=%(refname:strip=2) %(objectname)",
        "refs/tags",
    )
    tags = {}
    for line in refs.splitlines():
        name, sha = line.split()
        if TAG.fullmatch(name):
            done = _outside(primary, "rev-parse", "--verify", f"{sha}^{{commit}}")
            if done.returncode == 0:
                tags[name] = (sha, done.stdout.strip())
    return tags


def _release_merge(primary: Path, tip: str, tags: dict[str, tuple[str, str]]) -> bool:
    """Return whether raw `tip` says `chore(release): <tag>` and holds that tag."""
    subject = _history(primary, "log", "-1", "--format=%s", tip)
    return any(
        tip == commit and subject == f"chore(release): {tag}"
        for tag, (_, commit) in tags.items()
    )


def _merges_a_release(
    primary: Path, sha: str, tags: dict[str, tuple[str, str]]
) -> bool:
    """Return whether raw `sha` merges a tagged release with that release's tree."""
    parents = _history(primary, "rev-list", "--parents", "-n", "1", sha).split()
    if len(parents) != 3 or not _release_merge(primary, parents[2], tags):
        return False
    trees = _history(primary, "rev-parse", f"{sha}^{{tree}}", f"{parents[2]}^{{tree}}")
    return len(set(trees.split())) == 1


def _has_origin(primary: Path) -> bool:
    """Return whether the repo has a remote named `origin`."""
    return "origin" in _git(primary, "remote").split()


def _no_release(default: str, name: str) -> Stop:
    """Return the halt for a commit or tag on the default branch no run released."""
    return Stop(
        1,
        f"conduct: halt — {default} holds {name}, no run's release: a person reads it,"
        f" then git push origin {name if TAG.fullmatch(name) else default}",
    )


def _foreign_commit(
    primary: Path,
    base: str,
    default: str,
    tip: str | None = None,
    tags: dict[str, tuple[str, str]] | None = None,
) -> list[str]:
    """Return the `default` branch's first-parent release merges past raw `base`.

    Each release's parent must be a ledger head not yet reachable from `base`.
    Only ref snapshots come from the primary; all history comes from scratch.
    Why: 0053-sandbox-patch design D2.
    """
    base = _git(primary, "rev-parse", "--verify", base).strip()
    tip = tip or _git(primary, "rev-parse", f"refs/heads/{default}").strip()
    tags = _release_tags(primary) if tags is None else tags
    heads = {
        head
        for head in _ledger_heads(primary)
        if not _history_ancestor(primary, head, base)
    }
    commits = _history(primary, "rev-list", "--first-parent", f"{base}..{tip}").split()
    for sha in commits:
        if not (
            _merges_a_release(primary, sha, tags)
            and _history(primary, "rev-parse", f"{sha}^2^") in heads
        ):
            raise _no_release(default, sha[:7])
    return commits


def _unpushed(primary: Path, first_read: bool = False) -> list[tuple[str, str]]:
    """Return each `(ref, sha)` to push.

    Judge history in scratch against origin's listed default sha. A run's read takes
    the default's name from origin's own HEAD; `status` takes it from git. With no
    read allowed, use the local remote ref and no tags. Cleanup has no security
    weight: landed ledger heads never authorize another release, however they landed.
    Why: 0053-sandbox-patch design D2.
    """
    url = _read_url(primary, first_read)
    if not _has_origin(primary):
        return []
    default = (
        _push_default(primary, url) if first_read and url else default_branch(primary)
    )
    done = (
        _outside(primary, "ls-remote", "--heads", "--tags", "--", url) if url else None
    )
    if done is None or done.returncode != 0:
        if done is not None and first_read:
            raise Stop(1, "conduct: halt — cannot read origin: nothing pushed")
        commits = _foreign_commit(primary, f"origin/{default}", default)
        return [(f"refs/heads/{default}", commits[0])] if commits else []
    held = {
        ref: sha
        for sha, ref in (
            line.split("\t", 1) for line in done.stdout.split("\n") if line
        )
    }
    base = held.get(f"refs/heads/{default}")
    if base is None:
        raise Stop(
            1, f"conduct: halt — origin has no {default}: a person pushes it first"
        )
    if _outside(primary, "cat-file", "-e", f"{base}^{{commit}}").returncode != 0:
        raise Stop(
            1,
            f"conduct: halt — origin's {default} is at {base[:7]}, which this repo"
            " lacks: a person fetches",
        )
    if first_read:
        _close_releases(primary, base)
    tip = _git(primary, "rev-parse", f"refs/heads/{default}").strip()
    tags = _release_tags(primary)
    commits = _foreign_commit(primary, base, default, tip, tags)
    found = [(f"refs/heads/{default}", tip)] if commits else []
    released = {_history(primary, "rev-parse", f"{sha}^2") for sha in commits}
    for tag, (sha, commit) in tags.items():
        ref = f"refs/tags/{tag}"
        if ref in held or not _history_ancestor(primary, commit, tip):
            continue
        if not _release_merge(primary, commit, {tag: (sha, commit)}) or (
            commit not in released and not _history_ancestor(primary, commit, base)
        ):
            raise _no_release(default, tag)
        found.append((ref, sha))
    return found


def _unread(primary: Path) -> bool:
    """Return whether `origin` could lack a merged tag only a run may read for.

    Nothing kept, so `status` read no `origin`. A merged tag makes a run worth starting,
    and that run keeps the URLs, so this holds once. Why: 0052-security-hardening
    design D9.
    """
    return (
        "origin" in _git(primary, "remote").split()
        and not _kept_file(primary).is_file()
        and any(
            TAG.fullmatch(tag)
            for tag in _git(primary, "tag", "--merged", default_branch(primary)).split()
        )
    )


def probe_gate(mark: Path) -> str:
    """Return the scratch `Makefile`: its gate passes when `mark` refuses a write.

    Why: 0053-sandbox-patch design D1.
    """
    target = shlex.quote(str(mark)).replace("$", "$$")
    return f"gate:\n\t! echo escaped >> {target}\n\ttouch .gated\n"


def check_probe(scratch: Path, mark: Path | None) -> str | None:
    """Return why the probe check fails, or None; the scratch gate leaves `.gated`.

    A `mark` gone or written fails, naming its executor: `probe-codex-41` → `codex`.
    `check probe` has no mark, and skips it. Why: 0053-sandbox-patch design D1.
    """
    if mark is not None and (not mark.is_file() or mark.stat().st_size):
        executor = mark.name.split("-")[1]
        return f"{executor} wrote outside its reach: it runs unsandboxed"
    held = _show(scratch, "HEAD", "probe.txt")
    if held is None:
        return "HEAD holds no probe.txt"
    if held.strip() != "ok":
        return f"probe.txt reads {held.strip()!r}"
    return None if (scratch / ".gated").is_file() else "make gate left no .gated"


def check(
    primary: Path, stage: str, version: Version, first_read: bool = False
) -> str | None:
    """Return why a station's check on disk fails, or None when it passes."""
    if stage == "release":
        return _check_release(primary, version, first_read)
    if version.tree is None:
        return f"{version.change} has no worktree"
    if stage == "build":
        return _check_build(version, version.tree)
    if stage == "converge":
        return _check_converge(primary, version, version.tree)
    return _check_integrate(primary, version, version.tree)


def verify_log(path: Path) -> str | None:
    """Return why a run log is incomplete, or None when it is complete."""
    lines = [
        line
        for line in path.read_text().splitlines()
        if line.strip() and not line.startswith("# ")
    ]
    spawned: dict[tuple[str, str], int] = {}
    last = detail = ""
    for line in lines:
        match = EVENT.match(line)
        if not match or match[2] not in EVENTS:
            return f"unknown event: {line}"
        who, last = match[1], match[2]
        detail = line[match.end() :]
        station = detail.split(" · ")[0]
        if last == "spawn":
            spawned[who, station] = spawned.get((who, station), 0) + 1
        elif last == "finish" and spawned.get((who, station)):
            spawned[who, station] -= 1
    for (who, station), count in spawned.items():
        if count and detail != STOPPED:
            return f"a spawn with no finish: {who} {station}"
    if last not in ("halt", "done"):
        return "the run ends on neither halt nor done"
    return None


class RunLog:
    """The run log: one event per line, appended under a lock directory."""

    def __init__(self, runs: Path, stamp: str) -> None:
        """Create `<stamp>.md` in `runs`, titled; `<stamp>-2.md`, … when taken."""
        runs.mkdir(parents=True, exist_ok=True)
        for n in itertools.count(1):
            self.stamp = stamp if n == 1 else f"{stamp}-{n}"
            self.path = runs / f"{self.stamp}.md"
            try:
                with self.path.open("x") as log:
                    log.write(f"# Ship run {self.stamp}\n\n")
                break
            except FileExistsError:
                continue
        self.lock = runs / f"{self.stamp}.lock"

    def event(self, who: str, event: str, detail: str) -> None:
        """Append `<HH:MM:SS> · <who> · <event> — <detail>`, the detail on one line."""
        detail = " ".join(detail.split())
        deadline = time.monotonic() + LOCK_SECONDS
        while True:
            try:
                self.lock.mkdir()
                break
            except FileExistsError:
                if time.monotonic() > deadline:
                    raise Stop(
                        2, f"conduct: cannot run — {self.lock.name} held"
                    ) from None
                time.sleep(0.05)
        try:
            with self.path.open("a") as log:
                log.write(f"{time.strftime('%H:%M:%S')} · {who} · {event} — {detail}\n")
        finally:
            self.lock.rmdir()


def _table(runs: Path, change: str, name: str) -> dict[str, object]:
    """Return a table of the cut's models file; no file or no table is empty."""
    path = runs / "models" / f"{change}.toml"
    if not path.is_file():
        return {}
    try:
        data = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as error:
        raise Stop(1, f"conduct: halt — models/{path.name}: {error}") from None
    table = data.get(name)
    return table if isinstance(table, dict) else {}


def _models(
    runs: Path, change: str, station: str, run: str
) -> tuple[str, str | None, str | None]:
    """Return the station's executor, model and effort from the cut's models file.

    Integrate uses the `[release]` table. An absent executor is the run's, `run`;
    an absent model or effort is None. A table no executor can run halts the version.
    """
    table = _table(runs, change, "release" if station == "integrate" else station)
    executor = table.get("executor", run)
    model, effort = table.get("model"), table.get("effort")
    model = model if isinstance(model, str) else None
    file = f"models/{change}.toml"
    if executor not in EXECUTORS:
        raise Stop(1, f"conduct: halt — {file}: executor {executor!r} unknown")
    if executor == "codex" and (model or "").startswith("claude"):
        raise Stop(1, f"conduct: halt — {file}: {station} on codex, model {model}")
    return str(executor), model, effort if isinstance(effort, str) else None


def _tier(runs: Path, change: str) -> str:
    """Return the converge prompt's tier clause, or "" when the cut set no tier.

    e.g. `tier = "high"` under `[converge]` → " with tier=high"

    Any value but `TIERS` halts: the models file is writable by a worker, and the
    value lands in the next worker's prompt.
    """
    tier = _table(runs, change, "converge").get("tier")
    if tier is None:
        return ""
    if tier not in TIERS:
        raise Stop(1, f"conduct: halt — models/{change}.toml: tier {tier!r} unknown")
    return f" with tier={tier}"


def reach(primary: Path) -> list[Path]:
    """Return what a worker may edit: the primary and each linked worktree.

    A path inside another stays covered and unlisted, so no listed path can be
    swapped for a symlink by a worker. Why: 0050-codex-review design D5.
    """
    root = primary.resolve()
    if _common_dir(root) is None:
        return [root]
    trees = [root]
    for path in sorted(_worktrees(root).values()):
        if not any(path.is_relative_to(tree) for tree in trees):
            trees.append(path)
    return trees


def ship_lines(primary: Path) -> ShipLines:
    """Return `AGENTS.md`'s `Ship tools:`, `Ship network:` and `Ship loopback:` lines.

    A `Ship network:` value that is not a plain domain stops with 1, and so does a
    `Ship loopback:` other than `yes`. Why: 0052-security-hardening design D2;
    0054-loopback design D1.
    """
    network = _agents_values(primary, "Ship network") or []
    for domain in network:
        if not DOMAIN.fullmatch(domain):
            raise Stop(
                1, f"conduct: halt — AGENTS.md: Ship network {domain!r} is not a domain"
            )
    loopback = _agents_flag(primary, "Ship loopback")
    if loopback not in (None, "yes"):
        raise Stop(
            1, f"conduct: halt — AGENTS.md: Ship loopback {loopback!r} is not yes"
        )
    tools = _agents_values(primary, "Ship tools") or []
    return ShipLines(tools, network, loopback == "yes")


def allowlist(trees: list[Path], tools: list[str]) -> tuple[list[str], list[str]]:
    """Return the Claude worker's allowed and denied rules, editing inside `trees`."""
    allowed = [
        *TOOLS,
        *(f"Edit(/{tree}/**)" for tree in trees),
        *(f"Bash({command}:*)" for command in (*COMMANDS, *tools)),
    ]
    denied = [
        *(f"Bash({command}:*)" for command in DENIED),
        # `denyRead` holds Bash alone: a path and what is under it, for the Read tool.
        *(f"Read({secret}{tail})" for secret in SECRETS for tail in ("", "/**")),
    ]
    for sub, flag in FORCED:
        forms = (
            *(f"git {sub} {flag}", f"git {sub} * {flag}"),
            f"git * {sub} {flag}",
            *((f"git * {sub} * {flag}",) if flag != "-" else ()),
        )
        denied += [f"Bash({form}*)" for form in forms]
    return allowed, denied


def _loopback_listeners() -> list[tuple[str, str]]:
    """Return each process listening on loopback, with its address, once each.

    e.g. "ollama 101 … TCP 127.0.0.1:11434 (LISTEN)" → [("ollama", "127.0.0.1:11434")]
    An `lsof` that fails, or prints what does not parse, gives ("lsof", "unavailable").
    """
    unavailable = [("lsof", "unavailable")]
    try:
        done = subprocess.run(
            ["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired):
        return unavailable
    rows = done.stdout.splitlines()
    if done.returncode == 1 and not rows:
        return []
    if done.returncode != 0 or not rows[0].startswith("COMMAND"):
        return unavailable
    found: list[tuple[str, str]] = []
    for row in rows[1:]:
        fields = row.split()
        if len(fields) < 3 or fields[-1] != "(LISTEN)":
            return unavailable
        process, address = fields[0], fields[-2]
        host = address.rpartition(":")[0]
        if host in ("*", "[::1]") or host.startswith("127."):
            found.append((process, address))
    return list(dict.fromkeys(found))


def worker_settings(
    primary: Path,
    trees: list[Path],
    common: Path | None,
    network: list[str],
    loopback: bool,
) -> str:
    """Return the Claude worker's sandbox settings, as JSON.

    A sandbox that cannot start ends the worker. `loopback` lets it bind and reach
    every local service. Why: 0052-security-hardening design D1, 0053-sandbox-patch
    design D1 and 0054-loopback design D1.
    """
    writes = [*(str(tree) for tree in trees), *([str(common)] if common else [])]
    sandbox = {
        "enabled": True,
        "failIfUnavailable": True,
        "allowUnsandboxedCommands": False,
        "filesystem": {"allowWrite": writes, "denyRead": list(SECRETS)},
        "credentials": {
            "envVars": [{"name": name, "mode": "deny"} for name in TOKENS],
        },
        "network": {
            "allowedDomains": [*NETWORK, *network],
            **({"allowLocalBinding": True} if loopback else {}),
        },
    }
    return json.dumps({"sandbox": sandbox})


def argv(
    executor: str,
    prompt: str,
    cwd: Path,
    model: str | None,
    effort: str | None,
    repo: Repo,
    lines: ShipLines | None = None,
) -> list[str]:
    """Return the worker's command line, the shell rules appended to the prompt.

    `MF_SHIP_AGENT` replaces the executor. A Codex worker halts when the primary's
    `.git` no longer resolves to the common directory in `repo`. A run passes its
    `lines`; without them, `AGENTS.md` is read here.
    """
    prompt = f"{prompt}\n\n{SHELL_RULES}"
    if agent := os.environ.get("MF_SHIP_AGENT"):
        return [*shlex.split(agent), prompt]
    primary, common = repo
    trees = reach(primary)
    cache = f"UV_CACHE_DIR={primary / '.minions' / 'uv-cache'}"
    if executor == "claude":
        tools, network, loopback = lines or ship_lines(primary)
        allowed, denied = allowlist(trees, tools)
        return [
            *("env", *HOOKS_OFF, cache),
            *("claude", "-p", prompt),
            *(("--model", model) if model else ()),
            *(("--effort", effort) if effort else ()),
            *("--output-format", "stream-json", "--verbose"),
            *(arg for tree in trees for arg in ("--add-dir", str(tree))),
            *("--settings", worker_settings(primary, trees, common, network, loopback)),
            # A worker can write the project's settings and `.mcp.json`, and each
            # runs at a start, outside the sandbox.
            # Why: 0052-security-hardening design D1.
            *("--setting-sources", "user"),
            *("--allowedTools", *allowed, "--disallowedTools", *denied),
        ]
    # Why: 0050-codex-review design D5.
    if common and _common_dir(primary) != common:
        raise Stop(1, "conduct: halt — the primary's .git moved during the run")
    roots = [*([str(common)] if common else []), *(str(tree) for tree in trees)]
    # Why: 0050-codex-review design D4.
    system = "/usr/bin:/bin:/usr/sbin:/sbin"
    path = f"PATH={system}:{os.environ.get('PATH', '')}"
    env = ("env", *HOOKS_OFF, cache, path)
    return [
        *env,
        *("codex", "exec"),
        *(("-m", model) if model else ()),
        *(("-c", f"model_reasoning_effort={effort}") if effort else ()),
        *("-s", "workspace-write"),
        *("-c", "allow_login_shell=false"),
        *("-c", f"sandbox_workspace_write.writable_roots={json.dumps(roots)}"),
        *("-c", "sandbox_workspace_write.network_access=false"),
        # A worker can write a tree's `.codex/`, and an untrusted tree's starts nothing.
        # Why: 0053-sandbox-patch design D6.
        *codex_trust([cwd, *trees], "untrusted"),
        *("-C", str(cwd), prompt),
    ]


def codex_trust(paths: list[Path], level: str) -> list[str]:
    """Return the `-c` that sets each path's Codex trust, as one `projects` table.

    e.g. `[/r], "untrusted"` → `["-c", 'projects={"/r"={trust_level="untrusted"}}']`.
    Why: 0053-sandbox-patch design D6.
    """
    keys = dict.fromkeys(str(path.resolve()) for path in paths)
    table = ",".join(
        f"{json.dumps(key)}={{trust_level={json.dumps(level)}}}" for key in keys
    )
    return ["-c", f"projects={{{table}}}"]


def work(
    command: list[str], cwd: Path, out: Path, claim: Path | None
) -> tuple[int, bool]:
    """Run one worker in its own process group, output to `out`, held in `claim`.

    Return its exit code and whether `TIMEOUT` killed it.
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as sink:
        try:
            worker = subprocess.Popen(
                command,
                cwd=cwd,
                stdin=subprocess.DEVNULL,
                stdout=sink,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        except FileNotFoundError:
            raise Stop(2, f"conduct: cannot run — {command[0]} is missing") from None
        group = claim / str(worker.pid) if claim else None
        try:
            if group:
                group.write_text(_ps(worker.pid, "lstart="))
            return worker.wait(timeout=TIMEOUT), False
        except subprocess.TimeoutExpired:
            os.killpg(worker.pid, signal.SIGKILL)
            return worker.wait(), True
        finally:
            if group:
                group.unlink(missing_ok=True)


def _text(content: object) -> str:
    """Return a tool result's text, from a string or a list of text blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            str(block.get("text", "")) for block in content if isinstance(block, dict)
        )
    return ""


def _call(block: dict[str, object]) -> str:
    """Return a tool use as `Name(argument)`.

    e.g. a Bash use of `rm -rf build` → "Bash(rm -rf build)"
    """
    given = block.get("input")
    fields = given if isinstance(given, dict) else {}
    argument = next(
        (
            str(fields[key])
            for key in ("command", "file_path", "pattern")
            if key in fields
        ),
        "",
    )
    return f"{block.get('name')}({argument})"


def denials(log: Path) -> list[str]:
    """Return each tool use a worker's stream-json log shows denied."""
    uses: dict[str, str] = {}
    found: list[str] = []
    with log.open(errors="replace") as lines:
        for line in lines:
            if '"tool_use"' not in line and '"is_error"' not in line:
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            message = event.get("message") if isinstance(event, dict) else None
            content = message.get("content") if isinstance(message, dict) else None
            for block in content if isinstance(content, list) else []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    uses[str(block.get("id"))] = _call(block)
                elif block.get("type") == "tool_result" and block.get("is_error"):
                    text = _text(block.get("content"))
                    if any(denial in text for denial in DENIALS):
                        use = uses.get(str(block.get("tool_use_id")))
                        found.append(use or text.strip())
    return found


def usage_limit(log: Path) -> str:
    """Return ` · stopped by a usage limit · resets <time>`, or "" for any other exit.

    e.g. a `result` event with `api_error_status: 429`, its text naming `resets 5:50pm`
    """
    with log.open(errors="replace") as lines:
        for line in lines:
            if '"api_error_status"' not in line:
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if (
                isinstance(event, dict)
                and event.get("type") == "result"
                and event.get("is_error")
                and event.get("api_error_status") == 429
            ):
                resets = re.search(r"resets (.+)", str(event.get("result")))
                named = f" · resets {resets[1]}" if resets else ""
                return f" · stopped by a usage limit{named}"
    return ""


def _executor_missing(executor: str) -> bool:
    """Return whether neither `MF_SHIP_AGENT` nor the executor's CLI is there."""
    return not os.environ.get("MF_SHIP_AGENT") and shutil.which(executor) is None


def _ps(pid: int, field: str) -> str:
    """Return the `ps` field for `pid`, or "" when it cannot.

    A claim compares start times across processes, and `lstart` follows the caller's
    zone and locale, so both are fixed here.
    e.g. 501, "comm=" → "claude"
    """
    command = ["ps", "-o", field, "-p", str(pid)]
    try:
        done = subprocess.run(
            command,
            capture_output=True,
            encoding="utf-8",
            env={**os.environ, "LC_ALL": "C", "TZ": "UTC0"},
            errors="replace",
            timeout=GIT_TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return done.stdout.strip()


def _started(pid: int) -> str:
    """Return the start time of `pid`, above 1, or "" when it is gone.

    A failed `ps` is not a dead process: one still running stops with 2.
    """
    if started := _ps(pid, "lstart="):
        return started
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, OverflowError):
        return ""
    except PermissionError:
        pass
    raise Stop(2, f"conduct: cannot run — ps cannot read pid {pid}, which is running")


def _conductor(active: Path) -> int | None:
    """Return the claim's pid while it keeps the claim's start time, else None.

    After a reboot the number can name any process, and a worker can write the claim:
    to `kill`, 0 is the caller's group and -1 every process the operator owns.
    """
    try:
        pid = int((active / "pid").read_text())
        held = (active / "start").read_text().strip()
    except (OSError, ValueError):
        return None
    return pid if pid > 1 and held and held == _started(pid) else None


def _claim(active: Path) -> str:
    """Return `none`, `live` or `stale`: stale names no conductor still running."""
    if not active.exists():
        return "none"
    return "stale" if _conductor(active) is None else "live"


def _clear(active: Path) -> None:
    """Kill the stale claim's worker groups, then remove it.

    A group goes only while its leader keeps the start time the entry holds and is
    an executor: after a reboot its number can name any process. A group that keeps
    its start time and names no executor, or refuses the kill, stops the run and
    leaves the claim, so no worker races the next one.
    """
    foreign = []
    for entry in active.iterdir():
        # A worker can write the claim, and group 0 is this process's own.
        if entry.is_file() and entry.name.isdecimal() and int(entry.name) > 1:
            group = int(entry.name)
            held = entry.read_text(errors="replace").strip()
            if not held or held != _started(group):
                continue
            leader = _ps(group, "comm=")
            if not any(executor in leader for executor in EXECUTORS):
                foreign.append(f"{group} ({leader})")
                continue
            try:
                os.killpg(group, signal.SIGKILL)
            except ProcessLookupError:
                continue
            except (OSError, OverflowError) as error:
                raise Stop(
                    2,
                    f"conduct: cannot clear the claim — worker group {group}"
                    f" survives: {error}",
                ) from None
    if foreign:
        raise Stop(
            2,
            f"conduct: cannot clear the claim — worker group {', '.join(foreign)}"
            " names no executor: read it, then kill it or remove its entry in"
            " .minions/runs/active",
        )
    shutil.rmtree(active)


def _unlinked(executor: str) -> None:
    """Stop with 2 when a skill beside this one is not linked where `executor` looks.

    A fake worker loads no skill.
    """
    if os.environ.get("MF_SHIP_AGENT"):
        return
    linked = Path.home() / SKILLS[executor]
    for skill in sorted(Path(__file__).resolve().parents[1].parent.glob("mf-*")):
        if skill.is_dir() and not (linked / skill.name).exists():
            raise Stop(
                2, f"run: cannot run — {skill.name} is not linked; make install-skills"
            )


def preconditions(cwd: Path, executor: str) -> Path:
    """Return the primary checkout once every run precondition holds; else exit 2."""
    top = _maybe(cwd, "rev-parse", "--show-toplevel")
    common = _common_dir(cwd)
    # Why: 0050-codex-review design D5.
    if (
        top is None
        or common is None
        or Path(top.strip()).resolve() != common.parent
        or not cwd.resolve().is_relative_to(common.parent)
    ):
        raise Stop(2, "run: cannot run — the cwd is not the primary checkout")
    primary = common.parent
    default = default_branch(primary)
    if (branch := _git(primary, "branch", "--show-current").strip()) != default:
        raise Stop(2, f"run: cannot run — on {branch or 'no branch'}, not {default}")
    # A held key halts at `push_left`, in the run's log, before any `git status`.
    if not _config_held(primary) and _dirty(primary):
        raise Stop(2, "run: cannot run — the primary's tree is not clean")
    if not _agents_values(primary, "Worktrees"):
        raise Stop(2, "run: cannot run — AGENTS.md declares no **Worktrees:**")
    if _executor_missing(executor):
        raise Stop(2, f"run: cannot run — {executor} is not on PATH")
    _unlinked(executor)
    if _claim(primary / ".minions" / "runs" / "active") == "live":
        raise Stop(2, "run: cannot run — a run is live: .minions/runs/active exists")
    return primary


class Run:
    """One ship run: the probe, then every open version to the default branch."""

    def __init__(self, primary: Path, executor: str) -> None:
        """Load `integrate.py`, and open the run log in the primary's run directory."""
        self.delta = runpy.run_path(str(INTEGRATE))["delta"]
        self.git_state = _git_state(primary)
        self.pushes = (_kept_origin(primary) or _urls(primary))[1]
        self.primary = primary
        self.repo = _repo(primary)
        self.executor = executor
        self.runs = primary / ".minions" / "runs"
        self.log = RunLog(self.runs, time.strftime(STAMP))
        self.halts: list[tuple[str, str]] = []
        self.blocked: list[str] = []
        self.released: list[str] = []
        self.plan: dict[tuple[str, str], tuple[str, str | None, str | None]] = {}
        self.lines = ShipLines([], [], False)
        self.held: dict[str, str] = {}
        self.guard = threading.Lock()
        self.merging = threading.Lock()

    def halt(self, who: str, reason: str) -> None:
        """Record and log a halt; its version starts no new worker."""
        with self.guard:
            self.halts.append((who, reason))
        self.log.event(who, "halt", reason)

    def block(self, change: str, dependency: str) -> None:
        """Record and log a block; `change` starts no worker."""
        with self.guard:
            self.blocked.append(change)
        self.log.event(change, "blocked", f"by {dependency}")

    def stopped(self, change: str) -> bool:
        """Return whether a halt names `change` or the run."""
        with self.guard:
            return any(who in ("run", change) for who, _ in self.halts)

    def closing(self) -> str:
        """Return the closing line's detail: what halted, is blocked and released."""
        halted = " ".join(dict.fromkeys(who for who, _ in self.halts)) or "none"
        blocked = " ".join(self.blocked) or "none"
        released = " ".join(self.released) or "none"
        return f"halted {halted} · blocked {blocked} · released {released}"

    def spawn(
        self,
        who: str,
        station: str,
        cwd: Path,
        prompt: str,
        models: tuple[str, str | None, str | None],
        repo: Repo | None = None,
    ) -> list[str] | None:
        """Run one worker and log it and its denials; `repo` defaults to the run's.

        Return the denials, or None when a timeout or a failed exit halted `who`.
        """
        executor, model, effort = models
        command = argv(
            executor, prompt, cwd, model, effort, repo or self.repo, self.lines
        )
        other = f" · executor {executor}" if executor != self.executor else ""
        self.log.event(who, "spawn", f"{station} · model {model or 'default'}{other}")
        out = self.runs / self.log.stamp / f"{who}_{station}.log"
        started = time.monotonic()
        code, killed = work(command, cwd, out, self.runs / "active")
        seconds = round(time.monotonic() - started)
        self.log.event(who, "finish", f"{station} · exit {code} · {seconds}s")
        denied = denials(out)
        for call in denied:
            self.log.event(who, "denied", f"{station} · {call}")
        if killed:
            self.halt(
                who, f"{station} timed out after {TIMEOUT}s; its group was killed"
            )
            return None
        if code != 0:
            self.halt(who, f"{station} worker exit {code}{usage_limit(out)}")
            return None
        return denied

    def judge(
        self, who: str, stage: str, reason: str | None, denied: list[str]
    ) -> bool:
        """Log a station's check; a failure halts, naming the denials before it."""
        result = "pass" if reason is None else f"fail — {reason}"
        self.log.event(who, "check", f"{stage} · {result}")
        if reason is None:
            return True
        named = f" · denied: {', '.join(denied)}" if denied else ""
        self.halt(who, f"{stage} check fail — {reason}{named}")
        return False

    def advance(self, version: Version, stop_at: tuple[str, ...]) -> None:
        """Run the version's stations to a stage in `stop_at`, a release or a halt."""
        try:
            while not self.stopped(version.change):
                stage, why = stage_of(self.primary, version)
                if stage in STUCK:
                    self.halt(version.change, f"{stage} — {why}")
                    return
                if stage in stop_at:
                    return
                if stage == "integrate" and _has_origin(self.primary):
                    default = default_branch(self.primary)
                    _foreign_commit(self.primary, f"origin/{default}", default)
                cwd = self.primary if stage == "integrate" else version.tree
                if cwd is None:
                    self.halt(version.change, f"{version.change} has no worktree")
                    return
                minions = self.primary / ".minions"
                tier = _tier(minions, version.change) if stage == "converge" else ""
                granted = minions / "grants" / version.change
                if stage == "converge" and granted.is_file():
                    tier += " and grant=yes"
                    granted.unlink()
                prompt = PROMPTS[stage].format(change=version.change, tier=tier)
                models = _models(minions, version.change, stage, self.executor)
                if models != self.plan.get((version.change, stage)):
                    raise Stop(
                        1,
                        f"conduct: halt — models/{version.change}.toml changed during"
                        " the run",
                    )
                if stage == "release" and _tag_of(self.primary, version.change) is None:
                    head = _git(cwd, "rev-parse", "HEAD").strip()
                    _record_release(self.primary, version.change, head)
                    self.log.event(version.change, "ledger", f"{version.change} {head}")
                denied = self.spawn(version.change, stage, cwd, prompt, models)
                if denied is None:
                    return
                if stage == "release" and not self.push_left():
                    return
                reason = check(self.primary, stage, version, first_read=True)
                if not self.judge(version.change, stage, reason, denied):
                    return
                if stage == "release":
                    if tag := _tag_of(self.primary, version.change):
                        self.released.append(tag)
                    return
        except Stop as stop:
            self.halt(version.change, str(stop))
        except Exception as error:
            self.halt("run", f"conduct.py failed: {error}")

    def ready(self, version: Version, threads: dict[str, threading.Thread]) -> bool:
        """Wait for the version's dependencies, then bring the default branch in."""
        change, default = version.change, default_branch(self.primary)
        after = _dependencies(self.primary, change)
        for dependency in after:
            if dependency in threads and _change_number(dependency) < version.number:
                threads[dependency].join()
        if self.stopped(change):
            return False
        for dependency in after:
            if not _shipped(self.primary, default, dependency):
                self.block(change, dependency)
                return False
        tree = version.tree
        if tree and not all(_shipped(tree, "HEAD", name) for name in after):
            self.merge_in(tree, change, default)
        return True

    def merge_in(self, tree: Path, change: str, default: str) -> None:
        """Merge the default branch into a dependent, once the delta check passes.

        A requirement both sides changed leaves the merge open with its note, which
        `stage_of` reads as an `integrating` halt.
        """
        if changed := _config_changed(self.primary, self.git_state):
            raise changed
        note = self.primary / ".minions" / "integrate" / f"{change}.md"
        opened = _merge_open(tree)
        if opened and note.is_file():
            return
        _refuse_config_commands(tree)
        if not opened:
            _git(tree, "merge", "-q", "--no-ff", "--no-commit", default)
        if moved := _delta(self.delta, tree):
            note.parent.mkdir(parents=True, exist_ok=True)
            note.write_text(_note(tree, change, moved))
            return
        message = f"chore(integrate): merge {default} into {change}"
        _git(tree, "commit", "-q", "-m", message, "-m", f"Change: {change}")

    def take(self, version: Version, threads: dict[str, threading.Thread]) -> None:
        """Take one version to its release, a halt or a block."""
        try:
            if station := self.held.get(version.change):
                raise Stop(1, NEEDS_CLAUDE.format(station))
            for station in STATIONS:
                _models(
                    self.primary / ".minions", version.change, station, self.executor
                )
            if not self.ready(version, threads):
                return
            self.advance(version, ("integrate", "release"))
            if not self.stopped(version.change):
                with self.merging:
                    self.advance(version, ())
        except Stop as stop:
            self.halt(version.change, str(stop))
        except Exception as error:
            self.halt("run", f"conduct.py failed: {error}")

    def read_plan(self, versions: list[Version]) -> None:
        """Read each station's models and `AGENTS.md`'s `Ship` lines, once.

        A worker can write both. A table `_models` refuses stays out of the plan, and
        so does a loopback repo's version with a Codex station: each halts in `take`.
        Why: 0052-security-hardening design D4; 0054-loopback design D2.
        """
        self.lines = ship_lines(self.primary)
        if self.lines.loopback and self.executor == "codex":
            raise Stop(1, NEEDS_CLAUDE.format("the run"))
        for version, station in itertools.product(versions, STATIONS):
            try:
                models = _models(
                    self.primary / ".minions", version.change, station, self.executor
                )
            except (Stop, ValueError):
                continue
            if self.lines.loopback and models[0] == "codex":
                self.held.setdefault(version.change, station)
            self.plan[version.change, station] = models
        self.plan = {
            key: models for key, models in self.plan.items() if key[0] not in self.held
        }

    def executors(self) -> list[str]:
        """Return the run's executor, then each other one the plan names."""
        named = (executor for executor, *_ in self.plan.values())
        return list(dict.fromkeys((self.executor, *named)))

    def probe(self, executor: str) -> None:
        """Prove a sandboxed worker edits, commits and gates a scratch repo, or halt."""
        station = "probe" if executor == self.executor else f"probe-{executor}"
        if _executor_missing(executor):
            self.halt("run", f"{station} — {executor} is not on PATH")
            return
        try:
            _unlinked(executor)
        except Stop as stop:
            self.halt("run", f"{station} — {stop}")
            return
        scratch = Path(tempfile.mkdtemp(prefix="mf-ship-probe-")).resolve()
        mark = Path.home() / KEPT_ORIGINS / f"probe-{executor}-{os.getpid()}"
        try:
            try:
                mark.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                mark.unlink(missing_ok=True)
                os.close(os.open(mark, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600))
            except OSError as error:
                self.halt(
                    "run", f"{station} — cannot write the probe mark: {error.strerror}"
                )
                return
            _git(scratch, "init", "-q", "-b", "main")
            (scratch / "Makefile").write_text(probe_gate(mark))
            (scratch / ".gitignore").write_text(".gated\n")
            _git(scratch, "add", "Makefile", ".gitignore")
            _git(scratch, *SCRATCH_IDENTITY, "commit", "-q", "-m", "init")
            models = (executor, None, None)
            repo = _repo(scratch)
            denied = self.spawn("run", station, scratch, PROBE, models, repo)
            if denied is not None:
                self.judge("run", station, check_probe(scratch, mark), denied)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
            mark.unlink(missing_ok=True)

    def push_left(self) -> bool:
        """Push what a release merged and left; return False when that halted the run.

        A refusal or a rejection halts it, and so does a changed config, before any
        remote call: the URLs are the ones read before the first worker, so a worker
        steers none. A held key is refused first, so the halt names it. The default
        branch is the one origin's HEAD names, and the one a run kept. Its push
        removes entries whose heads are now on it; a head already there authorizes
        nothing even when cleanup did not run.
        Why: 0052-security-hardening design D9; 0053-sandbox-patch design D2.
        """
        try:
            _refuse_config_commands(self.primary)
            if self.pushes and (
                changed := _config_changed(self.primary, self.git_state)
            ):
                raise changed
            unpushed = _unpushed(self.primary, first_read=True)
        except Stop as stop:
            self.halt("run", str(stop))
            return False
        for ref, sha in unpushed:
            kind, name = ref.split("/", 2)[1:]
            for url in self.pushes:
                done = _outside(
                    self.primary,
                    *("push", "--no-verify", "--", url, f"{sha}:{ref}"),
                    timeout=PUSH_TIMEOUT,
                )
                if done.returncode != 0:
                    self.halt(
                        "run", f"git push origin {name} failed, exit {done.returncode}"
                    )
                    return False
            self.log.event("run", "push", name)
            if kind == "heads":
                _git(self.primary, "update-ref", f"refs/remotes/origin/{name}", sha)
                _close_releases(self.primary, sha)
        return True

    def ship(self) -> int:
        """Run the loop; return 0 when every version shipped, else 1."""
        versions = open_versions(self.primary)
        worker = " · worker MF_SHIP_AGENT" if os.environ.get("MF_SHIP_AGENT") else ""
        names = " ".join(version.change for version in versions) or "none"
        self.log.event(
            "run",
            "start",
            f"executor {self.executor} · permissions: sandbox{worker}"
            f" · versions {names}",
        )
        self.push_left()
        if self.halts:
            self.log.event("run", "halt", self.closing())
            return 1
        if unkept := _keep_origin(self.primary):
            self.log.event("run", "unkept", unkept)
        if (age := _clear_stale_lock(self.primary)) is not None:
            self.log.event("run", "unlock", f".minions/backlog.lock, {age}s old")
        if not versions:
            self.log.event("run", "done", "nothing to ship")
            return 0
        try:
            self.read_plan(versions)
        except Stop as stop:
            self.halt("run", str(stop))
            self.log.event("run", "halt", self.closing())
            return 1
        if self.lines.loopback:
            for process, address in _loopback_listeners():
                self.log.event("run", "loopback", f"{process} {address}")
        stages = {
            version.change: stage_of(self.primary, version) for version in versions
        }
        if all(stage in STUCK for stage, _ in stages.values()):
            for change, (stage, why) in stages.items():
                if stage == "waiting":
                    self.block(change, why.removeprefix("after ").split()[0])
                else:
                    self.halt(change, f"{stage} — {why}")
        else:
            for executor in self.executors():
                self.probe(executor)
                if self.halts:
                    break
        if not (self.halts or self.blocked):
            threads: dict[str, threading.Thread] = {}
            for version in versions:
                threads[version.change] = threading.Thread(
                    target=self.take, args=(version, threads)
                )
            for thread in threads.values():
                thread.start()
            for thread in threads.values():
                thread.join()
        if self.halts or self.blocked:
            self.log.event("run", "halt", self.closing())
            return 1
        self.log.event("run", "done", f"released {' '.join(self.released)}")
        return 0


def run(cwd: Path, executor: str, detach: bool) -> int:
    """Start the loop, claimed by `.minions/runs/active`; detached, return at once.

    A stale claim is cleared before the detach, so what stops that reaches the caller.
    """
    primary = preconditions(cwd, executor)
    if not (started := _ps(os.getpid(), "lstart=")):
        raise Stop(2, "run: cannot run — ps cannot read this run's start time")
    runs = primary / ".minions" / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    active = runs / "active"
    if _claim(active) == "stale":
        _clear(active)
    if detach:
        with (runs / "detached.log").open("a") as sink:
            child = subprocess.Popen(
                [sys.executable, str(Path(__file__).resolve()), "run"]
                + ["--executor", executor],
                cwd=primary,
                stdin=subprocess.DEVNULL,
                stdout=sink,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        print(f"run: started · pid {child.pid}")
        return 0
    try:
        active.mkdir()
    except FileExistsError:
        raise Stop(
            2, "run: cannot run — a run is live: .minions/runs/active exists"
        ) from None
    try:
        (active / "start").write_text(started)
        (active / "pid").write_text(str(os.getpid()))
        conductor = Run(primary, executor)
        try:
            code = conductor.ship()
        except Exception as error:
            conductor.log.event("run", "halt", f"conduct.py failed: {error}")
            code = 1
        ended = "done" if code == 0 else "halt"
        print(f"run: {ended} · .minions/runs/{conductor.log.stamp}.md")
        return code
    finally:
        shutil.rmtree(active)


def stop_run(cwd: Path) -> str:
    """End the live run: the conductor first, so it spawns nothing more.

    The claim's groups go next, then a last line in the newest run log. Return that
    log. A group `_clear` cannot end stops with its exit, the claim kept and the line
    written: with the conductor dead, a second stop could not write it. Why:
    0051-reliability-paydown design D5.
    """
    runs = primary_of(cwd) / ".minions" / "runs"
    active = runs / "active"
    if (pid := _conductor(active)) is None:
        return "stop: none — no run is live"
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except PermissionError as error:
        raise Stop(2, f"stop: cannot run — the conductor survives: {error}") from None
    try:
        _clear(active)
    except Stop as stop:
        _log_stop(runs)
        raise Stop(stop.code, f"stop: conductor stopped · {stop}") from None
    if (log := _log_stop(runs)) is None:
        return "stop: stopped · no run log"
    return f"stop: stopped · .minions/runs/{log.name}"


def _log_stop(runs: Path) -> Path | None:
    """Append the stop to the newest run log; return that log, or None with none."""
    if (log := last_log(runs)) is not None:
        with log.open("a") as file:
            file.write(f"{time.strftime('%H:%M:%S')} · run · halt — {STOPPED}\n")
    return log


def grant(cwd: Path, change: str, executor: str) -> int:
    """Record one more round for a version halted at the cap, then start a run."""
    primary = primary_of(cwd)
    if (version := find_version(primary, change)) is None:
        raise Stop(2, f"grant: cannot run — no version branch holds {change}")
    stage, why = stage_of(primary, version)
    if stage != "converge-halted" or "cap reached" not in why:
        raise Stop(2, f"grant: cannot run — {change} is at {stage}, not a cap halt")
    preconditions(cwd, executor)
    grants = primary / ".minions" / "grants"
    grants.mkdir(parents=True, exist_ok=True)
    (grants / change).touch()
    return run(cwd, executor, True)


def agent(cwd: Path, executor: str, prompt: str) -> int:
    """Run one worker in `cwd` under the run's permissions; return its exit code."""
    if _executor_missing(executor):
        raise Stop(2, f"agent: cannot run — {executor} is not on PATH")
    stamp = time.strftime(STAMP)
    repo = _repo(cwd)
    out = repo[0] / ".minions" / "runs" / f"agent-{stamp}.log"
    code, killed = work(argv(executor, prompt, cwd, None, None, repo), cwd, out, None)
    for denied in denials(out):
        print(f"agent: denied — {denied}")
    print(f"agent: exit {code}{' · timed out' if killed else ''} · {out}")
    return 1 if killed else code


def status(cwd: Path) -> str:
    """Return the claim and unpushed lines, then `<change-id> · <stage>` per version."""
    primary = primary_of(cwd)
    claim = _claim(primary / ".minions" / "runs" / "active")
    lines = {
        "none": [],
        "live": ["run · live"],
        "stale": ["run · stale — a run clears it, or stops naming why"],
    }[claim]
    unpushed = _unpushed(primary)
    if unpushed:
        names = (ref.split("/", 2)[2] for ref, _ in unpushed)
        lines.append(f"run · unpushed {' '.join(names)}")
    if _unread(primary):
        lines.append("run · unread — a run reads origin's tags, and keeps its URLs")
    lines += [
        f"{version.change} · {stage_of(primary, version)[0]}"
        for version in open_versions(primary)
    ]
    return "\n".join(lines) or "status: none — no open version"


def _merge_commit(primary: Path, version: Version) -> str | None:
    """Return the default branch's merge of the version's tip, or None."""
    tip = _git(primary, "rev-parse", version.change).strip()
    merges = _git(primary, "log", default_branch(primary), "--merges", "--format=%h %P")
    for line in merges.splitlines():
        short, *parents = line.split()
        if tip in parents[1:]:
            return short
    return None


def _cards(backlog: Path, change: str) -> list[str]:
    """Return the ids of the cards under the change's backlog heading.

    e.g. "- **0016·R5 — a title**" → "0016·R5"
    """
    ids: list[str] = []
    inside = False
    for line in backlog.read_text().splitlines() if backlog.is_file() else []:
        if line.startswith("## "):
            inside = line.strip() == f"## {change}"
        elif inside and (card := re.match(r"- \*\*(\S+) — ", line)):
            ids.append(card[1])
    return ids


def _log_order(log: Path) -> tuple[str, int, str]:
    """Return a run log's sort key, oldest first.

    e.g. `20261029-163000.md` sorts before `20261029-163000-2.md`
    """
    return log.stem[:15], len(log.stem), log.stem


def last_log(runs: Path) -> Path | None:
    """Return the newest run log in `runs`, or None.

    e.g. `20261029-163000.md`, `20261029-163000-2.md` → the second
    """
    logs = list(runs.glob("*.md"))
    if not logs:
        return None
    return max(logs, key=_log_order)


def _change_number(change: str) -> int:
    """Return a change id's number.

    e.g. "0002-marks" → 2
    """
    return int(change.split("-")[0])


def report(cwd: Path) -> str:
    """Return the last run's close-out: per version, its halts, then its last line."""
    primary = primary_of(cwd)
    runs = primary / ".minions"
    if (log := last_log(runs / "runs")) is None:
        return "report: none — no run yet"
    events = [
        found for line in log.read_text().splitlines() if (found := EVENT.match(line))
    ]
    closing = events[-1].string if events else f"{log.name}: no event"
    blocked = {
        found[1]: found.string[found.end() :]
        for found in events
        if found[2] == "blocked"
    }
    touched = dict.fromkeys(found[1] for found in events if found[1] != "run")
    denied: dict[str, list[str]] = {}
    for found in events:
        if found[2] == "denied":
            call = found.string[found.end() :].split(" · ", 1)[-1]
            denied.setdefault(found[1], []).append(call)
    lines = [f"run · denied {', '.join(denied['run'])}"] if "run" in denied else []
    for change in sorted(touched, key=_change_number):
        version = find_version(primary, change)
        if version is None:
            lines.append(f"{change} · no version branch")
            continue
        tag = _tag_of(primary, change)
        if tag is not None and not _tagged(primary, tag):
            tag = None
        pushed = _pushed(primary, change, tag) if tag is not None else False
        review = runs / "findings" / f"{change}_review.md"
        round_ = _frontmatter(review.read_text(), "round") if review.is_file() else None
        page = runs / "metrics" / f"{change}.html"
        lines.append(
            " · ".join(
                [
                    change,
                    tag or "no tag",
                    f"merge {_merge_commit(primary, version) or 'none'}",
                    {None: "no origin", True: "pushed", False: "not pushed"}[pushed],
                    f"round {round_ or 'none'}",
                    f"cards {' '.join(_cards(runs / 'backlog.md', change)) or 'none'}",
                    f"denied {', '.join(denied.get(change, [])) or 'none'}",
                    f".minions/metrics/{change}.html"
                    if page.is_file()
                    else "metrics: none",
                    *([f"blocked {blocked[change]}"] if change in blocked else []),
                ]
            )
        )
    lines += [found.string for found in events[:-1] if found[2] == "halt"]
    lines.append(closing)
    return "\n".join(lines)


def main(argv_: list[str] | None = None) -> int:
    """Run one command; return its exit code."""
    parser = argparse.ArgumentParser(
        prog="conduct.py",
        usage="conduct.py <command> [<args>]",
        description="Take every cut version to the default branch, unattended.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "status", help="the claim, what is unpushed, and each open version's stage"
    )
    checking = commands.add_parser("check", help="exit 0 when disk proves the stage")
    checking.add_argument("stage", choices=(*STATIONS, "probe"))
    checking.add_argument("change_id", metavar="change-id")
    logging = commands.add_parser("log", help="exit 0 when a run log is complete")
    logging.add_argument("--verify", required=True, metavar="run-log")
    running = commands.add_parser("run", help="the loop")
    running.add_argument("--executor", required=True, choices=("claude", "codex"))
    running.add_argument("--detach", action="store_true")
    commands.add_parser("stop", help="end the live run")
    granting = commands.add_parser("grant", help="one more round past the cap")
    granting.add_argument("change_id", metavar="change-id")
    granting.add_argument("--executor", required=True, choices=("claude", "codex"))
    agenting = commands.add_parser("agent", help="one worker in the cwd")
    agenting.add_argument("--executor", required=True, choices=("claude", "codex"))
    agenting.add_argument("prompt")
    commands.add_parser("report", help="the last run's close-out lines")
    args = parser.parse_args(argv_)
    cwd = Path.cwd()
    try:
        if args.command == "status":
            print(status(cwd))
        elif args.command == "check":
            return _check_command(cwd, args.stage, args.change_id)
        elif args.command == "log":
            if why := verify_log(Path(args.verify)):
                print(f"log: incomplete — {why}")
                return 1
            print("log: complete")
        elif args.command == "run":
            return run(cwd, args.executor, args.detach)
        elif args.command == "stop":
            print(stop_run(cwd))
        elif args.command == "grant":
            return grant(cwd, args.change_id, args.executor)
        elif args.command == "agent":
            return agent(cwd, args.executor, args.prompt)
        else:
            print(report(cwd))
    except Stop as stop:
        print(stop)
        return stop.code
    return 0


def _check_command(cwd: Path, stage: str, target: str) -> int:
    """Print a stage's check; return 0 on pass, 1 on fail.

    `probe` takes the scratch repo's path instead of a change id.
    """
    if stage == "probe":
        reason = check_probe(Path(target), None)
    else:
        primary = primary_of(cwd)
        if (version := find_version(primary, target)) is None:
            raise Stop(2, f"check: cannot run — no version branch holds {target}")
        reason = check(primary, stage, version)
    print(f"check: {stage} · {'pass' if reason is None else f'fail — {reason}'}")
    return 0 if reason is None else 1


if __name__ == "__main__":
    sys.exit(main())
