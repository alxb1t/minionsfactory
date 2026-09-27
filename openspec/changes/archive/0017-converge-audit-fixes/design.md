# 0017-converge-audit-fixes — design

**In one line:** rules added to `mf-converge` and `mf-release`, each from a leak the audit measured, and each held
by a text scan. No new station, no code. **Verdict: feasible** ([why](#verdict)).

Motivation is in [proposal.md → Why](proposal.md#why). This page holds the evidence, the decisions, and each
skill's before → after.

## Context

- `skills/mf-release/SKILL.md` Step 1 reads both findings files' `verdict:` and blocker states. It never compares
  their `head:` with `HEAD`.
- `skills/mf-converge/SKILL.md` Step 4 fixes the vocabularies: security `critical | high | medium | low`, review
  `blocking | nit` (`:115-118`). Step 3 gives each station the range, the patch, its findings path and the card.
- Step 6's fix station "fixes test-first where there is logic". Nothing records that the test failed first.
- Step 8 picks small cards by **Fix** size. Step 9 and `## Never` forbid deleting a backlog card (`:224`, `:281`).
- `docs/sdd.md` *The findings contract* states the vocabularies (`:140-141`).
- The parked runner's `prompts/reviewer.md` and `prompts/security.md` carry the same vocabularies.

### Terms

| term | means |
|---|---|
| **the judged head** | the `head:` in both findings files — the last commit a round judged |
| **catch-up round** | one verify round over `<judged head>..HEAD`, run when the findings files are clean but `HEAD` moved |
| **an anchor** | a harm class that always blocks: data loss or an irreversible delete, spend, exposure of personal data or secrets, silent wrong output |
| **drift** | docs, comments, README or CHANGELOG text the code contradicts. A spec scenario is not drift |
| **a repeat** | a finding that describes a defect already carded in `.minions/backlog.md` |
| **stale-claim pass** | review's second pass: grep the rest of the tree for what the diff renamed, deleted or recounted |
| **the red run** | the new test's failing output, run before the fix is applied |

## Goals / Non-Goals

**Goals**

- Every commit a release ships was judged by a round.
- A harm that costs money, data or trust is never deferred.
- Prose drift is fixed cheaply and stops inflating the blocker count.
- A defect deferred once is not deferred again silently.
- A fix is proven against the failure, not against the record.

**Non-Goals**

- Splitting large diffs, or a whole-system review. Both need their own grilling.
- Changing the adopted engines. The rules live in what the stations are told, not in `/code-review` or
  `/security-review`.
- Re-grading cards already in the backlog.

## Evidence

The audit ran over one target repository's changes 0008–0033. Its numbers are in that repository's
`.minions/audit/numbers.json`, produced by `python3 aggregate.py` there.

| fact | result |
|---|---|
| changes that shipped a commit after the judged head | `4` |
| blocking findings re-judged `low` | `23` of `49`, mostly docs or spec drift |
| security `medium` findings re-judged `low` | `10` of `16` |
| a data-loss `rm -rf` filed `low` and deferred | `1` |
| the same gap deferred in successive changes | `4` changes |
| post-release misses that were prose made false outside the diff | the largest docs class of `60` misses |
| findings that were regressions of converge's own fixes | `26` of `258` |
| re-judged findings the test gate would have caught | `0` of `102` |

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | **`mf-release` halts unless `HEAD` equals the judged head** of both findings files, when converge ran. A skipped converge has no head to compare. The check is a Step 1 precondition, so the release's own fold commit comes after it | commits after the last round shipped unreviewed ([evidence](#evidence)) | comparing only one file's head; checking after the fold |
| <a id="d2"></a>**D2** | **`mf-converge` gains a catch-up round.** When both findings files are clean and the judged head is an ancestor of `HEAD`, it freezes `<judged head>..HEAD`, runs one Step 7 verify round, writes the backlog, and reports. It counts against the cap; at the cap it halts, naming revert or re-converge. No pickup | re-running the whole loop for a one-line commit is waste; a scoped verify is the loop's own tool | a full re-converge; a human waiver |
| <a id="d3"></a>**D3** | **Anchors block.** An anchored finding is `blocking` in review and at least `high` in security, so it is fixed in the loop. Cards outside the anchors keep the station's judgement | the data-loss `rm -rf` was filed `low` and deferred; no human is in the backlog stage to catch it | deferring an anchor with a human's OK |
| <a id="d4"></a>**D4** | **Review grades `blocking \| drift \| nit`.** `drift` does not block and pickup takes every `drift` card, whatever its size. A spec scenario the code contradicts stays `blocking` | most blockers re-judged `low` were prose ([evidence](#evidence)); the spec is a contract, not prose | drift that blocks; drift as a nit |
| <a id="d5"></a>**D5** | **Repeats escalate.** Each station reads `.minions/backlog.md`. A repeat names `repeat of <id>` in **Related** and goes up one level: security one step, a review `nit` or `drift` to `blocking`. The conductor judges nothing | one gap was deferred in successive changes ([evidence](#evidence)); a repeat means this diff touched code that still has it | the conductor matching titles |
| <a id="d6"></a>**D6** | **A fixed repeat clears its old card.** Step 9 runs the old card's **Still true?** for every verified repeat; the check shows the defect gone → delete the card and name it in the report with the output | a card describing a fixed defect is a lie in the backlog; the check is the same evidence Step 9 already uses for moot cards | leaving it for a paydown change |
| <a id="d7"></a>**D7** | **Review runs a stale-claim pass after its engine.** For every path, symbol, verb, route or count the diff renames, deletes or changes, it runs `git grep` outside the diff and cards each now-false mention as `drift`. Its Summary says the pass ran; Step 5 checks that it does | prose a change made false without touching it is the largest docs class of misses | the conductor deriving the set mechanically — counts and meaning changes are not derivable |
| <a id="d8"></a>**D8** | **Red before green.** For a fix sized `a test`, the fixer pastes the red run into the card's **Status** note. The verify pass reopens the card when the red run is missing, or the test does not exercise **When you'd hit it**. Docs-only fixes are exempt | a fix's test checked the recorded kind, not the retry, and the defect returned | the verifier running the test on the parent — a read-only station cannot check out |
| <a id="d9"></a>**D9** | **The parked runner keeps `blocking \| nit`.** `docs/sdd.md` names the divergence in one sentence | Track B is parked and agrees with itself; v0.16 made the same call | changing the runner's prompts |

### D1–D2 — the head check and the catch-up round

```
  mf-release Step 1 ── converge ran? ── no ─▶ skip the check
                           │ yes
                           ▼
                  HEAD = judged head? ── yes ─▶ continue
                           │ no
                           ▼
                  halt: "run /mf-converge — it runs a catch-up round over <head>..HEAD"

  mf-converge, both files clean, judged head ≠ HEAD:
       judged head ancestor of HEAD? ── no ─▶ halt: history rewritten, re-converge from round 1
                           │ yes
                           ▼
       round < 3 ? ── no ─▶ halt: revert the late commits, or re-converge from round 1
                           │ yes
                           ▼
       freeze <head>..HEAD ─▶ Step 7 verify ─▶ Step 9 backlog ─▶ Step 10 report   (no pickup)
```

### Where each rule lands

| rule | file · section | before → after |
|---|---|---|
| D1 | `mf-release` Step 1 | — → a precondition: when converge ran, `HEAD` equals the `head:` of both files; else halt naming the catch-up round |
| D2 | `mf-converge`, a new `## Catch-up round` before Step 1 | — → the entry test and the flow above |
| D3, D4 | `mf-converge` Step 4, *Two severity vocabularies* | review `blocking \| nit` → `blocking \| drift \| nit`; the anchor list and its grades |
| D3, D4, D5 | `mf-converge` `## The card`, **Priority** row | `<severity> · <role>` and why → the same, plus: an anchor names itself; a repeat says `repeat of <id>` |
| D4 | `mf-converge` Step 5, non-blocking list | review nits, security `medium`/`low` → review `drift` and nits, security `medium`/`low` |
| D4 | `mf-converge` Step 8 | small cards → small cards and every `drift` card |
| D4 | `mf-converge` `## Never` | never pick a card sized `a design change` → never pick a non-`drift` card sized `a design change` |
| D5 | `mf-converge` Step 3, the station inputs | — → `.minions/backlog.md`, read-only, and the repeat rule |
| D6 | `mf-converge` Step 9 and `## Never` | never delete a backlog card → except a fixed repeat's card that **Still true?** shows gone |
| D7 | `mf-converge` Step 3 and Step 5 | — → the review station's stale-claim pass; Step 5 checks its Summary names it |
| D8 | `mf-converge` Step 6 and Step 7 | fixes test-first → plus the red run in the note; the verify pass checks it |
| D3, D4, D9 | `docs/sdd.md` *The findings contract* | review and simplify grade `blocking \| nit` → review grades `blocking \| drift \| nit`, the anchors, and one sentence on the runner's divergence |

## Seams — what the tests hold

The skills are prose, so the seam is the text scan in `tests/test_skills.py`. Each scan has a `tmp_path` twin that
plants the breach and checks it is reported, as the existing scans do.

| key | the scan checks |
|---|---|
| `sdd:converge-audit:reviewed-head` | `mf-release` names `HEAD equals the head:`; `mf-converge` names `catch-up round` |
| `sdd:converge-audit:anchors-and-drift` | `mf-converge` and `docs/sdd.md` name `blocking \| drift \| nit`; `mf-converge` names `data loss`, `spend`, `exposure`, `silent wrong output` |
| `sdd:converge-audit:repeats-escalate` | `mf-converge` names `repeat of` and `up one level` |
| `sdd:converge-audit:stale-claim-pass` | `mf-converge` names `stale-claim pass` at least twice |
| `sdd:converge-audit:red-before-green` | `mf-converge` names `failing run from before the fix`, and `When you'd hit it` inside Step 7 |

## Dependencies

None.

## Risks / Trade-offs

- **Anchors block more.** Changes with real harms take an extra round. → Intended; the cap still applies.
- **A repeat makes an old defect this change's work.** → Only when this diff re-raised it, so the code is in reach.
- **The stale-claim pass lengthens review.** → A `git grep` per changed name; cheap next to a missed drift.
- **The red run is the fixer's claim.** → The verifier checks it exists and fits the scenario; it cannot re-run it.

## Verdict

Feasible. Every edit is skill prose, one doc paragraph and text scans. Phase 1 stands alone. Phase 2 adds the
vocabulary phase 3's stale-claim pass writes into, so the order is fixed.
