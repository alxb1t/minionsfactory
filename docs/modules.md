# MinionsFactory — the module map

The declared shape of the scripts: each Python file under `skills/` and `scripts/`, its layer and the files it names.
`tests/test_structure.py` holds this table to the tree, per [D83](decisions.md#d83--the-code-is-layered-with-named-seams-held-by-the-gate).

The layers:

- **`conductor`** — the scripts under `skills/mf-ship/scripts/` that run a version's line and load a station in process.
- **`station`** — a station's own scripts.
- **`reader`** — the operator's readers of run data, and the metric scripts.
- **`gate`** — the scripts `make gate` and `make corpus` run, and the setup script a cloud environment runs.
- **`home`** — the shared home, `skills/mflib/`: the port to the OS, the layout of the run directory and of the home folder, and the formats of the state files.

A row gives a path once, and `check_map` fails on a `conductor` or `home` row outside its folder.

A file **names** another when a string constant outside its docstrings ends in the other's base name, after its last
`/`, or when an import loads the other's module by name: `"mf-integrate/scripts/integrate.py"` and `import integrate`
name `integrate.py`, `"run integrate.py"` names nothing. The `names` cell lists those base names in order, `—` for none.

| path | layer | names |
|---|---|---|
| `scripts/cloud_setup.py` | gate | layout.py, platform.py |
| `scripts/corpus.py` | gate | layout.py |
| `scripts/docstrings.py` | gate | — |
| `scripts/metrics/codebase.py` | reader | — |
| `scripts/metrics/conformance.py` | reader | — |
| `scripts/metrics/debt.py` | reader | debtfile.py, layout.py |
| `scripts/metrics/prose.py` | reader | — |
| `scripts/metrics/reading_set.py` | reader | — |
| `scripts/metrics/references.py` | reader | — |
| `scripts/metrics/rule_ids.py` | reader | — |
| `scripts/metrics/run.py` | reader | debtfile.py, eras.py, findings.py, layout.py, marks.py, prices.py, runlog.py, statefile.py, statuslog.py |
| `scripts/metrics/tests_collected.py` | reader | — |
| `skills/mf-build/scripts/metrics.py` | station | layout.py |
| `skills/mf-converge/scripts/bundle.py` | station | statefile.py |
| `skills/mf-converge/scripts/converge.py` | station | bundle.py, debt_match.py, debtfile.py, evidence.py, findings.py, gate_check.py, gate_integrity.py, gate_run.py, integrate.py, layout.py, marks.py, open_cards.py, overlap.py, plan_check.py, skip_stub.py, statefile.py, statuslog.py |
| `skills/mf-converge/scripts/debt_match.py` | station | debtfile.py, statefile.py |
| `skills/mf-converge/scripts/evidence.py` | station | — |
| `skills/mf-converge/scripts/gate_check.py` | station | kept.py, layout.py |
| `skills/mf-converge/scripts/gate_integrity.py` | station | — |
| `skills/mf-converge/scripts/gate_run.py` | station | layout.py, statefile.py |
| `skills/mf-converge/scripts/open_cards.py` | station | findings.py, statefile.py |
| `skills/mf-converge/scripts/overlap.py` | station | findings.py |
| `skills/mf-converge/scripts/plan_check.py` | station | gate_run.py, statefile.py |
| `skills/mf-converge/scripts/skip_stub.py` | station | findings.py, statefile.py |
| `skills/mf-converge/scripts/stamp.py` | station | statuslog.py |
| `skills/mf-cut-change/scripts/awake.py` | station | layout.py, platform.py |
| `skills/mf-cut-change/scripts/cut_check.py` | station | cut_pre.py, gate_check.py, plan_check.py, verify_check.py |
| `skills/mf-cut-change/scripts/cut_context.py` | station | brief_check.py, bundle.py, debtfile.py, facts.py, layout.py, statefile.py |
| `skills/mf-cut-change/scripts/cut_pre.py` | station | layout.py, statefile.py |
| `skills/mf-cut-change/scripts/facts.py` | station | brief_check.py, statefile.py |
| `skills/mf-cut-change/scripts/verify_check.py` | station | cut_pre.py, plan_check.py |
| `skills/mf-integrate/scripts/integrate.py` | station | findings.py, layout.py, marks.py |
| `skills/mf-plan/scripts/brief_check.py` | station | conduct.py, layout.py, modelsfile.py, verify_check.py |
| `skills/mf-release/scripts/next_tag.py` | station | — |
| `skills/mf-release/scripts/release.py` | station | debtfile.py, findings.py, gate_check.py, gate_run.py, layout.py, marks.py, metrics.py, modelsfile.py, next_tag.py, statefile.py |
| `skills/mf-review-metrics/scripts/review_metrics.py` | reader | conduct.py, layout.py, metrics.py, overlap.py, prices.py |
| `skills/mf-ship/scripts/conduct.py` | conductor | brief_check.py, claim.py, converge.py, cut_check.py, debtfile.py, findings.py, gate_run.py, integrate.py, kept.py, layout.py, marks.py, metrics.py, modelsfile.py, pin.py, plan_check.py, platform.py, queue.py, release.py, runlog.py, statefile.py, statuslog.py |
| `skills/mf-ship/scripts/pin.py` | conductor | conduct.py, kept.py, layout.py |
| `skills/mf-ui/scripts/viewer.py` | reader | conduct.py, converge.py, findings.py, kept.py, layout.py, platform.py, queue.py, runlog.py, statefile.py, statuslog.py |
| `skills/mflib/__init__.py` | home | — |
| `skills/mflib/claim.py` | home | layout.py, statefile.py |
| `skills/mflib/debtfile.py` | home | findings.py, statefile.py |
| `skills/mflib/eras.py` | home | statuslog.py |
| `skills/mflib/findings.py` | home | layout.py, statefile.py |
| `skills/mflib/kept.py` | home | layout.py, statefile.py |
| `skills/mflib/layout.py` | home | — |
| `skills/mflib/marks.py` | home | layout.py, statefile.py |
| `skills/mflib/modelsfile.py` | home | layout.py, statefile.py |
| `skills/mflib/platform.py` | home | — |
| `skills/mflib/prices.py` | home | statefile.py |
| `skills/mflib/queue.py` | home | layout.py, statefile.py |
| `skills/mflib/runlog.py` | home | layout.py, statefile.py |
| `skills/mflib/statefile.py` | home | — |
| `skills/mflib/statuslog.py` | home | layout.py, statefile.py |
