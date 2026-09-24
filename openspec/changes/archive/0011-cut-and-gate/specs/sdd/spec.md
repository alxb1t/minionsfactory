## ADDED Requirements

### Requirement: The skills run the repository's `make gate`

The `mf-build`, `mf-converge` and `mf-release` skills SHALL run the gate as `make gate`, from the repository
root. Each SHALL print the output of `make -n gate` before its first gate run in a session. Each SHALL halt,
naming the root `Makefile`, when that file is missing, has no `gate` target, or has a `gate` target that runs
no command. No shipped skill SHALL name `.minions/minions.toml`.

#### Scenario: Every gate-running skill names make gate, and no skill names the toml
- **Key:** `sdd:skills-gate:skills-run-make-gate`
- **Layers:** unit
- **WHEN** every `skills/*/SKILL.md` is scanned
- **THEN** no file names `minions.toml`
- **AND** `mf-build`, `mf-converge` and `mf-release` each name both `make gate` and `make -n gate`

### Requirement: The cut and the build share one input contract

`skills/mf-build/SKILL.md` SHALL own the input contract: a `## Input contract` section whose table rows are
the items a change must meet, one per row, the first cell holding the item's id in bold (`**I1**`).
`skills/mf-cut-change/SKILL.md` SHALL carry a `## Input contract` section with a row for the same ids. The two
id sets SHALL be equal, non-empty, and numbered from `I1` with no gap.

#### Scenario: The two skills carry the same contract ids
- **Key:** `sdd:input-contract:ids-agree`
- **Layers:** unit
- **WHEN** the ids are read from the first cell of each table row in the `## Input contract` section of both
  skills
- **THEN** the two sets are equal and non-empty
- **AND** they run from `I1` upward with no number missing
