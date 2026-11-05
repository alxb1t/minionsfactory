# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Print one metric of this repository's codebase, read from the tree.

e.g. `codebase.py largest-module-lines` → 5736. Why: 0078-code-metrics design D1.
"""

import argparse
import io
import json
import re
import subprocess
import sys
import tokenize
import tomllib
from collections.abc import Callable
from pathlib import Path
from xml.parsers import expat

ROOTS = ("skills", "scripts", "tests")
CODE = ("skills", "scripts")
BIG_MODULE_LINES = 1000
COMPLEXITY = 10
SLOW_SECONDS = 5
REPORT = Path(".minions/test-report.xml")
COVERAGE = Path("coverage.xml")
COLLECTED = re.compile(r"(\d+) tests? collected")
SUPPRESSION = re.compile(r"noqa|type:\s*ignore|pragma:\s*no cover")
# PEP 723's own pattern for an inline script block.
HEADER = re.compile(
    r"^# /// script$\s(?P<body>(?:^#(?:| .*)$\s)+)^# ///$", re.MULTILINE
)


def _modules(root: Path, names: tuple[str, ...]) -> list[Path]:
    """Return the `.py` files under the present directories of `names`, sorted."""
    return sorted(
        path
        for name in names
        if (root / name).is_dir()
        for path in (root / name).rglob("*.py")
    )


def _lines(path: Path) -> int:
    """Return the physical lines in a file."""
    return len(path.read_text(encoding="utf-8").splitlines())


def _total_lines(root: Path, names: tuple[str, ...]) -> int:
    """Return the physical lines of every module under `names`."""
    return sum(_lines(path) for path in _modules(root, names))


def complex_count(stdout: str, returncode: int, stderr: str) -> int:
    """Return the functions Ruff's `C901` flagged; exit with why on a Ruff failure.

    Ruff exits 0 with `[]` and 1 with findings, and 2 on a bad config.
    """
    if returncode not in (0, 1):
        why = stderr.strip().splitlines() or [f"ruff exit {returncode}"]
        sys.exit(why[0])
    return len(json.loads(stdout))


def _complex_functions(root: Path) -> int:
    """Return the functions over the complexity limit, by Ruff's `C901`."""
    present = [name for name in ROOTS if (root / name).is_dir()]
    if not present:
        return 0
    done = subprocess.run(
        ["uv", "run", "ruff", "check", "--select", "C901"]
        + ["--config", f"lint.mccabe.max-complexity = {COMPLEXITY}"]
        + ["--output-format", "json", "--no-cache", "--ignore-noqa", *present],
        cwd=root,
        capture_output=True,
        text=True,
    )
    return complex_count(done.stdout, done.returncode, done.stderr)


def _suppressions(root: Path) -> int:
    """Return the comments that suppress a lint, type or coverage check."""
    found = 0
    for path in _modules(root, ROOTS):
        text = path.read_text(encoding="utf-8")
        for token in tokenize.generate_tokens(io.StringIO(text).readline):
            if token.type == tokenize.COMMENT and SUPPRESSION.search(token.string):
                found += 1
    return found


def _test_to_code(root: Path) -> float:
    """Return the test lines per code line; exit when there is no code."""
    code = _total_lines(root, CODE)
    if not code:
        sys.exit("no code lines")
    return round(_total_lines(root, ("tests",)) / code, 2)


def _pyproject(root: Path) -> dict:
    """Return the parsed `pyproject.toml`, empty when there is none."""
    path = root / "pyproject.toml"
    return tomllib.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _header_dependencies(path: Path) -> int:
    """Return the packages a module's PEP 723 header lists."""
    found = HEADER.search(path.read_text(encoding="utf-8"))
    if not found:
        return 0
    body = "".join(
        line[2:] if line.startswith("# ") else line[1:]
        for line in found["body"].splitlines(keepends=True)
    )
    return len(tomllib.loads(body).get("dependencies", []))


def _dependencies(root: Path) -> int:
    """Return the runtime packages: the project's and every script header's."""
    project = _pyproject(root).get("project", {}).get("dependencies", [])
    return len(project) + sum(
        _header_dependencies(path) for path in _modules(root, ROOTS)
    )


def _dev_dependencies(root: Path) -> int:
    """Return the packages across every `[dependency-groups]` list."""
    groups = _pyproject(root).get("dependency-groups", {})
    return sum(isinstance(item, str) for group in groups.values() for item in group)


def stale(report_tests: int, collected: int) -> bool:
    """Return whether a report counts other tests than the tree collects."""
    return report_tests != collected


def _collected(root: Path) -> int:
    """Return the tests pytest collects in the tree; exit with why if none."""
    done = subprocess.run(
        ["uv", "run", "pytest", "--collect-only", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    found = COLLECTED.search(done.stdout)
    if done.returncode != 0 or not found:
        sys.exit(f"pytest collection failed (exit {done.returncode})")
    return int(found.group(1))


def _elements(path: Path) -> list[tuple[str, dict[str, str]]]:
    """Return each element's name and attributes, in order; exit if unreadable.

    Expat, not `xml.etree`: Ruff's `S314` flags the latter.
    """
    elements: list[tuple[str, dict[str, str]]] = []
    parser = expat.ParserCreate()
    parser.StartElementHandler = lambda name, attrs: elements.append((name, attrs))
    try:
        parser.Parse(path.read_bytes(), True)
    except (OSError, expat.ExpatError):
        sys.exit(f"no readable {path.name}")
    return elements


def _report(root: Path) -> tuple[float, list[float]]:
    """Return the suite's seconds and each test's, from a report of this tree.

    A report that counts other tests than the tree collects is stale: exit.
    """
    elements = _elements(root / REPORT)
    suites = [attrs for name, attrs in elements if name == "testsuite"]
    if not suites or not suites[0].get("tests", "").isdigit():
        sys.exit(f"no testsuite in {REPORT.name}")
    if stale(int(suites[0]["tests"]), _collected(root)):
        sys.exit(f"{REPORT.name} is stale: it counts other tests than the tree")
    times = [float(attrs["time"]) for name, attrs in elements if name == "testcase"]
    return float(suites[0]["time"]), times


def _total_coverage(root: Path) -> float:
    """Return the gate's line coverage in percent, from a report of this tree."""
    _report(root)
    rates = [a["line-rate"] for n, a in _elements(root / COVERAGE) if n == "coverage"]
    return round(float(rates[0]) * 100, 2)


KINDS: dict[str, Callable[[Path], int | float]] = {
    "largest-module-lines": lambda root: max(
        (_lines(path) for path in _modules(root, ROOTS)), default=0
    ),
    "modules-over-1000-lines": lambda root: sum(
        _lines(path) > BIG_MODULE_LINES for path in _modules(root, ROOTS)
    ),
    "complex-functions": _complex_functions,
    "suppressions": _suppressions,
    "test-to-code-lines": _test_to_code,
    "python-lines": lambda root: _total_lines(root, ROOTS),
    "dependencies": _dependencies,
    "dev-dependencies": _dev_dependencies,
    "test-seconds": lambda root: round(_report(root)[0], 2),
    "slowest-test-seconds": lambda root: round(max(_report(root)[1], default=0), 2),
    "test-seconds-summed": lambda root: round(sum(_report(root)[1]), 2),
    "slow-tests": lambda root: sum(t > SLOW_SECONDS for t in _report(root)[1]),
    "total-coverage": _total_coverage,
}


def count(root: Path, kind: str) -> int | float:
    """Return the number a kind measures over the tree at `root`."""
    return KINDS[kind](root)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=sorted(KINDS))
    print(count(Path.cwd(), parser.parse_args().kind))
