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
        text = f"---\nverdict: {verdict}\nhead: {head}\nround: {round}\n---\n"
        (folder / f"{role}.md").write_text(text)
    log = folder / "status_log.md"
    log.write_text("# t\n\n## Run 1 — d\n10:00:00 · round 1 · done — ok\n")


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
    categories = {"conformance": "stability", "adversarial": "security"}
    for role, listed in cards.items():
        text = f"---\nverdict: changes-requested\nhead: {head}\nround: 3\n---\n\n"
        for card, severity, fix, status in listed:
            text += (
                f"- **{card} — a finding**\n"
                f"  - **Priority:** {severity} · {role} · {categories[role]} — why.\n"
                f"  - **Fix:** a fix · size: {fix}.\n"
                f"  - **Status:** {status}\n"
            )
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
    role, severity, category = (
        ("adversarial", "high", "security")
        if card[0] == "S"
        else ("conformance", "blocking", "stability")
    )
    for name in ("conformance", "adversarial"):
        verdict = "changes-requested" if name == role else "clean"
        text = f"---\nverdict: {verdict}\nhead: {head}\nround: 1\n---\n"
        if name == role:
            text += (
                f"\n- **{card} — a finding**\n"
                f"  - **Priority:** {severity} · {role} · {category} — why.\n"
                "  - **Fix:** amend design.md's prose · size: one line.\n"
                "  - **Status:** wontfix — needs the amend of design.md's prose\n"
            )
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
    """Tick one phase's boxes in one commit, or close; halt, idle or die as told.

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


def _by_rule(tree: Path, folder: Path) -> list[str] | None:
    """Return a line per merge when a catch-up selects merges alone, each replaying."""
    conformance = folder / "conformance.md"
    text = conformance.read_text() if conformance.is_file() else ""
    found = re.search(r"^head: (\S+)$", text, re.MULTILINE)
    head = _git(tree, "rev-parse", "HEAD")
    if not found or found[1] == head:
        return None
    span = f"{found[1]}..HEAD"
    selected = _git(tree, "rev-list", "--first-parent", span).split()
    merges = _git(tree, "rev-list", "--first-parent", "--merges", span).split()
    if not selected or not all(sha in merges for sha in selected):
        return None
    script = Path(__file__).resolve().parent.parent / "skills" / "mf-integrate"
    lines = []
    for sha in selected:
        done = subprocess.run(
            [sys.executable, str(script / "scripts" / "integrate.py"), "replay", sha],
            cwd=tree,
            capture_output=True,
            text=True,
        )
        if done.returncode != 0:
            return None
        lines.append(f"- {sha}: {done.stdout.strip().removeprefix('replay: ')}")
    return lines


def _write_by_rule(folder: Path, head: str, lines: list[str]) -> None:
    """Write both findings files clean at `head` with `## By rule`; log the round."""
    for role in ("conformance", "adversarial"):
        text = f"---\nverdict: clean\nhead: {head}\nround: 2\nworkers: 0\n---\n"
        text += "\n## By rule\n\n" + "\n".join(lines) + "\n"
        (folder / f"{role}.md").write_text(text)
    paths = "; ".join(line.split(" — ", 1)[1] for line in lines)
    (folder / "status_log.md").write_text(
        "# t\n\n## Run 2 — d · catch-up\n10:00:01 · round 2 · done — ok\n"
        f"10:00:00 · round 2 · by rule — clean, {paths}\n"
    )


def _fix_surfaces(tree: Path, primary: Path, change: str) -> None:
    """Judge the head clean, commit a fix at `FAKE_FIX`, then judge it as Step 7 does.

    Adversarial takes the fix head by rule, `mode: by-rule`, when `surfaces.py` exits 0.
    """
    folder = _folder(primary, change)
    start = _git(tree, "rev-parse", "HEAD")
    _findings(primary, change, start)
    _commit(tree, {os.environ["FAKE_FIX"]: "fixed\n"}, "fix")
    end = _git(tree, "rev-parse", "HEAD")
    script = Path(__file__).resolve().parent.parent / "skills" / "mf-converge"
    done = subprocess.run(
        [sys.executable, str(script / "scripts" / "surfaces.py")]
        + [str(folder / "adversarial.md"), start, end],
        cwd=tree,
        capture_output=True,
        text=True,
    )
    # Read by its line, not its exit: a crash exits 1 too.
    said = done.stdout.split(" — ")[0].strip()
    mode = {"surfaces: no surface": "by-rule", "surfaces: verify": "parallel"}[said]
    _findings(primary, change, end, round=2)
    adversarial = folder / "adversarial.md"
    text = adversarial.read_text().replace("round: 2\n", f"round: 2\nmode: {mode}\n")
    adversarial.write_text(text)


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
_CHECKER = re.compile(r"converge's (\S+) checker for change (\S+?)[ .]")


def _front(here: Path, role: str, change: str, verdict: str, blocking: int) -> str:
    """Return a findings file's frontmatter with every key, the host `FAKE_HOST`."""
    keys = {
        "type": role.removeprefix("shadow-"),
        "plan": change,
        "project": "fake",
        "branch": _git(here, "branch", "--show-current"),
        "head": _git(here, "rev-parse", "HEAD"),
        "reviewed": "2026-11-08",
        "round": "1",
        "open_blocking": str(blocking),
        "verdict": verdict,
        "mode": "parallel",
        "workers": "1",
        "model": "fake",
        "executor": os.environ.get("FAKE_HOST", "claude"),
        "packet": "diff.patch",
    }
    return (
        "---\n" + "".join(f"{key}: {value}\n" for key, value in keys.items()) + "---\n"
    )


