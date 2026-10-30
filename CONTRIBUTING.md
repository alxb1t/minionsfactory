# Contributing to MinionsFactory

How a change lands here, and the evidence it carries: MF is built the way it builds. Mandatory context, named by
[AGENTS.md](AGENTS.md).

## How a change lands

```
mf-plan ──▶ mf-cut-change ──▶ mf-build ──▶ mf-converge or a hand read ──▶ mf-release
```

- **Planned** with `mf-plan` to a hard brief, then cut
  ([D5](docs/decisions.md#d5--a-change-is-planned-with-mf-plan-and-written-with-the-openspec-cli)).
- **Converge or a hand read** — a change of skill text alone may skip converge and be read by hand; the release
  states the skip ([D14](docs/decisions.md#d14--converge-is-optional-and-a-skip-is-stated)).
- **Side by side** — each version in its own worktree; `mf-integrate` merges a moved base in
  ([D44](docs/decisions.md#d44--versions-run-side-by-side-in-worktrees-one-primary-merges-them),
  [D45](docs/decisions.md#d45--one-station-merges-the-default-branch-into-the-next-version)).
- **Unattended** — `mf-ship` takes cut versions to the default branch ([D47](docs/decisions.md#d47--mf-ship-takes-cut-versions-to-the-default-branch-unattended)).

## The evidence a change carries

- **Its change directory** under `openspec/changes/`: proposal, design, tasks and spec delta.
- **Each `Verify:`**, run by the build before its box is ticked.
- **A green `make gate`** at every phase's commit.
- **A `Change: <change-id>` trailer** on every commit
  ([D21](docs/decisions.md#d21--every-commit-names-its-change)).
- **The check loop's findings**, in `.minions/findings/`, when converge ran. `.minions/backlog.md` holds only
  check-loop findings ([D16](docs/decisions.md#d16--deferred-work-is-a-card-in-the-repos-backlog)).
