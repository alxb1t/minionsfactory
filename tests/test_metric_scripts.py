"""MF's metric scripts, each over a small tree of its own.

Why: 0030-change-impact design D7.
"""

import importlib.util
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


def test_the_backlog_is_read_from_the_primary_run_directory(tmp_path: Path) -> None:
    primary, worktree = tmp_path / "primary", tmp_path / "v0.2_x"
    primary.mkdir()
    _git(primary, "init", "-q")
    _git(primary, "commit", "-q", "--allow-empty", "-m", "base")
    _git(primary, "worktree", "add", "-q", "-b", "v0.2_x", str(worktree))
    _write(primary, {".minions/backlog.md": "- **0023·a**\n- **0024·b**\n"})

    assert _load("backlog").cards(worktree) == 2
