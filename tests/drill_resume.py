# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Kill a real worker and a real conductor in a scratch repo, then re-run to `done`.

    drill_resume.py

Works in `../mf_resume_probe/`, deleted when both drills pass; a failure keeps it to
read. No gate runs this: it spends Claude tokens on two short converges.
Prints one line per drill. Exit 0 both done · 1 a drill failed.
Why: 0051-reliability-paydown design D10.
"""

import argparse
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONDUCT = REPO / "skills" / "mf-ship" / "scripts" / "conduct.py"
PROBE = REPO.parent / "mf_resume_probe"
MARK = ".mf-resume-probe"
POLL_SECONDS = 5
FAN_OUT_SECONDS = 1800
RUN_SECONDS = 5400
SIGNAL_SECONDS = 120
FAN_OUT = re.compile(r"· round (\d+) · fan-out — ")
VERDICTS = re.compile(r"· round (\d+) · verdicts — ")


class FailedError(Exception):
    """A drill's check failed; the message says which."""


def _git(cwd: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    )
    return done.stdout.strip()


def _environ() -> dict[str, str]:
    """Return this environment, minus what would stop or replace a real worker."""
    drop = ("CLAUDECODE", "MF_SHIP_AGENT")
    return {key: value for key, value in os.environ.items() if key not in drop}


def _start(primary: Path) -> subprocess.Popen[str]:
    command = [sys.executable, str(CONDUCT), "run", "--executor", "claude"]
    return subprocess.Popen(
        command,
        cwd=primary,
        env=_environ(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        text=True,
    )


def _conduct(primary: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CONDUCT), *args],
        cwd=primary,
        env=_environ(),
        capture_output=True,
        text=True,
        timeout=RUN_SECONDS,
    )


def _repo() -> Path:
    """Return a new primary checkout on `main`, inside the probe."""
    if PROBE.exists():
        if not (PROBE / MARK).is_file():
            raise FailedError(f"{PROBE.name} exists and is no drill's")
        shutil.rmtree(PROBE)
    primary = PROBE / "main"
    primary.mkdir(parents=True)
    (PROBE / MARK).touch()
    _git(primary, "init", "-q", "-b", "main")
    _git(primary, "config", "user.name", "mf-drill")
    _git(primary, "config", "user.email", "mf-drill@example.invalid")
    _git(primary, "config", "commit.gpgsign", "false")
    files = {
        ".gitignore": ".minions/\n",
        "AGENTS.md": (
            "# Drill probe\n\nA scratch repo. The gate is `make gate`.\n\n"
            "- **Worktrees:** `../` — a version's worktree is `<this path>/<branch>`.\n"
        ),
        "CHANGELOG.md": "# Changelog\n\n## [Unreleased]\n",
        "Makefile": "gate:\n\ttest -f AGENTS.md\n",
        "openspec/specs/.gitkeep": "",
    }
    _write(primary, files)
    _git(primary, "add", ".")
    _git(primary, "commit", "-q", "-m", "chore: base")
    _git(primary, "tag", "-a", "-m", "v0.1.0", "v0.1.0")
    return primary


def _write(root: Path, files: dict[str, str]) -> None:
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text)


def _cut(primary: Path, change: str) -> None:
    """Cut `change` with its phase built, so a run starts it at `converge`."""
    tree = PROBE / change
    _git(primary, "worktree", "add", "-q", "-b", change, str(tree))
    folder = f"openspec/changes/{change}"
    note = f"notes/{change}.md"
    tasks = (
        "## Progress\n\n- [x] 1 — The note\n\n## 1 — The note\n\n"
        f"- [x] 1.1 Write `{note}`.\n  Verify: `test -f {note}` exits 0.\n"
    )
    changelog = (
        (tree / "CHANGELOG.md")
        .read_text()
        .replace(
            "## [Unreleased]\n", f"## [Unreleased]\n\n- A note (change `{change}`).\n"
        )
    )
    proposal = f"---\nbump: patch\n---\n\n# A note\n\nAdds `{note}`.\n"
    design = "# A note\n\n## Tests\n\nNone.\n\n## Dependencies\n\nNone.\n"
    _write(
        tree,
        {
            note: "A note for the drill.\n",
            "CHANGELOG.md": changelog,
            f"{folder}/.openspec.yaml": "schema: spec-driven\nskip_specs: true\n",
            f"{folder}/proposal.md": proposal,
            f"{folder}/design.md": design,
            f"{folder}/tasks.md": tasks,
            f"{folder}/specs/.gitkeep": "",
        },
    )
    _git(tree, "add", ".")
    _git(tree, "commit", "-q", "-m", f"feat: add a note\n\nChange: {change}")
    table = '[converge]\nmodel = "sonnet"\n[release]\nmodel = "sonnet"\n'
    _write(primary, {f".minions/models/{change}.toml": table})


def _status_log(primary: Path, change: str) -> Path:
    return primary / ".minions" / "findings" / f"{change}_status_log.md"


