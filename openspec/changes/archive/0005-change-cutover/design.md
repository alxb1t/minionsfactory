# Design — 0005-change-cutover

The technical *how* for v0.5. Decisions are settled here; there are no open design questions. Line references are
against `4cb0e74` (v0.4.0 merged).

## 1. Shape of the change

The cutover is **wiring, deletion and prose**. Every mechanism R1–R7 needs is already built and unit-tested:
`read_change_state` / `select_change` / `validate_change` / `change_advanced` sit in `orchestrator/state.py:156-304`;
`driver.run` already takes its state reader as an injected seam (`driver.py:110`); the read-only roles already
receive an orchestrator-built Inputs block (`fanout.py:25-43`). No new module, no new dependency, no precursor
refactor. The change removes ~90 LOC from `state.py` and ~180 LOC of tests and adds one field, one helper and one
guard — net complexity goes down.

## 2. Version source (R4)

`ChangeState` gains `version: str` (`state.py:172`). `read_change_state` reads `<change>/proposal.md` through the
existing `parse_frontmatter` (`state.py:31`) and a new guard: absent, or present but not matching `vX.Y`, raises
`PlanContractError` naming the file and the field — alongside the artifact guard in `validate_change`
(`state.py:225`). **One reader, one refusal site.** `__main__._plan_version` (`__main__.py:95-97`) becomes dead and
is deleted in phase 3.

**Decision — frontmatter, not the prose header.** Existing proposals carry no YAML frontmatter; they open with
`**Change:** … · **Version:** vX.Y · …` (`openspec/changes/archive/0004-planning-skills/proposal.md:3`), and
`skills/mf-forge/SKILL.md:27` specifies exactly that shape. Parsing that prose line is genuinely simpler — and
rejected: it is regex-over-prose, the exact pattern being deleted from three prompt files in this same version.
Frontmatter costs one line in `mf-forge` and is read by a function that already exists.

**Consequence — `mf-forge` must be taught the convention in the same phase.** If it lands in code but not in the
skill, the next `mf-`authored change ships without `version:` and is refused at preflight. `skills/mf-forge/SKILL.md`
is edited in **phase 1**; it is the same decision, not a follow-up. (This proposal already carries the frontmatter.)

## 3. Findings home and key (R5)

Three call sites compute the path today — `fanout.py:67`, `__main__.py:141-143` (`_make_converge`), `__main__.py:221-223`
(`_make_release`). All three are replaced by one helper, `findings_path(vault_dir, change_id, role)` in
`orchestrator/findings.py`, returning `<vault>/findings/<change-id>_<role>.md`. `run_fanout`'s `version: str`
parameter becomes `change_id: str`.

**The orchestrator must `mkdir(parents=True, exist_ok=True)` on `<vault>/findings/` before spawning.**
`read_only_profile` (`provider.py:129-134`) grants `Write(<file>)` and denies `Bash`, so a read-only role cannot
create its own directory; without the mkdir the first fan-out of a fresh vault writes nothing and every verdict reads
as not-clean.

**Decision — key on the change id, not the version.** The change id matches the change directory and the `Change:`
commit trailer; the version is a property *of* the change, not its identifier. v0.8's PRD already assumes `findings/`.

## 4. Driver cutover (R1, R2)

- `decide` (`driver.py:39-59`) takes before/after `ChangeState` and delegates the advance test to `change_advanced`
  (`state.py:295`) rather than re-implementing it.
- `run` (`driver.py:103-126`) takes `state_reader: Callable[[Path], ChangeState] = read_change_state` — note the
  **single** argument: the change reader is repo-only, so the `(vault_project_dir, repo)` pair collapses to `repo`.
- The loop condition becomes `not before.is_complete`; `_plan_complete` (`driver.py:83-85`) is deleted.
- `vault_project_dir` **stays** on `run()`: `halt_report_exists` (`driver.py:78`) still reads `<vault>/HALT.md`.
- Event labels (`PhaseStart.phase`, `Advance.from_phase` / `to_phase`) render a phase as `f"{index}: {title}"`.
  `after.current` is `None` at completion, so the final `Advance` needs an explicit terminal label rather than a
  formatted `None`. `status._short_phase` (`status.py:125`) and its scenario `status:render:trims-verbose-phase`
  survive untouched — the field stays a `str`.

  **Decision — a colon, not an em-dash separator.** `_short_phase` trims a label with
  `phase.split(" — ")[0]`, a rule written for the old vault plan's verbose multi-line `current_phase` prose. Label a
  phase `f"{index} — {title}"` and that split fires on the separator itself: every CLI line renders `▶ building 3`
  and the title disappears — `_short_phase` would survive as code while quietly gutting
  `build-loop:run:emits-advancing-event-stream`, which says each phase is rendered as its index *and* title. A colon
  carries no `" — "`, so the label passes through whole and the 72-char truncation still guards a long title. The
  alternative — neutering `_short_phase` to a pure truncator — costs a behavior change and a scenario rewrite in a
  module this change otherwise does not touch.
