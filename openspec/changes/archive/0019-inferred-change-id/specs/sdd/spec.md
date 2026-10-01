## ADDED Requirements

### Requirement: A skill infers the one active change

`skills/mf-build/SKILL.md`, `skills/mf-converge/SKILL.md` and `skills/mf-release/SKILL.md` SHALL take `change-id`
from their parameter when one is given. When none is given, each SHALL take the candidates from
`git ls-files openspec/changes/`, without `archive/`: no candidate SHALL halt with `no active change`, several SHALL
halt listing them, and exactly one SHALL be used only if the current branch equals `v<version>_<slug>` built from
that change's `proposal.md` `version:` and its id, else halt naming both. The skill SHALL echo the id with
`(inferred:` before any other work, and SHALL NOT forbid inference.

#### Scenario: Build, converge and release each name the inference and its halts
- **Key:** `sdd:inferred-change-id:one-active-change`
- **Layers:** unit
- **WHEN** `skills/mf-build/SKILL.md`, `skills/mf-converge/SKILL.md` and `skills/mf-release/SKILL.md` are scanned
- **THEN** each names `git ls-files openspec/changes/`
- **AND** each names `no active change`
- **AND** each names `(inferred:`
- **AND** none names `Never infer it`
