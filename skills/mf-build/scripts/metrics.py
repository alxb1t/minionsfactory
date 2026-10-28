# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Collect a repository's declared metrics into a data file, and render its page.

    metrics.py collect --change <id> --base <rev> --out <path> [--value <id>=<n> …]
    metrics.py page <id> [--data <path>] [--out <path>]

Exit 0 written · 2 the catalogue is broken · 3 no catalogue · any other a crash.
Why: 0030-change-impact design D2…D5.
"""

import argparse
import html
import json
import math
import os
import re
import subprocess
import sys
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Any

CATALOGUE = Path("metrics/catalogue.toml")
CHANGES = Path("metrics/changes")
MF_PATH = Path("skills/mf-build/scripts/metrics.py")
NO_CATALOGUE = "metrics: none — no catalogue"
TIMEOUT_SECONDS = 300
REQUIRED = ("id", "title", "group", "unit", "better")
KEYS = {*REQUIRED, "watch", "noise", "script", "args", "source"}
DERIVED = ("diff-lines", "diff-files", "phases")
# What moved lists the states in this order; within a state, the catalogue's.
STATES = (
    "crossed here",
    "worsened",
    "over",
    "back under",
    "improved",
    "steady",
    "new",
    "unavailable",
)

Metric = dict[str, Any]
Value = dict[str, Any]
Number = int | float


class CatalogueError(Exception):
    """The catalogue is broken; the message names the entry."""


def metric_argv(script: str, args: list[str]) -> list[str]:
    """Return the command that runs a metric script; unit tests replace it."""
    return ["uv", "run", "--script", script, *args]


def _is_number(value: object) -> bool:
    """Return whether `value` is a TOML or JSON number, a bool excluded."""
    return isinstance(value, int | float) and not isinstance(value, bool)


def _inside(root: Path, script: str) -> bool:
    """Return whether `script` is a relative path inside `root`, not a URL or option."""
    if (
        script.startswith("-")
        or Path(script).is_absolute()
        or re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", script)
    ):
        return False
    return (root / script).resolve().is_relative_to(root.resolve())


def _entry_problem(entry: dict[str, Any], seen: set[str], root: Path) -> str | None:
    """Return what is wrong with one `[[metric]]` entry, or None."""
    missing = [key for key in REQUIRED if not isinstance(entry.get(key), str)]
    if missing:
        return "missing " + ", ".join(f"`{key}`" for key in missing)
    if entry["id"] in seen:
        return "`id` repeated"
    if unknown := sorted(entry.keys() - KEYS):
        return "unknown key " + ", ".join(f"`{key}`" for key in unknown)
    if entry["better"] not in ("lower", "higher"):
        return "`better` is neither `lower` nor `higher`"
    if "script" in entry and "source" in entry:
        return "declares both `script` and `source`"
    if "script" not in entry and "source" not in entry:
        return "declares neither `script` nor `source`"
    if "source" in entry and entry["source"] != "station":
        return '`source` is not "station"'
    if "script" in entry and not isinstance(entry["script"], str):
        return "`script` is not a string"
    if "script" in entry and not _inside(root, entry["script"]):
        return "`script` is not a path inside the repository"
    args = entry.get("args", [])
    if not isinstance(args, list) or not all(isinstance(a, str) for a in args):
        return "`args` is not a list of strings"
    for key in ("watch", "noise"):
        if key in entry and not _is_number(entry[key]):
            return f"`{key}` is not a number"
    return None


def load_catalogue(root: Path) -> list[Metric] | None:
    """Return the catalogue's metrics in order, or None when the repo has none.

    Raise CatalogueError, naming the entry, when the catalogue is broken.
    """
    path = root / CATALOGUE
    if not path.is_file():
        return None
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise CatalogueError(f"{CATALOGUE}: does not parse: {exc}") from exc
    entries = data.get("metric", [])
    if not isinstance(entries, list):
        raise CatalogueError(f"{CATALOGUE}: `metric` is not an array of tables")
    seen: set[str] = set()
    for number, entry in enumerate(entries, start=1):
        name = f"{CATALOGUE}: metric {number}"
        if not isinstance(entry, dict):
            raise CatalogueError(f"{name}: not a table")
        if isinstance(entry.get("id"), str):
            name += f" `{entry['id']}`"
        if problem := _entry_problem(entry, seen, root):
            raise CatalogueError(f"{name}: {problem}")
        seen.add(entry["id"])
    return entries


def _number(text: str) -> Number | None:
    """Return `text` as a finite number, or None.

    e.g. "10031" → 10031, "1.5" → 1.5, "n/a" → None
    """
    try:
        return int(text)
    except ValueError:
        pass
    try:
        value = float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def _unavailable(why: str) -> Value:
    """Return a value recording a gap and its reason."""
    return {"status": "unavailable", "why": why}


def _scrubbed(why: str, root: Path) -> str:
    """Return `why`, to be committed, with the root as `<repo>` and the home as `~`.

    A path is replaced unless a name character touches it: `/app` never inside
    `/usr/app/x`, `/apps` or `/app.bak`, but in `file:///app` and `(/app)`.
    """
    for path, name in ((root, "<repo>"), (Path.home(), "~")):
        if str(path) != path.anchor:
            whole = r"(?<![\w.~-])" + re.escape(str(path)) + r"(?![\w-]|\.\w)"
            why = re.sub(whole, name, why)
    return why


def run_metric(root: Path, metric: Metric, env: dict[str, str]) -> Value:
    """Return the number a metric script prints last, or `unavailable` and why."""
    argv = metric_argv(metric["script"], metric.get("args", []))
    try:
        done = subprocess.run(
            argv,
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return _unavailable(f"timed out after {TIMEOUT_SECONDS} s")
    except OSError as exc:
        return _unavailable(_scrubbed(str(exc), root))
    lines = done.stdout.strip().splitlines()
    number = _number(lines[-1]) if lines else None
    if done.returncode == 0 and number is not None:
        return {"value": number}
    if stderr := done.stderr.strip().splitlines():
        return _unavailable(_scrubbed(stderr[0], root))
    if done.returncode != 0:
        return _unavailable(f"exit {done.returncode}")
    return _unavailable("no number on the last line")


def _git(root: Path, *args: str) -> str:
    """Return a git command's stripped stdout; a failure raises."""
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    ).stdout.strip()


