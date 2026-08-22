# Design — 0003-sdd-adoption

Technical decisions for this change, mapped to **this repo's real modules**. The vault `research/v0.3_research.md`
(D1–D11) is the upstream design-lock; this file is the change-scoped realization. Durable, cross-change calls
graduate to the vault `decisions.md`.

---

## 1. Spec format + the scenario key (D2, D3, D11)

**Format** is OpenSpec verbatim — one `specs/<capability>/spec.md` per capability, requirements as normative
`SHALL` statements, each with WHEN/THEN scenarios; deltas use `## ADDED / MODIFIED / REMOVED Requirements`.

**We add two structured bullets per scenario** (still valid OpenSpec — extra bullets are allowed; `Scenario:` +
WHEN/THEN remain intact):

```markdown
### Requirement: Enforced binding
The system SHALL fail the gate on an orphan scenario or a dangling marker.

#### Scenario: Orphan scenario fails
- **Key:** `sdd:enforced-binding:orphan-scenario-fails`
- **Layers:** unit
- **WHEN** a shipped scenario declaring the `unit` layer has no referencing test
- **THEN** `specs check` exits non-zero and names the orphan
```

- **`Key:`** — an **explicit, author-assigned stable key** (`<capability>:<requirement-slug>:<scenario-slug>`).
  Explicit, not title-derived, so a scenario/requirement can be reworded without silently breaking its binding
  (D3: "a *stable* scenario key"). The checker parses it verbatim; the pytest marker references it verbatim.
- **`Layers:`** — comma-separated applicable layers (D11). **v0.3 recognizes `unit` and `e2e`; it enforces only
  `unit`.** A scenario proved by internal logic declares `unit`; a system-boundary / agent-judgment scenario
  declares `e2e` (reserved — recorded, **not** enforced until the v0.7 tester layer). A scenario may declare
  both (`unit, e2e`); it is unit-enforced now and e2e-enforced later.

**Why explicit keys, not derived slugs:** the example in D3 (`converge:round-cap:halts-at-max`) is shorter than a
full-title slug — the key is a deliberate short identifier the author owns. Deriving from titles couples the key
to prose; an explicit `Key:` bullet is the stable seam.

---

## 2. `orchestrator/specs.py` — the checker (new module) (R1, R6)

A pure, stdlib module (no new dependency — D2). Two collectors + a comparison:

- **Spec side.** Walk `<repo>/specs/**/spec.md` and each **active** `<repo>/changes/*/specs/**/spec.md` (exclude
  `changes/archive/`). A line parser extracts `### Requirement:` / `#### Scenario:` blocks and each scenario's
  `Key:` + `Layers:`. Delta files are parsed under their `## ADDED / MODIFIED / REMOVED` sections: ADDED and
  MODIFIED contribute keys to the **resolvable** set; REMOVED subtracts. Result: `specs_keys` (shipped, in
  top-level `specs/`) and `resolvable_keys` = `specs_keys` ∪ active-delta keys.
- **Test side.** Statically parse the test tree with `ast` (stdlib) — **no pytest run, no recursion into the
  gate**. Collect `@pytest.mark.spec("<key>"[, layer=...])` and `@pytest.mark.spec_exempt("<reason>")`
  decorators (literal args only — dynamic markers are unsupported in v0.3; documented). Result: for each test,
  its referenced keys (+ layer, default `unit`) or its exemption. Test paths come from pyproject
  `[tool.pytest.ini_options].testpaths`, falling back to `tests/`.
- **Checks.**
  1. **Orphan** — every scenario in **top-level `specs/`** whose layers include `unit` has ≥1 `unit` test
     referencing its key; else fail. **Pending delta scenarios are exempt from the orphan check until folded**
     (they are being built phase by phase) — this is how "pending scenario in delta → resolves" holds without a
     half-built change reddening the gate.
  2. **Dangling** — every `spec("key")` resolves to a key in `resolvable_keys`; else fail.
  3. **Traceability (`--strict` only)** — every collected test carries a `spec` or `spec_exempt` marker; else
     fail. **Off by default** (so the gate is a no-op until specs exist and stays green through phases 1–6);
     turned on at phase 7 by switching the gate command to `specs check --strict`.
- **Output / exit.** Human-readable listing of every violation; **exit 0 clean, exit 1 on any violation** — the
  machine-checkable gate contract.

