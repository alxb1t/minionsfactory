# Migrate to AGENTS.md — tasks

Build the settled [design](design.md); use its [transition handoff](design.md#transition-execution) for this cut.

## Progress

- [x] 1 — Migrate target context and installation
- [x] 2 — Add portable execution beside native Claude engines
- [ ] 3 — Prove the generic path and audit native preservation

## 1 — Migrate target context and installation

- [x] 1.1 Rename root `CLAUDE.md` to `AGENTS.md` and `skills/mf-bootstrap/templates/CLAUDE.md.tmpl` to `AGENTS.md.tmpl`; make context reads explicit per [D1](design.md#d1).
  Verify: `test -f AGENTS.md && test -f skills/mf-bootstrap/templates/AGENTS.md.tmpl` exits 0; root context explicitly directs reading `docs/principles.md` and `docs/decisions.md`.
- [x] 1.2 Update `_CLAUDE_TEMPLATE` and the template/layout fixtures in `tests/test_skills.py` per [D1](design.md#d1), retaining the tests named in [Tests](design.md#tests).
  Verify: `rg -q '^_AGENTS_TEMPLATE =' tests/test_skills.py && uv run pytest -q tests/test_skills.py -k 'template or layout'` exits 0.
- [x] 1.3 Update context reads in `skills/mf-bootstrap/SKILL.md`, `skills/mf-cut-change/SKILL.md`, `skills/mf-build/SKILL.md`, `skills/mf-converge/SKILL.md`, `skills/mf-release/SKILL.md` and `openspec/config.yaml`; fix `0026·N2`.
  Verify: cut, build, converge and release explicitly require root `AGENTS.md`; bootstrap's collision table names it; cut Step 6 says "Each dependency names an exact package and a version constraint".
- [x] 1.4 Update `README.md`, `docs/README.md` and D8/D18 in `docs/decisions.md` for the renamed context per [D1](design.md#d1) and [D9](design.md#d9).
  Verify: the README and D18 target trees name `AGENTS.md`; the docs map links the new root file; historical records remain unchanged.
- [x] 1.5 Change the `SKILLS_DIR` default and its comment in `Makefile` per [D5](design.md#d5), retaining the existing installer safeguards.
  Verify: `Makefile` declares `SKILLS_DIR ?= $(HOME)/.agents/skills`; the override and install/uninstall recipes retain their existing behavior; the gate recipe equals `bba6569`.

## 2 — Add portable execution beside native Claude engines

- [x] 2.1 Add build's executor selection and new `skills/mf-build/references/generic-simplify.md`; link it from `skills/mf-build/SKILL.md` per [D2](design.md#d2) and [D3](design.md#d3).
  Verify: build explicitly loads that resource on generic execution, preserves native `/simplify` for Claude Code, and halts when its required native command is unavailable.
- [x] 2.2 Add converge's executor/worker branches and new `skills/mf-converge/references/generic-review.md` and `generic-security.md`; fix `0026·N1` per [D2](design.md#d2) through [D4](design.md#d4).
  Verify: converge loads the generic resources, retains native review/security, accepts fresh processes and generic sequential workers, and passes `design.md` to review during Step 7.
- [x] 2.3 Add `_resource_problems`, `test_bundled_role_references_resolve` and `test_resource_scan_reports_missing_empty_and_escaping_targets` in `tests/test_skills.py` per [D8](design.md#d8).
  Verify: `uv run pytest -q tests/test_skills.py::test_bundled_role_references_resolve tests/test_skills.py::test_resource_scan_reports_missing_empty_and_escaping_targets` exits 0.
- [x] 2.4 Update `skills/mf-cut-change/SKILL.md` model suggestions per [D6](design.md#d6), preserving the suggestion-only boundary.
  Verify: the cutter uses an offered menu, describes capability when a menu is absent, omits unsupported effort controls and leaves model/provider selection unchanged.
- [x] 2.5 Update `AGENTS.md`, `README.md`, `docs/README.md`, `docs/principles.md`, `docs/decisions.md`, `skills/mf-bootstrap/SKILL.md` and `skills/mf-release/SKILL.md` per [D3](design.md#d3) through [D6](design.md#d6); fix `0026·N3`.
  Verify: live docs describe native/generic behavior and capabilities; D11/D13/D22 hold the agreed choices; the bootstrap no-remote warning is native-specific; the named long lines are wrapped.

## 3 — Prove the generic path and audit native preservation

- [ ] 3.1 **HALT CHECK** Confirm the installed Codex CLI can start the new-session fixture exercise specified by [D7](design.md#d7); missing execution capability is a plan halt, not an installation task.
  Verify: `codex exec --help` exits 0 and documents `--cd`, `--sandbox`, `--approve-for-me`, `--ephemeral`, `--json` and stdin prompt input.
- [ ] 3.2 Create the disposable `.minions/0027-smoke/target/` fixture and run the [smoke protocol](design.md#smoke-protocol); append sanitized actual results to this change's `design.md` Smoke evidence.
  Verify: live Codex evidence shows label simplification, review's invoice finding, security's cross-user finding, failing regression tests, green fixes and new workers verifying both findings on disk.
- [ ] 3.3 Record the [native dispatch review](design.md#native-dispatch-review) and [retirement inventory](design.md#d9) in this change's `design.md`, preserving the historical exceptions.
  Verify: design evidence names the preserved native dispatch, its restrictions and the kept/fixed retirement hits; no unrun host is labeled live-tested.
