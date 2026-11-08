# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Draw one page and its data from the repos named and the operator's Codex sessions.

The repos' findings, status logs and run logs are read, none written.

    review_metrics.py [--config <path>] [--repo <path> …] [--out <path>]

The data is `review-metrics.json`, beside the page.
Exit 0 written · 2 cannot run · any other a crash.
Why: 0045-review-metrics design D1…D4 and D7; 0077-run-metrics design D5.
"""

import argparse
import functools
import html
import importlib.util
import json
import os
import re
import statistics
import subprocess
import sys
import tomllib
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

CHANGES = Path(".minions/changes")
# A repo no run has moved keeps its files here, and its worker logs under `RUNS`.
FINDINGS = Path(".minions/findings")
RUNS = Path(".minions/runs")
DATA = "review-metrics.json"
FILES = (
    "conformance.md",
    "adversarial.md",
    "review.md",
    "security.md",
    "status_log.md",
)
OLD_FILES = re.compile(r"(.+)_(?:review|security|status_log)\.md")
STATIONS = ("build", "converge", "integrate", "release", "rescue")
ROLES = ("conformance", "adversarial")
# The checkers' names before 0095-converge-roles, read as written.
OLD_ROLES = ("review", "security")
# The old era's forms a `verdicts` line names both roles' tokens in, and each one's
# scale.
_TWO_ROLES = (
    (re.compile(r"\btokens review (\d+), security (\d+)"), 1),
    (re.compile(r"\btokens (\d+) \+ (\d+)"), 1),
    (re.compile(r"\(review (\d+)k, security (\d+)k\)"), 1000),
    (re.compile(r"\btokens (\d+) review, (\d+) security"), 1),
)
_TAIL = re.compile(r"executor (\S+) · model (\S+) · effort (\S+)")
_ROUND_EVENT = re.compile(
    r"^(\d\d:\d\d:\d\d) · round (\d+) · ([\w-]+) — (.*)$", re.MULTILINE
)
# why: a clock set back an hour is no midnight
HALF_DAY = timedelta(hours=12)
TOKENS = (
    "inputTokens",
    "outputTokens",
    "cacheReadInputTokens",
    "cacheCreationInputTokens",
)
# A Codex log's prices, read when one is priced. Why: 0096-codex-ready design D6.
PRICES = Path(__file__).resolve().parents[1] / "prices.toml"
# The events a worker log's cost is read from; a spawn line, from its first line alone.
SPENT = ("result", "turn.completed")
DAY_SECONDS = 86400
CHARTS = {
    "rounds": "rounds",
    "findings": "findings",
    "blocking": "blocking",
    "verified": "verified",
    "reopened": "reopened",
    "capped": "capped",
    "to_backlog": "to debt",
    "duration": "duration (s)",
    "tokens": "tokens",
}
# why: old cards hold free text in that field; the card in converge's worker reference
# names the list
CATEGORIES = (
    "security",
    "stability",
    "data integrity",
    "functional correctness",
    "performance",
    "maintainability",
)
TOP_CATEGORIES = 3
IDENTITY = 2  # the model table's leading columns: model, engine
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
            if _section(body, "Refuted") is not None
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


def _role_tokens(detail: str) -> list[tuple[str, int | None]]:
    """Return a `verdicts` line's tokens per role; `both` takes a shared figure.

    e.g. "conformance clean · tokens 9" → [("conformance", 9)],
    "review clean · security clean · tokens unavailable" →
    [("review", None), ("security", None)]. Why: 0077-run-metrics design D5;
    0095-converge-roles design D4.
    """
    for pattern, scale in _TWO_ROLES:
        if found := pattern.search(detail):
            pairs = enumerate(OLD_ROLES, 1)
            return [(role, int(found[n]) * scale) for n, role in pairs]
    named = [role for role in (*ROLES, *OLD_ROLES) if re.search(rf"\b{role}\b", detail)]
    if found := re.search(r"\btokens (\d+)(?:\s|$)", detail):
        one = len(named) == 1 and detail.startswith(named[0])
        return [(named[0] if one else "both", int(found[1]))]
    return [(role, None) for role in named]


def _utc(local: datetime) -> datetime:
    """Return a local time in UTC, by `$TZ`'s zone, else the system's."""
    try:
        zone = ZoneInfo(os.environ.get("TZ", "").removeprefix(":"))
    except (ValueError, ZoneInfoNotFoundError):
        return local.astimezone(UTC)
    return local.replace(tzinfo=zone).astimezone(UTC)


def _windows(heading: str, body: str) -> dict[str, tuple[datetime, datetime]]:
    """Return each round's window in UTC; a heading with no date has none.

    A window runs from the last freeze before the round's fan-out to its verdicts
    plus a minute. e.g. a round 1 frozen at 16:02:32, its verdicts at 16:13:13 →
    {"1": (16:02:32, 16:14:13)}, each in UTC.
    """
    dated = re.match(r"## Run \d+ — (\d{4}-\d\d-\d\d \d\d:\d\d)", heading)
    if not dated:
        return {}
    last = datetime.strptime(dated[1], "%Y-%m-%d %H:%M")
    lines: list[tuple[datetime, str, str]] = []
    for time, round_, event, _ in reversed(_ROUND_EVENT.findall(body)):
        clock = datetime.strptime(time, "%H:%M:%S").time()
        at = datetime.combine(last.date(), clock)
        last = at + timedelta(days=1) if last - at > HALF_DAY else at
        lines.append((last, round_, event))
    windows = {}
    for end, round_, event in lines:
        fan_outs = [
            t for t, r, e in lines if (r, e) == (round_, "fan-out") and t <= end
        ]
        freezes = [
            t for t, _, e in lines if e == "freeze" and fan_outs and t <= fan_outs[-1]
        ]
        if event == "verdicts" and freezes:
            windows[round_] = (_utc(freezes[-1]), _utc(end + timedelta(minutes=1)))
    return windows


def _round_records(path: Path) -> list[Record]:
    """Return a status log's tokens per run, round and role, with each round's window.

    D1's tail names a record's executor, model and effort, else each is a gap.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    parts = re.split(r"^(## Run\b.*)$", text, flags=re.MULTILINE)[1:]
    records: list[Record] = []
    for heading, body in zip(parts[::2], parts[1::2], strict=True):
        numbered = re.match(r"## Run (\d+)", heading)
        run = int(numbered[1]) if numbered else None
        windows = _windows(heading, body)
        for _, round_, event, detail in _ROUND_EVENT.findall(body):
            tail = _TAIL.search(detail)
            # `default` is no name known
            names = (
                [n if n != "default" else None for n in tail.groups()]
                if tail
                else [None] * 3
            )
            records += [
                {
                    "run": run,
                    "round": int(round_),
                    "role": role,
                    **dict(zip(("executor", "model", "effort"), names, strict=True)),
                    "tokens": tokens,
                    "sessions": None,
                    "source": "status-log",
                    "window": windows.get(round_),
                }
                for role, tokens in _role_tokens(detail)
                if event == "verdicts"
            ]
    return records


