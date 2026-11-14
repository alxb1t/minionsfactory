---
bump: patch
---

# Linux CI green

Fix the causes of CI's red tests on Linux where they are, in the product and in the tests, with no station's behaviour changed.

Reading map: [design](design.md) holds the causes and the proof of each, [tasks](tasks.md) holds a phase for each cause.

## Why

CI on Linux is red on the newest `main` run, from test-environment artefacts. Every later version needs a Linux signal, so each cause is fixed rather than allowlisted.

- **The replay has no identity.** `replay` in `skills/mf-integrate/scripts/integrate.py` merges with no git identity of its own. The conductor's scratch commits carry `SCRATCH_IDENTITY`. A machine with no identity refuses the replay, and macOS hides it by deriving one.
- **The dry runs inherit make's flags.** `gate_run.py` and `cut_pre.py` run `make -n gate` with the caller's `MAKEFLAGS`, `MFLAGS` and `MAKELEVEL`. Under `MAKEFLAGS=w` make prints directory lines, which change the dry run's hash and hide an empty recipe. `gate_check.py` already clears them.
- **A fake `claude` is linked to `sleep`.** `test_stop_ends_a_live_run` and `test_a_stale_claim_is_cleared` need a live process whose `comm` the fake `ps` reports. A plain `sleep` is that process with no link, and the registered `comm` still names `claude`.

## What Changes

- `integrate.py` gains `SCRATCH_IDENTITY`, and `replay` merges under it.
- `tests/conftest.py`'s `isolated_home` writes `user.useConfigOnly = true` into the test's global git config, so the macOS gate is as strict as Linux.
- `gate_run.py`'s dry run and `cut_pre.py`'s dry run drop `MAKEFLAGS`, `MFLAGS` and `MAKELEVEL` from the environment they run make in.
- `test_stop_ends_a_live_run` and `test_a_stale_claim_is_cleared` start a plain `sleep`.
- A case in `tests/test_gate_run.py` and one in `tests/test_cut_pre.py` run under `MAKEFLAGS=w`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change declares `skip_specs: true`: no requirement describes what it fixes.

## Impact

- Product: `skills/mf-integrate/scripts/integrate.py`, `skills/mf-converge/scripts/gate_run.py`, `skills/mf-cut-change/scripts/cut_pre.py`.
- Tests: `tests/conftest.py`, `tests/test_guardrails.py`, `tests/test_integrate.py`, `tests/test_gate_run.py`, `tests/test_cut_pre.py`, `tests/test_conduct.py`.
- No dependency, decision or requirement is added.

## Not in this change

- An allowlist of red tests: none is kept.
- A shared home for `SCRATCH_IDENTITY` or the cleared make variables: each script keeps its own copy until the region that moves them.
- The `make -n gate` capture in `skills/mf-converge/scripts/converge.py`: it prints and hashes nothing, and no plan item names it.
- Reading CI's run after the push: a second patch follows only if that run stays red.
