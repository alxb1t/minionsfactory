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
    conduct.py rejoin [<change-id>]
    conduct.py agent --executor claude|codex <prompt>
    conduct.py report
    conduct.py approve-gate <change-id> --yes <hash>

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
import stat
import subprocess
import sys
import tempfile
import threading
import time
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NamedTuple

TIMEOUT = 10800
STAMP = "%Y%m%d-%H%M%S"
GIT_TIMEOUT = 60
PUSH_TIMEOUT = 1800
RETRIES = (0, 10, 30)
PUSH_RETRIES = (0, 10)
LOCK_SECONDS = 30
LOCK_STALE = 600
DEBT = ".minions/debt.md"
DEBT_LOCK = ".minions/debt.lock"
OLD_DEBT = ".minions/backlog.md"
OLD_DEBT_LOCK = ".minions/backlog.lock"
REJOIN_POLL = 10
INTEGRATE = Path(__file__).resolve().parents[2] / "mf-integrate/scripts/integrate.py"
PIN = Path(__file__).resolve().with_name("pin.py")
MOVED = "delta: changed on the default branch: "
# A started build's gate and rules: changed since its base, they are merged in.
GATE_FILES = ("Makefile", "*.mk", "AGENTS.md", "CODING_STANDARDS.md", "CONTRIBUTING.md")
CHANGE_ID = re.compile(r"(\d+)-([a-z0-9-]+)")
SHA256 = re.compile(r"[0-9a-f]{64}")
PROGRESS = re.compile(r"^- \[([ x])\] (\d+) — (.*)$", re.MULTILINE)
RELEASE = re.compile(r"chore\(release\): (\S+)")
EVENT = re.compile(r"^\d\d:\d\d:\d\d · (\S+) · (\S+) — ")
EVENTS = (
    *("start", "spawn", "finish", "check", "denied", "halt", "blocked", "done"),
    *("push", "ledger", "unlock", "unkept", "kept", "removed", "rejoin", "grant"),
    *("rescue", "move"),
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
STATIONS = ("build", "converge", "integrate", "release")
# The rescue is no stage: it runs in a halted version's thread, and its models are
# planned with the stations'. Why: 0067-rescue design D3, D5.
PLANNED = (*STATIONS, "rescue")
RESCUED = ("converge-halted", "integrating")
RESCUES = 3
AMENDS = ("tasks.md", "design.md")
ROLES = ("review", "security")
# Each old-layout path of a change, by its name in the change's folder.
# Why: 0080-minions-layout design D1, D4.
OLD_LAYOUT = {
    "findings/{}_review.md": "review.md",
    "findings/{}_security.md": "security.md",
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
OLD_ID = r"(\d{4}-[a-z0-9-]+)"
OLD_STAMP = re.compile(r"\d{8}-\d{6}(?:-\d+)?")
OLD_LOG = re.compile(rf"{OLD_ID}_([a-z][a-z-]*?)(-\d+)?\.log")
# A cap of these alone gets the run's one grant. Why: 0070-cap-policy design D1, D2.
BLOCKS = {"review": ("blocking",), "security": ("critical", "high")}
SMALL = ("one line", "a test", "one line and a test")
CARD = re.compile(r"^- \*\*(\S+) — ", re.MULTILINE)
EXECUTORS = ("claude", "codex")
SKILLS = {"claude": ".claude/skills", "codex": ".agents/skills"}
STOPPED = "stopped by the person"
CONFIG_CHANGED = "the local git config changed during the run: {file} differs"
GIT_FILES = (".git/config", ".git/info/attributes")
KEPT_ORIGINS = ".mf-ship-origin"
SCANNER = "betterleaks"
CAFFEINATE = "caffeinate"
LEAKED = 3
SSH_COMMAND = "ssh -o ConnectTimeout=15 -o BatchMode=yes"
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
    "converge": "Run the mf-converge skill for change {change}{grant}.",
    "integrate": "Run the mf-integrate skill for change {change}.",
    "release": "Run the mf-release skill for change {change} with merge=yes.",
    "rescue": "Run the mf-rescue skill for change {change}.",
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
    """`AGENTS.md`'s `Ship tools:` and `Ship network:` values."""

    tools: list[str]
    network: list[str]


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
            try:
                os.mkdir(part, dir_fd=fd)
            except FileExistsError:
                pass
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


def _old_files(primary: Path) -> dict[str, list[tuple[Path, str]]]:
    """Return each change's old-layout files, each with its path in the change's folder.

    A file `OLD_LAYOUT` does not name stays out, prefix matches and strays alike.
    e.g. `findings/0001-x_review.md` → {"0001-x": [(…, "review.md")]}
    e.g. `runs/<stamp>/0001-x_converge-2.log` → `logs/<stamp>-converge-2.log`
    Why: 0080-minions-layout design D4.
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


def _closed(runs: Path, tree: Path, change: str) -> bool:
    """Return whether `.minions/changes/<change>/build.done` names the tree's `HEAD`.

    A missing or unreadable file is not closed, nor is one that is no regular file.
    Why: 0055-build-resume design D2.
    """
    done = _change_dir(runs.parent, change) / "build.done"
    if not done.is_file():
        return False
    try:
        text = done.read_text()
    except (OSError, UnicodeDecodeError):
        return False
    found = re.search(r"^head:\s*(\S+)", text, re.MULTILINE)
    if found is None:
        return False
    named = _maybe(tree, "rev-parse", "-q", "--verify", f"{found[1]}^{{commit}}")
    return (named or "").strip() == _git(tree, "rev-parse", "HEAD").strip()


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
    return line.split(" — ")[0].endswith(f" · {event}")


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
        (i for i, line in enumerate(lines) if line.startswith("## Run")), None
    )
    if heading is None:
        return False
    run = itertools.takewhile(
        lambda line: not line.startswith("## Run"), lines[heading + 1 :]
    )
    return any(_is_event(line, "start") for line in run)


def _before_round(runs: Path, change: str, halt: str) -> bool:
    """Return whether `halt` is a halt before round 1: no `start`, no `verify: halt`.

    Why: 0084-ship-fixes-2 design D1, D2.
    """
    return "verify: halt" not in halt and not _run_started(runs, change)


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
    """Return whether the person's amend answers a converge halt of this kind.

    The kinds: a halt in a catch-up run with both findings files still clean, a
    `verify: halt`, and an `amend needed`. Why: 0071-ship-fixes design D5.
    """
    if "verify: halt" in halt or "amend needed" in halt:
        return True
    if not _run_marked(runs, change, "catch-up"):
        return False
    files = (_change_dir(runs.parent, change) / f"{role}.md" for role in ROLES)
    return all(
        file.is_file() and _frontmatter(file.read_text(), "verdict") == "clean"
        for file in files
    )


def _amended_only(tree: Path, change: str, halted: str) -> bool:
    """Return whether only the person's amends of the change directory follow `halted`.

    `halted` is an ancestor of `HEAD` and not it, and each commit past it has one
    parent, the amend's subject, and paths under `openspec/changes/<change>/` alone.
    Why: 0071-ship-fixes design D5.
    """
    head = _git(tree, "rev-parse", "HEAD").strip()
    if halted == head or not _ancestor(tree, halted, "HEAD"):
        return False
    folder = f"openspec/changes/{change}/"
    subject = f"docs({change}): amend the change directory"
    listed = ("diff-tree", "--root", "-m", "-r", "--no-commit-id", "--name-only")
    for line in _git(tree, "rev-list", "--parents", f"{halted}..HEAD").splitlines():
        sha, *parents = line.split()
        paths = _git(tree, *listed, sha).split()
        if (
            len(parents) != 1
            or _subject(tree, sha) != subject
            or not all(path.startswith(folder) for path in paths)
        ):
            return False
    return True


def _answered(runs: Path, tree: Path, change: str, halt: str) -> bool:
    """Return whether a person's commit answered a converge halt.

    The halt names the head it stopped at, both findings files judged that head,
    and `HEAD` descends from it and is not it. A halt past the judged head — after
    converge's own fix, or in a catch-up run — names no head the files judged, and a
    rewritten history leaves no descendant. A halt the person's amend answers is
    answered by amends alone past its head, and a halt before round 1 by any commit.
    Why: 0071-ship-fixes design D5; 0084-ship-fixes-2 design D1.
    e.g. "… · halt — cap reached · head 7ee2179", `HEAD` a fix past 7ee2179 → True
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
    if _amendable(runs, change, halt) and _amended_only(tree, change, halted):
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


def _unjudged(runs: Path, tree: Path, change: str, rev: str = "HEAD") -> str | None:
    """Return why converge is not clean at `rev`, or None when it is."""
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
    end = _run_end(runs, change)
    if end is None and not _closed(runs, tree, change):
        return "build", "closing steps left"
    if halt := _converge_halt(runs, change):
        if DEBT_LOCK in halt or OLD_DEBT_LOCK in halt:
            return "converge", "halted on the debt lock: resumes at Step 9"
        if _rerun(runs, tree, change, halt):
            return "converge", RERUN
        if _answered(runs, tree, change, halt):
            return "converge", AMENDED
        if "cap reached" in halt and _granted(runs, change, take=False):
            return "converge", "granted"
        return "converge-halted", halt
    if end is not None and not _converge_done(runs, change):
        return "converge", f"unfinished run: {end}"
    if why := _unjudged(runs, tree, change):
        return "converge", why
    if not _ancestor(tree, default, "HEAD"):
        return "integrate", f"{default} is not an ancestor of HEAD"
    return "release", f"converge clean at HEAD; {default} is an ancestor"


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


def _check_converge(primary: Path, version: Version, tree: Path) -> str | None:
    """Return why the converge check fails, or None."""
    runs = primary / ".minions"
    halt = _converge_halt(runs, version.change)
    if halt and not _answered(runs, tree, version.change, halt):
        return f"the status log halts: {halt}"
    if not _converge_done(runs, version.change):
        return "the status log has no done"
    if why := _unjudged(runs, tree, version.change):
        return why
    return "the tree is not clean" if _dirty(tree) else None


def _check_integrate(primary: Path, version: Version, tree: Path) -> str | None:
    """Return why the integrate check fails, or None; an open merge names its note.

    A `.red` with a `head:` fails it until a green gate deletes it. The subject
    read is the newest first-parent merge's, so the person's fix commit after it
    passes. Why: 0071-ship-fixes design D2.
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

    Offline, a tag origin cannot list is released locally: the next good read
    pushes it. A run's read of the tag that fails is `Unreachable`, and the run
    goes offline. Why: 0062-offline-origin design D2, D4.
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

    It reads the operator's config, and what that includes, and no repo's, so a key
    a worker sets after the refusal starts nothing. The caller passes a URL, not a
    remote's name, behind `--`. With no ssh command the operator set, ssh neither
    hangs nor prompts.
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

    Betterleaks reads a scratch repo with `primary`'s objects, no system config and no
    attributes, so no worker-written filter or `textconv` runs; its report is redacted.
    It reads no ignore file and no allow comment, which a worker can write. `git log -p`
    prints no merge's diff, so a two-parent merge is read by what it adds to the
    automatic merge of its parents; git shows an octopus merge's not at all, so one
    stops the scan. Why: 0065-gate-hardening design D7.
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


def _local_releases(primary: Path, base: str, default: str) -> list[str]:
    """Return `default` and the tags of its release merges past raw `base`, or none."""
    tags = _release_tags(primary)
    commits = _foreign_commit(primary, base, default, tags=tags)
    released = {_history(primary, "rev-parse", f"{sha}^2") for sha in commits}
    named = [tag for tag, (_, commit) in tags.items() if commit in released]
    return [default, *named] if commits else []


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


def check(
    primary: Path,
    stage: str,
    version: Version,
    first_read: bool = False,
    offline: bool = False,
) -> str | None:
    """Return why a station's check on disk fails, or None when it passes."""
    if stage == "release":
        return _check_release(primary, version, first_read, offline)
    if version.tree is None:
        return f"{version.change} has no worktree"
    if stage == "build":
        return _check_build(primary, version, version.tree)
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


def _table(runs: Path, change: str, name: str) -> dict[str, object] | None:
    """Return a table of the cut's models file; None with no file or no such table."""
    path = _change_dir(runs.parent, change) / "models.toml"
    if not path.is_file():
        return None
    try:
        data = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as error:
        raise Stop(
            1, f"conduct: halt — changes/{change}/models.toml: {error}"
        ) from None
    table = data.get(name)
    return table if isinstance(table, dict) else None


def _models(
    runs: Path, change: str, station: str, run: str
) -> tuple[str, str | None, str | None]:
    """Return the station's executor, model and effort from the cut's models file.

    Integrate uses the `[release]` table, and the rescue `[rescue]`, else `[build]`.
    An absent executor is the run's, `run`; an absent model or effort is None. A
    table no executor can run halts the version. Why: 0067-rescue design D5.
    """
    names = {"integrate": ("release",), "rescue": ("rescue", "build")}
    tables = (_table(runs, change, name) for name in names.get(station, (station,)))
    table = next((table for table in tables if table is not None), {})
    executor = table.get("executor", run)
    model, effort = table.get("model"), table.get("effort")
    model = model if isinstance(model, str) else None
    file = f"changes/{change}/models.toml"
    if executor not in EXECUTORS:
        raise Stop(1, f"conduct: halt — {file}: executor {executor!r} unknown")
    if executor == "codex" and (model or "").startswith("claude"):
        raise Stop(1, f"conduct: halt — {file}: {station} on codex, model {model}")
    return str(executor), model, effort if isinstance(effort, str) else None


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
        starts = list(CARD.finditer(text))
        if not starts:
            continue
        ends = [card.start() for card in starts[1:]] + [len(text)]
        for title, end in zip(starts, ends, strict=True):
            card = text[title.start() : end]
            # A station may wrap a field's value in backticks.
            severity = _field(card, "Priority").split(" · ")[0].strip(" `").lower()
            if severity in BLOCKS[role] and re.match(r"open\b", _field(card, "Status")):
                sized = re.search(r"size:([^:]*)$", _field(card, "Fix"))
                size = sized[1].strip(" `.") if sized else ""
                found.append((title[1], size or "a design change"))
    return found


def _amend(
    tree: Path, change: str, before: str, amends: tuple[str, ...]
) -> tuple[str | None, str]:
    """Return the rescue's amend past `before`, or None and why it is none.

    An amend is one commit, its subject the amend's, with a `Rescue:` trailer,
    touching the change's `amends` files alone; with no `amends` there is none. No
    commit is (None, ""). Why: 0067-rescue design D3.
    """
    if not _ancestor(tree, before, "HEAD"):
        return None, f"rescue moved HEAD off {before[:7]}"
    commits = _git(tree, "rev-list", f"{before}..HEAD").split()
    allowed = {f"openspec/changes/{change}/{name}" for name in amends}
    listed = ("diff-tree", "--root", "-m", "-r", "--no-commit-id", "--name-only")
    paths = {path for sha in commits for path in _git(tree, *listed, sha).splitlines()}
    if touched := sorted(paths - allowed):
        return None, f"rescue touched {' '.join(touched)}"
    if not commits:
        return None, ""
    sha = commits[0]
    trailer = _git(tree, "log", "-1", "--format=%(trailers:key=Rescue)", sha)
    named = _subject(tree, sha) == f"docs({change}): amend the change directory"
    if len(commits) > 1 or not amends or not named or not trailer.strip():
        return None, f"rescue commit {sha[:7]} is not one amend with a Rescue: trailer"
    return sha, ""


def _mtime(path: Path) -> int | None:
    """Return a regular file's modification time in nanoseconds, else None."""
    try:
        status = path.lstat()
    except OSError:
        return None
    return status.st_mtime_ns if stat.S_ISREG(status.st_mode) else None


def _entries(folder: Path, empty: bool) -> list[str]:
    """Return the names in `folder`, deleting each when `empty`; none through a link.

    The folder is opened once, following no link, and read and emptied through that
    descriptor, so a link swapped in after the listing deletes nothing. An entry
    `unlink` refuses, a folder say, is left and not named. Why: 0067-rescue design D7.
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


def _granted(runs: Path, change: str, take: bool) -> bool:
    """Return whether `runs/grants` holds `change`'s grant, deleting it when `take`.

    The folder is opened following no link, and the grant read and deleted through
    that descriptor, so a link at the folder holds no grant and loses no file. Only a
    regular file is a grant. Why: 0067-rescue design D7.
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
    """Return `AGENTS.md`'s `Ship tools:` and `Ship network:` lines.

    A `Ship network:` value that is not a plain domain stops with 1, and so does a
    `Ship loopback:` line of any value. Why: 0052-security-hardening design D2;
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
    """Return the Claude worker's sandbox settings, as JSON.

    A sandbox that cannot start ends the worker. Why: 0052-security-hardening design
    D1, 0053-sandbox-patch design D1 and 0056-loopback-removal design D1.
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
        tools, network = lines or ship_lines(primary)
        allowed, denied = allowlist(trees, tools)
        return [
            *("env", "-u", "VIRTUAL_ENV", *HOOKS_OFF, cache),
            *("claude", "-p", prompt),
            *(("--model", model) if model else ()),
            *(("--effort", effort) if effort else ()),
            *("--output-format", "stream-json", "--verbose"),
            *(arg for tree in trees for arg in ("--add-dir", str(tree))),
            *("--settings", worker_settings(primary, trees, common, network)),
            # A worker can write the project's settings and `.mcp.json`, and each
            # runs at a start, outside the sandbox.
            # Why: 0052-security-hardening design D1.
            *("--setting-sources", "user"),
            # No MCP server starts, the operator's own included.
            # Why: 0076-context-cost design D2.
            *("--strict-mcp-config",),
            *("--allowedTools", *allowed, "--disallowedTools", *denied),
        ]
    # Why: 0050-codex-review design D5.
    if common and _common_dir(primary) != common:
        raise Stop(1, "conduct: halt — the primary's .git moved during the run")
    roots = [*([str(common)] if common else []), *(str(tree) for tree in trees)]
    # Why: 0050-codex-review design D4.
    system = "/usr/bin:/bin:/usr/sbin:/sbin"
    path = f"PATH={system}:{os.environ.get('PATH', '')}"
    env = ("env", "-u", "VIRTUAL_ENV", *HOOKS_OFF, cache, path)
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


def _free_log(root: Path, parts: tuple[str, ...], name: str) -> tuple[Path, int]:
    """Return the first free of `<name>.log`, `<name>-2.log`, … in `root`'s `parts`.

    And a descriptor open on it for writing, made through the folders' own, so a
    link a worker swaps in at any of them names no place outside the run directory.
    e.g. a converge's second spawn in a stamp → `<stamp>-converge-2.log`.
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
    command: list[str], cwd: Path, out: Path | int, claim: Path | None
) -> tuple[int, bool]:
    """Run one worker in its own process group, output to `out`, held in `claim`.

    `out` is a path, or a descriptor it closes. Return its exit code and whether
    `TIMEOUT` killed it.
    """
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


def mcp_started(executor: str, log: Path) -> str | None:
    """Return why a worker's start fails the probe, or None when no MCP server started.

    e.g. an `init` event's `"mcp_servers": [{"name": "runpod"}]` → "claude started an
    MCP server: runpod". A log with no `init` event, as Codex's, passes. Why: D51.
    """
    names: list[str] = []
    with log.open(errors="replace") as lines:
        for line in lines:
            if '"mcp_servers"' not in line:
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if not isinstance(event, dict) or event.get("subtype") != "init":
                continue
            servers = event.get("mcp_servers")
            for server in servers if isinstance(servers, list) else [servers]:
                name = server.get("name") if isinstance(server, dict) else server
                names.append(str(name))
    return f"{executor} started an MCP server: {', '.join(names)}" if names else None


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


def _pin() -> dict[str, Any]:
    """Return `pin.py`'s namespace: the live marks, the links, the quiet move."""
    return runpy.run_path(str(PIN))


def _mark_live(pin: dict[str, Any], primary: Path) -> Path | None:
    """Write this run's live mark, holding its pid; return it, or None if not written.

    A mark another live run holds stays: the parent that detached this run is not
    another. Where the home folder refuses it, none is written.
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


class Run:
    """One ship run: the probe, then every open version to the default branch."""

    def __init__(self, primary: Path, executor: str) -> None:
        """Load `integrate.py`, and open the run log in the primary's run directory."""
        integrate = runpy.run_path(str(INTEGRATE))
        self.delta = integrate["delta"]
        self.rules = {
            "CHANGELOG.md": integrate["changelog"],
            "docs/decisions.md": integrate["decisions"],
        }
        self.git_state = _git_state(primary)
        self.pushes = (_kept_origin(primary) or _urls(primary))[1]
        self.primary = primary
        self.repo = _repo(primary)
        self.worktrees = primary / (_agents_values(primary, "Worktrees") or [""])[0]
        self.executor = executor
        self.runs = primary / ".minions" / "runs"
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
        self.rescues: dict[str, list[str]] = {}
        self.answered: dict[str, str] = {}
        self.reruns: set[str] = set()
        self.skips: set[str] = set()
        self.capped: set[str] = set()
        self.grants_auto: dict[str, bool] = {}
        self.outs: dict[tuple[str, str], Path] = {}
        self.lines = ShipLines([], [])
        self.guard = threading.Lock()
        self.merging = threading.Lock()

    def halt(self, who: str, reason: str) -> None:
        """Record and log a halt; its version starts no new worker but its rescue."""
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
        return f"halted {halted} · blocked {blocked} · released {released}" + (
            self.unpushed()
        )

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
    ) -> list[str] | None:
        """Run one worker and log it and its denials; `repo` defaults to the run's.

        Return the denials, or None when a timeout or a failed exit halted `who`.
        """
        executor, model, effort = models
        command = argv(
            executor, prompt, cwd, model, effort, repo or self.repo, self.lines
        )
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
        started = time.monotonic()
        code, killed = work(command, cwd, sink, self.runs / "active")
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
        """Run a halted version's rescue on `held`; True when its amend cleared it.

        The amend may touch the change's `amends` files alone: none at a converge or
        integrate halt, which a rescue diagnoses. Any other outcome halts the version
        again, naming what the rescue left, and one at such a halt is then checked for
        an answer on disk. A halted run, a skip or a spent rescue starts none. A
        converge `verify: halt` the run diagnoses itself, with no worker.
        Why: 0067-rescue design D2, D3; 0071-ship-fixes design D8.
        """
        change, tree = version.change, version.tree
        spent = change in self.skips or self.rescued(change, held)
        if tree is None or spent or self.stopped("run"):
            return False
        halt = _converge_halt(self.primary / ".minions", change)
        if held == "converge-halted" and halt and "verify: halt" in halt:
            self.diagnose(change, halt)
            return False
        with self.guard:
            self.rescues.setdefault(change, []).append(held)
        models = self.planned_models(change, "rescue")
        before = _git(tree, "rev-parse", "HEAD").strip()
        diagnosis = _change_dir(self.primary, change) / "rescue.md"
        written = _mtime(diagnosis)
        prompt = PROMPTS["rescue"].format(change=change)
        try:
            if self.spawn(change, "rescue", tree, prompt, models) is None:
                return False
            sha, why = _amend(tree, change, before, amends)
            if sha is not None:
                self.log.event("run", "rescue", f"{change}: fixed · {held} · {sha[:7]}")
                with self.guard:
                    self.halts = [halt for halt in self.halts if halt[0] != change]
                return True
            name = f".minions/changes/{change}/rescue.md"
            if not why and _mtime(diagnosis) not in (None, written):
                self.log.event("run", "rescue", f"{change}: diagnosed · {name}")
                why = f"rescue diagnosed — {name}"
            self.halt(change, why or "rescue wrote no amend and no diagnosis")
            return False
        finally:
            if held in RESCUED:
                self.hold(version, tree, before)

    def diagnose(self, change: str, halt: str) -> None:
        """Write the run's diagnosis of a verify halt, through no link, and halt on it.

        The folders are opened following no link, and the file created through their
        descriptor, so a link at any names no place outside the run directory.
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
        self.halt(change, f"rescue diagnosed — {name}")

    def hold(self, version: Version, tree: Path, before: str) -> None:
        """Keep a version halted for the run when its rescue answered its halt on disk.

        A rescue at a converge or integrate halt may only diagnose, yet a commit past
        the halted head, a settled merge, a removed note or a grant it writes reads as
        no halt, and its rejoin request would take the version back. The halt names
        the stage on disk and a moved `HEAD`, for the person.
        Why: 0067-rescue design D3.
        """
        stage, why = stage_of(self.primary, version)
        if stage in HALTS:
            return
        head = _git(tree, "rev-parse", "HEAD").strip()
        moved = f" · HEAD {head[:7]}" if head != before else ""
        answered = f"rescue answered its halt — {stage}: {why}{moved}"
        with self.guard:
            self.answered[version.change] = answered
        self.halt(version.change, answered)

    def held(self, version: Version, stage: str, tree: Path) -> str | None:
        """Return what a failed check at `stage` is rescued on, or None for no rescue.

        A build halt is held on its sub-task, else `build`; one at a `**HUMAN` phase
        gets none, as it needs the person. A converge or integrate halt is held on its
        stage on disk, when that is in `RESCUED`. Why: 0067-rescue design D3.
        """
        change = version.change
        if stage == "build":
            unticked = _unticked(tree, change)
            if unticked is not None and "**HUMAN" in unticked[1]:
                return None
            found = _build_halt(self.primary / ".minions", tree, change)
            return found[0] if found else stage
        if stage in ("converge", "integrate"):
            disk = stage_of(self.primary, version)[0]
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

    def _would_grant(self, version: Version, stage: str, halt: str) -> tuple[bool, str]:
        """Return whether `halt` at `stage` is a cap the run grants, and the blockers.

        It grants a version's first cap in the run, when no granted round, in this
        run or an earlier one, reached it, every open blocker is small and the models
        file allows it; the ids are "" at no cap. A cap is `converge-halted` alone:
        another stage's text may name one. It changes nothing.
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

        Else the refused ids, "" at no cap. Every cap counts towards the first; the
        grant writes no grant file and starts no rescue. `advance` spawns the round
        on the path a person's grant takes, so its check judges it.
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

    def advance(self, version: Version, stop_at: tuple[str, ...]) -> None:
        """Run the version's stations to a stage in `stop_at`, a release or a halt.

        A cap the run grants gets its round, spawned and checked as a person's
        grant's is, and one it refuses a `re-plan` halt line; a build check,
        converge or integrate halt then gets its rescue. A halt before round 1 it runs
        again joins `reruns`. Why: 0070-cap-policy design D2, D3; 0084-ship-fixes-2
        design D1.
        """
        try:
            auto = False
            while not self.stopped(version.change):
                if auto:
                    stage, why = "converge", "granted automatically"
                else:
                    stage, why = stage_of(self.primary, version)
                if stage in STUCK:
                    auto, refused = self.auto_grant(version, stage, why)
                    if auto:
                        continue
                    rescued = stage in RESCUED
                    spent = self.rescued(version.change, stage) if rescued else ""
                    self.halt(version.change, f"{stage} — {why}{spent}")
                    if refused:
                        self.halt(version.change, f"re-plan: {refused}")
                    if rescued:
                        self.rescue(version, stage, ())
                    return
                if stage in stop_at:
                    return
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
                    return
                minions = self.primary / ".minions"
                # The run's own grant takes no person's grant file.
                clause = " and grant=yes" if auto else ""
                person = not auto and stage == "converge"
                auto = False
                if person and _granted(minions, version.change, take=True):
                    # An amended run starts from round 1: the grant goes unspent.
                    clause = "" if why == AMENDED else " and grant=yes"
                    if clause:
                        with self.guard:
                            self.capped.add(version.change)
                        self.log.event(
                            "run",
                            "grant",
                            f"{version.change}: one more round past the cap",
                        )
                prompt = PROMPTS[stage].format(change=version.change, grant=clause)
                models = self.planned_models(version.change, stage)
                if stage == "release" and _tag_of(self.primary, version.change) is None:
                    head = _git(cwd, "rev-parse", "HEAD").strip()
                    _record_release(self.primary, version.change, head)
                    self.log.event(version.change, "ledger", f"{version.change} {head}")
                denied = self.spawn(version.change, stage, cwd, prompt, models)
                if denied is None:
                    return
                if stage == "release" and not self.push_left(PUSH_RETRIES):
                    return
                try:
                    reason = check(self.primary, stage, version, True, self.offline)
                except Unreachable as down:
                    self.waited(str(down))
                    self.offline = True
                    reason = check(self.primary, stage, version, True, True)
                held = None if reason is None else self.held(version, stage, cwd)
                if held is not None:
                    reason = f"{reason}{self.rescued(version.change, held)}"
                if not self.judge(version.change, stage, reason, denied):
                    amends = AMENDS if stage == "build" else ()
                    if held is None:
                        return
                    # Only a failed converge check meets a cap here.
                    cap = held if stage == "converge" else stage
                    auto, refused = self.auto_grant(version, cap, reason or "")
                    if refused:
                        self.halt(version.change, f"re-plan: {refused}")
                    if auto or self.rescue(version, held, amends):
                        continue
                    return
                if stage == "release":
                    if tag := _tag_of(self.primary, version.change):
                        self.released.append(tag)
                        if self.offline:
                            self.waited(f"{tag} released locally")
                    self.remove_tree(version)
                    return
        except Stop as stop:
            self.halt(version.change, str(stop))
        except Exception as error:
            self.halt("run", f"conduct.py failed: {error}")

    def _keeps(self, tree: Path, change: str) -> str | None:
        """Return why `remove_tree` keeps `tree`, or None to remove it.

        A changed or refused config, a link at the cut's path, or another path keeps
        it. e.g. a link at the cut's path → "a link at the cut's path"
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

        The branch stays. A worker can write the worktree entry, so its path is checked
        against `Worktrees:`, read before the first worker. The removal deletes the
        tree's ignored paths, so they are listed first and logged; a failed listing
        keeps the tree. A changed or refused config and a link at the cut's path keep it
        too, checked before the listing and again after it, which a worker can
        lengthen, so only the gap before git's own call is left.
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
        """Merge the default branch into a branch, once the delta check passes.

        A conflict goes to `settle`. A requirement both sides changed leaves the merge
        open with its note, which `stage_of` reads as an `integrating` halt.
        """
        if changed := _config_changed(self.primary, self.git_state):
            raise changed
        note = _change_dir(self.primary, change) / "integrate.md"
        opened = _merge_open(tree)
        if opened and note.is_file():
            return
        _refuse_config_commands(tree)
        merge = ("merge", "-q", "--no-ff", "--no-commit", default)
        if not opened and _maybe(tree, *merge) is None:
            self.settle(tree, change, default)
        if moved := _delta(self.delta, tree):
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
        message = f"chore(integrate): merge {default} into {change}"
        _git(tree, "commit", "-q", "-m", message, "-m", f"Change: {change}")

    def settle(self, tree: Path, change: str, default: str) -> None:
        """Settle a merge's conflicts by `integrate.py`'s rules; else abort it, stop.

        Why: 0063-rejoin design D6.
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
            if path in first and not stopped:
                try:
                    rule(tree)
                except Exception as error:
                    stopped = f" — {error}"
        if not (left := _conflicts(tree)) and not stopped:
            return
        _git(tree, "merge", "--abort")
        raise Stop(
            1,
            f"conduct: halt — merging {default} into {change} conflicts in"
            f" {', '.join(left or first)}{stopped}: {run}",
        )

    def catch_up(self, version: Version) -> None:
        """Merge the default branch into a version behind it.

        A cut-only version, its merges aside, gets it merged in by `merge_in`, and so
        does a started one with an unticked phase and no open merge, behind a default
        branch that changed `GATE_FILES`. One with an unticked phase and a merge open
        with no note stops with 1, naming the commit that finishes it, unless its `HEAD`
        lacks an `after:` id, a merge `ready` finishes. Any other goes on from its
        stage. Why: 0057-run-fixes design D2; 0071-ship-fixes design D4.
        """
        change, default, tree = (
            version.change,
            default_branch(self.primary),
            version.tree,
        )
        if tree is None or _ancestor(self.primary, default, change):
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

    def take(self, version: Version, threads: dict[str, threading.Thread]) -> None:
        """Take one version to its release, a halt or a block."""
        try:
            for station in PLANNED:
                _models(
                    self.primary / ".minions", version.change, station, self.executor
                )
            self.catch_up(version)
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
        """Read each station's models, once per version: at the start, or as it joins.

        A worker can write them. A table `_models` refuses stays out of the plan: it
        halts in `take`. The rescue's skip and `[converge] auto_grant` are read with
        them.
        Why: 0052-security-hardening design D4; 0067-rescue design D5; 0070-cap-policy
        design D4.
        """
        for version, station in itertools.product(versions, PLANNED):
            self.planned.add(version.change)
            if (models := self.models(version.change, station)) is not None:
                self.plan[version.change, station] = models
        for version in versions:
            try:
                skips = _skips_rescue(self.primary / ".minions", version.change)
                grants = _auto_grants(self.primary / ".minions", version.change)
            except (Stop, ValueError):
                continue
            with self.guard:
                self.grants_auto[version.change] = grants
                if skips:
                    self.skips.add(version.change)

    def models(
        self, change: str, station: str
    ) -> tuple[str, str | None, str | None] | None:
        """Return one station's models as `_models` reads them; None on a refusal."""
        try:
            return _models(self.primary / ".minions", change, station, self.executor)
        except (Stop, ValueError):
            return None

    def executors(self) -> list[str]:
        """Return the run's executor, then each other one the plan names."""
        named = (executor for executor, *_ in self.plan.values())
        return list(dict.fromkeys((self.executor, *named)))

    def take_requests(self, threads: dict[str, threading.Thread]) -> bool:
        """Start `take` for each requested open version no thread runs; True if any.

        The requests are read and deleted. A version whose stage is a halt stays out,
        logged; a taken one has its halts and blocks cleared, its models read and its
        new executors probed first. The blocked versions come back after them. It
        raises nothing: it runs beside live threads, so a failure skips the request
        or halts that version. Why: 0063-rejoin design D2; 0071-ship-fixes design D4.
        """
        names = _requests(self.runs)
        if not names or self.stopped("run"):
            return False
        try:
            versions = open_versions(self.primary)
        except Exception as error:
            self.log.event("run", "rejoin", f"skipped — {error}")
            return False
        started = False
        for version in versions:
            change = version.change
            thread = threads.get(change)
            if not names & {"all", change} or (thread and thread.is_alive()):
                continue
            started = self.take_back_safely(version, threads) or started
        self._unblock(threads)
        return started

    def _unblock(self, threads: dict[str, threading.Thread]) -> None:
        """Take back each blocked version one of whose dependencies has a live thread.

        Once per dependency thread, so a refused take-back logs once; in change-id
        order, so a chain comes back in one pass. It raises nothing, as
        `take_requests` does not. Why: 0071-ship-fixes design D4.
        """
        with self.guard:
            waiting = bool(self.blocked)
        if not waiting or self.stopped("run"):
            return
        try:
            versions = open_versions(self.primary)
        except Exception as error:
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

    def take_back_safely(
        self, version: Version, threads: dict[str, threading.Thread]
    ) -> bool:
        """Return `take_back`'s answer; a failure halts the version, raising nothing."""
        try:
            return self.take_back(version, threads)
        except Stop as stop:
            self.halt(version.change, str(stop))
        except Exception as error:
            self.halt(version.change, f"conduct.py failed: {error}")
        return False

    def take_back(self, version: Version, threads: dict[str, threading.Thread]) -> bool:
        """Start `take` for a requested version whose stage is no halt; True if so.

        One the run's plan holds stays out while its models file differs: a worker can
        write it, and so does one whose rescue answered its halt; only one the plan
        lacks has its models read. An executor whose probe failed halts it with that
        probe's reason, probed no second time. A halt before round 1 the run ran
        again stays out. Why: 0063-rejoin design D2, D3; 0067-rescue design D3;
        0071-ship-fixes design D4; 0084-ship-fixes-2 design D1.
        """
        change = version.change
        with self.guard:
            answered = self.answered.get(change)
            reran = change in self.reruns
        if answered is not None:
            self.log.event("run", "rejoin", f"{change}: still halted — {answered}")
            return False
        stage, why = stage_of(self.primary, version)
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
        with self.guard:
            self.halts = [held for held in self.halts if held[0] != change]
            self.blocked = [name for name in self.blocked if name != change]
        if change not in self.planned:
            self.read_plan([version])
        named = (self.plan.get((change, station)) for station in PLANNED)
        for executor in dict.fromkeys(models[0] for models in named if models):
            if executor in self.probed or self.stopped(change):
                continue
            if (refused := self.refused.get(executor)) is not None:
                self.halt(change, refused)
                continue
            self.probe(executor, change)
            if executor not in self.probed:
                with self.guard:
                    self.refused[executor] = next(
                        reason for who, reason in reversed(self.halts) if who == change
                    )
        if self.stopped(change):
            return False
        self.log.event("run", "rejoin", f"{change}: {stage}")
        threads[change] = threading.Thread(
            target=self.take, args=(version, threads), name=change
        )
        threads[change].start()
        return True

    def probe(self, executor: str, who: str = "run") -> None:
        """Prove a sandboxed worker edits, commits and gates a scratch repo; else halt.

        Its log's `init` event lists no MCP server. A failure halts `who`; a pass adds
        `executor` to `probed`. Why: 0063-rejoin design D3; D51.
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
            (scratch / ".gitignore").write_text(".gated\n.arch\n")
            _git(scratch, "add", "Makefile", ".gitignore")
            _git(scratch, *SCRATCH_IDENTITY, "commit", "-q", "-m", "init")
            models = (executor, None, None)
            repo = _repo(scratch)
            denied = self.spawn(who, station, scratch, PROBE, models, repo)
            with self.guard:
                out = self.outs[who, station]
            if denied is not None and self.judge(
                who,
                station,
                check_probe(scratch, mark) or mcp_started(executor, out),
                denied,
            ):
                self.probed.add(executor)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
            mark.unlink(missing_ok=True)

    def push_left(self, tries: tuple[int, ...]) -> bool:
        """Push what a release merged and left; return False when that halted the run.

        A refusal or a rejection halts it, and so does a changed config, before any
        remote call: the URLs are the ones read before the first worker, so a worker
        steers none. A held key is refused first, so the halt names it. The default
        branch is the one origin's HEAD names, and the one a run kept. Its push
        keeps the offline base and removes entries whose heads are now on it; a head
        already there authorizes nothing even when cleanup did not run. A failed read
        is tried again after each of `tries`' delays; past the last, the run is
        offline and judged against the offline base.
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
        """Push each `(ref, sha)`; return False when a refusal halted the run.

        None when a push failed and a re-read of `origin` fails too: a wait. Each heads
        ref's range from the offline base, origin's sha the read just kept, is scanned
        first, so a secret halts the run before any push.
        """
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
        """Wait for every thread, taking requests and blocked versions every poll.

        A poll is `REJOIN_POLL` seconds. With none alive, the requests are read once
        more. Why: 0063-rejoin design D1; 0071-ship-fixes design D4.
        """
        while True:
            self.take_requests(threads)
            self._unblock(threads)
            for thread in [thread for thread in threads.values() if thread.is_alive()]:
                thread.join(timeout=REJOIN_POLL)
            alive = any(thread.is_alive() for thread in threads.values())
            if not alive and not self.take_requests(threads):
                return

    def unlock(self, name: str) -> None:
        """Remove the lock `name` when stale, logging its age."""
        if (age := _clear_stale_lock(self.primary, name)) is not None:
            self.log.event("run", "unlock", f"{name}, {age}s old")

    def migrate_debt(self) -> str | None:
        """Move an old `backlog.md` to `debt.md`; return why the run must halt.

        A stale `backlog.lock` is removed. Both files, an old file that is a link,
        or beside the old file a lock still standing, halt: a person or a hand-run
        writer holds them. The move holds `debt.lock`, as every writer of `debt.md`
        does. Why: 0079-debt-rename design D3.
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

        Every file is checked before any moves: one beside its new path, or a link
        at an old file, an old folder, `changes/` or a change's folder, halts with
        nothing moved. A move links the file in and unlinks the old, so it never
        replaces one. Why: 0080-minions-layout design D4, D6.
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

        A request standing at the start is deleted: the run takes every open version.
        """
        _requests(self.runs)
        versions = open_versions(self.primary)
        worker = " · worker MF_SHIP_AGENT" if os.environ.get("MF_SHIP_AGENT") else ""
        names = " ".join(version.change for version in versions) or "none"
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
        if not versions:
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
            version.change: stage_of(self.primary, version) for version in versions
        }
        # A cap the run grants is not stuck. Why: 0070-cap-policy design D2, D3.
        takes = {
            version.change: self._would_grant(version, *stages[version.change])
            for version in versions
        }
        granted = any(grants for grants, _ in takes.values())
        if not granted and all(stage in STUCK for stage, _ in stages.values()):
            for change, (stage, why) in stages.items():
                if stage == "waiting":
                    self.block(change, why.removeprefix("after ").split()[0])
                else:
                    self.halt(change, f"{stage} — {why}")
                    if refused := takes[change][1]:
                        self.halt(change, f"re-plan: {refused}")
        else:
            for executor in self.executors():
                self.probe(executor)
                if self.halts:
                    break
        if not (self.halts or self.blocked):
            threads: dict[str, threading.Thread] = {}
            for version in versions:
                threads[version.change] = threading.Thread(
                    target=self.take, args=(version, threads), name=version.change
                )
            for thread in threads.values():
                thread.start()
            self.join(threads)
        if self.offline and not self.stopped("run"):
            self.push_left((0,))
        if self.halts or self.blocked:
            self.log.event("run", "halt", self.closing())
            return 1
        released = " ".join(self.released)
        self.log.event("run", "done", f"released {released}{self.unpushed()}")
        return 0


