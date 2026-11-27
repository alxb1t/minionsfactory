# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Conduct converge: the preconditions, the freeze, the rounds, the debt and the report.

`conduct.py converge <change-id>` or a version's thread calls `converge(host, …)`.
Exit 0 done · 1 halted · 2 cannot run. Why: design D1, D3, D6; Steps: `SKILL.md`.
"""

import errno
import io
import os
import re
import runpy
import shlex
import subprocess
import sys
import time
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, NamedTuple, NoReturn, Protocol, TextIO

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import mflib.debtfile
import mflib.findings
import mflib.layout
import mflib.marks
import mflib.statefile
import mflib.statuslog

HERE = Path(__file__).resolve().parent
BUNDLE = runpy.run_path(str(HERE / "bundle.py"))
DEBT_MATCH = runpy.run_path(str(HERE / "debt_match.py"))
SKIP_STUB = runpy.run_path(str(HERE / "skip_stub.py"))
OPEN_CARDS = runpy.run_path(str(HERE / "open_cards.py"))
PLAN_CHECK = runpy.run_path(str(HERE / "plan_check.py"))
EVIDENCE = runpy.run_path(str(HERE / "evidence.py"))
GATE_INTEGRITY = runpy.run_path(str(HERE / "gate_integrity.py"))
OVERLAP = runpy.run_path(str(HERE / "overlap.py"))
INTEGRATE = runpy.run_path(str(HERE.parents[1] / "mf-integrate/scripts/integrate.py"))
ROLES = ("conformance", "adversarial")
CAP = 3
TIMEOUT_SECONDS = 600
SPAN = re.compile(r"(\w+)\.\.(\w+) · (\d+) commits? · (\d+) files?")
HALTED = re.compile(r" · head (\w+)$")
NO_COMMAND = ("is up to date", "Nothing to be done")
PROGRESS = re.compile(r"^- \[([ x])\] (\d+) — ", re.MULTILINE)
PLANNED = re.compile(r"(\d+\.\d+) — ")
SUBTASK = re.compile(r"^  (\d+(?:\.\d+)+)(?: · uncommitted)?$", re.MULTILINE)
REFERENCES = HERE.parent / "references"
# The `## Prompt` placeholders. Why: design D2.
PLACEHOLDERS = (
    *("change", "role", "round", "base", "range", "scope", "findings", "patch"),
    *("bundle", "debt_cards", "open", "ids", "models", "mode", "evidence"),
    "attribution",
)
PROMPT = re.compile(r"^## Prompt\n\n```text\n(.*?)^```$", re.MULTILINE | re.DOTALL)
PLACEHOLDER = re.compile(r"\{(\w+)\}")
FALLBACK = "fallback: codex usage limit"
FAILED = "fallback: codex failed"
NO_OPEN_CARD = "verdict is changes-requested with no open card"
CLEAN_OPEN = "verdict is clean beside a blocking card not closed"
REWRITE = (
    "role: {role}\nchange: {change}\nround: {round}\n\n"
    "Your findings file {findings} breaks the findings file contract of"
    " `references/worker.md` of the installed `mf-converge` skill: {why}.\n"
    "Rewrite that file to the contract. Keep its verdict, each card's id, grade,"
    " fields and Status; judge nothing anew. Edit no other file.\n"
)
# why: 0157-ship-speed design D6
REWRITE_CLOSE = (
    "role: {role}\nchange: {change}\nround: {round}\n\n"
    "Your findings file {findings} breaks the findings file contract of"
    " `references/worker.md` of the installed `mf-converge` skill: {why}.\n"
    "Set what you meant: the first word of that card's Status line, `verified` or"
    " `accepted` when it is closed, or the file's verdict, `changes-requested`, when"
    " it is not. Keep each other card's id, grade, fields and Status. Edit no other"
    " file.\n"
)
# The debt lock's wait, in seconds. Why: design D5.
LOCK_WAIT = 600
COMMAND = re.compile(r"`([^`]+)`")
REPEAT = re.compile(r"repeat of `?([\w·]+)")
NOTE = re.compile(r"^Fix note \(\d{4}-\d\d-\d\d, ([^)]+)\):")
DECISION = re.compile(r"^### (D\d+)\b")
PLAN_TEXT = "Plan-text"


class Halt(Exception):
    """End the run with a `halt` event naming the reason, and exit 1."""


class Cannot(Exception):
    """End the run with exit 2: what it needs to run is missing."""


class Freeze(NamedTuple):
    """A frozen range: its ends and the counts converge stamps into a findings file."""

    base: str
    head: str
    commits: int
    files: int


class Checked(Protocol):
    """What `host.checker` returns of one checker's run.

    Why: design D4.
    """

    @property
    def code(self) -> int:
        """Return the worker's exit."""

    @property
    def killed(self) -> bool:
        """Return whether its timeout killed it."""

    @property
    def models(self) -> tuple[str, str | None, str | None]:
        """Return the executor, model and effort it ran on."""

    @property
    def limit(self) -> str:
        """Return the usage limit that stopped it, or ""."""

    @property
    def fallback(self) -> bool | str:
        """Return True for a Codex limit, a text for a Codex failure, else False.

        Why: 0145-halts-alone design D4.
        """

    @property
    def tokens(self) -> int | None:
        """Return its tokens, None when its log names none."""


class Host(Protocol):
    """What `converge` is handed: `conduct.py`'s `Run`, or a test's fake.

    Why: design D1.
    """

    primary: Path

    def trees(self) -> list[Path]:
        """Return the trees a sandboxed command may write."""

    def sandboxed(
        self,
        argv: list[str],
        cwd: Path,
        trees: list[Path],
        out: TextIO | None = None,
        timeout: float | None = None,
    ) -> int:
        """Run `argv` under the OS sandbox, ended after `timeout` s; return its exit."""

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
        """Run one checker on `table`'s models; return what it did."""

    def lacks(self, who: str, station: str) -> list[str]:
        """Return each tool the station's log asked for and its station lacks."""

    def worker(
        self,
        who: str,
        station: str,
        cwd: Path,
        prompt: str,
        models: tuple[str, str | None, str | None],
        timeout: float | None = None,
    ) -> tuple[int, bool, Path, list[str]]:
        """Run one worker; return its exit, whether it was killed, its log, denials."""

    def fix(
        self,
        change: str,
        station: str,
        cwd: Path,
        prompt: str,
        models: tuple[str, str | None, str | None],
        deadline: float,
    ) -> Checked:
        """Run the Codex fixer; return what it did."""

    def logged(self, change: str, event: str, detail: str) -> None:
        """Write one run-log line: `<event> — <detail>` for the change.

        Why: 0148-run-fields design D4.
        """


class SendBack(Exception):
    """Step 7's plan check failed: its subjects go back to the fixer, no round."""

    def __init__(self, subjects: list[str]) -> None:
        """Hold the subjects the plan check named, e.g. ["2.3", "a.py:4"]."""
        super().__init__(f"plan check: {', '.join(subjects)}")
        self.subjects = subjects


class Verdict(NamedTuple):
    """A findings file as converge reads it: its fields, its cards and its faults.

    `malformed` and `unclean` each say why, or are None. Why: design D2.
    """

    role: str
    verdict: str = ""
    head: str = ""
    round: int = 0
    open_blocking: int = 0
    stub: bool = False
    inconclusive: tuple[str, ...] = ()
    cards: tuple[mflib.findings.Card, ...] = ()
    malformed: str | None = None
    unclean: str | None = None


@dataclass
class Context:
    """One converge run: the host, the change, its worktree, workers and round."""

    host: Host
    change: str
    tree: Path
    workers: dict[str, Any]
    deadline: float
    round: int = 1
    mark: str | None = None
    base: str = ""
    cap: int = CAP
    picked: list[str] = field(default_factory=list)
    sent: set[str] = field(default_factory=set)
    stations: dict[str, tuple[str, str | None]] = field(default_factory=dict)

    @property
    def folder(self) -> Path:
        """Return the change's folder in the run directory."""
        return mflib.layout.change_dir(Path(self.host.primary), self.change)

    @property
    def log(self) -> Path:
        """Return the status log."""
        return mflib.layout.status_log(Path(self.host.primary), self.change)


def git(tree: Path, *args: str) -> str:
    """Return git's output for `args` in `tree`, or halt naming the command."""
    done = subprocess.run(
        ["git", *args],
        cwd=tree,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
    )
    if done.returncode != 0:
        raise Halt(f"git {args[0]} failed: {done.stderr.strip()}")
    return done.stdout


def _plural(count: int, noun: str) -> str:
    """Return the count and its noun.

    e.g. 1, "commit" → "1 commit"; 2, "file" → "2 files"
    """
    return f"{count} {noun}{'' if count == 1 else 's'}"


@contextmanager
def _change_folder(context: Context) -> Iterator[int]:
    """Yield a descriptor on the change's folder, made, through no link; or `Cannot`.

    Why: card 0109·S1; 0136-status-log design D7.
    """
    parts = (mflib.layout.MINIONS, mflib.layout.CHANGES, context.change)
    try:
        fd = mflib.statefile.folder(Path(context.host.primary), *parts)
    except OSError:
        raise Cannot(
            f"converge: cannot run — {context.log} cannot be stamped"
        ) from None
    try:
        yield fd
    finally:
        os.close(fd)


def stamp(context: Context, *events: str) -> None:
    """Write `events` of this round to the status log, the last given on top."""
    lines = [f"round {context.round} · {event}" for event in events]
    with _change_folder(context) as fd:
        if mflib.statuslog.command(context.log, lines, None, None, fd) != 0:
            raise Cannot(f"converge: cannot run — {context.log} cannot be stamped")


def open_run(context: Context, mark: str | None = None) -> None:
    """Open a new run in the status log, creating the log with its title if missing."""
    with _change_folder(context) as fd:
        if mflib.statuslog.open_run(context.log, context.change, mark, fd) != 0:
            raise Cannot(f"converge: cannot run — {context.log} cannot be stamped")


