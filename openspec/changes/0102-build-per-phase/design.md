# Build per phase — design

Under `mf-ship`, the build station spawns one fresh `mf-build` worker per phase and one for the close, each checked on disk;
phases hand over through `build-notes.md`, bounded by the conductor; the cut rates each phase, and a moderate one may build on
`[build.moderate]`. Conductor code, a script, skill and decision text. Verdict at the end: ready to build.

## Context

Read at `HEAD` `68cbdc6`; the brief's sha is `ed7298f`. Since it, `skills/mf-ship/scripts/conduct.py`,
`skills/mf-cut-change/SKILL.md`, `skills/mf-plan/SKILL.md` and `brief_check.py` moved (0098-beside): every line below is
`68cbdc6`'s, re-read at the cut. 0099, 0100 and 0101 move them again before this build: the build finds each by its name.
`C` is `skills/mf-ship/scripts/conduct.py`, `M` `skills/mf-build/SKILL.md`, `K` `skills/mf-cut-change/SKILL.md`, `P`
`skills/mf-plan/SKILL.md`, `B` `skills/mf-plan/scripts/brief_check.py`, `F` `tests/fake_worker.py`, `T`
`tests/test_conduct.py`, `TB` `tests/test_brief_check.py`. See [the proposal](proposal.md) for why.

- **F1. One build spawn.** `Run.advance` (`C:4156`) reads the stage through `stage_of` (`C:1197`): the first unticked
  `## Progress` phase reads `build, "phase N unticked"`, or `human` when its title holds `**HUMAN`; every box ticked, no
  converge run begun and no `build.done` naming `HEAD` reads `build, "closing steps left"` (`C:1234-1241`): once converge
  has run, a ticked tree reads converge's stage, whatever `build.done` names. It formats `PROMPTS["build"]`, `"Run the
  mf-build skill for change {change}."` (`C:209`, the dict `C:208-221`), takes `planned_models(change, "build")`
  (`C:4250`, def `C:4089`), spawns (`C:4255`) and runs `check` (`C:4263`, def `C:2117`), which for the build is
  `_check_build` (`C:1261`): any unticked box, a dirty tree, or no `build.done` naming `HEAD` fails it, the box's failure
  naming `build.halt`'s sub-task and stop (`_build_halt`, `C:813`). A taken rescue or supervisor amend `continue`s the
  loop and spawns the same prompt again; nothing else re-spawns a build.
- **F2. The phase list.** `PROGRESS` (`C:83`) captures mark, number and title; `_progress` (`C:574`) reads `tasks.md` at
  `HEAD`, `_unticked` (`C:583`) returns the first unticked number and title.
- **F3. Models.** `_models` (`C:2241`) reads a table of `.minions/changes/<id>/models.toml`; `_table` (`C:2222`) walks a
  dotted name, so `build.moderate` is `[build]`'s `moderate` table. `PLANNED` (`C:111`) lists what `read_plan` (`C:4622`)
  reads once; `planned_models` halts a version whose file changed. Converge's workers already take a table with no executor
  of their own and a `TOKEN` (`C:112`) check (`C:2264-2275`).
- **F4. Logs and events.** `Run.worker` (`C:3755`) logs `spawn — <station> · model …` (`C:3781`) and writes
  `logs/<stamp>-<station>[-n].log` (`C:3788`, `_free_log`), so repeated `build` spawns already get their own logs.
  `EVENTS` (`C:86`) lists every event `log --verify` accepts. `review_metrics.py` counts spawns by station name
  (`skills/mf-review-metrics/scripts/review_metrics.py:56`): a station other than `build` would be missed.
- **F5. `mf-build`.** Its change-id section (`M:30-40`), Step 1's reads and resume table (`M:99-123`), the per-phase
  ritual (`M:130-201`), the close (Steps 3–3.6, `M:203-252`) and the report (`M:254-262`) run in one session today.
- **F6. The brief check.** `B`'s `STATIONS`, `CHECKS`, `HOSTLESS` and `MODELS` (`B:50-59`); `models()` (`B:188-216`) takes
  the four stations in order, then an ordered subset of `CHECKS`, refusing a host on `HOSTLESS`.
