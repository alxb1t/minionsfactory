"""Converge's evidence builders: a patch, a junit report and a design read to lines.

Each case is text for a builder; none runs git.
Why: 0110-gate-hardening design D6.
"""

import importlib.util
from pathlib import Path
from types import ModuleType

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-converge" / "scripts" / "evidence.py"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("evidence", _SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


evidence = _load()


def _patch(path: str, *body: str) -> str:
    head = f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n"
    return head + "@@ -10,9 +10,9 @@\n" + "".join(f"{line}\n" for line in body)


def test_the_candidates_are_the_names_a_patch_removes() -> None:
    patch = _patch(
        "skills/x/a.py",
        "-def old_name(x):",
        "-    async def method(self):",
        "-class Gone:",
        "-LIMIT = 3",
        "-def kept(x):",
        "+def kept(x, y):",
        "-    return 1",
        "-def two(): pass",
        "+def two_again(): pass",
    )
    patch += _patch("docs/guide.md", "-def prose_name():")
    patch += _patch("skills/x/b.py", "+def fresh():")
    patch += (
        "diff --git a/skills/x/old.py b/skills/x/old.py\n"
        "deleted file mode 100644\n"
        "--- a/skills/x/old.py\n+++ /dev/null\n@@ -1,2 +0,0 @@\n"
        "-def in_old():\n-    pass\n"
    )

    # A name the patch adds again is an edit, a name in a document is no code,
    # and a deleted file is named by its base name.
    assert evidence.candidates(patch) == [
        "old_name",
        "method",
        "Gone",
        "LIMIT",
        "two",
        "in_old",
        "old.py",
    ]
    assert evidence.candidates("") == []
    assert evidence.touched(patch) == {
        "skills/x/a.py",
        "docs/guide.md",
        "skills/x/b.py",
        "skills/x/old.py",
    }

    found = (
        "docs/guide.md:41:call old_name to start\n"
        "docs/guide.md:50:Gone and old_name\n"
        "docs/other.md:7:  see Gone here  \n"
        "skills/x/a.py:3:old_name = 1\n"
        "a line that is no match\n"
    )
    # A mention inside a file the patch changes is no candidate; a line holding
    # two names is listed once for each, and cut at 120 characters.
    assert evidence.stale(["old_name", "Gone"], found, {"skills/x/a.py"}) == [
        "old_name · docs/guide.md:41: call old_name to start",
        "old_name · docs/guide.md:50: Gone and old_name",
        "Gone · docs/guide.md:50: Gone and old_name",
        "Gone · docs/other.md:7: see Gone here",
    ]
    (long,) = evidence.stale(["n"], "a.md:1:n " + "x" * 200, set())
    assert len(long.split(": ", 1)[1]) == 120
    assert evidence.stale([], "", set()) == []


def test_a_test_is_read_with_its_seconds() -> None:
    patch = _patch(
        "tests/test_b.py",
        "+@pytest.mark.slow",
        "+def test_b() -> None:",
        "+    _main(conduct, root, 'run')",
        "+    assert x",
        "+    async def test_c(self):",
        "+def test_d() -> None:",
        '+    _main(conduct, root, "run", "x")',
        "+    _main(conduct, root, 'cut')",
    )
    report = (
        '<testsuites><testsuite><testcase classname="tests.test_b" name="test_b"'
        ' time="0.310"/><testcase classname="tests.test_b" name="test_c[1]"'
        ' time="0.100"><failure message="a &gt; b"/></testcase>'
        '<testcase classname="tests.test_b" name="test_c[2]" time="0.250"/>'
        '<testcase classname="tests.test_b" name="test_other" time="9"/>'
        "</testsuite></testsuites>"
    )

    assert evidence.test_cost(patch, report, "") == [
        "added · tests/test_b.py:11 · test_b · 0.31 s",
        "added · tests/test_b.py:14 · test_c · 0.35 s",
        "added · tests/test_b.py:15 · test_d · no time in the report",
        "slow · tests/test_b.py:10 · @pytest.mark.slow",
        "boot · tests/test_b.py:12 · _main(conduct, root, 'run')",
        'boot · tests/test_b.py:16 · _main(conduct, root, "run", "x")',
    ]
    # A test is timed by its own module: a name shared with another file is not summed.
    twin = (
        '<testcase classname="tests.test_a" name="test_main" time="0.1"/>'
        '<testcase classname="tests.test_b" name="test_main" time="9.0"/>'
    )
    assert evidence.test_cost(
        _patch("tests/test_a.py", "+def test_main(): ..."), twin, ""
    ) == ["added · tests/test_a.py:10 · test_main · 0.10 s"]
    # With no report every added test has no time, and none added reads None.
    assert evidence.test_cost(_patch("tests/t.py", "+def test_e(): ..."), "", "") == [
        "added · tests/t.py:10 · test_e · no time in the report"
    ]
    assert evidence.test_cost(_patch("a.py", "+x = 1"), "", "") == []


