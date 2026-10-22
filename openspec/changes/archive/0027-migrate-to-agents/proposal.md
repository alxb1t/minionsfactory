---
version: v0.27
backlog: [0026·N1, 0026·N2, 0026·N3]
---

# Migrate to AGENTS.md

Make the execution line usable by coding agents while preserving Claude Code's native engines.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements. The [transition handoff](design.md#transition-execution)
builds this change in Codex.

## Why

The skills require `CLAUDE.md` and Claude Code engines, so other executors cannot finish the line as written.
The operator is moving target repos to `AGENTS.md` and uses Codex through ACP and OpenRouter through Zed.

## What Changes

- **BREAKING — Target context:** require `AGENTS.md`; remove the live `CLAUDE.md` contract without fallback.
- **Bootstrap test policy:** replace the requirement named for the old template with its `AGENTS.md` equivalent.
- **Shared installation:** default the skill symlinks to `~/.agents/skills`; retain `SKILLS_DIR` overrides.
- **Engine selection:** Claude Code keeps `/simplify`, `/code-review` and `/security-review`; other executors
  load bundled generic instructions. A missing native command halts instead of silently switching engines.
- **Generic passes:** specify simplify, review and security without a review plugin or remote prerequisite.
- **Independent workers:** accept fresh host subagents and fresh processes; generic checkers may run sequentially.
- **Bundled resources:** require readable generic role references, guarded by a unit check and its mutation twin.
- **Model suggestions:** name offered models and supported effort controls; keep provider setup with the operator.
- **Compatibility evidence:** require the live Codex generic smoke and the native-path hand review before claiming
  them complete. Other hosts remain capability-based until tested.
- Close `0026·N1`, `0026·N2` and `0026·N3`: pass the design to verification, clarify dependency wording, wrap prose.

## Capabilities

### New Capabilities

None. The line remains the existing `sdd` capability.

### Modified Capabilities

- `sdd`: target context, template test policy, installation, engine selection, generic roles, worker isolation,
  resource integrity, model suggestions and compatibility evidence.

## Impact

Changes the root context, `Makefile` installation default, `skills/mf-*`, bootstrap templates,
`tests/test_skills.py`, `README.md`, `docs/README.md`, `docs/principles.md`, `docs/decisions.md` and
`openspec/config.yaml`. The [delta](specs/sdd/spec.md) is folded by release, not by the build.

Dependencies: none. Model calls stay outside CI; the gate recipe stays unchanged.

## Not in this change

No target-repo migration, compatibility shim, model runner, provider configuration, host installation,
autonomous-line implementation, gate-hardening paydown, universal model-quality claim or hosted review service.
`CHANGELOG.md` history and `openspec/changes/archive/` retain truthful historical references.
