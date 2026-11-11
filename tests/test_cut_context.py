"""The cut's context pack: real git in a scratch repository, `RUNNER` the interpreter.

Why: 0116-cut-diet design D4.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-cut-change" / "scripts" / "cut_context.py"


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("cut_context", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cut_context = _load(_SCRIPT)

_BRIEF = """\
# Cut diet · a minor · hard · 2026-11-11

**The cut reads its context once.**

At f349aa8, 2026-11-11.

## Decisions
| # | decision | the reason that settled it |
|---|---|---|
| Q1 | a pack | P11 |

## Dependencies

None.

## For the cut
1. **`cut-diet`** · `minor` · after: none · debt: none
   - models: build opus high · converge opus high · release opus high · cut opus high
"""


def _runner(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cut_context, "RUNNER", (sys.executable,))


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=mf", "-c", "user.email=mf@example.invalid"]
        + ["-c", "commit.gpgsign=false", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _repo(root: Path, files: dict[str, str]) -> str:
    """Commit `files` in a new repository; return the sha."""
    root.mkdir()
    _git(root, "init", "-q")
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text)
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "base")
    return _git(root, "rev-parse", "HEAD")


def test_the_brief_sections_come_from_brief_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    brief = tmp_path / "brief.md"
    brief.write_text(_BRIEF)
    _runner(monkeypatch)
    found = cut_context.brief_sections(brief)
    assert list(found) == [
        "# Cut diet · a minor · hard · 2026-11-11",
        "## Decisions",
        "## Dependencies",
        "## For the cut",
    ]
    assert found["## Dependencies"] == ["", "None.", ""]
    garbage = tmp_path / "garbage.py"
    garbage.write_text("print('not json')\n")
    monkeypatch.setattr(cut_context, "BRIEF_CHECK", garbage)
    with pytest.raises(cut_context.Stop) as stop:
        cut_context.brief_sections(brief)
    assert (stop.value.code, "no JSON" in str(stop.value)) == (2, True)
    monkeypatch.setattr(cut_context, "BRIEF_CHECK", _REPO / "no-such.py")
    with pytest.raises(cut_context.Stop) as stop:
        cut_context.brief_sections(brief)
    assert stop.value.code == 2
    monkeypatch.setattr(cut_context, "RUNNER", ("no-such-program-here",))
    with pytest.raises(cut_context.Stop) as stop:
        cut_context.brief_sections(brief)
    assert "no-such-program-here" in str(stop.value)


def _facts_brief(root: Path, *lines: str) -> Path:
    brief = root / "brief.md"
    brief.write_text("## Facts\n\n" + "".join(f"- {line}\n" for line in lines))
    return brief


def test_a_fact_is_listed_with_its_state_and_lines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ten = "".join(f"line {n}\n" for n in range(1, 11))
    root = tmp_path / "repo"
    sha = _repo(root, {"src/a.py": ten, "src/b.py": ten})
    (root / "src" / "a.py").write_text("new\n" + ten)
    (root / "src" / "b.py").write_text(ten.replace("line 3\n", "edited\n"))
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "edit")
    brief = _facts_brief(
        root,
        f"a moved (`src/a.py:3-4` at `{sha}`)",
        f"a gone (`src/b.py:3` at `{sha}`)",
    )
    _runner(monkeypatch)
    monkeypatch.chdir(root)
    text, placed = cut_context.facts_section(brief)
    assert [one.state for one in placed] == ["moved", "unplaced"]
    assert text == (
        "## The facts at HEAD\n\n"
        "### moved · a moved\n\n`src/a.py:4-5`\n~~~~\n4: line 3\n5: line 4\n~~~~\n\n"
        "### unplaced · a gone\n\n`src/b.py:3`\n~~~~\n3: edited\n~~~~"
    )
    empty = root / "empty.md"
    empty.write_text("# nothing\n")
    assert cut_context.facts_section(empty) == ("## The facts at HEAD\n\nNone.", [])
    bad = root / "bad.md"
    bad.write_text("## Facts\n\n- a claim (`a.py:2` at `abcdef1`)\n")
    with pytest.raises(cut_context.Stop) as stop:
        cut_context.facts_section(bad)
    assert (stop.value.code, "fact 1" in str(stop.value)) == (2, True)


def test_the_decisions_are_bundles_stdout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    _repo(
        root,
        {
            "docs/decisions.md": "# Decisions\n\n### D1 · One\n\nbody one\n\n"
            "### D2 · Two\n\nbody two\n",
        },
    )
    brief = root / "brief.md"
    brief.write_text("A cite of [D2](docs/decisions.md#d2--two).\n")
    _runner(monkeypatch)
    monkeypatch.chdir(root)
    assert cut_context.decisions_section(brief) == (
        "## The decisions\n\n"
        "## Decisions the change cites\n\n### D2 · Two\n\nbody two\n\n"
        "## Every decision\n\n- D1 · One\n- D2 · Two"
    )
    with pytest.raises(cut_context.Stop) as stop:
        cut_context.decisions_section(root / "no-such.md")
    assert (stop.value.code, "no-such.md" in str(stop.value)) == (2, True)
    monkeypatch.setattr(cut_context, "RUNNER", ("no-such-program-here",))
    with pytest.raises(cut_context.Stop) as stop:
        cut_context.decisions_section(brief)
    assert stop.value.code == 2


_SPEC = """\
# Capability: sdd

