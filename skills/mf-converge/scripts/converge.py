# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Conduct converge: the preconditions, the freeze, the rounds, the debt and the report.

    converge(host, change, tree, *, workers, grant=False, deadline) -> int

`conduct.py` loads this file by `runpy` and calls `converge` in a version's thread;
by hand, `conduct.py converge <change-id> [conformance=…] [adversarial=…] [fix=…]
[grant=yes]` calls it. Exit 0 done · 1 halted · 2 cannot run; the report, or the
halt, is printed.

It loads, from this folder, `stamp.py`, which writes each status-log event,
`bundle.py`, `debt_match.py`, `skip_stub.py`, `open_cards.py`, `plan_check.py` and
`overlap.py`, and `../../mf-integrate/scripts/integrate.py` for `replay`. It runs
`gate_run.py`, `gate_check.py`, `plan_check.py`, `make -n gate`, each `Verify:` a
catch-up's range adds and each card's **Still true?** command under
`host.sandboxed`. Why: 0108-converge-script design D1, D3, D6.
"""

import errno
import io
import os
import re
import runpy
import shlex
import stat
import subprocess
import time
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, NamedTuple, NoReturn, Protocol, TextIO

HERE = Path(__file__).resolve().parent
STAMP = runpy.run_path(str(HERE / "stamp.py"))
BUNDLE = runpy.run_path(str(HERE / "bundle.py"))
DEBT_MATCH = runpy.run_path(str(HERE / "debt_match.py"))
SKIP_STUB = runpy.run_path(str(HERE / "skip_stub.py"))
OPEN_CARDS = runpy.run_path(str(HERE / "open_cards.py"))
PLAN_CHECK = runpy.run_path(str(HERE / "plan_check.py"))
OVERLAP = runpy.run_path(str(HERE / "overlap.py"))
INTEGRATE = runpy.run_path(str(HERE.parents[1] / "mf-integrate/scripts/integrate.py"))
ROLES = ("conformance", "adversarial")
CAP = 3
SMALL = ("one line", "a test", "one line and a test")
SIZE = re.compile(r"size:([^:]*)$")
EVENT = re.compile(r"^\d\d:\d\d:\d\d · round (\d+) · (by rule|[a-z-]+) — (.*)$")
SPAN = re.compile(r"(\w+)\.\.(\w+) · (\d+) commits? · (\d+) files?")
HALTED = re.compile(r" · head (\w+)$")
# Each path of a change's files before `/mf-ship`'s move, under `.minions/`.
OLD_LAYOUT = (
    *("findings/{}_review.md", "findings/{}_security.md"),
    *("findings/{}_status_log.md", "findings/{}_diff.patch"),
    *("models/{}.toml", "integrate/{}.md", "integrate/{}.red", "integrate/{}.resolved"),
    *("build/{}.done", "build/{}.halt", "build/{}.closing", "build/{}.discarded.patch"),
    *("rescue/{}.md", "release/{}.held", "gate-check/{}"),
    *("changes/{}/review.md", "changes/{}/security.md"),
)
NO_COMMAND = ("is up to date", "Nothing to be done")
PROGRESS = re.compile(r"^- \[([ xX])\] (\d+) — ", re.MULTILINE)
SUBTASK = re.compile(r"^  (\d+(?:\.\d+)+)(?: · uncommitted)?$", re.MULTILINE)
REFERENCES = HERE.parent / "references"
# The `## Prompt` placeholders. Why: design D2.
PLACEHOLDERS = (
    *("change", "role", "round", "base", "head", "range", "findings", "patch"),
    *("bundle", "debt_cards", "open", "ids", "models", "mode"),
)
PROMPT = re.compile(r"^## Prompt\n\n```text\n(.*?)^```$", re.MULTILINE | re.DOTALL)
PLACEHOLDER = re.compile(r"\{(\w+)\}")
FRONT = re.compile(r"\A---\n(.*?\n)---\n", re.DOTALL)
TITLE = re.compile(r"^- \*\*(\S+) — ")
FIELD = re.compile(r"^[ \t]+- \*\*(.+?):?\*\*:?[ \t]*(.*)$")
BLOCKS = {"conformance": ("blocking",), "adversarial": ("critical", "high")}
INTEGERS = ("round", "open_blocking", "files", "commits")
LISTS = ("passes", "inconclusive")
VERDICTS = ("clean", "changes-requested")
FALLBACK = "fallback: codex usage limit"
REWRITE = (
    "role: {role}\nchange: {change}\nround: {round}\n\n"
    "Your findings file {findings} breaks the findings file contract of"
    " `references/worker.md` of the installed `mf-converge` skill: {why}.\n"
    "Rewrite that file to the contract. Keep its verdict, each card's id, grade,"
    " fields and Status; judge nothing anew. Edit no other file.\n"
)
# The debt lock's poll and wait, in seconds. Why: design D5.
LOCK_POLL = 5
LOCK_WAIT = 600
LOCKED = re.compile(r"\.minions/(?:debt|backlog)\.lock")
COMMAND = re.compile(r"`([^`]+)`")
REPEAT = re.compile(r"repeat of `?([\w·]+)")
NOTE = re.compile(r"^Fix note \(\d{4}-\d\d-\d\d, ([^)]+)\):")
DECISION = re.compile(r"^### (D\d+)\b")
DEBT_TITLE = re.compile(r"^- \*\*(\S+) — ", re.MULTILINE)
DEBT_PREAMBLE = (
    "# Debt\n\n*Deferred work from converge, one heading per change; a paydown change"
    " lists the ids it closes under `debt:`.*\n"
)


class Halt(Exception):
    """End the run with a `halt` event naming the reason, and exit 1."""


class Cannot(Exception):
    """End the run with exit 2: what it needs to run is missing."""


class Freeze(NamedTuple):
    """A frozen range: its ends and the counts a checker's scope is held to."""

    base: str
    head: str
    commits: int
    files: int