- Preflight (`__main__.py:287-292`) swaps `read_plan_state` → `read_change_state(repo)`. The uncaught `ValueError`
  disappears by construction: `select_change` (`state.py:200-222`) raises `PlanContractError` on an empty candidate
  set, so `max()` is never reached on an empty sequence.
- **`tests/test_driver.py` is rewritten in this phase, not with the deletion.** `decide` and `run` change their
  parameter types here, so the 26 `PlanState` literals and the two-argument injected reader have to move to
  `ChangeState` in the same commit or the phase cannot go green (`ty check`, then `pytest`). Deferring it to phase 4
  — where the *type* is deleted — reads tidier and is simply not buildable.

## 5. Role inputs (R6)

`fanout._inputs_block` (`fanout.py:25-43`) is generalized into a public builder in the same module and gains change
dir · findings paths · head · version. A second small function assembles `Inputs block + role body` into the final
prompt, so "the prompt leads with the Inputs block" is a unit-testable fact rather than a property of `__main__`
wiring. `prompts/coder.md:19-31`, `prompts/fixer.md:16-30` and `prompts/release.md:22-35` lose their
`PLAN_FILE=$(ls …)` blocks and carry role mandate only. `coder.md` step 3.3 switches from "advance the plan's
`current_phase` frontmatter + flip `phaseN`" to "tick the `tasks.md` `## Progress` checkbox".

**Build-order note — the guard itself lands in phase 6, not here.** It scans `docs/` and `README.md`, which this
phase leaves dirty; R9 cleans them in phase 6. Authored here it would be red on arrival — the same build-order trap
as the REMOVED block in §6, in the opposite direction.

**Build-order note — the `plan_path` → `change_dir` substitution lands in phase 2, not here.** `run_fanout` takes a
`plan_path: Path` fed by `select_plan(vault_dir)` at `__main__.py:109` and `:144`. Those are two of **three** callers:
`_plan_version` (`__main__.py:95-97`, used at `:297`) is the third, and it survives until phase 3 deletes it — so
phase 2 clears the two factory sites but **keeps the import**, and phase 3 takes the count to zero. Phase 4 deletes
`select_plan` itself, so the swap has to precede it; phase 2 already rewrites this exact signature
(`version` → `change_id`), so it does both at once rather than churning it twice. The rest of
R6's Inputs-block work — the public builder, findings paths, head, version, the assembler — stays in this phase.

**Decision — the builder stays in `fanout.py`; no new module.** The Inputs block is already framed there as an
orchestrator-owned concern ("the role has no shell to resolve paths itself"), all four prompt-assembly sites are in
`__main__`, which already imports `fanout`, and a new module for one formatter is surface without benefit. Its
scenarios therefore live under the `fanout` capability.

**Decision — the release role's block is emitted, not prepended at spawn.** The release stage is deterministic code
(`_make_release` → `verify_release_gate` + `prepare_release`); it spawns no role, and `prompts/release.md` is invoked
by hand. The orchestrator still owns the path resolution: it builds the same Inputs block from the same helper and
emits it with the release handoff, so the human-invoked release role reads orchestrator-resolved paths instead of
shelling for them. This satisfies R6's "path resolution exists in exactly one place in code" without inventing a
release spawn the PRD did not authorize.

**A regression guard replaces prose discipline.** One unit test scans `orchestrator/`, `prompts/`, `docs/` and
`README.md` for the string `implementation_plans` and fails on any hit. This single test proves the structural half
of R3, R5 and R9 at once.

