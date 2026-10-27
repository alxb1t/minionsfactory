"""The bundled metrics collector: the catalogue, the values, the page.

Why: 0030-change-impact design D2…D5.
"""

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-build" / "scripts" / "metrics.py"


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("metrics", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


metrics = _load(_SCRIPT)

_HEADER = '# /// script\n# requires-python = ">=3.12"\n# dependencies = []\n# ///\n'
_TASKS = (
    "# T\n\n## Progress\n\n- [x] 1 — One\n- [ ] 2 — Two\n\n## 1 — One\n\n- [ ] 1.1 x\n"
)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=mf", "-c", "user.email=mf@example.invalid"]
        + ["-c", "commit.gpgsign=false", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _repo(root: Path, catalogue: str | None, version: str = "v0.2") -> str:
    """Make a git repo holding the change `0002-x`; return its first commit."""
    change = root / "openspec" / "changes" / "0002-x"
    change.mkdir(parents=True)
    (change / "proposal.md").write_text(f"---\nversion: {version}\n---\n\n# X\n")
    (change / "tasks.md").write_text(_TASKS)
    if catalogue is not None:
        (root / "metrics").mkdir()
        (root / "metrics" / "catalogue.toml").write_text(catalogue)
    _git(root, "init", "-q")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "base")
    return _git(root, "rev-parse", "HEAD")


def _metric(key: str, better: str = "lower", **fields: object) -> str:
    lines = [
        "[[metric]]",
        f'id = "{key}"',
        f'title = "{key} title"',
        'group = "g"',
        'unit = "u"',
        f'better = "{better}"',
    ]
    for name, value in fields.items():
        lines.append(f"{name} = {json.dumps(value)}")
    return "\n".join(lines) + "\n"


def _script(root: Path, name: str, body: str) -> str:
    path = root / "scripts" / name
    path.parent.mkdir(exist_ok=True)
    path.write_text(_HEADER + body)
    return f"scripts/{name}"


def _collect(*extra: str, base: str = "HEAD") -> int:
    out = ".minions/metrics/0002-x.json"
    argv = ["collect", "--change", "0002-x", "--base", base, "--out", out, *extra]
    return metrics.main(argv)


def _values(root: Path) -> dict[str, dict[str, object]]:
    data = json.loads((root / ".minions/metrics/0002-x.json").read_text())
    return data["values"]


def _by_python(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        metrics, "metric_argv", lambda script, args: [sys.executable, script, *args]
    )


def test_collect_writes_a_value_per_metric(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The real `uv run --script` path: the scripts declare no dependency.
    # The script adds its args to the change id's length, read from its environment.
    body = "import os, sys\nchange = os.environ['MF_METRICS_CHANGE']\n"
    body += "print(sum(int(a) for a in sys.argv[1:]) + len(change))\n"
    catalogue = _metric(
        "added", script=_script(tmp_path, "add.py", body), args=["3", "4"]
    ) + _metric("gate-seconds", source="station")
    _repo(tmp_path, catalogue)
    monkeypatch.chdir(tmp_path)

    assert _collect("--value", "gate-seconds=1.5") == 0
    assert _values(tmp_path) == {
        "added": {"value": 7 + len("0002-x")},
        "gate-seconds": {"value": 1.5},
    }


def test_a_failing_metric_is_unavailable_with_its_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bodies = {
        "says": 'import sys\nprint("cannot read the backlog", file=sys.stderr)\n'
        "sys.exit(1)\n",
        "silent": "import sys\nsys.exit(4)\n",
        "words": 'print("12")\nprint("n/a")\n',
        "slow": "import time\ntime.sleep(5)\n",
        "fine": 'print("note")\nprint(" 9 ")\n',
        # uv's error for a missing script names the home and the root in full.
        "paths": "import os, sys\nhome, root = os.path.expanduser('~'), os.getcwd()\n"
        "print(f\"{home}/x/python: can't open '{root}/gone.py'\", file=sys.stderr)\n"
        "sys.exit(2)\n",
    }
    catalogue = "".join(
        _metric(key, script=_script(tmp_path, f"{key}.py", body))
        for key, body in bodies.items()
    )
    _repo(tmp_path, catalogue)
    monkeypatch.chdir(tmp_path)
    _by_python(monkeypatch)
    monkeypatch.setattr(metrics, "TIMEOUT_SECONDS", 0.5)
    monkeypatch.setenv("HOME", str(tmp_path.parent / "fictional-home"))

    assert _collect() == 0
    assert _values(tmp_path) == {
        "says": {"status": "unavailable", "why": "cannot read the backlog"},
        "silent": {"status": "unavailable", "why": "exit 4"},
        "words": {"status": "unavailable", "why": "no number on the last line"},
        "slow": {"status": "unavailable", "why": "timed out after 0.5 s"},
        "fine": {"value": 9},
        "paths": {
            "status": "unavailable",
            "why": "~/x/python: can't open '<repo>/gone.py'",
        },
    }


def test_no_catalogue_exits_3_and_says_so(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _repo(tmp_path, None)
    monkeypatch.chdir(tmp_path)

    assert _collect() == 3
    assert metrics.main(["page", "0002-x"]) == 3
    assert capsys.readouterr().out == "metrics: none — no catalogue\n" * 2
    assert not (tmp_path / ".minions").exists()


def test_a_broken_catalogue_exits_2_naming_the_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    good = _metric("fine", source="station")
    broken = {
        "[[metric]\n": "does not parse",
        good + '[[metric]]\nid = "bare"\n': "metric 2 `bare`: missing `title`",
        good + good: "metric 2 `fine`: `id` repeated",
        _metric("up", source="station", better="up"): "metric 1 `up`: `better`",
        _metric("both", source="station", script="s"): "1 `both`: declares both",
        _metric("none"): "metric 1 `none`: declares neither",
    }
    _repo(tmp_path, "")
    monkeypatch.chdir(tmp_path)
    catalogue = tmp_path / "metrics" / "catalogue.toml"
    for text, named in broken.items():
        catalogue.write_text(text)
        assert _collect() == 2, named
        assert named in capsys.readouterr().err


def test_station_values_are_passed_or_derived(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    catalogue = "".join(
        _metric(key, source="station")
        for key in ("gate-seconds", "diff-lines", "diff-files", "phases", "unpassed")
    )
    base = _repo(tmp_path, catalogue)
    (tmp_path / "a.txt").write_text("one\ntwo\nthree\n")
    (tmp_path / "metrics" / "changes").mkdir()
    (tmp_path / "metrics" / "changes" / "0001-w.json").write_text("{}\n" * 9)
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "work")
    monkeypatch.chdir(tmp_path)

    # A value the catalogue does not declare is noted, never a halt.
    assert _collect("--value", "gate-seconds=12", "--value", "other=1", base=base) == 0
    assert "--value other ignored" in capsys.readouterr().err
    assert _values(tmp_path) == {
        "gate-seconds": {"value": 12},
        "diff-lines": {"value": 3},
        "diff-files": {"value": 1},
        "phases": {"value": 2},
        "unpassed": {"status": "unavailable", "why": "not passed by the station"},
    }


def test_the_states_against_the_previous_release() -> None:
    lower = {"better": "lower", "watch": 100, "noise": 5}
    higher = {"better": "higher", "noise": 5}
    rows = [
        (lower, 90, 110, "crossed here"),
        (lower, 110, 120, "over"),
        (lower, 110, 90, "back under"),
        (lower, 50, 60, "worsened"),
        (lower, 60, 50, "improved"),
        (lower, 50, 55, "steady"),
        (higher, 50, 40, "worsened"),
        (higher, 40, 50, "improved"),
        ({"better": "lower"}, 7, 7, "steady"),
        ({"better": "lower"}, 7, 8, "worsened"),
        (lower, None, 50, "new"),
        (lower, 50, None, "unavailable"),
    ]
    assert [metrics.classify(m, before, now) for m, before, now, _ in rows] == [
        state for *_, state in rows
    ]


def _record(version: str, change: str = "", **values: object) -> dict[str, object]:
    return {
        "change": change or f"c-{version}",
        "version": version,
        "base": "b",
        "analyzed": "a",
        "values": {
            key: {"value": v}
            if v is not None
            else {"status": "unavailable", "why": "no file"}
            for key, v in values.items()
        },
    }


def _track(root: Path, *records: dict[str, object]) -> None:
    folder = root / "metrics" / "changes"
    folder.mkdir(parents=True, exist_ok=True)
    for record in records:
        (folder / f"{record['change']}.json").write_text(json.dumps(record))
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "track")


def test_previous_is_the_highest_version_below(tmp_path: Path) -> None:
    _repo(tmp_path, "")
    assert metrics.previous_release(tmp_path, "v0.11") is None

    _track(tmp_path, _record("v0.9"), _record("v0.10"), _record("v0.11"))
    loose = tmp_path / "metrics" / "changes" / "loose.json"
    loose.write_text(json.dumps(_record("v0.10.5")))

    found = metrics.previous_release(tmp_path, "v0.11")
    assert found is not None and found["version"] == "v0.10"
    assert metrics.previous_release(tmp_path, "v0.9") is None


def test_the_page_leads_with_what_moved_and_shows_gaps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    catalogue = (
        _metric("steady", source="station", noise=5)
        + _metric("gone", source="station")
        + _metric("over", source="station", watch=10)
        + _metric("worse", source="station")
        + _metric("crossed", source="station", watch=10)
    )
    _repo(tmp_path, catalogue)
    _track(tmp_path, _record("v0.1", steady=50, gone=1, over=20, worse=1, crossed=5))
    now = _record("v0.2", "0002-x", steady=52, gone=None, over=30, worse=3, crossed=15)
    data = tmp_path / ".minions" / "metrics" / "0002-x.json"
    data.parent.mkdir(parents=True)
    data.write_text(json.dumps(now))
    monkeypatch.chdir(tmp_path)

    assert (
        metrics.main(["page", "0002-x", "--data", str(data.relative_to(tmp_path))]) == 0
    )
    page = (tmp_path / ".minions" / "metrics" / "0002-x.html").read_text()
    states = ["crossed here", "worsened", "over", "steady", "unavailable"]
    at = [page.index(f"<td>{state}</td>") for state in states]
    assert page.index("What moved") < at[0] and at == sorted(at)
    assert at[-1] < page.index("<svg")
    assert "unavailable — no file" in page
    assert "<script" not in page
    assert 'href="../../openspec/changes/0002-x/proposal.md"' in page

    gap = metrics.chart(
        {"title": "t", "better": "lower"},
        [("v0.1", 5, False), ("v0.2", 6, False), ("v0.3", None, False)]
        + [("v0.4", 7, False), ("v0.5", 8, True)],
    )
    assert gap.count("<polyline") == 2
    assert gap.count("<circle") == 4
    assert gap.count('<circle class="dot now"') == 1


def test_provenance_is_recorded_never_guessed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A copy outside any git checkout stands for an installed, frozen package.
    package = tmp_path / "package"
    package.mkdir()
    frozen = _load(Path(shutil.copy(_SCRIPT, package)))
    repo = tmp_path / "repo"
    repo.mkdir()
    base = _repo(repo, _metric("gate-seconds", source="station"))
    _git(repo, "commit", "-q", "--allow-empty", "-m", "head")
    monkeypatch.chdir(repo)
    out = ".minions/metrics/0002-x.json"

    argv = ["collect", "--change", "0002-x", "--base", base, "--out", out]
    assert frozen.main(argv) == 0
    data = json.loads((repo / out).read_text())
    assert {key: data[key] for key in ("mf_version", "executor", "model")} == {
        "mf_version": "unknown",
        "executor": "unidentified",
        "model": "unidentified",
    }
    assert data["change"] == "0002-x" and data["version"] == "v0.2"
    assert data["base"] == _git(repo, "rev-parse", "--short", base)
    assert data["analyzed"] == _git(repo, "rev-parse", "--short", "HEAD")
    assert data["base"] != data["analyzed"] and data["measured_on"] == "local"

    argv += ["--executor", "native (Claude Code)", "--model", "m-1"]
    assert frozen.main(argv) == 0
    data = json.loads((repo / out).read_text())
    assert (data["executor"], data["model"]) == ("native (Claude Code)", "m-1")