def _checker(here: Path, role: str, change: str, modes: set[str]) -> None:
    """Write a checker's findings file with every key, and a usage event.

    The probe's, for `0001-probe`, requests changes; `checker-silent` writes none. A
    shadow's blocks under `shadow-blocks`. Why: 0096-codex-ready design D9;
    0097-cross-model design D7.
    """
    if change == "0001-probe":
        if "checker-silent" in modes:
            return
        root, verdict, blocking, card = here, "changes-requested", 1, ""
    else:
        common = _git(here, "rev-parse", "--path-format=absolute", "--git-common-dir")
        root, verdict, blocking, card = Path(common).parent, "clean", 0, ""
        if role.startswith("shadow-") and "shadow-blocks" in modes:
            adversarial = role.endswith("adversarial")
            name, grade = ("S1", "high") if adversarial else ("R1", "blocking")
            verdict, blocking = "changes-requested", 1
            card = (
                f"\n- **{name} — a finding**\n"
                f"  - **Priority:** {grade} · {role[7:]} · stability — why.\n"
                "  - **What it affects:** `total.py:12`\n"
                "  - **Fix:** a fix · size: one line.\n"
                "  - **Status:** open\n"
            )
    folder = _folder(root, change)
    folder.mkdir(parents=True, exist_ok=True)
    front = _front(here, role, change, verdict, blocking)
    (folder / f"{role}.md").write_text(front + card)
    print(json.dumps({"type": "turn.completed", "usage": _USAGE}), flush=True)


def _mailed(here: Path, primary: Path, change: str, roles: list[str]) -> None:
    """Send each role through `conduct.py checker`, as converge's conductor does.

    A failed send ends the fake converge with 1, save a shadow's.
    Why: 0097-cross-model design D7.
    """
    conduct = Path(__file__).resolve().parent.parent / "skills" / "mf-ship" / "scripts"
    for role in roles:
        prompt = f"You are converge's {role} checker for change {change}.\n"
        _folder(primary, change).mkdir(parents=True, exist_ok=True)
        (_folder(primary, change) / f"{role}.prompt.md").write_text(prompt)
        done = subprocess.run(
            [
                sys.executable,
                "-S",
                str(conduct / "conduct.py"),
                "checker",
                change,
                role,
            ],
            cwd=here,
            capture_output=True,
            text=True,
        )
        if done.returncode != 0 and not role.startswith("shadow-"):
            sys.exit(1)


