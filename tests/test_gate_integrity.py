"""Converge's gate integrity: a frozen patch read to the lines a worker starts from.

Each case is patch text for `lines`, or a patch file for `main`.
Why: 0110-gate-hardening design D5.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-converge" / "scripts" / "gate_integrity.py"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("gate_integrity", _SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate_integrity = _load()


def _patch(path: str, *body: str) -> str:
    head = f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n"
    return head + "@@ -10,9 +10,9 @@\n" + "".join(f"{line}\n" for line in body)


_HUNK = "@@ -10,9 +10,9 @@\n"


def test_a_path_with_a_space_or_quotes_keeps_its_own_lines() -> None:
    plain = _patch("a.py", "+y = 1  # noqa: B")
    # Git ends an unquoted name that holds a space with a tab; the header holds ` b/`.
    spaced = (
        "diff --git a/tests/a b/x.py b/tests/a b/x.py\n"
        "--- a/tests/a b/x.py\t\n+++ b/tests/a b/x.py\t\n"
        f"{_HUNK}+x = f()  # noqa: A\n"
    )
    name = "caf\\303\\251.py"
    quoted = (
        f'diff --git "a/{name}" "b/{name}"\n--- "a/{name}"\n+++ "b/{name}"\n'
        f"{_HUNK}+z = 1  # noqa: C\n"
    )
    assert gate_integrity.lines(spaced) == [
        "noqa · tests/a b/x.py:10 · x = f()  # noqa: A"
    ]
    # Each file keeps its own lines, whichever comes first.
    assert gate_integrity.lines(plain + spaced) == [
        "noqa · a.py:10 · y = 1  # noqa: B",
        "noqa · tests/a b/x.py:10 · x = f()  # noqa: A",
    ]
    assert gate_integrity.lines(spaced + plain) == [
        "noqa · tests/a b/x.py:10 · x = f()  # noqa: A",
        "noqa · a.py:10 · y = 1  # noqa: B",
    ]
    # A quoted name is the UTF-8 its bytes spell, from its `+++` line or its header.
    assert gate_integrity.lines(plain + quoted) == [
        "noqa · a.py:10 · y = 1  # noqa: B",
        "noqa · café.py:10 · z = 1  # noqa: C",
    ]
    only_header = f'diff --git "a/{name}" "b/{name}"\n{_HUNK}+z = 1  # noqa: C\n'
    assert gate_integrity.lines(only_header) == ["noqa · café.py:10 · z = 1  # noqa: C"]


def test_a_quoted_name_is_unquoted_as_git_quotes_it() -> None:
    for quoted, path in (
        (r'"b/tab\there.py"', "tab\there.py"),
        (r'"b/say \"hi\" \\.py"', 'say "hi" \\.py'),
        (r'"b/\a\b\n\v\f\r.py"', "\a\b\n\v\f\r.py"),
    ):
        patch = f"diff --git a/x b/y\n+++ {quoted}\n{_HUNK}+z = 1  # noqa: C\n"
        assert gate_integrity.lines(patch) == [f"noqa · {path}:10 · z = 1  # noqa: C"]


def test_a_file_is_named_by_its_header_lines_in_order() -> None:
    body = f"{_HUNK}-    assert x\n+    assert y  # noqa: A\n"
    gone = f"diff --git a/gone.py b/gone.py\n--- a/gone.py\n+++ /dev/null\n{body}"
    moved = (
        "diff --git a/old.py b/new.py\nrename from old.py\n"
        f'rename to "caf\\303\\251.py"\n{body}'
    )
    both = "diff --git a/p b/q\n--- a/old.py\n+++ b/new.py\n" + body
    fresh = f"diff --git a/new.py b/new.py\n--- /dev/null\n+++ b/new.py\n{body}"
    assert [line.split(" · ")[1] for line in gate_integrity.lines(gone)] == [
        "gone.py:10",
        "gone.py:10",
    ]
    assert gate_integrity.lines(moved)[0].split(" · ")[1] == "café.py:10"
    # The `+++` name wins; an added file names itself by it too.
    assert gate_integrity.lines(both)[0].split(" · ")[1] == "new.py:10"
    assert gate_integrity.lines(fresh)[0].split(" · ")[1] == "new.py:10"


def test_a_hunk_of_a_file_with_no_path_reads_no_line() -> None:
    plain = _patch("a.py", "+y = 1  # noqa: B")
    unnamed = f"diff --git a/p b/q\n{_HUNK}+x = 1  # noqa: A\n"
    stray = f"{_HUNK}+x = 1  # noqa: A\n"
    # The two halves name two paths and no line says which is the file's.
    assert gate_integrity.lines(unnamed) == []
    assert gate_integrity.lines(stray + plain) == ["noqa · a.py:10 · y = 1  # noqa: B"]
    # A file opened after a named one starts with no path.
    assert gate_integrity.lines(plain + unnamed) == [
        "noqa · a.py:10 · y = 1  # noqa: B"
    ]


def test_an_added_noqa_is_a_line() -> None:
    added = _patch("skills/x/a.py", " ctx", "+x = f()  # noqa: BLE001")
    assert gate_integrity.lines(added) == [
        "noqa · skills/x/a.py:11 · x = f()  # noqa: BLE001"
    ]
    # Only an added line counts, and its text is cut at 120 characters.
    assert gate_integrity.lines(_patch("a.py", "-x = f()  # noqa: BLE001")) == []
    (long,) = gate_integrity.lines(_patch("a.py", "+x = 1  # noqa: " + "a" * 200))
    assert len(long.split(" · ", 2)[2]) == 120


def test_an_added_type_ignore_is_a_line() -> None:
    patch = _patch("a.py", "+x = f()  # type: ignore[arg]", "+y = g()  # ty: ignore[z]")
    assert gate_integrity.lines(patch) == [
        "type-ignore · a.py:10 · x = f()  # type: ignore[arg]",
        "type-ignore · a.py:11 · y = g()  # ty: ignore[z]",
    ]


def test_an_added_no_cover_pragma_is_a_line() -> None:
    patch = _patch("a.py", "+if x:  # pragma: no cover")
    assert gate_integrity.lines(patch) == [
        "no-cover · a.py:10 · if x:  # pragma: no cover"
    ]


def test_an_added_skip_is_a_line() -> None:
    patch = _patch(
        "tests/test_a.py",
        "+@pytest.mark.skip",
        '+@pytest.mark.skipif(sys.platform == "win32")',
        '+    pytest.skip("later")',
    )
    assert [line.split(" · ")[0] for line in gate_integrity.lines(patch)] == [
        "skip"
    ] * 3


def test_an_added_xfail_is_a_line() -> None:
    patch = _patch("tests/test_a.py", "+@pytest.mark.xfail", '+    pytest.xfail("x")')
    assert gate_integrity.lines(patch) == [
        "xfail · tests/test_a.py:10 · @pytest.mark.xfail",
        'xfail · tests/test_a.py:11 · pytest.xfail("x")',
    ]


def test_an_added_allowlist_line_is_a_line() -> None:
    body = ("+paths = ['a']", "+# a comment", "+", "-paths = ['b']")
    assert gate_integrity.lines(_patch(".betterleaks.toml", *body)) == [
        "allowlist · .betterleaks.toml:10 · paths = ['a']"
    ]
    assert gate_integrity.lines(_patch("other.toml", *body)) == []


def test_an_added_swallow_is_a_line() -> None:
    one = _patch("a.py", "+    except OSError: pass")
    assert gate_integrity.lines(one) == ["swallow · a.py:10 · except OSError: pass"]
    two = _patch("a.py", "+    except OSError:  # noqa: BLE001", "+        pass")
    assert [line.split(" · ")[0] for line in gate_integrity.lines(two)] == [
        "noqa",
        "swallow",
    ]
    # A pass under a context `except` is one; a raise or a far hunk's pass is not.
    assert gate_integrity.lines(
        _patch("a.py", "     except OSError:", "+        pass")
    ) == ["swallow · a.py:10 · except OSError:"]
    assert (
        gate_integrity.lines(_patch("a.py", "+    except OSError:", "+        raise"))
        == []
    )
    apart = (
        _patch("a.py", "+    except OSError:") + "@@ -40,1 +40,1 @@\n+        pass\n"
    )
    assert gate_integrity.lines(apart) == []


def test_a_removed_test_is_a_line() -> None:
    patch = _patch(
        "tests/test_a.py", " ctx", "-def test_a() -> None:", "+def test_b() -> None:"
    )
    assert gate_integrity.lines(patch) == [
        "test-removed · tests/test_a.py:11 · def test_a() -> None:"
    ]


def test_a_removed_assert_is_a_line() -> None:
    patch = _patch(
        "tests/test_a.py", "-    assert x == 1", "-    assertion = 2", "+    assert y"
    )
    assert gate_integrity.lines(patch) == [
        "assert-removed · tests/test_a.py:10 · assert x == 1"
    ]


def test_a_pyproject_line_is_a_line() -> None:
    patch = _patch(
        "pyproject.toml",
        '+select = ["E"]',
        '-ignore = ["S"]',
        '+    "ruff>=0.16.3",',
        '+version = "0.92.0"',
        "+",
    )
    assert gate_integrity.lines(patch) == [
        'pyproject · pyproject.toml:10 · select = ["E"]',
        'pyproject · pyproject.toml:10 · ignore = ["S"]',
    ]


def test_a_moved_line_is_no_line() -> None:
    patch = _patch(
        "tests/test_a.py",
        "-    def test_a(self) -> None:",
        " ctx",
        "+def test_a(self) -> None:",
    )
    assert gate_integrity.lines(patch) == []
    # A move is within one file, and each removal pairs with one addition.
    elsewhere = _patch("a.py", "-def test_a() -> None:") + _patch(
        "b.py", "+def test_a() -> None:"
    )
    assert gate_integrity.lines(elsewhere) == [
        "test-removed · a.py:10 · def test_a() -> None:"
    ]
    twice = _patch(
        "a.py", "-y = 1  # noqa: A", "+y = 1  # noqa: A", "+y = 1  # noqa: A"
    )
    assert gate_integrity.lines(twice) == ["noqa · a.py:11 · y = 1  # noqa: A"]


def test_a_patch_is_read_by_its_hunks() -> None:
    # `+++ ` in a hunk is an added line; a no-newline mark and a bare blank line pass.
    patch = (
        "diff --git a/old.py b/new.py\nrename from old.py\nrename to new.py\n"
        "--- a/old.py\n+++ b/new.py\n@@ -1,3 +1,3 @@\n\n+++ x  # noqa: A\n"
        "\\ No newline at end of file\n+y  # noqa: B\n"
    )
    assert gate_integrity.lines(patch) == [
        "noqa · new.py:2 · ++ x  # noqa: A",
        "noqa · new.py:3 · y  # noqa: B",
    ]
    assert gate_integrity.lines("@@ -1 +1 @@\n+x  # noqa: A\n") == []


def test_main_prints_each_line_or_none(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    patch = tmp_path / "diff.patch"
    patch.write_text(_patch("a.py", "+x  # noqa: A", "-    assert y"))
    assert gate_integrity.main([str(patch)]) == 0
    assert (
        capsys.readouterr().out
        == "noqa · a.py:10 · x  # noqa: A\nassert-removed · a.py:10 · assert y\n"
    )
    patch.write_text(_patch("a.py", "+x = 1"))
    assert gate_integrity.main([str(patch)]) == 0
    assert capsys.readouterr().out == "None.\n"
    # The script run as a file reads a patch the same way.
    done = subprocess.run(
        [sys.executable, str(_SCRIPT), str(patch)], capture_output=True, text=True
    )
    assert (done.returncode, done.stdout) == (0, "None.\n")


def test_main_stops_on_an_unreadable_patch(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_path / "none.patch"
    assert gate_integrity.main([str(missing)]) == 2
    assert capsys.readouterr().out.startswith(f"gate integrity: cannot read {missing}")
    binary = tmp_path / "bin.patch"
    binary.write_bytes(b"\xff\xfe")
    assert gate_integrity.main([str(binary)]) == 2
    assert "invalid start byte" in capsys.readouterr().out
