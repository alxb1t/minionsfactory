# Lighter converge — design

Converge's workers get models of their own, a reading set cut to what the change cites, a fixer by grade and a security verify
only where security can be reached. Verdict at the end: ready to build.

## Context

Read at `a2f9428` (v0.71.1). The brief's `At` commit is `bb4cf51`; every fact citing `skills/mf-converge/SKILL.md`,
`skills/mf-ship/scripts/conduct.py`, `openspec/specs/sdd/spec.md` or `THREAT_MODEL.md` was re-read, the rest stand. `S` is
`skills/mf-converge/SKILL.md`, `C` is `skills/mf-ship/scripts/conduct.py`, `T` is `tests/test_conduct.py`. This change builds
`after: [0092-amend-round]`, which rewrites `S`'s resume and catch-up, `docs/principles.md`'s *Nothing reads as clean by being
absent* and `THREAT_MODEL.md`'s *Out of scope*: the build reads those by section, never by line.

| measure | value | command |
|---|---|---|
| the worker reading set | 15,397 words | `uv run --script scripts/metrics/reading_set.py worker` |
| `docs/decisions.md` | 7,269 words | `wc -w docs/decisions.md` |
| the decisions index, its `### D` lines | 538 words | `grep '^### D' docs/decisions.md \| wc -w` |
| the worker set with the index | 8,666 words | 15,397 − 7,269 + 538 |
| tests at the cut | 243 | `git grep -c '^def test_' -- tests/`, summed |