def _fake(prompt: str) -> None:
    """Do on disk what the station the prompt names would, as `FAKE_MODE` says."""
    modes = set(os.environ["FAKE_MODE"].split(","))
    here = Path.cwd()
    found = re.search(r"Run the mf-([a-z-]+) skill(?: for change (\S+?)[ .])?", prompt)
    station, change = (found[1], found[2]) if found else ("probe", None)
    role = None
    if checked := _CHECKER.search(prompt):
        station, role, change = "checker", checked[1], checked[2]
    # Every key=value clause but the one every release prompt carries.
    clauses = "".join(re.findall(r" (?:with|and) (?!merge=yes\b)\w+=\w+", prompt))
    if station == "supervise" and (brief := re.search(r" and brief=(\S+)\.\s", prompt)):
        clauses += f" and brief={Path(brief[1]).name}"
    with open(os.environ["FAKE_CALLS"], "a") as calls:
        called = f"{station} {change}" if change else station
        if station == "checker":
            called = "checker" if change == "0001-probe" else f"checker {change} {role}"
        calls.write(f"{called}{clauses}\n")
    if station == "checker":
        _checker(here, str(role), str(change), modes)
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
    holds = {"build": f"hold-{change}", "converge": f"hold-converge-{change}"}
    if holds.get(station) in modes:
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
    elif station == "converge":
        if "plant-executor" in modes:
            table = _folder(primary, str(change)) / "models.toml"
            table.parent.mkdir(parents=True, exist_ok=True)
            table.write_text('[release]\nexecutor = "codex"\n')
        # Each caps on cards of its size; `cap-again` caps a granted round too.
        sizes = {
            "cap-small": "a test",
            "cap-design": "a design change",
            "cap-again": "a test",
        }
        capping = [sizes[mode] for mode in sizes if mode in modes]
        granted = "grant=yes" in clauses
        if capping and (not granted or "cap-again" in modes):
            head = _git(here, "rev-parse", "HEAD")
            _cards(primary, str(change), head, capping[0], granted)
            return
        if granted and "grant-unfinished" in modes:
            # A granted round whose host ended its turn mid-run: no `done`, exit 0.
            log = _folder(primary, str(change)) / "status_log.md"
            log.write_text(
                "# t\n\n## Run 2 — d · grant\n10:00:00 · round 4 · fix — R1\n"
            )
            return
        if "grant-halts" in modes:
            log = _folder(primary, str(change)) / "status_log.md"
            log.write_text(
                "# t\n\n## Run 2 — d\n10:00:00 · round 4 · halt — cap reached\n"
            )
            return
        if "amend-halts" in modes and not _prose(here, str(change)):
            _amend_needed(primary, str(change), _git(here, "rev-parse", "HEAD"))
            return
        folder = _folder(primary, str(change))
        log = folder / "status_log.md"
        held = log.read_text() if log.is_file() else ""
        head = _git(here, "rev-parse", "HEAD")
        if "verify-fails" in modes:
            # The amend round's amended `Verify:` fails before its `start`.
            run = (
                "## Run 2 — d · amend\n"
                f"10:00:00 · round 2 · halt — verify failed — 1.1 · head {head}\n\n"
            )
            log.write_text(held.replace("## Run", run + "## Run", 1))
            return
        # Step 1's halts before `start`: a `Verify:` edited since the cut, a red gate.
        before = {
            "verify-halts": "verify: halt — 1.1",
            "red-halts": "gate red before round 1",
        }
        if reason := next((before[mode] for mode in before if mode in modes), None):
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "status_log.md").write_text(
                "# t\n\n## Run 1 — d\n"
                f"10:00:00 · round 1 · halt — {reason} · head {head}\n"
            )
            return
        if "fix-surfaces" in modes:
            _fix_surfaces(here, primary, str(change))
            return
        if "by-rule" in modes and (lines := _by_rule(here, folder)):
            _write_by_rule(folder, head, lines)
            return
        if "amends" in modes or "amend-halts" in modes:
            conformance = folder / "conformance.md"
            text = conformance.read_text() if conformance.is_file() else ""
            found = re.search(r"^head: (\S+)$", text, re.MULTILINE)
            judged = found[1] if found else head
            _findings(primary, str(change), head, round=2)
            run = (
                "## Run 2 — d · amend\n10:00:01 · round 2 · done — ok\n"
                f"10:00:00 · round 2 · freeze — {judged}..{head}\n\n"
            )
            log.write_text(held.replace("## Run", run + "## Run", 1))
        else:
            mailed = re.findall(r" and (\w+)=mailbox\b", prompt)
            _mailed(here, primary, str(change), mailed)
            roles = ("conformance", "adversarial")
            alone = tuple(role for role in roles if role not in mailed)
            _findings(primary, str(change), head, roles=alone)
            if " and shadow=yes" in prompt:
                _mailed(here, primary, str(change), [f"shadow-{r}" for r in roles])
        if "dies-converge" in modes:
            log.write_text("# t\n\n## Run 1 — d\n10:00:00 · round 1 · pickup — R1\n")
            sys.exit(1)
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
