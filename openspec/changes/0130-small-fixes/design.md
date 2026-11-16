# Small fixes — design

Copies of one rule that disagree are made to agree, the cap's missing case is added, and the port's failing real-sandbox case is replaced. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

A patch fixes what the line already does and adds no station, parameter, decision or requirement; it may modify a requirement to correct it (`AGENTS.md`). Every fix here corrects a place that states a rule other than the line's own. Each fix is read at `HEAD`, which holds `0128-platform-port`; `0129-queue-cap` edits other lines of `conduct.py`, `docs/decisions.md` and the skills `mf-ship` and `mf-plan`, and adds no requirement this change modifies.

| rule | where it disagrees today | the line's own |
|---|---|---|
| a ticked phase | `PROGRESS` of converge reads `[ xX]`; the conductor and integrate read `[ x]`; the build ticks `[x]` | `[ x]` |
| no `## Progress` list | converge passes; the conductor and integrate halt | halt |
| a change id | `CHANGE_ID` of the conductor and of integrate takes `0001-a-` and `0001--a`; the conductor's `SLUG` and D20 refuse them | no empty word |
| the debt lock's wait | converge waits 600 s; the release's text and the spec say 2 minutes | ten minutes |
| a blocking card cleared | converge passes `verified` and `accepted`; the release's text and the spec ask for `verified` | both |
| the run directory | `mf-build`, `mf-plan`, `mf-cut-change`, `mf-release` and `mf-integrate` name it with a command substitution; the conductor's shell rules forbid one; `mf-rescue` has the plain form | the plain form |
| the scripts converge loads | `mf-converge`'s text omits `evidence.py` and `gate_integrity.py` | the module map's row |

```
phase 1  converge, conductor, integrate     phase 3  the skills' text
phase 2  the release's text and the spec    phase 4  one case of cap_of
                                            phase 5  one real-sandbox case, one card
```

## Goals / Non-Goals

