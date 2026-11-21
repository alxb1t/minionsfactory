"""The claim as the conductor takes, reads and clears it, pinned, and its module's.

Cases j to m and the claim's pins of 0140-run-log design's pin; the module's cases.
"""

import contextlib
import os
import re
import signal
import subprocess
import sys
import threading
import time
import types
from pathlib import Path

import pytest
from conduct_load import conduct as _conduct
from mflib import claim, layout, platform

conduct = _conduct()
_NAMES = conduct["main"].__globals__
_FAKE_PS = """
import os
import sys
from pathlib import Path

_, field, _, pid = sys.argv[1:]
known = Path(os.environ["FAKE_PS_REGISTRY"], f"{pid}.{field.rstrip('=')}")
if not known.is_file():
    sys.exit(1)
print(known.read_text())
"""


@pytest.fixture
def ps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Put a fake `ps` first on `PATH`, which exits 1 for a pid it does not know.

    Return the registry it reads: `<pid>.lstart` and `<pid>.comm`.
    """
    folder = tmp_path / "ps-bin"
    folder.mkdir()
    fake = folder / "ps"
    fake.write_text(f"#!{sys.executable} -S{_FAKE_PS}")
    fake.chmod(0o755)
    registry = tmp_path / "ps-registry"
    registry.mkdir()
    monkeypatch.setenv("PATH", str(folder), prepend=os.pathsep)
    monkeypatch.setenv("FAKE_PS_REGISTRY", str(registry))
    return registry


def _known(registry: Path, pid: int, start: str, comm: str = "python3") -> None:
    """Make the fake `ps` answer `start` and `comm` for `pid`."""
    (registry / f"{pid}.lstart").write_text(start)
    (registry / f"{pid}.comm").write_text(comm)


def _dead() -> int:
    """Return the pid of a process that has ended."""
    done = subprocess.Popen([sys.executable, "-c", "pass"])
    done.wait()
    return done.pid


def _claim_of(tmp_path: Path, pid: str, start: str) -> Path:
    """Return a claim folder holding `pid` and `start`."""
    active = tmp_path / "active"
    active.mkdir(parents=True)
    (active / "pid").write_text(pid)
    (active / "start").write_text(start)
    return active


def test_case_j_a_padded_claim_reads_live(tmp_path: Path, ps: Path) -> None:
    _known(ps, 4242, "S")

    assert conduct["_claim"](_claim_of(tmp_path, " 4242 \n", "S\n")) == "live"


def test_case_j_an_empty_start_is_stale_even_for_a_dead_pid(
    tmp_path: Path, ps: Path
) -> None:
    active = _claim_of(tmp_path, str(_dead()), "")

    assert conduct["_claim"](active) == "stale"


def test_case_j_the_pids_floor_is_above_1(tmp_path: Path, ps: Path) -> None:
    active = _claim_of(tmp_path, "2", "S")
    for pid in (-1, 0, 1, 2):
        _known(ps, pid, "S")

    assert conduct["_claim"](active) == "live"
    for pid in ("1", "0", "-1"):
        (active / "pid").write_text(pid)
        assert conduct["_claim"](active) == "stale", pid


def test_case_j_no_claim_is_none_and_a_file_at_the_claim_is_stale(
    tmp_path: Path, ps: Path
) -> None:
    active = tmp_path / "active"
    assert conduct["_claim"](active) == "none"

    active.write_text("4242\n")
    assert conduct["_claim"](active) == "stale"


@pytest.fixture
def killed(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """Record each group the conductor kills; a group 4246 is gone before the kill."""
    groups: list[int] = []

    def killpg(group: int, sig: int) -> None:
        groups.append(group)
        if group == 4246:
            raise ProcessLookupError(group)

    monkeypatch.setattr(os, "killpg", killpg)
    return groups


def test_case_k_clear_reads_decimal_entries_and_kills_their_groups(
    tmp_path: Path, ps: Path, killed: list[int]
) -> None:
    active = _claim_of(tmp_path, "x", "S")
    for name in ("abc", "²", "12a"):
        (active / name).write_text("S")
    _known(ps, 4243, "S", "/bin/claude")
    (active / "4243").write_text("S\n")
    (active / str(_dead())).touch()
    _known(ps, 4246, "S", "codex")
    (active / "4246").write_text("S")

    conduct["_clear"](active)

    assert sorted(killed) == [4243, 4246]
    assert not active.exists()


def test_case_k_a_foreign_group_stops_the_clear_and_its_neighbour_is_killed(
    tmp_path: Path, ps: Path, killed: list[int]
) -> None:
    active = _claim_of(tmp_path, "x", "S")
    _known(ps, 4244, "S", "sleep")
    (active / "4244").write_text("S")
    _known(ps, 4245, "S", "/bin/claude")
    (active / "4245").write_text("S")

    with pytest.raises(conduct["Stop"]) as stopped:
        conduct["_clear"](active)

    assert stopped.value.code == 2
    assert str(stopped.value) == (
        "conduct: cannot clear the claim — worker group 4244 (sleep) names no"
        " executor: read it, then kill it or remove its entry in .minions/runs/active"
    )
    assert killed == [4245]
    assert (active / "4244").is_file()


def _repo(tmp_path: Path) -> Path:
    """Return a primary checkout on `main` holding one commit, `.minions/` ignored."""
    root = (tmp_path / "main").resolve()
    root.mkdir()
    for args in (
        ("init", "-q", "-b", "main"),
        ("config", "user.name", "mf"),
        ("config", "user.email", "mf@example.invalid"),
        ("config", "commit.gpgsign", "false"),
    ):
        subprocess.run(["git", *args], cwd=root, check=True)
    (root / ".gitignore").write_text(".minions/\n")
    subprocess.run(["git", "add", ".gitignore"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=root, check=True)
    return root


def _entries(folder: Path) -> dict[str, str]:
    return {entry.name: entry.read_text() for entry in folder.iterdir()}


@pytest.fixture
def shipped(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, str]]:
    """Run `run` with its preconditions met and its ship recording the claim.

    Return the claim's entries as each ship saw them.
    """
    seen: list[dict[str, str]] = []

    class Ship:
        def __init__(self, primary: Path, executor: str) -> None:
            self.active = primary / ".minions" / "runs" / "active"
            self.log = types.SimpleNamespace(stamp="20261101-100001")

        def ship(self) -> int:
            seen.append(_entries(self.active))
            return 0

        def handled(self) -> None:
            return None

    pin = {"holder": lambda mark: None, "move": lambda mark: None}
    for name, value in {
        "preconditions": lambda cwd, executor: cwd,
        "_cap": lambda: None,
        "_pushes_tags": lambda: True,
        "_pin": lambda: pin,
        "_record_repo": lambda primary: None,
        "Run": Ship,
    }.items():
        monkeypatch.setitem(_NAMES, name, value)
    return seen


_OWN_START = "Sat Nov 21 10:00:00 2026"


def test_case_l_run_clears_a_stale_claim_and_holds_its_own_start_and_pid(
    tmp_path: Path,
    ps: Path,
    shipped: list[dict[str, str]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    _known(ps, os.getpid(), _OWN_START)
    root = _repo(tmp_path)
    active = root / ".minions" / "runs" / "active"
    active.mkdir(parents=True)
    (active / "pid").write_text(str(_dead()))
    (active / "start").write_text("Thu Jan  1 00:00:00 1970\n")
    (active / "7").mkdir()
    (active / "stray").write_text("x")

    assert conduct["run"](root, "claude", False) == 0

    assert shipped == [{"start": _OWN_START, "pid": str(os.getpid())}]
    assert not active.exists()
    assert capsys.readouterr().out == "run: done · .minions/runs/20261101-100001.md\n"


def test_case_l_a_live_claim_is_refused_with_2_and_left_whole(
    tmp_path: Path, ps: Path, shipped: list[dict[str, str]]
) -> None:
    _known(ps, os.getpid(), _OWN_START)
    root = _repo(tmp_path)
    active = _claim_of(root / ".minions" / "runs", str(os.getpid()), _OWN_START)
    (active / "4242").write_text("S")
    held = _entries(active)

    with pytest.raises(conduct["Stop"]) as stopped:
        conduct["run"](root, "claude", False)

    assert stopped.value.code == 2
    assert str(stopped.value) == (
        "run: cannot run — a run is live: .minions/runs/active exists"
    )
    assert shipped == []
    assert _entries(active) == held


@pytest.fixture
def closing(tmp_path: Path) -> tuple[Path, Path]:
    """Return a primary and its claim, which holds one entry."""
    root = _repo(tmp_path)
    active = _claim_of(root / ".minions" / "runs", "4242", "S")
    return root, active


def test_case_l_close_removes_the_claim(
    closing: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    root, active = closing

    conduct["_close"](root, active, "claude", None)

    assert not active.exists()
    assert capsys.readouterr().out == ""


def test_case_l_close_removes_the_claim_on_a_stop_before_the_removal(
    closing: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, active = closing

    def refused(primary: Path) -> contextlib.AbstractContextManager[None]:
        raise conduct["Stop"](2, "conduct: cannot run — the home folder refuses")

    monkeypatch.setitem(_NAMES, "_queue_lock", refused)

    conduct["_close"](root, active, "claude", set())

    assert not active.exists()
    assert capsys.readouterr().out == "conduct: cannot run — the home folder refuses\n"


def test_case_l_close_starts_the_next_run_on_a_request(
    closing: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, active = closing
    rejoin = layout.queue_dir(root) / "rejoin"
    rejoin.mkdir(parents=True)
    (rejoin / "0001-a").touch()
    monkeypatch.setitem(_NAMES, "_start_run", lambda primary, executor: 4242)

    conduct["_close"](root, active, "claude", set())

    assert not active.exists()
    assert capsys.readouterr().out == "run: next started · pid 4242\n"


def test_case_l_a_cut_seen_or_halted_starts_nothing(
    closing: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, active = closing
    monkeypatch.setitem(_NAMES, "_start_run", lambda primary, executor: 4242)
    cases = [
        ({"0003-a": {"halt": None}}, {"0003-a"}, ""),
        ({"0003-a": {"halt": "a halt"}}, set(), ""),
        ({"0003-a": {"halt": None}}, set(), "run: next started · pid 4242\n"),
    ]
    for cuts, seen, said in cases:
        active.mkdir(exist_ok=True)
        monkeypatch.setitem(_NAMES, "_cuts", lambda primary, cuts=cuts: cuts)
        conduct["_close"](root, active, "claude", seen)
        assert not active.exists()
        assert capsys.readouterr().out == said, cuts


def test_case_l_start_run_returns_once_the_claim_is_live(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repo(tmp_path)
    child = types.SimpleNamespace(pid=4242, poll=lambda: None)
    claims = iter(["none", "none", "live"])
    monkeypatch.setitem(_NAMES, "_detach", lambda primary, executor: child)
    monkeypatch.setitem(_NAMES, "_claim", lambda active: next(claims))

    assert conduct["_start_run"](root, "claude") == 4242
    assert next(claims, "read") == "read"


def test_case_l_start_run_reads_the_detached_logs_new_lines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repo(tmp_path)
    runs = root / ".minions" / "runs"
    runs.mkdir(parents=True)
    log = runs / "detached.log"
    log.write_text("run: done · .minions/runs/old.md\n")
    said = ["pin: moved to v0.2.0\n"]

    def detach(primary: Path, executor: str) -> types.SimpleNamespace:
        with log.open("a") as sink:
            sink.write(said[0])
        return types.SimpleNamespace(pid=4242, poll=lambda: 0)

    monkeypatch.setitem(_NAMES, "_detach", detach)
    monkeypatch.setitem(_NAMES, "_claim", lambda active: "none")

    with pytest.raises(conduct["Stop"]) as stopped:
        conduct["_start_run"](root, "claude")
    assert stopped.value.code == 2
    assert str(stopped.value) == "the run did not start — pin: moved to v0.2.0"
    for line in ("run: halt · .minions/runs/new.md\n", "run: done · x\n"):
        said[0] = line
        assert conduct["_start_run"](root, "claude") == 4242, line


_CHILD = """
import os, sys, time
claim, wait = sys.argv[1], float(sys.argv[2])
entry = os.path.join(claim, str(os.getpid()))
want = f"start-{os.getpid()}"
deadline = time.monotonic() + wait
while time.monotonic() < deadline:
    if os.path.isfile(entry) and open(entry).read() == want:
        break
    time.sleep(0.01)
