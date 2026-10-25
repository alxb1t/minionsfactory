"""Skill-text structure checks: what a reader cannot check by eye in `skills/mf-*`.

Why no check holds a sentence: docs/decisions.md D42.
"""

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent


# The shared lists: `mf-build` owns each, `mf-cut-change` carries the same ids, and a
# scan holds their labels equal and each id run unbroken. An id is the bold first cell
# of a table row in the named `## ` section, up to the next `## ` heading.
# Why: 0011-cut-and-gate design D5, 0013-how-the-builder-writes design D3.
_SHARED_OWNERS = ("mf-build", "mf-cut-change")
_CONTRACT = "## Input contract"


def _section_labels(path: Path, heading: str) -> list[str]:
    """Return the bold first cells of the table rows in `path`'s `heading` section.

    The section runs up to the next `## ` heading.
    """
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


def _shared_label_problems(
    base: Path, heading: str, owners: tuple[str, ...] = _SHARED_OWNERS
) -> list[str]:
    """Return one line per breach of the `heading` labels the `owners` carry.

    The first of `owners` owns the list; each carrier is compared with it.
    """
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
    first = sets.get(owners[0])
    for name in owners[1:]:
        carried = sets.get(name)
        if first and carried and first != carried:
            problems.append(
                f"labels differ: only in {owners[0]} {sorted(first - carried)}, "
                f"only in {name} {sorted(carried - first)}"
            )
    return problems


def _shared_id_problems(
    base: Path, heading: str, letter: str, owners: tuple[str, ...] = _SHARED_OWNERS
) -> list[str]:
    """Return one line per breach of the shared `heading` list in `base`'s skills."""
    problems = _shared_label_problems(base, heading, owners)
    for name in owners:
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


def _planted_problems(
    base: Path, heading: str, letter: str, owners: tuple[str, ...] = _SHARED_OWNERS
) -> list[str]:
    """Return what the scan reports for planted owners that disagree.

    The owner holds ids 1–3, the first carrier 1 and 3, and any later carrier 1–2, so
    the first carrier has a gap and each carrier differs by one id. A row past the
    section's end must not count.
    """
    outside = f"\n## Never\n\n| **{letter}9** | outside |\n"
    ids = [(1, 2, 3), (1, 3)] + [(1, 2)] * (len(owners) - 2)
    texts = {
        name: _table_text(heading, *(f"{letter}{n}" for n in held)) + outside
        for name, held in zip(owners, ids, strict=True)
    }
    _plant(base, texts)
    return _shared_id_problems(base, heading, letter, owners)


def test_the_cut_and_the_build_carry_the_same_contract_ids() -> None:
    assert _shared_id_problems(_REPO, _CONTRACT, "I") == []


def test_the_contract_scan_reports_a_differing_id_and_a_gap(tmp_path: Path) -> None:
    assert _planted_problems(tmp_path, _CONTRACT, "I") == [
        "labels differ: only in mf-build ['I2'], only in mf-cut-change []",
        "skills/mf-cut-change/SKILL.md: ids do not run I1…I3",
    ]


def test_the_cut_and_the_build_carry_the_same_prose_rule_ids() -> None:
    assert _shared_id_problems(_REPO, "## Prose rules", "P") == []


def test_the_prose_scan_reports_a_differing_id_and_a_gap(tmp_path: Path) -> None:
    assert _planted_problems(tmp_path, "## Prose rules", "P") == [
        "labels differ: only in mf-build ['P2'], only in mf-cut-change []",
        "skills/mf-cut-change/SKILL.md: ids do not run P1…P3",
    ]


# The rules for tests: `mf-build` owns them, and the cut and converge carry the same
# ids, since the fix station runs in a target repo and cannot be told to read the build.
# Why: 0026-test-cost design B2.
_TEST_RULE_CARRIERS = ("mf-build", "mf-cut-change", "mf-converge")
_TEST_RULES = "## Rules for tests"


def test_the_build_the_cut_and_converge_carry_the_same_test_rule_ids() -> None:
    assert _shared_id_problems(_REPO, _TEST_RULES, "T", _TEST_RULE_CARRIERS) == []