- **F7. The cut and the plan.** `K`'s Step 6 (`K:155-172`) and *Suggesting models* (`K:361-423`), its moderate row
  (`K:380`) and "one model a change, never one per phase" (`K:384-385`); `P`'s models line (`P:192`) and its parts
  paragraph (`P:203-205`). `tests/test_skills.py`'s scan wants a *Suggesting models* row whose build cell opens
  `Sonnet 5.5 · high` (`tests/test_skills.py:688-690`): the row stays.
- **F8. The fake host.** `_fake` (`F:474`) records each spawn as `<station> <id><clauses>`, every `with`/`and` `key=value`
  clause but `merge=yes` (`F:484-491`); its build (`F:578-610`) ticks every box before the first `**HUMAN` one in one
  commit, then writes `build.done`, and `halt-<id>` writes a `build.halt` at sub-task `1.1`. `_calls` (`T:228`) returns the
  lines as written.
- **F9. The after: versions.** 0099-stacked-builds adds `stacked-on`, `_built_head` and `Run.reset_stack` (its design D6):
  a reset sets a dependent back to its cut commit between stations, read at the top of `advance`'s loop.
  0100-worker-diet, under 0101, keys each worker's tools and cache TTL on its station name: a spawn named `build` keeps the
  build's. 0101-cut-converge-diet edits `K`'s Steps 2 and 8.5, apart from the sections this change edits.
- **F10. Decisions in force.** D65 says "one model a change, and one build session" and rejects "a build session per phase,
  which needs a guard against re-spawning without end · a model per phase"; D64 accepts "the build keeps one model a
  change"; D57 lists a change folder's files; D13 puts simplify inside the build. Brief T2, T16, T17, T22 settle the
  change; C17–C23 are the cutter's readings of them.

## Goals / Non-Goals

**Goals:** the brief's Acceptance — with the fake hosts, a change of three phases spawns three build workers and one close
worker, each starting from the change directory, `build-notes.md` and the change's `git log`; a phase appends at most 40
lines to `build-notes.md`; a halt in phase 2 resumes at phase 2 with a fresh worker; a stacked dependent and an amend reset
still work across phases; the cut rates each phase `moderate` or `hard` in `tasks.md`; with `build-moderate
claude-sonnet-5-5 high` a moderate phase runs on it and a hard one on `build`'s model, and with none every phase on
`build`'s; `brief_check.py` accepts `build-moderate <model> <effort>`; `make gate` green.