def sandboxed(context: Context, argv: list[str], out: TextIO | None = None) -> int:
    """Run `argv` in the worktree under the host's sandbox; return its exit.

    Its output goes to `out`, else to the round's `commands-r<N>.log`; it ends at
    converge's deadline. The sandbox's code 2 is `Cannot`. Why: design D1, D6.
    """
    trees = context.host.trees()
    limit = remaining(context)
    try:
        if out is not None:
            return context.host.sandboxed(argv, context.tree, trees, out, limit)
        with commands(context) as file:
            file.write(f"$ {shlex.join(argv)}\n")
            file.flush()
            return context.host.sandboxed(argv, context.tree, trees, file, limit)
    except Exception as error:
        if getattr(error, "code", None) == 2:
            raise Cannot(str(error)) from error
        raise


def commands(context: Context) -> TextIO:
    """Open the round's `commands-r<N>.log` to append, refusing a link."""
    path = context.folder / f"commands-r{context.round}.log"
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW
    try:
        return os.fdopen(os.open(path, flags, 0o644), "a")
    except OSError as error:
        raise Halt(f"{path.name} cannot be opened: {error.strerror}") from error


def script(name: str, *args: str) -> list[str]:
    """Return the argv that runs a converge script by the conductor's Python."""
    return [sys.executable, str(HERE / name), *args]


def preconditions(context: Context) -> str:
    """Check Step 1's preconditions, halting on the first that fails; return the base.

    The tree is clean, every phase ticked, the range not empty, the gate a command
    and green, and it changes only as the cut planned. Why: design D3.
    """
    tree = context.tree
    if dirty := git(tree, "status", "--porcelain").splitlines():
        raise Halt(f"the tree is dirty: {', '.join(line[3:] for line in dirty)}")
    tasks = tree / "openspec" / "changes" / context.change / "tasks.md"
    try:
        boxes = PROGRESS.findall(tasks.read_text())
    except OSError as error:
        raise Halt(f"tasks.md cannot be read: {error.strerror}") from error
    if not boxes:
        raise Halt("tasks.md has no ## Progress list")
    if open_box := next((n for box, n in boxes if box == " "), None):
        raise Halt(f"phase {open_box} of tasks.md is unticked: mf-build owns it")
    base = base_of(context)
    if base == head(context):
        raise Halt("the range is empty: base is HEAD")
    context.base = base
    dry = _captured(context, ["make", "-n", "gate"])
    if dry[0] != 0 or all(
        not line.strip() or any(word in line for word in NO_COMMAND)
        for line in dry[1].splitlines()
    ):
        raise Halt("the root Makefile's gate runs no command")
    gated(context, "before round 1")
    return base


def gated(context: Context, when: str) -> None:
    """Run the gate, then `gate_check.py`, halting on either.

    Why: design D6.
    """
    if code := gate_line(context)[0]:
        raise Halt(f"the gate is red {when}: gate_run.py exit {code}")
    argv = script("gate_check.py", "--change", context.change, "--base", context.base)
    code, printed = _captured(context, argv)
    said = printed.splitlines()
    if code == 1 and any(line.startswith("verify: halt") for line in said):
        raise Halt(f"verify: halt — {', '.join(SUBTASK.findall(printed))}")
    if code != 0:
        lines = (line.strip() for line in printed.splitlines())
        raise Halt(f"gate check: {' · '.join(line for line in lines if line)}")


def gate_line(context: Context, keep: bool = False) -> tuple[int, str]:
    """Run the gate, log its result and seconds through the host; return exit, output.

    `keep` runs it through `_captured`, so its output is returned and kept.
    Why: 0148-run-fields design D4.
    """
    argv = script("gate_run.py")
    start = time.monotonic()
    code, printed = _captured(context, argv) if keep else (sandboxed(context, argv), "")
    result = "fail — red" if code else "pass"
    seconds = round(time.monotonic() - start)
    context.host.logged(context.change, "check", f"gate · {result} · {seconds}s")
    return code, printed


def head(context: Context) -> str:
    """Return the worktree's `HEAD` sha."""
    return git(context.tree, "rev-parse", "HEAD").strip()


def _captured(context: Context, argv: list[str]) -> tuple[int, str]:
    """Run `argv` sandboxed; return its exit and its output, also kept in the log."""
    buffer = io.StringIO()
    code = sandboxed(context, argv, buffer)
    with commands(context) as file:
        file.write(f"$ {shlex.join(argv)}\n{buffer.getvalue()}")
    return code, buffer.getvalue()


def _read(path: Path) -> str:
    """Return a file's text, or nothing when it is missing or a link."""
    text = ""
    with suppress(OSError):
        text = _text(path) or ""
    return text


def _plan_output(context: Context, head: str) -> str:
    """Return the plan check's output, the close's own when `build.done` names `head`.

    The close's lines count only from this freeze's base. Otherwise a run's.
    Why: 0144-gate-outside design D7.
    """
    primary = Path(context.host.primary)
    kept = mflib.marks.plan_check_text(primary, context.change)
    done = mflib.marks.done_head(primary, context.change)
    based, _, lines = (kept or "").partition("\n")
    if done == head and based == f"base: {context.base}":
        return lines
    plan = script("plan_check.py", "--change", context.change, "--base", context.base)
    return _captured(context, plan)[1]


def _evidence(context: Context, base: str, head: str, diff: str) -> None:
    """Write `evidence.md` for a frozen patch: facts tools found, never a verdict.

    Each command runs through `_captured`, and its exit halts nothing.
    Why: 0110-gate-hardening design D6.
    """
    names = EVIDENCE["candidates"](diff)
    checked = _plan_output(context, head)
    grep = ["git", "grep", "-n", "-w", "-F", *(a for n in names for a in ("-e", n))]
    found = _captured(context, grep)[1] if names else ""
    sections = {
        "Gate integrity": GATE_INTEGRITY["lines"](diff),
        "Plan check": [line.rstrip() for line in checked.splitlines() if line.strip()],
        "Stale-claim candidates": EVIDENCE["stale"](
            names, found, EVIDENCE["touched"](diff)
        ),
        "Test cost": EVIDENCE["test_cost"](
            diff,
            _read(context.tree / ".minions" / "test-report.xml"),
            _read(context.tree / "openspec" / "changes" / context.change / "design.md"),
        ),
    }
    text = EVIDENCE["render"](context.change, base, head, sections)
    try:
        BUNDLE["write"](context.folder / "evidence.md", text)
    except BUNDLE["Stop"] as stop:
        raise Halt(f"evidence: cannot write — {stop}") from stop


def freeze(
    context: Context, base: str, head: str, scope: tuple[str, int, int] | None = None
) -> Freeze:
    """Write the patch, bundle, cards and evidence of `base..head`; return its counts.

    A catch-up's `scope` is its patch, commits and files. A non-zero exit of
    `debt_match.py` halts. Writes `freeze`. Why: design D3, D5; 0139-debt design D5.
    """
    tree, folder = context.tree, context.folder
    folder.mkdir(parents=True, exist_ok=True)
    patch = folder / "diff.patch"
    diff = git(tree, "diff", "--binary", base, head) if scope is None else scope[0]
    try:
        BUNDLE["write"](patch, diff)
    except BUNDLE["Stop"] as stop:
        raise Halt(f"the patch cannot be written — {stop}") from stop
    try:
        text, _, _ = BUNDLE["bundle"](context.change, tree)
        BUNDLE["write"](folder / "bundle.md", text)
    except BUNDLE["Stop"] as stop:
        raise Halt(f"bundle: cannot bundle — {stop}") from stop
    primary = Path(context.host.primary)
    debt = mflib.layout.debt_file(primary)
    old = mflib.layout.backlog_file(primary)
    debt = old if not os.path.lexists(debt) and os.path.lexists(old) else debt
    cards = folder / "debt-cards.md"
    if code := DEBT_MATCH["main"]([str(debt), str(patch), str(cards)]):
        raise Halt(f"debt_match.py exited {code} — the debt cannot be matched")
    _evidence(context, base, head, diff)
    commits, files = scope[1:] if scope else counts(context, base, head)[:2]
    shown = f"{_plural(commits, 'commit')} · {_plural(files, 'file')}"
    stamp(context, f"freeze — {base[:7]}..{head[:7]} · {shown}")
    return Freeze(base, head, commits, files)


def counts(context: Context, base: str, head: str) -> tuple[int, int, str]:
    """Return the range's commits and files, and them as the status log shows them.

    e.g. "3 commits · 1 file"
    """
    commits = int(git(context.tree, "rev-list", "--count", f"{base}..{head}"))
    files = len(git(context.tree, "diff", "--name-only", base, head).splitlines())
    return commits, files, f"{_plural(commits, 'commit')} · {_plural(files, 'file')}"


def prompt(reference: str, **values: object) -> str:
    """Return the reference's `## Prompt` block with each placeholder filled.

    A name outside `PLACEHOLDERS`, or a placeholder given no value, raises ValueError.
    e.g. "verify.md", role="conformance", … → "role: conformance", "change: …", …
    """
    if unknown := sorted(set(values) - set(PLACEHOLDERS)):
        raise ValueError(f"prompt: unknown placeholder: {', '.join(unknown)}")
    found = PROMPT.search((REFERENCES / reference).read_text())
    if found is None:
        raise ValueError(f"prompt: {reference} has no ## Prompt block")
    template = found[1]
    for name in dict.fromkeys(PLACEHOLDER.findall(template)):
        if name not in PLACEHOLDERS:
            raise ValueError(f"prompt: {reference}: {{{name}}} is no placeholder")
        if name not in values:
            raise ValueError(f"prompt: {reference}: {name} is not filled")
    for name, value in values.items():
        template = template.replace(f"{{{name}}}", str(value))
    return template


def _text(path: Path) -> str | None:
    """Return a file's text through one descriptor that refuses a link; None if none.

    A link or a file that is no regular file raises OSError.
    """
    try:
        return mflib.statefile.read(path)
    except FileNotFoundError:
        return None


