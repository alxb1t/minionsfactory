"""MF's metric scripts, each over a small tree of its own.

Why: 0030-change-impact design D7.
"""

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts" / "metrics"


def _load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, _SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(root: Path, files: dict[str, str]) -> None:
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=mf", "-c", "user.email=mf@example.invalid"]
        + ["-c", "commit.gpgsign=false", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def test_reading_sets_count_words(tmp_path: Path) -> None:
    _write(
        tmp_path,
        {
            "AGENTS.md": "one two\nthree",
            "docs/principles.md": "four  five",
            "docs/decisions.md": "six",
            "skills/mf-converge/SKILL.md": "seven eight nine ten",
            "CODING_STANDARDS.md": "eleven",
            "CONTRIBUTING.md": "twelve thirteen",
            "THREAT_MODEL.md": "fourteen",
            "skills/mf-converge/references/worker.md": "fifteen sixteen",
            "skills/mf-converge/references/generic-review.md": "seventeen",
        },
    )
    reading_set = _load("reading_set")

    assert reading_set.words(tmp_path, "shared") == 9
    assert reading_set.words(tmp_path, "converge") == 16
    assert reading_set.words(tmp_path, "worker") == 13


def test_rule_ids_are_counted_once(tmp_path: Path) -> None:
    _write(
        tmp_path,
        {
            "skills/mf-a/SKILL.md": "| **I1** | x |\n| **P2** | y |\n| **No** | z |\n",
            "skills/mf-b/SKILL.md": "| **I1** | x |\n| **X3** | y |\n| a | **T4** |\n",
            "skills/mf-b/references/r.md": "| **W5** | x |\n",
        },
    )

    assert _load("rule_ids").rule_ids(tmp_path) == 2


def test_tests_collected_is_unavailable_on_a_broken_collection() -> None:
    tests_collected = _load("tests_collected")
    assert tests_collected.collected("35 tests collected in 0.1s\n", 0) == 35

    # A test file that fails to import still prints a partial count.
    with pytest.raises(SystemExit, match="exit 2"):
        tests_collected.collected("1 test collected, 1 error in 0.1s\n", 2)


def test_prose_skips_code_and_tables(tmp_path: Path) -> None:
    long = " ".join(["word"] * 31) + "."
    limit = " ".join(["word"] * 30) + "."
    item = " ".join(["word"] * 20)
    _write(
        tmp_path,
        {
            "skills/mf-a/SKILL.md": "\n".join(
                [
                    # Frontmatter is not prose, and each list item is its own.
                    "---",
                    f"description: {item} {item}",
                    "---",
                    "",
                    f"- {item}",
                    f"  {item[:9]}",
                    f"- {item}",
                    f"1. {item}",
                    "",
                    "You should go. As NEEDED, it is etc. a shoulder.",
                    "Use `should` here.",
                    "",
                    "```",
                    "might might",
                    long,
                    "```",
                    "",
                    f"| should | {long} |",
                    "",
                    f"{long} {limit}",
                ]
            ),
            "skills/mf-a/references/r.md": "It might.\n",
        },
    )
    prose = _load("prose")

    assert prose.count(tmp_path, "hedge") == 4
    assert prose.count(tmp_path, "long") == 1


def test_broken_references_find_files_headings_and_ids(tmp_path: Path) -> None:
    _write(
        tmp_path,
        {
            "AGENTS.md": "\n".join(
                [
                    "[ok](docs/a.md) [gone](docs/missing.md) [web](https://example.com)",
                    "[head](docs/a.md#real-heading) [bad](docs/a.md#no-such-heading)",
                    "[id](docs/a.md#d1--one) per D1 and D9; `D7 [code](nowhere.md)`.",
                    # A heading's inline code keeps its text in the anchor.
                    "[claim](docs/a.md#fixed-is-a-claim-only-the-checker-writes-verified)",
                ]
            ),
            "README.md": "D9 is a version here. [self](#top)\n\n# Top\n",
            "docs/a.md": "# Real heading\n\n### D1 · One\n\n```\n[x](no.md)\n```\n"
            "\n### `fixed` is a claim; only the checker writes `verified`\n",
            "CONTRIBUTING.md": "[gone](nowhere.md)\n",
            "THREAT_MODEL.md": "[gone](nowhere.md)\n",
        },
    )

    assert _load("references").broken(tmp_path) == 5


def test_conformance_counts_trailers_amends_and_minions(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "commit", "-q", "--allow-empty", "-m", "base")
    base = _git(tmp_path, "rev-parse", "HEAD")
    messages = [
        "feat: one\n\nChange: 0002-x",
        "docs(0002-x): amend the change directory\n\nChange: 0002-x",
        "feat: two\n\nChange: 0001-w",
        "feat: three",
    ]
    for message in messages:
        _git(tmp_path, "commit", "-q", "--allow-empty", "-m", message)
    _write(tmp_path, {".minions/run.md": "x", ".gitignore": ".minions/\n"})
    _git(tmp_path, "add", "-f", ".minions/run.md")
    _git(tmp_path, "commit", "-q", "-m", "feat: four\n\nChange: 0002-x")
    head = _git(tmp_path, "rev-parse", "HEAD")
    conformance = _load("conformance")

    counts = {
        kind: conformance.count(tmp_path, kind, "0002-x", base, head)
        for kind in ("trailer", "amends", "minions")
    }
    assert counts == {"trailer": 2, "amends": 1, "minions": 1}


def test_backlog_cards_are_unavailable_without_a_backlog(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    backlog = _load("backlog")
    assert backlog.cards(tmp_path) is None
    done = subprocess.run(
        [sys.executable, _SCRIPTS / "backlog.py"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert done.returncode != 0 and done.stdout == ""
    assert done.stderr.splitlines()[0] == "no .minions/backlog.md"

    _write(
        tmp_path,
        {
            ".minions/backlog.md": "# Backlog\n\n- **0023·R7 — a**\n  - **0023·x**\n"
            "- **R1·b**\n- **0028·S1 — c**\n"
        },
    )
    assert backlog.cards(tmp_path) == 2


_RUN_A = """# Ship run 20261101-230000

23:00:00 · run · start — executor claude · versions 0001-x 0002-y · mf v1
23:00:20 · 0001-x · spawn — probe-codex · model default · executor codex
23:00:30 · 0001-x · spawn — build · model m
23:30:30 · 0001-x · finish — build · exit 0 · 1800s
23:30:30 · 0001-x · spawn — converge · model m · effort high
00:10:30 · 0001-x · finish — converge · exit 0 · 2400s
00:10:30 · 0001-x · halt — converge check fail — the status log halts: cap
00:10:31 · 0001-x · spawn — rescue · model m
00:11:31 · 0001-x · finish — rescue · exit 0 · 60s
00:11:31 · run · rescue — 0001-x: diagnosed · .minions/rescue/0001-x.md
00:11:31 · 0001-x · halt — rescue diagnosed — .minions/rescue/0001-x.md
00:12:00 · run · rejoin — 0001-x: still halted — answered
00:21:31 · run · rejoin — 0001-x: converge
00:21:31 · run · grant — 0001-x: one more round past the cap
00:21:31 · 0001-x · spawn — converge · model m
00:31:31 · 0001-x · finish — converge · exit 0 · 600s
00:31:31 · 0002-y · halt — build check fail — phase 1 unticked
00:31:31 · 0001-x · spawn — integrate · model m
00:33:31 · 0001-x · finish — integrate · exit 0 · 120s
00:33:31 · 0001-x · halt — integrate check fail — the gate is red
00:34:00 · run · halt — halted 0001-x · blocked none · released none
"""
_RUN_B = """# Ship run 20261102-090000

09:00:00 · run · start — executor claude · versions 0001-x · mf v1
09:00:10 · 0001-x · spawn — converge · model m
09:05:10 · 0001-x · finish — converge · exit 0 · 300s
09:05:10 · 0001-x · halt — converge worker exit 1
09:05:11 · run · grant — 0001-x: automatic · R1
09:05:11 · 0001-x · spawn — converge · model m
09:06:11 · 0001-x · finish — converge · exit 0 · 60s
09:06:11 · 0001-x · spawn — release · model m
09:08:11 · 0001-x · finish — release · exit 0 · 120s
09:08:11 · run · rescue — 0001-x: fixed · 2.1 · abc1234
09:09:00 · 0003-z · spawn — build · model m
09:09:30 · 0005-v · spawn — release · model m
"""
_STATUS = """# 0001-x — converge status

## Run 3 — 2026-11-02 09:05 · catch-up
09:06:00 · round 7 · done — converged by rule

## Run 2 — 2026-11-02 00:21 · grant
00:30:00 · round 4 · done — converged in 4 rounds

## Run 1 — 2026-11-01 23:30
00:10:00 · round 3 · halt — cap reached, R3 open
23:40:00 · round 1 · verdicts — security clean · open_blocking 0 · tokens unavailable
23:39:00 · round 1 · verdicts — review changes-requested · open_blocking 2 · tokens 9
"""


def _commit(root: Path, message: str, when: str = "2026-11-01T12:00:00") -> str:
    env = os.environ | {"GIT_COMMITTER_DATE": when, "GIT_AUTHOR_DATE": when}
    subprocess.run(
        ["git", "-c", "user.name=mf", "-c", "user.email=mf@example.invalid"]
        + ["-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty"]
        + ["-m", message],
        cwd=root,
        env=env,
        check=True,
    )
    return _git(root, "rev-parse", "HEAD")


def _run_fixture(root: Path) -> dict[str, str]:
    """Return the env naming 0001-x, over a repo and a run directory of its run."""
    _git(root, "init", "-q", "-b", "main")
    base = _commit(root, "base")
    _commit(root, "docs(0001-x): land the change directory", "2026-11-01T22:00:00")
    _commit(root, "feat(0001-x): one")
    built = _commit(root, "feat(0001-x): two")
    _git(root, "checkout", "-q", "-b", "side", base)
    _commit(root, "feat: on the default branch")
    _git(root, "checkout", "-q", "-b", "other", base)
    unmerged = _commit(root, "feat: never merged")
    _git(root, "checkout", "-q", "main")
    _git(root, "merge", "-q", "--no-ff", "-m", "merge", "side")
    head = _commit(root, "fix(0001-x): R1")
    _write(
        root,
        {
            ".minions/runs/20261101-230000.md": _RUN_A,
            ".minions/runs/20261102-090000.md": _RUN_B,
            # A later log in the same second sorts after its first.
            ".minions/runs/20261102-090000-2.md": "# Ship run 20261102-090000-2\n\n"
            "10:00:00 · 0001-x · spawn — release · model m\n"
            "10:01:00 · 0001-x · finish — release · exit 0 · 60s\n",
            ".minions/runs/notes.md": "12:00:00 · 0001-x · halt — build check fail\n",
            ".minions/findings/0001-x_status_log.md": _STATUS,
            ".minions/findings/0002-y_status_log.md": "# 0002-y\n\n## Run 1 — x\n",
            ".minions/build/0001-x.done": f"head: {built}\nsimplify: lean already\n",
            ".minions/build/0002-y.done": f"head: {unmerged}\n",
            ".minions/build/0004-w.done": f"head: {built}\n",
        },
    )
    return {"MF_METRICS_CHANGE": "0001-x", "MF_METRICS_BASE": base} | {
        "MF_METRICS_HEAD": head
    }


def test_run_metrics_read_the_run_logs(tmp_path: Path) -> None:
    env = _run_fixture(tmp_path)
    run = _load("run")

    def read(metric: str, change: str = "0001-x") -> object:
        try:
            return run.measure(tmp_path, [metric], env | {"MF_METRICS_CHANGE": change})
        except run.Gap as gap:
            return f"gap: {gap}"

    values = {metric: read(metric) for metric in run.METRICS}
    assert values == {
        # A converge after the first integrate is a catch-up; midnight adds a day.
        "lead-minutes": 720.0,
        "build-minutes": 30.0,
        "converge-minutes": 50.0,
        "catch-up-minutes": 6.0,
        "integrate-minutes": 2.0,
        # Rescue and an automatic grant are the run's own; a refused rejoin answers
        # nothing; the next run's start answers the integrate halt.
        "wait-minutes": 516.5,
        "converge-rounds": 4,
        "blockers-round-1": 2,
        "grants": 1,
        "halts-build": 0,
        "halts-converge": 2,
        "halts-integrate": 1,
        "halts-release": 0,
        "rescues-fixed": 1,
        "rescues-diagnosed": 1,
        "build-commits": 3,
        "fix-commits": 1,
    }

    # A version with a run log but no finish, release, status log or build mark.
    assert read("build-minutes", "0003-z") == "gap: a build spawn with no finish"
    assert read("lead-minutes", "0003-z") == "gap: no release spawn"
    assert read("integrate-minutes", "0003-z") == 0
    assert read("grants", "0003-z") == "gap: no 0003-z_status_log.md"
    assert read("build-commits", "0003-z") == "gap: no head in 0003-z.done"
    # A version released by hand: no run log, its commits and cards still read.
    assert read("wait-minutes", "0004-w") == "gap: no run log names 0004-w"
    assert read("halts-build", "0004-w") == "gap: no run log names 0004-w"
    assert read("build-commits", "0004-w") == 3
    assert read("converge-rounds", "0002-y") == "gap: no round in the status log"
    assert read("blockers-round-1", "0002-y") == (
        "gap: no round 1 verdicts with open_blocking"
    )
    assert read("fix-commits", "0002-y") == (
        "gap: 0002-y.done's head is not in the version's history"
    )
    assert read("lead-minutes", "0005-v") == (
        "gap: no commit `docs(0005-v): land the change directory`"
    )

    with pytest.raises(run.Gap, match="usage: run.py <id>, one of lead-minutes"):
        run.measure(tmp_path, [], env)
    with pytest.raises(run.Gap, match="no MF_METRICS_CHANGE"):
        run.measure(tmp_path, ["grants"], {})
    bare = {k: v for k, v in os.environ.items() if not k.startswith("MF_METRICS_")}
    done = subprocess.run(
        [sys.executable, _SCRIPTS / "run.py", "grants"],
        cwd=tmp_path,
        env=bare,
        capture_output=True,
        text=True,
    )
    assert (done.returncode, done.stdout) == (1, "")
    assert done.stderr == "no MF_METRICS_CHANGE, _BASE and _HEAD\n"


def test_the_backlog_is_read_from_the_primary_run_directory(tmp_path: Path) -> None:
    primary, worktree = tmp_path / "primary", tmp_path / "v0.2_x"
    primary.mkdir()
    _git(primary, "init", "-q")
    _git(primary, "commit", "-q", "--allow-empty", "-m", "base")
    _git(primary, "worktree", "add", "-q", "-b", "v0.2_x", str(worktree))
    _write(primary, {".minions/backlog.md": "- **0023·a**\n- **0024·b**\n"})

    assert _load("backlog").cards(worktree) == 2
