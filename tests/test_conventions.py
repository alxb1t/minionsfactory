"""Repo-hygiene guards: conventions a grep can prove, so prose discipline can't slip."""

import inspect
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent

# The retired vault-plan model. v0.5 deleted the reader; this guard keeps its directory
# AND its vocabulary from creeping back into shipped code, role prompts or docs. The
# needle set is deliberately wider than the path: every miss the v0.5 review found was a
# retired *symbol or phrase*, not the directory, and the two hand-run symbol greps that
# phase 4 and phase 6 used as acceptance left nothing durable behind.
#
# `current_phase` is in the set although `status._short_phase` once documented itself
# with it: that docstring was reworded to name the phase label it actually trims, so the
# needle needs no carve-out and the scan stays a plain "no hits anywhere" assertion.
_RETIRED = (
    "implementation_plans",
    "current_phase",
    "phaseN",
    "select_plan",
    "read_plan_state",
    "validate_plan",
    "PlanState",
    "_plan_version",
)

# The ONE root set, shared by every needle set below and asserted verbatim in
# `_assert_named_nowhere`, so narrowing *the tuple* is a visible edit and not a silent
# one. The literal does not catch a root that disappears from disk — `rglob` on a
# missing path yields nothing rather than raising — so what closes that half is the rule
# that a deletion lands in the same commit as the guard edit it forces, leaving no
# commit shipping a scan narrower than the tuple it asserts (0008-surface-collapse
# design §4). The two sets were once scanned over separate roots, because a retired
# *plan* needle was live check text inside the planning-skill surface; that surface is
# deleted, so one root set now crosses every needle set green.
#
# Deliberately EXCLUDED, each for its own reason (0005-change-cutover design §5):
#   - `openspec/specs/` — the specs describe the retirement and must be able to name it;
#     correctness there is owned by `specs check --strict` plus the release fold's
#     verify-after-fold, and this change's own delta prose folds in with the literal.
#   - `tests/` — the guard's own needles are literals in it.
#   - `CHANGELOG.md` and `openspec/changes/archive/` — the historical record, which must
#     keep saying what was true.
#
# v0.8 widened it to nine: `.github/`, `Makefile` and `pyproject.toml` were outside the
# scan and free of all fourteen needles, a future-regression gap rather than a live
# hole, and they are now inside it. v0.10 makes it ten by re-adding `skills/`, which WAS
# a scanned root under v0.7 and left the tuple in v0.8 only because that version deleted
# the directory — re-creating it without re-adding it would re-open a gap already closed
# once, and a shipped skill is a role prompt. That is the gap this widening closes, not
# the whole tree: `.gitignore`, `.python-version`, `uv.lock` and the four files of the
# ACTIVE `openspec/changes/<id>/` are tracked, non-historical, and neither scanned nor
# declared above. The active change is the load-bearing one,
# and it cannot simply be added — a change's own delta must be able to name the
# vocabulary it retires, the same reason `openspec/specs/` is excluded, so scanning it
# turns this guard red today.
#
# NO exclusion is declared for any directory inside the scanned roots — the deletions
# land in the same commit as the guard edit they force, so nothing needs suppressing.
_SCANNED = (
    "orchestrator",
    "prompts",
    "skills",
    "docs",
    "README.md",
    "CLAUDE.md",
    ".env.example",
    ".github",
    "Makefile",
    "pyproject.toml",
)

_TEXT_SUFFIXES = frozenset({".py", ".md", ".toml", ".txt", ".yml", ".yaml", ".json"})


def _text_files(root: Path) -> list[Path]:
    """Every text file at or under `root` (a file root yields itself)."""
    if root.is_file():
        return [root]
    return [
        path
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.suffix in _TEXT_SUFFIXES
    ]


def _hits(base: Path, roots: tuple[str, ...], needle: str) -> list[str]:
    """Return `path:line` for every occurrence of `needle` under the scanned roots."""
    found: list[str] = []
    for name in roots:
        for path in _text_files(base / name):
            for number, line in enumerate(path.read_text().splitlines(), start=1):
                if needle in line:
                    found.append(f"{path.relative_to(base)}:{number}")
    return found


def _assert_named_nowhere(needles: tuple[str, ...]) -> None:
    """Assert the root set verbatim, then that no needle is named under it."""
    assert _SCANNED == (
        "orchestrator",
        "prompts",
        "skills",
        "docs",
        "README.md",
        "CLAUDE.md",
        ".env.example",
        ".github",
        "Makefile",
        "pyproject.toml",
    )

    assert {needle: _hits(_REPO, _SCANNED, needle) for needle in needles} == {
        needle: [] for needle in needles
    }


# One planted file per scanned root, in `_SCANNED` order.
_PLANTS = (
    "orchestrator/plant.py",
    "prompts/plant.md",
    "skills/mf-build/SKILL.md",
    "docs/modules/plant.md",
    "README.md",
    "CLAUDE.md",
    ".env.example",
    ".github/workflows/ci.yml",
    "Makefile",
    "pyproject.toml",
)


