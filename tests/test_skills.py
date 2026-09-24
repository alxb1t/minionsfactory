"""Skill-text guards: what the shipped `skills/mf-*` must say, proved by a scan."""

from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent

# The three skills that run the gate. Each states the gate rule in its own words —
# skills are self-contained — so each must name both the gate and the dry run printed
# before it (0011-cut-and-gate design D1).
_GATE_RUNNERS = ("mf-build", "mf-converge", "mf-release")


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
