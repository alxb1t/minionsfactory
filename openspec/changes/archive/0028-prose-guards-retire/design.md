# Prose guards retire — design

Retire the phrase scans under a new decision, keep the structural checks, and take the unbuilt autonomous design
out of the mandatory context. Verdict: ready to build. Scope is [the proposal](proposal.md); behaviour is
[the delta](specs/sdd/spec.md).

## Context

Premises were re-checked on `main` at `0979957` before the cut.

| evidence at the cut | implication |
|---|---|
| `grep -c "^def test_" tests/test_skills.py` prints `58`: phrase scans and structural checks, each with its twin | Retire by kind, not one by one ([D1](#d1)) |
| `T5` and `I16` map a removed test only to "the remaining test that carries its assertions" (`skills/mf-build/SKILL.md:55,251`; `skills/mf-cut-change/SKILL.md:160,203`; `skills/mf-converge/SKILL.md:478`) | A retirement has nowhere to map ([D2](#d2)) |
| Review's coverage-trace pass makes "a proof carried by nothing" `blocking` (`skills/mf-converge/SKILL.md:221-225`); generic review restates the trace (`skills/mf-converge/references/generic-review.md:23`) | This change's own converge would block it ([D2](#d2)) |
| `docs/principles.md:51,61,70-72,94,107,127` name retired tests; `test_every_test_a_principle_names_exists` (`tests/test_principles.py:35`) fails on a name that is gone | Repoint them in the phase that deletes the tests ([D2](#d2)) |
| `W3` (`skills/mf-build/SKILL.md:235`) asks a named test for every *only*, *never*, *nothing else* | Read literally, it would ask for the scans back ([D5](#d5)) |
| `openspec/specs/sdd/spec.md:5`: "each proved by a scan over the skill text"; most scenarios read *WHEN … scanned* | Behavioural scenarios, and a Purpose edit ([D3](#d3)) |
| OpenSpec 1.11.0 rejects a MODIFIED block that drops a current scenario by name (`validator.js:528`); REMOVED and ADDED under one title fails validation | Old scenario names stay; their bodies change ([D3](#d3)) |
| An OpenSpec delta cannot change a capability's Purpose | The build edits the living spec's Purpose line directly ([D3](#d3)) |
| `## The autonomous line` is `docs/decisions.md:330` to the end — 978 words of 3,764 (`sed -n '330,$p' docs/decisions.md \| wc -w`); `docs/autonomous.md` is 1,038 (`wc -w docs/autonomous.md`) | Mandatory reading for a line not built ([D4](#d4)) |
| Live references: `AGENTS.md:39`, `README.md:79`, `docs/README.md:20,26`, `docs/decisions.md:14`, `docs/principles.md:174-175` | Each is edited in the deleting phase ([D4](#d4)) |
| The latest tag is `v0.27.0`; no active change exists | Cut `v0.28`, `0028-prose-guards-retire` |

The design and D24–D35 were harvested, verbatim at `0979957`, to the planning side before the cut (D23).

## Goals / Non-Goals

**Goal:** skill prose can be reworded without editing a test, while every structural check a reader cannot do by
eye stays in the gate.

**Non-goals:** see [the exclusions](proposal.md#not-in-this-change). No skill is shortened here.

## Decisions

The grilling settled these choices; the build does not reopen them.

### D1

| id | decision | because | rejected |
|---|---|---|---|
| D1 | Retire the phrase scans; keep the structural checks | A scan proves a sentence exists, not that it is obeyed, and freezes the wording | Keeping every scan; retiring all of `tests/test_skills.py` |

**Kept**, with their helpers and constants: `test_the_cut_and_the_build_carry_the_same_contract_ids`,
`test_the_cut_and_the_build_carry_the_same_prose_rule_ids`,
`test_the_build_the_cut_and_converge_carry_the_same_test_rule_ids`, `test_only_converge_carries_the_card`,
`test_the_bootstrap_holds_its_template_tests_section`, `test_the_bootstrap_templates_cover_the_target_layout`,
`test_bundled_role_references_resolve`, and each one's twin; all of `tests/test_guardrails.py` and
`tests/test_principles.py`.

**Retired:** every other function in `tests/test_skills.py`, listed in [Tests](#tests), and each helper or
constant that only they use: `_GATE_RUNNERS`, `_gate_problems`, `_needle_problems`, `_named_twice_problems`,
`_both_name_problems`, `_planted_both_name_problems`, and the constants and `_*_problems` helper above each
retired test. The `minions.toml` half of the gate scan tests a retired word, which D37 already forbids.

### D2

| id | decision | because | rejected |
|---|---|---|---|
| D2 | New decision D42; `T5`, `I16` and the coverage-trace pass accept a test retired by a named decision; the principles name skill steps | Without it, this change's converge blocks its own deletion and `test_principles.py` fails | A carve-out for this change alone |

**D42**, added to `docs/decisions.md` after D41 in *Repo conventions*:

```
### D42 · Skill prose is held by review, not by phrase scans

**A skill's rules are held by its own text, the spec and review. A test over skill text checks structure a
reader cannot see by eye — the shared id tables agreeing, the card's one owner, bundled references resolving,
the bootstrap templates — never that a sentence exists.**

- **Why:** a phrase scan proves a sentence exists, not that a station obeys it, and it freezes the wording: no
  sentence can be reworded without editing a test, so skill text only grows.
- **Gave up:** the gate failing when a rule's sentence is deleted. Review reads the diff for it.
```

The overview line at `docs/decisions.md:14` adds `D42` after `D41` in *Repo conventions*.

**`I16`**, in `skills/mf-build/SKILL.md:55` and `skills/mf-cut-change/SKILL.md:160` — the second cell:

```
before: … every test the change deletes or merges, each mapped to the remaining test that carries its assertions
        and scenario ids
after:  … every test the change deletes or merges, each mapped to the remaining test that carries its assertions
        and scenario ids, or to the decision that retires it (`retired by Dn`)
```

**`T5`**, in `skills/mf-build/SKILL.md:251`, `skills/mf-cut-change/SKILL.md:203` and
`skills/mf-converge/SKILL.md:478` — the same rule text in each:

```
before: … each removed test mapped to the remaining test that carries its assertions and scenario ids
after:  … each removed test mapped to the remaining test that carries its assertions and scenario ids, or to the
        decision that retires it
```

**The coverage-trace pass**, `skills/mf-converge/SKILL.md:222-223`:

```
before: It traces every removed assertion and scenario id to the test that runs it now, against `design.md`'s
        `## Tests` table. A proof carried by nothing, a scenario moved …
after:  It traces every removed assertion and scenario id to the test that runs it now, or to the decision in
        force that `design.md`'s `## Tests` table names as retiring it. A proof carried by neither, a scenario
        moved …
```

**Generic review**, `skills/mf-converge/references/generic-review.md:23`:

```
before: Trace removed tests against the design's Tests table, or state that the freeze removed no test.
after:  Trace each removed test to a carrying test or a retiring decision in the design's Tests table, or state
        that the freeze removed no test.
```

**D39**, `docs/decisions.md:313-314`: *"A test is deleted or merged only as the change's `## Tests` table names
it."* gains *", its proofs carried by a remaining test or retired by a named decision"* before the full stop.

**The principles**, `docs/principles.md:100-101` (*Never weaken the gate to pass*): *"its proofs carried by a
named remaining test"* becomes *"its proofs carried by a named remaining test or retired by a named decision"*.
Their *Held by:* lines, in the phase that deletes the tests:

| principle | the retired test it names | *Held by:* after |
|---|---|---|
| A checker is a fresh reader of a frozen diff | `test_the_release_checks_the_judged_head_and_converge_catches_up` | `mf-converge` Steps 2 and 3; `mf-release` precondition 7, which ships only the judged head. |
| `fixed` is a claim; only the checker writes `verified` | `test_converge_names_the_red_run_and_the_verify_check` | `mf-converge` Steps 6 and 7; Step 7 reopens a test fix with no red run. |
| Nothing reads as clean by being absent | the skip, release-halts and never-delete tests | `mf-converge` Step 5; `mf-release` precondition 4, which states a skip and halts on a lone patch or findings file; the *Never* lists of `mf-converge` and `mf-release`. |
| The gate is run, never summarized | `test_the_skills_run_make_gate_and_none_names_the_toml` | `mf-build` Step 1, `mf-converge` and `mf-release`, each printing `make -n gate` before its first `make gate`; `mf-release` precondition 1. |
| Never weaken the gate to pass | `test_converge_and_the_release_halt_on_an_unnamed_gate_recipe_change` | the list as it stands, without the test |
| State lives on disk | `test_build_converge_and_release_infer_the_one_active_change` | `mf-build` Step 1; the *Parameter — the change id* section of `mf-build`, `mf-converge` and `mf-release`, which reads the active change from git. |

### D3

| id | decision | because | rejected |
|---|---|---|---|
| D3 | Each requirement held by a retired scan keeps its SHALL text and old scenario names; the bodies become behaviour | OpenSpec keeps scenarios by name; D36 binds specs by review | Retitling the requirements; keeping the scan bodies |

The delta is written. Requirements held by a kept test keep their scan scenarios. Only *A test is deleted or
merged only as the design's table names it* and *Review judges test cost and traced coverage* change SHALL text,
for D2. The build edits the Purpose line of `openspec/specs/sdd/spec.md`, which the fold cannot reach:

```
before: The rules the `mf-*` skills hold, each proved by a scan over the skill text.
after:  The rules the `mf-*` skills hold. A scan proves the structure a reader cannot check by eye; review holds
        the rest (D42).
```

### D4

| id | decision | because | rejected |
|---|---|---|---|
| D4 | Delete D24–D35, `docs/autonomous.md` and each live reference; the ids stay a gap | A line not built is mandatory reading for every station | Moving them into `docs/autonomous.md` |

- `docs/decisions.md`: delete `## The autonomous line` to the end of the file; drop
  `· The autonomous line D24…D35` from the overview line.
- `docs/autonomous.md`: delete.
- `AGENTS.md:39`: `the map, the principles, the decisions, the autonomous design.` → `the map, the principles,
  the decisions.`
- `README.md:78-79`: drop `and [the autonomous design](docs/autonomous.md)`, joining the list with *and*.
- `docs/README.md`: delete the `autonomous.md` row; `What holds, what was chosen, and what is designed.` →
  `What holds, and what was chosen.`
- `docs/principles.md:174-175`: delete the *Known breaks* bullet.

D3, *one line of stations, conducted by a person or by an LLM*, stays: it names no deleted page or id. When the
autonomous line returns, it takes new decision ids.

### D5

| id | decision | because | rejected |
|---|---|---|---|
| D5 | `W3` covers claims of fact about code | Instructions and step-held principles are not claims a test proves | Leaving W3 literal |

`skills/mf-build/SKILL.md:235`, the rule cell:

```
before: **No *only*, *never* or *nothing else* without a named test** that fails when the claim stops being true
after:  **No *only*, *never* or *nothing else* in a claim of fact about code without a named test** that fails
        when the claim stops being true. An instruction (*never `git add -A`*), or a principle held by a named
        skill step, is not such a claim
```

### D6

| id | decision | because | rejected |
|---|---|---|---|
| D6 | Its own minor, before the skills are shortened; converge runs | The isekai audit's 10.8k-line 0013 produced 27 of converge's 60 misses; this deletes guards and edits converge's coverage rule | One version with the rewrite; a hand read |

## Tests

The gate stays offline. No test is added; the phrase scans and their twins are removed.

| layer | at cut | added | removed | proof |
|---|---:|---:|---:|---|
| Unit test functions | 62 | 0 | 44 | `uv run pytest -q --collect-only \| tail -1` prints `62 tests collected` at the cut, `18` after |
| Integration tests | 0 | 0 | 0 | — |
| End-to-end runs | 0 | 0 | 0 | — |

The removed tests, each mapped as `I16` and `T5` require — retired by D42, the scenario's body now held by review:

| removed test · its twin | scenario it held | carried by |
|---|---|---|
| `test_the_skills_run_make_gate_and_none_names_the_toml` · `test_the_gate_scan_reports_a_named_toml_and_a_missing_dry_run` | *Every gate-running skill names make gate, and no skill names the toml* | retired by D42 |
| `test_converge_names_the_one_backlog_and_the_pickup_sizes` · `test_the_converge_backlog_scan_reports_every_breach` | *Converge names the one backlog file and the pickup sizes* | retired by D42 |
| `test_the_release_reads_no_per_version_backlog_and_shares_the_key` · `test_the_release_backlog_scan_reports_every_breach` | *The release names no per-version backlog, and the paydown key is shared* | retired by D42 |
| `test_the_release_states_a_skipped_converge_and_converge_keeps_the_rule` · `test_the_converge_optional_scan_reports_all_three_breaches` | *The release names the skip, and the missing-file rule lives in converge only* | retired by D42 |
| `test_the_release_checks_the_judged_head_and_converge_catches_up` · `test_the_reviewed_head_scan_reports_both_breaches` | *The release compares HEAD with the judged head, and converge names the catch-up round* | retired by D42 |
| `test_converge_names_the_anchors_and_the_drift_tier` · `test_the_anchors_and_drift_scan_reports_every_breach` | *Converge and the method page name the anchors and the drift tier* | retired by D42 |
| `test_converge_names_the_repeat_rule` · `test_the_repeats_scan_reports_both_needles` | *Converge names the repeat rule* | retired by D42 |
| `test_converge_names_the_stale_claim_pass_where_it_runs_and_is_checked` · `test_the_stale_claim_scan_reports_a_single_mention` | *Converge names the stale-claim pass* | retired by D42 |
| `test_the_build_and_the_fix_station_name_consolidation` · `test_the_consolidation_scan_reports_both_needles_outside_their_sections` | *The build names the table, and the fix station never deletes* | retired by D42 |
| `test_converge_names_the_review_passes_where_they_run_and_are_checked` · `test_the_review_pass_scan_reports_a_single_mention_of_each` | *Converge names both passes where they run and where they are checked* | retired by D42 |
| `test_the_release_names_the_gate_clock` · `test_the_gate_clock_scan_reports_both_needles` | *The release names the line and the CI read* | retired by D42 |
| `test_converge_names_the_red_run_and_the_verify_check` · `test_the_red_run_scan_reports_both_breaches` | *Converge names the red run and the verifier's check* | retired by D42 |
| `test_converge_names_the_status_log_its_order_and_its_events` · `test_the_status_log_scan_reports_every_needle` | *Converge names the log, its order and its events* | retired by D42 |
| `test_build_converge_and_release_infer_the_one_active_change` · `test_the_inferred_id_scan_reports_every_breach` | *Build, converge and release each name the inference and its halts* | retired by D42 |
| `test_the_release_names_both_halts` · `test_the_release_halts_scan_reports_both_needles` | *The release names both halts* | retired by D42 |
| `test_converge_and_the_release_halt_on_an_unnamed_gate_recipe_change` · `test_the_recipe_halt_scan_reports_both_skills` | *Both stations name the dry-run check* | retired by D42 |
| `test_no_station_deletes_a_findings_file_or_the_patch` · `test_the_never_delete_scan_reports_both_skills` | *Both stations carry the rule* | retired by D42 |
| `test_the_cut_runs_no_check` · `test_the_runs_no_check_scan_reports_a_cut_that_runs_them` | *The cut's self-check runs no check* | retired by D42 |
| `test_every_skill_carries_the_close_out` · `test_the_close_out_scan_reports_a_missing_step_and_a_stray_needle` | *Each skill's report step carries the close-out rule* | retired by D42 |
| `test_the_cut_commits_without_waiting` · `test_the_cut_commits_scan_reports_a_cut_that_waits` | *The cut's show step commits without waiting* | retired by D42 |
| `test_the_release_merges_and_pushes_on_a_yes` · `test_the_merge_scan_reports_every_needle` | *The release names the merge and its guards* | retired by D42 |
| `test_a_human_phase_hands_over_a_human_checklist` · `test_the_human_checklist_scan_reports_every_breach` | *Both skills require commands, and the build prints them* | retired by D42 |

Row count: `grep -c '| retired by D42 |$' openspec/changes/0028-prose-guards-retire/design.md` prints `22`.

## Dependencies

None.

## Risks / Trade-offs

- **A deleted rule no longer turns the gate red** → D42 gives this up; review's read of the diff and its
  stale-claim pass look for it, and v0.29 adds a rule map.
- **Scenario names stay scan-worded** → OpenSpec keeps scenarios by name; a later change may retitle them as
  REMOVED and ADDED.
- **The ids D24–D35 stay a gap** → decisions are never renumbered; archived changes still cite them.
- **The coverage-trace pass changes in the change it judges** → the installed skill is a symlink into this
  checkout, so converge runs the branch's rule; review judges that edit like any other.

## Migration Plan

```
1 the retirement rule      D42 · W3 · I16 · T5 · coverage trace · D39 · a principle
  -> 2 the scans retire    tests/test_skills.py · the principles' Held by: · the spec's Purpose
    -> 3 the autonomous line leaves    D24–D35 · docs/autonomous.md · every live reference
      -> simplify -> converge -> release
```

Each phase ends on a green gate. The deletions are the last two phases (`A4`); rollback is a revert of their
commits. The release folds the delta.

## Verdict

Ready to build. Acceptance is a green gate with the structural checks kept, the named tests gone, the principles
naming only tests that exist, and no live page naming D24–D35 or `docs/autonomous.md`.