- **Goals:** each rule above has one reading; each correction has a case that fails before it; CI's macOS job has no case that can never pass.
- **Non-Goals:** a new station, parameter, decision or requirement; the bootstrap template's `Worktrees:` line; the other disagreements the audit lists; a move of any code.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | Converge reads `[ x]` and halts on a `tasks.md` with no `## Progress` list | the conductor and integrate already do, and `mf-build` ticks `[x]`; a capital tick is no tick | teaching the conductor and integrate `[ xX]` |
| [D2](#d2) | The conductor's and integrate's change id is the strict form | D20 and the conductor's `SLUG` refuse a trailing or a doubled hyphen | a looser `SLUG` |
| [D3](#d3) | The debt lock is waited for ten minutes everywhere | the code and the newer requirement say 600 s; a release behind a long debt write should wait, not halt | shortening converge's wait |
| [D4](#d4) | A blocking card `accepted` passes the release | converge judges cards, and a version converged clean must not halt at its release on the same card | making converge refuse `accepted` |
| [D5](#d5) | The run directory is named in the plain form, and a test holds every `SKILL.md` free of a command substitution | the conductor's shell rules forbid one, and a skill that tells a worker to run it is refused | a rule in prose alone |
| [D6](#d6) | `mf-converge`'s text names every script the module map's converge row names, and a test holds it | the text lags the code each time a script is added | a list of the loads in prose alone |
| [D7](#d7) | A resumed counted catch-up from round 2 with a blocker open at round 3 halts `cap reached` | the mutation proof of the station guards found `cap_of`'s `and` → `or` alive | none |
| [D8](#d8) | The real-sandbox case of the cut's hold goes; a case of a signal between siblings replaces it | the hold's walk reads `ps`, which Seatbelt refuses under any profile, so the case cannot pass | running the case without the walk |
| [D9](#d9) | Card `0107·S1` is listed under `debt:` and closed by a premise check, not an edit | the port paid it and left it on file; the release clears what a proposal lists | editing the card by hand |

### D1

`converge.py`'s `PROGRESS` becomes `^- \[([ x])\] (\d+) — `. `preconditions` halts `tasks.md has no ## Progress list` when `PROGRESS.findall` finds nothing, before it reads a box, in the words the conductor and integrate use. A `tasks.md` whose only ticks are `- [X]` has no box under the strict reading, so it halts the same way.

### D2

`conduct.py`'s `CHANGE_ID` is built from its own `SLUG`, `(\d+)-(` plus `SLUG`'s pattern plus `)`, so both groups stay and one rule says what a slug is. `integrate.py`'s `CHANGE_ID` becomes `(\d+)-([a-z0-9]+(?:-[a-z0-9]+)*)`. The helpers of `mf-cut-change` already take the strict form.

### D3

Only the text moves: the release's Step 4.6 says 10 minutes, and the spec's requirement says ten minutes. Converge's `LOCK_WAIT` stays 600 s.

### D4

The release's preconditions 2 and 3 read a blocking card as cleared when its Status is `verified` or `accepted`, as `converge.py`'s `blockers` does. `fixed` stays the producer's claim and halts.

### D5

The sentence of each of those skills becomes: `git rev-parse --path-format=absolute --git-common-dir`, then its parent's `.minions`. The scan reads each `skills/*/SKILL.md` for a `$(` followed by a lowercase letter other than `shell`: `$(git …)` is found, and the descriptions of what the rules forbid (`$(…)`, `$(shell …)`, `$(MAKE)`) are not. This is a rule that holds now, not a sentence that must exist, so [D42](../../../docs/decisions.md#d42--skill-prose-is-held-by-review-not-by-phrase-scans) and [D37](../../../docs/decisions.md#d37--tests-hold-what-is-true-now-nothing-tests-an-absence) stand; the person settled the scan at the plan.

### D6

`mf-converge/SKILL.md` names `evidence.py` and `gate_integrity.py` among the scripts converge loads. The scan reads the `names` cell of the `skills/mf-converge/scripts/converge.py` row of `docs/modules.md` and fails for each name the text does not hold.

### D7

The case plants a status log whose first event is a catch-up at round 2 counted, not its own count, and findings files of round 3 with a blocking card open. `cap_of` returns `CAP` for it, so `go_on` halts at once. With `or` for `and` it returns `round + 2` and the run goes on to a fix: the case is red under that change and green under `and`.

### D8

`test_the_cuts_hold_is_released_under_the_rule` goes. In its place one sandboxed command runs two processes: the first starts a `sleep` in a session of its own and prints its pid; the second, its sibling, signals that pid.

Under the profile's `(allow signal (target same-sandbox))` the signal is delivered, as the hold's release is. No `ps` runs. CI's macOS job sets `MF_REQUIRE_SEATBELT`, so the case fails there when Seatbelt cannot apply a profile.

### D9

`proposal.md` lists `0107·S1` under `debt:`, so the release deletes the card. The premise holds before the build: the profile's text in `skills/mflib/platform.py` holds `(deny signal)` and `(allow signal (target same-sandbox))`, and `tests/test_sandboxed.py` holds them as literals. A **HALT CHECK** in phase 5 checks it.

## Tests

The fixes are tested at the lowest layer that can fail. Each correction has a case red before it; none boots a browser, and no end-to-end run is added.

| test | file | layer | holds |
|---|---|---|---|
| `no progress` and `upper-case tick` cases of `test_a_converge_refuses_what_it_cannot_start` | `tests/test_converge.py` | integration | converge halts, naming `## Progress` |
| `test_a_change_id_has_no_empty_word` | `tests/test_conduct.py` | unit | `0001-a-` and `0001--a` are no change id; `0001-a-b` is |
| `test_next_names_no_version_whose_id_has_an_empty_word` | `tests/test_integrate.py` | integration | `next` calls such a branch not open |
| `test_no_skill_names_a_command_substitution` and its twin | `tests/test_skills.py` | unit | a planted `$(git …)` is found; the real skills hold none |
| `test_mf_converge_names_each_script_the_map_says_it_loads` and its twin | `tests/test_skills.py` | unit | a script missing from the text is named |
| `test_a_resumed_counted_catch_up_halts_at_round_three` | `tests/test_converge.py` | integration | `cap reached` at round 3 |
| `test_a_signal_between_siblings_is_delivered` | `tests/test_sandboxed.py` | integration | the signal rule's allow side, under the real sandbox |

- **Added, counted by** `git diff 0129-queue-cap --stat -- tests`: the table's rows; the parametrized cases add two.
- **End to end:** none. T1: each case is at the lowest layer that fails. T2: no end-to-end test reaches the state of a new one.
- **Removed:** `test_the_cuts_hold_is_released_under_the_rule`, mapped below.

| removed | carried by |
|---|---|
| `test_the_cuts_hold_is_released_under_the_rule` | `test_a_signal_between_siblings_is_delivered` carries its scenario, a signal to a process another call started in a session of its own, delivered under the rule; the awake tests hold the lines the hold prints |

## Dependencies

None.

## Risks / Trade-offs

- A capital tick no longer counts as a ticked phase for converge. `mf-build` ticks `[x]`, so no change in the line writes one.
- The substitution scan reads a pattern, not meaning: a `$(` followed by a lowercase letter in a new rule's prose is found, and is reworded or the pattern is widened with its reason.
- The real-sandbox case runs only where Seatbelt applies a profile. A worker's gate skips it, so its proof is CI's macOS job, read after the push; a red job is a follow-up patch, and the pin stays at its tag until it is green.
- The living spec holds the ten-minute wait and `accepted` only after the release folds [the delta](specs/sdd/spec.md); a search of `openspec/specs` for the old text is a release-time check.
- The cap's case is seen red under `cap_of`'s `and` → `or` by the build's worker, by hand, and the change put back.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): a phase and an id, the lock and the card, the prose, the cap's case, the port's case.
