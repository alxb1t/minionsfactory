# Debt paydown 2 — design

The small cards fixed where they stand, the stale archives corrected in place, the settled cards closed through `debt:`, and the
status log stamped by a script. Verdict at the end: ready to build.

## Context

Read at `5650ab1` (v0.70.0), the brief's own `At` commit: every fact citing a path stands. `C` is
`skills/mf-ship/scripts/conduct.py`, `T` is `tests/test_conduct.py`, `B` is `skills/mf-plan/scripts/brief_check.py`. This change
builds `after: [0086-ship-fixes-3, 0087-drift-amends]`: `0086` edits other functions of `C` and `T`, and `0087` edits
`skills/mf-converge/SKILL.md`'s Step 6, Step 9 and *Resuming a run*, so the build re-reads lines by symbol.

| measure | value | command |
|---|---|---|
| open numbered cards in the debt | 32, and `hand·N1` | `grep -c '^- \*\*[0-9][0-9][0-9][0-9]·' .minions/debt.md` |
| tests at the cut | 235 | `git grep -c '^def test_' -- tests/`, summed |

- **F1. The debt lock.** `Run.migrate_debt` (`C:4134-4172`) calls `self.unlock(DEBT_LOCK)`, whose `_clear_stale_lock`
  (`C:726-741`) returns at `if not lock.is_dir()`, then `lock.mkdir()` (`C:4160`) reads any `FileExistsError` as
  `.minions/debt.lock is held` (`C:4162`). The young-lock step is `T:3469-3475` of `test_a_run_moves_an_old_backlog_to_the_debt`.
- **F2. The re-cut.** `Run.cutting` returns `the branch's worktree {old} is kept: {why}` (`C:3643-3644`) when `_keeps`
  (`C:3400-3417`) keeps the old worktree; `_keeps`' `not at the cut's path` is `C:3416`. `mf-ship`'s `cut-halted` row
  (`skills/mf-ship/SKILL.md:96`) sends a branch with no change folder to a re-plan. The halt is asserted at `T:2985-2988` of
  `test_a_cut_halt_is_shown_and_rejoin_cuts_again`, marked `slow`.
- **F3. The join.** `Run.join` (`C:4103-4127`): a bottom `take_requests` that returns True reaches `continue` (`C:4121-4122`)
  and the top's `recheck` with no sleep, while its docstring (`C:4106-4109`) says a candidate's two reads are a wait apart. The
  bottom-take step is `T:1858-1862` of `test_a_halt_answered_on_disk_comes_back`, marked `slow`, which already patches
  `time.sleep` to log `wait` in `polled` (`T:1832-1844`).
- **F4. The stale diagnosis.** `Run.rescue` adds the change to `self.diagnosed` on a new `rescue.md` (`C:3139-3142`), then its
  `finally` calls `hold` (`C:3145-3147`). `hold`'s amended-alone branch (`C:3188-3192`) clears `self.halts` and leaves
  `self.diagnosed`, which `_needs` reads first (`C:2984-2985`). `test_an_amend_during_a_rescue_goes_on` is `T:1747-1775`.
- **F5. The brief check.** `fields` (`B:146-164`) reads a head only where `HEAD = re.compile(r"(\d+)\. (.*)")` (`B:32`) matches,
  and `head` (`B:118`) reads the first `after:` part alone. The docstring's why line (`B:13`) cites `its converge card S2`, a
  file under the git-ignored `.minions/`. `test_a_brief_out_of_shape_halts` is `tests/test_brief_check.py:81-114`.
- **F6. The probe's MCP halt.** `mcp_started` (`C:2641-2662`) fails the probe on a Claude `init` event listing a server
  (`C:4010`), held by `test_a_probe_halts_on_a_write_out` (`T:6789`, its MCP step `T:6854-6864`). The sandbox requirement
  (`openspec/specs/sdd/spec.md:1765-1826`) names no such halt.
- **F7. The status log.** `skills/mf-converge/SKILL.md:64-69` has the conductor take each event's time and the run heading's
  date from `date`. `C` reads the log's `## Run` headings and event lines (`C:649-666`, `C:778-786`, `_is_event` at `C:718`).
  `:232`'s `<date> · round N · by rule — clean` goes to a findings file's resolution log, not the status log.
