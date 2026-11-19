"""The findings file's writer and parser in the home, each name a case.

Why: 0138-findings design D1 and D2.
"""

import os
from collections.abc import Callable
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


def test_card_security_is_the_exact_category() -> None:
    def security(role: str, priority: str) -> bool:
        return findings.Card("S1", role, {"Priority": priority}).security

    assert security("adversarial", "high · adversarial · security — why.")
    assert not security("adversarial", "high · adversarial · Security — why.")
    assert not security("adversarial", "high · adversarial")
    assert not security("conformance", "blocking · conformance · security — why.")


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
        ("\n", {"R1": {"Status": "open"}}),
        ("a line\n", {"R1": {"Status": "open"}}),
        ("## Refuted\n", {"R1": {"Status": "open"}}),
        (
            "- **R2 — next**\n",
            {"R1": {"Status": "open"}, "R2": {"Fix": "a fix · size: one line."}},
        ),
    ],
    ids=["blank", "unindented", "heading", "title"],
)
def test_card_cards_end_at_the_first_unindented_line(
    between: str, fields: dict[str, dict[str, str]]
) -> None:
    body = (
        "- **R1 — a title**\n  - **Status:** open\n"
        f"{between}  - **Fix:** a fix · size: one line.\n"
    )
    assert {card.id: card.fields for card in findings.cards(body, "")} == fields


def test_card_strays_name_each_status_under_no_title() -> None:
    text = (
        "  - **Status:** open\n"
        "- **R1 — a**\n  - **Status:** open\n"
        "- **Note** a bold line\n  - **Status:** fixed\n"
        "* **Other:** x\n  - **Status:** fixed\n"
        "## Refuted\n  - **Status:** open\n"
        "- **R2 — b**\n  - **Status**: open\n"
        "- **Lone**\n  - **Status**: open\n"
    )
    assert findings.strays(text) == ["unnamed", "Note", "Other", "unnamed"]
    assert findings.strays("- **R1 — a**\n  - **Status:** open\n") == []


# The legacy forms of the card: each copy's rule as it stands, phase 4's to delete.


def test_card_cards_conduct_legacy_run_to_the_next_title() -> None:
    first = "- **R1 — a**\n  - **Status:** open\n\n## Refuted\n"
    second = "- **R2 — b**\n  - **Status:** fixed\n"

    found = list(findings.cards_conduct_legacy(f"---\nx: y\n---\n\n{first}{second}"))

    assert found == [("R1", first), ("R2", second)]
    assert list(findings.cards_conduct_legacy("no card\n")) == []


def test_card_field_conduct_legacy_needs_an_indented_colon_inside() -> None:
    field = findings.field_conduct_legacy
    assert field("- **R1 — a**\n  - **Status:**  open \n", "Status") == "open"
    assert field("- **R1 — a**\n  - **Status**: open\n", "Status") == ""
    assert field("- **R1 — a**\n- **Status:** open\n", "Status") == ""


def test_card_words_conduct_legacy_read_the_conductors_way() -> None:
    def card(name: str, value: str) -> str:
        return f"- **S1 — a**\n  - **{name}:** {value}\n"

    assert (
        findings.severity_conduct_legacy(card("Priority", "**high** · a")) == "**high**"
    )
    assert findings.severity_conduct_legacy(card("Priority", "`High` · a")) == "high"
    assert (
        findings.category_conduct_legacy(
            card("Priority", "high · adversarial · `Security` — y")
        )
        == "security"
    )
    assert (
        findings.category_conduct_legacy(card("Priority", "high · adversarial")) == ""
    )
    assert findings.status_conduct_legacy(card("Status", "**Open**")) == "**Open**"
    assert findings.status_conduct_legacy(card("Status", "`Open`")) == "Open"


def test_card_security_conduct_legacy_fails_closed() -> None:
    def card(priority: str) -> str:
        return f"- **S1 — a**\n  - **Priority:** {priority}\n"

    assert findings.security_conduct_legacy(card("high · adversarial · injection — w."))
    assert findings.security_conduct_legacy(card("critical · adversarial"))
    for named in findings.NON_SECURITY:
        assert not findings.security_conduct_legacy(
            card(f"high · adversarial · {named} — why.")
        ), named
    assert not findings.security_conduct_legacy(card("medium · adversarial · security"))


