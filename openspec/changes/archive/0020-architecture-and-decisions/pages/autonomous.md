# The autonomous line — the design

**Designed, not built.** A roadmap and its briefs go in; released versions come out, with no person between them.
An LLM conductor runs the same stations the operator runs by hand, and small deterministic scripts decide whether
each stage happened. The decisions behind this page are
[D24 to D35](decisions.md#the-autonomous-line); this page holds the shape they produce.

## The components

```
┌──────────────────────────────────── autonomous/ ─────────────────────────────────────────────┐
│  skills/mfa-orchestrate ── the conductor (LLM) · reads roadmap/ · loops versions · dispatches │
│      bin/mfa_check.py  ── deterministic: stage checks and `where`      exit code = verdict   │
│      bin/mfa_log.py    ── deterministic: the run log, its lock, --verify   insert-only        │
│  skills/mfa-cut-change ── no wait for a person · id from the roadmap · base-branch            │
│  skills/mfa-build      ── writes its changelog entries to a fragment, not CHANGELOG.md        │
│  skills/mfa-converge   ── base-branch · backlog to a fragment · logs through mfa_log.py       │
│  skills/mfa-integrate  ── merge in · catch-up · mfa-release · fast-forward      (serial)      │
│  skills/mfa-release    ── fold · archive · assemble CHANGELOG · release commit · never merges │
│  brief_template.md     ── what a brief must settle                                            │
│  README.md             ── install into a target · reset a run                                 │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
   grilling: the adopted `grilling` skill, run by a subagent that answers with its own recommendations
```

**Every stage takes** `change-id` (from the roadmap), `branch` (the loop branch) and `state-dir` (absolute); where
it applies, `base-branch` (the loop branch) and `autonomous`.

## The layout on disk

```
<target>/                                    ← main checkout · HEAD = the loop branch
├── roadmap/roadmap.md · roadmap/briefs/     ← the input, written by a person
├── openspec/ · CHANGELOG.md · the code      ← shared files: written only by integration
├── runs/<date>/                             ← the run record, committed once, at the end or a halt
└── .minions/                                ← THE state directory (gitignored)
    ├── runs/<date>/run_log.md               ← the one run log
    ├── findings/<change-id>_*.md            ← every version's converge evidence
    └── backlog.md · backlog.d/<change-id>.md

<target>.worktrees/                          ← a sibling: nothing run in the repo sees it
├── <change-id>/                             ← HEAD = that version's branch
└── <another-change-id>/                     ← side by side, once the width is above one
```

## A version's life

The states are what `mfa_check.py where` returns. Each arrow is one subagent, followed by a `check` line in the
log.

```
   grill ─────▶ cut ─────▶ build ─────▶ converge ─────▶ READY
     │ grilled    │ change     │ every box   │ both clean,    │
     │ brief      │ committed, │ ticked,     │ HEAD = judged  │
     │ committed  │ --strict   │ gate green  │ head (or off)  │
                                                              ▼
        ┌──── mfa-integrate (serial, in roadmap order, every `after:` integrated) ────┐
        │ 1 merge the loop branch into the version branch   (in the version's worktree) │
        │ 2 base moved? a catch-up round and the gate                                   │
        │ 3 mfa-release: fold · archive · CHANGELOG from the fragment · release commit  │
        │ 4 loop branch: merge --ff-only                     (in the main checkout)     │
        │ 5 backlog.d/<id> → backlog.md · the worktree removed                          │
        └──────────────────────────────────────────────────────────────── INTEGRATED ──┘
```

## A run

```
mfa-orchestrate <branch> <state-dir>
  │  log: start · git worktree prune
  │  where ──▶ the first version not INTEGRATED, at its stage
  │
  ├─ for each version whose `after:` are all INTEGRATED:          ← one at a time today
  │     worktree add (if missing)
  │     stage by stage:  log spawn ─▶ subagent ─▶ log finish ─▶ mfa_check <stage> ─▶ log check
  │                                                                │ exit ≠ 0 ─▶ log halt ─▶ STOP
  │     READY ─▶ mfa-integrate ─▶ INTEGRATED ─▶ log version-done
  │
  └─ log done ─▶ copy the run log and the record into runs/<date>/ ─▶ one commit on the loop branch
```

**The log's events:** a run's `start` · `preflight` · `halt` · `done`; a version's `version` · `merge` ·
`version-done`; any stage's `spawn` · `finish` · `check`; converge's `freeze` · `verdicts` · `pickup` ·
`backlog`; reserved, `remedy` · `retry`.

**Where a version stands, read from git:** archived and merged → done; a release commit not merged → merge; clean
and at the judged head, or converge off → release; every box ticked → converge; committed with a box open → build;
a grilled brief committed → cut; else grill.

## Git worktrees — what the design leans on

**A worktree is a directory where one branch is checked out**: one repository, several checkouts.

| shared by every worktree | each worktree's own |
|---|---|
| commits and objects · branches and tags · config and hooks · **the stash** | `HEAD` · the index · the files · untracked and ignored files · a merge in progress |

- **One branch, one worktree.** Git refuses a second checkout of a branch. So the main checkout owns the loop
  branch, each version branch lives only in its worktree, and integration runs in both places: the merge-in inside
  the worktree, `--ff-only` in the main checkout.
- **The commands a run uses:** `worktree add <path> -b <branch> <start>` · `list` · `remove`, which refuses a
  dirty tree · `prune`, which forgets directories deleted by hand.
- **The costs:** an install per worktree; a hand-deleted directory blocks re-adding its branch until `prune`; a
  bare `stash pop` can take another version's stash, so a stash is popped only by message; a tool that assumes
  `.git` is a directory breaks.

## Open

| | question | settled when |
|---|---|---|
| skills | whether `mfa-*` start as copies of `mf-*`, as parameters on them, or as different skills | the autonomous line is grilled |
| grill | a thin `mfa-grill` skill carrying the self-answer rule, or a prompt inside `mfa-orchestrate` | the first autonomous change is cut |
| fragment | the changelog fragment's shape, and how `mfa-release` assembles it | the first autonomous change is cut |
| width | how many versions at once; the queue's order when a later version is ready first | parallel versions are grilled |
| lock | two runs on one loop branch | not planned |
| remedy · retry | what the conductor may decide when a stage fails | a run has resumed from a halt |
| fold-back | whether the autonomous skills return into `mf-*` | the autonomous line has run a target end to end |
