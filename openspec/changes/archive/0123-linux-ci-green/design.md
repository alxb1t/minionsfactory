# Linux CI green — design

Fix each cause of Linux CI's red tests at its source, and make the macOS gate as strict as Linux. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

- `replay` in `skills/mf-integrate/scripts/integrate.py` runs `merge -q --no-ff --no-commit` under no `-c user.name` (`skills/mf-integrate/scripts/integrate.py:721-723`). `conduct.py` names `SCRATCH_IDENTITY` for its scratch commits (`skills/mf-ship/scripts/conduct.py:319`).
- `gate_check.py` clears `CLEARED = ("MAKEFLAGS", "MFLAGS", "MAKELEVEL")` from its environment (`skills/mf-converge/scripts/gate_check.py:27`, `:64-65`). `gate_run.py`'s `_make_env` drops `VIRTUAL_ENV` only (`skills/mf-converge/scripts/gate_run.py:46-48`), and `check_gate` in `cut_pre.py` runs `make -n gate` through `_tool`, which passes no `env` (`skills/mf-cut-change/scripts/cut_pre.py:141`).
- `isolated_home` points `GIT_CONFIG_GLOBAL` at `home/.gitconfig` and writes nothing into it (`tests/conftest.py:20-38`).
- `test_stop_ends_a_live_run` and `test_a_stale_claim_is_cleared` link a fake `claude` to `sleep` (`tests/test_conduct.py:9410`, `tests/test_conduct.py:10814`). The fake `ps` answers each worker's `comm` from a registry (`tests/test_conduct.py:219-223`), and `_clear` reads that `comm` (`skills/mf-ship/scripts/conduct.py:4336`).

## Goals / Non-Goals

Goals: CI's run on Linux has no red test of these causes; the macOS gate fails on a missing git identity as Linux does; no station's behaviour changes.

Non-goals: see [proposal](proposal.md#not-in-this-change).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `replay` merges under its own `SCRATCH_IDENTITY` in `integrate.py` | the fault is in the product: a machine with no git identity cannot run the replay | a fixture that supplies an identity, which would leave the fault live |
| [D2](#d2) | The dry runs of `gate_run.py` and `cut_pre.py` drop `MAKEFLAGS`, `MFLAGS` and `MAKELEVEL`; the gate run proper is unchanged | the dry run's output is hashed and counted, so it must not depend on the caller's make | clearing the flags for the gate run too, which changes what a caller's `-i` or `DIFF_BASE` does |
| [D3](#d3) | `isolated_home` writes `user.useConfigOnly = true` into the test's global config | the local gate then fails on a missing identity as Linux does | leaving macOS to derive an identity from the host name |
| [D4](#d4) | `test_stop_ends_a_live_run` and `test_a_stale_claim_is_cleared` start a plain `sleep` and register the `comm` the link gave | the tests need a live process and a `comm`, not an executable named `claude` | a link to a script, which adds a file to keep |
| [D5](#d5) | One phase a cause, the fixture first | each phase ends on a green `make check`, and the identity fault is seen red before it is fixed | one phase for all three, which hides which cause turned which test green |

### D1

`integrate.py` defines `SCRATCH_IDENTITY` beside `NO_HOOKS`, the same shape as `conduct.py`'s: `user.name`, `user.email` and `commit.gpgsign=false`, under the name `mf-integrate`. `replay` puts it in front of its `-c rerere.enabled=false`. `integrate.py` loads no other script, so it keeps its own copy.

### D2

Each of `gate_run.py` and `cut_pre.py` holds `CLEARED`, the tuple `gate_check.py` holds, and builds the dry run's environment without those keys. `gate_run.py` adds `_dry_env()` over `_make_env()`, so `VIRTUAL_ENV` stays dropped for both runs. `cut_pre.py`'s `_tool` takes an optional `env`, which only `check_gate` passes.

### D3

The fixture writes the config file before the test runs. A test that commits with no identity of its own then fails with git's identity error, as it does on a Linux runner. Such a test takes the identity its sibling helpers pass: `-c user.name=mf -c user.email=mf@example.invalid`.

### D4

Each test keeps `executor = tmp_path / "claude"` as the `comm` string it registers and starts `["sleep", "60"]` where it started `[str(executor), "60"]`. The path is never created.

### D5

The fixture lands first, so the replay tests are red on macOS before [D1](#d1) fixes them. Each phase then ends green on its own.

## Tests

Tests added, at the script's own layer, a real `make` in a scratch repository, and none end-to-end: `test_an_empty_gate_halts_under_inherited_make_flags` in `tests/test_cut_pre.py`, and `test_a_record_holds_under_inherited_make_flags` in `tests/test_gate_run.py`. `uv run pytest tests/test_cut_pre.py tests/test_gate_run.py --collect-only -q` lists each. The other edits extend what stands (`T2`):

| file | what it carries |
|---|---|
| `tests/conftest.py` | the fixture's `user.useConfigOnly`, which every replay test then runs under |
| `tests/test_guardrails.py` | an assertion on the fixture's config, in `test_the_isolation_fixture_holds_home_under_tmp_path` |
| `tests/test_integrate.py` | the replay tests, unchanged, red without `SCRATCH_IDENTITY` |
| `tests/test_conduct.py` | `test_stop_ends_a_live_run` and `test_a_stale_claim_is_cleared`, their process started plain |

No test is removed or merged, so `I16` has no table. No end-to-end run is added.

## Dependencies

None.

## Risks / Trade-offs

- The fixture may turn red a test that commits with no identity. The first phase's `make check` shows it; D3 says how it is fixed.
- If the replay passes under the fixture before D1 is built, the identity is not the cause and the plan is wrong: a `**HALT CHECK**` in [tasks](tasks.md) stops there.
- `SCRATCH_IDENTITY` and `CLEARED` are copies until a shared home exists. A later version removes them.

## Verdict

Ready to build. A phase for each cause; the gate stays green at the end of each.