def _dig(value: object, *keys: str) -> object:
    """Return the value at `keys` in nested dicts, None where one is missing."""
    for key in keys:
        value = value.get(key) if isinstance(value, dict) else None
    return value


def _object(line: str) -> dict[str, Any]:
    """Return a JSON line's object, an empty one for anything else."""
    try:
        found = json.loads(line)
    except json.JSONDecodeError:
        return {}
    return found if isinstance(found, dict) else {}


def _session(path: Path) -> Record:
    """Return a Codex session's id, cwd, start, repo URL, role and parent.

    A checker's model, effort and last cumulative tokens too, its role under either
    era's name.
    """
    with path.open(encoding="utf-8", errors="replace") as lines:
        meta = _dig(_object(next(lines, "")), "payload")
        spawn = _dig(meta, "source", "subagent", "thread_spawn")
        agent = str(_dig(spawn, "agent_path") or "").rpartition("/")[2]
        roles = (*ROLES, *OLD_ROLES)
        role = next((role for role in roles if agent.startswith(role)), None)
        session: Record = {
            "id": _dig(meta, "id"),
            "cwd": _dig(meta, "cwd"),
            "url": _dig(meta, "git", "repository_url"),
            "parent": _dig(spawn, "parent_thread_id"),
            "role": role,
            "model": None,
            "effort": None,
            "tokens": None,
        }
        started = _dig(meta, "timestamp")
        try:
            session["start"] = datetime.fromisoformat(str(started))
        except ValueError:
            session["start"] = None
        for line in lines if role else ():
            event = (
                _object(line) if "turn_context" in line or "token_count" in line else {}
            )
            if event.get("type") == "turn_context" and session["model"] is None:
                session["model"] = _dig(event, "payload", "model")
                session["effort"] = _dig(event, "payload", "effort")
            usage = _dig(event, "payload", "info", "total_token_usage", "total_tokens")
            if _dig(event, "payload", "type") == "token_count" and _number(usage):
                session["tokens"] = usage
    return session


