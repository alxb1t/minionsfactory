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

## REMOVED Requirements

> **No requirement is removed by this change — exactly two scenario keys are.** A REMOVED block must sit under a
> `### Requirement:` heading for the parser to reach its scenarios, so the heading below is a deliberate
> **placeholder that matches no live requirement**: *Repository is the source of truth for change progress* stays,
> restated by the MODIFIED block above, and a REMOVED block whose title matches nothing degrades to a no-op in
> `release._apply_fold`. The two retired scenarios are hand-deleted from `openspec/specs/sdd/spec.md` in phase 14's
> commit, so the fold has nothing left to do here. **Do not read this block as licence to delete *Repository is the
> source of truth for change progress*.**

**Authored by phase 14, not before, and not later.** `collect_spec_keys` discards a REMOVED key from *both* the
resolvable and the shipped sets the moment this block exists, so authoring it earlier would have dangled the live
test markers and held the gate red until phase 14; authoring it later, after the tests went, would have orphaned
two shipped scenarios. The window is one commit wide — *earlier the live markers dangle, later the shipped
scenarios orphan* — so the phase-14 commit deletes the two bound tests (and the `_VAULT_SCANNED` root set and
`_declared_vault_dir` helper they alone used), writes this block, and hand-deletes the two shipped scenario blocks,
all at once. The MODIFIED block above already omits them, but omission only takes effect at the release fold, so it
does not carry the removal on its own.

### Requirement: Retired scenario keys (placeholder — no live requirement is removed)

Carrier for two retired scenario keys. This heading intentionally matches no requirement in
`openspec/specs/sdd/spec.md`.

#### Scenario: The operator's vault path is named nowhere in the repo tree
- **Key:** `sdd:vault-layout:vault-path-not-in-repo`
- **Layers:** unit
- **WHEN** the tracked repo tree is scanned for the vault path the target's `.env` declares
- **THEN** none of them names it

The guard scanned the tracked tree for the path the target's `.env` declared. Once no `.env` declares one, the
guard has no needle to resolve and cannot run; the property it protected is now structural rather than checked,
since no code path resolves a directory outside the repository at all. Its two tests go with it.

#### Scenario: Findings and product intent stay in the vault
- **Key:** `sdd:vault-layout:findings-and-prd-in-vault`
- **Layers:** e2e
- **WHEN** a read-only role or the PM authors findings or a PRD
- **THEN** they are written under the vault (`prd/`, `findings/`)

This is the arrangement the version reverses. Findings move into `.minions/`; product intent stays where the
planning line writes it, which is no longer a claim this repository makes about itself.
