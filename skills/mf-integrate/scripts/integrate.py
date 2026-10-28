# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Merge the default branch into the next version by fixed rules.

    integrate.py next
    integrate.py changelog <worktree>
    integrate.py decisions <worktree>
    integrate.py delta <worktree>

Exit 0 done · 1 halt: not ready, or a conflict the rules do not cover · 2 cannot run.
`changelog` and `decisions` resolve an open merge and stage what they wrote.
Why: 0037-serial-integration design D2.
"""

import argparse
import difflib
import re
import subprocess
import sys
from pathlib import Path

TIMEOUT_SECONDS = 60
CHANGE_ID = re.compile(r"(\d+)-([a-z0-9-]+)")
PROGRESS = re.compile(r"^- \[([ x])\] (\d+) — ", re.MULTILINE)
UNRELEASED = re.compile(r"^## \[Unreleased\]\n", re.MULTILINE)
RELEASED = re.compile(r"^## \[", re.MULTILINE)
DECISIONS = "docs/decisions.md"
DECISION = re.compile(r"^### D(\d+) ", re.MULTILINE)
# A citation is `D45` in text or `#d45--` in a link's anchor.
CITATION = re.compile(r"(\bD|#d)(\d+)\b")
TOKEN = re.compile(r"\w+|\s+|[^\w\s]")
# An edit replaces `base[start:end]` with its lines.
type Edit = tuple[int, int, list[str]]


class Stop(Exception):
    """End the command with `code`; the message is what it prints."""

    def __init__(self, code: int, message: str) -> None:
        """Keep the exit code beside the message."""
        super().__init__(message)
        self.code = code


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Return a finished git command run in `cwd`; a missing git stops with exit 2."""
    try:
        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIMEOUT_SECONDS,
        )
    except FileNotFoundError:
        raise Stop(2, "integrate: cannot run — git is missing") from None
    except subprocess.TimeoutExpired:
        raise Stop(2, f"integrate: cannot run — git {args[0]} timed out") from None


def _git(cwd: Path, *args: str) -> str:
    """Return a git command's stdout; a failure stops with exit 2."""
    done = _run(cwd, *args)
    if done.returncode != 0:
        lines = [line for line in done.stderr.splitlines() if line.strip()]
        first = lines[0] if lines else f"exit {done.returncode}"
        raise Stop(2, f"integrate: cannot run — git {args[0]} failed: {first}")
    return done.stdout


def _maybe(cwd: Path, *args: str) -> str | None:
    """Return a git command's stdout, or None when it exits non-zero."""
    done = _run(cwd, *args)
    return done.stdout if done.returncode == 0 else None


def _show(cwd: Path, rev: str, path: str) -> str | None:
    """Return the file at `path` in `rev`, or None when `rev` has none."""
    return _maybe(cwd, "show", f"{rev}:{path}")


