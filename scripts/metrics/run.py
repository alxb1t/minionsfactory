# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Print one metric of a version's run, read from the primary's `.minions/` and git.

    run.py <id>

`MF_METRICS_CHANGE`, `_BASE` and `_HEAD` name the version. A metric the run left no
data for exits 1, naming what it lacked: a gap, never a zero.
Why: 0077-run-metrics design D3, D4.
"""

import json
import os
import re
import subprocess
import sys
import tomllib
from collections import Counter
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import cached_property
from pathlib import Path
from typing import Any

STAMP = re.compile(r"(\d{8})-(\d{6})(?:-(\d+))?")
EVENT = re.compile(r"^(\d\d):(\d\d):(\d\d) · (\S+) · ([\w-]+) — (.*)$", re.MULTILINE)
STATIONS = ("build", "converge", "integrate", "release", "rescue", "supervise")
# The checkers converge's mailbox starts: no stage of their own, so no minutes.
# Why: 0097-cross-model design D11.
CHECKERS = (
    "converge-conformance",
    "converge-adversarial",
    "converge-shadow-conformance",
    "converge-shadow-adversarial",
)
HALT = re.compile(r"(\w+) (?:check fail|worker exit|timed out)\b")
# why: a clock set back an hour is no midnight
MIDNIGHT = timedelta(hours=12)
STAGES = ("build", "converge", "catch-up", "integrate")
# The stages a version's cost sums; the release's own log is still being written.
SPENT = (*STAGES, "rescue", "supervise")
ROLES = ("conformance", "adversarial")
MODEL_USAGE = (
    "inputTokens",
    "outputTokens",
    "cacheReadInputTokens",
    "cacheCreationInputTokens",
)
USAGE = (
    "input_tokens",
    "output_tokens",
    "cache_read_input_tokens",
    "cache_creation_input_tokens",
)
# A Codex `turn.completed`'s tokens: its cached input is a part of its input.
CODEX_USAGE = ("input_tokens", "output_tokens")
ROLE = re.compile(r"\b(conformance|adversarial)\b", re.IGNORECASE)
PRIORITY = re.compile(r"^[ \t]*- \*\*Priority:\*\*", re.MULTILINE)
CONFIRMED = re.compile(r"^[ \t]*- \*\*Verdict:\*\*[ \t]*`?confirmed", re.MULTILINE)
REPEAT = re.compile(r"repeat of `?(\d+)·(\w+)")
# `conduct.py`'s: each old-layout path of a change, and a worker log's station part.
OLD_LAYOUT = (
    *("findings/{}_review.md", "findings/{}_security.md", "findings/{}_status_log.md"),
    *("findings/{}_diff.patch", "models/{}.toml", "integrate/{}.md"),
    *("integrate/{}.red", "integrate/{}.resolved", "build/{}.done", "build/{}.halt"),
    *("build/{}.closing", "build/{}.discarded.patch", "rescue/{}.md"),
    *("release/{}.held", "gate-check/{}"),
)
OLD_LOG = re.compile(r"[a-z][a-z-]*?(-\d+)?\.log")
# A Codex log's prices, read when one is priced. Why: 0096-codex-ready design D6.
PRICES = Path(__file__).resolve().parents[2] / "skills/mf-review-metrics/prices.toml"

Number = int | float


class Gap(Exception):
    """The run left no data for the metric; the message names what it lacked."""


class OldLayout(Exception):
    """The version's files sit at their old paths; the message names the first."""


@dataclass(frozen=True)
class Event:
    """One run log line, dated by its stamp."""

    stamp: str
    at: datetime
    who: str
    name: str
    detail: str


@dataclass
class Spawn:
    """One station spawn: the n-th of its station in its stamp, and its finish."""

    stamp: str
    station: str
    n: int
    start: datetime
    end: datetime | None = None


def _git(root: Path, *args: str) -> str:
    """Return a git command's stripped stdout; a failure raises."""
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    ).stdout.strip()