def test_card_cards_open_cards_legacy_run_to_a_title_or_heading() -> None:
    first = "- **R1 — a**\n  - **Status:** open\n\n  - **Fix:** f\n"
    second = "- **A4 — b**\n  - **Status:** fixed\n"
    text = f"{first}## Refuted\n  - **Fix:** g\n{second}"

    assert findings.cards_open_cards_legacy(text) == [first, second]
    assert findings.cards_overlap_legacy(text) == [first, second]


def test_card_statuses_open_cards_legacy_read_each_status_word() -> None:
    card = (
        "- **R1 — a**\n  - **Status:** `**Fixed**`. — a note\n"
        "  - **Status:** Verified-held\n  - **Status:** _wontfix_\n"
        "  - **Status:**\n  - **Status**: open\n"
    )
    assert findings.statuses_open_cards_legacy(card) == [
        ("`**Fixed**`.", "fixed"),
        ("Verified-held", "verified"),
        ("_wontfix_", "wontfix_"),
        ("", ""),
    ]


def test_card_overlap_legacy_reads_a_field_with_its_colon_inside() -> None:
    title = "- **R1 — a**\n"
    affects = findings.affects_overlap_legacy
    assert affects(f"{title}  - **What it affects:** `a.py:1`\n") == " `a.py:1`"
    assert affects(f"{title}  - **What it affects**: `a.py:1`\n") is None
    assert affects(f"{title}- **What it affects:** `a.py:1`\n") is None
    blocks = findings.blocks_overlap_legacy
    assert blocks(f"{title}  - **Priority:** blocking · c\n", ("blocking",))
    assert not blocks(f"{title}  - **Priority**: blocking · c\n", ("blocking",))
    assert not blocks(f"{title}  - **Priority:** **blocking** · c\n", ("blocking",))
    assert not blocks(f"{title}  - **Priority:** Blocking · c\n", ("blocking",))
    assert not findings.first_round_overlap_legacy(f"{title}  - **Round:** 2\n")
    assert findings.first_round_overlap_legacy(f"{title}  - **Round:** 1\n")
    assert findings.first_round_overlap_legacy(f"{title}  - **Round**: 2\n")
    assert findings.first_round_overlap_legacy(title)


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


def test_front_conduct_legacy_reads_the_first_word() -> None:
    for text, value in (
        ("---\nverdict:\nclean\n---\n", "clean"),
        ("---\nverdict: clean # note\n---\n", "clean"),
        ("---\nverdict: clean\n", "clean"),
        ("---\nhead: a\n---\nverdict: clean\n", None),
        ("verdict: clean\n", None),
    ):
        assert findings.frontmatter_conduct_legacy(text, "verdict") == value, text
        assert findings.frontmatter_integrate_legacy(text, "verdict") == value, text


def test_front_executor_overlap_legacy_needs_it_alone_on_its_line() -> None:
    for text, executor in (
        ("---\nexecutor: codex\n---\n", "codex"),
        ("---\nexecutor:  codex  \n---\n", "codex"),
        ("---\nexecutor: codex # x\n---\n", "unknown"),
        ("executor: codex\n", "unknown"),
        ("---\nhead: a\n---\nexecutor: codex\n", "unknown"),
    ):
        assert findings.executor_overlap_legacy(text) == executor, text


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


def test_read_open_cards_legacy_stops_saying_why(tmp_path: Path) -> None:
    path = tmp_path / "conformance.md"
    path.write_text("x\n")
    assert findings.read_open_cards_legacy(path) == "x\n"
    path.write_bytes(b"\xff\n")
    with pytest.raises(findings.Unread, match=r": invalid start byte$"):
        findings.read_open_cards_legacy(path)
    missing = tmp_path / "adversarial.md"
    with pytest.raises(findings.Unread, match=r"adversarial\.md: No such file"):
        findings.read_open_cards_legacy(missing)


def test_read_overlap_legacy_names_the_path(tmp_path: Path) -> None:
    path = tmp_path / "conformance.md"
    path.write_text("x\n")
    target = tmp_path / "target.md"
    target.write_text("y\n")
    (tmp_path / "adversarial.md").symlink_to(target)
    assert findings.read_overlap_legacy(path) == "x\n"
    assert findings.read_overlap_legacy(tmp_path / "adversarial.md") == "y\n"
    path.write_bytes(b"\xff\n")
    with pytest.raises(findings.Unread) as unread:
        findings.read_overlap_legacy(path)
    assert str(unread.value) == str(path)


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
    twice = _status("verified") + "  - **Status:** open\n"
    assert not findings.uncleared(_CLEAN + twice)


