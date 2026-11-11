"""The cut's fact placer and reader search: real git in a scratch repository.

Why: 0106-cut-scripts design D4.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import NamedTuple

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-cut-change" / "scripts" / "facts.py"


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("facts", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


facts = _load(_SCRIPT)

_LINES = "".join(f"line {n}\n" for n in range(1, 11))


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=mf", "-c", "user.email=mf@example.invalid"]
        + ["-c", "commit.gpgsign=false", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _repo(root: Path) -> tuple[Path, str]:
    """Commit `src/a.py` and `src/b.py` in a new repository; return it and the sha."""
    root.mkdir()
    _git(root, "init", "-q")
    (root / "src").mkdir()
    (root / "src" / "a.py").write_text(_LINES)
    (root / "src" / "b.py").write_text(_LINES)
    return root, _commit(root, "base")


def _commit(root: Path, message: str) -> str:
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", message)
    return _git(root, "rev-parse", "HEAD")


def _edit(root: Path, name: str, lines: list[str]) -> None:
    (root / name).write_text("".join(f"{line}\n" for line in lines))


def _old(*numbers: int) -> list[str]:
    return [f"line {n}" for n in numbers]


class _Outcome(NamedTuple):
    state: str
    cites: list[tuple[str, int, int]]


def _fact(sha: str, *cites: tuple[str, int, int]) -> object:
    return facts.Fact("a claim", [facts.Cite(*cite) for cite in cites], sha)


def _placed(root: Path, fact: object, monkeypatch: pytest.MonkeyPatch) -> _Outcome:
    monkeypatch.chdir(root)
    (placed,) = facts.place_all([fact])
    return _Outcome(placed.state, [tuple(cite) for cite in placed.cites])


def test_a_fact_on_an_untouched_path_stands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, sha = _repo(tmp_path / "repo")
    _edit(root, "src/b.py", ["changed"])
    _commit(root, "touch b")
    placed = _placed(root, _fact(sha, ("src/a.py", 3, 5)), monkeypatch)
    assert (placed.state, placed.cites) == ("stands", [facts.Cite("src/a.py", 3, 5)])


def test_a_fact_on_a_touched_path_whose_lines_held_stands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, sha = _repo(tmp_path / "repo")
    _edit(root, "src/a.py", [*_old(1, 2, 3, 4, 5, 6, 7, 8, 9), "tail", "added"])
    _commit(root, "touch the end")
    placed = _placed(root, _fact(sha, ("src/a.py", 2, 4)), monkeypatch)
    assert placed.state == "stands"


def test_a_fact_whose_lines_shifted_is_moved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, sha = _repo(tmp_path / "repo")
    _edit(root, "src/a.py", ["new 1", "new 2", *_old(*range(1, 11))])
    _edit(root, "src/b.py", _old(*range(4, 11)))
    _commit(root, "shift both")
    above = _placed(root, _fact(sha, ("src/a.py", 3, 5)), monkeypatch)
    assert (above.state, above.cites) == ("moved", [facts.Cite("src/a.py", 5, 7)])
    below = _placed(root, _fact(sha, ("src/b.py", 5, 5)), monkeypatch)
    assert (below.state, below.cites) == ("moved", [facts.Cite("src/b.py", 2, 2)])
    mixed = _placed(
        root, _fact(sha, ("src/a.py", 3, 5), ("src/b.py", 1, 1)), monkeypatch
    )
    assert mixed.state == "unplaced"
    both = _placed(
        root, _fact(sha, ("src/a.py", 3, 5), ("src/b.py", 5, 6)), monkeypatch
    )
    assert (both.state, both.cites) == (
        "moved",
        [facts.Cite("src/a.py", 5, 7), facts.Cite("src/b.py", 2, 3)],
    )


def test_an_insertion_between_two_cited_lines_is_unplaced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, sha = _repo(tmp_path / "repo")
    _edit(root, "src/a.py", [*_old(1, 2, 3), "between", *_old(4, 5, 6, 7, 8, 9, 10)])
    _commit(root, "insert inside")
    inside = _placed(root, _fact(sha, ("src/a.py", 2, 4)), monkeypatch)
    assert (inside.state, inside.cites) == ("unplaced", [facts.Cite("src/a.py", 2, 4)])
    after = _placed(root, _fact(sha, ("src/a.py", 4, 6)), monkeypatch)
    assert (after.state, after.cites) == ("moved", [facts.Cite("src/a.py", 5, 7)])
    before = _placed(root, _fact(sha, ("src/a.py", 1, 3)), monkeypatch)
    assert before.state == "stands"


def test_a_fact_on_a_changed_line_is_unplaced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, sha = _repo(tmp_path / "repo")
    _edit(root, "src/a.py", [*_old(1, 2), "edited", *_old(4, 5, 6, 7, 8, 9, 10)])
    _git(root, "rm", "-q", "src/b.py")
    (root / "src" / "c.py").write_text(_LINES)
    _commit(root, "edit, delete, add")
    edited = _placed(root, _fact(sha, ("src/a.py", 3, 3)), monkeypatch)
    assert edited.state == "unplaced"
    on_an_end = _placed(root, _fact(sha, ("src/a.py", 3, 5)), monkeypatch)
    assert on_an_end.state == "unplaced"
    inside = _placed(root, _fact(sha, ("src/a.py", 2, 4)), monkeypatch)
    assert (inside.state, inside.cites) == ("unplaced", [facts.Cite("src/a.py", 2, 4)])
    deleted = _placed(root, _fact(sha, ("src/b.py", 2, 4)), monkeypatch)
    assert deleted.state == "unplaced"
    one_of_two = _placed(
        root, _fact(sha, ("src/a.py", 8, 9), ("src/a.py", 3, 3)), monkeypatch
    )
    assert one_of_two.state == "unplaced"


def test_a_renamed_file_is_unplaced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, sha = _repo(tmp_path / "repo")
    _git(root, "mv", "src/a.py", "src/renamed.py")
    _commit(root, "rename")
    placed = _placed(root, _fact(sha, ("src/a.py", 2, 3)), monkeypatch)
    assert placed.state == "unplaced"


def test_a_fact_with_no_commit_or_a_bad_sha_is_unplaced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _repo(tmp_path / "repo")
    cite = ("src/a.py", 2, 3)
    for sha in ("--output=x", "HEAD", "abc", "0123456", "A" * 8):
        assert _placed(root, _fact(sha, cite), monkeypatch).state == "unplaced"
    assert not (root / "x").exists()


def _runner(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(facts, "RUNNER", (sys.executable,))


def _brief(root: Path, *lines: str) -> Path:
    brief = root / "brief.md"
    brief.write_text("## Facts\n\n" + "".join(f"- {line}\n" for line in lines))
    return brief


def test_readers_print_each_hit_or_none(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _ = _repo(tmp_path / "repo")
    _edit(root, "src/a.py", ["old_name = 1", "x = old_name + 1", "-dash"])
    _commit(root, "uses")
    (root / "src" / "untracked.py").write_text("old_name\n")
    monkeypatch.chdir(root)
    code = facts.main(["readers", "old_name", "gone", "--", "-dash"])
    assert code == 0
    assert capsys.readouterr().out.splitlines() == [
        "readers of old_name — old_name = 1 · src/a.py:1",
        "readers of old_name — x = old_name + 1 · src/a.py:2",
        "readers of gone — none · HEAD",
        "readers of -dash — -dash · src/a.py:3",
    ]


def _refused(capsys: pytest.CaptureFixture[str], *argv: str) -> str:
    assert facts.main(["readers", *argv]) == 2
    last = capsys.readouterr().out.splitlines()[-1]
    assert last.startswith("facts: cannot place — ")
    return last


def test_readers_refuse_a_bare_call_and_a_bad_signature(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _ = _repo(tmp_path / "repo")
    monkeypatch.chdir(root)
    notes = root / "notes.md"
    assert "a name" in _refused(capsys)
    assert "a name" in _refused(capsys, "--notes", str(notes))
    assert not notes.exists()
    for bad in ("", "a b", "x.y", "1x", "f(x)"):
        assert repr(bad) in _refused(capsys, "old", "--signature", bad)


def test_a_changed_signature_lists_its_stand_ins_and_monkeypatches(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _ = _repo(tmp_path / "repo")
    _edit(
        root,
        "src/a.py",
        [
            "def old_fn(x):",
            "old_fn = lambda x: x",
            "class old_fn:",
            "y = old_fn(1)",
            "def old_fn_two(x):",
            'monkeypatch.setattr(mod, "old_fn", fake)',
            'with patch("pkg.old_fn"):',
            "setattr(obj, old_fn, 1)",
            "xold_fn = lambda x: x",
        ],
    )
    _commit(root, "uses")
    notes = root / "notes.md"
    monkeypatch.chdir(root)
    code = facts.main(
        ["readers", "--signature", "old_fn", "--signature", "gone"]
        + ["--notes", str(notes)]
    )
    assert code == 0
    expected = [
        "stand-in of old_fn — def old_fn(x): · src/a.py:1",
        "stand-in of old_fn — old_fn = lambda x: x · src/a.py:2",
        "stand-in of old_fn — class old_fn: · src/a.py:3",
        'monkeypatch of old_fn — monkeypatch.setattr(mod, "old_fn", fake) · src/a.py:6',
        'monkeypatch of old_fn — with patch("pkg.old_fn"): · src/a.py:7',
        "stand-in of gone — none · HEAD",
        "monkeypatch of gone — none · HEAD",
    ]
    assert capsys.readouterr().out.splitlines() == expected
    assert notes.read_text().splitlines()[-len(expected) :] == [
        f"- {line}" for line in expected
    ]


def test_a_changed_file_lists_its_runpy_and_import_readers(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _ = _repo(tmp_path / "repo")
    _edit(
        root,
        "src/a.py",
        [
            'runpy.run_path("scripts/tool.py")',
            'argv = ["uv", "run", "--script", "tool.py"]',
            "import tool",
            "from tool import x",
            "import toolkit",
            'note = "other tool.py"',
            "tool = 1",
        ],
    )
    _commit(root, "uses")
    monkeypatch.chdir(root)
    assert (
        facts.main(["readers", "--file", "scripts/tool.py", "--file", "gone.py"]) == 0
    )
    assert capsys.readouterr().out.splitlines() == [
        'runpy reader of scripts/tool.py — runpy.run_path("scripts/tool.py")'
        " · src/a.py:1",
        'runpy reader of scripts/tool.py — argv = ["uv", "run", "--script", "tool.py"]'
        " · src/a.py:2",
        "import reader of scripts/tool.py — import tool · src/a.py:3",
        "import reader of scripts/tool.py — from tool import x · src/a.py:4",
        "runpy reader of gone.py — none · HEAD",
        "import reader of gone.py — none · HEAD",
    ]


def test_a_changed_string_lists_each_line_holding_it(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _ = _repo(tmp_path / "repo")
    _edit(root, "src/a.py", ["x = a.b(c)", "aa.b(c)d", "axb(c)", "-dash"])
    _commit(root, "uses")
    monkeypatch.chdir(root)
    argv = ["readers", "gone", "--string", "a.b(c)", "--string=-dash", "--string", "no"]
    assert facts.main(argv) == 0
    assert capsys.readouterr().out.splitlines() == [
        "readers of gone — none · HEAD",
        "string reader of a.b(c) — x = a.b(c) · src/a.py:1",
        "string reader of a.b(c) — aa.b(c)d · src/a.py:2",
        "string reader of -dash — -dash · src/a.py:4",
        "string reader of no — none · HEAD",
    ]


def test_the_notes_file_is_written_and_appended(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, sha = _repo(tmp_path / "repo")
    _edit(root, "src/a.py", ["new", *_old(*range(1, 11))])
    _commit(root, "shift")
    _runner(monkeypatch)
    monkeypatch.chdir(root)
    notes = root / "0106-x" / "cut-notes.md"
    notes.parent.mkdir()
    notes.write_text("stale\n")
    brief = _brief(
        root,
        f"a is here (`src/a.py:3-4` at `{sha}`)",
        f"b is there (`src/b.py:2` at `{sha}`)",
    )
    assert facts.main(["place", str(brief), "--notes", str(notes)]) == 0
    assert notes.read_text() == (
        "# 0106-x — cut notes\n\n"
        "- a is here — moved · src/a.py:4-5\n"
        "- b is there — stands · src/b.py:2\n"
    )
    assert facts.main(["readers", "line", "--notes", str(notes)]) == 0
    assert notes.read_text().startswith("# 0106-x — cut notes\n\n- a is here")
    assert notes.read_text().endswith("· src/b.py:10\n")
    assert "- readers of line — line 1 · src/a.py:2\n" in notes.read_text()
    capsys.readouterr()
    assert facts.main(["place", str(brief), "--at", sha]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "stands · a is here · src/a.py:3-4",
        "stands · b is there · src/b.py:2",
    ]


def test_what_cannot_be_read_exits_2(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, sha = _repo(tmp_path / "repo")
    good = _brief(root, f"a claim (`src/a.py:2` at `{sha}`)")
    bad = root / "bad.md"
    bad.write_text("## Facts\n\n- a claim (`a.py:2` at `abcdef1`)\n")
    garbage = root / "garbage.py"
    garbage.write_text("print('not json')\n")
    _runner(monkeypatch)
    monkeypatch.chdir(root)

    def exits_2(*argv: str) -> str:
        assert facts.main(list(argv)) == 2
        last = capsys.readouterr().out.splitlines()[-1]
        assert last.startswith("facts: cannot place — ")
        return last

    assert "no-such.md" in exits_2("place", "no-such.md")
    assert "fact 1" in exits_2("place", str(bad))
    assert "notes.md" in exits_2(
        "readers", "x", "--notes", str(root / "no" / "notes.md")
    )
    outside = tmp_path / "not-a-repo"
    outside.mkdir()
    (outside / "brief.md").write_text(good.read_text())
    assert "no-such-rev" in exits_2("place", str(good), "--at", "no-such-rev")
    assert "--at" in exits_2("place", str(good), "--at=--output=x")
    monkeypatch.chdir(outside)
    assert "git rev-parse failed" in exits_2("place", "brief.md")
    monkeypatch.chdir(root)
    monkeypatch.setattr(facts, "BRIEF_CHECK", garbage)
    assert "no JSON" in exits_2("place", str(good))
    monkeypatch.setattr(facts, "RUNNER", ("no-such-program-here",))
    assert "no-such-program-here" in exits_2("place", str(good))


def test_the_brief_reaches_the_placer(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, sha = _repo(tmp_path / "repo")
    _edit(root, "src/a.py", [*_old(1), "edited", *_old(3, 4, 5, 6, 7, 8, 9, 10)])
    _commit(root, "edit")
    brief = _brief(
        root,
        f"kept (`src/b.py:1-2` at `{sha}`)",
        f"gone (`./src/a.py:2` at `{sha}`)",
    )
    _runner(monkeypatch)
    monkeypatch.chdir(root)
    assert facts.main(["place", str(brief)]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "stands · kept · src/b.py:1-2",
        "unplaced · gone · src/a.py:2",
    ]
    empty = root / "empty.md"
    empty.write_text("# nothing\n")
    assert facts.main(["place", str(empty)]) == 0
    assert capsys.readouterr().out == ""


def test_the_script_runs_as_a_program(tmp_path: Path) -> None:
    root, _ = _repo(tmp_path / "repo")
    done = subprocess.run(
        [sys.executable, str(_SCRIPT), "readers", "line 2"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0
    assert done.stdout.splitlines()[0].startswith("readers of line 2 — line 2 · src/")
