# Proving evidence — `0006-teardown` phase 6

Copies of the reports the v0.6 proving runs and contract exercises produced, committed as evidence (R11). Each
lives for real at `<vault>/findings/teardown.md` in its own target's vault — these are snapshots, not the
running files, and the vault paths are deliberately absent.

| File | What it evidences |
|---|---|
| `minionsfactory_teardown.md` | **Proving run 1** — MinionsFactory against its own rubric. Round 2, `verdict: compliant`, 23/23. The resolution log carries round 1's three gaps and how each was closed. |
| `isekai_teardown.md` | **Proving run 2** — a real, un-onboarded target. Round 1, `verdict: gaps-found`, 8 open gaps and 4 criteria withheld under the absent-subject rule. |
| `exercise_degradation.md` | **Contract exercise 1** — a repo with no Python manifest. Proves `profile: none`, the not-assessed statement, `criteria_total: 16`, and that no toolchain gap is reported for an undetected profile (R4). |
| `exercise_seeded_rerun.md` | **Contract exercise 2** — a re-run against a report hand-seeded with two `fixed` entries. Proves `fixed → verified` for the claim that held and `fixed → open` with a rejected-fix log line for the one that did not, `round` 1 → 2, overwritten in place (R9). |

**Read-only was verified on every target**: `git status` byte-identical before and after, no untracked file
appeared, HEAD unchanged, and no command from any target's gate array was executed.
