# Halts alone — design

Each halt below gets a route the line takes alone, or a rule that keeps it from happening; the rest of a run is left as it is. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The conductor (`skills/mf-ship/scripts/conduct.py`), converge (`skills/mf-converge/scripts/converge.py`) and integrate
(`skills/mf-integrate/scripts/integrate.py`) halt a version on causes a rule can answer. Each halt below waited for a
person at `8ca85458`, with the cause read from disk: a rescue's amend refused for a trailer, a gate red on a loaded
machine, a Codex checker that never wrote a file, a worker's exit with no verdict read, a verdict one file short, a hand
converge on the host's default model, a cap whose blocker is the plan's, a stacked base's entries already released.
Q-numbers cite the settled decisions of the brief; the repo's own decisions are `D<n>`.

```
a halt ──▶ has a route? ─┬─ yes ─▶ the run takes it, logs it, goes on
                         └─ no ──▶ the version stops for the person (as today)
```

## Goals / Non-Goals

- Goals: each route below, each with a test red before its edit; one `wait --halt` command that ends at a halt nothing answers.
- Non-Goals: the refusal of a `**HUMAN` phase; new fields of the run log; a notification feature; a change to the release's gate runs.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | Under the switch the rescue's decided amend is taken with or without `Decided-by: rescue` | Q14: correct amends were refused for the trailer alone | keeping the trailer a condition |
| [D2](#d2) | Without the switch a refused amend is reset off `HEAD` when every commit past the start has a `Rescue:` trailer and the tree was clean, and logged `reset` | Q14, Q53, C1, C2: a refused commit left at `HEAD` is the next worker's base; a commit with no trailer is the person's | a reset that drops a person's amend or the build's own changes |
| [D3](#d3) | A red conductor gate read under a load at or over the cores waits, at most 1,800 s, then runs once more | Q16, Q53: 0136 halted twice on `timeout=1` tests that pass alone | a load budget that fails the gate |
| [D4](#d4) | A Codex checker that exits non-zero twice before a completed turn runs on Claude, its result `fallback: codex failed` | Q17, Q34, Q53: 0143 halted on `model_not_found` with the fallback ready | telling a limit from a failure in the conductor |
| [D5](#d5) | A failed Codex checker probe marks Codex not ready for the version, whose checkers start on Claude | Q17, Q51: 0140 waited on a probe that wrote no file, with the fallback ready | a second probe |
| [D6](#d6) | A converge halt a worker's exit or timeout caused, with no `verdicts` line, reads as a rerun | Q43: 0143's halt had no way back | a retry of the halted round inside converge |
| [D7](#d7) | A verdict that misses the freeze's scope sends its checker out once more | Q49: 0144's halt closed only by an amend that restarted the round | a halt at the first miss |
| [D8](#d8) | `conduct.py converge` by hand reads the models file, its arguments over it | Q44: 0143's hand converge ran on Opus for $10.85 | a flag for the file |
| [D9](#d9) | Under the switch the supervisor may amend a design-sized cap's plan once a version, marked in the run directory | Q45, Q50, Q53: the plan is what to fix, and the cap's rescue only diagnoses | a grant past a design-sized cap |
| [D10](#d10) | The changelog rule drops a stacked base's entries the default branch holds released | Q18: isekai's 0198 stopped on entries already released | a halt for every lacking entry |
| [D11](#d11) | `wait --halt` ends, exit 1, at a version's final halt line | Q19: one background command replaces the watching agent | a notification |
| [D12](#d12) | D60, D61, D76 and the threat model are edited where they live; D88 is added | A7; Q50, Q53 | prose in this file alone |

### D1

`_amend` in `conduct.py` takes a commit that changes a decision, under the switch, when it is one amend with a `Rescue:`
trailer, and reads `Decided-by: rescue` no longer. It returns `(sha, "", True)` as before, so the log, the closing line and
`report` name it decided. `mf-rescue` still asks for the trailer; a `### D<n>` body is a decision, said in its text.

### D2

`Run.rescue` resets after a refused amend when `before` is an ancestor of `HEAD`, the tree was clean when the rescue
started and is clean at the reset, and every commit past `before` carries a `Rescue:` trailer. The reset is `git reset -q --hard
<before>`, logged as a `reset` event `rescue commit <sha7> dropped: <why>` before the halt's line. A commit with no `Rescue:` trailer reads as the person's
([D60](../../../docs/decisions.md)), and a tree with other changes holds the build's work: both stay (the cutter's C1, C2).

### D3

`_run_gate` reads the 1-minute load right after a red gate, through `load_average` and `CPUS` of `plan_check.py`, which
`_load_wait` loads with `runpy.run_path(str(PLAN_CHECK))`: the load read is the plan check's. At or over `CPUS` it logs `wait — gate · load <n> over
<cores> cores`, polls every `LOAD_POLL` seconds up to `LOAD_WAIT` (1,800), logs `wait — gate · load <n> · <seconds>s`, and
runs the gate once more; a green rerun is the result, a red one and a load that never fell leave the red. The wait is
inside `_run_gate`, so the repair's rerun and the dropped simplify's rerun are separate calls, each with its own wait.

### D4

`Run.checker` counts a Codex run that exits non-zero, not killed by its deadline, with `tokens_of` None, a completed turn
lacking, as a failure beside a usage limit. A second such end runs the checker on `_shadow`'s Claude models, as the limit's second does today; a shadow checker stops with
` · stopped by a codex failure` instead and falls back nowhere (the cutter's C3). `Checked.fallback`
becomes `bool | str`: `True` stays the usage limit's, and the string `codex failed` is a failure's; `converge.py`'s `_spent` writes
`fallback: codex failed` for the string. D76's wording changes: the checker call counts failures and tells no limit
from a failure.

### D5

`probe_checker` returns False with no halt for a version whose plan gives Codex to its checkers alone; `Run` keeps
`codex_off`, the changes marked, and `codex_ready` is False for a marked change. The run logs `codex — <id>: probe failed ·
its checkers run on Claude`. `codex_ready` and `probe_for` read `codex_off` before they probe, and `probe_for` caches no
`refused` reason for the failure. A version with a station of its own on Codex halts on the failed probe as before.

### D6

`skills/mflib/statuslog.py` gains `names_worker`, true for a halt whose reason holds `worker exit <code>` or `timed out
after`. `conduct.py`'s `_rerun` and `converge.py`'s `before_round` read a halt that names a worker, in a run whose status log
holds no `verdicts` line, no `verify: halt` and no grant, as a halt before round 1. The existing once-a-run guard
(`self.reruns`) keeps the second halt a halt; a new run and `rejoin` read it as a rerun.

### D7

`held` in `converge.py` sends a role whose file `read_findings` marks `its scope resolved` out once more through `dispatch`
with `roles=[role]`, on the role's station, stamping `fan-out — rescope — <role>: <why>`, and reads the file again; a second
miss raises the halt as before.

### D8

`converge_by_hand` reads, per role and for the fixer, `_models` and the skip of the version's models file through the
helpers a run reads its plan with; an argument replaces the file's value for its role, and a missing file or role takes the
executor's default as before.

### D9

`Run.supervise` starts the supervisor at a `cap reached` halt whose last halt line is `re-plan: <ids>` with an open blocker sized `a design change`,
under the switch and with no `replan.mark` in the change's folder of the run directory, passing `replan=yes` in the prompt.
A taken amend writes the mark, logs `supervise — <id>: decided · converge-halted · <sha7> · re-plan`, and the stage reads
`converge`, amended, one amend round, no grant spent. `Run.closing` names ` · re-planned <ids>`. `mf-supervise` takes the
parameter `replan=yes`, and may amend `design.md`'s `## Decisions` and `proposal.md` then. A security card, a second cap and
a standing mark stay the person's. `THREAT_MODEL.md`'s supervisor and settle sentences state the paths the code takes.

### D10

`changelog` in `integrate.py` drops each base entry the branch's entries do not lead with from where the branch holds it
when a line of the default branch's released sections equals it; one the default branch does not hold halts as today.

### D11

`Run.take`'s `finally` logs `<id> · halt — final — needs <action> · <reason>` when the version's thread ends with a halt
standing. `wait_run(cwd, halt=True)` reads each polled line, and the first `final` line ends the wait: it prints `wait:
halt — <id> · <reason>` and `status`, exit 1. `main` adds `--halt` to the `wait` command.

### D12

`docs/decisions.md` is edited: D60 and D61 where the amend and the re-plan change them, D76 for its wording, and D88 · The line closes the halts it can,
after D87, holds D6, D7, D8, D10 and D11. `THREAT_MODEL.md` is edited where cards `0089·S2` and `0090·S1` name. The release deletes those cards.

## Tests

Each test sits at the lowest layer that can fail; no end-to-end run is added. No test is deleted or merged, and a test the change turns red is edited by its task.

Base counts, each from `git grep -c "^def test_" -- <file>`:

- `tests/test_conduct.py` prints `289`; `tests/test_converge.py` prints `79`.
- `tests/test_integrate.py` prints `23`; `tests/test_statuslog.py` prints `34`.

| layer | file | tests added |
|---|---|---|
| unit | `tests/test_statuslog.py` | `test_names_worker_reads_a_workers_halt` |
| unit | `tests/test_converge.py` | `test_a_scope_that_misses_once_is_sent_out_again`, `test_a_scope_missed_twice_halts_on_a_file_gone_or_malformed`, `test_a_worker_halt_with_no_verdict_is_a_halt_before_round_1`, `test_a_codex_failure_fallback_is_named_in_the_verdicts_line` |
| integration | `tests/test_conduct.py` | `test_a_decided_amend_needs_no_trailer_under_the_switch`, `test_a_refused_amend_is_reset_off_head`, `test_a_gate_red_under_load_waits_and_runs_again`, `test_a_codex_checker_that_fails_twice_runs_on_claude`, `test_a_failed_checker_probe_leaves_the_checkers_on_claude`, `test_a_worker_halt_is_a_rerun_at_the_same_head`, `test_a_hand_converge_reads_the_models_file`, `test_the_supervisor_re_plans_a_design_cap_once`, `test_wait_halt_ends_at_a_final_halt` |
| integration | `tests/test_integrate.py` | `test_changelog_drops_a_stacked_bases_released_entries` |
| end-to-end | none | none: no browser shows any of it (T1) |

Each new `test_conduct.py` test runs the conductor against `fake_worker.py` or `fake_codex.py`, as its neighbours do (T2). Three
carry `@pytest.mark.slow`, which `make check` skips (T1): `test_a_refused_amend_is_reset_off_head` (11.73 s),
`test_the_supervisor_re_plans_a_design_cap_once` (37.97 s) and `test_a_failed_checker_probe_leaves_the_checkers_on_claude`.
No other added test runs over 5 s.

## Dependencies

None.

## Risks / Trade-offs

- A rerun of a worker's halt starts converge from round 1, which spends a round a halted run had begun; the halt carries no verdict, so none is lost.
- `git reset --hard` on a refused amend is the conductor's own, in the version's tree, on a tree it read clean (D2).
- The load wait holds a version's thread for 1,800 s at most; the gate it waits on takes longer on a loaded machine.

## Verdict

Ready to build, in the phases of [tasks](tasks.md). Each phase ends on a green `make check`; the last closes the records.