def run(cwd: Path, executor: str, detach: bool) -> int:
    """Start the loop, claimed by `.minions/runs/active`; detached, return at once.

    A stale claim is cleared before the detach, so what stops that reaches the caller.
    The live mark comes first, and a stop before the claim removes it; the last run to
    end moves the links before it goes. Why: 0068-pinned-release design D2 and D3.
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
        _unmark(pin, mark)
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
        try:
            if moved := pin["move"](mark):
                print(moved)
        finally:
            _unmark(pin, mark)
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


def _requests(runs: Path) -> set[str]:
    """Delete the rejoin requests in `runs`; return their names.

    An entry `unlink` refuses, a folder say, is no request, and an unreadable folder
    holds none: the poll runs beside live threads. A folder that is a link holds
    none: a worker may write it, and the conductor deletes outside the sandbox.
    Why: 0063-rejoin design D2.
    e.g. `.minions/runs/rejoin/0001-todo` and `…/all` → {"0001-todo", "all"}
    """
    return set(_entries(runs / "rejoin", empty=True))


def rejoin(cwd: Path, change: str | None) -> str:
    """Ask the live run to take back `change`, or every version, and return the line.

    Why: 0063-rejoin design D1.
    """
    primary = primary_of(cwd)
    runs = primary / ".minions" / "runs"
    if _claim(runs / "active") != "live":
        raise Stop(2, "rejoin: no run is live — run /mf-ship")
    if change is not None and change not in (
        version.change for version in open_versions(primary)
    ):
        raise Stop(2, f"rejoin: cannot run — no open version holds {change}")
    _request(runs, change or "all")
    return f"rejoin: requested {change or 'every halted version'}"


def _request(runs: Path, name: str) -> None:
    """Write the rejoin request `name` for the live run."""
    (runs / "rejoin").mkdir(parents=True, exist_ok=True)
    (runs / "rejoin" / name).touch()


def _rescuing(runs: Path, change: str) -> bool:
    """Return whether the newest run log's last rescue event for `change` is a spawn.

    e.g. `… · 0001-todo · spawn — rescue · model default`, no `finish — rescue` after
    """
    log = last_log(runs)
    lines = log.read_text(errors="replace").splitlines() if log else []
    events = [
        found[2]
        for line in lines
        if (found := EVENT.match(line))
        and found[1] == change
        and found[2] in ("spawn", "finish")
        and line[found.end() :].startswith("rescue · ")
    ]
    return events[-1:] == ["spawn"]


def grant(cwd: Path, change: str, executor: str) -> int:
    """Record one more round for a version halted at the cap, then start a run.

    With a run live, the grant goes with a rejoin request instead, and none while
    that version's rescue runs: `Run.hold` takes a grant then for the rescue's.
    Why: 0063-rejoin design D5; 0067-rescue design D3.
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
    live = _claim(runs / "active") == "live"
    if live and _rescuing(runs, change):
        raise Stop(
            2,
            f"grant: cannot run — {change} is at {stage} with its rescue running:"
            " grant once it ends",
        )
    if not live:
        preconditions(cwd, executor)
    grants = primary / ".minions" / "grants"
    grants.mkdir(parents=True, exist_ok=True)
    (grants / change).touch()
    if not live:
        return run(cwd, executor, True)
    _request(runs, change)
    print(f"grant: recorded — the live run takes {change} back")
    return 0


