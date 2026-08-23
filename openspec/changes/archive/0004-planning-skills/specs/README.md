# Spec delta — N-A (doc-only change)

`0004-planning-skills` is a **doc-only change**: it ships prose (the `mf-` planning skills, their rubrics, a
`template/vault-pm/` example, and `make` install/uninstall targets), not test-backed Python. There is **no
behavioral capability to bind**, so this change carries **no spec delta** — no `ADDED` / `MODIFIED` / `REMOVED`
requirements, no scenarios.

This directory exists only to satisfy the four-artifact change contract (`proposal.md` · `design.md` · `tasks.md` ·
`specs/`). The checker parses `spec.md` files only, so this `README.md` adds no scenarios and the gate stays green;
there is nothing to fold at release.

This is the reusable precedent (PRD Option 1) for future doc / prompt-only changes: full `Change:`-trailer
traceability with an explicitly N-A spec delta.