def read_findings(path: Path, role: str) -> Verdict | None:
    """Return a findings file read by its fields; None when missing.

    Not clean: conformance's passes short. Its counts are converge's own stamp.
    Why: design D2; 0151-stamps design D4; `references/worker.md`.
    """
    name = path.name
    try:
        text = mflib.findings.read(path)
    except OSError as error:
        why = "it is a link" if error.errno == errno.ELOOP else error.strerror
        return Verdict(role, malformed=f"{name} is malformed: {why}")
    if text is None:
        return None
    front, body = mflib.findings.front(text)
    stub = front.get("mode") == "skipped"
    cards = mflib.findings.cards(body, role)
    fault = mflib.findings.fault(front, role, stub) or mflib.findings.malformed(
        body, role
    )
    unmarked = (card for card in cards if card.word("Amend") not in ("yes", "no"))
    if fault is None and (card := next(unmarked, None)):
        fault = f"card {card.id} has no Amend line"
    if fault is not None:
        return Verdict(role, malformed=f"{name} is malformed: {fault}")
    no_open = (
        not stub
        and front["verdict"] == "changes-requested"
        and all(card.status in ("verified", "accepted") for card in cards)
    )
    verdict = Verdict(
        role,
        front["verdict"],
        front["head"],
        int(front["round"]),
        int(front["open_blocking"]),
        stub,
        () if stub else mflib.findings.listed(front["inconclusive"]),
        tuple(cards),
    )
    if stub:
        return verdict
    if role == "conformance":
        passes = set(mflib.findings.listed(front["passes"]))
        lacking = [
            needed for needed in ("stale-claim", "test-cost") if needed not in passes
        ]
        if not passes & {"coverage-trace", "no-removed-test"}:
            lacking.append("coverage-trace or no-removed-test")
        if lacking:
            why = f"its passes field lacks {', '.join(lacking)}"
            return verdict._replace(unclean=f"{path.name} is not clean: {why}")
    if no_open:
        # why: passes are judged first, so a conformance file whose passes ran short
        # is never rewritten clean
        return Verdict(role, malformed=f"{name} is malformed: {NO_OPEN_CARD}")
    shut = verdict.verdict == "clean" and verdict.open_blocking == 0
    if shut and (card := next(iter(blockers({role: verdict})), None)):
        why = f"{CLEAN_OPEN}, card {card.id} {card.status or 'unmarked'}"
        return Verdict(role, malformed=f"{name} is malformed: {why}")
    return verdict


def read_verdicts(
    context: Context, checked: dict[str, Checked]
) -> dict[str, Verdict | None]:
    """Read each role's findings file; write one `verdicts` line per role `checked`.

    `checked` holds what `host.checker` returned for each role it ran; a stub, and a
    file missing or malformed, gets no line. Why: design D2, D3.
    """
    read = {role: read_findings(context.folder / f"{role}.md", role) for role in ROLES}
    lines = []
    for role, result in checked.items():
        verdict = read[role]
        if verdict is None or verdict.malformed is not None:
            continue
        lines.append(
            f"verdicts — {role} {verdict.verdict} · open_blocking"
            f" {verdict.open_blocking} · {_spent(result)}"
        )
    if lines:
        stamp(context, *lines)
    return read


def _spent(result: Checked) -> str:
    """Return a checker's executor, model, effort and tokens, as the log shows them.

    e.g. "executor claude · model default · effort high · tokens 1200"
    """
    executor, model, effort = result.models
    tokens = "unavailable" if result.tokens is None else result.tokens
    spent = (
        f"executor {executor} · model {model or 'default'}"
        f" · effort {effort or 'default'} · tokens {tokens}"
    )
    if isinstance(result.fallback, str):
        return f"{spent} · {FAILED}"
    return spent + (f" · {FALLBACK}" if result.fallback else "")


def held(
    context: Context, read: dict[str, Verdict | None], frozen: Freeze
) -> dict[str, Verdict]:
    """Return each role's verdict; a malformed file gets one rewrite worker first.

    A file missing halts; an unblocked `changes-requested` is written `clean`.
    Why: design D5; 0141 D11.
    """
    kept: dict[str, Verdict] = {}
    for role in ROLES:
        verdict = read[role]
        if verdict is not None and verdict.malformed is not None:
            verdict = rewrite(context, role, frozen, verdict.malformed)
        if verdict is None:
            raise Halt(f"{role}.md is missing: its checker left no findings file")
        if verdict.unclean is not None:
            raise Halt(verdict.unclean)
        if verdict.verdict == "changes-requested" and not blockers({role: verdict}):
            cleared(context, role)
            verdict = verdict._replace(verdict="clean", open_blocking=0)
        kept[role] = verdict
    return kept


def cleared(context: Context, role: str) -> None:
    """Write `verdict: clean` and `open_blocking: 0` into a role's findings file."""
    path = context.folder / f"{role}.md"
    keys = {"verdict": "clean", "open_blocking": 0}
    BUNDLE["write"](path, mflib.findings.keyed(mflib.findings.read(path) or "", keys))


def verdicts(
    context: Context, frozen: Freeze, checked: dict[str, Checked]
) -> dict[str, Verdict]:
    """Read the verdicts under Step 5's table, halting on a file it refuses."""
    return held(context, read_verdicts(context, checked), frozen)


def rewrite(context: Context, role: str, frozen: Freeze, why: str) -> Verdict | None:
    """Run one rewrite worker on `role`'s malformed file; return the file read again.

    It repeats the role's last station. Still malformed, the role reads clean with no
    card and the debt cards the file; after `CLEAN_OPEN` it halts: 0157 design D6.
    """
    station, effort = context.stations.get(
        role, (f"converge-{role}-r{context.round}", None)
    )
    path = context.folder / f"{role}.md"
    stamp(context, f"fan-out — rewrite — {role}: {why}")
    closing = CLEAN_OPEN in why
    told = (REWRITE_CLOSE if closing else REWRITE).format(
        role=role, change=context.change, round=context.round, findings=path, why=why
    )
    seconds = remaining(context)
    result = run_checkers(context, {role: (station, role, told)}, effort)[role]
    fault = failure(station, seconds, result.code, result.killed, result.limit)
    if fault and (result.killed or result.limit):
        raise Halt(fault)
    counted(context, frozen, [role], pickup="-pickup-" in station)
    again = read_findings(path, role)
    if again is not None and again.malformed is not None:
        if closing:
            first = why.partition(f"{CLEAN_OPEN}, ")[2]
            now = again.malformed.partition(": ")[2]
            raise Halt(f"{role}: rewrite left {path.name} malformed — {first}; {now}")
        if again.malformed.endswith(NO_OPEN_CARD):
            cleared(context, role)
        return Verdict(role, "clean", head(context), context.round)
    return again


def converge(
    host: Host,
    change: str,
    tree: Path,
    *,
    workers: dict[str, Any],
    grant: bool = False,
    deadline: float,
) -> int:
    """Conduct one converge run of `change` in its worktree `tree`; return the exit.

    0 done · 1 halted, its `halt` event written · 2 cannot run.
    """
    context = Context(host, change, Path(tree), workers, deadline)
    if old := mflib.layout.old_layout(Path(host.primary), change):
        print(f"converge: halt — {old} is at an old path: /mf-ship's run moves it")
        return 1
    try:
        return resume(context, grant)
    except Cannot as cannot:
        print(cannot)
        # why: a status log that cannot be stamped takes no halt either; D1's exit 2
        with suppress(Cannot):
            halt(context, str(cannot))
        return 2
    except Halt as halted:
        halt(context, str(halted))
        print(f"converge: halt — {halted}")
        return 1


def latest(context: Context) -> mflib.statuslog.Run:
    """Return the status log's newest run; no log, or no run, is one of no event."""
    log = context.log
    text = mflib.statuslog.read(log) if os.path.lexists(log) else ""
    return mflib.statuslog.latest(text)


def resume(context: Context, granting: bool) -> int:
    """Go on with the newest run, or open the run this invocation is; return the exit.

    An unended run goes on; else a grant, an answered halt's amend round, a catch-up
    round, or a new run. Why: design D3.
    """
    run = latest(context)
    top = run.events[0] if run.events else None
    if top is not None and top.name not in ("halt", "done"):
        return go_on(context, run)
    if (
        top is not None
        and top.name == "halt"
        and mflib.statuslog.names_lock(top.detail)
    ):
        return unlocked(context, run)
    if granting:
        begin(context, "grant")
        return grant(context)
    if top is not None and top.name == "halt" and (judged := answered(context, run)):
        begin(context, "amend")
        return catch_up(context, judged)
    if judged := behind(context):
        begin(context, "catch-up")
        return catch_up(context, judged)
    if top is not None and top.name == "halt" and unanswered(context, run):
        # why: the cap's halt stands on top; `statuslog.py` takes no event after it
        print(f"converge: halt — {HALTED.sub('', top.detail)}")
        return 1
    begin(context, None)
    return fresh(context)


def unlocked(context: Context, run: mflib.statuslog.Run) -> int:
    """Go on at Step 9 with a run the debt lock halted, both files clean at `HEAD`.

    Else halt, naming the file. Why: design D3, D5.
    """
    context.mark, context.round = run.mark, run.events[0].round
    now = head(context)
    files = {verdict.role: verdict for verdict in _files(context)}
    for role in ROLES:
        verdict = files.get(role)
        if verdict is None or verdict.verdict != "clean" or verdict.head != now:
            raise Halt(f"{role}.md is not clean at HEAD: the debt write cannot go on")
    return finish(context)


def begin(context: Context, mark: str | None) -> None:
    """Open a run marked `mark`, then refuse a plan no converge can run.

    Why: design D3; D75.
    """
    open_run(context, mark)
    context.mark = mark
    if not dispatched(context):
        raise Halt("both checkers are skipped: a plan that skips both runs no converge")
    if context.workers.get("shadow") and len(dispatched(context)) < len(ROLES):
        raise Halt("a shadow round beside a skipped checker: the plan cannot run both")


def fresh(context: Context) -> int:
    """Run Steps 1 to 3 over the whole change, then its rounds; return the exit."""
    base = preconditions(context)
    now = head(context)
    stamp(
        context,
        f"start — base {base[:7]} · head {now[:7]} · {counts(context, base, now)[2]}",
    )
    frozen = freeze(context, base, now)
    shadowed = bool(context.workers.get("shadow"))
    return rounds(context, frozen, judge(context, frozen, shadowed=shadowed))


