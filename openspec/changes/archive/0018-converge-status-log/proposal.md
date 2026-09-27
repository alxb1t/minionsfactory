---
version: v0.18
---

# 0018-converge-status-log — proposal

**In one line:** while `mf-converge` runs, the conductor writes one line per event to
`.minions/findings/<change-id>_status_log.md`, newest on top, so the human can open one file and see where the loop is.

| read | for |
|---|---|
| this page | why, and what changes |
| [design.md](design.md) | the decisions (`D1`…`D6`), the log's shape, and where each event is written |
| [tasks.md](tasks.md) | the build: one phase |
| [specs/sdd/spec.md](specs/sdd/spec.md) | one new requirement, held by a scan |

## Why

A running converge leaves nothing a person can read until it ends. The findings files change round by round, but
they say what the stations found, not what the loop is doing now. When a run stalls or dies, nothing shows it.

## What Changes

```
  conductor ── each dispatch, each return, each decision ──▶ .minions/findings/<change-id>_status_log.md
                                                              newest run on top · newest line on top
                                                              a run ends on `halt` or `done`
```

- **The status log.** One file per change, beside the findings files. Only the conductor writes it. See
  [D1](design.md#d1), [D2](design.md#d2).
- **One line per event, newest on top**, timed by `date`, never edited. See [D3](design.md#d3).
- **A fixed event list**, ending every run on `halt` or `done`. See [D4](design.md#d4), [D5](design.md#d5).

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `sdd`: the ADDED requirement below.

| requirement | what changes |
|---|---|
| Converge keeps a status log | new: `mf-converge` names the log's path, the event list, the newest-on-top order, and the `halt` / `done` ending |

## Impact

| area | files |
|---|---|
| skills | `skills/mf-converge/SKILL.md` |
| tests | `tests/test_skills.py` |
| dependencies | none |
| target repos | none to change. Their next converge writes the log |

## Not in this change

- **`mf-build` and `mf-release`.** `mf-build` already leaves `tasks.md` ticks and a commit per phase. Either gets a
  log when a run shows it is needed.
- **The parked runner's `events.jsonl`.** The runner keeps its own event stream ([D6](design.md#d6)).
- **Any gate on the log.** It is for a person to read; no station or release check reads it.
