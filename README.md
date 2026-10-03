# MinionsFactory

**Disciplined feature development with Claude Code, shipped as skills.** Each station of the line is an `mf-*`
skill, and a person conducts them. The skills carry these practices: **grill** an idea until its decisions are
settled, write it as a **spec-driven change** with checkable acceptance, and close it with a **check loop** of
fresh readers before it is released.

## The line

One change goes from an idea to a local tag.

```
   grill ───▶ cut ───────────▶ build ────▶ converge ──────────▶ release      the stations
     │         │                 │            │                    │
 `grilling`  mf-cut-change    mf-build     mf-converge          mf-release    the skills
                                           review ‖ security

   conducted by a person today · by an LLM conductor held by scripts: designed, not built
```

Each skill is the authority on what it does; this table is a map, not a summary.

| skill | what it is for |
| --- | --- |
| [`mf-cut-change`](skills/mf-cut-change/SKILL.md) | cut a change from a settled grilling, written to `mf-build`'s input contract |
| [`mf-build`](skills/mf-build/SKILL.md) | build the active change, one phase per pass, to a green gate |
| [`mf-converge`](skills/mf-converge/SKILL.md) | conduct the end-of-change review ‖ security loop, judging nothing itself |
| [`mf-release`](skills/mf-release/SKILL.md) | verify, fold, archive, cut the changelog, tag — then stop |

## Install

The skills install into your personal skills directory as symlinks (the `Makefile` records why a symlink).

```bash
make install-skills      # symlink skills/mf-* into your personal skills directory
make uninstall-skills    # remove exactly those symlinks
```

## What a target repo needs

A layout on disk, and nothing else: the skills install nothing into it
([D18](docs/decisions.md#d18--the-contract-with-a-target-repo-is-a-layout-on-disk)).

```
<target>/
├── openspec/specs/      the living spec
├── openspec/changes/    the active change, and the archive
├── Makefile             with a `gate` target
├── CLAUDE.md            what is true of this repo
└── .minions/            run output, gitignored
```

## This repo's gate

**`make gate`**: lock sync · format · lint (`D` docstrings + `ANN` annotations) · strict type-check · tests. The
`Makefile` recipe is the one list of its commands, so this page names the target and does not copy them. CI (`.github/workflows/ci.yml`) runs `make gate` on every push.

## Docs

Start at the [docs map](docs/README.md). It links [the principles](docs/principles.md), [the
decisions](docs/decisions.md) and [the autonomous design](docs/autonomous.md). What shipped, per version, is in
[`CHANGELOG.md`](CHANGELOG.md).

## The deterministic runner — deprecated

`orchestrator/` and `prompts/` hold a deterministic runner for the same line. It is not extended, and is deleted by
the change that retires it. Its design is in [architecture](docs/architecture.md).
