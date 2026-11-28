"""The old forms' reader in the home, over the lines an old run left on disk.

Why: 0162-metric-scripts design D5.
"""

from mflib import eras, statuslog

_ISEKAI_0037 = (
    "verdicts — review changes-requested · open_blocking 2 (R1, R2)"
    " · 7 commits 29 files · stale-claim pass ran",
    "verdicts — security clean · open_blocking 0 · 7 commits 29 files (matches freeze)",
)
_MF_0095 = (
    "verdicts — security clean · open_blocking 0 · executor claude"
    " · model default · effort default · tokens 167263",
    "verdicts — review changes-requested · open_blocking 2 · executor claude"
    " · model default · effort default · tokens 341901",
)
_COLON = (
    "verdicts — review verdict: changes-requested; open_blocking: 2 (R1, R2);"
    " scope 8 commits, 43 files;"
)


def _count(line: str) -> int | None:
    """Return `eras.blocking` of a status-log event line."""
    event = statuslog.parse_event(f"10:00:00 · round 1 · {line}")
    assert event is not None
    return eras.blocking(event)


def _detail(detail: str, name: str = "verdicts") -> int | None:
    return eras.blocking(statuslog.Event(1, name, detail))


def test_blocking_reads_the_lines_of_isekais_0037() -> None:
    assert [_count(line) for line in _ISEKAI_0037] == [2, 0]


def test_blocking_reads_the_lines_of_mfs_0095() -> None:
    assert [_count(line) for line in _MF_0095] == [0, 2]


def test_blocking_reads_the_colon_form() -> None:
    assert _count(_COLON) == 2
    assert _detail("x · open_blocking: 7") == 7
    assert _detail("open_blocking: 3 · open_blocking: 4") == 3


def test_blocking_gives_none_for_the_roles_of_today() -> None:
    today = (
        "verdicts — adversarial clean · open_blocking 0 · executor claude · tokens 5",
        "verdicts — conformance changes-requested · open_blocking 1 · tokens 5",
    )

    assert [_count(line) for line in today] == [None, None]
    assert _detail("c changes-requested · open_blocking 4") is None


def test_blocking_gives_none_for_another_event_and_for_no_count() -> None:
    assert _detail("review changes-requested · open_blocking 2", "fix") is None
    assert _detail("review clean") is None
    assert _detail("review clean · open_blocking x") is None
    assert _detail("review clean · open_blocking ") is None
    assert _detail("reviewer clean · open_blocking 2") is None
    assert _detail("open_blocking: x") is None


def test_blocking_reads_no_count_of_a_long_run_of_digits() -> None:
    digits = "9" * 19
    assert _detail(f"review x · open_blocking {digits}") is None
    assert _detail(f"x open_blocking: {digits}") is None
    assert _detail("review x · open_blocking " + "9" * 18) == int("9" * 18)
    assert _detail("x open_blocking: " + "9" * 18) == int("9" * 18)


def test_an_old_role_with_no_count_after_its_first_marker_falls_to_the_colon() -> None:
    assert _detail("review x · open_blocking y; open_blocking: 5") == 5


def test_refuted_reads_the_entries_under_refused() -> None:
    text = "- **R1 — a card**\n\n## Refused\n\n- a\n- b\n  - nested\n\n## Next\n- c\n"

    assert eras.refuted(text) == ["- a", "- b"]
    assert eras.refuted("## Refused (2)\n- a\n") == ["- a"]
    assert eras.refuted("## Refused") == []
    assert eras.refuted("## Refused\r\n- a\r\n") == ["- a"]


def test_refuted_gives_none_over_refuted_and_over_no_heading() -> None:
    assert eras.refuted("## Refuted\n- a\n") is None
    assert eras.refuted("") is None
    assert eras.refuted("### Refused\n- a\n") is None
    assert eras.refuted(" ## Refused\n- a\n") is None
