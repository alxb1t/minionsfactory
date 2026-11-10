"""The docstring check: `C7` and `C3` held by the AST, over a temp repository.

Each case is source text for `check`, or files in a temp git repository for `main`.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "scripts" / "docstrings.py"
_LONG = 'def f() -> None:\n    """Do it.\n\n    One.\n    Two.\n    Three.\n    """\n'
_SPACED = 'def f() -> None:\n    """Do it.\n\n    One.\n\n    Two.\n    """\n'
_TWO_SENTENCES = 'class A:\n    """Do it. Then stop."""\n'
_OVER = "docstring runs over 3 non-blank lines"
_NOT_ONE = "docstring's first line is not one sentence"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("docstrings", _SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


docstrings = _load()


def _repo(root: Path) -> Path:
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    return root


def test_a_docstring_over_three_non_blank_lines_is_flagged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert docstrings.check(_LONG, "a.py") == [f"a.py:2: {_OVER}"]
    # A module and a class are read as a function is; a blank line is no line.
    module = '"""A.\n\nb\nc\nd\n"""\n' + _SPACED + _LONG.replace("f()", "g()")
    assert docstrings.check(module, "m.py") == [f"m.py:1: {_OVER}", f"m.py:15: {_OVER}"]
    assert docstrings.check(_SPACED, "b.py") == []
    # The script prints each site and exits 1; an untracked file is read.
    root = _repo(tmp_path / "repo")
    (root / "a.py").write_text(_LONG)
    monkeypatch.chdir(root)
    done = subprocess.run(
        [sys.executable, str(_SCRIPT)], capture_output=True, text=True
    )
    assert (done.returncode, done.stdout) == (1, f"a.py:2: {_OVER}\n")


def test_a_file_named_with_unicode_or_a_newline_is_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _repo(tmp_path / "repo")
    (root / "café.py").write_text(_LONG)
    (root / "a\nb.py").write_text(_LONG)
    monkeypatch.chdir(root)
    assert docstrings.main([]) == 1
    assert capsys.readouterr().out == f"a\nb.py:2: {_OVER}\ncafé.py:2: {_OVER}\n"


def test_a_first_line_of_two_sentences_is_flagged() -> None:
    assert docstrings.check(_TWO_SENTENCES, "a.py") == [f"a.py:2: {_NOT_ONE}"]
    assert docstrings.check('"""Do it.\n\nThen stop.\n"""\n', "b.py") == []
    assert docstrings.check('"""\nDo it. Then stop.\n"""\n', "c.py") == [
        f"c.py:1: {_NOT_ONE}"
    ]


def test_a_clean_file_prints_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path / "repo")
    (root / ".gitignore").write_text("ignored.py\n")
    (root / "clean.py").write_text(_SPACED)
    (root / "ignored.py").write_text(_LONG)
    (root / "gone.py").write_text(_LONG)
    subprocess.run(["git", "add", "gone.py"], cwd=root, check=True)
    (root / "gone.py").unlink()
    monkeypatch.chdir(root)
    assert docstrings.main([]) == 0
    assert capsys.readouterr().out == ""
