# 0012-converge-optional — design

**In one line:** the two findings files decide it — neither present means converge was skipped and the release
says so; either present means converge ran, and both must be clean. **Verdict: feasible** ([why](#verdict)).

Motivation is in [proposal.md → Why](proposal.md#why). This page holds 7 decisions, the before → after text, the
test and the evidence.

## Context

`mf-release` Step 1 has seven preconditions. Three of them assume converge ran:

| # | today (`skills/mf-release/SKILL.md`) |
|---|---|
| 2 | the review findings file exists, `verdict: clean`, every blocking finding `verified` |
| 3 | the security findings file exists, `verdict: clean`, every `critical` and `high` finding `verified` |
| 4 | *a missing findings file is not clean* — an absent file is a halt; simplify is declared out by name |

So a change converge never ran on cannot be released. `docs/sdd.md` says the same twice: in its findings contract
(*"cannot let the loop or the release pass falsely"*) and in *The release fold* (review and security must be
clean).

### Terms

| term | means |
|---|---|
| **findings files** | `.minions/findings/<change-id>_review.md` and `.minions/findings/<change-id>_security.md` — exactly these two paths |
| **converge ran** | at least one of the two findings files exists |
| **converge skipped** | neither findings file exists |
| **the skip line** | the literal `converge: skipped — no findings files` |

## Goals / Non-Goals

**Goals**

- A change converge never ran on releases, and the release record says it was skipped.
- A converge that ran and did not finish clean still stops the release.

**Non-Goals**

- Changing `mf-converge` — its rules stand; it is only no longer required.
- Changing the parked runner's release (`orchestrator/release.py`).
- Telling the release *why* converge was skipped. The skip is the human's call, made by not running it.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | **Neither findings file exists → converge was skipped.** Preconditions 2 and 3 pass, and the release states the skip line | on prose-only changes converge cycles to its cap and halts ([E1](#evidence)); the human reads the prose instead | never reading the files (a failed converge would ship unnoticed); a flag at invocation (a second way to say what the disk already says) |
| <a id="d2"></a>**D2** | **Either findings file exists → converge ran.** Both must exist and be clean, exactly as today. One without the other halts | a converge that ran and did not finish clean must not be released over silently | treating a lone file as a skip |
| <a id="d3"></a>**D3** | **Precondition 5 does not change.** Deferred work in `.minions/<version>_backlog.md` still blocks; a missing file still passes | only converge writes that file, so a skipped converge leaves none and the check passes on its own | exempting it on a skip |
| <a id="d4"></a>**D4** | **The skip is stated in two places:** the Step 5 report, and the release commit's body, as its own paragraph before the trailer block. The tag and the CHANGELOG entry do not change | the commit is the durable record; the report is read once | a CHANGELOG line (release writes no prose there); a tag message |
| <a id="d5"></a>**D5** | **The missing-file rule moves, it does not go.** It stays in `mf-converge` Step 5 and in `docs/sdd.md`'s findings contract, scoped to the loop; `mf-release` and `docs/sdd.md`'s release fold drop it | the loop still needs it to judge its own stations; only the release reads absence differently now | deleting the rule everywhere |
| <a id="d6"></a>**D6** | **A scan test holds it** — `tests/test_skills.py`, with a twin that shows the scan bites | skills are prose; a scan is the highest check, as in v0.11 | a grep in the tasks only (it proves the build, not the future) |
| <a id="d7"></a>**D7** | **One phase.** The skill, the test and `docs/sdd.md` change in one commit | the docs describe the release; split, one commit ships docs that are false | a separate docs phase |

### D1–D5 — `mf-release`, before → after

| where | before | after |
|---|---|---|
| frontmatter `description:` | "Finalize a converged change — … Use when converge has returned clean verdicts and the branch is ready to become a release." | "Finalize a built change — … Use when the build is done and, if `mf-converge` ran, its verdicts are clean." The middle of the sentence is kept |
| the paragraph under the title (`:13-15`) | "You re-read the verdicts from disk yourself" | the same, qualified: when converge ran. When it did not, the release is the only check after the build, and says so |
| the findings-file paths paragraph (`:52-54`) | "A file absent at its stated path is a halt (precondition 4), not an invitation to search." | "An absent file is never an invitation to search — precondition 4 says what absence means." |
| precondition 2 | review is clean | opens with "If converge ran (precondition 4):"; the rest unchanged |
| precondition 3 | security is clean | opens with "If converge ran (precondition 4):"; the rest unchanged |
| precondition 4 | *a missing findings file is not clean, and simplify is declared out by name* | **Converge ran, or was skipped — the two files decide.** Neither exists → skipped: 2 and 3 pass, and you state the skip line. One exists without the other → halt: a converge that ran leaves both. Simplify stays declared out by name, with its existing reason |
| precondition 5 | deferred work | **unchanged** (D3) |
| Step 4, item 4 (the commit) | the message is `chore(release): <version>.0` plus the trailer block | when converge was skipped, the body carries the skip line as its own paragraph, before the trailer block |
| Step 5, report item 1 | each of the seven preconditions and how it was verified | the same, and for precondition 4: *converge ran* or the skip line |

The numbering of the seven preconditions does not change: Step 4, item 3 cites precondition 6 by number.

A commit on the skipped path, for the builder to copy the shape from:

```
chore(release): v0.12.0

converge: skipped — no findings files

Co-Authored-By: <the attribution line this session uses>
Change: 0012-converge-optional
```

### D5 — `docs/sdd.md`, before → after

| where | before | after |
|---|---|---|
| findings contract, the sentence ending the *Frontmatter* paragraph | "…so a station that never ran cannot let the loop or the release pass falsely." | "…so a station that never ran cannot let the loop pass falsely. The release reads absence differently: no findings file at all means the check was skipped, which the release states; one file without the other is still a halt." |
| *The release fold*, its precondition sentence | "review and security are `verdict: clean` with every blocking finding `verified`, not merely `fixed`" | "if the check stations ran, review and security are `verdict: clean` with every blocking finding `verified`, not merely `fixed` — and if neither ran, the release states that the check was skipped" |

## Seams — what the test holds

The seam is the skill text on disk, as in v0.11. The new helper and its two tests go in `tests/test_skills.py`,
built like the two scans already there: a module-level helper taking a base path, a scan over the repo, and a
twin that plants each breach in `tmp_path`.

| scenario key | the scan | the twin plants |
|---|---|---|
| `sdd:converge-optional:skip-is-stated` | `skills/mf-release/SKILL.md` names the skip line and does not name `A missing findings file is not clean`; `skills/mf-converge/SKILL.md` names `A missing findings file is not clean` | a release with no skip line, a release that still carries the rule, a converge without it — all three reported |

The key is ADDED in [specs/sdd/spec.md](specs/sdd/spec.md). An active delta's keys resolve for the binding
checker before the fold, so the tests bind from their first commit.

## Evidence

| id | observation | check |
|---|---|---|
| **E1** | on docs and spec prose, converge cycles and halts at its cap, unconverged; the human would rather read the prose | vault field note, isekai, 2026-09-25 |
| **E2** | preconditions 2–4 require both findings files | `sed -n '59,70p' skills/mf-release/SKILL.md` |
| **E3** | `mf-converge` keeps its own missing-file rule | `grep -c 'A missing findings file is not clean' skills/mf-converge/SKILL.md` prints `1` |
| **E4** | `mf-release` carries the same phrase today | `grep -c 'A missing findings file is not clean' skills/mf-release/SKILL.md` prints `1` |
| **E5** | the deferred-work file is written only by converge | `grep -c '<version>_backlog.md' skills/mf-converge/SKILL.md` is non-zero; `mf-build` names no such file |

## Dependencies

None.

## Risks / Trade-offs

- **A converge that crashed before writing either file reads as a skip.** → The same as not running it, which is
  now allowed; the skip line in the commit makes it visible. A converge that wrote one file and died halts
  (D2).
- **Stale findings files from an earlier run of the same change id make a skip impossible.** → Intended: they
  are that change's verdicts. Deleting them is the human's act, not the release's.
- **Less checking by default.** → Converge is still one command away, and a change that ran it keeps every
  guarantee it had.

## Verdict

**feasible.** One skill, one test module, one doc. No dependency. One phase, green alone.
