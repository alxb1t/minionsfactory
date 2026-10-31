# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Draw one page of the review findings and status logs of the repos the operator names.

    review_metrics.py [--config <path>] [--repo <path> …] [--out <path>]

Exit 0 written · 2 cannot run · any other a crash.
Why: 0045-review-metrics design D1…D4 and D7.
"""

import argparse
import html
import importlib.util
import os
import re
import statistics
import sys
import tomllib
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any

FINDINGS = Path(".minions/findings")
FILES = re.compile(r"(.+)_(?:review|security|status_log)\.md")
DAY_SECONDS = 86400
CHARTS = {
    "rounds": "rounds",
    "findings": "findings",
    "blocking": "blocking",
    "verified": "verified",
    "reopened": "reopened",
    "capped": "capped",
    "to_backlog": "to backlog",
    "duration": "duration (s)",
    "tokens": "tokens",
}
# why: old cards hold free text in that field; mf-converge's card names the list
CATEGORIES = (
    "security",
    "stability",
    "data integrity",
    "functional correctness",
    "performance",
    "maintainability",
)
TOP_CATEGORIES = 3
IDENTITY = 3  # the tier table's leading columns: tier, model, engine
VERDICT_FIELDS = ("confirmed", "plausible", "plausible_verified", "refuted")
RESOLUTION_FIELDS = ("verified", "reopened")
GAP = "—"

Record = dict[str, Any]
Number = int | float
Chart = Callable[[dict[str, Any], list[tuple[str, Number | None, bool]]], str]
Table = tuple[list[str], list[list[str]]]

_E = html.escape


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
_DENIED = re.compile(r"\b(?:no|not|none|never|without)\b[^,.;]*inconclusive")
# why: a findings file's text is evidence; a terminal escape in it must not reach stdout
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
_PRINTABLE = re.compile(r"[\w.\-:/ ]{1,64}")
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
    block = _CONTROL.sub("", block)
    pairs = re.findall(
        r"^(\w+):[ \t]*(?:([\"'])(.*)\2|(.*?))[ \t]*$", block, re.MULTILINE
    )
    front = {key: quoted or plain for key, _, quoted, plain in pairs}
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
    "medium · security (integrity)" → ("medium", "integrity"),
    'nit · review · "a quoted clause"' → ("nit", None)
    """
    fields = [field.strip() for field in text.partition(" — ")[0].split("·")]
    bracket = re.search(r"\(([a-zA-Z]+)\)", fields[1]) if len(fields) > 1 else None
    third = fields[2].lower() if len(fields) > 2 else None
    category = bracket.group(1).lower() if bracket else None
    return _word(fields[0]), third if third in CATEGORIES else category


def _graded(
    front: dict[str, str], body: str, cards: list[str], blocking: tuple[str, ...]
) -> Record:
    """Return a file's severity and category counts, and its finding counts."""
    priorities = [_priority(text) for card in cards for text in _PRIORITY.findall(card)]
    grades = [grade for grade, _ in priorities] or [
        _word(grade) for grade in _SEVERITY.findall(body)
    ]
    severity = Counter(grades)
    readable = bool(grades) or front.get("verdict") == "clean"
    return {
        "findings": len(grades) if readable else None,
        "blocking": sum(severity[grade] for grade in blocking) if readable else None,
        "severity": severity,
        "categories": Counter(c for _, c in priorities if c),
    }


