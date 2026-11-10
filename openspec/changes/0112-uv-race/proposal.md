---
bump: patch
---

# uv race

Parallel versions of a run never race on what they share: converge builds no helper environment, a run builds each pinned
script's environment once and in sequence, and every shared resource has a named guard ([design](design.md#d3)).

Read [design](design.md) for the decisions and the audit, and [tasks](tasks.md) for the phases. This change has no spec
delta: no requirement changes ([design](design.md#d7)).

## Why

Versions of one run converge at once, each in its own thread. Each thread starts `uv run --script gate_check.py` with the
same `UV_CACHE_DIR`, so both build or remove the same script environment under `environments-v2/`. One halts on
`failed to remove directory …: Directory not empty`, then `Failed to spawn: python`. `test_a_rejoined_dependency_brings_its_chain_back`
failed about one run in four on 0110's tree, and 0110 needed a second gate run for its green ([design](design.md#context), F1, F5).

The gate's green record hides the race once a tree has passed. Each fix pass changes the tree, so each re-run gate draws it
again. A defect of the line, fixed before the next version builds on it.

## What Changes

- **converge's scripts** — `script()` in `converge.py` runs `[sys.executable, <script>, …]` in place of `uv run --script`, still
  under `sandboxed()`; a test holds that each script it starts declares `dependencies = []` ([D1](design.md#d1)).
- **the environments** — `conduct.py` runs `uv sync --script` once for each pinned MF script, in sequence, at a run's start
  and after each re-pin, so a worker or a thread only reuses an environment ([D2](design.md#d2)).
- **the audit** — [the audit table](design.md#d3) names each resource the versions of a run share and its guard; each gap
  is fixed here or deferred with its trigger.
- **the corpus guard** — `scripts/corpus.py` holds one lock while it runs, so parallel builds never delete each other's output
  ([D4](design.md#d4)).
- **the stress test** — a test runs versions that are cut, built, converged and closed at once, round after round, and no
  round halts ([D5](design.md#d5)).

No requirement is added, removed or modified.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change sets `skip_specs: true` ([design](design.md#d7)).

## Impact

Changes `skills/mf-converge/scripts/converge.py`, `skills/mf-ship/scripts/conduct.py`, `scripts/corpus.py`, and
`tests/test_converge.py`, `tests/test_conduct.py` and `tests/test_corpus.py`. Dependencies: none. The gate recipe is
unchanged.

The converge change acts from the next version: a run uses the pinned release's converge, so this version's own converge
runs as before ([design](design.md#d6)).

## Not in this change

- A target's own `uv run --script` in its gate: MF cannot know it. A uv cache for each version is the fallback, when a target's
  gate shows the race.
- The Codex quota attribution of parallel workers ([design](design.md#the-shared-state-audit), U9): deferred until a metric compares per-change
  quota across versions that ran at once.
- The plan review diet: its own version, after this one.
