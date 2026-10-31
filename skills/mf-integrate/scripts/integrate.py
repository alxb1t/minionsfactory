# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Merge the default branch into the next version by fixed rules.

    integrate.py next [<change-id>]
    integrate.py changelog <worktree>
    integrate.py decisions <worktree>
    integrate.py delta <worktree>

Exit 0 done · 1 halt: not ready, or a conflict the rules do not cover · 2 cannot run.
The worktree commands read an open merge; `changelog` and `decisions` stage
what they write.
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
RELEASE = re.compile(r"chore\(release\): \S+")
UNRELEASED = re.compile(r"^## \[Unreleased\]\n", re.MULTILINE)
RELEASED = re.compile(r"^## \[", re.MULTILINE)
DECISIONS = "docs/decisions.md"
DECISION = re.compile(r"^### D(\d+) ", re.MULTILINE)
# A citation is `D45` in text or `#d45--` in a link's anchor.
CITATION = re.compile(r"(\bD|#d)(\d+)\b")
EDITED = ("## MODIFIED Requirements", "## REMOVED Requirements")
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

    e.g. a findings file opening `verdict: clean` in its block, "verdict" → "clean"
    """
    if not text.startswith("---\n"):
        return None
    block = text[4:].split("\n---", 1)[0]
    found = re.search(rf"^{key}:\s*(\S+)", block, re.MULTILINE)
    return found[1] if found else None


def _after(text: str) -> list[str]:
    r"""Return the change ids a proposal's `after:` names.

    e.g. "---\nafter: [0047-x, 0048-y]\n---\n" → ["0047-x", "0048-y"]
    """
    found = re.search(r"^after:\s*\[(.*)\]", text.split("\n---", 1)[0], re.MULTILINE)
    return re.findall(r"[^,\s]+", found[1]) if found else []


def _shipped(cwd: Path, rev: str, change: str) -> bool:
    """Return whether `rev` holds the change's archive folder."""
    path = f"{rev}:openspec/changes/archive/{change}"
    return _maybe(cwd, "cat-file", "-e", path) is not None


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


def unready(cwd: Path, change: str, tree: Path | None) -> str | None:
    """Return why the version is not ready, or None when it is.

    Ready is every `## Progress` box ticked, every `after:` id in its tree, and both
    findings files clean or converge skipped: no findings file and no diff patch.
    """
    if tree is None:
        return "no worktree"
    tasks = _show(cwd, change, f"openspec/changes/{change}/tasks.md") or ""
    boxes = PROGRESS.findall(tasks)
    if not boxes:
        return "tasks.md has no ## Progress list"
    unticked = [number for mark, number in boxes if mark != "x"]
    if unticked:
        return f"phase {unticked[0]} unticked"
    proposal = _show(cwd, change, f"openspec/changes/{change}/proposal.md") or ""
    for dependency in _after(proposal):
        if not _shipped(cwd, change, dependency):
            return f"after {dependency}"
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


def _settling(cwd: Path, change: str, tree: Path | None) -> bool:
    """Return whether the version's merge is open with its note beside it."""
    note = _run_dir(cwd) / "integrate" / f"{change}.md"
    return (
        tree is not None
        and note.is_file()
        and _maybe(tree, "rev-parse", "-q", "--verify", "MERGE_HEAD") is not None
    )


def _holds(cwd: Path, change: str) -> bool:
    """Return whether a branch holds its change, active or just released."""
    if _show(cwd, change, f"openspec/changes/{change}/proposal.md") is not None:
        return True
    return (
        RELEASE.fullmatch(_git(cwd, "log", "-1", "--format=%s", change).strip())
        is not None
    )


