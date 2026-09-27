---
version: v0.16
---

# 0016-backlog-in-repo — proposal

**In one line:** deferred work never leaves the repository. `mf-converge` fixes the small cards itself and writes
the rest to one backlog, `.minions/backlog.md`. The release stops reading it, and `mf-backlog-export` is deleted.

| read | for |
|---|---|
| this page | why, and what changes |
| [design.md](design.md) | the decisions (`D1`…`D9`), the new converge steps, and the before → after text |
| [tasks.md](tasks.md) | the build: one phase per station, in order |
| [specs/sdd/spec.md](specs/sdd/spec.md) | the requirements, each held by a scan |

## Why

Every release with deferred work needed a human to run `mf-backlog-export`, which wrote into a backlog outside the
repository. That backlog was hard to read, and the step blocked the release until someone ran it. The small items
in it were often one-line fixes the loop could have made while its context was fresh.

## What Changes

```
  before:  converge ──▶ .minions/<version>_backlog.md ──▶ mf-backlog-export ──▶ a backlog outside the repo
                          (any list line blocks release)     (human-invoked)

  after:   converge ──▶ pickup ──▶ .minions/backlog.md          release never reads it
                        fixes the   one file, one heading      a paydown change lists card ids;
                        small cards per change                 its release deletes them
```

- **Pickup.** When converge is clean with a round to spare, it fixes this run's non-blocking cards sized
  `one line` or `a test`, in one more fix-and-verify round. No human confirms the pick. See [D2](design.md#d2).
- **The repo backlog.** Every other non-blocking card goes whole to `.minions/backlog.md` under a heading for its
  change, with a change-qualified id. See [D1](design.md#d1), [D3](design.md#d3).
- **The release stops reading the backlog.** `mf-release`'s *No deferred work is left* precondition goes. See
  [D5](design.md#d5).
- **Paydown.** `mf-cut-change` writes a paydown change's card ids to `backlog:` in `proposal.md`. `mf-release`
  deletes those cards after the fold. See [D6](design.md#d6).
- **BREAKING — the export retires.** `skills/mf-backlog-export/` is deleted, along with the card-parity scan that
  held it equal to `mf-converge`. See [D7](design.md#d7).

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `sdd`: the ADDED and REMOVED requirements below.

| requirement | what changes |
|---|---|
| Converge keeps deferred work in one repository backlog | new: `mf-converge` names `.minions/backlog.md` and the pickup sizes, and never names a per-version backlog file |
| The release does not read the backlog | new: `mf-release` names no per-version backlog file, and it and `mf-cut-change` name the `backlog:` key |
| The card is defined in converge alone | new: `mf-converge` owns `## The card`, and no other skill carries one. It keeps the `sdd:backlog-cards:fields-agree` key ([D8](design.md#d8)) |
| The backlog export is named nowhere | new: no shipped code, prompt, skill or doc names `mf-backlog-export` |
| Converge and the export share one card shape | removed: only one skill carries the card now |

## Impact

| area | files |
|---|---|
| skills | `skills/mf-converge/SKILL.md` · `skills/mf-release/SKILL.md` · `skills/mf-cut-change/SKILL.md` · `skills/mf-backlog-export/` (deleted) |
| tests | `tests/test_skills.py` · `tests/test_conventions.py` |
| docs | `README.md` · `CLAUDE.md` · `docs/sdd.md` · `.gitignore` |
| dependencies | none |
| target repos | none to change. Their next converge writes `.minions/backlog.md`. Old per-version files are left for the human to delete |

## Not in this change

- **The parked runner.** `orchestrator/`, `prompts/` and `openspec/specs/release/` keep the per-version file that
  blocks the runner's release. This is a declared divergence between the runner and the skills ([D9](design.md#d9)). It closes
  when the runner resumes.
- **Moving the existing backlog in.** The human moves the items kept outside the repository into
  `.minions/backlog.md` by hand, after this release.
- **Older cards in pickup.** Pickup takes only this run's findings. Older cards wait for a paydown change.
- **`mf-build`'s input contract.** `mf-build` never reads `backlog:`, so the contract does not change.
