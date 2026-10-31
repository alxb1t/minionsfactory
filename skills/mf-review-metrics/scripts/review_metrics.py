# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Read the review findings and status logs of the repos the operator names.

    review_metrics.py [--config <path>] [--repo <path> …] [--out <path>]

Exit 0 read · 2 cannot run · any other a crash.
Why: 0045-review-metrics design D1, D2 and D4.
"""

import argparse
import os
import re
import sys
import tomllib
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

FINDINGS = Path(".minions/findings")
FILES = re.compile(r"(.+)_(?:review|security|status_log)\.md")
DAY_SECONDS = 86400

Record = dict[str, Any]
Number = int | float


class CannotRun(Exception):
    """The run cannot start; the message names what is missing."""


def config_path() -> Path:
    """Return where the config lives, by `XDG_CONFIG_HOME`, else in `~/.config`."""
    home = os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"
    return Path(home) / "minionsfactory" / "review-metrics.toml"


def _read_config(path: Path) -> dict[str, Any]:
    """Return the config at `path`, empty when there is no file."""
    if not path.is_file():
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise CannotRun(f"{path}: does not parse: {exc}") from exc


def _strings(path: Path, repos: object) -> list[str]:
    """Return the config's `repos`, or raise when it is not a list of strings."""
    if not isinstance(repos, list) or not all(isinstance(r, str) for r in repos):
        raise CannotRun(f"{path}: `repos` is not a list of strings")
    return repos


def settings(
    config: Path | None, repos: list[Path], out: Path | None
) -> tuple[list[Path], Path]:
    """Return the repos and the page's path; flags win over the config.

    The config's relative paths are against its directory, a flag's against the cwd.
    """
    path = config or config_path()
    data = _read_config(path)
    named = _strings(path, data.get("repos", []))
    page = data.get("out")
    if page is not None and not isinstance(page, str):
        raise CannotRun(f"{path}: `out` is not a string")

    def inside(text: str) -> Path:
        return (path.parent / Path(text).expanduser()).resolve()

    chosen = [r.resolve() for r in repos] or [inside(r) for r in named]
    if not chosen:
        raise CannotRun(f"no repo named: looked for {path}")
    if out is None and page is None:
        raise CannotRun(f"no page path: no --out, and no `out` in {path}")
    return chosen, out.resolve() if out else inside(str(page))


def _bullet(name: str) -> re.Pattern[str]:
    """Return the pattern of a `- **<name>:** <value>` line, its value the group."""
    return re.compile(rf"^[ \t]*- \*{{0,2}}{name}:\*{{0,2}}[ \t]*(.+)$", re.MULTILINE)


_PRIORITY = _bullet("Priority")
_VERDICT = _bullet("Verdict")
_STATUS = _bullet("Status")
_SEVERITY = _bullet("severity")
_EVENT = re.compile(
    r"^(\d\d):(\d\d):(\d\d) · (?:round \S+ · )?([\w-]+) — (.*)$", re.MULTILINE
)


def _word(text: str) -> str:
    """Return the first word of `text`, lowered; e.g. "Nit — why" → "nit"."""
    found = re.search(r"\w+", text)
    return found.group().lower() if found else "unknown"


def _split_front(text: str) -> tuple[dict[str, str], str]:
    """Return a file's frontmatter keys, and its body with backticks stripped."""
    found = re.match(r"---\n(.*?)\n---\n?", text, re.DOTALL)
    block, body = (found.group(1), text[found.end() :]) if found else ("", text)
    front = dict(re.findall(r"^(\w+):[ \t]*(.*?)[ \t]*$", block, re.MULTILINE))
    return front, body.replace("`", "")