def _active(primary: Path) -> Path:
    return primary / ".minions" / "runs" / "active"


def _groups(primary: Path) -> list[int]:
    """Return the worker groups the claim names."""
    active = _active(primary)
    entries = active.iterdir() if active.is_dir() else ()
    return [int(entry.name) for entry in entries if entry.name.isdecimal()]


def _await_fan_out(
    primary: Path, change: str, conductor: subprocess.Popen[str]
) -> None:
    log = _status_log(primary, change)
    deadline = time.monotonic() + FAN_OUT_SECONDS
    while time.monotonic() < deadline:
        if conductor.poll() is not None:
            raise FailedError(f"the run ended, exit {conductor.returncode}, early")
        if log.is_file() and FAN_OUT.search(log.read_text()):
            return
        time.sleep(POLL_SECONDS)
    raise FailedError("no fan-out in time")


def _last_run_log(primary: Path) -> str:
    logs = sorted((primary / ".minions" / "runs").glob("*.md"), key=os.path.getmtime)
    return logs[-1].read_text() if logs else ""


def _finished(primary: Path, change: str) -> None:
    """Fail unless converge kept one run, repeated no round, and the change shipped."""
    text = _status_log(primary, change).read_text()
    if (runs := text.count("## Run")) != 1:
        raise FailedError(f"{runs} runs in the status log")
    judged: set[str] = set()
    for line in reversed(text.splitlines()):
        if (found := FAN_OUT.search(line)) and found[1] in judged:
            raise FailedError(f"round {found[1]} ran again after its verdicts")
        if found := VERDICTS.search(line):
            judged.add(found[1])
    top = next(line for line in text.splitlines() if " · round " in line)
    if " · done — " not in top:
        raise FailedError(f"the status log ends on: {top}")
    if " · run · done — released " not in _last_run_log(primary):
        raise FailedError("the run log has no release")
    checked = _conduct(primary, "check", "release", change)
    if checked.returncode != 0:
        raise FailedError(checked.stdout.strip())


def _worker_killed(primary: Path, change: str) -> None:
    """Kill the converge worker's group at its fan-out; a re-run finishes the change."""
    _cut(primary, change)
    conductor = _start(primary)
    try:
        _await_fan_out(primary, change, conductor)
        groups = _groups(primary)
        if not groups:
            raise FailedError("the claim names no worker")
        for group in groups:
            os.killpg(group, signal.SIGKILL)
        if (code := conductor.wait(timeout=SIGNAL_SECONDS)) != 1:
            raise FailedError(f"the killed run exited {code}, not 1")
    finally:
        _stop(primary, conductor)
    halted = f" · {change} · halt — converge worker exit -{signal.SIGKILL}"
    if halted not in _last_run_log(primary):
        raise FailedError("the run log names no killed worker")
    if (code := _conduct(primary, "run", "--executor", "claude").returncode) != 0:
        raise FailedError(f"the re-run exited {code}")
    _finished(primary, change)


def _conductor_killed(primary: Path, change: str) -> None:
    """Kill the conductor at a fan-out; a re-run kills the orphan and finishes."""
    _cut(primary, change)
    conductor = _start(primary)
    try:
        _await_fan_out(primary, change, conductor)
        orphans = _groups(primary)
        if not orphans:
            raise FailedError("the claim names no worker")
        conductor.kill()
        conductor.wait(timeout=SIGNAL_SECONDS)
        status = _conduct(primary, "status").stdout
        if not status.startswith("run · stale"):
            raise FailedError(f"status reads: {status.strip()}")
        if (code := _conduct(primary, "run", "--executor", "claude").returncode) != 0:
            raise FailedError(f"the re-run exited {code}")
        for group in orphans:
            try:
                os.killpg(group, 0)
            except ProcessLookupError:
                continue
            raise FailedError(f"worker group {group} outlived the re-run")
    finally:
        _stop(primary, conductor)
    _finished(primary, change)


def _stop(primary: Path, conductor: subprocess.Popen[str]) -> None:
    """Leave no conductor or worker of this drill running."""
    if conductor.poll() is None:
        conductor.kill()
        conductor.wait(timeout=SIGNAL_SECONDS)
    for group in _groups(primary):
        try:
            os.killpg(group, signal.SIGKILL)
        except ProcessLookupError:
            continue


def main() -> int:
    """Run both drills; return the exit code."""
    argparse.ArgumentParser(description=__doc__).parse_args()
    primary = _repo()
    drills = (
        ("worker killed", _worker_killed, "0001-worker"),
        ("conductor killed", _conductor_killed, "0002-conductor"),
    )
    for name, drill, change in drills:
        try:
            drill(primary, change)
        except (FailedError, subprocess.SubprocessError) as error:
            print(f"{name}: failed — {error}", flush=True)
            print(_last_run_log(primary), file=sys.stderr)
            return 1
        print(f"{name}: done", flush=True)
    shutil.rmtree(PROBE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
