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
