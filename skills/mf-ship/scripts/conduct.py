# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Take every cut version to the default branch, one agent process per station.

    conduct.py status
    conduct.py check <stage> <change-id>
    conduct.py log --verify <run-log>
    conduct.py run --executor claude|codex [--detach]
    conduct.py agent --executor claude|codex <prompt>
    conduct.py report

Exit 0 done · 1 halt · 2 cannot run. Every stage and check is read from git and
the run directory, so a re-run derives them again.
Why: 0040-mf-ship design D2.
"""

import argparse
import itertools
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import tomllib
from dataclasses import dataclass
from pathlib import Path

TIMEOUT = 10800
STAMP = "%Y%m%d-%H%M%S"
GIT_TIMEOUT = 60
LOCK_SECONDS = 30
CHANGE_ID = re.compile(r"(\d+)-([a-z0-9-]+)")
PROGRESS = re.compile(r"^- \[([ x])\] (\d+) — (.*)$", re.MULTILINE)
RELEASE = re.compile(r"chore\(release\): (\S+)")
EVENT = re.compile(r"^\d\d:\d\d:\d\d · (\S+) · (\S+) — ")
EVENTS = ("start", "spawn", "finish", "check", "denied", "halt", "done")
HALTS = ("integrating", "released", "human", "converge-halted")
STATIONS = ("build", "converge", "integrate", "release")
ROLES = ("review", "security")
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
# never `--force-with-lease`, `-fu`, `git -C <dir> …` or a trailing flag.
FORCED = (
    *(("push", "--force"), ("push", "-f"), ("push", "+"), ("reset", "--hard")),
    *(("clean", "-"), ("branch", "-D"), ("tag", "-d"), ("worktree remove", "--force")),
    ("worktree remove", "-f"),
)
DENIALS = ("has been denied", "needs approval")
PROMPTS = {
    "build": "Run the mf-build skill for change {change}.",
    "converge": "Run the mf-converge skill for change {change}{tier}.",
    "integrate": "Run the mf-integrate skill.",
    "release": "Run the mf-release skill for change {change} with merge=yes.",
}
SHELL_RULES = (
    "Shell rules for this run: one command per Bash call; no `$(…)`, shell variables"
    " or loops — run the inner command first and use its output literally; use"
    " `git -C <dir>`, never `cd`; never retry a denied command in a rewritten form"
    " to get past the list."
)
PROBE = (
    "In this directory, write the word ok to probe.txt, commit it with the"
    " message probe, then run make gate."
)
SCRATCH_IDENTITY = (
    *("-c", "user.name=mf-ship", "-c", "user.email=mf-ship@example.invalid"),
    *("-c", "commit.gpgsign=false"),
)


class Stop(Exception):
    """End the command with `code`; the message is what it prints."""

    def __init__(self, code: int, message: str) -> None:
        """Keep the exit code beside the message."""
        super().__init__(message)
        self.code = code


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Return a finished git command run in `cwd`; a missing git stops with exit 2."""
    try:
        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_TIMEOUT,
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
    """Return the primary checkout of the repo holding `cwd`; outside one, exit 2."""
    if (common := _common_dir(cwd)) is None:
        raise Stop(2, "conduct: cannot run — not in a git repository")
    return common.parent


def _root(cwd: Path) -> Path:
    """Return the primary checkout of the repo holding `cwd`, or `cwd` outside one."""
    common = _common_dir(cwd)
    return common.parent if common else cwd.resolve()


def run_dir(cwd: Path) -> Path:
    """Return `.minions/` beside the primary checkout, or in `cwd` outside a repo."""
    return _root(cwd) / ".minions"


def _frontmatter(text: str, key: str) -> str | None:
    """Return a key's value in the text's leading `---` block.

    e.g. a findings file opening `verdict: clean` in its block, "verdict" → "clean"
    """
    if not text.startswith("---\n"):
        return None
    block = text[4:].split("\n---", 1)[0]
    found = re.search(rf"^{key}:\s*(\S+)", block, re.MULTILINE)
    return found[1] if found else None


