# Spec delta — N-A (doc-only change)

`0007-pm-finds-repo` is a **doc-only change**: it ships prose (six `mf-*` skills, three shared rubrics, a
`template/vault-pm/` worked example, README lines) plus one vault frontmatter convention (`repo:`). It touches no
`orchestrator/` code and no tests. There is **no behavioral capability to bind**, so this change carries **no spec
delta** — no `ADDED` / `MODIFIED` / `REMOVED` requirements, no scenarios.

This directory exists only to satisfy the four-artifact change contract (`proposal.md` · `design.md` · `tasks.md` ·
`specs/`). The checker parses `spec.md` files only, so this `README.md` adds no scenarios and the gate stays green;
there is nothing to fold at release.

Follows the `0004-planning-skills` precedent, reaffirmed by `0006-teardown`: full `Change:`-trailer traceability
with an explicitly N-A spec delta.

**Note on scope.** The skills' *behaviour* is prose an agent follows, not code the gate can exercise — which is why
the change's own proof (R4, phase 5) is a recorded run of the corrected line rather than a test. See
`design.md` §7 for why enforcement here is by grep, and what v0.8 should absorb when it rewrites the convention
scan.