def test_stub_uncleared_skip_stub_legacy_reads_its_own_way() -> None:
    legacy = findings.uncleared_skip_stub_legacy
    open_card = _status("open")
    assert not legacy("mode: skipped\n---\n" + open_card)
    assert legacy("mode: parallel\n---\n" + open_card)
    assert legacy(_CLEAN + open_card)
    for card in (
        _status("`open`"),
        _status("**open**"),
        "- **S1 — a**\n  - **Status**: open\n",
        _status("verified"),
    ):
        assert not legacy(_CLEAN + card), card
    assert legacy(_CLEAN + _status("accepted"))
    assert legacy(_CLEAN + _status("verified") + "  - **Status:** open\n")


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


# Each legacy function on the pin's inputs, expecting what the copy it holds gave.
# Why: 0138-findings design D2, its cases e, h, i, k, l and m.

_H_FIRST = (
    "- **R1 — a**\n  - **Status:** open\n\n  - **Fix:** f\n## Refuted\n\n- **x.** why\n"
)
_H_SECOND = "- **R2 — b**\n  - **Status:** fixed\n"
_K_FIRST = "- **R1 — a**\n  - **Status:** open\n\n  - **Fix:** f\n"
_K_SECOND = "- **A4 — b**\n  - **Status:** fixed\n"
_K_TEXT = f"{_K_FIRST}## Refuted\n  - **Fix:** g\n{_K_SECOND}"
_TITLE = "- **R1 — a**\n"


def _field(name: str, value: str) -> str:
    return f"- **S1 — a**\n  - **{name}:** {value}\n"


def _conduct_cards(text: str) -> list[tuple[str, str]]:
    return list(findings.cards_conduct_legacy(text))


