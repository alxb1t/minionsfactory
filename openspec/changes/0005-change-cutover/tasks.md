# Tasks — 0005-change-cutover

Ordered phases for v0.5. **Build mode: by hand** (Claude Code + prompts; no orchestrator automation — driving this
change through `run` would require the working state reader that *is* the deliverable). Read `proposal.md` +
`design.md` (this dir) and the vault PRD (`prd/v0.5_change_cutover.md`) first.

**Per-phase ritual (every phase).**
- **Test-first** (red → green) for every unit of logic; the full gate green before the phase is done:
  `uv run ruff format --check .` · `uv run ruff check .` · `uv run ty check` · `uv run pytest -q` ·
  `uv run python -m orchestrator specs check`.
- **Commit** the phase in the code repo with a `Change: 0005-change-cutover` git trailer, **contiguous** with
  `Co-Authored-By:` (no blank line between — git parses the trailer block as the last paragraph). Vault edits
  (`log.md`, `backlog.md`) are separate from the code commit.
- Append the phase's changes under `## [Unreleased]` in `CHANGELOG.md`.
- **Delta scenarios are pending** (orphan-exempt) until the release fold; bind each new scenario in the phase that
  implements it.

**Requirement keys** referenced below live in `specs/` (this change's delta). One block is deliberately **not** in the
delta as authored — see phase 4 and `specs/README.md`.

## Progress

- [x] 1 — Version source: `version:` in the change proposal, the reader, the guard, and `mf-forge`
- [x] 2 — Findings home and key: `<vault>/findings/<change-id>_<role>.md`
- [x] 3 — Driver cutover: `decide` / `run` over `ChangeState`, preflight switch
- [ ] 4 — Delete the vault-plan path (code + tests + the `change-state` REMOVED block, one commit)
- [ ] 5 — Role inputs: coder / fixer / release; the release prompt gains the fold step
- [ ] 6 — Specs and docs: preambles, the docs sweep, and the retired-path regression guard
- [ ] 7 — Bookkeeping: backlog, `findings/`, CHANGELOG

---

## Phase 1 — Version source: `version:` in the change proposal, the reader, the guard, and `mf-forge`

Make the release version a declared property of the change (R4, half of R7).

**Scope.** Add `version: str` to `ChangeState` (`state.py:172`). `read_change_state` reads `<change>/proposal.md`
through the existing `parse_frontmatter` and a new guard: absent, or present but not matching `vX.Y`, raises
`PlanContractError` naming the file *and* the field. **In the same phase**, teach the convention to
`skills/mf-forge/SKILL.md` (the "Write the change" section): `proposal.md` opens with `---\nversion: vX.Y\n---`
followed by the existing header line. `__main__._plan_version` stays for now (it dies in phase 3).

**Machine-checkable acceptance.**
- `read_change_state` against a change whose `proposal.md` declares `version: v0.6` returns a state carrying `v0.6`.
- A `proposal.md` with no frontmatter, no `version` key, or a `version` that is not `vX.Y` raises `PlanContractError`
  whose message names `proposal.md` and `version`.
- `skills/mf-forge/SKILL.md` documents the frontmatter; `grep -c 'version:' skills/mf-forge/SKILL.md` is non-zero.
- Full gate green.

**Proves (delta, pending):** `sdd:change-structure:version-declared-in-proposal`,
`sdd:change-structure:missing-version-refused`.

## Phase 2 — Findings home and key: `<vault>/findings/<change-id>_<role>.md`

Move the findings home out of `implementation_plans/` and key it to the change id (R5).

**Scope.** New `findings_path(vault_dir, change_id, role)` in `orchestrator/findings.py` returning
`<vault>/findings/<change-id>_<role>.md`. Replace the three sites that compute it today — `fanout.py:67`,
`__main__.py:141-143` (`_make_converge`), `__main__.py:221-223` (`_make_release`). `run_fanout`'s `version: str`
parameter becomes `change_id: str`. **`run_fanout` creates `<vault>/findings/` (`mkdir(parents=True, exist_ok=True)`)
before spawning any role** — `read_only_profile` grants `Write(<file>)` and denies `Bash`, so the role cannot create
its own directory.

**In the same phase — the last two `select_plan` call sites die.** `run_fanout`'s `plan_path: Path` parameter becomes
`change_dir: Path`, and `_inputs_block`'s `- Plan (acceptance + conventions): {plan_path}` line becomes
`- Change (proposal · design · tasks): {change_dir}`. `_make_fanout` (`__main__.py:109`) and `_make_converge`
(`__main__.py:144`) drop `plan_path = select_plan(vault_dir)` for `select_change(repo)` (`state.py:200`). **The
`select_plan` import stays** — `_plan_version` (`__main__.py:95-97`, called at `:297`) is a **third** caller, and
phase 1 explicitly keeps it until phase 3 deletes it. This is build-order, not scope drift: phase 4 deletes
`select_plan`, so all three callers must be gone by then; this phase clears two and phase 3 clears the last. The phase rewrites both `run_fanout` parameters at once rather
than churning the same signature twice; the *rest* of the Inputs-block work (public builder, findings paths, head,
version, the assembler) stays in phase 5 where R6 puts it.

**Machine-checkable acceptance.**
- `findings_path(vault, "0005-change-cutover", "review")` == `vault / "findings" / "0005-change-cutover_review.md"`.
- A fan-out for `0005-change-cutover` writes `findings/0005-change-cutover_{review,security,simplify}.md`.
- `run_fanout` against a vault with no `findings/` dir creates it before the first spawn (assert on spawn ordering,
  not just on the end state).
- No literal findings path remains in `fanout.py` or `__main__.py`: `grep -n 'implementation_plans' orchestrator/`
  returns only `state.py` (the plan reader, deleted in phase 4).
- `grep -n 'select_plan' orchestrator/__main__.py` returns **exactly two lines** — the import and the one call
  inside `_plan_version`. Neither factory calls it; both resolve the change dir via `select_change(repo)`. (Phase 3
  deletes `_plan_version` and takes the count to zero.)
- The Inputs block a fanned-out role receives names the change dir; no line of it names a plan file.
- Full gate green.

**Proves (delta, pending):** `fanout:findings-path:change-id-keyed-path`,
`fanout:findings-path:fanout-writes-through-helper`, `fanout:findings-path:creates-findings-dir`.

## Phase 3 — Driver cutover: `decide` / `run` over `ChangeState`, preflight switch

Wire the built-and-tested reader into the loop (R1, R2, rest of R7).

**Scope.** `decide` takes before/after `ChangeState` + gate result + halt flag and delegates the advance test to
`change_advanced` (no re-implementation). `run` takes `state_reader: Callable[[Path], ChangeState] = read_change_state`
— one argument, the repo — and loops on `not before.is_complete`; `_plan_complete` is deleted. `vault_project_dir`
**stays** on `run()` (`halt_report_exists` still reads `<vault>/HALT.md`). Event labels render a phase as
`f"{index}: {title}"` — **a colon, not an em-dash separator**: `status._short_phase` (`status.py:125`) trims a label
by splitting on `" — "`, so an em-dash label would render as the bare index and drop the title the event stream is
supposed to carry. An explicit terminal label goes on the final `Advance` (`after.current` is `None` at completion). Preflight (`__main__.py:287-292`) swaps `read_plan_state` → `read_change_state(repo)`;
`__main__._plan_version` is deleted along with the now-unused `select_plan` import, the version coming from
`ChangeState`.

**In the same phase — rewrite `tests/test_driver.py`.** Every `PlanState` literal (26 occurrences) becomes
`ChangeState`, and the injected reader goes from two arguments to one. This is **not** deferrable to phase 4:
`decide` and `run` change their parameter types here (`driver.py:40-41, 83, 110`), so a phase-3 commit that leaves
the tests building `PlanState` fails `ty check` and `pytest` in the same phase — the gate cannot be green without
it. The rewrite must be **behaviour-preserving**: each test still asserts the same advance/halt outcome and the same
reason it asserted before, over the new type. This is the change's largest hand-edit and the one most able to
quietly soften the assertions that make the advance un-gameable.

**Machine-checkable acceptance.**
- `decide` advances only on: green gate + no HALT + a new commit + a moved current-phase index. A moved checkbox with
  no new commit halts; a new commit with no moved checkbox halts.
- `grep -c 'PlanState' tests/test_driver.py` is `0`, and the rewritten assertions are behaviour-preserving — each test
  asserts the same outcome and reason it asserted before the rewrite.
- `grep -n 'select_plan\|_plan_version' orchestrator/__main__.py` returns nothing.
- `run` drives a repo-only fixture to COMPLETE with **no vault plan file present anywhere**, and the fan-out still
  fires at change-complete (existing `build-loop:end-of-plan:fanout-on-complete` stays green).
- `status._short_phase` and `status:render:trims-verbose-phase` are untouched and green (the event field stays `str`),
  **and the rendered label always keeps its title**: `_short_phase(f"{index}: {title}")` never reduces the label to the
  bare index, because the label contains no `" — "` for it to split on. Four of this change's seven labels exceed 72
  characters and are tail-truncated with an ellipsis, which is the function doing its job — the index *and* the title
  are still there, which is what `build-loop:run:emits-advancing-event-stream` requires.
- `_make_release` receives its version from `ChangeState.version`; `grep -rn '_plan_version' orchestrator/` returns
  nothing and no version is derived from a vault filename anywhere in `__main__.py`.
- A misconfigured target reaches the preflight's `PlanContractError` branch — **no `ValueError` escapes**
  `python -m orchestrator run --repo <fixture>`; the process exits non-zero having spawned no role.
- Full gate green.

**Proves (delta, pending):** `build-loop:phase-decision:advances-on-commit-and-moved-phase`,
`build-loop:phase-decision:no-advance-halts`, `build-loop:phase-decision:moved-checkbox-without-commit-halts`,
`build-loop:run:drives-with-no-vault-plan`, `sdd:change-structure:no-active-change-refused`,
`sdd:change-structure:no-progress-checklist-refused`.

## Phase 4 — Delete the vault-plan path (code + tests + the `change-state` REMOVED block, one commit)

The riskiest commit, isolated behind an already-green driver (R3, half of R8).

> **BUILD-ORDER RULE — non-negotiable.** Create `specs/change-state/spec.md` with its `## REMOVED Requirements`
> block **in the same commit** as the code and test deletions. `specs.collect_spec_keys` (`specs.py:133-140`)
> discards a REMOVED key from **both** `resolvable` and `shipped` the moment the delta declares it, before any fold:
> author it earlier and the nine still-present plan-test markers go **dangling** (red gate); author it later and the
> nine shipped scenarios go **orphaned** (red gate). It is deliberately absent from the delta as authored — see
> `specs/README.md`.

**Scope — the complete deletion inventory. Every item lands in this one commit.**

1. **Code** — `select_plan`, `read_plan_state`, `validate_plan`, `PlanState`, `_PLAN_PATTERN` and
   `_CODE_PHASE_STATUSES` (`state.py:10-11, 17-28, 47-53, 68-87, 94-117`). **Keep** `PlanContractError` (the change
   reader raises it) and `parse_frontmatter` (`findings.py:9` and phase 1's version reader use it).
   **Two prose sites in the same file, which no grep in this change catches** (they name no deleted symbol and no
   retired path): the module docstring at `state.py:1` — "Plan-state reader: reconstruct 'where are we' from disk
   (plan + git)" — and the section comment at `state.py:156-160`, which frames the in-tree reader as a
   "sibling to the vault-plan reader above" and says "the driver keeps running the vault-plan reader until the loop
   self-hosts on changes". Both describe precisely the arrangement this change ends; after phase 3 they are false in
   shipped code. Rewrite both to describe the change reader as the only reader.
2. **`tests/test_state.py:24-135`** — the plan-reader tests, carrying nine
   `change-state:plan-{selection,state,contract}:*` markers. **The range stops at 135.** Line 138's `_write_settings`
   helper and the four `change-state:vault-preflight:*` tests from line 145 on belong to the **Vault-write
   preflight** requirement, which this change keeps — delete them and four kept scenarios go orphaned in the same
   commit that is already the riskiest.
3. **`tests/test_gate.py`** — `line 12` imports `read_plan_state` and `validate_plan` from `orchestrator.state`, and
   **lines 73-105 hold a second, duplicate copy of five plan-contract tests** (`accepts-conforming`,
   `rejects-empty-frontmatter`, `rejects-missing-current-phase`, `rejects-no-phase-flags`,
   `refuses-malformed-at-read`). Drop the import and that whole block. Miss it and the deletion breaks collection
   outright, and the same-commit REMOVED block leaves five **dangling** markers — the exact red gate the build-order
   rule above exists to prevent, in the commit it governs. The `gate:` tests in that file are untouched.
4. **`tests/test_driver.py`** — nothing to do here; **phase 3 already rewrote it**, because `decide` and `run`
   changed types there and the gate could not have been green otherwise.
5. **`docs/modules/state.md:83-93`** — the `select_plan` section (and the plan-reader sections around it) sits inside
   this phase's own grep acceptance, which scans `docs/`. Delete the sections for the symbols this phase deletes;
   phase 6 still owns the broader docs prose rewrite.
6. **The delta's `change-state` REMOVED block** — author `specs/change-state/spec.md` with the three plan
   requirements (**Plan selection**, **Plan-state assembly**, **Plan contract guard**), reproducing each requirement's
   scenarios with their `Key:` lines (the discard is per key, not per title). **Keep** the **Vault-write preflight**
   requirement.
7. **`openspec/specs/change-state/spec.md`** — hand-delete those same three shipped requirement blocks (they span
   `line 17` onward, the last surviving `implementation_plans` reference in the tree). The REMOVED block in (6) is the
   formal record and drives `collect_spec_keys`' discard; deleting the shipped prose in the same commit is what ends
   the R8 contradiction **now** rather than at release. Safe to do both: `_apply_fold` (`release.py:434-439`) skips a
   REMOVED block whose title it cannot find, so the fold's REMOVED pass simply becomes a no-op.

Re-bind `change-state:plan-state:parses-frontmatter`'s test — rewrite it against a proposal's `version:` frontmatter
and bind it to `sdd:change-structure:version-declared-in-proposal` rather than reaching for `spec_exempt`.

**Machine-checkable acceptance.**
- `grep -rn 'select_plan\|read_plan_state\|validate_plan\|PlanState' orchestrator/ tests/ prompts/ docs/modules/state.md`
  returns nothing.
- `grep -rn 'implementation_plans' orchestrator/ tests/ docs/modules/state.md openspec/specs/` returns nothing.
- **Scoped deliberately.** The rest of `docs/` still carries plan references this phase does not own —
  `docs/modules/driver.md` (4), `docs/modules/main.md` (2), `docs/modules/findings.md` (1),
  `docs/modules/fanout.md` (3), `docs/README.md` (1), `README.md` (1). They are prose about the loop, not about the
  deleted symbols, and R9 puts them in **phase 6**, which carries the repo-wide grep. A phase-4 acceptance that
  scanned all of `docs/` could not go green in phase 4.
- `uv run pytest -q tests/test_gate.py` collects and passes with the five duplicated plan-contract tests **gone**, and
  the `gate:*` markers in that file still bound.
- `uv run pytest -q` is green with the plan-reader tests **deleted, not skipped** — the collected-test count drops by
  exactly the number removed and no `skip`/`xfail` marker was added.
- `uv run python -m orchestrator specs check` is green **in this commit** (no dangling markers, no orphan scenarios) —
  this is the assertion that proves items 1-3, 6 and 7 landed together.
- `orchestrator/state.py` contains no prose describing a vault-plan reader: neither "plan-state reader" nor
  "vault-plan reader" appears in the module docstring or the section comments (checked by eye — these are the two
  sites no symbol or path grep reaches).
- The rewritten `test_driver.py` assertions are behaviour-preserving: each test still asserts the same advance/halt
  outcome and reason it asserted before, over `ChangeState` instead of `PlanState`.
- Full gate green.

**Proves (delta):** the `change-state` REMOVED block authored in this phase.

## Phase 5 — Role inputs: coder / fixer / release; the release prompt gains the fold step

The orchestrator owns path resolution; the prompts carry mandate only (R6).

**Scope.** Generalize `fanout._inputs_block` into a public builder in `fanout.py`, carrying change dir · findings
paths · head · version; add a small assembler so `Inputs block + role body` is unit-testable rather than a property of
`__main__` wiring. Prepend for coder and fixer at spawn; **emit** the same block with the release handoff (the release
stage is deterministic code and spawns no role — see `design.md` §5). Strip the `PLAN_FILE=$(ls …)` blocks from
`prompts/coder.md:19-31`, `prompts/fixer.md:16-30`, `prompts/release.md:22-35`. `coder.md` step 3.3 switches from
"advance the plan's `current_phase` frontmatter + flip `phaseN`" to "tick the `tasks.md` `## Progress` checkbox".
**`prompts/release.md` gains the fold step**: fold → verify-after-fold → archive in its Step 2, and
`specs check --strict` in its Step 1 checklist (`design.md` §7b). The **repo-wide regression guard is authored in phase 6**, not here: it scans
`docs/` and `README.md`, which this phase leaves dirty and phase 6 cleans. Writing it here would be red on arrival.

**Machine-checkable acceptance.**
- The assembled prompt for each of coder, fixer and release starts with the Inputs block, then the role body.
- The Inputs block names the change dir, each findings path, the head SHA and the version.
- `grep -rn 'PLAN_FILE\|implementation_plans' prompts/` returns nothing.
- `prompts/release.md` contains a fold step naming `openspec/specs/`, archive, and `specs check --strict`.
- Full gate green.

**Proves (delta, pending):** `fanout:role-inputs:block-carries-change-and-findings`,
`fanout:role-inputs:prompt-leads-with-inputs`.

## Phase 6 — Specs and docs: preambles, the docs sweep, and the retired-path regression guard

Make the shipped specs and docs describe the running model (R8, R9).

**Scope.** Rewrite `sdd:vault-layout:progress-in-repo`'s proving test so it drives `driver.run` with the real
`read_change_state` instead of calling the helper directly (`tests/test_state.py:308`) — the requirement is that the
*driver* consults no vault path. Bind the MODIFIED `cli:preflight:refuses-misconfigured-target` (e2e, reserved — no
unit test owed). **Hand-edit two capability preambles the fold cannot reach** (`release._apply_fold` keeps
`target_preamble` verbatim): `openspec/specs/change-state/spec.md:1-9`, which still says the capability captures "the
**vault-plan reader**" and calls the in-tree reader "the v0.5 sibling" — after this change it holds the vault-write
preflight only; and `openspec/specs/build-loop/spec.md:1-8`, which describes the loop over a plan. File the fold's
preamble blind spot to the vault backlog.

**Docs — the complete list; after this phase the tree names the retired path nowhere outside the historical record.**
`README.md:36`, `docs/README.md:4,33-35`, `docs/modules/fanout.md:34,67,83`, `docs/modules/driver.md` (4 plan-symbol
references), `docs/modules/main.md` (2, plus the `_plan_version` mermaid node at `:38` — a different symbol from the four above,
stale the moment phase 3 deletes it, and covered by this phase's grep), and `docs/modules/findings.md:55` (a `PlanState` cross-link into
`state.md#planstate`, an anchor phase 4 deletes — a dead link if it is missed). `docs/modules/state.md`'s remaining
plan prose is finished here; phase 4 removed only the sections for the symbols it deleted. **`CLAUDE.md` needs no
edit** — it already describes the in-tree change model end to end.

**The repo-wide regression guard lands here** (moved from phase 5, which leaves `docs/` and `README.md` dirty): one
test scanning `orchestrator/`, `prompts/`, `docs/` and `README.md` for the string `implementation_plans`, failing on
any hit. **`openspec/specs/` is deliberately not scanned, and neither is `tests/`** — see `design.md` §5: the living
specs are reconciled by this change's REMOVED/MODIFIED blocks and verified by `specs check --strict` plus the release
fold, and a grep guard over them is self-defeating (the delta must name the retired path to describe its own removal,
and that prose folds into `openspec/specs/` at release). `tests/` is excluded because the guard's own needle is a
literal in it. `CHANGELOG.md` and `openspec/changes/archive/` are the historical record and are out of scope by the
same reasoning.

**Machine-checkable acceptance.**
- `uv run python -m orchestrator specs check --strict` is green.
- No requirement in `openspec/specs/` asserts that progress is read from a vault plan file, and no two requirements
  assert contradictory behavior about where progress is read. (Reachable because **phase 4** hand-deleted the three
  shipped plan requirement blocks; this phase only fixes the two preambles the fold cannot reach.)
- **A one-off fold rehearsal, run at this phase and _not_ committed as a test.** Run
  `fold_change(repo, "0005-change-cutover", dry_run=True)` and assert **over `result.edits`, not `result.ok`**
  (`release.py:535` returns `ok=True` unconditionally on the dry-run path, so asserting on it proves nothing): every
  MODIFIED requirement in the delta appears as `("modified", <title>)`, and the only `("added", …)` entries are the
  two genuinely new `fanout` requirements. That is the check that bites — `_apply_fold` **appends** a non-REMOVED
  block whose title it cannot match, so a drifted MODIFIED title shows up as `added` and would silently duplicate the
  requirement at release instead of replacing it.
  **It must not become a gate test.** After the release fold the delta and the folded specs are identical, so
  `_apply_fold` emits no edit and `_resolve_delta_specs` still resolves the change from `changes/archive/` — the same
  call then returns `edits == ()` and a committed assertion would go red on the release commit. Verified against
  `0003-sdd-adoption`, folded and archived, which dry-runs today as `ok=True, edits=0`. Same after-fold trap as the
  regression guard in §5; record the rehearsal's output in the phase's log entry, not in `tests/`.
- `sdd:vault-layout:progress-in-repo` is bound to a test that calls `driver.run`, not `read_change_state` directly.
- The regression guard authored in this phase is green over `orchestrator/`, `prompts/`, `docs/` and `README.md`,
  and fails when an `implementation_plans` string is reintroduced into any of them.
- The guard's scanned set is exactly `orchestrator/`, `prompts/`, `docs/`, `README.md` — asserted in the test itself,
  so narrowing it later is a visible edit rather than a silent one.
- `grep -rn 'select_plan\|read_plan_state\|validate_plan\|PlanState\|_plan_version' docs/` returns nothing (no dead
  cross-links into anchors phase 4 removed, and no diagram node for a helper phase 3 deleted).
- Full gate green.

**Proves (delta, pending):** `sdd:vault-layout:progress-in-repo`, `sdd:vault-layout:no-plan-path-references`,
`cli:preflight:refuses-misconfigured-target` (e2e, reserved).

## Phase 7 — Bookkeeping: backlog, `findings/`, CHANGELOG

Close the loose ends this branch introduces or dissolves, and leave the release gate satisfiable (R10).

**Scope.** In the vault: retitle `backlog.md:10` `## Current release (v0.4)` → `## Current release (v0.5)` (the
release gate parses that heading — `release.py:32-49`); close the two items this version dissolves with a pointer
rather than work — the `_plan_complete` vs `validate_plan` status-vocabulary mismatch (`backlog.md:31`; checkbox
phases replace `{done, wip, planned, todo}` entirely) and the stale `minions.toml` relocation note (`backlog.md:82`;
`gate.py` already reads `.minions/minions.toml`); keep the isekai migration open, **retargeted at v0.6
`mf-teardown`** (`backlog.md:33`) and widened to name all five affected targets (isekai, KitchenScheduler,
Palimpsest, Apilogue, Tomten); file the two deferrals from `design.md` — the release stage's SDD-predicate wiring
(§7a) and the fold's preamble blind spot (§6). Create `<vault>/findings/`. Finalize the `## [Unreleased]` CHANGELOG
section for v0.5.

> The change directory `openspec/changes/0005-change-cutover/` is written at **planning** time by `mf-forge`. This
> phase is bookkeeping and the CHANGELOG cut, not artifact authoring.

**Machine-checkable acceptance.**
- `<vault>/backlog.md` has exactly one `## Current release (v0.5)` heading and **zero** open `- [ ]` items under it
  (the release role gates on this).
- `<vault>/findings/` exists.
- `CHANGELOG.md`'s `## [Unreleased]` section is non-empty and describes the cutover.
- `git log --format='%(trailers:key=Change)' main..HEAD` shows `Change: 0005-change-cutover` on every commit.
- Full gate green.
