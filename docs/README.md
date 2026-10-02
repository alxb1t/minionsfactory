# MinionsFactory — docs

The map of this repository's record. MinionsFactory is disciplined feature development with Claude Code, shipped
as the `mf-*` skills: each station of the line is a skill, and a person conducts them.

```
   grill ───▶ cut ───────────▶ build ────▶ converge ──────────▶ release      the stations
     │         │                 │            │                    │
 `grilling`  mf-cut-change    mf-build     mf-converge          mf-release    the skills
                                           review ‖ security

   conducted by a person today · by an LLM conductor held by scripts: designed, not built
```

## The pages

What holds, what was chosen, and what is designed.

| page | holds |
|---|---|
| [principles.md](principles.md) | the rules every station follows, each with why and what holds it |
| [decisions.md](decisions.md) | the choices in force, each with its reason |
| [autonomous.md](autonomous.md) | the autonomous line's design: designed, not built |

## Deprecated

The deterministic runner in `orchestrator/` and `prompts/`, kept until the change that retires it.

| page | holds |
|---|---|
| [architecture.md](architecture.md) and [modules/](modules/) | the runner's pages |

## Where the rest lives

| where | holds |
|---|---|
| [`skills/`](../skills/) | what each station does, one `SKILL.md` each |
| [`openspec/specs/`](../openspec/specs/) | the living spec |
| [`openspec/changes/`](../openspec/changes/) | the active change, and the archive |
| [`CHANGELOG.md`](../CHANGELOG.md) | what shipped, per version |
| [`CLAUDE.md`](../CLAUDE.md) | what is true of this repository: the gate, the layout, the guardrails |
