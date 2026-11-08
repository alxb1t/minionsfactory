# Cross-model converge — design

How a checker runs on the host its table names, how a shadow round measures it, and how the metrics show the result.
**Verdict:** settled; build the phases in order, on `0096-codex-ready`'s fake `codex`, spawn line and price table.

## Context

What the run does at `754ba66`; `C` is `skills/mf-ship/scripts/conduct.py`. Each count is the command's output.

- **F1. A checker runs on converge's host.** `_models` halts a worker table naming an `executor` (`C:2160-2162`) and puts every
  worker on converge's (`C:2170`). `_worker_clause` (`C:2182-2192`) gives `""` on Codex; its one caller is `C:3782-3785`.
  `test_a_worker_clause_names_its_model_and_effort` asserts the halt (`tests/test_conduct.py:3803-3805`).
- **F2. A Claude conductor cannot start Codex.** Its sandbox writes the trees and the common directory alone (`C:2633`),
  denies `~/.codex/auth.json` (`C:185`) and `OPENAI_API_KEY` (`C:193`), and reaches `NETWORK` (`C:196`) alone.
- **F3. The rejoin mailbox.** `_queue` (`C:4997`) is `~/.mf-ship-origin/<digest>.queue`, where no worker writes; `_entries`
  (`C:2510`) reads and empties a folder through one descriptor, following no link. D47 calls it "a mailbox that holds no state".
- **F4. A station's thread blocks.** `work` waits in `worker.wait(timeout=TIMEOUT)` (`C:2833`), `TIMEOUT = 10800` (`C:49`):
  nothing in a version's thread runs while its worker does. `conduct.py agent` (`C:5532`) takes no model, and no skill calls it.
- **F5. A Bash call is bounded.** Claude Code's Bash tool waits 120000 ms by default and 600000 ms at most, and a checker can
  run longer.
- **F6. The models line.** `brief_check.py`'s `models` (`:162-176`) wants four parts, `STATIONS` (`:46`) in order, each word
  matching `TOKEN` (`:42`): `codex/gpt-6.1-sol` fails it. The cut writes worker tables from its tiers
  (`skills/mf-cut-change/SKILL.md:365-367`); its template's `executor` is "usually the person's edit" (`:405`).
- **F7. The probes.** `Run.executors` (`C:4192-4195`) and `admit` (`C:4417-4418`) read the plan's executors, worker tables
  among them, so a worker table that names its own executor is probed once `_models` returns it.
- **F8. One model a change.** `read_change` keeps conformance's `model:` first (`review_metrics.py:781`); `model_table`
  (`:945-981`) groups changes by that model and the engine; the findings frontmatter has no `executor:`
  (`skills/mf-converge/references/worker.md:36-52`). `review_metrics.py`'s `STATIONS` (`:47`) and `run.py`'s (`:29`) name no
  checker; `run.py`'s `spawns` skips any other station (`:237`).
- **F9. Cards.** Conformance's ids are `R<n>`, adversarial's `S<n>` (`worker.md:148`); a card's **Round** field names the round
  that raised it. `debt_match.py` splits cards (`cards`, `:52`) and reads **What it affects** spans (`AFFECTS`, `SPAN`, `LINES`,
  `:26-28`); `open_cards.py` copies the split. No script matches cards across files.
- **F10. The verify log.** `verify.md:36-37` appends each transition "as a dated line" in no fixed form, so no reader can
  tell one card's first verify.
- **F11. The tests.** `grep -c "^def test_"` prints `131` for `tests/test_conduct.py` (`135` once `0096-codex-ready` lands, per
  its design), `3` for `tests/test_brief_check.py`, `10` for `tests/test_review_metrics.py` and `21` for
  `tests/test_skills.py`. `_METRICS_SCRIPTS` (`tests/test_skills.py:500-521`) names each script a skill must name.

## Goals / Non-Goals

