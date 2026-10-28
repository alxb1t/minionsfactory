# MinionsFactory — docs

The map of this repository's record. MinionsFactory is disciplined feature development with coding agents, shipped
as the `mf-*` skills: each station of the line is a skill, and a person conducts them.

```
   grill ───▶ cut ───────────▶ build ────▶ converge ──────────▶ release      the stations
     │         │                 │            │                    │
  mf-plan    mf-cut-change    mf-build     mf-converge          mf-release    the skills
                                           review ‖ security

   conducted by a person today · by an LLM conductor held by scripts: designed, not built
```

Executors load the skills with their own syntax. Convergence needs fresh observable workers with shared-disk
findings; generic workers can run sequentially. See [execution](../README.md#execution) for routing and evidence.

## The pages

What holds, and what was chosen.

| page | holds |
|---|---|
| [principles.md](principles.md) | the rules every station follows, each with why and what holds it |
| [decisions.md](decisions.md) | the choices in force, each with its reason |

## Where the rest lives

| where | holds |
|---|---|
| [`skills/`](../skills/) | station instructions, bundled generic role references and the bundled metrics script; Claude Code retains native engines |
| [`metrics/`](../metrics/) | MF's metrics catalogue and the data file each release records |
| [`scripts/metrics/`](../scripts/metrics/) | the metric scripts the catalogue names |
| [`openspec/specs/`](../openspec/specs/) | the living spec |
| [`openspec/changes/`](../openspec/changes/) | the active change, and the archive |
| [`CHANGELOG.md`](../CHANGELOG.md) | what shipped, per version |
| [`AGENTS.md`](../AGENTS.md) | what is true of this repository: the gate, the layout, the guardrails |
