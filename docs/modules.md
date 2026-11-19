# MinionsFactory — the module map

The declared shape of the scripts: each Python file under `skills/` and `scripts/`, its layer and the files it names.
`tests/test_structure.py` holds this table to the tree, per [D83](decisions.md#d83--the-code-is-layered-with-named-seams-held-by-the-gate).

The layers:

- **`conductor`** — the scripts under `skills/mf-ship/scripts/` that run a version's line and load a station in process.
- **`station`** — a station's own scripts.
- **`reader`** — the operator's readers of run data, and the metric scripts.
- **`gate`** — the scripts `make gate` and `make corpus` run.
- **`home`** — the shared home, `skills/mflib/`: the port to the OS, and the layout of the run directory and of the home folder.

A row gives a path once, and `check_map` fails on a `conductor` or `home` row outside its folder.

A file **names** another when a string constant outside its docstrings ends in the other's base name, after its last
`/`, or when an import loads the other's module by name: `"mf-integrate/scripts/integrate.py"` and `import integrate`
name `integrate.py`, `"run integrate.py"` names nothing. The `names` cell lists those base names in order, `—` for none.

| path | layer | names |
|---|---|---|
| `scripts/corpus.py` | gate | layout.py |
| `scripts/docstrings.py` | gate | — |
| `scripts/metrics/codebase.py` | reader | — |
| `scripts/metrics/conformance.py` | reader | — |
| `scripts/metrics/debt.py` | reader | layout.py |
| `scripts/metrics/prose.py` | reader | — |
| `scripts/metrics/reading_set.py` | reader | — |
| `scripts/metrics/references.py` | reader | — |
| `scripts/metrics/rule_ids.py` | reader | — |
| `scripts/metrics/run.py` | reader | layout.py |
| `scripts/metrics/tests_collected.py` | reader | — |
| `skills/mf-build/scripts/metrics.py` | station | layout.py |
| `skills/mf-converge/scripts/bundle.py` | station | — |
| `skills/mf-converge/scripts/converge.py` | station | bundle.py, debt_match.py, evidence.py, gate_check.py, gate_integrity.py, gate_run.py, integrate.py, layout.py, open_cards.py, overlap.py, plan_check.py, skip_stub.py, statuslog.py |
| `skills/mf-converge/scripts/debt_match.py` | station | — |
| `skills/mf-converge/scripts/evidence.py` | station | — |
| `skills/mf-converge/scripts/gate_check.py` | station | layout.py |
| `skills/mf-converge/scripts/gate_integrity.py` | station | — |
| `skills/mf-converge/scripts/gate_run.py` | station | layout.py |
| `skills/mf-converge/scripts/open_cards.py` | station | — |
| `skills/mf-converge/scripts/overlap.py` | station | — |
| `skills/mf-converge/scripts/plan_check.py` | station | gate_run.py |
| `skills/mf-converge/scripts/skip_stub.py` | station | — |
| `skills/mf-converge/scripts/stamp.py` | station | statuslog.py |
| `skills/mf-cut-change/scripts/awake.py` | station | layout.py, platform.py |
| `skills/mf-cut-change/scripts/cut_check.py` | station | cut_pre.py, gate_check.py, plan_check.py, verify_check.py |
| `skills/mf-cut-change/scripts/cut_context.py` | station | brief_check.py, bundle.py, debt_match.py, facts.py, layout.py |
| `skills/mf-cut-change/scripts/cut_pre.py` | station | layout.py |
| `skills/mf-cut-change/scripts/facts.py` | station | brief_check.py |
| `skills/mf-cut-change/scripts/verify_check.py` | station | — |
| `skills/mf-integrate/scripts/integrate.py` | station | layout.py |
| `skills/mf-plan/scripts/brief_check.py` | station | conduct.py, verify_check.py |
| `skills/mf-release/scripts/next_tag.py` | station | — |
| `skills/mf-review-metrics/scripts/review_metrics.py` | reader | conduct.py, layout.py, metrics.py, overlap.py |
| `skills/mf-ship/scripts/conduct.py` | conductor | brief_check.py, converge.py, integrate.py, layout.py, pin.py, platform.py, statuslog.py |
| `skills/mf-ship/scripts/pin.py` | conductor | conduct.py, layout.py |
| `skills/mf-ui/scripts/viewer.py` | reader | conduct.py, converge.py, layout.py, platform.py |
| `skills/mflib/__init__.py` | home | — |
| `skills/mflib/layout.py` | home | — |
| `skills/mflib/platform.py` | home | — |
| `skills/mflib/statefile.py` | home | — |
| `skills/mflib/statuslog.py` | home | layout.py, statefile.py |
