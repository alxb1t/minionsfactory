# 0024-bootstrap — design

**In one line:** a new skill, `skills/mf-bootstrap/`, writes a new repo's starting files from templates, runs the
gate and commits once; a scan holds the templates to D18; D2, D8, D18 and D21 are amended. Skill prose,
templates and one scan. **Verdict: feasible** ([why](#verdict)).

Motivation is in [proposal.md → Why](proposal.md#why). This page holds the decisions, the skill text, the
templates, the scan and the amended decisions.

## Context

- D18 draws the layout the skills need: `openspec/specs/`, `openspec/changes/`, `Makefile`, `CLAUDE.md`,
  `.minions/` (`docs/decisions.md:191-202`). It says the skills "install nothing into it" (`:193`); D2 says the
  same of the product (`:32`).
- D8 keeps the OpenSpec CLI out of every gate: "nothing in `make gate` or CI runs it" (`docs/decisions.md:83`).
- D21 has every commit end with `Change: <change-id>` (`docs/decisions.md:235`).
- The line needs more than D18's tree from a new repo:
  - `mf-cut-change` Step 1 needs the default branch, a clean tree and `make -n gate` printing a command;
  - converge and release run `git merge-base`, which needs a commit, and read `git show <base>:Makefile`;
  - `mf-build` appends under `## [Unreleased]` in `CHANGELOG.md`, and no skill creates the file;
  - an unignored `.minions/` fails the release's clean-tree check.
- `/security-review` reads `origin/HEAD`, so converge's security station needs an `origin` remote (D11).
- `tests/test_skills.py` scans every `skills/*/SKILL.md`: a skill naming `make gate` must name `make -n gate`
  (`tests/test_skills.py:21-39`).
- `make install-skills` links every `skills/mf-*` (`Makefile:37`), so the new skill installs with no change to it.
- `README.md` lists the skills (`:25-28`) and says the skills "install nothing" (`:41`); `CLAUDE.md` names them
  "cut, build, converge, release" (`:38`).

### Measurements

The OpenSpec CLI `1.11.0`, run 2026-10-06 in scratch directories:

| tree | `openspec validate --all --strict --no-interactive` |
|---|---|
| `openspec/.gitkeep` only | exit `1`: `No OpenSpec root found` |
| `openspec/config.yaml` only | exit `0`: `No items found to validate.` |
| `openspec/specs/.gitkeep` only | exit `0` |
| `openspec/config.yaml`, `specs/`, `changes/archive/` | exit `0` |

### Terms

| term | means |
|---|---|
| **the target** | the directory the skill runs in; it becomes the new repo |
| **a template** | a file under `skills/mf-bootstrap/templates/`, named for its target path plus `.tmpl` |
| **a collision** | a target path, or `openspec/`, that exists before the run and is not `README.md` or `.gitignore` |

## Goals / Non-Goals

**Goals**

- After one run in a new directory, `mf-cut-change` passes its Step 1 with nothing written by hand.
- The templates cannot drift from D18 unnoticed.

**Non-Goals**

- Adopting an existing codebase, adding CI or a remote, or choosing the target's toolchain.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="b1"></a>**B1** | **One skill writes the starting files, once:** `Makefile`, `CLAUDE.md`, `CHANGELOG.md`, `README.md`, `.gitignore`, `openspec/config.yaml`, `openspec/specs/.gitkeep`, `openspec/changes/archive/.gitkeep` | D18's tree plus what the stations assume and create nowhere; converge creates `.minions/` itself | CI, `docs/`, `.minions/` in the target · a template repo to clone |
| <a id="b2"></a>**B2** | **The file bodies are templates** in `skills/mf-bootstrap/templates/`, each named for its target path plus `.tmpl`: `templates/openspec/config.yaml.tmpl` → `openspec/config.yaml` | the skill stays short; the suffix stops `templates/.gitignore` ignoring paths and `templates/CLAUDE.md` loading as context in this repo | bodies inline in `SKILL.md` · bare names |
| <a id="b3"></a>**B3** | **No inputs.** The placeholders are `<name>`, the target's basename, and `<openspec-version>`, what `openspec --version` prints. No template carries a date | nothing to ask; the CLI version is what D8 records in `CLAUDE.md` | a `name` and a `what` parameter · a `<date>` placeholder |
| <a id="b4"></a>**B4** | **Git:** not a repo → `git init -b main`. One commit, `chore: bootstrap for minionsfactory`, staged by name, with `Co-Authored-By:` and no `Change:` trailer | the cut starts on a clean committed default branch; no change exists yet to name | leaving the commit to the human: the cut would halt on a dirty tree |
| <a id="b5"></a>**B5** | **A new repo only.** An existing `README.md` is skipped; an existing `.gitignore` gains the template's lines when no line reads `.minions/`. Any other collision halts, naming every one. The target must not sit inside another repo; a repo must be clean and on its default branch: `origin/HEAD`'s branch, or `main` with no `origin/HEAD`. Other files, `LICENSE` say, pass | a repo created on GitHub carries a README and a `.gitignore`; a `Makefile`, `CLAUDE.md`, `CHANGELOG.md` or `openspec/` means the repo is not new | skipping every existing file · merging into an existing `Makefile` |
| <a id="b6"></a>**B6** | **The gate validates the specs:** `gate:` runs `openspec validate --all --strict --no-interactive`. `openspec/config.yaml` holds `schema: spec-driven` | the spec is all a new repo has to check; a bare `openspec/` is no OpenSpec root ([Measurements](#measurements)) | `openspec/.gitkeep` alone · a `test -d` layout check |
| <a id="b7"></a>**B7** | **Checks around the write:** halt before writing when `openspec --version` fails or git has no `user.name` or `user.email`. After writing, run `make -n gate` and `make gate` and paste both; a red gate commits nothing and reports the files written | a bootstrap that leaves a red gate hands the cut a halt | committing and leaving the gate to the cut |
| <a id="b8"></a>**B8** | **The remote is reported, not added:** with no `origin`, the report says `/security-review` will not load, so converge's security station cannot run | adding a remote is outward-facing, and the human's | adding one · saying nothing |
| <a id="b9"></a>**B9** | **`CHANGELOG.md` is seeded empty:** the Keep a Changelog and SemVer header, then `## [Unreleased]`. No entry for the bootstrap | the bootstrap is not a version; the first build phase writes the first entry | an `Initial setup` entry |
| <a id="b10"></a>**B10** | **`CLAUDE.md` and `README.md` say only what is true of an empty repo:** the [templates](#the-templates) | facts, not a script; no seams or conventions exist yet | the full `CLAUDE.md` template with blanks to fill |
| <a id="b11"></a>**B11** | **A scan holds the templates to D18:** each directory entry but `.minions/` has a template under it, each file entry a template, `.gitignore` names `.minions/`, `CHANGELOG.md` and `README.md` exist, and the `Makefile` template names the validate line. A planted repo proves it bites | a template dropped, or a D18 entry added, turns the gate red | a scan of the skill's prose · no scan |
| <a id="b12"></a>**B12** | **D2, D8, D18 and D21 are amended** in `docs/decisions.md`, word for word in [the amended decisions](#the-amended-decisions): D2 and D18, the stations install nothing and the bootstrap writes once; D8, a target's gate may run the CLI and this repo's does not; D21, the bootstrap commit is the one without a `Change:` trailer | A7: a decision in force is edited where it lives; each would contradict the skill as it stands | a new decision beside the old ones |

## The skill

`skills/mf-bootstrap/SKILL.md`, whole:

````markdown
---
name: mf-bootstrap
description: Bootstrap a new repo for the mf-* line — write the gate, openspec/, CLAUDE.md, CHANGELOG.md, README.md and .gitignore from templates, run the gate, and commit once on main. Use in a new directory, or a freshly created repo, before the first mf-cut-change.
---

# mf-bootstrap — a new repo the line can cut in

> **Your role is BOOTSTRAP.** You write a new repo's starting files from the templates beside this file, prove
> the gate green, and commit once. You never overwrite a file, never add a remote, never push. A repo that
> already has its own setup is not new: halt.

```
  new directory ──▶ mf-bootstrap ──▶ committed main ──▶ mf-cut-change ──▶ mf-build …
```

## Parameters

None. The **target** is the current directory; the **name** is its basename.

## The files

The templates live in `templates/` beside this file. A template's **target path** is its path under `templates/`
without the `.tmpl` suffix: `templates/openspec/config.yaml.tmpl` → `openspec/config.yaml`.

| target path | when it already exists |
|---|---|
| `Makefile` · `CLAUDE.md` · `CHANGELOG.md` · `openspec/config.yaml` · `openspec/specs/.gitkeep` · `openspec/changes/archive/.gitkeep` | halt |
| `README.md` | skip it; the file stays as it is |
| `.gitignore` | append the template's lines when no line reads `.minions/`; else leave it |

The placeholders below are filled, and nothing else in a template changes:

- `<name>` → the target's basename, e.g. `lepalace_scheduler`;
- `<openspec-version>` → what `openspec --version` prints, e.g. `1.11.0`.

## Step 1 — Preconditions

Every one holds, or **halt** naming the one that failed:

- `openspec --version` runs. The gate runs the OpenSpec CLI; without it the gate is red.
- `git config user.name` and `git config user.email` each print a value.
- The target sits inside no other repo: `git rev-parse --show-toplevel` fails, or prints the target (`pwd -P`).
- When the target is a repo, `git status --porcelain` prints nothing, and `git branch --show-current` is the
  default branch: the one `git symbolic-ref --short refs/remotes/origin/HEAD` names after `origin/`, or `main`
  when that command fails.
- No collision: no `openspec/` directory, and no target path the table marks *halt*, exists. Name every
  collision in one halt. Adopting an existing repo is not this skill's job.

## Step 2 — Write

1. Not a repo → `git init -b main`.
2. Write each template to its target path, as the table says, with the placeholders filled. Create parent
   directories. Keep every other byte: the `Makefile` recipe line starts with a tab.
3. Keep a list of the paths written, skipped and appended.

## Step 3 — The gate

Run `make -n gate` and paste its output: it prints the `openspec validate` line. Then run `make gate` and paste
its output. It exits 0, or **halt**: commit nothing, and report the paths written so the human can inspect them.

## Step 4 — Commit

Stage each written or appended path by name — never `git add -A`. A skipped `README.md` is not staged. The
message is `chore: bootstrap for minionsfactory`, ending with:

    Co-Authored-By: <the attribution line this session uses>

No `Change:` trailer: no change exists yet. After the commit, `git status --porcelain` prints nothing, or halt.

## Step 5 — Report

- The paths written, skipped and appended.
- The commit id, and `git status --porcelain` printing nothing.
- When `git remote get-url origin` fails: no `origin` remote, so `/security-review` will not load and
  `mf-converge`'s security station cannot run until one is added.
- Next: `/mf-cut-change` with the first version's `change-id` and `version`.

Then stop.

## Never

- Never overwrite, truncate or reorder a file that exists. `.gitignore` is only appended to.
- Never write outside the target, or a path no template names.
- Never add a remote, push, or create a branch other than `main`.
- Never commit over a red gate.
- Never add a `Change:` trailer, a `CHANGELOG.md` entry, or a change under `openspec/changes/`.
- Never write a secret or a real absolute path from the machine the run is on into a file.
````

## The templates

Each under `skills/mf-bootstrap/templates/`, whole. A file shown empty is empty.

`Makefile.tmpl` — the recipe line starts with a tab:

```make
# The gate: the one list of the commands that say a change is done. Prose names
# `make gate` and never copies them. A new command lands through a change whose
# cut names this recipe in a task.
.PHONY: gate

gate:
	openspec validate --all --strict --no-interactive
```

`CLAUDE.md.tmpl`:

```markdown
# <name> — shared context for Claude Code

Work in progress: no code yet.

> **This file is what is true of this repo. It is not a script.** What to do comes from the task you were given.

## The quality gate — `make gate`

The gate is **`make gate`**, run at the repository root. The `Makefile` recipe is the one list of its commands;
prose names `make gate` and never copies them. Today it validates the specs. A new command lands through a change
whose cut names the gate recipe in a task.

## How a change is cut here

Each version is one change, cut, built, checked and released with the MinionsFactory `mf-*` skills. The OpenSpec
CLI is recorded, not pinned: `@fission-ai/openspec@<openspec-version>`, resolved on `PATH`.

## Layout — where things live here

- **`openspec/`** — the living specs in `specs/`; the changes in `changes/`, the shipped ones in `changes/archive/`.
- **`.minions/`** — run artefacts, **gitignored**; nothing in it is tracked.
- **`CHANGELOG.md`** — Keep a Changelog: each phase appends under `## [Unreleased]`, the release cuts it.

## Guardrails (hold for every role)

- **Never commit a secret, or a real absolute path from the machine the run is on.**
- **Dependencies are minimal and human-approved.** Argue for a new one, and wait for approval before installing it.
- **Never weaken the gate to pass.** A deleted test, a blanket suppression, a loosened config: halt and say so.
- **State lives on disk.** Rebuild where the work is from the active change's `tasks.md` and git.
```

`CHANGELOG.md.tmpl`:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0/).

## [Unreleased]
```

`README.md.tmpl`:

```markdown
# <name>

Work in progress.

The gate is `make gate`. Built with the [MinionsFactory](https://github.com/alxb1t/minionsfactory) skills.
```

`.gitignore.tmpl`:

```gitignore
# Run output, not source: `git add -A` would sweep it into history.
.minions/
```

`openspec/config.yaml.tmpl`:

```yaml
schema: spec-driven
```

`openspec/specs/.gitkeep.tmpl` and `openspec/changes/archive/.gitkeep.tmpl` — empty.

## The scan

In `tests/test_skills.py`, after the last scan, in the file's pattern: a problems function over `base`, a test on
the repo, a test on a planted repo.

- `_layout_problems(base)` reads D18's tree from `base/docs/decisions.md` — the lines matching `^[├└]── (\S+)`
  between `### D18` and the next `### ` — and lists the files under `base/skills/mf-bootstrap/templates/`, each
  mapped to its target path by dropping `.tmpl`. It returns one line per breach of [B11](#b11), e.g.
  `` skills/mf-bootstrap/templates: no template for `CLAUDE.md` ``.
- `test_the_bootstrap_templates_cover_the_target_layout` asserts the repo has none.
- `test_the_layout_scan_reports_every_breach` plants a D18 tree, and templates with no `CLAUDE.md`, no
  `README.md`, a `.gitignore` without `.minions/` and a `Makefile` without the validate line, and asserts each
  breach is reported.

A comment above the constants cites `0024-bootstrap design B11`, as the file's other scans do.

## The scratch runs

Run in phase 1 by a **fresh sub-agent**: one given only the path of `skills/mf-bootstrap/SKILL.md` and the scratch
directory, never this change. Each directory is removed first.

| run | setup | the sub-agent |
|---|---|---|
| **empty** | `mkdir /tmp/mf-bootstrap-empty` | runs the skill |
| **github** | `/tmp/mf-bootstrap-github`: `git init -b main`; `README.md` (`# github`), `LICENSE` (`MIT`), `.gitignore` (`*.pyc`), committed | runs the skill |
| **again** | the **empty** run's result | runs the skill again; its halt names `Makefile`, `CLAUDE.md`, `CHANGELOG.md` and `openspec/` |
| **cut** | the **again** run's result | runs `/mf-cut-change change-id=0001-hello version=v0.1` from one settled line, *`README.md` gains the line `Hello.`*, and stops at Step 9, declining |

## The amended decisions

In `docs/decisions.md`. Titles and anchors stay, so `README.md`'s D18 link holds.

**D2**, the bold line's last sentence:

```
before:  is not a framework, and it installs nothing into the repo it works on.**
after:   is not a framework. The stations install nothing into the repo they work on; `mf-bootstrap` writes a new
         repo's starting files, once.**
```

**D8**, the bold paragraph, and a bullet after **Accepts:**:

```
before:  **Its version is written in `CLAUDE.md`; nothing in `make gate` or CI runs it. The cut runs `openspec validate`; the
         gate does not.**
after:   **Its version is written in `CLAUDE.md`. This repo's `make gate` and CI never run it; the cut runs
         `openspec validate`. A target's gate may: the one `mf-bootstrap` writes validates the specs.**

added:   - **Why a target's gate may:** a new target has no CI to turn red, and its spec is all it has to check.
```

**D18**, the bold line, and a bullet after **Why:**:

```
before:  **The skills need the layout below from a repo, and nothing else. They install nothing into it.**
after:   **The skills need the layout below from a repo, and nothing else. The stations install nothing into it;
         `mf-bootstrap` writes it once into a new repo, `.minions/` as a `.gitignore` line, with `CHANGELOG.md` and
         `README.md`.**

added:   - **Held in step by:** the layout scan in `tests/test_skills.py`: every entry of the tree has a template in
           `skills/mf-bootstrap/templates/`.
```

**D21**, the bold line:

```
before:  **A commit ends with `Change: <change-id>`, in the trailer block, contiguous with `Co-Authored-By:`.**
after:   **A commit ends with `Change: <change-id>`, in the trailer block, contiguous with `Co-Authored-By:`. The
         bootstrap commit, made before any change exists, is the one without it.**
```

## The front door

`README.md`, a first row in the skills table:

```
| [`mf-bootstrap`](skills/mf-bootstrap/SKILL.md) | write a new repo's starting files and commit them, once, before the first cut |
```

`README.md`, *What a target repo needs*:

```
before:  A layout on disk, and nothing else: the skills install nothing into it
         ([D18](docs/decisions.md#d18--the-contract-with-a-target-repo-is-a-layout-on-disk)).
after:   A layout on disk, and nothing else
         ([D18](docs/decisions.md#d18--the-contract-with-a-target-repo-is-a-layout-on-disk)). `mf-bootstrap` writes
         it into a new repo; the other skills install nothing.
```

`CLAUDE.md`, the `skills/` line:

```
before:  the `mf-*` skills, one `SKILL.md` each: cut, build, converge, release.
after:   the `mf-*` skills, one `SKILL.md` each: bootstrap, cut, build, converge, release.
```

## Dependencies

None.

## Risks / Trade-offs

- **[A moving CLI turns a target's gate red]** → accepted ([B12](#b12)): the target has no CI, and the operator
  sees it at the next gate run.
- **[The skill is proved by scratch runs, not a test]** → the scan holds the templates; the run itself is checked
  by a fresh sub-agent in the build ([the scratch runs](#the-scratch-runs)).
- **[A target nested in another repo]** → Step 1 halts on it; the OpenSpec CLI would also resolve the outer
  `openspec/`.
- **[`origin/HEAD` unset in a clone]** → the default branch falls back to `main`; a repo on another branch halts
  and the human switches.

## Verdict

**Feasible.** Every file is new except the D2, D8, D18 and D21 paragraphs, the README's table and target
section, the `CLAUDE.md` skills line and the scan; the
measurements show the gate exits 0 on the tree the skill writes.
