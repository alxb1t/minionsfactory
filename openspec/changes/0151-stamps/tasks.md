# Stamps — tasks

Phases: converge stamps the counts, a halted version keeps its slot, and the cut's row, the tag and `status` follow. Decisions: [design](design.md).

## Progress

- [x] 1 — Converge stamps the counts · hard
- [x] 2 — The slot · hard
- [ ] 3 — The cut's row, the tag and status · moderate

## 1 — Converge stamps the counts

- [x] 1.1 Add `def counted(text, values)` and `def count(folder, name, values)` to `skills/mflib/findings.py` per [D3](design.md#d3); `stamp` and `count` share one staged-write helper.
  Verify: `git grep -n -F -e "def counted(" -- skills/mflib/findings.py` exits `0`.
- [x] 1.2 Add `test_counted_sets_and_adds_the_keys`, `test_counted_leaves_a_stub_a_by_rule_file_and_no_frontmatter` and `test_count_follows_no_link` to `tests/test_findings.py`.
  Verify: `uv run pytest tests/test_findings.py -q -k "sets_and_adds or leaves_a_stub or count_follows"` exits `0`.
- [x] 1.3 Add `counted(context, frozen, roles, *, pickup=False)` to `skills/mf-converge/scripts/converge.py`; `dispatch`, `check` (`pickup=True`) and `rewrite` call it before the read, per [D2](design.md#d2).
  Verify: `git grep -n -F -e "counted(context" -- skills/mf-converge/scripts/converge.py` exits `0`.
- [x] 1.4 Delete `SCOPE_MISSED = "its scope resolved"`, the scope comparison, `rescoped` and `held`'s branch from `skills/mf-converge/scripts/converge.py` ([D4](design.md#d4)).
  Then `read_findings` takes no `freeze`: edit `read_verdicts`, `rewrite`, `_files` and the debt write's `unscoped` freeze to match.
  Verify: `git grep -c -F -e "SCOPE_MISSED" -- skills` prints nothing.
- [x] 1.5 In `tests/test_converge.py` delete `test_a_scope_that_misses_once_is_sent_out_again` and `test_a_scope_missed_twice_halts_on_a_file_gone_or_malformed`, and the `rescoped` calls.
  Edit `test_a_findings_file_is_read_by_its_fields` and each `read_findings` call to pass no `frozen` and hold no scope case.
  Verify: `git grep -c -F -e "rescoped" -- tests/test_converge.py` prints nothing.
- [x] 1.6 Add `test_a_miscounted_file_is_stamped_clean` (`files: 3` under a freeze that holds more files reads clean) and `test_a_file_with_no_count_keys_is_stamped` to `tests/test_converge.py`.
  Verify: `uv run pytest tests/test_converge.py -q -k "miscounted_file or no_count_keys"` exits `0`.
- [x] 1.7 Add `test_a_verify_round_is_stamped_with_the_fixs_head_and_the_round`, `test_a_pickup_check_is_stamped_and_keeps_its_round` and `test_a_stub_and_a_by_rule_file_are_not_stamped` to `tests/test_converge.py`.
  Verify: `uv run pytest tests/test_converge.py -q -k "verify_round_is_stamped or pickup_check_is_stamped or by_rule_file_are_not_stamped"` exits `0`.
- [x] 1.8 In `skills/mf-converge/references/worker.md` say `converge stamps` `head`, `round`, `files` and `commits`: take them out of the frontmatter block, and the link `#not-clean` and their check out of *The fields converge reads*, the stub's exemption of `files` and `commits` among them.
  Verify: `git grep -n -F -e "converge stamps" -- skills/mf-converge/references/worker.md` exits `0`.
- [x] 1.9 In `skills/mf-converge/references/worker.md` reword the clause `freeze, and halts` of *Not clean*: converge halts on a malformed file, not on a count; say so in the sentence on a one-file fix. Reword `checks these` of *Empty resolutions* to say converge runs the gate on HEAD and checks no count; keep *scope resolution failed*.
  Verify: `git grep -c -F -e "freeze, and halts" -- skills/mf-converge/references/worker.md` prints nothing.
- [x] 1.10 In `skills/mf-converge/references/verify.md` drop `head`, `round`, `files` and `commits` from both rewrite lists, and the `save in` clause on a pickup check's `round`.
  Verify: `git grep -c -F -e "save in" -- skills/mf-converge/references/verify.md` prints nothing.
- [x] 1.11 In `skills/mf-converge/references/verify.md` drop `write head: {head}` from the prompt's list of the fix diff.
  Verify: `git grep -c -F -e "{head}" -- skills/mf-converge/references/verify.md` prints nothing.
- [x] 1.12 In `skills/mf-converge/references/generic-conformance.md` drop `write head: {head}` from the prompt; keep `mode`. Reword `reviewed head` in the line on what `worker.md` owns.
  Verify: `git grep -c -F -e "{head}" -- skills/mf-converge/references/generic-conformance.md` prints nothing.
- [x] 1.13 In `skills/mf-converge/references/generic-adversarial.md` drop `write head: {head}` from the prompt; keep `mode`. Reword `reviewed head` in the line on what `worker.md` owns.
  Verify: `git grep -c -F -e "{head}" -- skills/mf-converge/references/generic-adversarial.md` prints nothing.
- [x] 1.14 In `tests/test_converge.py` edit `test_a_clean_round_converges_with_no_fix` to expect `` `mode: parallel` `` in each checker's prompt and no `head`.
  Verify: `uv run pytest tests/test_converge.py -q -k clean_round_converges_with_no_fix` exits `0`.
- [x] 1.15 In `skills/mf-ship/scripts/conduct.py` take `head` and `round` out of `FINDINGS_KEYS`, `"branch", "head", "reviewed", "round"` becoming `"branch", "reviewed"`, and reword its comment to match: no converge run stamps a probe's file.
  Verify: `git grep -c -F -e '"branch", "head"' -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [x] 1.16 In `docs/decisions.md` replace D88's sentence on a verdict whose scope misses the freeze with one saying converge stamps `head`, `round`, `files` and `commits`; drop the rescoped checker from its *Accepts* line.
  Verify: `git grep -c -F -e "scope misses" -- docs/decisions.md` prints nothing.
- [x] 1.17 In `THREAT_MODEL.md` say converge also stamps `head`, `round`, `files` and `commits` through the staged write that holds the conductor's `model:` and `tokens:`.
  Verify: `git grep -n -F -e "also stamps" -- THREAT_MODEL.md` exits `0`.

## 2 — The slot

- [x] 2.1 In `skills/mf-ship/scripts/conduct.py` change `if not live or self.stopped(change)` in `in_flight` to test `self.stopped("run")` alone per [D5](design.md#d5).
  Verify: `git grep -c -F -e 'not live or self.stopped(change)' -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [x] 2.2 In `tests/test_conduct.py` change `test_cap_counts_only_versions_at_a_station`: a live thread a halt names counts, an ended one and every thread under a run-wide halt do not.
  Verify: `uv run pytest tests/test_conduct.py -q -k cap_counts` exits `0`.
- [x] 2.3 Add `test_a_halted_version_keeps_its_slot_while_its_thread_lives` and `test_a_revived_version_finds_no_second_in_flight` to `tests/test_conduct.py`.
  Verify: `uv run pytest tests/test_conduct.py -q -k "keeps_its_slot or revived_version"` exits `0`.
- [x] 2.4 In `docs/decisions.md` reword the clause `runs, no halt names it` of D84: a version is in flight while its thread runs, its rescue and supervisor included; a final halt frees its slot.
  Verify: `git grep -c -F -e "runs, no halt names it" -- docs/decisions.md` prints nothing.

## 3 — The cut's row, the tag and status

- [ ] 3.1 Add `def row_v9` to `skills/mf-cut-change/scripts/cut_check.py` per [D6](design.md#d6), and `V9` to `ROWS` and to the rows `check` runs.
  Verify: `git grep -n -F -e "def row_v9" -- skills/mf-cut-change/scripts/cut_check.py` exits `0`.
- [ ] 3.2 Add `test_v9_halts_an_unquoted_exit`, `test_v9_holds_a_quoted_exit_and_the_word_in_prose` and `test_v9_reads_a_halt_check_task` to `tests/test_cut_check.py`.
  Verify: `uv run pytest tests/test_cut_check.py -q -k v9` exits `0`.
- [ ] 3.3 In `skills/mf-cut-change/SKILL.md` add `V9` once to the rows `cut_check.py` decides and once to the sentence on what a `Verify:` row settles.
  Verify: `grep -c -F -e "V9" skills/mf-cut-change/SKILL.md` prints `2`.
- [ ] 3.4 In `skills/mf-release/scripts/next_tag.py` list `git tag --list` with `--merged` the default branch per [D7](design.md#d7).
  Verify: `git grep -n -F -e "--merged" -- skills/mf-release/scripts/next_tag.py` exits `0`.
- [ ] 3.5 In `tests/test_next_tag.py` start each repository with `git init -b main`, and add `test_a_stray_local_tag_is_no_base`: `v0.9.0` on `main`, `v0.10.0` on a commit no branch holds, a patch is `v0.9.1`.
  Verify: `uv run pytest tests/test_next_tag.py -q` exits `0`.
- [ ] 3.6 In `skills/mf-release/SKILL.md` say `next_tag.py` takes the highest tag the default branch holds merged.
  Verify: `git grep -n -F -e "holds merged" -- skills/mf-release/SKILL.md` exits `0`.
- [ ] 3.7 In `_status_line` of `skills/mf-ship/scripts/conduct.py` append the reason `stage_of` returns, per [D8](design.md#d8), under `and stage in HALTS:`.
  Verify: `git grep -n -F -e "and stage in HALTS:" -- skills/mf-ship/scripts/conduct.py` exits `0`.
- [ ] 3.8 In `tests/test_conduct.py` update `test_status_reads_each_stage_from_disk`, `test_a_rerun_recovers_a_dead_release` and `test_a_release_cut_short_is_recovered` to the reason, and add `test_status_prints_a_tip_tagged_elsewhere_with_its_reason`.
  Verify: `uv run pytest tests/test_conduct.py -q -k "status_reads_each_stage or dead_release or release_cut_short or tagged_elsewhere"` exits `0`.
