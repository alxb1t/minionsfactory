# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Place the brief's facts, and find the readers of a name, for the cut.

    facts.py place <brief> [--at <rev>] [--notes <f>] | readers <name>... [--notes <f>]
Exit 0 none unplaced · 1 one is · 2 unreadable. Why: 0106-cut-scripts design D4.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

# The runner is a constant so a test swaps it for the interpreter.
RUNNER = ("uv", "run", "--script")
BRIEF_CHECK = (
    Path(__file__).resolve().parents[2] / "mf-plan" / "scripts" / "brief_check.py"
)
TIMEOUT_SECONDS = 60
SHA = re.compile(r"[0-9a-f]{7,40}")
HUNK = re.compile(r"@@ -(\d+)(?:,(\d+))? \+\d+(?:,(\d+))? @@")
HIT = re.compile(r"^HEAD:(.+?):(\d+):(.*)$", re.MULTILINE)


class Stop(Exception):
    """End the run with `code`; the message is what it prints."""

    def __init__(self, code: int, message: str) -> None:
        """Keep the exit code beside the message."""
        super().__init__(message)
        self.code = code


class Cite(NamedTuple):
    """The lines `start` to `end` of `path`."""

    path: str
    start: int
    end: int


class Fact(NamedTuple):
    """A brief's fact: its text, the cites it rests on, and the sha it was read at."""

    text: str
    cites: list[Cite]
    sha: str


class Placed(NamedTuple):
    """A fact's state at HEAD, and its cites there; unplaced keeps the cited ones."""

    fact: Fact
    state: str
    cites: list[Cite]


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    """Return a finished git command, run here; exit 1 is its answer, any other stops.

    A missing program or a timeout stops with exit 2, as `_run` does.
    """
    done = _run(["git", *args], "git")
    if done.returncode > 1:
        first = done.stderr.strip().partition("\n")[0]
        raise Stop(2, f"facts: cannot place — git {args[0]} failed: {first}")
    return done


