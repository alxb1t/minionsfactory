## ADDED Requirements

### Requirement: The retired gate config is named nowhere

No shipped code, role prompt, skill or doc SHALL name `minions.toml`. The scan SHALL cover the same root set as
the retired-vocabulary scans — `orchestrator/`, `prompts/`, `skills/`, `docs/`, `README.md`, the root
`CLAUDE.md`, the tracked environment example, `.github/`, `Makefile` and `pyproject.toml` — and exclude the
specs, `tests/`, and the historical record (`CHANGELOG.md`, `openspec/changes/archive/`).

#### Scenario: The retired gate config is named nowhere in code, prompts, skills or docs
- **Key:** `sdd:retired-gate-config:named-nowhere`
- **Layers:** unit
- **WHEN** the shared root set is scanned for `minions.toml`
- **THEN** no file names it
- **AND** a mention planted in each root is reported