class Checked(Protocol):
    """What `host.checker` returns of one checker's run. Why: design D4."""

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
    def fallback(self) -> bool:
        """Return whether a Codex usage limit moved it to Claude."""

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
        self, argv: list[str], cwd: Path, trees: list[Path], out: TextIO | None = None
    ) -> int:
        """Run `argv` under the OS sandbox; return its exit."""

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


class SendBack(Exception):
    """Step 7's plan check failed: its subjects go back to the fixer, no round."""

    def __init__(self, subjects: list[str]) -> None:
        """Hold the subjects the plan check named, e.g. ["2.3", "a.py:4"]."""
        super().__init__(f"plan check: {', '.join(subjects)}")
        self.subjects = subjects


@dataclass(frozen=True)
class Card:
    """One finding of a findings file: its id, its role, its fields and its lines."""

    id: str
    role: str
    fields: dict[str, str]
    lines: list[str] = field(default_factory=list)

    def word(self, field: str) -> str:
        """Return the field's first word, case folded, its backticks and bold dropped.

        e.g. "**Fixed** — a note" → "fixed"
        """
        words = self.fields.get(field, "").replace("`", "").replace("*", "").split()
        return words[0].rstrip(".,;:").casefold() if words else ""

    @property
    def severity(self) -> str:
        """Return the grade its Priority opens with."""
        return self.word("Priority")

    @property
    def blocking(self) -> bool:
        """Return whether its grade blocks on its role's scale."""
        return self.severity in BLOCKS.get(self.role, ())

    @property
    def status(self) -> str:
        """Return its Status word: open, fixed, verified, wontfix or accepted."""
        return self.word("Status")

    @property
    def amend(self) -> bool:
        """Return whether it is an amend card."""
        return self.word("Amend") == "yes"

    @property
    def small(self) -> bool:
        """Return whether its Fix size is one of `SMALL`, read literally."""
        sized = SIZE.search(self.fields.get("Fix", ""))
        return bool(sized) and sized[1].strip(" `.") in SMALL

    @property
    def security(self) -> bool:
        """Return whether it is an adversarial card of category `security`."""
        parts = self.fields.get("Priority", "").split(" · ")
        category = parts[2].split(" — ")[0].strip() if len(parts) > 2 else ""
        return self.role == "adversarial" and category == "security"


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
    cards: tuple[Card, ...] = ()
    malformed: str | None = None
    unclean: str | None = None


@dataclass
class Context:
    """One converge run: the host, the change, its worktree, workers and round.

    `mark` is the run heading's; `cap` the round past which a blocker halts;
    `picked` this run's pickup; `sent` the plan-check subjects Step 7 sent back;
    `stations` each table's last station and effort, which a rewrite repeats.
    """

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
        return Path(self.host.primary) / ".minions" / "changes" / self.change

    @property
    def log(self) -> Path:
        """Return the status log."""
        return self.folder / "status_log.md"


def git(tree: Path, *args: str) -> str:
    """Return git's output for `args` in `tree`, or halt naming the command."""
    done = subprocess.run(["git", *args], cwd=tree, capture_output=True, text=True)
    if done.returncode != 0:
        raise Halt(f"git {args[0]} failed: {done.stderr.strip()}")
    return done.stdout


def _plural(count: int, noun: str) -> str:
    """Return the count and its noun.

    e.g. 1, "commit" → "1 commit"; 2, "file" → "2 files"
    """
    return f"{count} {noun}{'' if count == 1 else 's'}"


def stamp(context: Context, *events: str) -> None:
    """Write `events` of this round to the status log, the last given on top."""
    lines = [f"round {context.round} · {event}" for event in events]
    if STAMP["main"]([str(context.log), *lines]) != 0:
        raise Cannot(f"converge: cannot run — {context.log} cannot be stamped")


