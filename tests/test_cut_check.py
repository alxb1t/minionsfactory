"""The cut's self-check rows: a scratch repository, a fake `openspec` on PATH.

Why: 0106-cut-scripts design D6.
"""

import importlib.util
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-cut-change" / "scripts" / "cut_check.py"
_ID = "0003-new"
_FOLDER = f"openspec/changes/{_ID}"
_FAKE = (
    "#!/bin/sh\n"
    '[ -z "$FAKE_OPENSPEC_FAIL" ] || { echo "Change is invalid" >&2; exit 1; }\n'
    "echo valid\n"
)
_JUDGED = ["I5", "I6", "I7", "I8", "I9", "I10", "I15", "I16", "P12", "P13"]

_PROPOSAL = """---
bump: minor
---

# Thing

One line.

## Why

Because.

## What Changes

- A thing.

## Capabilities

None.

## Impact

Edits the file `a.py`.

## Not in this change

- A thing.
"""

_DESIGN = """# Thing — design

One line.

## Context

Read at `HEAD`.

## Goals / Non-Goals

Goals.

## Decisions

| id | decision |
|---|---|
| [D1](#d1) | a thing |

### D1

The thing.

It keeps the line x.

## Tests

None.

## Dependencies

None.

## Risks / Trade-offs

None.

## Verdict

Ready.
"""

_TASKS = """# Thing — tasks

Build it.

## Progress

- [ ] 1 — First · hard
- [ ] 2 — Second **HUMAN**

## 1 — First

- [ ] 1.1 Edit `a.py` per [D1](design.md#d1).
  Verify: `grep -n x a.py` prints a line.

## 2 — Second

- [ ] 2.1 Run `make gate`.
  Verify: `git tag` prints v1.
"""