def run_directory(root: Path) -> Path:
    """Return `.minions/` beside the primary checkout, the same from every worktree."""
    common = _git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(common).parent / ".minions"


def _change_dir(root: Path, change: str) -> Path:
    """Return the change's directory relative to `root`, active or archived."""
    active = Path("openspec/changes") / change
    archived = Path("openspec/changes/archive") / change
    return (
        archived
        if not (root / active).is_dir() and (root / archived).is_dir()
        else active
    )


def change_version(root: Path, change: str) -> str:
    """Return the `version:` of the change's `proposal.md` frontmatter."""
    text = (root / _change_dir(root, change) / "proposal.md").read_text(
        encoding="utf-8"
    )
    front = re.match(r"---\n(.*?)\n---", text, re.DOTALL)
    found = front and re.search(r"^version:\s*(\S+)", front.group(1), re.MULTILINE)
    if not found:
        raise SystemExit(f"{change}: no `version:` in its proposal.md frontmatter")
    return found.group(1)


def _derived(root: Path, change: str, base: str, head: str) -> dict[str, Value]:
    """Return the station values the collector derives from git and `tasks.md`."""
    numstat = _git(
        root, "diff", "--numstat", base, head, "--", ".", ":(exclude)metrics"
    )
    rows = [line.split("\t") for line in numstat.splitlines() if line]
    lines = sum(int(row[0]) + int(row[1]) for row in rows if row[0] != "-")
    tasks = root / _change_dir(root, change) / "tasks.md"
    values = {"diff-lines": {"value": lines}, "diff-files": {"value": len(rows)}}
    if not tasks.is_file():
        return values | {"phases": _unavailable(f"no tasks.md for {change}")}
    progress = tasks.read_text(encoding="utf-8").partition("## Progress")[2]
    progress = progress.split("\n## ", 1)[0]
    phases = re.findall(r"^- \[[ x]\] \d+ — ", progress, re.MULTILINE)
    return values | {"phases": {"value": len(phases)}}


def mf_version(package: Path) -> str:
    """Return `git describe` of the MF checkout holding `package`, else `unknown`.

    A checkout that tracks the collector anywhere but `MF_PATH` is not MF's.
    """
    try:
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--full-name", MF_PATH.name],
            cwd=package,
            capture_output=True,
            text=True,
        )
        if tracked.returncode != 0 or tracked.stdout.strip() != MF_PATH.as_posix():
            return "unknown"
        done = subprocess.run(
            ["git", "describe", "--tags", "--always", "--dirty"],
            cwd=package,
            capture_output=True,
            text=True,
        )
    except OSError:
        return "unknown"
    return (done.returncode == 0 and done.stdout.strip()) or "unknown"


