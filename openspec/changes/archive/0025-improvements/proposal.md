---
version: v0.25
backlog: [0024·N1, 0024·N2]
---

# 0025-improvements — proposal

**In one line:** friction found while running the line on real projects — the stations close in a few sentences
ending on `Next:`, the cut commits without asking, the release merges and pushes on one yes, and a HUMAN phase
hands the person a checklist of full commands.

| read | for |
|---|---|
| this page | why, and what changes |
| [design.md](design.md) | the decisions (`B1`…`B14`) and the text, word for word |
| [tasks.md](tasks.md) | the build: close-outs, the cut, the merge, the HUMAN checklist |

## Why

The operator does not read the stations' final reports: each is a wall of numbered blocks. Every cut stops for a
*"please commit"* that is almost always yes, and every release ends with the merge and the push typed by hand. A HUMAN phase
halts on prose — *"build `live/Dockerfile` … push them"* — and leaves the person to work out the commands.

## What Changes

```
  cut ──commit──▶ build ──▶ converge ──▶ release ──"merge and push?"──yes──▶ main + tag on origin
   │                │           │            │
   └────────────────┴───────────┴────────────┴──▶ ≤ 3 sentences, then `Next: <the next act>`
```

- **A close-out rule in all five skills:** at most three sentences, then `Next:`. A halt stays in full; a HUMAN
  halt is its checklist. See [B1](design.md#b1)–[B3](design.md#b3).
- **The cut commits without waiting,** except on a `## Dependencies` that is not `None.` or a self-check item it
  cannot meet. Starting `/mf-build` approves the `Verify:` commands. New decision **D38**; D7 and a principle's
  exception amended. See [B4](design.md#b4)–[B6](design.md#b6).
- **The release asks once, then merges and pushes:** `--no-ff` into the default branch, then the default branch and
  the tag to `origin`. It halts when the default branch moved. D17 amended. See [B7](design.md#b7)–[B10](design.md#b10).
- **A HUMAN phase carries commands:** the cut writes its sub-tasks as exact commands (`I14` extended), and the build
  halts with a checklist of `sh` blocks. See [B11](design.md#b11), [B12](design.md#b12).
- **Scans** in `tests/test_skills.py` hold each rule ([B13](design.md#b13)); the cards `0024·N1` and `0024·N2` are
  fixed ([B14](design.md#b14)).

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `sdd`: **ADDED** *Every station closes in a few sentences and names the next act* — the close-out sentence and
  `Next:` in each skill's report step.
- `sdd`: **ADDED** *The cut commits without waiting, unless it adds a dependency* — Step 9 commits; a dependency
  and an unmet self-check item still wait.
- `sdd`: **ADDED** *The release merges and pushes on the person's yes* — one question, `--no-ff`, a halt when the
  default branch moved, never `--force`.
- `sdd`: **ADDED** *A HUMAN phase is handed over as a checklist of commands* — `I14` names exact commands; the
  build's halt prints `sh` blocks.
- `sdd`: **MODIFIED** *The cut runs no check before the human reads it* — the build runs the checks once the
  human starts it, not after an OK at the cut.

## Impact

| area | files |
|---|---|
| skills | `skills/mf-bootstrap/SKILL.md`, `skills/mf-cut-change/SKILL.md`, `skills/mf-build/SKILL.md`, `skills/mf-converge/SKILL.md`, `skills/mf-release/SKILL.md` |
| tests | `tests/test_skills.py` |
| docs | `docs/decisions.md` (D7, D8, D17, D38), `docs/principles.md`, `README.md` |
| dependencies | none |
| target repos | none changed; their next run uses the new skills |

## Not in this change

- **A separate merge skill,** and the autonomous `mfa-*` skills: D26 keeps them untouched.
- **Pushing the version branch, or forcing a push.** The release pushes the default branch and the tag only
  ([B8](design.md#b8)).
- **A change to how converge or the release judge.** Only their reports and the release's last step change.
- **The `0023` gate-weakening cards.** They stay in the backlog.
