"""MF's metric scripts, each over a small tree of its own.

Why: 0030-change-impact design D7.
"""

import importlib.util
import json
import os
import re
import subprocess
import sys
from collections.abc import Callable
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
            "skills/mf-converge/references/generic-conformance.md": "seventeen",
            "skills/mf-converge/references/generic-adversarial.md": "eighteen nineteen",
        },
    )
    reading_set = _load("reading_set")

    assert reading_set.words(tmp_path, "shared") == 9
    # The converge conductor reads no decision, principle or threat model.
    assert reading_set.words(tmp_path, "converge") == 9
    # A decisions file with no `### D` heading counts whole in conformance's index.
    assert reading_set.words(tmp_path, "conformance") == 10
    # Adversarial reads the threat model, and no decision.
    assert reading_set.words(tmp_path, "adversarial") == 8

    # Conformance reads the decisions' index, its `### D` lines, not the whole file.
    _write(tmp_path, {"docs/decisions.md": "### D1 · six\nbody words"})
    assert reading_set.words(tmp_path, "shared") == 14
    assert reading_set.words(tmp_path, "converge") == 9
    assert reading_set.words(tmp_path, "conformance") == 13
    assert reading_set.words(tmp_path, "adversarial") == 8


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


def test_code_metrics_read_the_tree(tmp_path: Path) -> None:
    codebase = _load("codebase")
    with pytest.raises(SystemExit, match="no code lines"):
        codebase.count(tmp_path, "test-to-code-lines")
    assert codebase.count(tmp_path, "largest-module-lines") == 0

    header = '# /// script\n# dependencies = ["x", "y"]\n# ///\n'
    # Only a comment suppresses: the same words in a string do not.
    suppressed = "a = 1  # noqa: E501\nb = 2  # type: ignore\n"
    unsuppressed = 'c = "# noqa"\n# pragma: no cover\n'
    _write(
        tmp_path,
        {
            "skills/a/s.py": header + suppressed + unsuppressed,
            "skills/big.py": "x = 1\n" * 1001,
            "tests/t.py": "x = 1\n" * 504,
            "pyproject.toml": '[project]\ndependencies = ["a>=1"]\n\n'
            '[dependency-groups]\ndev = ["p", "q"]\n'
            'lint = [{include-group = "dev"}, "r"]\n',
        },
    )

    expected = {
        "largest-module-lines": 1001,
        "modules-over-1000-lines": 1,
        "suppressions": 3,
        "test-to-code-lines": 0.5,
        "python-lines": 1512,
        "dependencies": 3,
        "dev-dependencies": 3,
    }
    assert {kind: codebase.count(tmp_path, kind) for kind in expected} == expected


def test_complex_functions_are_read_from_ruff(tmp_path: Path) -> None:
    codebase = _load("codebase")
    found = (
        '[{"code": "C901", "filename": "a.py"}, {"code": "C901", "filename": "b.py"}]'
    )
    assert codebase.complex_count(found, 1, "") == 2
    assert codebase.complex_count("[]", 0, "") == 0
    with pytest.raises(SystemExit, match="invalid value"):
        codebase.complex_count("", 2, "error: invalid value\nmore\n")
    with pytest.raises(SystemExit, match="ruff exit 2"):
        codebase.complex_count("", 2, "")

    # A tree holding none of the roots runs no Ruff.
    assert codebase.count(tmp_path, "complex-functions") == 0


