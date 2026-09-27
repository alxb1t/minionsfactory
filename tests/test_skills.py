"""Skill-text guards: what the shipped `skills/mf-*` must say, proved by a scan."""

import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent

# The three skills that must run the gate. Each states the gate rule in its own words —
# skills are self-contained — so each must name both the gate and the dry run printed
# before it (0011-cut-and-gate design D1). Any other skill that names `make gate` is
# held to the same pair.
_GATE_RUNNERS = ("mf-build", "mf-converge", "mf-release")

# The shared lists: `mf-build` owns each, `mf-cut-change` carries the same ids, and a
# scan holds their labels equal and each id run unbroken. An id is the bold first cell
# of a table row in the named `## ` section, up to the next `## ` heading.
# Why: 0011-cut-and-gate design D5, 0013-how-the-builder-writes design D3.
_SHARED_OWNERS = ("mf-build", "mf-cut-change")


def _gate_problems(base: Path) -> list[str]:
    """Return one line per breach of the gate rule in `base`'s `skills/*/SKILL.md`."""
    texts = {
        path.parent.name: path.read_text()
        for path in sorted((base / "skills").glob("*/SKILL.md"))
    }
    problems: list[str] = []
    for name, text in texts.items():
        for number, line in enumerate(text.splitlines(), start=1):
            if "minions.toml" in line:
                problems.append(f"skills/{name}/SKILL.md:{number}: names minions.toml")
    runners = sorted(
        {*_GATE_RUNNERS, *(n for n, t in texts.items() if "make gate" in t)}
    )
    for name in runners:
        for needle in ("make gate", "make -n gate"):
            if needle not in texts.get(name, ""):
                problems.append(f"skills/{name}/SKILL.md: does not name `{needle}`")
    return problems


@pytest.mark.spec("sdd:skills-gate:skills-run-make-gate")
def test_the_skills_run_make_gate_and_none_names_the_toml() -> None:
    assert _gate_problems(_REPO) == []


@pytest.mark.spec("sdd:skills-gate:skills-run-make-gate")
def test_the_gate_scan_reports_a_named_toml_and_a_missing_dry_run(
    tmp_path: Path,
) -> None:
    # The scan is only worth having if it bites: name the toml in one skill, drop the
    # dry run from another and from a skill outside the three, and confirm all three
    # are reported.
    ok = "Run `make -n gate`, then `make gate`.\n"
    for name in _GATE_RUNNERS:
        (tmp_path / "skills" / name).mkdir(parents=True)
        (tmp_path / "skills" / name / "SKILL.md").write_text(ok)
    (tmp_path / "skills" / "mf-build" / "SKILL.md").write_text(
        ok + "Read `.minions/minions.toml`.\n"
    )
    (tmp_path / "skills" / "mf-release" / "SKILL.md").write_text("Run `make gate`.\n")
    (tmp_path / "skills" / "mf-other").mkdir()
    (tmp_path / "skills" / "mf-other" / "SKILL.md").write_text("Run `make gate`.\n")

    assert _gate_problems(tmp_path) == [
        "skills/mf-build/SKILL.md:2: names minions.toml",
        "skills/mf-other/SKILL.md: does not name `make -n gate`",
        "skills/mf-release/SKILL.md: does not name `make -n gate`",
    ]


def _section_labels(path: Path, heading: str) -> list[str]:
    """Return the bold first cells of the table rows in `path`'s `heading` section."""
    row = re.compile(r"^\| \*\*(.+?)\*\* \|")
    labels: list[str] = []
    inside = False
    for line in path.read_text().splitlines():
        if line.startswith("## "):
            inside = line == heading
        elif inside and (match := row.match(line)):
            labels.append(match.group(1))
    return labels


def _section_ids(path: Path, heading: str, letter: str) -> list[int]:
    """Return the `letter` ids in `path`'s `heading` section, in order.

    e.g. labels "I1", "I2", "Note" → [1, 2]
    """
    return [
        int(match.group(1))
        for label in _section_labels(path, heading)
        if (match := re.fullmatch(rf"{letter}(\d+)", label))
    ]