held = open(entry).read() if os.path.isfile(entry) else None
print(os.getpid(), sorted(os.listdir(claim)), held)
"""


def test_case_m_a_running_worker_holds_one_entry_gone_when_it_ends(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(platform, "process", lambda pid, field: f"start-{pid}")
    active = tmp_path / "active"
    active.mkdir()
    out = tmp_path / "logs" / "worker.log"
    command = [sys.executable, "-c", _CHILD, str(active), "10"]

    assert conduct["work"](command, tmp_path, out, active) == (0, False)

    pid = out.read_text().split()[0]
    assert out.read_text() == f"{pid} ['{pid}'] start-{pid}\n"
    assert list(active.iterdir()) == []


def test_case_m_with_no_claim_a_worker_holds_no_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(platform, "process", lambda pid, field: f"start-{pid}")
    active = tmp_path / "active"
    active.mkdir()
    out = tmp_path / "worker.log"
    command = [sys.executable, "-c", _CHILD, str(active), "0.3"]

    assert conduct["work"](command, tmp_path, out, None) == (0, False)

    pid = out.read_text().split()[0]
    assert out.read_text() == f"{pid} [] None\n"


def test_pin_a_bad_byte_in_pid_or_start_reads_stale_and_clear_removes_it_whole(
    tmp_path: Path, ps: Path, killed: list[int]
) -> None:
    _known(ps, 4242, "S")
    for name, held in (("pid", b"42\xff"), ("start", b"S\xff")):
        active = _claim_of(tmp_path, "4242", "S")
        assert conduct["_claim"](active) == "live"
        (active / name).write_bytes(held)
        (active / "stray").write_text("x")

        assert conduct["_claim"](active) == "stale", name
        conduct["_clear"](active)

        assert not active.exists(), name
    assert killed == []


@pytest.mark.slow
def test_pin_a_pipe_at_pid_blocks_the_claims_read(tmp_path: Path, ps: Path) -> None:
    active = tmp_path / "active"
    active.mkdir()
    (active / "start").write_text("S")
    os.mkfifo(active / "pid")
    read: list[str] = []
    child = threading.Thread(
        target=lambda: read.append(conduct["_claim"](active)), daemon=True
    )
    child.start()
    # A pipe opened blocking waits for its other end: the join bounds the run.
    child.join(timeout=10)

    assert child.is_alive()
    deadline = time.monotonic() + 10
    while child.is_alive():
        assert time.monotonic() < deadline
        with contextlib.suppress(OSError):
            os.close(os.open(active / "pid", os.O_WRONLY | os.O_NONBLOCK))
        time.sleep(0.01)
    assert read == ["stale"]


def _linked(tmp_path: Path, active: Path, pid: str) -> Path:
    """Return a claim folder holding `pid` and `S`, linked at `active`."""
    target = _claim_of(tmp_path / "elsewhere", pid, "S")
    active.parent.mkdir(parents=True, exist_ok=True)
    active.symlink_to(target)
    return target


def test_pin_the_claims_read_follows_a_link(tmp_path: Path, ps: Path) -> None:
    _known(ps, 4242, "S")
    active = tmp_path / "runs" / "active"
    _linked(tmp_path, active, "4242")

    assert conduct["_claim"](active) == "live"


def test_pin_clear_raises_on_a_link_and_leaves_link_and_target(
    tmp_path: Path, ps: Path
) -> None:
    active = tmp_path / "runs" / "active"
    target = _linked(tmp_path, active, str(_dead()))

    with pytest.raises(OSError, match="runs/active"):
        conduct["_clear"](active)

    assert active.is_symlink()
    assert _entries(target) == {"pid": (target / "pid").read_text(), "start": "S"}


def test_pin_a_dangling_link_reads_none_and_the_take_then_raises(
    tmp_path: Path, ps: Path, shipped: list[dict[str, str]]
) -> None:
    _known(ps, os.getpid(), _OWN_START)
    root = _repo(tmp_path)
    active = root / ".minions" / "runs" / "active"
    active.parent.mkdir(parents=True)
    active.symlink_to(tmp_path / "gone")
    assert conduct["_claim"](active) == "none"

    with pytest.raises(conduct["Stop"]) as stopped:
        conduct["run"](root, "claude", False)

    assert stopped.value.code == 2
    assert str(stopped.value) == (
        "run: cannot run — a run is live: .minions/runs/active exists"
    )
    assert shipped == []
    assert active.is_symlink()
    assert not (tmp_path / "gone").exists()


def test_pin_close_lets_the_error_of_a_link_out(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    active = root / ".minions" / "runs" / "active"
    target = _linked(tmp_path, active, "4242")

    with pytest.raises(OSError, match="runs/active"):
        conduct["_close"](root, active, "claude", None)

    assert active.is_symlink()
    assert target.is_dir()


def test_pin_stop_kills_the_conductor_then_a_link_escapes_before_the_stop_line(
    tmp_path: Path, ps: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _known(ps, 4242, "S")
    root = _repo(tmp_path)
    runs = root / ".minions" / "runs"
    active = runs / "active"
    _linked(tmp_path, active, "4242")
    log = runs / "20261101-100001.md"
    log.write_text("# Ship run 20261101-100001\n")
    kills: list[tuple[int, int]] = []
    monkeypatch.setattr(os, "kill", lambda pid, sig: kills.append((pid, sig)))

    with pytest.raises(OSError, match="runs/active"):
        conduct["stop_run"](root)

    assert kills == [(4242, signal.SIGKILL)]
    assert log.read_text() == "# Ship run 20261101-100001\n"
    assert active.is_symlink()


_DENIED = """
import json
use = {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "rm x"}}
result = {
    "type": "tool_result",
    "tool_use_id": "t1",
    "is_error": True,
    "content": "Permission to use Bash has been denied.",
}
for block in (use, result):
    print(json.dumps({"type": "assistant", "message": {"content": [block]}}))