def open_run(context: Context, mark: str | None = None) -> None:
    """Open a new run in the status log, creating the log with its title if missing."""
    context.folder.mkdir(parents=True, exist_ok=True)
    try:
        with context.log.open("x") as log:
            log.write(f"# {context.change} — converge status\n")
    except FileExistsError:
        pass
    runs = STAMP["read"](context.log).count("\n## Run")
    marked = [] if mark is None else ["--mark", mark]
    if STAMP["main"]([str(context.log), "--run", str(runs + 1), *marked]) != 0:
        raise Cannot(f"converge: cannot run — {context.log} cannot be stamped")


def sandboxed(context: Context, argv: list[str], out: TextIO | None = None) -> int:
    """Run `argv` in the worktree under the host's sandbox; return its exit.

    Its output goes to `out`, else to the round's `commands-r<N>.log`. The sandbox's
    code 2 is `Cannot`; any other exception propagates. Why: design D1, D6.
    """
    trees = context.host.trees()
    try:
        if out is not None:
            return context.host.sandboxed(argv, context.tree, trees, out)
        with commands(context) as file:
            file.write(f"$ {shlex.join(argv)}\n")
            file.flush()
            return context.host.sandboxed(argv, context.tree, trees, file)
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
    """Return the argv that runs a converge script by `uv`."""
    return ["uv", "run", "--script", str(HERE / name), *args]


def old_layout(primary: Path, change: str) -> str | None:
    """Return the first of the change's files at an old path, else None."""
    for old in OLD_LAYOUT:
        path = Path(".minions") / old.format(change)
        if os.path.lexists(primary / path):
            return str(path)
    return None


def default_branch(tree: Path) -> str:
    """Return the branch `origin/HEAD` names, else `main`."""
    done = subprocess.run(
        ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
        cwd=tree,
        capture_output=True,
        text=True,
    )
    named = done.stdout.strip().removeprefix("origin/")
    return named if done.returncode == 0 and named else "main"


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
    if open_box := next((n for box, n in boxes if box == " "), None):
        raise Halt(f"phase {open_box} of tasks.md is unticked: mf-build owns it")
    base = git(tree, "merge-base", default_branch(tree), "HEAD").strip()
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
    """Run the gate, then `gate_check.py`, halting on either. Why: design D6."""
    if code := sandboxed(context, script("gate_run.py")):
        raise Halt(f"the gate is red {when}: gate_run.py exit {code}")
    argv = script("gate_check.py", "--change", context.change, "--base", context.base)
    code, printed = _captured(context, argv)
    if code == 1 and printed.startswith("verify: halt"):
        raise Halt(f"verify: halt — {', '.join(SUBTASK.findall(printed))}")
    if code != 0:
        lines = (line.strip() for line in printed.splitlines())
        raise Halt(f"gate check: {' · '.join(line for line in lines if line)}")


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


def freeze(
    context: Context, base: str, head: str, scope: tuple[str, int, int] | None = None
) -> Freeze:
    """Write the patch, bundle and debt cards of `base..head`; return its counts.

    A catch-up's `scope` is its patch, commits and files. `debt_match.py`'s exit 2
    leaves a cards file of no card. Writes `freeze`. Why: design D3, D5.
    """
    tree, folder = context.tree, context.folder
    folder.mkdir(parents=True, exist_ok=True)
    patch = folder / "diff.patch"
    text = git(tree, "diff", "--binary", base, head) if scope is None else scope[0]
    try:
        BUNDLE["write"](patch, text)
    except BUNDLE["Stop"] as stop:
        raise Halt(f"the patch cannot be written — {stop}") from stop
    try:
        text, _, _ = BUNDLE["bundle"](context.change, tree)
        BUNDLE["write"](folder / "bundle.md", text)
    except BUNDLE["Stop"] as stop:
        raise Halt(f"bundle: cannot bundle — {stop}") from stop
    debt = Path(context.host.primary) / ".minions" / "debt.md"
    old = debt.with_name("backlog.md")
    debt = old if not os.path.lexists(debt) and os.path.lexists(old) else debt
    cards = folder / "debt-cards.md"
    if DEBT_MATCH["main"]([str(debt), str(patch), str(cards)]) != 0:
        DEBT_MATCH["write"](cards, DEBT_MATCH["page"]([]))
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
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return None
    with os.fdopen(fd, "rb") as file:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise OSError(errno.EINVAL, "it is not a file")
        return file.read().decode(errors="replace")


def _cards(body: str, role: str) -> list[Card]:
    """Return the cards of a findings file's body, each with its fields."""
    cards: list[Card] = []
    current: Card | None = None
    for line in body.splitlines():
        if title := TITLE.match(line):
            current = Card(title[1], role, {}, [line])
            cards.append(current)
        elif current is None or not line.startswith((" ", "\t")):
            current = None
        else:
            current.lines.append(line)
            if found := FIELD.match(line):
                current.fields.setdefault(found[1], found[2].strip())
    return cards


