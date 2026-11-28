"""The metric scripts' reads, pinned on the side each reads today.

A case holds the answer a script gives for a file now; a later phase turns the
cases its reading changes and no other. Why: 0162-metric-scripts design D12.
"""

import importlib.util
import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest
from mflib import debtfile, statuslog

_ROOT = Path(__file__).resolve().parent.parent
_RUN = _ROOT / "scripts" / "metrics" / "run.py"
_DEBT = _ROOT / "scripts" / "metrics" / "debt.py"
_REVIEW = _ROOT / "skills" / "mf-review-metrics" / "scripts" / "review_metrics.py"

_DAY = "%d %H:%M:%S"
_BOUND = 262_144
_GAP_ROUND = "gap: no round in the status log"
_GAP_BLOCKERS = "gap: no round 1 verdicts with open_blocking"
_GAP_STATUS = "gap: no 0001-x/status_log.md"
_GAP_FINDINGS = "gap: no ## Refuted in 0001-x/conformance.md"
_GAP_HEAD = "gap: no head in 0001-x/build.done"
_GAP_RESULT = "gap: no result event in 0001-x/logs/20261101-100000-build.log"
_GAP_QUOTA = "gap: no mf.quota line in a Codex log"


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


run = _load(_RUN)
debt = _load(_DEBT)
review_metrics = _load(_REVIEW)