def _change_dir(primary: Path, change: str) -> Path:
    """Return the change's folder in the run directory.

    e.g. "0001-todo" → <primary>/.minions/changes/0001-todo
    Why: 0080-minions-layout design D1, D2.
    """
    return primary / ".minions" / "changes" / change


def _old_layout(minions: Path, change: str) -> str | None:
    """Return the change's first file at its old path, worker logs included, or None.

    e.g. "0001-x" → ".minions/runs/20261101-230000/0001-x_build.log"
    Why: 0080-minions-layout design D4.
    """
    held = [minions / name.format(change) for name in OLD_LAYOUT]
    stamps = sorted(minions.glob("runs/*/"))
    held += [
        log
        for stamp in stamps
        if STAMP.fullmatch(stamp.name)
        for log in sorted(stamp.glob(f"{change}_*.log"))
        if OLD_LOG.fullmatch(log.name.removeprefix(f"{change}_"))
    ]
    found = next((path for path in held if os.path.lexists(path)), None)
    return f".minions/{found.relative_to(minions)}" if found else None


def _logs(runs: Path) -> list[tuple[Path, re.Match[str]]]:
    """Return the run logs and their stamps, oldest first.

    e.g. `20261105-174408.md`, then `20261105-174408-2.md`
    """
    logs = [(p, found) for p in runs.glob("*.md") if (found := STAMP.fullmatch(p.stem))]
    return sorted(logs, key=lambda log: (log[1][1], log[1][2], int(log[1][3] or 1)))


def _events(path: Path, stamp: re.Match[str]) -> list[Event]:
    """Return a run log's events, a day added at each midnight it crosses."""
    day = datetime.strptime(stamp[1], "%Y%m%d")
    events: list[Event] = []
    for line in EVENT.finditer(path.read_text(encoding="utf-8", errors="replace")):
        hour, minute, second, who, name, detail = line.groups()
        at = day.replace(hour=int(hour), minute=int(minute), second=int(second))
        if events and events[-1].at - at > MIDNIGHT:
            day, at = day + timedelta(days=1), at + timedelta(days=1)
        events.append(Event(path.stem, at, who, name, detail))
    return events


def _versions(detail: str) -> list[str]:
    """Return a `start` line's versions; e.g. "… · versions a b · mf v1" → [a, b]."""
    parts = (part.split() for part in detail.split(" · "))
    return next((words[1:] for words in parts if words[:1] == ["versions"]), [])


def _round(minutes: float) -> Number:
    """Return minutes to a tenth; e.g. 19.366 → 19.4."""
    return round(minutes, 1)


def _json(path: Path, marker: str) -> Iterator[dict[str, Any]]:
    """Yield a worker log's JSON objects on the lines holding `marker`."""
    with path.open(encoding="utf-8", errors="replace") as lines:
        for line in lines:
            if marker not in line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                yield event


def _summed(usage: object, keys: tuple[str, ...]) -> int:
    """Return the token counts `usage` holds under `keys`, a non-number none."""
    held = usage if isinstance(usage, dict) else {}
    values = (held.get(key) for key in keys)
    return sum(v for v in values if isinstance(v, int) and not isinstance(v, bool))


def _spawn_line(path: Path) -> dict[str, Any] | None:
    """Return a worker log's first line when it is an `mf.spawn` object, else None."""
    with path.open(encoding="utf-8", errors="replace") as lines:
        first = lines.readline()
    try:
        spawn = json.loads(first)
    except json.JSONDecodeError:
        return None
    return (
        spawn if isinstance(spawn, dict) and spawn.get("type") == "mf.spawn" else None
    )


def _priced(path: Path, name: str, turns: list[dict[str, Any]]) -> float | Gap:
    """Return a Codex log's turns priced at its spawn line's model, or the Gap why not.

    Why: 0096-codex-ready design D6.
    """
    spawn = _spawn_line(path)
    if spawn is None:
        return Gap(f"no spawn line in {name}")
    model = spawn.get("model")
    row = tomllib.loads(PRICES.read_text(encoding="utf-8"))["models"].get(model)
    if not model or not isinstance(row, dict):
        return Gap(f"no price for model {model or 'default'}")
    dollars = 0.0
    for turn in turns:
        usage = turn.get("usage")
        cached = _summed(usage, ("cached_input_tokens",))
        fresh = _summed(usage, ("input_tokens",)) - cached
        output = _summed(usage, ("output_tokens",))
        dollars += fresh * row["input"] + cached * row["cached_input"]
        dollars += output * row["output"]
    return dollars / 1_000_000


