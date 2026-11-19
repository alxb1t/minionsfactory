"""The findings file's writer and parser in the home, each name a case.

Why: 0138-findings design D1, and D4 to D12 for the `test_fix_*` cases.
"""

import os
from pathlib import Path

import pytest
from mflib import findings

# The card: its title, its fields and their words.


def _card(ident: str, **fields: str) -> str:
    lines = "".join(f"  - **{name}:** {value}\n" for name, value in fields.items())
    return f"- **{ident} — a finding**\n{lines}"


def test_card_blocks_are_each_roles_blocking_grades() -> None:
    assert findings.BLOCKS == {
        "conformance": ("blocking",),
        "adversarial": ("critical", "high"),
    }
    for role, grade, blocking in (
        ("conformance", "blocking", True),
        ("conformance", "high", False),
        ("adversarial", "critical", True),
        ("adversarial", "high", True),
        ("adversarial", "blocking", False),
        ("", "blocking", False),
    ):
        card = findings.Card("R1", role, {"Priority": f"{grade} · x · y — z."})
        assert card.blocking is blocking, (role, grade)


def test_card_non_security_names_the_other_categories() -> None:
    assert findings.NON_SECURITY == (
        "stability",
        "data integrity",
        "functional correctness",
        "performance",
        "maintainability",
    )


def test_card_word_drops_marks_and_folds_case() -> None:
    for value, word in (
        ("`**Fixed**` — a note", "fixed"),
        ("verified held", "verified"),
        ("open.", "open"),
        ("open,", "open"),
        ("open;", "open"),
        ("open:", "open"),
        ("OPEN", "open"),
        ("", ""),
    ):
        assert findings.Card("R1", "conformance", {"Status": value}).word("Status") == (
            word
        )
    assert findings.Card("R1", "conformance", {}).word("Status") == ""


def test_card_reads_its_grade_status_and_amend() -> None:
    card = findings.Card(
        "R1",
        "conformance",
        {"Priority": "`Blocking` · c · s — w.", "Status": "Open", "Amend": "`Yes`."},
    )
    assert (card.severity, card.status, card.amend) == ("blocking", "open", True)
    assert not findings.Card("R1", "conformance", {"Amend": "no"}).amend


def test_card_small_reads_the_fix_size() -> None:
    assert findings.SMALL == ("one line", "a test", "one line and a test")
    assert findings.SIZE.findall("a size: big · size: a test.") == [" a test."]

    def small(fix: str) -> bool:
        return findings.Card("R1", "conformance", {"Fix": fix}).small

    for fix in (
        "a fix · size: one line.",
        "a fix · size: `a test`.",
        "a fix · size: one line and a test",
        "a size: big · size: a test.",
    ):
        assert small(fix), fix
    for fix in ("a fix · size: a design change.", "a fix · size: a test. note: x", ""):
        assert not small(fix), fix


def test_card_size_is_the_last_size_its_fix_names() -> None:
    for fix, size in (
        ("a fix · size: `a test`.", "a test"),
        ("a size: big · size: a design change.", "a design change"),
        ("a fix · size: a test. note: x", ""),
        ("", ""),
    ):
        assert findings.Card("R1", "conformance", {"Fix": fix}).size == size, fix


def test_card_title_takes_an_id_and_a_dash() -> None:
    for title, ident in (
        ("- **A6 — a title**", "A6"),
        ("- **0138·S3 — a debt card**", "0138·S3"),
    ):
        assert findings.TITLE.findall(title) == [ident], title
    for title in (
        "  - **R1 — nested**",
        "- **R 1 — spaced**",
        "- **R1 – en dash**",
        "- **R1 - hyphen**",
        "- **R1 no dash**",
    ):
        assert findings.TITLE.match(title) is None, title


def test_card_field_takes_the_colon_inside_outside_or_absent() -> None:
    for line, pair in (
        ("  - **Status:** open", ("Status", "open")),
        ("  - **Status**: open", ("Status", "open")),
        ("  - **Still true?** `true`", ("Still true?", "`true`")),
        ("\t- **Round:** 1", ("Round", "1")),
    ):
        found = findings.FIELD.match(line)
        assert found is not None, line
        assert (found[1], found[2]) == pair
    assert findings.FIELD.match("- **Status:** open") is None


def test_card_cards_read_each_field_line() -> None:
    body = (
        "- **R1 — a title**\n"
        "  - **Priority**: blocking · conformance · stability — why.\n"
        "  - **Fix:**   a fix · size: one line.   \n"
        "  - **Still true?** `true`\n"
        "\t- **Round:** 1\n"
        "    - **Amend:** no\n"
        "  - **Status:** open\n"
        "  - **Status:** verified\n"
    )

    (card,) = findings.cards(body, "conformance")

    assert (card.id, card.role, card.lines[0]) == (
        "R1",
        "conformance",
        "- **R1 — a title**",
    )
    assert card.fields == {
        "Priority": "blocking · conformance · stability — why.",
        "Fix": "a fix · size: one line.",
        "Still true?": "`true`",
        "Round": "1",
        "Amend": "no",
        "Status": "open",
    }