def _verdicts(body: str, cards: list[str]) -> Record:
    """Return a file's verdict states; each a gap when no card carries `Verdict:`."""
    verdicts = [
        (_word(found.group(1)), _word("".join(_STATUS.findall(card))))
        for card in cards
        if (found := _VERDICT.search(card))
    ]
    if not verdicts:
        return dict.fromkeys(VERDICT_FIELDS)
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
        return dict.fromkeys(RESOLUTION_FIELDS)
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
    return {
        "front": front,
        **_graded(front, body, cards, blocking),
        **_verdicts(body, cards),
        **_resolutions(body),
        "inconclusive": (
            sum(
                "inconclusive" in line and not _DENIED.search(line.lower())
                for line in outside.splitlines()
            )
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
    return {
        "engine": engines[0] if engines else None,
        "duration": _held(_run_seconds(run) for run in runs),
        "tokens": _held(map(int, tokens)),
        "capped": int(bool(details("halt", r"\b(cap)\b"))),
        "to_backlog": _held(map(int, cards)),
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
    return None if None in held else _held(held)


def _held(values: Iterable[int | None]) -> int | None:
    """Return the sum of the values held, a gap when none is.

    Why: a clean file has no card or log, and adds nothing to its sibling's counts.
    """
    known = [value for value in values if value is not None]
    return sum(known) if known else None


def _merged(rows: Iterable[Record], key: str) -> Counter[str]:
    """Return the rows' `key` counters, added up."""
    return sum((row[key] for row in rows), Counter())


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
        "severity": _merged(files, "severity"),
        "categories": _merged(files, "categories"),
        **_status_log(folder / f"{change}_status_log.md"),
    }
    for key in ("findings", "blocking", "inconclusive"):
        record[key] = _total(found[key] for found in files)
    for key in (*VERDICT_FIELDS, *RESOLUTION_FIELDS):
        record[key] = _held(found[key] for found in files)
    return record


def read_repo(repo: Path) -> list[Record]:
    """Return the repo's records in `reviewed` order, those with no date last."""
    if not (repo / FINDINGS).is_dir():
        raise CannotRun(f"{repo}: no {FINDINGS} directory")
    names = (path.name for path in (repo / FINDINGS).glob("*.md"))
    changes = {found.group(1) for name in names if (found := FILES.fullmatch(name))}
    records = [read_change(repo, change) for change in changes]
    return sorted(
        records,
        key=lambda r: (r["reviewed"] is None, r["reviewed"] or "", r["change"]),
    )


def load_chart() -> tuple[Chart, str]:
    """Return `mf-build`'s `chart` and `_STYLE`, loaded from its package."""
    path = Path(__file__).resolve().parent / "../../mf-build/scripts/metrics.py"
    spec = importlib.util.spec_from_file_location("mf_build_metrics", path)
    if spec is None or spec.loader is None or not path.is_file():
        raise CannotRun(f"no chart: looked for {path.resolve()}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.chart, module._STYLE


def _known(records: list[Record], field: str) -> list[Number]:
    """Return the field's values, gaps left out."""
    return [record[field] for record in records if record[field] is not None]


def _figure(value: Number) -> str:
    """Return a number for a table; e.g. 1.5 → "1.5", 2.0 → "2", 1234567 → "1234567"."""
    return f"{value:.1f}".removesuffix(".0")


def _counted(
    stat: Callable[[list[Number]], Number], records: list[Record], field: str
) -> str:
    """Return the statistic with its count beside it; e.g. "1.5 (n=2)", a gap "—"."""
    known = _known(records, field)
    return f"{_figure(stat(known))} (n={len(known)})" if known else GAP


def _summed(records: list[Record], field: str) -> str:
    """Return the sum of the records holding the field, a gap when none does."""
    known = _known(records, field)
    return _figure(sum(known)) if known else GAP


def _top(records: list[Record]) -> str:
    """Return the most found categories; e.g. "maintainability 2, security 1"."""
    counts = _merged(records, "categories").most_common(TOP_CATEGORIES)
    return ", ".join(f"{name} {n}" for name, n in counts) or GAP


def _repo_table(records: list[Record]) -> Table:
    """Return a repo's table: a column per measure, its one row over every change."""
    per_change = ("findings", "blocking", "verified", "reopened")
    return (
        [
            "changes",
            "median rounds",
            *(f"{field} per change" for field in per_change),
            "capped",
            "to backlog",
        ],
        [
            [
                str(len(records)),
                _counted(statistics.median, records, "rounds"),
                *(_counted(statistics.fmean, records, field) for field in per_change),
                _summed(records, "capped"),
                _summed(records, "to_backlog"),
            ]
        ],
    )


def _severity_table(records: list[Record]) -> Table:
    """Return the findings per grade, a row per grade the repo used."""
    grades = _merged(records, "severity").most_common()
    return ["grade", "findings"], [[grade, str(count)] for grade, count in grades]


def tier_table(records: list[Record]) -> Table:
    """Return a row per tier, model and engine, `unknown` for a gap."""
    groups: dict[tuple[str, ...], list[Record]] = {}
    for record in records:
        key = tuple(record[f] or "unknown" for f in ("tier", "model", "engine"))
        groups.setdefault(key, []).append(record)
    summed = (*VERDICT_FIELDS, "inconclusive", "packet_included", "packet_skipped")
    headers = [
        "tier",
        "model",
        "engine",
        "changes",
        "median rounds",
        "findings per change",
        "blocking per change",
        "median workers",
        *(field.replace("_", " ") for field in summed),
        "top categories",
        "median duration (s)",
        "median tokens",
    ]
    rows = [
        [
            *key,
            str(len(group)),
            _counted(statistics.median, group, "rounds"),
            _counted(statistics.fmean, group, "findings"),
            _counted(statistics.fmean, group, "blocking"),
            _counted(statistics.median, group, "workers"),
            *(_summed(group, field) for field in summed),
            _top(group),
            _counted(statistics.median, group, "duration"),
            _counted(statistics.median, group, "tokens"),
        ]
        for key, group in sorted(groups.items())
    ]
    return headers, rows


def lacked(records: list[Record]) -> str:
    """Return each gap field and its count; e.g. "tier 2 · tokens 3", else "none"."""
    gaps = Counter(k for record in records for k, v in record.items() if v is None)
    return " · ".join(f"{k} {n}" for k, n in sorted(gaps.items())) or "none"


def _html_table(table: Table) -> str:
    """Return a table as escaped HTML."""

    def row(tag: str, cells: Sequence[str]) -> str:
        return "<tr>" + "".join(f"<{tag}>{_E(c)}</{tag}>" for c in cells) + "</tr>"

    headers, rows = table
    return "\n".join(
        ["<table>", row("th", headers), *(row("td", r) for r in rows), "</table>"]
    )


def _markdown_table(table: Table) -> str:
    """Return a table as markdown."""
    headers, rows = table
    lines = [headers, ["---"] * len(headers), *rows]
    return "\n".join("| " + " | ".join(cells) + " |" for cells in lines)


def _repo_section(name: str, records: list[Record], chart: Chart) -> list[str]:
    """Return a repo's lines: its tables, then a chart per measure over its changes."""
    lines = [
        '<section class="repo">',
        f"<h2>{_E(name)}</h2>",
        _html_table(_repo_table(records)),
        "<h3>findings per grade</h3>",
        _html_table(_severity_table(records)),
        '<div class="charts">',
    ]
    for field, title in CHARTS.items():
        # why: a whole change id overruns its neighbours on the axis
        points = [(r["change"].partition("-")[0], r[field], False) for r in records]
        lines.append(
            f"<figure><figcaption>{_E(title)}</figcaption>"
            f"{chart({'title': title}, points)}</figure>"
        )
    return [*lines, "</div>", "</section>"]


def _every_record(read: list[tuple[str, list[Record]]]) -> list[Record]:
    """Return the records of every repo read."""
    return [record for _, held in read for record in held]


def render_page(read: list[tuple[str, list[Record]]], chart: Chart, style: str) -> str:
    """Return the page, laid out per 0045-review-metrics design D7."""
    records = _every_record(read)
    lines = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        f"<title>Review metrics</title><style>{style}</style></head><body>",
        "<h1>Review metrics</h1>",
        f"<p>repos read {len(read)} · changes read {len(records)}</p>",
    ]
    for name, held in read:
        lines += _repo_section(name, held, chart)
    lines += ["<h2>tier × model</h2>", _html_table(tier_table(records))]
    lines += ["<h2>lacked</h2>", "<ul>"]
    lines += [f"<li>{_E(name)}: {_E(lacked(held))}</li>" for name, held in read]
    lines += ["</ul>", "</body></html>"]
    return "\n".join(lines) + "\n"


def _printable(text: str) -> str:
    """Return `text` when shaped like a tier, model or engine name, else `unknown`."""
    return text if _PRINTABLE.fullmatch(text) else "unknown"


def summary(out: Path, read: list[tuple[str, list[Record]]]) -> str:
    """Return what a written run prints, per 0045-review-metrics design D2."""
    records = _every_record(read)
    headers, rows = tier_table(records)
    shown = [[_printable(c) for c in row[:IDENTITY]] + row[IDENTITY:] for row in rows]
    return "\n".join(
        [
            str(out),
            f"repos: {len(read)} · changes: {len(records)}",
            _markdown_table((headers, shown)),
            f"lacked: {lacked(records)}",
        ]
    )


def _write(path: Path, text: str) -> None:
    """Write the page, its folder too."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise CannotRun(f"{path}: cannot write: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    """Draw the page of the repos the config or the flags name; return the exit code."""
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
        repos, out = settings(args.config, args.repo, args.out)
        chart, style = load_chart()
        read = [(repo.name, read_repo(repo)) for repo in repos]
        _write(out, render_page(read, chart, style))
    except CannotRun as exc:
        print(exc, file=sys.stderr)
        return 2
    print(summary(out, read))
    return 0


if __name__ == "__main__":
    sys.exit(main())