def next_version(cwd: Path, change: str | None = None) -> str:
    """Return the named or the lowest-id ready version, its worktree and readiness.

    A version is a branch named by a change id that holds its change. A named
    version whose merge is open with its note is ready: a dependent's opens before
    its build. With none ready, stop on the lowest id's line.
    """
    default = default_branch(cwd)
    listing = _git(
        cwd,
        *("branch", "--no-merged", default, "--list", "[0-9]*"),
        "--format=%(refname:short)",
    )
    changes = [
        name
        for name in listing.split()
        if CHANGE_ID.fullmatch(name) and _holds(cwd, name)
    ]
    if change is not None and change not in changes:
        raise Stop(1, f"next: {change} · not open")
    if not changes:
        raise Stop(1, "next: none — no open version")
    trees = _worktrees(cwd)
    lines = []
    picks = [change] if change else changes
    for name in sorted(picks, key=lambda name: int(name.split("-")[0])):
        tree = trees.get(name)
        line = f"next: {name} · {tree or 'no worktree'}"
        if change and _settling(cwd, name, tree):
            return f"{line} · ready"
        if (why := unready(cwd, name, tree)) is None:
            return f"{line} · ready"
        lines.append(f"{line} · not ready — {why}")
    raise Stop(1, lines[0])


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


def _safe_path(tree: Path, path: str) -> Path:
    """Return a regular worktree path, rejecting links and escaping components."""
    relative = Path(path)
    if relative.is_absolute() or ".." in relative.parts:
        raise Stop(1, f"integrate: halt — unsafe path: {path}")
    root = tree.resolve()
    target = root
    for part in relative.parts:
        target /= part
        if target.is_symlink():
            raise Stop(1, f"integrate: halt — unsafe path: {path}")
    if not target.resolve().is_relative_to(root) or (
        target.exists() and not target.is_file()
    ):
        raise Stop(1, f"integrate: halt — unsafe path: {path}")
    return target


def _write(tree: Path, path: str, text: str) -> None:
    """Write a resolved file and stage it, unless git still holds it in conflict."""
    _safe_path(tree, path).write_text(text)
    if "<<<<<<<" not in text or path not in _unmerged(tree):
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
    """Return a group-map line both sides appended decision ids to; else None.

    e.g. "D44", "D44, D46", "D44, D45" → "D44, D45, D46"
    """
    if not CITATION.search(base):
        return None
    tokens = TOKEN.findall(base)
    inserts: dict[int, list[str]] = {}
    for side in (theirs, ours):
        for start, end, added in _changes(tokens, TOKEN.findall(side)):
            if start != end or not re.fullmatch(r"(?:, D\d+)+", "".join(added)):
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


def _resolve(
    base: list[str], ours: list[str], theirs: list[str], group_map: bool
) -> list[str]:
    """Return one region both sides edited, by the rules; else stop with exit 1.

    One side alone edited → its edit. New decision sections → theirs, then ours.
    Group map lines accept added ids. Overlapping prose goes to the person.
    """
    if ours == base or ours == theirs:
        return theirs
    if theirs == base:
        return ours
    if not base and all(
        DECISION.match("".join(side).lstrip("\n")) for side in (ours, theirs)
    ):
        return theirs + ours
    if group_map and len(base) == len(ours) == len(theirs):
        lines = [_merge_line(*trio) for trio in zip(base, ours, theirs, strict=True)]
        if None not in lines:
            return [line for line in lines if line is not None]
    where = (base[0].strip() if base else "") or "a blank line"
    raise Stop(1, f"decisions: halt — both sides changed the text at: {where}")


def merge3(base: str, ours: str, theirs: str, *, decision_map: bool = False) -> str:
    """Return the three-way merge of the sides, by the rules in `_resolve`."""
    lines = base.splitlines(keepends=True)
    edits = sorted(
        (start, end, side, added)
        for side, text in enumerate((ours, theirs))
        for start, end, added in _changes(lines, text.splitlines(keepends=True))
    )
    # A group is the base span overlapping edits cover, with each side's edits in it.
    groups: list[tuple[int, int, list[list[Edit]]]] = []
    for start, end, side, added in edits:
        if groups and (start < groups[-1][1] or start == groups[-1][0]):
            first, last, sides = groups[-1]
            groups[-1] = (first, max(last, end), sides)
        else:
            sides = [[], []]
            groups.append((start, end, sides))
        sides[side].append((start, end, added))
    out: list[str] = []
    pos = 0
    for start, end, (mine, yours) in groups:
        regions = [_apply(lines, start, end, side) for side in (mine, yours)]
        prefix = lines[:start]
        in_map = (
            decision_map
            and not any(line.startswith("## ") for line in prefix)
            and sum(line.startswith("```") for line in prefix) % 2 == 1
        )
        out += lines[pos:start] + _resolve(
            lines[start:end], regions[0], regions[1], in_map
        )
        pos = end
    return "".join(out + lines[pos:])


