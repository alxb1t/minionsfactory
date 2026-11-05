# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Print one metric of a version's run, read from the primary's `.minions/` and git.

    run.py <id>

`MF_METRICS_CHANGE`, `_BASE` and `_HEAD` name the version. A metric the run left no
data for exits 1, naming what it lacked: a gap, never a zero.
Why: 0077-run-metrics design D3.
"""

import os
import re
import subprocess
import sys
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import cached_property
from pathlib import Path

STAMP = re.compile(r"(\d{8})-(\d{6})(?:-(\d+))?")
EVENT = re.compile(r"^(\d\d):(\d\d):(\d\d) · (\S+) · ([\w-]+) — (.*)$", re.MULTILINE)
STATIONS = ("build", "converge", "integrate", "release", "rescue")
HALT = re.compile(r"(\w+) (?:check fail|worker exit|timed out)\b")
# why: a clock set back an hour is no midnight
MIDNIGHT = timedelta(hours=12)

Number = int | float


class Gap(Exception):
    """The run left no data for the metric; the message names what it lacked."""


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


class Version:
    """A version's run: its run logs, status log and commits."""

    def __init__(self, root: Path, change: str, base: str, head: str) -> None:
        """Find the primary's `.minions/` from `root`, the same from every worktree."""
        self.root, self.change, self.base, self.head = root, change, base, head
        common = _git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
        self.minions = Path(common).parent / ".minions"

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
        """Return the version's station spawns, each closed by its finish line."""
        spawns: list[Spawn] = []
        counts: Counter[tuple[str, str]] = Counter()
        for event in self.events:
            station = event.detail.split(" · ", 1)[0]
            if event.who != self.change or station not in STATIONS:
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
        """Return the rescues that ended `fixed` or `diagnosed`."""
        return sum(
            e.name == "rescue" and e.detail.startswith(f"{self.change}: {kind}")
            for e in self.events
        )

    @cached_property
    def status_runs(self) -> list[tuple[str, str]]:
        """Return the status log's runs as heading and body, newest first."""
        path = self.minions / "findings" / f"{self.change}_status_log.md"
        if not path.is_file():
            raise Gap(f"no {path.name}")
        parts = re.split(
            r"^(## Run\b.*)$", path.read_text(encoding="utf-8"), flags=re.MULTILINE
        )
        return list(zip(parts[1::2], parts[2::2], strict=True))

    def rounds(self) -> int:
        """Return the highest round a run that is no catch-up reached."""
        found = [
            int(n)
            for heading, body in self.status_runs
            if not heading.rstrip().endswith("· catch-up")
            for n in re.findall(r"· round (\d+) ·", body)
        ]
        if not found:
            raise Gap("no round in the status log")
        return max(found)

    def blockers(self) -> int:
        """Return round 1's open blocking findings, in the oldest run's verdicts."""
        body = self.status_runs[-1][1] if self.status_runs else ""
        lines = re.findall(r"^.* · round 1 · verdicts — .*$", body, re.MULTILINE)
        counts = [
            int(n) for line in lines for n in re.findall(r"open_blocking:? (\d+)", line)
        ]
        if not counts:
            raise Gap("no round 1 verdicts with open_blocking")
        return sum(counts)

    def grants(self) -> int:
        """Return the converge runs marked as a grant's."""
        return sum(h.rstrip().endswith("· grant") for h, _ in self.status_runs)

    def commits(self, fixes: bool) -> int:
        """Return the commits up to the build's `.done` head, or after it, if `fixes`.

        Counted along the first parent, merges left out.
        """
        done = self.minions / "build" / f"{self.change}.done"
        found = done.is_file() and re.search(
            r"^head: ([0-9a-f]{7,40})\s*$", done.read_text(), re.MULTILINE
        )
        if not found:
            raise Gap(f"no head in {done.name}")
        built = found[1]
        ancestor = ["git", "merge-base", "--is-ancestor", built, self.head]
        if subprocess.run(ancestor, cwd=self.root, capture_output=True).returncode:
            raise Gap(f"{done.name}'s head is not in the version's history")
        span = f"{built}..{self.head}" if fixes else f"{self.base}..{built}"
        count = ("rev-list", "--first-parent", "--no-merges", "--count", span)
        return int(_git(self.root, *count))


METRICS: dict[str, Callable[[Version], Number]] = {
    "lead-minutes": Version.lead,
    **{
        f"{stage}-minutes": lambda v, s=stage: v.minutes(s)
        for stage in ("build", "converge", "catch-up", "integrate")
    },
    "wait-minutes": Version.waits,
    "converge-rounds": Version.rounds,
    "blockers-round-1": Version.blockers,
    "grants": Version.grants,
    **{
        f"halts-{station}": lambda v, s=station: v.halts(s)
        for station in ("build", "converge", "integrate", "release")
    },
    "rescues-fixed": lambda v: v.rescues("fixed"),
    "rescues-diagnosed": lambda v: v.rescues("diagnosed"),
    "build-commits": lambda v: v.commits(fixes=False),
    "fix-commits": lambda v: v.commits(fixes=True),
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