def judge(
    context: Context, frozen: Freeze, *, shadowed: bool = False
) -> dict[str, Verdict]:
    """Stub the skipped roles, run the round's checkers and read their verdicts.

    Round 1's shadow runs once its `verdicts` lines are written, before they decide.
    Why: design D3.
    """
    stubs(context)
    read = read_verdicts(context, dispatch(context, frozen))
    if shadowed:
        shadow(context, frozen)
    return held(context, read, frozen)


def _files(context: Context) -> list[Verdict]:
    """Return the conformance and adversarial files that read, by their fields."""
    read = (read_findings(context.folder / f"{r}.md", r) for r in ROLES)
    return [verdict for verdict in read if verdict and verdict.malformed is None]


def blockers(read: dict[str, Verdict]) -> list[mflib.findings.Card]:
    """Return each blocking card neither `verified` nor `accepted`, file by file."""
    return [
        card
        for verdict in read.values()
        for card in verdict.cards
        if card.blocking and card.status not in ("verified", "accepted")
    ]


def converged(read: dict[str, Verdict]) -> bool:
    """Return whether every file says `clean` and no blocking card is left."""
    clean = all(verdict.verdict == "clean" for verdict in read.values())
    return clean and not blockers(read)


def pick(read: dict[str, Verdict]) -> list[mflib.findings.Card]:
    """Return Step 8's pick: each open small card, and each open `drift` card."""
    return [
        card
        for verdict in read.values()
        for card in verdict.cards
        if card.status == "open"
        and not card.blocking
        and (card.small or card.severity == "drift")
    ]


def rounds(context: Context, frozen: Freeze, read: dict[str, Verdict]) -> int:
    """Run Steps 5 to 8 from a round's verdicts to a clean round or the cap.

    Round 1 of a run with no mark takes the pickup with its blockers. A clean round
    goes to Step 8, or to Step 9 in a marked run. Why: design D3; D71, D74.
    """
    while not converged(read):
        ids = [card.id for card in blockers(read)]
        if context.round >= context.cap:
            cap(context, read)
        if context.round == 1 and context.mark is None and not context.picked:
            context.picked = [card.id for card in pick(read)]
            if context.picked:
                stamp(context, f"pickup — {', '.join(context.picked)} · with the fix")
                ids += context.picked
        frozen, read = again(context, frozen, ids)
    if context.mark is not None:
        return finish(context)
    return pickup(context, frozen, read)


def cap(context: Context, read: dict[str, Verdict]) -> NoReturn:
    """Halt `cap reached`, naming the blockers, the security ones and the pickup.

    Every findings file stays as it stands. Why: design D3; D56.
    """
    left = blockers(read)
    reason = f"cap reached, {', '.join(card.id for card in left)} open"
    if security := [card.id for card in left if card.security]:
        reason += f" · security {', '.join(security)}"
    if context.picked:
        reason += f" · pickup {', '.join(context.picked)}"
    raise Halt(reason)


def again(
    context: Context, judged: Freeze, ids: list[str], note: str = ""
) -> tuple[Freeze, dict[str, Verdict]]:
    """Send `ids` to the fixer, then run Step 7 over its fix; return the round read."""
    return step7(context, judged, fix(context, judged, ", ".join(ids), note))


def step7(
    context: Context, judged: Freeze, frozen: Freeze, *, judging: bool = False
) -> tuple[Freeze, dict[str, Verdict]]:
    """Run Step 7 over `frozen`, sending each plan-check failure back to the fixer.

    A catch-up's judge round, `judging`, re-scopes after such a fix.
    """
    while True:
        try:
            return frozen, verify(context, frozen, judging=judging)
        except SendBack as back:
            frozen = fix(context, judged, str(back))
            if judging:
                frozen = scoped(context, judged.head, select(context, judged.head))


def remaining(context: Context) -> float:
    """Return the seconds left before converge's deadline, none below zero."""
    return max(context.deadline - time.monotonic(), 0)


def failure(
    station: str, seconds: float, code: int, killed: bool, limit: str = ""
) -> str | None:
    """Return a failed worker's halt in `Run.spawn`'s words, else None.

    e.g. "converge-fix-r1", 3600, 1, False → "converge-fix-r1 worker exit 1"
    """
    if killed:
        return f"{station} timed out after {round(seconds)}s; its group was killed"
    if code == 0:
        return None
    limit = limit if not limit or limit.startswith(" · ") else f" · {limit}"
    return f"{station} worker exit {code}{limit}"


def unequipped(context: Context, station: str) -> None:
    """Halt, naming each tool the station's log asked for and its station lacks.

    Why: design D5; 0100-worker-diet D5.
    """
    if missing := context.host.lacks(context.change, station):
        raise Halt(
            f"{station} asked for a tool its station lacks: {', '.join(missing)}"
        )


def fixer(context: Context, ids: str) -> None:
    """Run one fixer on `fix=`'s model, Codex's through `host.fix`, retried once.

    A Codex limit, a kill or a second failure halts; effort is `medium` unless named.
    Why: design D4, D5; 0117-codex-converge design D3, D7.
    """
    executor, model, effort = context.workers["fix"]
    station = f"converge-fix-r{context.round}"
    attribution = "the attribution line your session names"
    if executor == "codex":
        attribution = f"Co-Authored-By: Codex {model} <noreply@openai.com>"
    told = prompt(
        "fix.md",
        role="fix",
        change=context.change,
        round=context.round,
        ids=ids,
        findings=" and ".join(str(context.folder / f"{r}.md") for r in ROLES),
        base=context.base,
        evidence=context.folder / "evidence.md",
        attribution=attribution,
    )
    models = (executor, model, effort or "medium")
    for last in (False, True):
        (context.folder / "fix.md").unlink(missing_ok=True)
        seconds = remaining(context)
        if executor == "codex":
            result = context.host.fix(
                context.change, station, context.tree, told, models, context.deadline
            )
            if result.limit:
                raise Halt(result.limit)
            code, killed = result.code, result.killed
        else:
            code, killed, _, _ = context.host.worker(
                context.change, station, context.tree, told, models, timeout=seconds
            )
        if not killed:
            unequipped(context, station)
        why = failure(station, seconds, code, killed)
        if why is None:
            return
        if killed or last:
            raise Halt(why)
        stamp(context, f"fan-out — retry — fix: {why}")


class Design(NamedTuple):
    """A design's frame a fix commit keeps, and the decision bodies it may reword."""

    headings: list[str]
    table: list[str]
    bodies: list[list[str]]


def _design(text: str) -> Design:
    """Return a design's `## ` and `### D<n>` headings, decisions table and bodies.

    The table is the `## Decisions` section before its first entry; a body drops its
    blank lines and fix notes. Why: 0147-amends-alone design D3.
    """
    found = Design([], [], [])
    inside = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("## "):
            found.headings.append(line)
            inside = line.startswith("## Decisions")
        elif inside and DECISION.match(line):
            found.headings.append(line)
            found.bodies.append([])
        elif inside and line and not NOTE.match(line):
            (found.bodies[-1] if found.bodies else found.table).append(line)
    return found


def _shown(context: Context, rev: str, path: str) -> str:
    """Return `path` at `rev`, or "" where it is missing."""
    shown = subprocess.run(
        ["git", "show", f"{rev}:{path}"],
        cwd=context.tree,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
    )
    return shown.stdout if shown.returncode == 0 else ""


def _reworded(context: Context, sha: str, path: str) -> bool:
    """Return whether `sha` rewords a decision's body; halt on a heading or the table.

    Why: 0147-amends-alone design D3.
    """
    was, now = (_design(_shown(context, rev, path)) for rev in (f"{sha}^", sha))
    if was.headings != now.headings:
        raise Halt(f"plan edit refused — {sha[:7]} changes a heading of {path}")
    if was.table != now.table:
        raise Halt(f"plan edit refused — {sha[:7]} changes the decisions table")
    return was.bodies != now.bodies


def plan_text(context: Context, before: str, after: str) -> None:
    """Halt `plan edit refused` on a fix commit past the plan text a fixer may edit.

    Only `design.md` and `specs/` may change, the delta and a body under a `Plan-text:`
    trailer naming a card of the findings. Why: 0147-amends-alone D3.
    """
    folder = f"openspec/changes/{context.change}/"
    span = f"{before}..{after}"
    for sha in git(context.tree, "rev-list", "--reverse", span).split():
        if len(git(context.tree, "rev-list", "--parents", "-1", sha).split()) > 2:
            raise Halt(f"plan edit refused — {sha[:7]} is a merge in a fix pass")
        listed = ("diff-tree", "--root", "--no-commit-id", "--name-only", "-r", "-z")
        worded = []
        for path in git(context.tree, *listed, sha).split("\0"):
            if path.startswith(f"{folder}specs/"):
                worded.append(path)
            elif path == f"{folder}design.md":
                worded += [path] if _reworded(context, sha, path) else []
            elif path.startswith(folder):
                raise Halt(f"plan edit refused — {sha[:7]} edits {path}")
        if not worded:
            continue
        said = f"--format=%(trailers:key={PLAN_TEXT},valueonly)"
        ids = set(re.findall(r"[\w·]+", git(context.tree, "log", "-1", said, sha)))
        if not ids:
            raise Halt(
                f"plan edit refused — {sha[:7]} edits {', '.join(worded)}"
                f" with no {PLAN_TEXT}: trailer"
            )
        cards = [card for verdict in _files(context) for card in verdict.cards]
        if not ids & {card.id for card in cards}:
            raise Halt(
                f"plan edit refused — {sha[:7]} names no card of the findings"
                f" under {PLAN_TEXT}:"
            )
        if severe := sorted(
            card.id for card in cards if card.id in ids and card.security
        ):
            raise Halt(
                f"plan edit refused — {sha[:7]} names security card"
                f" {', '.join(severe)} under {PLAN_TEXT}:"
            )


