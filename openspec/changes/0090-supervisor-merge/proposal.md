---
bump: minor
after: [0088-paydown-2, 0089-supervisor]
---

# Supervisor merge

The supervisor 0089 adds also settles an integrate note in spec or docs text, which the integrate station then commits naming
it, and reads the version's brief, which a passed cut now keeps.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

0087's run halted on an integrate semantic conflict over a requirement 0086 rewrote, and 0085's on an integrate flag with no
real conflict and a decision id taken while it waited: a supervising chat settled each, none with code, each a restart. 0089
builds the supervisor for build and converge halts alone (its brief's C1). The plan's intent, the brief, is gone once a cut
passes: its queue entry is unlinked and nothing else names it.

## What Changes

- **The brief kept** — a passed cut records its brief's path in the home queue's `briefs/<id>`, where no worker writes; the
  supervisor's prompt names it as `brief=<path>`. A version cut by hand has none.
- **The supervisor at an integrate note** — under the version's switch, after the rescue diagnosed an `integrating` halt on a
  semantic conflict or was spent on it, the supervisor resolves and stages the conflict in `openspec/` and `docs/` Markdown
  alone, writes `integrate.settled`, and leaves the merge and the note open. Never a red gate, code or a test, and one try
  an open merge, across runs.
- **Its check** — HEAD unmoved, the merge and the note standing, every index path it changed `openspec/` or `docs/` Markdown,
  nothing unstaged, nothing unmerged, the mark written during its run; logged `supervise — <id>: decided · integrating ·
  <tree>`, and the version goes on in the same thread.
- **Integrate commits it** — the run spawns `mf-integrate` `with settled=supervisor`, which commits the merge with
  `<path>: the supervisor` lines and gates it.
- **The record** — D45, D57 and D61 edited; `THREAT_MODEL.md`; `skills/mf-ship/SKILL.md`; `README.md`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A supervisor answers what the rescue leaves* — MODIFIED: an `integrating` halt on a semantic conflict starts it too; its
    settle check; the brief kept at a passed cut and named in its prompt.
  - *A semantic conflict is handed to the person with the merge open* — MODIFIED: under the switch the supervisor may settle
    the note first, and integrate's next run commits it.
  - *The integrate merge commit names every path it settled* — MODIFIED: `<path>: the supervisor` after a note the supervisor
    settled.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-supervise/SKILL.md`, `skills/mf-integrate/SKILL.md`,
`skills/mf-ship/SKILL.md`, `docs/decisions.md`, `THREAT_MODEL.md`, `README.md`, `tests/test_conduct.py` and
`tests/fake_worker.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

- The supervisor at an integrate red gate: a red gate is code, the person's.
- Pruning the home queue's `briefs/` records — when their count matters.
- A brief for a version cut by hand — when a hand cut has a place to name one.
- A watcher running all night (D47), and a push notification.
