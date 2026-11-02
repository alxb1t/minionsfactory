# The re-judge

Whether the sandbox makes each open card moot, per [D8](../design.md#d8). Answer: it makes none moot, so `proposal.md`'s
`backlog:` stays as cut. Read from the code and the cards; no card's own confirming run was made.

The cards share one reason: the sandbox holds the worker, and each route runs through the worker's reach, which still holds the
run directory and the common directory, into the conductor or Codex's start, which it does not hold.

| card | verdict | because |
|---|---|---|
| `0049·S5` | stands | `.minions/runs/active` is in a worker's reach, so a worker still writes the claim the conductor kills from |
| `0049·S7` | stands | the common directory is in reach, and the conductor reads its config outside the sandbox. `Run.advance` pushes while other workers live, a new site of the same race, which converge took out of it, per [D9](../design.md#d9); the local git stays in it |
| `0050·R5` | stands | the same race in `merge_in`, at the conductor's rights |
| `0050·R11` | stands | `<primary>/.git` is in reach, so a worker can still swap it before Codex starts; the network being off stops no write to a sibling's `.git` |
| `0050·S7` | stands | any listed root can still be moved by a worker; the scratch run the card asks for was not made |