@pytest.mark.parametrize(
    ("between", "fields"),
    [
        ("a line\n", {"R1": {"Status": "open"}}),
        ("## Refuted\n", {"R1": {"Status": "open"}}),
        (
            "- **R2 — next**\n",
            {"R1": {"Status": "open"}, "R2": {"Fix": "a fix · size: one line."}},
        ),
    ],
    ids=["unindented", "heading", "title"],
)
def test_card_cards_end_at_the_first_unindented_line(
    between: str, fields: dict[str, dict[str, str]]
) -> None:
    body = (
        "- **R1 — a title**\n  - **Status:** open\n"
        f"{between}  - **Fix:** a fix · size: one line.\n"
    )
    assert {card.id: card.fields for card in findings.cards(body, "")} == fields


def test_card_strays_name_each_status_or_priority_under_no_title() -> None:
    text = (
        "  - **Status:** open\n"
        "- **R1 — a**\n  - **Status:** open\n"
        "- **Note** a bold line\n  - **Status:** fixed\n"
        "* **Other:** x\n  - **Priority:** high · a · b\n"
        "## Refuted\n  - **Status:** open\n"
        "- **R2 — b**\n  - **Status**: open\n"
        "- **R3 — c**\n  - **Fix:** f\n  - **Round:** 1\n"
    )
    assert findings.strays(text) == [
        ("Status", "unnamed"),
        ("Status", "Note"),
        ("Priority", "Other"),
        ("Status", "unnamed"),
    ]
    assert findings.strays("- **R1 — a**\n  - **Status:** open\n") == []
    assert findings.strays("- **N**\n  - **Fix:** f\n") == []


# The frontmatter: the leading block, its keys and their faults.

_KEYS = {
    "head": "h",
    "round": "1",
    "open_blocking": "0",
    "verdict": "clean",
    "files": "1",
    "commits": "1",
    "inconclusive": "[]",
    "passes": "[stale-claim]",
}


def test_front_is_the_leading_block_alone() -> None:
    assert findings.FRONT.match("---\nhead: a\n---\nbody") is not None
    assert findings.front("---\nhead: a\n---\nbody\n") == ({"head": "a"}, "body\n")
    assert findings.front("\n---\nhead: a\n---\n") == ({}, "\n---\nhead: a\n---\n")
    assert findings.front("---\nhead: a\n") == ({}, "---\nhead: a\n")
    late = "---\nhead: a\n---\nverdict: clean\n---\n"
    assert findings.front(late) == ({"head": "a"}, "verdict: clean\n---\n")


def test_front_strips_keys_and_values_and_keeps_colons() -> None:
    text = "---\n verdict :  clean  \nnotes\nhead: a:b\nverdict2:\n---\n"
    assert findings.front(text)[0] == {
        "verdict": "clean",
        "head": "a:b",
        "verdict2": "",
    }
    assert findings.frontmatter(text, "head") == "a:b"
    assert findings.frontmatter(text, "notes") is None
    assert findings.frontmatter("verdict: clean\n", "verdict") is None


def test_front_fault_names_each_missing_or_wrong_key() -> None:
    assert findings.fault(_KEYS, "conformance", stub=False) is None
    assert findings.fault({**_KEYS, "files": "x"}, "adversarial", stub=True) is None
    for change, role, why in (
        ({"head": None}, "conformance", "head is missing"),
        ({"passes": None}, "conformance", "passes is missing"),
        ({"round": "1.0"}, "conformance", "round is not an integer"),
        (
            {"files": "\N{FULLWIDTH DIGIT ONE}"},
            "conformance",
            "files is not an integer",
        ),
        ({"inconclusive": "none"}, "conformance", "inconclusive is not a list"),
        (
            {"verdict": "Clean"},
            "conformance",
            "verdict is neither clean nor changes-requested",
        ),
    ):
        keys = {k: v for k, v in {**_KEYS, **change}.items() if v is not None}
        assert findings.fault(keys, role, stub=False) == why, why
    adversarial = {k: v for k, v in _KEYS.items() if k != "passes"}
    assert findings.fault(adversarial, "adversarial", stub=False) is None


def test_front_listed_reads_a_lists_items() -> None:
    assert findings.listed("[stale-claim, 'test-cost', \"x\"]") == (
        "stale-claim",
        "test-cost",
        "x",
    )
    assert findings.listed("[]") == ()
    assert findings.listed("[ , a]") == ("a",)


# The read of a findings file, and a halt's card ids.


