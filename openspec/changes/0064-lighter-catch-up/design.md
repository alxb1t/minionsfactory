# Lighter catch-up — design

A green gate is recorded by its tree and reused; a merge the fixed rules reproduce is clean by recomputation. Verdict at the end:
ready to build.

## Context

Read at `40bd25e` (v0.52.0).

- **F1. Where the gate runs.** `mf-build` per phase (`skills/mf-build/SKILL.md:95`, `:150`); `mf-converge` before round 1 and at
  each verify (`skills/mf-converge/SKILL.md:47`, `:221`; Step 7); `mf-integrate` before its commit, on the staged merge
  (`skills/mf-integrate/SKILL.md:137-141`); `mf-release` at precondition 1, timed for the `Gate:` line, and after the fold
  (`skills/mf-release/SKILL.md:93-97`, `:176-180`, `:202-206`). Each prints `make -n gate` first. `make gate` took 382 s at
  `0063`'s cut (`uv run pytest -q`: `112 passed in 382.17s`).
- **F2. The integrate commit's body** is one line per `.resolved` hunk; a clean merge, a rule's resolution and a person's after a
  note halt leave no line (`skills/mf-integrate/SKILL.md:142-153`). Its *Why a station* line still says "Fixed rules settle the
  exact parts; judgement is the person's" (`:25-26`) — `0061·R3`. A test the integrator edits is named nowhere — `0061·S1`.
- **F3. `integrate.py`** — `next`, `changelog`, `decisions`, `delta` (`skills/mf-integrate/scripts/integrate.py:553-575`);
  `changelog(tree)` and `decisions(tree)` settle `CHANGELOG.md` and `docs/decisions.md` mid-merge from the merge base, `HEAD` and
  `MERGE_HEAD` (`:255`, `:301-321`, `:463-487`). Since `0063`, `conduct.py`'s `merge_in` runs the same two rules.
- **F4. The catch-up round** — both findings clean, `head:` not `HEAD`; merges only → its own count; freeze, remerge-diff, one
  Step 7 round (`skills/mf-converge/SKILL.md:150-206`). *Empty resolutions* still dispatches both checkers (`:206`).
- **F5. The release** needs both findings `verdict: clean`, `head:` = `HEAD`, every blocking and high security finding
  `verified` (`skills/mf-release/SKILL.md:98-122`).
- **F6. The principles in the way:** *Nothing reads as clean by being absent* and *The gate is run, never summarized*
  (`docs/principles.md:60-93`); D45 (`docs/decisions.md:428-440`).

## Goals / Non-Goals

**Goals:** no tree gated twice; a rule-settled merge judged in seconds; every merge commit naming how each path was settled.