def _shared_label_problems(base: Path, heading: str) -> list[str]:
    """Return one line per breach of the `heading` labels the shared owners carry."""
    owners = _SHARED_OWNERS
    problems: list[str] = []
    sets: dict[str, set[str]] = {}
    for name in owners:
        path = base / "skills" / name / "SKILL.md"
        if not path.is_file():
            problems.append(f"skills/{name}/SKILL.md: does not exist")
            continue
        labels = _section_labels(path, heading)
        if not labels:
            problems.append(f"skills/{name}/SKILL.md: no labels in `{heading}`")
        sets[name] = set(labels)
    first, second = (sets.get(name) for name in owners)
    if first and second and first != second:
        problems.append(
            f"labels differ: only in {owners[0]} {sorted(first - second)}, "
            f"only in {owners[1]} {sorted(second - first)}"
        )
    return problems


def _shared_id_problems(base: Path, heading: str, letter: str) -> list[str]:
    """Return one line per breach of the shared `heading` list in `base`'s skills."""
    problems = _shared_label_problems(base, heading)
    for name in _SHARED_OWNERS:
        path = base / "skills" / name / "SKILL.md"
        ids = _section_ids(path, heading, letter) if path.is_file() else []
        if ids and sorted(ids) != list(range(1, max(ids) + 1)):
            problems.append(
                f"skills/{name}/SKILL.md: ids do not run {letter}1…{letter}{max(ids)}"
            )
    return problems


def _table_text(heading: str, *labels: str) -> str:
    """Return a skill text whose `heading` table holds one row per label."""
    rows = "".join(f"| **{label}** | — |\n" for label in labels)
    return f"{heading}\n\n| label | holds |\n|---|---|\n{rows}"


def _plant(base: Path, texts: dict[str, str]) -> Path:
    """Write each named skill's text under `base`, and return `base`."""
    for name, text in texts.items():
        (base / "skills" / name).mkdir(parents=True)
        (base / "skills" / name / "SKILL.md").write_text(text)
    return base


def _planted_problems(base: Path, heading: str, letter: str) -> list[str]:
    """Return what the scan reports for a planted build and cut that disagree.

    The build holds ids 1–3 and the cut 1 and 3, so the cut has a gap and the two sets
    differ by one id. A row past the section's end must not count.
    """
    outside = f"\n## Never\n\n| **{letter}9** | outside |\n"
    build = _table_text(heading, f"{letter}1", f"{letter}2", f"{letter}3")
    cut = _table_text(heading, f"{letter}1", f"{letter}3")
    _plant(base, {"mf-build": build + outside, "mf-cut-change": cut + outside})
    return _shared_id_problems(base, heading, letter)


@pytest.mark.spec("sdd:input-contract:ids-agree")
def test_the_cut_and_the_build_carry_the_same_contract_ids() -> None:
    assert _shared_id_problems(_REPO, "## Input contract", "I") == []


@pytest.mark.spec("sdd:input-contract:ids-agree")
def test_the_contract_scan_reports_a_differing_id_and_a_gap(tmp_path: Path) -> None:
    assert _planted_problems(tmp_path, "## Input contract", "I") == [
        "labels differ: only in mf-build ['I2'], only in mf-cut-change []",
        "skills/mf-cut-change/SKILL.md: ids do not run I1…I3",
    ]


@pytest.mark.spec("sdd:prose-rules:ids-agree")
def test_the_cut_and_the_build_carry_the_same_prose_rule_ids() -> None:
    assert _shared_id_problems(_REPO, "## Prose rules", "P") == []


@pytest.mark.spec("sdd:prose-rules:ids-agree")
def test_the_prose_scan_reports_a_differing_id_and_a_gap(tmp_path: Path) -> None:
    assert _planted_problems(tmp_path, "## Prose rules", "P") == [
        "labels differ: only in mf-build ['P2'], only in mf-cut-change []",
        "skills/mf-cut-change/SKILL.md: ids do not run P1…P3",
    ]


# The card: `mf-converge` owns it, and no other skill carries a copy that could drift.
# A label is the bold first cell of a table row. Why: 0016-backlog-in-repo design D8.
_CARD_OWNER = "mf-converge"
_CARD_HEADING = "## The card"


def _card_owner_problems(base: Path) -> list[str]:
    """Return one line per breach of the one-card-owner rule in `base`'s skills."""
    owner = base / "skills" / _CARD_OWNER / "SKILL.md"
    problems: list[str] = []
    if not owner.is_file():
        problems.append(f"skills/{_CARD_OWNER}/SKILL.md: does not exist")
    elif not _section_labels(owner, _CARD_HEADING):
        problems.append(
            f"skills/{_CARD_OWNER}/SKILL.md: no labels in `{_CARD_HEADING}`"
        )
    for path in sorted((base / "skills").glob("*/SKILL.md")):
        if path != owner and _CARD_HEADING in path.read_text().splitlines():
            problems.append(
                f"skills/{path.parent.name}/SKILL.md: carries `{_CARD_HEADING}`"
            )
    return problems


