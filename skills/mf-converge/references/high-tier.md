# The high tier — more independent readers, the same method

Read by the conductor only at `tier=high`. Each worker is fresh, receives the role's packet and reference, writes
only its named output under `.minions/findings/high/<change-id>/`, and starts no worker of its own. You dispatch every
one; you judge none.

```
per role:  finders ─▶ verifiers ─▶ gap sweep ─▶ role writer ─▶ .minions/findings/<change-id>_<role>.md
```

1. **Finders.** Review: one per section of [review](generic-review.md#inspect-one-section-each-in-this-order) — the
   correctness section split into one finder per 150 changed lines, at least 2, at most 8 — and one **pass worker**,
   which runs the contract's stale-claim, test-cost and coverage-trace passes. Security: one finder per boundary the
   threat model names, at least 2, at most 4. Each writes `finder-<role>-<n>.md`, the pass worker `pass-review.md`:
   every candidate as one top-level list line, the half-believed ones too, with its scenario and quoted line —
   finders forward, verifiers judge. `pass-review.md` also says what each pass searched or read.
2. **Verifiers.** One per candidate, given the candidate without the finder's reasoning. Each writes
   `verify-<role>-<n>.md`: `confirmed`, `plausible` or `refuted`, with the evidence the reference asks for.

   **The ceiling is 40 verifiers per role per round.** Before each batch of a role's verifiers, count its candidates
   and add the verifiers that role already ran this round. Above the ceiling → halt, naming the role, the count and
   the ceiling, and start none of the batch: never trim or sample it. Every candidate gets a verifier, or the person
   decides, by splitting the change or running `tier=standard`.
3. **Gap sweep.** One per role, given the verified list and the packet: it looks only for what was missed — a moved
   guard, a flipped default, a sibling site — and writes `sweep-<role>.md`. Each new candidate gets a verifier.
4. **Role writer.** One per role: it writes the role's findings file from the verified outputs — `confirmed` and
   `plausible` as cards, `refuted` under `## Refuted` — applying the contract's repeat rule to each card against the
   backlog, with the frontmatter, `workers:` the count of workers this role used, and the Summary the reference asks
   for. Review's Summary reports each pass from `pass-review.md`.

Where the host runs workers in parallel, dispatch each step's workers together; else one at a time, and the files
record `mode: sequential`. **A verify round at high** gives each card marked `fixed` or `wontfix` a fresh verifier
over this round's freeze — the unchanged head and the previous freeze's patch when the fixer committed nothing — and
that verifier says `fixed` → `verified`, `wontfix` → `accepted`, or either → `open` with its reason. The round also
runs review's pass worker and each role's gap sweep over that freeze, under the same ceiling, and a fresh role writer
updates the file; no finders.
