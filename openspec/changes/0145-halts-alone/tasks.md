# Halts alone — tasks

Each phase gives a halt a route: the rescue's amend, the gate under load, Codex's fallbacks, converge's ways back, the supervisor at the cap, and the changelog rule with the wait and the records.

## Progress

- [x] 1 — The rescue's amend · hard
- [x] 2 — The gate under load · moderate
- [x] 3 — Codex's fallbacks · hard
- [x] 4 — Converge's ways back · hard
- [x] 5 — The supervisor at the cap · hard
- [x] 6 — The changelog rule, the wait and the records · moderate
- [x] 7 — The rescope's one missing-file halt · moderate

## 1 — The rescue's amend

- [x] 1.1 **HALT CHECK** `_amend` in `skills/mf-ship/scripts/conduct.py` still refuses a decision that lacks the `Decided-by: rescue` trailer.
  Verify: `git grep -n -e "decided with no Decided-by" -- skills/mf-ship/scripts/conduct.py` exits 0.
- [x] 1.2 In `_amend`, drop the trailer condition per [D1](design.md#d1). Edit `test_a_rescue_decides_under_the_switch` in `tests/test_conduct.py`: the trailer-less amend returns `(head, "", True)`; add `test_a_decided_amend_needs_no_trailer_under_the_switch`.
  Verify: `uv run pytest tests/test_conduct.py -k "decided_amend_needs_no_trailer" -q` exits 0.
- [x] 1.3 In `Run.rescue`, reset a refused amend per [D2](design.md#d2): only when `before` is an ancestor of `HEAD`, the tree was clean at the spawn and is clean now, and every commit past `before` has a `Rescue:` trailer, run `_git(tree, "reset", "-q", "--hard", before)` and log `reset` with `rescue commit <sha7> dropped: <why>`, both in the `elif spawned:` branch before `self.halt`. Add `test_a_refused_amend_is_reset_off_head` (a person's trailer-less amend stays).
  Verify: `uv run pytest tests/test_conduct.py -k "refused_amend_is_reset" -q` exits 0.
- [x] 1.4 Edit the no-switch half of `test_a_rescue_decides_under_the_switch` to commit its own decided amend again after the reset, and the security-card case of `test_a_rescue_amends_at_amend_needed`, whose `rescue answered its halt` assertion now reads no such line; read `test_a_rescue_outside_the_plan_halts` for the order of its `halt` lines.
  Verify: `uv run pytest tests/test_conduct.py -k "rescue_decides_under_the_switch or rescue_amends_at_amend_needed or rescue_outside_the_plan" -q` exits 0.
- [x] 1.5 In `skills/mf-rescue/SKILL.md`, *Parameter — `decide=recommended`* and the commit paragraph that names `Decided-by: rescue`: a `### D<n>` body is a decision; the commit asks for the trailer; under the switch the run takes a trailer-less decided amend.
  Verify: `git grep -n -F "trailer-less" -- skills/mf-rescue/SKILL.md` exits 0.
- [x] 1.6 In `docs/decisions.md`, D60: change "its commit carrying `Decided-by: rescue`" to "its commit asked to carry `Decided-by: rescue`, a trailer-less decided amend taken too", and add that a refused amend is reset.
  Verify: `git grep -n -F "trailer-less" -- docs/decisions.md` exits 0.

## 2 — The gate under load

- [x] 2.1 Add `LOAD_WAIT = 1800`, `LOAD_POLL = 30` and `_load_wait(say)` to `skills/mf-ship/scripts/conduct.py`, which loads `PLAN_CHECK` with `runpy.run_path`; call it in `_run_gate` on a red gate per [D3](design.md#d3). In `tests/test_conduct.py` add an autouse fixture patching `os.getloadavg` to `(0.0, 0.0, 0.0)` and `test_a_gate_red_under_load_waits_and_runs_again`: green after the wait, red twice, a low load, a load that never falls.
  Verify: `uv run pytest tests/test_conduct.py -k "gate_red_under_load" -q` exits 0.

## 3 — Codex's fallbacks

- [x] 3.1 **HALT CHECK** `Run.checker` counts only the runs that ended on a usage limit.
  Verify: `git grep -n -e "codex_runs == 2" -- skills/mf-ship/scripts/conduct.py` exits 0.
- [x] 3.2 In `Run.checker`, count a Codex run that exits non-zero, not killed, with `tokens_of(out)` None beside a usage limit; at two, run on `_shadow`'s models, `fallback` the string `codex failed` unless a run ended on a limit, a shadow checker stopping with ` · stopped by a codex failure`; type `Checked.fallback` as `bool | str` ([D4](design.md#d4)). In `converge.py`, type the protocol's `fallback` the same and make `_spent` write `fallback: codex failed` for a string.
  Verify: `git grep -n -F "fallback: codex failed" -- skills/mf-converge/scripts/converge.py` exits 0.
- [x] 3.3 Add `test_a_codex_checker_that_fails_twice_runs_on_claude` to `tests/test_conduct.py` (one failure stays on Codex, two run on Claude, a limit keeps its text) and `test_a_codex_failure_fallback_is_named_in_the_verdicts_line` to `tests/test_converge.py`.
  Verify: `uv run pytest tests/test_conduct.py tests/test_converge.py -k "codex_checker_that_fails_twice or codex_failure_fallback" -q` exits 0.
- [x] 3.4 Add `Run.codex_off` per [D5](design.md#d5): `probe` and `probe_checker` take a `solo` flag that `probe_for` sets when no `stations` entry names the executor; a failed checker probe then halts nothing, marks the change, and `probe_for` goes on to the next executor with no `refused` reason cached; it logs `codex — <id>: probe failed · its checkers run on Claude`, and `codex_ready` and `probe_for` read the mark before they probe. Add `test_a_failed_checker_probe_leaves_the_checkers_on_claude`; edit `test_the_codex_probe_runs_a_checker` where a checker-only version halts on `probe-codex-checker check fail`.
  Verify: `uv run pytest tests/test_conduct.py -k "failed_checker_probe" -q` exits 0.
- [x] 3.5 In `docs/decisions.md`, D76: under **Rejected** change "the conductor telling a limit from a failure" to "the checker call counts failures, and the conductor tells none from a limit", and add that a failed checker probe leaves a version's checkers on Claude.
  Verify: `git grep -n -F "counts failures" -- docs/decisions.md` exits 0.

## 4 — Converge's ways back

- [x] 4.1 **HALT CHECK** `skills/mflib/statuslog.py` has no `names_worker` yet.
  Verify: `git grep -n -e "def names_worker" -- skills/mflib/statuslog.py` exits 1.
- [x] 4.2 Add `names_worker(text)` to `skills/mflib/statuslog.py`, true when a halt's reason holds `worker exit <code>` or `timed out after` ([D6](design.md#d6)); add `test_names_worker_reads_a_workers_halt` to `tests/test_statuslog.py`.
  Verify: `uv run pytest tests/test_statuslog.py -k "names_worker" -q` exits 0.
- [x] 4.3 In `converge.py`, make `before_round(run)` true for a halt that `names_worker` in a run with no `verdicts` event and no grant mark; add `test_a_worker_halt_with_no_verdict_is_a_halt_before_round_1` to `tests/test_converge.py`.
  Verify: `uv run pytest tests/test_converge.py -k "worker_halt_with_no_verdict_is_a_halt_before_round_1" -q` exits 0.
- [x] 4.4 In `conduct.py`, add `_has_verdicts(runs, change)` beside `_run_started` and extend `_before_round` so `_rerun` and `_answered` read that halt as a rerun at `HEAD`; the `self.reruns` guard stays. Add `test_a_worker_halt_is_a_rerun_at_the_same_head`: stage `converge`, a second halt stays, a new run reads it again, a halt after a `verdicts` line stands.
  Verify: `uv run pytest tests/test_conduct.py -k "worker_halt_is_a_rerun_at_the_same_head" -q` exits 0.
- [x] 4.5 In `converge.py`, make `held` send a role whose file `read_findings` marks `its scope resolved` out once more through `dispatch(..., roles=[role])`, verify mode read from the role's station, stamping `fan-out — rescope — <role>: <why>` ([D7](design.md#d7)). Add `test_a_scope_that_misses_once_is_sent_out_again`; read `test_a_findings_file_is_read_by_its_fields` and edit what it expects of a first miss.
  Verify: `uv run pytest tests/test_converge.py -k "scope_that_misses_once" -q` exits 0.
- [x] 4.6 In `conduct.py`, make `converge_by_hand` read the version's models file for each checker's and the fixer's models and a checker's skip, its arguments over the file ([D8](design.md#d8)). Add `test_a_hand_converge_reads_the_models_file`: a file, an argument over it, no file; read `test_the_converge_command_runs_by_hand`.
  Verify: `uv run pytest tests/test_conduct.py -k "hand_converge_reads_the_models_file" -q` exits 0.
- [x] 4.7 In `skills/mf-converge/SKILL.md`, *Report, then stop*: a halt a worker's exit or timeout caused, with no verdict read, is run again by the conductor; a hand converge reads the models file.
  Verify: `git grep -n -F "verdict read" -- skills/mf-converge/SKILL.md` exits 0.

## 5 — The supervisor at the cap

- [x] 5.1 **HALT CHECK** `skills/mf-supervise/SKILL.md` names no re-plan parameter.
  Verify: `git grep -n -e "replan" -- skills/mf-supervise/SKILL.md` exits 1.
- [x] 5.2 In `conduct.py`, per [D9](design.md#d9): `Run.supervise` starts at a `cap reached` halt whose last line is `re-plan: <ids>` with a blocker sized `a design change`, under the switch, with no `replan.mark` and no security card held, passing `replan=yes` through `_supervise_prompt`. A taken amend writes the mark through `_write_state`, logs `supervise — <id>: decided · converge-halted · <sha7> · re-plan`, and `Run.closing` names ` · re-planned <ids>`.
  Verify: `git grep -n -F "replan.mark" -- skills/mf-ship/scripts/conduct.py` exits 0.
- [x] 5.3 Add `test_the_supervisor_re_plans_a_design_cap_once` to `tests/test_conduct.py`: a design-sized cap under the switch (amend taken, mark written, one amend round), a second cap, the same cap with no switch, a new run that meets the mark.
  Verify: `uv run pytest tests/test_conduct.py -k "supervisor_re_plans_a_design_cap_once" -q` exits 0.
- [x] 5.4 In `skills/mf-supervise/SKILL.md`, add *Parameter — `replan=yes`*: the conductor gives it alone at a design-sized cap, and the amend may then edit `design.md`'s `## Decisions` and `proposal.md`, once a version.
  Verify: `git grep -n -F "replan=yes" -- skills/mf-supervise/SKILL.md` exits 0.
- [x] 5.5 In `docs/decisions.md`, D61, under **Accepts**: the cap's one amend a version, marked by `replan.mark`, and the paths the amend and the settle take, per `0089·S2` and `0090·S1`.
  Verify: `git grep -n -F "replan.mark" -- docs/decisions.md` exits 0.
- [x] 5.6 In `THREAT_MODEL.md`, *Out of scope*, edit the supervisor sentence to name the spec delta, and at a design-sized cap `design.md`'s `## Decisions` and `proposal.md`, once a version; edit the settle sentence to name Markdown under `openspec/` and `docs/`, the living specs and `docs/decisions.md` among them. No path widens.
  Verify: `git grep -n -F "living specs" -- THREAT_MODEL.md` exits 0.

## 6 — The changelog rule, the wait and the records

- [x] 6.1 **HALT CHECK** `changelog` in `skills/mf-integrate/scripts/integrate.py` still halts a branch whose entries lack the base's.
  Verify: `git grep -n -e "do not hold" -- skills/mf-integrate/scripts/integrate.py` exits 0.
- [x] 6.2 In `changelog`, drop each base entry the branch's entries do not lead with from where the branch holds it, when a line of the default branch's released sections equals it ([D10](design.md#d10)). Add `test_changelog_drops_a_stacked_bases_released_entries` to `tests/test_integrate.py`; edit the `lacking` case of `test_changelog_keeps_the_branch_entries_above_the_released_sections` to exit 0, and add a case whose base entry no release holds, which still halts.
  Verify: `uv run pytest tests/test_integrate.py -k "drops_a_stacked_bases_released_entries" -q` exits 0.
- [x] 6.3 In `Run.take`'s `finally`, log `halt` with `final — needs <action> · <reason>` when the version's halt stands; add `halt: bool` to `wait_run`, ending at the first polled line holding `halt — final — needs`, printing `wait: halt — <id> · <reason>` and `status`, returning 1; add `--halt` to `main` ([D11](design.md#d11)). Add `test_wait_halt_ends_at_a_final_halt`: a final line, a halt a rescue still answers, a run's end; read `test_wait_ends_on_a_halted_run`.
  Verify: `uv run pytest tests/test_conduct.py -k "wait_halt_ends_at_a_final_halt" -q` exits 0.
- [x] 6.4 In `skills/mf-ship/SKILL.md`, name `wait --halt` where it names `wait`; in `skills/mf-integrate/SKILL.md`, name the changelog rule's dropped entries.
  Verify: `git grep -n -F "wait --halt" -- skills/mf-ship/SKILL.md` exits 0.
- [x] 6.5 In `docs/decisions.md`, add `### D88 · The line closes the halts it can` after D87, holding the worker-halt rerun, the rescoped verdict, the hand converge's models file, the changelog's dropped entries and `wait --halt`, with **Why**, **Accepts** and **Rejected** as its neighbours.
  Verify: `git grep -n -F "D88 · The line closes the halts it can" -- docs/decisions.md` exits 0.

## 7 — The rescope's one missing-file halt

- [x] 7.1 **HALT CHECK** `rescoped` in `skills/mf-converge/scripts/converge.py` still raises its own `<role>.md is missing` halt, a branch no run reaches: `dispatch` → `retried` already halts on a missing file through `_failed`, before `read_verdicts` runs.
  Verify: `git grep -c -F "is missing: its checker left no findings file" -- skills/mf-converge/scripts/converge.py` prints `skills/mf-converge/scripts/converge.py:3`.
- [x] 7.2 In `converge.py`, drop `rescoped`'s missing-file branch ([D7](design.md#d7)): `rescoped` returns `Verdict | None`, raising only on a malformed file, and `held` reads a file missing after its first read or after the rescope through its one existing `<role>.md is missing` halt, placed after the rescope. No behaviour changes.
  Verify: `git grep -c -F "is missing: its checker left no findings file" -- skills/mf-converge/scripts/converge.py` prints `skills/mf-converge/scripts/converge.py:2`.
- [x] 7.3 Keep `test_a_scope_missed_twice_halts_on_a_file_gone_or_malformed` in `tests/test_converge.py`: its gone case asserts the halt `retried` raises, its malformed case `rescoped`'s; edit it only if 7.2 turns it red.
  Verify: `uv run pytest tests/test_converge.py -k "scope_missed_twice or scope_that_misses_once or findings_file_is_read_by_its_fields" -q` exits 0.