@pytest.mark.spec("sdd:backlog-cards:fields-agree")
def test_only_converge_carries_the_card() -> None:
    assert _card_owner_problems(_REPO) == []


@pytest.mark.spec("sdd:backlog-cards:fields-agree")
def test_the_card_scan_reports_an_empty_owner_and_a_second_carrier(
    tmp_path: Path,
) -> None:
    # The owner's row past `## Never` must not count as a card field.
    _plant(
        tmp_path,
        {
            _CARD_OWNER: f"{_CARD_HEADING}\n\n## Never\n\n| **Title** | — |\n",
            "mf-other": _table_text(_CARD_HEADING, "Title"),
        },
    )

    assert _card_owner_problems(tmp_path) == [
        f"skills/{_CARD_OWNER}/SKILL.md: no labels in `{_CARD_HEADING}`",
        f"skills/mf-other/SKILL.md: carries `{_CARD_HEADING}`",
    ]


def _needle_problems(
    base: Path, name: str, present: tuple[str, ...] = (), absent: tuple[str, ...] = ()
) -> list[str]:
    """Return one line per `present` needle a skill lacks and `absent` needle it names.

    e.g. absent `x` on line 3 of mf-release → "skills/mf-release/SKILL.md:3: names `x`"
    """
    where = f"skills/{name}/SKILL.md"
    text = (base / where).read_text()
    problems = [f"{where}: does not name `{n}`" for n in present if n not in text]
    for number, line in enumerate(text.splitlines(), start=1):
        problems += [f"{where}:{number}: names `{n}`" for n in absent if n in line]
    return problems


# Deferred work stays in one repository backlog, and pickup matches the card's Fix
# size by its literal values. Why: 0016-backlog-in-repo design D1, D2, D4.
_BACKLOG = ".minions/backlog.md"
_PER_VERSION_BACKLOG = "_backlog.md"
_PICKUP_SIZES = ("`one line`", "`a test`")


def _converge_backlog_problems(base: Path) -> list[str]:
    """Return one line per breach of the one-backlog rule in `base`'s converge skill."""
    return _needle_problems(
        base,
        "mf-converge",
        present=(_BACKLOG, *_PICKUP_SIZES),
        absent=(_PER_VERSION_BACKLOG,),
    )


@pytest.mark.spec("sdd:repo-backlog:converge-writes-one-file")
def test_converge_names_the_one_backlog_and_the_pickup_sizes() -> None:
    assert _converge_backlog_problems(_REPO) == []


@pytest.mark.spec("sdd:repo-backlog:converge-writes-one-file")
def test_the_converge_backlog_scan_reports_every_breach(tmp_path: Path) -> None:
    # A converge that writes the per-version file and names the sizes only in prose is
    # the skill before this change: every needle is reported.
    text = "Carry to `.minions/<version>_backlog.md`.\nFix: one line, a test.\n"
    _plant(tmp_path, {"mf-converge": text})

    assert _converge_backlog_problems(tmp_path) == [
        f"skills/mf-converge/SKILL.md: does not name `{_BACKLOG}`",
        "skills/mf-converge/SKILL.md: does not name ``one line``",
        "skills/mf-converge/SKILL.md: does not name ``a test``",
        f"skills/mf-converge/SKILL.md:1: names `{_PER_VERSION_BACKLOG}`",
    ]


# The release holds nothing on the backlog; a paydown change's `backlog:` key is written
# by the cut and read by the release. Why: 0016-backlog-in-repo design D5, D6.
_PAYDOWN_KEY = "backlog:"


def _release_backlog_problems(base: Path) -> list[str]:
    """Return one line per breach of the backlog rule in `base`'s release and cut."""
    return _needle_problems(
        base,
        "mf-release",
        present=(_BACKLOG, _PAYDOWN_KEY),
        absent=(_PER_VERSION_BACKLOG,),
    ) + _needle_problems(base, "mf-cut-change", present=(_PAYDOWN_KEY,))


@pytest.mark.spec("sdd:repo-backlog:release-does-not-read")
def test_the_release_reads_no_per_version_backlog_and_shares_the_key() -> None:
    assert _release_backlog_problems(_REPO) == []


