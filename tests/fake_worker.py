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


def _findings(root: Path, change: str, head: str, verdict: str = "clean") -> None:
    folder = _folder(root, change)
    folder.mkdir(parents=True, exist_ok=True)
    for role in ("review", "security"):
        text = f"---\nverdict: {verdict}\nhead: {head}\nround: 1\n---\n"
        (folder / f"{role}.md").write_text(text)
    log = folder / "status_log.md"
    log.write_text("# t\n\n## Run 1 — d\n10:00:00 · round 1 · done — ok\n")


def _cards(
    root: Path, change: str, head: str, size: str, granted: bool = False
) -> None:
    """Write both findings files capped at `head`, security's open blocker sized `size`.

    Review's open blocker is sized `one line`; a nit, a `medium` and a verified
    blocker, each sized `a design change`, block nothing. A `granted` round's run is
    marked `· grant`, as `mf-converge` marks it.
    """
    folder = _folder(root, change)
    folder.mkdir(parents=True, exist_ok=True)
    cards = {
        "review": [
            ("R1", "blocking", "one line", "open"),
            ("R2", "nit", "a design change", "open"),
            ("R3", "blocking", "a design change", "verified — held"),
        ],
        "security": [
            ("S1", "high", size, "open"),
            ("S2", "medium", "a design change", "open"),
        ],
    }
    for role, listed in cards.items():
        text = f"---\nverdict: changes-requested\nhead: {head}\nround: 3\n---\n\n"
        for card, severity, fix, status in listed:
            text += (
                f"- **{card} — a finding**\n"
                f"  - **Priority:** {severity} · {role} · stability — why.\n"
                f"  - **Fix:** a fix · size: {fix}.\n"
                f"  - **Status:** {status}\n"
            )
        (folder / f"{role}.md").write_text(text)
    run = "## Run 2 — d · grant\n" if granted else "## Run 1 — d\n"
    log = folder / "status_log.md"
    log.write_text(f"# t\n\n{run}10:00:00 · round 3 · halt — cap reached\n")