@functools.cache
def _all_sessions(folder: Path) -> tuple[Record, ...]:
    """Return every Codex session under `folder`, read once a run."""
    return tuple(_session(path) for path in sorted(folder.glob("**/*.jsonl")))


def _git_lines(repo: Path, *args: str) -> list[str]:
    """Return a git command's stdout lines in `repo`, none when it fails."""
    done = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    return done.stdout.splitlines() if done.returncode == 0 else []


def _codex_sessions(repo: Path) -> list[Record]:
    """Return the Codex checker workers of `repo`, each with its `tree`.

    A worker's repo URL is `origin`'s, or its parent ran in one of the repo's
    worktrees; `tree` is where its parent ran, else None; a guardian or fix worker
    is none. Why: 0077-run-metrics design D5.
    """
    home = os.environ.get("CODEX_HOME") or Path.home() / ".codex"
    everything = _all_sessions(Path(home) / "sessions")
    origin = _git_lines(repo, "remote", "get-url", "origin")
    trees = {
        str(Path(line.removeprefix("worktree ")).resolve())
        for line in _git_lines(repo, "worktree", "list", "--porcelain")
        if line.startswith("worktree ")
    }
    cwds = {session["id"]: session["cwd"] for session in everything}

    def tree(session: Record) -> Path | None:
        parent = cwds.get(session["parent"])
        return Path(parent).resolve() if isinstance(parent, str) else None

    def ours(session: Record) -> bool:
        if origin and session["url"] == origin[0]:
            return True
        return str(tree(session)) in trees

    return [
        s | {"tree": tree(s)}
        for s in everything
        if s["role"] and s["start"] and ours(s)
    ]


def _filled(
    record: Record, sessions: list[Record], change: str, primary: Path | None
) -> Record:
    """Return a round's record, its gap filled from its change's Codex workers.

    A worker is the change's when its parent ran in the change's worktree, or in
    `primary`, None when another change's round overlaps; never for a round run on
    `claude`. Why: 0077-run-metrics design D5.
    """
    window = record["window"]
    if (
        record["tokens"] is not None
        or record["executor"] == "claude"
        or not window
        or record["role"] not in (*ROLES, *OLD_ROLES)
    ):
        return record
    found = [
        s
        for s in sessions
        if s["role"] == record["role"]
        and window[0] <= s["start"] <= window[1]
        and s["tree"] is not None
        and (s["tree"].name == change or s["tree"] == primary)
    ]
    if not found:
        return record
    return record | {
        "executor": "codex",
        "model": found[0]["model"],
        "effort": found[0]["effort"],
        "tokens": _held(s["tokens"] for s in found),
        "sessions": len(found),
        "source": "codex-session",
    }


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
    verdicts = [detail for event, detail in events if event == "verdicts"]
    tokens = (figure for detail in verdicts for _, figure in _role_tokens(detail))
    cards = details("done", r"\b(\d+) cards? to (?:backlog|debt)")
    return {
        "engine": engines[0] if engines else None,
        "duration": _held(_run_seconds(run) for run in runs),
        "tokens": _held(tokens),
        "capped": int(bool(details("halt", r"\b(cap)\b"))),
        "to_backlog": _held(map(int, cards)),
    }


def _results(path: Path) -> list[dict[str, Any]]:
    """Return a worker log's `result` events, or a Codex log's spawn line and turns.

    A line that is not JSON is none, and a log with neither result nor turn none.
    Why: 0096-codex-ready design D6.
    """
    events = []
    with path.open(encoding="utf-8", errors="replace") as lines:
        for n, line in enumerate(lines):
            if not any(f'"{kind}"' in line for kind in (*SPENT, "mf.spawn")):
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            kind = event.get("type") if isinstance(event, dict) else None
            if kind in SPENT or (n == 0 and kind == "mf.spawn"):
                events.append(event)
    return events if any(event["type"] in SPENT for event in events) else []


def _number(value: object) -> Number | None:
    """Return `value` when it is a number, else None; a bool is none."""
    return (
        value
        if isinstance(value, int | float) and not isinstance(value, bool)
        else None
    )


