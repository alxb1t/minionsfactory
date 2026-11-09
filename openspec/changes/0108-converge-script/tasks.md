# Converge script — tasks

Build the settled [design](design.md), one phase at a time; each test step goes red before its code. `K` is
`skills/mf-converge/SKILL.md`, `W` is `skills/mf-converge/references/worker.md`, `C` is `skills/mf-ship/scripts/conduct.py`. `K`
stays as it is until phase 6: it is the behaviour [D3](design.md#d3) maps. Inside a phase a sub-task's `Verify:` is its own;
only the phase's end is green.

## Progress

- [x] 1 — The fields · hard
- [x] 2 — The script's start: preconditions, freeze, dispatch, verdicts · hard
- [x] 3 — The loop: fix, verify, pickup, grant, catch-up, resume · hard
- [ ] 4 — The debt, the halts and the report · hard
- [ ] 5 — `conduct.py`: the in-process call and the retirements · hard
- [ ] 6 — The front, the record and the metrics · hard

## 1 — The fields

- [x] 1.1 **HALT CHECK** The base stands as the design's [Context](design.md#context) reads it.
  Verify: `git grep -n -e '^def stage_of(' -e '^def _check_converge(' -e '^    def checker(' -e '^def serve_requests(' -e '^INTEGRATE = ' -- skills/mf-ship/scripts/conduct.py` prints a line for each.
- [x] 1.2 **HALT CHECK** [0107-sandbox-runner](../0107-sandbox-runner/design.md) is built under this branch: `sandboxed` stands.
  Verify: `git grep -n -e '^def sandboxed(' -e '^def _profile(' -- skills/mf-ship/scripts/conduct.py` prints a line for each.
- [x] 1.3 Extend `test_open_cards_refuse_what_they_cannot_read` in `tests/test_open_cards.py` as [the Tests table](design.md#tests)
  says: a Status in another case is judged folded; a word outside `open`, `fixed`, `wontfix`, `verified` and `accepted`, and a
  Status line under no title, exit 2 naming the card. Then fail closed in `open_cards.py`.
  Verify: `uv run pytest -q tests/test_open_cards.py` exits 0; `git grep -n 'casefold' -- skills/mf-converge/scripts/open_cards.py` prints a line.
- [x] 1.4 Edit `W` as [D2](design.md#d2) says: the frontmatter block gains `files`, `commits`, `passes` and `inconclusive`; the
  card table gains an **Amend** row after **Fix**; the amend-card paragraph keys on it, adds the fix-note exception and `## Tests`
  and `## Dependencies` to the sections the fixer never edits.
  Verify: `git grep -n -e '^files: <' -e '^commits: <' -e '^passes: \[' -e '^inconclusive: \[' -e '^| \*\*Amend\*\* |' -- skills/mf-converge/references/worker.md` prints a line for each.
- [x] 1.5 Write `skills/mf-converge/references/fix.md`: the fixer's rules moved from `K`'s Step 6 bullets, the `fix.md` report
  ending `plan check left: <subjects>` or `plan check left: none`, and a `## Prompt` block per [D2](design.md#d2).
  Verify: `git grep -n -e '^## Prompt' -e 'plan check left:' -- skills/mf-converge/references/fix.md` prints a line for each.
- [x] 1.6 Add a `## Prompt` block, with [D2](design.md#d2)'s placeholders, to `skills/mf-converge/references/generic-conformance.md`,
  `generic-adversarial.md` and `verify.md`, below `## The packet` where there is one.
  Verify: `git grep -l '^## Prompt' -- skills/mf-converge/references/` prints each reference named in this task and `fix.md`.

## 2 — The script's start: preconditions, freeze, dispatch, verdicts

- [x] 2.1 Add `test_the_output_goes_to_the_file_given` to `tests/test_sandboxed.py`; then the parameter `out=None` of `sandboxed` in
  `C`, annotated `out: TextIO | None = None`, per [D6](design.md#d6): each output line and the denial line to `out`, else to
  `sys.stdout` and `sys.stderr`.
  Verify: `uv run pytest -q tests/test_sandboxed.py` exits 0; `git grep -n 'out: TextIO | None = None' -- skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 2.2 Add `tests/test_converge.py` with a fake `host` fixture (`primary`, `trees`, `plan`, `worker`, `checker`, `sandboxed`) and
  `test_a_converge_refuses_what_it_cannot_start` and `test_the_freeze_writes_the_patch_the_bundle_and_the_debt_cards`, per
  [the Tests table](design.md#tests); then `skills/mf-converge/scripts/converge.py`, a module docstring and a docstring on each
  function (the gate's `D` rules), with `converge`, `preconditions`, `freeze` and
  the status log through `stamp.py`'s `main`, per [D1](design.md#d1) and [D3](design.md#d3).
  Verify: `uv run pytest -q tests/test_converge.py` exits 0; `git grep -n -e '^def converge(' -e '^def preconditions(' -e '^def freeze(' -- skills/mf-converge/scripts/converge.py` prints a line for each.
- [x] 2.3 Add `test_each_worker_prompt_is_filled_from_its_reference` and `test_a_findings_file_is_read_by_its_fields`; then
  `prompt` (each `## Prompt` filled, no placeholder left) and `read_verdicts` ([D2](design.md#d2)'s fields, one `verdicts` line per role).
  Verify: `uv run pytest -q tests/test_converge.py` exits 0; `git grep -n -e '^def prompt(' -e '^def read_verdicts(' -- skills/mf-converge/scripts/converge.py` prints a line for each.
- [x] 2.4 Add `test_a_clean_round_converges_with_no_fix` and `test_a_skipped_checker_is_a_stub`; then `dispatch` (a round's
  checkers in threads through `host.checker`) and `stubs` (`skip_stub.py` after each freeze), per [D4](design.md#d4).
  Verify: `uv run pytest -q tests/test_converge.py` exits 0; `git grep -n -e '^def dispatch(' -e '^def stubs(' -- skills/mf-converge/scripts/converge.py` prints a line for each.

## 3 — The loop: fix, verify, pickup, grant, catch-up, resume

- [x] 3.1 Add `test_a_blocker_is_fixed_verified_and_cleared`, `test_a_red_gate_after_a_fix_gets_one_more_pass_then_the_cap`,
  `test_the_cap_halts_with_the_open_blockers` and `test_plan_check_left_halts_amend_needed`; then `fix` (the fixer on `fix=` always,
  one more pass on a red gate or dirty tree, the re-freeze, `fix.md`), `verify` and `cap`.
  Verify: `uv run pytest -q tests/test_converge.py` exits 0; `git grep -n -e '^def fix(' -e '^def verify(' -e '^def cap(' -- skills/mf-converge/scripts/converge.py` prints a line for each.
- [x] 3.2 Add `test_round_one_pickup_rides_with_the_fix`, `test_a_pickup_check_runs_on_the_needed_role` and
  `test_a_granted_round_goes_one_past_the_cap`; then `pickup` and `grant`, per [D3](design.md#d3).
  Verify: `uv run pytest -q tests/test_converge.py` exits 0; `git grep -n -e '^def pickup(' -e '^def grant(' -- skills/mf-converge/scripts/converge.py` prints a line for each.
- [x] 3.3 Add `test_a_catch_up_judges_the_new_commits` and `test_a_merge_only_catch_up_is_by_rule`; then `catch_up` and `by_rule`
  (`replay` called as a function, per [D1](design.md#d1); a failure of it a worker round).
  Verify: `uv run pytest -q tests/test_converge.py` exits 0; `git grep -n -e '^def catch_up(' -e '^def by_rule(' -- skills/mf-converge/scripts/converge.py` prints a line for each.
- [x] 3.4 Add `test_a_run_resumes_from_its_status_log` (parametrized by the latest event) and
  `test_a_shadow_round_runs_the_other_host_and_drives_nothing`; then `resume`, `open_run` and `shadow`.
  Verify: `uv run pytest -q tests/test_converge.py` exits 0; `git grep -n -e '^def resume(' -e '^def shadow(' -- skills/mf-converge/scripts/converge.py` prints a line for each.

## 4 — The debt, the halts and the report

- [ ] 4.1 Add `test_the_debt_is_written_once_under_its_lock`, `test_a_still_true_command_runs_sandboxed_and_a_prose_card_goes_unchecked`,
  `test_an_amend_card_halts_the_debt` and `test_a_fixed_repeats_old_card_is_cleared`; then `debt` and `still_true` per
  [D7](design.md#d7), each command through `host.sandboxed`.
  Verify: `uv run pytest -q tests/test_converge.py` exits 0; `git grep -n -e '^def debt(' -e '^def still_true(' -- skills/mf-converge/scripts/converge.py` prints a line for each.
- [ ] 4.2 Add `test_a_failed_worker_gets_one_retry`, `test_a_malformed_file_gets_a_rewrite_then_a_debt_card` and the exit-2 cases of
  `debt_match.py` and `replay`; then `retried` (the one retry) and `rewrite` (the rewrite worker, then the debt card) per
  [D5](design.md#d5).
  Verify: `uv run pytest -q tests/test_converge.py` exits 0; `git grep -n -e '^def retried(' -e '^def rewrite(' -- skills/mf-converge/scripts/converge.py` prints a line for each.
- [ ] 4.3 Add `test_the_report_names_the_verdicts`; then `report`, and the module docstring that names each script `converge.py`
  loads or runs and the hand command of [D1](design.md#d1).
  Verify: `uv run pytest -q tests/test_converge.py` exits 0; `git grep -n 'conduct.py converge' -- skills/mf-converge/scripts/converge.py` prints a line.

## 5 — `conduct.py`: the in-process call and the retirements

- [ ] 5.1 Add `test_the_run_hands_converge_its_trees_and_sandbox`; bring `test_a_limited_checker_falls_back_to_claude` and the two
  renamed tests of [the Tests table](design.md#tests) to the new call, the second extended with a spent deadline and a timeout kill;
  then make `Run.checker` take `(change, station, table, cwd, prompt, deadline, effort)` and return a frozen `Checked`, per
  [D4](design.md#d4), and add `Run.trees` and `Run.sandboxed`, per [D1](design.md#d1).
  Verify: `uv run pytest -q tests/test_conduct.py -k "hands_converge"` exits 0; `git grep -n -e '^class Checked' -e '    def trees(' -e '    def sandboxed(' -- skills/mf-ship/scripts/conduct.py` prints a line for each.
- [ ] 5.2 Add `test_a_skip_is_read_once`; then `CONVERGE` beside `INTEGRATE`, its load in `Run.__init__`, and in `Run.advance` the
  call in place of the converge spawn and its mailbox, logging `spawn converge · script` and `finish converge`; drop converge's entry of
  `PROMPTS` and `_worker_clause`. Pass `Run.skipped.get(change, frozenset())`, never none, to `stage_of` and `_unjudged` as their new
  `skips` argument, per [D8](design.md#d8); `status` and `check` pass none.
  Verify: `uv run pytest -q tests/test_conduct.py -k "skip_is_read_once"` exits 0; `git grep -n -e '^CONVERGE = ' -e 'skips: frozenset' -- skills/mf-ship/scripts/conduct.py` prints a line for each.
- [ ] 5.3 Delete the mailbox from `C` as [D8](design.md#d8) lists, the `between` parameter of `work`, `Run.worker` and `Run.spawn`
  included; `_entries`, `_bounded` and `_place` stay. Delete `CONDUCTOR`, its branch in `_models`, the converge row of
  `STATION_TOOLS` and `"converge"` from `CACHE_HOUR`.
  Verify: `git grep -n -e 'def serve_requests' -e 'def _open_mailbox' -e '^def _worker_clause(' -e '^CONDUCTOR = ' -e '^    "converge": ("Bash"' -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [ ] 5.4 Add `test_the_converge_command_runs_by_hand`; then the `converge` subparser, its branch in `main` and its line in the
  module docstring of `C`, per [D1](design.md#d1).
  Verify: `uv run pytest -q tests/test_conduct.py -k "by_hand"` exits 0; `git grep -n -e 'args.command == "converge"' -e 'conduct.py converge' -- skills/mf-ship/scripts/conduct.py` prints a line for each.
- [ ] 5.5 Move the fake `sandbox-exec` fixture of `tests/test_sandboxed.py` to `tests/conftest.py` as `fake_sandbox_exec`, and give each fake repo of
  `tests/test_conduct.py` a `gate` recipe that succeeds, per [C5](design.md#c-rows). Rewrite `tests/fake_worker.py` to play one worker
  per role from the prompt's role line, keeping the retired whole-converge modes as per-role modes.
  Verify: `git grep -n -e 'fix-surfaces' -e 'surfaces' -- tests/fake_worker.py` prints nothing; `git grep -n 'def fake_sandbox_exec' -- tests/conftest.py` prints a line.
- [ ] 5.6 Find each test of `tests/test_conduct.py` that names a converge station call, a `"checker"` call or the mailbox with
  `git grep -n -e 'converge 0001' -e '"checker"' -e 'mailbox' -e 'surfaces' tests/test_conduct.py`; bring each to the new fake under its own
  name, and add `test_a_version_converges_with_no_conducting_worker` (slow), per the renames and removals of
  [the Tests table](design.md#tests).
  Verify: `uv run pytest -q tests/test_conduct.py` exits 0; `git grep -n -e 'converge 0001-todo and' -e 'mailbox' -- tests/test_conduct.py` prints nothing.
- [ ] 5.7 Delete `skills/mf-converge/scripts/surfaces.py`, `tests/test_surfaces.py`, the `_METRICS_SCRIPTS` entry of
  `tests/test_skills.py` naming `surfaces.py` and the two expected-list strings that name it; reword the lines of `docs/principles.md`
  that name `surfaces.py` and its test.
  Verify: `uv run pytest -q tests/test_skills.py` exits 0; `git ls-files skills/mf-converge/scripts/surfaces.py tests/test_surfaces.py` prints nothing; `git grep -n 'surfaces' -- docs/principles.md` prints nothing.

## 6 — The front, the record and the metrics

- [ ] 6.1 Cut `K` to the front of [D10](design.md#d10): the parameters, `conduct.py converge <change-id> [conformance=…] [adversarial=…] [fix=…] [grant=yes]`,
  what it prints, a pointer to `converge.py`'s docstring. In `tests/test_skills.py` the converge rows become `converge.py` and
  `../mf-ship/scripts/conduct.py`, and the expected lists and `_GATE_RUN_UNNAMED` change in step.
  Verify: `uv run pytest -q tests/test_skills.py` exits 0; `git grep -n 'conduct.py converge' -- skills/mf-converge/SKILL.md` prints a line.
- [ ] 6.2 Reword what the docs say of the conductor: `W`'s *Not clean*, *The verify pass* and the `model` and `tokens` lines
  of its frontmatter block name `converge.py` and no mailbox; `verify.md` and the `Held by` lines of `docs/principles.md` name
  `converge.py`, not Steps of `K`; `skills/mf-ship/SKILL.md` loses its mailbox sentences and gains the `converge` row in its command
  table; `skills/mf-review-metrics/SKILL.md` and `docs/principles.md` lose their mailbox words.
  Verify: `git grep -n -i -e 'mailbox' -e 'conduct.py checker' -- skills/mf-ship/SKILL.md skills/mf-converge skills/mf-review-metrics/SKILL.md docs/principles.md` prints nothing.
- [ ] 6.3 Edit `THREAT_MODEL.md` as [D10](design.md#d10) says — the `## Surfaces` intro, *Out of scope*'s fixer line, the mailbox
  lines — and the same intro in `skills/mf-bootstrap/templates/THREAT_MODEL.md.tmpl`.
  Verify: `git grep -n -i -e 'surfaces.py' -e 'mailbox' -- THREAT_MODEL.md skills/mf-bootstrap/templates` prints nothing.
- [ ] 6.4 Add D78 to `docs/decisions.md` and its index line, and edit D3, D40, D47, D51, D53, D64, D68, D70, D71 and D76 where they
  live, as [D9](design.md#d9) says.
  Verify: `git grep -n -e '^### D78 · The converge conductor is a script' -e 'checker mailbox' -e 'mailbox checker' -e 'mailbox role' -- docs/decisions.md` prints the D78 heading alone.
- [ ] 6.5 Point `converge-reading-set` in `metrics/catalogue.toml` at `AGENTS.md`, `W` and `fix.md`, with `scripts/metrics/reading_set.py`
  and its test in `tests/test_metric_scripts.py`.
  Verify: `uv run pytest -q tests/test_metric_scripts.py` exits 0; `git grep -n 'references/fix.md' -- scripts/metrics/reading_set.py` prints a line.
- [ ] 6.6 Add `test_review_metrics_books_a_worker_by_its_log_name` to `tests/test_review_metrics.py`; then book the log name
  `<stamp>-converge-<role>-r<N>.log` in `review_metrics.py`, the description path kept; count each such log in the converge stage in
  `scripts/metrics/run.py`, its test in `tests/test_metric_scripts.py` extended.
  Verify: `uv run pytest -q tests/test_review_metrics.py tests/test_metric_scripts.py` exits 0.