def _write(root: Path, out: Path, text: str) -> None:
    """Write `text` to `out` under `root`, making its folder, and say so."""
    target = root / out
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    print(f"metrics: wrote {out}")


def collect(
    root: Path,
    change: str,
    base: str,
    out: Path,
    passed: dict[str, Number],
    executor: str,
    model: str,
) -> int:
    """Write the change's data file to `out`; return the exit code."""
    metrics = load_catalogue(root)
    if metrics is None:
        print(NO_CATALOGUE)
        return 3
    stations = {m["id"] for m in metrics if m.get("source") == "station"}
    for key in sorted(passed.keys() - stations):
        print(
            f"metrics: --value {key} ignored — {CATALOGUE} declares no station metric",
            file=sys.stderr,
        )
    base_sha, head_sha = _git(root, "rev-parse", f"{base}^{{commit}}", "HEAD").split()
    base_short, head_short = (
        _git(root, "rev-parse", "--short", sha) for sha in (base_sha, head_sha)
    )
    env = os.environ | {
        "MF_METRICS_CHANGE": change,
        "MF_METRICS_BASE": base_sha,
        "MF_METRICS_HEAD": head_sha,
    }
    derived: dict[str, Value] = {}
    values: dict[str, Value] = {}
    for metric in metrics:
        key = metric["id"]
        if "script" in metric:
            values[key] = run_metric(root, metric, env)
        elif key in passed:
            values[key] = {"value": passed[key]}
        elif key in DERIVED:
            derived = derived or _derived(root, change, base_sha, head_sha)
            values[key] = derived[key]
        else:
            values[key] = _unavailable("not passed by the station")
    record = {
        "change": change,
        "version": change_version(root, change),
        "base": base_short,
        "analyzed": head_short,
        "measured_on": "local",
        "collected_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "mf_version": mf_version(Path(__file__).resolve().parent),
        "executor": executor,
        "model": model,
        "values": values,
    }
    _write(root, out, json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    return 0


def version_key(version: str) -> tuple[int, ...]:
    """Return a version as numbers, so `v0.9` sorts below `v0.10`.

    e.g. "v0.10" → (0, 10), "v0.9.1" → (0, 9, 1)
    """
    return tuple(int(part) for part in version.lstrip("v").split("."))


def _tracked_records(root: Path) -> list[dict[str, Any]]:
    """Return every tracked data file in `metrics/changes/`, parsed."""
    listed = _git(root, "ls-files", "--", str(CHANGES))
    names = [name for name in listed.splitlines() if name.endswith(".json")]
    return [json.loads((root / name).read_text(encoding="utf-8")) for name in names]


def _below(root: Path, version: str) -> list[dict[str, Any]]:
    """Return the tracked data files with a version below `version`, oldest first."""
    below = [
        record
        for record in _tracked_records(root)
        if version_key(record["version"]) < version_key(version)
    ]
    return sorted(below, key=lambda record: version_key(record["version"]))


def previous_release(root: Path, version: str) -> dict[str, Any] | None:
    """Return the tracked data file with the highest version below `version`."""
    below = _below(root, version)
    return below[-1] if below else None


def _past(metric: Metric, value: Number) -> bool:
    """Return whether `value` is past the metric's `watch`, by `better`."""
    watch = metric["watch"]
    return value > watch if metric["better"] == "lower" else value < watch


def classify(metric: Metric, previous: Number | None, now: Number | None) -> str:
    """Return the metric's state against the previous release, one of STATES."""
    if now is None:
        return "unavailable"
    if previous is None:
        return "new"
    if "watch" in metric:
        was, is_now = _past(metric, previous), _past(metric, now)
        if is_now:
            return "over" if was else "crossed here"
        if was:
            return "back under"
    delta = now - previous
    if abs(delta) <= metric.get("noise", 0):
        return "steady"
    worse = delta > 0 if metric["better"] == "lower" else delta < 0
    return "worsened" if worse else "improved"


def _value(record: dict[str, Any] | None, key: str) -> Number | None:
    """Return a record's number for `key`, None for a gap or no record."""
    entry = (record or {}).get("values", {}).get(key, {})
    return entry.get("value")


def _fmt(value: Number | None, sign: bool = False) -> str:
    """Return a number for the page; e.g. 3 → "3", 1.5 → "+1.5" with `sign`."""
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:+g}" if sign else f"{value:g}"
    return f"{value:+d}" if sign else str(value)