- **F8. The archives.** The stale lines each card's **Still true?** names stand: `archive/0071-ship-fixes/design.md:94`, `:96`;
  `archive/0076-context-cost/design.md:65`; `archive/0083-plan-queues/design.md:42`, `:104` and `proposal.md:29`;
  `archive/0084-ship-fixes-2/design.md:50`, `:54-55`, `:106`, `:110-111`, `:118-121`, `:150`;
  `archive/0085-self-healing-ship/design.md:98`. No rule forbids editing an archive; `0038` D3 corrected `archive/0034`'s proposal
  in place, git keeping the old text ([D23](../../../docs/decisions.md#d23--superseded-is-deleted-harvested-first)).
- **F9. The threat model.** *Known gaps* opens with the carded list (`THREAT_MODEL.md:91-92`); `0052`'s `S15` is `:98`,
  `0049·S7`'s remainder `:99-101`, `0049·S5`'s hostile route `:121-123`, `0049·R15`'s LFS route `:124`. `0050·R11` is named at
  `:91` alone. `0086` and `0087` leave `THREAT_MODEL.md` unedited (`git diff --stat main...<branch>`).

## Goals / Non-Goals

**Goals:** each fixed card's test red before its fix; no archive holding the claim its card names; the settled cards gone from
the debt at the release.

**Non-Goals:** the kept cards ([D10](#d10)); any card that needs a decision or a design; editing `.minions/debt.md`.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | A file or a link at `.minions/debt.lock` halts the move as a file, not a lock | D1, `0079·R5` | clearing it as stale |
| [D2](#d2) | The kept-worktree halt names its remedy, and the `cut-halted` row stops sending it to a re-plan | D1, `0082·R8` | the remedy in the row alone |
| [D3](#d3) | A request taken at a poll's bottom sleeps out the poll before the next top | D1, `0085·R10` | a fixed `REJOIN_POLL` sleep |
| [D4](#d4) | `hold`'s amended-alone branch discards the diagnosis | D1, `0085·R11` | — |
| [D5](#d5) | `brief_check.py` halts on an item that does not open `<n>. ` and on a second `after:`; its why line cites the design | D1, `0083·S3`, `0083·R5` | — |
| [D6](#d6) | The probe's MCP halt is written into the sandbox requirement, the delta alone | D1, `0076·R3`, C2 | a phase of its own |
| [D7](#d7) | `stamp.py` writes each status-log event and run heading with the clock's time | D5, `hand·N1` | a script printing the time alone |
| [D8](#d8) | The stale archives corrected in place, each to its card's fix | D2 | a new note beside each |
| [D9](#d9) | *Known gaps* lists the cards still carded; each accepted route keeps its line | D3, D4 | deleting the accepted lines |
| [D10](#d10) | `debt:` closes the cards; the debt then holds the kept cards and any new ones | D8, C1 | closing more cards |

### D1

In `Run.migrate_debt`, after `self.unlock(DEBT_LOCK)` and `lock = self.primary / DEBT_LOCK`, before `lock.mkdir()`:
`if lock.is_symlink() or (lock.exists() and not lock.is_dir()): return f"{DEBT_LOCK} is a file, not a lock: a person removes it"`.
The docstring's halt list gains "a file at `debt.lock`". The delta's *Every worktree shares the primary's run directory* names it.

### D2

`Run.cutting`'s kept line becomes
`f"the branch's worktree {old} is kept: {why}; a person reads it, then removes it with git worktree remove or moves it back to the cut's path, before conduct.py rejoin {change}"`.
The `cut-halted` row of `skills/mf-ship/SKILL.md` gains, after "and the run cuts it again.": "A `the branch's worktree <path> is
kept` line is no plan's, and a re-plan halts the same way: a person reads that worktree, then removes it
(`git worktree remove <path>`) or moves it back to the cut's path, before `conduct.py rejoin <change-id>`."

### D3

In `Run.join`, the bottom branch reads `if self.take_requests(threads): time.sleep(max(0, deadline - time.monotonic()))`, then
`continue`. The docstring stands: it now holds.

```
  top: take · unblock · recheck ── deadline = now + REJOIN_POLL
        │ threads end early
  bottom: take ── True ──▶ sleep to deadline ──▶ top     (was: straight to top)
```

### D4

`hold`'s amended-alone branch, under `self.guard`, adds `self.diagnosed.discard(change)` beside its `self.halts` line, as
`Run.rescue`'s taken amend does (`C:3134`).

### D5

- **The item form.** `fields` gains a check over the section's raw lines: a line, tabs read as 4, short of the last head's text
  column (or of four spaces before any head) that opens `-`, `*`, `+`, `<n>.`, `<n>)` or `|` and does not open `<n>. ` and one
  space → `not a numbered item: <the line, in backticks>`, save the template's `- models:` and `- **Acceptance:**` lines from
  the head's indent plus three; a models line not written `- models:` → ``a models line not written `- models:`: <the line>``,
  and a second → `item <n> — more than one models line`. Each goes under the `## For the cut: ` prefix, e.g.
  ``brief: halt — ## For the cut: not a numbered item: `- **x;y** · minor · after: none` ``.
- **The second `after:`.** `head` counts the parts that start `after:`; more than one →
  `item <n> — more than one after:`, and no `after` entry is read.
- **The why line** (`B:13`) → "Why: 0083-plan-queues design D1; 0088-paydown-2 design D5." `0083`'s D1 gains the field checks
  under [D8](#d8).

### D6

The fix is the delta's sentence and `**AND**` lines in *A worker runs in an OS sandbox*; the release folds it into the living
spec. The halt's test stands: `test_a_probe_halts_on_a_write_out`. C2, decided by the cutter: the brief's phase 3 holds no work
once the delta is written at the cut, so it is no phase, and a text fix gets no new test
([D37](../../../docs/decisions.md#d37--tests-hold-what-is-true-now-nothing-tests-an-absence),
[D42](../../../docs/decisions.md#d42--skill-prose-is-held-by-review-not-by-phrase-scans)); `0083·R5`'s docstring is held the
same way.

### D7

`skills/mf-converge/scripts/stamp.py`, a `uv` script with standard-library imports alone, by `argparse`:

| form | writes | prints |
|---|---|---|
| `stamp.py <log> '<round N · event — detail>'` | `HH:MM:SS · <text>` directly under the first `## Run` line | the line |
| `stamp.py <log> --run <N> [--mark <mark>]` | `## Run <N> — YYYY-MM-DD HH:MM[ · <mark>]` directly under the first line, a `# ` title | the line |

- **The layout** is the log's own: the title, a blank line, the newest `## Run` heading with its events directly below it, and a
  blank line before each older heading. `--run` writes the title, a blank line, the new heading, then — when anything followed
  the title — a blank line and that rest, its leading blank lines dropped. An event goes on the line right after the first
  `## Run` line.
- **The time** is local, from `_now()`, a module function returning `datetime.now()`, so a test fixes it.
- **Exit 2**, `stamp: cannot stamp — <why>`, the log unchanged: a log that cannot be read (`<path>: <strerror>`), an event with
  no `## Run` line (`no ## Run heading`), a `--run` whose first line is no `# ` title (`no # title`), and an event beside
  `--run`, neither, or `--mark` with no `--run` (`give one event, or --run with an optional --mark`), checked in `main` after
  parsing, with no `argparse` group.
- **`tests/test_skills.py`** — `_METRICS_SCRIPTS` gains `("mf-converge", "scripts/stamp.py")`, appended last, its comment's why
  list `0088-paydown-2 design D7`; each expected list of `test_the_metrics_script_scan_reports_a_missing_script` gains
  `skills/mf-converge/SKILL.md: scripts/stamp.py: not named`, last.
- **`skills/mf-converge/SKILL.md`** — `:64-65`'s "Take the time from `date '+%H:%M:%S'`, run through Bash, never by hand" →
  "Write it with `uv run --script <this package>/scripts/stamp.py .minions/changes/<change-id>/status_log.md '<round N · event — detail>'`,
  which takes the clock's time; never write a time by hand"; `:68`'s "insert `## Run N — <date '+%Y-%m-%d %H:%M'>` directly under
  the title" → "insert the heading with `stamp.py <log> --run N`, `--mark <mark>` for a marked run".

### D8

Each archive is corrected to what the code does at this change's base, before → after:

- **`archive/0071-ship-fixes/design.md` D2 (`0071·R7`)** — "`stage_of` reads it before its `_merge_open` block:" → "`stage_of`
  reads it when no merge is open, a headed `.red` beside an open merge being stale:"; "`_check_integrate` fails on the sha being
  `HEAD`, before the subject check," → "`_check_integrate` fails while a headed `.red` stands, before the subject check,"; "so the
  person's fix commit after the merge passes." → "so the person's fix commit after the merge passes once a green gate deletes it."
- **`archive/0076-context-cost/design.md` D1 (`0076·R2`)** — "above the logs found, the cell reads `<logs> of <spawns>`" → "above
  the logs that held a result event, the cell reads `<read> of <spawns>`".
- **`archive/0084-ship-fixes-2/design.md` (`0084·R4`)** — D1's definition (`:50`) ends "in a newest run with no `start` line, not
  marked `· grant`."; the `_before_round` bullet (`:54-55`) reads "is `not _run_started(…)`, not `_granted_run(…)`, and no
  `verify: halt` in `halt`."; the flow's first line (`:67`) reads "converge halts, no start, no grant, head H"; the
  `test_a_halt_before_round_1_runs_again_at_the_same_head` bullet (`:118-121`) says its `stage_of` `RERUN`, `check` and `AMENDED`
  steps sit in `test_a_fix_after_a_cap_halt_converges_afresh`; the *Risks* line (`:150`) reads "after a halted `· amended` run".
- **The same design (`0084·R6`)** — D6 (`:106`) gains "A link at `.minions` halts the run, `.minions is a link: a person settles
  what it names`, and its target's `tmp` keeps its files: the delete runs through a descriptor on `.minions` itself."; the
  `mf-release` line (`:110-111`) reads "a scratch file for the fold is made with `mktemp`, inside a run's worker's sandbox: its
  environment names `.minions/tmp/`, and a Claude worker's sandboxed command may use Claude Code's own `TMPDIR` instead."; the
  `test_a_stale_lock_is_cleared_and_converge_resumes` bullet (`:131-133`) gains its third start, over `.minions` a link: the run
  halts naming it, and the link's target keeps its `tmp` file.
- **`archive/0085-self-healing-ship/design.md` D4 (`0085·R12`)** — "— the text from that heading to the next `## ` heading," →
  "— the text from the first line that starts `## Decisions` to the next `## ` heading, and every `## ` heading of the design, so
  a copied, added or renamed heading reads as decided —".
- **`archive/0083-plan-queues/` (`0083·R4`)**, to its delta and to [D59](../../../docs/decisions.md#d59--a-hard-plan-closes-on-a-checked-brief-and-queues-its-cut-on-the-persons-yes):
  - D1's summary row (`:40`) and table gain the item-head check — each `<n>. ` item's slug and `after` entries match `conduct.py`'s
    `SLUG`, its bump is `minor` or `patch`, it names `after:`, its lines `not a slug`, `not a bump`, `not an after id` and
    `no after:` — and the models check, its lines `the models line is not …`, `not a model or effort` and `no models line`; its
    prose names `CONDUCT`, loaded with `runpy` for `SLUG`, and `brief: cannot check — no conduct.py beside this skill`.
  - D3: the table row's (`:42`) "no ends on today's `Next:`" → "no ends on one `Next: /mf-cut-change` line per change"; the
    question (`:98`) first runs `conduct.py status` and shows each item and what `status` prints; the yes (`:104`) is "the
    person's to every merge and push in the run it joins or starts, as `mf-ship`'s is: each queued version, and each open
    version that run takes (P9)."; hard and not queued (`:107-108`) ends on one `Next: /mf-cut-change <NNNN>-<slug> <bump>
    brief=<path>` line per change, in order.
  - D4's D59 text (`:127-134`) reads as `docs/decisions.md`'s D59 does.
  - `## Tests` (`:149-156`): `test_a_brief_out_of_shape_halts` also holds the item-head and models halts;
    `test_what_cannot_be_checked_exits_2` an unclosed quote and a missing `CONDUCT`.
  - `proposal.md` *What Changes* (`:25-29`): the check also holds each item's slug, bump, `after` and models; the close shows the
    items and `conduct.py status`, its yes reaches every merge and push in the run, and no ends on one `Next: /mf-cut-change`
    line per change.

### D9

`THREAT_MODEL.md`, *Known gaps*:

- `:91-92` → "Carded in `.minions/debt.md`, accepted until paid down: `0050·R5`, `0050·S7`, `0034·R9`. D47 accepts `Ship tools:`."
- `:99`'s "`0049·S7` and `0050·R5`, what is left:" → "The config race, what is left, `0050·R5` among it:" (D3 of the brief:
  `0049·S7` is stale, the push check running from a scratch repo).
- `:124`'s "`0049·R15`, the LFS route:" → "The LFS route:" (`hookspath` is in `CONFIG_PLAIN`, `C:222`).
- A line after `:98`: "- `0050·R11`: a concurrent worker that swaps `<primary>/.git` for a link between `argv`'s check and a
  Codex worker's start puts another repository's `.git` in that worker's writable roots." — its only record was `:91`.
- `:98` (`0052`'s `S15`) and `:121-123` (`0049·S5`'s hostile route) stay as they stand: per the brief's D4, an accepted risk's
  threat-model line is its record. `0064·S4`'s remainder is `:100-101` already.

### D10

- **C1, decided by the cutter.** The brief read `0086-ship-fixes-3` as taking `0034·R9` and `0064·R6`, and the debt ending at
  10. `0086`'s proposal lists `debt: [0064·R6]`, keeps `0034·R9` carded (its D5), and edits no `THREAT_MODEL.md`. Closing more
  cards is scope no person settled.
- **What stays.** `0034·R9`, `0050·R5`, `0050·S7`, `0060·S6`, `0062·S1`, `0065·R8`, `0068·S3`, `0071·S2`, `0082·S5`, `0085·R3`,
  `0085·S1` and `0085·S2` — the brief's own kept cards, `0049·S5` closed by its D4 and `0034·R9` in its place — and any card a
  converge adds.
- **The close.** `mf-release` deletes each `debt:` card; no task edits `.minions/debt.md`.

## Tests

`git grep -c '^def test_' -- tests/` totals 235 at the cut. Added: 2, unit, in the new `tests/test_stamp.py`, loading the script
with `importlib` as `tests/test_brief_check.py` loads its own. No end-to-end test (`T1`); each other fix extends the test that
already reaches its state (`T2`).

- `test_a_stamp_writes_the_clock_time_under_the_latest_run` (new) — `_now` fixed at `2026-11-07 10:02:03`: on a log with a title
  and `## Run 1 — …` holding an event, `--run 2 --mark catch-up` inserts and prints `## Run 2 — 2026-11-07 10:02 · catch-up`
  directly under the title; `'round 1 · start — base a'` inserts and prints `10:02:03 · round 1 · start — base a` directly under
  it, above `Run 1`'s lines. The script run as a command, `[sys.executable, <script>, <log>, <event>]`, exits 0 the same.
- `test_a_log_out_of_shape_is_not_stamped` (new) — a missing log, an event on a log with no `## Run`, a `--run` on a log whose
  first line is no title, an event beside `--run`, and neither: each exits 2 with its `stamp: cannot stamp — …` line, the log
  unchanged.

Extended or edited, each card's step red before its fix:

| test | gains |
|---|---|
| `test_a_run_moves_an_old_backlog_to_the_debt` (`T:3382`) | after the young-debt-lock step (`T:3469-3475`): `held.rmdir()`, `held` a plain file, the run halts `.minions/debt.lock is a file, not a lock`, the old file unmoved; then `held.unlink()` and `held.mkdir()`, so the stale-lock twin's `held.rmdir()` (`T:3478`) still finds a folder |
| `test_a_cut_halt_is_shown_and_rejoin_cuts_again` (`T:2738`, `slow`) | `T:2985-2988` expects [D2](#d2)'s full line for `0018-v` |
| `test_a_halt_answered_on_disk_comes_back` (`T:1779`, `slow`) | the bottom-take step (`T:1858-1862`) logs each `take_requests` call in `polled`, and a `wait` stands between the bottom take that returned True and the next top take |
| `test_an_amend_during_a_rescue_goes_on` (`T:1747`) | `Run.hold`, wrapped with `monkeypatch`, adds the change to `self.diagnosed` before the real call, as a rescue that wrote `rescue.md` does, and records whether it is still there after; the record is `[(True, False)]` |
| `test_the_metrics_script_scan_reports_a_missing_script` (`tests/test_skills.py:510`) | `stamp.py`'s `not named` line, per [D7](#d7) |
| `test_a_hard_brief_is_ready_for_the_cut` (`tests/test_brief_check.py:69`) | a tenth item nested three spaces in, as the template writes it, is ready |
| `test_a_brief_out_of_shape_halts` (`tests/test_brief_check.py:81`) | `- **x;y** · minor · after: none` as a top-level item halts `not a numbered item`, and `5. **ok** · minor · after: none · after: a;touch-p`, with its models line, halts `item 5 — more than one after:`; the `*`, one-space `- `, `+` and two-space `2)` items halt `not a numbered item`; a `2.<tab>` head, a `3.  ` head and a three-space `- ` under a `10. ` head halt the same; a `* models:`, `-<tab>models:` or `-  models:` line halts `a models line not written`, and a second `- models:` halts `more than one models line` |

No test is deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- An archive corrected in place reads differently from the release that shipped it → git keeps the old text (D23), and this
  change's [D8](#d8) names each edit.
- A Codex conductor of converge runs `stamp.py` through `uv` as it runs `gate_run.py` → a host with no `uv` already halts at the
  gate.
- `0083`'s archive corrected to the code at this base reads without [D5](#d5)'s new halts → those are this change's, recorded
  here.

## Verdict

Ready to build.
