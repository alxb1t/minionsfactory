# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Project each project's ship line into one state tree, read-only.

`viewer.py project <primary>` prints a project's tree as JSON.
Why: 0120-ui-state design D1, D3.
"""

import glob
import hashlib
import json
import os
import re
import runpy
import stat
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, NamedTuple, Protocol

SKILLS = Path(__file__).resolve().parents[2]
CONDUCT = SKILLS / "mf-ship/scripts/conduct.py"
CONVERGE = SKILLS / "mf-converge/scripts/converge.py"
PART = 262144
USAGE = "usage: viewer.py project <primary> [--only liveness|fingerprint]"
STAMP = "%Y%m%d-%H%M%S"
ACTIVE = 60
QUIET = 300
ROLES = ("conformance", "adversarial")
NEEDS_YOU = ("human", "integrating", "released")
SUFFIX = re.compile(r" · (?:hard|moderate)$")
SUBTASK = re.compile(r"^- \[([ x])\] (\d+)\.\d+ ", re.MULTILINE)
RUN_HEADING = re.compile(r"^## Run (\d+) — \S+ \S+(?: · (\S+))?$", re.MULTILINE)
VERDICT = re.compile(
    r"verdicts — (conformance|adversarial) \S+ · open_blocking \d+ · (.*)"
)
SPENT = re.compile(r"(executor|model|effort|tokens) (\S+)")
SPAWNED = re.compile(r"(model|effort|executor) (\S+)")
LIMIT = re.compile(r"limited until (\d{4}-\d\d-\d\d \d\d:\d\d)$")
TIMESTAMP = re.compile(r'"timestamp"\s*:\s*"([^"]+)"')


class Event(NamedTuple):
    """A run-log line: its version, event, detail, epoch seconds and text."""

    who: str
    name: str
    detail: str
    at: float
    line: str


class Version(Protocol):
    """An open version as `conduct.py` returns it: its change id and worktree."""

    change: str
    tree: Path


def load(path: Path) -> dict[str, Any]:
    """Return a script's definitions, run by path with no `__main__` guard met."""
    return runpy.run_path(str(path))


def read_part(path: Path, tail: bool = False) -> str | None:
    """Return a regular file's first or last `PART` bytes as text, else None.

    e.g. a pipe, a link or a missing file → None
    """
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        return None
    try:
        status = os.fstat(fd)
        if not stat.S_ISREG(status.st_mode):
            return None
        if tail and status.st_size > PART:
            os.lseek(fd, status.st_size - PART, os.SEEK_SET)
        return os.read(fd, PART).decode(errors="replace")
    finally:
        os.close(fd)


def _int(value: str | None) -> int | None:
    """Return a field as an integer, None when it is not one."""
    return int(value) if value and value.isascii() and value.isdigit() else None


def _stat(path: Path) -> tuple[str, int, int] | None:
    """Return a path's name, mtime and size, None when it cannot be read."""
    try:
        status = os.lstat(path)
    except OSError:
        return None
    return str(path), status.st_mtime_ns, status.st_size


def _newest(roots: list[Path]) -> float:
    """Return the newest mtime under `roots`, following no link, skipping `.git`."""
    newest = 0.0
    for root in roots:
        for folder, names, files in os.walk(root, followlinks=False):
            names[:] = [name for name in names if name != ".git"]
            for name in (*names, *files):
                status = _stat(Path(folder, name))
                newest = max(newest, status[1] / 1e9 if status else 0.0)
    return newest


def _count(tasks: str | None, number: str) -> tuple[int | None, int | None]:
    """Return the ticked and all sub-tasks of phase `number`, None for an unread file.

    e.g. phase "1" holding `- [x] 1.1` and `- [ ] 1.2` → (1, 2)
    """
    if tasks is None:
        return None, None
    marks = [mark for mark, phase in SUBTASK.findall(tasks) if phase == number]
    return marks.count("x"), len(marks)


