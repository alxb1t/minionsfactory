# Spec delta — N-A (doc-only change)

`0006-teardown` is a **doc-only change**: it ships prose (the `compliance` rubric, the `mf-teardown` skill, two
reconciled vault notes, README lines), not test-backed Python. Nothing is added to `orchestrator/` and nothing to
`pyproject.toml` dependencies, so there is **no behavioral capability to bind** — this change carries **no spec
delta**: no `ADDED` / `MODIFIED` / `REMOVED` requirements, no scenarios.

The PRD's requirements (R1–R12) are acceptance over **observable behaviour of the skill and the artifacts it
writes** — run it, read the report — not bound pytest scenarios. Their verification is the proving runs and
contract exercises in `tasks.md` phase 6.

This directory exists only to satisfy the four-artifact change contract (`proposal.md` · `design.md` · `tasks.md` ·
`specs/`). The checker parses `spec.md` files only, so this `README.md` adds no scenarios and the gate stays green;
there is nothing to fold at release.

Follows the `0004-planning-skills` precedent for doc / prompt-only changes: full `Change:`-trailer traceability with
an explicitly N-A spec delta.