raise SystemExit(3)
"""


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Read every clock the conductor writes as `10:20:30`."""
    real = time.strftime

    def strftime(form: str, *at: time.struct_time) -> str:
        return "10:20:30" if form == "%H:%M:%S" else real(form, *at)

    monkeypatch.setattr(time, "strftime", strftime)


@pytest.mark.usefixtures("clock")
def test_case_m_the_spawn_finish_denied_and_limited_lines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    root = _repo(tmp_path)
    runs = root / ".minions" / "runs"
    log = conduct["RunLog"](runs, "20261101-100001")
    host = types.SimpleNamespace(
        repo=None,
        lines=None,
        executor="codex",
        log=log,
        runs=runs,
        primary=root,
        guard=threading.Lock(),
        outs={},
        claim=None,
        limited={},
    )
    command = [sys.executable, "-c", _DENIED]
    monkeypatch.setitem(_NAMES, "argv", lambda *given, **named: command)
    models = ("claude", "opus", "high")

    code, killed, out, denied = conduct["Run"].worker(
        host, "0001-a", "build", root, "prompt", models
    )
    conduct["Run"].limit(host, "codex", out)

    assert (code, killed, denied) == (3, False, ["Bash(rm x)"])
    assert out == root / ".minions/changes/0001-a/logs/20261101-100001-build.log"
    lines = log.path.read_text().splitlines()[2:]
    assert lines == [
        "10:20:30 · 0001-a · spawn — build · model opus · effort high"
        " · executor claude",
        lines[1],
        "10:20:30 · 0001-a · denied — build · Bash(rm x)",
        "10:20:30 · run · limited — codex limited until a reset it did not name",
    ]
    assert re.fullmatch(r"10:20:30 · 0001-a · finish — build · exit 3 · \d+s", lines[1])