def _fault(front: dict[str, str], role: str, stub: bool) -> str | None:
    """Return why the frontmatter breaks the contract's fields, else None."""
    keys = ["head", "round", "open_blocking", "verdict"]
    if not stub:
        keys += ["files", "commits", "inconclusive"]
        keys += ["passes"] if role == "conformance" else []
    for key in keys:
        value = front.get(key)
        if value is None:
            return f"{key} is missing"
        if key in INTEGERS and not (value.isascii() and value.isdigit()):
            return f"{key} is not an integer"
        if key in LISTS and not (value.startswith("[") and value.endswith("]")):
            return f"{key} is not a list"
    if front["verdict"] not in VERDICTS:
        return "verdict is neither clean nor changes-requested"
    return None


def _listed(value: str) -> tuple[str, ...]:
    """Return a frontmatter list's items.

    e.g. "[stale-claim, test-cost]" → ("stale-claim", "test-cost"); "[]" → ()
    """
    items = (item.strip().strip("'\"") for item in value[1:-1].split(","))
    return tuple(item for item in items if item)


def read_findings(path: Path, role: str, freeze: Freeze) -> Verdict | None:
    """Return a findings file read by its fields against `freeze`; None when missing.

    Not clean: fewer files or commits than the freeze, or conformance's passes short.
    Why: design D2; `references/worker.md`, *The fields converge reads*.
    """
    name = path.name
    try:
        text = _text(path)
    except OSError as error:
        why = "it is a link" if error.errno == errno.ELOOP else error.strerror
        return Verdict(role, malformed=f"{name} is malformed: {why}")
    if text is None:
        return None
    found = FRONT.match(text)
    pairs = (line.partition(":") for line in (found[1] if found else "").splitlines())
    front = {key.strip(): value.strip() for key, colon, value in pairs if colon}
    stub = front.get("mode") == "skipped"
    cards = _cards(text[found.end() :] if found else text, role)
    fault = _fault(front, role, stub)
    unmarked = (card for card in cards if card.word("Amend") not in ("yes", "no"))
    if fault is None and (card := next(unmarked, None)):
        fault = f"card {card.id} has no Amend line"
    if fault is not None:
        return Verdict(role, malformed=f"{name} is malformed: {fault}")
    verdict = Verdict(
        role,
        front["verdict"],
        front["head"],
        int(front["round"]),
        int(front["open_blocking"]),
        stub,
        () if stub else _listed(front["inconclusive"]),
        tuple(cards),
    )
    if stub:
        return verdict
    files, commits = int(front["files"]), int(front["commits"])
    if files < freeze.files or commits < freeze.commits:
        resolved = f"{_plural(files, 'file')} and {_plural(commits, 'commit')}"
        frozen = (
            f"{_plural(freeze.files, 'file')} and {_plural(freeze.commits, 'commit')}"
        )
        why = f"its scope resolved {resolved} of the freeze's {frozen}"
        return verdict._replace(unclean=f"{name} is not clean: {why}")
    if role != "conformance":
        return verdict
    passes = set(_listed(front["passes"]))
    lacking = [
        needed for needed in ("stale-claim", "test-cost") if needed not in passes
    ]
    if not passes & {"coverage-trace", "no-removed-test"}:
        lacking.append("coverage-trace or no-removed-test")
    if lacking:
        why = f"its passes field lacks {', '.join(lacking)}"
        return verdict._replace(unclean=f"{path.name} is not clean: {why}")
    return verdict


def read_verdicts(
    context: Context, freeze: Freeze, checked: dict[str, Checked]
) -> dict[str, Verdict | None]:
    """Read each role's findings file; write one `verdicts` line per role `checked`.

    `checked` holds what `host.checker` returned for each role it ran; a stub, and a
    file missing or malformed, gets no line. Why: design D2, D3.
    """
    read = {
        role: read_findings(context.folder / f"{role}.md", role, freeze)
        for role in ROLES
    }
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
    return spent + (f" · {FALLBACK}" if result.fallback else "")


def held(
    context: Context, read: dict[str, Verdict | None], frozen: Freeze
) -> dict[str, Verdict]:
    """Return each role's verdict; a malformed file gets one rewrite worker first.

    A file missing, or not clean, halts. Why: design D5.
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
        kept[role] = verdict
    return kept


def verdicts(
    context: Context, frozen: Freeze, checked: dict[str, Checked]
) -> dict[str, Verdict]:
    """Read the verdicts under Step 5's table, halting on a file it refuses."""
    return held(context, read_verdicts(context, frozen, checked), frozen)


