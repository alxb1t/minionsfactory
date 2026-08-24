"""Repo-hygiene guards: conventions a grep can prove, so prose discipline can't slip."""

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

# The scan set, asserted below so narrowing it later is a visible edit, not a silent
# one. Deliberately EXCLUDED, each for its own reason (0005-change-cutover design §5):
#   - `openspec/specs/` — the specs describe the retirement and must be able to name it;
#     correctness there is owned by `specs check --strict` plus the release fold's
#     verify-after-fold, and this change's own delta prose folds in with the literal.
#   - `tests/` — the guard's own needles are literals in it.
#   - `CHANGELOG.md` and `openspec/changes/archive/` — the historical record, which must
#     keep saying what was true.
_SCANNED = ("orchestrator", "prompts", "docs", "README.md")

# The vault-path needle gets its OWN root set, and deliberately not `_SCANNED`: that
# tuple's exclusions are argued for the retired-vocabulary needle, and none of them
# holds here. `openspec/` and `CHANGELOG.md` are excluded there because the specs and
# the historical record must be able to name the retirement — but they are exactly the
# tracked files a role writes on every phase (the change's `tasks.md` and spec delta,
# the per-phase `## [Unreleased]` append), committed by roles that hold `Edit`/`Write`
# and told to echo an Inputs block carrying the vault's absolute path. The likeliest
# leak route must be the one the guard walks. Widening `_SCANNED` instead would turn
# the vocabulary guard red — this change's own delta names the retired path in order to
# describe its retirement, and that prose folds into `openspec/specs/` at release.
#
# So: every tracked root, with exclusions of its own. `.env` declares the needle and is
# gitignored; `.minions/` holds gitignored run artifacts (whose leak route `.gitignore`
# closes — S4), so only its tracked file is listed; `.git`, `.venv` and the caches are
# not part of the repo tree. Asserted below, so narrowing this later is a visible edit.
_VAULT_SCANNED = (
    "orchestrator",
    "prompts",
    "docs",
    "tests",
    "openspec",
    "skills",
    "template",
    ".github",
    "README.md",
    "CHANGELOG.md",
    "CLAUDE.md",
    "Makefile",
    "pyproject.toml",
    "uv.lock",
    ".env.example",
    ".gitignore",
    ".minions/minions.toml",
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


def _declared_vault_dir() -> str | None:
    """The vault path this repo's own (gitignored) `.env` declares, if it has one."""
    env_path = _REPO / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text().splitlines():
        key, separator, value = line.partition("=")
        if separator and key.strip() == "VAULT_PROJECT_DIR":
            return value.strip().strip('"') or None
    return None


@pytest.mark.spec("sdd:vault-layout:no-plan-path-references")
def test_the_retired_plan_model_is_named_nowhere_in_code_prompts_or_docs() -> None:
    assert _SCANNED == ("orchestrator", "prompts", "docs", "README.md")

    assert {needle: _hits(_REPO, _SCANNED, needle) for needle in _RETIRED} == {
        needle: [] for needle in _RETIRED
    }


@pytest.mark.spec("sdd:vault-layout:no-plan-path-references")
def test_the_guard_fails_when_any_retired_needle_is_reintroduced(
    tmp_path: Path,
) -> None:
    # The guard is only worth having if every needle bites: plant each one in a scanned
    # root in turn and confirm the plant is reported.
    (tmp_path / "orchestrator").mkdir()
    (tmp_path / "prompts").mkdir()
    (tmp_path / "docs" / "modules").mkdir(parents=True)

    for needle in _RETIRED:
        (tmp_path / "orchestrator" / "state.py").write_text(f'D = "{needle}"\n')
        (tmp_path / "prompts" / "coder.md").write_text(f"read the {needle}\n")
        (tmp_path / "docs" / "modules" / "state.md").write_text(f"the {needle} thing\n")
        (tmp_path / "README.md").write_text(f"a vault with {needle}\n")

        assert _hits(tmp_path, _SCANNED, needle) == [
            "orchestrator/state.py:1",
            "prompts/coder.md:1",
            "docs/modules/state.md:1",
            "README.md:1",
        ]


@pytest.mark.spec("sdd:vault-layout:vault-path-not-in-repo")
def test_the_operators_vault_path_is_named_nowhere_in_the_repo() -> None:
    # "Never commit the vault path" is a standing guardrail; this is the test that
    # proves it. The vault path travels in every role's Inputs block and every role
    # prompt now echoes its inputs, so the literal is one `git add -A` away from
    # history (`.minions/` is gitignored for the same reason).
    assert _VAULT_SCANNED[:4] == ("orchestrator", "prompts", "docs", "tests")
    assert {"openspec", "CHANGELOG.md"} <= set(_VAULT_SCANNED)
    assert set(_SCANNED) <= set(_VAULT_SCANNED)  # never narrower than the other guard

    vault_dir = _declared_vault_dir()
    if vault_dir is None:  # CI has no .env — nothing to check against
        pytest.skip("no VAULT_PROJECT_DIR declared in this repo's .env")

    # Compare through a local, so a failure prints the offending sites and never the
    # vault path itself.
    hits = _hits(_REPO, _VAULT_SCANNED, vault_dir)

    assert hits == []


@pytest.mark.spec("sdd:vault-layout:vault-path-not-in-repo")
def test_the_vault_path_guard_scans_the_files_a_role_writes_each_phase(
    tmp_path: Path,
) -> None:
    # The roots `_SCANNED` excludes are the ones a role commits every phase, so the
    # guard is only worth having if it reports a plant in *those*: plant a stand-in path
    # in the change tree and the CHANGELOG and confirm both are reported.
    needle = "/Users/nobody/Vault/Project"
    change_dir = tmp_path / "openspec" / "changes" / "0000-planted"
    change_dir.mkdir(parents=True)
    (change_dir / "tasks.md").write_text(f"- [x] 1 — wrote {needle}\n")
    (tmp_path / "CHANGELOG.md").write_text(f"landed under {needle}\n")

    assert sorted(_hits(tmp_path, _VAULT_SCANNED, needle)) == [
        "CHANGELOG.md:1",
        "openspec/changes/0000-planted/tasks.md:1",
    ]
