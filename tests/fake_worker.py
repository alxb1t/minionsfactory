"""The fake agent `MF_SHIP_AGENT` names: it does on disk what a station would.

The standard library alone: it starts once per worker, and the suite spawns many.
Why: 0051-reliability-paydown design D9.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_IDENTITY = ["-c", "user.name=mf", "-c", "user.email=mf@example.invalid"]
_IDENTITY += ["-c", "commit.gpgsign=false"]


def _git(root: Path, *args: str, check: bool = True) -> str:
    return subprocess.run(
        ["git", *_IDENTITY, *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=check,
    ).stdout.strip()


def _commit(root: Path, files: dict[str, str], message: str) -> None:
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text)
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", message)


def _folder(root: Path, change: str) -> Path:
    return root / ".minions" / "changes" / change


def _findings(
    root: Path,
    change: str,
    head: str,
    verdict: str = "clean",
    round: int = 1,
    roles: tuple[str, ...] = ("conformance", "adversarial"),
) -> None:
    folder = _folder(root, change)
    folder.mkdir(parents=True, exist_ok=True)
    for role in roles:
        (folder / f"{role}.md").write_text(_front_of(role, head, round, verdict))
    log = folder / "status_log.md"
    log.write_text("# t\n\n## Run 1 — d\n10:00:00 · round 1 · done — ok\n")


def _front_of(role: str, head: str, round_: int, verdict: str) -> str:
    """Return a planted findings file's frontmatter, to the findings file contract."""
    blocking = int(verdict != "clean")
    passes = "passes: [stale-claim, test-cost, no-removed-test]\n"
    return (
        f"---\nverdict: {verdict}\nhead: {head}\nround: {round_}\n"
        f"open_blocking: {blocking}\nfiles: 1\ncommits: 1\n"
        f"{passes if role == 'conformance' else ''}inconclusive: []\n---\n"
    )


def _cards(
    root: Path, change: str, head: str, size: str, granted: bool = False
) -> None:
    """Write both findings files capped at `head`, the `S` blocker sized `size`.

    Conformance's open blocker is sized `one line`; a nit, a `medium` and a verified
    blocker, each sized `a design change`, block nothing. A `granted` round's run is
    marked `· grant`, as `mf-converge` marks it.
    """
    folder = _folder(root, change)
    folder.mkdir(parents=True, exist_ok=True)
    cards = {
        "conformance": [
            ("R1", "blocking", "one line", "open"),
            ("R2", "nit", "a design change", "open"),
            ("R3", "blocking", "a design change", "verified — held"),
        ],
        "adversarial": [
            ("S1", "high", size, "open"),
            ("S2", "medium", "a design change", "open"),
        ],
    }
    for role, listed in cards.items():
        text = _front_of(role, head, 3, "changes-requested") + "\n"
        for card, severity, fix, status in listed:
            text += _card(card, severity, role, f"a fix · size: {fix}.", status)
        (folder / f"{role}.md").write_text(text)
    run = "## Run 2 — d · grant\n" if granted else "## Run 1 — d\n"
    log = folder / "status_log.md"
    log.write_text(f"# t\n\n{run}10:00:00 · round 3 · halt — cap reached\n")


def _amend_needed(root: Path, change: str, head: str, card: str = "R1") -> None:
    """Write converge's `amend needed — <card>` halt at `head`, after round 1's start.

    The card is `wontfix`, naming a `design.md` prose amend: conformance's
    `blocking`, or adversarial's `high` security card for an `S` id. The other
    findings file is clean.
    """
    folder = _folder(root, change)
    folder.mkdir(parents=True, exist_ok=True)
    role, severity = (
        ("adversarial", "high") if card[0] == "S" else ("conformance", "blocking")
    )
    for name in ("conformance", "adversarial"):
        verdict = "changes-requested" if name == role else "clean"
        text = _front_of(name, head, 1, verdict)
        if name == role:
            fix = "amend design.md's prose · size: one line."
            why = "wontfix — needs the amend of design.md's prose"
            text += "\n" + _card(card, severity, role, fix, why, amend="yes")
        (folder / f"{name}.md").write_text(text)
    (folder / "status_log.md").write_text(
        "# t\n\n## Run 1 — d\n"
        f"10:00:01 · round 1 · halt — amend needed — {card} · head {head}\n"
        "10:00:00 · round 1 · start — base a · head b\n"
    )


def _done(root: Path, change: str, head: str) -> None:
    folder = _folder(root, change)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "build.done").write_text(f"head: {head}\nsimplify: lean already\n")


