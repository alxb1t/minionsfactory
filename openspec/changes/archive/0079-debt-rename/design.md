# Debt rename — design

The debt's file, lock, key, event and word renamed everywhere live; old names read where history holds them; a run moves an old
file at its start. Verdict at the end: ready to build.

## Context

Read at `5b8eb77` (v0.64.0); the brief carries no `At` line. Sites were mapped at `0077-run-metrics`'s tip and re-counted at
`5b8eb77` with `git grep -c -i backlog main -- …`: `skills/mf-converge/SKILL.md` 21, `openspec/specs/sdd/spec.md` 33,
`tests/test_metric_scripts.py` 14, `skills/mf-ship/scripts/conduct.py` 9, `docs/decisions.md` 7, `skills/mf-release/SKILL.md` 6,
`skills/mf-review-metrics/scripts/review_metrics.py` 6, `tests/test_conduct.py` 6, `tests/test_review_metrics.py` 6,
`skills/mf-plan/SKILL.md` 5, `scripts/metrics/run.py` 5, `scripts/metrics/backlog.py` 5, `metrics/catalogue.toml` 5. The builder
re-reads each by symbol.

- **F1. `conduct.py`:** `_clear_stale_lock` names `.minions/backlog.lock` (its docstring and path); the converge-halt parse reads
  `".minions/backlog.lock" in halt` → "halted on the backlog lock: resumes at Step 9"; the unlock event names the lock; `_cards`
  takes the backlog's path; `report` calls `_cards(runs / 'backlog.md', change)`. A halt line already in a status log names the
  old lock.
- **F2. The run's start:** `run()` refuses a live claim (`preconditions`, `active.mkdir()`); `Run.ship()` logs `start`, returns on
  `self.halts`, runs `_keep_origin`, then `_clear_stale_lock`, then reads the plan and probes — the move fits before
  `_clear_stale_lock`, under the claim, before any worker. `LOCK_STALE = 600`.