def test_test_metrics_read_the_junit_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    codebase = _load("codebase")
    collected = [3]
    monkeypatch.setattr(codebase, "_collected", lambda root: collected[0])
    assert codebase.stale(3, 4) and not codebase.stale(3, 3)
    kinds = [kind for kind in codebase.KINDS if kind.startswith(("test-s", "slow"))]
    kinds += ["total-coverage"]

    with pytest.raises(SystemExit, match="no readable test-report.xml"):
        codebase.count(tmp_path, "test-seconds")

    cases = "".join(
        f'<testcase classname="t" name="n{i}" time="{seconds}"/>'
        for i, seconds in enumerate(["0.5", "6.25", "5.0"])
    )
    report = f'<testsuite name="pytest" tests="3" time="12.5">{cases}</testsuite>'
    _write(tmp_path, {".minions/test-report.xml": "<testsuites"})
    with pytest.raises(SystemExit, match="no readable test-report.xml"):
        codebase.count(tmp_path, "test-seconds")
    _write(tmp_path, {".minions/test-report.xml": "<testsuites/>"})
    with pytest.raises(SystemExit, match="no testsuite in test-report.xml"):
        codebase.count(tmp_path, "test-seconds")

    _write(
        tmp_path,
        {
            ".minions/test-report.xml": f"<testsuites>{report}</testsuites>",
            "coverage.xml": '<coverage line-rate="0.9876"><packages/></coverage>',
        },
    )
    counts = {kind: codebase.count(tmp_path, kind) for kind in kinds}
    assert counts == {
        "test-seconds": 12.5,
        "slowest-test-seconds": 6.25,
        "test-seconds-summed": 11.75,
        "slow-tests": 1,
        "total-coverage": 98.76,
    }

    # A report of other tests is stale, so is the coverage beside it.
    collected[0] = 4
    for kind in kinds:
        with pytest.raises(SystemExit, match="test-report.xml is stale"):
            codebase.count(tmp_path, kind)
    collected[0] = 3
    (tmp_path / "coverage.xml").unlink()
    with pytest.raises(SystemExit, match="no readable coverage.xml"):
        codebase.count(tmp_path, "total-coverage")


def test_the_code_script_runs_as_the_collector_runs_it(tmp_path: Path) -> None:
    def run(kind: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, _SCRIPTS / "codebase.py", kind],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

    def branching(name: str, ifs: int) -> str:
        # Each `if` adds one to McCabe's base of one.
        cases = "".join(f"    if x == {i}:\n        return {i}\n" for i in range(ifs))
        return f"def {name}(x: int) -> int:\n{cases}    return x\n"

    _write(
        tmp_path,
        {
            # One function over complexity 10, and one at it, which is not over.
            "skills/a.py": branching("over", 10) + branching("at", 9),
            "tests/test_a.py": "def test_a() -> None:\n    pass\n",
            ".minions/test-report.xml": '<testsuites><testsuite tests="1" time="0.5">'
            '<testcase name="test_a" time="0.25"/></testsuite></testsuites>',
        },
    )
    assert run("python-lines").stdout == "44\n"
    # Ruff and `pytest --collect-only` start as the collector starts them.
    assert run("complex-functions").stdout == "1\n"
    assert run("slowest-test-seconds").stdout == "0.25\n"
    assert run("no-such-kind").returncode == 2

    # A tree whose collection fails is a gap, whatever the report says.
    _write(tmp_path, {"tests/test_b.py": "def ("})
    broken = run("slow-tests")
    assert broken.returncode == 1 and broken.stdout == ""
    assert broken.stderr.strip() == "pytest collection failed (exit 2)"


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
    debt = _load("debt")
    assert debt.cards(tmp_path) is None
    done = subprocess.run(
        [sys.executable, _SCRIPTS / "debt.py"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert done.returncode != 0 and done.stdout == ""
    assert done.stderr.splitlines()[0] == "no .minions/debt.md"

    _write(
        tmp_path,
        {
            ".minions/debt.md": "# Debt\n\n- **0023·R7 — a**\n  - **0023·x**\n"
            "- **R1·b**\n- **0028·S1 — c**\n"
        },
    )
    assert debt.cards(tmp_path) == 2


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
00:11:31 · run · rescue — 0001-x: diagnosed · .minions/changes/0001-x/rescue.md
00:11:31 · 0001-x · halt — rescue diagnosed — .minions/changes/0001-x/rescue.md
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
09:08:11 · run · rescue — 0001-x: decided · 2.2 · abc1235
09:08:11 · run · supervise — 0001-x: decided · 2.3 · abc1236
09:08:30 · 0003-z · wait — after 0001-x
09:09:00 · 0003-z · spawn — build · model m
09:09:30 · 0005-v · spawn — release · model m
"""
_STATUS = """# 0001-x — converge status

## Run 4 — 2026-11-02 10:00 · amend
10:30:00 · round 8 · done — converged in one amend round

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
    _write(root, {"a.txt": "1\n2\n3\n4\n", "metrics/changes/0001-x.json": "{}\n"})
    _git(root, "add", "a.txt", "metrics")
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
            ".minions/changes/0001-x/status_log.md": _STATUS,
            ".minions/changes/0002-y/status_log.md": "# 0002-y\n\n## Run 1 — x\n",
            # The first run halted before its fan-out; the next one holds round 1.
            ".minions/changes/0004-w/status_log.md": "# 0004-w\n\n"
            "## Run 2 — 2026-11-02 10:00\n"
            "10:20:00 · round 1 · verdicts — review changes-requested"
            " · open_blocking 1\n\n"
            "## Run 1 — 2026-11-02 09:00\n"
            "09:01:00 · round 1 · halt — the gate is red\n",
            ".minions/changes/0001-x/build.done": f"head: {built}\n"
            "simplify: lean already\n",
            ".minions/changes/0002-y/build.done": f"head: {unmerged}\n",
            ".minions/changes/0004-w/build.done": f"head: {built}\n",
        },
    )
    return {"MF_METRICS_CHANGE": "0001-x", "MF_METRICS_BASE": base} | {
        "MF_METRICS_HEAD": head
    }


