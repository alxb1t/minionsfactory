# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Conduct converge: the preconditions, the freeze, the checkers and their verdicts.

    converge(host, change, tree, *, workers, grant=False, deadline) -> int

`conduct.py` loads this file by `runpy` and calls `converge` in a version's thread;
exit 0 done · 1 halted · 2 cannot run. Each event goes to the status log through
`stamp.py`'s `main`; each command on the builder's code runs under `host.sandboxed`.
Why: 0108-converge-script design D1, D3, D6.
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
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NamedTuple, Protocol, TextIO

HERE = Path(__file__).resolve().parent
STAMP = runpy.run_path(str(HERE / "stamp.py"))
BUNDLE = runpy.run_path(str(HERE / "bundle.py"))
DEBT_MATCH = runpy.run_path(str(HERE / "debt_match.py"))
SKIP_STUB = runpy.run_path(str(HERE / "skip_stub.py"))
ROLES = ("conformance", "adversarial")
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
        raise NotImplementedError

    @property
    def killed(self) -> bool:
        """Return whether its timeout killed it."""
        raise NotImplementedError

    @property
    def models(self) -> tuple[str, str | None, str | None]:
        """Return the executor, model and effort it ran on."""
        raise NotImplementedError

    @property
    def limit(self) -> str:
        """Return the usage limit that stopped it, or ""."""
        raise NotImplementedError

    @property
    def fallback(self) -> bool:
        """Return whether a Codex usage limit moved it to Claude."""
        raise NotImplementedError

    @property
    def tokens(self) -> int | None:
        """Return its tokens, None when its log names none."""
        raise NotImplementedError


class Host(Protocol):
    """What `converge` is handed: `conduct.py`'s `Run`, or a test's fake.

    Why: design D1.
    """

    primary: Path

    def trees(self) -> list[Path]:
        """Return the trees a sandboxed command may write."""
        raise NotImplementedError

    def sandboxed(
        self, argv: list[str], cwd: Path, trees: list[Path], out: TextIO | None = None
    ) -> int:
        """Run `argv` under the OS sandbox; return its exit."""
        raise NotImplementedError

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
        raise NotImplementedError


@dataclass(frozen=True)
class Card:
    """One finding of a findings file: its id, its role and its fields by name."""

    id: str
    role: str
    fields: dict[str, str]

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
    """One converge run: the host, the change, its worktree, workers and round."""

    host: Host
    change: str
    tree: Path
    workers: dict[str, Any]
    deadline: float
    round: int = 1

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
    if base == git(tree, "rev-parse", "HEAD").strip():
        raise Halt("the range is empty: base is HEAD")
    dry = _captured(context, ["make", "-n", "gate"])
    if dry[0] != 0 or all(
        not line.strip() or any(word in line for word in NO_COMMAND)
        for line in dry[1].splitlines()
    ):
        raise Halt("the root Makefile's gate runs no command")
    if code := sandboxed(context, script("gate_run.py")):
        raise Halt(f"the gate is red before round 1: gate_run.py exit {code}")
    check = script("gate_check.py", "--change", context.change, "--base", base)
    code, printed = _captured(context, check)
    if code == 1 and printed.startswith("verify: halt"):
        raise Halt(f"verify: halt — {', '.join(SUBTASK.findall(printed))}")
    if code != 0:
        lines = (line.strip() for line in printed.splitlines())
        raise Halt(f"gate check: {' · '.join(line for line in lines if line)}")
    return base


def _captured(context: Context, argv: list[str]) -> tuple[int, str]:
    """Run `argv` sandboxed; return its exit and its output, also kept in the log."""
    buffer = io.StringIO()
    code = sandboxed(context, argv, buffer)
    with commands(context) as file:
        file.write(f"$ {shlex.join(argv)}\n{buffer.getvalue()}")
    return code, buffer.getvalue()