def _closed(tree: Path, primary: Path, change: str, modes: set[str]) -> None:
    """Write `build.done` at `HEAD`, then commit or plant as `modes` say."""
    _done(primary, change, _git(tree, "rev-parse", "HEAD"))
    if "person-commits" in modes:
        _commit(primary, {"mine.txt": "x\n"}, "a person's commit")
    if "plant-network" in modes:
        agents = primary / "AGENTS.md"
        line = "- **Ship network:** `later.example`\n"
        agents.write_text(agents.read_text() + line)


def _phase(tree: Path, primary: Path, change: str, phase: str, modes: set[str]) -> None:
    """Tick one phase's boxes in one commit, or close; halt, idle, die or note as told.

    Why: 0102-build-per-phase design *The fake host*.
    """
    if phase == "close":
        if "dies-simplify" in modes:
            sys.exit(1)
        _closed(tree, primary, change, modes)
        return
    if f"idle-phase-{phase}" in modes:
        return
    if modes & {f"halt-{change}", f"halt-phase-{phase}"} and not _amended(tree, change):
        folder = _folder(primary, change)
        folder.mkdir(parents=True, exist_ok=True)
        head = _git(tree, "rev-parse", "HEAD")
        (folder / "build.halt").write_text(
            f"sub-task: {phase}.1\nstop: 3\nevidence: two readings\nhead: {head}\n"
        )
        return
    tasks = tree / "openspec" / "changes" / change / "tasks.md"
    text = tasks.read_text()
    box = rf"^- \[ \] ({re.escape(phase)}(?:\.\d+)? )"
    files = {str(tasks): re.sub(box, r"- [x] \1", text, flags=re.MULTILINE)}
    if f"after-self-{change}" in modes:
        proposal = f"---\nbump: minor\nafter: [{change}]\n---\n"
        files[str(tasks.with_name("proposal.md"))] = proposal
    if files[str(tasks)] != text:
        _commit(tree, files, "build")
    notes = _folder(primary, change) / "build-notes.md"
    if f"notes-{change}" in modes:
        line = rf"^- \[[ x]\] {re.escape(phase)} — (.*?)(?: · (?:moderate|hard))?$"
        found = re.search(line, text, re.MULTILINE)
        notes.parent.mkdir(parents=True, exist_ok=True)
        with notes.open("a") as out:
            out.write(f"## {phase} — {found[1] if found else ''}\n")
            out.write("".join(f"note {n}\n" for n in range(49)))
    if f"notes-link-{change}" in modes:
        beside = notes.with_name("notes-beside.md")
        notes.parent.mkdir(parents=True, exist_ok=True)
        beside.write_text("x\n")
        notes.unlink(missing_ok=True)
        notes.symlink_to(beside)
    if f"dies-phase-{phase}" in modes:
        sys.exit(1)


def _integrate(
    tree: Path, message: str, modes: set[str], settled: Path | None = None
) -> None:
    """Merge `main` into `tree`, or finish a merge a dead worker left open.

    In the change's `settled` folder, a merge the supervisor settled is committed as
    staged, naming each note heading `the supervisor`.
    """
    if settled is not None and _git(
        tree, "rev-parse", "-q", "--verify", "MERGE_HEAD", check=False
    ):
        note = settled / "integrate.md"
        headings = re.findall(r"^## (.+)$", note.read_text(), re.MULTILINE)
        body = "".join(f"{h}: the supervisor\n" for h in headings if h != "Resolved")
        _git(tree, "commit", "-q", "-m", message, "-m", body)
        note.unlink()
        (settled / "integrate.settled").unlink()
    elif _git(tree, "rev-parse", "-q", "--verify", "MERGE_HEAD", check=False):
        _git(tree, "checkout", "--theirs", "--", ".")
        _git(tree, "add", ".")
        _git(tree, "commit", "-q", "-m", message)
    elif "dies-integrate" in modes:
        _git(tree, "merge", "-q", "--no-ff", "--no-commit", "main", check=False)
        sys.exit(1)
    else:
        _git(tree, "merge", "-q", "--no-ff", "-m", message, "main")


_AMENDED = "Amended: 1.1\n"


_PROSE = "Read the amended prose.\n"


def _amended(tree: Path, change: str | None) -> bool:
    """Return whether a rescue's fix stands in the change's `tasks.md`."""
    tasks = tree / "openspec" / "changes" / str(change) / "tasks.md"
    return _AMENDED in tasks.read_text()


def _prose(tree: Path, change: str) -> bool:
    """Return whether a rescue's prose amend stands in the change's `design.md`."""
    design = tree / "openspec" / "changes" / change / "design.md"
    return design.is_file() and _PROSE in design.read_text()


