---
bump: minor
debt: [0097·R1, 0097·R5, 0097·R6, 0097·S4, 0097·S5, 0101·S8, 0100·R2, 0094·S7, 0094·S8, 0114·R3, 0114·R5, 0100·R1, 0114·R6, 0117·R1, 0089·R4, 0102·R2, 0105·R6, 0108·R10, 0098·R1, 0113·R1, 0114·R2, 0116·R1, 0086·R3, 0089·R5, 0089·R6, 0091·R2, 0096·R2, 0099·R2, 0099·R6, 0104·R5, 0111·R5, 0113·R2, 0114·R4, 0115·R4, 0100·R3, 0100·S6, 0100·S7, 0095·S3, 0103·S2, 0100·S4, 0101·R7, 0114·R7]
---

# Debt paydown 3a

The debt from 75 cards to about 15: what later versions made moot is settled, the small fixes and this line's ideas are paid, in two versions split by file.

Reading map: [design](design.md) holds the decisions, the evidence for each card closed without code and the tests; [tasks](tasks.md) its phases.

## Why

The debt grew past its watch with each version, and no open card blocks. Later versions made some cards moot, the prose standard closed a class of them wontfix, and the rest are one-line fixes outside `skills/mf-ship/scripts/conduct.py`. Paying them now keeps the backlog metric moving down and lets a later version take the design-sized cards alone.

## What Changes

- The cards whose premise is gone or whose class closed wontfix are listed in `debt:`, each with its Still true? output in [design](design.md).
- Prose and archive cards are corrected in place: the archived designs and proposals of earlier changes, `docs/decisions.md`, `CHANGELOG.md`, `skills/mf-release/SKILL.md`, `skills/mf-build/SKILL.md`, `skills/mf-cut-change/SKILL.md` and `AGENTS.md`.
- `THREAT_MODEL.md` records that a security card is known by the category its checker writes, and a plugin gap in *Known gaps*.
- `scripts/corpus.py` skips an input a case's `shape` does not match, and refuses a linked case folder.
- `review_metrics.py` reads `$NAME` from the command's own assignments, books operator work to the session's own repo and counts only agent tasks as workers.
- `cut_check.py` decides a new row `V6`: a `Verify:` needle a later sub-task removes.

Requirements the delta touches:

- MODIFIED *A reader of run data has a corpus case*: a case may hold a `shape`, and a linked case folder stops the run.
- MODIFIED *The review-metrics station books the person's planning and operator work from session transcripts*: `$NAME`, the transcript's `cwd` and the session's own repo.
- MODIFIED *A cut's mechanical steps are scripts*: the row `V6`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: the corpus, review-metrics and cut-script requirements above.

## Impact

- `scripts/corpus.py`, `scripts/corpus.toml`, `tests/test_corpus.py`.
- `skills/mf-review-metrics/scripts/review_metrics.py`, `tests/test_review_metrics.py`.
- `skills/mf-cut-change/scripts/cut_check.py`, `tests/test_cut_check.py`, `skills/mf-cut-change/SKILL.md`.
- `tests/test_bundle.py`, `tests/test_plan_check.py`, `tests/test_conduct.py`.
- Read for each premise check, never edited: `skills/mf-ship/scripts/conduct.py`, `skills/mf-converge/SKILL.md`, `skills/mf-converge/scripts/plan_check.py`.
- `skills/mf-release/SKILL.md`, `skills/mf-build/SKILL.md`, `AGENTS.md`, `THREAT_MODEL.md`, `CHANGELOG.md`, `docs/decisions.md`.
- `openspec/specs/sdd/spec.md`, folded from the delta at release.
- The archived changes `openspec/changes/archive/0086-ship-fixes-3/design.md`, `openspec/changes/archive/0086-ship-fixes-3/proposal.md`, `openspec/changes/archive/0091-cut-halts/proposal.md`, `openspec/changes/archive/0096-codex-ready/design.md`, `openspec/changes/archive/0099-stacked-builds/proposal.md`, `openspec/changes/archive/0104-codex-limits/design.md`, `openspec/changes/archive/0111-sandbox-tmp/design.md`, `openspec/changes/archive/0113-plan-review-diet/design.md` and `openspec/changes/archive/0115-plan-metrics/design.md`.

## Not in this change

- The design-sized cards: 0107·S1, 0114·S3, 0111·S1, 0112·S2, 0108·S1, 0109·S1, 0068·S3, 0060·S6, 0062·S1, 0089·S2, 0090·S1, 0104·S3, 0116·S2, 0065·R8, 0111·R3 — a conductor-hardening version.
