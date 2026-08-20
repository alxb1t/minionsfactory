# MinionsFactory — developer docs

MinionsFactory is a **CLI + orchestrator for autonomous Python feature development with Claude Code**: pointed
at a target repo, it drives a vault-backed implementation plan to completion — a coder builds it phase by phase
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
| `driver` | The deterministic build-spine loop — advance the plan or halt. | [driver.md](modules/driver.md) |
| `provider` | Spawn a role as a fresh headless instance; parse its result. | [provider.md](modules/provider.md) |
| `gate` | Run the target repo's own quality gate; report pass/fail. | [gate.md](modules/gate.md) |
| `state` | Reconstruct "where are we" from disk (plan + git head). | [state.md](modules/state.md) |
| `status` | Typed event stream → append-only log + snapshot + stdout. | [status.md](modules/status.md) |
| `diff` | Compute a commit-range diff; hand it to a read-only role as a file. | [diff.md](modules/diff.md) |
| `findings` | Read a role's findings file into a validated convergence verdict. | [findings.md](modules/findings.md) |
| `fanout` | Run review ‖ security ‖ simplify over the frozen diff. | [fanout.md](modules/fanout.md) |
| `converge` | Loop fix → gate → re-verify on blocking findings, or halt. | [converge.md](modules/converge.md) |
| `__main__` | The composition root — wire the real adapters and run. | [main.md](modules/main.md) |

## Where the rest of the truth lives

- **The plan + settled design decisions** live in a **private Obsidian vault** (its path is in `.env` →
  `VAULT_PROJECT_DIR`, never committed); the active plan is the highest-versioned
  `implementation_plans/vX.Y_*implementation_plan.md`, and rationale sits in its `decisions.md`.
- **What is *true* about the repo** (layout, gate, invariants) is in the root [`CLAUDE.md`](../CLAUDE.md).
- **What shipped, per version** is in [`CHANGELOG.md`](../CHANGELOG.md) (Keep a Changelog).

The docstrings in the code are the authoritative "what each unit does"; these docs add the map, the *why*, the
data flow across functions, and the cross-links.