def freeze(context: Context, base: str, head: str) -> Freeze:
    """Write the patch, bundle and debt cards of `base..head`; return its counts.

    `debt_match.py`'s exit 2 leaves a cards file of no card. Writes `freeze`.
    Why: design D3, D5.
    """
    tree, folder = context.tree, context.folder
    folder.mkdir(parents=True, exist_ok=True)
    patch = folder / "diff.patch"
    try:
        BUNDLE["write"](patch, git(tree, "diff", "--binary", base, head))
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
    commits, files, shown = counts(context, base, head)
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
    for line in body.splitlines():
        if title := TITLE.match(line):
            cards.append(Card(title[1], role, {}))
        elif not line.startswith((" ", "\t")):
            continue
        elif cards and (field := FIELD.match(line)):
            cards[-1].fields.setdefault(field[1], field[2].strip())
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
        executor, model, effort = result.models
        tokens = "unavailable" if result.tokens is None else result.tokens
        line = (
            f"verdicts — {role} {verdict.verdict} · open_blocking"
            f" {verdict.open_blocking} · executor {executor} · model"
            f" {model or 'default'} · effort {effort or 'default'} · tokens {tokens}"
        )
        lines.append(line + (f" · {FALLBACK}" if result.fallback else ""))
    if lines:
        stamp(context, *lines)
    return read


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
    open_run(context)
    try:
        if not dispatched(context):
            raise Halt(
                "both checkers are skipped: a plan that skips both runs no converge"
            )
        base = preconditions(context)
        head = git(context.tree, "rev-parse", "HEAD").strip()
        shown = counts(context, base, head)[2]
        stamp(context, f"start — base {base[:7]} · head {head[:7]} · {shown}")
        frozen = freeze(context, base, head)
        return judge(context, frozen)
    except Cannot as cannot:
        print(cannot)
        halt(context, str(cannot))
        return 2
    except Halt as halted:
        halt(context, str(halted))
        return 1


def judge(context: Context, frozen: Freeze) -> int:
    """Stub the skipped roles, dispatch the others and read their verdicts; return 0.

    Both clean writes `done`; a file missing, malformed or not clean halts, and so
    does a blocking card open. Why: design D3.
    """
    stubs(context)
    read = read_verdicts(context, frozen, dispatch(context, frozen))
    for role in ROLES:
        verdict = read[role]
        if verdict is None:
            raise Halt(f"{role}.md is missing: its checker left no findings file")
        if fault := verdict.malformed or verdict.unclean:
            raise Halt(fault)
    blocking = [
        card.id
        for verdict in read.values()
        if verdict is not None
        for card in verdict.cards
        if card.blocking and card.status == "open"
    ]
    if blocking or any(v and v.verdict != "clean" for v in read.values()):
        raise Halt(f"changes requested, {' '.join(blocking) or 'no card'} open")
    stamp(
        context,
        f"done — converged in {_plural(context.round, 'round')} · 0 cards to debt",
    )
    return 0


def dispatched(context: Context) -> list[str]:
    """Return the roles the plan does not skip, in `ROLES` order."""
    return [role for role in ROLES if context.workers.get(role) != "skip"]


def stubs(context: Context) -> None:
    """Write each skipped role's stub at `HEAD` for this round, by `skip_stub.py`.

    Its refusal halts, naming what it would print. Why: design D3.
    """
    head = git(context.tree, "rev-parse", "HEAD").strip()
    for role in (role for role in ROLES if role not in dispatched(context)):
        path = context.folder / f"{role}.md"
        try:
            SKIP_STUB["role_of"](path)
            text = SKIP_STUB["stub"](path, role, context.round, head, context.tree)
            SKIP_STUB["write"](path, text)
        except SKIP_STUB["Stop"] as stop:
            raise Halt(f"skip_stub: cannot stub — {stop}") from stop


def checker_prompt(context: Context, frozen: Freeze, role: str, mode: str) -> str:
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
        findings=folder / f"{role}.md",
    )


def dispatch(context: Context, frozen: Freeze) -> dict[str, Checked]:
    """Run the round's checkers in threads through `host.checker`; return each result.

    Writes `fan-out` first. A worker killed, or one that exits non-zero, halts with
    `Run.spawn`'s words. Why: design D4.
    """
    roles = dispatched(context)
    mode = "parallel" if len(roles) > 1 else "sequential"
    span = f"{frozen.base[:7]}..{frozen.head[:7]}"
    workers = _plural(len(roles), "worker")
    stamp(context, f"fan-out — {' and '.join(roles)} dispatched · {span} · {workers}")
    seconds = max(round(context.deadline - time.monotonic()), 0)
    with ThreadPoolExecutor(max_workers=len(roles)) as pool:
        futures = {
            role: pool.submit(
                context.host.checker,
                context.change,
                f"converge-{role}-r{context.round}",
                role,
                context.tree,
                checker_prompt(context, frozen, role, mode),
                context.deadline,
            )
            for role in roles
        }
        checked = {role: future.result() for role, future in futures.items()}
    for role, result in checked.items():
        station = f"converge-{role}-r{context.round}"
        if result.killed:
            raise Halt(f"{station} timed out after {seconds}s; its group was killed")
        if result.code != 0:
            limit = result.limit or ""
            limit = limit if not limit or limit.startswith(" · ") else f" · {limit}"
            raise Halt(f"{station} worker exit {result.code}{limit}")
    return checked


def halt(context: Context, reason: str) -> None:
    """Write the `halt` event, ending ` · head <sha>`."""
    head = git(context.tree, "rev-parse", "HEAD").strip()
    stamp(context, f"halt — {reason} · head {head}")