def _assert_every_plant_bites(base: Path, needles: tuple[str, ...]) -> None:
    """Plant each needle in every scanned root in turn and assert every plant is hit."""
    # A guard whose needle does not bite in every root is decoration.
    for plant in _PLANTS:
        (base / plant).parent.mkdir(parents=True, exist_ok=True)
    for needle in needles:
        for plant in _PLANTS:
            (base / plant).write_text(f"the {needle}\n")
        assert _hits(base, _SCANNED, needle) == [f"{plant}:1" for plant in _PLANTS]


@pytest.mark.spec("sdd:vault-layout:no-plan-path-references")
def test_the_retired_plan_model_is_named_nowhere_in_code_prompts_or_docs() -> None:
    _assert_named_nowhere(_RETIRED)


@pytest.mark.spec("sdd:vault-layout:no-plan-path-references")
def test_the_guard_fails_when_any_retired_needle_is_reintroduced(
    tmp_path: Path,
) -> None:
    _assert_every_plant_bites(tmp_path, _RETIRED)


# The retired vault-write model. v0.7 moved findings, the HALT report and the
# deferred-work backlog into the target repo's `.minions/` and deleted the vault
# preflight, so the symbols that named the old root are dead. The needles are the six
# dead *symbols*: the declared environment key, the resolved-directory parameter in both
# its spellings, the two deleted preflight functions, and the release-record symbol.
#
# Kept DISTINCT from the plan needles above although both are now scanned over the same
# roots: the two record different retirements with different histories, and merging them
# would lose which regression a future failure is.
#
# `vault_project_dir` is listed although `vault_dir` looks like a substring of it — it
# is not, and without it a doc could ship a stale
# `halt_report_exists(vault_project_dir)` signature and pass. The bare word *vault* and
# the token `<vault>/` are NOT needles: the vault still exists, and the layout rule this
# repo states — the vault reaches the repo, the repo never reaches the vault — must be
# able to name it.
_RETIRED_VAULT = (
    "VAULT_PROJECT_DIR",
    "vault_dir",
    "vault_project_dir",
    "read_vault_dir",
    "verify_vault_access",
    "release_log",
)


@pytest.mark.spec("sdd:vault-layout:no-retired-vault-vocabulary")
def test_the_retired_vault_vocabulary_is_named_nowhere_in_code_prompts_or_docs() -> (
    None
):
    _assert_named_nowhere(_RETIRED_VAULT)


@pytest.mark.spec("sdd:vault-layout:no-retired-vault-vocabulary")
def test_the_scan_carves_out_no_directory_inside_its_scanned_roots() -> None:
    # The scenario asserts the absence of a carve-out, which is a property of the guard
    # itself and not only of the tree it scans. Two halves: the scan takes no exclusion
    # argument, so there is no seam a suppression could enter through...
    assert list(inspect.signature(_hits).parameters) == ["base", "roots", "needle"]
    assert list(inspect.signature(_text_files).parameters) == ["root"]

    # ...and in fact it reaches every directory inside the scanned roots — enumerated
    # here with `iterdir`, independently of the `rglob` walk under test, so the two can
    # disagree. Nothing is suppressed: a deletion lands in the same commit as the guard
    # edit it forces, so no commit ever ships a scan that steps around a live directory.
    for name in _SCANNED:
        root = _REPO / name
        if not root.is_dir():
            continue
        visited = {path.relative_to(root).parts[0] for path in _text_files(root)}
        declared = {entry.name for entry in root.iterdir() if entry.is_dir()}
        assert declared - {"__pycache__"} <= visited


@pytest.mark.spec("sdd:vault-layout:no-retired-vault-vocabulary")
def test_the_guard_fails_when_any_retired_vault_needle_is_reintroduced(
    tmp_path: Path,
) -> None:
    _assert_every_plant_bites(tmp_path, _RETIRED_VAULT)


# The retired gate config. The runner runs `make gate` like the skills and CI, so the
# file is deleted and its name retired (0015-runner-make-gate design D5). Its own
# needle, apart from the sets above: a different retirement, a different regression.
_RETIRED_GATE_CONFIG = ("minions.toml",)


@pytest.mark.spec("sdd:retired-gate-config:named-nowhere")
def test_the_retired_gate_config_is_named_nowhere_in_code_prompts_or_docs() -> None:
    _assert_named_nowhere(_RETIRED_GATE_CONFIG)


@pytest.mark.spec("sdd:retired-gate-config:named-nowhere")
def test_the_guard_fails_when_the_retired_gate_config_is_reintroduced(
    tmp_path: Path,
) -> None:
    _assert_every_plant_bites(tmp_path, _RETIRED_GATE_CONFIG)


@pytest.mark.spec_exempt("structural — the method doc is wired into the docs map")
def test_the_method_doc_exists_and_the_docs_map_links_it() -> None:
    # Two independent halves, so removing either one fails: the page exists, and the
    # docs map names it. A page nothing links to is as good as absent to a reader who
    # starts where the map tells them to.
    assert (_REPO / "docs" / "sdd.md").is_file()

    assert "sdd.md" in (_REPO / "docs" / "README.md").read_text()
