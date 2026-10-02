"""A test the principles page names exists: a rename cannot orphan a principle."""

import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent

_NAMED_TEST = re.compile(r"`(tests/[A-Za-z0-9_/]+\.py)::([A-Za-z0-9_]+)`")


def missing_tests(text: str, root: Path) -> list[str]:
    """Return each backticked `tests/<file>.py::<name>` in `text` absent under `root`.

    e.g. "`tests/test_a.py::test_gone`" → ["tests/test_a.py::test_gone"]
    """
    missing: list[str] = []
    for file, name in _NAMED_TEST.findall(text):
        path = root / file
        defined = path.is_file() and re.search(
            rf"^def {re.escape(name)}\(", path.read_text(), re.MULTILINE
        )
        if not defined:
            missing.append(f"{file}::{name}")
    return missing


@pytest.mark.spec_exempt("structural — the principles page names only tests that exist")
def test_every_test_a_principle_names_exists() -> None:
    text = (_REPO / "docs" / "principles.md").read_text()

    assert missing_tests(text, _REPO) == []


@pytest.mark.spec_exempt("structural — the principles check bites")
def test_the_check_catches_a_named_test_that_does_not_exist(tmp_path: Path) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text(
        "def test_here() -> None:\n    pass\n"
    )
    page = (
        "- **Held by:** `tests/test_a.py::test_here`; `tests/test_a.py::test_gone`;\n"
        "  `tests/test_b.py::test_here`.\n"
    )

    assert missing_tests(page, tmp_path) == [
        "tests/test_a.py::test_gone",
        "tests/test_b.py::test_here",
    ]