def _git(path: str, *body: str) -> str:
    # Git ends an unquoted name that holds a space with a tab.
    end = "\t" if " " in path else ""
    head = f"diff --git a/{path} b/{path}\n--- a/{path}{end}\n+++ b/{path}{end}\n"
    return head + "@@ -10,9 +10,9 @@\n" + "".join(f"{line}\n" for line in body)


def test_a_path_with_a_space_is_read_as_its_own_file() -> None:
    spaced = _git("tests/a b/x.py", "+def test_s(): ...")
    plain = _patch("a.py", "+x = 1")
    assert evidence.touched(spaced) == {"tests/a b/x.py"}
    assert evidence.touched(plain + spaced) == {"a.py", "tests/a b/x.py"}
    assert evidence.touched(spaced + plain) == {"a.py", "tests/a b/x.py"}
    assert evidence.test_cost(plain + spaced, "", "") == [
        "added · tests/a b/x.py:10 · test_s · no time in the report"
    ]
    # The header alone names a path whose two halves agree, quoted or not.
    deleted = "diff --git a/old name.py b/old name.py\ndeleted file mode 100644\n"
    assert evidence.candidates(deleted) == ["old name.py"]
    name = "caf\\303\\251.py"
    header = f'diff --git "a/{name}" "b/{name}"\nold mode 100644\nnew mode 100755\n'
    assert evidence.touched(header) == {"café.py"}
    # A deleted file is named by its `---` line, and its `+++ /dev/null` marks it gone.
    gone = (
        "diff --git a/tests/a b/old.py b/tests/a b/old.py\ndeleted file mode 100644\n"
        "--- a/tests/a b/old.py\t\n+++ /dev/null\n@@ -1,2 +0,0 @@\n-def old_fn():\n"
    )
    assert evidence.candidates(plain + gone) == ["old_fn", "old.py"]
    assert evidence.touched(gone) == {"tests/a b/old.py"}
    bare = (
        "diff --git a/tests/a b/old.py b/tests/a b/old.py\n--- a/tests/a b/old.py\t\n"
    )
    assert evidence.candidates(bare + "+++ /dev/null\n") == ["old.py"]


def test_a_file_is_named_by_its_header_lines_in_order() -> None:
    body = "@@ -10,9 +10,9 @@\n-def gone_fn():\n"
    moved = (
        "diff --git a/old.py b/new.py\nrename from old.py\n"
        f'rename to "caf\\303\\251.py"\n{body}'
    )
    both = f"diff --git a/p b/q\n--- a/old.py\n+++ b/new.py\n{body}"
    quoted = f'diff --git a/p b/q\n+++ "b/say \\"hi\\" \\\\ \\t.py"\n{body}'
    unnamed = f"diff --git a/p b/q\n{body}"
    assert evidence.touched(moved) == {"café.py"}
    assert evidence.touched(both) == {"new.py"}
    assert evidence.touched(quoted) == {'say "hi" \\ \t.py'}
    # The halves name two paths and no line says which is the file's: it is no file.
    assert evidence.touched(unnamed) == set()
    assert evidence.candidates(unnamed + moved) == ["gone_fn"]
    assert evidence.touched("@@ -1 +1 @@\n+x\n") == set()