def test_read_returns_the_text_a_bad_byte_replaced(tmp_path: Path) -> None:
    path = tmp_path / "conformance.md"
    path.write_bytes(b"---\nhead: a\n---\n\xff\n")
    assert findings.read(path) == "---\nhead: a\n---\n\N{REPLACEMENT CHARACTER}\n"
    assert findings.read(tmp_path / "adversarial.md") is None


def test_read_refuses_a_link_and_a_pipe(tmp_path: Path) -> None:
    target = tmp_path / "target.md"
    target.write_text("---\nhead: a\n---\n")
    linked = tmp_path / "conformance.md"
    linked.symlink_to(target)
    with pytest.raises(OSError, match="Too many levels of symbolic links"):
        findings.read(linked)
    os.mkfifo(tmp_path / "adversarial.md")
    with pytest.raises(OSError, match="it is not a file"):
        findings.read(tmp_path / "adversarial.md")


def test_read_halt_ids_takes_r_and_s_ids_after_amend_needed() -> None:
    assert findings.halt_ids("halt — amend needed — R1, S12 · head a") == {"R1", "S12"}
    assert findings.halt_ids("halt — amend needed — A1, R-1, XR1") == set()
    assert findings.halt_ids("halt — S1 · amend needed — R1") == {"R1"}
    assert findings.halt_ids("halt — cap reached — R1") == set()


# The stub, and whether a file it would replace is cleared.

_CLEAN = "---\nverdict: clean\n---\n\n"


def _status(status: str) -> str:
    return f"- **S1 — a**\n  - **Status:** {status}\n"


def test_stub_is_a_clean_skipped_file() -> None:
    text = findings.stub(
        "adversarial", "0001-a", "repo", "0001-a", "h", "2026-11-19", 2
    )
    assert text == (
        "---\ntype: adversarial\nplan: 0001-a\nproject: repo\nbranch: 0001-a\n"
        "head: h\nreviewed: 2026-11-19\nround: 2\nopen_blocking: 0\nverdict: clean\n"
        "mode: skipped\nworkers: 0\nmodel: none\nexecutor: none\npacket: skipped: all\n"
        f"---\n\n{findings.STUB_BODY}\n"
    )
    assert not findings.uncleared(text)


def test_stub_uncleared_reads_the_leading_block() -> None:
    open_card = _status("open")
    assert findings.uncleared("mode: skipped\n---\n" + open_card)
    assert not findings.uncleared("---\nmode: skipped\nverdict: x\n---\n" + open_card)
    assert findings.uncleared("---\nverdict: changes-requested\n---\n")
    assert not findings.uncleared(_CLEAN)


def test_stub_uncleared_clears_each_verified_card_alone() -> None:
    assert not findings.uncleared(_CLEAN + _status("verified"))
    assert not findings.uncleared(_CLEAN + _status("**Verified** — held"))
    for status in ("open", "`open`", "accepted", "fixed", "wontfix", ""):
        assert findings.uncleared(_CLEAN + _status(status)), status
    assert findings.uncleared(_CLEAN + "- **S1 — a**\n  - **Status**: open\n")


# The stamp's text: a checker's model and tokens set in the leading block.


def test_stamped_sets_the_model_in_place() -> None:
    assert findings.stamped(
        "---\ntype: c\nmodel: x\nround: 1\ntokens: 3\n---\nmodel: y\n", "m", 5
    ) == ("---\ntype: c\nmodel: m\ntokens: 5\nround: 1\n---\nmodel: y\n")
    assert findings.stamped("\n---\nmodel: x\n---\n", "m", 5) is None
    assert findings.stamped(
        "---\ntype: c\n---\nbody\n---\nmodel: x\n---\n", "m", None
    ) == ("---\ntype: c\nmodel: m\n---\nbody\n---\nmodel: x\n---\n")
    assert findings.stamped("---\nmodel: x\n---\n", None, None) == (
        "---\nmodel: default\n---\n"
    )


# The fix: each rule the copies disagreed on, on its one side.
# Why: 0138-findings design D4 to D12.


def test_fix_extent_a_card_runs_through_a_blank_line() -> None:
    body = (
        "- **R1 — a title**\n  - **Status:** open\n\n\n"
        "  - **Fix:** a fix · size: one line.\n\n"
        "## Refuted\n"
    )

    (card,) = findings.cards(body, "conformance")

    assert card.fields == {"Status": "open", "Fix": "a fix · size: one line."}
    # The blank lines between its lines are kept, the one after its last is not.
    assert card.lines == [
        "- **R1 — a title**",
        "  - **Status:** open",
        "",
        "",
        "  - **Fix:** a fix · size: one line.",
    ]
    # Twin: a blank line, then an unindented one, ends it.
    after = "- **R1 — a**\n  - **Status:** open\n\na line\n  - **Fix:** f\n"
    assert findings.cards(after, "")[0].fields == {"Status": "open"}