@pytest.fixture(autouse=True)
def _no_codex_sessions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Read Codex sessions from an empty folder, never the operator's."""
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=mf", "-c", "user.email=mf@example.invalid"]
        + ["-c", "commit.gpgsign=false", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _repo(root: Path) -> Path:
    """Return `root` as a new git repository, the primary of a version's run."""
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q", "-b", "main")
    return root


def _put(root: Path, name: str, text: str | bytes) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(text, bytes):
        path.write_bytes(text)
    else:
        path.write_text(text, encoding="utf-8")
    return path


def _lines(*lines: object) -> str:
    return "".join(
        (line if isinstance(line, str) else json.dumps(line)) + "\n" for line in lines
    )


def _event(clock: str, name: str, detail: str, who: str = "0001-x") -> str:
    return f"{clock} · {who} · {name} — {detail}"


def _pair(start: str, end: str, station: str = "build") -> list[str]:
    return [_event(start, "spawn", station), _event(end, "finish", station)]


def _runlog(root: Path, name: str, *lines: str) -> Path:
    """Write a run log of whole event lines, under the home's title."""
    stem = name.removesuffix(".md")
    return _put(root, f".minions/runs/{name}", f"# Ship run {stem}\n\n{_lines(*lines)}")


def _good(root: Path) -> Path:
    return _runlog(root, "20261105-100000.md", *_pair("10:00:00", "10:30:00"))


def _at(root: Path) -> list[str]:
    version = run.Version(root, "0001-x", "a", "b")
    return [event.at.strftime(_DAY) for event in version.events]


def _env(change: str = "0001-x", **named: str) -> dict[str, str]:
    given = {"MF_METRICS_CHANGE": change, "MF_METRICS_BASE": "a"}
    return given | {"MF_METRICS_HEAD": "b"} | named


def _read(root: Path, metric: str, change: str = "0001-x", **named: str) -> object:
    """Return one metric of a version: its number, `gap: <why>`, or the error's name."""
    try:
        return run.measure(root, [metric], _env(change, **named))
    except run.Gap as gap:
        return f"gap: {gap}"
    except (OSError, ValueError) as error:
        return type(error).__name__


def _pretty(error: Exception, root: Path) -> str:
    return f"raises {type(error).__name__}: {error}".replace(str(root), "<P>")


def _shaped(root: Path, name: str, kind: str, good: str, big: str = "") -> None:
    """Plant what a state file can be: nothing, a folder, a link, a pipe, bad bytes."""
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    match kind:
        case "missing":
            pass
        case "folder":
            path.mkdir()
        case "dangling":
            path.symlink_to(root / "nowhere.txt")
        case "link":
            target = _put(root, "elsewhere.txt", good)
            path.symlink_to(target)
        case "fifo":
            os.mkfifo(path)
        case "bad-byte":
            path.write_bytes(b"\xff\xfe")
        case "empty":
            path.write_text("")
        case "big":
            path.write_text(big, encoding="utf-8")
        case _:
            raise AssertionError(kind)


_CHILD = """
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('run', sys.argv[1])
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)
run.PRICES = Path(sys.argv[3])
version = run.Version(Path(sys.argv[2]), '0001-x', 'a', 'b')
print(len(version.events), version.spent(('converge',)))
"""


def _hangs(code: str, *args: object, timeout: float) -> bool:
    """Run `code` in a child and return whether it was still blocked at `timeout`."""
    argv = [sys.executable, "-c", code, *map(str, args)]
    try:
        subprocess.run(argv, capture_output=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        return True
    return False


# ---- slice R: the run log -----------------------------------------------------


def test_clock_stepping_back_under_12h_is_no_midnight(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _runlog(root, "20261105-100000.md", *_pair("10:00:00", "09:59:00"))

    assert _at(root) == ["05 10:00:00", "06 09:59:00"]
    assert _read(root, "build-minutes") == 1439.0


def test_clock_stepping_back_11h_and_a_second_is_no_midnight(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _runlog(root, "20261105-100000.md", *_pair("12:00:00", "00:59:59"))

    assert _at(root) == ["05 12:00:00", "06 00:59:59"]
    assert _read(root, "build-minutes") == 780.0


def test_clock_stepping_back_exactly_12h_is_no_midnight(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _runlog(root, "20261105-100000.md", *_pair("12:00:00", "00:00:00"))

    assert _at(root) == ["05 12:00:00", "06 00:00:00"]
    assert _read(root, "build-minutes") == 720.0


def test_a_clock_stepping_back_over_12h_is_a_midnight(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _runlog(root, "20261105-100000.md", *_pair("12:00:01", "00:00:00"))
    assert _at(root) == ["05 12:00:01", "06 00:00:00"]

    _runlog(root, "20261105-100000.md", *_pair("23:59:00", "00:01:00"))
    assert _read(root, "build-minutes") == 2.0

    _runlog(
        root,
        "20261105-100000.md",
        _event("23:59:00", "note", "a"),
        _event("00:01:00", "note", "b"),
        _event("13:00:00", "note", "c"),
    )
    assert _at(root) == ["05 23:59:00", "06 00:01:00", "06 13:00:00"]


def test_first_event_clock_before_the_log_name_stays_on_the_name_day(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    _runlog(root, "20261105-230000.md", *_pair("10:00:00", "10:30:00"))

    assert _at(root) == ["06 10:00:00", "06 10:30:00"]
    assert _read(root, "build-minutes") == 30.0
    assert _read(root, "wait-minutes") == 0.0


def test_logs_are_read_oldest_first_by_stamp_and_number(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    names = ["", "-10", "-3", "-11", "-9", "-2"]
    for suffix in names:
        stem = f"20261105-000000{suffix}"
        _runlog(root, f"{stem}.md", _event("10:00:00", "note", stem))
    version = run.Version(root, "0001-x", "a", "b")
    assert [e.stamp for e in version.events] == [
        f"20261105-000000{suffix}" for suffix in ("", "-2", "-3", "-9", "-10", "-11")
    ]

    other = _repo(tmp_path / "other")
    for stem in (
        "20261105-100000",
        "20261105-090000-2",
        "20261104-235959-3",
        "20261105-090000",
    ):
        _runlog(other, f"{stem}.md", _event("10:00:00", "note", stem))
    version = run.Version(other, "0001-x", "a", "b")
    assert [e.stamp for e in version.events] == [
        "20261104-235959-3",
        "20261105-090000",
        "20261105-090000-2",
        "20261105-100000",
    ]


def test_only_a_file_named_for_a_stamp_is_a_log(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _good(root)
    odd = _event("11:00:00", "spawn", "build")
    for name in (
        "20261106-100000.txt",
        "20261106-100000",
        "20261107-100000.md.bak",
        "x20261108-100000.md",
        "20261109-100000x.md",
        "20261110-100000-2x.md",
        "notes.md",
    ):
        _put(root, f".minions/runs/{name}", _lines(odd))

    assert _at(root) == ["05 10:00:00", "05 10:30:00"]


def test_a_log_name_with_hour_25_is_read_the_time_part_is_unused(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    _runlog(root, "20261105-250000.md", *_pair("10:00:00", "10:30:00"))

    with pytest.raises(run.Gap, match="no run log names 0001-x"):
        _at(root)


def test_a_link_to_a_regular_file_is_followed(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _good(root)
    elsewhere = _runlog(tmp_path / "elsewhere", "x.md", *_pair("11:00:00", "11:30:00"))
    (root / ".minions/runs/20261106-100000.md").symlink_to(elsewhere)

    assert _at(root) == ["05 10:00:00", "05 10:30:00"]


def test_the_runs_folder_may_itself_be_a_link(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _good(tmp_path / "real")
    (root / ".minions").mkdir()
    (root / ".minions/runs").symlink_to(tmp_path / "real/.minions/runs")

    assert _at(root) == ["05 10:00:00", "05 10:30:00"]


def test_an_empty_log_and_one_of_bad_bytes_add_no_event(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _good(root)
    _put(root, ".minions/runs/20261106-100000.md", "")
    _put(root, ".minions/runs/20261107-100000.md", b"\xff\xfe")

    assert _at(root) == ["05 10:00:00", "05 10:30:00"]


def test_a_log_over_the_bound_is_read_whole(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _runlog(
        root,
        "20261105-100000.md",
        *_pair("10:00:00", "10:30:00"),
        "x" * 300_000,
        *_pair("11:00:00", "11:30:00"),
    )

    assert _at(root) == ["05 10:00:00", "05 10:30:00", "05 11:00:00", "05 11:30:00"]


def test_crlf_line_ends_leave_no_carriage_return_in_a_detail(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    text = "\r\n".join(_pair("10:00:00", "10:30:00")) + "\r\n"
    _put(root, ".minions/runs/20261105-100000.md", text.encode())

    version = run.Version(root, "0001-x", "a", "b")
    assert [e.detail for e in version.events] == ["build", "build"]
    assert _read(root, "build-minutes") == 30.0


def test_an_event_name_with_a_hyphen_or_a_space(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _runlog(
        root,
        "20261105-100000.md",
        _event("10:00:00", "some-name", "a"),
        _event("10:01:00", "converge skipped", "b"),
        _event("10:02:00", "halt", "c"),
    )

    version = run.Version(root, "0001-x", "a", "b")
    assert [e.name for e in version.events] == ["some-name", "converge skipped", "halt"]


def test_a_clock_must_open_the_line(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _runlog(
        root,
        "20261105-100000.md",
        _event("10:00:00", "spawn", "build"),
        "note 10:00:00 · 0001-x · halt — build check fail",
    )
    version = run.Version(root, "0001-x", "a", "b")
    assert version.halts("build") == 0

    halted = _event("10:01:00", "halt", "build check fail").encode()
    again = _event("10:02:00", "halt", "build check fail").encode()
    _put(root, ".minions/runs/20261106-100000.md", b"\xff\xfe" + halted + b"\n")
    _put(root, ".minions/runs/20261107-100000.md", b"x\xff" + again + b"\n")
    assert run.Version(root, "0001-x", "a", "b").halts("build") == 0


@pytest.mark.parametrize("separator", [" ", "\x0b"])
def test_a_line_break_that_is_no_newline_joins_two_events(
    tmp_path: Path, separator: str
) -> None:
    root = _repo(tmp_path)
    joined = _event("10:00:00", "spawn", "build")
    joined += separator + _event("10:30:00", "finish", "build")
    _runlog(root, "20261105-100000.md", joined)

    version = run.Version(root, "0001-x", "a", "b")
    assert [(e.name, e.detail) for e in version.events] == [
        ("spawn", "build" + separator + _event("10:30:00", "finish", "build"))
    ]
    assert version.spawns == []
    assert version.minutes("build") == 0


@pytest.mark.parametrize(
    ("detail", "named"),
    [
        ("", False),
        ("versions", False),
        ("versions none", False),
        ("versions 0001-xy", False),
        ("executor c · mf v1", False),
        ("versions 0002-y · 0001-x", False),
        ("versions 0001-x", True),
        ("versions a 0001-x b", True),
        ("versions 0002-y 0001-x", True),
        ("executor c · versions 0001-x · mf v1", True),
    ],
)
def test_a_start_line_names_the_versions_of_its_versions_detail(
    tmp_path: Path, detail: str, named: bool
) -> None:
    root = _repo(tmp_path)
    _runlog(
        root,
        "20261105-100000.md",
        _event("10:00:00", "note", "a"),
        _event("10:01:00", "start", detail, who="run"),
    )

    version = run.Version(root, "0001-x", "a", "b")
    assert ("start" in [e.name for e in version.events]) is named


def test_a_run_line_names_a_version_by_its_colon_prefix(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    details = [
        "0001-xy: converge",
        "0001-x converge",
        "x0001-x: converge",
        "0001-x: converge",
    ]
    _runlog(
        root,
        "20261105-100000.md",
        *(_event(f"10:0{n}:00", "rejoin", d, who="run") for n, d in enumerate(details)),
    )

    version = run.Version(root, "0001-x", "a", "b")
    assert [e.detail for e in version.events] == ["0001-x: converge"]


def test_a_spawn_is_kept_for_a_station_or_a_checker_of_the_converge(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    stations = [
        "probe-codex",
        "build",
        "converge",
        "integrate",
        "release",
        "rescue",
        "supervise",
        "other",
    ]
    _runlog(
        root,
        "20261105-100000.md",
        *(_event(f"10:0{n}:00", "spawn", s) for n, s in enumerate(stations)),
    )
    version = run.Version(root, "0001-x", "a", "b")
    assert [s.station for s in version.spawns] == [
        "build",
        "converge",
        "integrate",
        "release",
        "rescue",
        "supervise",
    ]

    kept = ["converge-conformance", "converge-shadow-adversarial"]
    kept += ["converge-fix-r2", "converge-fix-r10"]
    dropped = ["converge-fix-r2-x", "converge-fix-r", "converge-conformance-x"]
    dropped += ["converge-fix-rx"]
    _runlog(
        root,
        "20261105-100000.md",
        *(_event(f"10:0{n}:00", "spawn", s) for n, s in enumerate(kept + dropped)),
    )
    version = run.Version(root, "0001-x", "a", "b")
    assert [s.station for s in version.spawns] == kept


def test_a_spawn_is_closed_by_the_next_finish_of_its_station(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _runlog(
        root,
        "20261105-100000.md",
        _event("10:00:00", "spawn", "converge · script"),
        _event("10:01:00", "spawn", "converge"),
        _event("10:02:00", "finish", "converge"),
        _event("10:03:00", "finish", "converge"),
        _event("10:04:00", "finish", "converge"),
        _event("10:05:00", "spawn", "build"),
    )

    version = run.Version(root, "0001-x", "a", "b")
    assert [(s.station, s.n, s.end is not None, s.script) for s in version.spawns] == [
        ("converge", 1, True, True),
        ("converge", 2, True, False),
        ("build", 1, False, False),
    ]
    assert _read(root, "build-minutes") == "gap: a build spawn with no finish"


def test_a_converge_after_the_first_integrate_is_a_catch_up(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _runlog(
        root,
        "20261105-100000.md",
        _event("10:00:00", "spawn", "integrate"),
        _event("10:00:00", "spawn", "converge"),
        _event("10:05:00", "finish", "converge"),
        _event("10:06:00", "finish", "integrate"),
        _event("10:10:00", "spawn", "converge"),
        _event("10:12:00", "finish", "converge"),
    )

    assert _read(root, "converge-minutes") == 5.0
    assert _read(root, "catch-up-minutes") == 2.0
    assert _read(root, "integrate-minutes") == 6.0


def test_a_halt_of_the_build_is_counted_by_its_words(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    counted = [
        "build check fail — x",
        "build worker exit 1",
        "build timed out after 600s",
        "build timed out",
    ]
    ignored = [
        "build check failure",
        "build timed outside",
        "rescue diagnosed — a build check fail",
        "xbuild check fail",
        "converge check fail",
        "build",
    ]
    _runlog(
        root,
        "20261105-100000.md",
        *(_event(f"10:{n:02d}:00", "halt", d) for n, d in enumerate(counted + ignored)),
    )

    assert _read(root, "halts-build") == 4
    assert _read(root, "halts-converge") == 1

    _runlog(
        root,
        "20261105-100000.md",
        _event("10:00:00", "halt", "build check fail"),
        _event("10:01:00", "halt", "0001-x: build check fail", who="run"),
        _event("10:02:00", "note", "build check fail"),
    )
    assert _read(root, "halts-build") == 1


def test_a_wait_ends_at_a_rejoin(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    halt = _event("10:00:00", "halt", "build check fail")
    _runlog(
        root,
        "20261105-100000.md",
        halt,
        _event("10:05:00", "halt", "build check fail"),
        _event("10:10:00", "rejoin", "0001-x: build", who="run"),
    )
    assert _read(root, "wait-minutes") == 10.0

    rejoin = _event("10:10:00", "rejoin", "0001-x: build", who="run")
    run_spawn = _event("10:02:00", "spawn", "0001-x: build", who="run")
    _runlog(root, "20261105-100000.md", halt, run_spawn, rejoin)
    assert _read(root, "wait-minutes") == 10.0

    _runlog(
        root, "20261105-100000.md", halt, _event("10:02:00", "spawn", "build"), rejoin
    )
    assert _read(root, "wait-minutes") == 0.0


@pytest.mark.parametrize("tail", ["automatic", "automatically", "automatic · R1"])
def test_an_automatic_grant_ends_a_wait_uncounted(tmp_path: Path, tail: str) -> None:
    root = _repo(tmp_path)
    _runlog(
        root,
        "20261105-100000.md",
        _event("10:00:00", "halt", "build check fail"),
        _event("10:05:00", "grant", f"0001-x: {tail}", who="run"),
        _event("10:10:00", "rejoin", "0001-x: build", who="run"),
    )

    assert _read(root, "wait-minutes") == 0.0


def test_a_grant_or_a_start_answers_a_halt_and_a_still_halted_rejoin_does_not(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    halt = _event("10:00:00", "halt", "build check fail")
    grant = _event("10:07:00", "grant", "0001-x: one more round", who="run")
    _runlog(root, "20261105-100000.md", halt, grant)
    assert _read(root, "wait-minutes") == 7.0

    start = _event("10:07:30", "start", "versions 0001-x", who="run")
    _runlog(root, "20261105-100000.md", halt, start)
    assert _read(root, "wait-minutes") == 7.5

    still = _event("10:07:00", "rejoin", "0001-x: still halted", who="run")
    _runlog(root, "20261105-100000.md", halt, still)
    assert _read(root, "wait-minutes") == 0.0


def test_the_minutes_after_a_wait_run_to_the_next_event_of_its_log(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    _runlog(
        root,
        "20261105-100000.md",
        _event("10:00:00", "wait", "0001-x: after 0002-y", who="run"),
        _event("10:05:00", "spawn", "build"),
        _event("10:10:00", "wait", "after 0002-y"),
        _event("10:12:00", "spawn", "build"),
    )

    assert _read(root, "after-wait-minutes") == 2.0


@pytest.mark.slow
def test_a_fifo_at_a_log_name_hangs_the_read(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _good(root)
    os.mkfifo(root / ".minions/runs/20261106-090000.md")
    prices = tmp_path / "prices.toml"

    assert not _hangs(_CHILD, _RUN, root, prices, timeout=8)


def test_a_folder_named_like_a_log_in_the_runs_folder_is_not_a_log_by_name_only(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    _good(root)
    (root / ".minions/runs/20261106-090000.md").mkdir()

    assert _at(root) == ["05 10:00:00", "05 10:30:00"]


def test_a_dangling_link_at_a_log_name_raises_filenotfound(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _good(root)
    (root / ".minions/runs/20261106-090000.md").symlink_to(tmp_path / "nowhere")

    assert _at(root) == ["05 10:00:00", "05 10:30:00"]


@pytest.mark.parametrize("kind", ["missing", "file", "dangling"])
def test_no_runs_folder_is_a_gap(tmp_path: Path, kind: str) -> None:
    root = _repo(tmp_path)
    (root / ".minions").mkdir()
    if kind == "file":
        (root / ".minions/runs").write_text("x")
    if kind == "dangling":
        (root / ".minions/runs").symlink_to(tmp_path / "nowhere")

    version = run.Version(root, "0001-x", "a", "b")
    with pytest.raises(run.Gap) as gap:
        version.events  # noqa: B018
    assert str(gap.value) == "no run log names 0001-x"


def test_a_clock_of_25_hours_in_a_line_raises_valueerror(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _runlog(root, "20261105-100000.md", _event("25:00:00", "spawn", "build"))

    version = run.Version(root, "0001-x", "a", "b")
    with pytest.raises(run.Gap, match="no run log names 0001-x"):
        version.events  # noqa: B018


def test_measure_reads_a_bad_clock_as_a_valueerror_not_a_gap(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _runlog(root, "20261105-100000.md", _event("25:00:00", "spawn", "build"))

    with pytest.raises(run.Gap, match="no run log names 0001-x"):
        run.measure(root, ["build-minutes"], _env())


def test_a_log_name_with_month_13_raises_valueerror_for_every_version(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    _good(root)
    _runlog(root, "20261399-250000.md", *_pair("10:00:00", "10:30:00"))

    assert _at(root) == ["05 10:00:00", "05 10:30:00"]
    assert _read(root, "build-minutes", "0002-y") == "gap: no run log names 0002-y"


# ---- slice S: the status log --------------------------------------------------

_SPENT = statuslog.spent(("claude", "claude-sonnet-5-5", "high"), 100, False)


def _round(n: int, clock: str = "10:00:00") -> str:
    return f"{clock} · round {n} · verify — gate exit 0"


def _verdicts(
    count: int | str,
    role: str = "conformance",
    word: str = "changes-requested",
    round_: int = 1,
) -> str:
    line = statuslog.verdicts_line(role, word, 0, _SPENT)
    line = line.replace("open_blocking 0", f"open_blocking {count}")
    return f"10:00:00 · round {round_} · {line}"


def _heading(number: int, mark: str | None = None) -> str:
    return f"## Run {number} — 2026-11-05 10:00" + (f" · {mark}" if mark else "")


def _status(*runs: tuple[str, list[str]]) -> str:
    text = statuslog.title("0001-x") + "\n"
    for heading, lines in runs:
        text += f"\n{heading}\n{_lines(*lines)}"
    return text


def _status_reads(root: Path) -> list[object]:
    metrics = ("converge-rounds", "blockers-round-1", "grants", "amend-rounds")
    return [_read(root, metric) for metric in metrics]


_HEADINGS = {
    "trailing-blanks": (
        [(_heading(2, "catch-up") + "   ", [_round(3)]), (_heading(1), [_round(1)])],
        [1, _GAP_BLOCKERS, 0, 0],
    ),
    "catch-up": (
        [(_heading(2, "catch-up"), [_round(5)]), (_heading(1), [_round(2)])],
        [2, _GAP_BLOCKERS, 0, 0],
    ),
    "grant-and-amend": (
        [(_heading(3, "grant"), [_round(2)]), (_heading(2, "amend"), [_round(3)])],
        [2, _GAP_BLOCKERS, 1, 1],
    ),
    "ten-beats-nine": (
        [(_heading(1), [_round(10), _round(9)])],
        [10, _GAP_BLOCKERS, 0, 0],
    ),
    "two-digit-only": ([(_heading(1), [_round(12)])], [12, _GAP_BLOCKERS, 0, 0]),
    "empty": ([], [_GAP_ROUND, _GAP_BLOCKERS, 0, 0]),
    "no-runs": ([("", [_round(3)])], [_GAP_ROUND, _GAP_BLOCKERS, 0, 0]),
    "odd-runner-heading": (
        [("## Runner", [_round(3)])],
        [3, _GAP_BLOCKERS, 0, 0],
    ),
    "odd-run-alone-heading": (
        [("## Run", [_round(3)]), (_heading(1), [_round(2)])],
        [3, _GAP_BLOCKERS, 0, 0],
    ),
    "odd-second-grant-mark": (
        [("## Run 2 · a · grant", [_round(3)])],
        [3, _GAP_BLOCKERS, 0, 0],
    ),
    "odd-second-amend-mark": (
        [("## Run 2 · a · amend", [_round(3)])],
        [3, _GAP_BLOCKERS, 0, 0],
    ),
    "odd-amend-in-the-middle": (
        [("## Run 2 · amend · a", [_round(3)])],
        [3, _GAP_BLOCKERS, 0, 0],
    ),
    "odd-catch-up-no-dot": (
        [("## Run 2 catch-up", [_round(5)]), (_heading(1), [_round(2)])],
        [5, _GAP_BLOCKERS, 0, 0],
    ),
    "odd-grant-no-dot": (
        [("## Run 3 · grant", [_round(1)]), ("## Run 2 grant", [_round(1)])],
        [1, _GAP_BLOCKERS, 1, 0],
    ),
    "odd-amend-no-dot": (
        [("## Run 3 · amend", [_round(4)]), ("## Run 2 amend", [_round(1)])],
        [1, _GAP_BLOCKERS, 0, 1],
    ),
    "odd-grant-then-amend": (
        [("## Run 4 · grant · amend", [_round(3)])],
        [3, _GAP_BLOCKERS, 0, 0],
    ),
    "odd-doubled-round-on-a-line": (
        [(_heading(1), [_round(3) + " · round 3 · x"])],
        [3, _GAP_BLOCKERS, 0, 0],
    ),
    "odd-bare-fragment-no-clock": (
        [(_heading(1), ["· round 3 ·"])],
        [_GAP_ROUND, _GAP_BLOCKERS, 0, 0],
    ),
}


@pytest.mark.parametrize("key", list(_HEADINGS))
def test_status_log_headings_and_marks(tmp_path: Path, key: str) -> None:
    root = _repo(tmp_path)
    runs, expected = _HEADINGS[key]
    text = statuslog.title("0001-x") + "\n" if key == "no-runs" else _status(*runs)
    if key == "no-runs":
        text += _lines(_round(3))
    _put(root, ".minions/changes/0001-x/status_log.md", text)

    assert _status_reads(root) == expected


def test_status_log_headings_and_marks_of_an_empty_and_a_title_only_file(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    for text in ("", statuslog.title("0001-x") + "\n"):
        _put(root, ".minions/changes/0001-x/status_log.md", text)
        assert _status_reads(root) == [_GAP_ROUND, _GAP_BLOCKERS, 0, 0]


def test_status_log_headings_and_marks_with_crlf(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    text = _status(
        (_heading(3, "grant"), [_round(2)]), (_heading(2, "amend"), [_round(3)])
    )
    path = ".minions/changes/0001-x/status_log.md"
    _put(root, path, text.replace("\n", "\r\n").encode())

    assert _status_reads(root) == [2, _GAP_BLOCKERS, 1, 1]


_BLOCKERS = {
    "today": ([(_heading(1), [_verdicts(2)])], 2),
    "two-digits": ([(_heading(1), [_verdicts(12)])], 12),
    "two-runs": ([(_heading(2), [_verdicts(5)]), (_heading(1), [_verdicts(2)])], 2),
    "two-lines": (
        [(_heading(1), [_verdicts(5), _verdicts(2, "adversarial", "clean")])],
        7,
    ),
    "round-2": ([(_heading(1), [_verdicts(4, round_=2)])], _GAP_BLOCKERS),
    "round-12": ([(_heading(1), [_verdicts(4, round_=12)])], _GAP_BLOCKERS),
    "r1-newer-r2-older": (
        [(_heading(2), [_verdicts(5)]), (_heading(1), [_verdicts(3, round_=2)])],
        5,
    ),
    "halted-run-between": (
        [
            (_heading(3), ["10:00:00 · round 1 · halt — the gate is red"]),
            (_heading(2), [_verdicts(4)]),
            (_heading(1), [_verdicts(7)]),
        ],
        7,
    ),
    "odd-colon-form": (
        [(_heading(1), [_verdicts(2).replace("open_blocking 2", "open_blocking: 2")])],
        2,
    ),
    "odd-oldest-run-no-count": (
        [
            (_heading(2), [_verdicts(7)]),
            (_heading(1), ["10:00:00 · round 1 · verdicts — conformance clean"]),
        ],
        _GAP_BLOCKERS,
    ),
    "odd-no-count-no-spent-tail": (
        [(_heading(1), ["10:00:00 · round 1 · verdicts — conformance clean"])],
        _GAP_BLOCKERS,
    ),
    "odd-no-clock": (
        [(_heading(1), [_verdicts(7).removeprefix("10:00:00 · ")])],
        _GAP_BLOCKERS,
    ),
    "odd-two-counts-on-a-line": (
        [(_heading(1), [_verdicts(2) + " · open_blocking: 3"])],
        2,
    ),
    "odd-role-c-no-spent-tail": (
        [
            (
                _heading(1),
                [
                    "10:00:00 · round 1 · verdicts — c changes-requested"
                    " · open_blocking 4"
                ],
            )
        ],
        _GAP_BLOCKERS,
    ),
    "odd-no-verdict-word": (
        [
            (
                _heading(1),
                ["10:00:00 · round 1 · verdicts — conformance · open_blocking 4"],
            )
        ],
        4,
    ),
}


@pytest.mark.parametrize("key", list(_BLOCKERS))
def test_blockers_read_the_round_one_verdicts(tmp_path: Path, key: str) -> None:
    root = _repo(tmp_path)
    runs, expected = _BLOCKERS[key]
    _put(root, ".minions/changes/0001-x/status_log.md", _status(*runs))

    assert _read(root, "blockers-round-1") == expected


def test_blockers_read_the_round_one_verdicts_of_a_crlf_log(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    text = _status((_heading(1, "grant"), [_round(2), _verdicts(7)]))
    path = ".minions/changes/0001-x/status_log.md"
    _put(root, path, text.replace("\n", "\r\n").encode())

    assert _read(root, "blockers-round-1") == 7


_ROUNDS = _status((_heading(2, "grant"), [_round(6)]))
_STATUS_SHAPES = {
    "missing": [_GAP_STATUS, _GAP_STATUS],
    "folder": [_GAP_STATUS, _GAP_STATUS],
    "dangling": [_GAP_STATUS, _GAP_STATUS],
    "link": [_GAP_STATUS, _GAP_STATUS],
    "fifo": [_GAP_STATUS, _GAP_STATUS],
    "bad-byte": [_GAP_ROUND, 0],
    "empty": [_GAP_ROUND, 0],
    "big": [6, 1],
}


@pytest.mark.parametrize("kind", list(_STATUS_SHAPES))
def test_status_log_file_shapes(tmp_path: Path, kind: str) -> None:
    root = _repo(tmp_path)
    big = statuslog.title("0001-x") + "\n" + "x" * (_BOUND + 200) + "\n"
    big += _ROUNDS.removeprefix(statuslog.title("0001-x") + "\n")
    _shaped(root, ".minions/changes/0001-x/status_log.md", kind, _ROUNDS, big)

    reads = [_read(root, m) for m in ("converge-rounds", "grants")]
    assert reads == _STATUS_SHAPES[kind]


# ---- slice S: the findings ----------------------------------------------------


def _card(
    n: int = 1,
    priority: str | None = "high",
    verdict: str | None = "confirmed",
    title: str | None = None,
) -> str:
    lines = [
        f"- **{title or f'R{n} — a title'}**",
        "  - **Why it's a problem:** a harm.",
    ]
    if priority:
        lines.append(f"  - **Priority:** {priority}")
    if verdict:
        lines.append(f"  - **Verdict:** {verdict}")
    return _lines(*lines)


def _findings(body: str, refuted: str | None = "") -> str:
    tail = "" if refuted is None else f"\n## Refuted\n{refuted}"
    return f"# Conformance\n\n{body}{tail}"


def _findings_reads(root: Path, role: str = "conformance") -> list[object]:
    return [_read(root, f"{role}-confirmed"), _read(root, f"{role}-refuted")]


_GAP_BOTH = [_GAP_FINDINGS, _GAP_FINDINGS]
_TWO = "- a\n- b\n"
_FINDINGS: dict[str, tuple[str | bytes, list[object]]] = {
    "plain": (_findings(_card(), _TWO), [1, 2]),
    "deeper-heading": (
        _findings("", "- a\n### sub\n- b\n## X\n- c\n"),
        [0, 2],
    ),
    "odd-dashless-entry": (_findings("", "-a\n- b\n  - nested\n * c\n"), [0, 1]),
    "odd-verdict-only": (_findings(_card(priority=None)), [1, 0]),
    "odd-unanchored-priority": (
        _findings(
            _lines(
                "- **R1 — a title**",
                "  note - **Priority:** high",
                "  - **Verdict:** confirmed",
            )
        ),
        [1, 0],
    ),
    "no-blank-after-verdict": (
        _findings(_card().replace("Verdict:** confirmed", "Verdict:**confirmed")),
        [1, 0],
    ),
    "tab-after-verdict": (
        _findings(_card().replace("Verdict:** confirmed", "Verdict:**\tconfirmed")),
        [1, 0],
    ),
    "backtick-verdict": (_findings(_card(verdict="`confirmed`")), [1, 0]),
    "repeat-note": (_findings(_card(verdict="confirmed — repeat of 0012·R3")), [1, 0]),
    "odd-capital-Confirmed": (_findings(_card(verdict="Confirmed")), [1, 0]),
    "refuted-verdict": (_findings(_card(verdict="refuted")), [0, 0]),
    "odd-heading-between-priority-and-verdict": (
        _findings(
            _lines(
                "- **R1 — a title**",
                "  - **Priority:** high",
                "## H",
                "  - **Verdict:** confirmed",
            )
        ),
        [0, 0],
    ),
    "odd-h1-between-two-cards-fields": (
        _findings(
            _card()
            + _lines("# x", "  - **Priority:** high", "  - **Verdict:** confirmed")
        ),
        [1, 0],
    ),
    "heading-above-priority": (
        _findings(
            _lines("# t", "  - **Priority:** high", "  - **Verdict:** confirmed")
        ),
        [0, 0],
    ),
    "odd-refused-heading": (
        _findings(_card(), "- a\n").replace("Refuted", "Refused"),
        [1, 1],
    ),
    "odd-no-section": (_findings(_card(), None), _GAP_BOTH),
    "odd-heading-no-newline": (_findings(_card(), None) + "\n## Refuted", [1, 0]),
    "odd-no-space-heading": (_findings(_card()).replace("## ", "##"), _GAP_BOTH),
    "odd-h3-heading": (
        _findings(_card()).replace("## Refuted", "### Refuted"),
        _GAP_BOTH,
    ),
    "odd-empty-file": ("", _GAP_BOTH),
    "odd-bad-byte-first": (b"\xff\xfe## Refuted\n- a\n", _GAP_BOTH),
    "empty-section": (_findings(_card(), ""), [1, 0]),
    "empty-then-heading": (_findings(_card(), "## Next\n- c\n"), [1, 0]),
    "heading-with-text": (
        _findings(_card(), _TWO).replace("Refuted", "Refuted (3)"),
        [1, 2],
    ),
    "refuted-twice": (
        _findings(_card(), "- a\n- b\n\n## Refuted\n- c\n- d\n- e\n"),
        [1, 2],
    ),
    "card-after-refuted": (_findings(_card(), "- a\n" + _card(2)), [2, 2]),
    "card-after-next-heading": (
        _findings(_card(), "- a\n\n## Next\n" + _card(2)),
        [2, 1],
    ),
    "odd-priority-at-column-0": (
        _findings(
            _lines(
                "- **R1 — a title**",
                "- **Priority:** high",
                "  - **Verdict:** confirmed",
            )
        ),
        [0, 0],
    ),
    "no-priority": (
        _findings(
            _lines(
                "- **R1 — a title**",
                "  - **Why it's a problem:** a harm.",
                "  - **Verdict:** confirmed",
            )
        ),
        [1, 0],
    ),
    "dated-note": (
        _findings(_lines("- **2026-11-05 — a note**", "  a line of text")),
        [0, 0],
    ),
    "dated-note-with-fields": (
        _findings(_card(title="2026-11-05 — a note")),
        [1, 0],
    ),
    "odd-untitled-card": (_findings(_card(title="a")), [0, 0]),
    "crlf": (_findings(_card(), _TWO).replace("\n", "\r\n").encode(), [1, 2]),
    "bad-byte-in-section": (
        _findings(_card(), "- a\n").encode() + b"\xff\n- b\n",
        [1, 2],
    ),
    "two-cards": (_findings(_card() + _card(2)), [2, 0]),
}


@pytest.mark.parametrize("key", list(_FINDINGS))
def test_findings_cards_and_the_refuted_section(tmp_path: Path, key: str) -> None:
    root = _repo(tmp_path)
    text, expected = _FINDINGS[key]
    _put(root, ".minions/changes/0001-x/conformance.md", text)

    assert _findings_reads(root) == expected


def test_the_adversarial_file_is_read_by_the_adversarial_metrics(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    _put(
        root,
        ".minions/changes/0001-x/adversarial.md",
        _findings(_card() + _card(2), "- a\n- b\n- c\n"),
    )

    assert _findings_reads(root, "adversarial") == [2, 3]
    assert _findings_reads(root) == ["gap: no 0001-x/conformance.md"] * 2


_GOOD_FINDINGS = _findings(_card())
_FINDINGS_SHAPES = {
    "missing": ["gap: no 0001-x/conformance.md"] * 2,
    "folder": ["gap: no 0001-x/conformance.md"] * 2,
    "dangling": ["gap: no 0001-x/conformance.md"] * 2,
    "link": ["gap: no 0001-x/conformance.md"] * 2,
    "fifo": ["gap: no 0001-x/conformance.md"] * 2,
    "bad-byte": _GAP_BOTH,
    "empty": _GAP_BOTH,
    "big": [1, 1],
}


@pytest.mark.parametrize("kind", list(_FINDINGS_SHAPES))
def test_findings_file_shapes(tmp_path: Path, kind: str) -> None:
    root = _repo(tmp_path)
    big = "x" * (_BOUND + 200) + "\n" + _findings(_card(), "- a\n")
    path = ".minions/changes/0001-x/conformance.md"
    _shaped(root, path, kind, _findings(_card(), "- a\n"), big)

    assert _findings_reads(root) == _FINDINGS_SHAPES[kind]


# ---- slice S: build.done ------------------------------------------------------


@pytest.fixture(scope="module")
def chain(tmp_path_factory: pytest.TempPathFactory) -> dict[str, object]:
    """A repository of a base and three commits: the version's two, then a fix."""
    root = _repo(tmp_path_factory.mktemp("chain"))
    commits = []
    for subject in ("base", "feat(0001-x): one", "feat(0001-x): two", "fix(0001-x)"):
        _git(root, "commit", "-q", "--allow-empty", "-m", subject)
        commits.append(_git(root, "rev-parse", "HEAD"))
    return {"root": root, "shas": commits}


def _commits(chain: dict[str, object], text: str | bytes) -> list[object]:
    """Write `build.done` and return the build and fix commits it counts."""
    root, shas = chain["root"], chain["shas"]
    assert isinstance(root, Path) and isinstance(shas, list)
    _planted(root, lambda: _put(root, ".minions/changes/0001-x/build.done", text))
    env = {"MF_METRICS_BASE": shas[0], "MF_METRICS_HEAD": shas[3]}
    return [_read(root, m, **env) for m in ("build-commits", "fix-commits")]


def _planted(root: Path, plant: Callable[[], object]) -> None:
    """Empty the change's run folder, then plant the file under test."""
    folder = root / ".minions/changes/0001-x"
    if folder.exists():
        for child in folder.iterdir():
            if child.is_dir() and not child.is_symlink():
                child.rmdir()
            else:
                child.unlink()
    plant()


_PAD = "pad\n"


def _done(sha: str, tail: str = "simplify: lean already\n") -> str:
    return f"head: {sha}\n{tail}"


def _done_cases(shas: list[str]) -> dict[str, tuple[str | bytes, list[object]]]:
    built, tip, first = shas[2], shas[3], shas[1]
    gap = [_GAP_HEAD, _GAP_HEAD]
    return {
        "7": (_done(built[:7]), [2, 1]),
        "8": (_done(built[:8]), [2, 1]),
        "40": (_done(built), [2, 1]),
        "odd-6-hex": (_done(built[:6]), gap),
        "odd-41-hex": (_done(built + "0"), gap),
        "odd-uppercase": (_done(built.upper()), gap),
        "odd-trailing-spaces": (f"head: {built}   \n", [2, 1]),
        "odd-trailing-tab": (f"head: {built}\t\n", [2, 1]),
        "odd-no-newline": (f"head: {built}", [2, 1]),
        "odd-crlf": (f"head: {built}\r\n", [2, 1]),
        "odd-text-after": (f"head: {built} extra\n", gap),
        "odd-indented": (f"  head: {built}\n", gap),
        "odd-two-blanks": (f"head:  {built}\n", [2, 1]),
        "odd-tab-after-colon": (f"head:\t{built}\n", [2, 1]),
        "odd-no-blank": (f"head:{built}\n", [2, 1]),
        "empty": ("", gap),
        "odd-over-65536-bytes": (_done(built, _PAD * 17_000), gap),
        "odd-over-262144-bytes": (_done(built, _PAD * 66_000), gap),
        "odd-head-after-65536-bytes": (_PAD * 17_000 + _done(built), gap),
        "first-head-wins": (f"head: {first}\nhead: {built}\n", gap),
        "after-other-line": (f"simplify: lean already\nhead: {built}\n", [2, 1]),
        "head-at-tip": (_done(tip), [3, 0]),
        "not-in-history": (
            _done("0" * 40),
            ["gap: 0001-x/build.done's head is not in the version's history"] * 2,
        ),
    }


_DONE_KEYS = list(_done_cases(["0" * 40] * 4))


@pytest.mark.parametrize("key", _DONE_KEYS)
def test_build_done_head(chain: dict[str, object], key: str) -> None:
    shas = chain["shas"]
    assert isinstance(shas, list)
    text, expected = _done_cases(shas)[key]

    assert _commits(chain, text) == expected


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        ("missing", [_GAP_HEAD] * 2),
        ("folder", [_GAP_HEAD] * 2),
        ("dangling", [_GAP_HEAD] * 2),
        ("link", [_GAP_HEAD] * 2),
        ("fifo", [_GAP_HEAD] * 2),
        ("bad-byte", [_GAP_HEAD] * 2),
        ("empty", [_GAP_HEAD] * 2),
        ("big", [_GAP_HEAD] * 2),
    ],
)
def test_build_done_file_shapes(
    chain: dict[str, object], kind: str, expected: list[object]
) -> None:
    root, shas = chain["root"], chain["shas"]
    assert isinstance(root, Path) and isinstance(shas, list)
    good = _done(shas[2])
    big = _PAD * 66_000 + good

    def plant() -> None:
        _shaped(root, ".minions/changes/0001-x/build.done", kind, good, big)

    _planted(root, plant)
    env = {"MF_METRICS_BASE": shas[0], "MF_METRICS_HEAD": shas[3]}
    reads = [_read(root, m, **env) for m in ("build-commits", "fix-commits")]
    assert reads == expected


# ---- slice S: the proposal ----------------------------------------------------


def _proposal(root: Path, text: str | bytes, where: str = "") -> None:
    name = f"openspec/changes/{where}0001-x/proposal.md"
    _put(root, name, text)


def _front(line: str) -> str:
    return f"---\nbump: minor\n{line}\n---\n\n# A change\n"


_PAID = {
    "comma-no-space": (_front("debt: [0023·R1,0023·R2]"), 2),
    "spaced-commas": (_front("debt: [0023·R1, 0023·R2]"), 2),
    "empty-item": (_front("debt: [A,,B]"), 3),
    "no-blank-after-colon": (_front("debt:[A]"), 1),
    "blanks-after-colon": (_front("debt:   [A]"), 1),
    "empty-list": (_front("debt: []"), 1),
    "blank-list": (_front("debt: [ ]"), 1),
    "backlog": (_front("backlog: [A]"), 1),
    "both-keys": (_front("debt: [A]\nbacklog: [B, C]"), 1),
    "indented": (_front("  debt: [A]"), 0),
    "in-body": (_front("") + "\ndebt: [A]\n", 1),
    "bare-list": (_front("debt: A"), 0),
    "backlog-bare": (_front("backlog: A"), 0),
    "empty-key": (_front("debt:"), 0),
    "none": (_front("debt: none"), 0),
    "no-line": (_front(""), 0),
    "crlf": (_front("debt: [A, B]").replace("\n", "\r\n"), 2),
    "two-lists": (_front("debt: [A], [B]"), 2),
    "note-after": (_front("debt: [A] a note"), 1),
}


@pytest.mark.parametrize("key", list(_PAID))
def test_the_proposals_debt_list_is_counted_by_its_line(
    tmp_path: Path, key: str
) -> None:
    root = _repo(tmp_path)
    text, expected = _PAID[key]
    _proposal(root, text)

    assert _read(root, "debt-paid") == expected


def test_the_proposal_is_read_from_the_change_or_its_archive(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _proposal(root, _front("debt: [A, B, C]"), "archive/")
    assert _read(root, "debt-paid") == 3

    _proposal(root, _front("debt: [A]"))
    assert _read(root, "debt-paid") == 1

    live = root / "openspec/changes/0001-x/proposal.md"
    live.unlink()
    live.mkdir()
    assert _read(root, "debt-paid") == 3


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        ("missing", "gap: no proposal.md for 0001-x"),
        ("dangling", "gap: no proposal.md for 0001-x"),
        ("fifo", "gap: no proposal.md for 0001-x"),
        ("link", 2),
        ("bad-byte", "UnicodeDecodeError"),
        ("big", 2),
    ],
)
def test_the_proposal_file_shapes(tmp_path: Path, kind: str, expected: object) -> None:
    root = _repo(tmp_path)
    good = _front("debt: [A, B]")
    big = "x" * (_BOUND + 200) + "\n" + good
    path = "openspec/changes/0001-x/proposal.md"
    _shaped(root, path, kind, good, big)

    assert _read(root, "debt-paid") == expected


def _escape_card(repeat: str | None, verdict: str = "confirmed") -> str:
    note = f"{verdict} — repeat of {repeat}" if repeat else verdict
    return _card(verdict=note)


def _setup_escape(
    root: Path, change: str, debt: str, conformance: str, adversarial: str
) -> None:
    _put(
        root,
        f"openspec/changes/{change}/proposal.md",
        _front(f"debt: {debt}"),
    )
    folder = f".minions/changes/{change}"
    _put(root, f"{folder}/conformance.md", _findings(conformance))
    _put(root, f"{folder}/adversarial.md", _findings(adversarial))


@pytest.mark.parametrize(
    ("conformance", "adversarial", "debt", "change", "expected"),
    [
        (_escape_card("0003·R1"), "", "[]", "0005-a", 1),
        ("", _escape_card("0003·R1"), "[]", "0005-a", 1),
        (_escape_card("0003·R1"), _escape_card("0003·R1"), "[]", "0005-a", 2),
        (_escape_card("0003·R1"), "", "[0003·R1]", "0005-a", 0),
        (
            _escape_card("0003·R2") + _escape_card("0004·R1"),
            "",
            "[0003·R2, 0004·R1]",
            "0005-a",
            0,
        ),
        (
            _escape_card("0003·R2") + _escape_card("0004·R1"),
            "",
            "[0003·R2]",
            "0005-a",
            1,
        ),
        (_escape_card("0007·R1"), "", "[]", "0005-a", 0),
        (_escape_card("0005·R1"), "", "[]", "0005-a", 0),
        (
            _lines(
                "- **R1 — a title**",
                "  - **Priority:** high",
                "  - **Verdict:** confirmed — repeat of 0003·R1",
                "  - **Note:** repeat of 0002·R4",
            ),
            "",
            "[]",
            "0005-a",
            1,
        ),
        (_escape_card("0020·R1"), "", "[]", "0005-a1", 0),
    ],
    ids=[
        "conformance-repeat",
        "adversarial-repeat",
        "both-roles",
        "paid-repeat",
        "paid-both",
        "paid-one-of-two",
        "later-change",
        "own-change",
        "odd-two-repeats-on-one-card",
        "id-with-a-suffix",
    ],
)
def test_an_escape_is_a_repeat_of_an_earlier_card_the_change_does_not_pay(
    tmp_path: Path,
    conformance: str,
    adversarial: str,
    debt: str,
    change: str,
    expected: int,
) -> None:
    root = _repo(tmp_path)
    _setup_escape(root, change, debt, conformance, adversarial)

    assert _read(root, "escapes", change) == expected


def test_a_change_with_no_proposal_has_no_escapes(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    folder = ".minions/changes/alpha"
    _put(root, f"{folder}/conformance.md", _findings(_escape_card("0003·R1")))
    _put(root, f"{folder}/adversarial.md", _findings(""))

    assert _read(root, "escapes", "alpha") == "gap: no proposal.md for alpha"


# ---- slice S group E: the old eras, from disk ---------------------------------

_ERA_E5 = (
    _verdicts(0, "adversarial", "clean").replace("tokens 100", "tokens 2971705"),
    _verdicts(1, "conformance").replace("tokens 100", "tokens 5852914"),
)
_ERAS = {
    "E1": (
        [
            "12:39:00 · round 1 · verdicts — review changes-requested"
            " · open_blocking 2 (R1, R2) · 7 commits 29 files · stale-claim pass ran",
            "12:39:00 · round 1 · verdicts — security clean · open_blocking 0"
            " · 7 commits 29 files (matches freeze)",
        ],
        [2, 1, [None, None]],
    ),
    "E2": (
        [
            "12:39:00 · round 1 · verdicts — security clean · open_blocking 0"
            " · executor claude · model default · effort default · tokens 167263",
            "12:39:00 · round 1 · verdicts — review changes-requested"
            " · open_blocking 2 · executor claude · model default · effort default"
            " · tokens 341901",
        ],
        [2, 1, [None, None]],
    ),
    "E3": (
        [
            "16:56:08 · round 1 · verdicts — review verdict: changes-requested;"
            " open_blocking: 2 (R1, R2); scope 8 commits, 43 files;"
        ],
        [2, 1, [None]],
    ),
    "E4": (
        ["12:39:01 · round 3 · verify — gate exit 0 · round 3 · fe3f5e6..c82f91b"],
        [_GAP_BLOCKERS, 3, [None]],
    ),
    "E4-with-E2": (
        [
            "12:39:01 · round 3 · verify — gate exit 0 · round 3 · fe3f5e6..c82f91b",
            "12:39:00 · round 1 · verdicts — review changes-requested"
            " · open_blocking 2 · executor claude · model default · effort default"
            " · tokens 341901",
        ],
        [2, 3, [None, None]],
    ),
    "E5": (
        list(_ERA_E5),
        [
            1,
            1,
            [
                statuslog.Verdicts(
                    "adversarial", "claude", "claude-sonnet-5-5", "high", 2971705, False
                ),
                statuslog.Verdicts(
                    "conformance", "claude", "claude-sonnet-5-5", "high", 5852914, False
                ),
            ],
        ],
    ),
}


@pytest.mark.parametrize("key", list(_ERAS))
def test_the_old_eras_from_disk(tmp_path: Path, key: str) -> None:
    root = _repo(tmp_path)
    lines, (blockers, rounds, verdicts) = _ERAS[key]
    text = statuslog.title("0001-x") + "\n\n## Run 1 — 2026-09-28 12:00\n"
    _put(root, ".minions/changes/0001-x/status_log.md", text + _lines(*lines))

    assert _read(root, "blockers-round-1") == blockers
    assert _read(root, "converge-rounds") == rounds
    events = [statuslog.parse_event(line) for line in lines]
    assert [e and statuslog.verdicts(e) for e in events] == verdicts


# ---- slice W: worker logs -----------------------------------------------------

_STAMP = "20261101-100000"


def _worker_logs(root: Path, *stations: str) -> Path:
    """Write a run log of one finished spawn of each station, and name its logs."""
    lines = [
        line
        for n, station in enumerate(stations)
        for line in _pair(f"10:{n:02d}:00", f"10:{n:02d}:30", station)
    ]
    return _runlog(root, f"{_STAMP}.md", *lines)


def _wlog(root: Path, name: str, *lines: object) -> Path:
    return _put(
        root, f".minions/changes/0001-x/logs/{_STAMP}-{name}.log", _lines(*lines)
    )


def _result(cost: object = 1.0, **usage: object) -> dict[str, object]:
    return {"type": "result", "total_cost_usd": cost, "modelUsage": usage}


def _spawn(model: str | None = "gpt-5.5") -> dict[str, object]:
    return {"type": "mf.spawn", "executor": "codex", "model": model, "effort": None}


def _spent_reads(root: Path, stage: str = "build") -> list[object]:
    metrics = (f"cost-usd-{stage}", f"tokens-{stage}")
    return [_read(root, metric) for metric in metrics]


def test_a_claude_logs_model_usage_is_summed_by_its_four_keys(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _worker_logs(root, "build")
    first = {
        "inputTokens": 1,
        "outputTokens": 2,
        "cacheReadInputTokens": 4,
        "cacheCreationInputTokens": 8,
    }
    usage: dict[str, object] = {
        "a": first,
        "b": {"inputTokens": True, "outputTokens": 3},
        "c": 5,
        "d": None,
        "e": [1],
    }
    _wlog(root, "build", _result(1.0, **usage))

    assert _spent_reads(root) == [1.0, 18]


def test_a_codex_logs_turns_are_summed_into_tokens(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repo(tmp_path)
    _worker_logs(root, "build")
    prices = _put(root, "own-prices.toml", _ROWS)
    monkeypatch.setattr(run, "PRICES", prices)
    last = {"type": "turn.completed", "usage": {"input_tokens": 9, "output_tokens": 1}}
    turns = [
        {"type": "turn.completed", "usage": value} for value in (None, "x", [1], 5)
    ]
    _wlog(root, "build", _spawn(), *turns, last)

    assert _read(root, "tokens-build") == 10
    assert _read(root, "cost-usd-build") == 0.0


def test_a_log_of_a_spawn_alone_is_free_and_one_with_no_result_is_a_gap(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    _worker_logs(root, "build")
    _wlog(root, "build", _spawn())
    assert _spent_reads(root) == [0.0, 0]

    for lines in ([], ["not json"], [{"type": "assistant"}], [{"type": "x"}]):
        _wlog(root, "build", *lines)
        assert _spent_reads(root) == [_GAP_RESULT, _GAP_RESULT]


def test_a_result_with_no_usable_cost_or_usage_is_a_gap(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _worker_logs(root, "build")
    cases = [
        {"type": "result", "total_cost_usd": 1.0},
        {"type": "result", "total_cost_usd": 1.0, "modelUsage": [1]},
        {"type": "result", "modelUsage": {}},
        {"type": "result", "total_cost_usd": "1.0", "modelUsage": {}},
    ]
    for case in cases:
        _wlog(root, "build", case)
        assert _spent_reads(root) == [_GAP_RESULT, _GAP_RESULT]

    _wlog(root, "build", _result(2))
    assert _spent_reads(root) == [2, 0]


def test_a_converge_spawns_checkers_are_those_started_while_it_ran(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    _runlog(
        root,
        f"{_STAMP}.md",
        _event("10:00:00", "spawn", "converge"),
        _event("10:01:00", "spawn", "converge-conformance"),
        _event("10:02:00", "finish", "converge-conformance"),
    )
    version = run.Version(root, "0001-x", "a", "b")

    assert [s.station for s in version.checkers("converge")] == ["converge-conformance"]
    assert version.checkers("build") == []


def test_the_codex_window_is_the_last_quota_line_of_each_spawn_line_log(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    _runlog(
        root,
        f"{_STAMP}.md",
        _event("10:00:00", "spawn", "build"),
        _event("10:00:30", "finish", "build"),
        _event("10:01:00", "spawn", "converge"),
        _event("10:02:00", "spawn", "converge-conformance"),
        _event("10:03:00", "finish", "converge-conformance"),
        _event("10:04:00", "finish", "converge"),
    )
    _wlog(root, "converge", {"type": "mf.quota", "five_hour": 50.0})
    quota = {"type": "mf.quota", "weekly": True}
    _wlog(
        root,
        "converge-conformance",
        _spawn(),
        quota | {"five_hour": 1.0},
        quota | {"five_hour": 2.5},
    )

    assert _read(root, "codex-window-5h") == 2.5
    assert _read(root, "codex-window-week") == _GAP_QUOTA


def test_a_roles_tokens_are_its_checkers_logs_and_none_of_the_shadows(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    _worker_logs(
        root, "converge", "converge-conformance-r1", "converge-conformance-shadow-r1"
    )
    _wlog(root, "converge", _result(1.0, m={"inputTokens": 1}))
    _wlog(root, "converge-conformance-r1", _result(1.0, m={"inputTokens": 100}))
    _wlog(root, "converge-conformance-shadow-r1", _result(1.0, m={"inputTokens": 50}))

    assert run.Version(root, "0001-x", "a", "b").role_tokens("conformance") == 100


_WORKER_OK = _result(1.0, m={"inputTokens": 7})
_WORKER_SHAPES = {
    "link": [1.0, 7],
    "dangling": [_GAP_RESULT] * 2,
    "bad-byte": [_GAP_RESULT] * 2,
    "empty": [_GAP_RESULT] * 2,
    "missing": [_GAP_RESULT] * 2,
    "bad-byte-then-result": [1.0, 7],
}


@pytest.mark.parametrize("kind", list(_WORKER_SHAPES))
def test_the_shapes_of_a_worker_log(tmp_path: Path, kind: str) -> None:
    root = _repo(tmp_path)
    _worker_logs(root, "build")
    name = f".minions/changes/0001-x/logs/{_STAMP}-build.log"
    if kind == "bad-byte-then-result":
        _put(root, name, b"\xff\xfe\n" + _lines(_WORKER_OK).encode())
    else:
        _shaped(root, name, kind, _lines(_WORKER_OK))

    assert _spent_reads(root) == _WORKER_SHAPES[kind]
    assert _read(root, "codex-window-5h") == _GAP_QUOTA


@pytest.mark.parametrize("kind", ["missing", "empty", "bad-byte"])
def test_the_shapes_of_a_checkers_log(tmp_path: Path, kind: str) -> None:
    root = _repo(tmp_path)
    _worker_logs(root, "converge-conformance")
    name = f".minions/changes/0001-x/logs/{_STAMP}-converge-conformance.log"
    _shaped(root, name, kind, "")
    version = run.Version(root, "0001-x", "a", "b")

    with pytest.raises(run.Gap) as gap:
        version.role_tokens("conformance")
    log = f"0001-x/logs/{_STAMP}-converge-conformance.log"
    expected = f"no {log}" if kind == "missing" else f"no result event in {log}"
    assert str(gap.value) == expected


# ---- slice W: the price table -------------------------------------------------

_ROWS = '[models]\n"gpt-5.5" = { input = 2.0, cached_input = 0.5, output = 10.0 }\n'
_SONNET = '"claude-sonnet-5-5" = { input = 3.0, cached_input = 0.3, cache_write = 3.75,'
_SONNET += " cache_write_1h = 6.0, output = 15.0 }\n"
_TURN = {
    "type": "turn.completed",
    "usage": {
        "input_tokens": 1_000_000,
        "cached_input_tokens": 400_000,
        "output_tokens": 100_000,
    },
}
_PRICED = (2.4, 1_100_000)


def _codex_repo(root: Path, turns: list[object], model: str | None) -> None:
    """Write a repository whose one converge log is a Codex log of `turns`."""
    _repo(root)
    _runlog(root, f"{_STAMP}.md", *_pair("10:00:00", "10:05:00", "converge"))
    _wlog(root, "converge", _spawn(model), *turns)
    _put(
        root, ".minions/changes/0001-x/status_log.md", statuslog.title("0001-x") + "\n"
    )


def _codex_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    plant: Callable[[Path], None] | None,
    turns: list[object] | None = None,
    model: str | None = "gpt-5.5",
) -> tuple[object, object]:
    """Return what `run.py` and `review_metrics.py` each make of one Codex log."""
    held = [_TURN] if turns is None else turns
    run_root, rm_root = tmp_path / "run", tmp_path / "rm"
    for root in (run_root, rm_root):
        _codex_repo(root, held, model)
        if plant:
            plant(root)
    monkeypatch.setattr(run, "PRICES", run_root / "prices.toml")
    monkeypatch.setattr(review_metrics, "PRICES", rm_root / "prices.toml")
    return _by_run(run_root, tmp_path), _by_review(rm_root, tmp_path)


def _by_run(root: Path, shown: Path) -> object:
    try:
        return run.Version(root, "0001-x", "a", "b").spent(("converge",))
    # why: each side's error is the value under test
    except Exception as error:  # noqa: BLE001
        return _pretty(error, shown)


def _by_review(root: Path, shown: Path) -> object:
    try:
        found = next(
            r for r in review_metrics.read_repo(root) if r["change"] == "0001-x"
        )
    # why: each side's error is the value under test
    except Exception as error:  # noqa: BLE001
        return _pretty(error, shown)
    return found["cost_converge"], found["tokens_converge"]


def _prices_text(text: str) -> Callable[[Path], None]:
    def plant(root: Path) -> None:
        _put(root, "prices.toml", text)

    return plant


_NO_CACHED = _ROWS.replace("cached_input = 0.5, ", "")


def _unreadable(reason: str) -> tuple[str, str]:
    """Return what `run.py` and `review_metrics.py` each make of a bad price table."""
    return f"raises Gap: prices: {reason}", f"raises Unreadable: {reason}"


_CODEX_PRICES = {
    "good": (_ROWS, (_PRICED, _PRICED)),
    "missing": (None, _unreadable("No such file or directory")),
    "not-toml": ("not = = toml", _unreadable("Invalid value (at line 1, column 7)")),
    "no-models": ("[other]\nx = 1\n", _unreadable("no models table")),
    "models-not-table": ("models = 5\n", _unreadable("no models table")),
    "codex-row-no-cached-input": (
        _NO_CACHED,
        ("raises Gap: no price for model gpt-5.5", "raises KeyError: 'cached_input'"),
    ),
    "price-string": (
        _ROWS.replace("input = 2.0", 'input = "2.0"'),
        ("raises Gap: no price for model gpt-5.5", (None, 1_100_000)),
    ),
    "claude-row-no-cache-write": (
        _ROWS + _SONNET.replace("cache_write = 3.75,", ""),
        (_PRICED, _PRICED),
    ),
    "codex-row-is-5": (
        '[models]\n"gpt-5.5" = 5\n',
        ("raises Gap: no price for model gpt-5.5", (None, 1_100_000)),
    ),
}


@pytest.mark.parametrize("key", list(_CODEX_PRICES))
def test_prices_toml_read_by_both_scripts_for_a_codex_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, key: str
) -> None:
    text, expected = _CODEX_PRICES[key]
    plant = None if text is None else _prices_text(text)

    assert _codex_read(tmp_path, monkeypatch, plant) == expected


_NO_FILE = "raises Gap: prices: No such file or directory"
_NO_ROW = "raises Gap: no price for model {}"


@pytest.mark.parametrize(
    ("model", "with_file", "expected"),
    [
        (None, True, (_NO_ROW.format("default"), (None, 1_100_000))),
        ("o9", True, (_NO_ROW.format("o9"), (None, 1_100_000))),
        (None, False, (_NO_FILE, (None, 1_100_000))),
        ("o9", False, _unreadable("No such file or directory")),
    ],
    ids=["model-null", "model-o9", "model-null-no-file", "model-o9-no-file"],
)
def test_a_codex_log_whose_model_is_null_or_has_no_row(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    model: str | None,
    with_file: bool,
    expected: tuple[object, object],
) -> None:
    plant = _prices_text(_ROWS) if with_file else None

    assert _codex_read(tmp_path, monkeypatch, plant, model=model) == expected


def _usage_turn(**usage: object) -> dict[str, object]:
    return {"type": "turn.completed", "usage": usage}


@pytest.mark.parametrize(
    ("turns", "expected"),
    [
        (
            [_usage_turn(input_tokens=1.0, output_tokens=1.0)],
            ((0.0, 0), (1.2e-05, 2.0)),
        ),
        (
            [_usage_turn(input_tokens=True, output_tokens=True)],
            ((0.0, 0), (0.0, 0)),
        ),
        (
            [_usage_turn(input_tokens=-5, output_tokens=-3)],
            ((-4e-05, -8), (-4e-05, -8)),
        ),
        ([_usage_turn(input_tokens=10)], ((2e-05, 10), (2e-05, 10))),
        (
            [_usage_turn(input_tokens=10, cached_input_tokens=0, output_tokens=0)],
            ((2e-05, 10), (2e-05, 10)),
        ),
        (
            [
                _TURN,
                {"type": "turn.completed", "usage": "x"},
                {"type": "turn.completed", "usage": [1]},
            ]
            + [{"type": "turn.completed", "usage": 5}, {"type": "turn.completed"}],
            (_PRICED, _PRICED),
        ),
    ],
    ids=["floats", "bools", "negative", "input-only", "zero-cached", "odd-turns"],
)
def test_a_codex_turns_usage_counts_as_each_script_reads_them(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    turns: list[object],
    expected: tuple[object, object],
) -> None:
    got = _codex_read(tmp_path, monkeypatch, _prices_text(_ROWS), turns)

    assert got == expected


def _claude_workers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    prices: str | None,
    usage: dict[str, object] | None = None,
    model: str | None = "claude-sonnet-5-5",
) -> object:
    """Return the first worker's (model, tokens, dollars) a Claude mailbox log gives."""
    repo = _repo(tmp_path / "repo")
    held = usage or {
        "input_tokens": 1_000_000,
        "cache_read_input_tokens": 1_000_000,
        "cache_creation_input_tokens": 2_000_000,
        "cache_creation": {"ephemeral_1h_input_tokens": 1_000_000},
        "output_tokens": 1_000_000,
    }
    _put(
        repo, ".minions/changes/0001-x/status_log.md", statuslog.title("0001-x") + "\n"
    )
    opened = {"type": "assistant", "message": {"id": "x1", "model": model, "usage": {}}}
    done = {"type": "result", "total_cost_usd": 0.1, "usage": held}
    _wlog(repo, "converge-adversarial", opened, done)
    if prices is not None:
        _put(repo, "prices.toml", prices)
    monkeypatch.setattr(review_metrics, "PRICES", repo / "prices.toml")
    monkeypatch.setenv("TZ", "UTC")
    out = tmp_path / "site" / "page.html"
    try:
        assert review_metrics.main(["--repo", str(repo), "--out", str(out)]) == 0
    # why: the error is the value under test
    except Exception as error:  # noqa: BLE001
        return _pretty(error, tmp_path)
    workers = json.loads(out.with_name("review-metrics.json").read_text())["workers"]
    return workers[0]["model"], workers[0]["tokens"], workers[0]["dollars"]


_CLAUDE_PRICES = _ROWS + _SONNET
_SONNET_5M = ("claude-sonnet-5-5", 5_000_000, 28.05)


@pytest.mark.parametrize(
    ("prices", "expected"),
    [
        (_CLAUDE_PRICES, _SONNET_5M),
        (None, "raises Unreadable: No such file or directory"),
        (
            "not = = toml",
            "raises Unreadable: Invalid value (at line 1, column 7)",
        ),
        ("[other]\nx = 1\n", "raises Unreadable: no models table"),
        ("models = 5\n", "raises Unreadable: no models table"),
    ],
    ids=["good", "missing", "not-toml", "no-models", "models-not-table"],
)
def test_prices_toml_for_a_claude_worker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    prices: str | None,
    expected: object,
) -> None:
    assert _claude_workers(tmp_path, monkeypatch, prices) == expected


@pytest.mark.parametrize(
    ("prices", "usage", "model", "expected"),
    [
        (
            _ROWS + _SONNET.replace("cache_write = 3.75,", ""),
            None,
            "claude-sonnet-5-5",
            ("claude-sonnet-5-5", 5_000_000, None),
        ),
        (
            _ROWS + _SONNET.replace("input = 3.0", 'input = "3.0"'),
            None,
            "claude-sonnet-5-5",
            ("claude-sonnet-5-5", 5_000_000, None),
        ),
        (
            _ROWS + '"claude-sonnet-5-5" = 5\n',
            None,
            "claude-sonnet-5-5",
            ("claude-sonnet-5-5", 5_000_000, None),
        ),
        (
            _CLAUDE_PRICES.replace("cached_input = 0.5, ", ""),
            None,
            "claude-sonnet-5-5",
            _SONNET_5M,
        ),
        (_CLAUDE_PRICES, None, None, (None, 5_000_000, None)),
        (_CLAUDE_PRICES, None, "zzz", ("zzz", 5_000_000, None)),
        (
            None,
            None,
            None,
            "raises Unreadable: No such file or directory",
        ),
        (
            _CLAUDE_PRICES,
            {"input_tokens": 1.0, "output_tokens": 1.0},
            "claude-sonnet-5-5",
            ("claude-sonnet-5-5", 2, 1.8e-05),
        ),
        (
            _CLAUDE_PRICES,
            {"input_tokens": True, "output_tokens": True},
            "claude-sonnet-5-5",
            ("claude-sonnet-5-5", 0, 0.0),
        ),
        (
            _CLAUDE_PRICES,
            {"input_tokens": -5, "output_tokens": 3},
            "claude-sonnet-5-5",
            ("claude-sonnet-5-5", -2, 3e-05),
        ),
        (
            _CLAUDE_PRICES,
            {"input_tokens": 10},
            "claude-sonnet-5-5",
            ("claude-sonnet-5-5", 10, 3e-05),
        ),
    ],
    ids=[
        "row-without-cache-write",
        "price-string",
        "row-is-5",
        "codex-row-lacks-cached-input",
        "model-null",
        "model-zzz",
        "model-none-no-prices-file",
        "usage-floats",
        "usage-bools",
        "usage-negative",
        "usage-input-only",
    ],
)
def test_a_claude_workers_model_and_usage_shapes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    prices: str | None,
    usage: dict[str, object] | None,
    model: str | None,
    expected: object,
) -> None:
    assert _claude_workers(tmp_path, monkeypatch, prices, usage, model) == expected


_PRICE_SHAPES = {
    "link": _unreadable("it is a link"),
    "crlf": (_PRICED, _PRICED),
    "dangling": _unreadable("it is a link"),
    "folder": _unreadable("it is not a file"),
    "badbyte": _unreadable(
        "'utf-8' codec can't decode byte 0xff in position 0: invalid start byte"
    ),
    "empty": _unreadable("no models table"),
    "big": _unreadable("it is over 262144 bytes"),
}


@pytest.mark.parametrize("kind", list(_PRICE_SHAPES))
def test_the_prices_file_as_a_link_a_folder_a_bad_byte_or_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    def plant(root: Path) -> None:
        shape = {"badbyte": "bad-byte", "crlf": "big"}.get(kind, kind)
        text = _ROWS.replace("\n", "\r\n") if kind == "crlf" else ""
        big = _ROWS + "# " + "x" * (_BOUND + 100) + "\n"
        _shaped(root, "prices.toml", shape, _ROWS, text if kind == "crlf" else big)

    got = _codex_read(tmp_path, monkeypatch, plant)

    assert got == _PRICE_SHAPES[kind]


_REVIEW_CHILD = """
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('review_metrics', sys.argv[1])
rm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rm)
rm.PRICES = Path(sys.argv[3])
print(rm.read_repo(Path(sys.argv[2])))
"""


@pytest.mark.slow
def test_a_prices_file_that_is_a_fifo_blocks_both_scripts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_root, rm_root = tmp_path / "run", tmp_path / "rm"
    for root in (run_root, rm_root):
        _codex_repo(root, [_TURN], "gpt-5.5")
        os.mkfifo(root / "prices.toml")

    assert not _hangs(_CHILD, _RUN, run_root, run_root / "prices.toml", timeout=3)
    assert not _hangs(
        _REVIEW_CHILD, _REVIEW, rm_root, rm_root / "prices.toml", timeout=3
    )


# ---- slice W: the debt file ---------------------------------------------------

_SECTIONS = _lines(
    "# Debt",
    "",
    "## 0000-y",
    "- **0023·y**",
    "### 0001-x",
    "- **0023·h**",
    "## 0001-x extra",
    "- **0023·e**",
    "## 0001-x",
    "- **0023·a — title**",
    "- **0024·b**",
    "  - **0025·nested**",
    "- **R1·c**",
    "some text",
    "## 0002-z",
    "- **0023·z**",
)


def _debt_script(root: Path) -> tuple[int, str, str]:
    done = subprocess.run(
        [sys.executable, str(_DEBT)],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    return done.returncode, done.stdout, done.stderr


def _debt_file(root: Path, text: str | bytes) -> None:
    _put(root, ".minions/debt.md", text)


def _debt_reads(root: Path, text: str | bytes) -> tuple[object, object]:
    _debt_file(root, text)
    return debt.cards(root), _debt_script(root)


_CARDS = {
    "titled": ("- **0023·a — title**\n", 1),
    "open": ("- **0023·a**\n", 0),
    "unclosed": ("- **0023·a\n", 0),
    "indented": ("  - **0023·a**\n", 0),
    "five-digits": ("- **12345·x\n", 0),
    "letters": ("- **R1·b**\n", 0),
    "hyphen": ("- **0023-a**\n", 0),
    "empty": ("", 0),
    "crlf": ("- **0023·a**\r\n- **0024·b**\r\n", 0),
    "30000": ("- **0023·a**\n" * 30_000, 0),
    "sections": (_SECTIONS, 1),
}


@pytest.mark.parametrize("key", list(_CARDS))
def test_the_debt_script_counts_cards_of_four_digits_at_a_line_start(
    tmp_path: Path, key: str
) -> None:
    root = _repo(tmp_path)
    text, count = _CARDS[key]

    assert _debt_reads(root, text) == (count, (0, f"{count}\n", ""))


_NO_DEBT = (None, (1, "", "no .minions/debt.md\n"))
_LINKED = (
    "raises Unreadable: it is a link",
    (1, "", "no .minions/debt.md: it is a link\n"),
)


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        ("link", _LINKED),
        ("missing", _NO_DEBT),
        ("dangling", _NO_DEBT),
        ("folder", _NO_DEBT),
        ("fifo", _NO_DEBT),
    ],
)
def test_the_debt_script_reads_a_link_and_reports_a_missing_file(
    tmp_path: Path, kind: str, expected: object
) -> None:
    root = _repo(tmp_path)
    _shaped(root, ".minions/debt.md", kind, "- **0023·a — x**\n")
    try:
        cards: object = debt.cards(root)
    except debtfile.Unreadable as error:
        cards = f"raises Unreadable: {error.reason}"

    assert (cards, _debt_script(root)) == expected


def test_a_debt_file_with_a_bad_byte_is_a_traceback(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _put(root, ".minions/debt.md", b"\xff\xfe")

    assert debt.cards(root) == 0
    assert _debt_script(root) == (0, "0\n", "")


def test_a_directory_that_is_no_repository_is_a_called_process_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))

    with pytest.raises(subprocess.CalledProcessError):
        debt.cards(plain)
    code, out, err = _debt_script(plain)
    assert (code, out) == (1, "")
    assert (
        err.rstrip()
        .splitlines()[-1]
        .startswith("subprocess.CalledProcessError: Command '['git', 'rev-parse'")
    )


def _debt_added(root: Path, change: str) -> object:
    return _read(root, "debt-added", change)


@pytest.mark.parametrize(
    ("change", "count"),
    [
        ("0001-x", 1),
        ("0002-z", 0),
        ("0000-y", 0),
        ("0001-x extra", 0),
        ("0009-q", 0),
        ("0001", 0),
        ("0001.x", 0),
    ],
)
def test_a_versions_debt_is_the_cards_of_its_own_section(
    tmp_path: Path, change: str, count: int
) -> None:
    root = _repo(tmp_path)
    _debt_file(root, _SECTIONS)

    assert _debt_added(root, change) == count


@pytest.mark.parametrize(
    ("text", "count"),
    [
        ("## 0001-x  \n- **0023·a**\n", 0),
        ("## 0001-x\ntext only\n", 0),
        ("## 0001-x\n- **R1·b**\n- **a**\n- **12345·x\n", 0),
        ("## 0001-x\r\n- **0023·a**\r\n", 0),
        ("", 0),
    ],
    ids=["trailing-blanks", "no-card", "three-odd-cards", "crlf", "empty"],
)
def test_a_versions_debt_in_odd_files(tmp_path: Path, text: str, count: int) -> None:
    root = _repo(tmp_path)
    _debt_file(root, text.encode())

    assert _debt_added(root, "0001-x") == count


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        ("missing", "gap: no .minions/debt.md"),
        ("dangling", "gap: no .minions/debt.md"),
        ("folder", "gap: no .minions/debt.md"),
        ("link", "gap: no .minions/debt.md: it is a link"),
        ("bad-byte", 0),
    ],
)
def test_a_versions_debt_file_that_is_missing_a_link_or_has_a_bad_byte(
    tmp_path: Path, kind: str, expected: object
) -> None:
    root = _repo(tmp_path)
    _shaped(root, ".minions/debt.md", kind, "## 0001-x\n- **0023·a**\n")

    assert _debt_added(root, "0001-x") == expected
