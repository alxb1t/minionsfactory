# Conductor guards — tasks

The test case each guard of the conductor lacks, then `W5`'s clause. Decisions: [design](design.md).

## Progress

- [x] 1 — The sandbox's lists · moderate
- [ ] 2 — The push guard and the remote call · hard
- [ ] 3 — Npm and processes · moderate
- [ ] 4 — W5's clause · moderate

## 1 — The sandbox's lists

- [x] 1.1 In `tests/test_sandboxed.py`, add `test_the_deny_lists_are_literals`. It asserts `conduct["SECRETS"]`, `conduct["TOKENS"]` (holding `"GITHUB_TOKEN"`), `conduct["NETWORK"]` and `conduct["HOOKS_OFF"]` each equal a literal tuple of the entries at `skills/mf-ship/scripts/conduct.py:248-271` and `:327-331` ([D1](design.md#d1)). Leave the loops over the lists as they are.
  Verify: `git grep -n '"GITHUB_TOKEN"' tests/test_sandboxed.py` prints the literal line.

## 2 — The push guard and the remote call

- [x] 2.1 In `tests/test_conduct.py`, add `def _unmerged_release(root, tag)` after `_released`. It makes `_released`'s branch, its recorded head through `conduct["_record_release"]`, its `chore(release): <tag>` tip and its annotated tag, stops before the merge, and returns the head and the tip.
  Verify: `git grep -n 'def _unmerged_release' tests/test_conduct.py` prints the definition.
- [x] 2.2 Add `test_a_release_merge_that_adds_a_file_is_not_pushed` after `test_a_release_merge_no_run_made_is_not_pushed`: a `--no-ff` merge of a recorded release's tip that adds a file of its own. It expects `conduct["_foreign_commit"](root, base, "main")` to raise `Stop` matching `no run's release` ([D2](design.md#d2)).
  Verify: `uv run pytest tests/test_conduct.py -q -k adds_a_file` exits 0.
- [x] 2.3 Add `test_a_merge_on_a_recorded_head_with_another_subject_is_not_pushed`: a side commit on a recorded head, empty, subject `feat: side`, tagged `v0.9.0`, merged `--no-ff`. Same expectation.
  Verify: `uv run pytest tests/test_conduct.py -q -k another_subject` exits 0.
- [x] 2.4 Add `test_a_tip_no_tag_names_is_not_pushed`: a tip on a recorded head named `chore(release): v0.9.0`, with the tag `v0.9.0` moved to the head and not on the tip, merged `--no-ff`. Same expectation.
  Verify: `uv run pytest tests/test_conduct.py -q -k no_tag_names` exits 0.
- [x] 2.5 Add `test_an_octopus_with_a_recorded_release_is_not_pushed`: one `--no-ff` merge of `main`, then that release's tip, then an empty side commit on the recorded head, in that parent order, the release's build commit empty too. Same expectation.
  Verify: `uv run pytest tests/test_conduct.py -q -k octopus` exits 0.
- [ ] 2.6 In `test_a_key_set_after_the_refusal_reaches_nothing`, add a step after the planted keys, the decoy bare repo made before it: within a `monkeypatch.context()` that sets the module's `_urls` to return `conduct["_urls"](root)` as read before the plant, set `url.<decoy path>.pushInsteadOf` to the origin's path in the primary's config, refresh `conductor.git_state`, run `conductor.push_left((0,))`, and assert the decoy bare repo holds no ref; then unset the key, with the real `_urls` back for the test's later steps ([D3](design.md#d3)).
  Verify: `git grep -n 'pushInsteadOf' tests/test_conduct.py` prints the plant.

## 3 — Npm and processes

- [ ] 3.1 In `test_a_manifest_is_judged_by_the_rows_of_the_cut`, loop over the literal `("dependencies", "devDependencies", "optionalDependencies", "peerDependencies")` in place of `conduct["DIRECT"]`. Before the `_land` of the `@vitejs/plugin-vue` row, add a `devDependencies` step that expects the unapproved line ([D4](design.md#d4)).
  Verify: `git grep -n '"peerDependencies"' tests/test_conduct.py` prints the literal.
- [ ] 3.2 Add `test_a_claim_naming_a_low_group_signals_nothing`, after `test_a_stale_claim_is_cleared`. `active/0` and `active/1` each hold a start time the fake `ps` confirms, with `_register` naming an executor; `os.killpg` is a recorder, as `os.kill` is in `test_stop_ends_a_live_run`. `conduct["_clear"](active)` records no call ([D5](design.md#d5)).
  Verify: `uv run pytest tests/test_conduct.py -q -k low_group` exits 0.
- [ ] 3.3 In `test_a_stacked_dependent_resets_and_merges_back`, after the `mf.race` step, set `core.pager` in the primary's config and refresh `run.git_state`. Expect `run.reset_stack(version)` to raise `Stop` matching `could name a program` and `marks` to stay at `stacked`; then unset the key and refresh.
  Verify: `git grep -n 'core.pager' tests/test_conduct.py` prints the plant.
- [ ] 3.4 In `test_a_grant_buys_one_round`, before the grant that records, write `dirt.txt` in the primary, expect `grant()` to return `(2, "run: cannot run — the primary's tree is not clean")`, with `started == []` and no `grants` file; then remove `dirt.txt`.
  Verify: `git grep -n 'dirt.txt' tests/test_conduct.py` prints the step.
- [ ] 3.5 Add `test_bounded_reads_only_a_regular_file_of_the_cap`: a FIFO, a file of `READ_BYTES + 1` bytes and a link to a regular file within the cap each read as `None` through `conduct["_bounded"]`; a file of exactly `READ_BYTES` reads whole. The FIFO read runs in a daemon thread joined with a timeout, and the test fails when the thread lives.
  Verify: `uv run pytest tests/test_conduct.py -q -k bounded_reads_only` exits 0.

## 4 — W5's clause

- [ ] 4.1 In `skills/mf-build/SKILL.md`, end the `W5` row's text with the clause "; a guard that is a conjunction has one case per conjunct, built so that only that conjunct can halt it", after "placed per `T6`" ([D7](design.md#d7)).
  Verify: `git grep -n conjunct skills/mf-build/SKILL.md` prints the `W5` row.