- **F1. Workers follow the conductor.** `S`'s *The workers* (`S:116-129`) gives a worker's call no model; D11
  ([decisions](../../../docs/decisions.md#d11--every-station-runs-mfs-own-method)) says workers follow the host. A Sonnet
  conductor alone would make every checker Sonnet.
- **F2. The models file.** `_models_file`, `_table` and `_models` (`C:2015-2062`) read a station's `executor`, `model` and
  `effort`; nothing checks a value's form, and a sub-table such as `[converge.review]` nests inside `[converge]` and is ignored.
  `read_plan` (`C:3716-3741`) reads each of `PLANNED` (`C:93`) once into `self.plan`; `planned_models` (`C:3252-3262`) halts a
  change during the run; a rejoin compares every `PLANNED` station (`C:3947-3953`).
- **F3. The prompt.** `PROMPTS["converge"]` is `"Run the mf-converge skill for change {change}{grant}."` (`C:181`), formatted in
  `Run.advance` (`C:3370`). `T:7324-7326` formats it with `change` and `grant` alone.
- **F4. The reading set.** `S`'s Step 3 (`S:290-295`) hands every worker `docs/decisions.md` and "the living specs the delta
  touches"; `skills/mf-converge/references/generic-review.md:12-16` lists the same packet. `AGENTS.md:14-18`, D48 ("converge
  hands both to every worker") and D49 ("from a packet given up front") say what a worker reads.
- **F5. The tools at hand.** `integrate.py`'s `_requirements` and `_requirement` (`skills/mf-integrate/scripts/integrate.py:608-629`)
  read a delta's titles and a living block; `gate_check.py`'s `TITLED` and `PLANNED` (`skills/mf-converge/scripts/gate_check.py:51-52`)
  read a decision heading and a plan's titled citation, copied there from `integrate.py`.
- **F6. The fixer.** Step 6 (`S:329-367`) dispatches one fresh worker for every open blocking card, or Step 8's picked cards;
  `open_blocking` and each card's grade say which block (`skills/mf-converge/references/worker.md:38`, `:52-55`).
- **F7. Security verify.** Step 7 (`S:369-376`) dispatches both checkers. `mf-release` halts unless both files' `head:` is
  `HEAD` (`skills/mf-release/SKILL.md:132-134`); `conduct.py`'s `_unjudged` (`C:910-924`) reads the same. The one clean no
  checker writes is by recomputation (`docs/principles.md:62-65`). `THREAT_MODEL.md` names its entry points in prose (`:47-69`),
  and no script decides a verify.
- **F8. The cut's template.** `skills/mf-cut-change/SKILL.md:365-387`: converge runs "in the build's model", and the TOML
  template holds `[build]`, `[converge]` and `[release]`.

## Goals / Non-Goals

**Goals:** the converge prompt names each worker's model; a worker's decisions are what the change cites; a fix that reaches no
surface costs no security worker; `converge-worker-reading-set` under 10,500.

**Non-Goals:** the conductor's own reading set; a security skip in a catch-up run, its fix round included; the build's model,
which stays one a change (`0093-lighter-build-cut`); per-worker models on Codex.

- **C9, decided by the cutter.** The second plan review asked whether a catch-up run's one fix round skips the security verify.
  It does not: that run counts one judge and one fix round, and `0092-amend-round`'s `· amend` run is unbuilt at this cut, so the
  narrower skip is the safe reading of C5.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | `[converge.review]`, `[converge.security]`, `[converge.fix]` are planned stations of `conduct.py`, read once and passed in the converge prompt | C1 | the skill reading the models file (0085·S2) |
| [D2](#d2) | Converge puts each on its worker's call, never reads the models file, and logs each worker's model | C1 | a model by alias in the models file |
| [D3](#d3) | A fixer sent any blocking card runs on review's model; otherwise on the fixer's | C2, C4 | a fourth table |
| [D4](#d4) | The cut writes the defaults as tiers, mapped to the offered models | C2 | model names in the skill |
| [D5](#d5) | `bundle.py` writes `bundle.md` at each freeze | C3 | a citation by bare `D<n>` |
| [D6](#d6) | Workers read the bundle in place of the decisions file and the living spec | C3 | the bundle replacing the plan |
| [D7](#d7) | `AGENTS.md`, D48 and D49 say what a worker reads | C3 | — |
| [D8](#d8) | `surfaces.py` decides a security verify; a fix reaching no surface takes its head by rule | C5 | the conductor's judgment |
| [D9](#d9) | D64; D11 and D41 amended | C7 | — |
| [D10](#d10) | The worker reading set counts the decisions index; watch 10,500 | C6 | — |
| [D11](#d11) | `README.md` says what converge spends | C8 | — |

### D1

The worker tables are planned as stations are, so the read-once guard, the rejoin compare and the halt on a change hold them
with no new code path.

- `C` gains `WORKERS = ("converge.review", "converge.security", "converge.fix")`, and `PLANNED` gains `*WORKERS` at its end,
  keeping every station it holds after the merge in — `(*STATIONS, "rescue", *WORKERS)` at this base — its comment naming this
  design. It gains `TOKEN = re.compile(r"[A-Za-z0-9._-]+")`.
- `_table` walks a dotted name: `"converge.review"` is the `review` table inside `[converge]`.
- `_models`, for a station in `WORKERS`: an `executor` key halts,
  `conduct: halt — changes/<change>/models.toml: converge.review names an executor`; a string `model` or `effort` that `TOKEN`
  does not match whole halts, `conduct: halt — changes/<change>/models.toml: converge.fix 'x y' is not a model or effort`. It
  returns converge's executor, the model and the effort, and runs no Codex check: a worker on Codex is given none.
- `_worker_clause(station, models)` returns `""` when the executor is `codex` or the table names neither model nor effort, else
  `f" and {role}={model or 'default'}/{effort or 'default'}"`, `role` the part after the dot.
- `PROMPTS["converge"]` becomes `"Run the mf-converge skill for change {change}{workers}{grant}."`. In `Run.advance`, before the
  format, `workers` joins `_worker_clause(station, self.planned_models(version.change, station))` over `WORKERS` for converge,
  and is `""` for every other stage; the format passes `workers=`. The grant clause stays last, so the delta's *A granted round*
  holds.
- `read_plan`'s docstring names the worker tables and this design.

### D2

`S`'s *The workers* gains a **Worker models** paragraph: `review=`, `security=` and `fix=`, each `<model>/<effort>` with
`default` for none, name each worker's model; `mf-ship` passes them from the models file, and a person may pass them by hand.
Put each on its worker's call — on Claude Code the Agent tool's `model` is the family the name holds, `claude-opus-5-5` →
`opus`, and its `effort` the effort; `default` passes none. A role given none, and every worker on a host whose call takes no
model, Codex among them, runs on the conductor's model; the conductor never reads the models file, since a worker can write it.

The status log's `verdicts` row reads: "the executor you run on; the model and effort the role's worker was given, `default`
where none". The row no longer reads `[converge]`, which is the conductor's.

### D3

Step 6's dispatch line becomes: dispatch a **fresh worker**, on `review=`'s model when any card it is sent is blocking, else on
`fix=`'s. Review's table names the strongest tier, so a blocker gets it, and the brief's three tables stay three. A pickup
round sends non-blocking cards alone; a granted round sends blockers.

### D4

`skills/mf-cut-change/SKILL.md`'s *Suggesting models*:

- The **Converge** bullet's "means run it, in the build's model" → "means run it: the conductor, `[converge]`, on the mid
  tier · medium, review and security on the strongest tier · high, and the fixer on the mid tier · high".
- After "write exactly those: the person chose them at the plan's close.": "The brief names no worker table: write
  `[converge.review]`, `[converge.security]` and `[converge.fix]` from the Converge bullet."
- The TOML template gains, after `[converge]`'s lines and before `[release]`:

```toml
[converge.review]
model = "<offered model>"
effort = "<effort>"
[converge.security]
model = "<offered model>"
effort = "<effort>"
[converge.fix]
model = "<offered model>"
effort = "<effort>"
```

Tiers keep D41: on Claude Code they map to Opus 5.5 and Sonnet 5.5, the brief's C2.

### D5

`skills/mf-converge/scripts/bundle.py`, a `uv` script, run from the repository root:
`bundle.py <change-id> <bundle.md>`. It prints `bundle: <n> decisions cited · <m> requirements` and exits 0, or prints
`bundle: cannot bundle — <why>` and exits 2, writing nothing.

- **Cited decisions.** It reads `openspec/changes/<change-id>/`'s `proposal.md`, `design.md`, `tasks.md` and each
  `specs/**/spec.md`; a missing proposal, design or tasks exits 2. A repo decision is cited by a `decisions.md#d<n>` link, or by
  `D<n> · <title>` where the cited title and that decision's heading title, each stripped of ` .,;:`, match when one starts with
  the other — `gate_check.py`'s `PLANNED`, `TITLED` and `_planned`'s rule, copied with a comment naming their source. A bare `D3`, a design's own id, cites nothing. Each cited decision goes in whole, from its
  `### D<n> · ` heading to the next `### ` or `## ` heading.
- **The index.** Each `### D` heading of `docs/decisions.md`, in file order, as `- D<n> · <title>`. A file with no `### D`
  heading goes in whole; no `docs/decisions.md` writes `No docs/decisions.md.`
- **Requirements.** For each delta file, the titles under `## MODIFIED Requirements` and `## REMOVED Requirements`, each block
  read from `openspec/specs/<capability>/spec.md` — `integrate.py`'s `_requirements` and `_requirement`, copied with a comment. A
  title the living spec lacks writes ``- `<title>` — not in the living spec``.
- **The file.** `# <change-id> — bundle`, a line saying what it replaces, then `## Decisions the change cites`,
  `## Every decision` and `## Requirements the delta modifies or removes`, each `None.` when empty. It writes through a staged
  `.tmp` with `O_NOFOLLOW`, as `stamp.py`'s `write` does; a bundle path that is a link exits 2, `<path> is a link`.
- `tests/test_skills.py`'s `_METRICS_SCRIPTS` gains `("mf-converge", "scripts/bundle.py")`.

### D6

- `S`'s Step 2 gains, after the patch: **Write the bundle** —
  `uv run --script <this package>/scripts/bundle.py <change-id> .minions/changes/<change-id>/bundle.md`; exit 2, or `uv`
  missing → **halt**, naming what it printed. Step 6's re-freeze rewrites it the same way, so the catch-up's freeze does too.
- Step 3's context bullet drops `docs/decisions.md` and "with the living specs the delta touches"; a new bullet hands
  `.minions/changes/<change-id>/bundle.md`, in place of `docs/decisions.md` and the living specs: the decisions the change cites,
  in full, an index of all, and the living requirements the delta modifies or removes. Other architecture documents —
  `ARCHITECTURE.md`, `docs/adr/*.md` — and the threat model stay whole.
- `generic-review.md`'s packet says the same; its **Spec** section reads "against the delta and the bundle's living
  requirements", and **Architecture** "against the bundle's decisions, and any decision the index names that the diff reaches,
  opened in `docs/decisions.md`". Security's packet is review's (`generic-security.md:10-11`), so it follows.
- The plan stays whole in the packet: `0092-amend-round` keeps the full plan in review's reading set.

### D7

- `AGENTS.md`, after the threat-model line: "**A converge worker reads, of the decisions, those its change cites, in full, and
  an index of all — its `bundle.md` — in place of the whole page.**"
- D48: "and converge hands both to every worker" → "and converge hands every worker the threat model and its bundle: of the
  decisions, those the change cites, in full, and an index of all".
- D49: "from a packet given up front" → "from a packet given up front, its decisions and living requirements in a bundle of what
  the change cites".

### D8

`skills/mf-converge/scripts/surfaces.py`, a `uv` script, run from the repository root:
`surfaces.py <security.md> <from> <to>`.

- Exit 0, `surfaces: no surface`, when the security file's frontmatter says `verdict: clean`, no card's `**Status:**` is `open`,
  `fixed` or `wontfix`, `THREAT_MODEL.md`'s `## Surfaces` lists a glob, and no path of
  `git diff --name-only --no-renames <from> <to>` matches one under `fnmatch.fnmatchcase`, whose `*` crosses `/`.
- Exit 1, `surfaces: verify — <reason>`, the first that holds: `security.md is not clean`; `security card <id> is <status>`;
  `THREAT_MODEL.md lists no surface`; `<path> matches <glob>`. A `wontfix` counts with `fixed`: the fixer's claim the checker
  has not judged, or an amend card's, which stays `wontfix` once judged and halts at Step 9, so security keeps running.
- Exit 2, `surfaces: cannot read — <why>`: a missing security file, or a `git diff` that fails.
- `tests/test_skills.py`'s `_METRICS_SCRIPTS` gains `("mf-converge", "scripts/surfaces.py")`.

`S`'s Step 7, between `verify` and the dispatch: after a Step 6 commit, run
`uv run --script <this package>/scripts/surfaces.py .minions/changes/<change-id>/security.md <previous head> <new head>`, the
re-freeze's range. Exit 0 → in the security file set `head:` to `HEAD`, `round:` to this round, `reviewed:` to today,
`mode: by-rule` and `workers: 0`, keeping `verdict: clean` and `open_blocking: 0`; add
`- <previous head>..<new head>: no surface` under a `## By rule` section above its `## Resolution log`; append
`<date> · round N · by rule: no surface` to the log; write `by rule` to the status log, `round N · by rule — no surface`; and
dispatch review alone. Step 5 reads that file for `verdict: clean` and its `head:` alone, with no `verdicts` line. Exit 1 →
both. Exit 2, or `uv` missing → **halt**, naming what it printed. A catch-up run, its fix round and an `· amend` run's
included, and a fixer that committed nothing, dispatch both: C9, decided by the cutter.

- The status log's `by rule` row is written in "`### By rule`, Step 7", its detail gaining "or `no surface`". The resume table's
  `by rule` row → "a catch-up run → Step 9; else Step 7's review dispatch". *Never*'s findings-file line names Step 7's security
  head beside By rule's write.
- `THREAT_MODEL.md` gains `## Surfaces` between *Entry points* and *Out of scope*: one answer-first line naming `surfaces.py`
  and `fnmatch`, then one `` - `<glob>` — <why> `` line each for `skills/*/scripts/*`, `scripts/*`,
  `skills/mf-bootstrap/templates/*`, `skills/mf-ship/SKILL.md`, `skills/mf-release/SKILL.md`,
  `skills/mf-converge/references/generic-security.md`, `Makefile`, `.betterleaks.toml`, `.gitignore`, `pyproject.toml`,
  `uv.lock`, `.github/*`, `AGENTS.md` and `THREAT_MODEL.md`. *Out of scope*'s worker-steering bullet gains, at its end: "So is
  the security head by rule: it reads the security file's cards, which a worker writes, so a forged Status skips one verify."
- `skills/mf-bootstrap/templates/THREAT_MODEL.md.tmpl` gains `## Surfaces` before `## Out of scope`: "Not written yet: the path
  globs a fix reaches security through, one `` - `<glob>` — why `` line each; with none, every fix gets a security verify."
- `docs/principles.md`'s *Nothing reads as clean by being absent* gains, after the sentence naming `integrate.py replay`: "So is
  a security head over a fix that touches no surface the threat model lists, with no security card awaiting its checker:
  `surfaces.py` recomputes it." Its *Held by* gains `tests/test_surfaces.py::test_a_fix_that_reaches_no_surface_is_by_rule`.

### D9

`docs/decisions.md` gains, in *The check loop and the release* after D40:

```
### D64 · Converge spends where judgment is

**Converge's conductor runs on the mid tier · medium, its review and security workers on the strongest tier · high, and its
fixer on the mid tier · high, on review's model when a card it is sent blocks: the models file's `[converge]`,
`[converge.review]`, `[converge.security]` and `[converge.fix]`, which `conduct.py` reads once and passes in the converge
prompt. Each worker reads `bundle.md` — the decisions the change cites, in full, an index of all, and the living requirements
the delta modifies or removes — in place of the decisions file and the living spec. A fix that touches no `## Surfaces` path of
`THREAT_MODEL.md`, with no security card awaiting its checker, takes its security head by recomputation.**

- **Why:** converge was most of a run's spend, its conductor judges nothing, and the decisions file was 47% of a worker's
  reading set.
- **Accepts:** on Codex every worker runs on the conductor's model; a decision the change does not cite is read by its index
  line alone; the build keeps one model a change.
- **Rejected:** a mid-tier conductor alone — every worker follows it · the skill reading the models file — a worker can write
  it · a security verify skipped by the conductor's judgment.
```

- The map's check-loop list gains `D64`.
- D11's last bold sentence → "Workers follow the host, or the models file's `executor`; converge's take their model and effort
  from its worker tables ([D64](#d64--converge-spends-where-judgment-is))."
- D41's "writes it to `.minions/changes/<change-id>/models.toml`, never into the change" → "writes it to
  `.minions/changes/<change-id>/models.toml`, converge's worker tables on [D64](#d64--converge-spends-where-judgment-is)'s tiers
  among it, never into the change". Its tail stays: `0093-lighter-build-cut` appends a bullet there.

### D10

`scripts/metrics/reading_set.py`'s `worker` set names `INDEX`, `"docs/decisions.md · index"`, in place of
`docs/decisions.md`; `words` counts, for `INDEX`, the `### D` lines of `docs/decisions.md`, or the whole file when it holds
none. The docstring's why line gains this design. `metrics/catalogue.toml`'s `converge-worker-reading-set` gains
`watch = 10500` after `better = "lower"`.

### D11

`README.md`'s *Execution* gains, after "need no remote review service.": "Converge's conductor judges nothing and runs on the mid
tier; review and security run on the strongest, each reading a bundle of what the change cites; the fixer moves up a tier only
for a blocking card, and a fix that reaches no surface in `THREAT_MODEL.md` skips the security verify
([D64](docs/decisions.md#d64--converge-spends-where-judgment-is))."

## Tests

243 tests at the cut (`git grep -c '^def test_' -- tests/`, summed). Added: 5 unit tests, 4 of them in 2 new files, and 1
`slow` integration test in `T`. No browser layer exists; no engine runs.

- `test_a_worker_clause_names_its_model_and_effort` (new, `T`) — `_worker_clause` gives `" and review=claude-opus-5-5/high"`
  for `("converge.review", ("claude", "claude-opus-5-5", "high"))`, `" and fix=claude-sonnet-5-5/default"` for an absent
  effort, `""` on `codex` and `""` for neither. `_models` on a `tmp_path` models file reads `[converge.review]` with converge's
  executor, and raises `Stop` with [D1](#d1)'s line on a worker table naming an `executor` and on `model = "x y"`.

- `tests/test_bundle.py` (new, loaded with `importlib` as `tests/test_stamp.py` loads its script):
  - `test_a_bundle_holds_what_the_change_cites` — a tree whose `docs/decisions.md` holds D1, D2 and D48 with bodies, a change
    whose design links `decisions.md#d48--x`, cites `D2 · <D2's title>` and names its own `D1` and `[D1](#d1)`, and a delta that
    modifies requirement A and removes B of a living spec holding A, B and C: the bundle holds D48's and D2's bodies and not D1's,
    an index of D1, D2 and D48, and A's and B's blocks and not C's. Then a decisions file with no heading goes in whole; no
    `docs/decisions.md` writes `No docs/decisions.md.`; a delta title the living spec lacks writes its `not in the living spec`
    line; and a change citing nothing, with no delta, writes `None.` under each empty section.
  - `test_a_bundle_that_cannot_be_written_is_refused` — a missing change folder, and a bundle path that is a link: each exits 2
    with its `bundle: cannot bundle — …` line, and the link's target is unchanged.
- `tests/test_surfaces.py` (new, a `git` repository in `tmp_path`):
  - `test_a_fix_that_reaches_no_surface_is_by_rule` — `## Surfaces` lists `skills/*/scripts/*`; a fix touching `docs/a.md`, the
    security file clean with a `verified` card: exit 0, `surfaces: no surface`.
  - `test_a_fix_that_reaches_security_is_verified` — the fix touching `skills/x/scripts/y.py`; a card `fixed`; a `wontfix`;
    `verdict: changes-requested`; no `## Surfaces`: each exits 1 with its reason. A revision git cannot read, and a missing
    security file, each exit 2.
- A line of `bundle.py` or `surfaces.py` these cases leave uncovered gets a step in one of its phase's named tests, never a new
  test: the gate holds the changed lines at 100%.
- `test_a_fix_reaching_no_surface_takes_security_by_rule` (new, `T`, `slow`) — a primary whose `main` holds a `THREAT_MODEL.md`
  listing `0001-todo.txt`; `tests/fake_worker.py`'s new converge mode `fix-surfaces` writes both findings files at the head,
  commits a fix at `FAKE_FIX`, runs `surfaces.py` over it, and writes review at the new head and security at the new head with
  `mode: by-rule` on exit 0, `mode: parallel` on exit 1. With `FAKE_FIX=notes.txt` the version releases with security
  `mode: by-rule`; in a second primary with `FAKE_FIX=0001-todo.txt` it releases with `mode: parallel`. No existing test runs a
  fix round through a run, so this one is new (`T2`), and its commit body says why.

Extended or edited:

| test | gains |
|---|---|
| `test_a_station_runs_on_its_executor` (`T:3128`) | `table` gains `[converge.review]` with `model = "claude-opus-5-5"` and `effort = "high"`; `_models` of `converge.review` is `("codex", "claude-opus-5-5", "high")` and of `converge.fix` `("codex", None, None)`; the spy keeps each prompt, and the Codex converge's holds no ` and review=` |
| `test_the_plan_is_read_once` (`T:5472`) | before the run, the models file holds `[converge.review]` and `[converge.fix]`; the calls assertion (`T:5493`) expects `converge 0001-todo and review=claude and fix=claude`, the fake recording each clause by `\w+=\w+`; a spawned prompt holds ` and review=claude-opus-5-5/high and fix=claude-sonnet-5-5/high.`; before `def domains`, a fresh `Run` reads the plan, a changed `[converge.fix]` model makes `planned_models("0001-todo", "converge.fix")` raise `changed during the run` |
| `test_a_worker_carries_the_allowlist_and_a_denial_is_named` (`T:7020`) | the `PROMPTS["converge"]` format at `T:7324` passes `workers=""`, and a second format with `workers=" and review=a/b"` and `grant=" and grant=yes"` ends `and review=a/b and grant=yes.` |
| `test_reading_sets_count_words` (`tests/test_metric_scripts.py:46`) | the existing step's `six`, no heading, covers the whole-file fallback, `worker` staying 13; then `docs/decisions.md` rewritten `### D1 · six` and `body words`: `shared` 14, `converge` 21, `worker` 16 |
| `test_the_metrics_script_scan_reports_a_missing_script` (`tests/test_skills.py:511`) | `bundle.py`'s and `surfaces.py`'s `not named` lines in each expected list |

No test is deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- A worker forges a security card's Status to `verified`, and a fix skips one verify → the class *Out of scope* accepts, named
  there by [D8](#d8); review still verifies every fix.
- A surface left off the list skips a verify it needed → the list is the threat model's, and security cards an edit to it;
  with no list every fix is verified.
- A cited decision the citation forms miss is read by its index line alone → review may open it in `docs/decisions.md` for
  its architecture angle.
- A host whose worker call takes no model runs every worker on the conductor's, a mid-tier conductor among them → `S` says so,
  and Codex is named.
- `0092-amend-round` edits the same sections of `S`, `docs/principles.md` and `THREAT_MODEL.md` → it merges in before this
  build, and each task names its section.

## Verdict

Ready to build.