def fix(context: Context, judged: Freeze, ids: str, note: str = "") -> Freeze:
    """Run Step 6's fixer on `ids`; return the freeze Step 7 judges.

    Why: design D3, D4, D5.
    """
    sent, why = ids, ""
    for more in ("", " · one more pass"):
        before = head(context)
        stamp(context, f"fix — sent {ids}{more or note}")
        fixer(context, sent)
        after = head(context)
        plan_text(context, before, after)
        code, printed = gate_line(context, keep=True)
        status = git(context.tree, "status", "--porcelain").splitlines()
        dirty = ", ".join(line[3:] for line in status)
        why = f"the gate is red, exit {code}" if code else ""
        why = why or (f"the tree is dirty: {dirty}" if dirty else "")
        done = f"commit {after[:7]}" if after != before else "nothing committed"
        stamp(context, f"fix — {done} · {why or 'gate green'}")
        if not why:
            break
        red = [line for line in printed.splitlines() if line.strip()][-20:]
        sent = f"{ids}; and {why}" + (f": {' / '.join(red)}" if code else "")
    else:
        raise Halt(f"cap reached — {why} after one more fix pass")
    amends = [
        card.id
        for verdict in _files(context)
        for card in verdict.cards
        if card.blocking and card.amend and card.status == "wontfix"
    ]
    if amends:
        raise Halt(f"amend needed — {', '.join(amends)}")
    now = head(context)
    return judged if now == judged.head else freeze(context, judged.head, now)


def left(context: Context) -> set[str]:
    """Return the subjects the last fixer's `fix.md` names under `plan check left:`."""
    text = _text(context.folder / "fix.md") or ""
    said = [line for line in text.splitlines() if line.startswith("plan check left:")]
    named = said[-1].partition(":")[2].split(",") if said else []
    return {each.strip() for each in named} - {"", "none"}


def planned(context: Context) -> None:
    """Run `plan_check.py`; raise `SendBack` with its subjects, or halt on a repeat.

    A repeat is a subject the last fixer left or Step 7 sent back; a `timed out` line
    is no card. e.g. "plan: 2.3 — `git grep x` exited 1" → "2.3". Why: design D3, D12.
    """
    argv = script("plan_check.py", "--change", context.change, "--base", context.base)
    code, printed = _captured(context, argv)
    if code == 0:
        return
    lines = [line[6:] for line in printed.splitlines() if line.startswith("plan: ")]
    if code != 1:
        raise Halt(f"plan check: {' · '.join(lines)}")
    slow = [line for line in lines if line.endswith(" timed out")]
    lines = [line for line in lines if line not in slow]
    if slow and not lines:
        names = dict.fromkeys(line.split()[0] for line in slow)
        stamp(context, f"plan check — timed out: {', '.join(names)}")
        return
    subjects = list(dict.fromkeys(line.split()[0] for line in lines))
    if repeats := [s for s in subjects if s in left(context) | context.sent]:
        raise Halt(f"amend needed — plan check: {', '.join(repeats)}")
    context.sent.update(subjects)
    raise SendBack(subjects)


def open_cards(context: Context, role: str) -> None:
    """Write `<role>.open.md`, the cards a verify judges; one it cannot read halts."""
    findings = context.folder / f"{role}.md"
    try:
        OPEN_CARDS["open_page"](findings, context.folder / mflib.layout.open_name(role))
    except OPEN_CARDS["Stop"] as stop:
        raise Halt(f"open cards: cannot read — {stop}") from stop


def verify(
    context: Context, frozen: Freeze, *, judging: bool = False
) -> dict[str, Verdict]:
    """Run Step 7: the gate, `gate_check.py`, `verify`, the plan check, one round.

    The round is counted; `judging` dispatches a catch-up's judge round on Step 3's
    inputs, else each role's verify worker on its open cards. Why: design D3, D4.
    """
    gated(context, "after the fix")
    span = f"{frozen.base[:7]}..{frozen.head[:7]}"
    stamp(context, f"verify — round {context.round + 1} · {span} · gate green")
    planned(context)
    context.round += 1
    if judging:
        return judge(context, frozen)
    stubs(context)
    for role in dispatched(context):
        open_cards(context, role)
    return verdicts(context, frozen, dispatch(context, frozen, verify=True))


def pickup(context: Context, frozen: Freeze, read: dict[str, Verdict]) -> int:
    """Run Step 8 once, while a round remains, then Steps 9 and 10.

    Why: design D3; D71.
    """
    picked = [card.id for card in pick(read)]
    if context.picked or context.round >= context.cap or not picked:
        return finish(context)
    context.picked = picked
    stamp(context, f"pickup — {', '.join(picked)}")
    return picked_up(context, frozen)


def picked_up(context: Context, judged: Freeze) -> int:
    """Send the picked cards to the fixer, then check its fix; return the exit.

    A fixer that committed nothing gets no check. Why: D74.
    """
    frozen = fix(context, judged, ", ".join(context.picked))
    if frozen == judged:
        stamp(context, "pickup — checked — nothing committed")
        return rounds(context, judged, verdicts(context, judged, {}))
    return rounds(context, frozen, check(context, frozen))


def check(context: Context, frozen: Freeze) -> dict[str, Verdict]:
    """Run the pickup check: one verify worker, on the needed role's table, at medium.

    It needs adversarial when a picked card is adversarial's, else conformance; it is
    no round. Why: design D3, D4; D71.
    """
    gated(context, "after the pickup")
    span = f"{frozen.base[:7]}..{frozen.head[:7]}"
    stamp(context, f"verify — pickup check · {span} · gate green")
    roles = dispatched(context)
    for role in roles:
        open_cards(context, role)
    needed = (
        "adversarial" if any(i[:1] == "S" for i in context.picked) else "conformance"
    )
    station = f"converge-verify-pickup-r{context.round}"
    told = verify_prompt(context, frozen, "pickup", roles)
    result = retried(context, {needed: (station, needed, told)}, "medium")[needed]
    counted(context, frozen, roles, pickup=True)
    read = verdicts(context, frozen, {})
    files = " · ".join(
        f"{role} {verdict.verdict} · open_blocking {verdict.open_blocking}"
        for role, verdict in read.items()
    )
    stamp(context, f"pickup — checked · {files} · {_spent(result)}")
    return read


def finish(context: Context, owed: bool = True) -> int:
    """Run Steps 9 and 10: the stubs at `HEAD`, the debt, the gate, `done`, the report.

    `owed` is false when the run's `debt` event stands: the debt is not written again.
    """
    stubs(context)
    paid = debt(context) if owed else debted(context)
    if gate := gate_line(context)[0]:
        raise Halt(f"the gate is red at the close: gate_run.py exit {gate}")
    rounds_ = _plural(context.round, "round")
    cards = _plural(len(paid.written), "card")
    stamp(context, f"done — converged in {rounds_} · {cards} to debt")
    print(report(context, paid, gate))
    return 0


class Debt(NamedTuple):
    """What a debt write did: the ids written, moot and cleared, and the debt's size.

    `checks` holds the command that judged each moot or cleared id.
    """

    written: list[str]
    moot: list[str]
    cleared: list[str]
    total: int
    checks: dict[str, str]


def still_true(context: Context, value: str) -> tuple[int | None, str]:
    """Return a card's **Still true?** command's exit, run sandboxed, and the command.

    Why: design D6, D7.
    """
    found = COMMAND.match(value.strip())
    if found is None:
        return None, ""
    try:
        argv = shlex.split(found[1])
    except ValueError:
        return None, found[1]
    return (_captured(context, argv)[0] if argv else None), found[1]


@contextmanager
def debt_lock(primary: Path) -> Iterator[mflib.debtfile.Holder]:
    """Hold `.minions/debt.lock` while the body runs; wait for it, then halt.

    An old `.minions/backlog.md` takes no lock. Why: design D5, D7.
    """
    if os.path.lexists(mflib.layout.backlog_file(primary)):
        raise Halt(
            ".minions/debt.lock not taken — an old .minions/backlog.md stands;"
            " /mf-ship moves it at a run's start"
        )
    try:
        with mflib.debtfile.lock(mflib.layout.debt_lock(primary), LOCK_WAIT) as held:
            yield held
    except mflib.debtfile.Held:
        raise Halt(f".minions/debt.lock held for {LOCK_WAIT // 60} minutes") from None


def _debt_text(path: Path) -> str:
    """Return the debt's text, "" when missing; one that cannot be read halts."""
    try:
        return mflib.debtfile.read(path)
    except mflib.debtfile.Unreadable as unread:
        raise Halt(f".minions/debt.md cannot be read: {unread.reason}") from unread


def answered_amends(context: Context) -> set[str]:
    """Return the ids each `amend needed` halt named since this converge began.

    It began at the newest `round 1 · start` of a run with no mark: a catch-up or
    amend run goes on with it. Why: design D3, D7.
    """
    ids: set[str] = set()
    mark = None
    for line in mflib.statuslog.read(context.log).splitlines():
        if mflib.statuslog.is_heading(line):
            mark = mflib.statuslog.mark_of(line)
        elif found := mflib.statuslog.parse_event(line):
            round_, name, detail = found
            if (name, round_, mark) == ("start", 1, None):
                break
            if name == "halt" and detail.startswith("amend needed — "):
                named = HALTED.sub("", detail).removeprefix("amend needed — ")
                ids.update(each.strip() for each in named.split(","))
    return ids


def amends(
    context: Context, cards: list[mflib.findings.Card], holds: set[str]
) -> dict[str, str]:
    """Run each amend card's check before the debt; return the moot ones' commands.

    An amend card's check that is not exit 1 halts `amend needed`; no check goes
    unchecked. Why: design D7.
    """
    number = context.change.partition("-")[0]
    answered = answered_amends(context)
    moot, left = {}, []
    for card in cards:
        due = card.status == "wontfix" or (
            card.status == "open" and card.severity == "drift"
        )
        if not card.amend or not due or card.id in answered:
            continue
        if f"{number}·{card.id}" in holds:
            continue
        code, command = still_true(context, card.fields.get("Still true?", ""))
        if code == 1:
            moot[card.id] = command
        elif code is not None:
            left.append(card.id)
    if left:
        raise Halt(f"amend needed — {', '.join(left)}")
    return moot