**Non-Goals:** reusing a red run; skipping the release's post-fold gate; a conductor change.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `gate_run.py` runs `make gate` and records a green run by its tree; it reuses the record on the same clean tree and dry run | a recorded run of this exact tree is the gate, not a claim | a station's word; a mark integrate writes |
| [D2](#d2) | Every station gates through it; `mf-release` after its fold passes `--fresh` | the fold changes the tree; a forged record must never reach a tag | reusing at the release's last gate |
| [D3](#d3) | `integrate.py replay <merge>` rebuilds the merge with the rules alone and compares trees | the rules are deterministic, so recomputing proves the merge | trusting the commit body |
| [D4](#d4) | A by-rule catch-up writes both findings clean with `## By rule`, no worker, within the merges-only count | `0060`'s 873 s and 167,167 tokens for one rule-settled file | review of a rule's output |
| [D5](#d5) | The integrate commit names every settled path, in four line kinds | the history tells the merges apart; replay never reads it | — |
| [D6](#d6) | The record: the two principles, D45, `THREAT_MODEL.md` | A7: a decision in force is edited where it lives | — |

### D1

`skills/mf-converge/scripts/gate_run.py`, a stdlib `uv run --script`:

- `git diff --quiet`, `git diff --cached --quiet` aside, and no untracked file (`git ls-files --others --exclude-standard`) →
  the worktree is **settled**; the tree is `git write-tree`, so a staged merge and its commit share one key.
- `make -n gate`'s output hashed (sha256) is the **dry run**.
- A settled tree whose `.minions/gate/<tree>` holds the same dry run → print `gate: reused — <tree> · <seconds>s · <date>`, exit 0.
- Else run `make gate`, its output streamed; exit 0 on a settled tree → write `.minions/gate/<tree>` (`dry:`, `date:`,
  `seconds:`), print `gate: green — <tree> · <seconds>s`; any other exit → write nothing, exit with `make`'s code.
- `--fresh` runs `make gate` whatever stands, and records it.

### D2

`mf-build`'s per-phase gate, `mf-converge`'s precondition 5 and Step 7, `mf-integrate`'s Step 4.1 and `mf-release`'s precondition 1
call `uv run --script ../mf-converge/scripts/gate_run.py`, each still printing `make -n gate` first. `mf-release`'s Step 4.3 passes
`--fresh`. Precondition 1's `Gate:` time is the record's `seconds`, or the run's.

### D3

`replay(merge)`: a scratch worktree (`git worktree add --detach <tmp> <merge>^1`), `git merge --no-ff --no-commit <merge>^2`;
on conflict, `changelog` when `CHANGELOG.md` is unmerged and `decisions` when `docs/decisions.md` is, each staged; any path left
unmerged → exit 1. Then `git write-tree` against `git rev-parse <merge>^{tree}`: equal → print `replay: by rule — <paths>`,
exit 0; else exit 1. The scratch worktree is removed in every case. A merge without two parents, or whose second parent
is not an ancestor of the default branch (`git merge-base --is-ancestor`), → exit 2, before any scratch worktree.

### D4

In *Catch-up round*, after the selection: each merge in it run through `replay`; every one exits 0 and the selection holds no other
commit → write both findings files (`head: HEAD`, `verdict: clean`, `round:` the run's own count) with a `## By rule` section naming
each merge and its paths, log `round N · by rule — clean, <paths>`, then Step 9. Any exit 1 → the round as before. *Nothing reads as
clean by being absent* gains its exception: clean by recomputation.

### D5

Step 4.3's body: `<path>: integrate.py changelog` and `<path>: integrate.py decisions` for each rule's path; the union line as
before; `<path>: the person` for each path the note named; `<path>: test fixed — <what it now asserts>` for each test the integrator
edited, which never removes or loosens an assertion (`0061·S1`). *Why a station* says the integrator also resolves additive hunks
(`0061·R3`), and so does `README.md`'s integrate line.

### D6

*The gate is run, never summarized* → "a recorded run of this exact tree counts; the release's post-fold gate runs fresh".
*Nothing reads as clean by being absent* → its exception for a by-rule catch-up. D45 names `replay` and the body lines.
`THREAT_MODEL.md` *Known gaps*: a worker can forge a gate record; the release's fresh post-fold gate keeps a red tree from a tag.

## Tests

`uv run pytest -q --collect-only tests/` collects the suite at the cut; `grep -c '^def test_' tests/test_integrate.py` counts
`test_integrate.py`'s. This change adds unit and integration tests, no end-to-end run (`T1`); none is deleted or merged.

| test | layer | why new (`T2`) |
|---|---|---|
| `tests/test_gate_run.py` — a green run recorded, a red run unrecorded, reuse refused on a dirty tree, another tree, a changed dry run; `--fresh` | integration, a scratch repo and `Makefile` | a new script |
| `test_replay_reproduces_a_rule_settled_merge` | integration | a new subcommand |
| `test_replay_refuses_a_judged_merge` — a union, a person's edit, a cleanly merged test edited | integration | the same, its other side |

Extended: `tests/test_skills.py` (each station names `gate_run.py`, the release's Step 4.3 `--fresh`); `tests/test_conduct.py`
with a `by-rule` mode in `tests/fake_worker.py` (a version whose catch-up is by rule releases).

## Dependencies

None.

## Risks / Trade-offs

- **A forged gate record** can skip an earlier gate; the release's post-fold gate runs fresh, so it cannot tag a red tree.
- **An environment change** — a tool upgraded between stations on one tree — is not in the key; the release's fresh gate catches it.
- **Replay's scratch worktree** writes under the primary's `.git/worktrees`, removed in every case.

## Verdict

Ready to build.