def _rescue(tree: Path, primary: Path, change: str, modes: set[str]) -> None:
    """Amend the plan, its prose or a decision, hollowly, outside it or by a rewrite.

    Or diagnose, answer or die.
    """
    tasks = f"openspec/changes/{change}/tasks.md"
    message = f"docs({change}): amend the change directory\n\nfix\n\nRescue: 1.1"
    text = (tree / tasks).read_text()
    if "dies-rescue" in modes:
        sys.exit(1)
    if "rescue-fix" in modes:
        _commit(tree, {tasks: text + _AMENDED}, message)
    elif modes & {"rescue-prose", "rescue-decides", "rescue-person-amends"}:
        design = tree / f"openspec/changes/{change}/design.md"
        prose = (design.read_text() if design.is_file() else "") + _PROSE
        message = message.replace("1.1", "R1")
        if "rescue-decides" in modes:
            prose += "\n## Decisions\n\n| D1 | the card's fix |\n"
            message += "\nDecided-by: rescue"
        if "rescue-person-amends" in modes:
            # The person's amend, landing while the rescue runs, carries no trailer.
            message = message.split("\n", 1)[0]
        _commit(tree, {str(design): prose}, message)
    elif "rescue-hollow" in modes:
        _commit(tree, {tasks: text + "Read again.\n"}, message)
    elif "rescue-wild" in modes:
        _commit(tree, {tasks: text + "Read again.\n", "src.py": "x = 1\n"}, message)
    elif "rescue-rewrite" in modes:
        _git(tree, "commit", "-q", "--amend", "-m", "rewritten")
    elif "rescue-diagnose" in modes:
        folder = _folder(primary, change)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "rescue.md").write_text("# diagnosis\n")
    if "rescue-answers" in modes:
        # A rescue answering its halt on disk with a grant, then asking to rejoin; a
        # worker's request is unread, and the home one stands in for the person's.
        digest = hashlib.sha256(str(primary.resolve()).encode()).hexdigest()[:16]
        home = Path(os.environ["HOME"], ".mf-ship-origin", f"{digest}.queue")
        minions = primary / ".minions"
        for folder in (minions / "grants", minions / "runs/rejoin", home / "rejoin"):
            folder.mkdir(parents=True, exist_ok=True)
            (folder / change).touch()


def _supervise(tree: Path, primary: Path, change: str, modes: set[str]) -> None:
    """Amend the plan, the spec delta besides, hollowly or outside it, as decided.

    Or amend the prose undecided; `supervise-none` commits nothing. At an integrate
    note, stage a settle of the delta, or of code, and write the mark, uncommitted.
    """
    folder = f"openspec/changes/{change}"
    if modes & {"supervise-settle", "supervise-settle-code"}:
        if "supervise-settle" in modes:
            spec = tree / folder / "specs" / "sdd" / "spec.md"
            spec.write_text(spec.read_text() + "Settled.\n")
            _git(tree, "add", str(spec))
        else:
            (tree / "src.py").write_text("x = 1\n")
            _git(tree, "add", "src.py")
        mark = _folder(primary, change) / "integrate.settled"
        mark.write_text("sdd: First: the branch's block kept\n")
        return
    subject = f"docs({change}): amend the change directory\n\nfix\n\n"
    message = f"{subject}Supervisor: 1.1\nDecided-by: supervisor"
    tasks = f"{folder}/tasks.md"
    text = (tree / tasks).read_text()
    if "supervise-delta" in modes:
        spec = {f"{folder}/specs/sdd/spec.md": "## ADDED Requirements\n"}
        _commit(tree, {tasks: text + _AMENDED, **spec}, message)
    elif "supervise-hollow" in modes:
        _commit(tree, {tasks: text + "Look again.\n"}, message)
    elif "supervise-test" in modes:
        test = {"tests/test_todo.py": "x = 1\n"}
        _commit(tree, {tasks: text + _AMENDED, **test}, message)
    elif "supervise-undecided" in modes:
        design = tree / folder / "design.md"
        prose = (design.read_text() if design.is_file() else "") + _PROSE
        _commit(tree, {f"{folder}/design.md": prose}, f"{subject}Supervisor: R1")


# A fenced brief table opens it, so the station must skip a quoted example.
_PACKAGES = """\
# design

```markdown
## Dependencies
| item | package | constraint | why |
|---|---|---|---|
| first-call | livekit-client | ^2.5.0 | the browser's audio |
```

## Dependencies
| package | constraint | why |
|---|---|---|
| left-pad | 1.3.0 | a pad |
| right-pad | ^2 | a pad |
"""