_E = html.escape

_W, _H, _LEFT, _RIGHT, _TOP, _BOTTOM = 360, 150, 52, 14, 12, 34


def chart(metric: Metric, points: list[tuple[str, Number | None, bool]]) -> str:
    """Return an inline SVG line chart of `points` — (version, value, is this change).

    The x axis is by version; `watch` is dashed; a missing value is a gap.
    """
    known = [v for _, v, _ in points if v is not None]
    span = known + ([metric["watch"]] if "watch" in metric else [])
    lo, hi = (min(span), max(span)) if span else (0, 1)
    if lo == hi:
        lo, hi = lo - 1, hi + 1
    plot_w, plot_h = _W - _LEFT - _RIGHT, _H - _TOP - _BOTTOM

    def x(i: int) -> float:
        if len(points) == 1:
            return _LEFT + plot_w / 2
        return _LEFT + i * plot_w / (len(points) - 1)

    def y(v: Number) -> float:
        return _TOP + (hi - v) / (hi - lo) * plot_h

    parts = [
        f'<svg viewBox="0 0 {_W} {_H}" width="{_W}" height="{_H}" role="img">',
        f"<title>{_E(metric['title'])}</title>",
        *(
            f'<text class="axis" x="{_LEFT - 6}" y="{at}" text-anchor="end">'
            f"{_fmt(v)}</text>"
            for v, at in ((hi, _TOP + 4), (lo, _TOP + plot_h))
        ),
    ]
    if "watch" in metric:
        wy = f"{y(metric['watch']):.1f}"
        parts.append(
            f'<line class="watch" x1="{_LEFT}" x2="{_W - _RIGHT}" y1="{wy}" y2="{wy}" '
            'stroke-dasharray="4 3"/>'
        )
    run: list[str] = []
    for i, (_, value, _) in enumerate([*points, ("", None, False)]):
        if value is None:
            if len(run) > 1:
                parts.append(f'<polyline class="line" points="{" ".join(run)}"/>')
            run = []
        else:
            run.append(f"{x(i):.1f},{y(value):.1f}")
    for i, (version, value, here) in enumerate(points):
        now = " now" if here else ""
        parts.append(
            f'<text class="axis{now}" x="{x(i):.1f}" y="{_H - 14}" '
            f'text-anchor="middle">{_E(version)}</text>'
        )
        if value is not None:
            radius = 4 if here else 2.5
            parts.append(
                f'<circle class="dot{now}" cx="{x(i):.1f}" cy="{y(value):.1f}" '
                f'r="{radius}">'
                f"<title>{_E(version)}: {_fmt(value)}</title></circle>"
            )
    parts.append("</svg>")
    return "\n".join(parts)


_STYLE = """
body { font: 14px/1.4 system-ui, sans-serif; margin: 2rem; color: #222; }
table { border-collapse: collapse; } td, th { padding: .2rem .7rem; text-align: left; }
tr + tr td { border-top: 1px solid #ddd; } .num { text-align: right; }
.charts { display: flex; flex-wrap: wrap; gap: 1rem; } figure { margin: 0; }
.line { fill: none; stroke: #4a6fa5; stroke-width: 1.5; } .dot { fill: #4a6fa5; }
.dot.now { fill: #d1495b; } .watch { stroke: #d1495b; }
.axis { font-size: 10px; fill: #666; } .axis.now { fill: #d1495b; font-weight: bold; }
"""


Row = tuple[Metric, Number | None, Number | None, str]


def moved(
    metrics: list[Metric], record: dict[str, Any], previous: dict[str, Any] | None
) -> list[Row]:
    """Return (metric, previous, now, state) per metric, in What moved's order."""
    rows = []
    for metric in metrics:
        key = metric["id"]
        now, before = _value(record, key), _value(previous, key)
        rows.append((metric, before, now, classify(metric, before, now)))
    return sorted(rows, key=lambda row: STATES.index(row[-1]))