def rewrite(context: Context, role: str, frozen: Freeze, why: str) -> Verdict | None:
    """Run one rewrite worker on `role`'s malformed file; return the file read again.

    It repeats the role's last station. Still malformed, the role reads clean at
    `HEAD` with no card, and the debt write cards the file. Why: design D5.
    """
    station, effort = context.stations.get(
        role, (f"converge-{role}-r{context.round}", None)
    )
    path = context.folder / f"{role}.md"
    stamp(context, f"fan-out — rewrite — {role}: {why}")
    told = REWRITE.format(
        role=role, change=context.change, round=context.round, findings=path, why=why
    )
    seconds = remaining(context)
    result = run_checkers(context, {role: (station, role, told)}, effort)[role]
    fault = failure(station, seconds, result.code, result.killed, result.limit)
    if fault and (result.killed or result.limit):
        raise Halt(fault)
    again = read_findings(path, role, frozen)
    if again is not None and again.malformed is not None:
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
    if old := old_layout(Path(host.primary), change):
        print(f"converge: halt — {old} is at an old path: /mf-ship's run moves it")
        return 1
    try:
        return resume(context, grant)
    except Cannot as cannot:
        print(cannot)
        halt(context, str(cannot))
        return 2
    except Halt as halted:
        halt(context, str(halted))
        print(f"converge: halt — {halted}")
        return 1


class Event(NamedTuple):
    """One status-log event: its round, its name and its detail."""

    round: int
    name: str
    detail: str


class Run(NamedTuple):
    """The status log's newest run: its heading's mark and its events, newest first."""

    mark: str | None
    events: list[Event]


def latest(context: Context) -> Run:
    """Return the status log's newest run; no log, or no run, is one of no event."""
    text = STAMP["read"](context.log) if os.path.lexists(context.log) else ""
    lines = text.splitlines()
    at = next(
        (i for i, line in enumerate(lines) if line.startswith("## Run")), len(lines)
    )
    mark = lines[at].partition(" · ")[2] if at < len(lines) else ""
    events = []
    for line in lines[at + 1 :]:
        if not line.strip() or line.startswith("## Run"):
            break
        if found := EVENT.match(line):
            events.append(Event(int(found[1]), found[2], found[3]))
    return Run(mark or None, events)


def resume(context: Context, granting: bool) -> int:
    """Go on with the newest run, or open the run this invocation is; return the exit.

    An unended run goes on; else a grant, an answered halt's amend round, a catch-up
    round, or a new run. Why: design D3.
    """
    run = latest(context)
    top = run.events[0] if run.events else None
    if top is not None and top.name not in ("halt", "done"):
        return go_on(context, run)
    if top is not None and top.name == "halt" and LOCKED.search(top.detail):
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
    begin(context, None)
    return fresh(context)


def unlocked(context: Context, run: Run) -> int:
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
    read = read_verdicts(context, frozen, dispatch(context, frozen))
    if shadowed:
        shadow(context, frozen)
    return held(context, read, frozen)


def _files(context: Context) -> list[Verdict]:
    """Return the conformance and adversarial files that read, by their fields."""
    unscoped = Freeze("", "", 0, 0)
    read = (read_findings(context.folder / f"{r}.md", r, unscoped) for r in ROLES)
    return [verdict for verdict in read if verdict and verdict.malformed is None]


def blockers(read: dict[str, Verdict]) -> list[Card]:
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


def pick(read: dict[str, Verdict]) -> list[Card]:
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
        if not ids:
            raise Halt("changes requested with no blocking card open")
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


def fixer(context: Context, ids: str) -> None:
    """Run one fixer through `host.worker`, on `fix=`'s model, retried once.

    Its effort is `fix=`'s, `medium` when it names none. A timeout kill, or a second
    failure, halts. Why: design D4, D5.
    """
    executor, model, effort = context.workers["fix"]
    station = f"converge-fix-r{context.round}"
    told = prompt(
        "fix.md",
        role="fix",
        change=context.change,
        round=context.round,
        ids=ids,
        findings=" and ".join(str(context.folder / f"{r}.md") for r in ROLES),
        base=context.base,
    )
    models = (executor, model, effort or "medium")
    for last in (False, True):
        (context.folder / "fix.md").unlink(missing_ok=True)
        seconds = remaining(context)
        code, killed, _, _ = context.host.worker(
            context.change, station, context.tree, told, models, timeout=seconds
        )
        why = failure(station, seconds, code, killed)
        if why is None:
            return
        if killed or last:
            raise Halt(why)
        stamp(context, f"fan-out — retry — fix: {why}")