def _agents_values(root: Path, key: str) -> list[str] | None:
    """Return the backticked values of `AGENTS.md`'s `**<key>:**` line, or None.

    e.g. "- **Ship tools:** `npm`, `pnpm`", "Ship tools" → ["npm", "pnpm"]
    """
    path = root / "AGENTS.md"
    if not path.is_file():
        return None
    found = re.search(rf"\*\*{key}:\*\*(.*)", path.read_text())
    return re.findall(r"`([^`]+)`", found[1]) if found else None


@dataclass(frozen=True)
class Version:
    """A cut version: its change, branch, declared version and worktree."""

    change: str
    branch: str
    version: str
    tree: Path | None

    @property
    def number(self) -> int:
        """Return the change id's number, the ship order."""
        return int(self.change.split("-")[0])

    @property
    def tag(self) -> str:
        """Return the tag the release makes.

        e.g. "v0.35" → "v0.35.0"; "v0.34.1" → "v0.34.1"
        """
        return self.version if self.version.count(".") == 2 else f"{self.version}.0"


def _worktrees(primary: Path) -> dict[str, Path]:
    """Map each checked-out branch to its worktree."""
    found: dict[str, Path] = {}
    path = None
    for line in _git(primary, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            path = Path(line.removeprefix("worktree ")).resolve()
        elif line.startswith("branch refs/heads/") and path:
            found[line.removeprefix("branch refs/heads/")] = path
    return found


def _change_on(primary: Path, branch: str) -> tuple[str, str] | None:
    """Return the change a branch holds and its version, or None.

    The one active change; after a release commit, the change it archived.
    """
    listing = _maybe(primary, "ls-tree", "--name-only", f"{branch}:openspec/changes")
    active = [name for name in (listing or "").split() if CHANGE_ID.fullmatch(name)]
    if len(active) == 1:
        change, folder = active[0], f"openspec/changes/{active[0]}"
    elif not active and RELEASE.fullmatch(_subject(primary, branch)):
        archive = "openspec/changes/archive"
        moved = _maybe(primary, "diff", "--name-only", f"{branch}~1", branch, archive)
        names = {path.split("/")[3] for path in (moved or "").split()}
        if len(names) != 1:
            return None
        change = names.pop()
        folder = f"{archive}/{change}"
    else:
        return None
    proposal = _show(primary, branch, f"{folder}/proposal.md") or ""
    version = _frontmatter(proposal, "version")
    return (change, version) if version else None


def open_versions(primary: Path) -> list[Version]:
    """Return the open versions in change-id order.

    Open is a `v*` branch the default branch lacks, in a linked worktree,
    holding one active change.
    """
    default = default_branch(primary)
    listing = _git(
        primary,
        *("branch", "--no-merged", default, "--list", "v*"),
        "--format=%(refname:short)",
    )
    trees = _worktrees(primary)
    found = []
    for branch in listing.split():
        tree = trees.get(branch)
        if tree is None or tree == primary.resolve():
            continue
        if (held := _change_on(primary, branch)) is not None:
            found.append(Version(held[0], branch, held[1], tree))
    return sorted(found, key=lambda version: version.number)


def find_version(primary: Path, change: str) -> Version | None:
    """Return the version of a change, open or merged, or None."""
    if not (match := CHANGE_ID.fullmatch(change)):
        return None
    slug = match[2].replace("-", "_")
    trees = _worktrees(primary)
    listing = _git(primary, "branch", "--list", "v*", "--format=%(refname:short)")
    for branch in listing.split():
        held = _change_on(primary, branch) if branch.endswith(f"_{slug}") else None
        if held and held[0] == change:
            return Version(change, branch, held[1], trees.get(branch))
    return None


def _progress(tree: Path, change: str) -> list[tuple[str, str, str]]:
    """Return the `## Progress` lines as (mark, number, title); none stops with 1."""
    tasks = tree / "openspec" / "changes" / change / "tasks.md"
    boxes = PROGRESS.findall(tasks.read_text()) if tasks.is_file() else []
    if not boxes:
        raise Stop(1, f"conduct: halt — {change}: tasks.md has no ## Progress list")
    return boxes


def _unticked(tree: Path, change: str) -> tuple[str, str] | None:
    """Return the first unticked phase's number and title, or None."""
    for mark, number, title in _progress(tree, change):
        if mark != "x":
            return number, title
    return None


def _converge_halt(runs: Path, change: str) -> str | None:
    """Return the newest converge run's first event when it is a halt, else None."""
    log = runs / "findings" / f"{change}_status_log.md"
    lines = log.read_text().splitlines() if log.is_file() else []
    heading = next(
        (i for i, line in enumerate(lines) if line.startswith("## Run")), None
    )
    if heading is None:
        return None
    first = next((line for line in lines[heading + 1 :] if line.strip()), "")
    return first.strip() if "· halt" in first else None


def _unjudged(runs: Path, tree: Path, change: str) -> str | None:
    """Return why converge is not clean at `HEAD`, or None when it is."""
    head = _git(tree, "rev-parse", "HEAD").strip()
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
            return f"{role}: judged {judged or 'no head'}, not HEAD"
    return None


def _merge_open(tree: Path) -> bool:
    """Return whether a merge is open in `tree`."""
    return _maybe(tree, "rev-parse", "-q", "--verify", "MERGE_HEAD") is not None


def _unmerged(tree: Path) -> bool:
    """Return whether an open merge leaves a path unmerged in `tree`."""
    return bool(_git(tree, "diff", "--name-only", "--diff-filter=U").strip())


def _dirty(tree: Path) -> bool:
    """Return whether `git status --porcelain` prints anything."""
    return bool(_git(tree, "status", "--porcelain").strip())


def stage_of(primary: Path, version: Version) -> tuple[str, str]:
    """Return a version's stage, read in its worktree, and why; the first match wins."""
    tree = version.tree
    if tree is None:
        raise Stop(2, f"conduct: cannot run — {version.branch} has no worktree")
    runs = primary / ".minions"
    change = version.change
    if _merge_open(tree):
        marks = runs / "integrate"
        if (marks / f"{change}.red").is_file():
            return "integrating", f"red gate: .minions/integrate/{change}.red"
        if (marks / f"{change}.md").is_file():
            return "integrating", f"semantic conflict: .minions/integrate/{change}.md"
        if _unmerged(tree):
            return "integrating", "interrupted: a merge is open with no note"
        return (
            "integrate",
            "a merge is open and staged, with no note: integrate resumes",
        )
    if _subject(tree) == f"chore(release): {version.tag}" and _tagged(
        primary, version.tag
    ):
        return (
            "released",
            f"{version.tag} is tagged; the release stopped before its merge",
        )
    if unticked := _unticked(tree, change):
        number, title = unticked
        if "**HUMAN" in title:
            return "human", f"phase {number} — {title}"
        return "build", f"phase {number} unticked"
    if halt := _converge_halt(runs, change):
        return "converge-halted", halt
    if why := _unjudged(runs, tree, change):
        return "converge", why
    default = default_branch(primary)
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
    if subject != f"chore(integrate): merge {default} into {version.branch}":
        return f"HEAD is not the integrate commit: {subject}"
    if not _ancestor(tree, default, "HEAD"):
        return f"{default} is not an ancestor of HEAD"
    return None


def _check_release(primary: Path, version: Version) -> str | None:
    """Return why the release check fails, or None."""
    default = default_branch(primary)
    if not _ancestor(primary, version.branch, default):
        return f"{default} does not contain {version.branch}"
    if not _tagged(primary, version.tag):
        return f"{version.tag} does not exist"
    if _pushed(primary, version.tag) is False:
        return f"{version.tag} is not on origin"
    return None


def _pushed(primary: Path, tag: str) -> bool | None:
    """Return whether origin holds the tag, or None when there is no origin."""
    if "origin" not in _git(primary, "remote").split():
        return None
    return bool((_maybe(primary, "ls-remote", "--tags", "origin", tag) or "").strip())


def check_probe(scratch: Path) -> str | None:
    """Return why the probe check fails, or None; the scratch gate leaves `.gated`."""
    held = _show(scratch, "HEAD", "probe.txt")
    if held is None:
        return "HEAD holds no probe.txt"
    if held.strip() != "ok":
        return f"probe.txt reads {held.strip()!r}"
    return None if (scratch / ".gated").is_file() else "make gate left no .gated"


def check(primary: Path, stage: str, version: Version) -> str | None:
    """Return why a station's check on disk fails, or None when it passes."""
    if stage == "release":
        return _check_release(primary, version)
    if version.tree is None:
        return f"{version.branch} has no worktree"
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
    last = ""
    for line in lines:
        match = EVENT.match(line)
        if not match or match[2] not in EVENTS:
            return f"unknown event: {line}"
        who, last = match[1], match[2]
        station = line[match.end() :].split(" · ")[0]
        if last == "spawn":
            spawned[who, station] = spawned.get((who, station), 0) + 1
        elif last == "finish" and spawned.get((who, station)):
            spawned[who, station] -= 1
    for (who, station), count in spawned.items():
        if count:
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


def _models(runs: Path, change: str, station: str) -> tuple[str | None, str | None]:
    """Return the station's model and effort from the cut's models file, or Nones.

    Integrate uses the `[release]` table.
    """
    table = _table(runs, change, "release" if station == "integrate" else station)
    model, effort = table.get("model"), table.get("effort")
    return (
        model if isinstance(model, str) else None,
        effort if isinstance(effort, str) else None,
    )


def _tier(runs: Path, change: str) -> str:
    """Return the converge prompt's tier clause, or "" when the cut set no tier.

    e.g. `tier = "high"` under `[converge]` → " with tier=high"
    """
    tier = _table(runs, change, "converge").get("tier")
    return f" with tier={tier}" if isinstance(tier, str) else ""


def edit_root(cwd: Path) -> Path:
    """Return the directory a worker may edit: `Worktrees:`, resolved, else `cwd`."""
    root = _root(cwd)
    values = _agents_values(root, "Worktrees")
    return (root / values[0]).resolve() if values else cwd.resolve()


def allowlist(cwd: Path, tree: Path) -> tuple[list[str], list[str]]:
    """Return the Claude worker's allowed and denied rules, editing inside `tree`."""
    extra = _agents_values(_root(cwd), "Ship tools") or []
    allowed = [
        *TOOLS,
        f"Edit(/{tree}/**)",
        *(f"Bash({command}:*)" for command in (*COMMANDS, *extra)),
    ]
    denied = [f"Bash({command}:*)" for command in DENIED]
    for sub, flag in FORCED:
        forms = (
            *(f"git {sub} {flag}", f"git {sub} * {flag}"),
            *(f"git * {sub} {flag}", f"git * {sub} * {flag}"),
        )
        denied += [f"Bash({form}*)" for form in forms]
    return allowed, denied


def argv(
    executor: str, prompt: str, cwd: Path, model: str | None, effort: str | None
) -> list[str]:
    """Return the worker's command line, the shell rules appended to the prompt.

    `MF_SHIP_AGENT` replaces the executor.
    """
    prompt = f"{prompt}\n\n{SHELL_RULES}"
    if agent := os.environ.get("MF_SHIP_AGENT"):
        return [*shlex.split(agent), prompt]
    if executor == "claude":
        tree = edit_root(cwd)
        allowed, denied = allowlist(cwd, tree)
        return [
            *("claude", "-p", prompt),
            *(("--model", model) if model else ()),
            *(("--effort", effort) if effort else ()),
            *("--output-format", "stream-json", "--verbose"),
            *("--add-dir", str(tree)),
            *("--allowedTools", *allowed, "--disallowedTools", *denied),
        ]
    common = _common_dir(cwd)
    roots = [str(run_dir(cwd)), *([str(common)] if common else []), str(edit_root(cwd))]
    return [
        *("codex", "exec"),
        *(("-m", model) if model else ()),
        *(("-c", f"model_reasoning_effort={effort}") if effort else ()),
        *("-s", "workspace-write"),
        *("-c", f"sandbox_workspace_write.writable_roots={json.dumps(roots)}"),
        *("-c", "sandbox_workspace_write.network_access=true"),
        *("-C", str(cwd), prompt),
    ]


def work(command: list[str], cwd: Path, out: Path) -> tuple[int, bool]:
    """Run one worker in its own process group, output to `out`.

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
        try:
            return worker.wait(timeout=TIMEOUT), False
        except subprocess.TimeoutExpired:
            os.killpg(worker.pid, signal.SIGKILL)
            return worker.wait(), True


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


def _executor_missing(executor: str) -> bool:
    """Return whether neither `MF_SHIP_AGENT` nor the executor's CLI is there."""
    return not os.environ.get("MF_SHIP_AGENT") and shutil.which(executor) is None


def preconditions(cwd: Path, executor: str) -> Path:
    """Return the primary checkout once every run precondition holds; else exit 2."""
    git_dir = _maybe(cwd, "rev-parse", "--path-format=absolute", "--git-dir")
    common = _common_dir(cwd)
    if git_dir is None or common is None or Path(git_dir.strip()).resolve() != common:
        raise Stop(2, "run: cannot run — the cwd is not the primary checkout")
    primary = common.parent
    default = default_branch(primary)
    if (branch := _git(primary, "branch", "--show-current").strip()) != default:
        raise Stop(2, f"run: cannot run — on {branch or 'no branch'}, not {default}")
    if _dirty(primary):
        raise Stop(2, "run: cannot run — the primary's tree is not clean")
    if not _agents_values(primary, "Worktrees"):
        raise Stop(2, "run: cannot run — AGENTS.md declares no **Worktrees:**")
    if _executor_missing(executor):
        raise Stop(2, f"run: cannot run — {executor} is not on PATH")
    if (primary / ".minions" / "runs" / "active").exists():
        raise Stop(2, "run: cannot run — a run is live: .minions/runs/active exists")
    return primary


class Run:
    """One ship run: the probe, then every open version to the default branch."""

    def __init__(self, primary: Path, executor: str) -> None:
        """Open the run log under the primary's run directory."""
        self.primary = primary
        self.executor = executor
        self.runs = primary / ".minions" / "runs"
        self.log = RunLog(self.runs, time.strftime(STAMP))
        self.halts: list[tuple[str, str]] = []
        self.released: list[str] = []
        self.guard = threading.Lock()

    def halt(self, who: str, reason: str) -> None:
        """Record a halt; no new worker starts after it."""
        with self.guard:
            self.halts.append((who, reason))

    def spawn(
        self,
        who: str,
        station: str,
        cwd: Path,
        prompt: str,
        models: tuple[str | None, str | None] = (None, None),
    ) -> list[str] | None:
        """Run one worker and log it and its denials.

        Return the denials, or None when a timeout halted the run.
        """
        model, effort = models
        self.log.event(who, "spawn", f"{station} · model {model or 'default'}")
        out = self.runs / self.log.stamp / f"{who}_{station}.log"
        started = time.monotonic()
        code, killed = work(argv(self.executor, prompt, cwd, model, effort), cwd, out)
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
            while not self.halts:
                stage, why = stage_of(self.primary, version)
                if stage in HALTS:
                    self.halt(version.change, f"{stage} — {why}")
                    return
                if stage in stop_at:
                    return
                cwd = self.primary if stage == "integrate" else version.tree
                runs = self.primary / ".minions"
                tier = _tier(runs, version.change) if stage == "converge" else ""
                prompt = PROMPTS[stage].format(change=version.change, tier=tier)
                if cwd is None:
                    self.halt(version.change, f"{version.branch} has no worktree")
                    return
                models = _models(runs, version.change, stage)
                denied = self.spawn(version.change, stage, cwd, prompt, models)
                if denied is None:
                    return
                reason = check(self.primary, stage, version)
                if not self.judge(version.change, stage, reason, denied):
                    return
                if stage == "release":
                    self.released.append(version.tag)
                    return
        except Stop as stop:
            self.halt(version.change, str(stop))

    def probe(self) -> None:
        """Prove a worker can edit, commit and gate in a scratch repo, or halt."""
        scratch = Path(tempfile.mkdtemp(prefix="mf-ship-probe-")).resolve()
        try:
            _git(scratch, "init", "-q", "-b", "main")
            (scratch / "Makefile").write_text("gate:\n\ttouch .gated\n")
            (scratch / ".gitignore").write_text(".gated\n")
            _git(scratch, "add", "Makefile", ".gitignore")
            _git(scratch, *SCRATCH_IDENTITY, "commit", "-q", "-m", "init")
            denied = self.spawn("run", "probe", scratch, PROBE)
            if denied is not None:
                self.judge("run", "probe", check_probe(scratch), denied)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)

    def ship(self) -> int:
        """Run the loop; return 0 when every version shipped, else 1."""
        versions = open_versions(self.primary)
        permissions = "allowlist" if self.executor == "claude" else "workspace-write"
        worker = " · worker MF_SHIP_AGENT" if os.environ.get("MF_SHIP_AGENT") else ""
        names = " ".join(version.change for version in versions) or "none"
        self.log.event(
            "run",
            "start",
            f"executor {self.executor} · permissions: {permissions}{worker}"
            f" · versions {names}",
        )
        if not versions:
            self.log.event("run", "done", "nothing to ship")
            return 0
        stages = {
            version.change: stage_of(self.primary, version) for version in versions
        }
        if all(stage in HALTS for stage, _ in stages.values()):
            for change, (stage, why) in stages.items():
                self.halt(change, f"{stage} — {why}")
        else:
            self.probe()
        if not self.halts:
            threads = [
                threading.Thread(
                    target=self.advance, args=(version, ("integrate", "release"))
                )
                for version in versions
                if stages[version.change][0] in ("build", "converge")
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
        for version in versions:
            self.advance(version, ())
        for who, reason in self.halts:
            self.log.event(who, "halt", reason)
        if self.halts:
            return 1
        self.log.event("run", "done", f"released {' '.join(self.released)}")
        return 0


def run(cwd: Path, executor: str, detach: bool) -> int:
    """Start the loop, claimed by `.minions/runs/active`; detached, return at once."""
    primary = preconditions(cwd, executor)
    runs = primary / ".minions" / "runs"
    runs.mkdir(parents=True, exist_ok=True)
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
    active = runs / "active"
    try:
        active.mkdir()
    except FileExistsError:
        raise Stop(
            2, "run: cannot run — a run is live: .minions/runs/active exists"
        ) from None
    try:
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
        active.rmdir()


def agent(cwd: Path, executor: str, prompt: str) -> int:
    """Run one worker in `cwd` under the run's permissions; return its exit code."""
    if _executor_missing(executor):
        raise Stop(2, f"agent: cannot run — {executor} is not on PATH")
    stamp = time.strftime(STAMP)
    out = run_dir(cwd) / "runs" / f"agent-{stamp}.log"
    code, killed = work(argv(executor, prompt, cwd, None, None), cwd, out)
    for denied in denials(out):
        print(f"agent: denied — {denied}")
    print(f"agent: exit {code}{' · timed out' if killed else ''} · {out}")
    return 1 if killed else code


def status(cwd: Path) -> str:
    """Return one line per open version: `<change-id> · <branch> · <stage>`."""
    primary = primary_of(cwd)
    versions = open_versions(primary)
    if not versions:
        return "status: none — no open version"
    return "\n".join(
        f"{version.change} · {version.branch} · {stage_of(primary, version)[0]}"
        for version in versions
    )


def _merge_commit(primary: Path, version: Version) -> str | None:
    """Return the default branch's merge of the version's tip, or None."""
    tip = _git(primary, "rev-parse", version.branch).strip()
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


def last_log(runs: Path) -> Path | None:
    """Return the newest run log in `runs`, or None.

    e.g. `20261029-163000.md`, `20261029-163000-2.md` → the second
    """
    logs = list(runs.glob("*.md"))
    if not logs:
        return None
    return max(logs, key=lambda log: (log.stem[:15], len(log.stem), log.stem))


def report(cwd: Path) -> str:
    """Return the last run's close-out: per version touched, then its last line."""
    primary = primary_of(cwd)
    runs = primary / ".minions"
    if (log := last_log(runs / "runs")) is None:
        return "report: none — no run yet"
    events = [
        found for line in log.read_text().splitlines() if (found := EVENT.match(line))
    ]
    touched = dict.fromkeys(found[1] for found in events if found[1] != "run")
    denied: dict[str, list[str]] = {}
    for found in events:
        if found[2] == "denied":
            call = found.string[found.end() :].split(" · ", 1)[-1]
            denied.setdefault(found[1], []).append(call)
    lines = [f"run · denied {', '.join(denied['run'])}"] if "run" in denied else []
    for change in sorted(touched, key=lambda name: int(name.split("-")[0])):
        version = find_version(primary, change)
        if version is None:
            lines.append(f"{change} · no version branch")
            continue
        tagged = _tagged(primary, version.tag)
        pushed = _pushed(primary, version.tag) if tagged else False
        review = runs / "findings" / f"{change}_review.md"
        round_ = _frontmatter(review.read_text(), "round") if review.is_file() else None
        page = runs / "metrics" / f"{change}.html"
        lines.append(
            " · ".join(
                [
                    change,
                    version.tag if tagged else "no tag",
                    f"merge {_merge_commit(primary, version) or 'none'}",
                    {None: "no origin", True: "pushed", False: "not pushed"}[pushed],
                    f"round {round_ or 'none'}",
                    f"cards {' '.join(_cards(runs / 'backlog.md', change)) or 'none'}",
                    f"denied {', '.join(denied.get(change, [])) or 'none'}",
                    f".minions/metrics/{change}.html"
                    if page.is_file()
                    else "metrics: none",
                ]
            )
        )
    lines.append(events[-1].string if events else f"{log.name}: no event")
    return "\n".join(lines)


def main(argv_: list[str] | None = None) -> int:
    """Run one command; return its exit code."""
    parser = argparse.ArgumentParser(
        prog="conduct.py",
        usage="conduct.py <command> [<args>]",
        description="Take every cut version to the default branch, unattended.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="one line per open version, with its stage")
    checking = commands.add_parser("check", help="exit 0 when disk proves the stage")
    checking.add_argument("stage", choices=(*STATIONS, "probe"))
    checking.add_argument("change_id", metavar="change-id")
    logging = commands.add_parser("log", help="exit 0 when a run log is complete")
    logging.add_argument("--verify", required=True, metavar="run-log")
    running = commands.add_parser("run", help="the loop")
    running.add_argument("--executor", required=True, choices=("claude", "codex"))
    running.add_argument("--detach", action="store_true")
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
        reason = check_probe(Path(target))
    else:
        primary = primary_of(cwd)
        if (version := find_version(primary, target)) is None:
            raise Stop(2, f"check: cannot run — no version branch holds {target}")
        reason = check(primary, stage, version)
    print(f"check: {stage} · {'pass' if reason is None else f'fail — {reason}'}")
    return 0 if reason is None else 1


if __name__ == "__main__":
    sys.exit(main())
