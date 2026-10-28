# Release on a moved base — design

One ancestry check moves ahead of the release's irreversible steps, the late one names a recovery, and the default
branch is named the same way in every station. Verdict: ready to build. Scope is [the proposal](proposal.md);
behaviour is [the delta](specs/sdd/spec.md).

## Context

Premises were re-checked on `main` at `ee2e751` (v0.31.2) before the cut.

| evidence at the cut | implication |
|---|---|
| Release Step 1 holds preconditions 1–8 (`skills/mf-release/SKILL.md:69-101`); 6 and 8 are cited by number in the backlog and *Never weaken the gate to pass* (`docs/principles.md:100-102`) | the new check is appended as 9 ([D1](#d1)) |
| Step 5.1 checks `git merge-base --is-ancestor <default-branch> HEAD` (`:195-196`) after the commit (`:167`), the tag (`:181`) and the card deletions (`:183-187`) | a moved base strands the change ([D1](#d1), [D2](#d2)) |
| Converge's catch-up round accepts commits after the judged head that keep it an ancestor (`skills/mf-converge/SKILL.md:119-145`) | a merge-in is judged by one round ([D1](#d1)) |
| `<default-branch>` is undefined in build (`skills/mf-build/SKILL.md:191`), converge (`skills/mf-converge/SKILL.md:167-168`, "usually `main`"), release (`skills/mf-release/SKILL.md:99`); the cut says "the default branch" (`skills/mf-cut-change/SKILL.md:39`); `mf-plan` (`skills/mf-plan/SKILL.md:38`) defines it | [D3](#d3) |
| `uv run pytest --collect-only -q \| tail -1` prints `50 tests collected` | [Tests](#tests) |

## Goals / Non-Goals

**Goal:** a release never tags a branch whose base moved, and says exactly what to do when one has.

**Non-goals:** see [the exclusions](proposal.md#not-in-this-change).

## Decisions

The grilling settled these choices (the brief's Q2–Q7); the build does not reopen them.

### D1

| id | decision | because | rejected |
|---|---|---|---|
| D1 | Release precondition 9, appended to Step 1 | The fold, the commit, the tag and the card deletions come after Step 1; 6 and 8 are cited by number | Inserting it and renumbering |

```markdown
9. **The base has not moved** — `git merge-base --is-ancestor <default-branch> HEAD` exits 0. Else → halt, naming
   the way out:

       git merge <default-branch>        # resolve, then make gate
       /mf-converge                      # when converge ran: its catch-up round judges the merge
       /mf-release
```

### D2

| id | decision | because | rejected |
|---|---|---|---|
| D2 | Step 5.1 stays; its halt names the person's recovery, which the station never runs | `main` can move between precondition 9 and the person's yes; release edits no history | Dropping 5.1; a station that resets or deletes tags |

Step 5.1, after:

```markdown
1. **The default branch has not moved:** `git merge-base --is-ancestor <default-branch> HEAD` exits 0. Else halt:
   the gate judged this branch on its base, and a merge would ship a tree nobody checked. The release commit and
   `<tag>` exist; name the person's recovery, and run none of it:

       git tag -d <tag>
       git reset --hard HEAD~1           # the release commit
       git merge <default-branch>  ·  /mf-converge  ·  /mf-release
```

### D3

| id | decision | because | rejected |
|---|---|---|---|
| D3 | `mf-build`, `mf-converge`, `mf-cut-change` and `mf-release` each name the default branch as `mf-plan` does | One branch, found one way, in every station | A shared reference file; leaving it to each executor |

The line, at each station's first use of the default branch:

```markdown
The **default branch** is the one `git symbolic-ref --short refs/remotes/origin/HEAD` names after `origin/`, or
`main` when that fails.
```

Converge's *the repository's own default branch (usually `main`)* becomes *the default branch*.

## Tests

No test is added or removed: skill prose is held by review (D42).

| layer | at cut | added | removed | proof |
|---|---:|---:|---:|---|
| Unit test functions | 50 | 0 | 0 | `uv run pytest --collect-only -q \| tail -1` prints `50 tests collected` at the cut and after |
| Integration tests | 0 | 0 | 0 | — |
| End-to-end runs | 0 | 0 | 0 | — |

## Dependencies

None.

## Risks / Trade-offs

- **A base can still move after precondition 9** → 5.1 stays and names the recovery.
- **Converge is skipped, read by hand** → every phase is skill text.

## Migration Plan

```
1 the release: precondition 9 · Step 5.1's recovery ─▶ 2 the default branch named ─▶ release
```

Each phase ends on a green gate. Nothing is irreversible.

## Verdict

Ready to build. Acceptance: precondition 9 before the fold, 5.1's recovery named, and the default branch named in
the four stations.
