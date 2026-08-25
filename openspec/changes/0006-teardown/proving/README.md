# Proving evidence — `0006-teardown` phase 6

Copies of the reports the v0.6 proving runs and contract exercises produced, committed as evidence (R11). Each
lives for real at `<vault>/findings/teardown.md` in its own target's vault — these are snapshots, not the
running files, and the vault paths are deliberately absent.

| File | What it evidences |
|---|---|
| `minionsfactory_teardown.md` | **Proving run 1** — MinionsFactory against its own rubric. Round 2, `verdict: compliant`, 23/23. The resolution log carries round 1's three gaps and how each was closed. |
| `isekai_teardown.md` | **Proving run 2** — a real, un-onboarded target. Round 1, `verdict: gaps-found`, 8 open gaps and 4 criteria withheld under the absent-subject rule. |
| `exercise_degradation.md` | **Contract exercise 1** — a repo with no Python manifest. Proves `profile: none`, the not-assessed statement, `criteria_total: 16`, and that no toolchain gap is reported for an undetected profile (R4). |
| `exercise_seeded_rerun.md` | **Contract exercise 2** — re-runs against a hand-seeded report, now over **three rounds**. Round 2 proved `fixed → verified` for the producer claim that held and `fixed → open` with a rejected-fix log line for the one that did not. **Round 3 (added in the review round-1 fix pass, R1) proves the fifth prior state:** a `verified` criterion that fails again returns to `open` with fresh evidence and a rejected-**regression** log line, and is **counted** — the transition the merge table had no row for. `round` 1 → 2 → 3, overwritten in place, one file (R9). |

**Read-only was verified on every target**: `git status` byte-identical before and after, no untracked file
appeared, HEAD unchanged, and no command from any target's gate array was executed.

> **That `git status` check was the human's verification harness around these runs, not a step the skill takes** —
> it was run outside the measurement, before and after, and its result is the evidence above. The security round-1
> fix pass (**S4**) **dropped `git status` from the skill's own read-only set**, because no criterion needs it and
> a repo carrying its own `.git/config` can make git run target-chosen commands (`core.fsmonitor`, `core.pager`, a
> `.gitattributes` clean filter) from it. **R6's acceptance is unaffected:** it was already performed and is
> committed here. A hand re-verification should use the hygiene form,
> `git -c core.fsmonitor=false -c core.pager=cat status`.
