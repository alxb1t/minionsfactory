# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Print each docstring over the comment limit or with a first line of two sentences.

Exit 0 none · 1 any. Why: 0110-gate-hardening design D2.
"""

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path

TIMEOUT_SECONDS = 600
MAX_LINES = 3
SECOND_SENTENCE = re.compile(r"\. [A-Z]")
OWNERS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def check(source: str, name: str) -> list[str]:
    """Return `<path>:<line>: <what>` for each docstring that breaks `C7` or `C3`.

    e.g. `a.py:2: docstring runs over 3 non-blank lines`
    """
    found: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, OWNERS):
            continue
        doc = ast.get_docstring(node, clean=False)
        if doc is None:
            continue
        line = node.body[0].lineno
        if sum(1 for row in doc.splitlines() if row.strip()) > MAX_LINES:
            found.append((line, f"docstring runs over {MAX_LINES} non-blank lines"))
        if SECOND_SENTENCE.search(doc.strip().partition("\n")[0]):
            found.append((line, "docstring's first line is not one sentence"))
    return [f"{name}:{line}: {what}" for line, what in sorted(found)]


def main(argv: list[str] | None = None) -> int:
    """Print each site in the tracked and new Python files; return 1 on any."""
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    listed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "--", "*.py"],
        capture_output=True,
        text=True,
        check=True,
        timeout=TIMEOUT_SECONDS,
    )
    lines = [
        line
        for name in sorted(set(listed.stdout.splitlines()))
        if Path(name).is_file()
        for line in check(Path(name).read_text(encoding="utf-8"), name)
    ]
    if lines:
        print(*lines, sep="\n")
    return 1 if lines else 0


if __name__ == "__main__":
    sys.exit(main())