def test_the_test_rule_scan_reports_each_differing_carrier_and_a_gap(
    tmp_path: Path,
) -> None:
    assert _planted_problems(tmp_path, _TEST_RULES, "T", _TEST_RULE_CARRIERS) == [
        "labels differ: only in mf-build ['T2'], only in mf-cut-change []",
        "labels differ: only in mf-build ['T3'], only in mf-converge []",
        "skills/mf-cut-change/SKILL.md: ids do not run T1…T3",
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


def test_only_converge_carries_the_card() -> None:
    assert _card_owner_problems(_REPO) == []


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


# A new repo starts under the rules for tests: the bootstrap's `AGENTS.md` states them.
# Why: 0026-test-cost design B13.
_AGENTS_TEMPLATE = "skills/mf-bootstrap/templates/AGENTS.md.tmpl"
_TEMPLATE_TESTS = "## Tests"


def _template_tests_problems(base: Path) -> list[str]:
    """Return a line when `base`'s bootstrap `AGENTS.md` template has no `## Tests`."""
    lines = (base / _AGENTS_TEMPLATE).read_text().splitlines()
    if _TEMPLATE_TESTS in lines:
        return []
    return [f"{_AGENTS_TEMPLATE}: no `{_TEMPLATE_TESTS}` line"]


def test_the_bootstrap_holds_its_template_tests_section() -> None:
    assert _template_tests_problems(_REPO) == []


def test_the_template_tests_scan_reports_a_wrong_heading(tmp_path: Path) -> None:
    # A heading one level down is not the section.
    (tmp_path / _AGENTS_TEMPLATE).parent.mkdir(parents=True)
    (tmp_path / _AGENTS_TEMPLATE).write_text("# <name>\n\n### Tests\n")

    assert _template_tests_problems(tmp_path) == [
        f"{_AGENTS_TEMPLATE}: no `{_TEMPLATE_TESTS}` line"
    ]


# The bootstrap's templates cover D18's target layout, with `.minions/` as a
# `.gitignore` line, and the gate template validates the specs.
# Why: 0024-bootstrap design B11.
_TEMPLATES = "skills/mf-bootstrap/templates"
_LAYOUT_ENTRY = re.compile(r"^[├└]── (\S+)")
_RUN_OUTPUT = ".minions/"
_ALSO_WRITTEN = ("CHANGELOG.md", "README.md")
_VALIDATE = "openspec validate --all --strict --no-interactive"


def _layout_entries(base: Path) -> list[str]:
    """Return the entries of D18's tree in `base`'s decisions, in order.

    e.g. "├── openspec/specs/      the living spec" → "openspec/specs/"
    """
    entries: list[str] = []
    inside = False
    for line in (base / "docs" / "decisions.md").read_text().splitlines():
        if line.startswith("### "):
            inside = line.startswith("### D18 ")
        elif inside and (match := _LAYOUT_ENTRY.match(line)):
            entries.append(match.group(1))
    return entries


def _layout_problems(base: Path) -> list[str]:
    """Return one line per breach of B11 by `base`'s bootstrap templates.

    e.g. no `AGENTS.md.tmpl` → "…/templates: no template for `AGENTS.md`"
    """
    root = base / _TEMPLATES
    targets = {
        path.relative_to(root).as_posix().removesuffix(".tmpl"): path
        for path in root.rglob("*.tmpl")
    }
    entries = _layout_entries(base)
    problems = [] if entries else ["docs/decisions.md: no tree under `### D18`"]
    for entry in [*entries, *_ALSO_WRITTEN]:
        if entry == _RUN_OUTPUT:
            continue
        if entry.endswith("/"):
            if not any(t.startswith(entry) for t in targets):
                problems.append(f"{_TEMPLATES}: no template under `{entry}`")
        elif entry not in targets:
            problems.append(f"{_TEMPLATES}: no template for `{entry}`")
    ignore = targets.get(".gitignore")
    if ignore is None or _RUN_OUTPUT not in ignore.read_text().splitlines():
        problems.append(f"{_TEMPLATES}: `.gitignore` does not name `{_RUN_OUTPUT}`")
    makefile = targets.get("Makefile")
    if makefile is None or _VALIDATE not in makefile.read_text():
        problems.append(f"{_TEMPLATES}: `Makefile` does not name `{_VALIDATE}`")
    return problems


def test_the_bootstrap_templates_cover_the_target_layout() -> None:
    assert _layout_problems(_REPO) == []


def test_the_layout_scan_reports_every_breach(tmp_path: Path) -> None:
    # A D18 tree, and a later decision's tree entry that must not count.
    decisions = (
        "### D18 · The layout\n\n"
        "├── openspec/specs/      the living spec\n"
        "├── openspec/changes/    the changes\n"
        "├── Makefile             the gate\n"
        "├── AGENTS.md            what is true\n"
        "└── .minions/            run output\n\n"
        "### D19 · Another\n\n"
        "└── docs/                outside D18\n"
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "decisions.md").write_text(decisions)
    # Templates with no `openspec/changes/`, `AGENTS.md` or `README.md`, a `.gitignore`
    # that only mentions `.minions/` in a comment, and a gate that validates nothing.
    root = tmp_path / _TEMPLATES
    (root / "openspec" / "specs").mkdir(parents=True)
    (root / "openspec" / "specs" / ".gitkeep.tmpl").write_text("")
    (root / "Makefile.tmpl").write_text("gate:\n\ttrue\n")
    (root / "CHANGELOG.md.tmpl").write_text("## [Unreleased]\n")
    (root / ".gitignore.tmpl").write_text("# not .minions/\n*.pyc\n")

    assert _layout_problems(tmp_path) == [
        f"{_TEMPLATES}: no template under `openspec/changes/`",
        f"{_TEMPLATES}: no template for `AGENTS.md`",
        f"{_TEMPLATES}: no template for `README.md`",
        f"{_TEMPLATES}: `.gitignore` does not name `{_RUN_OUTPUT}`",
        f"{_TEMPLATES}: `Makefile` does not name `{_VALIDATE}`",
    ]

    # A D18 with no tree is reported, not read as clean.
    (tmp_path / "docs" / "decisions.md").write_text("### D18 · The layout\n")
    assert _layout_problems(tmp_path)[0] == "docs/decisions.md: no tree under `### D18`"


def _resource_problems(base: Path) -> list[str]:
    """Return missing, empty or escaping local skill-resource targets."""
    problems: list[str] = []
    for skill in sorted((base / "skills").glob("*/SKILL.md")):
        package = skill.parent.resolve()
        for target in re.findall(
            r"\[[^\]]*\]\((references/[^)\s]+)\)", skill.read_text()
        ):
            resolved = (package / target).resolve()
            prefix = f"{skill.relative_to(base)}: {target}"
            if not resolved.is_relative_to(package):
                problems.append(f"{prefix}: outside skill package")
            elif not resolved.is_file():
                problems.append(f"{prefix}: missing file")
            elif not resolved.read_text().strip():
                problems.append(f"{prefix}: empty file")
    return problems


def test_bundled_role_references_resolve() -> None:
    assert _resource_problems(_REPO) == []


def test_resource_scan_reports_missing_empty_and_escaping_targets(
    tmp_path: Path,
) -> None:
    _plant(
        tmp_path,
        {
            "mf-example": (
                "[valid](references/valid.md)\n"
                "[missing](references/missing.md)\n"
                "[empty](references/empty.md)\n"
                "[escape](references/../../outside.md)\n"
                "[symlink](references/linked.md)\n"
                "[design](design.md)\n"
                "[external](https://example.invalid/reference.md)\n"
            )
        },
    )
    skill = tmp_path / "skills" / "mf-example"
    references = skill / "references"
    references.mkdir()
    (references / "valid.md").write_text("Read the role.\n")
    (references / "empty.md").write_text(" \n\t")
    outside = tmp_path / "skills" / "outside.md"
    outside.write_text("Readable, but outside the package.\n")
    (references / "linked.md").symlink_to(outside)

    assert _resource_problems(tmp_path) == [
        "skills/mf-example/SKILL.md: references/missing.md: missing file",
        "skills/mf-example/SKILL.md: references/empty.md: empty file",
        "skills/mf-example/SKILL.md: references/../../outside.md: "
        "outside skill package",
        "skills/mf-example/SKILL.md: references/linked.md: outside skill package",
    ]