def _cut(tree: Path, primary: Path, change: str, prompt: str, modes: set[str]) -> None:
    """Commit the change directory, write its models file; or halt, die, fall short."""
    folder = _folder(primary, change)
    folder.mkdir(parents=True, exist_ok=True)
    if "dies-cut" in modes:
        sys.exit(1)
    if "cut-halts" in modes:
        halt = f"{change} waits on one doubt: two readings · tasks.md:3\n"
        (folder / "cut.halt").write_text(halt)
        return
    found = re.search(
        rf"`{change} (\w+) brief=\S+(?: after=(\S+))?(?: beside=(\S+))? ", prompt
    )
    bump, after, beside = found.groups() if found else ("minor", None, None)
    line = f"after: [{after.replace(',', ', ')}]\n" if after else ""
    line += f"beside: [{beside.replace(',', ', ')}]\n" if beside else ""
    spec = f"openspec/changes/{change}"
    files = {
        f"{spec}/proposal.md": f"---\nbump: {bump}\n{line}---\n",
        f"{spec}/design.md": "## Dependencies\n\nNone.\n",
        f"{spec}/tasks.md": "## Progress\n\n- [ ] 1 — One\n",
    }
    if "cut-packages" in modes:
        files[f"{spec}/design.md"] = _PACKAGES
    if "cut-prose" in modes:
        files[f"{spec}/design.md"] = "## Dependencies\n\nleft-pad, any version\n"
    if "cut-twice" in modes:
        listed = _PACKAGES.partition("```\n\n")[2]
        files[f"{spec}/design.md"] = f"## Dependencies\n\nNone.\n\n{listed}"
    if "cut-empty" in modes:
        files = {"cut.txt": "x\n"}
    _commit(tree, files, f"docs({change}): land the change directory")
    if "cut-dirty" in modes:
        (tree / "stray.txt").write_text("x\n")
    if "cut-bare" not in modes:
        switch = 'decide = "recommended"\n' if "cut-decides" in modes else ""
        (folder / "models.toml").write_text(f"{switch}[build]\n[converge]\n[release]\n")


_USAGE = {"input_tokens": 1000, "cached_input_tokens": 400, "output_tokens": 100}
_PROBE = "converge's conformance checker for change 0001-probe"
# A converge worker's prompt opens on its role, change and round lines.
_ROLE = re.compile(r"\Arole: (\S+)\nchange: (\S+)\nround: (\d+)\n")
_RANGE = re.compile(r"\b([0-9a-f]{7,40})\.\.([0-9a-f]{7,40})\b")
_BLOCKS = {"conformance": ("blocking",), "adversarial": ("critical", "high")}
# Each caps on blockers of its size; `cap-again` and `grant-halts` keep them through a
# granted round.
_CAPS = {
    "cap-small": "a test",
    "cap-design": "a design change",
    "cap-again": "a test",
    "grant-halts": "a design change",
}
_KEPT = ("cap-again", "grant-halts")
_HELD = ("verified", "accepted")


def _card(
    card: str, severity: str, role: str, fix: str, status: str, amend: str = "no"
) -> str:
    """Return one findings card, its fields as the worker reference names them."""
    category = "security" if role == "adversarial" else "stability"
    return (
        f"- **{card} — a finding**\n"
        f"  - **Priority:** {severity} · {role} · {category} — why.\n"
        "  - **What it affects:** `total.py:12`\n"
        f"  - **Fix:** {fix}\n"
        f"  - **Amend:** {amend}\n"
        f"  - **Status:** {status}\n"
    )


def _cards_of(text: str) -> list[str]:
    """Return each card of a findings file's text, its title and indented lines."""
    blocks: list[list[str]] = []
    current: list[str] | None = None
    for line in text.splitlines(keepends=True):
        if line.startswith("- **"):
            current = [line]
            blocks.append(current)
        elif current is not None and line.startswith((" ", "\t")):
            current.append(line)
        else:
            current = None
    return ["".join(block) for block in blocks]


def _blocking(cards: list[str], role: str) -> int:
    """Return the `cards` that block on `role`'s scale, unverified and unaccepted."""
    count = 0
    for card in cards:
        severity = re.search(r"\*\*Priority:\*\* (\w+)", card)
        status = re.search(r"\*\*Status:\*\* (\w+)", card)
        if severity and status and severity[1] in _BLOCKS[role]:
            count += status[1] not in _HELD
    return count


