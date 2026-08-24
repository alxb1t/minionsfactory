# Spec delta — 0005-change-cutover

Four capability deltas, plus one block deliberately deferred to build time.

| File | Section | What changes |
|---|---|---|
| `sdd/spec.md` | MODIFIED ×2 | **Change structure** gains the declared `version:` and per-condition refusals (R4, R7); **Repository is the source of truth** is restated at the driver level, names `findings/`, and adds the retired-path regression guard (R1, R3, R5, R9) |
| `build-loop/spec.md` | MODIFIED ×2 | `decide` and `run` restated over `ChangeState`, advance delegated to `change_advanced` (R1, R2) |
| `fanout/spec.md` | ADDED ×2 | **Findings location and key** — `<vault>/findings/<change-id>_<role>.md`, one resolution site, dir created before spawn (R5); **Orchestrator-owned role inputs** — coder / fixer / release get their paths from the orchestrator (R6) |
| `cli/spec.md` | MODIFIED ×1 | The zero-token preflight reads the change, not the plan, and names the specific problem (R7) |

## The deferred `change-state` REMOVED block

R3 retires `select_plan`, `read_plan_state`, `validate_plan` and `PlanState`, and with them three `change-state`
requirements — **Plan selection**, **Plan-state assembly**, **Plan contract guard**. That `## REMOVED Requirements`
block is **not authored here**. It is written in **phase 4**, in the same commit as the code and test deletions.

`specs.collect_spec_keys` (`orchestrator/specs.py:133-140`) discards a REMOVED key from **both** `resolvable` and
`shipped` the moment the delta declares it, before any fold. So:

- author it now → the nine still-present plan-test markers go **dangling** → red gate from phase 1;
- author it after the deletion → the nine shipped scenarios go **orphaned** → red gate at phase 4.

There is exactly one green ordering, and it is a single commit. See `../design.md` §6 and `../tasks.md` phase 4.

That same commit carries the rest of the deletion: the plan-reader tests in `tests/test_state.py:24-135` (the range
stops there — the four `change-state:vault-preflight:*` tests from line 145 belong to the requirement this change
keeps), the duplicated plan-contract tests in `tests/test_gate.py:73-105` (five markers the REMOVED block would
otherwise leave dangling), the `select_plan` sections of `docs/modules/state.md`, and a **hand-deletion of the three
plan requirement blocks from `openspec/specs/change-state/spec.md`**. The hand-deletion is what ends the R8 contradiction at build time rather
than at release; it does not conflict with the REMOVED block, because `_apply_fold` skips a REMOVED title it cannot
match, so the fold's REMOVED pass becomes a no-op.

The **Vault-write preflight** requirement stays — it is what the `change-state` capability holds after this change.
Its capability preamble still describes the vault-plan reader; the fold preserves preamble prose verbatim
(`release._apply_fold`), so that edit is by hand in phase 6.

## Conventions

Format is OpenSpec verbatim; each scenario carries a stable `Key:` and declares its `Layers:` (`unit` enforced;
`e2e` reserved for the v0.7 tester — recorded, not enforced). Every MODIFIED requirement reproduces **all** of its
scenarios, surviving ones verbatim, because the fold replaces the whole requirement block matched by **title** — and
no requirement is retitled.
