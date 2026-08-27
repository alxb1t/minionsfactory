# Proving evidence — `0007-pm-side-process-standard` phase 5

**A4's claim:** the corrected planning line proves itself by rendering this change. It did — the full line ran
from the vault project dir and produced every artifact below. **The point of this record is the gaps it exposed**,
because a line that renders cleanly on its first real use has not been tested, it has been flattered.

The artifacts live at `<vault>/planning/v0.7/`; **the vault paths are deliberately absent**, as v0.6's proving
record established, because the repo is scanned for the operator's vault path until stage B retires that guard.

| Stage | Artifact | Outcome |
|---|---|---|
| `mf-order` | `<vault>/planning/v0.7/v0.7_pm_side_process_standard.md` | The PRD, already authored; revised across six gauge rounds |
| `mf-gauge` | `<vault>/planning/v0.7/v0.7_gauge.md` | **`clean` at round 6** — 4 blocking at round 1, then 1, 1, 2, 1, 0 |
| `mf-blueprint` | `<vault>/planning/v0.7/v0.7_design.md` | **`feasible-with-caveats`**, two caveats carried into `design.md` |
| `mf-forge` | this change directory | Four artifacts; the spec delta went from N-A to six capabilities |
| `mf-inspect` | `<vault>/planning/v0.7/v0.7_inspect.md` | **`clean` at round 3** — 2 blocking, then 1, then 0 |

## Gaps the run exposed — the requirements for the real skills

**1. `mf-forge`'s derived change id collides with a deliberately-kept one, and the only exit is a HALT.** The skill
derives `<name>` from the PRD's short name and halts on *some other `NNNN-*`*. This PRD had deliberately kept the
id `0007-pm-finds-repo` while its short name changed, so the first render could not start. Resolved by renaming
the directory and rewriting five commit trailers — but the skill offered no path other than stopping. **The
roadmap already parks the fix at `mf-execute` (v0.9): take the change id explicitly rather than inferring it.**
This run is evidence that the same argument applies to `mf-forge`.

**2. `mf-forge` says nothing about *when* a spec-delta removal may be authored, and the naive rendering is wrong.**
The first render wrote a complete `## REMOVED Requirements` block for the eleven vault-preflight scenarios. That
turned the gate **red immediately**: `collect_spec_keys` discards a REMOVED key from both the shipped and the
resolvable sets the moment the block exists, so eleven live test markers dangled. Authoring it later instead
orphans eleven shipped scenarios. The window is exactly one commit wide, and **nothing in the skill or the
conformance rubric mentions it** — it was caught by running the gate, not by the line. The repo's own history had
recorded the rule once, in a v0.5 commit message. A rendering skill should not depend on someone remembering a
commit message.

**3. `mf-forge` can render a `proposal.md` requirement that reaches no phase in `tasks.md`.** `mf-inspect` round 1
found two: **B7** (remove the vault grant from the untracked settings file) and **C2**'s README clause. B7 is the
one requirement in the whole change that **no automated check can catch** — the file is untracked, so it is
neither committed nor scanned — and it would have shipped with the grant live. Two documents in the same change,
one listing scope and one listing phases, drifted apart in a single render.

**4. `mf-gauge`'s scope drifts if the prompt lets it.** Round 1 found genuine PRD defects — carried acceptance
clauses mandating the opposite of the live text. Rounds 2–4 mostly enumerated *repo sites* that no requirement
owned. That is real work, but it is `mf-blueprint`'s and `mf-inspect`'s, not PRD readiness: the PRD says what and
why, the design says where. The gauge went looking there because the invoking prompt invited it to. **Requirement
for the real skill: the gauge's roots are the rubric's ten criteria, and the prompt should not widen them.**

**5. A rename is a removal plus an addition, and only the removal half needs a delta block.** `mf-inspect` round 2
caught a renamed scenario key whose old form would have orphaned. The fix generalised into a standing rule in
`tasks.md`'s preamble covering all three phases that remove keys. **Requirement: the conformance rubric should ask
this question directly** — every key the change stops using, is its removal actually rendered?

## What worked

The **producer → blind-checker** split did the work it exists for. Every blocking finding in this change came from
a fresh instance that had not seen the reasoning which produced the artifact — six gauge rounds and three inspect
rounds, each blind. Three of the five gaps above were found by a checker contradicting the producer, and two of
them (the unowned requirement, the orphaning rename) were defects a self-review would have been structurally
unlikely to see, because they are invisible from inside the document that created them.