def _write(
    path: Path,
    here: Path,
    role: str,
    change: str,
    round_: str,
    span: tuple[str, str],
    cards: list[str],
) -> None:
    """Write a findings file to the contract: `span`'s scope, its cards' verdict."""
    checked = role.removeprefix("shadow-")
    base, head = span
    blocking = _blocking(cards, checked)
    keys: dict[str, object] = {
        "type": checked,
        "plan": change,
        "project": "fake",
        "branch": _git(here, "branch", "--show-current"),
        "head": head,
        "reviewed": "2026-11-09",
        "round": round_,
        "open_blocking": blocking,
        "verdict": "changes-requested" if blocking else "clean",
        "mode": "parallel",
        "workers": 1,
        "files": len(_git(here, "diff", "--name-only", base, head).splitlines()),
        "commits": _git(here, "rev-list", "--count", f"{base}..{head}"),
    }
    if checked == "conformance":
        keys["passes"] = "[stale-claim, test-cost, no-removed-test]"
    keys |= {
        "inconclusive": "[]",
        "model": "fake",
        "executor": os.environ.get("FAKE_HOST", "claude"),
        "packet": "diff.patch",
    }
    front = "".join(f"{key}: {value}\n" for key, value in keys.items())
    body = "".join(cards)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\n{front}---\n\n## Summary\n\nJudged.\n\n{body}\n## Resolution log\n"
    )


def _judged_cards(here: Path, role: str, change: str, modes: set[str]) -> list[str]:
    """Return the cards a round-1 checker of `role` finds, as `modes` say."""
    sizes = [_CAPS[mode] for mode in _CAPS if mode in modes]
    if sizes and role == "conformance":
        return [
            _card("R1", "blocking", role, "a fix · size: one line.", "open"),
            _card("R2", "nit", role, "a fix · size: a design change.", "open"),
            _card("R3", "blocking", role, "a fix · size: one line.", "verified — held"),
        ]
    if sizes:
        return [
            _card("S1", "high", role, f"a fix · size: {sizes[0]}.", "open"),
            _card("S2", "medium", role, "a fix · size: a design change.", "open"),
        ]
    if "amend-halts" in modes and role == "conformance" and not _prose(here, change):
        fix = f"amend `openspec/changes/{change}/design.md`'s prose · size: one line."
        return [_card("R1", "blocking", role, fix, "open", amend="yes")]
    return []


def _judge(
    here: Path, role: str, change: str, round_: str, span: tuple[str, str], path: Path
) -> None:
    """Write a checker's findings file, or a shadow's, as `FAKE_MODE` says.

    `hold-converge-<change>` waits for `FAKE_HOLD`; `checker-sleep` waits a minute;
    `dies-converge` exits 1; `plant-executor` plants a models file first.
    """
    modes = set(os.environ["FAKE_MODE"].split(","))
    if f"hold-converge-{change}" in modes:
        hold, deadline = Path(os.environ["FAKE_HOLD"]), time.monotonic() + 60
        while not hold.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
    if "checker-sleep" in modes:
        time.sleep(60)
    if "dies-converge" in modes:
        sys.exit(1)
    common = _git(here, "rev-parse", "--path-format=absolute", "--git-common-dir")
    primary = Path(common).parent
    if "plant-executor" in modes:
        table = _folder(primary, change) / "models.toml"
        table.write_text('[release]\nexecutor = "codex"\n')
    if path.name.startswith("shadow-"):
        cards = []
        if "shadow-blocks" in modes:
            name, grade = (
                ("S1", "high") if role == "adversarial" else ("R1", "blocking")
            )
            cards = [_card(name, grade, role, "a fix · size: one line.", "open")]
        _write(path, here, f"shadow-{role}", change, round_, span, cards)
    else:
        cards = _judged_cards(here, role, change, modes)
        _write(path, here, role, change, round_, span, cards)
    print(json.dumps({"type": "turn.completed", "usage": _USAGE}), flush=True)


def _verify(
    here: Path, change: str, round_: str, span: tuple[str, str], paths: list[Path]
) -> None:
    """Rewrite each findings file at the fix's head, its fixed cards verified.

    A cap mode keeps every card through round 3, and `_KEPT`'s through a granted
    round too; an amend card's `wontfix` stays.
    """
    modes = set(os.environ["FAKE_MODE"].split(","))
    capped = any(mode in modes for mode in _CAPS)
    kept = any(mode in modes for mode in _KEPT)
    keep = kept or (capped and int(round_) < 4)
    for path in paths:
        role = path.stem
        cards = _cards_of(path.read_text() if path.is_file() else "")
        if not keep:
            cards = [
                re.sub(
                    r"\*\*Status:\*\* (open|fixed)\b.*", "**Status:** verified", card
                )
                for card in cards
            ]
        _write(path, here, role, change, round_, span, cards)
    print(json.dumps({"type": "turn.completed", "usage": _USAGE}), flush=True)


