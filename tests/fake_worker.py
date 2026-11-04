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
    elif station == "build":
        tasks = here / "openspec" / "changes" / str(change) / "tasks.md"
        files = {str(tasks): tasks.read_text().replace("- [ ]", "- [x]")}
        if f"after-self-{change}" in modes:
            proposal = f"---\nbump: minor\nafter: [{change}]\n---\n"
            files[str(tasks.with_name("proposal.md"))] = proposal
        if "- [ ]" in tasks.read_text():
            _commit(here, files, "build")
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
        log = primary / ".minions" / "findings" / f"{change}_status_log.md"
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