def _reader(
    root: Path, env: dict[str, str], prices: Path | None = None
) -> Callable[..., object]:
    """Return a reader of one metric of a change: its number, or `gap: <why>`.

    Its Codex logs are priced by `prices`, when given.
    """
    run = _load("run")
    if prices is not None:
        vars(run)["PRICES"] = prices

    def read(metric: str, change: str = "0001-x", **named: str) -> object:
        given = env | {"MF_METRICS_CHANGE": change} | named
        try:
            return run.measure(root, [metric], given)
        except run.Gap as gap:
            return f"gap: {gap}"

    return read


def test_run_metrics_read_the_run_logs(tmp_path: Path) -> None:
    env = _run_fixture(tmp_path)
    run = _load("run")
    read = _reader(tmp_path, env)

    expected = {
        # A converge after the first integrate is a catch-up; midnight adds a day.
        "lead-minutes": 720.0,
        "build-minutes": 30.0,
        "converge-minutes": 50.0,
        "catch-up-minutes": 6.0,
        "integrate-minutes": 2.0,
        # Rescue and an automatic grant are the run's own; a refused rejoin answers
        # nothing; the next run's start answers the integrate halt.
        "wait-minutes": 516.5,
        "after-wait-minutes": 0,
        "converge-rounds": 4,
        "blockers-round-1": 2,
        "grants": 1,
        "amend-rounds": 1,
        "halts-build": 0,
        "halts-converge": 2,
        "halts-integrate": 1,
        "halts-release": 0,
        "rescues-fixed": 1,
        "rescues-diagnosed": 1,
        "rescues-decided": 1,
        "supervisor-decided": 1,
        "build-commits": 3,
        "fix-commits": 1,
    }
    assert {metric: read(metric) for metric in expected} == expected

    # A version with a run log but no finish, release, status log or build mark.
    assert read("build-minutes", "0003-z") == "gap: a build spawn with no finish"
    assert read("lead-minutes", "0003-z") == "gap: no release spawn"
    assert read("integrate-minutes", "0003-z") == 0
    # The wait on an `after:` id runs to the version's next event.
    assert read("after-wait-minutes", "0003-z") == 0.5
    # A wait its run left unfinished ends with that run: the next run's start, a day
    # later, closes nothing.
    _write(
        tmp_path,
        {
            ".minions/runs/20261107-100000.md": "# Ship run 20261107-100000\n\n"
            "10:00:00 · 0006-u · wait — after 0001-x\n",
            ".minions/runs/20261108-100000.md": "# Ship run 20261108-100000\n\n"
            "10:00:00 · run · start — executor claude · versions 0006-u · mf v1\n"
            "10:01:00 · 0006-u · spawn — build · model m\n",
        },
    )
    assert read("after-wait-minutes", "0006-u") == 0
    assert read("grants", "0003-z") == "gap: no 0003-z/status_log.md"
    assert read("build-commits", "0003-z") == "gap: no head in 0003-z/build.done"
    # A version released by hand: no run log, its commits and cards still read.
    assert read("wait-minutes", "0004-w") == "gap: no run log names 0004-w"
    assert read("halts-build", "0004-w") == "gap: no run log names 0004-w"
    assert read("build-commits", "0004-w") == 3
    assert read("blockers-round-1", "0004-w") == 1
    assert read("converge-rounds", "0002-y") == "gap: no round in the status log"
    assert read("blockers-round-1", "0002-y") == (
        "gap: no round 1 verdicts with open_blocking"
    )
    assert read("fix-commits", "0002-y") == (
        "gap: 0002-y/build.done's head is not in the version's history"
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


def test_run_metrics_halt_on_an_old_layout(tmp_path: Path) -> None:
    env = _run_fixture(tmp_path)
    run = _load("run")
    # A stray the move leaves is no old layout.
    strays = {
        ".minions/runs/20261101-230000/0001-x_Notes.log": "x\n",
        ".minions/findings/0001-x_review.run1.md": "x\n",
        ".minions/findings/0001-xy_review.md": "x\n",
    }
    _write(tmp_path, strays)
    assert run.measure(tmp_path, ["grants"], env) == 1

    old = ".minions/runs/20261101-230000/0001-x_converge-2.log"
    _write(tmp_path, {old: "x\n"})
    said = f"{old} is the old layout: /mf-ship moves it"
    with pytest.raises(run.OldLayout, match=re.escape(said)):
        run.measure(tmp_path, ["grants"], env)
    done = subprocess.run(
        [sys.executable, _SCRIPTS / "run.py", "grants"],
        cwd=tmp_path,
        env=os.environ | env,
        capture_output=True,
        text=True,
    )
    assert (done.returncode, done.stdout, done.stderr) == (2, "", f"{said}\n")


def _worker_log(
    root: Path, name: str, cost: float, tokens: int, *events: object
) -> None:
    """Write a worker log: `events`, then a result event of `cost` and `tokens`."""
    result = {
        "type": "result",
        "total_cost_usd": cost,
        "modelUsage": {"m": {"inputTokens": tokens, "outputTokens": "n/a"}},
    }
    lines = [e if isinstance(e, str) else json.dumps(e) for e in [*events, result]]
    _write(root, {f".minions/changes/{name}": "".join(f"{line}\n" for line in lines)})


def _task(tool: str, description: str) -> object:
    return {"subtype": "task_started", "tool_use_id": tool, "description": description}


def _turn(parent: str | None, message: str, **usage: int) -> object:
    return {
        "type": "assistant",
        "parent_tool_use_id": parent,
        "message": {"id": message, "usage": usage},
    }


def _role_file(cards: str, refuted: str = "## Refuted\n\n- **x.** why\n") -> str:
    return (
        f"---\nverdict: clean\n---\n\n## Findings\n\n{cards}\n{refuted}\n## Summary\n"
    )


def _finding(card: str, verdict: str, related: str) -> str:
    return (
        f"- **{card} — a defect**\n  - **Verdict:** {verdict}.\n"
        f"  - **Priority:** nit · conformance · stability — why.\n"
        f"  - **Related:** {related}.\n"
    )


def test_run_metrics_read_cost_and_review_yield(tmp_path: Path) -> None:
    env = _run_fixture(tmp_path)
    read = _reader(tmp_path, env)
    first = {"type": "result", "total_cost_usd": 0.5, "modelUsage": {}}
    conformance = _task("t1", "Converge conformance worker 0001")
    _worker_log(tmp_path, "0001-x/logs/20261101-230000-build.log", 1.0, 110)
    _worker_log(
        tmp_path,
        "0001-x/logs/20261101-230000-converge.log",
        2.0,
        500,
        "not json, holding tool_use_id",
        first,
        conformance,
        # A description names its role in any case.
        _task("t2", "Adversarial station, round 1"),
        _task("t3", "Converge fix station 0001"),
        # Each subagent turn counts once, by its message id, every token kind summed.
        _turn(
            "t1", "m1", input_tokens=10, output_tokens=5, cache_read_input_tokens=100
        ),
        _turn(
            "t1", "m1", input_tokens=10, output_tokens=5, cache_read_input_tokens=100
        ),
        _turn("t2", "m2", input_tokens=30, cache_creation_input_tokens=0),
        _turn("t3", "m3", input_tokens=999),
        _turn(None, "m4", input_tokens=999),
    )
    verify = _task("t4", "Conformance station round 2")
    converge_2 = "0001-x/logs/20261101-230000-converge-2.log"
    _worker_log(
        tmp_path, converge_2, 0.5, 50, verify, _turn("t4", "m5", input_tokens=85)
    )
    _worker_log(tmp_path, "0001-x/logs/20261101-230000-rescue.log", 0.25, 5)
    _worker_log(tmp_path, "0001-x/logs/20261101-230000-integrate.log", 0.25, 5)
    _worker_log(tmp_path, "0001-x/logs/20261102-090000-converge.log", 0.1, 1)
    _worker_log(tmp_path, "0001-x/logs/20261102-090000-converge-2.log", 0.2, 2)
    _worker_log(tmp_path, "0001-x/logs/20261102-090000-release.log", 9.0, 900)
    reviewed = _finding("R1", "confirmed", "repeat of `0000·R9`")
    reviewed += _finding("R2", "plausible", "repeat of 0001·R1")
    reviewed += _finding("R3", "`confirmed`", "repeat of 0000·R4")
    refuted = "## Refuted\n\n- **x.** why\n- **y.** why\n"
    _write(
        tmp_path,
        {
            ".minions/changes/0001-x/conformance.md": _role_file(reviewed, refuted),
            ".minions/changes/0001-x/adversarial.md": _role_file(
                _finding("S1", "plausible", "none")
            ),
            ".minions/changes/0002-y/conformance.md": _role_file(reviewed, ""),
            "openspec/changes/archive/0001-x/proposal.md": "---\nbump: minor\n"
            "debt: [0000·R4, 0000·S2]\n---\n",
            "openspec/changes/0002-y/proposal.md": "---\nbump: patch\n---\n",
            "openspec/changes/archive/0004-w/proposal.md": "---\nbump: patch\n"
            "backlog: [0000·R4]\n---\n",
            ".minions/debt.md": "# Debt\n\n## 0000-old\n\n- **0000·R4 — a**\n\n"
            "## 0001-x\n\n- **0001·R2 — b**\n  - **Why:** c\n- **0001·S1 — d**\n",
        },
    )

    expected = {
        # The release's own log is left out; a catch-up's logs are the converges
        # spawned after the first integrate, the n-th spawn in a stamp its `-<n>.log`.
        "cost-usd": 4.3,
        "cost-usd-build": 1.0,
        "cost-usd-converge": 2.5,
        "cost-usd-catch-up": 0.3,
        "cost-usd-integrate": 0.25,
        "tokens": 673,
        "tokens-build": 110,
        "tokens-converge": 550,
        "tokens-catch-up": 3,
        "tokens-integrate": 5,
        "cost-per-changed-line": 1.075,
        "conformance-confirmed": 2,
        "adversarial-confirmed": 0,
        "conformance-refuted": 2,
        "adversarial-refuted": 1,
        "conformance-tokens-per-confirmed": 100,
        "adversarial-tokens-per-confirmed": "gap: no confirmed adversarial card",
        # R1 repeats an earlier change's card it does not pay; R3's is paid, and R2
        # repeats its own change's.
        "escapes": 1,
        "debt-added": 2,
        "debt-paid": 2,
    }
    assert {metric: read(metric) for metric in expected} == expected

    assert read("debt-paid", "0002-y") == 0
    assert read("debt-paid", "0004-w") == 1
    assert read("debt-added", "0002-y") == 0
    assert (
        read("conformance-refuted", "0002-y")
        == "gap: no ## Refuted in 0002-y/conformance.md"
    )
    assert read("adversarial-confirmed", "0003-z") == "gap: no 0003-z/adversarial.md"
    assert read("debt-paid", "0003-z") == "gap: no proposal.md for 0003-z"
    assert read("cost-usd-build", "0003-z") == (
        "gap: no result event in 0003-z/logs/20261102-090000-build.log"
    )
    assert read("conformance-tokens-per-confirmed", "0003-z") == (
        "gap: no 0003-z/conformance.md"
    )
    # An adversarial worker's turns are read, and no card to divide them by is a gap.
    run = _load("run")
    assert run.Version(tmp_path, "0001-x", "a", "b").role_tokens("adversarial") == 30
    with pytest.raises(
        run.Gap, match="no conformance subagent event in a converge log"
    ):
        run.Version(tmp_path, "0002-y", "a", "b").role_tokens("conformance")
    assert read("cost-per-changed-line", MF_METRICS_HEAD=env["MF_METRICS_BASE"]) == (
        "gap: no line changed"
    )

    # A spawn whose log is gone is a gap, never a smaller sum.
    (tmp_path / ".minions/changes/0001-x/logs/20261102-090000-converge-2.log").unlink()
    assert read("cost-usd") == (
        "gap: no result event in 0001-x/logs/20261102-090000-converge-2.log"
    )
    assert read("conformance-tokens-per-confirmed") == (
        "gap: no 0001-x/logs/20261102-090000-converge-2.log"
    )
    (tmp_path / ".minions/debt.md").unlink()
    assert read("debt-added") == "gap: no .minions/debt.md"

    # A Codex converge log: its turns' tokens, priced at its spawn line's model.
    prices = tmp_path / "prices.toml"
    # A `default` row prices no log: a spawn line naming no model stays a gap.
    prices.write_text(
        '[models]\n"gpt-5.5" = { input = 2.0, cached_input = 0.5, output = 10.0 }\n'
        '"default" = { input = 2.0, cached_input = 0.5, output = 10.0 }\n'
    )
    priced = _reader(tmp_path, env, prices)
    usage = {"input_tokens": 1_000_000, "cached_input_tokens": 400_000}
    turn = {"type": "turn.completed", "usage": usage | {"output_tokens": 100_000}}

    def codex(model: str | None, first: str | None = None) -> None:
        spawn = {"type": "mf.spawn", "executor": "codex", "model": model}
        lines = [first or json.dumps(spawn | {"effort": None})]
        lines += [json.dumps(turn), json.dumps(turn)]
        _write(tmp_path, {f".minions/changes/{converge_2}": "\n".join(lines) + "\n"})

    codex("gpt-5.5")
    assert priced("cost-usd-converge") == 2.0 + 2 * 2.4
    assert priced("tokens-converge") == 500 + 2 * 1_100_000
    for model, named in (("o9", "o9"), (None, "default")):
        codex(model)
        assert priced("cost-usd-converge") == f"gap: no price for model {named}"
        assert priced("tokens-converge") == 500 + 2 * 1_100_000
    codex("gpt-5.5", first="not json")
    assert priced("cost-usd-converge") == f"gap: no spawn line in {converge_2}"
    assert priced("tokens-converge") == 500 + 2 * 1_100_000

    # A checker the mailbox started counts in the stage whose converge holds its
    # start, in its role's tokens, and in no stage's minutes.
    codex("gpt-5.5")
    _worker_log(tmp_path, "0001-x/logs/20261102-090000-converge-2.log", 0.2, 2)
    checked = _RUN_A.replace(
        "00:10:30 · 0001-x · finish — converge",
        "23:40:00 · 0001-x · spawn — converge-conformance · model gpt-5.5"
        " · executor codex\n"
        "23:50:00 · 0001-x · finish — converge-conformance · exit 0 · 600s\n"
        "00:10:30 · 0001-x · finish — converge",
    )
    late = _RUN_B.replace(
        "09:05:10 · 0001-x · finish — converge",
        "09:01:00 · 0001-x · spawn — converge-adversarial · model m\n"
        "09:02:00 · 0001-x · finish — converge-adversarial · exit 0 · 60s\n"
        "09:05:10 · 0001-x · finish — converge",
    )
    spawn = {"type": "mf.spawn", "executor": "codex", "model": "gpt-5.5"}
    log = "\n".join([json.dumps(spawn | {"effort": "high"}), json.dumps(turn)])
    _write(
        tmp_path,
        {
            ".minions/runs/20261101-230000.md": checked,
            ".minions/runs/20261102-090000.md": late,
            ".minions/changes/0001-x/logs/20261101-230000-converge-conformance.log": (
                log + "\n"
            ),
        },
    )
    _worker_log(
        tmp_path, "0001-x/logs/20261102-090000-converge-adversarial.log", 0.7, 7
    )
    assert priced("cost-usd-converge") == round(2.0 + 3 * 2.4, 2)
    assert priced("tokens-converge") == 500 + 3 * 1_100_000
    assert priced("cost-usd-catch-up") == 1.0
    assert priced("tokens-catch-up") == 10
    assert (priced("converge-minutes"), priced("catch-up-minutes")) == (50.0, 6.0)
    # Conformance's subagent turns and its Codex checker's tokens, over 2 cards.
    assert priced("conformance-tokens-per-confirmed") == round((115 + 1_100_000) / 2)
    assert run.Version(tmp_path, "0001-x", "a", "b").role_tokens("adversarial") == 37
    # Twin: a role with neither a subagent event nor a checker log stays a gap.
    (tmp_path / ".minions/changes/0001-x/logs/20261101-230000-converge.log").unlink()
    _worker_log(tmp_path, "0001-x/logs/20261101-230000-converge.log", 2.0, 500)
    assert run.Version(tmp_path, "0001-x", "a", "b").role_tokens("conformance") == (
        1_100_000
    )
    checker = "0001-x/logs/20261101-230000-converge-conformance.log"
    (tmp_path / ".minions/changes" / checker).unlink()
    with pytest.raises(run.Gap, match=f"no {checker}"):
        run.Version(tmp_path, "0001-x", "a", "b").role_tokens("conformance")


def test_the_backlog_is_read_from_the_primary_run_directory(tmp_path: Path) -> None:
    primary, worktree = tmp_path / "primary", tmp_path / "v0.2_x"
    primary.mkdir()
    _git(primary, "init", "-q")
    _git(primary, "commit", "-q", "--allow-empty", "-m", "base")
    _git(primary, "worktree", "add", "-q", "-b", "v0.2_x", str(worktree))
    _write(primary, {".minions/debt.md": "- **0023·a**\n- **0024·b**\n"})

    assert _load("debt").cards(worktree) == 2
