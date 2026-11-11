# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Project each project's ship line into one state tree and serve it, read-only.

`viewer.py project <primary>` prints a tree; `serve`, `start` and `stop` run the server.
Why: 0120-ui-state design D1, D3, D7, D8.
"""

import contextlib
import glob
import hashlib
import json
import os
import re
import runpy
import signal
import stat
import subprocess
import sys
import threading
import time
import tomllib
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, NamedTuple, NoReturn, Protocol

SELF = Path(__file__).resolve()
SKILLS = SELF.parents[2]
CONDUCT = SKILLS / "mf-ship/scripts/conduct.py"
CONVERGE = SKILLS / "mf-converge/scripts/converge.py"
PAGE = SKILLS / "mf-ui/page/index.html"
PART = 262144
BOUND = 10
POLL = 2
REREAD = 10
LIVENESS = 5
KEEPALIVE = 15
START_WAIT = 2
PORT = 8737
SECURITY = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}
POLICY = (
    "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
    "connect-src 'self'; base-uri 'none'; form-action 'none'"
)
USAGE = (
    "usage: viewer.py project <primary> [--only liveness|fingerprint]"
    " | serve | start | stop"
)
STAMP = "%Y%m%d-%H%M%S"
ACTIVE = 60
QUIET = 300
ROLES = ("conformance", "adversarial")
READ_EVENTS = frozenset({"spawn", "finish", "halt", "limited", "rescue", "supervise"})
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


class Entry(NamedTuple):
    """A project the server shows: its primary checkout and its name."""

    path: Path
    name: str


class Child(Protocol):
    """A started process: its pid, and a wait that raises on a timeout."""

    pid: int

    def wait(self, timeout: float) -> int:
        """Return the exit code, or raise `subprocess.TimeoutExpired`."""


Read = Callable[[Path, str | None], dict[str, Any]]


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


def read_lines(path: Path) -> Iterator[str]:
    """Yield a regular file's lines one at a time, each cut at `PART` characters.

    The whole file is streamed, so the memory held is one line; a long line's rest is
    dropped. e.g. a pipe, a link or a missing file → no lines
    """
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        return
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        return
    with os.fdopen(fd, encoding="utf-8", errors="replace") as file:
        while piece := file.readline(PART):
            if not piece.endswith("\n") and len(piece) == PART:
                while (rest := file.readline(PART)) and not rest.endswith("\n"):
                    pass
            yield piece.rstrip("\n")


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
        """Read a log's events; a line earlier than the one before is a day on.

        The whole log is streamed, so a spawn or a midnight far back still counts; only
        the events the projector reads, and the last one, are kept.
        """
        base = datetime.strptime(log.stem[:15], STAMP)
        days, before, found = 0, 0, []
        newest: Event | None = None
        for line in read_lines(log):
            if not (match := self.conduct["EVENT"].match(line)):
                continue
            hours, minutes, seconds = (int(part) for part in line[:8].split(":"))
            moment = hours * 3600 + minutes * 60 + seconds
            days += moment < before
            before = moment
            at = base.replace(hour=hours, minute=minutes, second=seconds)
            at += timedelta(days=days)
            newest = Event(
                match[1], match[2], line[match.end() :], at.timestamp(), line
            )
            if newest.name in READ_EVENTS:
                found.append(newest)
        if newest and (not found or found[-1] is not newest):
            found.append(newest)
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

    def halted_in_log(self, change: str) -> bool:
        """Return whether the version's last line in the newest run log is a halt.

        e.g. `halt — build worker exit 1` or `halt — rescue diagnosed`; a later spawn
        of the version, or a newer log with no line of its own, clears it
        """
        mine = [event for event in self.newest() if event.who == change]
        return bool(mine) and mine[-1].name == "halt"

    def state(self, version: Version, stage: str, workers: list[dict[str, Any]]) -> str:
        """Return a version's state by the first matching row, `blocked` aside."""
        change = version.change
        halted = stage == "build" and self.conduct["_build_halt"](
            self.runs, version.tree, change
        )
        if stage in NEEDS_YOU:
            return "needs you"
        if stage == "converge-halted" or halted or self.halted_in_log(change):
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
    # why: the spec has the projector read with no optional git lock, however it is run.
    os.environ["GIT_OPTIONAL_LOCKS"] = "0"
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