def spoiled(context: Context) -> list[str]:
    """Return a debt card for each role's file still malformed after its rewrite.

    Why: design D5.
    """
    number = context.change.partition("-")[0]
    found = []
    for role in dispatched(context):
        path = mflib.layout.findings_file(
            Path(context.host.primary), context.change, role
        )
        read = read_findings(path, role)
        if read is None or read.malformed is None:
            continue
        where = f".minions/changes/{context.change}/{role}.md"
        found.append(
            mflib.debtfile.spoiled(
                number,
                len(found) + 1,
                role,
                read.malformed,
                context.round,
                context.change,
                where,
            )
        )
    return found


def debt(context: Context) -> Debt:
    """Write Step 9's debt once, under its lock; return what it did.

    Why: design D7.
    """
    primary = Path(context.host.primary)
    path = mflib.layout.debt_file(primary)
    number = context.change.partition("-")[0]
    files = _files(context)
    cards = [
        card
        for verdict in files
        for card in verdict.cards
        if not card.blocking and card.status != "verified"
    ]
    checks = amends(context, cards, set(mflib.debtfile.ids(_debt_text(path))))
    moot, written, cleared = list(checks), [], []
    with debt_lock(primary) as held:
        text = _debt_text(path) or mflib.debtfile.PREAMBLE
        holds = set(mflib.debtfile.ids(text))
        filed = []
        for card in cards:
            qualified = f"{number}·{card.id}"
            if card.id in checks or qualified in holds:
                continue
            code, command = still_true(context, card.fields.get("Still true?", ""))
            held.renew()
            if code == 1:
                moot.append(card.id)
                checks[card.id] = command
                continue
            filed.append(mflib.debtfile.qualify(card.lines, card.id, qualified))
            written.append(qualified)
        for spoilt in spoiled(context):
            qualified = mflib.debtfile.ids(spoilt)[0]
            if qualified not in holds:
                filed.append(spoilt)
                written.append(qualified)
        text = mflib.debtfile.filed(text, context.change, filed)
        for card in (c for v in files for c in v.cards if c.status == "verified"):
            repeat = REPEAT.search(card.fields.get("Related", ""))
            old = next(
                (
                    c
                    for c in mflib.findings.cards(text, "")
                    if repeat and c.id == repeat[1]
                ),
                None,
            )
            if old is None:
                continue
            code, command = still_true(context, old.fields.get("Still true?", ""))
            held.renew()
            if code == 1:
                text = mflib.debtfile.unfiled(text, old.id)
                cleared.append(old.id)
                checks[old.id] = command
        _write_debt(primary, text)
    paid = Debt(written, moot, cleared, mflib.debtfile.count(text), checks)
    stamp(context, f"debt — {_debt_detail(paid)}")
    return paid


def _write_debt(primary: Path, text: str) -> None:
    """Write the debt through the folder it opens; a link at `.minions` halts.

    Why: 0139-debt design D7.
    """
    path = mflib.layout.debt_file(primary)
    try:
        fd = mflib.statefile.folder(primary, mflib.layout.MINIONS)
    except OSError as error:
        why = f"{path.parent}: {error.strerror}"
        raise Halt(f".minions/debt.md cannot be written — {why}") from error
    try:
        mflib.debtfile.write(Path(path.name), text, folder=fd)
    except mflib.statefile.WriteFailed as failed:
        link = failed.error.errno == errno.ELOOP
        why = f"{path} is a link" if link else f"{path}: {failed.error.strerror}"
        raise Halt(f".minions/debt.md cannot be written — {why}") from failed
    finally:
        os.close(fd)


def _debt_detail(paid: Debt) -> str:
    """Return the `debt` event's detail.

    e.g. "written 0001·R2 · moot R3 · cleared 0000·R1", or "none"
    """
    parts = [
        f"{word} {', '.join(ids)}"
        for word, ids in (
            ("written", paid.written),
            ("moot", paid.moot),
            ("cleared", paid.cleared),
        )
        if ids
    ]
    return " · ".join(parts) or "none"


def debted(context: Context) -> Debt:
    """Return the run's written debt, read back from its `debt` event."""
    detail = next(e.detail for e in latest(context).events if e.name == "debt")
    named = {
        part.partition(" ")[0]: part.partition(" ")[2].split(", ")
        for part in detail.split(" · ")
    }
    text = _debt_text(mflib.layout.debt_file(Path(context.host.primary)))
    return Debt(
        named.get("written", []),
        named.get("moot", []),
        named.get("cleared", []),
        mflib.debtfile.count(text),
        {},
    )


def fix_notes(context: Context) -> list[str]:
    """Return each fix note this run's fixers appended, as its decision and card.

    A fix's diff is the re-freeze that follows its `fix — commit` event.
    e.g. ["D3 (R1)"]
    """
    path = f"openspec/changes/{context.change}/design.md"
    added: set[str] = set()
    fixed = False
    for event in reversed(latest(context).events):
        if event.name == "fix":
            fixed = event.detail.startswith("commit ")
        elif event.name == "freeze" and fixed and (span := SPAN.search(event.detail)):
            ends = resolve(context, span[1]), resolve(context, span[2])
            diff = git(context.tree, "diff", "-U0", *ends, "--", path)
            added.update(line[1:] for line in diff.splitlines() if line[:1] == "+")
            fixed = False
    notes, decision = [], "a decision"
    design = context.tree / path
    for line in design.read_text().splitlines() if design.is_file() else []:
        if heading := DECISION.match(line):
            decision = heading[1]
        elif line in added and (note := NOTE.match(line)):
            notes.append(f"{decision} ({note[1]})")
    return notes


def _sentence(parts: list[str]) -> str:
    """Return `parts` as one sentence, its first letter upper case."""
    said = "; ".join(parts)
    return f"{said[:1].upper()}{said[1:]}."


def report(context: Context, paid: Debt, gate: int) -> str:
    """Return Step 10's close-out, read from disk, then its `Next:` line.

    The verdicts, the rounds and each skipped role; each blocking card's end state,
    each `inconclusive` section and fix note; the debt and the gate. Why: design D3.
    """
    files = _files(context)
    judged = ", ".join(
        f"{v.role} skipped, the loop judged without it"
        if v.stub
        else f"{v.role} {v.verdict}"
        for v in files
    )
    first = (
        f"Converged in {_plural(context.round, 'round')}"
        f" at {head(context)[:7]}: {judged}."
    )
    found = []
    if blocking := [f"{c.id} {c.status}" for v in files for c in v.cards if c.blocking]:
        found.append(f"blocking {', '.join(blocking)}")
    if unsure := [
        f"{v.role} {', '.join(v.inconclusive)}" for v in files if v.inconclusive
    ]:
        found.append(f"inconclusive: {', '.join(unsure)}")
    if notes := fix_notes(context):
        found.append(f"fix notes to read: {', '.join(notes)}")
    second = _sentence(found or ["no blocking card, inconclusive section or fix note"])

    def checked(ids: list[str]) -> str:
        return ", ".join(
            f"{i} (`{paid.checks[i]}` exited 1)" if i in paid.checks else i for i in ids
        )

    owed = [
        f"to the debt {', '.join(paid.written)}"
        if paid.written
        else "no card to the debt"
    ]
    owed += [f"moot {checked(paid.moot)}"] if paid.moot else []
    owed += [f"cleared {checked(paid.cleared)}"] if paid.cleared else []
    owed += [f"the debt holds {_plural(paid.total, 'card')}", f"the gate exits {gate}"]
    return "\n".join(
        [first, second, _sentence(owed), "Next: /mf-release, in a fresh session."]
    )


def base_of(context: Context) -> str:
    """Return Step 2's base: the merge-base of the default branch and `HEAD`."""
    default = INTEGRATE["default_branch"](context.tree)
    return git(context.tree, "merge-base", default, "HEAD").strip()


def grant(context: Context) -> int:
    """Run a granted round: the open blockers to one fixer, then one verify round.

    Its first event names the grant; a blocker left is `cap reached`.
    Why: design D3; D56.
    """
    context.base = base_of(context)
    files = _files(context)
    read = {verdict.role: verdict for verdict in files}
    if not (ids := [card.id for card in blockers(read)]):
        raise Halt("a granted round needs a blocking card open")
    context.round = max(verdict.round for verdict in files)
    context.cap = context.round + 1
    judged = Freeze(files[0].head, files[0].head, 0, 0)
    return rounds(context, *again(context, judged, ids, " · grant"))


def ancestor(context: Context, older: str, newer: str) -> bool:
    """Return whether `older` is an ancestor of `newer`."""
    done = subprocess.run(
        ["git", "merge-base", "--is-ancestor", older, newer],
        cwd=context.tree,
        capture_output=True,
        timeout=TIMEOUT_SECONDS,
    )
    return done.returncode == 0


def select(context: Context, judged: str) -> list[tuple[str, list[str]]]:
    """Return the version's own commits past `judged`, oldest first, with parents.

    `judged` must be on `HEAD`'s first-parent chain, and each merge one of the
    default branch. Why: `references/worker.md`, *Catch-up scope*.
    """
    listed = ("rev-list", "--reverse", "--first-parent", "--parents", f"{judged}..HEAD")
    chosen = [
        (sha, parents)
        for sha, *parents in map(str.split, git(context.tree, *listed).splitlines())
    ]
    if not chosen or chosen[0][1][:1] != [judged]:
        raise Halt(
            f"history rewritten: {judged[:7]} is not on HEAD's first-parent chain"
            " — re-converge from round 1"
        )
    default = INTEGRATE["default_branch"](context.tree)
    for sha, parents in chosen:
        if len(parents) > 2 or (
            len(parents) == 2 and not ancestor(context, parents[1], default)
        ):
            raise Halt(
                f"{sha[:7]} is no merge of {default}: catch-up scope cannot judge it"
            )
    return chosen


def amended(context: Context, sha: str, parents: list[str]) -> bool:
    """Return whether `sha` is an amend: one parent, its subject, the change's paths."""
    if len(parents) != 1:
        return False
    subject = git(context.tree, "log", "-1", "--format=%s", sha).strip()
    paths = git(context.tree, "diff-tree", "--no-commit-id", "--name-only", "-r", sha)
    folder = f"openspec/changes/{context.change}/"
    return subject == f"docs({context.change}): amend the change directory" and all(
        path.startswith(folder) for path in paths.split()
    )


