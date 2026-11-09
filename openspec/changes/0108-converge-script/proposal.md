---
bump: minor
after: [0107-sandbox-runner]
beside: [0106-cut-scripts]
debt: [0105·S2, 0095·S1, 0101·S4, 0103·R2, 0105·R7]
---

# Converge script

Converge's conductor becomes code: the loop, the reads and the debt run as `skills/mf-converge/scripts/converge.py`; only the
checkers, the fixer and the verify workers are LLMs.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

The conductor cost $2.91 of 0105's $12.04 converge and $2.34 of 0104's $14.13 ([design](design.md#context), F1), and judges almost
nothing: six places in a 561-line skill, the rest is git, frontmatter, scripts and status-log events (F4, F5). A script holds a
rule the same way each run, and `conduct.py` already judges converge from disk by exit code, status line and frontmatter (F3).
The sandbox runner of [0107-sandbox-runner](../0107-sandbox-runner/proposal.md) lets that script run the gate and the `Verify:`
lines outside an LLM's sandbox without running them bare ([D51](../../../docs/decisions.md#d51--a-worker-runs-in-an-os-sandbox-and-no-worker-pushes)).

## What Changes

- **The script** — `converge.py` holds the preconditions, the freeze, the dispatch, the verdict read, the loop, the pickup, a
  granted round, the catch-up and by-rule round, the resume and the debt write; `conduct.py` loads it in-process.
- **The fields** — a findings file gains `files`, `commits`, `passes` and `inconclusive`; a card gains `Amend: yes | no`; the
  fixer writes `fix.md` with a `plan check left:` line; each reference gains a `## Prompt` template.
- **The workers** — the script starts each through `Run.worker` and `Run.checker`, one log per worker named
  `<stamp>-converge-<role>-r<N>.log`; a failed worker gets one retry, a malformed file one rewrite worker.
- **The sandbox** — the gate, `gate_check.py`, `plan_check.py` and each **Still true?** command run under `sandboxed()`.
- **The retired** — the checker mailbox, the `checker` command, `CONDUCTOR`, converge's `STATION_TOOLS` and `CACHE_HOUR` rows,
  the fixer by grade, and H5: `surfaces.py` and its test.
- **The front** — `skills/mf-converge/SKILL.md` becomes a thin front for `conduct.py converge`.
- **The record** — D78 in `docs/decisions.md`, amending D3, D40, D47, D51, D53, D64, D68 and D70.
- **The debt** — the cards the frontmatter names closed, the mailbox cards cleared as moot ([design](design.md#d11)).

Requirements, in [the delta](specs/sdd/spec.md):

- *Converge's conductor is a script* — ADDED.
- *A converge worker is booked by its log name* — ADDED.
- *Converge keeps a status log* — MODIFIED: the script writes it; no mailbox answer, no by-rule security head.
- *A station's executor comes from the models file* — MODIFIED: converge's tokens come from each worker's log.
- *The converge fixer leaves the plan to the person* — MODIFIED: `Amend:` marks an amend card; `## Tests` and `## Dependencies`
  join the sections it never edits; `fix.md`.
- *Each release records its run* — MODIFIED: a converge worker's log counts in the converge stage.
- *Converge's workers take their models from the models file* — MODIFIED: no conductor model, the fixer always on `fix=`, a skip
  read once.
- *A shadow round 1 runs the other host's checkers* — MODIFIED: through the checker call, not the mailbox.
- *A Claude worker starts with its station's tools and nothing of the operator's* — MODIFIED: no converge row.
- *A converge conductor stubs a skipped checker* — MODIFIED: the script calls it; the judged-file refusal named.
- *A Codex checker falls back to Claude while Codex is limited* — MODIFIED: no mailbox.
- *A Codex spawn records its share of the plan's windows* — MODIFIED: a converge checker, not a mailbox checker.
- *A fix that reaches no surface takes its adversarial head by recomputation* — REMOVED.
- *A converge checker on another host runs through the mailbox* — REMOVED.
- *A converge worker's description names its role and round* — REMOVED.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *Converge's conductor is a script* — ADDED.
  - *A converge worker is booked by its log name* — ADDED.
  - The requirements listed above as MODIFIED or REMOVED.

## Impact

Adds `skills/mf-converge/scripts/converge.py`, `skills/mf-converge/references/fix.md`, `tests/test_converge.py`. Changes
`skills/mf-converge/SKILL.md`, its references, `open_cards.py`, `skills/mf-ship/scripts/conduct.py`, `skills/mf-ship/SKILL.md`,
`tests/fake_worker.py`, `tests/conftest.py`, `tests/test_conduct.py`, `tests/test_sandboxed.py`, `tests/test_skills.py`,
`tests/test_open_cards.py`, `tests/test_review_metrics.py`, `tests/test_metric_scripts.py`, `scripts/metrics/reading_set.py`,
`skills/mf-review-metrics/SKILL.md`, `skills/mf-bootstrap/templates/THREAT_MODEL.md.tmpl`, `docs/principles.md`, `skills/mf-review-metrics/scripts/review_metrics.py`,
`scripts/metrics/run.py`, `metrics/catalogue.toml`, `THREAT_MODEL.md` and `docs/decisions.md`. Deletes
`skills/mf-converge/scripts/surfaces.py` and `tests/test_surfaces.py`.

Dependencies: none. The gate recipe stays unchanged. `0106-cut-scripts` opens `conduct.py` too, in `_models_file`, `_table`,
`_models`, `PROMPTS` and `main`, as this change does: a merge there is a text merge ([design](design.md#risks--trade-offs)).

## Not in this change

- Tool evidence before the checkers: the *evidence step*, which runs when its own version is cut.
- Linux: bubblewrap waits for a run on Linux; with no `sandbox-exec`, converge halts (exit 2, `no OS sandbox`).
- A conducting LLM for a converge by hand: the front calls the script.
- The efficiency ledger's hypotheses H15 and H16, which the person records outside the repository.