def _ids(text: str) -> set[int]:
    """Return the decision ids `text` heads a section with."""
    return {int(n) for n in DECISION.findall(text)}


def _recite(tree: Path, path: str, ids: dict[int, int], base: str) -> None:
    """Merge the branch's renumbered citations using edit positions in the base.

    A manual resolution that differs from the mechanical merge has ambiguous
    ownership and is handed to the person.
    """
    target = _safe_path(tree, path)
    try:
        text = target.read_text()
    except (OSError, UnicodeDecodeError):
        return
    if not any(int(match[2]) in ids for match in CITATION.finditer(text)):
        return
    before, ours, theirs = (
        _show(tree, rev, path) or "" for rev in (base, "HEAD", "MERGE_HEAD")
    )
    expected = merge3(before, ours, theirs)
    rewritten = merge3(before, _renumber(ours, ids), theirs)
    if text not in (expected, rewritten):
        raise Stop(1, f"decisions: halt — citation ownership is ambiguous in {path}")
    if rewritten != text:
        _write(tree, path, rewritten)


def decisions(tree: Path) -> str:
    """Renumber the branch's new decisions past the default branch's, and merge."""
    base = _merge_base(tree)
    sides = [_show(tree, rev, DECISIONS) for rev in (base, "HEAD", "MERGE_HEAD")]
    if sides == [None, None, None]:
        return f"decisions: none — no {DECISIONS}"
    base_text, ours, theirs = (side or "" for side in sides)
    top = max(_ids(theirs), default=0)
    new = sorted(_ids(ours) - _ids(base_text))
    ids: dict[int, int] = {}
    if new and new[0] <= top:
        ids = {old: top + i for i, old in enumerate(new, 1)}
    _write(
        tree,
        DECISIONS,
        merge3(base_text, _renumber(ours, ids), theirs, decision_map=True),
    )
    if not ids:
        return "decisions: no id collides"
    for path in _git(tree, "diff", "--name-only", base, "HEAD").splitlines():
        if path != DECISIONS:
            _recite(tree, path, ids, base)
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
    base = _merge_base(tree)
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
        before, after = (_show(tree, rev, living) for rev in (base, "MERGE_HEAD"))
        for title in _requirements(_show(tree, "HEAD", path) or "", EDITED):
            if _requirement(before, title) != _requirement(after, title):
                moved.append(
                    f"delta: changed on the default branch: {capability}: {title}"
                )
    if moved:
        raise Stop(1, "\n".join(moved))
    return "delta: the default branch changed no requirement the delta edits"


ON_A_MERGE = {
    "changelog": (
        changelog,
        "keep the branch's [Unreleased] entries above the releases",
    ),
    "decisions": (
        decisions,
        "renumber the branch's new decisions, citations with them",
    ),
    "delta": (delta, "name each delta title the default branch changed since the base"),
}


def main(argv: list[str] | None = None) -> int:
    """Run one command; return its exit code."""
    parser = argparse.ArgumentParser(
        description="Merge the default branch into the next version by fixed rules."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    picking = commands.add_parser(
        "next", help="print the named or the lowest-id ready version"
    )
    picking.add_argument("change", metavar="change-id", nargs="?")
    for name, (_, text) in ON_A_MERGE.items():
        commands.add_parser(name, help=text).add_argument("worktree")
    args = parser.parse_args(argv)
    try:
        if args.command == "next":
            print(next_version(Path.cwd(), args.change))
        else:
            print(ON_A_MERGE[args.command][0](_tree(args.worktree)))
    except Stop as stop:
        print(stop)
        return stop.code
    return 0


if __name__ == "__main__":
    sys.exit(main())
