# MinionsFactory — developer docs

Raw-markdown docs for the MinionsFactory orchestrator (the `minions_factory` product repo).
No build tooling — read them directly, here or in any markdown viewer.

> **Scope of these docs:** they describe the repo as built **through Phase P5** of the
> `v0.1_loop_spine` plan — all orchestrator modules (provider seam, gate runner, plan-state reader,
> build-spine driver, CLI entry) now exist. P6 is the dogfood *run*, not a new module.

## Index

| Doc | What it covers |
| --- | --- |
| [architecture.md](architecture.md) | The big picture: what v0.1 builds, the load-bearing invariants, the package/dependency graph, and the P0→P6 roadmap. |
| [data-flow.md](data-flow.md) | Control + data flow: how a role runs (`run_role`), and the build-spine loop (driver → gate → advance/halt). |
| [modules/orchestrator.md](modules/orchestrator.md) | Per-package API reference — every public symbol currently in `orchestrator/`, with signatures and purpose. |

## Where the rest of the truth lives

- **The plan + design decisions** live in a **private Obsidian vault** (its path is in `.env` →
  `VAULT_PROJECT_DIR`; never committed). The active plan is the highest-versioned
  `implementation_plans/vX.Y_*implementation_plan.md`.
- **What is *true* about the repo** (layout, gate, invariants) is in the repo's root `CLAUDE.md`.
- **What shipped, per version** is in [`../CHANGELOG.md`](../CHANGELOG.md) (Keep a Changelog).

These `docs/` are the **cross-cutting view** (how the pieces relate); the **docstrings in the code**
are the authoritative "what each unit does".