def fix(context: Context, judged: Freeze, ids: str, note: str = "") -> Freeze:
    """Run Step 6's fixer on `ids`; return the freeze Step 7 judges.

    A red gate or a dirty tree gets one more pass, with its lines as the cards, then
    `cap reached`; a blocking amend card halts `amend needed`. The re-freeze is
    `judged.head..HEAD`, and a fixer that committed nothing leaves `judged`.
    Why: design D3, D4, D5.
    """
    sent, why = ids, ""
    for more in ("", " · one more pass"):
        before = head(context)
        stamp(context, f"fix — sent {ids}{more or note}")
        fixer(context, sent)
        after = head(context)
        code, printed = _captured(context, script("gate_run.py"))
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

    A repeat is a subject the last fixer left, or one Step 7 already sent back.
    e.g. "plan: 2.3 — `git grep x` exited 1" → the subject "2.3". Why: design D3.
    """
    argv = script("plan_check.py", "--change", context.change, "--base", context.base)
    code, printed = _captured(context, argv)
    if code == 0:
        return
    lines = [line[6:] for line in printed.splitlines() if line.startswith("plan: ")]
    if code != 1:
        raise Halt(f"plan check: {' · '.join(lines)}")
    subjects = list(dict.fromkeys(line.split()[0] for line in lines))
    if repeats := [s for s in subjects if s in left(context) | context.sent]:
        raise Halt(f"amend needed — plan check: {', '.join(repeats)}")
    context.sent.update(subjects)
    raise SendBack(subjects)


def open_cards(context: Context, role: str) -> None:
    """Write `<role>.open.md`, the cards a verify judges; one it cannot read halts."""
    findings = context.folder / f"{role}.md"
    try:
        OPEN_CARDS["open_page"](findings, findings.with_suffix(".open.md"))
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
    gate = sandboxed(context, script("gate_run.py"))
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

    The command is the backtick-quoted span the value opens with; with none, or one
    that cannot be split, the exit is None. Why: design D6, D7.
    e.g. "`grep -n x a.py` prints a line" → (0, "grep -n x a.py")
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
def debt_lock(minions: Path) -> Iterator[None]:
    """Hold `.minions/debt.lock` while the body runs; wait for it, then halt.

    An old `.minions/backlog.md` takes no lock. Why: design D5, D7.
    """
    if os.path.lexists(minions / "backlog.md"):
        raise Halt(
            ".minions/debt.lock not taken — an old .minions/backlog.md stands;"
            " /mf-ship moves it at a run's start"
        )
    lock, waited = minions / "debt.lock", 0
    while True:
        try:
            lock.mkdir()
            break
        except FileExistsError:
            if waited >= LOCK_WAIT:
                raise Halt(
                    f".minions/debt.lock held for {LOCK_WAIT // 60} minutes"
                ) from None
            time.sleep(LOCK_POLL)
            waited += LOCK_POLL
    try:
        yield
    finally:
        lock.rmdir()


def _debt_text(path: Path) -> str:
    """Return the debt's text, "" when missing; one that cannot be read halts."""
    try:
        return _text(path) or ""
    except OSError as error:
        why = "it is a link" if error.errno == errno.ELOOP else error.strerror
        raise Halt(f".minions/debt.md cannot be read: {why}") from error


def answered_amends(context: Context) -> set[str]:
    """Return the ids each `amend needed` halt named since this converge began.

    It began at the newest `round 1 · start` of a run with no mark: a catch-up or
    amend run goes on with it. Why: design D3, D7.
    """
    ids: set[str] = set()
    mark = None
    for line in STAMP["read"](context.log).splitlines():
        if line.startswith("## Run"):
            mark = line.partition(" · ")[2] or None
        elif found := EVENT.match(line):
            round_, name, detail = found.groups()
            if (name, round_, mark) == ("start", "1", None):
                break
            if name == "halt" and detail.startswith("amend needed — "):
                named = HALTED.sub("", detail).removeprefix("amend needed — ")
                ids.update(each.strip() for each in named.split(","))
    return ids


