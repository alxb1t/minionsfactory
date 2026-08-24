---
version: v0.5
---

# Proposal — 0005-change-cutover

**Change:** `0005-change-cutover` · **Version:** v0.5 · **PRD:** vault `prd/v0.5_change_cutover.md` (R1–R10)
**Build mode:** hand-authored (Claude Code + prompts; **no orchestrator automation** — the broken state reader *is*
the deliverable, so the loop cannot drive its own repair). Self-hosting resumes at v0.8.

> This proposal's `version:` frontmatter is the convention R4 introduces — this change dogfoods it.

## Why

v0.3 adopted spec-driven development and moved change progress into the repo. It **built** the in-tree change
reader (`read_change_state` · `select_change` · `validate_change` · `change_advanced`), spec'd it and unit-tested
it — and **never wired it in**. The reader is called from `tests/` and nowhere else; `driver.run` still defaults to
`read_plan_state` and `__main__` passes no override. The deferral is recorded in the code (`orchestrator/state.py:160`)
and in the spec, which calls the in-tree reader "the v0.5 sibling".

Meanwhile the vault restructured: `implementation_plans/` no longer exists. So the framework **is broken against its
own vault** — not at risk of breaking, broken now:

```
select_plan(<MinionsFactory vault>) → ValueError: max() iterable argument is empty
```

The preflight catches `PlanContractError` / `PreflightError`, not `ValueError`, so a run dies on an uncaught traceback
instead of the diagnostic the preflight exists to produce. Five surfaces still assume the retired model, and **two
shipped specs assert contradictory behavior** — `sdd:vault-layout:progress-in-repo` says the reader consults no vault
plan file, while `change-state` says `select_plan` SHALL read `implementation_plans/`. The one actually wired is the
retired one.

Nothing runs until this is fixed. No feature can be built through the loop — v0.8 remediation included.

## What (scope)

1. **The driver reads the in-tree change (R1).** `driver.run` determines where the work stands via
   `read_change_state` (repo only), detects advance via `change_advanced`, and detects completion via
   `ChangeState.is_complete`. This wires `sdd:vault-layout:progress-in-repo`, spec'd today but bound to no running code.
2. **The phase verdict is computed over `ChangeState` (R2).** `decide` takes before/after `ChangeState` plus the gate
   result and the halt flag; a moved checkbox is trusted only when a real commit proves it.
3. **The vault-plan path is deleted, not kept alongside (R3).** `select_plan`, `read_plan_state`, `validate_plan` and
   `PlanState` go, with their tests and their spec requirements. `PlanContractError` stays — the change reader raises it.
4. **The release version is declared in the change (R4).** `openspec/changes/<id>/proposal.md` frontmatter carries
   `version: vX.Y`; the orchestrator reads it and supplies it to the release gate, whose predicates are unchanged. An
   absent or malformed `version` is refused at preflight, before spend.
5. **Findings live at `<vault>/findings/<change-id>_<role>.md` (R5).** The findings home moves out of
   `implementation_plans/` and is keyed to the change id — the same identifier as the change directory and the
   `Change:` commit trailer. One resolution site in code; fan-out, converge and release all use it.
6. **The orchestrator supplies coder, fixer and release their inputs (R6).** Each receives the orchestrator-built
   Inputs block — change directory, findings paths, head, version — as the three read-only fan-out roles already do.
   The prompts stop deriving paths by shell and carry role mandate only.
7. **Preflight refuses a malformed target before spend (R7).** No active change, a change missing an artifact, a
   `tasks.md` with no `## Progress` checklist, or a `proposal.md` with no `version` — each with its own diagnostic and
   a non-zero exit, no role spawned, no `ValueError`-class traceback reachable.
8. **The two specs are reconciled (R8).** The delta retires the `change-state` plan requirements and leaves the
   in-tree reader as the described behavior; `specs check --strict` is green with no two requirements contradicting.
9. **Docs match the shipped model (R9).** `README.md`, `docs/README.md` and the affected `docs/modules/*.md` describe
   the in-tree change reader, the `findings/` location and the declared-version source.
10. **Tracked as change `0005-change-cutover` (R10)** — four artifacts, `version: v0.5` in this proposal, and a
    `Change: 0005-change-cutover` trailer on every commit.

## Approach

Wiring, deletion and prose — **every mechanism R1–R7 needs already exists and is unit-tested**. Nothing is invented;
the three seams the cutover needs are already the shipped design (the state reader is injected into `run()`, the gate
command list is read from the target, role inputs are orchestrator-supplied for the read-only roles).

Seven phases, ordered so the driver only switches once its inputs exist and the deletion only happens once nothing
reads the old path: version source → findings home → driver cutover → delete the plan path → role inputs → specs and
docs → bookkeeping. The riskiest commit (phase 4's deletion) is isolated behind an already-green driver switch.

Net complexity goes **down**: the change removes ~90 LOC of module and ~180 LOC of tests, and adds one field, one
helper and one guard. See `design.md` for the decisions, the build-order rule the delta depends on, and the two
hand-edits the automated fold cannot reach.

## Out of scope

- **Migrating isekai or any other target to `openspec/changes/`.** Deleting the plan reader means an un-migrated
  target cannot run until it moves. Five targets are affected (isekai, KitchenScheduler, Palimpsest, Apilogue,
  Tomten) → backlog, routed to v0.6 `mf-teardown`.
- **Rewriting `Lab/CLAUDE.md`'s autonomous-build variant** and propagating it → backlog.
- **The standalone remediation loop** → v0.8 (depends on this).
- **Wiring the release stage's SDD predicates** (`specs_valid` / `change_folded` / `commits` / `known_change_ids` and
  `change_id` into `prepare_release`) → backlog: new behavior the PRD's "no new capability" excludes. The **fold step
  itself** is in scope as prose in `prompts/release.md` (phase 5) — see `design.md` §7b.
- **Any new capability** — no new subcommands, no new roles, no behavior the framework did not already claim.
- **Relocating `.minions/minions.toml`** — already correct in `gate.py`; the backlog item saying otherwise is stale
  and gets closed, not acted on.

## Success criteria

`python -m orchestrator run --repo <target>` drives a target off `openspec/changes/<id>/tasks.md` with no vault-plan
hop; findings land in `<vault>/findings/<change-id>_<role>.md`; the release version comes from the change that declares
it; **no code, prompt or doc under `orchestrator/`, `prompts/`, `docs/` or `README.md` names `implementation_plans/`**
(a test guards this; the specs describing the retirement, and the historical record, are outside its scan set — see
`design.md` §5); the full gate is green with the plan-reader tests **gone, not skipped**; `specs check --strict` is
green with no two requirements asserting contradictory behavior; every commit carries a `Change: 0005-change-cutover`
trailer; and the delta folds cleanly on release (proved by a `fold_change(..., dry_run=True)` assertion in phase 6,
not deferred to release day).