## Requirements

### Requirement: A gate runs

The gate SHALL run.

#### Scenario: It runs
- **WHEN** a station starts
- **THEN** it runs

### Requirement: A cache holds

The cache SHALL hold.

## Other

after the requirements
"""


def test_a_requirement_the_brief_names_is_read_in_full(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    _repo(root, {"openspec/specs/sdd/spec.md": _SPEC})
    brief = root / "brief.md"
    brief.write_text("The change MODIFIES a gate runs, and no other.\n")
    monkeypatch.chdir(root)
    named, index = cut_context.requirements_sections(brief)
    assert named == (
        "## The requirements the brief names\n\n"
        "### Requirement: A gate runs\n\nThe gate SHALL run.\n\n"
        "#### Scenario: It runs\n- **WHEN** a station starts\n- **THEN** it runs"
    )
    assert index == (
        "## Every requirement\n\nsdd:5 · A gate runs\nsdd:13 · A cache holds"
    )
    brief.write_text("A cache holds.\n")
    named, _ = cut_context.requirements_sections(brief)
    assert named == (
        "## The requirements the brief names\n\n"
        "### Requirement: A cache holds\n\nThe cache SHALL hold."
    )
    brief.write_text("nothing here\n")
    none, _ = cut_context.requirements_sections(brief)
    assert none == "## The requirements the brief names\n\nNone."
    (root / "openspec" / "specs" / "sdd" / "spec.md").unlink()
    assert cut_context.requirements_sections(brief)[1] == (
        "## Every requirement\n\nNone."
    )
    tail = root / "openspec" / "specs" / "tail" / "spec.md"
    tail.parent.mkdir()
    tail.write_text("### Requirement: A tail ends\n\nThe tail SHALL end.\n")
    brief.write_text("A tail ends.\n")
    assert cut_context.requirements_sections(brief) == (
        "## The requirements the brief names\n\n"
        "### Requirement: A tail ends\n\nThe tail SHALL end.",
        "## Every requirement\n\ntail:1 · A tail ends",
    )
    with pytest.raises(cut_context.Stop) as stop:
        cut_context.requirements_sections(root / "no-such.md")
    assert stop.value.code == 2


_DEBT = """\
# Backlog

## 0060-x

- **0060·S6 — on a cited file**
  - **What it affects:** `src/a.py:3`

- **0061·S1 — on another file**
  - **What it affects:** `src/zzz.py`

