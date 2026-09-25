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
# scan holds the two id sets equal. An id is the bold first cell of a table row in the
# named `## ` section, up to the next `## ` heading.
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


def _section_ids(path: Path, heading: str, letter: str) -> list[int]:
    """Return the `letter` ids in `path`'s `heading` section, in order."""
    row = re.compile(rf"^\| \*\*{letter}(\d+)\*\* \|")
    ids: list[int] = []
    inside = False
    for line in path.read_text().splitlines():
        if line.startswith("## "):
            inside = line == heading
        elif inside and (match := row.match(line)):
            ids.append(int(match.group(1)))
    return ids


def _shared_id_problems(base: Path, heading: str, letter: str) -> list[str]:
    """Return one line per breach of the shared `heading` list in `base`'s skills."""
    problems: list[str] = []
    sets: dict[str, set[int]] = {}
    for name in _SHARED_OWNERS:
        path = base / "skills" / name / "SKILL.md"
        if not path.is_file():
            problems.append(f"skills/{name}/SKILL.md: does not exist")
            continue
        ids = _section_ids(path, heading, letter)
        if not ids:
            problems.append(f"skills/{name}/SKILL.md: no ids in `{heading}`")
        elif sorted(ids) != list(range(1, max(ids) + 1)):
            problems.append(
                f"skills/{name}/SKILL.md: ids do not run {letter}1…{letter}{max(ids)}"
            )
        sets[name] = set(ids)
    build, cut = (sets.get(name) for name in _SHARED_OWNERS)
    if build is not None and cut is not None and build != cut:
        problems.append(
            f"id sets differ: only in mf-build {sorted(build - cut)}, "
            f"only in mf-cut-change {sorted(cut - build)}"
        )
    return problems


def _planted_problems(base: Path, heading: str, letter: str) -> list[str]:
    """Return what the scan reports for a planted build and cut that disagree.

    The build holds ids 1–3 and the cut 1 and 3, so the cut has a gap and the two sets
    differ by one id. A row past the section's end must not count.
    """
    for name, numbers in {"mf-build": (1, 2, 3), "mf-cut-change": (1, 3)}.items():
        rows = "".join(f"| **{letter}{n}** | must | — |\n" for n in numbers)
        text = f"{heading}\n\n| id | a | b |\n|---|---|---|\n{rows}\n"
        text += f"## Never\n\n| **{letter}9** | outside | — |\n"
        (base / "skills" / name).mkdir(parents=True)
        (base / "skills" / name / "SKILL.md").write_text(text)
    return _shared_id_problems(base, heading, letter)


@pytest.mark.spec("sdd:input-contract:ids-agree")
def test_the_cut_and_the_build_carry_the_same_contract_ids() -> None:
    assert _shared_id_problems(_REPO, "## Input contract", "I") == []


@pytest.mark.spec("sdd:input-contract:ids-agree")
def test_the_contract_scan_reports_a_differing_id_and_a_gap(tmp_path: Path) -> None:
    assert _planted_problems(tmp_path, "## Input contract", "I") == [
        "skills/mf-cut-change/SKILL.md: ids do not run I1…I3",
        "id sets differ: only in mf-build [2], only in mf-cut-change []",
    ]


@pytest.mark.spec("sdd:prose-rules:ids-agree")
def test_the_cut_and_the_build_carry_the_same_prose_rule_ids() -> None:
    assert _shared_id_problems(_REPO, "## Prose rules", "P") == []


@pytest.mark.spec("sdd:prose-rules:ids-agree")
def test_the_prose_scan_reports_a_differing_id_and_a_gap(tmp_path: Path) -> None:
    assert _planted_problems(tmp_path, "## Prose rules", "P") == [
        "skills/mf-cut-change/SKILL.md: ids do not run P1…P3",
        "id sets differ: only in mf-build [2], only in mf-cut-change []",
    ]