def _refuse(message: str) -> NoReturn:
    """Print a refusal on stderr and exit 2."""
    print(f"viewer: {message}", file=sys.stderr)
    raise SystemExit(2)


def config_path() -> Path:
    """Return `ui.toml` under `$XDG_CONFIG_HOME`, else `~/.config`."""
    base = os.environ.get("XDG_CONFIG_HOME")
    return (Path(base) if base else Path.home() / ".config") / "minionsfactory/ui.toml"


def state_folder() -> Path:
    """Return the state folder under `$XDG_STATE_HOME`, else `~/.local/state`."""
    base = os.environ.get("XDG_STATE_HOME")
    return (Path(base) if base else Path.home() / ".local/state") / "minionsfactory"


def recorded() -> Path:
    """Return the list of repos a run started in, which `conduct.py run` keeps."""
    return Path.home() / ".mf-ship-origin" / "repos"


def read_config(path: Path) -> tuple[int, list[dict[str, Any]]]:
    """Return the config's port and container rows; a missing file gives the defaults.

    e.g. `port = 9000` and one `[[container]]` row → (9000, [{"path": ...}])
    """
    if not path.is_file():
        return PORT, []
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        _refuse(f"{path}: {error}")
    port, rows = data.get("port", PORT), data.get("container", [])
    if not isinstance(port, int) or isinstance(port, bool) or not 0 < port < 65536:
        _refuse(f"{path}: `port` is not an integer from 1 to 65535")
    if not isinstance(rows, list) or not all(
        isinstance(row, dict) and isinstance(row.get("path"), str) for row in rows
    ):
        _refuse(f"{path}: a `[[container]]` row has no string `path`")
    return port, rows


def projects(record: Path, rows: list[dict[str, Any]]) -> list[Entry]:
    """Return the shown projects: the rows first, then the record, each path once.

    e.g. a row with `hide = true` drops its project; a path with no `.minions/` is none
    """
    named: dict[Path, dict[str, Any]] = {}
    for row in rows:
        named.setdefault(Path(row["path"]).expanduser().resolve(), row)
    lines = (read_part(record) or "").splitlines()
    listed = [Path(line.strip()).resolve() for line in lines if line.strip()]
    found = []
    for path in dict.fromkeys([*named, *listed]):
        row = named.get(path, {})
        if row.get("hide") is True or not (path / ".minions").is_dir():
            continue
        name = row.get("name")
        found.append(Entry(path, name if isinstance(name, str) and name else path.name))
    return found


def _unread(primary: Path, reason: str) -> dict[str, Any]:
    """Return a project whose read failed: its name, the reason, no versions."""
    return {
        "name": primary.name,
        "unread": reason,
        "run": None,
        "for_you": [],
        "versions": [],
        "queue": [],
    }


def read_project(primary: Path, only: str | None, bound: int = BOUND) -> dict[str, Any]:
    """Return one project's read by a child process, killed past `bound` seconds.

    A failed read is a project `unread` with the reason; `only` reads fail the same way.
    """
    argv = [sys.executable, str(SELF), "project", str(primary)]
    child = subprocess.Popen(
        [*argv, *(["--only", only] if only else [])],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        start_new_session=True,
    )
    try:
        out, err = child.communicate(timeout=bound)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(child.pid, signal.SIGKILL)
        child.communicate()
        return _unread(primary, f"read past {bound} s")
    if child.returncode:
        lines = err.strip().splitlines()
        return _unread(primary, lines[0] if lines else f"exit {child.returncode}")
    try:
        shown = json.loads(out)
    except ValueError:
        shown = None
    return shown if isinstance(shown, dict) else _unread(primary, "no state read")


