---
bump: minor
debt: [0034·R9, 0099·R5, 0103·R4, 0106·R3, 0109·R1, 0108·R9]
---

# Gate hardening

A stricter gate, and tool evidence before the checkers: what a tool can find, a tool finds; the checkers judge the rest
([D79](design.md#d8)).

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

The checkers spend tokens on facts a script finds: a new `# noqa`, a test removed, a name the diff deletes, a docstring over
the comment limit, a `subprocess.run` with no timeout. The same classes come back as debt cards, and `gate_check.py` reads
makefiles and dry runs only, so a ruff `select` edit passes it unseen ([design](design.md#context), F3, F4, F10).

This is the evidence step of the token diet: the gate holds what a rule can hold, and converge hands every checker the facts
a tool found, in one file.

## What Changes

- **The lint** — ruff's wider families, the sites they find cleaned; each deliberate blind `except` a `# noqa: BLE001` with
  its reason.
- **The docstring check** — `scripts/docstrings.py` holds `C7` and `C3` by the AST, in the gate and in `make check`.
- **The timeout rule** — `ast-grep-cli` as a dev dependency and one rule, `subprocess-run-needs-timeout`, in the gate; each
  site it finds gets a timeout.
- **The prefetch** — `conduct.py cut` fetches each package the brief approves into `.minions/uv-cache`, wheels only, from
  PyPI's hosts only.
- **The evidence** — `gate_integrity.py` writes one line per suppression, skip, removed test or assertion, gate-config edit
  and swallowed error; converge writes `evidence.md` at every freeze and gives it to each worker through `{evidence}`.
- **The prose** — the worker references start from the evidence; [D79](design.md#d79), the ratchet in `CONTRIBUTING.md`,
  the docstring rule in `CODING_STANDARDS.md`.

Requirements, in [the delta](specs/sdd/spec.md), all ADDED:

- *The gate holds the wider lint, the timeout rule and the docstring check* — each a line of `make gate`.
- *Converge writes the evidence of each freeze* — `evidence.md` at every freeze, `{evidence}` in every worker prompt.
- *The checkers start from the evidence and judge the rest* — no re-deriving a line the file holds.
- *A queued cut prefetches the packages it approves* — wheels only, PyPI's hosts only.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: the requirements above, added.

## Impact

Changes `pyproject.toml`, `uv.lock`, `Makefile`, `sgconfig.yml`, the rule file under `sg-rules/`, `scripts/docstrings.py`,
`skills/mf-converge/scripts/gate_integrity.py`, `scripts/corpus.toml`, `skills/mf-converge/scripts/evidence.py`,
`skills/mf-converge/scripts/converge.py`, the references under `skills/mf-converge/references/`,
`skills/mf-ship/scripts/conduct.py`, the sites the lint, the docstring check and the timeout rule find, their tests,
`docs/decisions.md`, `CONTRIBUTING.md` and `CODING_STANDARDS.md`. Dependencies: `ast-grep-cli` ([design](design.md#dependencies)).
The gate recipe gains lines, quoted in [tasks](tasks.md).

Its own gate takes the lint, the docstring check and the timeout rule at once. `gate_integrity.py`, the evidence step and
`{evidence}` run from the pinned release, so they act from the next version ([design](design.md#d9)).

## Not in this change

- The plan review diet, and `plan` and `operator` stations in `mf-review-metrics` — their own versions.
- `deptry`: it reads no PEP 723 header, and MF has no runtime dependency.
- `TRY`, `C901` and `PLR09` as gates: `TRY` is churn against `Stop(f"…")`, and `C901` stays a metric ([D43](../../../docs/decisions.md#d43--project-health-is-measured-per-change-from-the-repos-own-catalogue)).
- A prefetch at `conduct.py rejoin`, when a person approves new rows there: add it when a rejoined cut meets a cache miss.
- Paying `0108·S4` and `0104·S7`, which the brief lists: they stay open. `0108·S4` is `sandboxed()`'s unbounded
  `process.wait()`, `0104·S7` a probe killed on what is left of converge's time; the rule here holds `subprocess.run` calls
  with no timeout, and reaches neither ([design](design.md#risks--trade-offs), C1 of the brief, decided by the cutter).
