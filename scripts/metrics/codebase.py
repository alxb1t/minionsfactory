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

ROOTS = ("skills", "scripts", "tests")
CODE = ("skills", "scripts")
BIG_MODULE_LINES = 1000
COMPLEXITY = 10
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
}


def count(root: Path, kind: str) -> int | float:
    """Return the number a kind measures over the tree at `root`."""
    return KINDS[kind](root)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=sorted(KINDS))
    print(count(Path.cwd(), parser.parse_args().kind))