- **0113·S4 — listed by id**
  - **What it affects:** `src/yyy.py`
"""


def test_the_debt_cards_on_cited_files_and_listed_ids(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    sha = _repo(root, {"src/a.py": "one\ntwo\nthree\n"})
    brief = _facts_brief(root, f"a fact (`src/a.py:3` at `{sha}`)")
    monkeypatch.chdir(root)
    _runner(monkeypatch)
    _, placed = cut_context.facts_section(brief)
    assert cut_context.run_dir() == root.resolve() / ".minions"
    assert cut_context.debt_section(None, placed) == "## Debt cards\n\nNone."
    (root / ".minions").mkdir()
    (root / ".minions" / "debt.md").write_text(_DEBT)
    cited = "- **0060·S6 — on a cited file**\n  - **What it affects:** `src/a.py:3`"
    listed = "- **0113·S4 — listed by id**\n  - **What it affects:** `src/yyy.py`"
    assert cut_context.debt_section(None, placed) == f"## Debt cards\n\n{cited}"
    item = ["**`x`**", "`minor`", "after: none", "debt: [0113·S4, 9999·X1]"]
    assert cut_context.debt_section(item, placed) == (
        f"## Debt cards\n\n{cited}\n\n{listed}"
    )
    assert cut_context.debt_section(["debt: none"], []) == "## Debt cards\n\nNone."
    (root / ".minions" / "debt.md").write_bytes(b"\xff\xfe")
    with pytest.raises(cut_context.Stop) as stop:
        cut_context.debt_section(None, placed)
    assert stop.value.code == 2
    outside = tmp_path / "not-a-repo"
    outside.mkdir()
    monkeypatch.chdir(outside)
    with pytest.raises(cut_context.Stop) as stop:
        cut_context.run_dir()
    assert (stop.value.code, "git rev-parse" in str(stop.value)) == (2, True)


def _headings(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.startswith("#")]


def test_each_skeleton_holds_its_headings_in_order() -> None:
    skeletons = cut_context.SKELETONS
    assert list(skeletons) == [
        "proposal.md",
        "design.md",
        "tasks.md",
        "specs/<capability>/spec.md",
    ]
    assert _headings(skeletons["proposal.md"]) == [
        "# <Title>",
        "## Why",
        "## What Changes",
        "## Capabilities",
        "### New Capabilities",
        "### Modified Capabilities",
        "## Impact",
        "## Not in this change",
    ]
    assert skeletons["proposal.md"].startswith("---\nbump: <minor | patch>\n---\n")
    assert _headings(skeletons["design.md"]) == [
        "# <Title> — design",
        "## Context",
        "## Goals / Non-Goals",
        "## Decisions",
        "### D1",
        "## Tests",
        "## Dependencies",
        "## Risks / Trade-offs",
        "## Migration Plan",
        "## Verdict",
    ]
    assert _headings(skeletons["tasks.md"]) == [
        "# <Title> — tasks",
        "## Progress",
        "## <N> — <Title>",
    ]
    assert _headings(skeletons["specs/<capability>/spec.md"]) == [
        "## ADDED Requirements",
        "### Requirement: <title>",
        "#### Scenario: <name>",
        "## MODIFIED Requirements",
        "### Requirement: <an existing title, exactly>",
        "## REMOVED Requirements",
        "### Requirement: <an existing title, exactly>",
    ]
    delta = skeletons["specs/<capability>/spec.md"]
    assert "- **WHEN** " in delta and "- **THEN** " in delta
    assert "**Reason:** " in delta and "**Migration:** " in delta
    section = cut_context.skeletons_section()
    assert section.startswith("## The skeletons\n\n")
    positions = [section.index(f"### {name}") for name in skeletons]
    assert positions == sorted(positions)
    assert section.count("~~~~markdown\n") == len(skeletons)


_PACK_BRIEF = """\
# Cut diet · a minor · hard · 2026-11-11