**Goals:** a checker runs on its table's host; a shadow round 1 runs the other host on the same freeze; the review metrics read
per role and executor and show four headline numbers; the gate proves each with the fake `codex` and a fake `claude`.

**Non-Goals:** the calibration bench; Codex as builder or releaser; a recommendation on the page.

The cut decided these under the brief's switch, each logged in the brief's `## Decisions`:

| id | decision | because |
|---|---|---|
| C3 | a models part names its host on build, converge, release, conformance and adversarial alone; `cut` and `fix` take none, and an unprefixed checker runs on converge's host | the cut's executor is the plan session's runtime evidence, passed as `--executor` (`skills/mf-plan/SKILL.md:139-141`); the fixer is converge's own subagent, and the brief keeps it on Claude |
| C4 | a shadow checker runs on the host its role's checker does not, on `[converge]`'s model and effort when converge runs there, else that host's default; the models line takes a last `shadow`, which the cut writes as `[converge] shadow = true`; the next five versions' `shadow` is the person's at each plan's close | X4 names no shadow model, and an unattended run halts on a models file a hand edits mid-run, so the flag travels through the brief |
| C5 | an escape is `run.py`'s — a card `repeat of` an earlier change's card — traced to that change's round 1 by the card's role and that role's executor; the page reads no proposal, so a paydown's own repeat counts; the verify log line names its card, `- <YYYY-MM-DD> · <id> <from> → <to>`, so a first verify can be read | the repo holds no other escape (F9); review metrics read `.minions/` alone ([D50](../../../docs/decisions.md#d50--review-metrics-are-read-across-repos-and-drawn-on-one-page)); F10 |

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | The models line grammar | X2, C3, C4 | a separate checkers line |
| [D2](#d2) | The plan's and the cut's text | X2, C4 | `executor` left to the person's edit |
| [D3](#d3) | Checker tables name an executor; the clause; the probes | X2, X3 | a checker's executor read from the request |
| [D4](#d4) | The mailbox and `conduct.py checker` | X3 | `.minions/` as the mailbox · `conduct.py agent` |
| [D5](#d5) | `conduct.py` serves the mailbox while converge runs | X3 | polling from `Run.join` |
| [D6](#d6) | The converge worker may write its mailbox | X3 | widening every worker |
| [D7](#d7) | `tests/fake_claude.py` and the fakes' checker | X3 | faking through `MF_SHIP_AGENT` alone |
| [D8](#d8) | Converge's text: dispatch, verdicts, the fixer, `executor:` | X3, X5 | — |
| [D9](#d9) | Shadow round 1 | X4, C4 | a shadow on every round |
| [D10](#d10) | `overlap.py` | X4 | matching by title |
| [D11](#d11) | The run metrics count the mailbox's checkers | X5 | a stage of their own |
| [D12](#d12) | The review metrics per role and executor, and the headline | X5, C5 | a recommendation |
| [D13](#d13) | D68; D11, D40, D41, D47, D49, D50 and D64 amended; the threat model | X8 | — |

### D1

`brief_check.py`'s `models(number, text)` splits the line on ` · ` as now. Its parts are the four of `STATIONS` in order, then
any of `CHECKS = ("conformance", "adversarial", "fix")` in that order, each of three words, then at most one last part
`shadow` of one word. Out of shape → `MODELS`, reworded: "the models line is not build · converge · release · cut, then any of
conformance · adversarial · fix, each <model> <effort>, then shadow". A model word may open `<host>/`:

- `HOSTS = ("claude", "codex")`; another host → `item <n> — not a host: \`<host>\``;
- a host on `cut` or `fix` → `item <n> — <part> takes no host: \`<word>\``;
- the word after the host, and each effort, still matches `TOKEN`.

The module docstring names this design's D1. `tests/test_brief_check.py`'s `test_a_hard_brief_is_ready_for_the_cut` gains the
spec's full line; `test_a_brief_out_of_shape_halts` gains `gemini/x`, a host on `fix` and on `cut`, `shadow` before `fix`, and
a second `shadow`.

### D2

- **`skills/mf-plan/SKILL.md`** — the template's models line gains
  ` · conformance <host/model> <effort> · adversarial <host/model> <effort> · fix <model> <effort> · shadow`, each optional,
  and the paragraph under it says: a host prefix, `claude/` or `codex/`, names a part's executor, none meaning the run's for a
  station and converge's for a checker; `cut` and `fix` take none; `shadow` turns on the shadow round 1, the person's choice
  at each close.
- **`skills/mf-cut-change/SKILL.md`** — *Suggesting models*' paragraph at `:365-367` becomes: the brief's parts are written
  exactly, each host as the table's `executor`; a checker or fixer part the brief lacks is written from the Converge bullet;
  `shadow` is written as `shadow = true` under `[converge]`. The template's `# executor = "codex"` comment at `:405` becomes
  `# executor = "codex"  # optional, per table, from the brief's host; absent, the run's, and converge's for a checker`, and
  `[converge]` gains `# shadow = true  # from the brief's shadow`.

### D3

- **`_models`** — for a station of `WORKERS`, an `executor` in `converge.conformance` or `converge.adversarial` is kept; in
  `converge.fix` it still halts, `… converge.fix names an executor`. A checker with none takes converge's. The Codex check
  covers a checker whose own executor is Codex, as a station's. The docstring names this design's D3.
- **`_worker_clause(station, models, converge)`** — `converge` is converge's executor. A checker whose executor differs →
  ` and <role>=mailbox`; else, as now, `""` with `converge == "codex"` or neither named, and the model clause otherwise.
  `C:3782-3785` passes converge's executor.
- **`_shadows(runs, change)`** — whether `[converge]` says `shadow = true`; `read_plan` adds the version to `self.shadowed`, as
  it reads `auto_grant`. The converge prompt then ends its worker clauses with ` and shadow=yes`.
- **`_shadow(converge, checker)`** — returns a shadow checker's models: the executor of `EXECUTORS` that is not `checker`'s,
  with `converge`'s model and effort when `converge` runs on it, else `None, None`.
- **`Run.named(change)`** — the executors the version's plan names, plus `_shadow`'s for each checker of a shadowed version.
  `executors` and `admit` read it, so each checker host and shadow host is probed at the start or as the version joins.

### D4

The **checker mailbox** of a version is `_mailbox(primary, change)`, `_queue(primary) / "checkers" / change`. It sits outside
the trees, where only that version's converge worker is given a write ([D6](#d6)); `_queue`'s docstring says so. Constants:
`CHECKERS = ("conformance", "adversarial", "shadow-conformance", "shadow-adversarial")`, `MAILBOX_POLL = 2`,
`CHECKER_WAIT = 100`, `REQUEST_BYTES = 65536`, `CHECKER_SPAWNS = 8` — three rounds of two checkers and a shadow pair.

`conduct.py checker <change-id> <role> [--wait]`, run by the sandboxed converge conductor, is `checker(cwd, change, role, wait)`:

- `change` not matching `CHANGE_ID`, or `role` not of `CHECKERS` → exit 2. The primary is `primary_of(cwd)`; no mailbox
  folder, or a link → `checker: cannot run — this converge has no mailbox`, exit 2.
- Without `--wait`: read `.minions/changes/<change-id>/<role>.prompt.md`, a regular file by `os.lstat`, at most
  `REQUEST_BYTES`, else exit 2; write it to `.<role>.request` through the mailbox's descriptor, `O_CREAT | O_EXCL | O_NOFOLLOW`,
  and rename it to `<role>.request`.
- Then wait, polling every `MAILBOX_POLL` seconds, for `<role>.answer`; on it, read it through the descriptor, unlink it,
  print it and exit with the number after `exit `, 1 when there is none. Past `CHECKER_WAIT` seconds, print
  `checker: waiting — run conduct.py checker <change-id> <role> --wait` and exit 3. `--wait` waits alone.

`CHECKER_WAIT` sits under F5's default, so one foreground call never outlives the tool, whatever timeout the conductor
passes; a re-run without `--wait` would send a second request, so the skill says `--wait` ([D8](#d8)).

### D5

- **`work(command, cwd, out, claim, between=None)`** — with `between`, it waits in steps of `MAILBOX_POLL` seconds, calling
  `between()` after each, until the worker exits or `TIMEOUT` passes from its start; without it, as now.
- **`serve_requests(mailbox, served, spawn)`** — a module function. It lists the mailbox by `_entries(mailbox, empty=False)`
  and takes each `<role>.request` of `CHECKERS`, in that order: opened through the folder's descriptor with `O_NOFOLLOW`, a
  regular file by `fstat`, at most `REQUEST_BYTES`, then unlinked. A request of a role that is a link, no regular file or
  past `REQUEST_BYTES` is unlinked, and answered `exit 1 · refused: <role>.request is a link, no file or too long`. Any entry
  named for no role is left and named nowhere: `conduct.py checker` sends none. Past `CHECKER_SPAWNS` served, the answer is
  `exit 1 · refused: more than 8 checker requests`; else `spawn(role, prompt)` returns the answer. Each answer is written as `<role>.answer`: any old one unlinked, then made `O_CREAT | O_EXCL | O_NOFOLLOW`
  through the descriptor. It returns the count served.
- **`Run.checker(change, role, cwd, prompt)`** — the models are `self.plan[change, "converge.<role>"]`, or `_shadow` of
  converge's and the role's for a shadow. It runs the worker as `spawn` does — `argv`, the run log's `spawn` event
  naming `converge-<role>`, `_free_log`'s `<stamp>-converge-<role>.log` opening with `0096-codex-ready`'s `mf.spawn` line on
  Codex, so its dollars are priced, `work` with the run's claim folder, `finish` and `denied` events — and halts nothing. It
  returns `_answer(code, killed, models, limit)`, a module function: `exit <code> · executor <x> · model <m or default> ·
  effort <e or default>`, then ` · timed out` when `TIMEOUT` killed it, then `usage_limit`'s text.
- **`Run.spawn`** — gains `mailbox: Path | None = None`, passed to `argv` as `mailbox=` only when set, so a test's spy on
  `argv` keeps its shape. With it, `work` gets `between`, which calls `serve_requests` with `Run.checker` bound to the version.
- **`advance`** — before a converge spawn of a version with a checker on another host or a shadow, `_open_mailbox` makes the
  folder, mode `0o700`, and empties it by `_entries(…, empty=True)`; a mailbox that is a link or no folder by `os.lstat` halts
  the version: `the checker mailbox <path> is a link`.

Serving runs in the version's own thread, so its checkers run one at a time: [D40](../../../docs/decisions.md#d40--workers-are-fresh-and-observable)
allows sequential workers on one freeze.

### D6

`argv` gains `mailbox: Path | None = None`. On Claude it joins the writes `worker_settings` gets, and no `--add-dir` or `Edit`
rule: the conductor writes it through `conduct.py checker` alone. On Codex it joins the writable roots, so `0096-codex-ready`'s
`_unswapped` checks it. No other spawn passes one.

### D7

- **`tests/fake_claude.py`** — stands in for `claude`: it appends its argv, one JSON list a line, to `FAKE_CLAUDE_ARGV`, sets
  `FAKE_HOST=claude`, and hands the argument after `-p` to `_fake` of `tests/fake_worker.py`, loaded with `runpy`.
- **The `fake_codex` fixture** — also writes `bin/claude`, a `#!/bin/sh` script running `sys.executable -S
  tests/fake_claude.py "$@"`, and sets `FAKE_CLAUDE_ARGV`. `tests/fake_codex.py` sets `FAKE_HOST=codex` before it calls
  `_fake`.
- **`tests/fake_worker.py`** — a prompt matching `converge's (\S+) checker for change (\S+?)[ .]` is the station `checker`. For
  `0001-probe` it keeps `0096-codex-ready`'s D9 record and verdict, and gains `executor:` `FAKE_HOST`, as `FINDINGS_KEYS`
  now holds it. Otherwise it records `checker <change> <role>`, and writes
  `.minions/changes/<change>/<role>.md` with every key of `FINDINGS_KEYS`, `executor:` `FAKE_HOST` — `claude` when unset, as
  under the `fake` fixture — `verdict: clean`,
  `open_blocking: 0`, `head:` the worktree's `HEAD` and `round: 1`. Under `FAKE_MODE` `shadow-blocks`, a shadow role's file
  instead reads `verdict: changes-requested`, `open_blocking: 1` and holds one `blocking` card.
- **The fake converge** — for each clause `<role>=mailbox`, it writes `.minions/changes/<change>/<role>.prompt.md`,
  `You are converge's <role> checker for change <change>.`, and runs `conduct.py checker <change> <role>` with
  `sys.executable -S`, exiting 1 on a non-zero exit. Then `_findings`, given a new `roles` argument, writes the file of each
  role no clause names — none when both are mailbox roles — and the status log. Under ` and shadow=yes` it does the same for
  `shadow-conformance` and `shadow-adversarial` after both, ignoring their exits.

### D8

- **`skills/mf-converge/SKILL.md`, *The workers*** — `<role>=mailbox` names a checker on another host: send it by writing its
  whole dispatch prompt to `.minions/changes/<change-id>/<role>.prompt.md`, then running
  `uv run --script <this package>/../mf-ship/scripts/conduct.py checker <change-id> <role>` in the foreground; exit 3 → run it
  again with `--wait`, never without, until it exits 0 or 1. Its answer gives the role's executor, model and effort. Exit 1 is a worker that
  failed. Every other role is dispatched as now.
- **Step 5's `verdicts` row** — the executor, model and effort are the mailbox's answer for a mailbox role, else as now.
- **Step 6** — the fixer runs on `adversarial=`'s model when a card it is sent blocks and adversarial is no mailbox role, else
  on `fix=`'s: a model of another host cannot run there.
- **`references/worker.md`** — the frontmatter gains `executor: <claude | codex, the host you run on, from runtime evidence>`
  after `model:`; a shadow checker writes `shadow-<role>.md`, with the same contract. `FINDINGS_KEYS` in `C` gains `executor`.
- **`skills/mf-ship/SKILL.md`** — "Converge runs MF's method." gains "; a checker on another host than converge's runs through
  the checker mailbox `conduct.py` serves."

### D9

A new section, `## Shadow round 1`, after *The workers* in `skills/mf-converge/SKILL.md`, says: under `shadow=yes`, round 1 of a
run marked neither `catch-up` nor `amend`, once its `verdicts` lines are written and before Step 5 decides, sends
`shadow-conformance` and `shadow-adversarial` through the mailbox, each with its role's packet and reference and the findings
path `shadow-<role>.md`. Step 5 reads no shadow file; no fixer, pickup, debt card or `done` counts one. After both, run
`uv run --script <this package>/scripts/overlap.py .minions/changes/<change-id>` and write its line as the round's `shadow`
event; a shadow that exited 1, or an `overlap.py` exit 2, is written as the `shadow` event instead and halts nothing. A resumed
run sends no shadow. The events table gains a `shadow` row, written in *Shadow round 1*, and the resume table a `shadow` row
that goes on at Step 5.

### D10

`skills/mf-converge/scripts/overlap.py <change-folder>`, a `uv` script, reads `conformance.md` and `adversarial.md`, the cards
whose **Round** is `1` or absent, and `shadow-conformance.md` and `shadow-adversarial.md`, every card. Its card split and
`AFFECTS`, `SPAN` and `LINES` are `debt_match.py`'s, copied, as `open_cards.py` copies them.

- **Anchors** — a card's anchors are the `path` and line numbers of each span of its **What it affects**: `path:12`,
  `path:12-14`, or a bare `path`.
- **A match** — two cards match when they share a path and a line of one lies within `NEAR = 5` of a line of the other, or
  either names that path with no line. Each shadow card matches at most one primary card, taken in the files' order.
- **A blocker** — a card whose Priority's first word is one of its role's blocking grades: `blocking`; `critical`, `high`.
- **`overlap(primary, shadow, blocking)`** — returns `shared`, `primary_alone`, `shadow_alone`, `shared_blockers`,
  `primary_blockers` and `shadow_blockers`.

It prints one line, the roles joined by `; `: `conformance shared 1 · primary (codex) alone 2 · shadow (claude) alone 1 ·
blockers shared 1 · primary 0 · shadow 1`, each side's executor its file's `executor:`, else `unknown`. A missing or unreadable file →
`overlap: cannot read — <file>`, exit 2. `tests/test_overlap.py` holds `test_the_overlap_counts_shared_and_unique_catches` and
`test_the_overlap_refuses_what_it_cannot_read`.

### D11

`scripts/metrics/run.py`:

- `CHECKERS = ("converge-conformance", "converge-adversarial", "converge-shadow-conformance", "converge-shadow-adversarial")`;
  `Version.spawns` also takes their spawns, which `stage` returns for no stage, so no minute changes.
- `spent(stages)` adds each `CHECKERS` spawn's log with the stage of the converge spawn whose start-to-finish holds its start,
  so a catch-up's checker counts in `catch-up`; `_spent` reads it as any log.
- `role_tokens(role)` adds the tokens `_spent` reads from each `converge-<role>` log, and gaps only when neither a subagent
  event nor such a log is found.

`test_run_metrics_read_cost_and_review_yield` gains a priced Codex `converge-conformance` log inside a converge.

### D12

`skills/mf-review-metrics/scripts/review_metrics.py`:

- **Stations** — `STATIONS` gains `converge-conformance`, `converge-adversarial`, `converge-shadow-conformance` and
  `converge-shadow-adversarial`, so each checker's log is a cost cell.
- **`roles`** — `read_change` keeps a record per role: `role`, `executor` — the file's `executor:`, else the executor its round
  1 `verdicts` line names, else `null` — `model`, `findings`, `blocking`, `confirmed` and `confirmed_blockers`, the cards both
  `Verdict: confirmed` and blocking. `model_table` groups these by role, executor and model, in place of the change's one
  model and engine. The change record's own `model` and `engine` fields stay, as their tests assert.
- **`escapes`** — each card in a role file whose `repeat of <N>·<id>` names an earlier change `N`, as `run.py`'s `REPEAT` reads
  it: `change`, `card`, `earlier`, and the role and executor of `N`'s file for the card's role, `R` conformance, `S`
  adversarial.
- **`shadow`** — per change and role with a shadow file, `overlap.py`'s `overlap`, loaded with `runpy` from
  `../../mf-converge/scripts/overlap.py`, with each side's executor.
- **First verifies** — on each role record, `first_verified` and `first_reopened`: per card, the first `## Resolution log`
  line naming it with `fixed → verified` or `fixed → open`, by [C5](#goals--non-goals)'s form; a log in no such form is a gap.
- **`headline(changes, shadow, escapes)`** — over `read_repo`'s change records, which hold the role records and cost cells,
  four numbers, each per executor where it has one, `null` with no data:
  - `unique_blocker_share` — per executor, the blockers its side alone caught over every shadow round's distinct blockers,
    shared ones counted once;
  - `escapes_per_version` — escapes over the changes read with a role file;
  - `dollars_per_confirmed_blocker` — per pairing, `claude`, `codex` or `mixed` by the role files' executors, the converge
    and checker cost cells summed over the confirmed blockers, changes with a cost gap left out;
  - `first_verify_pass_rate` — per executor of the file that raised the card, first verifies `verified` over all first
    verifies.
- **The page and the JSON** — `render_page` opens with a `headline` table of the four numbers; `review-metrics.json` gains
  `roles`, `shadow`, `escapes` and `headline` beside `generated` and `records`.

`skills/mf-converge/references/verify.md:36-37` names the log line's form; `skills/mf-review-metrics/SKILL.md` names the
headline numbers in its *Run* and the role table in its *Report*. `test_the_cross_model_numbers` is the spec's scenario;
`test_the_page_draws_charts_and_lists_gaps` asserts the role table where it asserted the model table.

### D13

- **D68**, in `docs/decisions.md` after D66, in *The check loop and the release* and the map's line:

### D68 · Converge's checkers may run on another host, and a shadow round measures it

**A conformance or adversarial table may name its executor, and the models line its host. A checker on another host than
converge's runs through the checker mailbox, in the home folder's queue: the conductor writes the request, `conduct.py` spawns
the checker on the plan's model and effort, and the conductor reads its findings from disk. The fixer stays on converge's host.
Under `[converge] shadow = true`, round 1 also runs the other host's checkers on the same freeze, into shadow files that drive
nothing, and `overlap.py` counts what each side alone caught. The review metrics read per role and executor.**

- **Why:** a sandboxed Claude conductor cannot start Codex, and the person wanted Codex's review with Claude's fix, and the
  numbers first.
- **Accepts:** a mailbox the converge worker writes, bounded to `CHECKER_SPAWNS` a spawn · checkers served one at a time ·
  a shadow pair's spend each round 1 it is on.
- **Rejected:** `.minions/` as the mailbox — every worker writes it · a checker's model from its request · a fixer on another
  host · a shadow on every round.

- **D11** — "converge's take their model and effort from its worker tables" gains ", a checker its executor too
  ([D68](#d68--converges-checkers-may-run-on-another-host-and-a-shadow-round-measures-it))".
- **D40** — the body gains "A checker on another host than its conductor's is a fresh agent process `conduct.py` starts on the
  conductor's request ([D68](#d68--converges-checkers-may-run-on-another-host-and-a-shadow-round-measures-it))."
- **D41** — "converge's worker tables on [D64]'s tiers among it" gains ", each host the brief names as its `executor`".
- **D47** — the *Executors* bullet's "the models file names a station's executor, absent meaning the run's" gains ", and a
  checker's, absent meaning converge's"; its "a worker reaches the primary and the open worktrees alone" gains ", and a
  converge worker its checker mailbox".
- **D49** — the Rejected "a third findings file" gains " — a shadow file drives nothing
  ([D68](#d68--converges-checkers-may-run-on-another-host-and-a-shadow-round-measures-it))".
- **D50** — "tables per repo and per model" becomes "tables per repo and per role, executor and model, four headline numbers".
- **D64** — the Accepts' "on Codex every worker runs on the conductor's model" becomes "on Codex every worker on the
  conductor's host runs on the conductor's model".
- **`THREAT_MODEL.md`** — *Entry points* gains, after the rejoin bullet: "Checker requests, in the home folder's queue,
  `checkers/<change-id>/`: that version's converge worker alone may write it, so no other worker forges one. A request names
  one of four roles by its file name and holds a checker's prompt; `conduct.py` reads it through one descriptor, following no
  link, at most `REQUEST_BYTES`, takes the executor, model and effort from the plan it read once, never from the request, and
  serves at most `CHECKER_SPAWNS` a converge spawn, so a forged request spends at most that." In *Trust boundaries*, "writes
  stay in the repo and its worktrees" gains ", a converge worker's also in its checker mailbox", and the mixed-run bullet
  gains: "Within converge, a checker the mailbox starts on another host writes its findings file, which the conductor
  reads as evidence, as it reads a subagent's."
- **`docs/principles.md`** — *The repo reaches nothing outside itself*'s queue item, "its lock, its queued cuts and its rejoin
  requests", gains ", and a converge worker's checker mailbox, which that worker writes".

## Tests

The tests the change adds and extends, all at the unit and integration layer of `pytest`; no end-to-end test, so no engine
runs (`T1`).

| file | before | after | counted by |
|---|---|---|---|
| `tests/test_conduct.py` | 135 | 140 | `grep -c "^def test_" tests/test_conduct.py` |
| `tests/test_brief_check.py` | 3 | 3 | `grep -c "^def test_" tests/test_brief_check.py` |
| `tests/test_overlap.py` | 0 | 2 | `grep -c "^def test_" tests/test_overlap.py` |
| `tests/test_review_metrics.py` | 10 | 11 | `grep -c "^def test_" tests/test_review_metrics.py` |
| `tests/test_metric_scripts.py` | 15 | 15 | `grep -c "^def test_" tests/test_metric_scripts.py` |
| `tests/test_skills.py` | 21 | 21 | `grep -c "^def test_" tests/test_skills.py` |

- **Added:** `test_a_checker_on_another_host_is_planned_and_probed` (D3; unit, `_models`, `_shadow`, `Run.named`),
  `test_a_codex_checker_runs_through_the_mailbox` (D4–D7; integration: `main run` over `fake_codex`, as
  `test_a_station_runs_on_its_executor` drives it, with `_unlinked` and `_executor_missing` patched through `main`'s globals
  so the fake hosts pass them), `test_the_checker_command_sends_and_waits` (D4; unit, `checker` in-process: each exit 2, the
  exit 3 with `CHECKER_WAIT` patched to 0, `--wait` reading an answer), `test_a_checker_request_is_bounded` (D5; unit,
  `serve_requests`, `_answer` with `killed`, and `_open_mailbox` on a link), `test_a_shadow_round_drives_no_fix` (D9; integration),
  the overlap tests (D10; unit), `test_the_cross_model_numbers` (D12; unit over a fake repo).
- **Extended:** `test_a_brief_out_of_shape_halts` and `test_a_hard_brief_is_ready_for_the_cut` (D1),
  `test_run_metrics_read_cost_and_review_yield` (D11).
- **Edited:** `test_a_worker_clause_names_its_model_and_effort` — the clause's `converge` argument, a Codex conformance under a
  Claude converge giving ` and conformance=mailbox`, and the executor halt moved to `converge.fix`;
  `test_the_page_draws_charts_and_lists_gaps` — the role table; `test_run_logs_give_cost_turns_and_tokens_per_station` — the
  cost row's checker columns; `_METRICS_SCRIPTS` and the expected lists of
  `test_the_metrics_script_scan_reports_a_missing_script` — `("mf-converge", "../mf-ship/scripts/conduct.py")` and
  `("mf-converge", "scripts/overlap.py")`.
- **Removed:** none.

## Dependencies

None.

## Risks / Trade-offs

- **[A worker writes the home queue]** → the converge worker writes one folder there, not the queue's lock, cuts or rejoin
  requests; each read and answer goes through the folder's descriptor, following no link ([D5](#d5)).
- **[A forged request spends]** → at most `CHECKER_SPAWNS` checkers a converge spawn, each on the plan's model; it is in the
  threat model's accepted class of a worker steering the conductor through what it writes.
- **[Sequential checkers]** → a Codex checker and the conductor's own subagent still run side by side; two mailbox checkers wait
  on each other, a longer round, never a wrong one.
- **[A long checker]** → `conduct.py checker` returns at `CHECKER_WAIT` with exit 3, and the conductor waits again; `TIMEOUT`
  still bounds the converge worker.
- **[The shadow's spend]** → the person turns it on per version at the plan's close ([C4](#goals--non-goals)).
- **[Card matching is coarse]** → two findings on nearby lines count as one; the page gives counts, never a ranking.

## Verdict

Settled: the models line, the mailbox, the shadow round, then the metrics and the record, each phase ending on a green
`make check`, the last on the gate.