def _codex_spent(events: list[dict[str, Any]]) -> Record:
    """Return a Codex log's priced cost and tokens; its turns and seconds are gaps.

    The cost is a gap with no spawn line or no price for its model.
    Why: 0096-codex-ready design D6.
    """
    usages = [
        usage
        for event in events
        if event.get("type") == "turn.completed"
        and isinstance(usage := event.get("usage"), dict)
    ]

    def total(key: str) -> Number:
        return sum(_number(usage.get(key)) or 0 for usage in usages)

    spawn = events[0] if events[0].get("type") == "mf.spawn" else {}
    models = tomllib.loads(PRICES.read_text(encoding="utf-8"))["models"]
    row = models.get(spawn.get("model") or "default") if spawn else None
    cost = None
    if isinstance(row, dict):
        cached = total("cached_input_tokens")
        fresh = total("input_tokens") - cached
        paid = fresh * row["input"] + cached * row["cached_input"]
        cost = (paid + total("output_tokens") * row["output"]) / 1_000_000
    tokens = total("input_tokens") + total("output_tokens")
    return {"cost": cost, "turns": None, "tokens": tokens, "seconds": None}


def _spent(events: list[dict[str, Any]]) -> Record:
    """Return one log's cost, turns, tokens and seconds, each a gap with no event.

    Why: `total_cost_usd` and `modelUsage` are cumulative, the rest per segment.
    """
    if not events:
        return dict.fromkeys(("cost", "turns", "tokens", "seconds"))
    if not any(event.get("type") == "result" for event in events):
        return _codex_spent(events)
    usage = events[-1].get("modelUsage")
    models = usage.values() if isinstance(usage, dict) else ()
    tokens = [
        _number(model.get(key))
        for model in models
        if isinstance(model, dict)
        for key in TOKENS
    ]
    ms = _held(_number(event.get("duration_ms")) for event in events)
    return {
        "cost": _number(events[-1].get("total_cost_usd")),
        "turns": _held(_number(event.get("num_turns")) for event in events),
        "tokens": _held(tokens),
        "seconds": None if ms is None else round(ms / 1000),
    }


def _station_logs(repo: Path, change: str, station: str) -> list[Path]:
    """Return each spawn's log of a station: `<stamp>-<station>.log`, then `-<n>.log`.

    A change no run has moved keeps them as `runs/<stamp>/<change>_<station>.log`.
    Why: 0077-run-metrics design D2; 0080-minions-layout design D3, D5.
    """
    if _moved(repo, change):
        folder = _change_dir(repo, change) / "logs"
        found = (folder.glob(f"*-{station}{n}.log") for n in ("", "-[0-9]*"))
    else:
        stamps = sorted(path for path in (repo / RUNS).glob("*") if path.is_dir())
        names = (f"{change}_{station}.log", f"{change}_{station}-[0-9]*.log")
        found = (stamp.glob(name) for stamp in stamps for name in names)
    return [path for paths in found for path in sorted(paths) if path.is_file()]


def _cost_logs(repo: Path, change: str) -> Record:
    """Return a change's cost, turns, tokens and seconds per station, over every run.

    Each spawn's log counts; a field one read log lacks is the station's gap.
    Why: 0076-context-cost design D1; 0096-codex-ready design D6.
    """
    runs = repo / RUNS
    spawn = re.compile(
        rf"^\d\d:\d\d:\d\d · {re.escape(change)} · spawn — ({'|'.join(STATIONS)})"
        r"(?: ·|$)",
        re.MULTILINE,
    )
    spawns = Counter(
        found
        for log in runs.glob("*.md")
        for found in spawn.findall(log.read_text(encoding="utf-8", errors="replace"))
    )
    record: Record = {}
    for station in STATIONS:
        logs = _station_logs(repo, change, station)
        found = [_results(path) for path in logs]
        spent = [_spent(events) for events in found if events]
        for key in ("cost", "turns", "tokens", "seconds"):
            record[f"{key}_{station}"] = _total(row[key] for row in spent)
        record[f"logs_{station}"] = len(logs)
        record[f"read_{station}"] = sum(map(bool, found))
        record[f"spawns_{station}"] = spawns[station]
    return record


def _integer(text: str | None) -> int | None:
    """Return `text` as an int, or None; e.g. "3" → 3, "n/a" → None."""
    return int(text) if text and text.isdecimal() else None


