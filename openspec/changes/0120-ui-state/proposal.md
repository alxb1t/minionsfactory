---
bump: minor
beside: [0118-debt-paydown-3a, 0119-debt-paydown-3b]
---

# ui · state

A read-only server projects every project's ship line into one state tree and streams it to a plain page.

Reading map: [design](design.md) holds the decisions, the state rules and the tests, [tasks](tasks.md) holds the
phases: projector, server, page, record, live check.

## Why

`conduct.py status` prints a stage per open version, with no why, no worker, no converge round and nothing about the
other projects. A person who runs several versions in several repos reads files to learn what runs, what halted and
what waits for them. Every fact is already on disk, so a viewer can read it without any station changing.

## What Changes

- **A new skill** `mf-ui` holds `scripts/viewer.py` and `page/index.html`. `/mf-ui` starts the server detached and
  prints its URL; `/mf-ui stop` ends it.
- **A projector**, `viewer.py project <primary>`, loads `conduct.py` by path and prints one project's state tree as JSON:
  each version's stage and why, phases with the worktree's ticks, converge's round, blockers and verdicts, workers,
  liveness, a state by fixed rules, **for you** rows, and the queue.
- **A server** reads each project in a child process the server kills past 10 s, serves `/`, `/events` and `/state` on
  `127.0.0.1` and refuses a foreign `Host`. `/events` streams each whole numbered state as server-sent events.
- **A page**, one HTML file with an inline script and style, no build step, sets every string as text.
- **A record**: decision [D81](design.md#d10), a bullet under *The repo reaches nothing outside itself*, a requirement
  beside review metrics', a `THREAT_MODEL.md` entry, and the README, `AGENTS.md`, docs map and `CHANGELOG.md` rows.
- **A corpus case**, `viewer`, runs the projector over this checkout's run directory.

Requirements the delta adds:

- **The viewer projects every ship line, read-only** — a child per project, a state by fixed rules, the routes, a
  `Host` check, a stream of whole numbered states, a page that sets text.
- **The viewer starts, is found and stops by files in its own state folder** — the pid, port and log, and nothing in a repo.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: the requirements above are added; none is modified or removed.

## Impact

- New: `skills/mf-ui/SKILL.md`, `skills/mf-ui/scripts/viewer.py`, `skills/mf-ui/page/index.html`,
  `tests/test_viewer.py`.
- Edited: `scripts/corpus.toml`, `docs/decisions.md`, `docs/principles.md`, `THREAT_MODEL.md`, `README.md`,
  `AGENTS.md`, `docs/README.md`, and the `sdd` spec through the delta. The build writes the changelog entries.
- No station, conductor script, makefile, gate or CI line changes. A pinned install exports `skills/`, so the skill
  reaches a machine with its release.

## Not in this change

- Vue, Vite, Node, `ui/`, any gate or CI line: `ui · prepare` and `ui · board`.
- Any station change (series Q55).
- Any write to a repo (series Q1); the phone and `tailscale serve`; keys, sheets, themes.