**Marker registration.** `spec` and `spec_exempt` are registered in pyproject `[tool.pytest.ini_options].markers`
so pytest raises no unknown-marker warning (the gate treats warnings as noise, not failure, but keep it clean).

---

## 3. CLI — the `specs check` subcommand (D2)

`orchestrator/__main__.py` today uses `argparse` with a single `run` subparser. Add a **nested** `specs` subparser
carrying a `check` sub-subparser (`--repo`, default cwd; optional `--strict`) → dispatches to `specs.py`. Same
run-from-source shape as `run`. No installed binary — `minions specs check` is only the future alias, referenced
nowhere in code or tests.

---

## 4. `.minions/minions.toml` — MF self-validates (D4)

MF ships **no** `.minions/minions.toml` today (CI runs raw gate commands). Phase 1 adds one whose `gate` list is
the existing four pillars **plus** the checker:

```toml
gate = [
  "uv run ruff format --check .",
  "uv run ruff check .",
  "uv run ty check",
  "uv run pytest -q",
  "uv run python -m orchestrator specs check",
]
```

Phase 7 switches the last entry to `... specs check --strict`. The Makefile `gate` target and
`.github/workflows/ci.yml` gain the same step (so every push enforces it). No-op until specs exist.

---

## 5. Change structure in the repo — the state reader + contract-guard (R4, R5)

`orchestrator/state.py` today reads the **vault** `implementation_plans/` plan (`select_plan`, `read_plan_state`,
`validate_plan`, `PlanContractError`) via `current_phase` + `phaseN` frontmatter. This change adds **in-tree
change resolution** (a sibling reader — the old plan reader stays until the loop self-hosts on changes at v0.5):

- **`read_change_state(repo)`** — resolve the active change dir under `<repo>/changes/` (highest version-id,
  excluding `changes/archive/`); parse `tasks.md`'s **progress checklist** into ordered phases with done/pending
  state; **current phase = the first unchecked phase**; `head` = git HEAD (as today).
- **Progress format (canonical `tasks.md`).** A `## Progress` section of `- [ ] N — <title>` items (checked =
  done). This file dogfoods it. **Advance = a new commit AND the current-phase index moved** (the checkbox
  progressed) — the `driver.decide` advance signal, re-expressed from `current_phase` frontmatter to the
  checklist. `driver.decide` stays deterministic; only the state it compares changes.
- **Contract-guard (`validate_change`, reusing `PlanContractError` semantics).** A well-formed change is
  `changes/<id>/` containing **all** of `proposal.md`, `design.md`, `tasks.md`, and a `specs/` dir; a missing
  artifact is refused at read time with a diagnostic (never a silent empty state or a mid-run `KeyError`).

`R5` is the **locus** decision this realizes: change progress lives in the repo `tasks.md`, read with **no vault
hop**; the vault keeps only product intent (PRD), findings, and narrative. The physical vault directory moves
(`prd/`, `research/`, `archive/`) were a **one-time hand op** already executed (research §"Vault restructure") —
recorded, not code.

---

## 6. Reviewer conformance axis (R2)

