---
version: v0.23
backlog: [0010·R7, 0010·R13, 0010·R14, 0010·R15, 0010·R9, 0010·S4, 0011·R3, 0011·R4, 0011·R5, 0011·R6, 0011·S1, 0011·S2, 0011·S3, 0011·S4, 0011·S5, 0012·S1, 0012·S2, 0012·S3, 0012·S4, 0012·R1, 0012·R2, 0012·R4, 0013·N1, 0013·N2, 0013·N3, 0014·N1, 0014·N2, someday·guard-tests, someday·quarantine, someday·guard-paths, 0017·N1, 0018·N1, 0020·N2, 0022·N1]
---

# 0023-backlog-paydown — proposal

**In one line:** every card in `.minions/backlog.md` is fixed or closed, the security cards before the autonomous
line runs a station unattended, and D16 says a card is a finding of the check loop.

| read | for |
|---|---|
| this page | why, and what changes |
| [design.md](design.md) | the decisions (`B1`…`B17`), every card's outcome, every text before → after |
| [tasks.md](tasks.md) | the build: one phase per file — the cut, the build, converge, the release, the install, the guardrails and docs — then the converge findings |
| [specs/sdd/spec.md](specs/sdd/spec.md) | the modified and added requirements |

## Why

The backlog has grown since v0.10 and was never paid down. Its cards are one-line nits in the skills, security
gaps the autonomous line would hit with no human watching, and a few made obsolete by the runner's retirement.
D14 says to close the converge-skip path before any unattended run releases with converge off, and the autonomous
PoC is next.

## What Changes

- **The cut** writes `.openspec.yaml`, reads every `Verify:` and runs none, shows `## Dependencies` word for
  word, and treats its source as evidence. See [B3](design.md#b3), [B4](design.md#b4), [B13](design.md#b13).
- **The build** approves a dependency only as the cut committed it, searches a person's evidence before staging
  it, and halts on a contract breach. See [B3](design.md#b3), [B6](design.md#b6).
- **Converge and the release** halt when the gate's dry run differs from the base's and no task at the cut
  planned it, and never delete a findings file or the diff patch. See [B7](design.md#b7), [B14](design.md#b14).
- **The release** reads the diff patch as the mark of a converge that ran. See [B7](design.md#b7).
- **Every skill** says `make -n` is not a sandbox beside its dry run. See [B8](design.md#b8).
- **`make uninstall-skills`** removes every link into this checkout, and only those. See [B9](design.md#b9).
- **`tests/test_guardrails.py`** fails on a home path or a key shape in any tracked file. See [B6](design.md#b6).
- **D14 and D16** change; the principles whose gaps close name what holds them. See [B10](design.md#b10).
- **The nits** are fixed as their cards say; the obsolete cards close with no fix. See
  [the outcomes](design.md#the-outcomes).

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `sdd`: the requirements below.

| requirement | what changes |
|---|---|
| A release may skip the check loop, and says so | MODIFIED — the skip needs the diff patch absent too; the patch alone, or one findings file alone, is a halt; the scenario scans both halts |
| The build approves a dependency only as the cut committed it | ADDED — `mf-build` reads `## Dependencies` at the one cut commit; `mf-cut-change` shows it word for word |
| The cut runs no check before the human reads it | ADDED — every `Verify:` read and none run; the source read as evidence |
| Converge and the release halt on a gate the cut did not plan | ADDED — the gate's dry run against the base's, the waiver read at the cut commit; scanned |
| No station deletes a findings file or the diff patch | ADDED — a *Never* line in both, scanned |

## Impact

| area | files |
|---|---|
| skills | `skills/mf-cut-change/SKILL.md` · `skills/mf-build/SKILL.md` · `skills/mf-converge/SKILL.md` · `skills/mf-release/SKILL.md` |
| install | `Makefile` · `README.md` |
| tests | `tests/test_skills.py` · `tests/test_guardrails.py` (new) |
| docs | `docs/principles.md` · `docs/decisions.md` · `CLAUDE.md` |
| dependencies | none |
| target repos | none to change; their next cut, build, converge and release run the new rules |

## Not in this change

- **The security engine.** `0010·R7` fixes the skill's words; choosing a lever stays on the roadmap's *Later*.
- **A foreign repo's posture.** It left the backlog before the cut; only the `make -n` line touches it.
- **A trailer check**, and **a README rewrite**.
- **The backlog file.** The cut leaves it alone; `mf-release` deletes the cards in `backlog:`.