**Decision — the guard does not scan `openspec/specs/`.** The obvious instinct is to include it; it is wrong in both
directions in time. *Before* the fold, `openspec/specs/change-state/spec.md:17` still carries the literal — the
delta's REMOVED block does not touch shipped prose until release — so a guard written in phase 5 would be red the
moment it is authored. *After* the fold, this change's own **requirement prose** carries the literal by necessity:
`specs/build-loop/spec.md:78` asserts a run against a target with no `implementation_plans/` directory, and that
scenario folds straight into `openspec/specs/`, so the guard would go red again on the first commit after archive,
contradicting R8's "the fold applies the delta cleanly". (`specs/fanout/spec.md:3` also names the retired location,
but it is *preamble* and never folds — §6.) (The `sdd` guard scenario itself is now written without the literal, but the other two
cannot be: they describe the retired path.) The
retired path *has* to be nameable in the specs that describe its retirement. Spec correctness is already owned by a
mechanism built for it — `specs check --strict` plus the release fold's verify-after-fold — and the contradiction R8
targets is removed directly, by phase 4's hand-deletion of the three shipped plan requirement blocks (§6), not by a
grep. `tests/` is excluded for the mechanical reason that the guard's own needle is a literal in it; `CHANGELOG.md`
and `openspec/changes/archive/` are the historical record and must keep saying what was true.

## 6. Deletion and the build-order rule (R3, R8)

Phase 4 removes `state.py:10-11, 17-28, 47-53, 68-87, 94-117` (~90 LOC) and `tests/test_state.py:24-135`. By then
`tests/test_driver.py` no longer mentions `PlanState` — phase 3 rewrote it (§4). `PlanContractError` (`state.py:90`) and
`parse_frontmatter` stay — the change reader raises the first and `findings.py:9` plus §2's version reader use the
second.

**The test range stops at 135.** `tests/test_state.py:138` onward is the `_write_settings` helper and the four
`change-state:vault-preflight:*` tests, which belong to the **Vault-write preflight** requirement this change keeps.
Taking the block to the end of the plan-reader region by eye would orphan four surviving scenarios in the commit that
can least afford it.

**Three further dependents, easy to miss, each of them fatal to the one-green-commit rule.**

1. **`tests/test_gate.py`** imports `read_plan_state` and `validate_plan` at `line 12`, and `lines 73-105` hold a
   **duplicate** copy of five plan-contract tests that also exist in `test_state.py` — same five
   `change-state:plan-contract:*` markers, asserted twice. Deleting the code without deleting these breaks collection;
   deleting the code *and* declaring the REMOVED block without deleting these leaves five **dangling** markers. The
   duplication is pre-existing and is resolved by deletion, not consolidation — `test_state.py` owned these first.
2. **`__main__.py:109` and `:144`** call `select_plan(vault_dir)` and pass the result into `run_fanout`. Handled in
   **phase 2** (§5, build-order note), so by phase 4 `select_plan` has no caller left.
3. **`docs/modules/state.md:83-93`** documents `select_plan` and the plan reader, and sits inside phase 4's own grep
   acceptance (which scans `docs/`). The sections for deleted symbols go in phase 4; phase 6 keeps the broader docs
   prose rewrite.