_SPEC = "## ADDED Requirements\n"


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("cut_check", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cut_check = _load(_SCRIPT)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=mf", "-c", "user.email=mf@example.invalid"]
        + ["-c", "commit.gpgsign=false", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _put(root: Path, name: str, text: str) -> None:
    (root / name).parent.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(text)


def _edit(root: Path, name: str, old: str, new: str) -> None:
    path = root / _FOLDER / name
    text = path.read_text()
    assert old in text
    path.write_text(text.replace(old, new, 1))


def _repo(tmp_path: Path) -> Path:
    """Commit `a.py` in a repository on `main`, and write a clean change beside it."""
    root = tmp_path / "primary"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    _put(root, "a.py", "x\n")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "base")
    _put(root, f"{_FOLDER}/proposal.md", _PROPOSAL)
    _put(root, f"{_FOLDER}/design.md", _DESIGN)
    _put(root, f"{_FOLDER}/tasks.md", _TASKS)
    _put(root, f"{_FOLDER}/.openspec.yaml", "schema: spec-driven\n")
    _put(root, f"{_FOLDER}/specs/thing/spec.md", _SPEC)
    return root


def _tools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Put a fake `openspec` first on PATH."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "openspec"
    fake.write_text(_FAKE)
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")


def _run(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    *argv: str,
) -> tuple[int, list[str]]:
    monkeypatch.chdir(root)
    code = cut_check.main([_ID, *argv])
    return code, capsys.readouterr().out.splitlines()


def _halted(lines: list[str]) -> list[str]:
    heads = [line.split(" — ") for line in lines if line.startswith("cut_check: halt")]
    return [head[1] for head in heads if len(head) > 2]


def test_a_clean_change_prints_its_judgment_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    _git(root, "checkout", "-q", "-b", "0002-open")
    _put(root, "b.py", "x\n")
    _git(root, "add", "b.py")
    _git(root, "commit", "-q", "-m", "open")
    _git(root, "checkout", "-q", "main")
    _edit(root, "proposal.md", "bump: minor\n", "bump: minor\nafter: [0002-open]\n")
    _tools(tmp_path, monkeypatch)
    code, lines = _run(root, monkeypatch, capsys, "--bump", "minor")
    assert code == 0
    judged = [
        line.split(" — ")[1] for line in lines if line.startswith("cut_check: judge")
    ]
    assert [row for row in judged if row in _JUDGED] == _JUDGED
    assert lines[-1].startswith("cut_check: ready — ")
    assert "cut_check: match — 1.1: a.py:1: x" in lines
    assert not _halted(lines)


def _no_spec(root: Path) -> None:
    (root / _FOLDER / "specs" / "thing" / "spec.md").unlink()


def _no_suffix(root: Path) -> None:
    _edit(root, "tasks.md", "- [ ] 1 — First · hard", "- [ ] 1 — First")


def _prose_dependencies(root: Path) -> None:
    _edit(root, "design.md", "## Dependencies\n\nNone.", "## Dependencies\n\nA lib.")


def _ritual(root: Path) -> None:
    _edit(root, "tasks.md", "1.1 Edit `a.py`", "1.1 Run `make gate` on `a.py`")


def _bad_bump(root: Path) -> None:
    _edit(root, "proposal.md", "bump: minor", "bump: major")


def _human_without_tasks(root: Path) -> None:
    text = "- [ ] 2.1 Run `make gate`.\n  Verify: `git tag` prints v1.\n"
    _edit(root, "tasks.md", text, "")


def _after_not_open(root: Path) -> None:
    _edit(root, "proposal.md", "bump: minor\n", "bump: minor\nafter: [0002-gone]\n")


def _headings_out_of_order(root: Path) -> None:
    _edit(root, "design.md", "## Context", "## Background")


def _proposal_ends_elsewhere(root: Path) -> None:
    (root / _FOLDER / "proposal.md").write_text(_PROPOSAL + "\n## Extra\n\nA.\n")


def _id_outside_a_link(root: Path) -> None:
    _edit(root, "tasks.md", "per [D1](design.md#d1)", "per D1 [D1](design.md#d1)")


def _four_lines(root: Path) -> None:
    _edit(root, "tasks.md", "Edit `a.py`", "Edit `a.py`\n  a\n  b\n  c")


def _check_before_its_task(root: Path) -> None:
    old = "Run `make gate`.\n  Verify: `git tag` prints v1."
    new = "Run `make gate` for x.\n  Verify: `grep -n x a.py` prints a line."
    _edit(root, "tasks.md", old, new)


def _selects_a_later_test(root: Path) -> None:
    old = "Verify: `grep -n x a.py` prints a line."
    new = "Verify: `uv run pytest -q test_widget.py -k widget` exits 0."
    _edit(root, "tasks.md", old, new)
    _edit(root, "tasks.md", "Run `make gate`.", "Add `test_widget` to the suite.")


def _git_grep_of_a_file_the_phase_adds(root: Path) -> None:
    old = "Verify: `grep -n x a.py` prints a line."
    _edit(root, "tasks.md", old, "Verify: `git grep -n x b.py` prints a line.")


def _needle_named_nowhere(root: Path) -> None:
    _edit(root, "design.md", "It keeps the line x.", "It keeps the line.")


def _pytest_names_no_test_file(root: Path) -> None:
    old = "Verify: `grep -n x a.py` prints a line."
    _edit(
        root,
        "tasks.md",
        old,
        "Verify: `uv run pytest -q --junitxml out/r.xml -k widget` exits 0.",
    )


def _impact_names_a_stranger(root: Path) -> None:
    old = "Edits the file `a.py`."
    _edit(root, "proposal.md", old, "Edits the files `a.py` and `b.py`.")


def _tests_names_a_stranger(root: Path) -> None:
    _edit(root, "design.md", "## Tests\n\nNone.", "## Tests\n\nAdds `tests/test_x.py`.")


def _table_without_a_heading(root: Path) -> None:
    old = "| [D1](#d1) | a thing |"
    _edit(root, "design.md", old, f"{old}\n| [D2](#d2) | b |")


def _link_without_a_heading(root: Path) -> None:
    old = "per [D1](design.md#d1)"
    _edit(root, "tasks.md", old, f"{old} and [D9](design.md#d9)")


def _constant_not_in_its_file(root: Path) -> None:
    old = "Edit `a.py` per [D1](design.md#d1)."
    _edit(root, "tasks.md", old, "Edit `a.py` per [D1](design.md#d1) for `MISSING`.")


def _cite_in_two_tasks(root: Path) -> None:
    old = "Edit `a.py` per [D1](design.md#d1)."
    _edit(root, "tasks.md", old, f"{old[:-1]} as at a.py:1.")
    _edit(root, "tasks.md", "Run `make gate`.", "Run `make gate` as at a.py:1.")


@pytest.mark.parametrize(
    ("row", "defect"),
    [
        ("I2", _no_spec),
        ("I4", _no_suffix),
        ("I11", _prose_dependencies),
        ("I12", _ritual),
        ("I13", _bad_bump),
        ("I14", _human_without_tasks),
        ("I17", _after_not_open),
        ("A1", _headings_out_of_order),
        ("A2", _proposal_ends_elsewhere),
        ("P9", _id_outside_a_link),
        ("P13", _four_lines),
        ("V1", _check_before_its_task),
        ("V2", _selects_a_later_test),
        ("V3", _git_grep_of_a_file_the_phase_adds),
        ("V4", _needle_named_nowhere),
        ("V5", _pytest_names_no_test_file),
        ("K1", _impact_names_a_stranger),
        ("K2", _tests_names_a_stranger),
        ("K3", _table_without_a_heading),
        ("K4", _link_without_a_heading),
        ("K5", _constant_not_in_its_file),
        ("K6", _cite_in_two_tasks),
    ],
)
def test_each_mechanical_row_fails_by_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    row: str,
    defect: Callable[[Path], None],
) -> None:
    root = _repo(tmp_path)
    defect(root)
    _tools(tmp_path, monkeypatch)
    code, lines = _run(root, monkeypatch, capsys)
    assert _halted(lines) == [row]
    assert code == 1
    assert lines[-1] == "cut_check: halt — 1 rows failed"