def test_fix_field_a_stray_reads_the_colon_outside() -> None:
    assert findings.strays("- **Lone**\n  - **Status**: open\n") == [("Status", "Lone")]
    # A stray after a blank line under its card is no stray: the card goes on.
    assert findings.strays("- **R1 — a**\n  - **Fix:** f\n\n  - **Status:** o\n") == []


def test_fix_word_the_category_reads_as_a_word() -> None:
    def category(priority: str) -> str:
        return findings.Card("S1", "adversarial", {"Priority": priority}).category

    assert category("high · adversarial · `Data integrity`. — why") == (
        "data integrity"
    )
    assert category("high · adversarial · **Security** — why") == "security"
    assert category("high · adversarial") == ""


def test_fix_security_a_card_fails_closed_on_an_unread_category() -> None:
    def security(role: str, priority: str) -> bool:
        return findings.Card("S1", role, {"Priority": priority}).security

    for priority in (
        "high · adversarial · security — why.",
        "high · adversarial · Security — why.",
        "critical · adversarial · injection — why.",
        "**high** · adversarial",
    ):
        assert security("adversarial", priority), priority
    for named in findings.NON_SECURITY:
        assert not security("adversarial", f"high · adversarial · `{named}` — why.")
    assert not security("adversarial", "medium · adversarial · security — why.")
    assert not security("conformance", "blocking · conformance · security — why.")


def test_fix_ids_malformed_names_an_id_or_a_stray() -> None:
    assert findings.malformed(_card("R1", Status="open") + _card("S12"), "") is None
    for text, why in (
        (_card("S-1", Status="open"), "card S-1 is not R<n> or S<n>"),
        (_card("A6", Status="open"), "card A6 is not R<n> or S<n>"),
        (_card("R1x"), "card R1x is not R<n> or S<n>"),
        ("- **Note**\n  - **Status:** open\n", "a Status under no card: Note"),
        ("## Findings\n  - **Priority:** high\n", "a Priority under no card: unnamed"),
    ):
        assert findings.malformed(_CLEAN + text, "adversarial") == why, text
    # The frontmatter alone is no card: a reader of its keys never meets the check.
    assert findings.malformed("---\nverdict: clean\nmode: x\n---\n", "") is None


def test_fix_frontmatter_keyed_sets_the_block_alone() -> None:
    text = "---\n head : a\nround: 1\nmode: x\n---\nround: 7\nworkers: 3\n"
    assert findings.keyed(text, {"head": "b", "round": 2, "workers": 0}) == (
        "---\nhead: b\nround: 2\nmode: x\n---\nround: 7\nworkers: 3\n"
    )
    assert findings.keyed("round: 1\n", {"round": 2}) == "round: 1\n"


def test_fix_first_a_repeated_status_reads_its_first_line() -> None:
    twice = _status("verified") + "  - **Status:** open\n"
    assert not findings.uncleared(_CLEAN + twice)
    assert findings.uncleared(_CLEAN + _status("open") + "  - **Status:** verified\n")


def test_fix_stamp_writes_at_0600_and_leaves_a_link(tmp_path: Path) -> None:
    folder = tmp_path / "folder"
    folder.mkdir()
    path = folder / "conformance.md"
    path.write_bytes(b"---\nmodel: x\n---\n\xff\n")
    path.chmod(0o644)

    findings.stamp(folder, "conformance.md", "m", 5)

    assert (
        path.read_text() == "---\nmodel: m\ntokens: 5\n---\n\N{REPLACEMENT CHARACTER}\n"
    )
    assert path.stat().st_mode & 0o777 == 0o600
    assert sorted(item.name for item in folder.iterdir()) == ["conformance.md"]
    # A file with no frontmatter, a linked file and a linked folder are left alone.
    path.write_text("no block\n")
    findings.stamp(folder, "conformance.md", "m", 5)
    assert path.read_text() == "no block\n"
    target = tmp_path / "target.md"
    target.write_text("---\nmodel: x\n---\n")
    (folder / "adversarial.md").symlink_to(target)
    findings.stamp(folder, "adversarial.md", "m", 5)
    (tmp_path / "linked").symlink_to(folder)
    path.write_text("---\nmodel: x\n---\n")
    findings.stamp(tmp_path / "linked", "conformance.md", "m", 5)
    assert target.read_text() == path.read_text() == "---\nmodel: x\n---\n"


def test_fix_stamp_keeps_the_file_when_its_write_fails(tmp_path: Path) -> None:
    path = tmp_path / "conformance.md"
    path.write_text("---\nmodel: x\n---\n")
    (tmp_path / "conformance.md.tmp").mkdir()

    findings.stamp(tmp_path, "conformance.md", "m", 5)

    assert path.read_text() == "---\nmodel: x\n---\n"