def _spent(path: Path, name: str) -> tuple[float | Gap, int]:
    """Return a worker log's dollars, or the Gap naming why none, and its tokens.

    A Claude log's are its last result event's totals: `total_cost_usd` and
    `modelUsage` are cumulative, per 0076-context-cost D1. A Codex log's are its
    `turn.completed` events', priced by `_priced`; one stopped before its first turn
    spent none. Why: 0104-codex-limits design D5.
    """
    events = list(_json(path, '"type"')) if path.is_file() else []
    results = [e for e in events if e.get("type") == "result"]
    turns = [e for e in events if e.get("type") == "turn.completed"]
    if not results and turns:
        tokens = sum(_summed(t.get("usage"), CODEX_USAGE) for t in turns)
        return _priced(path, name, turns), tokens
    if not results and path.is_file() and _spawn_line(path) is not None:
        return 0.0, 0
    last = results[-1] if results else {}
    cost, models = last.get("total_cost_usd"), last.get("modelUsage")
    if not isinstance(cost, int | float) or not isinstance(models, dict):
        raise Gap(f"no result event in {name}")
    return cost, sum(_summed(model, MODEL_USAGE) for model in models.values())


class Version:
    """A version's run: its run logs, status log and commits."""

    def __init__(self, root: Path, change: str, base: str, head: str) -> None:
        """Find the primary's `.minions/` from `root`, the same from every worktree."""
        self.root, self.change, self.base, self.head = root, change, base, head
        common = _git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
        self.minions = Path(common).parent / ".minions"
        self.folder = _change_dir(Path(common).parent, change)
        if old := _old_layout(self.minions, change):
            raise OldLayout(f"{old} is the old layout: /mf-ship moves it")

    def _names(self, event: Event) -> bool:
        """Return whether a run log line names the version."""
        if event.who == self.change:
            return True
        if event.who != "run":
            return False
        if event.name == "start":
            return self.change in _versions(event.detail)
        return event.detail.startswith(f"{self.change}: ")

    @cached_property
    def events(self) -> list[Event]:
        """Return the events naming the version, oldest first; none is a gap."""
        logs = _logs(self.minions / "runs")
        named = [e for log in logs for e in _events(*log) if self._names(e)]
        if not named:
            raise Gap(f"no run log names {self.change}")
        return named

    @cached_property
    def spawns(self) -> list[Spawn]:
        """Return the version's station and checker spawns, each closed by a finish."""
        spawns: list[Spawn] = []
        counts: Counter[tuple[str, str]] = Counter()
        for event in self.events:
            station = event.detail.split(" · ", 1)[0]
            if event.who != self.change or station not in (*STATIONS, *CHECKERS):
                continue
            if event.name == "spawn":
                counts[event.stamp, station] += 1
                n = counts[event.stamp, station]
                spawns.append(Spawn(event.stamp, station, n, event.at))
            elif event.name == "finish":
                running = (event.stamp, station, None)
                if found := [
                    s for s in spawns if (s.stamp, s.station, s.end) == running
                ]:
                    found[0].end = event.at
        return spawns

    def stage(self, stage: str) -> list[Spawn]:
        """Return a stage's spawns; a catch-up's, the converges after an integrate."""
        starts = [s.start for s in self.spawns if s.station == "integrate"]
        first = min(starts, default=None)
        if stage not in ("converge", "catch-up"):
            return [s for s in self.spawns if s.station == stage]
        late = stage == "catch-up"
        return [
            s
            for s in self.spawns
            if s.station == "converge"
            and (first is not None and s.start > first) == late
        ]

    def minutes(self, stage: str) -> Number:
        """Return the minutes from each of a stage's spawns to its finish, summed."""
        spawns = self.stage(stage)
        if any(s.end is None for s in spawns):
            raise Gap(f"a {stage} spawn with no finish")
        seconds = sum((s.end - s.start).total_seconds() for s in spawns if s.end)
        return _round(seconds / 60)

    def lead(self) -> Number:
        """Return the minutes from the cut commit to the release's spawn."""
        releases = self.stage("release")
        if not releases:
            raise Gap("no release spawn")
        subject = f"docs({self.change}): land the change directory"
        log = _git(
            self.root, "log", "--format=%ct %s", "--fixed-strings", "--grep", subject
        )
        times = [
            int(t)
            for t, _, s in (x.partition(" ") for x in log.splitlines())
            if s == subject
        ]
        if not times:
            raise Gap(f"no commit `{subject}`")
        cut = datetime.fromtimestamp(times[-1])
        return _round((releases[-1].start - cut).total_seconds() / 60)

    def waits(self) -> Number:
        """Return the minutes from each halt to the rejoin, grant or start answering it.

        A spawn of the version or an automatic grant ends a wait uncounted: the run's
        own work, no person's.
        """
        total, since = 0.0, None
        for event in self.events:
            mine = event.who == self.change
            detail = event.detail.removeprefix(f"{self.change}: ")
            if mine and event.name == "halt":
                since = since or event.at
            elif (mine and event.name == "spawn") or detail.startswith("automatic"):
                since = None
            elif since and (
                event.name in ("start", "grant")
                or (event.name == "rejoin" and not detail.startswith("still "))
            ):
                total += (event.at - since).total_seconds()
                since = None
        return _round(total / 60)

    def after_waits(self) -> Number:
        """Return the minutes from each `wait` event of the version to its next event.

        The spans are summed: none is 0, and a wait with no later event in its run
        counts nothing. Why: 0099-stacked-builds design D7.
        """
        events = self.events
        total = sum(
            (later.at - event.at).total_seconds()
            for event, later in zip(events, events[1:], strict=False)
            if event.who == self.change
            and event.name == "wait"
            and later.stamp == event.stamp
        )
        return _round(total / 60)

    def halts(self, station: str) -> int:
        """Return the version's halts on a station's check, exit or timeout."""
        return sum(
            e.who == self.change
            and e.name == "halt"
            and (found := HALT.match(e.detail)) is not None
            and found[1] == station
            for e in self.events
        )

    def rescues(self, kind: str) -> int:
        """Return the rescues that ended `kind`: `fixed`, `decided` or `diagnosed`."""
        return sum(
            e.name == "rescue" and e.detail.startswith(f"{self.change}: {kind}")
            for e in self.events
        )

    def supervised(self) -> int:
        """Return the supervisor amends the run took, each `decided` for the person.

        Why: 0089-supervisor design D10.
        """
        return sum(
            e.name == "supervise" and e.detail.startswith(f"{self.change}: decided")
            for e in self.events
        )

    @cached_property
    def status_runs(self) -> list[tuple[str, str]]:
        """Return the status log's runs as heading and body, newest first."""
        path = self.folder / "status_log.md"
        if not path.is_file():
            raise Gap(f"no {self.change}/{path.name}")
        parts = re.split(
            r"^(## Run\b.*)$", path.read_text(encoding="utf-8"), flags=re.MULTILINE
        )
        return list(zip(parts[1::2], parts[2::2], strict=True))

    def rounds(self) -> int:
        """Return the highest round a run that is no catch-up or amend run reached."""
        found = [
            int(n)
            for heading, body in self.status_runs
            if not heading.rstrip().endswith(("· catch-up", "· amend"))
            for n in re.findall(r"· round (\d+) ·", body)
        ]
        if not found:
            raise Gap("no round in the status log")
        return max(found)

    def blockers(self) -> int:
        """Return round 1's open blocking findings, in the oldest run with its verdicts.

        A run that halted before its fan-out left none, so the next run holds them.
        """
        verdicts = r"^.* · round 1 · verdicts — .*$"
        lines: list[str] = []
        for _, body in reversed(self.status_runs):
            if lines := re.findall(verdicts, body, re.MULTILINE):
                break
        counts = [
            int(n) for line in lines for n in re.findall(r"open_blocking:? (\d+)", line)
        ]
        if not counts:
            raise Gap("no round 1 verdicts with open_blocking")
        return sum(counts)

    def grants(self) -> int:
        """Return the converge runs marked as a grant's."""
        return sum(h.rstrip().endswith("· grant") for h, _ in self.status_runs)

    def amends(self) -> int:
        """Return the converge runs marked as an answered halt's amend round."""
        return sum(h.rstrip().endswith("· amend") for h, _ in self.status_runs)

    def commits(self, fixes: bool) -> int:
        """Return the commits up to `build.done`'s head, or after it, if `fixes`.

        Counted along the first parent, merges left out.
        """
        done = self.folder / "build.done"
        name = f"{self.change}/{done.name}"
        found = done.is_file() and re.search(
            r"^head: ([0-9a-f]{7,40})\s*$", done.read_text(), re.MULTILINE
        )
        if not found:
            raise Gap(f"no head in {name}")
        built = found[1]
        ancestor = ["git", "merge-base", "--is-ancestor", built, self.head]
        if subprocess.run(ancestor, cwd=self.root, capture_output=True).returncode:
            raise Gap(f"{name}'s head is not in the version's history")
        span = f"{built}..{self.head}" if fixes else f"{self.base}..{built}"
        count = ("rev-list", "--first-parent", "--no-merges", "--count", span)
        return int(_git(self.root, *count))

    def log(self, spawn: Spawn) -> tuple[Path, str]:
        """Return a spawn's worker log and its name in the change's `logs/`.

        e.g. a stamp's second converge → `<change>/logs/<stamp>-converge-2.log`.
        Why: D2; 0080-minions-layout design D3.
        """
        n = f"-{spawn.n}" if spawn.n > 1 else ""
        log = f"{spawn.stamp}-{spawn.station}{n}.log"
        return self.folder / "logs" / log, f"{self.change}/logs/{log}"

    def checkers(self, stage: str) -> list[Spawn]:
        """Return the checker spawns that started while one of a stage's spawns ran.

        Why: 0097-cross-model design D11.
        """
        held = self.stage(stage)
        return [
            spawn
            for spawn in self.spawns
            if spawn.station in CHECKERS
            and any(
                run.start <= spawn.start and (run.end is None or spawn.start <= run.end)
                for run in held
            )
        ]

    def spent(self, stages: tuple[str, ...], dollars: bool = True) -> tuple[float, int]:
        """Return the stages' dollars and tokens, each spawn's log read; none is 0.

        A checker the mailbox started counts in the stage that held it. A log priced
        to no dollars is a gap only when `dollars` are asked for.
        """
        logs = [
            self.log(spawn)
            for stage in stages
            for spawn in (*self.stage(stage), *self.checkers(stage))
        ]
        spent = [_spent(*log) for log in logs]
        costs = [cost for cost, _ in spent]
        if dollars and (gaps := [cost for cost in costs if isinstance(cost, Gap)]):
            raise gaps[0]
        paid = sum(cost for cost in costs if not isinstance(cost, Gap))
        return paid, sum(tokens for _, tokens in spent)

    def quota(self, window: str) -> float:
        """Return a window's share the version's Codex spawns used, from their logs.

        Each spawn of `SPENT`'s stages and its checkers whose first line is an
        `mf.spawn` has its `mf.quota` line's `window` summed to a tenth; a log with no
        such line is passed over, and none holding one is a gap.
        Why: 0104-codex-limits design D5.
        """
        logs = [
            self.log(spawn)[0]
            for stage in SPENT
            for spawn in (*self.stage(stage), *self.checkers(stage))
        ]
        shares: list[float] = []
        for path in logs:
            if not path.is_file() or _spawn_line(path) is None:
                continue
            held = [e for e in _json(path, '"mf.quota"') if e.get("type") == "mf.quota"]
            share = held[-1].get(window) if held else None
            if isinstance(share, int | float) and not isinstance(share, bool):
                shares.append(share)
        if not shares:
            raise Gap("no mf.quota line in a Codex log")
        return round(sum(shares), 1)

    def lines(self) -> int:
        """Return the lines the change adds and removes, `metrics/` left out."""
        excluded = (".", ":(exclude)metrics")
        numstat = _git(
            self.root, "diff", "--numstat", self.base, self.head, "--", *excluded
        )
        rows = [line.split("\t") for line in numstat.splitlines()]
        return sum(int(row[0]) + int(row[1]) for row in rows if row[0] != "-")

    def per_line(self) -> Number:
        """Return the dollars per changed line."""
        lines = self.lines()
        if not lines:
            raise Gap("no line changed")
        return round(self.spent(SPENT)[0] / lines, 4)

    def role_tokens(self, role: str) -> int:
        """Return a role's tokens: its subagents' over the converge logs, its checkers'.

        A subagent's `assistant` events carry its Task's `tool_use_id`, which the
        log's `task_started` event names; a `converge-<role>` log is read as any log.
        Why: 0077-run-metrics design D4; 0097-cross-model design D11.
        """
        total, seen = 0, set()
        checked = [s for s in self.spawns if s.station == f"converge-{role}"]
        for spawn in checked:
            path, name = self.log(spawn)
            if not path.is_file():
                raise Gap(f"no {name}")
            total += _spent(path, name)[1]
        for spawn in (s for s in self.spawns if s.station == "converge"):
            path, name = self.log(spawn)
            if not path.is_file():
                raise Gap(f"no {name}")
            tasks: dict[object, str] = {}
            for event in _json(path, "tool_use_id"):
                message = event.get("message")
                if event.get("subtype") == "task_started":
                    found = ROLE.search(str(event.get("description")))
                    tasks[event.get("tool_use_id")] = found[1].lower() if found else ""
                elif (
                    event.get("type") == "assistant"
                    and tasks.get(event.get("parent_tool_use_id")) == role
                    and isinstance(message, dict)
                    and message.get("id") not in seen
                ):
                    seen.add(message.get("id"))
                    total += _summed(message.get("usage"), USAGE)
        if not seen and not checked:
            raise Gap(f"no {role} subagent event in a converge log")
        return total

    def cards(self, role: str) -> tuple[list[str], str]:
        """Return a role's findings cards and its `## Refuted` section."""
        path = self.folder / f"{role}.md"
        if not path.is_file():
            raise Gap(f"no {self.change}/{path.name}")
        text = path.read_text(encoding="utf-8", errors="replace")
        refuted = re.search(r"^## Refuted.*?\n(.*?)(?=^## |\Z)", text, re.M | re.S)
        if not refuted:
            raise Gap(f"no ## Refuted in {self.change}/{path.name}")
        pieces = re.split(r"^(?=- \*\*|#)", text, flags=re.MULTILINE)
        return [p for p in pieces if PRIORITY.search(p)], refuted[1]

    def confirmed(self, role: str) -> int:
        """Return a role's cards whose verdict is `confirmed`."""
        return sum(bool(CONFIRMED.search(card)) for card in self.cards(role)[0])

    def refuted(self, role: str) -> int:
        """Return the entries of a role's `## Refuted` section."""
        return len(re.findall(r"^- ", self.cards(role)[1], re.MULTILINE))

    def per_confirmed(self, role: str) -> int:
        """Return a role's tokens per confirmed card."""
        confirmed = self.confirmed(role)
        if not confirmed:
            raise Gap(f"no confirmed {role} card")
        return round(self.role_tokens(role) / confirmed)

    def paid(self) -> list[str]:
        """Return the card ids the proposal's `debt:` or `backlog:` lists."""
        folder = Path("openspec/changes")
        found = [
            path
            for path in (folder / self.change, folder / "archive" / self.change)
            if (self.root / path / "proposal.md").is_file()
        ]
        if not found:
            raise Gap(f"no proposal.md for {self.change}")
        text = (self.root / found[0] / "proposal.md").read_text(encoding="utf-8")
        listed = re.search(r"^(?:debt|backlog):[ \t]*\[(.*)\]", text, re.MULTILINE)
        return [card.strip() for card in listed[1].split(",")] if listed else []

    def escapes(self) -> int:
        """Return the cards repeating an earlier change's card it does not pay."""
        own = int(re.sub(r"\D.*", "", self.change) or 0)
        paid = self.paid()
        return sum(
            any(
                int(number) < own and f"{number}·{card}" not in paid
                for number, card in REPEAT.findall(text)
            )
            for role in ROLES
            for text in self.cards(role)[0]
        )

    def debt(self) -> int:
        """Return the cards under the version's heading in `.minions/debt.md`."""
        path = self.minions / "debt.md"
        if not path.is_file():
            raise Gap("no .minions/debt.md")
        text = path.read_text(encoding="utf-8")
        heading = rf"^## {re.escape(self.change)}[ \t]*\n(.*?)(?=^## |\Z)"
        section = re.search(heading, text, re.MULTILINE | re.DOTALL)
        return len(re.findall(r"^- \*\*", section[1], re.MULTILINE)) if section else 0