class State:
    """The newest numbered state, shared by the poll thread and the streams."""

    def __init__(self) -> None:
        """Start at sequence 0 with no projects."""
        self.seq = 0
        self.projects: list[dict[str, Any]] = []
        self.last: str | None = None
        self.changed = threading.Condition()

    def publish(self, projects: list[dict[str, Any]]) -> bool:
        """Raise `seq` and wake the streams when `projects` differ; return whether."""
        text = json.dumps(projects)
        with self.changed:
            if text == self.last:
                return False
            self.last, self.projects, self.seq = text, projects, self.seq + 1
            self.changed.notify_all()
        return True

    def latest(self) -> tuple[int, list[dict[str, Any]]]:
        """Return the newest `seq` and its projects."""
        with self.changed:
            return self.seq, self.projects

    def wait(self, after: int, timeout: float) -> bool:
        """Block until `seq` is above `after` or the timeout; return whether it is."""
        with self.changed:
            return self.changed.wait_for(lambda: self.seq > after, timeout)


def frame(seq: int, projects: list[dict[str, Any]]) -> str:
    r"""Return one server-sent event holding the whole numbered state.

    e.g. `id: 2\nevent: state\ndata: {"seq":2,"projects":[]}\n\n`
    """
    data = json.dumps({"seq": seq, "projects": projects}, separators=(",", ":"))
    return f"id: {seq}\nevent: state\ndata: {data}\n\n"


def stream(state: State, keepalive: float = KEEPALIVE) -> Iterator[str]:
    """Yield the newest frame, each newer one once, and a comment when none comes."""
    seen = -1
    while True:
        seq, shown = state.latest()
        if seq > seen:
            seen = seq
            yield frame(seq, shown)
        elif not state.wait(seen, keepalive):
            yield ": keep-alive\n\n"


def _answer(
    status: int, kind: str, body: str | Iterator[str], extra: dict[str, str]
) -> tuple[int, dict[str, str], str | Iterator[str]]:
    """Return a status, the headers every answer carries and the body."""
    return status, {"Content-Type": kind, **SECURITY, **extra}, body


def route(
    path: str, host: str | None, port: int, state: State
) -> tuple[int, dict[str, str], str | Iterator[str]]:
    """Return the status, headers and body of a GET; no socket is touched.

    e.g. `/state?x=1` from `127.0.0.1:8737` → 200 and the newest frame as JSON
    """
    if host not in (f"127.0.0.1:{port}", f"localhost:{port}"):
        return _answer(403, "text/plain", "forbidden", {})
    match path.split("?", 1)[0]:
        case "/":
            page = PAGE.read_text(encoding="utf-8")
            return _answer(
                200,
                "text/html; charset=utf-8",
                page,
                {"Content-Security-Policy": POLICY},
            )
        case "/state":
            seq, shown = state.latest()
            body = json.dumps({"seq": seq, "projects": shown})
            return _answer(200, "application/json", body, {})
        case "/events":
            return _answer(200, "text/event-stream", stream(state), {})
        case _:
            return _answer(404, "text/plain", "not found", {})


def _read_one(
    now: float, entry: Entry, memory: dict[Path, list[Any]], read: Read
) -> dict[str, Any]:
    """Return one project's state: a full read on a change or on time, else liveness."""
    last: list[Any] | None = memory.get(entry.path)
    mark = read(entry.path, "fingerprint").get("fingerprint")
    if last is None or mark is None or mark != last[0] or now - last[1] >= REREAD:
        last = memory[entry.path] = [mark, now, now, read(entry.path, None)]
    elif now - last[2] >= LIVENESS:
        lively = read(entry.path, "liveness")
        shown: dict[str, Any] = last[3]
        last[2] = now
        last[3] = {
            **shown,
            "versions": [
                {**each, "liveness": lively.get(each["id"], each["liveness"])}
                for each in shown["versions"]
            ],
        }
    project: dict[str, Any] = last[3]
    return {**project, "name": entry.name}


def tick(
    now: float, entries: list[Entry], memory: dict[Path, list[Any]], read: Read
) -> list[dict[str, Any]]:
    """Return each project's state, the projects read in parallel.

    `memory[path]` is the last fingerprint, full read time, liveness time and project.
    """
    with ThreadPoolExecutor(max_workers=max(1, len(entries))) as pool:
        return list(
            pool.map(lambda entry: _read_one(now, entry, memory, read), entries)
        )