def amends(context: Context, cards: list[Card], holds: set[str]) -> dict[str, str]:
    """Run each amend card's check before the debt; return the moot ones' commands.

    An amend card is `Amend: yes`, `wontfix` or an `open` `drift`. One whose check is
    not exit 1 halts `amend needed`, unless an answered halt named it or the debt holds
    it. Why: design D7.
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
        else:
            left.append(card.id)
    if left:
        raise Halt(f"amend needed — {', '.join(left)}")
    return moot


def spoiled(context: Context) -> list[str]:
    """Return a debt card for each role's file still malformed after its rewrite.

    Why: design D5.
    """
    number, unscoped = context.change.partition("-")[0], Freeze("", "", 0, 0)
    found = []
    for role in dispatched(context):
        read = read_findings(context.folder / f"{role}.md", role, unscoped)
        if read is None or read.malformed is None:
            continue
        where = f".minions/changes/{context.change}/{role}.md"
        found.append(
            f"- **{number}·M{len(found) + 1} — {role}'s findings file was malformed"
            " after a rewrite**\n"
            "  - **Why it's a problem:** converge read the role as clean at HEAD with"
            " no card, so a finding in the file went unjudged.\n"
            "  - **When you'd hit it:** the release reads the file's own verdict.\n"
            f"  - **What it affects:** `{where}`.\n"
            f"  - **Evidence:** {read.malformed} · read.\n"
            "  - **Verdict:** confirmed.\n"
            "  - **Priority:** medium · conformance · maintainability — the role's"
            " verdict this run is the script's, not its checker's.\n"
            f"  - **Round:** {context.round}\n"
            "  - **Fix:** rewrite the file to the findings file contract, then converge"
            " again · size: a design change.\n"
            "  - **Amend:** no\n"
            f"  - **Trigger:** the release of {context.change}.\n"
            f"  - **Still true?** read `{where}` against the contract.\n"
            "  - **Related:** none.\n"
            "  - **Status:** open\n"
        )
    return found


def _filed(text: str, change: str, cards: list[str]) -> str:
    """Return the debt with `cards` at the end of `## <change>`, made if missing."""
    if not cards:
        return text
    lines = [line if line.endswith("\n") else f"{line}\n" for line in text.splitlines()]
    heading = f"## {change}\n"
    if heading not in lines:
        return f"{''.join(lines).rstrip()}\n\n{heading}\n{''.join(cards)}"
    at = lines.index(heading) + 1
    end = _section_end(lines, at)
    while end > at and not lines[end - 1].strip():
        end -= 1
    gap = ["\n"] if end < len(lines) and lines[end].startswith("## ") else []
    return "".join([*lines[:end], *cards, *gap, *lines[end:]])


def _section_end(lines: list[str], at: int) -> int:
    """Return the index of the first `## ` heading at or past `at`, else the end."""
    return next(
        (i for i in range(at, len(lines)) if lines[i].startswith("## ")), len(lines)
    )


def _unfiled(text: str, ident: str) -> str:
    """Return the debt without the card `ident`, and its heading when left empty."""
    lines = text.splitlines(keepends=True)
    start = next(
        i for i, line in enumerate(lines) if line.startswith(f"- **{ident} — ")
    )
    end = start + 1
    while end < len(lines) and lines[end].startswith((" ", "\t")):
        end += 1
    del lines[start:end]
    tops = [i for i in range(start) if lines[i].startswith("## ")]
    if tops and not "".join(lines[tops[-1] + 1 : _section_end(lines, start)]).strip():
        del lines[tops[-1] : _section_end(lines, start)]
    return "".join(lines)


def debt(context: Context) -> Debt:
    """Write Step 9's debt once, under its lock; return what it did.

    Amend cards first; then each non-blocking card not `verified` and not moot, its
    id qualified, an id the debt holds skipped; then each fixed repeat's old card
    cleared when its check exits 1. Writes `debt`. Why: design D7.
    """
    minions = Path(context.host.primary) / ".minions"
    path = minions / "debt.md"
    number = context.change.partition("-")[0]
    files = _files(context)
    cards = [
        card
        for verdict in files
        for card in verdict.cards
        if not card.blocking and card.status != "verified"
    ]
    checks = amends(context, cards, set(DEBT_TITLE.findall(_debt_text(path))))
    moot, written, cleared = list(checks), [], []
    with debt_lock(minions):
        text = _debt_text(path) or DEBT_PREAMBLE
        holds = set(DEBT_TITLE.findall(text))
        filed = []
        for card in cards:
            qualified = f"{number}·{card.id}"
            if card.id in checks or qualified in holds:
                continue
            code, command = still_true(context, card.fields.get("Still true?", ""))
            if code == 1:
                moot.append(card.id)
                checks[card.id] = command
                continue
            title = card.lines[0].replace(f"- **{card.id} — ", f"- **{qualified} — ")
            filed.append("".join(f"{line}\n" for line in [title, *card.lines[1:]]))
            written.append(qualified)
        for spoilt in spoiled(context):
            qualified = DEBT_TITLE.findall(spoilt)[0]
            if qualified not in holds:
                filed.append(spoilt)
                written.append(qualified)
        text = _filed(text, context.change, filed)
        for card in (c for v in files for c in v.cards if c.status == "verified"):
            repeat = REPEAT.search(card.fields.get("Related", ""))
            old = next(
                (c for c in _cards(text, "") if repeat and c.id == repeat[1]), None
            )
            if old is None:
                continue
            code, command = still_true(context, old.fields.get("Still true?", ""))
            if code == 1:
                text = _unfiled(text, old.id)
                cleared.append(old.id)
                checks[old.id] = command
        try:
            DEBT_MATCH["write"](path, text)
        except DEBT_MATCH["Stop"] as stop:
            raise Halt(f".minions/debt.md cannot be written — {stop}") from stop
    paid = Debt(written, moot, cleared, len(DEBT_TITLE.findall(text)), checks)
    stamp(context, f"debt — {_debt_detail(paid)}")
    return paid


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
    text = _debt_text(Path(context.host.primary) / ".minions" / "debt.md")
    return Debt(
        named.get("written", []),
        named.get("moot", []),
        named.get("cleared", []),
        len(DEBT_TITLE.findall(text)),
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
    return git(context.tree, "merge-base", default_branch(context.tree), "HEAD").strip()


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
    default = default_branch(context.tree)
    for sha, parents in chosen:
        if (
            len(parents) > 2
            or len(parents) == 2
            and not ancestor(context, parents[1], default)
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
    """Run each `Verify:` the range adds to `tasks.md`, ticked or not, sandboxed.

    One that fails halts `verify failed — <sub-task ids>`. Why: design D3, D6; D63.
    """
    path = f"openspec/changes/{context.change}/tasks.md"
    shown = subprocess.run(
        ["git", "show", f"{judged}:{path}"],
        cwd=context.tree,
        capture_output=True,
        text=True,
    )
    tasks = PLAN_CHECK["subtasks"]
    was = {
        task.name: PLAN_CHECK["verify_of"](task.text) for task in tasks(shown.stdout)
    }
    failed = []
    for task in tasks((context.tree / path).read_text()):
        said = PLAN_CHECK["verify_of"](task.text)
        if said is None or was.get(task.name) == said:
            continue
        for command in PLAN_CHECK["commands"](said):
            code, printed = _captured(context, PLAN_CHECK["tokens"](command.text))
            if not PLAN_CHECK["passed"](command, code, printed):
                failed.append(task.name)
                break
    if failed:
        raise Halt(f"verify failed — {', '.join(failed)}")


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
    text = _text(path) or ""
    for key, value in (
        ("head", now),
        ("round", round_),
        ("reviewed", today),
        ("mode", "by-rule"),
        ("workers", 0),
    ):
        text = re.sub(
            rf"^{key}:.*$", f"{key}: {value}", text, count=1, flags=re.MULTILINE
        )
    before, log, after = text.partition("## Resolution log\n")
    text = f"{before}## By rule\n\n{lines}\n{log}{after}"
    BUNDLE["write"](
        path, text.rstrip("\n") + f"\n{today} · round {round_} · by rule — clean\n"
    )


def before_round(run: Run) -> bool:
    """Return whether the run's halt is a halt before round 1.

    No `start`, no grant, and no `verify: halt`. Why: design D3.
    """
    return (
        run.mark != "grant"
        and not any(event.name == "start" for event in run.events)
        and "verify: halt" not in run.events[0].detail
    )


def answered(context: Context, run: Run) -> str | None:
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


def frozen_of(context: Context, run: Run) -> Freeze:
    """Return the run's latest freeze; with none yet, the files' judged head."""
    for event in run.events:
        if event.name == "freeze" and (span := SPAN.search(event.detail)):
            ends = resolve(context, span[1]), resolve(context, span[2])
            return Freeze(*ends, int(span[3]), int(span[4]))
    judged = next((verdict.head for verdict in _files(context)), head(context))
    return Freeze(judged, judged, 0, 0)


def cap_of(run: Run) -> int:
    """Return the run's cap: a grant's one round past it, an own count's two rounds."""
    first = run.events[-1]
    if run.mark == "grant":
        return first.round + 1
    if first.name == "catch-up" and first.detail.endswith(" · its own count"):
        return first.round + 2
    return CAP


