# Worktree cleanup — design

The release's one ask names the worktree it will remove and the ignored paths inside it; README and 0034's record
say what is true. Verdict: ready to build. Scope is [the proposal](proposal.md); behaviour is
[the delta](specs/sdd/spec.md).

## Context

Premises were re-checked on `main` at `193a550` (v0.33.0) before the cut.

| evidence at the cut | implication |
|---|---|
| Step 5's ask is `Merge <branch> into <default-branch> and push? (yes/no)` (`skills/mf-release/SKILL.md:214`); item 6 retains the worktree on any path `git ls-files --others --ignored --exclude-standard` lists (`:234-237`) | a built worktree always holds `.venv/` and caches, so it is never removed ([D1](#d1)) |
| In a scratch repo on git 2.54.0, a linked worktree holding an ignored `.venv/` is listed by `git ls-files --others --ignored --exclude-standard --directory` as `.venv/`, and `git worktree remove` without `--force` removes it and exits 0 | the guard was MF's, not git's; `--directory` gives one name per ignored folder ([D1](#d1)) |
| `.gitignore` holds rebuildable entries (`.venv/`, `__pycache__/`, `.ruff_cache`, `.pytest_cache`) beside ones that are not (`.env`, `.idea/`, `.vscode/`) | no list of rebuildable outputs exists; the person reads the names ([D1](#d1)) |
| The spec requirement *The release merges and pushes on the person's yes* holds the removal at `openspec/specs/sdd/spec.md:370-372`, scenarios `:393-396` and `:398-400` | the [delta](specs/sdd/spec.md) corrects it |
| README names the primary `main/`: the tree at `README.md:84`, the runbook at `:92-96` | [D2](#d2) |
| The archived 0034 proposal says "every route that silences a check halts" (`openspec/changes/archive/0034-gate-recipe-hardening/proposal.md:8-9`); `CHANGELOG.md:67`, under `[0.31.2]`, says "a branch can no longer certify its own weakened gate"; the archived design's D7 (`design.md:92`) puts a file make reads at parse time out of reach | [D3](#d3) |
| `uv run pytest --collect-only -q \| tail -1` prints `58 tests collected in 0.07s` | [Tests](#tests) |

## Goals / Non-Goals

**Goal:** a release from a built worktree removes it on the person's yes, and the person sees what goes with it.

**Non-goals:** see [the exclusions](proposal.md#not-in-this-change).

## Decisions

The grilling settled these choices (the brief's Q1–Q5); the build does not reopen them.

### D1

| id | decision | because | rejected |
|---|---|---|---|
| D1 | Step 5's one ask names the worktree and its ignored paths; item 6 removes it on yes with plain `git worktree remove` | Git deletes ignored files on a plain remove; naming them keeps one question and shows a `.env` before it goes | A list of rebuildable outputs: hardcoded it is Python-only, declared in `AGENTS.md` it is a new parameter a patch cannot add |

Step 5's ask, before:

```markdown
Ask once, and wait: `Merge <branch> into <default-branch> and push? (yes/no)`. Anything but yes → Step 6.
```

After:

```markdown
Ask once, and wait: `Merge <branch> into <default-branch> and push? (yes/no)`. Anything but yes → Step 6.

When this checkout is a linked worktree other than the primary, the ask names it and what goes with it. List its
ignored paths by name, never reading a file: `git -C <this worktree> ls-files --others --ignored --exclude-standard
--directory`. Then ask `Merge <branch> into <default-branch> and push? The worktree <this worktree> goes too, with:
<the listed paths> (yes/no)`, the `with:` part dropped when nothing is listed. A listing that fails → ask
`… and push? The worktree <this worktree> stays: its ignored paths could not be listed. (yes/no)`.
```

Item 6, before:

```markdown
6. **Remove the version's worktree**, when this checkout is a linked worktree other than the primary:
   inspect `git -C <this worktree> ls-files --others --ignored --exclude-standard` without reading file contents.
   Any ignored path, or a failed check → retain the worktree and report cleanup skipped; otherwise
   `git -C <primary> worktree remove <this worktree>`, keeping the branch. A refusal is reported, never forced.
```

After:

```markdown
6. **Remove the version's worktree**, when the ask said it goes: `git -C <primary> worktree remove
   <this worktree>`, keeping the branch; git deletes the ignored paths the ask named. A refusal is reported, never
   forced.
```

### D2

| id | decision | because | rejected |
|---|---|---|---|
| D2 | README's tree and runbook name the primary `<repo>/`; the archived 0036 design keeps `<container>/main` | The primary is named after the repository; an archive is a record | Editing the archive |

`README.md:84`, before → after:

```text
├── main/              the primary checkout, on the default branch; .minions/ lives here
├── <repo>/            the primary checkout, named after the repository, on the default branch; .minions/ lives here
```

The runbook, `README.md:92-96`: `<container>/main` → `<container>/<repo>` in steps 1, 2 and 3, and the
command `mv <repo> <repo>.tmp && mkdir <repo> && mv <repo>.tmp <repo>/main` →
`mv <repo> <repo>.tmp && mkdir <repo> && mv <repo>.tmp <repo>/<repo>`.

### D3

| id | decision | because | rejected |
|---|---|---|---|
| D3 | The archived 0034 proposal and the `[0.31.2]` entry are corrected in place to D7's claim | No rule forbids it; git keeps the old text (D23); a new note leaves the `[0.31.2]` reader misled | Closing `0034·R3` unfixed; a correction under `[Unreleased]` |

`openspec/changes/archive/0034-gate-recipe-hardening/proposal.md:8-9`, before → after:

```markdown
A branch can no longer certify its own weakened gate: both sides' dry runs come from fresh exports, and every
route that silences a check halts.

A branch can no longer certify a gate it weakened through a gate makefile or the dry run: both sides' dry runs come
from fresh exports, and an unplanned change to either halts. A file make reads at parse time is out of reach
([D7](design.md#d7)).
```

`CHANGELOG.md:67`, in the `[0.31.2]` phase-1 entry: `a branch can no longer certify its own weakened gate` →
`a file make reads at parse time stays out of its reach`.

## Tests

No test is added or removed: skill prose is held by review (D42).

| layer | at cut | added | removed | proof |
|---|---:|---:|---:|---|
| Unit test functions | 58 | 0 | 0 | `uv run pytest --collect-only -q \| tail -1` prints `58 tests collected` at the cut and after |
| Integration tests | 0 | 0 | 0 | — |
| End-to-end runs | 0 | 0 | 0 | — |

## Dependencies

None.

## Risks / Trade-offs

- **A yes deletes an ignored `.env` in the worktree** → the ask names it first; the person answers.
- **This release runs the old Step 5.6** → its own worktree is removed by hand; the next release from a worktree is
  the live check.
- **Converge is skipped, read by hand** → every phase is skill text or docs.

## Migration Plan

```
1 the release names and removes the worktree ─▶ 2 the records corrected ─▶ release
```

Each phase ends on a green gate. Nothing is irreversible.

## Verdict

Ready to build. Acceptance: the ask names the worktree and its ignored paths, item 6 removes it on yes, README names
the primary `<repo>/`, and 0034's claims match D7.