def _fix(here: Path, primary: Path, change: str, round_: str, ids: str) -> None:
    """Commit a fix and mark the cards `fixed`, or idle, as `FAKE_MODE` says; report.

    A cap mode commits nothing; `amend-halts` sets its amend card `wontfix`; a
    granted round's fixer, past round 2, dies under `grant-unfinished`.
    """
    modes = set(os.environ["FAKE_MODE"].split(","))
    if "grant-unfinished" in modes and int(round_) > 2:
        sys.exit(1)
    folder = _folder(primary, change)
    sent = [each.strip() for each in ids.split(";")[0].split(",")]
    fixed, wontfix, commit = "none", "none", "nothing committed"
    if "amend-halts" in modes and not _prose(here, change):
        conformance = folder / "conformance.md"
        why = "**Status:** wontfix — needs the amend of design.md's prose"
        text = conformance.read_text().replace("**Status:** open", why)
        conformance.write_text(text)
        wontfix = "R1"
    elif not any(mode in modes for mode in _CAPS):
        _commit(here, {f"fixes/r{round_}.txt": f"{ids}\n"}, f"fix({change}): {ids}")
        commit = _git(here, "rev-parse", "--short", "HEAD")
        fixed = ", ".join(sent)
        for role in ("conformance", "adversarial"):
            path = folder / f"{role}.md"
            if not path.is_file():
                continue
            text = path.read_text()
            for card in _cards_of(text):
                title = re.match(r"- \*\*(\S+) — ", card)
                if title and title[1] in sent:
                    done = card.replace("**Status:** open", "**Status:** fixed")
                    text = text.replace(card, done)
            path.write_text(text)
    (folder / "fix.md").write_text(
        f"fixed: {fixed}\nwontfix: {wontfix}\ncommit: {commit}\nplan check left: none\n"
    )


def _rewrite(here: Path, role: str, change: str, round_: str, path: Path) -> None:
    """Rewrite a malformed findings file to the contract, its cards kept."""
    text = path.read_text() if path.is_file() else ""
    head = re.search(r"^head: (\S+)$", text, re.MULTILINE)
    now = head[1] if head else _git(here, "rev-parse", "HEAD")
    base = _git(here, "merge-base", "main", now)
    cards = [
        card if "**Amend:**" in card else card + "  - **Amend:** no\n"
        for card in _cards_of(text)
    ]
    _write(path, here, role, change, round_, (base, now), cards)


def _converge_worker(prompt: str, found: re.Match[str]) -> None:
    """Play the one converge worker the prompt's role line names; log its call.

    The station is the checker, its shadow, a verify worker, the fixer or a rewrite
    worker, read from the prompt; `liar-<change>` writes nothing.
    Why: 0108-converge-script design D8.
    """
    role, change, round_ = found.groups()
    here = Path.cwd()
    common = _git(here, "rev-parse", "--path-format=absolute", "--git-common-dir")
    primary = Path(common).parent
    written = re.search(r"Your findings file, the one file you write: (\S+)", prompt)
    path = Path(written[1]) if written else None
    span = _RANGE.search(prompt)
    ends = (span[1], span[2]) if span else ("HEAD", "HEAD")
    if "You are converge's fixer" in prompt:
        station = f"converge-fix-r{round_}"
    elif "You are the verify worker" in prompt:
        station = f"converge-verify-{role}-r{round_}"
    elif "Rewrite that file to the contract" in prompt:
        station = f"converge-rewrite-{role}-r{round_}"
    elif path is not None and path.name.startswith("shadow-"):
        station = f"converge-shadow-{role}-r{round_}"
    else:
        station = f"converge-{role}-r{round_}"
    modes = set(os.environ["FAKE_MODE"].split(","))
    with open(os.environ["FAKE_CALLS"], "a") as calls:
        calls.write(f"{station} {change}\n")
    if f"liar-{change}" in modes:
        return
    if station.startswith("converge-fix-"):
        ids = re.search(r"The cards to clear, by id: (.+)", prompt)
        _fix(here, primary, change, round_, ids[1] if ids else "")
    elif station.startswith("converge-verify-"):
        listed = re.search(
            r"Your findings file, or a pickup check's files: (.+)", prompt
        )
        paths = [Path(each) for each in (listed[1] if listed else "").split(" and ")]
        _verify(here, change, round_, ends, paths)
    elif station.startswith("converge-rewrite-"):
        broken = re.search(r"Your findings file (\S+) breaks", prompt)
        _rewrite(here, role, change, round_, Path(broken[1] if broken else ""))
    elif path is not None:
        _judge(here, role, change, round_, ends, path)


