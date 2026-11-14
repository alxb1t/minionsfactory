# Conductor guards — design

Where each guard of `skills/mf-ship/scripts/conduct.py` gets its missing test case, and how each case is proven. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The tests audit ([A1](#d1), [A3–A6](#d2)) found guards of the conductor that no test holds, in these shapes:

```
a list:   SECRETS = (s1 … s13)    test: for s in conduct["SECRETS"]: assert s in profile
                                  ── delete s2 and both sides shrink
a guard:  if A and B and C: refuse    test: an input where A fails
                                      ── B and C can go and the test stays green
```

Each guard sits where `conduct.py` names it today: the lists at `conduct.py:248-271` and `HOOKS_OFF` at `:327`, `_merges_a_release` at `:2253`, `_foreign_commit` at `:2278`, `_outside` at `:2068`, `DIRECT` at `:96`, `_clear` at `:4326`, `reset_stack` at `:5868`, `grant` at `:7773`, `_bounded` at `:3121`. The change edits none of them: no behaviour changes, and each case must be seen red under a change to the guard, then green.

## Goals / Non-Goals

**Goals**

- A removal of an entry, a conjunct or a call in the guards above turns a test red.
- `W5` says so, so a feature built beside the series stops adding the miss.

**Non-Goals**

- The stations' guards, the sandbox's real-denial proofs and the audit's `Also` items. They are named in [proposal](proposal.md#not-in-this-change).
- A mutation tool in the repo.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The sandbox's lists are literals in one test of `tests/test_sandboxed.py` | a removal then edits a test | a literal in `test_conduct.py`: the loops there stay as they are |
| [D2](#d2) | The push guard gets one unit case per conjunct, each calling `_foreign_commit` on a history that holds every other conjunct | only then does a removed conjunct leave a case red | a case through `halts_on`: a full run costs more and adds no proof |
| [D3](#d3) | `_outside`'s config isolation is held by a new step of the existing test, planting `url.<decoy>.pushInsteadOf` with `_urls` held at its read before the plant | `T2`: extend before adding; the key is one a URL-addressed push obeys and a URL-addressed `ls-remote` does not | `remote.origin.uploadpack`: a URL call never reads it; `url.<decoy>.insteadOf`: `_unpushed`'s `ls-remote` reads the empty decoy and halts before any push |
| [D4](#d4) | `DIRECT`'s sections are a literal in the test, and the `devDependencies` case fails before it passes | with `DIRECT` cut to `("dependencies",)` every case that reaches `_direct` still passes | looping over `conduct["DIRECT"]` |
| [D5](#d5) | Each guard of the processes and trees has one planted case | the audit proved each guard removable with the suite green | none |
| [D6](#d6) | A case's twin is its red run, in the phase's commit body | `T6`: the guard test's red run with the guard removed; a mutation tool is not in the repo | a mutation tool |
| [D7](#d7) | `W5` gains one clause, on conjunctions | the miss of A3 and A7 is the same | a new rule `W7` |

### D1

[A1](#context): `test_conduct.py` and `test_sandboxed.py` build the expected settings from `conduct["SECRETS"]`, `conduct["TOKENS"]`, `conduct["NETWORK"]` and `conduct["HOOKS_OFF"]`, so removing an entry removes it from both sides. A new test of `tests/test_sandboxed.py` asserts each tuple equals a literal of the same entries. The loops over the lists stay: they hold the profile's shape, and the literal holds the content.

### D2

`_foreign_commit` refuses a commit on the default branch unless `_merges_a_release` holds and the merge's `^2^` is a recorded ledger head.

`_merges_a_release` holds when the commit merges exactly one branch, its tip is a release merge, and the commit's tree equals the tip's tree. `_release_merge` holds when that tip is a tagged commit named `chore(release): <tag>`.

```
conjunct                        the case                                  held by
one merged branch               an octopus: main, a recorded release's    new case
                                tip, a side commit on its head, in
                                that parent order, all empty
subject of the tip              a tagged tip on a recorded head,          new case
                                subject not `chore(release): <tag>`
tag on the tip                  a tip named `chore(release): <tag>`,      new case
                                the tag on the recorded head
tree equal to the tip's tree    a merge of a recorded release that adds   new case
                                a file of its own
`^2^` in the ledger             a release by hand                         test_a_hand_release_is_the_persons_to_push
```

Each new case calls `conduct["_foreign_commit"](root, base, "main")`, `base` the head `_origin_judged` left on `origin`. It expects `Stop` with `no run's release`.

A recorded head is one `conduct["_record_release"]` wrote, as `_released` writes it. A helper of the test file builds a recorded release and stops before its merge.

The existing `test_a_tagged_side_merge_is_not_pushed`, `test_a_release_merge_no_run_made_is_not_pushed` and `test_a_forged_release_is_not_pushed` stay: they hold the plain-commit, base and ledger paths, and no test is deleted.

### D3

`_outside` runs a remote call from a scratch repo, so the primary's config is never read. The audit's proof: the scratch made to carry the primary's whole config leaves every test green. `test_a_key_set_after_the_refusal_reaches_nothing` plants only keys a URL-addressed call never reads. A new step plants `url.<decoy path>.pushInsteadOf` set to the origin's path in the primary's config, runs `push_left` as the test's own steps do, and expects the decoy bare repo to hold no ref.

`git remote get-url` expands `insteadOf` and `pushInsteadOf`, so `_urls` (`conduct.py:1834`) would read the decoy, and `_refuse_origin` (`conduct.py:2022`) would halt on the kept URLs before any remote call. The step therefore holds `_urls` at what it returned before the plant, within a `monkeypatch.context()`, as the test already holds `_refuse_config_commands`: the refusal reads the config clean, then the key is set. The test's later steps run with the real `_urls`. With the scratch carrying the primary's whole config, `_unpushed`'s `ls-remote` still reads the origin, and the push goes to the decoy, which then holds `main`: red. With the code as it is, the push goes to the origin, which refuses it, and the decoy holds no ref: green.

### D4

`test_a_manifest_is_judged_by_the_rows_of_the_cut` loops over `conduct["DIRECT"]`. Its one other case, a scoped `devDependencies` entry, expects *approved*, which also holds when the section is never read. The loop runs over the literal `("dependencies", "devDependencies", "optionalDependencies", "peerDependencies")`, and a `devDependencies` entry no row approves is judged unapproved before a row approves it.

### D5

| guard | the case | where |
|---|---|---|
| `_clear` skips groups 0 and 1 | `active/0` and `active/1` hold a start time the fake `ps` confirms, and `os.killpg` is replaced by a recorder | a new test, mirroring `test_stop_ends_a_live_run`'s guard step |
| `reset_stack` calls `_refuse_config_commands` | a key outside `CONFIG_PLAIN` in the repo's config before a stacked reset, the git state refreshed so `_config_changed` passes | a step of `test_a_stacked_dependent_resets_and_merges_back` |
| `grant` calls `preconditions` | a dirty primary and no live run: the grant is refused and no grant file is written | a step of `test_a_grant_buys_one_round` |
| `_bounded` takes a regular file of at most `READ_BYTES` | a FIFO, a file of `READ_BYTES + 1` bytes and a link to a regular file each read as `None`; a file of exactly `READ_BYTES` reads whole | a new test; the FIFO read runs in a daemon thread joined with a timeout, so a missing `O_NONBLOCK` fails the test and hangs nothing |

### D6

The build's worker runs each new case under the change the audit names, sees it red, restores the code and sees it green. The change and its red result go in the phase's commit body, per `T6`.

| case | the change that turns it red |
|---|---|
| the lists | one entry deleted from `SECRETS`, `TOKENS`, `NETWORK` or `HOOKS_OFF` |
| the push conjuncts | the case's own conjunct removed from `_foreign_commit` or `_merges_a_release`: red; each other conjunct removed in turn: still green |
| `_outside` | the scratch repo made to carry the primary's whole config |
| `DIRECT` | `DIRECT = ("dependencies",)` |
| `_clear` | the `int(entry.name) > 1` test removed |
| `reset_stack` | the `_refuse_config_commands(tree)` call deleted |
| `grant` | the `preconditions(cwd, executor)` call deleted |
| `_bounded` | `O_NONBLOCK` dropped; the `S_ISREG` test dropped; the size test dropped |

A change that leaves a case green is a case that holds nothing: the worker rewrites the case, and does not edit the code to suit it.

### D7

`skills/mf-build/SKILL.md`'s `W5` row, before → after:

```
before:  A test that holds a guard ships with a twin showing the test fails when the guard is gone, placed per `T6`
after:   … placed per `T6`; a guard that is a conjunction has one case per conjunct, built so that only that conjunct can halt it
```

## Tests

This change adds tests and removes none. Counts come from `uv run pytest tests/test_conduct.py tests/test_sandboxed.py --collect-only -q`, its last line.

| layer | added | where |
|---|---|---|
| unit | the lists literal | `tests/test_sandboxed.py` |
| unit | one case per conjunct: octopus, subject, tag, tree | `tests/test_conduct.py` |
| unit | `_clear`'s groups 0 and 1; `_bounded` | `tests/test_conduct.py` |
| step of an existing test | `_outside`'s config, `DIRECT`, `reset_stack`, `grant` | `tests/test_conduct.py` |
| end-to-end | none | |

Before: 221 tests collected. After: 229, eight new: the seven of the phases, and converge's S1 case, the another-subject case run again with subject `chore(release): v0.8.0` on a side tip tagged `v0.9.0`.

No new end-to-end run: `T1` puts each guard at the lowest layer that can fail for it, a direct call. `T2` extends the tests that already reach the state.

No test is deleted or merged, so there is no `I16` table.

## Dependencies

None.

## Risks / Trade-offs

- A case built wrong passes for the wrong reason. [D6](#d6) holds each to its red run; a case whose construction fails some other conjunct first is the one the audit found.
- The FIFO read blocks without `O_NONBLOCK`. The thread join bounds a red run to its timeout.
- `os.killpg` is replaced in the `_clear` case. A removed guard must record a call and signal nothing, or a red run would kill the test runner's own group.

## Verdict

Ready to build, in the phases of [tasks](tasks.md). The code of the conductor is read, never edited.
