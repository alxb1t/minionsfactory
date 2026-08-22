# Tasks — 0003-sdd-adoption

Ordered phases for v0.3. **Build mode: by hand** (Claude Code + prompts; no orchestrator automation — D9).
Read `proposal.md` + `design.md` (this dir) and the vault PRD/research first.

**Per-phase ritual (every phase).**
- **Test-first** (red → green) for every unit of logic; the full gate green before the phase is done:
  `uv run ruff format --check .` · `uv run ruff check .` · `uv run ty check` · `uv run pytest -q` ·
  `uv run python -m orchestrator specs check`.
- **Commit** the phase in the code repo with a `Change: 0003-sdd-adoption` git trailer (R7). The vault edits
  (`log.md`, `backlog.md`) are separate from the code commit.
- Append the phase's changes under `## [Unreleased]` in `CHANGELOG.md`.
- **Delta scenarios are pending** (orphan-exempt) until the phase-5 fold; that is by design (see `design.md` §8).

**Requirement keys** referenced below live in `specs/sdd/spec.md` (this change's delta).

## Progress

- [x] 1 — Spec format + `specs.py` + `specs check` subcommand + wire MF gate
- [ ] 2 — Change-structure code (in-tree change resolution + contract-guard)
- [ ] 3 — Prove the mechanism on `converge` + `release` (spec directly; bind tests; seed orphan/dangling)
- [ ] 4 — Reviewer conformance axis (`prompts/reviewer.md`)
- [ ] 5 — Release fold + gate predicate + `Change:`-trailer predicate + `changes/archive/`
- [ ] 6 — `conventions.md`: the `Change: <id>` trailer + `specs/` / `changes/` conventions
- [ ] 7 — Full backfill: every capability spec'd; every test → a scenario or `spec_exempt`

---

## Phase 1 — Spec format + `specs.py` + `specs check` subcommand + wire MF gate

Build the checker mechanism (R1) and wire it into MF's own gate as a **no-op until specs exist**.

**Scope.** New `orchestrator/specs.py`: parse `specs/**/spec.md` ∪ active `changes/*/specs/**/spec.md` (exclude
`changes/archive/`) into scenario keys (`Key:` + `Layers:` bullets), statically collect `@pytest.mark.spec(...)`
/ `spec_exempt(...)` via `ast`, and check orphan / dangling (+ `--strict` traceability, off by default). Nested
`specs check` subcommand in `orchestrator/__main__.py` (`--repo` default cwd, optional `--strict`). Register
`spec` + `spec_exempt` markers in `pyproject.toml`. Create `.minions/minions.toml` and add the checker to the
Makefile `gate` target + `.github/workflows/ci.yml`.

**Machine-checkable acceptance.**
- `uv run python -m orchestrator specs check` exits **0** on the current tree (no top-level `specs/` yet → no-op).
- `uv run python -m orchestrator specs check --help` shows the subcommand (CLI wired).
- `orchestrator/specs.py` exists; unit tests (against fixtures under a tmp dir) prove: parse a spec file → keys;
  collect markers from a sample test module via `ast`; an orphan fixture → non-zero; a dangling fixture →
  non-zero; a pending-delta key resolves; a clean fixture → zero; `--strict` on an unmarked test → non-zero.
- `.minions/minions.toml` exists with a `gate` array whose final entry is
  `uv run python -m orchestrator specs check`; the Makefile `gate` target and `ci.yml` include the same step.
- `pyproject.toml` `[tool.pytest.ini_options].markers` registers `spec` and `spec_exempt` (no unknown-marker
  warning in `pytest -q`).
- Full gate green.

**Proves (delta, pending):** `sdd:enforced-binding:*` (orphan / dangling / pending-delta / clean / empty-noop),
`sdd:full-backfill:untraceable-test-fails`. Phase-1 tests may bind to these delta keys (they resolve via the
delta) or, being mechanism tests, carry `spec_exempt`.

---

## Phase 2 — Change-structure code (in-tree change resolution + contract-guard)

Make the framework resolve the active change from the repo `changes/<id>/` in-tree (R4, R5). `CLAUDE.md` already
documents this model — the code lands to match it; keep them consistent.

**Scope.** In `orchestrator/state.py` (sibling to the existing vault-plan reader, which stays until v0.5
self-hosting): `read_change_state(repo)` resolves the active change dir under `changes/` (highest version-id,
excluding `archive/`), parses `tasks.md`'s `## Progress` checklist into ordered phases, and sets the current
phase to the first `- [ ]`. `validate_change(...)` (reusing `PlanContractError` semantics) refuses a change
missing any of `proposal.md` / `design.md` / `tasks.md` / `specs/`. The `driver.decide` advance signal is
re-expressed as "new commit AND current-phase index moved" over this state (driver stays deterministic).

**Machine-checkable acceptance.**
- Unit tests (tmp `changes/<id>/` dirs): a well-formed change → ordered phases with current = first unchecked;
  a checked-through change → current = complete; each missing artifact (4 cases) → `PlanContractError` with a
  diagnostic naming the missing artifact; `archive/` is excluded from active resolution.
- A test proves `read_change_state` consults **no** vault path (locus: `sdd:vault-layout:progress-in-repo`).
- This change's own `changes/0003-sdd-adoption/tasks.md` parses under `read_change_state` (dogfood).
- Full gate green.

**Proves (delta, pending):** `sdd:change-structure:wellformed-resolves`,
`sdd:change-structure:missing-artifact-refused`, `sdd:vault-layout:progress-in-repo`.

---

## Phase 3 — Prove the mechanism on `converge` + `release`

Validate the checker on two shipped capabilities **before** scaling (R1). Spec them **directly** into top-level
`specs/` (shipped behavior — not a delta), bind their existing tests, and demonstrate seeded failures.

**Scope.** Author `specs/converge/spec.md` and `specs/release/spec.md` (requirements + keyed `unit` scenarios for
the behavior already in `converge.py` / `release.py`). Add `@pytest.mark.spec("<key>")` to the existing
`tests/test_converge.py` + `tests/test_release.py` tests that prove each scenario.

**Machine-checkable acceptance.**
- After binding, `uv run python -m orchestrator specs check` exits **0** (every `converge`/`release` `unit`
  scenario has ≥1 proving test; no dangling markers).
- **Seeded orphan** — a test asserts that adding a scenario with no proving test to a fixture `specs/` makes the
  checker exit non-zero and name it (`sdd:enforced-binding:orphan-scenario-fails`, proven live).
- **Seeded dangling** — a test asserts that a `spec("<bad-key>")` marker on a fixture test makes the checker exit
  non-zero and name it (`sdd:enforced-binding:dangling-marker-fails`, proven live).
- Every scenario in `specs/converge/` and `specs/release/` resolves to ≥1 real test (no orphan in the real tree).
- Full gate green (checker now enforcing on `converge` + `release`).

**Proves (directly, shipped):** the `converge` + `release` capability scenarios. **Proves (delta, pending):**
`sdd:enforced-binding:orphan-scenario-fails`, `sdd:enforced-binding:dangling-marker-fails`,
`sdd:enforced-binding:clean-passes`.

---

## Phase 4 — Reviewer conformance axis (`prompts/reviewer.md`)

Add the spec-conformance judgment axis (R2), re-anchoring "acceptance met" onto scenarios.

**Scope.** Edit `prompts/reviewer.md`: the reviewer flags a delta **not genuinely implemented**, **not genuinely
test-backed** (a test that exists but does not exercise the scenario — the checker proves existence; the reviewer
proves it bites), or **incoherent vs the diff**. Prompt-only; no code.

**Machine-checkable acceptance.**
- `prompts/reviewer.md` contains a spec-conformance section naming the three failure modes (grep-checkable:
  "genuinely implemented", "genuinely test-backed", "coherent"/"incoherent vs the diff").
- The prompt references scenarios/`specs check` (not the retired implementation-plan "acceptance" prose only).
- Full gate green (no code change).

**Proves (delta):** `sdd:reviewer-conformance:nominal-only-test-blocks` — `Layers: e2e` (reserved; structural
acceptance here, behavioral proof at v0.7).

---

## Phase 5 — Release fold + gate predicate + `Change:`-trailer predicate + `changes/archive/`

The fold that makes the delta living (R3) and the commit-traceability gate (R7).

**Scope.** In `orchestrator/release.py`: `fold_change(repo, change_id, dry_run=False)` — ADDED adds, MODIFIED
overwrites the **whole** requirement, REMOVED deletes; `dry_run=True` reports planned edits without writing;
**verify-after-fold** runs the spec validator and HALTs (without moving) if `specs/` is invalid; **idempotent**
re-run. Add `_specs_blocker` (specs valid + folded) and `_trailer_blocker` (every `base..HEAD` commit carries a
`Change: <id>` trailer resolving to the change) to the `verify_release_gate` blocker scan — the commit list is
gathered by the effectful caller, keeping the verdict function pure. Write the `Change:` trailer on the release
commit. On a green fold + gate, move `changes/<id>/` → `changes/archive/<id>/`.

**Machine-checkable acceptance.**
- Unit tests (tmp `specs/` + `changes/<id>/` dirs, `FakeGate`/fake commit lists): fold applies an ADDED
  requirement and moves the change to `archive/`; MODIFIED replaces the whole prior requirement (not appended);
  invalid-after-fold → HALT and the change is **not** moved; dry-run leaves disk unchanged; re-run is idempotent
  (no duplicate requirement).
- `_trailer_blocker`: a `base..HEAD` list with one untrailed commit → `ReleaseVerdict.ok is False` naming the
  commit; all-trailed and resolving → passes.
- Full gate green.

**Proves (delta, pending):** `sdd:release-fold:*` (fold-applied / modified-overwrites-whole /
invalid-specs-halts / dry-run-writes-nothing / idempotent-rerun), `sdd:commit-traceability:missing-trailer-halts`,
`sdd:commit-traceability:trailer-resolves`.

---

## Phase 6 — `conventions.md`: the `Change: <id>` trailer + `specs/` / `changes/` conventions

Document the framework-wide conventions in the vault (R7; D10).

**Scope.** In the vault `conventions.md` (inside `$VAULT_PROJECT_DIR`): the `Change: <id>` commit-trailer
convention (git-native, greppable via `git log --grep "Change: <id>"`, written per-commit by the coder and on the
release commit, verified by the release gate); the `specs/` (living) vs `changes/<id>/` (active, four artifacts)
layout; the delta markers + fold-on-release; the scenario `Key:`/`Layers:` shape and the `spec`/`spec_exempt`
markers. **Vault-only** — no repo code, no edit to the vault-wide `CLAUDE.md` schema.

**Machine-checkable acceptance.**
- `$VAULT_PROJECT_DIR/conventions.md` contains sections for the `Change:` trailer and the `specs/`+`changes/`
  conventions (grep-checkable within the vault).
- No repo diff other than, if needed, a pointer from the repo `CLAUDE.md` (already consistent).
- Full gate green.

**Proves:** documentation for R7 / D10 (no test binding — a convention doc, not code).

---

## Phase 7 — Full backfill: every capability spec'd; every test → a scenario or `spec_exempt`

Apply the proven mechanism across the whole suite (R6). **Sequenced last.**

**Scope.** Author `specs/<cap>/spec.md` for every remaining capability (`build-loop`, `change-state`, `gate`,
`provider`, `fanout`, `diff`, `status`, `cli` — plus `converge`/`release` from phase 3). Bind **every** test in
the test tree with `@pytest.mark.spec("<key>")`, or mark genuinely structural tests
`@pytest.mark.spec_exempt("reason")`. Switch the gate's checker step to **`--strict`** (`.minions/minions.toml`,
Makefile, `ci.yml`).