def _section(body: str, heading: str) -> str | None:
    """Return the text of a `## ` section, or None when the body has none."""
    found = re.search(
        rf"^## +{heading}[^\n]*\n(.*?)(?=^## |\Z)",
        body,
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    return found.group(1) if found else None


def _priority(text: str) -> tuple[str, str | None]:
    """Return a `Priority:` value's severity and category.

    e.g. "medium · security · stability — why" → ("medium", "stability"),
    "medium · security (integrity)" → ("medium", "integrity")
    """
    fields = [field.strip() for field in text.partition(" — ")[0].split("·")]
    bracket = re.search(r"\(([^)]+)\)", fields[1]) if len(fields) > 1 else None
    category = fields[2] if len(fields) > 2 else bracket and bracket.group(1)
    return _word(fields[0]), category.lower() if category else None


def _graded(front: dict[str, str], body: str, cards: list[str]) -> Record:
    """Return a file's severity and category counts, and its finding count."""
    priorities = [_priority(text) for card in cards for text in _PRIORITY.findall(card)]
    grades = [grade for grade, _ in priorities] or [
        _word(grade) for grade in _SEVERITY.findall(body)
    ]
    readable = bool(grades) or front.get("verdict") == "clean"
    return {
        "findings": len(grades) if readable else None,
        "severity": Counter(grades),
        "categories": Counter(c for _, c in priorities if c),
    }


def _verdicts(body: str, cards: list[str]) -> Record:
    """Return a file's verdict states; each a gap when no card carries `Verdict:`."""
    verdicts = [
        (_word(_VERDICT.findall(card)[0]), _word("".join(_STATUS.findall(card))))
        for card in cards
        if _VERDICT.search(card)
    ]
    if not verdicts:
        return dict.fromkeys(
            ("confirmed", "plausible", "plausible_verified", "refuted")
        )
    words = [word for word, _ in verdicts]
    refuted = _section(body, "Refuted") or ""
    return {
        "confirmed": words.count("confirmed"),
        "plausible": words.count("plausible"),
        "plausible_verified": verdicts.count(("plausible", "verified")),
        "refuted": len(re.findall(r"^- ", refuted, re.MULTILINE)),
    }


def _resolutions(body: str) -> Record:
    """Return a file's `→ verified` and reopening transitions; gaps with no log."""
    log = _section(body, "Resolution log")
    if log is None:
        return {"verified": None, "reopened": None}
    reopened = re.findall(r"\b(?:fixed|wontfix|accepted) → open\b", log)
    return {
        "verified": len(re.findall(r"→ verified\b", log)),
        "reopened": len(reopened),
    }


def _findings_file(path: Path, blocking: tuple[str, ...]) -> Record | None:
    """Return what a findings file holds, or None when there is no file.

    `blocking` names the grades that block on this file's scale.
    """
    if not path.is_file():
        return None
    front, body = _split_front(path.read_text(encoding="utf-8", errors="replace"))
    pieces = re.split(r"^(?=- \*\*|#)", body, flags=re.MULTILINE)
    cards = [piece for piece in pieces if _PRIORITY.search(piece)]
    outside = "".join(piece for piece in pieces if not _PRIORITY.search(piece))
    graded = _graded(front, body, cards)
    found = graded["findings"]
    held = sum(graded["severity"][grade] for grade in blocking)
    return {
        "front": front,
        **graded,
        **_verdicts(body, cards),
        **_resolutions(body),
        "blocking": None if found is None else held,
        "inconclusive": (
            sum("inconclusive" in line for line in outside.splitlines())
            if "tier" in front
            else None
        ),
    }


def _seconds(event: tuple[str, ...]) -> int:
    """Return an event's time of day in seconds."""
    return int(event[0]) * 3600 + int(event[1]) * 60 + int(event[2])


def _run_seconds(run: str) -> int | None:
    """Return the seconds a run took, across midnight too; its log is newest on top."""
    events = _EVENT.findall(run)
    if not events:
        return None
    return (_seconds(events[0]) - _seconds(events[-1])) % DAY_SECONDS


def _status_log(path: Path) -> Record:
    """Return what a change's status log holds, every field a gap with no file."""
    if not path.is_file():
        return dict.fromkeys(("engine", "duration", "tokens", "capped", "to_backlog"))
    text = path.read_text(encoding="utf-8", errors="replace")
    runs = re.split(r"^## Run\b.*$", text, flags=re.MULTILINE)[1:]
    events = [(name, detail) for *_, name, detail in _EVENT.findall(text)]

    def details(name: str, pattern: str) -> list[str]:
        found = (re.search(pattern, d) for event, d in events if event == name)
        return [match.group(1) for match in found if match]

    engines = details("start", r"\bengine:? (\w[\w-]*)")
    tokens = details("verdicts", r"\btokens (\d+)(?:\s|$)")
    cards = details("done", r"\b(\d+) cards? to backlog")
    durations = [seconds for run in runs if (seconds := _run_seconds(run)) is not None]
    return {
        "engine": engines[0] if engines else None,
        "duration": sum(durations) if durations else None,
        "tokens": sum(map(int, tokens)) if tokens else None,
        "capped": int(bool(details("halt", r"\b(cap)\b"))),
        "to_backlog": sum(map(int, cards)) if cards else None,
    }


def _integer(text: str | None) -> int | None:
    """Return `text` as an int, or None; e.g. "3" → 3, "n/a" → None."""
    return int(text) if text and text.isdecimal() else None


def _packet(text: str | None) -> tuple[int | None, int | None]:
    """Return the entries included and skipped.

    e.g. "proposal.md, design.md; skipped: threat model" → (2, 1)
    """
    if not text:
        return None, None

    def count(entries: str) -> int:
        parts = (part.strip().lower() for part in re.split(r"[,;]", entries))
        return sum(part not in ("", "none") for part in parts)

    included, _, skipped = text.partition("skipped:")
    return count(included), count(skipped)


def _first(fronts: list[dict[str, str]], key: str) -> str | None:
    """Return `key` from the first frontmatter holding it, the review file's first."""
    return next((front[key] for front in fronts if front.get(key)), None)


def _total(values: Iterable[int | None]) -> int | None:
    """Return the sum; a gap in any file, or no file, is a gap."""
    held = list(values)
    return None if not held or None in held else sum(v for v in held if v is not None)


def _held(values: Iterable[int | None]) -> int | None:
    """Return the sum of the files that hold the field, a gap when none does.

    Why: a clean file has no card or log, and adds nothing to its sibling's counts.
    """
    known = [value for value in values if value is not None]
    return sum(known) if known else None


def read_change(repo: Path, change: str) -> Record:
    """Return a change's record, each field parsed on its own, None when unreadable."""
    folder = repo / FINDINGS
    files = [
        found
        for role, blocking in (
            ("review", ("blocking",)),
            ("security", ("critical", "high")),
        )
        if (found := _findings_file(folder / f"{change}_{role}.md", blocking))
    ]
    fronts = [found["front"] for found in files]
    included, skipped = _packet(_first(fronts, "packet"))
    record: Record = {
        "repo": repo.name,
        "change": change,
        "reviewed": _first(fronts, "reviewed"),
        "tier": _first(fronts, "tier"),
        "model": _first(fronts, "model"),
        "mode": _first(fronts, "mode"),
        "workers": _total(_integer(front.get("workers")) for front in fronts),
        "packet_included": included,
        "packet_skipped": skipped,
        "rounds": _integer(_first(fronts, "round")),
        "severity": sum((found["severity"] for found in files), Counter()),
        "categories": sum((found["categories"] for found in files), Counter()),
        **_status_log(folder / f"{change}_status_log.md"),
    }
    for key in ("findings", "blocking", "inconclusive"):
        record[key] = _total(found[key] for found in files)
    for key in (
        "confirmed",
        "plausible",
        "plausible_verified",
        "refuted",
        "verified",
        "reopened",
    ):
        record[key] = _held(found[key] for found in files)
    return record


def read_repo(repo: Path) -> list[Record]:
    """Return the repo's records in `reviewed` order, those with no date last."""
    names = (path.name for path in (repo / FINDINGS).glob("*.md"))
    changes = {found.group(1) for name in names if (found := FILES.fullmatch(name))}
    records = [read_change(repo, change) for change in changes]
    return sorted(
        records,
        key=lambda r: (r["reviewed"] is None, r["reviewed"] or "", r["change"]),
    )


def main(argv: list[str] | None = None) -> int:
    """Read the repos the config or the flags name; return the exit code."""
    parser = argparse.ArgumentParser(
        prog="review_metrics.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--config", type=Path)
    parser.add_argument("--repo", action="append", default=[], type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    try:
        repos, _ = settings(args.config, args.repo, args.out)
    except CannotRun as exc:
        print(exc, file=sys.stderr)
        return 2
    read = [read_repo(repo) for repo in repos]
    print(f"repos: {len(read)} · changes: {sum(map(len, read))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
