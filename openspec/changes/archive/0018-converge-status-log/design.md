# 0018-converge-status-log — design

**In one line:** a new `## The status log` section in `mf-converge` fixes the file, its shape and its events;
each step names the event it writes. Skill prose and one scan. **Verdict: feasible** ([why](#verdict)).

Motivation is in [proposal.md → Why](proposal.md#why). This page holds the decisions, the log's shape, and where
each event is written.

## Context

- `skills/mf-converge/SKILL.md` writes run artefacts under `.minions/findings/`: the frozen patch (Step 2) and,
  through the stations, the review and security files (Step 4). `## Never` forbids the conductor editing a
  findings file.
- `skills/mf-release/SKILL.md` Step 1 reads the review and security files at exact paths and never globs the
  directory, so a new file there is not read as a verdict.
- The parked runner writes `.minions/events.jsonl` and `status.json` from `orchestrator/status.py`.

### Terms

| term | means |
|---|---|
| **the status log** | `.minions/findings/<change-id>_status_log.md` |
| **an event** | one line: `HH:MM:SS · round N · <event> — <detail>` |
| **a run** | one invocation of `mf-converge`, opened by a `## Run N — <date time>` heading |

## Goals / Non-Goals

**Goals**

- Open one file and see what the loop is doing now, and what it did before.
- A stalled or dead run is visible: its top line is neither `halt` nor `done`, and its time is old.

**Non-Goals**

- A machine-readable stream, or a gate on the log.
- Logging from the stations or the fix station.
- `mf-build` and `mf-release`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | **The log lives at `.minions/findings/<change-id>_status_log.md`**, and it is not a findings file: no station writes it, `mf-release` never reads it, and the conductor's rule against editing findings files does not cover it | beside the files it narrates; gitignored with them | a tracked file; a file per round |
| <a id="d2"></a>**D2** | **Only the conductor writes it**, logging each dispatch and each return | one writer, no interleaving; the stations' detail is already in their findings files | each subagent logging itself |
| <a id="d3"></a>**D3** | **One line per event, newest on top, never edited.** The time comes from `date '+%H:%M:%S'` run through Bash, never written by hand. A new line is inserted directly under the latest `## Run` heading | a person reads the top first; a real clock makes a stale run visible | append at the bottom; a rewritten "Now:" block |
| <a id="d4"></a>**D4** | **A fixed event list**: `start` · `freeze` · `fan-out` · `verdicts` · `fix` · `verify` · `pickup` · `catch-up` · `backlog` · `halt` · `done` | the same words every run make runs comparable; free text drifts | free-form lines |
| <a id="d5"></a>**D5** | **Runs stack newest on top.** Each run opens `## Run N — <date time>` above the previous run; a catch-up round opens its own run, marked `· catch-up`. Its top line must be `halt` or `done` | a re-run keeps its history; the ending rule is how a dead run shows | overwriting the log each run |
| <a id="d6"></a>**D6** | **It replaces run events for the skills.** The parked runner keeps `events.jsonl` | the same question — where is this now — without an orchestrator call | making the skills call the orchestrator |

### The log's shape

```
# <change-id> — converge status

## Run 2 — 2026-09-28 10:04
10:21:40 · round 1 · done — converged in 1 round · 0 cards to backlog
10:09:02 · round 1 · verdicts — review clean · security clean
10:04:20 · round 1 · fan-out — review and security dispatched
10:04:12 · round 1 · start — base a1b2c3 · head d4e5f6 · 3 commits · 5 files

## Run 1 — 2026-09-27 14:02
14:31:00 · round 3 · halt — cap reached, R3 open
…
```

### Where each event is written

| event | written in | detail holds |
|---|---|---|
| `start` | Step 1, once the preconditions pass | base, head, commit count, files changed |
| `freeze` | Step 2 and Step 6's re-freeze | the range and its counts |
| `fan-out` | Step 3, Step 7 | the roles dispatched and the range they judge |
| `verdicts` | Step 5, after each read | each file's `verdict` and `open_blocking` |
| `fix` | Step 6, at dispatch and at commit | the ids sent; then the commit id and the gate's result |
| `verify` | Step 7 | the round and the range |
| `pickup` | Step 8 | the picked ids, or `none` |
| `catch-up` | `## Catch-up round` | the judged head and `HEAD` |
| `backlog` | Step 9 | the cards written, moot and cleared, by id |
| `halt` | wherever the skill halts | the reason, as reported |
| `done` | Step 10 | rounds used, cards to the backlog |

## Seams — what the tests hold

The skill is prose, so the seam is the text scan in `tests/test_skills.py`, with a `tmp_path` twin that plants
the breach.

| key | the scan checks |
|---|---|
| `sdd:converge-status:log` | `mf-converge` names `_status_log.md`, `newest on top`, and each event in [D4](#d4) |

## Dependencies

None.

## Risks / Trade-offs

- **The conductor forgets a line.** → The ending rule makes the worst case visible: a run whose top line is not
  `halt` or `done` is live or dead, and its time says which.
- **Inserting under a heading is an edit to the file.** → Only new lines are inserted; no existing line changes.

## Verdict

Feasible. One skill section, a line in each step, one scan. One phase: the section and the step lines cannot be
green apart.