def test_a_test_is_identified_by_its_module_class_and_name() -> None:
    report = (
        '<testcase classname="tests.test_a.TestFast" name="test_main" time="0.1"/>'
        '<testcase classname="tests.test_a.TestSlow" name="test_main" time="9.0"/>'
        '<testcase classname="tests.test_a.TestSlow" name="test_cut[1]" time="1.5"/>'
        '<testcase classname="tests.test_a.TestFast" name="test_cut[1]" time="0.1"/>'
        '<testcase classname="tests.test_a.TestFast" name="test_cut[2]" time="0.2"/>'
        '<testcase classname="tests.test_a.Outer.TestIn" name="test_in" time="2"/>'
    )

    def cost(*lines: str, header: str = "") -> list[str]:
        text = _patch("tests/test_a.py").removesuffix("\n") + f"{header}\n"
        return evidence.test_cost(text + "".join(f"{x}\n" for x in lines), report, "")

    # The class is the nearest less indented line above, a context line first.
    assert cost(" class TestFast:", " ", "+    def test_main(self): ...") == [
        "added · tests/test_a.py:12 · test_main · 0.10 s"
    ]
    # A removed line is not in the file, and the hunk header names the class above.
    assert cost(
        "-class TestSlow:", "+    def test_main(self): ...", header=" class TestFast:"
    ) == ["added · tests/test_a.py:10 · test_main · 0.10 s"]
    assert cost("+    def test_main(self): ...", header=" class TestSlow:") == [
        "added · tests/test_a.py:10 · test_main · 9.00 s"
    ]
    # A parametrized test sums within its own class alone; a nested class by its name.
    assert cost("+class TestFast:", "+    def test_cut(self): ...") == [
        "added · tests/test_a.py:11 · test_cut · 0.30 s"
    ]
    assert cost(" class TestIn:", "+    def test_in(self): ...") == [
        "added · tests/test_a.py:11 · test_in · 2.00 s"
    ]
    # No class in the patch: each class's time. A module-level test has none of its own.
    each = "test_main · 0.10 s in TestFast · 9.00 s in TestSlow"
    assert cost("+    def test_main(self): ...") == [
        f"added · tests/test_a.py:10 · {each}"
    ]
    assert cost("+def helper():", "+    def test_main(self): ...") == [
        f"added · tests/test_a.py:11 · {each}"
    ]
    assert cost("+def test_main(): ...") == [
        "added · tests/test_a.py:10 · test_main · no time in the report"
    ]
    assert cost("+    def test_none(self): ...") == [
        "added · tests/test_a.py:10 · test_none · no time in the report"
    ]


def test_a_removed_test_is_read_against_the_design() -> None:
    patch = _patch(
        "tests/test_a.py",
        "-def test_a() -> None:",
        "-    async def test_z(self):",
        "-def test_moved() -> None:",
        "+def test_moved() -> None:",
    )
    design = (
        "# D\n\nIt keeps test_z in prose.\n\n## Tests\n\n"
        "| unit | `tests/test_a.py` | `test_a`, `test_a_longer` |\n\n"
        "## Dependencies\n\nNone; test_z.\n"
    )

    # A test the patch removes and adds again is neither; test_z is named outside the
    # section only.
    assert evidence.test_cost(patch, "", design) == [
        "removed · test_a · named in ## Tests",
        "removed · test_z · not named in ## Tests",
    ]
    assert evidence.test_cost(patch, "", "# D\n\nNo tests section.\n") == [
        "removed · test_a · not named in ## Tests",
        "removed · test_z · not named in ## Tests",
    ]
    last = design.replace("## Dependencies\n\nNone; test_z.\n", "")
    assert (
        evidence.test_cost(patch, "", last)[0] == "removed · test_a · named in ## Tests"
    )


def test_a_section_is_capped() -> None:
    many = [f"line {n}" for n in range(evidence.LIMIT + 5)]
    sections = {"Gate integrity": many, "Plan check": ["plan: clean"], "Test cost": []}

    text = evidence.render("0001-a", "abcdef0123", "0123456789", sections)

    assert text.splitlines() == [
        "# Evidence — 0001-a · abcdef0..0123456",
        "",
        "Facts a tool found, not verdicts. Start from them; judge them.",
        "",
        "## Gate integrity",
        *many[: evidence.LIMIT],
        "… 5 more",
        "",
        "## Plan check",
        "plan: clean",
        "",
        "## Test cost",
        "None.",
    ]
    assert text.endswith("None.\n")
    exact = evidence.render("c", "a", "b", {"S": many[: evidence.LIMIT]})
    assert "more" not in exact