def approve_gate(cwd: Path, change: str, hashed: str) -> str:
    """Record the hash a gate check's halt named, as a person's yes to that diff.

    The record is the person's, in the home folder, where no worker writes. It runs
    no make: this process is outside the sandbox, and a branch's makefile is code a
    worker wrote. A hash no check reads approves nothing.
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

    A person's session alone: no worker can write the home folder, and the tracking
    ref is one a worker writes, so it writes only the sha the person names with
    `yes` after seeing it. Why: 0062-offline-origin design D6.
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
    # why: 0080-minions-layout design D4
    old = _old_files(primary)
    lines += [
        f"{version.change} · old layout — a run moves it"
        if version.change in old
        else f"{version.change} · {stage_of(primary, version)[0]}"
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
    return int(change.split("-")[0])


def report(cwd: Path) -> str:
    """Return the last run's close-out: its waits, each version, the halts, the end.

    A version that rejoined has a `rejoined` line after the halts before it, and one
    rescued a `rescued <sub-task> · <sha>` or `diagnosed <file>` line; a skipped
    request, which names no version, keeps its line as it stands.
    Why: 0067-rescue design D6.
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
        review = _change_dir(primary, change) / "review.md"
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
    rejoining = commands.add_parser("rejoin", help="the live run takes a version back")
    rejoining.add_argument("change_id", metavar="change-id", nargs="?")
    agenting = commands.add_parser("agent", help="one worker in the cwd")
    agenting.add_argument("--executor", required=True, choices=("claude", "codex"))
    agenting.add_argument("prompt")
    commands.add_parser("report", help="the last run's close-out lines")
    approving = commands.add_parser("approve-gate", help="the person's yes to a gate")
    approving.add_argument("change_id", metavar="change-id")
    approving.add_argument("--yes", required=True, metavar="hash")
    anchoring = commands.add_parser(
        "anchor", help="a person seeds the first offline base"
    )
    anchoring.add_argument("--yes", metavar="sha")
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
        elif args.command == "rejoin":
            print(rejoin(cwd, args.change_id))
        elif args.command == "agent":
            return agent(cwd, args.executor, args.prompt)
        elif args.command == "approve-gate":
            print(approve_gate(cwd, args.change_id, args.yes))
        elif args.command == "anchor":
            print(anchor(cwd, args.yes))
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