def go_on(context: Context, run: Run) -> int:
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
    if name == "by rule" and caught or top.detail == "none":
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
        path = context.folder / f"{role}.md"
        try:
            SKIP_STUB["role_of"](path)
            text = SKIP_STUB["stub"](path, role, context.round, now, context.tree)
            SKIP_STUB["write"](path, text)
        except SKIP_STUB["Stop"] as stop:
            raise Halt(f"skip_stub: cannot stub — {stop}") from stop


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
        head=frozen.head,
        mode=mode,
        patch=folder / "diff.patch",
        bundle=folder / "bundle.md",
        debt_cards=folder / "debt-cards.md",
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
        head=frozen.head,
        open=" and ".join(str(folder / f"{each}.open.md") for each in roles),
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

    Writes `fan-out` first; returns each result by role. A verify worker runs at
    medium. Each worker is retried once, as `retried` says. Why: design D4.
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
    return retried(context, jobs, "medium" if verify else None)


def _failed(
    context: Context, job: tuple[str, str, str], result: Checked, seconds: float
) -> str | None:
    """Return why a worker failed, in `Run.spawn`'s words, or that it left no file.

    A timeout kill, or a usage limit, halts at once. Why: design D5.
    """
    station, table, _ = job
    why = failure(station, seconds, result.code, result.killed, result.limit)
    if why and (result.killed or result.limit):
        raise Halt(why)
    if why is None and not os.path.lexists(context.folder / f"{table}.md"):
        why = f"{table}.md is missing: its checker left no findings file"
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
    checked = run_checkers(context, jobs, effort)
    faults = {
        key: why
        for key, job in jobs.items()
        if (why := _failed(context, job, checked[key], seconds))
    }
    if not faults:
        return checked
    stamp(context, *(f"fan-out — retry — {key}: {why}" for key, why in faults.items()))
    again = {key: jobs[key] for key in faults}
    seconds = remaining(context)
    checked.update(run_checkers(context, again, effort))
    for key, job in again.items():
        if why := _failed(context, job, checked[key], seconds):
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
    """Write the `halt` event, ending ` · head <sha>`."""
    stamp(context, f"halt — {reason} · head {head(context)}")
