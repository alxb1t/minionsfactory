# /// script
# requires-python = ">=3.12"
# dependencies = ["markdown-it-py>=3,<4"]
# ///
"""Take every cut version to the default branch, one agent process per station.

Why: 0040-mf-ship design D2.
"""

import argparse
import contextlib
import errno
import fcntl
import functools
import hashlib
import html
import itertools
import json
import math
import os
import re
import runpy
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
import tomllib
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, NamedTuple, TextIO

if TYPE_CHECKING:
    from markdown_it import MarkdownIt
    from markdown_it.token import Token

TIMEOUT = 10800
STAMP = "%Y%m%d-%H%M%S"
GIT_TIMEOUT = 60
PUSH_TIMEOUT = 1800
PYPI_INDEX = "https://pypi.org/simple"
PREFETCH_SECONDS = 600
RETRIES = (0, 10, 30)
PUSH_RETRIES = (0, 10)
LOCK_SECONDS = 30
LOCK_STALE = 600
DEBT = ".minions/debt.md"
DEBT_LOCK = ".minions/debt.lock"
OLD_DEBT = ".minions/backlog.md"
OLD_DEBT_LOCK = ".minions/backlog.lock"
REJOIN_POLL = 10
# The most of a file a worker leaves that `_bounded` reads.
READ_BYTES = 65536
# A Codex limit: the longest wait for a reset, and the primary window's share that
# counts as a limit. Why: 0104-codex-limits design D1.
LIMIT_WAIT = 900
HEADROOM = 90
INTEGRATE = Path(__file__).resolve().parents[2] / "mf-integrate/scripts/integrate.py"
CONVERGE = Path(__file__).resolve().parents[2] / "mf-converge/scripts/converge.py"
STAMP_SCRIPT = Path(__file__).resolve().parents[2] / "mf-converge/scripts/stamp.py"
# The brief's checker, and the runner of its `--models`.
# Why: 0106-cut-scripts design D7.
BRIEF_CHECK = Path(__file__).resolve().parents[2] / "mf-plan/scripts/brief_check.py"
UV_RUN = ("uv", "run", "--script")
PIN = Path(__file__).resolve().with_name("pin.py")
MOVED = "delta: changed on the default branch: "
DECISIONS = "docs/decisions.md"
# A started build's gate and rules: changed since its base, they are merged in.
GATE_FILES = ("Makefile", "*.mk", "AGENTS.md", "CODING_STANDARDS.md", "CONTRIBUTING.md")
CHANGE_ID = re.compile(r"(\d+)-([a-z0-9-]+)")
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
CUT_KEYS = frozenset({"bump", "brief", "after", "executor", "model", "effort", "halt"})
DEPENDENCIES = "## Dependencies"
INLINE_HEADING = re.compile(r"<h[1-6](?:[\s/>]|$)", re.IGNORECASE)
BLOCK_HEADING = re.compile(r"<h[12](?:[\s/>]|$)", re.IGNORECASE)
APPROVED = ["item", "package", "constraint", "why"]
PACKAGE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
SPECIFIER = re.compile(r"[<>=!~][<>=!~,.0-9A-Za-z*+ -]*")
UNAPPROVED = "design.md adds what the brief did not approve"
CLAIM_SECONDS = 30
SHA256 = re.compile(r"[0-9a-f]{64}")
PROGRESS = re.compile(r"^- \[([ x])\] (\d+) — (.*)$", re.MULTILINE)
RELEASE = re.compile(r"chore\(release\): (\S+)")
# why: the plan's skipped converge logs `converge skipped — plan`, the spec's words;
# 0105-converge-switches design D2
EVENT = re.compile(r"^\d\d:\d\d:\d\d · (\S+) · (converge skipped|\S+) — ")
EVENTS = (
    *("start", "spawn", "finish", "check", "denied", "halt", "blocked", "done"),
    *("push", "ledger", "unlock", "unkept", "kept", "removed", "rejoin", "grant"),
    *("rescue", "move", "cut", "supervise", "wait", "stacked", "reset", "notes"),
    "limited",
    "converge skipped",
)
TAG = re.compile(r"v\d+\.\d+\.\d+")
HALTS = ("integrating", "released", "human", "converge-halted")
AMENDED = "amended: HEAD past the halted head"
# A halt before round 1 runs again once a run at its head.
# Why: 0084-ship-fixes-2 design D1.
RERUN = "re-run: halted before round 1 at this head"
RERAN = "halted before round 1 again at this head: a commit answers it"
HALT_HEAD = re.compile(r" · head ([0-9a-f]{7,40})$")
STUCK = (*HALTS, "waiting")
# A stacked version's file: the built head it builds on, its build's base.
# Why: 0099-stacked-builds design D2, D5.
STACKED_ON = "stacked-on"
# What a phase hands the next, and the lines of each phase's append the run keeps.
# Why: 0102-build-per-phase design D3.
NOTES_FILE = "build-notes.md"
NOTES = 40
STATIONS = ("build", "converge", "integrate", "release")
FIXER = "converge.fix"
WORKERS = ("converge.conformance", "converge.adversarial", FIXER)
# A cut's worker table under its old name. Why: 0095-converge-roles design D2.
OLD_WORKERS = {
    "converge.conformance": "converge.review",
    "converge.adversarial": "converge.security",
}
# A phase the cut rates moderate builds on this table.
# Why: 0102-build-per-phase design D5.
MODERATE = "build.moderate"
# The rescue, the supervisor, converge's workers and the moderate build are no stage:
# each is planned with the stations'. Why: 0067-rescue design D3, D5; 0089-supervisor
# design D2; 0094-lighter-converge design D1; 0102-build-per-phase design D5.
PLANNED = (*STATIONS, "rescue", "supervise", *WORKERS, MODERATE)
TOKEN = re.compile(r"[A-Za-z0-9._-]+")
RESCUED = ("converge-halted", "integrating")
RESCUES = 3
SUPERVISES = 2
# A supervisor at an integrate note stages Markdown under these alone.
# Why: 0090-supervisor-merge design D3.
SETTLES = ("openspec/", "docs/")
SETTLED = "the supervisor settled the note: integrate commits it"
SUPERVISOR = ("claude-opus-5-5", "high")
CHECKER_DEFAULT = ("claude-sonnet-5-5", "high")
AMENDS = ("tasks.md", "design.md")
# A line the converge fixer appends to a decision's entry; the run reads it as no
# decision change. Why: 0103-fewer-rounds design D3.
FIX_NOTE = re.compile(r"Fix note \(\d{4}-\d{2}-\d{2}, [RS]\d+\): \S.*")
ROLES = ("conformance", "adversarial")
# Each old-layout path of a change, by its name in the change's folder.
# Why: 0080-minions-layout design D1, D4; 0095-converge-roles design D2.
OLD_LAYOUT = {
    "findings/{}_review.md": "conformance.md",
    "findings/{}_security.md": "adversarial.md",
    "findings/{}_status_log.md": "status_log.md",
    "findings/{}_diff.patch": "diff.patch",
    "models/{}.toml": "models.toml",
    "integrate/{}.md": "integrate.md",
    "integrate/{}.red": "integrate.red",
    "integrate/{}.resolved": "integrate.resolved",
    "build/{}.done": "build.done",
    "build/{}.halt": "build.halt",
    "build/{}.closing": "build.closing",
    "build/{}.discarded.patch": "build.discarded.patch",
    "rescue/{}.md": "rescue.md",
    "release/{}.held": "release.held",
    "gate-check/{}": "gate-check",
}
# A change folder's old findings names. Why: 0095-converge-roles design D2.
OLD_ROLES = {"review.md": "conformance.md", "security.md": "adversarial.md"}
OLD_ID = r"(\d{4}-[a-z0-9-]+)"
OLD_STAMP = re.compile(r"\d{8}-\d{6}(?:-\d+)?")
OLD_LOG = re.compile(rf"{OLD_ID}_([a-z][a-z-]*?)(-\d+)?\.log")
# A cap of these alone gets the run's one grant. Why: 0070-cap-policy design D1, D2.
BLOCKS = {"conformance": ("blocking",), "adversarial": ("critical", "high")}
SMALL = ("one line", "a test", "one line and a test")
CARD = re.compile(r"^- \*\*(\S+) — ", re.MULTILINE)
EXECUTORS = ("claude", "codex")
SKILLS = {"claude": ".claude/skills", "codex": ".agents/skills"}
SKILLS_DIR = Path(__file__).resolve().parents[2]
# The longest one script's environment takes to build. Why: 0112-uv-race design D2.
SYNC_SECONDS = 600
STOPPED = "stopped by the person"
CONFIG_CHANGED = "the local git config changed during the run: {file} differs"
GIT_FILES = (".git/config", ".git/info/attributes")
KEPT_ORIGINS = ".mf-ship-origin"
SCANNER = "betterleaks"
CAFFEINATE = "caffeinate"
LEAKED = 3
SSH_COMMAND = "ssh -o ConnectTimeout=15 -o BatchMode=yes"
TOOLS = ("Read", "Glob", "Grep", "Agent", "Skill")
# The tools a Claude worker starts with, by `--tools`; any other station takes
# `WORKER_TOOLS`. Why: 0100-worker-diet design D1.
STATION_TOOLS = {
    "cut": ("Bash", "Read", "Edit", "Write", "Glob", "Grep", "Skill", "Agent"),
    "probe": ("Bash", "Read"),
}
WORKER_TOOLS = ("Bash", "Read", "Edit", "Write", "Glob", "Grep", "Skill")
# Only these stations wait past 5 minutes. Why: 0100-worker-diet design D3;
# 0108-converge-script design D4.
CACHE_HOUR = ("cut",)
# A Claude worker's error for a tool its station lacks. Why: 0100-worker-diet design D5.
MISSING = "No such tool available"
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
# The macOS sandbox's refusal, in a Codex command's output.
CODEX_DENIAL = "Operation not permitted"
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
# A build spawn builds one phase, or closes. Why: 0102-build-per-phase design D1, D2.
PROMPTS = {
    "build": "Run the mf-build skill for change {change} with phase={phase}.",
    "integrate": "Run the mf-integrate skill for change {change}{settled}.",
    "release": "Run the mf-release skill for change {change} with merge=yes.",
    "rescue": "Run the mf-rescue skill for change {change}{decide}.",
    "supervise": (
        "Run the mf-supervise skill for change {change} with decide=recommended{brief}."
    ),
    "cut": (
        "Run the mf-cut-change skill for change {change} with arguments"
        " `{change} {bump} brief={brief}{after}{beside} unattended=yes`."
    ),
}
SHELL_RULES = (
    "Shell rules for this run: one command per Bash call; no `$(…)`, shell variables"
    " or loops — run the inner command first and use its output literally;"
    " no here-document (<<): write a file with your editing tool; use"
    " `git -C <dir>`, never `cd`; never retry a denied command in a rewritten form"
    " to get past the list. Give these rules, word for word,"
    " to every subagent you start."
)
PROBE = (
    "In this directory, write the word ok to probe.txt, commit it with the"
    " message probe, then run make gate."
)
# A Codex probe's linked worktree: its index must be writable. Why: 0104-codex-limits
# design D6.
TREE_PROBE = (
    "Then run git write-tree in tree/ and write what it prints to tree/tree.txt."
)
# A Codex probe's second worker. Why: 0096-codex-ready design D8.
CHECKER_PROBE = (
    "You are converge's conformance checker for change 0001-probe in this directory."
    " Load the mf-converge skill's references/generic-conformance.md and"
    " references/worker.md. Judge the range {base}..{head}, its patch"
    " .minions/changes/0001-probe/diff.patch and openspec/changes/0001-probe/, and"
    " write .minions/changes/0001-probe/conformance.md to the worker reference's"
    " findings file contract. Edit nothing else."
)
# The findings file contract's frontmatter keys, as the worker reference lists them,
# save `tokens`, which `conduct.py` stamps. Why: 0104-codex-limits design D5.
FINDINGS_KEYS = (
    *("type", "plan", "project", "branch", "head", "reviewed", "round"),
    *("open_blocking", "verdict", "mode", "workers", "model", "executor", "packet"),
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
    """`AGENTS.md`'s `Ship tools:` and `Ship network:` values."""

    tools: list[str]
    network: list[str]


class Opened(NamedTuple):
    """An open merge as its supervisor found it: `HEAD`, `MERGE_HEAD`, index, mark."""

    head: str
    merge: str
    index: str
    written: int | None


class Stop(Exception):
    """End the command with `code`; the message is what it prints."""

    def __init__(self, code: int, message: str) -> None:
        """Keep the exit code beside the message."""
        super().__init__(message)
        self.code = code


class Unreachable(Stop):
    """A read of `origin` that failed: the run waits on it, and halts on no other."""


def _run(
    cwd: Path, *args: str, env: dict[str, str] | None = None, timeout: int = GIT_TIMEOUT
) -> subprocess.CompletedProcess[str]:
    """Return a finished git command run in `cwd`; a missing git stops with exit 2.

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

    Why: 0052-security-hardening design D9; 0086-ship-fixes-3 design D6.
    """
    done = _run(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if done.returncode != 0 and "not a git repository" in done.stderr:
        raise Stop(2, "conduct: cannot run — not in a git repository")
    if done.returncode != 0:
        lines = [line for line in done.stderr.splitlines() if line.strip()]
        first = lines[0] if lines else f"exit {done.returncode}"
        raise Stop(
            2,
            f"conduct: cannot run — git rev-parse failed: {first};"
            f" run it as uv run --script {Path(__file__)}",
        )
    primary = Path(done.stdout.strip()).resolve().parent
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
    # why: a tag of the branch's name is no branch. 0103-fewer-rounds design D6.
    found = RELEASE.fullmatch(_subject(primary, f"refs/heads/{change}"))
    return found[1] if found else None


def _holds(primary: Path, change: str) -> bool:
    """Return whether a branch holds its change, active or just released."""
    folder = f"openspec/changes/{change}"
    # why: a tag of the branch's name is no branch. 0103-fewer-rounds design D6.
    branch = f"refs/heads/{change}"
    active = _show(primary, branch, f"{folder}/proposal.md") is not None
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


def _rating(title: str) -> str:
    """Return a `## Progress` title's rating: `moderate`, else `hard`.

    e.g. "Two · moderate" → "moderate"; "Three" → "hard"
    Why: 0102-build-per-phase design D5.
    """
    return "moderate" if title.endswith(" · moderate") else "hard"


def _change_dir(primary: Path, change: str) -> Path:
    """Return the change's folder in the run directory.

    e.g. "0001-todo" → <primary>/.minions/changes/0001-todo
    Why: 0080-minions-layout design D1, D2.
    """
    return primary / ".minions" / "changes" / change


def _folder_fd(root: Path, *parts: str) -> int:
    """Return a descriptor on `root`'s folder `parts`, each made, none read as a link.

    A link at any of `parts` raises `OSError`; `root` itself is followed.
    Why: 0071-ship-fixes design D8; 0080-minions-layout design D6.
    """
    root.mkdir(parents=True, exist_ok=True)
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in parts:
            with contextlib.suppress(FileExistsError):
                os.mkdir(part, dir_fd=fd)
            inner = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
            )
            os.close(fd)
            fd = inner
    except BaseException:
        os.close(fd)
        raise
    return fd


def _write_in_change(primary: Path, change: str, name: str, text: str) -> None:
    """Write `text` to the change's file `name`, through no link; one raises `OSError`.

    Why: 0071-ship-fixes design D8; 0080-minions-layout design D6.
    """
    fd = _folder_fd(primary / ".minions", "changes", change)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW
    try:
        file = os.open(name, flags, 0o644, dir_fd=fd)
    finally:
        os.close(fd)
    with os.fdopen(file, "w") as out:
        out.write(text)


def _remove_in(root: Path, *parts: str, name: str) -> None:
    """Remove `root`'s file `parts`/`name` when it stands, through no link."""
    fd = _folder_fd(root, *parts)
    try:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(name, dir_fd=fd)
    finally:
        os.close(fd)


def _open_notes(primary: Path, change: str, flags: int) -> int | None:
    """Return a descriptor on the change's `build-notes.md`; None with no file.

    Why: 0102-build-per-phase design D3.
    """
    fd = _folder_fd(primary / ".minions", "changes", change)
    name = f".minions/changes/{change}/{NOTES_FILE}"
    try:
        file = os.open(NOTES_FILE, flags | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    except FileNotFoundError:
        return None
    except OSError as error:
        linked = error.errno == errno.ELOOP
        why = "is a link" if linked else f"cannot be opened — {error.strerror}"
        raise Stop(1, f"conduct: halt — {name} {why}") from None
    finally:
        os.close(fd)
    found = os.fstat(file)
    if not stat.S_ISREG(found.st_mode) or found.st_nlink != 1:
        os.close(file)
        raise Stop(1, f"conduct: halt — {name} is not a regular file of one name")
    return file


def _note_lines(primary: Path, change: str) -> int:
    """Return the lines of the change's `build-notes.md`; 0 with no file."""
    file = _open_notes(primary, change, os.O_RDONLY)
    if file is None:
        return 0
    with os.fdopen(file, "rb") as notes:
        return len(notes.read().splitlines())


def _cutter_halt(primary: Path, change: str) -> str | None:
    """Return the cutter's `cut.halt` line, read through no link; None with none."""
    fd = _folder_fd(primary / ".minions", "changes", change)
    try:
        halt = os.open("cut.halt", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
    except OSError:
        halt = None
    finally:
        os.close(fd)
    if halt is None:
        return None
    with os.fdopen(halt, errors="replace") as file:
        return file.readline().strip()[:300]


def _cut_answer(change: str, brief: str) -> str:
    """Return the action a cut halt the plan answers needs.

    e.g. "0001-a", "/b.md" → "its brief answered (/mf-plan 0001-a depth=hard brief=/b.md
    from=/b.md), then conduct.py rejoin 0001-a". Why: 0091-cut-halts design D5.
    """
    return (
        f"its brief answered (/mf-plan {change} depth=hard brief={brief}"
        f" from={brief}), then conduct.py rejoin {change}"
    )


def _models_hash(primary: Path, change: str) -> str | None:
    """Return the sha256 of the change's `models.toml`, read through no link.

    None when the file is missing, a link, or its folder is one. Why: 0106 design D7.
    """
    try:
        fd = _folder_fd(primary / ".minions", "changes", change)
        try:
            file = os.open("models.toml", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
        finally:
            os.close(fd)
    except OSError:
        return None
    with os.fdopen(file, "rb") as models:
        return hashlib.sha256(models.read()).hexdigest()


def _check_cut(primary: Path, change: str, tree: Path) -> str | None:
    """Return why a cut did not pass, the cutter's own halt line first; None on a pass.

    A queued entry that holds `models` fails a file whose bytes differ from its text.
    Why: 0082-cut-station design D4; 0106-cut-scripts design D7.
    """
    if (halt := _cutter_halt(primary, change)) is not None:
        return halt
    # why: a tag of the branch's name is no branch. 0103-fewer-rounds design D6.
    tip = _subject(primary, f"refs/heads/{change}")
    if tip != f"docs({change}): land the change directory":
        return f"{change}: no cut commit at the branch's tip"
    if not _holds(primary, change):
        return f"{change}: the branch holds no openspec/changes/{change}/"
    if _dirty(tree):
        return "the tree is not clean"
    if not (_change_dir(primary, change) / "models.toml").is_file():
        return f"no .minions/changes/{change}/models.toml"
    queued = _cuts(primary).get(change, {}).get("models")
    if (
        queued is not None
        and _models_hash(primary, change) != hashlib.sha256(queued.encode()).hexdigest()
    ):
        return f"changes/{change}/models.toml changed since the cut was queued"
    return None


def _unapproved(primary: Path, change: str, approved: list[list[str]]) -> str | None:
    """Return why the cut's `design.md` lists a package `approved` does not hold.

    Why: 0091-cut-halts design D4.
    """
    # why: a tag of the branch's name is no branch. 0103-fewer-rounds design D6.
    branch = f"refs/heads/{change}"
    design = _show(primary, branch, f"openspec/changes/{change}/design.md") or ""
    rows = _rows(design, DEPENDENCIES)
    if (
        not _headed(design, DEPENDENCIES)
        or rows is None
        or (rows and rows[0][:2] != ["package", "constraint"])
    ):
        return (
            "design.md's ## Dependencies is neither None. nor a table of"
            " package · constraint · why"
        )
    added = [f"{row[0]} {row[1]}" for row in rows[1:] if row[:2] not in approved]
    return f"{UNAPPROVED}: {', '.join(added)}" if added else None


def _old_files(primary: Path) -> dict[str, list[tuple[Path, str]]]:
    """Return each change's old-layout files, each with its path in the change's folder.

    Why: 0080-minions-layout design D4; 0095-converge-roles design D2.
    """
    minions = primary / ".minions"
    found: dict[str, list[tuple[Path, str]]] = {}
    for old, new in OLD_LAYOUT.items():
        folder, name = old.split("/")
        pattern = re.compile(re.escape(name).replace(re.escape("{}"), OLD_ID))
        listed = (minions / folder).iterdir() if (minions / folder).is_dir() else ()
        for path in listed:
            if matched := pattern.fullmatch(path.name):
                found.setdefault(matched[1], []).append((path, new))
    changes = minions / "changes"
    folders = sorted(changes.iterdir()) if changes.is_dir() else []
    for folder in (f for f in folders if f.is_dir()):
        for name, new in OLD_ROLES.items():
            if os.path.lexists(folder / name):
                found.setdefault(folder.name, []).append((folder / name, new))
    runs = minions / "runs"
    stamps = runs.iterdir() if runs.is_dir() else ()
    for stamp in (s for s in stamps if OLD_STAMP.fullmatch(s.name) and s.is_dir()):
        for path in stamp.iterdir():
            if matched := OLD_LOG.fullmatch(path.name):
                change, station, n = matched[1], matched[2], matched[3] or ""
                new = f"logs/{stamp.name}-{station}{n}.log"
                found.setdefault(change, []).append((path, new))
    return found


def _old_layout(primary: Path, change: str) -> str | None:
    """Return the change's first old-layout file, relative to the primary, or None.

    Why: 0080-minions-layout design D4.
    """
    held = sorted(path for path, _ in _old_files(primary).get(change, []))
    return str(held[0].relative_to(primary)) if held else None


def _run_end(runs: Path, change: str) -> str | None:
    """Return the newest converge run's top event line, or None with no run."""
    log = _change_dir(runs.parent, change) / "status_log.md"
    lines = log.read_text().splitlines() if log.is_file() else []
    heading = next(
        (i for i, line in enumerate(lines) if line.startswith("## Run")), None
    )
    if heading is None:
        return None
    return next((line for line in lines[heading + 1 :] if line.strip()), "").strip()


def _run_marked(runs: Path, change: str, mark: str) -> bool:
    """Return whether the newest converge run's heading ends ` · <mark>`.

    e.g. "## Run 4 — 2026-11-05 10:04 · grant", "grant" → True
    """
    log = _change_dir(runs.parent, change) / "status_log.md"
    lines = log.read_text().splitlines() if log.is_file() else []
    heading = next((line for line in lines if line.startswith("## Run")), "")
    return heading.rstrip().endswith(f" · {mark}")


def _granted_run(runs: Path, change: str) -> bool:
    """Return whether the newest converge run is a granted round, marked `· grant`.

    Why: 0070-cap-policy design D2.
    """
    return _run_marked(runs, change, "grant")


def _done_head(primary: Path, change: str) -> str | None:
    """Return the word `build.done`'s `head:` names, or None.

    A missing or unreadable file names none, nor does one that is no regular file.
    Why: 0055-build-resume design D2.
    """
    done = _change_dir(primary, change) / "build.done"
    if not done.is_file():
        return None
    try:
        text = done.read_text()
    except (OSError, UnicodeDecodeError):
        return None
    found = re.search(r"^head:\s*(\S+)", text, re.MULTILINE)
    return found[1] if found else None


def _closed(runs: Path, tree: Path, change: str) -> bool:
    """Return whether `.minions/changes/<change>/build.done` names the tree's `HEAD`."""
    if (done := _done_head(runs.parent, change)) is None:
        return False
    named = _maybe(tree, "rev-parse", "-q", "--verify", f"{done}^{{commit}}")
    return (named or "").strip() == _git(tree, "rev-parse", "HEAD").strip()


def _built_head(primary: Path, change: str) -> str | None:
    """Return the full sha `build.done` names while that build stands, else None.

    Why: 0099-stacked-builds design D1, D6.
    """
    done = _done_head(primary, change)
    named = done and _maybe(
        primary, "rev-parse", "-q", "--verify", f"{done}^{{commit}}"
    )
    if not named:
        return None
    head = named.strip()
    if not _ancestor(primary, head, f"refs/heads/{change}"):
        return None
    tasks = _show(primary, head, f"openspec/changes/{change}/tasks.md") or ""
    boxes = PROGRESS.findall(tasks)
    if not boxes or any(mark != "x" for mark, _, _ in boxes):
        return None
    return None if _replanned(primary, change, head) else head


def _replanned(primary: Path, change: str, since: str) -> bool:
    """Return whether an amend of the change directory past `since` changes a decision.

    Why: 0099-stacked-builds design D6.
    """
    folder = f"openspec/changes/{change}"
    subject = f"docs({change}): amend the change directory"
    listed = ("diff-tree", "--root", "-r", "--no-commit-id", "--name-only")
    span = f"{since}..refs/heads/{change}"
    for sha in _git(primary, "rev-list", "--no-merges", span).split():
        if _subject(primary, sha) != subject:
            continue
        if f"{folder}/proposal.md" in _git(primary, *listed, sha).split():
            return True
        design = f"{folder}/design.md"
        was, now = (_decisions(_show(primary, rev, design)) for rev in (f"{sha}^", sha))
        if was != now:
            return True
    return False


def _stacked_on(
    primary: Path, change: str, tree: Path, unreleased: list[str]
) -> str | None:
    """Return the full sha `stacked-on` names while it stands, else None.

    Why: 0099-stacked-builds design D3.
    """
    file = _change_dir(primary, change) / STACKED_ON
    try:
        words = file.read_text().split() if file.is_file() else []
    except (OSError, UnicodeDecodeError):
        return None
    if not words or not re.fullmatch(r"[0-9a-f]{40}", words[0]):
        return None
    named = _maybe(tree, "rev-parse", "-q", "--verify", f"{words[0]}^{{commit}}")
    if not named or not _ancestor(tree, named.strip(), "HEAD"):
        return None
    sha = named.strip()
    held = (f"{sha}:openspec/changes/{name}/tasks.md" for name in unreleased)
    if any(_maybe(tree, "cat-file", "-e", path) is None for path in held):
        return None
    return sha


def _merged_back(tree: Path, done: str, default: str) -> bool:
    """Return whether `HEAD` merges the default branch into the head `build.done` names.

    Such a merge has two parents, the first that head, the second on the default
    branch. Why: 0099-stacked-builds design D3.
    """
    named = _maybe(tree, "rev-parse", "-q", "--verify", f"{done}^{{commit}}")
    parents = _git(tree, "rev-list", "--parents", "-n", "1", "HEAD").split()[1:]
    return (
        named is not None
        and len(parents) == 2
        and parents[0] == named.strip()
        and _ancestor(tree, parents[1], default)
    )


def _cut_commit(tree: Path, change: str) -> str | None:
    """Return the newest first-parent commit that lands the change directory, or None.

    Why: 0099-stacked-builds design D6.
    """
    landed = f"docs({change}): land the change directory"
    log = _git(tree, "log", "--first-parent", "--format=%H %s", "HEAD")
    for line in log.splitlines():
        sha, _, subject = line.partition(" ")
        if subject == landed:
            return sha
    return None


def _unstack(primary: Path, change: str) -> None:
    """Remove the change's `stacked-on` when one stands, through no link."""
    if os.path.lexists(_change_dir(primary, change) / STACKED_ON):
        _remove_in(primary / ".minions", "changes", change, name=STACKED_ON)


def _build_halt(runs: Path, tree: Path, change: str) -> tuple[str, str] | None:
    r"""Return `build.halt`'s sub-task and stop when it names `HEAD`.

    None for a missing, unreadable or stale file. Why: 0067-rescue design D1.
    e.g. "sub-task: 1.2\nstop: 3\nhead: <HEAD>\n" → ("1.2", "3")
    """
    file = _change_dir(runs.parent, change) / "build.halt"
    try:
        text = file.read_text() if file.is_file() else ""
    except (OSError, UnicodeDecodeError):
        return None
    keys = dict(re.findall(r"^(sub-task|stop|head):[ \t]*(\S.*?)[ \t]*$", text, re.M))
    if not {"sub-task", "stop", "head"} <= keys.keys():
        return None
    named = _maybe(tree, "rev-parse", "-q", "--verify", f"{keys['head']}^{{commit}}")
    if (named or "").strip() != _git(tree, "rev-parse", "HEAD").strip():
        return None
    return keys["sub-task"], keys["stop"]


def _is_event(line: str, event: str) -> bool:
    """Return whether a status-log line holds `event`, its detail aside.

    e.g. "10:00:00 · round 1 · done — ok", "done" → True
    """
    return line.split(" — ", maxsplit=1)[0].endswith(f" · {event}")


def _clear_stale_lock(primary: Path, name: str = DEBT_LOCK) -> int | None:
    """Remove the lock `name` older than `LOCK_STALE`; return its age in seconds.

    A lock younger, or one `rmdir` refuses, stays. Why: 0053-sandbox-patch design D3.
    """
    lock = primary / name
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


def _fresh_tmp(primary: Path) -> str | None:
    """Leave `.minions/tmp/`, the Claude workers' `TMPDIR`, empty; return why to halt.

    Why: 0084-ship-fixes-2 design D6, its delta's *A worker makes a scratch file*.
    """
    if (primary / ".minions").is_symlink():
        return ".minions is a link: a person settles what it names"
    fd = _folder_fd(primary, ".minions")
    try:
        try:
            mode = os.lstat("tmp", dir_fd=fd).st_mode
        except FileNotFoundError:
            mode = None
        if mode is not None and stat.S_ISDIR(mode):
            shutil.rmtree("tmp", dir_fd=fd)
        elif mode is not None:
            os.unlink("tmp", dir_fd=fd)
        os.mkdir("tmp", dir_fd=fd)
    finally:
        os.close(fd)
    return None


def _pinned_scripts(skills: Path) -> list[Path]:
    """Return the scripts under `skills` that open with a PEP 723 header, sorted.

    e.g. Path("skills") → [Path("skills/mf-build/scripts/metrics.py"), …]
    """
    found = []
    for script in sorted(skills.glob("*/scripts/*.py")):
        with script.open("rb") as file:
            if file.readline().rstrip() == b"# /// script":
                found.append(script)
    return found


def _sync_scripts(primary: Path, roots: Iterable[Path]) -> str | None:
    """Build each pinned script's environment, one at a time; return why one failed.

    Why: 0112-uv-race design D2. e.g. [Path("skills")] → None
    """
    env = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith(("UV_", "PIP_")) and name != "VIRTUAL_ENV"
    }
    env["UV_CACHE_DIR"] = str(primary / ".minions" / "uv-cache")
    for script in (s for root in dict.fromkeys(roots) for s in _pinned_scripts(root)):
        failed = f"uv sync --script {script.name} failed: "
        try:
            done = subprocess.run(
                ["uv", "sync", "--script", str(script)],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                timeout=SYNC_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return failed + "timed out"
        except OSError as error:
            return failed + (error.strerror or str(error))
        if done.returncode != 0:
            lines = (line.strip() for line in done.stderr.splitlines())
            return failed + next(
                (line for line in lines if line), f"exit {done.returncode}"
            )
    return None


def _converge_halt(runs: Path, change: str) -> str | None:
    """Return the newest converge run's top event when it is a halt, else None."""
    end = _run_end(runs, change)
    return end if end and _is_event(end, "halt") else None


def _run_started(runs: Path, change: str) -> bool:
    """Return whether the newest converge run, to the next heading, holds a `start`.

    e.g. "## Run 2 — d", "… · halt — red", "… · start — base a" → True
    """
    log = _change_dir(runs.parent, change) / "status_log.md"
    lines = log.read_text().splitlines() if log.is_file() else []
    heading = next(
        (i for i, line in enumerate(lines) if line.startswith("## Run")), len(lines)
    )
    run = itertools.takewhile(
        lambda line: not line.startswith("## Run"), lines[heading + 1 :]
    )
    return any(_is_event(line, "start") for line in run)


def _before_round(runs: Path, change: str, halt: str) -> bool:
    """Return whether `halt` is a halt before round 1: no `start`, no `verify: halt`.

    A granted round writes no `start`, and its halt is none: its cap re-plans.
    Why: 0084-ship-fixes-2 design D1, D2; D56.
    """
    return (
        "verify: halt" not in halt
        and not _granted_run(runs, change)
        and not _run_started(runs, change)
    )


def _rerun(runs: Path, tree: Path, change: str, halt: str) -> bool:
    """Return whether `halt` is a halt before round 1 whose head is `HEAD`.

    Why: 0084-ship-fixes-2 design D1.
    """
    found = HALT_HEAD.search(halt)
    halted = found and _maybe(
        tree, "rev-parse", "-q", "--verify", f"{found[1]}^{{commit}}"
    )
    head = _git(tree, "rev-parse", "HEAD").strip()
    return bool(halted) and halted.strip() == head and _before_round(runs, change, halt)


def _amendable(runs: Path, change: str, halt: str) -> bool:
    """Return whether the person's amend during a rescue answers a halt of this kind.

    Why: 0071-ship-fixes design D5;
    0092-amend-round design D7.
    """
    if "verify: halt" in halt or "amend needed" in halt:
        return True
    if not (
        _run_marked(runs, change, "catch-up") or _run_marked(runs, change, "amend")
    ):
        return False
    files = (_change_dir(runs.parent, change) / f"{role}.md" for role in ROLES)
    return all(
        file.is_file() and _frontmatter(file.read_text(), "verdict") == "clean"
        for file in files
    )


def _amends(tree: Path, change: str, halted: str) -> list[bool]:
    """Return, per commit past `halted`, whether it is an amend of the change directory.

    Why: 0071-ship-fixes design D5; 0092-amend-round design D2.
    """
    head = _git(tree, "rev-parse", "HEAD").strip()
    if halted == head or not _ancestor(tree, halted, "HEAD"):
        return []
    folder = f"openspec/changes/{change}/"
    subject = f"docs({change}): amend the change directory"
    listed = ("diff-tree", "--root", "-m", "-r", "--no-commit-id", "--name-only")
    amends = []
    for line in _git(tree, "rev-list", "--parents", f"{halted}..HEAD").splitlines():
        sha, *parents = line.split()
        paths = _git(tree, *listed, sha).split()
        amends.append(
            len(parents) == 1
            and _subject(tree, sha) == subject
            and all(path.startswith(folder) for path in paths)
        )
    return amends


def _amended_only(tree: Path, change: str, halted: str) -> bool:
    """Return whether only amends of the change directory follow `halted`.

    Why: 0071-ship-fixes design D5.
    """
    amends = _amends(tree, change, halted)
    return bool(amends) and all(amends)


def _answered(runs: Path, tree: Path, change: str, halt: str) -> bool:
    """Return whether a commit answered a converge halt.

    Why: 0071-ship-fixes design D5; 0084-ship-fixes-2 design D1;
    0092-amend-round design D2.
    """
    found = HALT_HEAD.search(halt)
    halted = found and _maybe(
        tree, "rev-parse", "-q", "--verify", f"{found[1]}^{{commit}}"
    )
    if not halted:
        return False
    halted = halted.strip()
    if halted == _git(tree, "rev-parse", "HEAD").strip():
        return False
    if _before_round(runs, change, halt):
        return _ancestor(tree, halted, "HEAD")
    if any(_amends(tree, change, halted)):
        return True
    for role in ROLES:
        file = _change_dir(runs.parent, change) / f"{role}.md"
        judged = _frontmatter(file.read_text(), "head") if file.is_file() else None
        resolved = judged and _maybe(
            tree, "rev-parse", "-q", "--verify", f"{judged}^{{commit}}"
        )
        if not resolved or resolved.strip() != halted:
            return False
    return _ancestor(tree, halted, "HEAD")


def _converge_done(runs: Path, change: str) -> bool:
    """Return whether the newest converge run ends on `done`."""
    return _is_event(_run_end(runs, change) or "", "done")


def _buried_done(runs: Path, change: str) -> str | None:
    """Return the newest run's `done` line under a top line that ends no run, else None.

    e.g. "… · debt — d" over "… · round 2 · done — ok" → the `done` line
    """
    log = _change_dir(runs.parent, change) / "status_log.md"
    lines = log.read_text().splitlines() if log.is_file() else []
    heading = next(
        (i for i, line in enumerate(lines) if line.startswith("## Run")), len(lines)
    )
    run = [
        line
        for line in itertools.takewhile(
            lambda line: not line.startswith("## Run"), lines[heading + 1 :]
        )
        if line.strip()
    ]
    if not run or _is_event(run[0], "halt") or _is_event(run[0], "done"):
        return None
    return next((line for line in run if _is_event(line, "done")), None)


def _restamp(runs: Path, change: str, buried: str) -> int:
    """Stamp `done` on top of the status log, as the run's own; return the exit code.

    e.g. "10:00:00 · round 2 · done — ok" → "round 2 · done — re-stamped by the run"
    """
    log = _change_dir(runs.parent, change) / "status_log.md"
    found = re.search(r"· (round \d+) · done\b", buried)
    event = f"{found[1] if found else 'round 1'} · done — re-stamped by the run"
    return int(runpy.run_path(str(STAMP_SCRIPT))["main"]([str(log), event]))


def _unjudged(
    runs: Path,
    tree: Path,
    change: str,
    rev: str = "HEAD",
    skips: frozenset[str] | None = None,
) -> str | None:
    """Return why converge is not clean at `rev`, or None when it is.

    A converge the plan skips is None: the run's `skips`, read once, else the file's.
    Why: 0105-converge-switches design D2; 0108-converge-script design D8.
    """
    if "converge" in (_skips(runs, change) if skips is None else skips):
        return None
    head = _git(tree, "rev-parse", rev).strip()
    for role in ROLES:
        file = _change_dir(runs.parent, change) / f"{role}.md"
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


def _red(primary: Path, tree: Path, change: str) -> str | None:
    r"""Return the full sha a `.red` file's `head:` names, else its raw text.

    None for no file, or no `head:` line. Why: 0071-ship-fixes design D2.
    e.g. "gate red\n2026-11-05\nhead: 7ee2179\n" → "7ee2179…" in full
    """
    file = _change_dir(primary, change) / "integrate.red"
    try:
        text = file.read_text() if file.is_file() else ""
    except (OSError, UnicodeDecodeError):
        return None
    found = re.search(r"^head:[ \t]*(\S+)", text, re.MULTILINE)
    if found is None:
        return None
    named = _maybe(tree, "rev-parse", "-q", "--verify", f"{found[1]}^{{commit}}")
    return named.strip() if named else found[1]


def _merge_open(tree: Path) -> bool:
    """Return whether a merge is open in `tree`."""
    return _maybe(tree, "rev-parse", "-q", "--verify", "MERGE_HEAD") is not None


def _conflicts(tree: Path) -> list[str]:
    """Return the paths an open merge leaves unmerged in `tree`.

    Past the refusal: a stat-dirty file makes `git diff` run a clean filter.
    """
    _refuse_config_commands(tree)
    return _git(tree, "diff", "--name-only", "--diff-filter=U").split()


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
    # why: `delta` may fail any way; a crash stops with exit 2, naming it.
    except Exception as error:  # noqa: BLE001
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


def _release_tip(
    primary: Path,
    tree: Path,
    change: str,
    tag: str,
    skips: frozenset[str] | None = None,
) -> tuple[str, str]:
    """Return the stage of a tip that says it is released; only a death re-enters."""
    runs = primary / ".minions"
    if (_change_dir(primary, change) / "release.held").is_file():
        return "released", (
            f"{tag}: .minions/changes/{change}/release.held holds a person's no:"
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
    if why := _unjudged(runs, tree, change, "HEAD~1", skips):
        return "released", f"{tag} {stated}; {why}: a person reads this tip"
    if _release_died(runs / "runs", change):
        return "release", f"{tag} {stated}; the merge is left"
    return "released", (
        f"{tag} {stated}; the release stopped before its merge:"
        f" /mf-release {change} merges it on a person's yes"
    )


def stage_of(
    primary: Path, version: Version, skips: frozenset[str] | None = None
) -> tuple[str, str]:
    """Return a version's stage, read in its worktree, and why; the first match wins.

    A run passes `skips`, its plan's converge skips read once; with none, the models
    file is read. Why: 0108-converge-script design D8.
    """
    tree = version.tree
    change = version.change
    if tree is None:
        raise Stop(2, f"conduct: cannot run — {change} has no worktree")
    runs = primary / ".minions"
    red, merging = _red(primary, tree, change), _merge_open(tree)
    note = f".minions/changes/{change}/integrate"
    if red is not None and not merging:
        if red == _git(tree, "rev-parse", "HEAD").strip():
            return "integrating", f"red gate: {note}.red"
        return "integrate", "red gate on another head: integrate gates again"
    if merging:
        marks = _change_dir(primary, change)
        # A `.red` with a `head:` names a committed merge: an open one's is stale.
        if red is None and (marks / "integrate.red").is_file():
            return "integrating", f"red gate: {note}.red"
        if (marks / "integrate.md").is_file():
            return "integrating", f"semantic conflict: {note}.md"
        if _conflicts(tree):
            return "integrate", "interrupted: a merge is open with no note"
        return (
            "integrate",
            "a merge is open and staged, with no note: integrate resumes",
        )
    tag = _tag_of(primary, change)
    default = default_branch(primary)
    if tag is not None:
        return _release_tip(primary, tree, version.change, tag, skips)
    after = _dependencies(primary, change)
    missing = [name for name in after if not _shipped(primary, default, name)]
    stacked = _stacked_on(primary, change, tree, missing)
    if missing and stacked is None:
        return "waiting", f"after {' '.join(missing)}"
    if unticked := _unticked(tree, change):
        number, title = unticked
        if "**HUMAN" in title:
            return "human", f"phase {number} — {title}"
        return "build", f"phase {number} unticked"
    end = _run_end(runs, change)
    done = _done_head(primary, change)
    if (
        end is None
        and not _closed(runs, tree, change)
        and not (done and _merged_back(tree, done, default))
    ):
        return "build", "closing steps left"
    lacking = [name for name in after if not _shipped(tree, "HEAD", name)]
    if stacked is not None and lacking:
        return (
            "stacked",
            f"built on {' '.join(lacking)} at {stacked[:7]}: waits for its release",
        )
    # why: a skipped converge has no halt or run to read; 0105-converge-switches D2
    skipped = "converge" in (_skips(runs, change) if skips is None else skips)
    if halt := None if skipped else _converge_halt(runs, change):
        if DEBT_LOCK in halt or OLD_DEBT_LOCK in halt:
            return "converge", "halted on the debt lock: resumes at Step 9"
        if _rerun(runs, tree, change, halt):
            return "converge", RERUN
        if _answered(runs, tree, change, halt):
            return "converge", AMENDED
        if "cap reached" in halt and _granted(runs, change, take=False):
            return "converge", "granted"
        return "converge-halted", halt
    if end is not None and not skipped and not _converge_done(runs, change):
        return "converge", f"unfinished run: {end}"
    if why := _unjudged(runs, tree, change, skips=skips):
        return "converge", why
    if not _ancestor(tree, default, "HEAD"):
        return "integrate", f"{default} is not an ancestor of HEAD"
    verdict = "converge skipped by plan" if skipped else "converge clean at HEAD"
    return "release", f"{verdict}; {default} is an ancestor"


def _check_build(primary: Path, version: Version, tree: Path) -> str | None:
    """Return why the build check fails, or None."""
    change = version.change
    if unticked := _unticked(tree, change):
        held = _build_halt(primary / ".minions", tree, change)
        named = f" · {held[0]}: {held[1]}" if held else ""
        return f"phase {unticked[0]} unticked{named}"
    if _dirty(tree):
        return "the tree is not clean"
    if not _closed(primary / ".minions", tree, change):
        return f"no .minions/changes/{change}/build.done names HEAD"
    return None


def _check_phase(primary: Path, version: Version, tree: Path, phase: str) -> str | None:
    """Return why a phase spawn's check fails, or None: phase ticked, tree clean.

    The phase's line must stand, and it and every line before it must be ticked.
    Why: 0102-build-per-phase design D2.
    """
    change = version.change
    boxes = _progress(tree, change)
    if all(number != phase for _, number, _ in boxes):
        return f"phase {phase} gone from ## Progress"
    for mark, number, _ in boxes:
        if mark != "x":
            held = _build_halt(primary / ".minions", tree, change)
            named = f" · {held[0]}: {held[1]}" if held else ""
            return f"phase {number} unticked{named}"
        if number == phase:
            break
    return "the tree is not clean" if _dirty(tree) else None


def _check_converge(
    primary: Path, version: Version, tree: Path, *, notes: list[str] | None = None
) -> str | None:
    """Return why the converge check fails, or None.

    A buried `done` is stamped on top again, `notes` gets `re-stamped done`. Why:
    0109-converge-done-order design D2, D3.
    """
    runs = primary / ".minions"
    halt = _converge_halt(runs, version.change)
    if halt and not _answered(runs, tree, version.change, halt):
        return f"the status log halts: {halt}"
    done = _converge_done(runs, version.change)
    buried = None if done else _buried_done(runs, version.change)
    if not done and buried is None:
        return "the status log has no done"
    if why := _unjudged(runs, tree, version.change):
        return why
    if _dirty(tree):
        return "the tree is not clean"
    if buried is not None:
        if _restamp(runs, version.change, buried) != 0:
            return "the status log has no done"
        if notes is not None:
            notes.append("re-stamped done")
    return None


def _check_integrate(primary: Path, version: Version, tree: Path) -> str | None:
    """Return why the integrate check fails, or None; an open merge names its note.

    Why: 0071-ship-fixes design D2.
    """
    note = f".minions/changes/{version.change}/integrate"
    red = _red(primary, tree, version.change)
    if _merge_open(tree):
        if red is None and (primary / f"{note}.red").is_file():
            return f"integrate halted — red gate, see {note}.red"
        if (primary / f"{note}.md").is_file():
            return f"integrate halted — semantic conflict, see {note}.md"
        return "a merge is still open"
    if red is not None:
        return f"integrate halted — red gate, see {note}.red"
    default = default_branch(primary)
    merge = _git(tree, "rev-list", "--first-parent", "--merges", "-1", "HEAD").strip()
    subject = _subject(tree, merge) if merge else _subject(tree)
    if subject != f"chore(integrate): merge {default} into {version.change}":
        return f"HEAD is not the integrate commit: {subject}"
    if not _ancestor(tree, default, "HEAD"):
        return f"{default} is not an ancestor of HEAD"
    return None


def _check_release(
    primary: Path, version: Version, first_read: bool, offline: bool = False
) -> str | None:
    """Return why the release check fails, or None.

    Why: 0062-offline-origin design D2, D4.
    """
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
    if not offline and _pushed(primary, version.change, tag, first_read) is False:
        return f"{tag} is not on origin"
    return None


def _config_held(cwd: Path) -> list[str]:
    """Return the keys in the repo's own git config that `CONFIG_PLAIN` lacks.

    Each linked worktree's `config.worktree` is read as a file, which git itself reads
    only under `extensions.worktreeConfig`. Why: 0104-codex-limits design D6.
    """
    listed = _git(cwd, "config", "--list", "--show-scope", "--name-only")
    held = [
        name
        for scope, _, name in (line.partition("\t") for line in listed.splitlines())
        if scope in ("local", "worktree") and not CONFIG_PLAIN.fullmatch(name)
    ]
    common = _common_dir(cwd)
    for folder in _gitdirs(common) if common else []:
        file = folder / "config.worktree"
        with contextlib.suppress(OSError):
            if stat.S_ISREG(os.lstat(file).st_mode):
                names = _git(
                    cwd, "config", "--file", str(file), "--list", "--name-only"
                )
                held += [n for n in names.splitlines() if not CONFIG_PLAIN.fullmatch(n)]
    return held


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

    Why: 0053-sandbox-patch design D2.
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


def _kept_default(primary: Path) -> str:
    """Return the default branch's name a run kept, else the one git names."""
    named = _default_file(primary)
    return named.read_text() if named.is_file() else default_branch(primary)


def _pushed_file(primary: Path) -> Path:
    """Return the offline base's file: the default branch's sha origin last listed.

    Why: 0062-offline-origin design D1.
    """
    return Path.home() / KEPT_ORIGINS / f"{_digest(primary)}.pushed"


def _keep_base(primary: Path, sha: str) -> str | None:
    """Keep `sha` as the offline base, over an older one; return why it could not.

    Owner-only, through a temp file and `os.replace`. Where the home folder refuses
    it, this process is itself in a sandbox, and nothing is kept.
    """
    file = _pushed_file(primary)
    try:
        file.parent.mkdir(mode=0o700, exist_ok=True)
        fd, temp = tempfile.mkstemp(dir=file.parent, prefix=f".{file.name}-")
        with os.fdopen(fd, "w") as kept:
            kept.write(f"{sha}\n")
        os.replace(temp, file)
    except OSError as error:
        return error.strerror or type(error).__name__
    return None


def _offline_base(primary: Path) -> str | None:
    """Return the offline base's sha, or None when none stands."""
    file = _pushed_file(primary)
    if not file.is_file():
        return None
    return file.read_text().strip() or None


def _origin_head(primary: Path, url: str) -> str | None:
    """Return the branch `url`'s own HEAD names, or None when it names none.

    A read that fails is `Unreachable`.
    """
    done = _remote(primary, "ls-remote", "--symref", "--", url, "HEAD")
    if done.returncode != 0:
        raise Unreachable(1, _why(done))
    for line in done.stdout.splitlines():
        ref, _, name = line.partition("\t")
        if name == "HEAD" and ref.startswith("ref: refs/heads/"):
            return ref.removeprefix("ref: refs/heads/")
    return None


def _push_default(primary: Path, url: str) -> str:
    """Return the default branch a push judges and pushes: the one origin's HEAD names.

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
    """Return `_urls`; stop with 1 unless a remote call can run only its own git."""
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

    Why: 0052-security-hardening design D9; 0062-offline-origin design D3.
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
        operator = ("GIT_SSH_COMMAND", "GIT_SSH")
        named = _maybe(root, "config", "--get", "core.sshCommand")
        if not any(env.get(name) for name in operator) and not (named or "").strip():
            env["GIT_SSH_COMMAND"] = SSH_COMMAND
        return _run(root, *args, env=env, timeout=timeout)


def _scan(primary: Path, base: str | None, sha: str) -> None:
    """Stop with 1 when a commit in `base..sha` holds a secret; with no base, in `sha`.

    Why: 0065-gate-hardening design D7.
    """
    commits = f"{base}..{sha}" if base else sha
    span = f"--remerge-diff {commits}"
    with _scratch() as scratch:
        root = Path(scratch)
        _git(root, "init", "-q", "--bare", "--template=")
        objects = _git(
            primary, "rev-parse", "--path-format=absolute", "--git-path", "objects"
        )
        (root / "objects" / "info" / "alternates").write_text(objects)
        report = root / "leaks.json"
        quiet = ("GIT_CONFIG_NOSYSTEM", "GIT_ATTR_NOSYSTEM", "GIT_NO_REPLACE_OBJECTS")
        env = {**os.environ, "GIT_DIR": scratch, "GIT_NO_LAZY_FETCH": "1"}
        env |= dict.fromkeys(quiet, "1")
        listed = _run(root, "rev-list", "--min-parents=3", commits, env=env)
        if listed.returncode != 0:
            why = _why(listed)
            raise Stop(
                1, f"conduct: halt — the secret scan failed: {why}; nothing pushed"
            )
        if octopus := listed.stdout.split():
            raise Stop(
                1,
                "conduct: halt — the push range holds an octopus merge, which the scan"
                f" cannot read: {octopus[0][:7]}; nothing pushed",
            )
        argv = [
            *(SCANNER, "git", "--no-banner", "--no-color", "--redact"),
            *("--ignore-gitleaks-allow", f"--gitleaks-ignore-path={scratch}"),
            *(f"--exit-code={LEAKED}", f"--log-opts={span}", "--report-format=json"),
            *(f"--report-path={report}", scratch),
        ]
        try:
            done = subprocess.run(
                argv,
                capture_output=True,
                encoding="utf-8",
                env=env,
                errors="replace",
                timeout=PUSH_TIMEOUT,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise Stop(
                1,
                f"conduct: halt — the secret scan cannot run: {error}; nothing pushed",
            ) from None
        if done.returncode == LEAKED:
            hit = json.loads(report.read_text())[0]
            raise Stop(
                1,
                f"conduct: halt — the push range holds a secret: {hit['RuleID']} in"
                f" {hit['File']} at {hit['Commit'][:7]}; nothing pushed",
            )
    if done.returncode != 0:
        raise Stop(
            1, f"conduct: halt — the secret scan failed: {_why(done)}; nothing pushed"
        )


def _remote(
    primary: Path, *args: str, timeout: int = GIT_TIMEOUT
) -> subprocess.CompletedProcess[str]:
    """Return `_outside`'s call; one that stopped, a timeout, exits 1 naming why."""
    try:
        return _outside(primary, *args, timeout=timeout)
    except Stop as stop:
        return subprocess.CompletedProcess(args, 1, "", str(stop))


def _why(done: subprocess.CompletedProcess[str]) -> str:
    """Return a failed call's last stderr line, or its exit."""
    lines = [line for line in done.stderr.splitlines() if line.strip()]
    return lines[-1].strip() if lines else f"exit {done.returncode}"


def _listed(
    primary: Path, url: str, *refs: str, first_read: bool = False
) -> str | None:
    """Return what `url` lists of its tags and `refs`, or None if it cannot be read.

    A run's read that fails is `Unreachable`. Why: 0062-offline-origin design D2.
    """
    done = _remote(primary, "ls-remote", "--tags", "--", url, *refs)
    if done.returncode != 0 and first_read:
        raise Unreachable(1, _why(done))
    return done.stdout if done.returncode == 0 else None


def _pushed(
    primary: Path, change: str, tag: str, first_read: bool = False
) -> bool | None:
    """Return whether origin's tag is on the branch's tip, or None with no origin.

    An `origin` this may not read lacks the tag, as one that cannot be read does,
    save on a run's read, where that is `Unreachable`.
    """
    if "origin" not in _git(primary, "remote").split():
        return None
    url = _read_url(primary, first_read)
    ref = f"refs/tags/{tag}"
    # Origin lists an annotated tag's own id on `ref`, and its commit only on `^{}`.
    listed = (
        _listed(primary, url, ref, f"{ref}^{{}}", first_read=first_read)
        if url
        else None
    )
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


def _local_releases(primary: Path, base: str, default: str) -> list[str]:
    """Return `default` and the tags of its release merges past raw `base`, or none."""
    tags = _release_tags(primary)
    commits = _foreign_commit(primary, base, default, tags=tags)
    released = {_history(primary, "rev-parse", f"{sha}^2") for sha in commits}
    named = [tag for tag, (_, commit) in tags.items() if commit in released]
    return [default, *named] if commits else []


def _unpushed(primary: Path, first_read: bool = False) -> list[tuple[str, str]]:
    """Return each `(ref, sha)` to push.

    Why: 0053-sandbox-patch design D2.
    """
    url = _read_url(primary, first_read)
    if not _has_origin(primary):
        return []
    default = (
        _push_default(primary, url) if first_read and url else default_branch(primary)
    )
    done = (
        _remote(primary, "ls-remote", "--heads", "--tags", "--", url) if url else None
    )
    if done is None or done.returncode != 0:
        if done is not None and first_read:
            raise Unreachable(1, _why(done))
        tracking = f"refs/remotes/origin/{default}"
        if _maybe(primary, "rev-parse", "-q", "--verify", tracking) is None:
            raise Stop(1, f"conduct: halt — origin has no {default}: push it by hand")
        commits = _foreign_commit(primary, tracking, default)
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
        _keep_base(primary, base)
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

    Why: 0052-security-hardening
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


def _native() -> str:
    """Return the host's native architecture, read past a translated process.

    e.g. an `x86_64` Python under Rosetta on Apple silicon → "arm64"
    Why: 0057-run-fixes design D1.
    """
    try:
        done = subprocess.run(
            ["sysctl", "-n", "hw.optional.arm64"],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired):
        return os.uname().machine
    return "arm64" if done.stdout.strip() == "1" else os.uname().machine


def probe_gate(mark: Path, native: str) -> str:
    """Return the scratch `Makefile`: its gate passes when `mark` refuses a write.

    Its shell must run as `native`: a translated one fails before the mark.
    Why: 0053-sandbox-patch design D1; 0057-run-fixes design D1.
    """
    target = shlex.quote(str(mark)).replace("$", "$$")
    arch = shlex.quote(native).replace("$", "$$")
    return (
        f'gate:\n\tuname -m > .arch\n\ttest "$$(cat .arch)" = {arch}\n'
        f"\t! echo escaped >> {target}\n\ttouch .gated\n"
    )


def _read_arch(arch: Path) -> tuple[str, int] | None:
    """Return the first 64 bytes of `arch` and its link count, or None for a link.

    The scratch folder is worker-written. e.g. `.arch` holding "i386" → ("i386", 1)
    Why: 0072-paydown design D1.
    """
    try:
        fd = os.open(arch, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError:
        return None
    with os.fdopen(fd, "rb") as handle:
        text = handle.read(64).decode(errors="replace").strip()
        return text, os.fstat(handle.fileno()).st_nlink


def check_probe(scratch: Path, mark: Path | None) -> str | None:
    """Return why the probe check fails, or None; the scratch gate leaves `.gated`.

    A `mark` gone or written fails, naming its executor: `probe-codex-41` → `codex`.
    `check probe` has no mark, and skips it. Why: 0053-sandbox-patch design D1.
    """
    executor = mark.name.split("-")[1] if mark is not None else "the worker"
    if mark is not None and (not mark.is_file() or mark.stat().st_size):
        return f"{executor} wrote outside its reach: it runs unsandboxed"
    arch = scratch / ".arch"
    if arch.is_symlink() or arch.is_file():
        native = _native()
        shell, links = _read_arch(arch) or ("", 0)
        if shell != native:
            if links == 1 and re.fullmatch(r"[A-Za-z0-9_]{1,16}", shell):
                return f"{executor}'s shell runs as {shell} on a {native} host"
            return f"{executor}'s shell runs an unreadable .arch on a {native} host"
    held = _show(scratch, "HEAD", "probe.txt")
    if held is None:
        return "HEAD holds no probe.txt"
    if held.strip() != "ok":
        return f"probe.txt reads {held.strip()!r}"
    if (scratch / ".gated").is_file():
        return None
    return "make gate left no .gated"


def check_tree(tree: Path) -> str | None:
    """Return why the probe's linked tree fails, or None when its index was written.

    `tree.txt`, read through no link, must hold what `git write-tree` prints there.
    Why: 0104-codex-limits design D6.
    """
    named = _bounded(tree / "tree.txt")
    made = _maybe(tree, "write-tree")
    if named is not None and made is not None and named.strip() == made.strip():
        return None
    return "the worker could not write a linked worktree's index: git write-tree"


def checker_fixture(scratch: Path) -> tuple[str, str]:
    """Build the checker probe's repo in `scratch`; return its base and head shas.

    Its change asks `total` to round to cents, and its head does not: the seeded
    defect. Why: 0096-codex-ready design D8.
    """
    change = "openspec/changes/0001-probe"
    total = "def total(prices: list[float]) -> float:\n"
    base = {
        ".gitignore": ".minions/\n",
        "AGENTS.md": "# Probe fixture\n",
        "total.py": f"{total}    return sum(prices)\n",
    }
    head = {
        f"{change}/proposal.md": "---\nbump: patch\n---\n\n# Probe\n\n"
        "`total` rounds its sum to cents.\n",
        f"{change}/design.md": "# Probe — design\n\n## Decisions\n\n"
        "| id | decision |\n|---|---|\n| D1 | `total` rounds its sum to cents |\n\n"
        "## Dependencies\n\nNone.\n",
        f"{change}/tasks.md": "## Progress\n\n- [x] 1 — Round\n\n## 1 — Round\n\n"
        "- [x] 1.1 Round `total`'s sum to cents in `total.py`.\n",
        f"{change}/specs/probe/spec.md": "## ADDED Requirements\n\n"
        "### Requirement: The total rounds to cents\n\n"
        "`total` SHALL round its sum to cents.\n\n#### Scenario: Two prices\n"
        "- **WHEN** `total([0.1, 0.2])` runs\n- **THEN** it returns `0.3`\n",
        "total.py": f'{total}    """Return the sum of `prices`."""\n'
        "    return sum(prices)\n",
    }
    _git(scratch, "init", "-q", "-b", "main")
    shas = []
    for files, message in ((base, "base"), (head, "docs(0001-probe): the change")):
        for name, text in files.items():
            (scratch / name).parent.mkdir(parents=True, exist_ok=True)
            (scratch / name).write_text(text)
        _git(scratch, "add", *files)
        _git(scratch, *SCRATCH_IDENTITY, "commit", "-q", "-m", message)
        shas.append(_git(scratch, "rev-parse", "HEAD").strip())
    packet = scratch / ".minions" / "changes" / "0001-probe" / "diff.patch"
    packet.parent.mkdir(parents=True)
    packet.write_text(_git(scratch, "diff", *shas))
    return shas[0], shas[1]


def check_checker(scratch: Path, log: Path) -> str | None:
    """Return why the checker probe fails, or None; its verdict is never judged.

    Why: 0096-codex-ready design D9.
    """
    findings = scratch / ".minions" / "changes" / "0001-probe" / "conformance.md"
    try:
        regular = stat.S_ISREG(os.lstat(findings).st_mode)
    except OSError:
        regular = False
    if not regular:
        return "the checker wrote no conformance.md"
    text = findings.read_text(errors="replace")
    if missing := [key for key in FINDINGS_KEYS if _frontmatter(text, key) is None]:
        return f"conformance.md lacks {missing[0]}"
    for key, held in (("type", "conformance"), ("plan", "0001-probe")):
        if (value := _frontmatter(text, key)) != held:
            return f"conformance.md's {key} is {value}"
    with log.open(errors="replace") as lines:
        for line in lines:
            if '"turn.completed"' not in line:
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if (
                isinstance(event, dict)
                and event.get("type") == "turn.completed"
                and isinstance(event.get("usage"), dict)
            ):
                return None
    return "codex's log holds no usage event"


def check(
    primary: Path,
    stage: str,
    version: Version,
    first_read: bool = False,
    offline: bool = False,
    *,
    phase: str | None = None,
    notes: list[str] | None = None,
) -> str | None:
    """Return why a station's check on disk fails, or None when it passes.

    A build `phase` number checks that phase alone; `close` or none, the whole build.
    Why: 0102-build-per-phase design D2; 0109-converge-done-order design D3.
    """
    if stage == "release":
        return _check_release(primary, version, first_read, offline)
    if version.tree is None:
        return f"{version.change} has no worktree"
    if stage == "build" and phase is not None and phase != "close":
        return _check_phase(primary, version, version.tree, phase)
    if stage == "build":
        return _check_build(primary, version, version.tree)
    if stage == "converge":
        return _check_converge(primary, version, version.tree, notes=notes)
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
        self.held: list[tuple[str, str, str]] | None = None

    def event(self, who: str, event: str, detail: str) -> None:
        """Append `<HH:MM:SS> · <who> · <event> — <detail>`, the detail on one line.

        While `held` is a list, the event waits there instead.
        """
        if self.held is not None:
            self.held.append((who, event, detail))
            return
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


def _models_file(runs: Path, change: str) -> dict[str, object]:
    """Return the cut's models file as TOML reads it; {} with no file."""
    path = _change_dir(runs.parent, change) / "models.toml"
    if not path.is_file():
        return {}
    try:
        return tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as error:
        raise Stop(
            1, f"conduct: halt — changes/{change}/models.toml: {error}"
        ) from None


def _table(runs: Path, change: str, name: str) -> dict[str, object] | None:
    """Return a table of the cut's models file; None with no file or no such table.

    A dotted name walks in: e.g. "converge.fix" → `[converge]`'s `fix` table.
    """
    table: object = _models_file(runs, change)
    for part in name.split("."):
        table = table.get(part) if isinstance(table, dict) else None
    return table if isinstance(table, dict) else None


def _decides(runs: Path, change: str) -> bool:
    """Return whether the cut's models file says `decide = "recommended"` at its top.

    Why: 0085-self-healing-ship design D3.
    """
    return _models_file(runs, change).get("decide") == "recommended"


def _models(
    runs: Path, change: str, station: str, run: str
) -> tuple[str, str | None, str | None]:
    """Return the station's executor, model and effort from the cut's models file.

    Integrate uses the `[release]` table, and the rescue `[rescue]`, else `[build]`.
    Why: 0067 D5; 0089 D2; 0094 D1; 0095 D2; 0097 D3; 0100 D8; 0102 D5; 0108 D8.
    """
    names = {"integrate": ("release",), "rescue": ("rescue", "build")}
    names |= {worker: (worker, old) for worker, old in OLD_WORKERS.items()}
    tables = (_table(runs, change, name) for name in names.get(station, (station,)))
    table = next((table for table in tables if table is not None), {})
    executor = table.get("executor", run)
    model, effort = table.get("model"), table.get("effort")
    file = f"changes/{change}/models.toml"
    own = "executor" in table
    if station in (*WORKERS, MODERATE):
        if own and station in (FIXER, MODERATE):
            raise Stop(1, f"conduct: halt — {file}: {station} names an executor")
        for value in (model, effort):
            if isinstance(value, str) and not TOKEN.fullmatch(value):
                raise Stop(
                    1,
                    f"conduct: halt — {file}: {station} {value!r}"
                    " is not a model or effort",
                )
    if station == MODERATE:
        executor = _models(runs, change, "build", run)[0]
    if station in WORKERS:
        converge = _models(runs, change, "converge", run)[0]
        executor = executor if own else converge
    model = model if isinstance(model, str) else None
    if station == "supervise" and executor == "claude":
        model, effort = model or SUPERVISOR[0], effort or SUPERVISOR[1]
    if station == "converge" and executor == "claude" and model is effort is None:
        model, effort = CHECKER_DEFAULT
    if executor not in EXECUTORS:
        raise Stop(1, f"conduct: halt — {file}: executor {executor!r} unknown")
    codex = executor == "codex" and (station not in WORKERS or own)
    if codex and (model or "").startswith("claude"):
        raise Stop(1, f"conduct: halt — {file}: {station} on codex, model {model}")
    return str(executor), model, effort if isinstance(effort, str) else None


def _shadows(runs: Path, change: str) -> bool:
    """Return whether the cut's models file says `[converge] shadow = true`.

    Why: 0097-cross-model design D3.
    """
    table = _table(runs, change, "converge")
    return table is not None and table.get("shadow") is True


def _shadow(
    converge: tuple[str, str | None, str | None],
    checker: tuple[str, str | None, str | None],
) -> tuple[str, str | None, str | None]:
    """Return a shadow checker's models: the executor `checker` does not run on.

    Why: 0097-cross-model design D3.
    """
    executor = next(name for name in EXECUTORS if name != checker[0])
    if converge[0] == executor:
        return converge
    return executor, None, None


def _skips(runs: Path, change: str) -> frozenset[str]:
    """Return the converge stations the cut's models file skips; none on a bad file.

    Why: 0105-converge-switches design D2.
    e.g. `[converge.adversarial] skip = true` → {"converge.adversarial"}
    """
    checkers = [name for name in WORKERS if name != FIXER]
    try:
        tables = {name: _table(runs, change, name) for name in ("converge", *checkers)}
    except (Stop, ValueError):
        return frozenset()
    skipping = {
        name for name, table in tables.items() if table and table.get("skip") is True
    }
    return (
        frozenset(("converge", *WORKERS))
        if "converge" in skipping
        else frozenset(skipping)
    )


def _skips_rescue(runs: Path, change: str) -> bool:
    """Return whether the cut's models file says `[rescue] skip = true`."""
    table = _table(runs, change, "rescue")
    return table is not None and table.get("skip") is True


def _auto_grants(runs: Path, change: str) -> bool:
    """Return whether the run may grant a cap: no `[converge] auto_grant = false`.

    Why: 0070-cap-policy design D4.
    """
    table = _table(runs, change, "converge")
    return table is None or table.get("auto_grant") is not False


def _is_cap(stage: str, halt: str) -> bool:
    """Return whether a halt is a converge cap: `cap reached` at `converge-halted`.

    Why: 0070-cap-policy design D2.
    """
    return stage == "converge-halted" and "cap reached" in halt


def _field(card: str, name: str) -> str:
    """Return a card's `- **<name>:** <value>` value, or "" with none."""
    found = re.search(rf"^[ \t]+- \*\*{name}:\*\*[ \t]*(.*)$", card, re.MULTILINE)
    return found[1].strip() if found else ""


def _cards_in(text: str) -> Iterator[tuple[str, str]]:
    r"""Yield each findings card's id and its text, to the next card.

    e.g. "- **R1 — a finding**\n  - **Status:** open\n" → ("R1", that text)
    """
    starts = list(CARD.finditer(text))
    ends = [card.start() for card in starts[1:]] + [len(text)]
    for title, end in zip(starts, ends[: len(starts)], strict=True):
        yield title[1], text[title.start() : end]


def _severity(card: str) -> str:
    """Return a card's severity: its `Priority`'s first part, in lower case."""
    # A station may wrap a field's value in backticks.
    return _field(card, "Priority").split(" · ")[0].strip(" `").lower()


def _category(card: str) -> str:
    """Return a card's category: its `Priority`'s third part, in lower case, or "".

    e.g. "high · adversarial · security — why" → "security"
    """
    parts = _field(card, "Priority").split(" · ")
    return parts[2].split(" — ")[0].strip(" `").lower() if len(parts) > 2 else ""


def _status(card: str) -> str:
    """Return a card's `Status`, its backticks dropped, as `_severity` drops them."""
    return _field(card, "Status").strip(" `")


def _open_blockers(runs: Path, change: str) -> list[tuple[str, str]] | None:
    """Return each open blocking card's id and fix size; None when a file is unread.

    A card with no size is `a design change`. Why: 0070-cap-policy design D1.
    e.g. "- **R1 — …**", blocking, open, "· size: a test." → [("R1", "a test")]
    """
    found = []
    for role in ROLES:
        file = _change_dir(runs.parent, change) / f"{role}.md"
        if not file.is_file():
            return None
        try:
            text = file.read_text()
        except (OSError, UnicodeDecodeError):
            return None
        for name, card in _cards_in(text):
            blocking = _severity(card) in BLOCKS[role]
            if blocking and re.match(r"open\b", _status(card)):
                sized = re.search(r"size:([^:]*)$", _field(card, "Fix"))
                size = sized[1].strip(" `.") if sized else ""
                found.append((name, size or "a design change"))
    return found


def _security_blocks(runs: Path, change: str, halt: str) -> bool:
    """Return whether a card an `amend needed` halt names is a blocking security one.

    Why: 0085-self-healing-ship design D2;
    0095-converge-roles design D2.
    """
    ids = set(re.findall(r"\b[RS]\d+\b", halt.partition("amend needed — ")[2]))
    try:
        text = (_change_dir(runs.parent, change) / "adversarial.md").read_text()
    except (OSError, UnicodeDecodeError):
        return True
    return any(name in ids and _security_card(card) for name, card in _cards_in(text))


def _security_card(card: str) -> bool:
    """Return whether an adversarial card blocks, of category `security` or none.

    Why: 0095-converge-roles design D2.
    """
    return _severity(card) in BLOCKS["adversarial"] and _category(card) in (
        "security",
        "",
    )


def _security_held(runs: Path, change: str, halt: str) -> bool:
    """Return whether a blocking security card bars the supervisor at a converge halt.

    Why: 0089-supervisor design D6;
    0095-converge-roles design D2.
    """
    ids = set(re.findall(r"\b[RS]\d+\b", halt.partition("amend needed — ")[2]))
    try:
        text = (_change_dir(runs.parent, change) / "adversarial.md").read_text()
    except (OSError, UnicodeDecodeError):
        return True
    return any(
        _security_card(card) and (name in ids or _status(card).startswith("open"))
        for name, card in _cards_in(text)
    )


def _rescue_amends(
    runs: Path, change: str, station: str, decide: bool
) -> tuple[str, ...]:
    """Return the change's files a rescue of `station`'s halt may amend; () for none.

    Why: 0085-self-healing-ship design D1, D2.
    """
    halt = _converge_halt(runs, change) or ""
    if station == "converge" and "amend needed" in halt:
        amends = () if _security_blocks(runs, change, halt) else AMENDS
    else:
        amends = AMENDS if station == "build" else ()
    return (*amends, "proposal.md") if decide and amends else amends


def _decisions(text: str | None) -> str:
    """Return a design's `## ` headings and its `## Decisions` section, or "".

    Why: 0085-self-healing-ship design D4; 0103-fewer-rounds design D3.
    """
    text = text or ""
    headings = re.findall(r"^## [^\n]*", text, re.MULTILINE)
    found = re.search(
        r"^## Decisions[^\n]*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
    )
    parts = re.split(r"^(?=### )", found[1] if found else "", flags=re.MULTILINE)
    return "\n".join([*headings, "".join(_unnoted(part) for part in parts)])


def _unnoted(part: str) -> str:
    """Return a `### D<n>` entry without its closing blank lines and fix notes.

    Any other part comes back as it is. Why: 0103-fewer-rounds design D3.
    """
    if not re.match(r"### D\d", part):
        return part
    lines = part.split("\n")
    while lines and (
        (line := lines[-1].removesuffix("\r")) == "" or FIX_NOTE.fullmatch(line)
    ):
        lines.pop()
    return "\n".join(lines) + "\n"


def _amend(
    tree: Path, change: str, before: str, amends: tuple[str, ...]
) -> tuple[str | None, str, bool]:
    """Return the rescue's amend past `before`, or None and why; and if it decided.

    Why: 0067-rescue design D3; 0085-self-healing-ship design D4.
    """
    if not _ancestor(tree, before, "HEAD"):
        return None, f"rescue moved HEAD off {before[:7]}", False
    commits = _git(tree, "rev-list", f"{before}..HEAD").split()
    allowed = {f"openspec/changes/{change}/{name}" for name in amends}
    listed = ("diff-tree", "--root", "-m", "-r", "--no-commit-id", "--name-only")
    paths = {path for sha in commits for path in _git(tree, *listed, sha).splitlines()}
    if touched := sorted(paths - allowed):
        return None, f"rescue touched {' '.join(touched)}", False
    if not commits:
        return None, "", False
    sha = commits[0]
    trailer = _git(tree, "log", "-1", "--format=%(trailers:key=Rescue)", sha)
    named = _subject(tree, sha) == f"docs({change}): amend the change directory"
    if len(commits) > 1 or not amends or not named or not trailer.strip():
        why = f"rescue commit {sha[:7]} is not one amend with a Rescue: trailer"
        return None, why, False
    proposal = f"openspec/changes/{change}/proposal.md"
    design = f"openspec/changes/{change}/design.md"
    was, now = (_decisions(_show(tree, rev, design)) for rev in (before, sha))
    if proposal in paths:
        decision = proposal
    elif was != now:
        decision = design
    else:
        return sha, "", False
    if "proposal.md" not in amends:
        return None, f"rescue changed a decision: {decision}", False
    by = ("log", "-1", "--format=%(trailers:key=Decided-by,valueonly)", sha)
    if _git(tree, *by).strip() != "rescue":
        why = f"rescue commit {sha[:7]} decided with no Decided-by: rescue trailer"
        return None, why, False
    return sha, "", True


def _supervised(tree: Path, change: str, before: str) -> tuple[str | None, str]:
    """Return the supervisor's amend past `before`, or None and why.

    Why: 0089-supervisor design D3.
    """
    if not _ancestor(tree, before, "HEAD"):
        return None, f"supervisor moved HEAD off {before[:7]}"
    commits = _git(tree, "rev-list", f"{before}..HEAD").split()
    folder = f"openspec/changes/{change}/"
    listed = ("diff-tree", "--root", "-m", "-r", "--no-commit-id", "--name-only")
    paths = {path for sha in commits for path in _git(tree, *listed, sha).splitlines()}
    if touched := sorted(path for path in paths if not path.startswith(folder)):
        return None, f"supervisor touched {' '.join(touched)}"
    if not commits:
        return None, ""
    sha = commits[0]
    parents = _git(tree, "rev-list", "--parents", "-n", "1", sha).split()[1:]
    trailer = _git(tree, "log", "-1", "--format=%(trailers:key=Supervisor)", sha)
    by = ("log", "-1", "--format=%(trailers:key=Decided-by,valueonly)", sha)
    named = _subject(tree, sha) == f"docs({change}): amend the change directory"
    one = len(commits) == 1 and len(parents) == 1
    decided = _git(tree, *by).strip() == "supervisor"
    if not (one and named and trailer.strip() and decided):
        why = "is not one amend with Supervisor: and Decided-by: supervisor trailers"
        return None, f"supervisor commit {sha[:7]} {why}"
    return sha, ""


def _opened(primary: Path, tree: Path, change: str) -> Opened:
    """Return the open merge in `tree` before its supervisor runs."""
    return Opened(
        _git(tree, "rev-parse", "HEAD").strip(),
        _git(tree, "rev-parse", "MERGE_HEAD").strip(),
        _git(tree, "ls-files", "-s"),
        _mtime(_change_dir(primary, change) / "integrate.settled"),
    )


def _settled(
    primary: Path, tree: Path, change: str, start: Opened
) -> tuple[str | None, str]:
    """Return the tree the supervisor staged in the open merge, or None and why.

    Why: 0090-supervisor-merge design D3.
    """
    if _git(tree, "rev-parse", "HEAD").strip() != start.head:
        return None, f"supervisor moved HEAD off {start.head[:7]}"
    merge = _maybe(tree, "rev-parse", "-q", "--verify", "MERGE_HEAD")
    if merge is None or merge.strip() != start.merge:
        return None, "supervisor closed the merge"
    marks = _change_dir(primary, change)
    if not (marks / "integrate.md").is_file():
        return None, f"supervisor removed .minions/changes/{change}/integrate.md"
    entries = set(start.index.splitlines()) ^ set(
        _git(tree, "ls-files", "-s").splitlines()
    )
    changed = {entry.split("\t", 1)[1] for entry in entries}
    if touched := sorted(
        path
        for path in changed
        if not (path.startswith(SETTLES) and path.endswith(".md"))
    ):
        return None, f"supervisor touched {' '.join(touched)}"
    unmerged = _conflicts(tree)
    unstaged = set(_git(tree, "diff", "--name-only").split()) - set(unmerged)
    unstaged |= set(_git(tree, "ls-files", "--others", "--exclude-standard").split())
    if unstaged:
        return None, f"supervisor left unstaged {' '.join(sorted(unstaged))}"
    if _mtime(marks / "integrate.settled") in (None, start.written):
        return None, ""
    if unmerged:
        return None, f"supervisor left {' '.join(unmerged)} unmerged"
    return _git(tree, "write-tree").strip(), ""


def _settle_kept(tree: Path, staged: str) -> str | None:
    """Return why integrate's merge holds more than the settled tree, or None.

    Why: 0090-supervisor-merge security S2.
    """
    merge = _git(tree, "rev-list", "--first-parent", "--merges", "-1", "HEAD").strip()
    body = _git(tree, "log", "-1", "--format=%b", merge).splitlines()
    fixed = {
        line.split(": test fixed", 1)[0] for line in body if ": test fixed" in line
    }
    moved = set(_git(tree, "diff", "--name-only", staged, f"{merge}^{{tree}}").split())
    if past := sorted(moved - fixed):
        return f"the merge holds {' '.join(past)} past the supervisor's settle"
    return None


def _mtime(path: Path) -> int | None:
    """Return a regular file's modification time in nanoseconds, else None."""
    try:
        status = path.lstat()
    except OSError:
        return None
    return status.st_mtime_ns if stat.S_ISREG(status.st_mode) else None


def _entries(folder: Path, empty: bool) -> list[str]:
    """Return the names in `folder`, deleting each when `empty`; none through a link.

    Why: 0067-rescue design D7.
    """
    try:
        fd = os.open(folder, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError:
        return []
    try:
        names = sorted(os.listdir(fd))
        if not empty:
            return names
        deleted = []
        for name in names:
            try:
                os.unlink(name, dir_fd=fd)
            except OSError:
                continue
            deleted.append(name)
        return deleted
    except OSError:
        return []
    finally:
        os.close(fd)


def _bounded(path: Path | str, fd: int | None = None) -> str | None:
    """Return a regular file's text, read following no link, at most `READ_BYTES`.

    A relative `path` is read in the folder `fd` holds. None when it is a link, no
    file or unreadable. Why: 0097-cross-model design D4.
    """
    text = None
    with contextlib.suppress(OSError):
        file = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        try:
            if stat.S_ISREG(os.fstat(file).st_mode):
                with os.fdopen(file, "rb", closefd=False) as handle:
                    data = handle.read(READ_BYTES + 1)
                if len(data) <= READ_BYTES:
                    text = data.decode(errors="replace")
        finally:
            os.close(file)
    return text


def _place(fd: int, name: str, text: str) -> None:
    """Write `name` whole through `fd`: made as `.<name>`, then renamed over the old.

    Each is made `O_EXCL`, following no link; a failure raises `OSError`.
    """
    part = f".{name}"
    for old in (name, part):
        with contextlib.suppress(OSError):
            os.unlink(old, dir_fd=fd)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW
    with os.fdopen(os.open(part, flags, 0o600, dir_fd=fd), "w") as handle:
        handle.write(text)
    os.rename(part, name, src_dir_fd=fd, dst_dir_fd=fd)


def _granted(runs: Path, change: str, take: bool) -> bool:
    """Return whether `runs/grants` holds `change`'s grant, deleting it when `take`.

    Why: 0067-rescue design D7.
    """
    try:
        fd = os.open(runs / "grants", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError:
        return False
    try:
        status = os.stat(change, dir_fd=fd, follow_symlinks=False)
        if take and stat.S_ISREG(status.st_mode):
            os.unlink(change, dir_fd=fd)
        return stat.S_ISREG(status.st_mode)
    except OSError:
        return False
    finally:
        os.close(fd)


def reach(primary: Path) -> list[Path]:
    """Return what a worker may edit: the primary and each open worktree.

    Why: 0050-codex-review design D5; 0096-codex-ready design D7;
    0100-worker-diet design D4.
    """
    root = primary.resolve()
    if _common_dir(root) is None:
        return [root]
    live = {version.change for version in open_versions(root)} | set(_cuts(root))
    trees = [root]
    for branch, path in sorted(_worktrees(root).items(), key=lambda item: item[1]):
        if branch in live and not any(path.is_relative_to(tree) for tree in trees):
            trees.append(path)
    return trees


def ship_lines(primary: Path) -> ShipLines:
    """Return `AGENTS.md`'s `Ship tools:` and `Ship network:` lines.

    Why: 0052-security-hardening design D2;
    0056-loopback-removal design D2.
    """
    network = _agents_values(primary, "Ship network") or []
    for domain in network:
        if not DOMAIN.fullmatch(domain):
            raise Stop(
                1, f"conduct: halt — AGENTS.md: Ship network {domain!r} is not a domain"
            )
    if _agents_line(primary, "Ship loopback") is not None:
        raise Stop(
            1,
            "conduct: halt — AGENTS.md: Ship loopback: was removed"
            " (change 0056-loopback-removal): delete the line",
        )
    tools = _agents_values(primary, "Ship tools") or []
    return ShipLines(tools, network)


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


def worker_settings(
    primary: Path,
    trees: list[Path],
    common: Path | None,
    network: list[str],
) -> str:
    """Return the Claude worker's settings, as JSON: its sandbox, the operator's off.

    Why: 0052-security-hardening D1; 0053-sandbox-patch D1; 0056-loopback-removal D1;
    0100-worker-diet D2.
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
        "network": {"allowedDomains": [*NETWORK, *network]},
    }
    return json.dumps(
        {
            "sandbox": sandbox,
            "enabledPlugins": _plugins_off(),
            "outputStyle": "default",
            "autoMemoryEnabled": False,
        }
    )


def _plugins_off() -> dict[str, bool]:
    """Return each plugin the operator's Claude settings name, mapped to False.

    User settings merge under `--settings`, so a plugin is off only by name; a file
    it cannot read names none. Why: 0100-worker-diet design D2.
    """
    folder = os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude"
    try:
        settings = json.loads((Path(folder) / "settings.json").read_text())
    except (OSError, ValueError):
        return {}
    plugins = settings.get("enabledPlugins") if isinstance(settings, dict) else None
    return dict.fromkeys(plugins, False) if isinstance(plugins, dict) else {}


def _temp_folder(prefix: str) -> Path:
    """Return a fresh folder under `TMPDIR`, else stop with 2.

    e.g. `_temp_folder("mf-sandbox-")` → `<TMPDIR>/mf-sandbox-k3j9x2`.
    Why: 0111-sandbox-tmp design D2.
    """
    parent = Path(os.environ.get("TMPDIR") or "/tmp")  # noqa: S108
    inside = subprocess.run(
        ["git", "-C", str(parent), "rev-parse", "--git-dir"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        timeout=GIT_TIMEOUT,
    )
    if inside.returncode == 0:
        raise Stop(
            2, f"conduct: cannot run — TMPDIR {parent} lies inside a git repository"
        )
    try:
        return Path(tempfile.mkdtemp(prefix=prefix, dir=parent)).resolve()
    except OSError as error:
        raise Stop(2, f"conduct: cannot run — TMPDIR {parent}: {error}") from error


def _profile(trees: list[Path], home: Path) -> str:
    """Return the Seatbelt profile: writes in `trees`, no secret read, no network.

    A later rule beats an earlier one, so the secrets stay denied inside a tree.
    Why: 0107-sandbox-runner design D1.
    """

    def quoted(path: Path) -> str:
        escaped = str(path.resolve()).replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    writes = " ".join(f"(subpath {quoted(tree)})" for tree in trees)
    devices = " ".join(
        f'(literal "{device}")'
        for device in (
            *("/dev/null", "/dev/tty", "/dev/dtracehelper", "/dev/autofs_nowait"),
            *("/dev/stdout", "/dev/stderr"),
        )
    )
    secrets = " ".join(
        f"(subpath {quoted(home / secret.removeprefix('~/'))})" for secret in SECRETS
    )
    return "\n".join(
        (
            "(version 1)",
            "(allow default)",
            "(deny file-write*)",
            f"(allow file-write* {writes} {devices})",
            f"(deny file-read* file-write* {secrets})",
            "(deny network*)",
        )
    )


def _watch(
    group: int,
    timeout: float,
    grace: float,
    done: threading.Event,
    expired: threading.Event,
) -> None:
    """End `group` after `timeout` s: SIGTERM, then SIGKILL after `grace`.

    Return at once when `done` is set first. Why: 0114-faster-plan-check design D5.
    """
    if done.wait(max(timeout, 0)):
        return
    expired.set()
    with contextlib.suppress(ProcessLookupError):
        os.killpg(group, signal.SIGTERM)
    if done.wait(grace):
        return
    with contextlib.suppress(ProcessLookupError):
        os.killpg(group, signal.SIGKILL)


def sandboxed(
    argv: list[str],
    cwd: Path,
    trees: list[Path],
    out: TextIO | None = None,
    timeout: float | None = None,
    grace: float = 5.0,
) -> int:
    """Run `argv` in `cwd` under macOS Seatbelt and return its exit code.

    A `timeout` ends the command's group and gives 124. Why: 0107-sandbox-runner
    design D2, 0108-converge-script D6, 0111-sandbox-tmp D3, 0114-faster-plan-check D5.
    """
    sandbox_exec = shutil.which("sandbox-exec")
    if sandbox_exec is None:
        raise Stop(
            2, "conduct: cannot run — no OS sandbox: sandbox-exec is not on PATH"
        )
    minions = trees[0] / ".minions"
    try:
        os.close(_folder_fd(trees[0], ".minions"))
    except OSError as error:
        raise Stop(2, f"conduct: cannot run — run folder {minions}: {error}") from error
    tmp = _temp_folder("mf-sandbox-")
    env = {
        name: value
        for name, value in os.environ.items()
        if name != "VIRTUAL_ENV" and name not in TOKENS
    }
    for pair in HOOKS_OFF:
        key, _, value = pair.partition("=")
        env[key] = value
    env["UV_OFFLINE"] = "1"
    env["UV_CACHE_DIR"] = str(trees[0] / ".minions" / "uv-cache")
    env["TMPDIR"] = str(tmp)
    denied = False
    done, expired = threading.Event(), threading.Event()
    try:
        with subprocess.Popen(
            [sandbox_exec, "-p", _profile([*trees, tmp], Path.home()), *argv],
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="replace",
            start_new_session=timeout is not None,
        ) as process:
            if timeout is not None:
                watcher = (process.pid, timeout, grace, done, expired)
                threading.Thread(target=_watch, args=watcher, daemon=True).start()
            for line in process.stdout or ():
                print(line, end="", file=out or sys.stdout, flush=True)
                denied = denied or CODEX_DENIAL in line
            code = process.wait()
    finally:
        done.set()
        _remove_temp(tmp, out)
    if expired.is_set():
        print(
            f"sandboxed: timed out — killed after {timeout} s", file=out or sys.stderr
        )
        return 124
    if code != 0 and denied:
        print(
            "sandboxed: denied — the OS sandbox refused a call:"
            " writes stay in the trees, no network",
            file=out or sys.stderr,
        )
    return code if code >= 0 else 128 - code


def tools_for(station: str) -> tuple[str, ...]:
    """Return the tools a Claude worker of `station` starts with.

    e.g. "probe-codex" → ("Bash", "Read"); "converge-adversarial" → `WORKER_TOOLS`.
    Why: 0100-worker-diet design D1, C5.
    """
    if station.startswith("probe"):
        return STATION_TOOLS["probe"]
    return STATION_TOOLS.get(station, WORKER_TOOLS)


def _brief_refused(brief: Path, executor: str, remedy: str) -> str | None:
    """Return why a cutter may not be given `brief`, else None.

    Why: 0082-cut-station design D5.
    """
    try:
        regular = stat.S_ISREG(os.lstat(brief).st_mode)
        beside = os.listdir(brief.parent)
    except OSError:
        regular, beside = False, []
    if not regular:
        return f"the brief {brief} is a link or no file"
    if executor == "codex" and beside != [brief.name]:
        return (
            f"a Codex cutter writes its brief's whole folder, and {brief.parent} holds"
            f" more than the brief: {remedy}"
        )
    return None


def _run_dir(primary: Path) -> Path:
    """Return the primary's `.minions`, stopping with 1 when it is a link or no folder.

    A cutter is given it by name, and its parent is every other worker's to rename
    in. Why: 0082-cut-station design D5.
    """
    minions = primary / ".minions"
    try:
        folder = stat.S_ISDIR(os.lstat(minions).st_mode)
    except OSError:
        folder = False
    if not folder:
        raise Stop(1, "conduct: halt — .minions is a link or no folder")
    return minions


def _unswapped(paths: list[Path]) -> None:
    """Stop with 1 at the first path that is a link, no folder or not its resolved path.

    A worker can swap a writable root between `reach` and a Codex spawn.
    Why: 0096-codex-ready design D7.
    """
    for path in paths:
        try:
            folder = stat.S_ISDIR(os.lstat(path).st_mode)
        except OSError:
            folder = False
        if not folder or path.resolve() != path:
            raise Stop(
                1,
                f"conduct: halt — the writable root {path} is a link or moved:"
                " a worker swapped it",
            )


def _gitdirs(common: Path) -> list[Path]:
    """Return each linked worktree's gitdir under `common`, sorted: folders, no link.

    Why: 0104-codex-limits design D6.
    """
    folder = common / "worktrees"
    try:
        if not stat.S_ISDIR(os.lstat(folder).st_mode):
            return []
        names = sorted(os.listdir(folder))
    except OSError:
        return []
    found: list[Path] = []
    for name in names:
        with contextlib.suppress(OSError):
            if stat.S_ISDIR(os.lstat(folder / name).st_mode):
                found.append(folder / name)
    return found


def argv(
    executor: str,
    prompt: str,
    cwd: Path,
    model: str | None,
    effort: str | None,
    repo: Repo,
    lines: ShipLines | None = None,
    brief: Path | None = None,
    *,
    station: str | None = None,
) -> list[str]:
    """Return the worker's command line, the shell rules appended to the prompt.

    Why: 0082-cut-station design D5; 0100-worker-diet design D1–D4;
    a Codex worker's own `TMPDIR`, 0111-sandbox-tmp design D5.
    """
    prompt = f"{prompt}\n\n{SHELL_RULES}"
    if agent := os.environ.get("MF_SHIP_AGENT"):
        return [*shlex.split(agent), prompt]
    primary, common = repo
    emptied = "remove every other file from it, hidden ones too, then rejoin the cut"
    if brief is not None and (why := _brief_refused(brief, executor, emptied)):
        raise Stop(1, f"conduct: halt — {why}")
    trees = reach(primary) if brief is None else [cwd, _run_dir(primary)]
    edits = [] if brief is None else [brief]
    cache = f"UV_CACHE_DIR={primary / '.minions' / 'uv-cache'}"
    if executor == "claude":
        # A worker's `mktemp` lands inside its sandbox.
        # Why: 0084-ship-fixes-2 design D6.
        tmp = primary / ".minions" / "tmp"
        tmp.mkdir(parents=True, exist_ok=True)
        scratch = f"TMPDIR={tmp}"
        tools, network = lines or ship_lines(primary)
        allowed, denied = allowlist(trees, tools)
        allowed += [f"Edit(/{path})" for path in edits]
        hour = "ENABLE_PROMPT_CACHING_1H=1"
        ttl = hour if station in CACHE_HOUR else "FORCE_PROMPT_CACHING_5M=1"
        return [
            *("env", "-u", "VIRTUAL_ENV", *HOOKS_OFF, cache, scratch),
            *((ttl,) if station else ()),
            *("claude", "-p", prompt),
            *(("--model", model) if model else ()),
            *(("--effort", effort) if effort else ()),
            *("--output-format", "stream-json", "--verbose"),
            *(arg for tree in trees for arg in ("--add-dir", str(tree))),
            *(
                "--settings",
                worker_settings(primary, [*trees, *edits], common, network),
            ),
            # A worker can write the project's settings and `.mcp.json`, and each
            # runs at a start, outside the sandbox.
            # Why: 0052-security-hardening design D1.
            *("--setting-sources", "user"),
            # No MCP server starts, the operator's own included.
            # Why: 0076-context-cost design D2.
            *("--strict-mcp-config",),
            *("--exclude-dynamic-system-prompt-sections",),
            *(("--tools", ",".join(tools_for(station))) if station else ()),
            *("--allowedTools", *allowed, "--disallowedTools", *denied),
        ]
    # Why: 0050-codex-review design D5.
    if common and _common_dir(primary) != common:
        raise Stop(1, "conduct: halt — the primary's .git moved during the run")
    # Codex roots are folders: a cutter's holds its brief's.
    folders = [
        *([common, *_gitdirs(common)] if common else []),
        *trees,
        *(path.parent for path in edits),
    ]
    _unswapped([*folders, cwd])
    # The worker's own temp folder; zsh makes a here-document's file under `TMPPREFIX`.
    # Why: 0111-sandbox-tmp design D5.
    temp = _temp_folder("mf-codex-")
    roots = [*(str(folder) for folder in folders), str(temp)]
    # Why: 0050-codex-review design D4.
    system = "/usr/bin:/bin:/usr/sbin:/sbin"
    path = f"PATH={system}:{os.environ.get('PATH', '')}"
    own = (f"TMPDIR={temp}", f"TMPPREFIX={temp}/zsh")
    env = ("env", "-u", "VIRTUAL_ENV", *HOOKS_OFF, cache, *own, path)
    return [
        *env,
        *("codex", "exec"),
        *(("-m", model) if model else ()),
        *(("-c", f"model_reasoning_effort={effort}") if effort else ()),
        *("-s", "workspace-write"),
        # The operator's Codex config sets nothing, and the log is one event a line.
        # Why: 0096-codex-ready design D1.
        *("--ignore-user-config", "--json"),
        *("-c", "allow_login_shell=false"),
        *("-c", f"sandbox_workspace_write.writable_roots={json.dumps(roots)}"),
        # The temp folder is a root by its name in `roots` alone: Codex's own root of
        # `TMPDIR`, links resolved, stays off. Why: D51; 0111-sandbox-tmp design D5.
        *("-c", "sandbox_workspace_write.exclude_tmpdir_env_var=true"),
        # No `/tmp` root; a Claude worker's own temp folder can still hold a forged
        # entry's folder, which Known gaps names. Why: 0096-codex-ready design D7.
        *("-c", "sandbox_workspace_write.exclude_slash_tmp=true"),
        *("-c", "sandbox_workspace_write.network_access=false"),
        # A worker can write a tree's `.codex/`, and an untrusted tree's starts nothing.
        # Why: 0053-sandbox-patch design D6.
        *codex_trust([cwd, *trees], "untrusted"),
        *("-C", str(cwd), prompt),
    ]


def _remove_temp(folder: Path, err: TextIO | None = None) -> None:
    """Remove `folder`, unlocking what a worker left unreadable; say so if it stays.

    e.g. a `000` subfolder is made `700`, then removed; a link is left.
    Why: 0111-sandbox-tmp design D3.
    """
    seen: set[str] = set()

    def unlock(_function: object, path: str, error: BaseException) -> None:
        if isinstance(error, PermissionError) and not os.path.islink(path):
            seen.add(path)
            os.chmod(path, 0o700)
            os.chmod(os.path.dirname(path), 0o700)

    previous: set[str] | None = None
    while os.path.lexists(folder) and seen != previous:
        previous = set(seen)
        shutil.rmtree(folder, onexc=unlock)
    if os.path.lexists(folder):
        print(f"conduct: could not remove {folder}", file=err or sys.stderr)


def _temp_of(command: list[str]) -> Path | None:
    """Return the folder `argv` made for a Codex `command`, else None.

    Why: 0111-sandbox-tmp design D6.
    """
    for element in command:
        name, _, value = element.partition("=")
        if name == "TMPDIR" and Path(value).name.startswith("mf-codex-"):
            return Path(value)
    return None


def _temp_gone(command: list[str]) -> None:
    """Remove the folder `_temp_of` names; a link is left, its target untouched."""
    if folder := _temp_of(command):
        _remove_temp(folder)


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


def _free_log(root: Path, parts: tuple[str, ...], name: str) -> tuple[Path, int]:
    """Return the first free of `<name>.log`, `<name>-2.log`, … in `root`'s `parts`.

    Why: 0077-run-metrics design D2; 0071-ship-fixes design D8;
    0080-minions-layout design D3, D6.
    """
    folder = root.joinpath(*parts)
    fd = _folder_fd(root, *parts)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW
    n = 1
    try:
        while True:
            log = f"{name}.log" if n == 1 else f"{name}-{n}.log"
            try:
                return folder / log, os.open(log, flags, 0o666, dir_fd=fd)
            except FileExistsError:
                n += 1
    finally:
        os.close(fd)


def work(
    command: list[str],
    cwd: Path,
    out: Path | int,
    claim: Path | None,
    timeout: float | None = None,
) -> tuple[int, bool]:
    """Run one worker in its own process group, output to `out`, held in `claim`.

    `out` is a path, or a descriptor it closes. Return its exit code and whether its
    `timeout`, else `TIMEOUT`, killed it. Why: 0104-codex-limits design D3.
    """
    limit = TIMEOUT if timeout is None else timeout
    if isinstance(out, Path):
        out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as sink:
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
            return worker.wait(timeout=limit), False
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


def _item(event: object, *kinds: str) -> dict[str, object]:
    """Return a Codex event's item when the event is one of `kinds`, else {}."""
    if not isinstance(event, dict) or event.get("type") not in kinds:
        return {}
    item = event.get("item")
    return item if isinstance(item, dict) else {}


def _codex_denied(item: dict[str, object]) -> str | None:
    """Return a Codex command the sandbox refused as `Bash(<command>)`, else None.

    Why: 0096-codex-ready design D3.
    """
    code = item.get("exit_code")
    if (
        item.get("type") == "command_execution"
        and isinstance(code, int)
        and code != 0
        and CODEX_DENIAL in str(item.get("aggregated_output"))
    ):
        return f"Bash({item.get('command')})"
    return None


def denials(log: Path) -> list[str]:
    """Return each tool use a worker's stream-json or Codex JSON log shows denied."""
    uses: dict[str, str] = {}
    found: list[str] = []
    with log.open(errors="replace") as lines:
        for line in lines:
            if not any(
                key in line for key in ('"tool_use"', '"is_error"', CODEX_DENIAL)
            ):
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if denied := _codex_denied(_item(event, "item.completed")):
                found.append(denied)
                continue
            for block in _blocks(event):
                if block.get("type") == "tool_use":
                    uses[str(block.get("id"))] = _call(block)
                elif block.get("type") == "tool_result" and block.get("is_error"):
                    text = _text(block.get("content"))
                    if any(denial in text for denial in DENIALS):
                        use = uses.get(str(block.get("tool_use_id")))
                        found.append(use or text.strip())
    return found


def _blocks(event: object) -> list[dict[str, object]]:
    """Return a Claude event's message content blocks; any other event's, none."""
    message = event.get("message") if isinstance(event, dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    listed = content if isinstance(content, list) else []
    return [block for block in listed if isinstance(block, dict)]


def lacked(log: Path) -> list[str]:
    """Return each tool a worker's log asked for and its station lacks.

    A result whose use the log lacks is named by its text. Why: 0100-worker-diet
    design D5.
    """
    names: dict[str, str] = {}
    found: list[str] = []
    with log.open(errors="replace") as lines:
        for line in lines:
            if '"tool_use"' not in line and MISSING not in line:
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            for block in _blocks(event):
                if block.get("type") == "tool_use":
                    names[str(block.get("id"))] = str(block.get("name"))
                elif block.get("type") == "tool_result" and block.get("is_error"):
                    text = _text(block.get("content"))
                    if MISSING in text:
                        name = names.get(str(block.get("tool_use_id")))
                        found.append(name or text.strip())
    return found


def first_turn(log: Path) -> int | None:
    """Return the context a worker's first turn read: its input and cache tokens.

    Why: 0100-worker-diet design D6.
    """
    kinds = ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
    codex = None
    with log.open(errors="replace") as lines:
        for line in lines:
            try:
                event = json.loads(line) if '"usage"' in line else None
            except ValueError:
                continue
            if not isinstance(event, dict):
                continue
            message = event.get("message")
            usage = message.get("usage") if isinstance(message, dict) else None
            if event.get("type") == "assistant" and isinstance(usage, dict):
                return sum(_count(usage.get(kind)) for kind in kinds)
            usage = event.get("usage")
            if isinstance(usage, dict) and event.get("type") == "turn.completed":
                codex = _count(usage.get("input_tokens")) if codex is None else codex
    return codex


def _count(value: object) -> int:
    """Return a usage count, 0 when it is no whole number."""
    return value if isinstance(value, int) else 0


def _codex_limit(event: dict[str, object]) -> str | None:
    """Return a Codex failed turn's or error's message naming a usage limit, else None.

    Why: 0096-codex-ready design D4.
    """
    error = event.get("error")
    message = {
        "turn.failed": error.get("message") if isinstance(error, dict) else None,
        "error": event.get("message"),
    }.get(str(event.get("type")))
    if isinstance(message, str) and "usage limit" in message.lower():
        return message
    return None


def usage_limit(log: Path) -> str:
    """Return ` · stopped by a usage limit · resets <time>`, or "" for any other exit.

    e.g. a `result` event with `api_error_status: 429`, its text naming `resets 5:50pm`;
    a Codex `turn.failed` whose message says `Try again at 5:50 PM.` → `resets 5:50 PM`
    """
    with log.open(errors="replace") as lines:
        for line in lines:
            if '"api_error_status"' not in line and "usage limit" not in line.lower():
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if isinstance(event, dict) and (message := _codex_limit(event)):
                resets = re.search(r"try again (?:at|in) ([^.]+)", message, re.I)
                named = f" · resets {resets[1].strip()}" if resets else ""
                return f" · stopped by a usage limit{named}"
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


class Window(NamedTuple):
    """A Codex rate-limit window: the share used and the epoch second it resets."""

    used: float
    resets: float


def _codex_home() -> Path:
    """Return Codex's home folder: `CODEX_HOME`, else `~/.codex`."""
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def _thread_id(log: Path) -> str | None:
    """Return the first `thread.started` event's `thread_id`, or None if not a token.

    The log is worker-written: the pattern keeps a glob out of `_rollout`.
    e.g. `{"type": "thread.started", "thread_id": "019a-b"}` → `019a-b`
    """
    with log.open(errors="replace") as lines:
        for line in lines:
            if '"thread.started"' not in line:
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if isinstance(event, dict) and event.get("type") == "thread.started":
                thread = event.get("thread_id")
                if isinstance(thread, str) and re.fullmatch(r"[0-9A-Za-z-]+", thread):
                    return thread
                return None
    return None


def _rollout(thread: str | None) -> Path | None:
    """Return the Codex rollout file `thread` names, or the newest one for None.

    e.g. `rollout-2026-11-08T10-00-00-<thread>.jsonl` under `sessions/YYYY/MM/DD/`
    """
    pattern = (
        "*/*/*/rollout-*.jsonl" if thread is None else f"*/*/*/rollout-*-{thread}.jsonl"
    )
    files = [
        path
        for path in (_codex_home() / "sessions").glob(pattern)
        if path.is_file() and not path.is_symlink()
    ]
    return max(files, key=os.path.getmtime, default=None)


def _number(value: object) -> float | None:
    """Return `value` as a float when it is a number, else None; a bool is no number."""
    if isinstance(value, int | float) and not isinstance(value, bool):
        return float(value)
    return None


def _windows(rollout: Path | None) -> dict[str, Window]:
    """Return the `primary` and `secondary` windows of a rollout's last `token_count`.

    A window whose `used_percent` or `resets_at` is no number is left out; a missing or
    unreadable rollout gives `{}`.
    """
    if rollout is None:
        return {}
    limits: dict[str, object] = {}
    try:
        with rollout.open(errors="replace") as lines:
            for line in lines:
                if '"token_count"' not in line:
                    continue
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                payload = event.get("payload") if isinstance(event, dict) else None
                if isinstance(payload, dict) and payload.get("type") == "token_count":
                    rates = payload.get("rate_limits")
                    limits = rates if isinstance(rates, dict) else limits
    except OSError:
        return {}
    windows: dict[str, Window] = {}
    for name in ("primary", "secondary"):
        rate = limits.get(name)
        if not isinstance(rate, dict):
            continue
        used, resets = _number(rate.get("used_percent")), _number(rate.get("resets_at"))
        if used is not None and resets is not None:
            windows[name] = Window(used, resets)
    return windows


def _next_clock(text: str, now: float) -> float | None:
    """Return the epoch of the next local time `text` names after `now`, or None.

    e.g. `5:50 PM` at 10:00 → today 17:50; at 18:00 → tomorrow 17:50
    """
    try:
        clock = time.strptime(text.strip(), "%I:%M %p")
    except ValueError:
        return None
    today = time.localtime(now)
    day = (*today[:3], clock.tm_hour, clock.tm_min, 0, 0, 0, -1)
    ahead = time.mktime(day)
    if ahead > now:
        return ahead
    return time.mktime((*today[:2], today.tm_mday + 1, *day[3:]))


def _reset_at(log: Path, now: float) -> float:
    """Return the epoch second a Codex limit lifts: the rollout, the text, else never.

    The rollout is the one the log's `thread_id` names; its latest window at 100%, else
    its most used, gives the reset. The log's `try again at` time is the fallback.
    """
    windows = _windows(_rollout(_thread_id(log)))
    if windows:
        full = [window.resets for window in windows.values() if window.used >= 100]
        return max(full) if full else max(windows.values(), key=lambda w: w.used).resets
    named = re.search(r"resets (.+)$", usage_limit(log))
    clock = _next_clock(named[1], now) if named else None
    return math.inf if clock is None else clock


def _headroom(now: float) -> float | None:
    """Return the reset of a primary window at `HEADROOM` or more, else None."""
    primary = _windows(_rollout(None)).get("primary")
    if primary and primary.used >= HEADROOM and primary.resets > now:
        return primary.resets
    return None


def tokens_of(log: Path) -> int | None:
    """Return a worker log's tokens, or None when it holds no usage.

    Why: 0104-codex-limits design D5.
    """
    codex: int | None = None
    claude: int | None = None
    kinds = ("inputTokens", "outputTokens", "cacheReadInputTokens")
    kinds += ("cacheCreationInputTokens",)
    with log.open(errors="replace") as lines:
        for line in lines:
            if '"turn.completed"' not in line and '"modelUsage"' not in line:
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if not isinstance(event, dict):
                continue
            usage = event.get("usage")
            if event.get("type") == "turn.completed" and isinstance(usage, dict):
                turn = _count(usage.get("input_tokens")) + _count(
                    usage.get("output_tokens")
                )
                codex = (codex or 0) + turn
            models = event.get("modelUsage")
            if event.get("type") == "result" and isinstance(models, dict):
                claude = sum(
                    _count(model.get(kind))
                    for model in models.values()
                    if isinstance(model, dict)
                    for kind in kinds
                )
    return codex if codex is not None else claude


def _stamped(text: str, model: str | None, tokens: int | None) -> str | None:
    """Return a findings file with its frontmatter's `model:` and `tokens:` set.

    None when it has no frontmatter. e.g. `model: x` → `model: m`, then `tokens: 5`
    """
    found = re.match(r"---\n(.*?\n)---\n", text, re.DOTALL)
    if found is None:
        return None
    kept = [
        line
        for line in found[1].splitlines(keepends=True)
        if not line.startswith("tokens:")
    ]
    stamp = [f"model: {model or 'default'}\n"]
    stamp += [] if tokens is None else [f"tokens: {tokens}\n"]
    at = next((i for i, line in enumerate(kept) if line.startswith("model:")), None)
    if at is None:
        kept += stamp
    else:
        kept[at : at + 1] = stamp
    return f"---\n{''.join(kept)}---\n{text[found.end() :]}"


def _stamp(folder: Path, name: str, model: str | None, tokens: int | None) -> None:
    """Set a findings file's `model:` and `tokens:`, following no link; else leave it.

    A file that is no regular file, or has no frontmatter, is left as it is.
    Why: 0104-codex-limits design D5.
    """
    try:
        fd = os.open(folder, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError:
        return
    try:
        with contextlib.suppress(OSError):
            file = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
            try:
                if not stat.S_ISREG(os.fstat(file).st_mode):
                    return
                with os.fdopen(file, "rb", closefd=False) as handle:
                    text = handle.read().decode(errors="replace")
            finally:
                os.close(file)
            if (stamped := _stamped(text, model, tokens)) is not None:
                _place(fd, name, stamped)
    finally:
        os.close(fd)


def _quota(log: Path, before: dict[str, Window]) -> None:
    """Append a Codex log's `mf.quota` line: the shares its windows moved.

    Why: 0104-codex-limits design D5.
    """
    thread = _thread_id(log)
    after = {} if thread is None else _windows(_rollout(thread))
    if not after:
        return
    shares: dict[str, float] = {}
    for name, key in (("primary", "five_hour"), ("secondary", "weekly")):
        if (end := after.get(name)) is None:
            continue
        start = before.get(name)
        used = (
            end.used - start.used if start and start.resets == end.resets else end.used
        )
        shares[key] = round(max(used, 0.0), 1)
    with contextlib.suppress(OSError):
        fd = os.open(log, os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW)
        with os.fdopen(fd, "w") as handle:
            handle.write(json.dumps({"type": "mf.quota", **shares}) + "\n")


def _until(reset: float) -> str:
    """Return a limit's reset as local `%Y-%m-%d %H:%M`, or what `inf` says.

    e.g. 1794153000.0 → `2026-11-08 17:50`; `math.inf` → `a reset it did not name`
    """
    if reset == math.inf:
        return "a reset it did not name"
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(reset))


def mcp_started(executor: str, log: Path) -> str | None:
    """Return why a worker's start fails the probe, or None when no MCP server started.

    Why: D51; 0096-codex-ready design D3.
    """
    names: list[str] = []
    with log.open(errors="replace") as lines:
        for line in lines:
            if '"mcp_servers"' not in line and '"mcp_tool_call"' not in line:
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            item = _item(event, "item.started", "item.completed")
            if item.get("type") == "mcp_tool_call":
                names.append(str(item.get("server")))
                continue
            if not isinstance(event, dict) or event.get("subtype") != "init":
                continue
            servers = event.get("mcp_servers")
            for server in servers if isinstance(servers, list) else [servers]:
                name = server.get("name") if isinstance(server, dict) else server
                names.append(str(name))
    shown = ", ".join(dict.fromkeys(names))
    return f"{executor} started an MCP server: {shown}" if names else None


def _executor_missing(executor: str) -> bool:
    """Return whether neither `MF_SHIP_AGENT` nor the executor's CLI is there."""
    return not os.environ.get("MF_SHIP_AGENT") and shutil.which(executor) is None


def _hold_awake(pid: int) -> str:
    """Hold the machine awake until `pid` exits; return the `start` line's field.

    e.g. `awake: held`. Why: 0069-caffeinate design D1.
    """
    found = shutil.which(CAFFEINATE)
    if found is None:
        return "awake: not held — caffeinate not on PATH"
    subprocess.Popen(
        [found, "-is", "-w", str(pid)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return "awake: held"


def _ps(pid: int, field: str) -> str:
    """Return the `ps` field for `pid`, or "" when it cannot."""
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
    """Kill the stale claim's worker groups, then remove it."""
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


def _pin() -> dict[str, Any]:
    """Return `pin.py`'s namespace: the live marks, the links, the quiet move."""
    return runpy.run_path(str(PIN))


def _mark_live(pin: dict[str, Any], primary: Path) -> Path | None:
    """Write this run's live mark, holding its pid; return it, or None if not written.

    Why: 0068-pinned-release design D2.
    """
    mark = Path.home() / KEPT_ORIGINS / "live" / _digest(primary)
    if pin["holder"](mark) not in (None, os.getpid(), os.getppid()):
        return None
    try:
        mark.parent.parent.mkdir(mode=0o700, exist_ok=True)
        mark.parent.mkdir(mode=0o700, exist_ok=True)
        mark.write_text(f"{os.getpid()}\n")
    except OSError:
        return None
    return mark


def _record_repo(primary: Path) -> None:
    """Add the primary to the home folder's list of repos a run started in, once.

    The review metrics read it; no worker writes there. A home folder that refuses
    it records nothing. Why: 0100-worker-diet design C1, D12.
    """
    path = Path.home() / KEPT_ORIGINS / "repos"
    line = str(primary.resolve())
    try:
        path.parent.mkdir(mode=0o700, exist_ok=True)
        if path.is_file() and line in path.read_text(errors="replace").splitlines():
            return
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW
        with os.fdopen(os.open(path, flags, 0o600), "a") as file:
            file.write(f"{line}\n")
    except OSError:
        return


def _unmark(pin: dict[str, Any], mark: Path | None) -> None:
    """Remove this run's live mark, when it still holds this run's pid."""
    if mark and pin["holder"](mark) == os.getpid():
        mark.unlink()


def _unlinked(executor: str) -> None:
    """Stop with 2 when a skill beside this one is not linked where `executor` looks.

    Every `mf-*` link on both hosts must point into the tree beside this one. A fake
    worker loads no skill. Why: 0068-pinned-release design D5.
    """
    if os.environ.get("MF_SHIP_AGENT"):
        return
    here = Path(__file__).resolve().parents[1].parent
    linked = Path.home() / SKILLS[executor]
    for skill in sorted(here.glob("mf-*")):
        if skill.is_dir() and not (linked / skill.name).exists():
            raise Stop(
                2, f"run: cannot run — {skill.name} is not linked; make install-skills"
            )
    trees = _pin()["trees"]().items()
    if astray := [link for tree, links in trees if tree != here for link in links]:
        raise Stop(
            2,
            "run: cannot run — the mf-* links point into more than one tree:"
            f" {', '.join(astray)}; make install-skills",
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
    if shutil.which(SCANNER) is None:
        raise Stop(
            2, f"run: cannot run — {SCANNER} is not on PATH: brew install {SCANNER}"
        )
    _unlinked(executor)
    if _claim(primary / ".minions" / "runs" / "active") == "live":
        raise Stop(2, "run: cannot run — a run is live: .minions/runs/active exists")
    return primary


@dataclass(frozen=True)
class Checked:
    """What one converge checker did: its exit, the models it ran on, its tokens.

    `limit` is the usage limit or the refusal that ended it, else "".
    Why: 0108-converge-script design D4.
    """

    code: int
    killed: bool
    models: tuple[str, str | None, str | None]
    limit: str
    fallback: bool
    tokens: int | None


class Run:
    """One ship run: the probe, then every open version to the default branch."""

    def __init__(self, primary: Path, executor: str) -> None:
        """Load `integrate.py` and `converge.py`, and open the run log.

        The run log is in the primary's run directory. Why: 0108-converge-script
        design D1.
        """
        integrate = runpy.run_path(str(INTEGRATE))
        self.converge = runpy.run_path(str(CONVERGE))["converge"]
        self.delta = integrate["delta"]
        self.unreleased = integrate["unreleased"]
        self.rules = {
            "CHANGELOG.md": integrate["changelog"],
            DECISIONS: integrate["decisions"],
        }
        self.git_state = _git_state(primary)
        self.pushes = (_kept_origin(primary) or _urls(primary))[1]
        self.primary = primary
        self.repo = _repo(primary)
        self.worktrees = primary / (_agents_values(primary, "Worktrees") or [""])[0]
        self.executor = executor
        self.runs = primary / ".minions" / "runs"
        # Where each worker's group is held; a converge by hand holds none.
        self.claim: Path | None = self.runs / "active"
        self.queue = _queue(primary)
        # The queued cuts the run read; None until `ship` reads the queue.
        self.seen: set[str] | None = None
        self.log = RunLog(self.runs, time.strftime(STAMP))
        self.halts: list[tuple[str, str]] = []
        self.blocked: list[str] = []
        self.unblocked: set[tuple[str, threading.Thread]] = set()
        self.released: list[str] = []
        self.offline = False
        self.plan: dict[tuple[str, str], tuple[str, str | None, str | None]] = {}
        self.planned: set[str] = set()
        self.probed: set[str] = set()
        self.refused: dict[str, str] = {}
        self.limited: dict[str, float] = {}
        self.rescues: dict[str, list[str]] = {}
        self.answered: dict[str, str] = {}
        self.reruns: set[str] = set()
        self.skips: set[str] = set()
        self.decides: set[str] = set()
        self.shadowed: set[str] = set()
        # Each version's skipped converge stations as the plan read them, and the
        # versions whose skipped converge the log says. Why: 0105-converge-switches
        # design D2.
        self.skipped: dict[str, frozenset[str]] = {}
        self.skip_logged: set[str] = set()
        self.decided: list[str] = []
        self.supervisions: dict[str, list[str]] = {}
        # Each settle `_settled` took, by change: the tree integrate must commit.
        self.settled: dict[str, str] = {}
        self.supervisor_decided: list[str] = []
        self.diagnosed: set[str] = set()
        # Each halted version's stage, why and `HEAD` on disk at its halt, and a
        # change from it the re-check read once. Why: 0085-self-healing-ship design D6.
        self.seen_halts: dict[str, tuple[str, str, str] | None] = {}
        self.candidates: dict[str, tuple[str, str, str]] = {}
        self.capped: set[str] = set()
        self.grants_auto: dict[str, bool] = {}
        self.outs: dict[tuple[str, str], Path] = {}
        self.lines = ShipLines([], [])
        self.guard = threading.Lock()
        self.merging = threading.Lock()
        self.probing = threading.Lock()
        # Notified when a version's thread reads its stage past the build, and when
        # it ends. Why: 0099-stacked-builds design D1.
        self.built = threading.Condition()
        # The changes whose `take` has returned.
        self.ended: set[str] = set()

    def halt(self, who: str, reason: str) -> None:
        """Record and log a halt; its version starts only its rescue and supervisor.

        Why: 0085-self-healing-ship design D6;
        0089-supervisor design D1.
        """
        seen = None if who == "run" else self.on_disk(who)
        with self.guard:
            self.halts.append((who, reason))
            if who != "run":
                self.seen_halts[who] = seen
        self.log.event(who, "halt", reason)

    def on_disk(self, change: str) -> tuple[str, str, str] | None:
        """Return a version's stage, why and `HEAD` on disk; None when a read raises."""
        try:
            version = find_version(self.primary, change)
            if version is None or version.tree is None:
                return None
            stage, why = stage_of(self.primary, version, self.skips_of(version.change))
            return stage, why, _git(version.tree, "rev-parse", "HEAD").strip()
        # why: a read of the disk may fail any way; None says the version is unread.
        except Exception:  # noqa: BLE001
            return None

    def block(self, change: str, dependency: str) -> None:
        """Record and log a block; `change` starts no worker."""
        with self.guard:
            self.blocked.append(change)
        self.log.event(change, "blocked", f"by {dependency}")

    def stopped(self, change: str) -> bool:
        """Return whether a halt names `change` or the run."""
        with self.guard:
            return any(who in ("run", change) for who, _ in self.halts)

    def limit(self, executor: str, log: Path) -> None:
        """Record an executor's limit from the log of the worker it stopped, and log it.

        Why: 0104-codex-limits design D2.
        """
        reset = _reset_at(log, time.time())
        with self.guard:
            self.limited[executor] = reset
        self.log.event("run", "limited", f"{executor} limited until {_until(reset)}")

    def limited_until(self, executor: str) -> float | None:
        """Return an executor's reset while it is ahead; a passed one is dropped."""
        with self.guard:
            reset = self.limited.get(executor)
            if reset is not None and reset <= time.time():
                del self.limited[executor]
                return None
            return reset

    def limited_reason(self, executor: str) -> str:
        """Return why a station on a limited executor halts.

        e.g. `probe-codex — codex limited until 2026-11-08 17:50`
        """
        station = "probe" if executor == self.executor else f"probe-{executor}"
        with self.guard:
            reset = self.limited.get(executor, math.inf)
        return f"{station} — {executor} limited until {_until(reset)}"

    def on_stations(self, change: str) -> list[str]:
        """Return the executors of a version's planned stations, its checkers' left out.

        A skipped station names none. Why: 0104-codex-limits design D2.
        """
        left = {*WORKERS[:2], *self.skipped.get(change, frozenset())}
        stations = (station for station in PLANNED if station not in left)
        named = (
            models[0]
            for station in stations
            if (models := self.plan.get((change, station)))
        )
        return list(dict.fromkeys(named))

    def hold_limited(self, changes: list[str], cuts: list[str]) -> set[str]:
        """Halt what has a station on a limited executor; return the cuts it halted.

        Each planned change halts, and each queued cut whose executor is limited
        halts as a cut. Why: 0104-codex-limits design D2.
        """
        for change in changes:
            for executor in self.on_stations(change):
                if self.limited_until(executor) is not None:
                    self.halt(change, self.limited_reason(executor))
                    break
        entries = _cuts(self.primary)
        held: set[str] = set()
        for change in cuts:
            executor = str(entries.get(change, {}).get("executor"))
            if self.limited_until(executor) is not None:
                self.cut_halted(change, self.limited_reason(executor), False)
                held.add(change)
        return held

    def closing(self) -> str:
        """Return the closing line's detail: what halted, is blocked and released."""
        halted = " ".join(dict.fromkeys(who for who, _ in self.halts)) or "none"
        blocked = " ".join(self.blocked) or "none"
        released = " ".join(self.released) or "none"
        return f"halted {halted} · blocked {blocked} · released {released}" + (
            self.decisions() + self.supervisors() + self.needs() + self.unpushed()
        )

    def needs(self) -> str:
        """Return ` · needs <id> <action>, …` for each halted version, or "".

        e.g. "0001-a" diagnosed, "0002-b" timed out → " · needs 0001-a rescue.md,
        0002-b a fix". Why: 0085-self-healing-ship design D7.
        """
        with self.guard:
            halted = dict.fromkeys(who for who, _ in self.halts if who != "run")
        needs = ", ".join(f"{change} {self._needs(change)}" for change in halted)
        return f" · needs {needs}" if needs else ""

    def _needs(self, change: str) -> str:
        """Return the one action a halted version needs, read from the run and disk.

        A queued cut whose halt ends in its answer needs that answer. Why:
        0091-cut-halts design D5.
        """
        with self.guard:
            if change in self.answered:
                return "a re-run"
            if change in self.diagnosed:
                return "rescue.md"
        entry = _cuts(self.primary).get(change, {})
        halt, brief = entry.get("halt"), entry.get("brief")
        if (
            isinstance(halt, str)
            and isinstance(brief, str)
            and halt.endswith(answer := _cut_answer(change, brief))
        ):
            return answer
        stage, why, _ = self.on_disk(change) or ("", "", "")
        if _is_cap(stage, why):
            return "a grant or a re-plan"
        return {"integrating": "the merge settled", "human": "its **HUMAN phase"}.get(
            stage, "a fix"
        )

    def decisions(self) -> str:
        """Return ` · decided <ids>`, each version a rescue decided for, or "".

        Why: 0085-self-healing-ship design D7.
        """
        with self.guard:
            ids = " ".join(dict.fromkeys(self.decided))
        return f" · decided {ids}" if ids else ""

    def supervisors(self) -> str:
        """Return ` · supervised <ids>`, each version a supervisor decided for, or "".

        Why: 0089-supervisor design D10.
        """
        with self.guard:
            ids = " ".join(dict.fromkeys(self.supervisor_decided))
        return f" · supervised {ids}" if ids else ""

    def unpushed(self) -> str:
        """Return ` · unpushed <names>`, as `status` names them, or "" with none.

        Offline, they are the default branch and the tags of its release merges past
        the offline base. Why: 0062-offline-origin design D5.
        """
        try:
            if self.offline and (base := _offline_base(self.primary)):
                names = _local_releases(self.primary, base, _kept_default(self.primary))
            else:
                names = [ref.split("/", 2)[2] for ref, _ in _unpushed(self.primary)]
        except Stop:
            return ""
        return f" · unpushed {' '.join(names)}" if names else ""

    def waited(self, why: str) -> None:
        """Log a push that waits on `origin`."""
        self.log.event("run", "push", f"waiting: {why}")

    def spawn(
        self,
        who: str,
        station: str,
        cwd: Path,
        prompt: str,
        models: tuple[str, str | None, str | None],
        repo: Repo | None = None,
        brief: Path | None = None,
        limits: bool = False,
        deadline: float | None = None,
    ) -> list[str] | None:
        """Run one worker and log it and its denials; `repo` defaults to the run's.

        Why: 0100-worker-diet design D5;
        0104-codex-limits design D2.
        """
        timeout = None if deadline is None else deadline - time.monotonic()
        code, killed, out, denied = self.worker(
            who, station, cwd, prompt, models, repo, brief, timeout
        )
        if killed:
            took = TIMEOUT if timeout is None else max(round(timeout), 0)
            self.halt(who, f"{station} timed out after {took}s; its group was killed")
            return None
        # Why: 0100-worker-diet design D5.
        if missing := lacked(out):
            named = ", ".join(missing)
            self.halt(who, f"{station} asked for a tool its station lacks: {named}")
            return None
        if code != 0:
            if limits and self.limited_until(models[0]) is not None:
                return None
            self.halt(who, f"{station} worker exit {code}{usage_limit(out)}")
            return None
        return denied

    def checker(
        self,
        change: str,
        station: str,
        table: str,
        cwd: Path,
        prompt: str,
        deadline: float,
        effort: str | None = None,
    ) -> Checked:
        """Run one converge checker as `station` on `table`'s models; halt nothing.

        A given `effort` replaces the plan's; past `deadline` it starts nothing.
        Why: 0097-cross-model D9; 0104-codex-limits D3; 0108-converge-script D4, D8.
        """
        checked = table.removeprefix("shadow-")
        shadow = checked != table
        converge = self.plan[change, "converge"]
        models = self.plan[change, f"converge.{checked}"]
        if models[0] == converge[0] and models[1] is None:
            models = (models[0], converge[1], models[2] or converge[2])
        if shadow:
            models = _shadow(converge, models)

        def given(
            planned: tuple[str, str | None, str | None],
        ) -> tuple[str, str | None, str | None]:
            return planned if effort is None else (planned[0], planned[1], effort)

        models = given(models)
        if time.monotonic() >= deadline:
            return Checked(1, False, models, "converge's time is spent", False, None)
        fallback, codex_runs = False, 0
        while True:
            if models[0] == "codex" and (
                codex_runs == 2 or not self.codex_ready(change, deadline)
            ):
                if shadow:
                    stopped = " · stopped by a usage limit"
                    return Checked(1, False, models, stopped, False, None)
                models, fallback = given(_shadow(converge, models)), True
            code, killed, out, _ = self.worker(
                change,
                station,
                cwd,
                prompt,
                models,
                timeout=deadline - time.monotonic(),
            )
            if models[0] != "codex" or not usage_limit(out):
                tokens = tokens_of(out)
                if code == 0:
                    folder = _change_dir(self.primary, change)
                    _stamp(folder, f"{table}.md", models[1], tokens)
                return Checked(code, killed, models, usage_limit(out), fallback, tokens)
            codex_runs += 1

    def lacks(self, who: str, station: str) -> list[str]:
        """Return each tool the station's last log asked for and its station lacks.

        Why: 0100-worker-diet design D5; 0108-converge-script design D5.
        """
        with self.guard:
            out = self.outs.get((who, station))
        return lacked(out) if out is not None else []

    def trees(self) -> list[Path]:
        """Return what a sandboxed command may write: `reach`'s trees.

        Why: 0108-converge-script design D1.
        """
        return reach(self.primary)

    def sandboxed(
        self,
        argv: list[str],
        cwd: Path,
        trees: list[Path],
        out: TextIO | None = None,
        timeout: float | None = None,
    ) -> int:
        """Run `argv` under the OS sandbox, as `sandboxed` does; return its exit.

        Why: 0108-converge-script design D1, D6; `timeout`, 0114-faster-plan-check D5.
        """
        return sandboxed(argv, cwd, trees, out, timeout)

    def codex_ready(self, change: str, deadline: float) -> bool:
        """Return whether Codex may run a checker now, waiting for a near reset.

        Why: 0104-codex-limits design D3.
        """
        resets = [self.limited_until("codex"), _headroom(time.time())]
        if reset := max((at for at in resets if at is not None), default=None):
            ahead = reset - time.time()
            if ahead > LIMIT_WAIT or time.monotonic() + ahead >= deadline:
                return False
            time.sleep(max(ahead, 0))
        if "codex" not in self.probed:
            self.probe_for(change, ["codex"], [], deadline)
        return "codex" in self.probed

    def worker(
        self,
        who: str,
        station: str,
        cwd: Path,
        prompt: str,
        models: tuple[str, str | None, str | None],
        repo: Repo | None = None,
        brief: Path | None = None,
        timeout: float | None = None,
    ) -> tuple[int, bool, Path, list[str]]:
        """Run one worker and log it and its denials; halt nothing.

        A `timeout` replaces `TIMEOUT`; `work` is called as before without one.

        Return its exit, whether `TIMEOUT` killed it, its log and its denials.
        """
        executor, model, effort = models
        held = (repo or self.repo, self.lines)
        given = (executor, prompt, cwd, model, effort, *held)
        if brief is not None:
            command = argv(*given, brief=brief, station=station)
        else:
            command = argv(*given, station=station)
        other = f" · executor {executor}" if executor != self.executor else ""
        shown = f" · effort {effort}" if effort else ""
        self.log.event(
            who, "spawn", f"{station} · model {model or 'default'}{shown}{other}"
        )
        if who == "run":
            out, sink = _free_log(self.runs, (self.log.stamp,), f"run_{station}")
        else:
            parts = ("changes", who, "logs")
            name = f"{self.log.stamp}-{station}"
            out, sink = _free_log(self.primary / ".minions", parts, name)
        with self.guard:
            self.outs[who, station] = out
        if executor == "codex":
            # A Codex log names no model; a reader prices its tokens by this line.
            # Why: 0096-codex-ready design D5.
            line = {
                "type": "mf.spawn",
                "executor": executor,
                "model": model,
                "effort": effort,
            }
            os.write(sink, f"{json.dumps(line)}\n".encode())
        before = _windows(_rollout(None)) if executor == "codex" else {}
        started = time.monotonic()
        try:
            if timeout is not None:
                code, killed = work(command, cwd, sink, self.claim, timeout=timeout)
            else:
                code, killed = work(command, cwd, sink, self.claim)
        finally:
            _temp_gone(command)
        seconds = round(time.monotonic() - started)
        self.log.event(who, "finish", f"{station} · exit {code} · {seconds}s")
        if executor == "codex":
            _quota(out, before)
            if code != 0 and usage_limit(out):
                self.limit("codex", out)
        denied = denials(out)
        for call in denied:
            self.log.event(who, "denied", f"{station} · {call}")
        return code, killed, out, denied

    def judge(
        self,
        who: str,
        stage: str,
        reason: str | None,
        denied: list[str],
        shown: str = "",
    ) -> bool:
        """Log a station's check, `shown` after a pass; a failure halts.

        A failure names the denials before it.
        """
        result = f"pass{shown}" if reason is None else f"fail — {reason}"
        self.log.event(who, "check", f"{stage} · {result}")
        if reason is None:
            return True
        named = f" · denied: {', '.join(denied)}" if denied else ""
        self.halt(who, f"{stage} check fail — {reason}{named}")
        return False

    def rescued(self, change: str, held: str) -> str:
        """Return ` · rescued <sub-tasks>` when a halt on `held` gets no rescue.

        Else "". Why: 0067-rescue design D4.
        """
        with self.guard:
            done = self.rescues.get(change, [])
        if held in done or len(done) >= RESCUES:
            return f" · rescued {' '.join(done)}"
        return ""

    def rescue(self, version: Version, held: str, amends: tuple[str, ...]) -> bool:
        """Run a halted version's rescue on `held`; True when the version goes on.

        Why: 0067-rescue design D2, D3; 0071-ship-fixes design D8;
        0085-self-healing-ship design D1, D5.
        """
        change, tree = version.change, version.tree
        spent = change in self.skips or self.rescued(change, held)
        if tree is None or spent or self.stopped("run"):
            return False
        halt = _converge_halt(self.primary / ".minions", change)
        if held == "converge-halted" and halt and "verify: halt" in halt:
            self.diagnose(change, halt)
            return False
        if held == "converge-halted" and halt and "usage limit" in halt:
            return False
        with self.guard:
            self.rescues.setdefault(change, []).append(held)
        models = self.planned_models(change, "rescue")
        before = _git(tree, "rev-parse", "HEAD").strip()
        diagnosis = _change_dir(self.primary, change) / "rescue.md"
        written = _mtime(diagnosis)
        decide = " with decide=recommended" if change in self.decides else ""
        prompt = PROMPTS["rescue"].format(change=change, decide=decide)
        sha = None
        try:
            spawned = self.spawn(change, "rescue", tree, prompt, models) is not None
            sha, why, decided = (
                _amend(tree, change, before, amends) if spawned else (None, "", False)
            )
            if sha is not None:
                kind = "decided" if decided else "fixed"
                detail = f"{change}: {kind} · {held} · {sha[:7]}"
                self.log.event("run", "rescue", detail)
                with self.guard:
                    self.halts = [halt for halt in self.halts if halt[0] != change]
                    self.diagnosed.discard(change)
                    if decided:
                        self.decided.append(change)
            elif spawned:
                name = f".minions/changes/{change}/rescue.md"
                if not why and _mtime(diagnosis) not in (None, written):
                    self.log.event("run", "rescue", f"{change}: diagnosed · {name}")
                    with self.guard:
                        self.diagnosed.add(change)
                    why = f"rescue diagnosed — {name}"
                self.halt(change, why or "rescue wrote no amend and no diagnosis")
        finally:
            # A taken amend is the rescue's answer: converge picks its run from disk.
            going = held in RESCUED and sha is None and self.hold(version, tree, before)
        return sha is not None or going

    def supervised(self, change: str, held: str) -> str:
        """Return ` · supervised <halts>` when a halt on `held` gets no supervisor.

        Else "". Why: 0089-supervisor design D5.
        """
        with self.guard:
            done = self.supervisions.get(change, [])
        if held in done or len(done) >= SUPERVISES:
            return f" · supervised {' '.join(done)}"
        return ""

    def supervise(self, version: Version, held: str, spent: bool) -> bool:
        """Run a version's supervisor on `held`; True when the version goes on.

        Why: 0089-supervisor design D1, D4,
        D5, D6; 0090-supervisor-merge design D2, D4.
        """
        change, tree = version.change, version.tree
        minions = self.primary / ".minions"
        integrating = held == "integrating"
        converged = held == "converge-halted"
        halt = (_converge_halt(minions, change) or "") if converged else ""
        with self.guard:
            left = (change in self.diagnosed or spent) and change not in self.answered
        if (
            tree is None
            or change not in self.decides
            or not left
            or self.supervised(change, held)
            or self.stopped("run")
            or (
                converged
                and ("usage limit" in halt or _security_held(minions, change, halt))
            )
            or (
                integrating
                and (
                    not stage_of(self.primary, version, self.skips_of(version.change))[
                        1
                    ].startswith("semantic conflict")
                    or _merge_tried(
                        self.primary,
                        change,
                        _git(tree, "rev-parse", "MERGE_HEAD").strip(),
                    )
                )
            )
        ):
            return False
        with self.guard:
            self.supervisions.setdefault(change, []).append(held)
        models = self.planned_models(change, "supervise")
        start = _opened(self.primary, tree, change) if integrating else None
        if start is not None:
            with _queue_lock(self.primary):
                folder = _queue(self.primary) / "supervised"
                folder.mkdir(mode=0o700, exist_ok=True)
                (folder / change).write_text(f"{start.merge}\n")
        before = start.head if start else _git(tree, "rev-parse", "HEAD").strip()
        prompt = _supervise_prompt(self.primary, change)
        sha = None
        try:
            if self.spawn(change, "supervise", tree, prompt, models) is not None:
                if start is not None:
                    sha, why = _settled(self.primary, tree, change, start)
                    nothing = "supervisor settled nothing"
                else:
                    sha, why = _supervised(tree, change, before)
                    nothing = "supervisor wrote no amend"
                if sha is not None:
                    detail = f"{change}: decided · {held} · {sha[:7]}"
                    self.log.event("run", "supervise", detail)
                    with self.guard:
                        self.halts = [halt for halt in self.halts if halt[0] != change]
                        self.diagnosed.discard(change)
                        self.supervisor_decided.append(change)
                        if start is not None:
                            self.settled[change] = sha
                else:
                    self.halt(change, why or nothing)
        finally:
            going = (
                held in RESCUED
                and sha is None
                and self.hold(version, tree, before, "supervise")
            )
        return sha is not None or going

    def diagnose(self, change: str, halt: str) -> None:
        """Write the run's diagnosis of a verify halt, through no link, and halt on it.

        Why: 0071-ship-fixes design D8; 0080-minions-layout design D6.
        """
        name = f".minions/changes/{change}/rescue.md"
        text = (
            f"# {change} — rescue diagnosis\n\nhalt: {halt}\nsub-task: none\n"
            "cause: a Verify: changed since the cut\n"
            f"proposal: commit docs({change}): amend the change directory, then"
            f" conduct.py rejoin {change}, or /mf-ship with no run live\n"
        )
        try:
            _write_in_change(self.primary, change, "rescue.md", text)
        except OSError as error:
            self.halt(change, f"rescue: cannot write {name} — {error.strerror}")
            return
        self.log.event("run", "rescue", f"{change}: diagnosed · {name}")
        with self.guard:
            self.diagnosed.add(change)
        self.halt(change, f"rescue diagnosed — {name}")

    def hold(
        self, version: Version, tree: Path, before: str, who: str = "rescue"
    ) -> bool:
        """Keep a version halted for the run when its rescue answered its halt on disk.

        Why: 0067-rescue design D3; 0085-self-healing-ship design D5;
        0088-paydown-2 design D4; 0089-supervisor design D6.
        """
        change = version.change
        stage, why = stage_of(self.primary, version, self.skips_of(version.change))
        if stage in HALTS:
            return False
        head = _git(tree, "rev-parse", "HEAD").strip()
        if stage == "converge" and self._amended_alone(tree, change, before):
            with self.guard:
                self.halts = [halt for halt in self.halts if halt[0] != change]
                self.diagnosed.discard(change)
            self.log.event("run", who, f"{change}: amended · {head[:7]}")
            return True
        moved = f" · HEAD {head[:7]}" if head != before else ""
        name = "supervisor" if who == "supervise" else "rescue"
        answered = f"{name} answered its halt — {stage}: {why}{moved}"
        with self.guard:
            self.answered[change] = answered
        self.halt(change, answered)
        return False

    def _amended_alone(self, tree: Path, change: str, before: str) -> bool:
        """Return whether the person's amends alone answer the converge halt rescued.

        Why: 0085-self-healing-ship
        design D5; 0089-supervisor design D6.
        """
        runs = self.primary / ".minions"
        halt = _converge_halt(runs, change) or ""
        found = HALT_HEAD.search(halt)
        halted = found and _maybe(
            tree, "rev-parse", "-q", "--verify", f"{found[1]}^{{commit}}"
        )
        if not halted or not _amendable(runs, change, halt):
            return False
        trailers = "--format=%(trailers:key=Rescue)%(trailers:key=Supervisor)"
        rescued = _git(tree, "log", trailers, f"{before}..HEAD")
        return _amended_only(tree, change, halted.strip()) and not rescued.strip()

    def held(self, version: Version, stage: str, tree: Path) -> str | None:
        """Return what a failed check at `stage` is rescued on, or None for no rescue.

        Why: 0067-rescue design D3.
        """
        change = version.change
        if stage == "build":
            unticked = _unticked(tree, change)
            if unticked is not None and "**HUMAN" in unticked[1]:
                return None
            found = _build_halt(self.primary / ".minions", tree, change)
            return found[0] if found else stage
        if stage in ("converge", "integrate"):
            disk = stage_of(self.primary, version, self.skips_of(version.change))[0]
            return disk if disk in RESCUED else None
        return None

    def planned_models(
        self, change: str, station: str
    ) -> tuple[str, str | None, str | None]:
        """Return a station's models as the run planned them; a change halts."""
        models = _models(self.primary / ".minions", change, station, self.executor)
        if models != self.plan.get((change, station)):
            raise Stop(
                1,
                f"conduct: halt — changes/{change}/models.toml changed during the run",
            )
        return models

    def trim_notes(self, change: str, phase: str, before: int) -> None:
        """Keep `build-notes.md`'s first `before` lines and `NOTES` past them.

        It reads and rewrites the file through one descriptor that follows no link,
        and logs a cut. Why: 0102-build-per-phase design D3.
        """
        file = _open_notes(self.primary, change, os.O_RDWR)
        if file is None:
            return
        with os.fdopen(file, "r+b") as notes:
            lines = notes.read().splitlines(keepends=True)
            added = len(lines) - before
            if added > NOTES:
                notes.seek(0)
                notes.truncate()
                notes.write(b"".join(lines[: before + NOTES]))
                said = f"phase {phase}: kept {NOTES} of {added} lines"
                self.log.event(change, "notes", said)

    def _would_grant(self, version: Version, stage: str, halt: str) -> tuple[bool, str]:
        """Return whether `halt` at `stage` is a cap the run grants, and the blockers.

        Why: 0070-cap-policy design D2.
        """
        change = version.change
        if not _is_cap(stage, halt) or self.stopped("run"):
            return False, ""
        runs = self.primary / ".minions"
        blockers = _open_blockers(runs, change)
        if not blockers:
            return False, "no open blocking card read"
        with self.guard:
            first = change not in self.capped
            allowed = self.grants_auto.get(change, True)
        first = first and not _granted_run(runs, change)
        small = all(size in SMALL for _, size in blockers)
        return first and allowed and small, " ".join(card for card, _ in blockers)

    def auto_grant(self, version: Version, stage: str, halt: str) -> tuple[bool, str]:
        """Take one round past a cap `_would_grant` takes; True if it did.

        Why: 0070-cap-policy design D2.
        """
        change = version.change
        granted, ids = self._would_grant(version, stage, halt)
        with self.guard:
            if _is_cap(stage, halt):
                self.capped.add(change)
        if not granted or version.tree is None:
            return False, ids
        with self.guard:
            self.halts = [held for held in self.halts if held[0] != change]
        self.log.event("run", "grant", f"{change}: automatic · {ids}")
        return True, ""

    def skips_of(self, change: str) -> frozenset[str]:
        """Return the converge stations the plan skips for `change`, read once.

        A version the plan holds no skip for gets the empty set, never None: no stage
        read of the run reads the models file. Why: 0108-converge-script design D8.
        """
        with self.guard:
            return self.skipped.get(change, frozenset())

    def workers(self, change: str) -> dict[str, object]:
        """Return converge's workers as the plan holds them, for `converge.py`.

        Why: 0108-converge-script design D1.
        """
        skipped = self.skips_of(change)
        workers: dict[str, object] = {}
        for name in WORKERS:
            models = self.planned_models(change, name)
            workers[name.split(".", 1)[1]] = "skip" if name in skipped else models
        workers["shadow"] = change in self.shadowed
        return workers

    def conducted(
        self, change: str, tree: Path, workers: dict[str, object], grant: bool
    ) -> list[str]:
        """Run `converge.py` in this thread; return no denial: its halt is on disk.

        It is logged as a spawn and a finish, so the run log keeps its pairs.
        Why: 0108-converge-script design D1, D8.
        """
        self.log.event(change, "spawn", "converge · script")
        started = time.monotonic()
        code = self.converge(
            self,
            change,
            tree,
            workers=workers,
            grant=grant,
            deadline=started + TIMEOUT,
        )
        seconds = round(time.monotonic() - started)
        self.log.event(change, "finish", f"converge · exit {code} · {seconds}s")
        return []

    def stage(self, version: Version) -> tuple[str, str]:
        """Return `stage_of`'s read; a note the supervisor settled reads `integrate`.

        Why: 0090-supervisor-merge design D4.
        """
        change = version.change
        skips = self.skips_of(change)
        stage, why = stage_of(self.primary, version, skips)
        # Logged once, at the first stage past a skipped converge.
        # Why: 0105-converge-switches design D2.
        if stage in ("integrate", "release") and "converge" in skips:
            with self.guard:
                first = change not in self.skip_logged
                self.skip_logged.add(change)
            if first:
                self.log.event(change, "converge skipped", "plan")
        with self.guard:
            settled = version.change in self.settled
        if settled and stage == "integrating" and why.startswith("semantic conflict"):
            return "integrate", SETTLED
        return stage, why

    def advance(self, version: Version, stop_at: tuple[str, ...]) -> str | None:
        """Run the version's stations to a stage in `stop_at`, a release or a halt.

        Why: 0070 D2, D3; 0084 D1; 0085 D1; 0089 D1; 0090 D4; 0099 D3; 0102 D1, D2, D3;
        0105 D2; 0108 D8.
        """
        minions, change = self.primary / ".minions", version.change
        decide = change in self.decides
        try:
            auto = close = False
            while not self.stopped(version.change):
                if self.reset_stack(version):
                    return "waiting"
                if auto:
                    stage, why = "converge", "granted automatically"
                elif close:
                    stage, why = "build", "closing steps left"
                else:
                    stage, why = self.stage(version)
                close = False
                if stage not in ("build", "human", "waiting"):
                    self.notify_built()
                if stage == "stacked":
                    return stage
                if stage in STUCK:
                    auto, refused = self.auto_grant(version, stage, why)
                    if auto:
                        continue
                    rescued = stage in RESCUED
                    spent = self.rescued(version.change, stage) if rescued else ""
                    tried = self.supervised(version.change, stage) if rescued else ""
                    self.halt(version.change, f"{stage} — {why}{spent}{tried}")
                    if refused:
                        self.halt(version.change, f"re-plan: {refused}")
                    if rescued:
                        station = "converge" if stage == "converge-halted" else stage
                        amends = _rescue_amends(minions, change, station, decide)
                        if self.rescue(version, stage, amends) or self.supervise(
                            version, stage, bool(spent)
                        ):
                            continue
                    return None
                if stage in stop_at:
                    return stage
                if (stage, why) == ("converge", RERUN):
                    with self.guard:
                        self.reruns.add(version.change)
                if stage == "integrate" and _has_origin(self.primary):
                    default = default_branch(self.primary)
                    base = _offline_base(self.primary) if self.offline else None
                    _foreign_commit(self.primary, base or f"origin/{default}", default)
                cwd = self.primary if stage == "integrate" else version.tree
                if cwd is None:
                    self.halt(version.change, f"{version.change} has no worktree")
                    return None
                # The run's own grant takes no person's grant file.
                grant = auto
                person = not auto and stage == "converge"
                auto = False
                if person and _granted(minions, version.change, take=True):
                    # An answered halt gets one amend round:
                    # the grant goes unspent.
                    grant = why != AMENDED
                    if grant:
                        with self.guard:
                            self.capped.add(version.change)
                        self.log.event(
                            "run",
                            "grant",
                            f"{version.change}: one more round past the cap",
                        )
                with self.guard:
                    staged = self.settled.pop(version.change, None)
                settled = "" if staged is None else " with settled=supervisor"
                workers = self.workers(change) if stage == "converge" else {}
                phase, rating = None, "hard"
                if stage == "build":
                    unticked = _unticked(cwd, change)
                    phase = unticked[0] if unticked else "close"
                    rating = _rating(unticked[1]) if unticked else rating
                numbered = phase not in (None, "close")
                # A link at the notes halts here, before the spawn.
                notes = _note_lines(self.primary, change) if numbered else 0
                prompt = PROMPTS.get(stage, "").format(
                    change=version.change, settled=settled, phase=phase
                )
                models = self.planned_models(version.change, stage)
                # A moderate phase builds on `[build.moderate]` when it names one,
                # its missing model or effort `[build]`'s.
                # Why: 0102-build-per-phase design D5.
                if numbered and rating == "moderate":
                    moderate = self.planned_models(change, MODERATE)
                    if moderate[1] or moderate[2]:
                        models = (
                            moderate[0],
                            moderate[1] or models[1],
                            moderate[2] or models[2],
                        )
                if stage == "release" and _tag_of(self.primary, version.change) is None:
                    head = _git(cwd, "rev-parse", "HEAD").strip()
                    _record_release(self.primary, version.change, head)
                    self.log.event(version.change, "ledger", f"{version.change} {head}")
                if stage in ("converge", "release"):
                    _unstack(self.primary, change)
                if stage == "converge":
                    denied = self.conducted(change, cwd, workers, grant)
                else:
                    denied = self.spawn(version.change, stage, cwd, prompt, models)
                # A phase that failed after its notes still has them cut.
                if numbered:
                    self.trim_notes(change, str(phase), notes)
                if denied is None:
                    return None
                if stage == "release" and not self.push_left(PUSH_RETRIES):
                    return None
                restamped: list[str] = []
                ask = functools.partial(
                    check, self.primary, stage, version, phase=phase, notes=restamped
                )
                try:
                    reason = ask(True, self.offline)
                except Unreachable as down:
                    self.waited(str(down))
                    self.offline = True
                    reason = ask(True, True)
                merged = version.tree if stage == "integrate" else None
                if reason is None and staged is not None and merged is not None:
                    reason = _settle_kept(merged, staged)
                held = None if reason is None else self.held(version, stage, cwd)
                spent = "" if held is None else self.rescued(version.change, held)
                if held is not None:
                    reason = f"{reason}{spent}{self.supervised(version.change, held)}"
                shown = "".join(f" · {note}" for note in restamped)
                if not self.judge(version.change, stage, reason, denied, shown):
                    if held is None:
                        return None
                    amends = _rescue_amends(minions, change, stage, decide)
                    # Only a failed converge check meets a cap here.
                    cap = held if stage == "converge" else stage
                    auto, refused = self.auto_grant(version, cap, reason or "")
                    if refused:
                        self.halt(version.change, f"re-plan: {refused}")
                    if (
                        auto
                        or self.rescue(version, held, amends)
                        or self.supervise(version, held, bool(spent))
                    ):
                        continue
                    return None
                # A phase built last, an amend's after converge began, still closes.
                # Why: 0102-build-per-phase design D1.
                close = numbered and _unticked(cwd, change) is None
                close = close and not _closed(minions, cwd, change)
                if stage == "release":
                    if tag := _tag_of(self.primary, version.change):
                        self.released.append(tag)
                        if self.offline:
                            self.waited(f"{tag} released locally")
                    self.remove_tree(version)
                    return None
        except Stop as stop:
            self.halt(version.change, str(stop))
        # why: a version's thread ends in a halt line, never a traceback.
        except Exception as error:  # noqa: BLE001
            self.halt("run", f"conduct.py failed: {error}")

    def _keeps(self, tree: Path, change: str) -> str | None:
        """Return why `remove_tree` keeps `tree`, or None to remove it.

        Why: 0072-paydown design D2.
        """
        try:
            if changed := _config_changed(self.primary, self.git_state):
                raise changed
            _refuse_config_commands(tree)
        except Stop as stop:
            return str(stop)
        if (self.worktrees / change).is_symlink():
            return "a link at the cut's path"
        if tree != self.worktrees.resolve() / change:
            return "not at the cut's path"
        return None

    def remove_tree(self, version: Version) -> None:
        """Remove a released version's worktree at the cut's path; else log it kept.

        Why: 0057-run-fixes design D3; 0072-paydown design D2.
        """
        tree, change = version.tree, version.change
        if tree is None:
            return
        if why := self._keeps(tree, change):
            self.log.event(change, "kept", f"{tree}: {why}")
            return
        listing = ("ls-files", "--others", "--ignored", "--exclude-standard")
        ignored = _maybe(tree, *listing, "--directory")
        if ignored is None:
            why = "its ignored paths could not be listed"
            self.log.event(change, "kept", f"{tree}: {why}")
            return
        if why := self._keeps(tree, change):
            self.log.event(change, "kept", f"{tree}: {why}")
            return
        done = _run(self.primary, "worktree", "remove", str(tree))
        if done.returncode != 0:
            lines = [line for line in done.stderr.splitlines() if line.strip()]
            why = lines[0] if lines else f"exit {done.returncode}"
            self.log.event(change, "kept", f"{tree}: {why}")
            return
        paths = ", ".join(ignored.splitlines()) or "none"
        self.log.event(change, "removed", f"{tree}: ignored {paths}")

    def notify_built(self) -> None:
        """Wake each version waiting on another's build or end."""
        with self.built:
            self.built.notify_all()

    def live(self, change: str, threads: dict[str, threading.Thread]) -> bool:
        """Return whether `change`'s thread runs: in `threads`, alive, not ended.

        Read under `self.built`. Why: 0099-stacked-builds design D1.
        """
        thread = threads.get(change)
        return thread is not None and thread.is_alive() and change not in self.ended

    def stackable(self, version: Version, unreleased: list[str]) -> str | None:
        """Return the built head a version may stack on, else None.

        Its one unreleased dependency is lower, has no halt, and has a built head
        that holds the version's base. Why: 0099-stacked-builds design D1.
        """
        if len(unreleased) != 1:
            return None
        dependency = unreleased[0]
        if _change_number(dependency) >= version.number or self.stopped(dependency):
            return None
        if (head := _built_head(self.primary, dependency)) is None:
            return None
        default = default_branch(self.primary)
        base = _git(self.primary, "merge-base", default, version.change).strip()
        return head if _ancestor(self.primary, base, head) else None

    def until(
        self,
        version: Version,
        dependency: str,
        threads: dict[str, threading.Thread],
        stack: bool,
    ) -> None:
        """Wait while the dependency's thread lives; with `stack`, until it may stack.

        Why: 0099-stacked-builds design D1.
        """
        logged = False
        with self.built:
            while self.live(dependency, threads):
                if stack and self.stackable(version, [dependency]):
                    return
                if not logged:
                    self.log.event(version.change, "wait", f"after {dependency}")
                    logged = True
                self.built.wait(REJOIN_POLL)

    def ready(self, version: Version, threads: dict[str, threading.Thread]) -> bool:
        """Wait for the version's dependencies, then bring the default branch in.

        Why: 0099-stacked-builds design D1, D3, D6.
        """
        change, default = version.change, default_branch(self.primary)
        after, tree = _dependencies(self.primary, change), version.tree

        def unreleased() -> list[str]:
            return [name for name in after if not _shipped(self.primary, default, name)]

        left = unreleased()
        stacked = tree and _stacked_on(self.primary, change, tree, left)
        if not stacked:
            for dependency in after:
                if (
                    dependency in threads
                    and _change_number(dependency) < version.number
                ):
                    self.until(version, dependency, threads, left == [dependency])
            left = unreleased()
        if self.stopped(change):
            return False
        if not left:
            if stacked:
                self.reset_stack(version)
            if tree and not all(_shipped(tree, "HEAD", name) for name in after):
                self.merge_in(tree, change, default)
            if tree and all(_shipped(tree, "HEAD", name) for name in after):
                _unstack(self.primary, change)
            return True
        if stacked:
            return True
        if tree and (head := self.stackable(version, left)):
            self.stack(tree, change, left[0], head)
            return True
        self.block(change, left[0])
        return False

    def merge_in(
        self, tree: Path, change: str, ref: str, stacked: str | None = None
    ) -> None:
        """Merge `ref` into a branch, once the delta check passes.

        Why: 0086-ship-fixes-3 design D3;
        0099-stacked-builds design D2.
        """
        if changed := _config_changed(self.primary, self.git_state):
            raise changed
        note = _change_dir(self.primary, change) / "integrate.md"
        opened = _merge_open(tree)
        if opened and note.is_file():
            return
        _refuse_config_commands(tree)
        merge = ("merge", "-q", "--no-ff", "--no-commit", ref)
        if not opened and (_maybe(tree, *merge) is None or _merge_open(tree)):
            self.settle(tree, change, ref)
        if stacked is None and (moved := _delta(self.delta, tree)):
            text = _note(tree, change, moved)
            # A link at the change's folder raises: the version halts, nothing written.
            try:
                _write_in_change(self.primary, change, "integrate.md", text)
            except OSError as error:
                name = f".minions/changes/{change}/integrate.md"
                raise Stop(
                    1, f"conduct: halt — cannot write {name} — {error.strerror}"
                ) from None
            return
        message = f"chore(integrate): merge {ref} into {change}"
        if stacked is not None:
            message = f"chore(stack): merge {stacked} at {ref[:7]} into {change}"
        if changed := _config_changed(self.primary, self.git_state):
            raise changed
        _refuse_config_commands(tree)
        _git(tree, "commit", "-q", "-m", message, "-m", f"Change: {change}")

    def stack(self, tree: Path, change: str, dependency: str, head: str) -> None:
        """Mark a version stacked, then merge its dependency's built head in.

        A merge that halts leaves a file naming no ancestor of `HEAD`, which
        `_stacked_on` reads as none. Why: 0099-stacked-builds design D2.
        """
        _write_in_change(self.primary, change, STACKED_ON, f"{head}\n")
        if not _ancestor(tree, head, "HEAD"):
            self.merge_in(tree, change, head, dependency)
        self.log.event(change, "stacked", f"on {dependency} at {head[:7]}")

    def settle(self, tree: Path, change: str, default: str) -> None:
        """Settle a merge by `integrate.py`'s rules; else abort it, stop.

        Why: 0063-rejoin design D6; 0086-ship-fixes-3 design D3;
        0099-stacked-builds design D4.
        """
        at, branch = shlex.quote(str(tree)), shlex.quote(default)
        run = f"git -C {at} merge {branch}, then re-run"
        if not _merge_open(tree):
            raise Stop(
                1, f"conduct: halt — merging {default} into {change} failed: {run}"
            )
        first = _conflicts(tree)
        stopped = ""
        for path, rule in self.rules.items():
            stacked = path == "CHANGELOG.md" and self.unreleased(tree)
            if (path in first or path == DECISIONS or stacked) and not stopped:
                try:
                    rule(tree)
                # why: a rule may fail any way; the merge aborts and the halt names it.
                except Exception as error:  # noqa: BLE001
                    stopped = f" — {error}"
        if not (left := _conflicts(tree)) and not stopped:
            return
        _git(tree, "merge", "--abort")
        if not first:
            # `git merge` would commit a clean merge at once, the rule unapplied.
            raise Stop(
                1,
                f"conduct: halt — merging {default} into {change} is clean, but its"
                f" decisions rule halted{stopped}: git -C {at} merge --no-ff"
                f" --no-commit {branch}, settle the decision ids by hand, commit,"
                " then re-run",
            )
        raise Stop(
            1,
            f"conduct: halt — merging {default} into {change} conflicts in"
            f" {', '.join(left or first)}{stopped}: {run}",
        )

    def catch_up(self, version: Version) -> None:
        """Merge the default branch into a version behind it.

        Why: 0057-run-fixes design D2; 0071-ship-fixes design D4.
        """
        change, default, tree = (
            version.change,
            default_branch(self.primary),
            version.tree,
        )
        if tree is None or _ancestor(self.primary, default, change):
            return
        # A gate merge would give the merge back two merge-bases.
        # Why: 0099-stacked-builds design D3.
        if _stacked_on(self.primary, change, tree, []) is not None:
            return
        base = _git(self.primary, "merge-base", default, change).strip()
        span = f"{base}..{change}"
        held = _git(self.primary, "rev-list", "--count", "--no-merges", span).strip()
        if held == "1":
            self.merge_in(tree, change, default)
            return
        if (unticked := _unticked(tree, change)) is None:
            return
        at = shlex.quote(str(tree))
        if _merge_open(tree):
            marks = _change_dir(self.primary, change)
            noted = any(
                (marks / f"integrate{end}").is_file() for end in (".md", ".red")
            )
            after = _dependencies(self.primary, change)
            if noted or not all(_shipped(tree, "HEAD", name) for name in after):
                return
            raise Stop(
                1,
                f"conduct: halt — a merge is open in {change}'s worktree with no note"
                f" while phase {unticked[0]} is unticked: finish it with"
                f" git -C {at} commit, then re-run",
            )
        diff = ("diff", "--name-only", base, default, "--", *GATE_FILES)
        if _git(self.primary, *diff).split():
            self.merge_in(tree, change, default)

    def landed(self, version: Version, threads: dict[str, threading.Thread]) -> bool:
        """Wait while a stacked version's dependency lives; True to be ready again.

        A reset while it waits makes it ready again; its dependency ended unreleased
        blocks it. Why: 0099-stacked-builds design D3, D6.
        """
        change, default = version.change, default_branch(self.primary)
        after = _dependencies(self.primary, change)
        left = [name for name in after if not _shipped(self.primary, default, name)]
        if not left:
            return True
        dependency = left[0]
        self.log.event(change, "wait", f"stacked on {dependency}")
        with self.built:
            while self.live(dependency, threads):
                if self.reset_stack(version):
                    return True
                self.built.wait(REJOIN_POLL)
        if _shipped(self.primary, default, dependency):
            return True
        self.block(change, dependency)
        return False

    def reset_stack(self, version: Version) -> bool:
        """Reset a stacked version whose dependency re-planned past it; True if so.

        Why: 0099-stacked-builds design D6;
        0102-build-per-phase design D3.
        """
        change, tree = version.change, version.tree
        if tree is None:
            return False
        default = default_branch(self.primary)
        after = _dependencies(self.primary, change)
        unreleased = [n for n in after if not _shipped(self.primary, default, n)]
        if len(unreleased) > 1:
            return False
        if (head := _stacked_on(self.primary, change, tree, unreleased)) is None:
            return False
        if unreleased:
            dependency = unreleased[0]
            if not _replanned(self.primary, dependency, head) and _ancestor(
                self.primary, head, f"refs/heads/{dependency}"
            ):
                return False
        else:
            holders = [
                name
                for name in after
                if _ancestor(self.primary, head, f"refs/heads/{name}")
            ]
            if len(holders) != 1 or not _replanned(self.primary, holders[0], head):
                return False
            dependency = holders[0]
        if (cut := _cut_commit(tree, change)) is None:
            raise Stop(1, f"conduct: halt — {change}: no cut commit to reset to")
        if changed := _config_changed(self.primary, self.git_state):
            raise changed
        _refuse_config_commands(tree)
        # The notes go first: a folder there halts the version before the branch moves.
        try:
            _remove_in(self.primary / ".minions", "changes", change, name=NOTES_FILE)
        except OSError as error:
            name = f".minions/changes/{change}/{NOTES_FILE}"
            raise Stop(
                1, f"conduct: halt — {name} cannot be removed — {error.strerror}"
            ) from None
        left = _git(tree, "rev-parse", "HEAD").strip()
        _git(tree, "reset", "-q", "--hard", cut)
        _unstack(self.primary, change)
        moved = f"{left[:7]} → {cut[:7]}"
        said = f"{dependency} re-planned past {head[:7]}: {moved}"
        self.log.event(change, "reset", said)
        return True

    def take(self, version: Version, threads: dict[str, threading.Thread]) -> None:
        """Take one version to its release, a halt or a block.

        Why: 0099-stacked-builds design D1, D3.
        """
        if self.stopped(version.change):
            return
        with self.built:
            self.ended.discard(version.change)
        try:
            for station in PLANNED:
                _models(
                    self.primary / ".minions", version.change, station, self.executor
                )
            self.catch_up(version)
            reached: str | None = "waiting"
            while reached in ("waiting", "stacked"):
                if reached == "stacked" and not self.landed(version, threads):
                    return
                if not self.ready(version, threads):
                    return
                reached = self.advance(version, ("integrate", "release"))
            if reached is not None and not self.stopped(version.change):
                with self.merging:
                    self.advance(version, ())
        except Stop as stop:
            self.halt(version.change, str(stop))
        # why: a version's thread ends in a halt line, never a traceback.
        except Exception as error:  # noqa: BLE001
            self.halt("run", f"conduct.py failed: {error}")
        finally:
            with self.built:
                self.ended.add(version.change)
                self.built.notify_all()

    def cut(self, change: str, threads: dict[str, threading.Thread]) -> None:
        """Cut a queued brief in its own worktree, check it on disk, then take it.

        Every exit that keeps the queue entry sets its halt, so no close starts it
        again. Why: 0082-cut-station design D4, D6.
        """
        try:
            failed = self.cutting(change)
        except Stop as stop:
            failed = str(stop), False
        # why: a cut's thread ends in a halt line, never a traceback.
        except Exception as error:  # noqa: BLE001
            failed = f"conduct.py failed: {error}", False
        if failed is not None:
            self.cut_halted(change, *failed)
            return
        version = Version(change, _worktrees(self.primary).get(change))
        try:
            if self.admit(version):
                self.take(version, threads)
        except Stop as stop:
            self.halt(change, str(stop))
        # why: a cut's thread ends in a halt line, never a traceback.
        except Exception as error:  # noqa: BLE001
            self.halt(change, f"conduct.py failed: {error}")

    def cutting(self, change: str) -> tuple[str, bool] | None:
        """Run the cutter and its check; return why it halts and if that is logged.

        Why: 0091-cut-halts design D4, D5; 0106-cut-scripts design D7.
        """
        entry = _cuts(self.primary)[change]
        for named in entry["after"]:
            while (queued := _cuts(self.primary).get(named)) is not None:
                if queued.get("halt") is not None or self.stopped(named):
                    return f"after {named} is cut-halted", False
                time.sleep(REJOIN_POLL)
        primary = self.primary
        tree = (self.worktrees / change).resolve()
        if (queued := entry.get("models")) is not None:
            _write_models(primary, change, queued)
        branch = _maybe(primary, "rev-parse", "-q", "--verify", f"refs/heads/{change}")
        _remove_in(primary / ".minions", "changes", change, name="cut.halt")
        if not (branch and _holds(primary, change)):
            # A checkout runs the filters a live worker's config names, outside it.
            if changed := _config_changed(primary, self.git_state):
                raise changed
            _refuse_config_commands(primary)
            if branch:
                if (old := _worktrees(primary).get(change)) is not None:
                    # A worker can point another tree's entry at this branch.
                    if why := self._keeps(old, change):
                        return (
                            f"the branch's worktree {old} is kept: {why}; a person"
                            " reads it, then removes it with git worktree remove or"
                            " moves it back to the cut's path, before conduct.py"
                            f" rejoin {change}"
                        ), False
                    _git(primary, "worktree", "remove", "--force", str(old))
                _git(primary, "branch", "-D", change)
            default = default_branch(primary)
            _git(primary, "worktree", "add", "-b", change, str(tree), default)
            after = f" after={','.join(entry['after'])}" if entry["after"] else ""
            named = entry.get("beside")
            beside = f" beside={','.join(named)}" if named else ""
            prompt = PROMPTS["cut"].format(
                change=change,
                bump=entry["bump"],
                brief=entry["brief"],
                after=after,
                beside=beside,
            )
            models = (entry["executor"], entry["model"], entry["effort"])
            brief = Path(entry["brief"])
            if self.spawn(change, "cut", tree, prompt, models, brief=brief) is None:
                with self.guard:
                    why = next(r for who, r in reversed(self.halts) if who == change)
                return why, True
        why = _check_cut(primary, change, tree)
        answered = why is not None and why == _cutter_halt(primary, change)
        if why is None:
            why = _unapproved(primary, change, entry.get("dependencies", []))
            answered = why is not None and why.startswith(UNAPPROVED)
        result = "pass" if why is None else f"fail — {why}"
        self.log.event(change, "check", f"cut · {result}")
        if why is not None:
            if answered:
                why += f" · needs {change} {_cut_answer(change, entry['brief'])}"
            return why, False
        with _queue_lock(primary):
            folder = _queue(primary) / "briefs"
            folder.mkdir(mode=0o700, exist_ok=True)
            (folder / change).write_text(f"{entry['brief']}\n")
            # The entry goes last, so a reservation that cannot go keeps it to halt.
            _remove_in(primary / ".minions", "cuts", name=change)
            (_queue(primary) / "cuts" / change).unlink()
        sha = _git(primary, "rev-parse", "--short=7", change).strip()
        self.log.event("run", "cut", f"{change}: cut at {sha}")
        return None

    def cut_halted(self, change: str, reason: str, logged: bool) -> None:
        """Set a queued cut's halt to `reason`, and log it unless `spawn` did.

        An entry gone stays gone: one written with no fields would halt every run.
        """
        with _queue_lock(self.primary):
            if (entry := _cuts(self.primary).get(change)) is not None:
                _write_cut(self.primary, change, {**entry, "halt": reason})
        if not logged:
            self.halt(change, f"cut-halted — {reason}")

    def read_plan(self, versions: list[Version]) -> None:
        """Read each station's models, once per version: at the start, or as it joins.

        Why: 0052 D4; 0067 D5; 0070 D4; 0085 D3; 0094 D1; 0097 D3; 0105 D2.
        """
        for version, station in itertools.product(versions, PLANNED):
            self.planned.add(version.change)
            if (models := self.models(version.change, station)) is not None:
                self.plan[version.change, station] = models
        for version in versions:
            try:
                skips = _skips_rescue(self.primary / ".minions", version.change)
                grants = _auto_grants(self.primary / ".minions", version.change)
                decides = _decides(self.primary / ".minions", version.change)
                shadows = _shadows(self.primary / ".minions", version.change)
                skipped = _skips(self.primary / ".minions", version.change)
            except (Stop, ValueError):
                continue
            with self.guard:
                self.grants_auto[version.change] = grants
                if skipped:
                    self.skipped[version.change] = skipped
                if skips:
                    self.skips.add(version.change)
                if decides:
                    self.decides.add(version.change)
                if shadows:
                    self.shadowed.add(version.change)

    def models(
        self, change: str, station: str
    ) -> tuple[str, str | None, str | None] | None:
        """Return one station's models as `_models` reads them; None on a refusal."""
        try:
            return _models(self.primary / ".minions", change, station, self.executor)
        except (Stop, ValueError):
            return None

    def named(self, change: str) -> list[str]:
        """Return each executor a version's plan names, a shadow's among them.

        A skipped station and a skipped checker's shadow name none.
        Why: 0097-cross-model design D3; 0105-converge-switches design D2.
        """
        skipped = self.skipped.get(change, frozenset())
        planned = [
            self.plan.get((change, station))
            for station in PLANNED
            if station not in skipped
        ]
        named = [models[0] for models in planned if models]
        converge = self.plan.get((change, "converge"))
        if change in self.shadowed and converge is not None:
            checkers = (self.plan.get((change, name)) for name in WORKERS)
            named += [
                _shadow(converge, models)[0]
                for name, models in zip(WORKERS, checkers, strict=True)
                if models and name != FIXER and name not in skipped
            ]
        return list(dict.fromkeys(named))

    def executors(self, *cutters: str) -> list[str]:
        """Return the run's executor, then each other one the plan or `cutters` name."""
        changes = dict.fromkeys(change for change, _ in self.plan)
        named = (executor for change in changes for executor in self.named(change))
        return list(dict.fromkeys((self.executor, *named, *cutters)))

    def cut_halts(self, cuts: dict[str, dict[str, Any]]) -> None:
        """Log each halted cut as a halt: it starts no thread and stops no other."""
        for change, entry in cuts.items():
            if entry["halt"] is not None:
                self.halt(change, f"cut-halted — {entry['halt']}")

    def take_requests(self, threads: dict[str, threading.Thread]) -> bool:
        """Start `take` for each requested open version no thread runs; True if any.

        Why: 0063-rejoin design D2; 0071-ship-fixes design D4; 0082-cut-station
        design D4.
        """
        cuts = _cuts(self.primary)
        names = _requests(self.queue)
        if names:
            # A rejoin clears its cut's halt before it writes its request, so a request
            # read after the queue may be newer than the entry read: read it again.
            cuts = _cuts(self.primary)
        if self.stopped("run"):
            return False
        started = False
        for change, entry in cuts.items():
            thread = threads.get(change)
            seen = change in (self.seen or set()) and change not in names
            if entry.get("halt") is not None or seen or (thread and thread.is_alive()):
                continue
            try:
                started = self.take_cut(change, entry, threads) or started
            # why: one cut's failure halts it and leaves the other versions running.
            except Exception as error:  # noqa: BLE001
                self.halt(change, f"conduct.py failed: {error}")
        if not names:
            return started
        try:
            versions = open_versions(self.primary)
        # why: a failed listing is logged and skipped; the poll raises nothing.
        except Exception as error:  # noqa: BLE001
            self.log.event("run", "rejoin", f"skipped — {error}")
            return started
        for version in versions:
            change = version.change
            thread = threads.get(change)
            if not names & {"all", change} or (thread and thread.is_alive()):
                continue
            if change in cuts:
                continue
            started = self.take_back_safely(version, threads) or started
        self._unblock(threads)
        return started

    def take_cut(
        self, change: str, entry: dict[str, Any], threads: dict[str, threading.Thread]
    ) -> bool:
        """Start a queued cut's thread once its executor is probed; True if so."""
        with self.guard:
            self.halts = [held for held in self.halts if held[0] != change]
        if self.seen is not None:
            self.seen.add(change)
        cutter = str(entry.get("executor"))
        self.probe_for(change, [cutter], [cutter])
        if self.stopped(change):
            return False
        self.log.event("run", "cut", f"{change}: taken")
        threads[change] = threading.Thread(target=self.cut, args=(change, threads))
        threads[change].start()
        return True

    def _unblock(self, threads: dict[str, threading.Thread]) -> None:
        """Take back each blocked version one of whose dependencies has a live thread.

        Why: 0071-ship-fixes design D4.
        """
        with self.guard:
            waiting = bool(self.blocked)
        if not waiting or self.stopped("run"):
            return
        try:
            versions = open_versions(self.primary)
        # why: a failed listing is logged and skipped; the poll raises nothing.
        except Exception as error:  # noqa: BLE001
            self.log.event("run", "rejoin", f"skipped — {error}")
            return
        for version in versions:
            change = version.change
            own = threads.get(change)
            with self.guard:
                blocked = change in self.blocked
            if not blocked or (own and own.is_alive()):
                continue
            live = {
                threads[name]
                for name in _dependencies(self.primary, change)
                if name in threads and threads[name].is_alive()
            }
            fresh = {(change, thread) for thread in live} - self.unblocked
            if fresh:
                self.unblocked |= fresh
                self.take_back_safely(version, threads)

    def recheck(self, threads: dict[str, threading.Thread]) -> bool:
        """Take back each halted version answered on disk, with no request; True if any.

        Why: 0085-self-healing-ship design D6.
        """
        with self.guard:
            halted = {who for who, _ in self.halts} - {"run", *self.blocked}
            halted -= set(self.answered)
        cuts: dict[str, dict[str, Any]] = {}
        versions: list[Version] = []
        if halted and not self.stopped("run"):
            try:
                cuts, versions = _cuts(self.primary), open_versions(self.primary)
            # why: a failed listing is logged and skipped; the poll raises nothing.
            except Exception as error:  # noqa: BLE001
                self.log.event("run", "rejoin", f"skipped — {error}")
        live = {change for change, thread in threads.items() if thread.is_alive()}
        versions = [
            version
            for version in versions
            if version.change in halted - live and version.change not in cuts
        ]
        with self.guard:
            kept = {version.change for version in versions}
            self.candidates = {
                change: read
                for change, read in self.candidates.items()
                if change in kept
            }
        started = False
        for version in versions:
            change = version.change
            read = self.on_disk(change)
            with self.guard:
                baseline = self.seen_halts.get(change)
                previous = self.candidates.pop(change, None)
                if baseline is None:
                    self.seen_halts[change] = read
                    continue
                if read is None or read[0] in STUCK or read == baseline:
                    continue
                if previous != read:
                    self.candidates[change] = read
                    continue
                del self.seen_halts[change]
            started = self.take_back_safely(version, threads) or started
        return started

    def take_back_safely(
        self, version: Version, threads: dict[str, threading.Thread]
    ) -> bool:
        """Return `take_back`'s answer; a failure halts the version, raising nothing."""
        try:
            return self.take_back(version, threads)
        except Stop as stop:
            self.halt(version.change, str(stop))
        # why: a take-back failure halts the version and raises nothing.
        except Exception as error:  # noqa: BLE001
            self.halt(version.change, f"conduct.py failed: {error}")
        return False

    def take_back(self, version: Version, threads: dict[str, threading.Thread]) -> bool:
        """Start `take` for a requested version whose stage is no halt; True if so.

        Why: 0063-rejoin design D2, D3; 0067-rescue design D3;
        0071-ship-fixes design D4; 0084-ship-fixes-2 design D1.
        """
        change = version.change
        with self.guard:
            answered = self.answered.get(change)
            reran = change in self.reruns
        if answered is not None:
            self.log.event("run", "rejoin", f"{change}: still halted — {answered}")
            return False
        stage, why = stage_of(self.primary, version, self.skips_of(version.change))
        if (stage, why) == ("converge", RERUN) and reran:
            self.log.event("run", "rejoin", f"{change}: still halted — {RERAN}")
            return False
        if stage in HALTS:
            self.log.event("run", "rejoin", f"{change}: still {stage} — {why}")
            return False
        if change in self.planned and any(
            self.models(change, station) != self.plan.get((change, station))
            for station in PLANNED
        ):
            moved = f"changes/{change}/models.toml changed during the run"
            self.log.event("run", "rejoin", f"{change}: still halted — {moved}")
            return False
        if not self.admit(version):
            return False
        self.log.event("run", "rejoin", f"{change}: {stage}")
        threads[change] = threading.Thread(
            target=self.take, args=(version, threads), name=change
        )
        threads[change].start()
        return True

    def admit(self, version: Version) -> bool:
        """Clear a joining version's halts, read its plan, probe its new executors.

        Why: 0063-rejoin design D2, D3; 0082-cut-station design
        D4; 0085-self-healing-ship design D7.
        """
        change = version.change
        with self.guard:
            self.halts = [held for held in self.halts if held[0] != change]
            self.blocked = [name for name in self.blocked if name != change]
            self.diagnosed.discard(change)
        if change not in self.planned:
            self.read_plan([version])
        self.probe_for(change, self.named(change), self.on_stations(change))
        return not self.stopped(change)

    def probe_for(
        self,
        change: str,
        executors: list[str],
        stations: list[str],
        deadline: float | None = None,
    ) -> None:
        """Probe each executor the run has not, once; a refused one halts `change`.

        A limited executor halts `change` only when among `stations`; a probe ends by
        `deadline`, when given. Why: 0104-codex-limits design D2.
        """
        with self.probing:
            for executor in dict.fromkeys(executors):
                if executor in self.probed or self.stopped(change):
                    continue
                if (refused := self.refused.get(executor)) is not None:
                    self.halt(change, refused)
                    continue
                if self.limited_until(executor) is None:
                    self.probe(executor, change, deadline)
                    if executor in self.probed:
                        continue
                # A probe that failed and halted nothing met a limit `spawn` excused.
                with self.guard:
                    halts = (
                        reason for who, reason in self.halts[::-1] if who == change
                    )
                    refused = next(halts, None)
                    if refused is not None:
                        self.refused[executor] = refused
                if refused is None and executor in stations:
                    self.halt(change, self.limited_reason(executor))

    def probe(
        self, executor: str, who: str = "run", deadline: float | None = None
    ) -> None:
        """Prove a sandboxed worker edits, commits and gates a scratch repo; else halt.

        Why: 0063-rejoin design D3; D51; 0096-codex-ready
        design D9; 0100-worker-diet design D6.
        """
        station = "probe" if executor == self.executor else f"probe-{executor}"
        if _executor_missing(executor):
            self.halt(who, f"{station} — {executor} is not on PATH")
            return
        try:
            _unlinked(executor)
        except Stop as stop:
            self.halt(who, f"{station} — {stop}")
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
                    who, f"{station} — cannot write the probe mark: {error.strerror}"
                )
                return
            _git(scratch, "init", "-q", "-b", "main")
            (scratch / "Makefile").write_text(probe_gate(mark, _native()))
            codex = executor == "codex"
            ignored = ".gated\n.arch\n" + ("tree/\n" if codex else "")
            (scratch / ".gitignore").write_text(ignored)
            _git(scratch, "add", "Makefile", ".gitignore")
            _git(scratch, *SCRATCH_IDENTITY, "commit", "-q", "-m", "init")
            if codex:
                _git(scratch, "worktree", "add", "-q", "--detach", "tree")
            models = (executor, None, None)
            repo = _repo(scratch)
            prompt = f"{PROBE} {TREE_PROBE}" if codex else PROBE
            denied = self.spawn(
                who,
                station,
                scratch,
                prompt,
                models,
                repo,
                limits=True,
                deadline=deadline,
            )
            with self.guard:
                out = self.outs[who, station]
            # Why: 0100-worker-diet design D6.
            turn = first_turn(out)
            shown = "" if turn is None else f" · first turn {turn} tokens"
            tree = check_tree(scratch / "tree") if codex else None
            if (
                denied is not None
                and self.judge(
                    who,
                    station,
                    check_probe(scratch, mark) or tree or mcp_started(executor, out),
                    denied,
                    shown,
                )
                and (not codex or self.probe_checker(executor, who, deadline))
            ):
                self.probed.add(executor)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
            mark.unlink(missing_ok=True)

    def probe_checker(
        self, executor: str, who: str, deadline: float | None = None
    ) -> bool:
        """Prove a checker writes a findings file to the contract; else halt `who`.

        Its verdict is logged, never judged; it ends by `deadline`, when given. Why:
        0096-codex-ready design D9.
        """
        scratch = Path(tempfile.mkdtemp(prefix="mf-ship-checker-")).resolve()
        station = "probe" if executor == self.executor else f"probe-{executor}"
        checker = f"{station}-checker"
        try:
            base, head = checker_fixture(scratch)
            prompt = CHECKER_PROBE.format(base=base, head=head)
            models = (executor, None, None)
            repo = _repo(scratch)
            denied = self.spawn(
                who,
                checker,
                scratch,
                prompt,
                models,
                repo,
                limits=True,
                deadline=deadline,
            )
            with self.guard:
                out = self.outs[who, checker]
            reason = check_checker(scratch, out) or mcp_started(executor, out)
            findings = scratch / ".minions" / "changes" / "0001-probe"
            verdict = None
            if reason is None:
                text = (findings / "conformance.md").read_text(errors="replace")
                verdict = _frontmatter(text, "verdict")
            shown = f" · verdict {verdict}"
            return denied is not None and self.judge(
                who, checker, reason, denied, shown
            )
        finally:
            shutil.rmtree(scratch, ignore_errors=True)

    def push_left(self, tries: tuple[int, ...]) -> bool:
        """Push what a release merged and left; return False when that halted the run.

        Why: 0052-security-hardening design D9; 0053-sandbox-patch design D2;
        0062-offline-origin design D2.
        """
        for delay in tries:
            time.sleep(delay)
            try:
                _refuse_config_commands(self.primary)
                if self.pushes and (
                    changed := _config_changed(self.primary, self.git_state)
                ):
                    raise changed
                unpushed = _unpushed(self.primary, first_read=True)
            except Unreachable as down:
                self.waited(str(down))
                continue
            except Stop as stop:
                self.halt("run", str(stop))
                return False
            self.offline = False
            pushed = self.push(unpushed)
            if pushed is not None:
                return pushed
        self.offline = True
        try:
            if (base := _offline_base(self.primary)) is None:
                raise Stop(
                    1,
                    "conduct: halt — cannot read origin, and no offline base: a person"
                    " runs conduct.py anchor",
                )
            _foreign_commit(self.primary, base, _kept_default(self.primary))
        except Stop as stop:
            self.halt("run", str(stop))
            return False
        return True

    def push(self, unpushed: list[tuple[str, str]]) -> bool | None:
        """Push each `(ref, sha)`; return False when a refusal halted the run."""
        try:
            for ref, sha in unpushed:
                if ref.startswith("refs/heads/"):
                    _scan(self.primary, _offline_base(self.primary), sha)
        except Stop as stop:
            self.halt("run", str(stop))
            return False
        for ref, sha in unpushed:
            kind, name = ref.split("/", 2)[1:]
            for url in self.pushes:
                done = _remote(
                    self.primary,
                    *("push", "--no-verify", "--", url, f"{sha}:{ref}"),
                    timeout=PUSH_TIMEOUT,
                )
                if done.returncode != 0:
                    read = _remote(self.primary, "ls-remote", "--heads", "--", url)
                    if read.returncode != 0:
                        self.waited(_why(read))
                        return None
                    self.halt(
                        "run", f"git push origin {name} failed, exit {done.returncode}"
                    )
                    return False
            self.log.event("run", "push", name)
            if kind == "heads":
                _git(self.primary, "update-ref", f"refs/remotes/origin/{name}", sha)
                _keep_base(self.primary, sha)
                _close_releases(self.primary, sha)
        return True

    def join(self, threads: dict[str, threading.Thread]) -> None:
        """Wait for every thread, taking requests, blocked and answered versions.

        Why: 0063-rejoin design D1;
        0071-ship-fixes design D4; 0085-self-healing-ship design D6, D7.
        """
        while True:
            self.take_requests(threads)
            self._unblock(threads)
            self.recheck(threads)
            deadline = time.monotonic() + REJOIN_POLL
            for thread in [thread for thread in threads.values() if thread.is_alive()]:
                thread.join(timeout=max(0, deadline - time.monotonic()))
            if any(thread.is_alive() for thread in threads.values()):
                continue
            if self.take_requests(threads):
                time.sleep(max(0, deadline - time.monotonic()))
                continue
            with self.guard:
                pending = bool(self.candidates)
            if not pending:
                return
            time.sleep(REJOIN_POLL)

    def unlock(self, name: str) -> None:
        """Remove the lock `name` when stale, logging its age."""
        if (age := _clear_stale_lock(self.primary, name)) is not None:
            self.log.event("run", "unlock", f"{name}, {age}s old")

    def migrate_debt(self) -> str | None:
        """Move an old `backlog.md` to `debt.md`; return why the run must halt.

        Why: 0079-debt-rename design D3;
        0088-paydown-2 design D1.
        """
        old, new = self.primary / OLD_DEBT, self.primary / DEBT
        both = f"{OLD_DEBT} and {DEBT} both stand: a person settles which to keep"
        if old.is_file() and new.exists():
            return both
        self.unlock(OLD_DEBT_LOCK)
        if not old.is_file():
            return None
        if old.is_symlink():
            # A link would make the debt a second name of the file it names.
            return f"{OLD_DEBT} is a link: a person settles what it names"
        old_lock = self.primary / OLD_DEBT_LOCK
        if old_lock.is_dir():
            return f"{OLD_DEBT_LOCK} is held: a person or a hand-run writer holds it"
        if old_lock.exists():
            return f"{OLD_DEBT_LOCK} is a file, not a lock: a person removes it"
        self.unlock(DEBT_LOCK)
        lock = self.primary / DEBT_LOCK
        if lock.is_symlink() or (lock.exists() and not lock.is_dir()):
            return f"{DEBT_LOCK} is a file, not a lock: a person removes it"
        try:
            lock.mkdir()
        except FileExistsError:
            return f"{DEBT_LOCK} is held: a person or a hand-run writer holds it"
        try:
            # A link never replaces: a debt file made since the check stands.
            os.link(old, new)
            old.unlink()
        except FileExistsError:
            return both
        finally:
            lock.rmdir()
        self.log.event("run", "move", f"{OLD_DEBT} → {DEBT}")
        return None

    def migrate_layout(self) -> str | None:
        """Move each change's old-layout files into its folder; return why to halt.

        Why: 0080-minions-layout design
        D4, D6; 0095-converge-roles design D2.
        """
        found = _old_files(self.primary)
        minions = self.primary / ".minions"
        runs = minions / "runs"
        stamps = sorted(runs.iterdir()) if runs.is_dir() else []
        folders = sorted({minions / old.split("/")[0] for old in OLD_LAYOUT})
        olds = [*folders, runs, *(s for s in stamps if OLD_STAMP.fullmatch(s.name))]
        for change, files in sorted(found.items()):
            folder = _change_dir(self.primary, change)
            links = [*olds, minions / "changes", folder, folder / "logs"]
            for link in [*links, *(old for old, _ in files)]:
                if link.is_symlink():
                    named = link.relative_to(self.primary)
                    return f"{named} is a link: a person settles what it names"
            named_by: dict[str, Path] = {}
            for old, new in files:
                if (other := named_by.setdefault(new, old)) != old:
                    return (
                        f"{other.relative_to(self.primary)} and"
                        f" {old.relative_to(self.primary)} both name"
                        f" {(folder / new).relative_to(self.primary)}:"
                        " a person settles which to keep"
                    )
            for old, new in files:
                if os.path.lexists(folder / new):
                    return (
                        f"{old.relative_to(self.primary)} and"
                        f" {(folder / new).relative_to(self.primary)} both stand:"
                        " a person settles which to keep"
                    )
        for change, files in sorted(found.items()):
            for old, new in files:
                where, _, name = new.rpartition("/")
                fd = _folder_fd(minions, "changes", change, *([where] if where else []))
                try:
                    if old.is_dir():
                        os.rename(old, name, dst_dir_fd=fd)
                    else:
                        os.link(old, name, dst_dir_fd=fd)
                        old.unlink()
                finally:
                    os.close(fd)
            self.log.event("run", "move", f"{change}: {len(files)} files")
        return None

    def ship(self) -> int:
        """Run the loop; return 0 when every version shipped, else 1.

        Why: 0082-cut-station design D4.
        """
        self.seen = set()
        _requests(self.queue)
        cuts = _cuts(self.primary)
        self.seen |= set(cuts)
        takeable = {change for change, entry in cuts.items() if entry["halt"] is None}
        versions = [
            version
            for version in open_versions(self.primary)
            if version.change not in cuts
        ]
        worker = " · worker MF_SHIP_AGENT" if os.environ.get("MF_SHIP_AGENT") else ""
        names = " ".join(version.change for version in versions) or "none"
        names += f" · cuts {' '.join(cuts)}" if cuts else ""
        self.log.held = []
        self.push_left(RETRIES)
        held, self.log.held = self.log.held, None
        down = " · origin: unreachable — pushes wait" if self.offline else ""
        # A worker may link the folder elsewhere: a link lists nothing.
        standing = _entries(self.primary / ".minions" / "grants", empty=False)
        grants = f" · grant {' '.join(standing)}" if standing else ""
        release = _pin()["describe"]()
        awake = (
            "" if os.environ.get("MF_SHIP_AGENT") else f" · {_hold_awake(os.getpid())}"
        )
        self.log.event(
            "run",
            "start",
            f"executor {self.executor} · permissions: sandbox{worker}"
            f" · versions {names}{grants}{down}{release}{awake}",
        )
        for event in held:
            self.log.event(*event)
        if self.halts:
            self.log.event("run", "halt", self.closing())
            return 1
        if unkept := _keep_origin(self.primary):
            self.log.event("run", "unkept", unkept)
        if why := self.migrate_debt() or self.migrate_layout():
            self.halt("run", why)
            self.log.event("run", "halt", self.closing())
            return 1
        self.unlock(DEBT_LOCK)
        roots = [SKILLS_DIR, *_pin()["trees"]()]
        if why := _fresh_tmp(self.primary) or _sync_scripts(self.primary, roots):
            self.halt("run", why)
            self.log.event("run", "halt", self.closing())
            return 1
        if not versions and not takeable:
            if cuts:
                self.cut_halts(cuts)
                self.log.event("run", "halt", self.closing())
                return 1
            self.log.event("run", "done", "nothing to ship")
            return 0
        try:
            self.lines = ship_lines(self.primary)
            self.read_plan(versions)
        except Stop as stop:
            self.halt("run", str(stop))
            self.log.event("run", "halt", self.closing())
            return 1
        stages = {
            version.change: stage_of(
                self.primary, version, self.skips_of(version.change)
            )
            for version in versions
        }
        # A cap the run grants is not stuck. Why: 0070-cap-policy design D2, D3.
        takes = {
            version.change: self._would_grant(version, *stages[version.change])
            for version in versions
        }
        granted = any(grants for grants, _ in takes.values())
        # An `amend needed` halt its rescue may amend is not stuck either: its thread
        # starts for the entry rescue, one the models file skips none.
        # Why: 0085-self-healing-ship design D1.
        minions = self.primary / ".minions"
        stuck = all(
            stage in STUCK
            and not (
                stage == "converge-halted"
                and change not in self.skips
                and _rescue_amends(minions, change, "converge", change in self.decides)
            )
            for change, (stage, _) in stages.items()
        )
        if not (granted or takeable) and stuck:
            for change, (stage, why) in stages.items():
                if stage == "waiting":
                    self.block(change, why.removeprefix("after ").split()[0])
                else:
                    self.halt(change, f"{stage} — {why}")
                    if refused := takes[change][1]:
                        self.halt(change, f"re-plan: {refused}")
        else:
            cutters = (str(cuts[change]["executor"]) for change in takeable)
            for executor in self.executors(*cutters):
                self.probe(executor)
                if self.halts:
                    break
        halted = bool(self.halts)
        cut_held: set[str] = set()
        if not halted:
            changes = [version.change for version in versions]
            cut_held = self.hold_limited(changes, sorted(takeable))
        if not (halted or self.blocked):
            threads: dict[str, threading.Thread] = {}
            for version in versions:
                threads[version.change] = threading.Thread(
                    target=self.take, args=(version, threads), name=version.change
                )
            for change in sorted(takeable - cut_held):
                threads[change] = threading.Thread(
                    target=self.cut, args=(change, threads)
                )
            for thread in threads.values():
                thread.start()
            self.cut_halts(cuts)
            self.join(threads)
        else:
            self.cut_halts(cuts)
        if self.offline and not self.stopped("run"):
            self.push_left((0,))
        if self.halts or self.blocked:
            self.log.event("run", "halt", self.closing())
            return 1
        released = " ".join(self.released)
        self.log.event(
            "run",
            "done",
            f"released {released}{self.decisions()}{self.supervisors()}"
            f"{self.unpushed()}",
        )
        return 0


def run(cwd: Path, executor: str, detach: bool) -> int:
    """Start the loop, claimed by `.minions/runs/active`; detached, return at once.

    Why: 0068-pinned-release design D2 and D3; 0082-cut-station design D2.
    """
    pin = _pin()
    mark = _mark_live(pin, primary_of(cwd))
    try:
        primary = preconditions(cwd, executor)
        if not (started := _ps(os.getpid(), "lstart=")):
            raise Stop(2, "run: cannot run — ps cannot read this run's start time")
        runs = primary / ".minions" / "runs"
        runs.mkdir(parents=True, exist_ok=True)
        active = runs / "active"
        if _claim(active) == "stale":
            _clear(active)
    except Stop:
        _unmark(pin, mark)
        raise
    if detach:
        print(f"run: started · pid {_detach(primary, executor).pid}")
        return 0
    try:
        active.mkdir()
    except FileExistsError:
        _unmark(pin, mark)
        raise Stop(
            2, "run: cannot run — a run is live: .minions/runs/active exists"
        ) from None
    seen: set[str] | None = None
    try:
        (active / "start").write_text(started)
        (active / "pid").write_text(str(os.getpid()))
        _record_repo(primary)
        conductor = Run(primary, executor)
        try:
            code = conductor.ship()
        # why: a conductor failure is logged as the run's halt, never a traceback.
        except Exception as error:  # noqa: BLE001
            conductor.log.event("run", "halt", f"conduct.py failed: {error}")
            code = 1
        seen = conductor.seen
        ended = "done" if code == 0 else "halt"
        print(f"run: {ended} · .minions/runs/{conductor.log.stamp}.md")
        return code
    finally:
        try:
            if moved := pin["move"](mark):
                print(moved)
                if moved.startswith("pin: moved to") and (
                    why := _sync_scripts(primary, pin["trees"]())
                ):
                    print(f"run: {why}")
        finally:
            _unmark(pin, mark)
            _close(primary, active, executor, seen)


def _detach(primary: Path, executor: str) -> subprocess.Popen[bytes]:
    """Start a run in a new session, its output in `.minions/runs/detached.log`."""
    with (primary / ".minions" / "runs" / "detached.log").open("a") as sink:
        return subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "run"]
            + ["--executor", executor],
            cwd=primary,
            stdin=subprocess.DEVNULL,
            stdout=sink,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )


def _start_run(primary: Path, executor: str) -> int:
    """Detach a run and wait until it holds its claim or has ended; return its pid.

    Why: 0082-cut-station
    design D2.
    """
    runs = primary / ".minions" / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    log = runs / "detached.log"
    size = log.stat().st_size if log.is_file() else 0
    child = _detach(primary, executor)
    deadline = time.monotonic() + CLAIM_SECONDS
    while _claim(runs / "active") != "live":
        if child.poll() is not None or time.monotonic() >= deadline:
            with log.open("rb") as file:
                file.seek(size)
                lines = file.read().decode(errors="replace").splitlines()
            if any(line.startswith(("run: done", "run: halt")) for line in lines):
                return child.pid
            last = lines[-1] if lines else "no line in .minions/runs/detached.log"
            raise Stop(2, f"the run did not start — {last}")
        time.sleep(0.1)
    return child.pid


def _close(primary: Path, active: Path, executor: str, seen: set[str] | None) -> None:
    """Remove the claim under the queue lock, then start the next run when one waits.

    Why: 0082-cut-station design D2.
    """
    try:
        with _queue_lock(primary):
            shutil.rmtree(active)
            if seen is None:
                return
            unread = any(
                entry["halt"] is None and change not in seen
                for change, entry in _cuts(primary).items()
            )
            if not (unread or _requested(_queue(primary))):
                return
            pid = _start_run(primary, executor)
    except Stop as stop:
        if active.exists():
            shutil.rmtree(active)
        print(stop)
        return
    print(f"run: next started · pid {pid}")


def stop_run(cwd: Path) -> str:
    """End the live run: the conductor first, so it spawns nothing more.

    Why:
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


def _queue(primary: Path) -> Path:
    """Return the repo's queue in the home folder, where no worker writes.

    e.g. `~/.mf-ship-origin/<digest>.queue`. Why: 0082-cut-station design D2.
    """
    return Path.home() / KEPT_ORIGINS / f"{_digest(primary)}.queue"


def _brief_of(primary: Path, change: str) -> str | None:
    """Return the brief path a passed cut recorded for `change`, while it names a file.

    The record stands in the home queue, where no worker writes; a version cut by
    hand has none. Why: 0090-supervisor-merge design D1.
    """
    try:
        named = (_queue(primary) / "briefs" / change).read_text().strip()
    except (OSError, UnicodeDecodeError):
        return None
    return named if named and Path(named).is_file() else None


def _merge_tried(primary: Path, change: str, merge: str) -> bool:
    """Return whether a supervisor was spawned on `change`'s open merge `merge`.

    The record stands in the home queue, where no worker writes, so the try holds
    across runs. Why: 0090-supervisor-merge design D2.
    """
    try:
        return (_queue(primary) / "supervised" / change).read_text().strip() == merge
    except (OSError, UnicodeDecodeError):
        return False


def _supervise_prompt(primary: Path, change: str) -> str:
    """Return the supervisor's prompt, naming the brief `_brief_of` reads.

    e.g. "… with decide=recommended and brief=/b/brief.md."
    """
    named = _brief_of(primary, change)
    brief = f" and brief={named}" if named else ""
    return PROMPTS["supervise"].format(change=change, brief=brief)


@contextlib.contextmanager
def _queue_lock(primary: Path) -> Iterator[None]:
    """Hold the queue's lock, blocking; the kernel drops it when its process ends.

    Why: 0082-cut-station design D2.
    """
    queue = _queue(primary)
    try:
        for folder in (queue.parent, queue):
            folder.mkdir(mode=0o700, exist_ok=True)
        fd = os.open(queue / "lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    except OSError as error:
        raise Stop(
            2,
            f"conduct: cannot run — the home folder refuses the queue:"
            f" {error.strerror}; run it outside a sandbox",
        ) from None
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def _cuts(primary: Path) -> dict[str, dict[str, Any]]:
    """Return each queued cut's entry by its id, in id order.

    An entry that is no JSON object, or lacks one of `CUT_KEYS`, holds only its halt.
    e.g. {"0003-a": {"bump": "minor", …, "halt": None}}
    """
    folder = _queue(primary) / "cuts"
    found: dict[str, dict[str, Any]] = {}
    for name in _entries(folder, empty=False):
        if not CHANGE_ID.fullmatch(name):
            continue
        try:
            entry = json.loads((folder / name).read_text())
        except (OSError, ValueError):
            entry = None
        if not isinstance(entry, dict) or not entry.keys() >= CUT_KEYS:
            entry = {"halt": "the queue entry is unreadable"}
        found[name] = entry
    return found


@functools.cache
def _markdown() -> "MarkdownIt":
    """Return the CommonMark parser, GFM tables on, imported on its first call.

    The import waits: `pin.py` and the escape drill load this script with no package
    installed. Why: 0103-fewer-rounds design D6.
    """
    from markdown_it import MarkdownIt  # noqa: PLC0415

    return MarkdownIt("commonmark").enable("table")


def _read(text: str) -> tuple[list[str], list["Token"]]:
    r"""Return a document's source lines and its tokens.

    Lines split at `\r\n`, `\r` or `\n`, as CommonMark's do, so a token's `map` indexes
    them. Why: 0103-fewer-rounds design D6.
    """
    return re.split(r"\r\n|\r|\n", text), _markdown().parse(text)


def _span(token: "Token") -> range:
    """Return the source lines a block token spans, none for a token with no map."""
    start, end = token.map or (0, 0)
    return range(start, end)


def _fold(line: str) -> str:
    """Return the letters and digits a line renders as, tags dropped, case-folded.

    e.g. "<h2>D&#101;pendencies</h2>" → "dependencies"
    """
    text = html.unescape(re.sub(r"<[^>]*>", "", line))
    return "".join(char for char in text if char.isalnum()).casefold()


def _headed(text: str, heading: str) -> bool:
    """Return whether `heading` stands at most once, as an ATX `h2` written so.

    A look-alike or an open fence fails it. Why: 0103-fewer-rounds design D6.
    """
    lines, tokens = _read(text)
    code: set[int] = set()
    checked: set[int] = set()
    exact: set[int] = set()
    for token in tokens:
        span = _span(token)
        if token.type in ("fence", "code_block"):
            code.update(span)
            # A closed fence spans its content and its two marker lines.
            if token.type == "fence" and len(span) != token.content.count("\n") + 2:
                return False
        elif token.type == "html_block":
            checked.update(span)
        elif token.type == "heading_open":
            checked.add(span.start)
            if (
                token.tag == "h2"
                and token.markup == "##"
                and lines[span.start] == heading
            ):
                exact.add(span.start)
    checked.update(n for n, line in enumerate(lines) if INLINE_HEADING.search(line))
    other = [n for n in checked - code - exact if _fold(lines[n]) == _fold(heading)]
    return len(exact) <= 1 and not other


def _cells(line: str) -> int:
    r"""Return how many cells a table row's source line holds, GFM's way.

    Why: 0103-fewer-rounds design D6.
    """
    parts = re.split(r"(?<!\\)\|", line.strip())
    return len(parts) - (parts[0] == "") - (len(parts) > 1 and parts[-1] == "")


def _boundary(token: "Token") -> bool:
    """Return whether a token ends a section: an `h1` or `h2`, or HTML opening one."""
    if token.type == "heading_open":
        return token.tag in ("h1", "h2")
    return token.type == "html_block" and bool(
        BLOCK_HEADING.match(token.content.lstrip())
    )


def _rows(text: str, heading: str) -> list[list[str]] | None:
    """Return `heading`'s table, header first; [] for no section or one `None.`.

    Anything else, an empty section too, is None. Why: 0103-fewer-rounds design D6.
    """
    lines, tokens = _read(text)
    start = next(
        (
            i
            for i, token in enumerate(tokens)
            if token.type == "heading_open"
            and token.level == 0
            and token.tag == "h2"
            and token.markup == "##"
            and lines[_span(token).start] == heading
        ),
        None,
    )
    if start is None:
        return []
    blocks: list[int] = []
    for i, token in enumerate(tokens[start + 3 :], start + 3):
        if token.level or token.nesting < 0:
            continue
        if _boundary(token):
            break
        blocks.append(i)
    if len(blocks) != 1:
        return None
    first = tokens[blocks[0]]
    if first.type == "paragraph_open":
        return [] if tokens[blocks[0] + 1].content == "None." else None
    if first.type != "table_open":
        return None
    rows: list[list[str]] = []
    starts: list[int] = []
    for token in tokens[blocks[0] :]:
        if token.type == "table_close":
            break
        if token.type == "tr_open":
            rows.append([])
            starts.append(_span(token).start)
        elif token.type == "inline":
            rows[-1].append(token.content.strip(" `"))
    wide = any(
        len(row) != len(rows[0]) or _cells(lines[at]) > len(rows[0])
        for row, at in zip(rows, starts, strict=True)
    )
    return None if wide else rows


def _approved(text: str, slug: str) -> list[list[str]] | None:
    """Return `[package, constraint]` per `## Dependencies` row whose item is `slug`.

    None for a section out of shape. Why: 0091-cut-halts design D3.
    """
    rows = _rows(text, DEPENDENCIES)
    if rows is None or rows[:1] not in ([], [APPROVED]):
        return None
    return [
        [package, constraint]
        for item, package, constraint, _ in rows[1:]
        if item == slug
    ]


def _approval(path: Path, slug: str, command: str) -> list[list[str]]:
    """Return the packages the brief at `path` approves for `slug`, or stop with 2."""
    try:
        text = path.read_text()
    except (OSError, UnicodeDecodeError):
        raise Stop(
            2, f"{command}: cannot run — the brief {path} cannot be read"
        ) from None
    if (approved := _approved(text, slug)) is None:
        raise Stop(
            2,
            f"{command}: cannot run — the brief's ## Dependencies is neither None."
            " nor a table of item · package · constraint · why",
        )
    return approved


def _prefetch(primary: Path, rows: list[list[str]]) -> None:
    """Fetch each approved row's wheel into the primary's uv cache, or stop with 2.

    Why: 0110-gate-hardening design D4.
    """
    for package, constraint in rows:
        if not (PACKAGE.fullmatch(package) and SPECIFIER.fullmatch(constraint)):
            raise Stop(
                2,
                f"cut: cannot run — the brief's row {package} {constraint} is not a"
                " package name and a plain version specifier",
            )
    scratch = primary / ".minions" / "tmp"
    env = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith(("UV_", "PIP_"))
    }
    env["UV_CACHE_DIR"] = str(primary / ".minions" / "uv-cache")
    for package, constraint in rows:
        try:
            os.close(_folder_fd(primary, ".minions", "tmp"))
        except OSError as error:
            raise Stop(
                2, f"cut: cannot run — scratch folder {scratch}: {error}"
            ) from error
        target = tempfile.mkdtemp(dir=scratch)
        command = ["uv", "pip", "install", "--no-config", "--no-build"]
        command += ["--default-index", PYPI_INDEX, "--target", target]
        try:
            done = subprocess.run(
                [*command, f"{package}{constraint}"],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                timeout=PREFETCH_SECONDS,
            )
        except (subprocess.TimeoutExpired, OSError) as error:
            why = error.strerror if isinstance(error, OSError) else "timed out"
            raise Stop(
                2, f"cut: cannot run — fetching {package} failed: {why}"
            ) from None
        finally:
            shutil.rmtree(target, ignore_errors=True)
        if done.returncode != 0:
            raise Stop(
                2,
                f"cut: cannot run — fetching {package} failed: exit {done.returncode}",
            )


def _rows_hash(rows: list[list[str]]) -> str:
    """Return the sha256 of `rows` as JSON: the hash a rejoin's `--yes` names.

    Why: 0091-cut-halts design D3.
    """
    return hashlib.sha256(json.dumps(rows).encode()).hexdigest()


def _models_text(brief: Path, slug: str) -> str:
    """Return the models file `brief_check.py --models` prints for `slug`.

    A failed run, a timeout or text `tomllib` refuses stops with 2. Why: 0106 design D7.
    """
    command = [*UV_RUN, str(BRIEF_CHECK), "--models", str(brief), slug]
    try:
        done = subprocess.run(
            command,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        raise Stop(2, "cut: cannot run — brief_check.py timed out") from None
    except OSError as error:
        raise Stop(2, f"cut: cannot run — {error.strerror}") from None
    if done.returncode != 0:
        lines = (done.stdout.strip() or done.stderr).splitlines()
        first = next(
            (line for line in lines if line.strip()), f"exit {done.returncode}"
        )
        raise Stop(2, f"cut: cannot run — the brief's models for {slug}: {first}")
    try:
        tomllib.loads(done.stdout)
    except tomllib.TOMLDecodeError as error:
        raise Stop(
            2, f"cut: cannot run — the brief's models for {slug} are not TOML: {error}"
        ) from None
    return done.stdout


def _write_models(primary: Path, change: str, text: str) -> None:
    """Write the change's `models.toml` from `text`; a refused write stops with 2.

    Why: 0106-cut-scripts design D7.
    """
    try:
        # A fresh file: truncating the old one would write through a hard link.
        _remove_in(primary / ".minions", "changes", change, name="models.toml")
        _write_in_change(primary, change, "models.toml", text)
    except OSError as error:
        raise Stop(
            2,
            f"cut: cannot run — changes/{change}/models.toml cannot be written:"
            f" {error.strerror}",
        ) from None


def _write_cut(primary: Path, change: str, entry: dict[str, Any]) -> None:
    """Write a queued cut's entry whole: to a temporary name, then moved in."""
    folder = _queue(primary) / "cuts"
    folder.mkdir(mode=0o700, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=folder, prefix=".")
    with os.fdopen(fd, "w") as file:
        json.dump(entry, file)
    os.replace(temp, folder / change)


def _next_id(primary: Path) -> int:
    """Return one above every change number the repo, its branches or the queue hold.

    Why: 0082-cut-station design D1.
    """
    default = default_branch(primary)
    branches = _git(primary, "branch", "--list", "[0-9]*", "--format=%(refname:short)")
    names = [*branches.split(), *_entries(primary / ".minions" / "cuts", empty=False)]
    names += _cuts(primary)
    for rev in [default, *branches.split()]:
        for folder in ("openspec/changes", "openspec/changes/archive"):
            listed = _maybe(primary, "ls-tree", "--name-only", f"{rev}:{folder}")
            names += (listed or "").splitlines()
    numbers = [int(found[1]) for name in names if (found := CHANGE_ID.fullmatch(name))]
    return max(numbers, default=0) + 1


def cut(
    cwd: Path,
    slug: str,
    bump: str,
    brief: str,
    links: list[str],
    executor: str,
    model: str | None,
    effort: str | None,
) -> str:
    """Queue a settled brief under the next free number; return the line.

    Why: 0082-cut-station design D1; 0091-cut-halts
    design D3; 0098-beside design D3; 0106-cut-scripts design D7.
    """
    if not SLUG.fullmatch(slug):
        raise Stop(2, f"cut: cannot run — not a slug: {slug}")
    if not brief.startswith("brief="):
        raise Stop(2, "cut: cannot run — expected brief=<path>")
    linked: dict[str, list[str]] = {}
    for link in links:
        kind, equals, named = link.partition("=")
        if not equals or kind not in ("after", "beside") or kind in linked:
            raise Stop(
                2, f"cut: cannot run — expected after=<ids> or beside=<ids>: {link}"
            )
        linked[kind] = named.split(",")
    for named in linked.get("beside", []):
        if not CHANGE_ID.fullmatch(named):
            raise Stop(2, f"cut: cannot run — beside={named} is not a change id")
    path = Path(brief.removeprefix("brief="))
    if not path.is_absolute() or not path.is_file():
        raise Stop(2, f"cut: cannot run — {brief} is not an absolute path to a file")
    moved = "move the brief into a folder of its own"
    if why := _brief_refused(path.resolve(), executor, moved):
        raise Stop(2, f"cut: cannot run — {why}")
    approved = _approval(path.resolve(), slug, "cut")
    models = _models_text(path.resolve(), slug)
    ids = linked.get("after", [])
    primary = primary_of(cwd)
    _prefetch(primary, approved)
    with _queue_lock(primary):
        known = {version.change for version in open_versions(primary)}
        known |= set(_cuts(primary))
        for named in ids:
            if named not in known:
                raise Stop(
                    2,
                    f"cut: cannot run — after={named} names no open version or"
                    " queued cut",
                )
        live = _claim(primary / ".minions" / "runs" / "active") == "live"
        if not live:
            preconditions(cwd, executor)
        change = f"{_next_id(primary):04d}-{slug}"
        _write_models(primary, change, models)
        fd = _folder_fd(primary / ".minions", "cuts")
        try:
            flags = os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW
            os.close(os.open(change, flags, 0o644, dir_fd=fd))
        finally:
            os.close(fd)
        entry = {
            "bump": bump,
            "brief": str(path.resolve()),
            "after": ids,
            "executor": executor,
            "model": model,
            "effort": effort,
            "halt": None,
            "dependencies": approved,
            "models": models,
        }
        if "beside" in linked:
            entry["beside"] = linked["beside"]
        _write_cut(primary, change, entry)
        if live:
            return f"cut: queued {change} · the live run takes it"
        try:
            pid = _start_run(primary, executor)
        except Stop as stop:
            raise Stop(2, f"cut: queued {change} · {stop}") from None
    return f"cut: queued {change} · run started · pid {pid}"


def _requests(queue: Path) -> set[str]:
    """Delete the rejoin requests in `queue`; return their names.

    Why: 0063-rejoin design D2.
    """
    return set(_entries(queue / "rejoin", empty=True))


def _requested(queue: Path) -> bool:
    """Return whether `queue`'s rejoin folder holds a request: a regular file.

    Read through the folder's descriptor, as `_requests` deletes, following no link.
    """
    try:
        fd = os.open(queue / "rejoin", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError:
        return False
    try:
        return any(
            stat.S_ISREG(os.lstat(name, dir_fd=fd).st_mode) for name in os.listdir(fd)
        )
    except OSError:
        return False
    finally:
        os.close(fd)


def rejoin(cwd: Path, change: str | None, yes: str | None = None) -> str:
    """Ask the live run to take back `change`, or every version, and return the line.

    Why: 0063-rejoin design D1; 0082-cut-station design D3, D6;
    0091-cut-halts design D3.
    """
    primary = primary_of(cwd)
    runs = primary / ".minions" / "runs"
    with _queue_lock(primary):
        live = _claim(runs / "active") == "live"
        if change is not None and (entry := _cuts(primary).get(change)) is not None:
            if not entry.keys() >= CUT_KEYS:
                name = _queue(primary) / "cuts" / change
                raise Stop(
                    2,
                    f"rejoin: cannot run — the queue entry {name} is unreadable: remove"
                    " it, then queue the cut again",
                )
            slug = change.split("-", 1)[1]
            queued = entry.get("dependencies", [])
            approved = _approval(Path(entry["brief"]), slug, "rejoin")
            if new := [row for row in approved if row not in queued]:
                if yes != (hashed := _rows_hash(new)):
                    rows = ", ".join(" ".join(row) for row in new)
                    raise Stop(
                        1,
                        "rejoin: halted — the brief adds rows the queue does not hold:"
                        f" {rows}; the person's yes: conduct.py rejoin {change}"
                        f" --yes {hashed}",
                    )
                entry = {**entry, "dependencies": queued + new}
            _write_cut(primary, change, {**entry, "halt": None})
            if live:
                _request(primary, change)
                return f"rejoin: requested {change}"
            preconditions(cwd, entry["executor"])
            pid = _start_run(primary, entry["executor"])
            return f"rejoin: requested {change} · run started · pid {pid}"
        if yes is not None:
            raise Stop(2, "rejoin: cannot run — --yes answers a queued cut's packages")
        if not live:
            raise Stop(2, "rejoin: no run is live — run /mf-ship")
        if change is not None and change not in (
            version.change for version in open_versions(primary)
        ):
            raise Stop(2, f"rejoin: cannot run — no open version holds {change}")
        _request(primary, change or "all")
    return f"rejoin: requested {change or 'every halted version'}"


def _request(primary: Path, name: str) -> None:
    """Write the rejoin request `name` for the live run, in the home folder's queue."""
    folder = _queue(primary) / "rejoin"
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    (folder / name).touch()


def _rescuing(runs: Path, change: str) -> bool:
    """Return whether the newest run log's last rescue or supervisor event is a spawn.

    e.g. `… · 0001-todo · spawn — rescue · model default`, no `finish — rescue` after
    Why: 0089-supervisor design D6.
    """
    log = last_log(runs)
    lines = log.read_text(errors="replace").splitlines() if log else []
    events = [
        found[2]
        for line in lines
        if (found := EVENT.match(line))
        and found[1] == change
        and found[2] in ("spawn", "finish")
        and line[found.end() :].startswith(("rescue · ", "supervise · "))
    ]
    return events[-1:] == ["spawn"]


def grant(cwd: Path, change: str, executor: str) -> int:
    """Record one more round for a version halted at the cap, then start a run.

    Why: 0063-rejoin design D5; 0067-rescue design D3; 0082-cut-station design D3;
    0089-supervisor design D6.
    """
    primary = primary_of(cwd)
    if (version := find_version(primary, change)) is None:
        raise Stop(2, f"grant: cannot run — no version branch holds {change}")
    if old := _old_layout(primary, change):
        raise Stop(2, f"grant: cannot run — {old} is the old layout: /mf-ship moves it")
    stage, why = stage_of(primary, version)
    if (stage, why) == ("converge", "granted"):
        raise Stop(2, f"grant: cannot run — {change} has a grant waiting: run /mf-ship")
    if stage != "converge-halted" or "cap reached" not in why:
        raise Stop(
            2,
            f"grant: cannot run — {change} is at {stage}: run /mf-ship; grant once"
            " converge caps",
        )
    runs = primary / ".minions" / "runs"
    with _queue_lock(primary):
        live = _claim(runs / "active") == "live"
        if live and _rescuing(runs, change):
            raise Stop(
                2,
                f"grant: cannot run — {change} is at {stage}"
                " with its rescue or supervisor running: grant once it ends",
            )
        if not live:
            preconditions(cwd, executor)
        grants = primary / ".minions" / "grants"
        grants.mkdir(parents=True, exist_ok=True)
        (grants / change).touch()
        if not live:
            pid = _start_run(primary, executor)
            print(f"grant: recorded · run started · pid {pid}")
            return 0
        _request(primary, change)
    print(f"grant: recorded — the live run takes {change} back")
    return 0


def approve_gate(cwd: Path, change: str, hashed: str) -> str:
    """Record the hash a gate check's halt named, as a person's yes to that diff.

    Why: 0060-gate-planning design D4.
    """
    primary = primary_of(cwd)
    version = find_version(primary, change)
    if version is None or version.tree is None:
        raise Stop(2, f"approve-gate: cannot run — no version worktree holds {change}")
    if not SHA256.fullmatch(hashed):
        raise Stop(1, f"approve-gate: refused — not the hash a halt names: {hashed}")
    folder = Path.home() / KEPT_ORIGINS / f"{_digest(primary)}.gate"
    try:
        folder.mkdir(mode=0o700, parents=True, exist_ok=True)
        entry = folder / change
        entry.unlink(missing_ok=True)
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        with os.fdopen(os.open(entry, flags, 0o600), "w") as file:
            file.write(f"{hashed}\n")
    except OSError as error:
        raise Stop(
            2,
            f"approve-gate: cannot write the approval — {error.strerror}; "
            "a sandbox refuses the home folder: run it outside one",
        ) from None
    return f"approve-gate: approved — {hashed} · {change}"


def anchor(cwd: Path, yes: str | None) -> str:
    """Seed the first offline base from the default branch's tracking ref, checked.

    Why: 0062-offline-origin design D6.
    """
    primary = primary_of(cwd)
    _refuse_config_commands(primary)
    if _claim(primary / ".minions" / "runs" / "active") == "live":
        raise Stop(2, "anchor: cannot run — a run is live: .minions/runs/active exists")
    file = _pushed_file(primary)
    if file.is_file():
        raise Stop(
            2,
            f"anchor: cannot run — an offline base stands:"
            f" ~/{KEPT_ORIGINS}/{file.name}",
        )
    default = _kept_default(primary)
    tracking = f"origin/{default}"
    sha = _maybe(
        primary, "rev-parse", "-q", "--verify", f"refs/remotes/{tracking}^{{commit}}"
    )
    if sha is None:
        raise Stop(2, f"anchor: cannot run — {tracking} is missing")
    sha = sha.strip()
    tip = _git(primary, "rev-parse", f"refs/heads/{default}").strip()
    if not _history_ancestor(primary, sha, tip):
        raise Stop(2, f"anchor: cannot run — {tracking} is not on {default}")
    if not _merges_a_release(primary, sha, _release_tags(primary)):
        raise Stop(2, f"anchor: cannot run — {tracking} is no release merge")
    if yes is None:
        raise Stop(
            1,
            f"anchor: check {sha} · {_subject(primary, sha)} against origin's"
            f" {default}, then run conduct.py anchor --yes {sha}",
        )
    if yes != sha:
        raise Stop(2, f"anchor: cannot run — {tracking} is {sha}, not {yes}")
    if why := _keep_base(primary, sha):
        raise Stop(
            2,
            f"anchor: cannot write the offline base — {why}; a sandbox refuses the"
            " home folder: run it outside one",
        )
    return f"anchor: {sha} · {_subject(primary, sha)}"


def agent(cwd: Path, executor: str, prompt: str) -> int:
    """Run one worker in `cwd` under the run's permissions; return its exit code."""
    if _executor_missing(executor):
        raise Stop(2, f"agent: cannot run — {executor} is not on PATH")
    stamp = time.strftime(STAMP)
    repo = _repo(cwd)
    out = repo[0] / ".minions" / "runs" / f"agent-{stamp}.log"
    command = argv(executor, prompt, cwd, None, None, repo)
    try:
        code, killed = work(command, cwd, out, None)
    finally:
        _temp_gone(command)
    for denied in denials(out):
        print(f"agent: denied — {denied}")
    print(f"agent: exit {code}{' · timed out' if killed else ''} · {out}")
    return 1 if killed else code


def converge_by_hand(cwd: Path, change: str, given: list[str], executor: str) -> int:
    """Run `converge.py` for `change` in its worktree; return its exit.

    Why: 0108-converge-script design D1.
    """
    if _executor_missing(executor):
        raise Stop(2, f"converge: cannot run — {executor} is not on PATH")
    primary = primary_of(cwd)
    version = find_version(primary, change)
    if version is None or version.tree is None:
        raise Stop(2, f"converge: cannot run — no version worktree holds {change}")
    named: dict[str, tuple[str, str | None, str | None]] = {}
    skipped: set[str] = set()
    grant = False
    for arg in given:
        role, _, value = arg.partition("=")
        model, slash, effort = value.partition("/")
        if (role, value) == ("grant", "yes"):
            grant = True
        elif role in ROLES and value == "skip":
            skipped.add(role)
        elif (
            role in (*ROLES, "fix")
            and slash
            and TOKEN.fullmatch(model)
            and TOKEN.fullmatch(effort)
        ):
            named[role] = (
                executor,
                None if model == "default" else model,
                None if effort == "default" else effort,
            )
        else:
            raise Stop(
                2,
                f"converge: cannot run — {arg} is not <role>=<model>/<effort>,"
                " <checker>=skip or grant=yes",
            )
    run = Run(primary, executor)
    run.claim = None
    run.lines = ship_lines(primary)
    run.plan[change, "converge"] = (executor, None, None)
    workers: dict[str, object] = {"shadow": False}
    for role in (*ROLES, "fix"):
        models = named.get(role, (executor, None, None))
        run.plan[change, f"converge.{role}"] = models
        workers[role] = "skip" if role in skipped else models
    return run.converge(
        run,
        change,
        version.tree,
        workers=workers,
        grant=grant,
        deadline=time.monotonic() + TIMEOUT,
    )


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
    # why: 0080-minions-layout design D4
    old = _old_files(primary)
    cuts = _cuts(primary)
    lines += [
        f"{version.change} · old layout — a run moves it"
        if version.change in old
        else f"{version.change} · {stage_of(primary, version)[0]}"
        for version in open_versions(primary)
        if version.change not in cuts
    ]
    # A queued cut's line stands for its version's. Why: 0082-cut-station design D6.
    lines += [
        f"{change} · cut"
        if entry["halt"] is None
        else f"{change} · cut-halted — {entry['halt']}"
        for change, entry in cuts.items()
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


def _cards(debt: Path, change: str) -> list[str]:
    """Return the ids of the cards under the change's debt heading.

    e.g. "- **0016·R5 — a title**" → "0016·R5"
    """
    ids: list[str] = []
    inside = False
    for line in debt.read_text().splitlines() if debt.is_file() else []:
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
    return int(change.split("-", maxsplit=1)[0])


def report(cwd: Path) -> str:
    """Return the last run's close-out: its waits, each version, the halts, the end.

    Why: 0067-rescue design D6; 0085-self-healing-ship design D4.
    """
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
    lines += [
        f"run · waited {detail.removeprefix('waiting: ')}"
        for found in events
        if found[2] == "push"
        and (detail := found.string[found.end() :]).startswith("waiting: ")
    ]
    old = _old_files(primary)
    for change in sorted(touched, key=_change_number):
        version = find_version(primary, change)
        if version is None:
            lines.append(f"{change} · no version branch")
            continue
        if change in old:
            lines.append(f"{change} · old layout — a run moves it")
            continue
        tag = _tag_of(primary, change)
        if tag is not None and not _tagged(primary, tag):
            tag = None
        pushed = _pushed(primary, change, tag) if tag is not None else False
        conformance = _change_dir(primary, change) / "conformance.md"
        round_ = (
            _frontmatter(conformance.read_text(), "round")
            if conformance.is_file()
            else None
        )
        page = runs / "metrics" / f"{change}.html"
        lines.append(
            " · ".join(
                [
                    change,
                    tag or "no tag",
                    f"merge {_merge_commit(primary, version) or 'none'}",
                    {None: "no origin", True: "pushed", False: "not pushed"}[pushed],
                    f"round {round_ or 'none'}",
                    f"cards {' '.join(_cards(runs / 'debt.md', change)) or 'none'}",
                    f"denied {', '.join(denied.get(change, [])) or 'none'}",
                    f".minions/metrics/{change}.html"
                    if page.is_file()
                    else "metrics: none",
                    *([f"blocked {blocked[change]}"] if change in blocked else []),
                ]
            )
        )
    for found in events[:-1]:
        detail = found.string[found.end() :]
        change, _, stage = detail.partition(": ")
        skipped = found[2] == "rejoin" and detail.startswith("skipped — ")
        if found[2] == "halt" or skipped:
            lines.append(found.string)
        elif found[2] == "rejoin" and not stage.startswith("still "):
            lines.append(f"{change} · rejoined {stage}")
        elif found[2] == "rescue":
            kind, _, rest = stage.partition(" · ")
            lines.append(f"{change} · {'rescued' if kind == 'fixed' else kind} {rest}")
        elif found[2] == "supervise":
            kind, _, rest = stage.partition(" · ")
            said = "supervised" if kind == "decided" else kind
            lines.append(f"{change} · {said} {rest}")
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
    cutting = commands.add_parser("cut", help="queue a settled brief for a run to cut")
    cutting.add_argument("slug")
    cutting.add_argument("bump", choices=("minor", "patch"))
    cutting.add_argument("brief", metavar="brief=<path>")
    cutting.add_argument("links", metavar="[after=<ids>] [beside=<ids>]", nargs="*")
    cutting.add_argument("--executor", required=True, choices=("claude", "codex"))
    cutting.add_argument("--model")
    cutting.add_argument("--effort")
    commands.add_parser("stop", help="end the live run")
    granting = commands.add_parser("grant", help="one more round past the cap")
    granting.add_argument("change_id", metavar="change-id")
    granting.add_argument("--executor", required=True, choices=("claude", "codex"))
    rejoining = commands.add_parser("rejoin", help="the live run takes a version back")
    rejoining.add_argument("change_id", metavar="change-id", nargs="?")
    rejoining.add_argument("--yes", metavar="hash")
    agenting = commands.add_parser("agent", help="one worker in the cwd")
    agenting.add_argument("--executor", required=True, choices=("claude", "codex"))
    agenting.add_argument("prompt")
    converging = commands.add_parser(
        "converge", help="converge one version by hand, in the cwd's repo"
    )
    converging.add_argument("change_id", metavar="change-id")
    converging.add_argument(
        "given",
        metavar="[conformance=<m>/<e>] [adversarial=…] [fix=…] [grant=yes]",
        nargs="*",
    )
    converging.add_argument("--executor", default="claude", choices=EXECUTORS)
    commands.add_parser("report", help="the last run's close-out lines")
    approving = commands.add_parser("approve-gate", help="the person's yes to a gate")
    approving.add_argument("change_id", metavar="change-id")
    approving.add_argument("--yes", required=True, metavar="hash")
    anchoring = commands.add_parser(
        "anchor", help="a person seeds the first offline base"
    )
    anchoring.add_argument("--yes", metavar="sha")
    boxing = commands.add_parser(
        "sandboxed", help="run a command under the OS sandbox, over the version's trees"
    )
    boxing.add_argument("argv", metavar="cmd", nargs=argparse.REMAINDER)
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
        elif args.command == "cut":
            line = cut(
                cwd,
                args.slug,
                args.bump,
                args.brief,
                args.links,
                args.executor,
                args.model,
                args.effort,
            )
            print(line)
        elif args.command == "stop":
            print(stop_run(cwd))
        elif args.command == "grant":
            return grant(cwd, args.change_id, args.executor)
        elif args.command == "rejoin":
            print(rejoin(cwd, args.change_id, args.yes))
        elif args.command == "agent":
            return agent(cwd, args.executor, args.prompt)
        elif args.command == "converge":
            return converge_by_hand(cwd, args.change_id, args.given, args.executor)
        elif args.command == "approve-gate":
            print(approve_gate(cwd, args.change_id, args.yes))
        elif args.command == "anchor":
            print(anchor(cwd, args.yes))
        elif args.command == "sandboxed":
            command = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
            if not command:
                raise Stop(2, "sandboxed: cannot run — no command")
            return sandboxed(command, cwd, reach(primary_of(cwd)))
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