METRICS: dict[str, Callable[[Version], Number]] = {
    "lead-minutes": Version.lead,
    **{f"{stage}-minutes": lambda v, s=stage: v.minutes(s) for stage in STAGES},
    "wait-minutes": Version.waits,
    "after-wait-minutes": Version.after_waits,
    "converge-rounds": Version.rounds,
    "blockers-round-1": Version.blockers,
    "grants": Version.grants,
    "amend-rounds": Version.amends,
    **{
        f"halts-{station}": lambda v, s=station: v.halts(s)
        for station in ("build", "converge", "integrate", "release")
    },
    "rescues-fixed": lambda v: v.rescues("fixed"),
    "rescues-diagnosed": lambda v: v.rescues("diagnosed"),
    "rescues-decided": lambda v: v.rescues("decided"),
    "supervisor-decided": Version.supervised,
    "build-commits": lambda v: v.commits(fixes=False),
    "fix-commits": lambda v: v.commits(fixes=True),
    "cost-usd": lambda v: round(v.spent(SPENT)[0], 2),
    **{
        f"cost-usd-{stage}": lambda v, s=stage: round(v.spent((s,))[0], 2)
        for stage in STAGES
    },
    "tokens": lambda v: v.spent(SPENT, dollars=False)[1],
    **{
        f"tokens-{stage}": lambda v, s=stage: v.spent((s,), dollars=False)[1]
        for stage in STAGES
    },
    "codex-window-5h": lambda v: v.quota("five_hour"),
    "codex-window-week": lambda v: v.quota("weekly"),
    "cost-per-changed-line": Version.per_line,
    **{f"{role}-confirmed": lambda v, r=role: v.confirmed(r) for role in ROLES},
    **{f"{role}-refuted": lambda v, r=role: v.refuted(r) for role in ROLES},
    **{
        f"{role}-tokens-per-confirmed": lambda v, r=role: v.per_confirmed(r)
        for role in ROLES
    },
    "escapes": Version.escapes,
    "debt-added": Version.debt,
    "debt-paid": lambda v: len(v.paid()),
}


def measure(root: Path, argv: list[str], env: dict[str, str]) -> Number:
    """Return the metric `argv` names, of the version `env` names; a gap raises Gap."""
    if len(argv) != 1 or argv[0] not in METRICS:
        raise Gap(f"usage: run.py <id>, one of {', '.join(METRICS)}")
    change, base, head = (
        env.get(f"MF_METRICS_{k}") for k in ("CHANGE", "BASE", "HEAD")
    )
    if not (change and base and head):
        raise Gap("no MF_METRICS_CHANGE, _BASE and _HEAD")
    return METRICS[argv[0]](Version(root, change, base, head))


if __name__ == "__main__":
    try:
        print(measure(Path.cwd(), sys.argv[1:], dict(os.environ)))
    except Gap as gap:
        sys.exit(str(gap))
    except OldLayout as old:
        print(old, file=sys.stderr)
        sys.exit(2)
