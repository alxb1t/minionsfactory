---
version: v0.35
backlog: [0038·N1]
---

# mf-ship

A new station, `mf-ship`, takes every cut version to the default branch unattended: each station runs as a fresh
agent process in its version's worktree, a script checks each from disk, and the release merges and pushes without
asking.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements.

## Why

The pilot (v0.33.1 + v0.34) proved worktrees and integration, and cost the person three checkouts and a dozen
commands run in an order the line already knew. Once versions are planned and cut, everything after is the line's:
the person wants to hand the cut versions over and find them on `main`, the change-impact pages ready to read.

## What Changes

- **`mf-ship`**, run in the primary: builds and converges every open version in parallel, then integrates, runs the
  catch-up round and releases them one at a time in cut order.
- **`skills/mf-ship/scripts/conduct.py`**, a stdlib `uv` script: the stage of each version from disk, a check per
  stage, the run log, and the loop that starts one agent process per station.
- **`mf-release` takes `merge=yes`**: the conductor's yes, given by starting `mf-ship`; a hand-edit flag halts it
  before the merge. Its close-out names the worktree removed, kept or refused (`0038·N1`).
- **`mf-cut-change` writes its model suggestion** to `.minions/models/<change-id>.toml`, which `mf-ship` reads.
- **`mf-integrate` marks a red gate** on disk, so a halted integrate is told apart from an interrupted one.
- **Decisions:** D3, D17 and D41 amended; D47 added.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *The release merges and pushes on the person's yes* — MODIFIED: `merge=yes` stands for the yes; a hand-edit
    flag halts before the merge; the close-out names the worktree's outcome.
  - *Model suggestions use exposed capabilities* — MODIFIED: the cut writes the suggestion to the run directory.
  - *The integrate station merges the default branch into the next version* — MODIFIED: a red gate leaves a marker.
  - *The ship station takes cut versions to the default branch* — ADDED.
  - *The ship station judges every station from disk* — ADDED.
  - *A halt stops the ship run, and a re-run resumes* — ADDED.

## Impact

Adds `skills/mf-ship/` (the skill and `scripts/conduct.py`) and `tests/test_conduct.py`. Changes
`skills/mf-release/SKILL.md`, `skills/mf-cut-change/SKILL.md`, `skills/mf-integrate/SKILL.md`,
`tests/test_skills.py`, `docs/decisions.md`, `AGENTS.md`, `CONTRIBUTING.md`, `README.md` and `docs/README.md`.
The [delta](specs/sdd/spec.md) is folded by release.

Dependencies: none. The gate recipe stays unchanged. Running `mf-ship` needs an agent CLI on `PATH` — `claude` or
`codex` — set up by the operator.

## Not in this change

Planning and the cut stay the person's. Self-answered grilling, cloud and nightly runs, retries after a halt, gate
resources per target and a width setting wait for a run that needs them. Workers act under an allowlist (Claude
Code) or the workspace-write sandbox (Codex), never with prompts bypassed — a guardrail, not a containment. The
bootstrap still declares no `Worktrees:`.
