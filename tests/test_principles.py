"""A test the principles page names exists: a rename cannot orphan a principle."""

import ast
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent

_NAMED_TEST = re.compile(r"`(tests/[A-Za-z0-9_/]+\.py)::([A-Za-z0-9_]+)`")


def _top_level_functions(path: Path) -> set[str]:
    """Return the names of the functions `path` defines at module level."""
    tree = ast.parse(path.read_text())
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def missing_tests(text: str, root: Path) -> list[str]:
    """Return each backticked `tests/<file>.py::<name>` in `text` absent under `root`.

    e.g. "`tests/test_a.py::test_gone`" → ["tests/test_a.py::test_gone"]
    """
    missing: list[str] = []
    for file, name in _NAMED_TEST.findall(text):
        path = root / file
        if not path.is_file() or name not in _top_level_functions(path):
            missing.append(f"{file}::{name}")
    return missing


def test_every_test_a_principle_names_exists() -> None:
    text = (_REPO / "docs" / "principles.md").read_text()

    assert missing_tests(text, _REPO) == []


def test_the_check_catches_a_named_test_that_does_not_exist(tmp_path: Path) -> None:
    (tmp_path / "tests").mkdir()
    # A `def` inside a string defines nothing; a text match would count it.
    (tmp_path / "tests" / "test_a.py").write_text(
        "def test_here() -> None:\n    pass\n\n\n"
        'X = """\ndef test_in_text() -> None:\n"""\n'
    )
    page = (
        "- **Held by:** `tests/test_a.py::test_here`; `tests/test_a.py::test_gone`;\n"
        "  `tests/test_a.py::test_in_text`; `tests/test_b.py::test_here`.\n"
    )

    assert missing_tests(page, tmp_path) == [
        "tests/test_a.py::test_gone",
        "tests/test_a.py::test_in_text",
        "tests/test_b.py::test_here",
    ]
