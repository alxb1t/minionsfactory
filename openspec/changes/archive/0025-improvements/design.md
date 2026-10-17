# 0025-improvements — design

**In one line:** one close-out rule in every `mf-*` skill; the cut commits without waiting; the release asks once,
then merges and pushes; a HUMAN phase carries commands and halts with a checklist; a scan per rule; D7, D8, D17
amended and D38 added. Skill prose, docs and scans. **Verdict: feasible** ([why](#verdict)).

Motivation is in [proposal.md → Why](proposal.md#why). This page holds the decisions and the text to place, word
for word.

## Context

- **The reports:** `mf-build` Step 4 reports *"the output of each verification"* (`skills/mf-build/SKILL.md:158-161`),
  and Step 2 item 2 has it pasted *"into your report"* (`:106-109`). `mf-converge` Step 10 reports numbered
  blocks (`skills/mf-converge/SKILL.md:365-379`); `mf-release` Step 5 too (`skills/mf-release/SKILL.md:173-202`).
  `mf-cut-change` Step 11 ends *"Next: `/mf-build <change-id>`"* (`skills/mf-cut-change/SKILL.md:121-124`);
  `mf-bootstrap` Step 5 ends *"Next: `/mf-cut-change` …"* (`skills/mf-bootstrap/SKILL.md:70-78`).
- **The cut's waits:** Step 9 *"wait[s] for their OK"* and takes an OK for each dependency and every `Verify:`
  (`skills/mf-cut-change/SKILL.md:105-111`); Step 8 says the build runs the checks *"after the human's OK"* (`:96`);
  the role line says it commits *"only after they read it"* (`:8-10`); *Never* holds *"Never commit before the
  human's OK"* (`:225`); the description says *"commit on their OK"* (`:3`).
- **The record of the wait:** D7 ends *"The person's OK precedes the commit."* (`docs/decisions.md:75-78`);
  `docs/principles.md:40-41` names *"The person's read before the commit"* as an independent check; the spec
  requirement *The cut runs no check before the human reads it* says *"after the human's OK"*
  (`openspec/specs/sdd/spec.md:209-217`); a test comment says the same (`tests/test_skills.py:666`).
- **A dependency changed after the cut already stops the build:** stop-condition 4 reads `## Dependencies` at the
  commit that adds `design.md` (`skills/mf-build/SKILL.md:173-178`).
- **The release never merges:** D17 (`docs/decisions.md:180-187`); the role line (`skills/mf-release/SKILL.md:8-11`);
  the hand-off with a squash caveat (`:189-202`); *Never* (`:206-207`); the description (`:3`); `README.md:10`
  (*"to a local tag"*) and `:29` (*"tag — then stop"*). Merges so far are `Merge branch '<branch>'` with no
  trailer (`git log -1 --format=%B ca5aa96`).
- **HUMAN phases:** `I14` in both skills (`skills/mf-cut-change/SKILL.md:145`, `skills/mf-build/SKILL.md:50`); the
  build *"print[s] its sub-tasks as the person's checklist"* (`skills/mf-build/SKILL.md:96-101`).
- **The scans:** `_section_lines` ends a section at any line starting `## ` (`tests/test_skills.py:70-79`), so text
  placed in a section must not start a line with `## `. `_needle_problems` joins a section's lines with `\n`, so a
  needle must sit on one line (`:235-259`).
- **The cards:** `0024·N1` — D8's title (`docs/decisions.md:82`); `0024·N2` — the `.gitignore` row
  (`skills/mf-bootstrap/SKILL.md:29`).

### Terms

| term | means |
|---|---|
| **the close-out** | the report a station gives when it finishes without a halt |
| **the close-out line** | the literal rule, [below](#the-close-out-line), carried word for word by every `mf-*` skill |
| **the person's checklist** | what `mf-build` prints when a HUMAN phase's checks fail |

## Goals / Non-Goals

**Goals**

- A finished station reads in a few seconds and names what comes next.
- No routine *"please commit"*, and no merge typed by hand.
- A HUMAN phase is copy, run, tick.

**Non-Goals**

- Changing what any station checks, judges or halts on, beyond the merge's own guards.
- The autonomous `mfa-*` skills (D26).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="b1"></a>**B1** | **One close-out line**, word for word in the report step of `mf-bootstrap`, `mf-cut-change`, `mf-build`, `mf-converge` and `mf-release`: at most three sentences, then `Next: <the next act>`; the detail stays on disk | one rule cannot drift between stations; the long reports are not read | an id table shared by two owners, as `P` is: five carriers have no owner |
| <a id="b2"></a>**B2** | **The `Next:` lines:** bootstrap → `/mf-cut-change`; cut → `/mf-build <change-id>`; build → `/mf-converge`; converge, on `done` only → `/mf-release`; release after the push → `grill the next version.`; release with no merge → `merge and push` and the commands | the last line is the next act | `Next:` on a halt: a halt names its own way out |
| <a id="b3"></a>**B3** | **A halt stays in full; a HUMAN halt is its checklist.** The build's close-out gives verification counts and names any that failed; each output shows in the session as it runs | the halt is the report the human must read; the evidence is the command that exited, not its copy | counts on a halt |
| <a id="b4"></a>**B4** | **The cut commits without waiting.** Step 9 shows, then Step 10 commits. An edit after it is a further trailered commit, `docs(<change-id>): amend the change directory` | the cut is almost always right; a wrong one costs one commit | an OK every time |
| <a id="b5"></a>**B5** | **Still waiting:** a `## Dependencies` that is not `None.`, an OK per package; and a self-check item the cut cannot meet | the supply-chain principle keeps its person; both are rare | no wait at all, approval by starting the build |
| <a id="b6"></a>**B6** | **Starting `/mf-build` is the OK for the `Verify:` commands**, shown word for word in Step 9. **D38** records B4–B6; D7, `docs/principles.md` and the spec requirement are amended to match | A7: a decision in force is edited where it lives | — |
| <a id="b7"></a>**B7** | **`mf-release` Step 5 asks once:** `Merge <branch> into <default-branch> and push? (yes/no)`. Anything but yes prints the commands | the yes is the person's act; one question, not a second skill | a separate `mf-merge` · merging without asking |
| <a id="b8"></a>**B8** | **On yes:** halt unless `git merge-base --is-ancestor <default-branch> HEAD` exits 0; `git switch <default-branch>`; `git merge --no-ff`; `git diff --quiet <branch> <default-branch>` exits 0; push the default branch, then the tag `<version>.0`. Never `--force`, never pull, never the version branch | an unmoved base merges to exactly the tree the gate judged, so no second gate run; a moved one would ship an unjudged tree | `--ff-only` (D29's, for the autonomous line) · resolving conflicts · pushing the branch |
| <a id="b9"></a>**B9** | **The merge commit carries the trailer block:** `Merge branch '<branch>'`, then `Co-Authored-By:` and `Change: <change-id>`, contiguous | D21: every commit names its change; a station's commit is no exception | the bare message a person's merge has |
| <a id="b10"></a>**B10** | **No `origin`:** merge, push nothing, say so in one sentence. **A rejected push:** halt; the default branch stays merged locally; report the error and the push commands. **D17**, `README.md` and the skill's description and role line are amended | nothing outward is retried by guessing | pulling and retrying |
| <a id="b11"></a>**B11** | **`I14` asks for commands:** each HUMAN sub-task is exact commands with real values — names, tags, repo-relative paths; a step with no command is one line naming the file and the exact text; a value known only at run time is the command that prints it, then the edit that uses it | written at the cut, the commands are read and fixed by a commit; made up at the halt, nobody reads them first | the build working out commands from prose |
| <a id="b12"></a>**B12** | **The person's checklist:** the phase as `<N> — <Title> · HUMAN`; `cd <the repository root>` in chat only; a `- [ ]` line per step with its commands in an `sh` block; secrets by env-var name, never a value; the failing checks; `Next: /mf-build` | copy, run, tick; a heading line starting `## ` would end the scanned section | a `##` heading in the checklist |
| <a id="b13"></a>**B13** | **A scan per rule** in `tests/test_skills.py`, each with a planted twin that fails ([the scans](#the-scans)) | a rule no scan holds drifts | no scans for prose rules |
| <a id="b14"></a>**B14** | **`0024·N1`:** D8's title says *this repo's gate*. **`0024·N2`:** the `.gitignore` row appends *starting on a new line* | both triggers fire in this change | — |

## The close-out line

The first line starts the line, so the scan's needle never wraps:

```markdown
**Close-out:** at most three sentences — what happened, the gate's exit code, and anything the human must act on
— then a last line, `Next: <the next act>`. The detail stays on disk; a halt is reported in full.
```

## The report steps

Each replaces the step's body below its heading, which stays. `<the close-out line>` is the text above.

**`skills/mf-bootstrap/SKILL.md`, `## Step 5 — Report`:**

```markdown
<the close-out line>

Your sentences: the paths written, skipped and appended; the commit id, with `git status --porcelain` printing
nothing; and, when `git remote get-url origin` fails, that there is no `origin` remote, so `/security-review` will
not load and `mf-converge`'s security station cannot run until one is added.

The last line: `Next: /mf-cut-change with the first version's change-id and version.` Then stop.
```

**`skills/mf-cut-change/SKILL.md`, `## Step 11 — Report`:**

```markdown
<the close-out line>

Your sentences: the branch, the commit id, and `git status --porcelain` printing nothing. Then suggest models, as
[Suggesting models](#suggesting-models) says. The last line: `Next: /mf-build <change-id>, in a fresh session.`
Then stop.
```

**`skills/mf-build/SKILL.md`, `## Step 4 — Report, then stop`:**

```markdown
<the close-out line>

Your sentences: the phases built, the gate's exit code, how many verifications ran and passed — naming any that
did not — and that the simplify commit has landed. The last line: `Next: /mf-converge, in a fresh session.` Then
**stop** and hand back.
```

And Step 2 item 2, before → after: *"Paste the command's real output into your report."* → *"Show the command's
real output as it runs."*

**`skills/mf-converge/SKILL.md`, `## Step 10 — Report, then stop`:**

```markdown
<the close-out line>

Your sentences: the verdicts and the round, read from disk; each blocking finding's end state, by id; the cards
written, by qualified id, and the backlog's total card count, so a vanished file shows as a drop; the gate's exit
code, re-run by you at the end. The rest is on disk: the findings files, the status log and `.minions/backlog.md`.

Write `done` to the status log. The last line: `Next: /mf-release, in a fresh session.` Then **stop**.
```

**`skills/mf-release/SKILL.md`, `## Step 5 — Close: report, and stop`,** in phase 1 — the paragraph on the Step 4.3
gate stays above it:

````markdown
<the close-out line>

Your sentences: the release commit and the tag, with the Step 4.3 gate's exit code; `converge ran`, or
`converge: skipped — no findings files`; the paid-down cards, or `backlog: none`. A preamble flagged for a
hand-edit (Step 2) is something the human must act on.

The last lines — the merge and the push are the human's:

    Next: merge and push — release <version>.0 is on branch <branch>, NOT merged, NOT pushed:
      git checkout <default-branch>
      git merge --no-ff <branch>
      git push origin <default-branch>
      git push origin <version>.0

    Squash caveat: a squash-merge leaves the local tag pointing at the branch commit —
    re-tag the resulting commit on the default branch before pushing the tag.

Then **STOP**. Do not run the merge, the push, or a checkout of the default branch yourself.
````

Phase 3 replaces it, [below](#the-release-merges-and-pushes).

## The cut commits

**`skills/mf-cut-change/SKILL.md`:**

- the description, before → after: *"check them, show the human, and commit on their OK."* → *"check them, commit,
  and show the human."*
- the role line, before → after: *"and you commit it only after they read it."* → *"and you commit it once its
  self-check passes."*
- Step 8's first bullet, before → after: *"The build runs them, after the human's OK."* → *"The build runs them,
  once the human starts it."*
- Step 8's last paragraph, before → after: *"the human's read in Step 9"* → *"the human's read of the committed
  change"*.
- `## Step 9 — Show` becomes:

```markdown
## Step 9 — Show, then commit

Show the human what the change does, its phases, its decision ids, the self-check table, the file list, and every
`Verify:` word for word: the build runs them once the human starts it. Then go to Step 10 and commit without waiting.

These wait for the human's OK before Step 10. A `## Dependencies` that is not `None.`: show it word for word,
and get an OK for each package. A self-check item the cut cannot meet (Step 8). On edits, go back to Step 7.

An edit the human asks for after the commit is a further commit on the branch,
`docs(<change-id>): amend the change directory`, with the same trailer block.
```

- *Never*, before → after: *"Never commit before the human's OK."* → *"Never commit a `## Dependencies` that is not
  `None.` before the human's OK."*

**`docs/decisions.md`:**

- D7's bold paragraph, before → after: *"checks them before a person reads the change. The person's OK precedes the
  commit."* → *"checks them before it commits the change ([D38](#d38--the-cut-commits-without-waiting))."*
- D38, the last entry of `## Planning`, after D10:

```markdown
### D38 · The cut commits without waiting

**`mf-cut-change` commits the change once its self-check passes, and the person reads it after. A `## Dependencies`
that is not `None.`, and a self-check item the cut cannot meet, still wait for the person's OK. Starting
`/mf-build` is the OK for the `Verify:` commands.**

- **Why:** the cut is almost always right, and a wrong one costs one more commit; the wait cost a *"please commit"*
  every time.
- **Accepts:** an edit after the read is a further commit on the branch, before the build.
```

- the map's Planning ids, before → after: `D5…D10` → `D5…D10, D38`.

**`docs/principles.md`**, the accepted exception, before → after: *"The person's read before the commit and"* →
*"The person's read of the committed change and"*.

## The release merges and pushes

**`skills/mf-release/SKILL.md`:**

- the description, before → after: *"cut the changelog and tag locally, then stop without merging or pushing."* →
  *"cut the changelog and tag, then on the person's yes merge into the default branch and push."*
- the title, before → after: `# mf-release — verify, fold, archive, tag, stop` →
  `# mf-release — verify, fold, archive, tag, then merge and push on a yes`
- the role block, whole:

```markdown
> **You verify and finalize, then ask.** You never edit feature code or lower a bar to ship. If any precondition
> fails, **halt** naming exactly what is missing and who owns it. The merge and the push are high-consequence:
> you run them only on the person's yes, asked once in Step 5.
```

- a new step after Step 4, and the close renumbered:

````markdown
## Step 5 — Merge and push, on the person's yes

Ask once, and wait: `Merge <branch> into <default-branch> and push? (yes/no)`. Anything but yes → Step 6.

On yes, in order. A failure is a **halt**: report the error and the commands still to run.

1. **The default branch has not moved:** `git merge-base --is-ancestor <default-branch> HEAD` exits 0. Else
   halt: the gate judged this branch on its base, and a merge would ship a tree nobody checked.
2. **Merge:** `git switch <default-branch>`, then `git merge --no-ff <branch>` with the message
   `Merge branch '<branch>'`, ending with the trailer block — `Co-Authored-By:` and `Change: <change-id>`,
   contiguous.
3. **The merged tree is the tagged tree:** `git diff --quiet <branch> <default-branch>` exits 0.
4. **No `origin`:** when `git remote get-url origin` fails, push nothing; say so in your sentences.
5. **Push:** `git push origin <default-branch>`, then `git push origin <version>.0`. A rejected push halts; the
   default branch stays merged locally. Never pull, never `--force`, never push the version branch.

## Step 6 — Close: report, and stop
````

- Step 6's body: the Step 4.3 gate paragraph, then:

````markdown
<the close-out line>

Your sentences: the release commit and the tag, with the Step 4.3 gate's exit code; `converge ran`, or
`converge: skipped — no findings files`; the paid-down cards, or `backlog: none`; and the merge and the push, or
that there is no `origin`. A preamble flagged for a hand-edit (Step 2) is something the human must act on.

The last line, after a merge: `Next: grill the next version.` With no merge:

    Next: merge and push — release <version>.0 is on branch <branch>:
      git switch <default-branch>
      git merge --no-ff <branch>
      git push origin <default-branch>
      git push origin <version>.0

Then **stop**.
````

- *Never*, the first bullet, whole: *"**Never merge or push without the person's yes in this session**, never
  `--force`, never pull, and never push the version branch. A halt in Step 5 leaves the rest to the human."*

**`docs/decisions.md`, D17, whole:**

```markdown
### D17 · The release verifies, folds, archives, tags, and on the person's yes merges and pushes

**It re-runs the gate, folds the spec delta into `openspec/specs/`, archives the change, cuts the changelog and tags.
Then it asks once; on yes it merges into the default branch with `--no-ff` and pushes the default branch and the
tag. It never forces, never pushes the version branch, never edits feature code. Fold and archive land in one
commit.**

- **Why:** the yes is the person's act; the commands typed after it added nothing. A fold without its archive
  leaves the spec tree and the change disagreeing.
- **Rejected:** `openspec archive` for the fold: the release does the same fold inside a gate-verified commit · a
  separate merge skill: one more invocation · a merge without asking.
```

**`docs/decisions.md`, D8's title** ([B14](#b14)), before → after: *"and stays out of the gate"* → *"and stays out
of this repo's gate"*.

**`README.md`**, before → after: `:10` *"One change goes from an idea to a local tag."* → *"One change goes from an
idea to a tag on the default branch."*; `:29` *"verify, fold, archive, cut the changelog, tag — then stop"* →
*"verify, fold, archive, cut the changelog, tag — then, on a yes, merge and push"*.

## The HUMAN checklist

**`I14`, the middle cell, in both skills, whole:**

```markdown
mark a phase a person must do with `**HUMAN` on its `## Progress` line (qualifiers may follow: `**HUMAN · METERED**`); write each of its sub-tasks as exact commands with real values — names, tags, repo-relative paths — or, for a step with no command, one line naming the file and the exact text; a value known only at run time is the command that prints it, then the edit that uses it; and give it at least one `Verify:` naming the evidence that closes it
```

`mf-cut-change`'s last cell gains *"; reading each sub-task for its commands"*.

**`skills/mf-build/SKILL.md`, the HUMAN paragraph in Step 2,** its second and third sentences replaced:

`````markdown
**A HUMAN phase is done by a person, not by you.** Its `## Progress` line contains `**HUMAN`. Do none of its
tasks; run its `Verify:` checks. If any fails, **halt** with the person's checklist and nothing else — the one
halt not reported in full:

````
<N> — <Title> · HUMAN
cd <the repository root>
- [ ] <N.M, one line>
  ```sh
  <the sub-task's commands, as the cut wrote them>
  ```
- [ ] <N.M with no command: the file and the exact text>
Closes when: <each failing Verify:, word for word>
Next: /mf-build
````

The repository root is printed in chat only. A secret appears by its env-var name, never a value. If all pass, the
person has done it. …
`````

The rest of the paragraph, from *"Search their evidence files"*, stays.

## The scans

In `tests/test_skills.py`, each a function returning one line per breach, a test that `_REPO` gives `[]`, and a
planted twin that gives every breach ([B13](#b13)):

| scan | holds | the twin plants |
|---|---|---|
| `_close_out_problems` | in each `mf-*` skill, the first `## Step` heading naming a report (`re.compile(r"^## Step \d+ — .*[Rr]eport")`) exists, and its section names the close-out needle and `Next:` | a skill with no report step, and one whose needle sits outside it |
| `_cut_commits_problems` | `mf-cut-change`'s `## Step 9 — Show, then commit` names `commit without waiting` and `## Dependencies` | a Step 9 that names neither |
| `_merge_problems` | `mf-release` names the question, `git merge-base --is-ancestor <default-branch> HEAD`, `git merge --no-ff`, `git diff --quiet <branch> <default-branch>` and ``never `--force` `` | a release with the hand-off only |
| `_human_checklist_problems` | `exact commands with real values` in both skills' `## Input contract`; `the person's checklist`, ```` ```sh ```` and `Next: /mf-build` in `mf-build`'s `## Step 2 — The per-phase ritual` | a build and a cut with today's `I14` |

The close-out needle is `at most three sentences — what happened, the gate's exit code, and anything the human must act on`.
The test comment at `:666`, before → after: *"the build runs them after the human's OK."* → *"the build runs them
once the human starts it."*

## Dependencies

None.

## Risks / Trade-offs

- **[A wrong cut is committed]** → a further commit fixes it; a dependency still waits ([B5](#b5)), and the build's
  stop-condition 4 halts on one changed after the cut.
- **[A push publishes a mistake]** → only after the gate went green on the exact tree, the person said yes, and the
  default branch had not moved ([B8](#b8)).
- **[A short close-out hides a problem]** → anything the human must act on is in the sentences, and a halt
  stays in full ([B3](#b3)).
- **[This change edits the skills that build it]** → the skills are symlinked, so later phases run the edited text.
  Phase 1 edits only the report steps; the cut is done before phase 2; the merge runs at this change's own release.

## Verdict

**Feasible.** Every edit is skill or doc text at a cited line, plus a scan per rule in an existing file; no code path,
no dependency.
