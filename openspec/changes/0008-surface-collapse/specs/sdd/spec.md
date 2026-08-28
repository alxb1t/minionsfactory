# Spec delta — `sdd`

## MODIFIED Requirements

### Requirement: Repository is the source of truth for change progress

The repository SHALL hold the active change, its progress (`changes/<id>/tasks.md`) **and the roles' working
artifacts** — findings, the HALT report and deferred work, all under `.minions/`. The **driver** SHALL determine
where the work stands with no hop outside the repository. No shipped code, role prompt or doc SHALL name the
retired plan location or its retired vocabulary, and none SHALL name the **retired vault vocabulary** — the
symbols by which the repository once reached a directory outside itself. Both retirements SHALL be scanned over
**one root set**, asserted verbatim so that narrowing it is a visible edit.

#### Scenario: Progress is read from the repo, not the vault
- **Key:** `sdd:vault-layout:progress-in-repo`
- **Layers:** unit
- **WHEN** the driver runs and determines where the work stands
- **THEN** it reads the phase state from the repo `changes/<id>/tasks.md` and consults no external plan file — the
  run drives to completion against a target that has no vault at all

#### Scenario: The retired plan model is named nowhere in code, prompts or docs
- **Key:** `sdd:vault-layout:no-plan-path-references`
- **Layers:** unit
- **WHEN** the shared root set is scanned — `orchestrator/`, `prompts/`, `docs/`, `README.md`, the root
  `CLAUDE.md`, the tracked environment example, `.github/`, `Makefile` and `pyproject.toml`
- **THEN** none of them names the retired plan directory or the retired plan vocabulary — the deleted symbols and the
  `current_phase` pointer the driver no longer reads
- **AND** the scan set excludes the specs themselves, which describe the retirement and must be able to name it, and
  the historical record (`CHANGELOG.md`, `openspec/changes/archive/`), which must keep saying what was true

#### Scenario: The retired vault vocabulary is named nowhere in shipped code, prompts or docs
- **Key:** `sdd:vault-layout:no-retired-vault-vocabulary`
- **Layers:** unit
- **WHEN** the retired vault symbols are scanned for — the declared environment key, the resolved-directory
  parameter in both its spellings, the two deleted preflight functions, and the external release-record symbol
- **THEN** none of them appears, over the **same** root set as the retired-plan needles: `orchestrator/`,
  `prompts/`, `docs/`, `README.md`, the root `CLAUDE.md`, the tracked environment example, `.github/`, `Makefile`
  and `pyproject.toml`
- **AND** the two needle sets share one root set: the split existed only because a retired *plan* needle was live
  check text inside the planning-skill surface, and that surface is deleted
- **AND** no exclusion is declared for any directory inside the scanned roots — the deletions land before the scan
  does, so nothing needs suppressing
- **AND** the exclusions are the specs, the historical record, and `tests/`, where the guard's own needles are
  literals
