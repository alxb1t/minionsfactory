# MinionsFactory — developer docs

MinionsFactory is a **CLI + orchestrator for autonomous Python feature development with Claude Code**: pointed
at a target repo, it drives an **in-repo change** to completion — a coder builds its `tasks.md` phase by phase
behind a strict quality gate, then review ‖ security ‖ simplify fan out and a converge loop drives their
blocking findings to clean. These docs are raw markdown — read them here or in any viewer.

## Reading order

1. This page — the map of what's where.
2. [architecture.md](architecture.md) — what it is, the load-bearing invariants, the one dependency graph.
3. [modules/driver.md](modules/driver.md) — the build-spine loop that ties every seam together; start there,
   then follow its links out to the seams it drives.

## Modules

| Module | What it does | Doc |
| --- | --- | --- |
| `driver` | The deterministic build-spine loop — advance the change or halt. | [driver.md](modules/driver.md) |
| `provider` | Spawn a role as a fresh headless instance; parse its result. | [provider.md](modules/provider.md) |
| `gate` | Run the target repo's own quality gate; report pass/fail. | [gate.md](modules/gate.md) |
| `state` | Reconstruct "where are we" from disk (the change + git head). | [state.md](modules/state.md) |
| `status` | Typed event stream → append-only log + snapshot + stdout. | [status.md](modules/status.md) |
| `diff` | Compute a commit-range diff; hand it to a read-only role as a file. | [diff.md](modules/diff.md) |
| `findings` | Read a role's findings file into a validated convergence verdict. | [findings.md](modules/findings.md) |
| `fanout` | Run review ‖ security ‖ simplify over the frozen diff. | [fanout.md](modules/fanout.md) |
| `converge` | Loop fix → gate → re-verify on blocking findings, or halt. | [converge.md](modules/converge.md) |
| `release` | Verify the release gate over disk facts; prepare locally + halt for the human. | [release.md](modules/release.md) |
| `__main__` | The composition root — wire the real adapters and run. | [main.md](modules/main.md) |

## Where the rest of the truth lives

- **The method itself** — spec-driven development as this project practises it, stated once above the tool
  layer — is [sdd.md](sdd.md): the one page here that is about the *method* rather than about this codebase.
- **The active change** lives **in the repo**, under `openspec/changes/<id>/` — proposal · design · tasks ·
  spec delta — and its `tasks.md` `## Progress` checklist is where the driver reads the phase pointer. The
  living, test-backed behavioural spec is `openspec/specs/`, which the delta folds into on release.
- **A run's own artefacts** live **in the target repo**, under the gitignored `.minions/`: each role's findings
  at `.minions/findings/<change-id>_<role>.md`, the coder's halt report at `.minions/HALT.md`, deferred work at
  `.minions/<version>_backlog.md`, and the event stream + snapshot. The orchestrator resolves no directory
  outside the repo it is pointed at.
- **Product intent and the narrative record** live in a **private Obsidian vault** kept by the human — the PRD,
  the rationale in its `decisions.md`. Nothing in the orchestrator reads or writes it.
- **What is *true* about the repo** (layout, gate, invariants) is in the root [`CLAUDE.md`](../CLAUDE.md).
- **What shipped, per version** is in [`CHANGELOG.md`](../CHANGELOG.md) (Keep a Changelog).

The docstrings in the code are the authoritative "what each unit does"; these docs add the map, the *why*, the
data flow across functions, and the cross-links.
