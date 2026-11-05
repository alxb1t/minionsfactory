# Cap policy — design

At a converge cap the conductor reads the open blocking cards and their sizes; a cap of small cards gets one automatic grant a run,
any other cap halts as a re-plan. Verdict at the end: ready to build.

## Context

Read at `a3814cb` (v0.55.0) and on `0067-rescue` at `22c68d3`, whose code it builds on, released as v0.56.0 before this cut's
commit, so the run merges it in before the build — line numbers on `0067-rescue` unless named. `conduct.py` is `skills/mf-ship/scripts/conduct.py`; the granted round still runs, so its lines may
move: the build re-reads them by symbol.

- **F1. A cap is text:** `"cap reached"` in the converge halt line, read at `stage_of`'s converge-halt branch (`:787-794`) and in
  `grant()` (`:3138`). A normal cap, a catch-up over its count and a granted round that still blocks write the same text
  (`skills/mf-converge/SKILL.md:445-446`, `:192`, `:125` on `main`).
- **F2. Where a cap meets the run:** `Run.advance`'s STUCK branch halts and calls `Run.rescue` for a stage in `RESCUED`
  (`:2436-2442`); the post-spawn path checks, holds, judges and rescues a cap reached inside the run (`:2476-2488`). The grant clause:
  `_granted(…, take=True)`, `" and grant=yes"`, the `grant` event, `PROMPTS["converge"]` (`:2454-2464`, `:137`).
- **F3. Findings cards:** frontmatter `verdict`, `round`, `open_blocking`…; a card's `**Priority:** <severity> · <role> · …`,
  `**Fix:** … · size: <one line|a test|one line and a test|a design change>`, `**Status:** open|fixed|verified|wontfix`
  (`skills/mf-converge/SKILL.md:313-348`, `:499-536` on `main`). Review blocks on `blocking`, security on `critical` and `high`.
  `conduct.py` has no card reader; `review_metrics.py`'s `_bullet`, `_PRIORITY` and `_STATUS` (`skills/mf-review-metrics/scripts/review_metrics.py:115-172`)
  are the pattern, a separate script.
- **F4. Models:** `_table` returns a table or `None` (`:1645-1655`); `_skips_rescue` reads `[rescue] skip` once at plan time
  (`:1681-1684`, `:2672-2677`).
- **F5.** `EVENTS` holds `grant` (`:63-67`); D47's "needs the person" list and D53 (`docs/decisions.md:454-468`, `:505-526`).
- **F6. Tests:** `tests/fake_worker.py`'s `_findings` writes no cards (`:38-45`); `grant-halts` (`:268-273`); `test_a_grant_buys_one_round`
  (`tests/test_conduct.py:3765-3900`), `test_rescue_skip_runs_none` (`:1405`).

## Goals / Non-Goals

**Goals:** a cap of small cards converges in the same run; a cap of a design, or a second one, goes back to planning.

**Non-Goals:** a grant by hand outside `mf-ship`; tracking a function across caps.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | `_open_blockers(runs, change)` reads each open blocking card's id and size | Q3 | the rescue's judgement |
| [D2](#d2) | `Run.auto_grant` at a cap — both places F2 names — spawns converge with `grant=yes`, once a version a run | Q3, Q4 | a grant file |
| [D3](#d3) | Any other cap halts as `re-plan`, `cap reached` kept in its text; the rescue names `/mf-plan` | Q5 | a new stage |
| [D4](#d4) | `[converge] auto_grant`, default `true`, read at plan time | Q7 | an `AGENTS.md` line |
| [D5](#d5) | The record: D47 amended, D54, `mf-ship`'s halt table | Q6, Q8 | — |

### D1

`_open_blockers(runs, change) -> list[tuple[str, str]]`: for each of the review and security findings files, each card bullet
`- **<id> — …**` whose `**Status:**` is `open` and whose `**Priority:**` severity blocks its role, the id and the `size:` after its
`**Fix:**`, its trailing period stripped; a card with no size reads `a design change`. Review's severity `blocking`, security's
`critical` or `high`, is the first ` · ` field of `**Priority:**`. A missing or unreadable file → `None`; `None` or `[]` grants nothing.

### D2

`Run.auto_grant(version, halt) -> tuple[bool, str]` — whether it granted, and the refused ids — before the rescue at both places F2
names, its rule in a side-effect-free `_would_grant(version, halt) -> tuple[bool, str]`: `"cap reached"` in `halt`, `self.stopped("run")`
false, the version's first cap in this run — `self.capped`, every cap counted, and `advance`'s grant clause adding the version when it
spends a person's grant, so a cap after it is the second —
`self.grants_auto.get(change, True)`, and `_open_blockers` a non-empty list all sized `one line`, `a test` or `one line and a test` →
remove its halts as `take_back` does, log `grant — <id>: automatic · <ids>`, spawn converge with `PROMPTS["converge"]` and
`" and grant=yes"`, and return `(True, "")`; the caller `continue`s `advance`'s loop, whose next pass judges the round — a cap there is the
second, refused. The STUCK branch reads `if self.auto_grant(version, why): continue` before its halt; the post-spawn path reads
`held is not None and (self.auto_grant(…) or self.rescue(…))`. It writes no grant file and starts no rescue, so `Run.hold` never
reads it as a rescue's answer. `ship()`'s every-version-stuck shortcut (`conduct.py:2958-2963`) leaves out of its `all(...)` test a version whose cap
`_would_grant` takes, so its thread starts; it calls nothing that spawns.

### D3

When `auto_grant` refuses at a cap, the run writes a second halt line, `<id> · halt — re-plan: <ids>`, after the STUCK branch's or
`judge`'s, so it is the version's last halt line, which the rescue reads (`skills/mf-rescue/SKILL.md:40` on `0067-rescue`) — or
`re-plan: no open blocking card read`; the status log keeps its `cap reached`, so `grant()` still
spends a person's round. `skills/mf-rescue/SKILL.md`'s cap diagnosis names `/mf-plan <the version> depth=hard
from=<its brief>` as the way back when the halt says `re-plan`.

### D4

`_auto_grants(runs, change) -> bool`: `[converge]` absent, or `auto_grant` not `false` → `True`; read once in `read_plan` into
`self.grants_auto`, as `self.skips` is, and read with `.get(change, True)`.

### D5

D47: a cap of small cards is the run's to grant once; a re-plan halt needs the person. D54, *The cap policy* — the sizes, the once a run,
the re-plan halt, the setting. `skills/mf-ship/SKILL.md`'s halt table gains the `re-plan` row: run `/mf-plan … from=`, or grant.

## Tests

`git grep -c '^def test_' 0067-rescue -- tests/test_conduct.py` counts the file at the cut. Added on the fake worker, `slow` when over
5 s (`T1`): `test_a_small_cap_is_granted_automatically`, `test_a_design_change_cap_halts_as_replan`,
`test_an_auto_granted_round_that_blocks_halts_as_replan`, `test_auto_grant_false_grants_none` — `T2`: no test reaches an automatic
grant — with a `_cards` helper and `cap-small`, `cap-design` and `cap-again` modes in `tests/fake_worker.py`. Extended:
`test_a_grant_buys_one_round` with a person's grant on a re-plan halt. None deleted.

## Dependencies

None.

## Risks / Trade-offs

- **A small card that is not small:** one more round, spent once; the second cap is a re-plan.
- **Sizes are the checker's word:** converge's review writes them; a wrong size buys one round at most.

## Verdict

Ready to build.