def default_branch(cwd: Path) -> str:
    """Return the branch `origin/HEAD` names, or `main`."""
    ref = _maybe(cwd, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    return ref.strip().removeprefix("origin/") if ref else "main"


def _frontmatter(text: str, key: str) -> str | None:
    """Return a key's value in the text's leading `---` block.

    e.g. a proposal opening `version: v0.33` in its block, "version" → "v0.33"
    """
    if not text.startswith("---\n"):
        return None
    block = text[4:].split("\n---", 1)[0]
    found = re.search(rf"^{key}:\s*(\S+)", block, re.MULTILINE)
    return found[1] if found else None


def change_of(cwd: Path, branch: str) -> str:
    """Return the change on `branch` whose version and slug name the branch.

    e.g. "v0.33_serial_integration" → "0037-serial-integration"
    """
    listing = _git(cwd, "ls-tree", "--name-only", f"{branch}:openspec/changes")
    for name in listing.split():
        if not (match := CHANGE_ID.fullmatch(name)):
            continue
        proposal = _show(cwd, branch, f"openspec/changes/{name}/proposal.md") or ""
        version = _frontmatter(proposal, "version")
        if f"{version}_{match[2].replace('-', '_')}" == branch:
            return name
    raise Stop(2, f"integrate: cannot run — {branch} holds no change that names it")


def _worktrees(cwd: Path) -> dict[str, Path]:
    """Map each checked-out branch to its worktree."""
    found: dict[str, Path] = {}
    path = None
    for line in _git(cwd, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            path = Path(line.removeprefix("worktree "))
        elif line.startswith("branch refs/heads/") and path:
            found[line.removeprefix("branch refs/heads/")] = path
    return found


def _run_dir(cwd: Path) -> Path:
    """Return `.minions/` beside the primary checkout, from any worktree."""
    common = _git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(common.strip()).parent / ".minions"


def unready(cwd: Path, branch: str, change: str, tree: Path | None) -> str | None:
    """Return why the version is not ready, or None when it is.

    Ready is every `## Progress` box ticked, and both findings files clean or
    converge skipped: no findings file and no diff patch.
    """
    if tree is None:
        return "no worktree"
    tasks = _show(cwd, branch, f"openspec/changes/{change}/tasks.md") or ""
    boxes = PROGRESS.findall(tasks)
    if not boxes:
        return "tasks.md has no ## Progress list"
    unticked = [number for mark, number in boxes if mark != "x"]
    if unticked:
        return f"phase {unticked[0]} unticked"
    findings = _run_dir(cwd) / "findings"
    files = [findings / f"{change}_{role}.md" for role in ("review", "security")]
    patch = findings / f"{change}_diff.patch"
    present = [file for file in files if file.is_file()]
    if not present and not patch.is_file():
        return None
    if len(present) != len(files):
        return "converge ran, and a findings file is missing"
    for file in files:
        if _frontmatter(file.read_text(), "verdict") != "clean":
            return f"{file.name} is not clean"
    return None


def next_version(cwd: Path) -> str:
    """Return the lowest-id unmerged version, its worktree and readiness."""
    default = default_branch(cwd)
    listing = _git(
        cwd, "branch", "--no-merged", default, "--list", "v*", "--format=%(refname)"
    )
    branches = [ref.removeprefix("refs/heads/") for ref in listing.split()]
    if not branches:
        raise Stop(1, "next: none — no open version")
    queue = sorted((int(change_of(cwd, b).split("-")[0]), b) for b in branches)
    branch = queue[0][1]
    change = change_of(cwd, branch)
    tree = _worktrees(cwd).get(branch)
    line = f"next: {branch} · {change} · {tree or 'no worktree'}"
    if why := unready(cwd, branch, change, tree):
        raise Stop(1, f"{line} · not ready — {why}")
    return f"{line} · ready"


def _tree(path: str) -> Path:
    """Return the worktree root given; anything else stops with exit 2."""
    tree = Path(path).resolve()
    top = _maybe(tree, "rev-parse", "--show-toplevel") if tree.is_dir() else None
    if top is None or Path(top.strip()).resolve() != tree:
        raise Stop(2, f"integrate: cannot run — {path} is not a worktree root")
    return tree


def _merge_base(tree: Path) -> str:
    """Return the base of the merge open in `tree`; no open merge stops with exit 2."""
    if _maybe(tree, "rev-parse", "-q", "--verify", "MERGE_HEAD") is None:
        raise Stop(2, f"integrate: cannot run — no merge in progress in {tree}")
    return _git(tree, "merge-base", "HEAD", "MERGE_HEAD").strip()


def _unmerged(tree: Path) -> set[str]:
    """Return the paths git still holds in conflict."""
    return set(_git(tree, "diff", "--name-only", "--diff-filter=U").splitlines())


def _write(tree: Path, path: str, text: str) -> None:
    """Write a resolved file and stage it, unless git still holds it in conflict."""
    (tree / path).write_text(text)
    if path not in _unmerged(tree) or "<<<<<<<" not in text:
        _git(tree, "add", "--", path)


def _split_changelog(text: str) -> tuple[str, str, str]:
    """Return the head through `## [Unreleased]`, its entries, and the released rest."""
    if not (heading := UNRELEASED.search(text)):
        raise Stop(1, "changelog: halt — a side has no ## [Unreleased] heading")
    rest = RELEASED.search(text, heading.end())
    cut = rest.start() if rest else len(text)
    return text[: heading.end()], text[heading.end() : cut], text[cut:]


def changelog(tree: Path) -> str:
    """Keep the branch's `[Unreleased]` entries above the default branch's releases."""
    base = _merge_base(tree)
    sides = [_show(tree, rev, "CHANGELOG.md") for rev in (base, "HEAD", "MERGE_HEAD")]
    if None in sides:
        raise Stop(2, "integrate: cannot run — a side has no CHANGELOG.md")
    base_head, _, base_rest = _split_changelog(sides[0] or "")
    our_head, entries, our_rest = _split_changelog(sides[1] or "")
    their_head, their_entries, their_rest = _split_changelog(sides[2] or "")
    if (our_head, our_rest) != (base_head, base_rest):
        raise Stop(1, "changelog: halt — the branch changed text outside [Unreleased]")
    if their_entries.strip():
        raise Stop(1, "changelog: halt — the default branch holds [Unreleased] entries")
    kept = entries.strip("\n")
    body = f"\n{kept}\n" if kept else ""
    _write(
        tree, "CHANGELOG.md", f"{their_head}{body}\n{their_rest}".rstrip("\n") + "\n"
    )
    return "changelog: the branch's [Unreleased] entries kept above the releases"


def _renumber(text: str, ids: dict[int, int]) -> str:
    """Return `text` with each cited decision id in `ids` replaced.

    e.g. "per [D45](decisions.md#d45--x)", {45: 46} → "per [D46](decisions.md#d46--x)"
    """

    def swap(match: re.Match[str]) -> str:
        new = ids.get(int(match[2]))
        return match[0] if new is None else f"{match[1]}{new}"

    return CITATION.sub(swap, text)


def _changes(base: list[str], side: list[str]) -> list[Edit]:
    """Return a side's edits as `(start, end, lines)` replacing `base[start:end]`."""
    matcher = difflib.SequenceMatcher(None, base, side, autojunk=False)
    return [
        (i1, i2, side[j1:j2])
        for tag, i1, i2, j1, j2 in matcher.get_opcodes()
        if tag != "equal"
    ]


def _merge_line(base: str, ours: str, theirs: str) -> str | None:
    """Return a line both sides only inserted into, theirs first; else None.

    e.g. "D44", "D44, D46", "D44, D45" → "D44, D45, D46"
    """
    tokens = TOKEN.findall(base)
    inserts: dict[int, list[str]] = {}
    for side in (theirs, ours):
        for start, end, added in _changes(tokens, TOKEN.findall(side)):
            if start != end:
                return None
            inserts.setdefault(start, []).extend(added)
    return "".join(
        "".join(inserts.get(i, [])) + (tokens[i] if i < len(tokens) else "")
        for i in range(len(tokens) + 1)
    )


def _apply(base: list[str], start: int, end: int, edits: list[Edit]) -> list[str]:
    """Return `base[start:end]` with one side's edits inside it applied."""
    out: list[str] = []
    pos = start
    for edit_start, edit_end, lines in edits:
        out += base[pos:edit_start] + lines
        pos = edit_end
    return out + base[pos:end]


def _resolve(base: list[str], ours: list[str], theirs: list[str]) -> list[str]:
    """Return one region both sides edited, by the rules; else stop with exit 1.

    Both inserted at one point → theirs, then ours. The same lines edited →
    each line merged by insertions. Anything else is not a mechanical conflict.
    """
    if ours == theirs:
        return ours
    if not base:
        return theirs + ours
    if len(base) == len(ours) == len(theirs):
        lines = [_merge_line(*trio) for trio in zip(base, ours, theirs, strict=True)]
        if None not in lines:
            return [line for line in lines if line is not None]
    where = base[0].strip() or "a blank line"
    raise Stop(1, f"decisions: halt — both sides changed the text at: {where}")


def merge3(base: str, ours: str, theirs: str) -> str:
    """Return the three-way merge of the sides, by the rules in `_resolve`."""
    lines = base.splitlines(keepends=True)
    sides = {"ours": ours.splitlines(keepends=True)}
    sides["theirs"] = theirs.splitlines(keepends=True)
    edits = sorted(
        (start, end, side, added)
        for side, text in sides.items()
        for start, end, added in _changes(lines, text)
    )
    out: list[str] = []
    pos = group_end = 0
    group: list[tuple[int, int, str, list[str]]] = []
    for edit in [*edits, None]:
        if edit and group and (edit[0] < group_end or edit[0] == group[0][0]):
            group.append(edit)
            group_end = max(group_end, edit[1])
            continue
        if group:
            start = group[0][0]
            mine = [(s, e, a) for s, e, side, a in group if side == "ours"]
            yours = [(s, e, a) for s, e, side, a in group if side == "theirs"]
            out += lines[pos:start]
            regions = [_apply(lines, start, group_end, x) for x in (mine, yours)]
            if mine and yours:
                out += _resolve(lines[start:group_end], *regions)
            else:
                out += regions[0] if mine else regions[1]
            pos = group_end
        if edit:
            group, group_end = [edit], edit[1]
    return "".join(out + lines[pos:])


def _added(base: str, side: str) -> set[str]:
    """Return the lines `side` added or rewrote against `base`."""
    edits = _changes(base.splitlines(), side.splitlines())
    return {line for _, _, added in edits for line in added}


def _recite(tree: Path, path: str, base: str, ids: dict[int, int]) -> bool:
    """Renumber citations on the lines the branch wrote in `path`; return if any."""
    file = tree / path
    try:
        text = file.read_text()
    except (OSError, UnicodeDecodeError):
        return False
    ours = _added(_show(tree, base, path) or "", _show(tree, "HEAD", path) or "")
    ours -= set((_show(tree, "MERGE_HEAD", path) or "").splitlines())
    lines = text.splitlines(keepends=True)
    out = [_renumber(x, ids) if x.rstrip("\n") in ours else x for x in lines]
    if out == lines:
        return False
    _write(tree, path, "".join(out))
    return True


def decisions(tree: Path) -> str:
    """Renumber the branch's new decisions past the default branch's, and merge."""
    base = _merge_base(tree)
    sides = [_show(tree, rev, DECISIONS) for rev in (base, "HEAD", "MERGE_HEAD")]
    if sides == [None, None, None]:
        return f"decisions: none — no {DECISIONS}"
    base_text, ours, theirs = (side or "" for side in sides)

    def numbers(text: str) -> set[int]:
        return {int(n) for n in DECISION.findall(text)}

    taken = numbers(theirs)
    new = sorted(numbers(ours) - numbers(base_text))
    ids: dict[int, int] = {}
    if new and taken and new[0] <= max(taken):
        ids = {old: max(taken) + i for i, old in enumerate(new, 1)}
    _write(tree, DECISIONS, merge3(base_text, _renumber(ours, ids), theirs))
    if not ids:
        return "decisions: no id collides"
    changed = _git(tree, "diff", "--name-only", base, "HEAD").splitlines()
    for path in changed:
        if path != DECISIONS:
            _recite(tree, path, base, ids)
    moves = ", ".join(f"D{old} → D{new}" for old, new in ids.items())
    return f"decisions: renumbered {moves}, citations with them"


def _requirements(spec: str, sections: tuple[str, ...]) -> list[str]:
    """Return the requirement titles under the named `## ` sections."""
    titles, inside = [], False
    for line in spec.splitlines():
        if line.startswith("## "):
            inside = line.strip() in sections
        elif inside and line.startswith("### Requirement: "):
            titles.append(line.removeprefix("### Requirement: ").strip())
    return titles


def _requirement(spec: str | None, title: str) -> str | None:
    """Return a requirement's block by title, or None when the spec lacks it."""
    block: list[str] | None = None
    for line in (spec or "").splitlines():
        if line.strip() == f"### Requirement: {title}":
            block = [line]
        elif block is not None:
            if line.startswith(("# ", "## ", "### Requirement: ")):
                break
            block.append(line)
    return "\n".join(block).strip() if block is not None else None


def delta(tree: Path) -> str:
    """Return the check that the default branch changed no requirement the delta edits.

    Stops with exit 1, naming each MODIFIED or REMOVED title it changed since the base.
    """
    merging = _maybe(tree, "rev-parse", "-q", "--verify", "MERGE_HEAD") is not None
    theirs = "MERGE_HEAD" if merging else default_branch(tree)
    base = _git(tree, "merge-base", "HEAD", theirs).strip()
    listing = _git(tree, "ls-tree", "--name-only", "HEAD:openspec/changes").split()
    changes = [name for name in listing if CHANGE_ID.fullmatch(name)]
    if len(changes) != 1:
        raise Stop(2, "integrate: cannot run — HEAD holds no single active change")
    specs = f"openspec/changes/{changes[0]}/specs"
    files = _git(tree, "ls-tree", "-r", "--name-only", "HEAD", "--", specs).split()
    moved = []
    for path in (p for p in files if p.endswith("/spec.md")):
        capability = Path(path).parent.name
        living = f"openspec/specs/{capability}/spec.md"
        sections = ("## MODIFIED Requirements", "## REMOVED Requirements")
        for title in _requirements(_show(tree, "HEAD", path) or "", sections):
            before = _requirement(_show(tree, base, living), title)
            if before != _requirement(_show(tree, theirs, living), title):
                moved.append(
                    f"delta: changed on the default branch: {capability}: {title}"
                )
    if moved:
        raise Stop(1, "\n".join(moved))
    return "delta: the default branch changed no requirement the delta edits"


def main(argv: list[str] | None = None) -> int:
    """Run one command; return its exit code."""
    parser = argparse.ArgumentParser(
        description="Merge the default branch into the next version by fixed rules."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("next", help="print the lowest-id open version, and if ready")
    for name, text in (
        ("changelog", "keep the branch's [Unreleased] entries above the releases"),
        ("decisions", "renumber the branch's new decisions, citations with them"),
        ("delta", "name each delta title the default branch changed since the base"),
    ):
        commands.add_parser(name, help=text).add_argument("worktree")
    args = parser.parse_args(argv)
    try:
        if args.command == "next":
            print(next_version(Path.cwd()))
        else:
            run = {"changelog": changelog, "decisions": decisions, "delta": delta}
            print(run[args.command](_tree(args.worktree)))
    except Stop as stop:
        print(stop)
        return stop.code
    return 0


if __name__ == "__main__":
    sys.exit(main())