def test_a_bump_that_differs_from_the_given_one_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    _tools(tmp_path, monkeypatch)
    code, lines = _run(root, monkeypatch, capsys, "--bump", "patch")
    assert _halted(lines) == ["I13"]
    assert code == 1


def test_a_change_with_no_delta_holds_skip_specs_and_a_keep_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    _no_spec(root)
    _put(root, f"{_FOLDER}/.openspec.yaml", "schema: spec-driven\nskip_specs: true\n")
    _tools(tmp_path, monkeypatch)
    assert _halted(_run(root, monkeypatch, capsys)[1]) == ["I2"]
    _put(root, f"{_FOLDER}/specs/.gitkeep", "")
    assert _halted(_run(root, monkeypatch, capsys)[1]) == []
    _put(root, f"{_FOLDER}/specs/thing/spec.md", _SPEC)
    assert _halted(_run(root, monkeypatch, capsys)[1]) == ["I2"]


def test_a_missing_artifact_fails_i2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    (root / _FOLDER / "tasks.md").unlink()
    _tools(tmp_path, monkeypatch)
    code, lines = _run(root, monkeypatch, capsys)
    assert "cut_check: halt — I2 — tasks.md is missing" in lines
    assert code == 1


def test_a_dependencies_table_is_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    table = "| package | constraint | why |\n|---|---|---|\n| `x` | `>=1` | y |\n"
    _edit(root, "design.md", "## Dependencies\n\nNone.", f"## Dependencies\n\n{table}")
    _tools(tmp_path, monkeypatch)
    assert _halted(_run(root, monkeypatch, capsys)[1]) == []
    _edit(root, "design.md", "| package |", "| name |")
    assert _halted(_run(root, monkeypatch, capsys)[1]) == ["I11"]
    _edit(root, "design.md", "## Dependencies", "## Needs")
    assert _halted(_run(root, monkeypatch, capsys)[1]) == ["I11", "A1"]


def test_i4_names_each_defect_of_the_tasks_shape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    _tools(tmp_path, monkeypatch)
    _edit(root, "tasks.md", "## 1 — First", "## 3 — First")
    _edit(root, "tasks.md", "Verify: `grep -n x a.py` prints a line.", "")
    _edit(root, "tasks.md", "Build it.\n\n", "")
    _, lines = _run(root, monkeypatch, capsys)
    why = [line for line in lines if line.startswith("cut_check: halt — I4 — ")]
    assert why
    text = " ".join(why)
    assert "no `## 1 — …` section" in text
    assert "section 3 is not listed in `## Progress`" in text
    assert "1.1 has no Verify:" in text
    assert "`## Progress` does not follow the title and its line" in text
    # An unlisted phase's sub-task under a listed phase's section, then in its own.
    _edit(root, "tasks.md", "## 3 — First", "## 1 — First")
    _edit(root, "tasks.md", "- [ ] 2 — Second **HUMAN**\n", "")
    _edit(root, "tasks.md", "## 2 — Second\n\n", "")
    _, lines = _run(root, monkeypatch, capsys)
    why = " ".join(line for line in lines if line.startswith("cut_check: halt — I4 — "))
    assert "sub-task 2.1 is not of a listed phase" in why
    assert "sub-task 2.1 sits in section 1" not in why
    _edit(root, "tasks.md", "- [ ] 2.1 Run", "## 2 — Second\n\n- [ ] 2.1 Run")
    _, lines = _run(root, monkeypatch, capsys)
    why = " ".join(line for line in lines if line.startswith("cut_check: halt — I4 — "))
    assert "sub-task 2.1 is not of a listed phase" in why
    assert "section 2 is not listed in `## Progress`" in why


