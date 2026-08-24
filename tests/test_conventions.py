"""Repo-hygiene guards: conventions a grep can prove, so prose discipline can't slip."""

from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent

# The retired vault-plan location. v0.5 deleted the reader; this guard keeps the string
# from creeping back into shipped code, role prompts or docs.
_RETIRED_PLAN_DIR = "implementation_plans"

# The scan set, asserted below so narrowing it later is a visible edit, not a silent
# one. Deliberately EXCLUDED, each for its own reason (0005-change-cutover design §5):
#   - `openspec/specs/` — the specs describe the retirement and must be able to name it;
#     correctness there is owned by `specs check --strict` plus the release fold's
#     verify-after-fold, and this change's own delta prose folds in with the literal.
#   - `tests/` — the guard's own needle is a literal in it.
#   - `CHANGELOG.md` and `openspec/changes/archive/` — the historical record, which must
#     keep saying what was true.
_SCANNED = ("orchestrator", "prompts", "docs", "README.md")

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
def test_the_retired_plan_location_is_named_nowhere_in_code_prompts_or_docs() -> None:
    assert _SCANNED == ("orchestrator", "prompts", "docs", "README.md")

    assert _hits(_REPO, _SCANNED, _RETIRED_PLAN_DIR) == []


@pytest.mark.spec("sdd:vault-layout:no-plan-path-references")
def test_the_guard_fails_when_the_retired_path_is_reintroduced(tmp_path: Path) -> None:
    # The guard is only worth having if it bites: plant the string in each scanned root
    # and confirm every plant is reported.
    (tmp_path / "orchestrator").mkdir()
    (tmp_path / "prompts").mkdir()
    (tmp_path / "docs" / "modules").mkdir(parents=True)
    (tmp_path / "orchestrator" / "state.py").write_text(f'D = "{_RETIRED_PLAN_DIR}"\n')
    (tmp_path / "prompts" / "coder.md").write_text(f"read {_RETIRED_PLAN_DIR}/\n")
    (tmp_path / "docs" / "modules" / "state.md").write_text(
        f"the {_RETIRED_PLAN_DIR}/ dir\n"
    )
    (tmp_path / "README.md").write_text(f"a vault with {_RETIRED_PLAN_DIR}/\n")

    hits = _hits(tmp_path, _SCANNED, _RETIRED_PLAN_DIR)

    assert hits == [
        "orchestrator/state.py:1",
        "prompts/coder.md:1",
        "docs/modules/state.md:1",
        "README.md:1",
    ]
