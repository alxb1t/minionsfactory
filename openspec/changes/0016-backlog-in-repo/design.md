# 0016-backlog-in-repo — design

**In one line:** `mf-converge` gets a pickup step and a backlog-writing step, `mf-release` loses its deferred-work
precondition and gains a paydown step, `mf-cut-change` writes `backlog:`, and the export is deleted last.
**Verdict: feasible** ([why](#verdict)).

Motivation is in [proposal.md → Why](proposal.md#why). This page holds the decisions, each skill's before → after,
every file the export's name leaves, the tests and the evidence.

## Context

- `skills/mf-converge/SKILL.md` Step 5 carries every non-blocking card, every round, into
  `.minions/<version>_backlog.md`. Step 6's fix station clears open blocking findings only. Step 8 reports.
- `skills/mf-release/SKILL.md` Step 1, precondition 5, halts on any list line in `.minions/<version>_backlog.md`.
  Precondition 6 is the tag check, and Step 4.3 cites it by number.
- `skills/mf-backlog-export/SKILL.md` empties that file into a backlog outside the repository, and carries the same
  `## The card` section as `mf-converge`. `tests/test_skills.py` holds their labels equal
  (`sdd:backlog-cards:fields-agree`).
- The parked runner has its own copy of the rule: `orchestrator/release.py` (`deferred_work_text`,
  `_backlog_blocker`), the role prompts under `prompts/`, and `openspec/specs/release/spec.md`.
- `orchestrator/specs.py` `collect_spec_keys`: a scenario key listed under `## REMOVED Requirements` in the active
  delta leaves both the shipped and the resolvable set at once.

### Terms

| term | means |
|---|---|
| **the backlog** | `.minions/backlog.md` — one gitignored file for every change, the only copy of the deferred work |
| **a card** | one finding, in the shape `mf-converge`'s `## The card` fixes |
| **pickup** | the extra fix-and-verify round converge runs after it is clean, over the small cards |
| **a small card** | a non-blocking card whose **Fix** size is `one line`, `a test`, or `one line and a test` |
| **a paydown change** | a change cut to close cards from the backlog. Its `proposal.md` lists them under `backlog:` |
| **a qualified id** | a card id prefixed with its change number: `0016·R1` |

## Goals / Non-Goals

**Goals**

- Deferred work never leaves the repository, and nothing needs a human between converge and release.
- The small cards are fixed while their context is fresh, and verified like every other fix.
- A paydown change removes exactly the cards it closed.

**Non-Goals**

- Changing the parked runner ([D9](#d9)).
- Picking up older cards from the backlog.
- Moving the existing items kept outside the repository. The human does that by hand.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | **One backlog file, `.minions/backlog.md`, gitignored**, with one `## <change-id>` heading per change | one place to groom. Tracking it would publish security findings in a public repo | one file per version; a tracked `docs/backlog.md` |
| <a id="d2"></a>**D2** | **Pickup is mechanical and reuses the loop.** It runs once, after both verdicts are clean, and only while the last judged round is below the cap of three. It picks every `open` small card in either findings file, sends them to the Step 6 fix station by id, and verifies them in a normal Step 7 round. No human confirms | the size is already on the card. The loop already knows how to fix and verify. The human judges at grooming, not here | human confirmation; a separate skill; picking by the conductor's judgement |
| <a id="d3"></a>**D3** | **Cards are written once, at convergence, not every round.** Every non-blocking card whose **Status** is not `verified` goes to the backlog, whole, with a qualified id, after its **Still true?** check. A card the check shows gone is moot, and is named in the report instead. An id already in the backlog is skipped. On a halt at the cap nothing is written: the findings files stand and hold every card | writing each round would write cards pickup then fixes. The findings files live for the whole session, so nothing is lost before the write | carrying each round (today's Step 5) |
| <a id="d4"></a>**D4** | **The card's Fix size is a closed set**: `one line` · `a test` · `one line and a test` · `a design change`. Pickup takes the first three. A size outside the set is not picked | a mechanical pick needs values it can match. The example card already uses `one line and a test` | free-text sizes |
| <a id="d5"></a>**D5** | **`mf-release` drops precondition 5** and renumbers the rest. Its prose names no count of preconditions (`P12`) | the backlog always holds open cards by design, so blocking on it would block every release | blocking on this change's heading in the backlog |
| <a id="d6"></a>**D6** | **Paydown: the cut writes `backlog:`, the release deletes.** `mf-cut-change` lists the qualified ids in `proposal.md` frontmatter and checks each is in the backlog. `mf-release` deletes exactly those cards after the tag, and removes a change heading left empty. An id not found is reported, not a halt. `mf-build`'s input contract does not change | the cut leaves the backlog alone, so an abandoned change loses nothing. `mf-build` never reads the key | the cut moving cards into the change; a new contract row |
| <a id="d7"></a>**D7** | **The export retires last**: delete `skills/mf-backlog-export/`, replace the card-parity scan, and add `mf-backlog-export` to the retired-word scans in `tests/test_conventions.py` | `A4` — the irreversible act is the last phase. Until phase 2 lands, the release still reads the per-version file the export empties | deleting it in phase 1 |
| <a id="d8"></a>**D8** | **The card-parity requirement is REMOVED without listing its scenario, and an ADDED requirement reuses its key** `sdd:backlog-cards:fields-agree` | listing the key under REMOVED makes today's tests dangling at the cut commit, so the cut's gate is red (`I3`). Dropping it without a successor leaves the key orphaned once phase 3 deletes its tests. Reusing the key keeps every commit green | a fresh key; listing the key under REMOVED |
| <a id="d9"></a>**D9** | **The parked runner keeps its per-version file.** `orchestrator/`, `prompts/` and `openspec/specs/release/` are unchanged, and `docs/sdd.md` names the divergence | Track B is parked, and its release, prompts and spec agree with each other today. Changing half of it would make it disagree with itself. `CLAUDE.md` already lets the two lines disagree when a change says so | changing the runner too |

### D2–D3 — `mf-converge`, before → after

```
  before:  5 read verdicts ── carry nits to <version>_backlog.md (every round) ──┬─ clean → 8 report
                                                                                 └─ else  → 6 fix → 7 verify ─┐
                                                                                          ▲──────────────────┘
  after:   5 read verdicts ─┬─ clean ─▶ 8 pickup ─┬─ small cards, round < 3 → 6 fix (picked ids) → 7 verify ─┐
                            │                     └─ none, or no round left ─────────────────────────────┐  │
                            └─ else → 6 fix → 7 verify → back to 5                                        ▼  │
                                                          9 write the backlog ◀── clean after pickup ◀──────┘
                                                          10 report
```

| where | before | after |
|---|---|---|
| `## Parameter` | the deferred-work file is `.minions/<version>_backlog.md` | the backlog is `.minions/backlog.md` ([D1](#d1)) |
| Step 5, last two paragraphs | carry the non-blocking findings every round; both clean → Step 8 | non-blocking cards stay in the findings files until Step 9; both clean → Step 8, or Step 9 when pickup already ran |
| Step 6, first line | clear every open blocking finding | clear every open blocking finding, or, in the pickup round, exactly the cards Step 8 names |
| Step 6, carrying bullet | does not carry the non-blocking findings | does not write the backlog. Only you do, in Step 9 |
| Step 7 | both clean → Step 8 | both clean → Step 8, or Step 9 when pickup already ran. The cap counts the pickup round |
| new Step 8 — Pickup | — | [D2](#d2), [D4](#d4). Print the picked ids before dispatching. One pickup per run: a card first found in the pickup's verify round is not picked |
| new Step 9 — Write the backlog | — | [D3](#d3). Create the file with a `# Backlog` title and one line saying what it is, if missing. Card title becomes `- **<NNNN>·<id> — …**`; every other field verbatim |
| Step 10 — Report (was 8) | item 3: the nits carried, by id | item 3: the picked ids and their end state; the cards written, by qualified id; the moot ones with the **Still true?** output; the backlog's total card count |
| `## The card`, **Fix** row | size: one line, a test, or a design change | the closed set in [D4](#d4) |
| `## Never` | — | never pick a `a design change` card or an older backlog card; never delete a card from the backlog |

### D5–D6 — `mf-release` and `mf-cut-change`, before → after

| where | before | after |
|---|---|---|
| `mf-release` Step 1, lead-in | the findings files and the deferred-work file are evidence | the findings files are evidence |
| `mf-release` Step 1, heading | `(seven; every one holds, or halt)` | `(every one holds, or halt)` |
| `mf-release` precondition 5 | *No deferred work is left* | deleted; 6 → 5, 7 → 6 |
| `mf-release` Step 4.3 | precondition 6 — the tag does not already exist | precondition 5 — the tag does not already exist |
| `mf-release` new Step 4.6 | — | *Clear the paid-down cards* — [D6](#d6). No `backlog:` key → `backlog: none`. Nothing to commit: the file is gitignored |
| `mf-release` Step 5, item 1 and `## Never` | the seven preconditions; all seven of Step 1 | each precondition; every precondition in Step 1 |
| `mf-release` Step 5 | — | a new item: the cards cleared, by qualified id, or `backlog: none` |
| `mf-cut-change` Step 6 | — | a bullet: a paydown change lists `backlog: [0012·S1, 0012·R4]` in `proposal.md` frontmatter, and checks each id with `grep` in `.minions/backlog.md`. An id not found goes to the human |

### D7 — where the export's name leaves

| file | today | after |
|---|---|---|
| `skills/mf-backlog-export/` | the skill | deleted |
| `skills/mf-converge/SKILL.md` | Step 5 cites it; `## The card` says it carries the same fields | Step 5 rewritten in phase 1; the card intro says no other skill carries the card |
| `README.md` | a row in the skills table | the row goes; one sentence on the backlog |
| `CLAUDE.md` | "the five `mf-*` … skills: cut, build, converge, backlog export, release" | "the `mf-*` … skills: cut, build, converge, release"; `.minions/` holds `backlog.md` |
| `docs/sdd.md` | *The findings contract* and *The release fold* name the per-version file and the export | the backlog, the release that does not read it, and the runner's divergence ([D9](#d9)) |
| `.gitignore` | the comment names "the deferred-work file" | it names the runner's per-version file and the skills' `backlog.md` |
| `tests/test_skills.py` | `_CARD_CARRIERS` and the parity scan | a card-owner scan ([D8](#d8)) |

## Seams — what the tests hold

The skills are prose, so the seam is the text scan in `tests/test_skills.py` and `tests/test_conventions.py`. Each
scan has a `tmp_path` twin that plants the breach and checks it is reported, as the existing scans do.

| key | test file | the scan checks |
|---|---|---|
| `sdd:repo-backlog:converge-writes-one-file` | `tests/test_skills.py` | `mf-converge` names `.minions/backlog.md`, `one line`, `a test`, and not `_backlog.md` |
| `sdd:repo-backlog:release-does-not-read` | `tests/test_skills.py` | `mf-release` does not name `_backlog.md` and names `.minions/backlog.md`; `mf-release` and `mf-cut-change` name `backlog:` |
| `sdd:backlog-cards:fields-agree` | `tests/test_skills.py` | only `mf-converge` carries `## The card`, with at least one label |
| `sdd:retired-export:named-nowhere` | `tests/test_conventions.py` | `mf-backlog-export` over `_SCANNED`, with the plant-per-root twin |

## Evidence

| fact | command | result at the cut |
|---|---|---|
| converge names the per-version file | `grep -c '_backlog.md' skills/mf-converge/SKILL.md` | `4` |
| release names it | `grep -c '_backlog.md' skills/mf-release/SKILL.md` | `1` |
| no skill names `backlog:` yet | `grep -c 'backlog:' skills/mf-release/SKILL.md skills/mf-cut-change/SKILL.md` | `0` each |
| files outside the specs and changelog naming the export | `git grep -l 'mf-backlog-export' -- . ':!openspec' ':!CHANGELOG.md' \| wc -l` | `4` |
| the export's length | `wc -l < skills/mf-backlog-export/SKILL.md` | `148` |

## Dependencies

None.

## Risks / Trade-offs

- **The backlog is lost with `.minions/`** — a re-clone or `git clean -fdx` deletes the only copy. → Accepted
  ([D1](#d1)). The converge report prints the card count, so a file that vanished shows as a drop to zero.
- **Pickup can turn a clean branch into a halt** — a pickup fix that breaks something, found in round 3, halts at
  the cap. → Accepted in the grilling. The halt report names the pickup round, and the human can revert its commit.
- **A station writes a size outside the closed set** — the card is not picked and goes to the backlog. → Safe by
  default: the failure is a missed pickup, never a wrong one.
- **Key reuse** ([D8](#d8)) — `fields-agree` now means "one owner". → The requirement title says what it proves;
  the key is an id, not a description.

## Migration Plan

1. After the release is merged, the human removes the `mf-backlog-export` symlink from their personal skills
   directory. `make uninstall-skills` cannot, because the skill directory it loops over is gone.
2. The human moves the items kept outside the repository into `.minions/backlog.md` by hand, as cards, under one
   heading per change.
3. Old `.minions/<version>_backlog.md` files are no longer read by the skills. The human deletes them.

## Verdict

Feasible. Every edit is to skill prose, docs and text-scan tests. The runner is untouched. Each phase ends green:
phase 1 adds the writer while the release still reads only the per-version file. Phase 2 removes that reader.
Phase 3 deletes the export after nothing reads its output.