def added(context: Context, judged: str) -> None:
    """Run the `Verify:` lines the range adds to `tasks.md` in one plan check.

    One that fails halts `verify failed — <sub-task ids>`. Why: design D3, D6; D63;
    0114-faster-plan-check design D8.
    """
    path = f"openspec/changes/{context.change}/tasks.md"
    shown = subprocess.run(
        ["git", "show", f"{judged}:{path}"],
        cwd=context.tree,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
    )
    tasks = PLAN_CHECK["subtasks"]
    was = {
        task.name: PLAN_CHECK["verify_of"](task.text) for task in tasks(shown.stdout)
    }
    changed = [
        task.name
        for task in tasks((context.tree / path).read_text())
        if "**HALT CHECK**" not in task.text
        and (said := PLAN_CHECK["verify_of"](task.text)) is not None
        and was.get(task.name) != said
    ]
    if not changed:
        return
    argv = script("plan_check.py", "--change", context.change, "--base", context.base)
    code, printed = _captured(context, [*argv, "--only", *changed])
    if code == 0:
        return
    lines = [line[6:] for line in printed.splitlines() if line.startswith("plan: ")]
    named = [match[1] for line in lines if (match := PLANNED.match(line))]
    if code == 1 and named:
        raise Halt(f"verify failed — {', '.join(dict.fromkeys(named))}")
    raise Halt(f"plan check: {' · '.join(lines)}")


def catch_up(context: Context, judged: str) -> int:
    """Judge the commits past the judged head: by rule, or one round under its count.

    Merges and amends alone, and an amend run, have their own count: one judge round
    and at most one fix round. Why: design D3; D63.
    """
    context.round = max(verdict.round for verdict in _files(context))
    chosen = select(context, judged)
    now = head(context)
    merges = [sha for sha, parents in chosen if len(parents) == 2]
    amends = [sha for sha, parents in chosen if amended(context, sha, parents)]
    own = context.mark == "amend" or len(merges) + len(amends) == len(chosen)
    count = "its own count" if own else "counted"
    stamp(context, f"catch-up — judged head {judged[:7]} · HEAD {now[:7]} · {count}")
    if not own and context.round >= CAP:
        raise Halt(
            f"the files judged round {context.round}, the cap: revert the late"
            " commits, or re-converge from round 1"
        )
    context.cap = context.round + 2 if own else CAP
    base = preconditions(context)
    added(context, judged)
    stamp(
        context,
        f"start — base {base[:7]} · head {now[:7]} · {counts(context, base, now)[2]}",
    )
    if (
        len(merges) == len(chosen)
        and context.mark != "amend"
        and by_rule(context, chosen)
    ):
        return finish(context)
    frozen = scoped(context, judged, chosen)
    return rounds(
        context, *step7(context, Freeze(judged, judged, 0, 0), frozen, judging=True)
    )


def scoped(
    context: Context, judged: str, chosen: list[tuple[str, list[str]]]
) -> Freeze:
    """Freeze `judged..HEAD`; with a merge, each commit by its own diff.

    Why: `references/worker.md`, *Catch-up scope*.
    """
    now = head(context)
    if all(len(parents) == 1 for _, parents in chosen):
        return freeze(context, judged, now)
    patches, paths = [], set()
    for sha, parents in chosen:
        kind = "--remerge-diff" if len(parents) == 2 else "--patch"
        patches.append(git(context.tree, "show", "--format=fuller", kind, sha))
        paths.update(
            git(context.tree, "show", "--format=", "--name-only", kind, sha).split()
        )
    return freeze(context, judged, now, ("".join(patches), len(chosen), len(paths)))


def by_rule(context: Context, chosen: list[tuple[str, list[str]]]) -> bool:
    """Write each findings file clean by rule when every merge replays; return whether.

    `replay` stopping, on any exit, sends the merges to a worker round.
    Why: design D1, D3, C7.
    """
    settled = []
    for sha, parents in chosen:
        try:
            said = INTEGRATE["replay"](context.tree, sha)
        except INTEGRATE["Stop"]:
            return False
        settled.append((sha, parents, said.removeprefix("replay: by rule — ")))
    context.round += 1
    today = date.today().isoformat()
    lines = "".join(
        f"- {sha} ({' '.join(parents)}): {paths}\n" for sha, parents, paths in settled
    )
    now = head(context)
    for role in dispatched(context):
        ruled(context.folder / f"{role}.md", now, context.round, today, lines)
    stubs(context)
    stamp(context, f"by rule — clean, {'; '.join(paths for *_, paths in settled)}")
    return True


def ruled(path: Path, now: str, round_: int, today: str, lines: str) -> None:
    """Set a findings file clean by rule at `now`: frontmatter, `## By rule`, log."""
    keys = {
        "head": now,
        "round": round_,
        "reviewed": today,
        "mode": "by-rule",
        "workers": 0,
    }
    text = mflib.findings.keyed(mflib.findings.read(path) or "", keys)
    before, log, after = text.partition("## Resolution log\n")
    text = f"{before}## By rule\n\n{lines}\n{log}{after}"
    BUNDLE["write"](
        path, text.rstrip("\n") + f"\n{today} · round {round_} · by rule — clean\n"
    )


def before_round(run: mflib.statuslog.Run) -> bool:
    """Return whether the run's halt is a halt before round 1.

    No grant and no `verify: halt`, and no `start`, or a halt that names a worker
    and no usage limit, with no `verdicts`. Why: design D3; 0145-halts-alone D6.
    """
    names = {event.name for event in run.events}
    detail = run.events[0].detail
    unjudged = (
        "verdicts" not in names
        and mflib.statuslog.names_worker(detail)
        and "usage limit" not in detail
    )
    return (
        run.mark != "grant"
        and ("start" not in names or unjudged)
        and "verify: halt" not in detail
    )


def answered(context: Context, run: mflib.statuslog.Run) -> str | None:
    """Return the files' judged head when a commit answered the run's halt, else None.

    `HEAD` descends from the halt's head and is not it, and the files judged that
    head, or an amend follows it. Why: design D3; D63.
    """
    halted = HALTED.search(run.events[0].detail)
    files = _files(context)
    heads = {verdict.head for verdict in files}
    if not halted or before_round(run) or len(files) < len(ROLES) or len(heads) != 1:
        return None
    sha, judged = halted[1], heads.pop()
    if sha == head(context) or not ancestor(context, sha, "HEAD"):
        return None
    listed = git(context.tree, "rev-list", "--parents", f"{sha}..HEAD").splitlines()
    amends = (amended(context, c, parents) for c, *parents in map(str.split, listed))
    return judged if judged == sha or any(amends) else None


def unanswered(context: Context, run: mflib.statuslog.Run) -> bool:
    """Return whether the run's halt is a cap no grant or answer has moved.

    Its files read, at one head. Why: design D3; D56.
    """
    files = _files(context)
    heads = {verdict.head for verdict in files}
    cap = run.events[0].detail.startswith("cap reached")
    return (
        cap and not before_round(run) and len(files) == len(ROLES) and len(heads) == 1
    )


def behind(context: Context) -> str | None:
    """Return the judged head when both files are clean at one head not `HEAD`."""
    files = _files(context)
    heads = {verdict.head for verdict in files}
    clean = all(verdict.verdict == "clean" for verdict in files)
    if len(files) == len(ROLES) and clean and len(heads) == 1:
        judged = heads.pop()
        return judged if judged != head(context) else None
    return None


def resolve(context: Context, short: str) -> str:
    """Return the commit a short sha names."""
    return git(context.tree, "rev-parse", "--verify", f"{short}^{{commit}}").strip()


def frozen_of(context: Context, run: mflib.statuslog.Run) -> Freeze:
    """Return the run's latest freeze; with none yet, the files' judged head."""
    for event in run.events:
        if event.name == "freeze" and (span := SPAN.search(event.detail)):
            ends = resolve(context, span[1]), resolve(context, span[2])
            return Freeze(*ends, int(span[3]), int(span[4]))
    judged = next((verdict.head for verdict in _files(context)), head(context))
    return Freeze(judged, judged, 0, 0)


def cap_of(run: mflib.statuslog.Run) -> int:
    """Return the run's cap: a grant's one round past it, an own count's two rounds."""
    first = run.events[-1]
    if run.mark == "grant":
        return first.round + 1
    if first.name == "catch-up" and first.detail.endswith(" · its own count"):
        return first.round + 2
    return CAP


def go_on(context: Context, run: mflib.statuslog.Run) -> int:
    """Go on with an unended run from its latest event.

    Why: design D3; `test_a_run_resumes_from_its_status_log` holds each row.
    """
    events, top = run.events, run.events[0]
    context.mark, context.round, context.cap = run.mark, top.round, cap_of(run)
    context.base = base_of(context)
    pickups = [event.detail for event in events if event.name == "pickup"]
    named = [d for d in pickups if not d.startswith(("none", "checked"))]
    context.picked = (
        named[-1].removesuffix(" · with the fix").split(", ") if named else []
    )
    newest = pickups[0] if pickups else "none"
    due = not newest.startswith(("none", "checked")) and not newest.endswith(
        " · with the fix"
    )
    sent = [
        e.detail[5:] for e in events if e.name == "fix" and e.detail.startswith("sent ")
    ]
    context.sent = {
        s for d in sent if d.startswith("plan check: ") for s in d[12:].split(", ")
    }
    frozen = frozen_of(context, run)
    fixed = bool(sent)
    caught = run.mark in ("catch-up", "amend")
    name = top.name
    if caught and name in ("catch-up", "start"):
        judged = re.search(r"judged head (\w+)", events[-1].detail)
        return catch_up(context, resolve(context, judged[1] if judged else "HEAD"))
    if name == "debt":
        return finish(context, owed=False)
    if (name == "by rule" and caught) or top.detail == "none":
        return finish(context)
    if name == "start":
        frozen = freeze(context, context.base, head(context))
        return rounds(context, frozen, judge(context, frozen))
    if name in ("verdicts", "shadow") or top.detail.startswith("checked"):
        return rounds(context, frozen, verdicts(context, frozen, {}))
    if name == "pickup" and not due:
        ids = [card.id for card in blockers(verdicts(context, frozen, {}))]
        return rounds(context, *again(context, frozen, [*ids, *context.picked]))
    if name == "pickup":
        return picked_up(context, frozen)
    if name == "fix":
        now = head(context)
        ids = sent[0].split(" · ")[0]
        plan_text(context, frozen.head, now)
        later = (
            fix(context, frozen, ids)
            if now == frozen.head
            else freeze(context, frozen.head, now)
        )
        if due:
            return rounds(context, later, check(context, later))
        return rounds(context, *step7(context, frozen, later))
    if name == "fan-out":
        done = {
            v.role
            for v in _files(context)
            if v.head == frozen.head and v.round == context.round
        }
        roles = [role for role in dispatched(context) if role not in done]
        checked = dispatch(context, frozen, verify=fixed, roles=roles) if roles else {}
        return rounds(context, frozen, verdicts(context, frozen, checked))
    if name == "freeze" and not fixed and not caught:
        return rounds(context, frozen, judge(context, frozen))
    judged = Freeze(frozen.base, frozen.base, 0, 0)
    if due:
        return rounds(context, frozen, check(context, frozen))
    return rounds(
        context, *step7(context, judged, frozen, judging=caught and not fixed)
    )