def _probe_checker(here: Path, modes: set[str]) -> None:
    """Write the probe checker's findings file, requesting changes, every key in it.

    `checker-silent` writes none. Why: 0096-codex-ready design D9.
    """
    if "checker-silent" in modes:
        return
    keys = {
        "type": "conformance",
        "plan": "0001-probe",
        "project": "fake",
        "branch": _git(here, "branch", "--show-current"),
        "head": _git(here, "rev-parse", "HEAD"),
        "reviewed": "2026-11-08",
        "round": "1",
        "open_blocking": "1",
        "verdict": "changes-requested",
        "mode": "parallel",
        "workers": "1",
        "model": "fake",
        "executor": os.environ.get("FAKE_HOST", "claude"),
        "packet": "diff.patch",
    }
    folder = _folder(here, "0001-probe")
    folder.mkdir(parents=True, exist_ok=True)
    front = "".join(f"{key}: {value}\n" for key, value in keys.items())
    (folder / "conformance.md").write_text(f"---\n{front}---\n")
    print(json.dumps({"type": "turn.completed", "usage": _USAGE}), flush=True)


def _fake(prompt: str) -> None:
    """Do on disk what the station the prompt names would, as `FAKE_MODE` says."""
    modes = set(os.environ["FAKE_MODE"].split(","))
    here = Path.cwd()
    if role_line := _ROLE.match(prompt):
        _converge_worker(prompt, role_line)
        return
    found = re.search(r"Run the mf-([a-z-]+) skill(?: for change (\S+?)[ .])?", prompt)
    station, change = (found[1], found[2]) if found else ("probe", None)
    if _PROBE in prompt:
        station = "checker"
    # Every key=value clause but the one every release prompt carries.
    clauses = "".join(re.findall(r" (?:with|and) (?!merge=yes\b)\w+=\w+", prompt))
    if station == "supervise" and (brief := re.search(r" and brief=(\S+)\.\s", prompt)):
        clauses += f" and brief={Path(brief[1]).name}"
    with open(os.environ["FAKE_CALLS"], "a") as calls:
        called = f"{station} {change}" if change else station
        calls.write(f"{called}{clauses}\n")
    if station == "checker":
        _probe_checker(here, modes)
        return
    phase = re.search(r" with phase=(\w+)", prompt) if station == "build" else None
    if station == "build" and "deny" in modes and not (phase and phase[1] == "close"):
        use = {
            "type": "tool_use",
            "id": "t1",
            "name": "Bash",
            "input": {"command": "rm -rf build"},
        }
        result = {
            "type": "tool_result",
            "tool_use_id": "t1",
            "is_error": True,
            "content": "Bash has been denied.",
        }
        blocks = [use, result]
        if "heredoc" in modes:
            command = 'git commit -m "$(cat <<EOF\nbuild\nEOF\n)"'
            blocks += [
                {**use, "id": "t2", "input": {"command": command}},
                {**result, "tool_use_id": "t2"},
            ]
        for block in blocks:
            print(json.dumps({"message": {"content": [block]}}))
    if station == "build" and "missing-tool" in modes:
        use = {"type": "tool_use", "id": "t1", "name": "Agent", "input": {}}
        result = {
            "type": "tool_result",
            "tool_use_id": "t1",
            "is_error": True,
            "content": "<tool_use_error>No such tool available: Agent</tool_use_error>",
        }
        for block in (use, result):
            print(json.dumps({"message": {"content": [block]}}))
    if station == "build" and "dies-limit" in modes:
        event = {
            "type": "result",
            "is_error": True,
            "api_error_status": 429,
            "result": "You've hit your limit · resets 5:50pm (Europe/Athens)",
        }
        print(json.dumps(event))
        sys.exit(1)
    if station == "build" and "sleep" in modes:
        time.sleep(60)
    if station == "build" and f"slow-{change}" in modes:
        time.sleep(2)
    if station == "build" and f"hold-{change}" in modes:
        hold, deadline = Path(os.environ["FAKE_HOLD"]), time.monotonic() + 60
        while not hold.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
    if station == "build" and (script := os.environ.get("FAKE_SCRIPT")):
        Path(script).write_text("raise OSError('planted')\n")
    if f"liar-{change or station}" in modes:
        return
    if station == "build" and "liar" in modes:
        return
    common = _git(here, "rev-parse", "--path-format=absolute", "--git-common-dir")
    primary = Path(common).parent
    if station == "probe":
        if "mcp" in modes:
            servers = [
                {"name": "runpod", "status": "connected", "source": "user"},
                {"name": "claude.ai Claude Docs", "status": "connected"},
            ]
            init = {"type": "system", "subtype": "init", "mcp_servers": servers}
            print(json.dumps(init))
        if "first-turn" in modes:
            usage = {
                "input_tokens": 3,
                "cache_read_input_tokens": 15000,
                "cache_creation_input_tokens": 4000,
            }
            print(json.dumps({"type": "assistant", "message": {"usage": usage}}))
        sandboxed = "unsandboxed" not in modes
        # The sandbox's stand-in: a read-only mark refuses the gate's write out.
        if sandboxed:
            for mark in Path(os.environ["HOME"], ".mf-ship-origin").glob("probe-*"):
                mark.chmod(0o400)
        _commit(here, {"probe.txt": "ok\n"}, "probe")
        # A Codex probe's linked tree: `tree-silent` leaves its index unwritten.
        if "git write-tree in tree/" in prompt and "tree-silent" not in modes:
            tree = here / "tree"
            made = subprocess.run(
                ["git", "write-tree"], cwd=tree, capture_output=True, text=True
            )
            (tree / "tree.txt").write_text(made.stdout)
        translated = "translated" in modes
        with tempfile.TemporaryDirectory(prefix="fake-uname-") as folder:
            env = dict(os.environ)
            # A translated shell's stand-in: a `uname` first on `PATH` names another.
            if translated:
                uname = Path(folder, "uname")
                uname.write_text("#!/bin/sh\necho i386\n")
                uname.chmod(0o755)
                env["PATH"] = f"{folder}{os.pathsep}{env['PATH']}"
            subprocess.run(
                ["make", "gate"],
                cwd=here,
                env=env,
                capture_output=True,
                check=sandboxed and not translated,
            )
    elif station == "rescue":
        _rescue(here, primary, str(change), modes)
    elif station == "supervise":
        _supervise(here, primary, str(change), modes)
    elif station == "cut-change":
        _cut(here, primary, str(change), prompt, modes)
    elif phase is not None:
        _phase(here, primary, str(change), phase[1], modes)
    elif (
        station == "build" and f"halt-{change}" in modes and not _amended(here, change)
    ):
        folder = _folder(primary, str(change))
        folder.mkdir(parents=True, exist_ok=True)
        head = _git(here, "rev-parse", "HEAD")
        (folder / "build.halt").write_text(
            f"sub-task: 1.1\nstop: 3\nevidence: two readings\nhead: {head}\n"
        )
    elif station == "build":
        tasks = here / "openspec" / "changes" / str(change) / "tasks.md"
        # A build ticks each phase before the first unticked HUMAN one, and stops there.
        lines = tasks.read_text().splitlines(keepends=True)
        human = [i for i, line in enumerate(lines) if "[ ]" in line and "HUMAN" in line]
        stop = human[0] if human else len(lines)
        built = "".join(lines[:stop])
        files = {str(tasks): built.replace("- [ ]", "- [x]") + "".join(lines[stop:])}
        if f"after-self-{change}" in modes:
            proposal = f"---\nbump: minor\nafter: [{change}]\n---\n"
            files[str(tasks.with_name("proposal.md"))] = proposal
        if "- [ ]" in built:
            _commit(here, files, "build")
        if human:
            return
        if "dies-simplify" in modes:
            sys.exit(1)
        _closed(here, primary, str(change), modes)
    elif station == "integrate":
        message = f"chore(integrate): merge main into {change}"
        settled = "with settled=supervisor" in prompt
        folder = _folder(primary, str(change)) if settled else None
        _integrate(primary.parent / str(change), message, modes, folder)
    elif station == "release":
        branch = _git(here, "branch", "--show-current")
        tag = f"v0.{len(_git(here, 'tag', '-l').split()) + 1}.0"
        subject = _git(here, "log", "-1", "--format=%s")
        if subject.startswith("chore(release): "):
            named = subject.removeprefix("chore(release): ")
            if not _git(here, "tag", "-l", named):
                _git(here, "tag", named)
        else:
            _git(here, "restore", "--source=HEAD", "--staged", "--worktree", "--", ".")
            (here / "openspec" / "changes" / "archive").mkdir(exist_ok=True)
            _git(
                here,
                "mv",
                f"openspec/changes/{change}",
                f"openspec/changes/archive/{change}",
            )
            if "dies-release-fold" in modes:
                sys.exit(1)
            _git(here, "commit", "-q", "-m", f"chore(release): {tag}")
            if "dies-release-commit" in modes:
                sys.exit(1)
            _git(here, "tag", tag)
            if "dies-release-tag" in modes:
                sys.exit(1)
            if "stops-release-tag" in modes:
                return
        _git(
            primary, "merge", "-q", "--no-ff", "-m", f"Merge branch '{branch}'", branch
        )
        if "plant-config" in modes:
            _git(primary, "config", "pull.rebase", "true")
        if "plant-held" in modes:
            _git(primary, "config", "mf.planted", "x")
        if "plant-origin" in modes:
            elsewhere = str(primary.parent / "elsewhere.git")
            _git(primary, "remote", "set-url", "origin", elsewhere)
        if "plant-attributes" in modes:
            (Path(common) / "info").mkdir(exist_ok=True)
            (Path(common) / "info" / "attributes").write_text("* filter=x\n")


if __name__ == "__main__":
    _fake(sys.argv[1])
