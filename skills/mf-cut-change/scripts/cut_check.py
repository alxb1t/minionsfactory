# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Decide the self-check rows a script can, and list the rest for the cut to judge.

    cut_check.py <id> [--bump <bump>]
Exit 0 ready · 1 a row failed · 2 unrunnable. Why: 0106-cut-scripts design D6.
"""

import argparse
import re
import runpy
import subprocess
import sys
from pathlib import Path
from typing import Any, NamedTuple

TIMEOUT_SECONDS = 600
HERE = Path(__file__).resolve().parent
CUT_PRE = HERE / "cut_pre.py"
VERIFY_CHECK = HERE / "verify_check.py"
CONVERGE = HERE.parents[1] / "mf-converge" / "scripts"
GATE_CHECK = CONVERGE / "gate_check.py"
PLAN_CHECK = CONVERGE / "plan_check.py"
CHANGE_ID = re.compile(r"\d+-[a-z0-9]+(?:-[a-z0-9]+)*")
PROGRESS = re.compile(r"^- \[[ x]\] (\d+) — (.+)$")
PHASE = re.compile(r"(\d+) — ")
SUBTASK = re.compile(r"- \[[ x]\] (\d+\.\d+\b.*)$")
DEFINED = re.compile(r"^### ([A-Z]\d+)\b")
SKIP_SPECS = re.compile(r"^skip_specs:\s*true\s*$", re.MULTILINE)
SPAN = re.compile(r"(`+)(.+?)(?<!`)\1(?!`)")
LINK = re.compile(r"\[[^\]]*\]\([^)]*\)")
SENTENCE = re.compile(r"[.!?](?=\s+[A-Z`*\[(]|\s*$)")
COUNTED = re.compile(
    r"(?<![\w.])(?:\d+|(?i:two|three|four|five|six|seven|eight|nine|ten|eleven|twelve))"
    r"\s+(?:[a-z-]+\s+)?[a-z]+s\b"
)
RITUAL = re.compile(
    r"(?:\*\*[A-Z ]+\*\*\s*(?:`[^`]*`\s*)?)?(?:"
    r"run\s+`?(?:make\s+(?:gate|check)\b|mf-[a-z]+)"
    r"|(?:add|write|append)\b[^`.]{0,40}\bCHANGELOG\b"
    r"|(?:tick|commit|tag|archive|release)\b)",
    re.IGNORECASE,
)
PROPOSAL_HEADINGS = [
    "Why",
    "What Changes",
    "Capabilities",
    "Impact",
    "Not in this change",
]
DESIGN_HEADINGS = [
    "Context",
    "Goals / Non-Goals",
    "Decisions",
    "Tests",
    "Dependencies",
    "Risks / Trade-offs",
    "Verdict",
]
ROWS = [
    "I2",
    "I3",
    "I4",
    "I11",
    "I12",
    "I13",
    "I14",
    "I17",
    "I18",
    "I19",
    "A1",
    "A2",
    "P9",
    "P13",
    "corpus",
]
JUDGED = {
    "I5": "each `Verify:` runs on this machine, or is a fact on disk",
    "I6": "each task has one reading: files named, no `or`, things named not counted",
    "I7": "each existing file the change turns red is named in a task",
    "I8": "each phase ends on a green `make check`, the last on a green gate",
    "I9": "a delta for each behaviour change; each MODIFIED title is a requirement",
    "I10": "each file and symbol `design.md` names exists, or an `after:` adds it",
    "I15": "`**HALT CHECK**` on each sub-task whose failure means the plan is wrong",
    "I16": "each deleted or merged test is in `## Tests`, with the test that keeps it",
    "P12": "no counts in prose: read each candidate",
    "P13": "no paragraph past 3 sentences: read each candidate",
}


class Stop(Exception):
    """End the check with exit 2; the message says what could not run."""


class Failure(NamedTuple):
    """A failed row, why, and the output lines of the check that failed it."""

    row: str
    why: str
    detail: list[str]


class Change(NamedTuple):
    """The texts of a change directory, empty when a file is missing."""

    id: str
    folder: Path
    proposal: str
    design: str
    tasks: str


def _spawn(argv: list[str], name: str) -> tuple[int, list[str]]:
    """Return a program's exit code and its output lines; one that cannot run stops."""
    try:
        done = subprocess.run(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        gone = isinstance(error, FileNotFoundError)
        raise Stop(f"{name} is not on PATH" if gone else f"{name}: {error}") from None
    return done.returncode, done.stdout.splitlines()


def _script(path: Path, *args: str) -> tuple[int, list[str]]:
    """Run a sibling script under this interpreter; an exit above 1 stops."""
    code, lines = _spawn([sys.executable, str(path), *args], path.name)
    if code > 1:
        raise Stop(next((line for line in lines if line.strip()), path.name))
    return code, lines


def prose_lines(text: str) -> list[tuple[int, str]]:
    """Return each numbered line outside a code fence and a leading frontmatter."""
    kept: list[tuple[int, str]] = []
    fenced = False
    front = text.startswith("---\n")
    for number, line in enumerate(text.splitlines(), 1):
        if front:
            front = number == 1 or line.strip() != "---"
        elif line.lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced:
            kept.append((number, line))
    return kept


def headings(text: str) -> list[str]:
    """Return the title of each `## ` heading outside a fence."""
    return [line[3:].strip() for _, line in prose_lines(text) if line.startswith("## ")]


def section(text: str, title: str) -> list[str] | None:
    """Return the stripped, non-blank lines under `## <title>`, or None without it."""
    found: list[str] | None = None
    for _, line in prose_lines(text):
        if line.startswith("## "):
            if found is not None:
                break
            found = [] if line[3:].strip() == title else None
        elif found is not None and line.strip():
            found.append(line.strip())
    return found


def frontmatter(text: str) -> dict[str, str]:
    """Return the `key: value` pairs of a leading `---` block."""
    lines = text.splitlines()
    if lines[:1] != ["---"]:
        return {}
    pairs: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, colon, value = line.partition(":")
        if colon:
            pairs[key.strip()] = value.strip()
    return pairs


def masked(line: str) -> str:
    """Return a line with its code spans and links blanked."""
    return LINK.sub(" ", SPAN.sub(" ", line))


def blocks(tasks: str) -> list[tuple[str, list[str]]]:
    """Return each sub-task's name and its lines outside a fence, wrapped ones too."""
    found: list[tuple[str, list[str]]] = []
    wrapped = fenced = False
    for line in tasks.splitlines():
        if match := SUBTASK.match(line):
            found.append((match[1].split()[0], [line]))
            wrapped, fenced = True, False
        elif wrapped and line[:1] in (" ", "\t") and line.strip():
            if line.strip().startswith("```"):
                fenced = not fenced
            elif not fenced:
                found[-1][1].append(line)
        else:
            wrapped = False
    return found


def in_order(wanted: list[str], found: list[str]) -> str | None:
    """Return the first of `wanted` that `found` lacks in that order, or None."""
    at = 0
    for title in wanted:
        if title not in found[at:]:
            return title
        at = found.index(title, at) + 1
    return None


def row_i2(change: Change) -> str | None:
    """Return why the artifacts or the delta are not in place, or None."""
    for name in ("proposal.md", "design.md", "tasks.md"):
        if not (change.folder / name).is_file():
            return f"{name} is missing"
    specs = change.folder / "specs"
    delta = sorted(specs.glob("*/spec.md"))
    meta = change.folder / ".openspec.yaml"
    skip = meta.is_file() and SKIP_SPECS.search(meta.read_text())
    if not skip:
        return None if delta else "no specs/*/spec.md, and no `skip_specs: true`"
    if delta:
        return "`skip_specs: true` beside a spec file"
    return (
        None if (specs / ".gitkeep").is_file() else "no specs/.gitkeep for `skip_specs`"
    )


def row_i4(change: Change, plan: dict[str, Any]) -> str | None:
    """Return what is out of shape in `tasks.md`'s progress list and sub-tasks."""
    problems: list[str] = []
    lines = change.tasks.splitlines()
    first = next((n for n, line in enumerate(lines) if line.startswith("## ")), None)
    if not (
        first is not None
        and lines[0].startswith("# ")
        and lines[first].strip() == "## Progress"
        and any(line.strip() for line in lines[1:first])
    ):
        problems.append("`## Progress` does not follow the title and its line")
    sections = {
        int(m[1])
        for _, line in prose_lines(change.tasks)
        if line.startswith("## ") and (m := PHASE.match(line[3:]))
    }
    listed = section(change.tasks, "Progress") or []
    phases = [m for line in listed if (m := PROGRESS.match(line))]
    if not phases:
        problems.append("`## Progress` lists no phase")
    for phase in phases:
        suffixed = phase[2].endswith((" · moderate", " · hard"))
        if not suffixed and "**HUMAN" not in phase[2]:
            problems.append(f"phase {phase[1]} lacks ` · moderate` or ` · hard`")
        if int(phase[1]) not in sections:
            problems.append(f"phase {phase[1]} has no `## {phase[1]} — …` section")
    ids = [int(phase[1]) for phase in phases]
    problems.extend(
        f"section {number} is not listed in `## Progress`"
        for number in sorted(sections - set(ids))
    )
    problems.extend(
        f"phase {number} is listed twice in `## Progress`"
        for number in sorted({n for n in ids if ids.count(n) > 1})
    )
    for task in plan["subtasks"](change.tasks):
        if plan["verify_of"](task.text) is None:
            problems.append(f"{task.name} has no Verify:")
    return " · ".join(problems) or None


def row_i11(change: Change) -> str | None:
    """Return why `## Dependencies` is neither `None.` nor the package table."""
    lines = section(change.design, "Dependencies")
    if lines is None:
        return "design.md has no `## Dependencies`"
    header = [cell.strip().lower() for cell in "".join(lines[:1]).strip("|").split("|")]
    if lines == ["None."] or (header == ["package", "constraint", "why"] and lines[2:]):
        return None
    return "`## Dependencies` is not `None.` or a table of package, constraint, why"


def row_i12(change: Change, plan: dict[str, Any]) -> str | None:
    """Return the sub-tasks that open with another station's step, a person's apart."""
    human = plan["phases"](change.tasks)[1]
    found = [
        task.name
        for task in plan["subtasks"](change.tasks)
        if int(task.name.split(".")[0]) not in human
        and RITUAL.match(task.text[len(task.name) :].strip())
    ]
    return (
        f"{', '.join(found)} open with a step another station owns" if found else None
    )


def row_i13(change: Change, bump: str | None) -> str | None:
    """Return why the proposal's `bump:` is not `minor` or `patch`, or not the given."""
    found = frontmatter(change.proposal).get("bump")
    if found not in ("minor", "patch"):
        return "proposal.md opens no frontmatter with `bump: minor` or `bump: patch`"
    if bump not in (None, found):
        return f"`bump: {found}` is not the bump given, {bump}"
    return None


def row_i14(change: Change, plan: dict[str, Any]) -> str | None:
    """Return each phase a person does that holds no sub-task with a `Verify:`."""
    human = plan["phases"](change.tasks)[1]
    checked = {
        int(task.name.split(".")[0])
        for task in plan["subtasks"](change.tasks)
        if plan["verify_of"](task.text) is not None
    }
    bare = ", ".join(str(phase) for phase in sorted(human - checked))
    return f"phase {bare} holds no sub-task with Verify:" if bare else None


def row_i17(change: Change, pre: dict[str, Any]) -> str | None:
    """Return why an `after:` id is not an open version of a lower number, or None."""
    value = frontmatter(change.proposal).get("after", "")
    ids = [named.strip() for named in value.strip("[]").split(",") if named.strip()]
    if not ids:
        return None
    return pre["after_problem"](change.id, ids, pre["default_branch"]())


def row_a1(change: Change) -> str | None:
    """Return the headings each file lacks, in the order `A1` gives."""
    named = headings(change.tasks)
    lacking = [
        f"{file} lacks `## {title}` in order"
        for file, wanted, found in (
            ("proposal.md", PROPOSAL_HEADINGS, headings(change.proposal)),
            ("design.md", DESIGN_HEADINGS, headings(change.design)),
        )
        if (title := in_order(wanted, found))
    ]
    if named[:1] != ["Progress"] or not all(PHASE.match(h) for h in named[1:]):
        lacking.append("tasks.md headings are not `## Progress`, then `## N — Title`")
    return " · ".join(lacking) or None


def row_a2(change: Change) -> str | None:
    """Return why the proposal does not end with `## Not in this change`."""
    if headings(change.proposal)[-1:] == ["Not in this change"]:
        return None
    return "proposal.md does not end with `## Not in this change`"


def row_p9(change: Change) -> str | None:
    """Return each id of the design cited outside a link in the tasks or proposal."""
    defined = {
        m[1] for _, line in prose_lines(change.design) if (m := DEFINED.match(line))
    }
    found = [
        f"{name}:{number} cites {cited}"
        for name, text in (("tasks.md", change.tasks), ("proposal.md", change.proposal))
        for number, line in prose_lines(text)
        for cited in re.findall(r"\b[A-Z]\d+\b", masked(line))
        if cited in defined
    ]
    return " · ".join(found) + " outside a link" if found else None


def row_p13(change: Change) -> str | None:
    """Return each sub-task of more than 3 lines, wrapped ones counted."""
    long = [
        f"{name} ({len(lines)} lines)"
        for name, lines in blocks(change.tasks)
        if len(lines) > 3
    ]
    return f"{', '.join(long)} hold more than 3 lines" if long else None


def counted_lines(change: Change) -> list[str]:
    """Return each line naming a number before a plural noun, as `path:line: text`."""
    texts = (
        ("proposal.md", change.proposal),
        ("design.md", change.design),
        ("tasks.md", change.tasks),
    )
    return [
        f"{name}:{number}: {line.strip()}"
        for name, text in texts
        for number, line in prose_lines(text)
        if COUNTED.search(masked(line))
    ]


def long_paragraphs(change: Change) -> list[str]:
    """Return each paragraph past 3 sentences, as `path:line: its first words`."""
    found: list[str] = []
    for name, text in (("proposal.md", change.proposal), ("design.md", change.design)):
        start, words = 0, []
        for number, line in [*prose_lines(text), (0, "")]:
            if line.strip() and line[:1] not in " \t#|-*>" and not line[:1].isdigit():
                start = start or number
                words.append(line.strip())
                continue
            if len(SENTENCE.findall(masked(" ".join(words)))) > 3:
                found.append(f"{name}:{start}: {words[0][:60]}")
            start, words = 0, []
    return found


def folded(change: Change) -> tuple[list[Failure], list[str]]:
    """Run `openspec validate`, the gate-edit check and the search script.

    A failure keeps the output lines under its row; each match of the search script is
    returned as a line of its own.
    """
    tasks = str(change.folder / "tasks.md")
    failures: list[Failure] = []
    code, lines = _spawn(["openspec", "validate", change.id, "--strict"], "openspec")
    if code:
        why = f"`openspec validate {change.id} --strict` failed"
        failures.append(Failure("I3", why, lines))
    if not (change.folder / "tasks.md").is_file():
        return failures, []
    code, lines = _script(GATE_CHECK, "--tasks", tasks)
    if code:
        failures.append(Failure("I18", lines[0], lines[1:]))
    code, lines = _script(VERIFY_CHECK, tasks)
    summary = [line for line in lines if line.startswith("verify:")]
    detail = [line for line in lines if "I19 —" in line]
    matches = [line for line in lines if line not in summary + detail]
    if code:
        failures.append(Failure("I19", summary[0], detail))
    return failures, matches


def check(
    identifier: str, bump: str | None
) -> tuple[list[Failure], list[str], list[str]]:
    """Return the failed rows, the search matches and the judgment lines of a change."""
    folder = Path("openspec/changes") / identifier
    if not folder.is_dir():
        raise Stop(f"no {folder}/")
    proposal, design, tasks = (
        path.read_text(errors="replace") if path.is_file() else ""
        for path in (folder / name for name in ("proposal.md", "design.md", "tasks.md"))
    )
    change = Change(identifier, folder, proposal, design, tasks)
    pre = runpy.run_path(str(CUT_PRE))
    plan = runpy.run_path(str(PLAN_CHECK))
    failures, matches = folded(change)
    try:
        corpus = plan["check_corpus"](plan["subtasks"](tasks), Path.cwd())
        rows = [
            ("I2", row_i2(change)),
            ("I4", row_i4(change, plan)),
            ("I11", row_i11(change)),
            ("I12", row_i12(change, plan)),
            ("I13", row_i13(change, bump)),
            ("I14", row_i14(change, plan)),
            ("I17", row_i17(change, pre)),
            ("A1", row_a1(change)),
            ("A2", row_a2(change)),
            ("P9", row_p9(change)),
            ("P13", row_p13(change)),
            *[("corpus", line.removeprefix("plan: ")) for line in corpus],
        ]
    except (pre["Stop"], plan["Stop"]) as error:
        raise Stop(str(error)) from None
    failures += [Failure(row, why, []) for row, why in rows if why]
    judge = [f"{row} — {what}" for row, what in JUDGED.items()]
    judge += [f"P12 — {line}" for line in counted_lines(change)]
    judge += [f"P13 — {line}" for line in long_paragraphs(change)]
    failures.sort(key=lambda failure: ROWS.index(failure.row))
    return failures, matches, judge


def main(argv: list[str] | None = None) -> int:
    """Check a change from the repository root; print its rows, return the exit code."""
    parser = argparse.ArgumentParser(
        description="Check a cut change's mechanical rows."
    )
    parser.add_argument("change", help="the change id, <digits>-<slug>")
    parser.add_argument("--bump", help="the bump the cut was given")
    args = parser.parse_args(argv)
    try:
        if not CHANGE_ID.fullmatch(args.change):
            raise Stop(f"`{args.change}` is not <digits>-<slug>")
        failures, matches, judge = check(args.change, args.bump)
    except Stop as stop:
        print(f"cut_check: cannot check — {stop}")
        return 2
    out: list[str] = []
    for failure in failures:
        out.append(f"cut_check: halt — {failure.row} — {failure.why}")
        out += [f"  {line.strip()}" for line in failure.detail]
    out += [f"cut_check: match — {line}" for line in matches]
    out += [f"cut_check: judge — {line}" for line in judge]
    failed = {failure.row for failure in failures}
    if failed:
        out.append(f"cut_check: halt — {len(failed)} rows failed")
    else:
        out.append(f"cut_check: ready — {len(ROWS)} rows met, {len(JUDGED)} to judge")
    print("\n".join(out))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