def dispatched(context: Context) -> list[str]:
    """Return the roles the plan does not skip, in `ROLES` order."""
    return [role for role in ROLES if context.workers.get(role) != "skip"]


def stubs(context: Context) -> None:
    """Write each skipped role's stub at `HEAD` for this round, by `skip_stub.py`.

    Its refusal halts, naming what it would print. Why: design D3.
    """
    now = head(context)
    for role in (role for role in ROLES if role not in dispatched(context)):
        path = mflib.layout.findings_file(
            Path(context.host.primary), context.change, role
        )
        try:
            SKIP_STUB["role_of"](path)
            text = SKIP_STUB["stub"](path, role, context.round, now, context.tree)
            SKIP_STUB["write"](path, text)
        except SKIP_STUB["Stop"] as stop:
            raise Halt(f"skip_stub: cannot stub — {stop}") from stop


def scope_of(context: Context, frozen: Freeze) -> str:
    """Return a judge round's scope: the whole range, or a catch-up's selection.

    Each selected commit, its parents and diff kind, then the counts. Why: `worker.md`.
    """
    if context.mark not in ("catch-up", "amend"):
        return "The scope: the whole range."
    noun = "an amend" if context.mark == "amend" else "a catch-up"
    lines = [
        f"- {sha} (parents {' '.join(parents)}):"
        f" {'remerge-diff' if len(parents) == 2 else 'ordinary diff'}"
        for sha, parents in select(context, frozen.base)
    ]
    counts = f"{_plural(frozen.commits, 'commit')} and {_plural(frozen.files, 'file')}"
    return "\n".join([f"The scope: {noun} round of {counts}.", *lines])


def checker_prompt(
    context: Context,
    frozen: Freeze,
    role: str,
    mode: str,
    findings: Path | None = None,
) -> str:
    """Return a judge round's prompt for `role`, from its reference's `## Prompt`."""
    folder = context.folder
    return prompt(
        f"generic-{role}.md",
        role=role,
        change=context.change,
        round=context.round,
        range=f"{frozen.base}..{frozen.head}",
        scope=scope_of(context, frozen),
        mode=mode,
        patch=folder / "diff.patch",
        bundle=folder / "bundle.md",
        debt_cards=folder / "debt-cards.md",
        evidence=folder / "evidence.md",
        findings=findings or folder / f"{role}.md",
    )


def verify_prompt(context: Context, frozen: Freeze, role: str, roles: list[str]) -> str:
    """Return a verify worker's prompt over `roles`' files.

    A pickup check's role is `pickup`, over both files.
    """
    folder = context.folder
    return prompt(
        "verify.md",
        role=role,
        change=context.change,
        round=context.round,
        range=f"{frozen.base}..{frozen.head}",
        patch=folder / "diff.patch",
        evidence=folder / "evidence.md",
        open=" and ".join(str(folder / mflib.layout.open_name(each)) for each in roles),
        findings=" and ".join(str(folder / f"{each}.md") for each in roles),
    )


def run_checkers(
    context: Context, jobs: dict[str, tuple[str, str, str]], effort: str | None
) -> dict[str, Checked]:
    """Run each job, `(station, table, prompt)`, in a thread; return each result."""
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futures = {
            key: pool.submit(
                context.host.checker,
                context.change,
                station,
                table,
                context.tree,
                told,
                context.deadline,
                effort,
            )
            for key, (station, table, told) in jobs.items()
        }
        return {key: future.result() for key, future in futures.items()}


def dispatch(
    context: Context,
    frozen: Freeze,
    *,
    verify: bool = False,
    roles: list[str] | None = None,
) -> dict[str, Checked]:
    """Run a round's checkers, or its verify workers, through `host.checker`.

    Writes `fan-out` first; returns each result by role, its file stamped. A verify
    worker runs at medium; each is retried once, as `retried` says. Why: design D4.
    """
    roles = dispatched(context) if roles is None else roles
    mode = "parallel" if len(roles) > 1 else "sequential"
    span = f"{frozen.base[:7]}..{frozen.head[:7]}"
    workers = _plural(len(roles), "worker")
    stamp(context, f"fan-out — {' and '.join(roles)} dispatched · {span} · {workers}")
    kind = "verify-" if verify else ""
    jobs = {
        role: (
            f"converge-{kind}{role}-r{context.round}",
            role,
            verify_prompt(context, frozen, role, [role])
            if verify
            else checker_prompt(context, frozen, role, mode),
        )
        for role in roles
    }
    checked = retried(context, jobs, "medium" if verify else None)
    counted(context, frozen, roles)
    return checked


def counted(
    context: Context, frozen: Freeze, roles: list[str], *, pickup: bool = False
) -> None:
    """Stamp each role's findings file with the freeze's head and counts, and the round.

    A pickup check is no round: its files keep theirs. Why: 0151-stamps design D1, D2.
    """
    values: dict[str, object] = {"head": frozen.head}
    values |= {} if pickup else {"round": context.round}
    values |= {"files": frozen.files, "commits": frozen.commits}
    for role in roles:
        path = context.folder / f"{role}.md"
        if not mflib.findings.count(context.folder, path.name, values) and (
            os.path.lexists(path)
        ):
            raise Halt(f"{path.name} could not be stamped: the write failed")


def _signature(path: Path) -> tuple[int, int, int] | None:
    """Return a file's mtime, size and inode, or None with no file."""
    try:
        seen = path.lstat()
    except OSError:
        return None
    return seen.st_mtime_ns, seen.st_size, seen.st_ino


def _failed(
    context: Context,
    job: tuple[str, str, str],
    result: Checked,
    seconds: float,
    before: tuple[int, int, int] | None = None,
) -> str | None:
    """Return why a worker failed, in `Run.spawn`'s words, or that it left no file.

    A timeout kill, or a usage limit, halts at once. A file `before` still stands
    untouched was not written. Why: design D5; 0151-stamps S1.
    """
    station, table, _ = job
    why = failure(station, seconds, result.code, result.killed, result.limit)
    if why and (result.killed or result.limit):
        raise Halt(why)
    unequipped(context, station)
    path = context.folder / f"{table}.md"
    if why is None and not os.path.lexists(path):
        why = f"{table}.md is missing: its checker left no findings file"
    elif why is None and before is not None and _signature(path) == before:
        why = f"{table}.md is unchanged: its checker wrote no findings"
    return why


def retried(
    context: Context, jobs: dict[str, tuple[str, str, str]], effort: str | None
) -> dict[str, Checked]:
    """Run each job, `(station, table, prompt)`, in a thread; a failed one runs again.

    The retry's prompt is the same, and its failure is logged as a `fan-out` detail;
    a second failure halts. Why: design D5.
    """
    for station, table, _ in jobs.values():
        context.stations[table] = (station, effort)
    seconds = remaining(context)
    before = {
        key: _signature(context.folder / f"{table}.md")
        for key, (_, table, _) in jobs.items()
    }
    checked = run_checkers(context, jobs, effort)
    faults = {
        key: why
        for key, job in jobs.items()
        if (why := _failed(context, job, checked[key], seconds, before[key]))
    }
    if not faults:
        return checked
    stamp(context, *(f"fan-out — retry — {key}: {why}" for key, why in faults.items()))
    again = {key: jobs[key] for key in faults}
    seconds = remaining(context)
    checked.update(run_checkers(context, again, effort))
    for key, job in again.items():
        if why := _failed(context, job, checked[key], seconds, before[key]):
            raise Halt(why)
    return checked


def shadow(context: Context, frozen: Freeze) -> None:
    """Run round 1's shadow checkers; write `overlap.py`'s line, or their failure.

    A shadow drives nothing and halts nothing. Why: design D3; D68.
    """
    folder = context.folder
    jobs = {
        f"shadow-{role}": (
            f"converge-shadow-{role}-r1",
            f"shadow-{role}",
            checker_prompt(
                context, frozen, role, "parallel", folder / f"shadow-{role}.md"
            ),
        )
        for role in ROLES
    }
    seconds = remaining(context)
    failed = [
        why
        for key, result in run_checkers(context, jobs, None).items()
        if (
            why := failure(
                jobs[key][0], seconds, result.code, result.killed, result.limit
            )
        )
    ]
    if failed:
        stamp(context, f"shadow — {'; '.join(failed)}")
        return
    try:
        line = OVERLAP["line"](folder)
    except OVERLAP["Unread"] as unread:
        line = f"overlap: cannot read — {unread}"
    stamp(context, f"shadow — {line}")


def halt(context: Context, reason: str) -> None:
    """Write the `halt` event, ending ` · head <sha>`; a log that ended keeps its bytes.

    Why: 0119-debt-paydown-3b design D14.
    """
    if (events := latest(context).events) and (
        events[0].name == "done"
        or (
            events[0].name == "halt"
            and not mflib.statuslog.names_lock(events[0].detail)
        )
    ):
        return
    stamp(context, f"halt — {reason} · head {head(context)}")