def _run(argv: list[str], what: str) -> subprocess.CompletedProcess[str]:
    """Return a finished process; a missing program or a timeout stops with exit 2."""
    try:
        return subprocess.run(
            argv,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise Stop(2, f"facts: cannot place — {what}: {error}") from None


def brief_facts(brief: Path) -> list[Fact]:
    """Return the facts of a brief, read by `brief_check.py --facts`.

    A brief it halts on or cannot read stops with exit 2, naming its first line.
    """
    done = _run([*RUNNER, str(BRIEF_CHECK), "--facts", str(brief)], "brief_check.py")
    if done.returncode:
        first = (done.stdout or done.stderr).strip().partition("\n")[0]
        raise Stop(2, f"facts: cannot place — {first}")
    try:
        found = json.loads(done.stdout)
    except ValueError:
        raise Stop(2, "facts: cannot place — brief_check.py printed no JSON") from None
    return [
        Fact(item["fact"], [Cite(**cite) for cite in item["cites"]], item["sha"])
        for item in found
    ]


def shift(line: int, hunks: list[tuple[int, int, int]]) -> int:
    """Return where an old line is after the hunks, none of which holds it.

    A hunk is its old start, old count and new count; an old count of 0 inserts after
    the old start. e.g. 5, [(1, 0, 2)] → 7
    """
    offset = 0
    for start, old, new in hunks:
        last = start + old - 1 if old else start
        if last < line:
            offset += new - old
    return line + offset


def moved(cite: Cite, sha: str, at: str = "HEAD") -> Cite | None:
    """Return a cite of a touched path where it stands at `at`, or None when unplaced.

    A hunk over a cited line, or a changed length, is unplaced. Why: design D4.
    """
    diff = _git("diff", "-U0", "--no-renames", f"{sha}..{at}", "--", cite.path).stdout
    hunks = [
        (int(hunk[1]), int(hunk[2] or 1), int(hunk[3] or 1))
        for line in diff.splitlines()
        if (hunk := HUNK.match(line))
    ]
    if any(
        old and first <= cite.end and cite.start < first + old
        for first, old, _ in hunks
    ):
        return None
    start, end = shift(cite.start, hunks), shift(cite.end, hunks)
    if end - start != cite.end - cite.start:
        return None
    return Cite(cite.path, start, end)


def resolve(rev: str) -> str:
    """Return the commit `rev` names, as a full sha; a rev that names none stops."""
    done = (
        None
        if rev.startswith("-")
        else _git("rev-parse", "-q", "--verify", f"{rev}^{{commit}}")
    )
    if done is None or done.returncode:
        raise Stop(2, f"facts: cannot place — --at {rev} names no commit")
    return done.stdout.strip()


def place(fact: Fact, at: str = "HEAD") -> Placed:
    """Return a fact's state at `at`, by its own sha.

    A sha that is not 7 to 40 hex or names no commit is unplaced: no git command takes
    it. A cite on a path the diff leaves alone stands. Why: 0106-cut-scripts design D4.
    """
    unplaced = Placed(fact, "unplaced", fact.cites)
    if not SHA.fullmatch(fact.sha):
        return unplaced
    if _git("rev-parse", "-q", "--verify", f"{fact.sha}^{{commit}}").returncode:
        return unplaced
    names = _git("diff", "--name-only", "-z", "--no-renames", f"{fact.sha}..{at}")
    touched = set(names.stdout.split("\0"))
    found = [moved(c, fact.sha, at) if c.path in touched else c for c in fact.cites]
    placed = [cite for cite in found if cite is not None]
    if len(placed) < len(found):
        return unplaced
    return Placed(fact, "stands" if placed == fact.cites else "moved", placed)


def place_all(facts: list[Fact], at: str = "HEAD") -> list[Placed]:
    """Return each fact placed at `at`, in order."""
    return [place(fact, at) for fact in facts]


def where(cite: Cite) -> str:
    """Return a cite as `<path>:<line>` or `<path>:<first>-<last>`."""
    last = f"-{cite.end}" if cite.end != cite.start else ""
    return f"{cite.path}:{cite.start}{last}"


def reader_lines(name: str) -> list[str]:
    """Return one line per hit of `name` at HEAD, or one saying there is none.

    e.g. "old" → ["readers of old — x = old() · src/a.py:3"]
    """
    done = _git("grep", "-nwI", "-e", name, "HEAD", "--")
    lines = [
        f"readers of {name} — {text.strip()} · {path}:{number}"
        for path, number, text in HIT.findall(done.stdout)
    ]
    return lines or [f"readers of {name} — none · HEAD"]


def write_notes(notes: Path, lines: list[str], fresh: bool) -> None:
    """Write the notes' `- ` lines: afresh under the title, or appended to the file.

    The title is `# <id> — cut notes`, `<id>` the file's folder name.
    """
    body = "".join(f"- {line}\n" for line in lines)
    title = f"# {notes.resolve().parent.name} — cut notes\n\n"
    try:
        if fresh:
            notes.write_text(title + body)
        else:
            with notes.open("a") as handle:
                handle.write(body)
    except OSError as error:
        raise Stop(2, f"facts: cannot place — {notes}: {error.strerror}") from None


def run_readers(names: list[str], notes: Path | None) -> int:
    """Print the readers of each name, append them to `notes`, and return 0."""
    lines = [line for name in names for line in reader_lines(name)]
    print("\n".join(lines))
    if notes:
        write_notes(notes, lines, fresh=False)
    return 0


def run_place(brief: Path, notes: Path | None, at: str | None = None) -> int:
    """Print each fact placed at `at` (HEAD), write `notes` afresh; return the code."""
    placed = place_all(brief_facts(brief), resolve(at) if at else "HEAD")
    lines = [
        f"{one.fact.text} — {one.state} · {', '.join(map(where, one.cites))}"
        for one in placed
    ]
    for one in placed:
        print(f"{one.state} · {one.fact.text} · {', '.join(map(where, one.cites))}")
    if notes:
        write_notes(notes, lines, fresh=True)
    return 1 if any(one.state == "unplaced" for one in placed) else 0


def main(argv: list[str] | None = None) -> int:
    """Run `place` or `readers` from the repository root; return the exit code."""
    parser = argparse.ArgumentParser(
        description="Place a brief's facts at HEAD, or find the readers of a name."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    placing = commands.add_parser("place", help="place each fact of a brief")
    placing.add_argument("brief", type=Path, help="the brief")
    placing.add_argument("--at", help="the revision to place at, HEAD by default")
    finding = commands.add_parser("readers", help="find the hits of each name")
    finding.add_argument("names", nargs="+", help="a deleted or renamed name")
    for sub in (placing, finding):
        sub.add_argument("--notes", type=Path, help="the cut's notes file")
    args = parser.parse_args(argv)
    try:
        if args.command == "readers":
            return run_readers(args.names, args.notes)
        return run_place(args.brief, args.notes, args.at)
    except Stop as stop:
        print(stop)
        return stop.code


if __name__ == "__main__":
    sys.exit(main())