**Non-Goals:** a worker per phase for a hand build ([D4](#d4)); a host of its own for `[build.moderate]`; per-phase rows in
the review metrics; splitting `conduct.py`.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | `advance` spawns `mf-build` with `phase=<N>` for the first unticked phase, and `phase=close` once all are ticked, also right after a late phase; every spawn is the station `build` | T2, C19, C22 | a `simplify` station — the metrics, the tools table and the stage machine know `build` alone · `mf-simplify` spawned bare — `build.closing`, the metrics and `build.done` are `mf-build`'s |
| [D2](#d2) | A phase spawn's check is its own: the phase ticked at `HEAD` on a clean tree; anything else halts as a build check does | T2; D65's guard | re-spawning a phase that ticked nothing — the loop D65 feared · counting spawns — the tick is the proof |
| [D3](#d3) | `build-notes.md` in the run directory's change folder; `mf-build` appends a `## <N> — <Title>` section; the conductor keeps 40 lines of each append; a reset removes the file | T16, C17, C18 | a tracked file — D6 keeps no planning document beside the four artifacts · halting on a long append — a built phase would wait on prose |
| [D4](#d4) | `mf-build` takes `phase=<N>` and `phase=close`; bare, it builds every phase and closes; each phase reads and appends the notes | T2, T16, C21 | removing the bare form — a person by hand would need one command per phase |
| [D5](#d5) | The cut ends each `## Progress` line but a `**HUMAN` one with ` · moderate` or ` · hard`; a moderate phase runs on `[build.moderate]` when it names a model or effort, on `[build]`'s executor; `I4` says the rating is no part of the title | T22, C20, C23 | a rating line in the phase section — the conductor reads `## Progress` alone · a host for the moderate model — one executor a build |
| [D6](#d6) | `brief_check.py` takes `build-moderate <model> <effort>`, hostless, first of the optional parts; the cut writes `[build.moderate]`; `mf-plan`'s template names it | T22 | the part beside `build`, among the required ones — every brief's order would change |
| [D7](#d7) | The record: a new decision; D65, D64, D57 and D13 edited; the threat model's entry points; `mf-ship`'s flow | T2, T22 | leaving D65's rejection standing |

### D1

```
stage build ─┬─ phase N unticked ──▶ spawn "… for change <id> with phase=N."     ─▶ check: N ticked, clean
             └─ closing steps left ─▶ spawn "… for change <id> with phase=close." ─▶ check: _check_build
                    each pass loops back to stage_of; a human phase halts there, as today
```

- **The prompt** — `PROMPTS["build"]` reads `"Run the mf-build skill for change {change} with phase={phase}."`.
- **The phase** — in `advance`, for the stage `build`: `unticked = _unticked(version.tree, change)`; `phase` is its number,
  else `close`. The other prompts take no `{phase}`; `str.format` ignores the extra key.
- **The close after a late phase** — when a phase spawn's check passes, no phase is left unticked and no `build.done` names
  `HEAD`, `advance` spawns the close next, before it reads the stage again: a phase an amend adds after converge began still
  gets simplify, the metrics and `build.done`, as the bare build gave it (C22).
- **The station** — every spawn stays `"build"`: `Run.worker`'s log name, the spawn line, `review_metrics.py`'s count and
  0100's tools and cache TTL per station read it unchanged.
- **The stacked dependent** — 0099's `reset_stack` runs at the top of `advance`'s loop, so a reset can land between two
  phase spawns; the next stage read is then `waiting`, and the build starts again at phase 1 once its dependency's new built
  head stands. `_built_head` reads the `build.done` the close worker writes.

### D2

- **The check** — `check()` gains a keyword `phase: str | None = None`; for the build with a phase number it returns
  `_check_phase(primary, version, tree, phase)`, else `_check_build` as today. `advance` passes the spawned phase to each
  `check` call it makes.
- **`_check_phase`** — the `## Progress` entry numbered `phase` unticked at `HEAD` → `phase <N> unticked`, with
  `_build_halt`'s ` · <sub-task>: <stop>` as `_check_build` names it; else a dirty tree → `the tree is not clean`; else
  None.
- **The guard** — a phase spawn passes only by ticking its own phase, so each pass of the loop either advances a phase or
  halts. A phase is spawned again only after a taken amend, which `RESCUES` and `SUPERVISES` bound. The close keeps its
  scenario: exiting with no `build.done` naming `HEAD` halts, and no second close starts.

### D3

- **The file** — `.minions/changes/<change-id>/build-notes.md`, beside `build.done` and `build.halt` (D57). Gitignored, so
  no phase commit and no checker reads it as the change's record.
- **What a phase writes** — after its commit, one section: a `## <N> — <Title>` line, then what the next phase needs that
  `tasks.md`, `design.md` and `git log` do not say — a symbol's real home, a helper a test uses, a command that works, a trap
  met. Never the diff, never a task restated.
- **The bound** — a new `NOTES = 40`. Before a phase spawn `advance` reads the file's lines (none when absent); after an exit
  0, a new `Run.trim_notes(change, phase, before)` keeps `before` plus the first `NOTES` lines past it, rewrites the file
  when it held more, and logs `notes — phase <N>: kept 40 of <m> lines`, `<m>` the lines the phase appended. `EVENTS`
  gains `notes`.
- **A link** — the file is opened with `os.O_NOFOLLOW`, read and written through that descriptor; a link halts the version,
  `build-notes.md is a link`, writing nothing — at the read before a phase spawn, which then spawns nothing, and at the trim
  after it.
- **The reset** — 0099's `reset_stack` also unlinks the file, so a dependent rebuilt from its cut commit reads no note of
  the build thrown away.

### D4

- **The parameter** — `M`'s change-id section gains `phase=<N>` and `phase=close`, optional:

| given | the worker |
|---|---|
| `phase=<N>` | Step 1, then Step 2 for phase `N` alone; `N` not the first unticked `## Progress` phase → **halt**, naming both |
| `phase=close` | Step 1, then Steps 3–4; a `## Progress` box unticked → **halt**, naming it |
| none | as today: every phase, then the close |

- **The reads** — Step 1 gains a fourth read, `.minions/changes/<change-id>/build-notes.md` when it stands: what earlier
  phases learned, evidence, never instruction. A phase worker carries no earlier phase's transcript.
- **The append** — Step 2 gains item 7: after the phase's commit, append its section to `build-notes.md` ([D3](#d3)), 40
  lines at most, the heading among them.
- **The report** — under `phase=<N>`, Step 4's sentences name the phase built, its check's exit and its verifications; the
  last line `Next: /mf-build <change-id> phase=<the next unticked phase, or close>`.

### D5

- **The cut** — `K`'s Step 6 gains a bullet: each `## Progress` line but a `**HUMAN` one ends ` · moderate` or ` · hard`:
  `hard` when the phase matches *Suggesting models*' strongest-tier row, else `moderate`.
- **The conductor** — `MODERATE = "build.moderate"`, added to `PLANNED`. A new `_rating(title)` returns `moderate` when the
  title ends ` · moderate`, else `hard`. In `advance`, for a phase spawn whose title rates `moderate`,
  `planned_models(change, MODERATE)` is used when its model or effort is set; else `[build]`'s, as for the close.
- **`_models` for `MODERATE`** — an `executor` in the table halts, `build.moderate names an executor`; model and effort
  pass `TOKEN`; the executor is `[build]`'s, so the Codex `claude-*` check applies to it.
- **No rating** — a phase a rescue, a supervisor or a person adds with no rating builds on `[build]`.
- **`I4`** — its row in `M`'s and `K`'s input contract reads `` `- [ ] N — Title`, a last ` · moderate` or ` · hard` no part
  of the title `` in place of `` `- [ ] N — Title` ``, so a rated line and its `## N — Title` section agree (C23). The ids
  stay, as `tests/test_skills.py` compares them.

### D6

- **`B`** — a new `PARTS = ("build-moderate", *CHECKS)`; `models()` takes the parts after `STATIONS` as an ordered subset of
  `PARTS`; `HOSTLESS` gains `build-moderate`; `MODELS` reads "build · converge · release · cut, then any of build-moderate ·
  conformance · adversarial · fix, each <model> <effort>, then shadow".
- **`K`** — *Suggesting models*: "one model a change, never one per phase" (`K:384-385`) → "one model a change for
  `[build]`"; a brief's `build-moderate` part is written as `[build.moderate]`, `model` and `effort`, and the toml block
  gains that table, commented optional.
- **`P`** — the template's models line (`P:192`) gains ` · build-moderate <model> <effort>` after the `cut` part; the parts
  paragraph (`P:203-205`) names `build-moderate` among the optional parts and among those taking no host: it builds the
  phases the cut rates `moderate`.

### D7

The decision, added to `docs/decisions.md`'s *The check loop and the release* group, its id one above the highest there at
the build's `HEAD`, and named in the map's list for that group:

```markdown
### D<n> · A build runs a fresh worker per phase

**Under `mf-ship`, the build station spawns `mf-build` once per unticked phase, `phase=<N>`, and once for the close,
`phase=close`: simplify, the metrics and `build.done`. A phase spawn passes only on its phase ticked at `HEAD` on a clean
tree, so none runs twice without an amend between. Phases hand over through `.minions/changes/<id>/build-notes.md`, of
which the conductor keeps 40 lines a phase. The cut rates each phase `moderate` or `hard`; a moderate one runs on
`[build.moderate]` when the models file names it.**

- **Why:** one session carried every phase's reads to its end, 547k of context at 0097's last phase; a fresh worker per
  phase simulated −$4.3 on 0097 and +$0.2 on 0096.
- **Accepts:** each phase re-reads its base · a note the conductor cuts at 40 lines.
- **Rejected:** a per-phase worker only on big changes — one behaviour is simpler · a tracked notes file — D6 keeps the
  record to four artifacts · a host per phase.
```

- **D65** — its bold text's "one model a change, and one build session" → "one `[build]` model a change"; its *Rejected* drops "a build session per phase, which needs a
  guard against re-spawning without end · a model per phase".
- **D64** — *Accepts*' "the build keeps one model a change" → "the build's model is `[build]`'s, a moderate phase's
  `[build.moderate]`'s".
- **D57** — the file list gains `build-notes.md` after `build.{done,halt,closing,discarded.patch}`.
- **D13** — "The build closes with a simplify pass" → "The build closes with a simplify pass, its own worker under
  `mf-ship`,".
- **`THREAT_MODEL.md`** — the *Entry points* bullet on findings files, status logs and worker output gains:
  "`build-notes.md`, which the next phase reads as evidence and the conductor trims through a descriptor that follows no
  link."
- **`skills/mf-ship/SKILL.md`'s flow** — 0099 rewrites its line 22 to read "build, stacked on it": that → "build, stacked on
  it, a worker a phase, then its close".
- **The spec** — [the delta](specs/sdd/spec.md); the release folds it.

## Evidence

What [D7](#d7)'s why and [the Tests](#tests) rest on.

| measure | value | source |
|---|---|---|
| 0097's build: turns · context at start · max | 206 · 28.6k · 547k | the efficiency ledger, read at the plan (brief *Facts*) |
| fresh worker per phase, simulated: 0097 · 0096 | −$4.3 · +$0.2 | the same |
| `def test_` lines in `tests/` at the cut | 278 | `git grep -c "^def test_" HEAD -- tests/`, its counts summed |
| of them in `tests/test_conduct.py` · `tests/test_brief_check.py` | 141 · 3 | the same command |

## Tests

`test_a_build_runs_a_worker_per_phase` and `test_a_halt_in_a_phase_resumes_there` are new in `T`: no test reaches a
multi-phase build. Every other step extends a test that reaches its state (`T2`), at the fake host's layer, the lowest that
holds a run (`T1`), or the unit layer for `_models` and `brief_check.py`. No end-to-end test: the repo has no browser layer.

| test | gains |
|---|---|
| `test_a_build_runs_a_worker_per_phase` (new, `T`) | `0001-todo` with phases `1 — One · moderate`, `2 — Two · hard`, `3 — Three`; `[build]` `claude-opus-5-5` and `[build.moderate]` `claude-sonnet-5-5` `high`; mode `notes-0001-todo`. The raw `FAKE_CALLS` lines are `build 0001-todo with phase=1`, `… phase=2`, `… phase=3`, `… phase=close`, then converge and release; the run log's spawn lines show `claude-sonnet-5-5` for the first and `claude-opus-5-5` for the others; `build-notes.md` holds 40 lines of each section and a `notes — phase 1: kept 40 of 50 lines` event. A second root with no `[build.moderate]` spawns every build on `claude-opus-5-5`. A third root with a link planted at `build-notes.md` halts `0001-todo` naming `build-notes.md is a link`, with no build spawn; a fourth, mode `notes-link-0001-todo`, halts it the same after its `phase=1` spawn ([D1](#d1), [D3](#d3), [D5](#d5)) |
| `test_a_halt_in_a_phase_resumes_there` (new, `T`) | phases 1 and 2; modes `halt-phase-2`, `rescue-fix`: the raw calls are `phase=1`, `phase=2`, the rescue, `phase=2`, `phase=close`. A second root, mode `idle-phase-1` alone: the raw calls hold one `phase=1` spawn, and the run log holds `build check fail — phase 1 unticked` ([D2](#d2)) |
| `test_an_amend_past_the_judged_head_gets_one_round` (`T`) | its added-phase step's `_calls` list reads `probe`, `build 0001-todo`, `build 0001-todo with phase=close`, `converge 0001-todo`, `release 0001-todo` ([D1](#d1)'s late phase) |
| `test_rescue_skip_runs_none` (`T`, its `_models` steps) | `[build]` `executor = "codex"` and `[build.moderate]` `model = "m"` → `_models(minions, "0001-todo", "build.moderate", "claude")` is `("codex", "m", None)`; a `[build.moderate]` naming `executor = "codex"` raises `Stop` naming `build.moderate names an executor`; one with `model = "a;b"` raises `Stop` naming `'a;b' is not a model or effort` ([D5](#d5)) |
| `test_a_stacked_dependent_resets_and_merges_back` (`T`, 0099's) | a `build-notes.md` stands in the dependent's change folder before the reset: after it, the file is gone ([D3](#d3)) |
| `test_each_check_passes_only_on_disk_evidence` (`T`) | `check(root, "build", version, phase="1")` with phase 1 ticked and an untracked file in the tree returns `the tree is not clean` ([D2](#d2)) |
| `test_a_station_runs_on_its_executor` (`T`) | its exact `started` list gains a second `("build", "claude")` after the first: the close ([D1](#d1)) |
| `test_a_hard_brief_is_ready_for_the_cut` (`TB`) | a step whose models line ends ` · build-moderate claude-sonnet-5-5 high · conformance claude-opus-5-5 high`, ready ([D6](#d6)) |
| `test_a_brief_out_of_shape_halts` (`TB`) | `build-moderate` after `conformance`, and `build-moderate claude/claude-sonnet-5-5 high`, each halt naming the item; the pinned `MODELS` text in its item-3 and items-5-to-8 expectations (`TB:186-188`, `TB:212-214`) reads [D6](#d6)'s new wording |
| `test_run_halts_on_a_human_phase` (`T`) | the `stops` step: phase 1 built, the halt reads `human — phase 2 — Ship **HUMAN**`, no rescue ([D2](#d2)) |
| `test_a_codex_worker_starts_on_mf_settings_alone` (`T`) | the build prompt it pins gains ` with phase=1` ([D1](#d1)) |

**The fake host** (`F`) — a build prompt's `phase=<N>` ticks phase `N`'s `## Progress` line and its `N.M` boxes in one
commit; mode `notes-<id>` then appends a `## <N> — <Title>` line and 49 more to `build-notes.md`, and `notes-link-<id>`
replaces that file with a link to a file beside it; `phase=close` writes
`build.done`, and `dies-simplify` exits 1 there; `halt-<id>` halts any phase spawn, `halt-phase-<N>` phase `N`'s alone, each
unless amended; `idle-phase-<N>` exits 0 with nothing done on phase `N`; `deny` prints its blocks on a phase spawn alone, so
a report's denials read once. A build prompt with no `phase=` keeps today's behaviour. `_calls` (`T:228`) drops each
` with phase=<digits>` clause, so a test reads one `build <id>` line per phase spawn, and the close as
`build <id> with phase=close`: each exact `_calls` list the run turns red gains that close line after its version's last
phase spawn, and a run that resumes at the close — the second run of `test_a_build_dead_in_simplify_resumes_at_it` — reads
`build <id> with phase=close` in place of its build line; nothing else changes. The new tests read the file raw.

**Guards.** `_check_phase`'s guard is held by `idle-phase-1`'s step, its twin the same step's halt line (`W5`, `T6`). No test
is deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- **Each phase re-reads its base** → about 100k a spawn; the ledger judges it over the next versions (brief T20).
- **A note cut at 40 lines loses what the next phase needed** → the next phase reads `tasks.md`, design and `git log`, as a
  fresh session always could; the log names the cut.
- **A worker-written note steers the next phase** → it is read as evidence, as every file a worker wrote; the class is the
  threat model's accepted *worker steering* one.
- **A moderate model halts more** → one models line reverts it (brief T22); the rescue answers a plan halt as for any model.
- **0099 is mid-build** → its names may move; the build finds `reset_stack` and the reset by 0099's archived design, and
  halts on a contradiction.

## Verdict

Ready to build.
