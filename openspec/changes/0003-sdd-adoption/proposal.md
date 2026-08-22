# Proposal — 0003-sdd-adoption

**Change:** `0003-sdd-adoption` · **Version:** v0.3 · **PRD:** vault `prd/v0.3_sdd_adoption.md` (R1–R7)
**Research / design-lock:** vault `research/v0.3_research.md` (D1–D11) · **Build mode:** by hand (Claude Code +
prompts; no orchestrator automation — D9). **This is the first change authored in the new structure** — it builds
the very `specs/` + `changes/` machinery it is expressed in.

## Why

The single implementation-plan file does five jobs at once (proposal · design · tasks · acceptance · progress),
which is the "hacky" feeling; there is no **living** behavioral spec (what the system does *now* is only
reconstructable from code + N archived plans, and per-plan acceptance evaporates on archive); and there is no
standardized, **enforced** change structure. SDD (OpenSpec-style `specs/` + `changes/`) decomposes those five
jobs into named single-job artifacts. OpenSpec is **advisory** — nothing checks that code matches the spec. The
value we add, and the only version we can ship, is **enforcement**: bind every scenario to a proving test and
check that binding at **gate → reviewer → release**.

## What (scope)

Adopt SDD in this repo and make the binding enforced, at three points, with a full backfill:

1. **Enforced binding (R1).** A new `orchestrator/specs.py` + a `specs check` subcommand of the orchestrator CLI
   (run-from-source: `uv run python -m orchestrator specs check` — the shape of the existing `run`; there is **no
   installed `minions` binary** — `minions specs check` is only the future alias). It parses `specs/**` ∪ the
   active change delta into scenario **keys**, statically collects `@pytest.mark.spec(...)` / `spec_exempt(...)`
   markers from the test tree, and fails on an **orphan** scenario (a shipped scenario with no proving test) or a
   **dangling** marker (a key that resolves to no scenario). Wired into MF's own `.minions/minions.toml` gate (+
   Makefile + CI) — **self-validating**, and a no-op until specs exist. Layer-aware (D11): scenarios declare
   applicable layers; **v0.3 enforces `unit` only**, reserving the `e2e` seam for the v0.7 tester.
2. **Change structure in the repo (R4, R5).** The active change is read **in-tree** from `changes/<id>/`
   (`proposal.md` · `design.md` · `tasks.md` · `specs/` delta — proposal + design **always present**); progress
   is `tasks.md`, not a vault plan. A contract-guard asserts the shape; the change-state reader replaces the
   vault `implementation_plans/` hop. (`CLAUDE.md` already documents this model — the code lands to match it.)
3. **Prove the mechanism on `converge` + `release` (R1).** Spec those two shipped capabilities **directly** into
   top-level `specs/`, bind their existing tests, and demonstrate live that a **seeded orphan** and a **seeded
   dangling marker** each fail `specs check`. Validate the mechanism before scaling it.
4. **Reviewer conformance axis (R2).** `prompts/reviewer.md` gains a spec-conformance axis (delta genuinely
   implemented · genuinely test-backed · coherent vs the diff), re-anchoring the existing "acceptance met" axis
   onto scenarios.
5. **Release fold (R3, R7).** `orchestrator/release.py` folds the change delta into `specs/` (MODIFIED overwrites
   the whole requirement; dry-run + verify-after-fold; idempotent), adds a release-gate predicate (`specs/`
   validates + change folded) and a **`Change:`-trailer** predicate (every `base..HEAD` commit carries a trailer
   resolving to this change — else HALT), writes the trailer on the release commit, and moves the change to
   `changes/archive/<id>/`.
6. **Conventions (R7).** Document the `Change: <id>` commit-trailer + the `specs/` / `changes/` conventions in the
   vault `conventions.md` (framework-wide; folds into the template at ≥ v0.7).
7. **Full backfill (R6).** Every remaining capability gets a `specs/<cap>/spec.md`; **every test** traces to a
   scenario via `@pytest.mark.spec(...)` or an explicit `@pytest.mark.spec_exempt("reason")`. Enforced by
   `specs check --strict` (bidirectional traceability). **Sequenced last** — repetitive application of a
   proven mechanism.

## Approach

- **Format = OpenSpec verbatim; enforcement = our own stdlib checker (D2).** Borrow OpenSpec's `### Requirement:`
  / `#### Scenario:` / WHEN·THEN format and its `## ADDED / MODIFIED / REMOVED Requirements` delta markers; do
  **not** take its Node CLI. The checker is stdlib Python (`ast` for marker collection, a line parser for the
  spec markdown) — **no new runtime dependency** (a hard constraint).
- **Binding = a stable scenario key + a scenario-level pytest marker (D3).** `@pytest.mark.spec("sdd:enforced-
  binding:orphan-scenario-fails")`. Keys resolve against `specs/` ∪ the active delta, so **pending** scenarios
  resolve during the build (their orphan-enforcement waits for the release fold).
- **Delta vs backfill.** The **new SDD capability** (R1–R7) is a delta in `changes/0003-sdd-adoption/specs/sdd/`,
  folded into `specs/` at release. **Already-shipped** behavior (`converge` + `release` in phase 3, and every
  remaining capability in phase 7) is spec'd **directly** into top-level `specs/` — it is not a delta, it ships
  now.
- **Test-first, green gate per phase; a `Change: 0003-sdd-adoption` trailer on every commit** (R7). Findings stay
  in the vault (D8) — this change writes no findings file and touches no vault schema (PRD constraint).

## Out of scope (deferred)

Authoring **automation** (`/drill-me`, `/plan-check`, `/research`) → v0.4. **e2e/acceptance testing + the
`tester` role** → v0.7 (v0.3 only makes the binding layer-aware). The sandbox → v0.10. Other projects' backfill,
a JS gate, and **format-migrating** historical plans (they are relocated to the vault `archive/` as record, not
converted). **No edit to the vault-wide `CLAUDE.md` schema** — pilot on MF, generalize later.

## Success criteria

`uv run python -m orchestrator specs check` is green and in the gate (MF + CI); `converge` and `release` are
spec'd in `specs/` with their tests bound and seeded orphan/dangling failing; `release.py` folds a delta
idempotently and halts on an untrailed commit; every test carries a `spec`/`spec_exempt` marker under
`specs check --strict`; the full gate is green; and this change archives cleanly into `changes/archive/`.
