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

# The ONE root set, shared by both needle sets below and asserted verbatim in each scan
# test, so narrowing *the tuple* is a visible edit and not a silent one. The literal
# does not catch a root that disappears from disk — `rglob` on a missing path yields
# nothing rather than raising — so what closes that half is the rule that a deletion
# lands in the same commit as the guard edit it forces, leaving no commit shipping a
# scan narrower than the tuple it asserts (0008-surface-collapse design §4). The two
# sets were once scanned over separate roots, because a retired *plan* needle was live
# check text inside the planning-skill surface; that surface is deleted, so one root set
# now crosses both needle sets green.
#
# Deliberately EXCLUDED, each for its own reason (0005-change-cutover design §5):
#   - `openspec/specs/` — the specs describe the retirement and must be able to name it;
#     correctness there is owned by `specs check --strict` plus the release fold's
#     verify-after-fold, and this change's own delta prose folds in with the literal.
#   - `tests/` — the guard's own needles are literals in it.
#   - `CHANGELOG.md` and `openspec/changes/archive/` — the historical record, which must
#     keep saying what was true.
#
# Still narrower than a whole-tree grep: `.github/`, `Makefile` and `pyproject.toml` are
# outside it, free of all fourteen needles today, so the gap is a future regression
# rather than a live hole. Widening is recorded for v0.8.
#
# NO exclusion is declared for any directory inside the scanned roots — the deletions
# land in the same commit as the guard edit they force, so nothing needs suppressing.
_SCANNED = (
    "orchestrator",
    "prompts",
    "docs",
    "README.md",
    "CLAUDE.md",
    ".env.example",
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


@pytest.mark.spec("sdd:vault-layout:no-plan-path-references")
def test_the_retired_plan_model_is_named_nowhere_in_code_prompts_or_docs() -> None:
    assert _SCANNED == (
        "orchestrator",
        "prompts",
        "docs",
        "README.md",
        "CLAUDE.md",
        ".env.example",
    )

    assert {needle: _hits(_REPO, _SCANNED, needle) for needle in _RETIRED} == {
        needle: [] for needle in _RETIRED
    }


@pytest.mark.spec("sdd:vault-layout:no-plan-path-references")
def test_the_guard_fails_when_any_retired_needle_is_reintroduced(
    tmp_path: Path,
) -> None:
    # The guard is only worth having if every needle bites: plant each one in every
    # scanned root in turn and confirm every plant is reported.
    (tmp_path / "orchestrator").mkdir()
    (tmp_path / "prompts").mkdir()
    (tmp_path / "docs" / "modules").mkdir(parents=True)

    for needle in _RETIRED:
        (tmp_path / "orchestrator" / "state.py").write_text(f'D = "{needle}"\n')
        (tmp_path / "prompts" / "coder.md").write_text(f"read the {needle}\n")
        (tmp_path / "docs" / "modules" / "state.md").write_text(f"the {needle} thing\n")
        (tmp_path / "README.md").write_text(f"a vault with {needle}\n")
        (tmp_path / "CLAUDE.md").write_text(f"the {needle} model is retired\n")
        (tmp_path / ".env.example").write_text(f"{needle}=\n")

        assert _hits(tmp_path, _SCANNED, needle) == [
            "orchestrator/state.py:1",
            "prompts/coder.md:1",
            "docs/modules/state.md:1",
            "README.md:1",
            "CLAUDE.md:1",
            ".env.example:1",
        ]


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
    assert _SCANNED == (
        "orchestrator",
        "prompts",
        "docs",
        "README.md",
        "CLAUDE.md",
        ".env.example",
    )

    assert {needle: _hits(_REPO, _SCANNED, needle) for needle in _RETIRED_VAULT} == {
        needle: [] for needle in _RETIRED_VAULT
    }


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
    # Same bar as the plan needles: each one must bite, in every root of the shared set,
    # or the scan is decoration.
    (tmp_path / "orchestrator").mkdir()
    (tmp_path / "prompts").mkdir()
    (tmp_path / "docs" / "modules").mkdir(parents=True)

    for needle in _RETIRED_VAULT:
        (tmp_path / "orchestrator" / "findings.py").write_text(f'D = "{needle}"\n')
        (tmp_path / "prompts" / "coder.md").write_text(f"write to the {needle}\n")
        (tmp_path / "docs" / "modules" / "findings.md").write_text(f"the {needle}\n")
        (tmp_path / "README.md").write_text(f"a report under {needle}\n")
        (tmp_path / "CLAUDE.md").write_text(f"the vault is {needle}\n")
        (tmp_path / ".env.example").write_text(f"{needle}=\n")

        assert _hits(tmp_path, _SCANNED, needle) == [
            "orchestrator/findings.py:1",
            "prompts/coder.md:1",
            "docs/modules/findings.md:1",
            "README.md:1",
            "CLAUDE.md:1",
            ".env.example:1",
        ]


@pytest.mark.spec_exempt("structural — the method doc is wired into the docs map")
def test_the_method_doc_exists_and_the_docs_map_links_it() -> None:
    # Two independent halves, so removing either one fails: the page exists, and the
    # docs map names it. A page nothing links to is as good as absent to a reader who
    # starts where the map tells them to.
    assert (_REPO / "docs" / "sdd.md").is_file()

    assert "sdd.md" in (_REPO / "docs" / "README.md").read_text()
