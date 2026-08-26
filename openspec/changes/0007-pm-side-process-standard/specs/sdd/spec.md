# Spec delta — `sdd`

## MODIFIED Requirements

### Requirement: Repository is the source of truth for change progress

The repository SHALL hold the active change, its progress (`changes/<id>/tasks.md`) **and the roles' working
artifacts** — findings, the HALT report and deferred work, all under `.minions/`. The **driver** SHALL determine
where the work stands with no hop outside the repository. No shipped code, role prompt or doc SHALL name the
retired plan location or its retired vocabulary, and none SHALL name the **retired vault vocabulary** — the
symbols by which the repository once reached a directory outside itself.

#### Scenario: Progress is read from the repo, not the vault
- **Key:** `sdd:vault-layout:progress-in-repo`
- **Layers:** unit
- **WHEN** the driver runs and determines where the work stands
- **THEN** it reads the phase state from the repo `changes/<id>/tasks.md` and consults no external plan file — the
  run drives to completion against a target that has no vault at all

#### Scenario: The retired plan model is named nowhere in code, prompts or docs
- **Key:** `sdd:vault-layout:no-plan-path-references`
- **Layers:** unit
- **WHEN** `orchestrator/`, `prompts/`, `docs/` and `README.md` are scanned
- **THEN** none of them names the retired plan directory or the retired plan vocabulary — the deleted symbols and the
  `current_phase` pointer the driver no longer reads
- **AND** the scan set excludes the specs themselves, which describe the retirement and must be able to name it, and
  the historical record (`CHANGELOG.md`, `openspec/changes/archive/`), which must keep saying what was true

#### Scenario: The retired vault vocabulary is named nowhere in shipped code, prompts, docs or skills
- **Key:** `sdd:vault-layout:no-retired-vault-vocabulary`
- **Layers:** unit
- **WHEN** the retired vault symbols are scanned for — the declared environment key, the resolved-directory
  parameter in both its spellings, the two deleted preflight functions, and the external release-record symbol
- **THEN** none of them appears, over this needle set's **own** root set: `orchestrator/`, `prompts/`, `docs/`,
  `README.md`, **`skills/`**, the root `CLAUDE.md` and the tracked environment example
- **AND** the root set is the needle set's own, not the retired-plan needle's: one root set crossed with both
  needle sets cannot pass, because a retired *plan* needle is live check text inside `skills/`
- **AND** no exclusion is declared for any directory inside the scanned roots — the deletions land before the scan
  does, so nothing needs suppressing
- **AND** the exclusions are the specs, the historical record, and `tests/`, where the guard's own needles are
  literals

## Pending scenario removals — authored by phase 14, not before

Two scenarios go from *Repository is the source of truth for change progress*. The requirement itself is MODIFIED
above, not removed, and the MODIFIED block already omits them — but omission only takes effect at the release
fold, so it does not carry the removal on its own.

**The live `## REMOVED Requirements` block is deliberately not written yet**, for the reason the `change-state`
delta states in full: a REMOVED key is discarded from the shipped and resolvable sets the moment the block exists,
so writing it now dangles two live test markers, and writing it after the tests go orphans two shipped scenarios.
**Phase 14 authors the live block, deletes the two bound tests, and hand-deletes the two shipped scenario blocks
in one commit.**
>
> **`sdd:vault-layout:vault-path-not-in-repo`** — *The operator's vault path is named nowhere in the repo tree.*
> The guard scanned the tracked tree for the path the target's `.env` declared. Once no `.env` declares one, the
> guard has no needle to resolve and cannot run; the property it protected is now structural rather than checked,
> since no code path resolves a directory outside the repository at all. Its test goes with it.
>
> **`sdd:vault-layout:findings-and-prd-in-vault`** — *Findings and product intent stay in the vault.* This is the
> arrangement the version reverses. Findings move into `.minions/`; product intent stays where the planning line
> writes it, which is no longer a claim this repository makes about itself.