- **F3. Converge:** Step 9 (the lock's `mkdir`, the `# Backlog` file, "under `backlog:`", the `backlog` status-log event), the
  resume rows (the lock halt, `backlog` → Step 10), the diagram and events table.
- **F4. The release:** Step 4 item 6 reads the archived proposal's `backlog:`, deletes those cards from `.minions/backlog.md` under
  the lock, records `backlog: none`.
- **F5. Metrics:** `scripts/metrics/run.py`'s `paid()` (`^backlog:[ \t]*\[`, feeding `debt-paid` and `escapes`) and `debt()`
  (`.minions/backlog.md`); `scripts/metrics/backlog.py` (`open-backlog-cards`, its catalogue entry `script`); `review_metrics.py`'s
  `\b(\d+) cards? to backlog` and its two labels; `metrics/changes/*.json` hold the id in 44 files.
- **F6. The record:** D16's heading `### D16 · Deferred work is a card in the repo's backlog` — its anchor linked from
  `CONTRIBUTING.md:29` alone — and body; D15's "a backlog card"; `docs/principles.md`, `AGENTS.md`, `THREAT_MODEL.md`, `mf-plan`
  (the paydown grep over `.minions/backlog.md`, `backlog: [<ids>]`), `mf-cut-change` (`backlog:`), `worker.md`, `generic-review.md`.
- **F7. What stays:** `CHANGELOG.md`'s history, `openspec/changes/archive/**`, `metrics/changes/*.json`, the citations
  `tests/test_guardrails.py:17` and `tests/test_skills.py:183` (`Why: 00NN-backlog-…`), the spec's two kept scenario titles,
  `review_metrics.py`'s internal key `to_backlog` (`tests/test_review_metrics.py:304-313` assert it), `tests/test_metrics.py`'s
  fixture message, and D1–D3's old-name readers, their old-wording fixtures and the test names that say "backlog", the living spec
  until the release folds the delta, and the delta itself — `git grep -n -i backlog` matches them by design.

## Goals / Non-Goals

**Goals:** the word gone from every live file; every old name still read where history holds it; no chore.

**Non-Goals:** the per-change layout; renaming the metric id or the archives.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | `.minions/debt.md`, `.minions/debt.lock`, the event `debt`, the key `debt:`; each reader also takes the old name | Q1, Q2 | dropping the old names at once |
| [D2](#d2) | The word, everywhere live; `scripts/metrics/backlog.py` → `debt.py`, the id kept | Q2 | renaming the id |
| [D3](#d3) | `conduct.py run` moves the old file and a stale lock at its start; both standing, or a young old lock, halts | Q3 | a manual migration |

### D1

`conduct.py`: `DEBT = ".minions/debt.md"`, `DEBT_LOCK = ".minions/debt.lock"`; `_clear_stale_lock` clears the new lock; the halt
parse reads either lock's name and says "halted on the debt lock: resumes at Step 9"; the unlock event names the new lock; `report`
reads `debt.md`; `_cards`' parameter and docstring say debt. Converge's `SKILL.md` says debt throughout — the diagram, the events table, `## Step 9 — Write the debt`, `**The debt** is
`.minions/debt.md`` — and its `done` detail reads `N cards to debt`; Step 9 writes `.minions/debt.md` under `debt.lock`, its file
titled `# Debt`, and logs `debt`; its resume rows send a `debt` or an old `backlog` top line to Step 10, a halt naming either lock to
Step 9. The release reads `debt:`, else
`backlog:`, deletes those cards from `debt.md` under `debt.lock`, records `debt: none`, calls the file gitignored debt, and its diagram (`skills/mf-release/SKILL.md:21`) says debt. `run.py`'s `paid()` reads `^(?:debt|backlog):[ \t]*\[`;
`debt()` reads `.minions/debt.md`, naming it when missing. `review_metrics.py` reads `cards? to (?:backlog|debt)`, its labels "to
debt".

### D2

Each F6 site reads "debt" for the store and "debt card" for a card: D16's heading becomes `### D16 · Deferred work is a card in the
repo's debt file`, and `CONTRIBUTING.md:29` links its new anchor; `mf-plan`'s checks read `.minions/debt.md`, else an old `.minions/backlog.md` a run has not moved yet, and propose
`debt: [<ids>]`; the cut lists `debt: [<ids>]` and greps each id in the same file. `git mv scripts/metrics/backlog.py scripts/metrics/debt.py`; it reads
`.minions/debt.md`; the catalogue entry `open-backlog-cards` keeps its id, its `title` "Open debt cards", its `script` the new path; `debt-added` and
`debt-paid` are titled "Cards carried to the debt" and "Debt cards paid";
the tests `_load("debt")`. The F7 sites stay.

### D3

`Run.migrate_debt()`, called in `ship()` before `_clear_stale_lock`: a `backlog.lock` older than `LOCK_STALE` is removed and logged
`unlock`, as `ship()` logs `_clear_stale_lock`'s, with or without an old file. With `.minions/backlog.md` and no `debt.md`, the move
takes `.minions/debt.lock` with `mkdir`, as every writer of `debt.md` does — a `debt.lock` older than `LOCK_STALE` is removed first —
then links the old file to `debt.md` and unlinks it, so a `debt.md` made since the check is never replaced, releases `debt.lock`, and
logs `move — .minions/backlog.md → .minions/debt.md`. With no old file, nothing moves, whatever stands at the old lock. The run halts before
any worker — `self.halt("run", <why>)`, `self.log.event("run", "halt", self.closing())`, `return 1`, as the `Stop` path does,
before `if not versions` — naming the cause, when an old file stands and: `debt.md` stands too, or `debt.md` appears before the link;
the old file is a link, which the move would turn into a second name of its target; a `backlog.lock` younger than `LOCK_STALE` is held,
or is a plain file; or a young `debt.lock` is held. Each is a person or a hand-run writer holding it.

## Tests

`git grep -c '^def test_' 5b8eb77 -- tests/test_conduct.py tests/test_metric_scripts.py tests/test_review_metrics.py` counts the
files at the cut. Added: `test_a_run_moves_an_old_backlog_to_the_debt` (`tests/test_conduct.py`) — the move, a second start moving
nothing, a stale old lock removed, a linked old file halting, both files halting, a young old lock halting beside an old file and not
without one, a plain file at the old lock halting, a young `debt.lock` halting, a stale one removed and the move releasing its own —
`T2`: no test starts a run beside an old file.
Extended: `test_a_stale_lock_is_cleared_and_converge_resumes` with the new lock and a halt naming the old one;
`test_a_fix_after_a_cap_halt_converges_afresh`, whose lock-halt line reads the new text;
`test_backlog_cards_are_unavailable_without_a_backlog` and `test_the_backlog_is_read_from_the_primary_run_directory`
(`tests/test_metric_scripts.py`) on `debt.md`, through `_load("debt")`; `test_run_metrics_read_cost_and_review_yield` on `debt.md`, its gap
naming it, and a `debt:` key beside an old `backlog:`; `test_the_status_log_gives_duration_tokens_and_the_cap` (`tests/test_review_metrics.py`) with a "cards to debt" line beside the
old wording. None deleted.

## Dependencies

None.

## Risks / Trade-offs

- **A hand-run converge writing the old file or the debt mid-run:** a young old lock beside an old file, or a young `debt.lock`, halts
  the move, and the link never replaces a `debt.md` made since the check; a person settles it.
- **A missed live site:** `git grep -n -i backlog` over the live paths is the build's last check, F7's sites the only matches.
- **A repo not run since the upgrade:** `mf-plan` and the cut read its old `backlog.md`; its next run moves it.

## Verdict

Ready to build.
