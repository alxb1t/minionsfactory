"""Skill-text guards: what the shipped `skills/mf-*` must say, proved by a scan."""

import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent

# The three skills that run the gate. Each states the gate rule in its own words —
# skills are self-contained — so each must name both the gate and the dry run printed
# before it (0011-cut-and-gate design D1).
_GATE_RUNNERS = ("mf-build", "mf-converge", "mf-release")

# The input contract: `mf-build` owns it, `mf-cut-change` carries the same ids, and
# this scan holds the two id sets equal (0011-cut-and-gate design D5). An id is the
# bold first cell of a table row in the `## Input contract` section, up to the next
# `## ` heading.
_CONTRACT_OWNERS = ("mf-build", "mf-cut-change")
_CONTRACT_ROW = re.compile(r"^\| \*\*I(\d+)\*\* \|")


def _gate_problems(base: Path) -> list[str]:
    """Return one line per breach of the gate rule in `base`'s `skills/*/SKILL.md`."""
    problems: list[str] = []
    for path in sorted((base / "skills").glob("*/SKILL.md")):
        for number, line in enumerate(path.read_text().splitlines(), start=1):
            if "minions.toml" in line:
                problems.append(
                    f"{path.relative_to(base)}:{number}: names minions.toml"
                )
    for name in _GATE_RUNNERS:
        path = base / "skills" / name / "SKILL.md"
        text = path.read_text() if path.is_file() else ""
        for needle in ("make gate", "make -n gate"):
            if needle not in text:
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
    # dry run from another, and confirm both are reported.
    ok = "Run `make -n gate`, then `make gate`.\n"
    for name in _GATE_RUNNERS:
        (tmp_path / "skills" / name).mkdir(parents=True)
        (tmp_path / "skills" / name / "SKILL.md").write_text(ok)
    (tmp_path / "skills" / "mf-build" / "SKILL.md").write_text(
        ok + "Read `.minions/minions.toml`.\n"
    )
    (tmp_path / "skills" / "mf-release" / "SKILL.md").write_text("Run `make gate`.\n")

    assert _gate_problems(tmp_path) == [
        "skills/mf-build/SKILL.md:2: names minions.toml",
        "skills/mf-release/SKILL.md: does not name `make -n gate`",
    ]


def _contract_ids(path: Path) -> list[int]:
    """Return the ids in `path`'s `## Input contract` section, in order."""
    ids: list[int] = []
    inside = False
    for line in path.read_text().splitlines():
        if line.startswith("## "):
            inside = line == "## Input contract"
        elif inside and (match := _CONTRACT_ROW.match(line)):
            ids.append(int(match.group(1)))
    return ids


def _contract_problems(base: Path) -> list[str]:
    """Return one line per breach of the shared input contract in `base`'s skills."""
    problems: list[str] = []
    sets: dict[str, set[int]] = {}
    for name in _CONTRACT_OWNERS:
        path = base / "skills" / name / "SKILL.md"
        if not path.is_file():
            problems.append(f"skills/{name}/SKILL.md: does not exist")
            continue
        ids = _contract_ids(path)
        if not ids:
            problems.append(f"skills/{name}/SKILL.md: no input contract ids")
        elif sorted(ids) != list(range(1, max(ids) + 1)):
            problems.append(f"skills/{name}/SKILL.md: ids do not run I1…I{max(ids)}")
        sets[name] = set(ids)
    build, cut = (sets.get(name) for name in _CONTRACT_OWNERS)
    if build is not None and cut is not None and build != cut:
        problems.append(
            f"id sets differ: only in mf-build {sorted(build - cut)}, "
            f"only in mf-cut-change {sorted(cut - build)}"
        )
    return problems


@pytest.mark.spec("sdd:input-contract:ids-agree")
def test_the_cut_and_the_build_carry_the_same_contract_ids() -> None:
    assert _contract_problems(_REPO) == []


@pytest.mark.spec("sdd:input-contract:ids-agree")
def test_the_contract_scan_reports_a_differing_id_and_a_gap(tmp_path: Path) -> None:
    # Plant I1–I3 in the build and I1, I3 in the cut: the cut has a gap, and the two
    # sets differ by one id. A row past the section's end must not count.
    def write(name: str, ids: tuple[int, ...]) -> None:
        rows = "".join(f"| **I{n}** | must | — |\n" for n in ids)
        text = f"## Input contract\n\n| id | a | b |\n|---|---|---|\n{rows}\n"
        text += "## Never\n\n| **I9** | outside | — |\n"
        (tmp_path / "skills" / name).mkdir(parents=True)
        (tmp_path / "skills" / name / "SKILL.md").write_text(text)

    write("mf-build", (1, 2, 3))
    write("mf-cut-change", (1, 3))

    assert _contract_problems(tmp_path) == [
        "skills/mf-cut-change/SKILL.md: ids do not run I1…I3",
        "id sets differ: only in mf-build [2], only in mf-cut-change []",
    ]