def test_module_take_makes_the_claim_once(tmp_path: Path) -> None:
    active = tmp_path / "active"

    claim.take(active)

    assert active.is_dir()
    with pytest.raises(FileExistsError):
        claim.take(active)


def test_module_present_says_whether_a_claim_stands(tmp_path: Path) -> None:
    active = tmp_path / "active"
    assert not claim.present(active)

    active.mkdir()
    assert claim.present(active)


def test_module_mark_writes_the_start_and_the_pid(tmp_path: Path) -> None:
    active = tmp_path / "active"
    active.mkdir()

    claim.mark(active, "S", 4242)

    assert (active / "start").read_text() == "S"
    assert (active / "pid").read_text() == "4242"


def test_module_conductor_reads_the_pid_and_the_start(tmp_path: Path) -> None:
    assert claim.conductor(_claim_of(tmp_path / "a", " 1 \n", "S\n")) == (1, "S")
    assert claim.conductor(_claim_of(tmp_path / "b", "x", "S")) is None
    assert claim.conductor(tmp_path / "none") is None
    (tmp_path / "file").write_text("4242\n")
    assert claim.conductor(tmp_path / "file") is None


def test_module_groups_reads_each_decimal_entry(tmp_path: Path) -> None:
    active = _claim_of(tmp_path, "x", "S")
    for name in ("abc", "²", "12a"):
        (active / name).write_text("S")
    (active / "4243").write_text("S\n")
    (active / "1").write_bytes(b"\xff")
    (active / "4244").mkdir()

    assert sorted(claim.groups(active)) == [(1, "�"), (4243, "S")]


def test_module_enter_and_leave_hold_a_groups_entry(tmp_path: Path) -> None:
    active = tmp_path / "active"
    active.mkdir()

    entry = claim.enter(active, 4243, "S")
    assert entry == active / "4243"
    assert entry.read_text() == "S"

    claim.leave(entry)
    assert not entry.exists()
    claim.leave(entry)


def test_module_remove_removes_the_claim_whole(tmp_path: Path) -> None:
    active = _claim_of(tmp_path, "4242", "S")
    (active / "4243").write_text("S")

    claim.remove(active)

    assert not active.exists()