**The cut reads its context once.**

At f349aa8, 2026-11-11.

## Facts
- a is here (`src/a.py:2-3` at `{sha}`)

## Decisions
| # | decision | the reason that settled it |
|---|---|---|
| Q1 | a gate runs, per [D1](docs/decisions.md#d1--one) | P11 |

## Dependencies

None.

## For the cut
1. **`cut-diet`** · `minor` · after: none · debt: [0113·S4]
   - models: build opus high · converge opus high · release opus high · cut opus high
"""

_HEADINGS = (
    "The brief",
    "The facts at HEAD",
    "The decisions",
    "The requirements the brief names",
    "Every requirement",
    "Debt cards",
    "The skeletons",
)


def _pack_repo(root: Path) -> Path:
    sha = _repo(
        root,
        {
            "src/a.py": "one\ntwo\nthree\nfour\n",
            "docs/decisions.md": "### D1 · One\n\nbody one\n",
            "openspec/specs/sdd/spec.md": _SPEC,
        },
    )
    (root / ".minions").mkdir()
    (root / ".minions" / "debt.md").write_text(_DEBT)
    brief = root / "brief.md"
    brief.write_text(_PACK_BRIEF.replace("{sha}", sha))
    return brief


def test_the_pack_and_the_notes_are_written_and_exit_by_the_facts(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    brief = _pack_repo(root)
    monkeypatch.chdir(root)
    _runner(monkeypatch)
    folder = root.resolve() / ".minions" / "changes" / "0116-cut-diet"
    assert cut_context.main([str(brief), "0116-cut-diet"]) == 0
    assert capsys.readouterr().out == (
        f"cut_context: pack — {folder / 'context.md'} · 1 facts, 0 unplaced\n"
    )
    text = (folder / "context.md").read_text()
    assert text.startswith("## The brief\n\n# Cut diet · a minor")
    positions = [text.index(f"\n## {heading}\n") for heading in _HEADINGS[1:]]
    assert positions == sorted(positions)
    assert "### stands · a is here\n\n`src/a.py:2-3`\n~~~~\n2: two\n3: three\n" in text
    assert "### D1 · One\n\nbody one" in text
    assert "### Requirement: A gate runs" in text
    assert "- **0113·S4 — listed by id**" in text
    assert (folder / "cut-notes.md").read_text() == (
        "# 0116-cut-diet — cut notes\n\n- a is here — stands · src/a.py:2-3\n"
    )
    (root / "src" / "a.py").write_text("one\nchanged\nthree\nfour\n")
    _git(root, "commit", "-q", "-am", "change a cited line")
    assert cut_context.main([str(brief), "0116-cut-diet"]) == 1
    assert capsys.readouterr().out.endswith("· 1 facts, 1 unplaced\n")
    assert "### unplaced · a is here\n\n`src/a.py:2-3`\n~~~~\n2: changed\n" in (
        (folder / "context.md").read_text()
    )
    assert "- a is here — unplaced · src/a.py:2-3\n" in (
        (folder / "cut-notes.md").read_text()
    )


def test_a_pack_that_cannot_be_written_exits_2(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    brief = _pack_repo(root)
    monkeypatch.chdir(root)
    _runner(monkeypatch)

    def exits_2(*argv: str) -> str:
        assert cut_context.main(list(argv)) == 2
        last = capsys.readouterr().out.splitlines()[-1]
        assert last.startswith(
            ("cut_context: cannot write — ", "facts: cannot place — ")
        )
        return last

    assert "no-such.md" in exits_2("no-such.md", "0116-cut-diet")
    for bad in ("cut-diet", "../x", "0116-Cut", "0116-"):
        assert bad in exits_2(str(brief), bad)
    folder = root.resolve() / ".minions" / "changes"
    folder.mkdir()
    (folder / "0116-cut-diet").write_text("a file, not a folder\n")
    assert "0116-cut-diet" in exits_2(str(brief), "0116-cut-diet")
    (folder / "0116-cut-diet").unlink()
    (folder / "0116-cut-diet").mkdir()
    (folder / "0116-cut-diet" / "context.md").symlink_to(root / "brief.md")
    assert "is a link" in exits_2(str(brief), "0116-cut-diet")
    (folder / "0116-cut-diet" / "context.md").unlink()
    (folder / "0116-cut-diet" / "context.md").mkdir()
    assert "context.md" in exits_2(str(brief), "0116-cut-diet")
    (folder / "0116-cut-diet" / "context.md").rmdir()
    (folder / "0116-cut-diet" / "cut-notes.md").mkdir()
    assert "cut-notes.md" in exits_2(str(brief), "0116-cut-diet")
    monkeypatch.setattr(cut_context, "FACTS", root / "no-such.py")
    assert "no-such.py" in exits_2(str(brief), "0116-cut-diet")
    monkeypatch.setattr(cut_context, "FACTS", root / "facts.txt")
    assert "facts.txt" in exits_2(str(brief), "0116-cut-diet")


def test_the_script_runs_as_a_program(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    brief = _pack_repo(root)
    done = subprocess.run(
        [sys.executable, str(_SCRIPT), str(brief), "0116-cut-diet"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert (done.returncode, done.stdout.startswith("cut_context: pack — ")) == (
        0,
        True,
    )
    assert (root / ".minions" / "changes" / "0116-cut-diet" / "context.md").is_file()


def test_the_item_of_a_slug_gives_its_parts() -> None:
    sections = {
        "## For the cut": [
            "1. **`other`** · `patch` · after: none",
            "   - models: build opus high",
            "2. **`cut-diet`** · `minor` · after: 0115-other · debt: [0113·S4]",
            "   - models: build opus high",
        ]
    }
    assert cut_context.item_parts(sections, "cut-diet") == [
        "**`cut-diet`**",
        "`minor`",
        "after: 0115-other",
        "debt: [0113·S4]",
    ]
    assert cut_context.item_parts(sections, "0116-cut-diet") is None
    assert cut_context.item_parts({}, "cut-diet") is None


def test_a_cite_is_read_at_head_and_cut_at_the_cap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    long = "".join(f"line {n}\n" for n in range(1, 201))
    root = tmp_path / "repo"
    _repo(root, {"src/a.py": long, "src/short.py": "one\ntwo\n"})
    (root / "src" / "a.py").write_text("edited in the tree\n")
    monkeypatch.chdir(root)
    assert cut_context.cite_lines(("src/a.py", 3, 5)) == [
        "3: line 3",
        "4: line 4",
        "5: line 5",
    ]
    cut = cut_context.cite_lines(("src/a.py", 10, 200))
    assert len(cut) == cut_context.SLICE_LINES + 1
    assert cut[0] == "10: line 10"
    assert cut[-2] == "89: line 89"
    assert cut[-1] == "… cut at 80 lines — src/a.py:90-200 not shown"
    exact = cut_context.cite_lines(("src/a.py", 1, cut_context.SLICE_LINES))
    assert len(exact) == cut_context.SLICE_LINES
    assert cut_context.cite_lines(("src/gone.py", 1, 2)) == [
        "src/gone.py — missing at HEAD"
    ]
    assert cut_context.cite_lines(("src/short.py", 5, 6)) == [
        "src/short.py:5-6 — past the end of the file, at 2"
    ]


_SCAFFOLD_BRIEF = """\
# Cut diet · a minor · hard · 2026-11-11

**The cut reads its context once.**

At f349aa8, 2026-11-11.

## Decisions
| # | decision | the reason that settled it |
|---|---|---|
| Q1 | a pack, `a | b` | P11 |
| Q2 | — | dropped |
| C1 | a scaffold |  |
| X9 | not a decision | no |

## Dependencies
| item | package | constraint | why |
|---|---|---|---|
| cut-diet | `markdown-it-py` | `>=3,<4` | parses |
| other | zzz | * | no |

## Phases
```
1  the pack ·
     hard
2  scaffold
   and V2 · moderate · extra
```

## Not in this
- the cut's model in code
- the plan-metrics defects

## For the cut
1. **`cut-diet`** · `minor` · after: 0115-a, 0115-b · beside: none · debt: [0113·S4]
   - models: build opus high · converge opus high · release opus high · cut opus high
"""


def _sections(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, text: str
) -> dict[str, list[str]]:
    brief = tmp_path / "brief.md"
    brief.write_text(text)
    _runner(monkeypatch)
    return cut_context.brief_sections(brief)


def test_the_proposal_scaffold_holds_the_frontmatter_and_what_is_out(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sections = _sections(tmp_path, monkeypatch, _SCAFFOLD_BRIEF)
    assert cut_context.title_of("cut-diet") == "Cut diet"
    assert cut_context.title_of("a") == "A"
    assert cut_context.proposal_text(sections, "cut-diet") == (
        "---\nbump: minor\nafter: [0115-a, 0115-b]\ndebt: [0113·S4]\n---\n\n"
        "# Cut diet\n\nThe cut reads its context once.\n\n"
        "## Not in this change\n\n"
        "- the cut's model in code\n- the plan-metrics defects\n"
    )
    bare = _SCAFFOLD_BRIEF.replace(
        " · after: 0115-a, 0115-b · beside: none · debt: [0113·S4]",
        " · beside: 0115-c · debt: none",
    ).replace("## Not in this\n- the cut's model in code\n", "")
    assert cut_context.proposal_text(
        _sections(tmp_path, monkeypatch, bare), "cut-diet"
    ).startswith("---\nbump: minor\nbeside: [0115-c]\n---\n\n# Cut diet\n")
    assert cut_context.proposal_text(
        _sections(
            tmp_path, monkeypatch, "# T\n\n## For the cut\n1. **`a`** · `patch`\n"
        ),
        "a",
    ) == ("---\nbump: patch\n---\n\n# A\n\n\n\n## Not in this change\n\nNone.\n")
    for missing in ("other", "a-b"):
        with pytest.raises(cut_context.Stop) as stop:
            cut_context.proposal_text(sections, missing)
        assert (stop.value.code, missing in str(stop.value)) == (2, True)
    short = _sections(tmp_path, monkeypatch, "## For the cut\n1. **`cut-diet`**\n")
    with pytest.raises(cut_context.Stop) as stop:
        cut_context.proposal_text(short, "cut-diet")
    assert stop.value.code == 2


def test_the_design_scaffold_numbers_the_decisions_and_lists_the_packages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sections = _sections(tmp_path, monkeypatch, _SCAFFOLD_BRIEF)
    assert cut_context.design_text(sections, "cut-diet") == (
        "# Cut diet — design\n\n## Decisions\n\n"
        "| id | decision | because | rejected |\n|---|---|---|---|\n"
        "| [D1](#d1) | a pack, `a | b` | P11 | — |\n"
        "| [D2](#d2) | a scaffold | — | — |\n\n"
        "## Dependencies\n\n"
        "| package | constraint | why |\n|---|---|---|\n"
        "| `markdown-it-py` | `>=3,<4` | parses |\n"
    )
    other = cut_context.design_text(sections, "other")
    assert other.endswith(
        "## Dependencies\n\n| package | constraint | why |\n"
        "|---|---|---|\n| zzz | * | no |\n"
    )
    none = _SCAFFOLD_BRIEF.replace(
        "| item | package | constraint | why |\n|---|---|---|---|\n", ""
    )
    text = cut_context.design_text(_sections(tmp_path, monkeypatch, none), "x")
    assert text.endswith("## Dependencies\n\nNone.\n")
    assert cut_context.design_text({}, "cut-diet") == (
        "# Cut diet — design\n\n## Decisions\n\n"
        "| id | decision | because | rejected |\n|---|---|---|---|\n\n"
        "## Dependencies\n\nNone.\n"
    )


def test_the_tasks_scaffold_lists_each_phase(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sections = _sections(tmp_path, monkeypatch, _SCAFFOLD_BRIEF)
    assert cut_context.phases(sections) == [
        ("1", "the pack", "hard"),
        ("2", "scaffold and V2", "moderate"),
    ]
    assert cut_context.tasks_text(sections) == (
        "## Progress\n\n"
        "- [ ] 1 — the pack · hard\n- [ ] 2 — scaffold and V2 · moderate\n\n"
        "## 1 — the pack\n\n## 2 — scaffold and V2\n"
    )
    loose = "## Phases\n   stray\nnot a head\n1  a · b · hard\n  c\n"
    assert cut_context.phases(_sections(tmp_path, monkeypatch, loose)) == [
        ("1", "a · b", "hard")
    ]
    for text, said in (
        ("## Phases\n1  a\n2  b · hard\n", "phase 1 has no rating"),
        ("## Phases\n", "holds no phase"),
        ("# T\n", "holds no phase"),
    ):
        with pytest.raises(cut_context.Stop) as stop:
            cut_context.tasks_text(_sections(tmp_path, monkeypatch, text))
        assert (stop.value.code, said in str(stop.value)) == (1, True)


def test_the_scaffold_refuses_a_file_that_exists(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    brief = root / "brief.md"
    brief.write_text(_SCAFFOLD_BRIEF)
    monkeypatch.chdir(root)
    _runner(monkeypatch)
    folder = root / "openspec" / "changes" / "0116-cut-diet"
    names = ("proposal.md", "design.md", "tasks.md")

    def scaffold(*extra: str) -> tuple[int, str]:
        code = cut_context.main([str(brief), "0116-cut-diet", "--scaffold", *extra])
        return code, capsys.readouterr().out

    folder.mkdir(parents=True)
    (folder / "design.md").write_text("mine\n")
    code, out = scaffold()
    assert (code, "design.md exists, none written" in out) == (1, True)
    assert sorted(path.name for path in folder.iterdir()) == ["design.md"]
    (folder / "design.md").unlink()
    (folder / "tasks.md").symlink_to(root / "nowhere")
    assert scaffold()[0] == 1
    assert sorted(path.name for path in folder.iterdir()) == ["tasks.md"]
    (folder / "tasks.md").unlink()
    assert scaffold() == (
        0,
        "cut_context: scaffold — openspec/changes/0116-cut-diet"
        " · proposal.md, design.md, tasks.md\n",
    )
    written = {name: (folder / name).read_text() for name in names}
    assert written["tasks.md"].startswith("# Cut diet — tasks\n\n## Progress\n")
    assert written["design.md"].startswith("# Cut diet — design\n")
    assert written["proposal.md"].startswith("---\nbump: minor\n")
    assert str(brief) not in "".join(written.values())
    code, out = scaffold()
    assert (code, "proposal.md exists, none written" in out) == (1, True)
    assert {name: (folder / name).read_text() for name in names} == written
    unrated = root / "unrated.md"
    unrated.write_text(_SCAFFOLD_BRIEF.replace(" · moderate", ""))
    assert cut_context.main([str(unrated), "0117-cut-diet", "--scaffold"]) == 1
    assert "phase 2 has no rating" in capsys.readouterr().out
    assert not (root / "openspec" / "changes" / "0117-cut-diet").exists()
    assert cut_context.main([str(brief), "0117-other", "--scaffold"]) == 2
    assert "`other`" in capsys.readouterr().out
    assert cut_context.main([str(brief), "cut-diet", "--scaffold"]) == 2
    assert "no change id" in capsys.readouterr().out
