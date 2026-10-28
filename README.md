# MinionsFactory

**Disciplined feature development with coding agents, shipped as skills.** Each station of the line is an `mf-*`
skill, and a person conducts them. The skills carry these practices: **grill** an idea until its decisions are
settled, write it as a **spec-driven change** with checkable acceptance, and close it with a **check loop** of
fresh readers before it is released.

## The line

One change goes from an idea to a tag on the default branch.

```
   grill ───▶ cut ───────────▶ build ────▶ converge ──────────▶ release      the stations
     │         │                 │            │                    │
  mf-plan    mf-cut-change    mf-build     mf-converge          mf-release    the skills
                                           review ‖ security

   conducted by a person today · by an LLM conductor held by scripts: designed, not built
```

Each skill is the authority on what it does; this table is a map, not a summary.

| skill | what it is for |
| --- | --- |
| [`mf-plan`](skills/mf-plan/SKILL.md) | grill a version to settled decisions and write the brief the cut reads |
| [`mf-bootstrap`](skills/mf-bootstrap/SKILL.md) | write a new repo's starting files and commit them, once, before the first cut |
| [`mf-cut-change`](skills/mf-cut-change/SKILL.md) | cut a change from a settled grilling, written to `mf-build`'s input contract |
| [`mf-build`](skills/mf-build/SKILL.md) | build the active change, one phase per pass, to a green gate |
| [`mf-converge`](skills/mf-converge/SKILL.md) | conduct the end-of-change review ‖ security loop, judging nothing itself |
| [`mf-release`](skills/mf-release/SKILL.md) | verify, fold, archive, cut the changelog, tag — then, on a yes, merge and push |

## Install

The skills install into your personal skills directory as symlinks (the `Makefile` records why a symlink).

```bash
make install-skills      # symlink skills/mf-* into your personal skills directory
make uninstall-skills    # remove the symlinks into this checkout
```

## Execution

Claude Code uses native `/simplify`, `/code-review` and `/security-review`; a required missing command halts.
Other and unidentified executors load the bundled generic roles. The host must support instruction loading and,
for convergence, fresh subagents or fresh agent processes whose completion and findings the conductor can read.
Generic workers may run sequentially over the same frozen head and need no remote review service.

Use each host's syntax to load the `mf-*` instructions. The editor, provider and model do not identify the
executor: Codex through Zed ACP, Zed's native agent and a Claude model through OpenRouter take the generic path.
Authentication and provider configuration belong to the operator. Model suggestions use offered menus and
supported controls; they do not change configuration.

Compatibility evidence belongs in the change's [smoke record](openspec/changes/archive/0027-migrate-to-agents/design.md#smoke-evidence).
Hosts without live evidence are described by required capabilities, not labeled tested.

## What a target repo needs

A layout on disk, and nothing else
([D18](docs/decisions.md#d18--the-contract-with-a-target-repo-is-a-layout-on-disk)). `mf-bootstrap` writes
it into a new repo; the other skills install nothing.

```
<target>/
├── openspec/specs/      the living spec
├── openspec/changes/    the active change, and the archive
├── Makefile             with a `gate` target
├── AGENTS.md            what is true of this repo
└── .minions/            run output, gitignored
```

`metrics/catalogue.toml` is optional: a repo that declares it gets its metrics measured at every change, and one
that does not is told so ([D43](docs/decisions.md#d43--project-health-is-measured-per-change-from-the-repos-own-catalogue)).

## This repo's gate

**`make gate`**: lock sync · format · lint (`D` docstrings + `ANN` annotations) · strict type-check · tests. The
`Makefile` recipe is the one list of its commands, so this page names the target and does not copy them. CI
(`.github/workflows/ci.yml`) runs `make gate` on every push.

## Docs

Start at the [docs map](docs/README.md). It links [the principles](docs/principles.md) and [the
decisions](docs/decisions.md). What shipped, per version, is in [`CHANGELOG.md`](CHANGELOG.md).