def render_page(
    root: Path, metrics: list[Metric], record: dict[str, Any], out: Path
) -> str:
    """Return the page: a header, what moved since the previous release, the charts."""
    change, version = record["change"], record["version"]
    history = _below(root, version)
    previous = history[-1] if history else None
    history.append(record)
    rows = moved(metrics, record, previous)

    folder = _change_dir(root, change)
    here = (root / out).parent

    def link(name: str) -> str:
        href = Path(os.path.relpath(root / folder / name, here)).as_posix()
        return f'<a href="{_E(href)}">{_E(name)}</a>'

    provenance = ", ".join(
        f"{key} {_E(str(record.get(key)))}"
        for key in ("measured_on", "collected_at", "mf_version", "executor", "model")
    )
    lines = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        f"<title>{_E(change)} · metrics</title><style>{_STYLE}</style></head><body>",
        f"<h1>{_E(change)} · {_E(version)}</h1>",
        f"<p>base {_E(record['base'])} · analyzed {_E(record['analyzed'])} · "
        f"previous {_E(previous['version'] if previous else 'none')}</p>",
        f"<p>{provenance}</p>",
        f"<p>{link('proposal.md')} · {link('design.md')}"
        + (
            f" · archived at {_E(folder.as_posix())}/"
            if "archive" in folder.parts
            else ""
        )
        + "</p>",
        "<h2>What moved</h2>",
        "<table><tr><th>metric</th><th>previous</th><th>now</th><th>Δ</th>"
        "<th>state</th></tr>",
    ]
    for metric, before, now, state in rows:
        if now is None:
            why = (
                record["values"]
                .get(metric["id"], {})
                .get("why", "not in the data file")
            )
            shown = f"unavailable — {_E(why)}"
        else:
            shown = _fmt(now)
        delta = now - before if now is not None and before is not None else None
        lines.append(
            f'<tr><td>{_E(metric["title"])}</td><td class="num">{_fmt(before)}</td>'
            f'<td class="num">{shown}</td><td class="num">{_fmt(delta, sign=True)}</td>'
            f"<td>{state}</td></tr>"
        )
    lines.append("</table>")
    groups = list(dict.fromkeys(m["group"] for m in metrics))
    for group in groups:
        lines += [f"<h2>{_E(group)}</h2>", '<div class="charts">']
        for metric in (m for m in metrics if m["group"] == group):
            points = [
                (r["version"], _value(r, metric["id"]), r is record) for r in history
            ]
            caption = (
                f"{metric['title']} ({metric['unit']}, {metric['better']} is better)"
            )
            lines.append(
                f"<figure><figcaption>{_E(caption)}</figcaption>"
                f"{chart(metric, points)}</figure>"
            )
        lines.append("</div>")
    lines.append("</body></html>")
    return "\n".join(lines) + "\n"


def page(root: Path, change: str, data: Path | None, out: Path | None) -> int:
    """Write the change's page from its data file; return the exit code."""
    metrics = load_catalogue(root)
    if metrics is None:
        print(NO_CATALOGUE)
        return 3
    data = data or CHANGES / f"{change}.json"
    out = out or run_directory(root) / "metrics" / f"{change}.html"
    record = json.loads((root / data).read_text(encoding="utf-8"))
    _write(root, out, render_page(root, metrics, record, out))
    rows = moved(metrics, record, previous_release(root, record["version"]))
    states = [row[-1] for row in rows]
    crossed, worsened = states.count("crossed here"), states.count("worsened")
    print(f"metrics: crossed here {crossed} · worsened {worsened}")
    return 0


def _passed(text: str) -> tuple[str, Number]:
    """Parse a `--value <metric-id>=<number>` argument."""
    key, _, raw = text.partition("=")
    number = _number(raw)
    if not key or number is None:
        raise argparse.ArgumentTypeError(f"not <metric-id>=<number>: {text}")
    return key, number


def main(argv: list[str] | None = None) -> int:
    """Run `collect` or `page` from the current directory; return the exit code."""
    parser = argparse.ArgumentParser(
        prog="metrics.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    commands = parser.add_subparsers(dest="command", required=True)
    gather = commands.add_parser("collect", help="write a change's data file")
    gather.add_argument("--change", required=True)
    gather.add_argument("--base", required=True)
    gather.add_argument("--out", required=True, type=Path)
    gather.add_argument("--value", action="append", default=[], type=_passed)
    gather.add_argument("--executor", default="unidentified")
    gather.add_argument("--model", default="unidentified")
    show = commands.add_parser("page", help="render a change's page from its data file")
    show.add_argument("change")
    show.add_argument("--data", type=Path)
    show.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    root = Path.cwd()
    try:
        if args.command == "collect":
            return collect(
                root,
                args.change,
                args.base,
                args.out,
                dict(args.value),
                args.executor,
                args.model,
            )
        return page(root, args.change, args.data, args.out)
    except CatalogueError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