def test_a_ritual_is_each_station_the_build_owns(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    _tools(tmp_path, monkeypatch)
    for opening in (
        "Run `make check`",
        "Run `mf-simplify`",
        "Add a CHANGELOG entry",
        "Tick the box",
        "Commit the phase",
        "Tag the release",
        "Archive the change",
        "Release it",
    ):
        _edit(root, "tasks.md", "Edit `a.py`", opening)
        assert _halted(_run(root, monkeypatch, capsys)[1]) == ["I12"], opening
        _edit(root, "tasks.md", opening, "Edit `a.py`")
    _edit(root, "tasks.md", "Edit `a.py`", "**HALT CHECK** Commit it")
    assert _halted(_run(root, monkeypatch, capsys)[1]) == ["I12"]


def test_the_folded_checks_report_their_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    _tools(tmp_path, monkeypatch)
    monkeypatch.setenv("FAKE_OPENSPEC_FAIL", "1")
    code, lines = _run(root, monkeypatch, capsys)
    assert _halted(lines) == ["I3"]
    assert "  Change is invalid" in lines
    assert code == 1
    monkeypatch.delenv("FAKE_OPENSPEC_FAIL")
    _edit(root, "tasks.md", "1.1 Edit `a.py`", "1.1 Edit `Makefile`")
    _, lines = _run(root, monkeypatch, capsys)
    assert _halted(lines) == ["I18"]
    assert any(line.startswith("  ") and "1.1" in line for line in lines)
    _edit(root, "tasks.md", "1.1 Edit `Makefile`", "1.1 Edit `a.py`")
    _edit(root, "tasks.md", "`git tag` prints v1", "`cd x` prints a")
    _, lines = _run(root, monkeypatch, capsys)
    assert _halted(lines) == ["I19"]
    assert any(line.startswith("  2.1: I19") for line in lines)
    _edit(root, "tasks.md", "`cd x` prints a", "`git tag` prints v1")
    _edit(root, "tasks.md", "1.1 Edit `a.py`", "1.1 **CORPUS** `nope` Edit `a.py`")
    _, lines = _run(root, monkeypatch, capsys)
    assert _halted(lines) == ["corpus"]
    assert (
        "cut_check: halt — corpus — 1.1 — no case nope in scripts/corpus.toml" in lines
    )


def test_the_candidates_of_p12_and_p13_are_listed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    _tools(tmp_path, monkeypatch)
    _edit(root, "design.md", "Goals.", "It adds three files and 12 tests.")
    _edit(root, "design.md", "The thing.", "A. B. C. D.\n\n```\nfive files.\n```\n")
    code, lines = _run(root, monkeypatch, capsys)
    assert code == 0
    judge = [line for line in lines if line.startswith("cut_check: judge")]
    assert (
        "cut_check: judge — P12 — design.md:11: It adds three files and 12 tests."
        in judge
    )
    assert any(line.startswith("cut_check: judge — P13 — design.md:") for line in judge)
    assert not any("five files" in line for line in judge)


def test_what_cannot_be_checked_exits_2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    _tools(tmp_path, monkeypatch)
    held = root / _FOLDER
    held.rename(root / "held")
    code, lines = _run(root, monkeypatch, capsys)
    assert code == 2
    assert lines == [f"cut_check: cannot check — no {_FOLDER}/"]
    assert cut_check.main(["bad_id"]) == 2
    assert "is not <digits>-<slug>" in capsys.readouterr().out
    (root / "held").rename(held)
    tools = tmp_path / "tools"
    tools.mkdir()
    found = shutil.which("git")
    assert found
    (tools / "git").symlink_to(found)
    monkeypatch.setenv("PATH", str(tools))
    code, lines = _run(root, monkeypatch, capsys)
    assert code == 2
    assert lines == ["cut_check: cannot check — openspec is not on PATH"]


def test_a_script_that_cannot_run_exits_2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    _tools(tmp_path, monkeypatch)
    real = cut_check.GATE_CHECK
    stub = tmp_path / "stub.py"
    stub.write_text("print('gate: cannot check — x')\nraise SystemExit(2)\n")
    monkeypatch.setattr(cut_check, "GATE_CHECK", stub)
    code, lines = _run(root, monkeypatch, capsys)
    assert code == 2
    assert lines == ["cut_check: cannot check — gate: cannot check — x"]
    monkeypatch.setattr(cut_check, "GATE_CHECK", tmp_path / "missing.py")
    code, lines = _run(root, monkeypatch, capsys)
    assert code == 2
    assert lines[0].startswith("cut_check: cannot check — ")
    monkeypatch.setattr(cut_check, "GATE_CHECK", real)
    _edit(root, "tasks.md", "1.1 Edit `a.py`", "1.1 **CORPUS** `x` Edit `a.py`")
    _put(root, "scripts/corpus.toml", "not toml [\n")
    code, lines = _run(root, monkeypatch, capsys)
    assert code == 2
    assert lines[0].startswith("cut_check: cannot check — scripts/corpus.toml: ")


def test_a_fenced_block_does_not_count_toward_the_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    _tools(tmp_path, monkeypatch)
    block = (
        "Edit `Makefile`'s `gate` recipe per [D1](design.md#d1).\n"
        "  ```diff\n  + a\n  - b\n  ```"
    )
    _edit(root, "tasks.md", "Edit `a.py` per [D1](design.md#d1).", block)
    code, lines = _run(root, monkeypatch, capsys)
    assert _halted(lines) == []
    assert code == 0


def test_the_script_runs_as_a_program(tmp_path: Path) -> None:
    done = subprocess.run(
        [sys.executable, str(_SCRIPT), "bad_id"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 2
    assert done.stdout == "cut_check: cannot check — `bad_id` is not <digits>-<slug>\n"


def test_a_proposal_with_no_frontmatter_fails_i13(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    _tools(tmp_path, monkeypatch)
    _edit(root, "proposal.md", "---\nbump: minor\n---\n\n", "")
    code, lines = _run(root, monkeypatch, capsys)
    assert _halted(lines) == ["I13"]
    assert code == 1


def test_a_search_names_its_literal_needle() -> None:
    parts = cut_check.search_parts
    assert parts("git grep -n 'a b' -- x.py") == (["a b"], ["x.py"])
    two = "git grep -n -e 'one' -e 'two' HEAD -- x.py y.py"
    assert parts(two) == (["one", "two"], ["x.py", "y.py"])
    assert parts("grep -n a.b x.py") == ([], ["x.py"])
    assert parts("grep -n 'a\\|b' x.py") == ([], ["x.py"])
    assert parts("grep 'a\\-b' x.py") == (["a-b"], ["x.py"])
    assert parts("git grep -F -e 'a.b' x.py") == (["a.b"], ["x.py"])
    assert parts("grep -nF 'a.b' x.py") == (["a.b"], ["x.py"])
    assert parts("grep --fixed-strings a.b x.py") == (["a.b"], ["x.py"])
    assert parts("grep -ne a x.py") == (["a"], ["x.py"])
    assert parts("grep a x.py | wc -l") == (["a"], ["x.py"])
    assert parts("grep -n x") == (["x"], [])
    assert parts("grep") == ([], [])
    assert parts("make gate") == ([], [])
    assert parts("grep 'x") == ([], [])
    assert parts('git grep -nF "|" HEAD -- a.py') == (["|"], ["a.py"])
    assert parts("grep ';' a.py && ls") == ([";"], ["a.py"])
    assert parts("grep a\\;b a.py; ls") == (["a;b"], ["a.py"])
    assert parts("grep 'a' a.py \"|\" wc") == (["a"], ["a.py", "|", "wc"])
    assert cut_check._selected(
        "Verify: `pytest -k 'not widget and gadget'` passes.", cut_check._plan()
    ) == ["gadget"]
    assert (
        cut_check._selected(
            "Verify: `pytest -k 'not (a or b)'` passes.", cut_check._plan()
        )
        == []
    )


def test_a_pytest_command_names_a_test_path_or_none() -> None:
    plan = cut_check._plan()

    def halts(command: str) -> bool:
        change = cut_check.Change(
            "x", Path("x"), "", "", f"- [ ] 1.1 A.\n  Verify: `{command}`.\n"
        )
        return cut_check.row_v5(change, plan) is not None

    for none in ("pytest", 'pytest -m "not slow"', "pytest tests/", "uv run pytest -q"):
        assert halts(none)
    for named in ("pytest a.py", "pytest tests/test_a", "pytest t::test_a", "grep x"):
        assert not halts(named)


def test_a_decision_section_keeps_its_fenced_lines() -> None:
    text = "### D1\n\nA.\n\n```\n### D9\nB\n```\n\n### D2\n\nC.\n\n## Tests\n\nD.\n"
    found = cut_check.decision_texts(text)
    assert sorted(found) == ["d1", "d2"]
    assert "B" in found["d1"]
    assert "D." not in found["d2"]


def test_a_check_with_a_stray_backtick_names_no_command() -> None:
    plan = cut_check._plan()
    whole = "- [ ] 1.1 Edit.\n  Verify: `grep -n x a.py` prints a line."
    stray = "- [ ] 1.1 Edit.\n  Verify: `grep -n x a.py` prints a `line."
    assert cut_check._commands(plan["subtasks"](whole)[0].text, plan) == [
        "grep -n x a.py"
    ]
    assert cut_check._commands(plan["subtasks"](stray)[0].text, plan) == []


def test_k1_and_k2_read_each_side_of_the_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    _tools(tmp_path, monkeypatch)
    _put(root, "src/b.py", "x\n")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "more")
    first = "Edit `a.py` per [D1](design.md#d1)."
    _edit(root, "tasks.md", first, "Edit `a.py` and `src/b.py` per [D1](design.md#d1).")
    code, lines = _run(root, monkeypatch, capsys)
    assert _halted(lines) == ["K1"]
    assert "cut_check: halt — K1 — 1.1: `src/b.py` is absent from `## Impact`" in lines
    assert code == 1
    old = "Edits the file `a.py`."
    _edit(root, "proposal.md", old, "Edits the file `a.py` and the directory `src/`.")
    assert _halted(_run(root, monkeypatch, capsys)[1]) == []
    _edit(root, "tasks.md", "`src/b.py`", "`tests/test_y.py`")
    _edit(root, "proposal.md", " and the directory `src/`", "")
    assert _halted(_run(root, monkeypatch, capsys)[1]) == ["K2"]


def test_k5_reads_the_step_and_the_constant_of_the_one_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    _tools(tmp_path, monkeypatch)
    _put(root, "s.md", "## Step 1 — a\n\nWORD\n")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "more")
    _edit(root, "proposal.md", "Edits the file `a.py`.", "Edits `a.py` and `s.md`.")
    first = "Edit `a.py` per [D1](design.md#d1)."
    task = "Edit `s.md` at Step 1 for `WORD` per [D1](design.md#d1)."
    _edit(root, "tasks.md", first, task)
    assert _halted(_run(root, monkeypatch, capsys)[1]) == []
    _edit(root, "tasks.md", "Step 1", "Step 2")
    _edit(root, "tasks.md", "`WORD`", "`WORDS`")
    code, lines = _run(root, monkeypatch, capsys)
    assert _halted(lines) == ["K5"]
    assert "1.1: s.md has no `## Step 2` at HEAD" in lines[0]
    assert "1.1: s.md has no `WORDS` at HEAD" in lines[0]
    assert code == 1
    _edit(root, "tasks.md", "Edit `s.md`", "Add `s.md`")
    assert _halted(_run(root, monkeypatch, capsys)[1]) == []


def test_an_unreadable_head_exits_2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repo(tmp_path)
    _tools(tmp_path, monkeypatch)
    _git(root, "update-ref", "-d", "refs/heads/main")
    code, lines = _run(root, monkeypatch, capsys)
    assert code == 2
    assert lines[0].startswith("cut_check: cannot check — git ls-tree failed")