class Reader:
    """Read one project: the scripts, the primary, the run log and the clock."""

    def __init__(
        self,
        conduct: dict[str, Any],
        converge: dict[str, Any],
        primary: Path,
        now: float,
    ) -> None:
        """Keep the loaded scripts and the primary `primary_of` names."""
        self.conduct = conduct
        self.converge = converge
        self.primary: Path = conduct["primary_of"](primary)
        self.runs = self.primary / ".minions"
        self.now = now
        self.log: Path | None = conduct["last_log"](self.runs / "runs")
        self.cache: dict[Path, list[Event]] = {}
        self.claimed: str | None = None

    def claim(self) -> str:
        """Return the claim once per project: `none`, `live`, `stale` or `unread`."""
        if self.claimed is None:
            try:
                self.claimed = self.conduct["_claim"](self.runs / "runs" / "active")
            except self.conduct["Stop"]:
                self.claimed = "unread"
        return self.claimed

    def events(self, log: Path) -> list[Event]:
        """Return a run log's events, each at the epoch second its line's time names."""
        if log not in self.cache:
            self.cache[log] = self._events(log)
        return self.cache[log]

    def _events(self, log: Path) -> list[Event]:
        """Read a log's events; a line earlier than the one before is a day on."""
        base = datetime.strptime(log.stem[:15], STAMP)
        days, before, found = 0, 0, []
        for line in (read_part(log, tail=True) or "").splitlines():
            if not (match := self.conduct["EVENT"].match(line)):
                continue
            hours, minutes, seconds = (int(part) for part in line[:8].split(":"))
            moment = hours * 3600 + minutes * 60 + seconds
            days += moment < before
            before = moment
            at = base.replace(hour=hours, minute=minutes, second=seconds)
            at += timedelta(days=days)
            found.append(
                Event(match[1], match[2], line[match.end() :], at.timestamp(), line)
            )
        return found

    def newest(self) -> list[Event]:
        """Return the newest run log's events, none without a log."""
        return self.events(self.log) if self.log else []

    def versions(self) -> list[Any]:
        """Return the open versions, a queued cut being none."""
        cuts = self.conduct["_cuts"](self.primary)
        found = self.conduct["open_versions"](self.primary)
        return [version for version in found if version.change not in cuts]

    def workers(self, change: str) -> list[dict[str, Any]]:
        """Return the version's spawns in the newest log that no finish pairs."""
        unfinished: list[Event] = []
        for event in self.newest():
            if event.who != change:
                continue
            station = event.detail.split(" · ")[0]
            if event.name == "spawn":
                unfinished.append(event)
            elif event.name == "finish":
                for spawn in unfinished:
                    if spawn.detail.split(" · ")[0] == station:
                        unfinished.remove(spawn)
                        break
        return [self._worker(event) for event in unfinished]

    def _worker(self, spawn: Event) -> dict[str, Any]:
        """Return a spawn as a worker: station, model, effort, executor, start."""
        parts = dict(SPAWNED.findall(spawn.detail))
        return {
            "station": spawn.detail.split(" · ")[0],
            "model": parts.get("model"),
            "effort": parts.get("effort"),
            "executor": parts.get("executor"),
            "started": spawn.at,
        }

    def liveness(
        self, version: Version, workers: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        """Return how lately a version with a worker moved, None without one."""
        if not workers or self.log is None:
            return None
        folder = self.runs / "changes" / version.change
        found = []
        for worker in workers:
            name = f"{self.log.stem}-{glob.escape(worker['station'])}*.log"
            found += (folder / "logs").glob(name)
        stats = [status for status in map(_stat, found) if status]
        times = [_newest([version.tree, folder])]
        if stats:
            newest = max(stats, key=lambda status: status[1])
            times += [newest[1] / 1e9, *self._stamped(Path(newest[0]))]
        last = max(times)
        age = self.now - last
        level = "active" if age < ACTIVE else "quiet" if age >= QUIET else "recent"
        return {"level": level, "last": last}

    def _stamped(self, log: Path) -> list[float]:
        """Return a worker log's last `timestamp` in epoch seconds, else none."""
        found = TIMESTAMP.findall(read_part(log, tail=True) or "")
        try:
            return [datetime.fromisoformat(found[-1]).timestamp()]
        except (IndexError, ValueError):
            return []

    def phases(self, version: Version) -> list[dict[str, Any]]:
        """Return the `## Progress` lines at `HEAD`, each with the worktree's ticks."""
        change = version.change
        tasks = read_part(version.tree / f"openspec/changes/{change}/tasks.md")
        found = []
        for mark, number, title in self.conduct["_progress"](version.tree, change):
            done, total = _count(tasks, number)
            found.append(
                {
                    "number": number,
                    "title": SUFFIX.sub("", title),
                    "rating": self.conduct["_rating"](title),
                    "box": mark == "x",
                    "done": done,
                    "total": total,
                }
            )
        return found

    def spent(self, text: str) -> dict[str, dict[str, Any]]:
        """Return each role's newest `verdicts` line fields in the status log's text."""
        found: dict[str, dict[str, Any]] = {}
        for line in text.splitlines():
            if (match := VERDICT.search(line)) and match[1] not in found:
                fields = dict(SPENT.findall(match[2]))
                found[match[1]] = {
                    "executor": fields.get("executor"),
                    "model": fields.get("model"),
                    "effort": fields.get("effort"),
                    "tokens": _int(fields.get("tokens")),
                    "fallback": self.converge["FALLBACK"] in line,
                }
        return found

    def converge_of(self, change: str) -> dict[str, Any] | None:
        """Return converge's run, round, cap and roles; None with no status log."""
        folder = self.runs / "changes" / change
        text = read_part(folder / "status_log.md")
        if text is None:
            return None
        heading = RUN_HEADING.search(text)
        after = text[heading.end() :].splitlines() if heading else []
        top = next((line for line in after if line.strip()), "")
        spent = self.spent(text)
        roles, rounds = {}, []
        for role in ROLES:
            front = read_part(folder / f"{role}.md") or ""
            field = self.conduct["_frontmatter"]
            rounds.append(_int(field(front, "round")))
            roles[role] = {
                "verdict": field(front, "verdict"),
                "open_blocking": _int(field(front, "open_blocking")),
                **{
                    key: spent.get(role, {}).get(key)
                    for key in ("executor", "model", "effort", "tokens", "fallback")
                },
            }
        known = [number for number in rounds if number is not None]
        return {
            "run": int(heading[1]) if heading else None,
            "mark": heading[2] if heading else None,
            "round": max(known, default=None),
            "cap": self.converge["CAP"],
            "fixing": " · fix — sent" in top,
            "roles": roles,
        }

    def diagnosed(self, change: str) -> bool:
        """Return whether the version's last run-log line is a rescue diagnosis."""
        order = self.conduct["_log_order"]
        for log in sorted((self.runs / "runs").glob("*.md"), key=order, reverse=True):
            mine = [event for event in self.events(log) if event.who == change]
            if mine:
                return mine[-1].name == "halt" and mine[-1].detail.startswith(
                    "rescue diagnosed"
                )
        return False

    def state(self, version: Version, stage: str, workers: list[dict[str, Any]]) -> str:
        """Return a version's state by the first matching row, `blocked` aside."""
        change = version.change
        halted = stage == "build" and self.conduct["_build_halt"](
            self.runs, version.tree, change
        )
        if stage in NEEDS_YOU:
            return "needs you"
        if stage == "converge-halted" or halted or self.diagnosed(change):
            return "halted"
        if stage in ("waiting", "stacked"):
            return stage
        return "running" if self.claim() == "live" and workers else "idle"

    def notes(self, change: str) -> list[dict[str, str]]:
        """Return the newest log's rescue decisions and supervisor lines."""
        found = []
        for event in self.newest():
            decided = event.name == "rescue" and re.match(
                rf"{change}: (decided|fixed)", event.detail
            )
            if event.who == "run" and (
                decided
                or (event.name == "supervise" and event.detail.startswith(f"{change}:"))
            ):
                found.append({"text": f"{event.name} — {event.detail}"})
        return found

    def version(self, version: Version) -> dict[str, Any]:
        """Return one version's tree, its state before `blocked` is read."""
        stage, why = self.conduct["stage_of"](self.primary, version)
        workers = self.workers(version.change)
        return {
            "id": version.change,
            "state": self.state(version, stage, workers),
            "stage": stage,
            "why": why,
            "unread": None,
            "phases": self.phases(version),
            "converge": self.converge_of(version.change),
            "workers": workers,
            "liveness": self.liveness(version, workers),
            "notes": self.notes(version.change),
        }

    def unread(self, version: Version, error: Exception) -> dict[str, Any]:
        """Return a version whose read raised: `unread` and nothing else."""
        return {
            "id": version.change,
            "state": "unread",
            "stage": None,
            "why": None,
            "unread": str(error),
            "phases": [],
            "converge": None,
            "workers": [],
            "liveness": None,
            "notes": [],
        }

    def tree(self) -> dict[str, Any]:
        """Return the project's state tree."""
        built = []
        for version in self.versions():
            try:
                built.append(self.version(version))
            # why: a reader may raise anything; one version is unread, the rest read.
            except Exception as error:  # noqa: BLE001
                built.append(self.unread(version, error))
        states = {each["id"]: each["state"] for each in built}
        for each in built:
            named = each["why"].split()[1:] if each["state"] == "waiting" else []
            if any(states.get(name) in ("halted", "needs you") for name in named):
                each["state"] = "blocked"
        cuts = self.conduct["_cuts"](self.primary)
        claim = self.claim()
        newest = self.newest()
        return {
            "name": self.primary.name,
            "unread": None,
            "run": {
                "claim": claim,
                "log": self.log.stem if self.log else None,
                "last": newest[-1].line if newest else None,
            },
            "for_you": self.for_you(built, cuts, claim),
            "versions": built,
            "queue": [
                {
                    "id": name,
                    "state": "cut" if entry["halt"] is None else "cut halted",
                    "halt": entry["halt"],
                }
                for name, entry in cuts.items()
            ],
        }

    def for_you(
        self, built: list[dict[str, Any]], cuts: dict[str, Any], claim: str
    ) -> list[dict[str, Any]]:
        """Return what needs a person, by kind and then by id."""
        rows = [
            {"kind": kind, "id": each["id"], "why": each["why"]}
            for kind in ("needs you", "halted")
            for each in built
            if each["state"] == kind
        ]
        rows += [
            {"kind": "cut halted", "id": name, "why": entry["halt"]}
            for name, entry in cuts.items()
            if entry["halt"] is not None
        ]
        if claim == "stale":
            why = "a run clears it, or stops naming why"
            rows.append({"kind": "stale run", "id": None, "why": why})
        if limit := self.limit():
            rows.append({"kind": "usage limit", "id": None, "why": limit})
        if self.unpushed():
            default = self.conduct["default_branch"](self.primary)
            rows.append(
                {"kind": "unpushed", "id": None, "why": f"{default} is ahead of origin"}
            )
        return rows

    def limit(self) -> str | None:
        """Return the last limit line's detail while the limit stands."""
        lines = [e for e in self.newest() if e.who == "run" and e.name == "limited"]
        if not lines:
            return None
        found = LIMIT.search(lines[-1].detail)
        if found is None:
            return lines[-1].detail
        reset = time.mktime(time.strptime(found[1], "%Y-%m-%d %H:%M"))
        return lines[-1].detail if reset > self.now else None

    def unpushed(self) -> bool:
        """Return whether the default branch is ahead of its origin ref, no network."""
        default = self.conduct["default_branch"](self.primary)
        span = f"refs/remotes/origin/{default}..refs/heads/{default}"
        count = self.conduct["_maybe"](self.primary, "rev-list", "--count", span)
        return bool(_int(count and count.strip()))

    def lively(self) -> dict[str, Any]:
        """Return the liveness of each version that has a worker, by id."""
        found = {}
        for version in self.versions():
            workers = self.workers(version.change)
            if workers:
                found[version.change] = self.liveness(version, workers)
        return found

    def fingerprint(self) -> str:
        """Return a hash of the stats of what a change of state touches."""
        git = self.primary / ".git"
        paths = [self.runs / "runs" / "active", git / "packed-refs"]
        paths += [self.log] if self.log else []
        paths += (self.runs / "changes").glob("*/*")
        paths += (git / "refs").rglob("*")
        for link in (git / "worktrees").glob("*/gitdir"):
            tree = Path((read_part(link) or "").strip()).parent
            paths += tree.glob("openspec/changes/*/tasks.md")
        paths += (self.conduct["_queue"](self.primary) / "cuts").glob("*")
        stats = sorted(status for status in map(_stat, paths) if status)
        return hashlib.sha256(json.dumps(stats).encode()).hexdigest()


def project(primary: Path, only: str | None, now: float) -> str:
    """Return a project's tree as JSON, or its liveness or fingerprint with `only`."""
    conduct = load(CONDUCT)
    try:
        reader = Reader(conduct, load(CONVERGE), primary, now)
        shown: Any = {
            None: reader.tree,
            "liveness": reader.lively,
            "fingerprint": lambda: {"fingerprint": reader.fingerprint()},
        }[only]()
    except conduct["Stop"] as stop:
        raise SystemExit(f"viewer: {stop}") from None
    return json.dumps(shown)


def main(argv: list[str] | None = None) -> int:
    """Run a command: print its JSON, or a usage line and return 2."""
    args = sys.argv[1:] if argv is None else argv
    match args:
        case ["project", primary]:
            only = None
        case ["project", primary, "--only", ("liveness" | "fingerprint") as only]:
            pass
        case _:
            print(USAGE, file=sys.stderr)
            return 2
    print(project(Path(primary), only, time.time()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
