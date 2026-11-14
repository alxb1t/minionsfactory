# MinionsFactory — the module map

The declared shape of the scripts: each Python file under `skills/` and `scripts/`, its layer and the files it names.
`tests/test_structure.py` holds this table to the tree, per [D83](decisions.md#d83--the-code-is-layered-with-named-seams-held-by-the-gate).

The layers:

- **`conductor`** — the scripts that run a version's line and load a station in process.
- **`station`** — a station's own scripts.
- **`reader`** — the operator's readers of run data, and the metric scripts.
- **`gate`** — the scripts `make gate` and `make corpus` run.
- **`home`** — the shared home, `skills/mflib/`; no row until it exists.

A file **names** another when a string constant outside its docstrings ends in the other's base name, after its last
`/`: `"mf-integrate/scripts/integrate.py"` names `integrate.py`, `"run integrate.py"` names nothing. The `names` cell
lists those base names in order, `—` for none.

| path | layer | names |
|---|---|---|
| `scripts/corpus.py` | gate | — |
| `scripts/docstrings.py` | gate | — |
| `scripts/metrics/codebase.py` | reader | — |
| `scripts/metrics/conformance.py` | reader | — |
| `scripts/metrics/debt.py` | reader | — |
| `scripts/metrics/prose.py` | reader | — |
| `scripts/metrics/reading_set.py` | reader | — |
| `scripts/metrics/references.py` | reader | — |
| `scripts/metrics/rule_ids.py` | reader | — |
| `scripts/metrics/run.py` | reader | — |
| `scripts/metrics/tests_collected.py` | reader | — |
| `skills/mf-build/scripts/metrics.py` | station | — |
| `skills/mf-converge/scripts/bundle.py` | station | — |
| `skills/mf-converge/scripts/converge.py` | station | bundle.py, debt_match.py, evidence.py, gate_check.py, gate_integrity.py, gate_run.py, integrate.py, open_cards.py, overlap.py, plan_check.py, skip_stub.py, stamp.py |
| `skills/mf-converge/scripts/debt_match.py` | station | — |
| `skills/mf-converge/scripts/evidence.py` | station | — |
| `skills/mf-converge/scripts/gate_check.py` | station | — |
| `skills/mf-converge/scripts/gate_integrity.py` | station | — |
| `skills/mf-converge/scripts/gate_run.py` | station | — |
| `skills/mf-converge/scripts/open_cards.py` | station | — |
| `skills/mf-converge/scripts/overlap.py` | station | — |
| `skills/mf-converge/scripts/plan_check.py` | station | gate_run.py |
| `skills/mf-converge/scripts/skip_stub.py` | station | — |
| `skills/mf-converge/scripts/stamp.py` | station | — |
| `skills/mf-cut-change/scripts/awake.py` | station | — |
| `skills/mf-cut-change/scripts/cut_check.py` | station | cut_pre.py, gate_check.py, plan_check.py, verify_check.py |
| `skills/mf-cut-change/scripts/cut_context.py` | station | brief_check.py, bundle.py, debt_match.py, facts.py |
| `skills/mf-cut-change/scripts/cut_pre.py` | station | — |
| `skills/mf-cut-change/scripts/facts.py` | station | brief_check.py |
| `skills/mf-cut-change/scripts/verify_check.py` | station | — |
| `skills/mf-integrate/scripts/integrate.py` | station | — |
| `skills/mf-plan/scripts/brief_check.py` | station | conduct.py, verify_check.py |
| `skills/mf-release/scripts/next_tag.py` | station | — |
| `skills/mf-review-metrics/scripts/review_metrics.py` | reader | conduct.py, metrics.py, overlap.py |
| `skills/mf-ship/scripts/conduct.py` | conductor | brief_check.py, converge.py, integrate.py, pin.py, stamp.py |
| `skills/mf-ship/scripts/pin.py` | conductor | conduct.py |
| `skills/mf-ui/scripts/viewer.py` | reader | conduct.py, converge.py |
