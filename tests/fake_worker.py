"""The fake agent `MF_SHIP_AGENT` names: it does on disk what a station would.

The standard library alone: it starts once per worker, and the suite spawns many.
Why: 0051-reliability-paydown design D9.
"""

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


def _findings(root: Path, change: str, head: str, verdict: str = "clean") -> None:
    folder = root / ".minions" / "findings"
    folder.mkdir(parents=True, exist_ok=True)
    for role in ("review", "security"):
        text = f"---\nverdict: {verdict}\nhead: {head}\nround: 1\n---\n"
        (folder / f"{change}_{role}.md").write_text(text)
    log = folder / f"{change}_status_log.md"
    log.write_text("# t\n\n## Run 1 — d\n10:00:00 · round 1 · done — ok\n")


def _done(root: Path, change: str, head: str) -> None:
    folder = root / ".minions" / "build"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{change}.done").write_text(f"head: {head}\nsimplify: lean already\n")


def _by_rule(tree: Path, findings: Path, change: str) -> list[str] | None:
    """Return each merge's `replay` line when a catch-up selects merges that all replay.

    None when no catch-up applies, the selection holds another commit, or one exits 1.
    """
    review = findings / f"{change}_review.md"
    text = review.read_text() if review.is_file() else ""
    found = re.search(r"^head: (\S+)$", text, re.MULTILINE)
    head = _git(tree, "rev-parse", "HEAD")
    if not found or found[1] == head:
        return None
    span = f"{found[1]}..HEAD"
    selected = _git(tree, "rev-list", "--first-parent", span).split()
    merges = _git(tree, "rev-list", "--first-parent", "--merges", span).split()
    if not merges or selected != merges:
        return None
    script = Path(__file__).resolve().parent.parent / "skills" / "mf-integrate"
    lines = []
    for merge in merges:
        done = subprocess.run(
            [sys.executable, str(script / "scripts" / "integrate.py"), "replay", merge],
            cwd=tree,
            capture_output=True,
            text=True,
        )
        if done.returncode != 0:
            return None
        lines.append(f"- {merge}: {done.stdout.strip().removeprefix('replay: ')}")
    return lines


def _write_by_rule(findings: Path, change: str, head: str, lines: list[str]) -> None:
    """Write both findings files clean at `head` with `## By rule`; log the round."""
    for role in ("review", "security"):
        text = f"---\nverdict: clean\nhead: {head}\nround: 2\nworkers: 0\n---\n"
        text += "\n## By rule\n\n" + "\n".join(lines) + "\n"
        (findings / f"{change}_{role}.md").write_text(text)
    paths = "; ".join(line.split(" — ", 1)[1] for line in lines)
    (findings / f"{change}_status_log.md").write_text(
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


def _amended(tree: Path, change: str | None) -> bool:
    """Return whether a rescue's fix stands in the change's `tasks.md`."""
    tasks = tree / "openspec" / "changes" / str(change) / "tasks.md"
    return _AMENDED in tasks.read_text()


def _rescue(tree: Path, primary: Path, change: str, modes: set[str]) -> None:
    """Amend the plan, hollowly, outside it or by a rewrite; diagnose; or die."""
    tasks = f"openspec/changes/{change}/tasks.md"
    message = f"docs({change}): amend the change directory\n\nfix\n\nRescue: 1.1"
    text = (tree / tasks).read_text()
    if "dies-rescue" in modes:
        sys.exit(1)
    if "rescue-fix" in modes:
        _commit(tree, {tasks: text + _AMENDED}, message)
    elif "rescue-hollow" in modes:
        _commit(tree, {tasks: text + "Read again.\n"}, message)
    elif "rescue-wild" in modes:
        _commit(tree, {tasks: text + "Read again.\n", "src.py": "x = 1\n"}, message)
    elif "rescue-rewrite" in modes:
        _git(tree, "commit", "-q", "--amend", "-m", "rewritten")
    elif "rescue-diagnose" in modes:
        folder = primary / ".minions" / "rescue"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{change}.md").write_text("# diagnosis\n")


def _fake(prompt: str) -> None:
    """Do on disk what the station the prompt names would, as `FAKE_MODE` says."""
    modes = set(os.environ["FAKE_MODE"].split(","))
    here = Path.cwd()
    found = re.search(r"Run the mf-(\w+) skill(?: for change (\S+?)[ .])?", prompt)
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
    elif (
        station == "build" and f"halt-{change}" in modes and not _amended(here, change)
    ):
        folder = primary / ".minions" / "build"
        folder.mkdir(parents=True, exist_ok=True)
        head = _git(here, "rev-parse", "HEAD")
        (folder / f"{change}.halt").write_text(
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
            table = primary / ".minions" / "models" / f"{change}.toml"
            table.parent.mkdir(parents=True, exist_ok=True)
            table.write_text('[release]\nexecutor = "codex"\n')
        if "grant-halts" in modes:
            log = primary / ".minions" / "findings" / f"{change}_status_log.md"
            log.write_text(
                "# t\n\n## Run 2 — d\n10:00:00 · round 4 · halt — cap reached\n"
            )
            return
        findings = primary / ".minions" / "findings"
        if "by-rule" in modes and (lines := _by_rule(here, findings, str(change))):
            _write_by_rule(
                findings, str(change), _git(here, "rev-parse", "HEAD"), lines
            )
            return
        log = findings / f"{change}_status_log.md"
        held = log.read_text() if log.is_file() else ""
        _findings(primary, str(change), _git(here, "rev-parse", "HEAD"))
        if "amends" in modes:
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
