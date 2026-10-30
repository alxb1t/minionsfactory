# The high tier — more independent readers, the same method

Read by the conductor only at `tier=high`. Each worker is fresh, receives the role's packet and reference, writes
only its named output under `.minions/findings/high/<change-id>/`, and starts no worker of its own. You dispatch every
one; you judge none.

```
per role:  finders ─▶ verifiers ─▶ gap sweep ─▶ role writer ─▶ .minions/findings/<change-id>_<role>.md
```

1. **Finders.** Review: one per section of [review](generic-review.md#inspect-one-section-each-in-this-order) — the
   correctness section split into one finder per 150 changed lines, at least 2, at most 8. Security: one finder per
   boundary the threat model names, at least 2, at most 4. Each writes `finder-<role>-<n>.md`: every candidate, the
   half-believed ones too, with its scenario and quoted line — finders forward, verifiers judge.
2. **Verifiers.** One per candidate, given the candidate without the finder's reasoning. Each writes
   `verify-<role>-<n>.md`: `confirmed`, `plausible` or `refuted`, with the evidence the reference asks for.
3. **Gap sweep.** One per role, given the verified list and the packet: it looks only for what was missed — a moved
   guard, a flipped default, a sibling site — and writes `sweep-<role>.md`. Each new candidate gets a verifier.
4. **Role writer.** One per role: it writes the role's findings file from the verified outputs — `confirmed` and
   `plausible` as cards, `refuted` under `## Refuted` — with the frontmatter, `workers:` the count of workers this
   role used, and the Summary the reference asks for.

Where the host runs workers in parallel, dispatch each step's workers together; else one at a time, and the files
record `mode: sequential`. **A verify round at high** gives each card marked `fixed` a fresh verifier over the fix
range, runs the gap sweep over that range, and has a fresh role writer update the file; no finders.