**The shipped plan requirements are hand-deleted in the same commit.** Beyond authoring the delta's REMOVED block,
phase 4 deletes the three requirement blocks from `openspec/specs/change-state/spec.md` itself. Doing both is safe —
`_apply_fold` (`release.py:434-439`) skips a REMOVED block whose title it cannot match, so the fold's REMOVED pass
degrades to a no-op — and it is what makes R8 true at phase 4 instead of at release: the tree stops holding two
requirements that assert contradictory behavior the moment the code stops being able to satisfy either. It also
clears the last `implementation_plans` string from `openspec/specs/`, which is otherwise unreachable until the fold
(see §5 on why the guard still does not scan there — the delta's own prose reintroduces it post-fold).

**Build-order rule — the `change-state` `## REMOVED Requirements` block MUST land in the same commit as the code and
test deletions.** `specs.collect_spec_keys` (`specs.py:133-140`) discards a REMOVED key from **both** `resolvable`
and `shipped` the moment the delta declares it, *before* any fold. Author it early and the nine still-present
plan-test markers go **dangling** → red gate from phase 1. Author it late and the nine shipped scenarios go
**orphaned** → red gate at phase 4. It is therefore **deliberately absent from this delta as authored**; phase 4
creates `specs/change-state/spec.md` and deletes the code in one commit. See `specs/README.md`.

`change-state:plan-state:parses-frontmatter` is **re-bound**, not exempted: `parse_frontmatter` survives, so its test
is rewritten against a proposal's `version:` frontmatter and bound to the new version-source scenario. Same function,
same behavior, a scenario that still describes it.

**Two hand-edits the fold cannot reach.** `release._apply_fold` (`release.py:445`) keeps `target_preamble` verbatim
and only upserts `### Requirement:` blocks, so capability **preamble prose** is out of a delta's reach. Phase 6
hand-edits `openspec/specs/change-state/spec.md:1-9`, whose header still says the capability captures "the
**vault-plan reader**" and calls the in-tree reader "the v0.5 sibling", and `openspec/specs/build-loop/spec.md:1-8`
where the loop is described over a plan. The fold's blind spot is filed to the backlog.

**MODIFIED overwrites whole.** `_apply_fold` matches by requirement **title** and replaces the entire block, so every
MODIFIED requirement in this delta reproduces *all* of its scenarios — surviving ones verbatim — and no MODIFIED
requirement is retitled (a retitle would append a duplicate and orphan the original).

## 7. Release stage — what is and is not in scope

`verify_release_gate` (`release.py:139-151`) defaults `specs_valid=True`, `change_folded=True`, `commits=()`,
`known_change_ids=()`; `_make_release` (`__main__.py:212-242`) passes none of them, never passes `change_id` to
`prepare_release`, and never calls `fold_change` (`release.py:503`) — all spec'd, all unit-tested, all unreachable.
The response is split:

- **(a) Orchestrator wiring → deferred to the backlog.** Passing the four gathered facts and `change_id` into the
  release gate is new behavior; the PRD's "no new capability" excludes it. It gets its own version.
- **(b) The fold step → in scope, phase 5, prose only.** `specs.collect_spec_keys` (`specs.py:143-146`) skips
  `changes/archive/`, so the instant `0005-change-cutover` is archived its ADDED keys stop resolving and every marker
  bound to them goes dangling — `specs check --strict` goes red on the first commit after release unless the delta
  was folded into `openspec/specs/` in the same commit. It is manual today (0003's fold + archive landed inside
  `chore(release): v0.3.0` by hand) and `prompts/release.md` mentions fold, archive and `specs check` **nowhere**,
  though `CLAUDE.md:6-8` says the release step does exactly that. Phase 5 rewrites that prompt anyway: add
  fold → verify-after-fold → archive to its Step 2 and `specs check --strict` to its Step 1 checklist.

## 8. Names kept deliberately

`PlanContractError` keeps its name although its subject is now a change. Renaming it touches every raise site, every
`except` clause in `__main__`, and the preflight's contract — churn with no behavioral payoff, in the commit that is
already the riskiest. Recorded here so it reads as a decision rather than an oversight.

## 9. Known-stale prose deliberately left alone

`CHANGELOG.md:73` describes `coder.md` as a "warm whole-plan" coder building every remaining phase in one session,
while `prompts/coder.md:5-12` says "exactly ONE phase per invocation" and `driver.run` (`driver.py:126-217`) spawns
one coder per phase. Noticed while surveying, and **not** corrected here.

Two reasons. It is not stale prose — it is a **shipped `## [0.2.0]` entry**, an accurate record of what v0.2.0 did,
and `CHANGELOG.md:71` in that same section already records the revert to the per-phase coder, so the file read in
order is not misleading. And rewriting it would cut directly against this change's own justification for holding the
CHANGELOG outside the regression guard (§5): the historical record must keep saying what was true. No PRD requirement
authorizes the edit — R9 scopes docs to `README.md`, `docs/README.md` and `docs/modules/*.md`. If the entry ever needs
qualifying, that belongs in an `## [Unreleased]` note, not in a rewrite of a shipped section.

## 10. Risks carried into the build

1. **REMOVED-block ordering** (§6) — the most likely mid-build gate failure. It is a hard build-order rule, stated in
   `tasks.md` phase 4, not a preference.
2. **Test-rewrite volume in `test_driver.py`, in phase 3** — 26 `PlanState` literals become `ChangeState` in the same
   commit that retypes `decide` and `run`. A careless rewrite can quietly soften assertions in the module that proves
   the un-gameable advance, and it happens *before* the deletion phase that would otherwise force the issue. Named
   explicitly for the reviewer's gate-integrity axis.
3. **`mf-forge` drift** — the convention must land in the skill in phase 1 (§2). Low blast radius today (v0.6–v0.7 are
   doc-only) but it is the code-says-X / prose-says-Y class this version exists to kill.
4. **Five targets break at merge**, not one. Accepted in Non-goals and routed to v0.6 `mf-teardown`.
5. **The after-fold trap, twice.** Two otherwise-reasonable gate assertions go red *after* release rather than during
   the build: a regression guard scanning `openspec/specs/` (§5) and a committed `fold_change(dry_run=True)` edit-set
   assertion (phase 6). Both are resolved by scoping — the guard skips the specs, the fold check is a one-off
   rehearsal, not a test. The general rule this change learns: **an assertion whose subject the release fold mutates
   cannot live in the gate.**