@pytest.mark.spec("sdd:repo-backlog:release-does-not-read")
def test_the_release_backlog_scan_reports_every_breach(tmp_path: Path) -> None:
    # A release that still blocks on the per-version file, and a cut and release that
    # never name the paydown key: every breach is reported.
    _plant(
        tmp_path,
        {
            "mf-release": "Halt on a line in `.minions/<version>_backlog.md`.\n",
            "mf-cut-change": "Write `proposal.md`.\n",
        },
    )

    assert _release_backlog_problems(tmp_path) == [
        f"skills/mf-release/SKILL.md: does not name `{_BACKLOG}`",
        f"skills/mf-release/SKILL.md: does not name `{_PAYDOWN_KEY}`",
        f"skills/mf-release/SKILL.md:1: names `{_PER_VERSION_BACKLOG}`",
        f"skills/mf-cut-change/SKILL.md: does not name `{_PAYDOWN_KEY}`",
    ]


# Converge is optional (0012-converge-optional design D1, D5): the release states a
# skipped converge in one literal line, and the rule that a missing findings file is
# not clean leaves the release but stays in converge, which judges its own stations
# by it.
_SKIP_LINE = "converge: skipped — no findings files"
_MISSING_FILE_RULE = "A missing findings file is not clean"


def _converge_optional_problems(base: Path) -> list[str]:
    """Return one line per breach of the converge-optional rule in `base`'s skills."""
    return _needle_problems(
        base, "mf-release", present=(_SKIP_LINE,), absent=(_MISSING_FILE_RULE,)
    ) + _needle_problems(base, "mf-converge", present=(_MISSING_FILE_RULE,))


@pytest.mark.spec("sdd:converge-optional:skip-is-stated")
def test_the_release_states_a_skipped_converge_and_converge_keeps_the_rule() -> None:
    assert _converge_optional_problems(_REPO) == []


@pytest.mark.spec("sdd:converge-optional:skip-is-stated")
def test_the_converge_optional_scan_reports_all_three_breaches(tmp_path: Path) -> None:
    # Plant a release with no skip line that still carries the rule, and a converge
    # without it: all three breaches are reported.
    for name in ("mf-release", "mf-converge"):
        (tmp_path / "skills" / name).mkdir(parents=True)
    (tmp_path / "skills" / "mf-release" / "SKILL.md").write_text(
        f"{_MISSING_FILE_RULE}, so an absent file halts.\n"
    )
    (tmp_path / "skills" / "mf-converge" / "SKILL.md").write_text("Converge.\n")

    assert _converge_optional_problems(tmp_path) == [
        f"skills/mf-release/SKILL.md: does not name `{_SKIP_LINE}`",
        f"skills/mf-release/SKILL.md:1: names `{_MISSING_FILE_RULE}`",
        f"skills/mf-converge/SKILL.md: does not name `{_MISSING_FILE_RULE}`",
    ]


# The release ships only a head a round judged, and converge's catch-up round is how a
# late commit gets judged. Why: 0017-converge-audit-fixes design D1, D2.
_HEAD_CHECK = "HEAD equals the head:"
_CATCH_UP = "catch-up round"


def _reviewed_head_problems(base: Path) -> list[str]:
    """Return one line per breach of the reviewed-head rule in `base`'s skills."""
    return _needle_problems(
        base, "mf-release", present=(_HEAD_CHECK,)
    ) + _needle_problems(base, "mf-converge", present=(_CATCH_UP,))


@pytest.mark.spec("sdd:converge-audit:reviewed-head")
def test_the_release_checks_the_judged_head_and_converge_catches_up() -> None:
    assert _reviewed_head_problems(_REPO) == []


@pytest.mark.spec("sdd:converge-audit:reviewed-head")
def test_the_reviewed_head_scan_reports_both_breaches(tmp_path: Path) -> None:
    # A release that reads only the verdicts, and a converge with no catch-up round:
    # both breaches are reported.
    _plant(
        tmp_path,
        {
            "mf-release": "Read each findings file's `verdict:`.\n",
            "mf-converge": "Loop to a cap of three rounds.\n",
        },
    )

    assert _reviewed_head_problems(tmp_path) == [
        f"skills/mf-release/SKILL.md: does not name `{_HEAD_CHECK}`",
        f"skills/mf-converge/SKILL.md: does not name `{_CATCH_UP}`",
    ]