_LEGACY: list[tuple[str, Callable[..., object], tuple[object, ...], object]] = [
    (
        "h-extent",
        _conduct_cards,
        (f"---\nx: y\n---\n\n{_H_FIRST}{_H_SECOND}",),
        [("R1", _H_FIRST), ("R2", _H_SECOND)],
    ),
    (
        "h-field",
        findings.field_conduct_legacy,
        (f"{_TITLE}  - **Status:**  open \n", "Status"),
        "open",
    ),
    (
        "h-field-tab",
        findings.field_conduct_legacy,
        (f"{_TITLE}\t- **Status:** open\n", "Status"),
        "open",
    ),
    (
        "h-field-colon-outside",
        findings.field_conduct_legacy,
        (f"{_TITLE}  - **Status**: open\n", "Status"),
        "",
    ),
    (
        "h-field-unindented",
        findings.field_conduct_legacy,
        (f"{_TITLE}- **Status:** open\n", "Status"),
        "",
    ),
    (
        "h-severity-bold",
        findings.severity_conduct_legacy,
        (_field("Priority", "**high** · adversarial · x — y"),),
        "**high**",
    ),
    (
        "h-severity-ticked",
        findings.severity_conduct_legacy,
        (_field("Priority", "`High` · adversarial · x — y"),),
        "high",
    ),
    (
        "h-category",
        findings.category_conduct_legacy,
        (_field("Priority", "high · adversarial · `Security` — y"),),
        "security",
    ),
    (
        "h-category-none",
        findings.category_conduct_legacy,
        (_field("Priority", "high · adversarial"),),
        "",
    ),
    (
        "h-status-bold",
        findings.status_conduct_legacy,
        (_field("Status", "**Open**"),),
        "**Open**",
    ),
    (
        "h-status-ticked",
        findings.status_conduct_legacy,
        (_field("Status", "`Open`"),),
        "Open",
    ),
    (
        "i-security-unknown",
        findings.security_conduct_legacy,
        (_field("Priority", "high · adversarial · injection — why."),),
        True,
    ),
    (
        "i-security-missing",
        findings.security_conduct_legacy,
        (_field("Priority", "critical · adversarial"),),
        True,
    ),
    (
        "i-security-named",
        findings.security_conduct_legacy,
        (_field("Priority", "high · adversarial · stability — why."),),
        False,
    ),
    (
        "i-security-medium",
        findings.security_conduct_legacy,
        (_field("Priority", "medium · adversarial · security — why."),),
        False,
    ),
    *(
        (f"e-{script}-{n}", function, (text, "verdict"), value)
        for script, function in (
            ("conduct", findings.frontmatter_conduct_legacy),
            ("integrate", findings.frontmatter_integrate_legacy),
        )
        for n, (text, value) in enumerate(
            (
                ("---\nverdict:\nclean\n---\n", "clean"),
                ("---\nverdict: clean # note\n---\n", "clean"),
                ("---\nverdict: clean\n", "clean"),
                ("---\nhead: a\n---\nverdict: clean\n", None),
                ("verdict: clean\n", None),
            )
        )
    ),
    ("k-extent", findings.cards_open_cards_legacy, (_K_TEXT,), [_K_FIRST, _K_SECOND]),
    *(
        (
            f"k-status-{n}",
            findings.statuses_open_cards_legacy,
            (_field("Status", said),),
            [(said, word)],
        )
        for n, (said, word) in enumerate(
            (
                ("`**Fixed**`.", "fixed"),
                ("Verified-held", "verified"),
                ("WONTFIX", "wontfix"),
                ("_wontfix_", "wontfix_"),
                ("", ""),
            )
        )
    ),
    (
        "k-status-colon-outside",
        findings.statuses_open_cards_legacy,
        ("- **R1 — a**\n  - **Status**: open\n",),
        [],
    ),
    ("l-extent", findings.cards_overlap_legacy, (_K_TEXT,), [_K_FIRST, _K_SECOND]),
    (
        "l-affects",
        findings.affects_overlap_legacy,
        (f"{_TITLE}  - **What it affects:** `a.py:1`\n",),
        " `a.py:1`",
    ),
    (
        "l-affects-colon-outside",
        findings.affects_overlap_legacy,
        (f"{_TITLE}  - **What it affects**: `a.py:1`\n",),
        None,
    ),
    (
        "l-affects-unindented",
        findings.affects_overlap_legacy,
        (f"{_TITLE}- **What it affects:** `a.py:1`\n",),
        None,
    ),
    *(
        (
            f"l-blocks-{n}",
            findings.blocks_overlap_legacy,
            (f"{_TITLE}  - **Priority{colon} {grade} · c\n", ("blocking",)),
            blocking,
        )
        for n, (colon, grade, blocking) in enumerate(
            (
                (":**", "blocking", True),
                ("**:", "blocking", False),
                (":**", "**blocking**", False),
                (":**", "Blocking", False),
            )
        )
    ),
    (
        "l-round-2",
        findings.first_round_overlap_legacy,
        (f"{_TITLE}  - **Round:** 2\n",),
        False,
    ),
    (
        "l-round-colon-outside",
        findings.first_round_overlap_legacy,
        (f"{_TITLE}  - **Round**: 2\n",),
        True,
    ),
    ("l-round-none", findings.first_round_overlap_legacy, (_TITLE,), True),
    *(
        (f"l-executor-{n}", findings.executor_overlap_legacy, (text,), executor)
        for n, (text, executor) in enumerate(
            (
                ("---\nexecutor: codex\n---\n", "codex"),
                ("---\nexecutor:  codex  \n---\n", "codex"),
                ("---\nexecutor: codex # x\n---\n", "unknown"),
                ("executor: codex\n", "unknown"),
                ("---\nhead: a\n---\nexecutor: codex\n", "unknown"),
            )
        )
    ),
    *(
        (f"m-uncleared-{n}", findings.uncleared_skip_stub_legacy, (text,), uncleared)
        for n, (text, uncleared) in enumerate(
            (
                ("mode: skipped\n---\n" + _status("open"), False),
                ("mode: parallel\n---\n" + _status("open"), True),
                (
                    "---\nmode: skipped\nverdict: changes-requested\n---\n"
                    + _status("open"),
                    False,
                ),
                (_CLEAN + _status("open"), True),
                (_CLEAN + _status("`open`"), False),
                (_CLEAN + _status("**open**"), False),
                (_CLEAN + "- **S1 — a**\n  - **Status**: open\n", False),
                (_CLEAN + _status("verified"), False),
                (_CLEAN + _status("accepted"), True),
                (_CLEAN + _status("fixed"), True),
                (_CLEAN + _status("wontfix"), True),
                (_CLEAN + _status("verified") + "  - **Status:** open\n", True),
            )
        )
    ),
]


@pytest.mark.parametrize(
    ("function", "args", "expected"),
    [row[1:] for row in _LEGACY],
    ids=[row[0] for row in _LEGACY],
)
def test_legacy_gives_what_the_copy_gave(
    function: Callable[..., object], args: tuple[object, ...], expected: object
) -> None:
    assert function(*args) == expected