`prompts/reviewer.md` gains a spec-conformance axis, re-anchoring the existing "Acceptance met" axis onto
scenarios: the reviewer flags a delta **not genuinely implemented**, **not genuinely test-backed** (a nominal
test that doesn't exercise the scenario — the checker proves a test *exists*; only judgment proves it *bites*),
or **incoherent vs the diff**. This is **prompt** work — the R2 scenario is agent judgment, provable at the
**e2e** tier (declared `Layers: e2e`, reserved for v0.7); phase 4's machine-checkable acceptance is structural
(the axis text is present in `reviewer.md`).

---

## 7. Release fold + gate predicates (R3, R7)

`orchestrator/release.py` today is pure verdict logic (`verify_release_gate`) + effectful `prepare_release`
(cut CHANGELOG, bump pyproject, commit + tag, release log). This change adds:

- **`fold_change(repo, change_id, dry_run=False)`** — fold `changes/<id>/specs/` into top-level `specs/`. **ADDED**
  requirements create/append; **MODIFIED** overwrites the **whole requirement** (D3, open-call §3 — not a patch);
  **REMOVED** deletes. **`dry_run=True`** returns the planned edits without writing. **Verify-after-fold:** after
  writing, run the spec validator (`specs check`) — if `specs/` is invalid, **HALT** (do not move the change).
  **Idempotent:** folding an already-folded change is a no-op (detect by comparing the delta's requirements to
  what is already in `specs/`).
- **`_specs_blocker`** — a new blocker in the `verify_release_gate` scan: `specs/` validates **and** the active
  change is folded; else block.
- **`_trailer_blocker`** (R7) — every `base..HEAD` commit carries a `Change: <id>` trailer resolving to the
  active/archived change; a commit missing it blocks release ("commit missing trailer → HALT"). Fed a commit
  list gathered by the effectful caller (`__main__.py`, via `git log --format=%(trailers...)` or `%B`), keeping
  `verify_release_gate` pure — the established pattern (it "judges over already-gathered facts").
- **Trailer on the release commit** — `SubprocessReleaseGit.commit_all` (or the release message builder) appends
  `Change: <id>`.
- **Archive move** — on a green fold + gate, move `changes/<id>/` → `changes/archive/<id>/`.

These slot into the existing first-non-`None`-blocker scan and the `ReleaseVerdict` / `ReleaseResult` shapes;
`prepare_release`'s "never push, never merge" boundary is unchanged.

---

## 8. Enforcement timeline (why the gate stays green every phase)

| Phase | Adds | Enforced by the gate |
| --- | --- | --- |
| 1 | checker + CLI + `.minions.toml` (no specs yet) | `specs check` no-ops (nothing to check) |
| 2 | change-state reader + contract-guard | unchanged (no new scenarios) |
| 3 | `specs/converge` + `specs/release` **directly**; bind their tests | orphan + dangling now live on those two |
| 4 | reviewer axis (prompt) | unchanged (R2 is e2e-reserved) |
| 5 | fold + gate predicates + trailer | unit-tested; delta still unfolded (pending, so exempt) |
| 6 | `conventions.md` | unchanged |
| 7 | backfill every capability; every test bound | switch to `specs check --strict` (traceability on) |

Delta scenarios (R1–R7 in `changes/0003-.../specs/sdd/`) are **pending** — orphan-exempt — until the release fold
moves them into `specs/`, at which point the **release gate** requires the unit-layer ones proven. R2/R5 boundary
scenarios declare `e2e` and stay unenforced in v0.3 (D11 seam). This is how bidirectional traceability lands
**last** with a green gate the whole way.

---

## 9. Capability taxonomy (for the phase-7 backfill)

One `specs/<cap>/spec.md` per behavioral capability (not strictly 1:1 with modules):

| Capability | Modules | Layer notes |
| --- | --- | --- |
| `sdd` | `specs.py` + reviewer axis + fold + trailer | the delta, folded at release (R1–R7) |
| `converge` | `converge.py` | unit (spec'd early, phase 3) |
| `release` | `release.py` | unit (spec'd early, phase 3) |
| `build-loop` | `driver.py` | unit |
| `change-state` | `state.py` | unit (change reader + contract-guard); vault-move is manual |
| `gate` | `gate.py` | unit |
| `provider` | `provider.py` | unit (`FakeProvider`; real `claude -p` is e2e-reserved) |
| `fanout` | `fanout.py` + `findings.py` | unit |
| `diff` | `diff.py` | unit |
| `status` | `status.py` | unit |
| `cli` | `__main__.py` | unit where logic; wiring is `spec_exempt` |

Genuinely structural tests (parse edge cases, wiring, smoke) use `@pytest.mark.spec_exempt("reason")` — the
explicit, reviewable escape hatch (confirmed 2026-08-22), mirroring the `tests/**`-waives-`D` convention.

---

## Risks / open nuances

- **Static marker collection misses dynamic markers** (`pytestmark`, parametrized markers). MF's suite uses
  literal decorators, so this is fine for the pilot; documented as a v0.3 limitation.
- **Explicit keys can drift from prose** if an author rewords a scenario without updating the marker — but that
  surfaces as a dangling/orphan **failure**, which is the intended loud behavior, not a silent break.
- **`fold` idempotency vs MODIFIED** — re-folding must not double-append; detect "already present, identical" and
  no-op. Covered by a dedicated idempotent-re-run test (R3).
