---
bump: minor
beside: [0103-fewer-rounds]
debt: [0097·S2, 0097·S3, 0097·S6]
---

# Codex limits

A Codex usage limit stops neither the run nor a converge: the run reads Codex's own limit data, sends a checker to Claude until
the reset, and records what each Codex spawn cost in plan quota and tokens.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

One operator session at 99% of the Plus 5-hour window stopped a whole run at its probe, a Claude-only version included
([design](design.md#context), F1). A mailbox checker that meets the limit fails converge, and a rescue then runs on a halt
D53 says needs the person (F3). Nothing records what a Codex spawn costs in quota, and a mailbox checker's findings read
`model: unknown` and `tokens unavailable` (F7). A Codex worker in a linked worktree cannot write that tree's index (F9).

## What Changes

- **The probe** — a usage limit at the probe is no refusal: the run logs `codex limited until <time>` and goes on. Only a
  version or a queued cut with a station on Codex halts, alone.
- **The limit data** — the reset and the headroom come from Codex's rollout file, found by the log's `thread_id`, the
  `try again at` text as a fallback. A primary window at 90% or more counts as a limit until its reset.
- **The mailbox fallback** — a Codex checker that is limited, or meets the limit, runs on Claude on converge's model and
  effort until the reset. A reset at most 15 minutes away, inside converge's remaining time, is waited for. A converge halt
  that names a usage limit gets no rescue and no supervisor.
- **The record** — the answer names `fallback: codex usage limit` and the checker's tokens; `conduct.py` stamps a mailbox
  findings file's `model:` and `tokens:`; each Codex spawn's log ends with its share of the 5-hour and weekly windows, which
  the run metrics sum; `prices.toml` gains the fitted Claude rows.
- **The linked worktree** — each linked worktree's gitdir is a Codex writable root; the config guard reads each linked
  worktree's `config.worktree`; the Codex probe runs `git write-tree` in a scratch linked worktree.
- **The debt** — a served checker gets only what is left of converge's time (`0097·S2`); an answer names the request it
  answers (`0097·S3`); the threat model's mailbox entry says what a request can still do (`0097·S6`).
- **The record of decisions** — D76; D47, D51, D67 and D68 amended; `THREAT_MODEL.md`; `skills/mf-ship/SKILL.md` and
  `skills/mf-converge/SKILL.md`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *The ship station judges every station from disk* — MODIFIED: the Codex probe writes a linked worktree's index; a usage
    limit at the probe follows the new requirement.
  - *A halt stops only its version, and a re-run resumes* — MODIFIED: a failed probe stops the run, save one a usage limit
    stopped.
  - *A station's executor comes from the models file* — MODIFIED: the start probe's usage limit halts only the versions with
    a station on Codex; a Codex checker that meets its limit falls back.
  - *A worker's reach stops at the repository* — MODIFIED: each linked worktree's gitdir is a Codex writable root; the
    config guard reads each `config.worktree`.
  - *A halted version rejoins a live run* — MODIFIED: a joining version's probe stopped by a usage limit halts only the
    versions with a station on that executor.
  - *A converge checker on another host runs through the mailbox* — MODIFIED: the answer's form, the request id and
    converge's remaining time.
  - *A Codex usage limit halts only what runs on Codex* — ADDED.
  - *A Codex checker falls back to Claude while Codex is limited* — ADDED.
  - *A Codex spawn records its share of the plan's windows* — ADDED.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-ship/SKILL.md`, `skills/mf-converge/SKILL.md`,
`skills/mf-converge/references/worker.md`, `skills/mf-review-metrics/prices.toml`, `scripts/metrics/run.py`,
`metrics/catalogue.toml`, `docs/decisions.md`, `THREAT_MODEL.md`, `tests/fake_codex.py`, `tests/fake_worker.py`,
`tests/test_conduct.py`, `tests/test_metric_scripts.py` and `tests/test_review_metrics.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

- Dollar prices for Codex: Codex is plan quota here, and D67 rejects list prices written by the cut.
- A Codex station's own fallback: a station on Codex still halts its version.
- A usage subcommand: Codex CLI 0.163.0 has none.
- Debt `0097·S4`, `R5`, `R6` and `S5`: their code is read, not changed.
