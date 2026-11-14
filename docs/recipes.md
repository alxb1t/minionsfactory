# MinionsFactory — the recipes

What an extension edits today: a station, a state file, an OS, an executor. Each section names the files, the row it
adds to [the module map](modules.md) and the structure rule of `tests/test_structure.py` that holds it, per
[D83](decisions.md#d83--the-code-is-layered-with-named-seams-held-by-the-gate).

```
  the map says what exists ──▶ modules.md
  a recipe says what an extension edits ──▶ recipes.md
  the rules hold both ──▶ tests/test_structure.py ──▶ make gate / make check
```

## A station

A new `mf-*` skill, with or without scripts.

| file | edit |
|---|---|
| `skills/mf-<name>/SKILL.md` | the station's instructions; `pin.py` exports the `skills/` tree and links each `mf-*` folder, so the pin needs no edit |
| `skills/mf-<name>/scripts/<script>.py` | each script, a `uv` script per [the coding standards](../CODING_STANDARDS.md) |
| `tests/test_<script>.py` | each script's tests |
| `skills/mf-ship/scripts/conduct.py` | when `mf-ship` starts it: `STATIONS` or `PLANNED`, and its prompt in `PROMPTS` |
| `skills/mf-plan/scripts/brief_check.py` | when the brief picks its model: `STATIONS` |
| `AGENTS.md`, `README.md` | the station in the `skills/` bullet of *Layout*, and a row in the README's table of skills |

- **Row:** one per script, layer `station`, its `names` cell the base names it names, `—` for none.
- **Base name:** a script's base name must be held by one file under `skills/` and `scripts/`: an edge finds its file
  by base name, and `check_map` fails on a base name that more than one file holds.
- **Rules:** `check_map` holds the row. `check_loads` lets the script name a file of its own folder or of the shared
  home, never another station's script or `conduct.py`. `check_cycles` and `check_names` hold no cycle and no `_name`
  taken from a named file.

## A state file

A new file in `.minions/changes/<change-id>/`, per
[D57](decisions.md#d57--one-folder-per-change-in-minions).

| file | edit |
|---|---|
| `docs/decisions.md` | the file's name in `D57`'s list |
| the writer's `SKILL.md` or script | where it is written, and its lines |
| `skills/mf-ship/scripts/conduct.py` | when the run reads it: through `_change_dir` |
| `skills/mf-ui/scripts/viewer.py` | when the page shows it |
| `scripts/metrics/run.py`, `skills/mf-review-metrics/scripts/review_metrics.py` | when a metric reads it, each through its own `_change_dir` |

Until the home holds the finder, each script finds the change folder through its own `_change_dir`: `conduct.py`,
`gate_check.py`, `integrate.py`, `review_metrics.py` and `scripts/metrics/run.py` each define one. When the home holds
the finder, a reader takes it from there.

- **Row:** none, unless the extension adds a script; then a row as for a station.
- **Rules:** `check_names` holds that no script takes another's `_change_dir`: a private name taken from a named file
  fails unless `PRIVATE_REACH` lists the pair.

## An OS

A platform other than macOS. Today's OS commands are `sandbox-exec`, `caffeinate`, `sysctl` and `ps`.

| file | edit |
|---|---|
| `skills/mf-ship/scripts/conduct.py` | `_profile` and `_sandbox_exec`, the worker's sandbox; `_native`, the host's architecture; `_hold_awake` and `_ps`, the awake hold |
| `skills/mf-cut-change/scripts/awake.py` | `_ps`, `_name` and `_start`, the cut's awake hold |
| `skills/mf-ui/scripts/viewer.py` | `run_ps`, a worker's command line |

Until the home holds the platform port, an OS's commands go in these functions. When the home holds the port, they move
there, and `OS_NAMES` loses their lines.

- **Row:** none, unless the extension adds a script; then a row as for a station.
- **Rules:** `check_os` fails on an OS command a file names unless `OS_NAMES` lists the pair. A new command joins
  `_OS_WORDS`, so the rule finds it.

## An executor

A worker host beside `claude` and `codex`.

| file | edit |
|---|---|
| `skills/mf-ship/scripts/conduct.py` | `EXECUTORS`; `SKILLS`, where its skills live; `argv`, its command line and sandbox flags; `_executor_missing`; its log readers beside `_codex_denied`, `_codex_limit` and `usage_limit` |
| `skills/mf-plan/scripts/brief_check.py` | `HOSTS`, the executors a brief may name |
| `skills/mf-ship/scripts/pin.py` | `HOSTS`, the skills folders the pin links |
| `skills/mf-converge/scripts/converge.py` | `fixer`, its attribution line; `Host`, when it needs a call the conductor does not give |
| `skills/mf-review-metrics/scripts/review_metrics.py` | its session reader beside `_codex_sessions`, `_codex_spent` and `_codex_usage` |
| `tests/escape_drill.py` | the sandbox-escape drill for it |

Until the home holds the executor port, an executor is a branch in each of these. When the home holds the port, it is
one module there.

- **Row:** none, unless the extension adds a script; then a row as for a station.
- **Rules:** `check_loads` holds that `converge.py` reaches an executor through the `Host` the conductor hands it,
  never by naming `conduct.py`. `check_names` holds that no reader takes a new `_name` from `conduct.py`.