def _amend_needed(root: Path, change: str, head: str, card: str = "R1") -> None:
    """Write converge's `amend needed — <card>` halt at `head`, after round 1's start.

    The card is `wontfix`, naming a `design.md` prose amend: review's `blocking`, or
    security's `high` for an `S` id. The other findings file is clean.
    """
    folder = _folder(root, change)
    folder.mkdir(parents=True, exist_ok=True)
    role, severity = ("security", "high") if card[0] == "S" else ("review", "blocking")
    for name in ("review", "security"):
        verdict = "changes-requested" if name == role else "clean"
        text = f"---\nverdict: {verdict}\nhead: {head}\nround: 1\n---\n"
        if name == role:
            text += (
                f"\n- **{card} — a finding**\n"
                f"  - **Priority:** {severity} · {role} · stability — why.\n"
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


def _person_amends(tree: Path, change: str, sha: str) -> bool:
    """Return whether `sha` is the person's amend of the change directory."""
    subject = _git(tree, "log", "-1", "--format=%s", sha)
    listed = ("diff-tree", "--root", "-r", "--no-commit-id", "--name-only", sha)
    folder = f"openspec/changes/{change}/"
    return subject == f"docs({change}): amend the change directory" and all(
        path.startswith(folder) for path in _git(tree, *listed).split()
    )


def _by_rule(tree: Path, folder: Path, change: str) -> list[str] | None:
    """Return a line per commit when a catch-up selects merges that replay and amends.

    A merge's line is its `replay` line; an amend's names the person's amend. None
    when no catch-up applies, the selection holds another commit, or one exits 1.
    """
    review = folder / "review.md"
    text = review.read_text() if review.is_file() else ""
    found = re.search(r"^head: (\S+)$", text, re.MULTILINE)
    head = _git(tree, "rev-parse", "HEAD")
    if not found or found[1] == head:
        return None
    span = f"{found[1]}..HEAD"
    selected = _git(tree, "rev-list", "--first-parent", span).split()
    merges = _git(tree, "rev-list", "--first-parent", "--merges", span).split()
    if not selected or not all(
        sha in merges or _person_amends(tree, change, sha) for sha in selected
    ):
        return None
    script = Path(__file__).resolve().parent.parent / "skills" / "mf-integrate"
    lines = []
    for sha in selected:
        if sha not in merges:
            lines.append(f"- {sha} — the person's amend")
            continue
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
    for role in ("review", "security"):
        text = f"---\nverdict: clean\nhead: {head}\nround: 2\nworkers: 0\n---\n"
        text += "\n## By rule\n\n" + "\n".join(lines) + "\n"
        (folder / f"{role}.md").write_text(text)
    paths = "; ".join(line.split(" — ", 1)[1] for line in lines)
    (folder / "status_log.md").write_text(
        "# t\n\n## Run 2 — d · catch-up\n10:00:01 · round 2 · done — ok\n"
        f"10:00:00 · round 2 · by rule — clean, {paths}\n"
    )


def _integrate(tree: Path, message: str, modes: set[str]) -> None:
    """Merge `main` into `tree`, or finish a merge a dead worker left open."""
    if _git(tree, "rev-parse", "-q", "--verify", "MERGE_HEAD", check=False):
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
    found = re.search(rf"`{change} (\w+) brief=\S+(?: after=(\S+))? ", prompt)
    bump, after = (found[1], found[2]) if found else ("minor", None)
    line = f"after: [{after.replace(',', ', ')}]\n" if after else ""
    spec = f"openspec/changes/{change}"
    files = {
        f"{spec}/proposal.md": f"---\nbump: {bump}\n{line}---\n",
        f"{spec}/tasks.md": "## Progress\n\n- [ ] 1 — One\n",
    }
    if "cut-empty" in modes:
        files = {"cut.txt": "x\n"}
    _commit(tree, files, f"docs({change}): land the change directory")
    if "cut-dirty" in modes:
        (tree / "stray.txt").write_text("x\n")
    if "cut-bare" not in modes:
        (folder / "models.toml").write_text("[build]\n[converge]\n[release]\n")


def _fake(prompt: str) -> None:
    """Do on disk what the station the prompt names would, as `FAKE_MODE` says."""
    modes = set(os.environ["FAKE_MODE"].split(","))
    here = Path.cwd()
    found = re.search(r"Run the mf-([a-z-]+) skill(?: for change (\S+?)[ .])?", prompt)
    station, change = (found[1], found[2]) if found else ("probe", None)
    # Every key=value clause but the one every release prompt carries.
    clauses = "".join(re.findall(r" (?:with|and) (?!merge=yes\b)\w+=\w+", prompt))
    with open(os.environ["FAKE_CALLS"], "a") as calls:
        called = f"{station} {change}" if change else station
        calls.write(f"{called}{clauses}\n")
    if station == "build" and "deny" in modes:
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
    elif station == "cut-change":
        _cut(here, primary, str(change), prompt, modes)
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
        _done(primary, str(change), _git(here, "rev-parse", "HEAD"))
        if "person-commits" in modes:
            _commit(primary, {"mine.txt": "x\n"}, "a person's commit")
        if "plant-network" in modes:
            agents = primary / "AGENTS.md"
            line = "- **Ship network:** `later.example`\n"
            agents.write_text(agents.read_text() + line)
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
        # Step 1's halts before `start`: a `Verify:` edited since the cut, a red gate.
        before = {
            "verify-halts": "verify: halt — 1.1",
            "red-halts": "gate red before round 1",
        }
        if reason := next((before[mode] for mode in before if mode in modes), None):
            head = _git(here, "rev-parse", "HEAD")
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "status_log.md").write_text(
                "# t\n\n## Run 1 — d\n"
                f"10:00:00 · round 1 · halt — {reason} · head {head}\n"
            )
            return
        if "by-rule" in modes and (lines := _by_rule(here, folder, str(change))):
            _write_by_rule(folder, _git(here, "rev-parse", "HEAD"), lines)
            return
        log = folder / "status_log.md"
        held = log.read_text() if log.is_file() else ""
        _findings(primary, str(change), _git(here, "rev-parse", "HEAD"))
        if "amends" in modes or "amend-halts" in modes:
            run = "## Run 2 — d · amended\n10:00:00 · round 1 · done — ok\n\n"
            log.write_text(held.replace("## Run", run + "## Run", 1))
        if "dies-converge" in modes:
            log.write_text("# t\n\n## Run 1 — d\n10:00:00 · round 1 · pickup — R1\n")
            sys.exit(1)
    elif station == "integrate":
        message = f"chore(integrate): merge main into {change}"
        _integrate(primary.parent / str(change), message, modes)
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