def _workers(front: dict[str, str]) -> int | None:
    """Return a file's workers; a by-rule catch-up's `0` is a gap.

    Why: by rule overwrites the judged round's count and keeps its `model:`.
    """
    if front.get("mode") == "by-rule":
        return None
    return _integer(front.get("workers"))


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
    """Return `key` from the first frontmatter holding it, conformance's first."""
    return next((front[key] for front in fronts if front.get(key)), None)


def _total(values: Iterable[Number | None]) -> Number | None:
    """Return the sum; a gap in any file, or no file, is a gap."""
    held = list(values)
    return None if None in held else _held(held)


def _held(values: Iterable[Number | None]) -> Number | None:
    """Return the sum of the values held, a gap when none is.

    Why: a clean file has no card or log, and adds nothing to its sibling's counts.
    """
    known = [value for value in values if value is not None]
    return sum(known) if known else None


def _merged(rows: Iterable[Record], key: str) -> Counter[str]:
    """Return the rows' `key` counters, added up."""
    return sum((row[key] for row in rows), Counter())


def _change_dir(repo: Path, change: str) -> Path:
    """Return the change's folder in the repo's run directory.

    e.g. "0001-todo" → <repo>/.minions/changes/0001-todo
    Why: 0080-minions-layout design D1, D2.
    """
    return repo / CHANGES / change


def _moved(repo: Path, change: str) -> bool:
    """Return whether the change's folder holds its files: it wins over the old ones.

    Why: 0080-minions-layout design D5.
    """
    return any((_change_dir(repo, change) / name).is_file() for name in FILES)


def _file(repo: Path, change: str, name: str) -> Path:
    """Return a change's file by its name in the change's folder, or its old path.

    e.g. "review.md" → `changes/0001-x/review.md`, or `findings/0001-x_review.md`
    """
    if _moved(repo, change):
        return _change_dir(repo, change) / name
    return repo / FINDINGS / f"{change}_{name}"


def _checker(repo: Path, change: str, role: str, old: str) -> Path:
    """Return a checker's findings file, by its name when it stands, else its old one.

    e.g. ("0001-x", "conformance", "review") → `changes/0001-x/review.md` with no
    `conformance.md`
    """
    named = _file(repo, change, f"{role}.md")
    return named if named.is_file() else _file(repo, change, f"{old}.md")


def _changes(repo: Path) -> set[str]:
    """Return the changes with a file in their folder or, unmoved, in `findings/`."""
    folders = (repo / CHANGES).iterdir() if (repo / CHANGES).is_dir() else ()
    moved = {path.name for path in folders if _moved(repo, path.name)}
    names = (path.name for path in (repo / FINDINGS).glob("*.md"))
    return moved | {found[1] for name in names if (found := OLD_FILES.fullmatch(name))}


def read_change(repo: Path, change: str) -> Record:
    """Return a change's record, each field parsed on its own, None when unreadable.

    A checker's file is read by its name, else by its old one.
    Why: 0095-converge-roles design D4.
    """
    files = [
        found
        for role, old, blocking in (
            ("conformance", "review", ("blocking",)),
            ("adversarial", "security", ("critical", "high")),
        )
        if (found := _findings_file(_checker(repo, change, role, old), blocking))
    ]
    fronts = [found["front"] for found in files]
    included, skipped = _packet(_first(fronts, "packet"))
    record: Record = {
        "repo": repo.name,
        "change": change,
        "reviewed": _first(fronts, "reviewed"),
        "model": _first(fronts, "model"),
        "mode": _first(fronts, "mode"),
        "workers": _total(_workers(front) for front in fronts),
        "packet_included": included,
        "packet_skipped": skipped,
        "rounds": _integer(_first(fronts, "round")),
        "severity": _merged(files, "severity"),
        "categories": _merged(files, "categories"),
        **_status_log(_file(repo, change, "status_log.md")),
        **_cost_logs(repo, change),
    }
    for key in ("findings", "blocking", "inconclusive"):
        record[key] = _total(found[key] for found in files)
    for key in (*VERDICT_FIELDS, *RESOLUTION_FIELDS):
        record[key] = _held(found[key] for found in files)
    return record