class Handler(BaseHTTPRequestHandler):
    """Answer a GET by `route`, writing a generator body as it yields."""

    state: State
    port: int

    def do_GET(self) -> None:  # pragma: no cover
        """Write the answer `route` gives to this request."""
        host = self.headers.get("Host")
        status, headers, body = route(self.path, host, self.port, self.state)
        self.send_response(status)
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()
        for chunk in [body] if isinstance(body, str) else body:
            self.wfile.write(chunk.encode())
            self.wfile.flush()


def serve(config: Path) -> int:  # pragma: no cover
    """Run the server on `127.0.0.1` in the foreground, polling the projects."""
    port, rows = read_config(config)
    state = State()
    memory: dict[Path, list[Any]] = {}

    def poll() -> None:
        while True:
            entries = projects(recorded(), rows)
            state.publish(tick(time.monotonic(), entries, memory, read_project))
            time.sleep(POLL)

    Handler.state, Handler.port = state, port
    threading.Thread(target=poll, daemon=True).start()
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
    return 0


def run_ps(pid: int) -> str:
    """Return the command line `ps` shows for `pid`, empty when it shows none."""
    done = subprocess.run(
        ["ps", "-o", "command=", "-p", str(pid)],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    return done.stdout.strip()


def serves(pid: int, ps: Callable[[int], str]) -> bool:
    """Return whether `pid` is this script's `serve` command."""
    words = ps(pid).split()
    return "serve" in words and any(word.endswith("viewer.py") for word in words)


def spawn(argv: list[str], log: Path) -> subprocess.Popen[bytes]:
    """Start `argv` in a new session, its output appended to `log`, mode 0600."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW
    fd = os.open(log, flags, 0o600)
    try:
        return subprocess.Popen(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=fd,
            stderr=fd,
            start_new_session=True,
        )
    finally:
        os.close(fd)


def _private(path: Path, text: str) -> None:
    """Write `text` at `path`, mode 0600."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, "w") as file:
        file.write(text)


def _forget(folder: Path) -> None:
    """Remove the pid and port files, which say a server runs."""
    for name in ("viewer.pid", "viewer.port"):
        (folder / name).unlink(missing_ok=True)


def _held(folder: Path, name: str) -> int | None:
    """Return the integer in the state folder's file `name`, None when it holds none."""
    return _int((read_part(folder / name) or "").strip())


def start(
    folder: Path,
    config: Path,
    spawn: Callable[[list[str], Path], Child],
    ps: Callable[[int], str],
    wait: float = START_WAIT,
) -> int:
    """Print the URL of the running server, starting one detached when none runs.

    Returns 1 when the new server exits within `wait` seconds.
    """
    port, _ = read_config(config)
    pid = _held(folder, "viewer.pid") or 0
    if pid > 1 and serves(pid, ps):
        print(f"http://127.0.0.1:{_held(folder, 'viewer.port') or port}/")
        return 0
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    folder.chmod(0o700)
    log = folder / "viewer.log"
    child = spawn([sys.executable, str(SELF), "serve"], log)
    _private(folder / "viewer.pid", f"{child.pid}\n")
    _private(folder / "viewer.port", f"{port}\n")
    try:
        child.wait(timeout=wait)
    except subprocess.TimeoutExpired:
        print(f"http://127.0.0.1:{port}/")
        return 0
    _forget(folder)
    print(f"viewer: the server exited — see {log}")
    return 1


def stop(
    folder: Path, ps: Callable[[int], str], kill: Callable[[int, int], None]
) -> int:
    """End the server `start` started, signalling its pid only while it serves."""
    pid = _held(folder, "viewer.pid") or 0
    running = pid > 1 and serves(pid, ps)
    if running:
        kill(pid, signal.SIGTERM)
    _forget(folder)
    print("viewer: stopped" if running else "viewer: not running")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run a command: print its JSON, serve, start or stop, else a usage line and 2."""
    args = sys.argv[1:] if argv is None else argv
    match args:
        case ["serve"]:
            return serve(config_path())
        case ["start"]:
            return start(state_folder(), config_path(), spawn, run_ps)
        case ["stop"]:
            return stop(state_folder(), run_ps, os.kill)
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