# The card: `mf-converge` owns its fields and `mf-backlog-export` carries the same
# labels, so the card converge carries is the card the export keeps whole. A label is
# the bold first cell of a table row. Why: 0014-backlog-cards design D1, D7.
_CARD_CARRIERS = ("mf-converge", "mf-backlog-export")
_CARD_HEADING = "## The card"


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


def _card_problems(base: Path) -> list[str]:
    """Return one line per breach of the shared card fields in `base`'s skills."""
    problems: list[str] = []
    sets: dict[str, set[str]] = {}
    for name in _CARD_CARRIERS:
        path = base / "skills" / name / "SKILL.md"
        labels = _section_labels(path, _CARD_HEADING) if path.is_file() else []
        if not labels:
            problems.append(f"skills/{name}/SKILL.md: no labels in `{_CARD_HEADING}`")
        sets[name] = set(labels)
    converge, export = (sets[name] for name in _CARD_CARRIERS)
    if converge and export and converge != export:
        problems.append(
            f"label sets differ: only in mf-converge {sorted(converge - export)}, "
            f"only in mf-backlog-export {sorted(export - converge)}"
        )
    return problems


def _card_text(*labels: str) -> str:
    """Return a skill text whose `## The card` table holds `labels`."""
    rows = "".join(f"| **{label}** | — |\n" for label in labels)
    return f"{_CARD_HEADING}\n\n| field | holds |\n|---|---|\n{rows}"


@pytest.mark.spec("sdd:backlog-cards:fields-agree")
def test_converge_and_the_export_carry_the_same_card_fields() -> None:
    assert _card_problems(_REPO) == []


@pytest.mark.spec("sdd:backlog-cards:fields-agree")
def test_the_card_scan_reports_a_differing_label_and_a_missing_section(
    tmp_path: Path,
) -> None:
    # A pair differing by one label, and an export with no card section: each is
    # reported. The export's row past `## Never` must not count as a card field.
    plants = {
        "differ": (_card_text("Title", "Fix", "Status"), _card_text("Title", "Status")),
        "missing": (_card_text("Title"), "## Never\n\n| **Title** | — |\n"),
    }
    for case, texts in plants.items():
        for name, text in zip(_CARD_CARRIERS, texts, strict=True):
            (tmp_path / case / "skills" / name).mkdir(parents=True)
            (tmp_path / case / "skills" / name / "SKILL.md").write_text(text)

    assert _card_problems(tmp_path / "differ") == [
        "label sets differ: only in mf-converge ['Fix'], only in mf-backlog-export []",
    ]
    assert _card_problems(tmp_path / "missing") == [
        "skills/mf-backlog-export/SKILL.md: no labels in `## The card`",
    ]


# Converge is optional (0012-converge-optional design D1, D5): the release states a
# skipped converge in one literal line, and the rule that a missing findings file is
# not clean leaves the release but stays in converge, which judges its own stations
# by it.
_SKIP_LINE = "converge: skipped — no findings files"
_MISSING_FILE_RULE = "A missing findings file is not clean"


def _converge_optional_problems(base: Path) -> list[str]:
    """Return one line per breach of the converge-optional rule in `base`'s skills."""
    release_text = (base / "skills" / "mf-release" / "SKILL.md").read_text()
    converge_text = (base / "skills" / "mf-converge" / "SKILL.md").read_text()
    problems: list[str] = []
    if _SKIP_LINE not in release_text:
        problems.append(f"skills/mf-release/SKILL.md: does not name `{_SKIP_LINE}`")
    if _MISSING_FILE_RULE in release_text:
        problems.append(f"skills/mf-release/SKILL.md: names `{_MISSING_FILE_RULE}`")
    if _MISSING_FILE_RULE not in converge_text:
        problems.append(
            f"skills/mf-converge/SKILL.md: does not name `{_MISSING_FILE_RULE}`"
        )
    return problems


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
        f"skills/mf-release/SKILL.md: names `{_MISSING_FILE_RULE}`",
        f"skills/mf-converge/SKILL.md: does not name `{_MISSING_FILE_RULE}`",
    ]