def read_repo(repo: Path) -> list[Record]:
    """Return the repo's records in `reviewed` order, those with no date last."""
    if not (repo / CHANGES).is_dir() and not (repo / FINDINGS).is_dir():
        raise CannotRun(f"{repo}: no {CHANGES} or {FINDINGS} directory")
    records = [read_change(repo, change) for change in _changes(repo)]
    return sorted(
        records,
        key=lambda r: (r["reviewed"] is None, r["reviewed"] or "", r["change"]),
    )


def round_data(repo: Path) -> list[Record]:
    """Return a record per run, round and role of the repo's status logs.

    A round's gap is filled from its change's Codex workers in its window.
    """
    sessions = _codex_sessions(repo)
    logs = {
        change: _round_records(path)
        for change in sorted(_changes(repo))
        if (path := _file(repo, change, "status_log.md")).is_file()
    }
    windows = {
        change: [r["window"] for r in records if r["window"]]
        for change, records in logs.items()
    }
    rows = []
    for change, records in logs.items():
        others = [w for name, held in windows.items() if name != change for w in held]
        for record in records:
            window = record["window"]
            alone = window and not any(
                start <= window[1] and window[0] <= end for start, end in others
            )
            filled = _filled(
                record, sessions, change, repo.resolve() if alone else None
            )
            del filled["window"]
            rows.append({"repo": repo.name, "change": change, **filled})
    return rows


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
            "to debt",
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


def _cost_cell(record: Record, station: str) -> str:
    """Return a station's spend; e.g. "$1.50 · 15 turns · 376 tokens · 91 s · 2 of 3".

    `<read> of <spawns>` ends it when the run logs name more spawns than logs read,
    a log with neither result nor `turn.completed` event unread.
    """
    cost, turns, tokens, seconds = (
        record[f"{key}_{station}"] for key in ("cost", "turns", "tokens", "seconds")
    )
    parts = [
        f"${cost:.2f}" if cost is not None else GAP,
        *(
            f"{_figure(value)} {unit}"
            for value, unit in ((turns, "turns"), (tokens, "tokens"), (seconds, "s"))
            if value is not None
        ),
    ]
    read, spawns = record[f"read_{station}"], record[f"spawns_{station}"]
    if spawns > read:
        parts.append(f"{read} of {spawns}")
    return " · ".join(parts)


def cost_table(records: list[Record]) -> Table:
    """Return a row per change, a column per station, `—` where no log tells."""
    return (
        ["change", *STATIONS],
        [
            [record["change"], *(_cost_cell(record, s) for s in STATIONS)]
            for record in records
        ],
    )


def model_table(records: list[Record]) -> Table:
    """Return a row per model and engine, `unknown` for a gap."""
    groups: dict[tuple[str, ...], list[Record]] = {}
    for record in records:
        key = tuple(record[f] or "unknown" for f in ("model", "engine"))
        groups.setdefault(key, []).append(record)
    summed = (*VERDICT_FIELDS, "inconclusive", "packet_included", "packet_skipped")
    headers = [
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
    """Return each gap field and its count; e.g. "model 2 · tokens 3", else "none"."""
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
        "<h3>cost</h3>",
        _html_table(cost_table(records)),
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
    lines += ["<h2>model</h2>", _html_table(model_table(records))]
    lines += ["<h2>lacked</h2>", "<ul>"]
    lines += [f"<li>{_E(name)}: {_E(lacked(held))}</li>" for name, held in read]
    lines += ["</ul>", "</body></html>"]
    return "\n".join(lines) + "\n"


def _printable(text: str) -> str:
    """Return `text` when shaped like a model or engine name, else `unknown`."""
    return text if _PRINTABLE.fullmatch(text) else "unknown"


def summary(out: Path, read: list[tuple[str, list[Record]]]) -> str:
    """Return what a written run prints, per 0045-review-metrics design D2."""
    records = _every_record(read)
    headers, rows = model_table(records)
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
    """Write the page or its data, its folder too."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise CannotRun(f"{path}: cannot write: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    """Draw the page and its data of the repos the config or the flags name.

    Return the exit code.
    """
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
        data = {
            "generated": datetime.now().astimezone().isoformat(timespec="seconds"),
            "records": [row for repo in repos for row in round_data(repo)],
        }
        _write(out.with_name(DATA), json.dumps(data, indent=2) + "\n")
    except CannotRun as exc:
        print(exc, file=sys.stderr)
        return 2
    print(summary(out, read))
    return 0


if __name__ == "__main__":
    sys.exit(main())
