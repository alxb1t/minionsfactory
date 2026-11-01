# Gate speed

`_fake` left the test file, per [D9](../design.md#d9). Measured with `uv run pytest -q --durations=5`, on the machine the
build ran on, with 92 tests each way.

before: 158.13s, at phase 3's commit, `_fake` in `tests/test_conduct.py`
after: 155.25s, `_fake` in `tests/fake_worker.py`, and `0049·R9`'s step added

The bar is below 169s, the cut's measure. It holds.

| slowest, before | s | slowest, after | s |
|---|---:|---|---:|
| `test_after_waits_for_its_dependency` | 23.34 | `test_after_waits_for_its_dependency` | 22.63 |
| `test_a_rerun_recovers_a_dead_release` | 21.11 | `test_a_rerun_recovers_a_dead_release` | 22.47 |
| `test_an_include_changed_on_the_branch_halts` | 12.13 | `test_an_include_changed_on_the_branch_halts` | 12.60 |
| `test_a_halted_dependency_blocks_a_chain` | 10.00 | `test_a_halted_dependency_blocks_a_chain` | 9.82 |
| `test_a_ready_version_ships_past_a_slow_one` | 5.92 | `test_status_reads_each_stage_from_disk` | 5.82 |

## Past 20s after the move

- `test_after_waits_for_its_dependency`: its scratch repositories each take full runs with real git, and each run's probe
  starts `make gate`. A worker's interpreter start is a small part of that.
- `test_a_rerun_recovers_a_dead_release`: its time is the runs a death and its re-run take, and it gained the
  `dies-integrate` runs here.

The move saves little: the time is git and the runs, not `import pytest`.