**Machine-checkable acceptance.**
- `uv run python -m orchestrator specs check --strict` exits **0**: every collected test carries a `spec` or
  `spec_exempt` marker (direction 2), and every shipped `unit` scenario has a proving test (direction 1).
- `specs/` has a `spec.md` for every capability in the taxonomy (`design.md` §9); no capability module is
  unspec'd.
- No `spec` marker is dangling; no shipped `unit` scenario is orphaned.
- The gate command list (`.minions/minions.toml` last entry, Makefile, `ci.yml`) uses `specs check --strict`.
- Full gate green.

**Proves (delta, pending):** `sdd:full-backfill:untraceable-test-fails`, `sdd:full-backfill:exempt-test-passes`;
plus **every** shipped capability scenario across `specs/`.

---

## Release (end of build, after all phases)

Not a numbered phase — the release role runs it. Fold `changes/0003-sdd-adoption/specs/sdd/` into
`specs/sdd/spec.md` (the delta becomes living), which makes the R1/R3/R4/R6/R7 `unit` scenarios shipped and
therefore orphan-enforced — the release gate confirms each has a proving test. `sdd:reviewer-conformance:*` and
the `e2e`-declared scenarios remain reserved (unenforced in v0.3). Then cut `## [0.3.0]` in `CHANGELOG.md`, bump
`pyproject`, verify every `base..HEAD` commit carries a `Change: 0003-sdd-adoption` trailer, tag `v0.3.0`, and
move the change to `changes/archive/0003-sdd-adoption/`.
