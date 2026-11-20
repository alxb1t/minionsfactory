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
| `skills/mf-ship/scripts/conduct.py` | when the run reads it: through `change_dir` |
| `skills/mf-ui/scripts/viewer.py` | when the page shows it |
| `scripts/metrics/run.py`, `skills/mf-review-metrics/scripts/review_metrics.py` | when a metric reads it, through `change_dir` |

A reader takes `change_dir(primary, change)` from `skills/mflib/layout.py`, the home's run-directory layout. It keeps
its own git call for the primary, and `layout.primary_of` maps git's answer to it.

A writer stages the file through `write` of `skills/mflib/statefile.py`, which renames `<name>.tmp` over it and raises
`WriteFailed` for the writer to word; a reader takes `statefile.read`, which follows no link. The status log is
written and parsed through `skills/mflib/statuslog.py`, its path `layout.status_log(primary, change)`. The findings
files are written and parsed through `skills/mflib/findings.py`, their paths `layout.findings_file(primary, change, role)`.
The debt file is written and parsed through `skills/mflib/debtfile.py`, its path `layout.debt_file(primary)`, and its
lock taken through `debtfile.lock`.

- **Row:** none, unless the extension adds a script; then a row as for a station, its `names` cell holding `layout.py`.
- **Rules:** `check_layout` holds that `.minions` is joined in `skills/mflib/layout.py` alone: a string constant
  elsewhere equal to `.minions`, or starting `.minions/`, fails unless `LAYOUT_SITES` lists the pair. It holds the home
  folder's names there too: a string constant elsewhere that contains `.mf-ship-origin`, or equals `XDG_CONFIG_HOME`,
  `XDG_DATA_HOME` or `XDG_STATE_HOME`, fails whatever the list holds, and `LAYOUT_SITES` lists neither.
  `check_formats` holds the format names in `skills/mflib/`: a string constant elsewhere equal to `status_log.md`, or
  containing `## Run`, or the card head `- **` or `- \*\*`, fails unless `FORMAT_SITES` lists the pair.

## An OS

A platform other than macOS or Linux. Today's OS commands are `sandbox-exec`, `bwrap`, `caffeinate`, `sysctl` and `ps`.

| file | edit |
|---|---|
| `skills/mflib/platform.py` | `OS` and `side`, the host's side, read once; `Policy`, `profile`, `confine` and `has_sandbox`, the sandbox, `confine` and `has_sandbox` on Linux through `bwrap`; `no_sandbox`, why no sandbox stands; `refused`, its refusal per `OS`; `arch`, the host's architecture; `process`, a process's `ps` field; `has_hold`, `hold_awake`, `no_hold` and `CAFFEINATE`, the awake hold; `marks`, the worker sandbox's names |

- **Row:** none, unless the extension adds a script; then a row as for a station.
- **Rules:** `check_os` fails on an OS command a file other than the port, `skills/mflib/platform.py`, names unless
  `OS_NAMES` lists the pair; the port needs no pair. A new command joins `_OS_WORDS`, so the rule finds it.

## An executor

A worker host beside `claude` and `codex`.

| file | edit |
|---|---|
| `skills/mf-ship/scripts/conduct.py` | `EXECUTORS`; `argv`, its command line and sandbox flags; `_executor_missing`; its log readers beside `_codex_denied`, `_codex_limit` and `usage_limit` |
| `skills/mflib/layout.py` | `SKILLS`, each host's skills folder, which the conductor checks and the pin links |
| `skills/mf-plan/scripts/brief_check.py` | `HOSTS`, the executors a brief may name |
| `skills/mf-converge/scripts/converge.py` | `fixer`, its attribution line; `Host`, when it needs a call the conductor does not give |
| `skills/mf-review-metrics/scripts/review_metrics.py` | its session reader beside `_codex_sessions`, `_codex_spent` and `_codex_usage` |
| `tests/escape_drill.py` | the sandbox-escape drill for it |

Until the home holds the executor port, an executor is a branch in each of these. When the home holds the port, it is
one module there.

- **Row:** none, unless the extension adds a script; then a row as for a station.
- **Rules:** `check_loads` holds that `converge.py` reaches an executor through the `Host` the conductor hands it,
  never by naming `conduct.py`. `check_names` holds that no reader takes a new `_name` from `conduct.py`.
