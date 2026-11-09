# Converge switches — design

A person skips converge's conformance, its adversarial, or converge whole, per version, on the models line; a repo's
`AGENTS.md` default pre-fills the line. The grammar, the conductor's reading of the models file, converge's one-role round
and its stub, the release's wording, and the record. Verdict at the end: ready to build.

## Context

Read at `HEAD` `10a84f3`; the brief's sha is `048246b`. Since it, `conduct.py`, `brief_check.py`, `skills/mf-converge/`,
`skills/mf-cut-change/SKILL.md`, `skills/mf-plan/SKILL.md`, `docs/decisions.md`, `THREAT_MODEL.md` and the spec moved (0099,
0102, 0103): every line below is `10a84f3`'s, from the cut's notes, `.minions/changes/0105-converge-switches/cut-notes.md`,
one line per fact with its `path:line`. The brief's facts hold with new line numbers, bar one: the debt card `0101·R6` the brief names for Step 8 does not exist ([C7](#c-rows)).

`C` is `skills/mf-ship/scripts/conduct.py`, `B` `skills/mf-plan/scripts/brief_check.py`, `V` `skills/mf-converge/SKILL.md`, `W`
`skills/mf-converge/references/worker.md`, `R` `skills/mf-release/SKILL.md`, `K` `skills/mf-cut-change/SKILL.md`, `P`
`skills/mf-plan/SKILL.md`, `M` `skills/mf-review-metrics/scripts/review_metrics.py`, `T` `tests/test_conduct.py`, `TB`
`tests/test_brief_check.py`, `F` `tests/fake_worker.py`. See [the proposal](proposal.md) for why.

- **F1. Build to release today.** `stage_of` checks the converge halt, an unfinished run, then `_unjudged`, then integrate and
  release (`C:1450-1466`). `_unjudged` loops `ROLES` (`C:144`) and needs each role's file at `verdict: clean` with `head:` at
  `HEAD` (`C:1225-1239`). `_release_tip` re-checks it at `HEAD~1` (`C:1386`); `_check_converge` needs `done` and it
  (`C:1503-1513`). The spec says "Converge SHALL always run." (`openspec/specs/sdd/spec.md:1230`).
- **F2. A hand skip lives in release.** Precondition 4: no findings file and no diff patch is a stated skip, `converge:
  skipped — no findings files` (`R:122-130`); preconditions 2, 3 and 7 apply "if converge ran" (`R:117-138`). Integrate's
  Ready accepts it (`skills/mf-integrate/SKILL.md:81-82`). D14 (`docs/decisions.md:246-255`). `conduct.py` never takes the
  path: `_unjudged` sends it back to converge.
- **F3. Dead text.** `K` offers `skip, read by hand` and writes `skip = true # mf-ship runs converge anyway`
  (`K:416`, `:426`, `:439`); `conduct.py` reads only `[rescue] skip` (`C:2574-2577`).
- **F4. A role with no worker has a precedent.** Step 7's adversarial head by rule writes `adversarial.md` with `mode:
  by-rule`, `workers: 0`, `verdict: clean` and `head:` at `HEAD` (`V:421-431`); the findings frontmatter is `W:46-52`;
  `review_metrics.py`'s `_workers` reads a by-rule file's `0` as a gap (`M:1054-1061`).
- **F5. The models file.** `_models` reads `executor`, `model` and `effort` of a station's table; a key it does not know parses
  and does nothing (`C:2477-2528`). `read_plan` reads each version's tables once (`C:5291-5321`). The converge prompt is
  `PROMPTS["converge"]` with `_worker_clause` per worker (`C:245`, `:2531-2546`, `:4666-4679`). `named()` and `executors()`
  choose the hosts to probe (`C:5332-5353`). `RunLog.event(who, event, detail)` writes the run log (`C:2418-2441`).
- **F6. The models line.** `models()` splits on ` · `, pops a last `shadow`, takes a part's name only when it has three words,
  and checks `STATIONS` then `PARTS` order (`B:59-65`, `:219-248`). The grammar line is `P:192`.
- **F7. One role in converge's prose.** Step 3 dispatches both (`V:314`); Step 5 writes "its one line" for one checker
  (`V:337`); the fixer runs on adversarial's model for a blocking card (`V:357-358`); Step 8's check "needs adversarial" for its
  cards or a surface (`V:473`); the catch-up applies "when both findings files exist" (`V:214`); the shadow pairs both roles
  (`V:154`). In `C`, `_amendable` needs both files clean (`C:1131-1148`); `_security_blocks` and `_security_held` read a missing
  `adversarial.md` as blocking (`C:2658-2701`), and read a card-less file as not.
- **F8. A repo's per-repo keys.** `conduct.py` reads `**Key:**` lines of the primary's `AGENTS.md` (`C:491-506`); no skill
  does. D56, D58 and D60 reject a per-version switch in `AGENTS.md` (`docs/decisions.md:150`, `:846`, `:894-906`).
- **F9. The floor without converge.** A green `make check` per phase and a green gate at the build's end; integrate gates its
  merge; release gates in its own session and runs `gate_check.py`; conduct's secret scan runs before a push
  (`THREAT_MODEL.md:50-54`). No decision makes review mandatory. D64 rejects an adversarial verify skipped "by the conductor's
  judgment" (`docs/decisions.md:337`), not a person's switch.
- **F10. The threat.** `models.toml` is worker-writable; a planted `skip` disables the check that would catch the worker that
  planted it. The class is "a worker steering the conductor through what it may write" (`THREAT_MODEL.md:153`, in `## Out of
  scope`); `## Surfaces` is at `THREAT_MODEL.md:104`.
- **F11. Debt `0100·S5`.** `WORKER` takes the first role word before `round <N>` anywhere in a description
  (`M:96`, `:915`); `V` never tells the conductor what to write (`.minions/debt.md:668`).

## Goals / Non-Goals

**Goals:** the brief's Acceptance — `brief_check.py` accepts the three `skip` forms and refuses a skip beside `shadow`, beside
the role's models and on both roles; a version whose plan says `converge skip` goes from build to integrate and release with no
converge spawn, the run log naming `converge skipped — plan` and the release `converge: skipped — by plan`; a version with
`adversarial skip` runs conformance alone, writes `adversarial.md` as a `mode: skipped` stub at `HEAD`, its rescue and supervisor
not barred by the stub, and releases naming `adversarial: skipped`; a skipped Codex role is not probed; `mf-plan` pre-fills
`converge skip` from `**Converge:** skip`; the cut warns on an adversarial skip over `## Surfaces`; the spec names `skipped — by
plan`; `make gate` green. Also `0100·S5`.

**Non-Goals:** the switches out of `models.toml`; a hand read or debt for a skipped converge; an automatic floor under an
adversarial skip; a skipped fixer; a corpus case for `conduct.py`'s read of `models.toml` ([C6](#c-rows)).

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | The models line takes `converge skip`, `conformance skip` and `adversarial skip` in place of a part's model and effort; `models.toml` takes `skip = true` under `[converge]` or `[converge.<role>]`; `brief_check.py` refuses each skip beside `shadow`, `converge skip` beside any other converge part, and both roles skipped | G1 | a flag on the command line — the plan is the record · `model = "skip"` — a model word that parses and does nothing · `[converge] roles = [...]` — a second grammar beside `[rescue] skip` |
| [D2](#d2) | `conduct.py` reads the switches with the plan, for its probes and prompt, and from the file at each stage read; `converge skip` sends a built version from build to integrate and release, logging `converge skipped — plan`; a skipped role leaves the probes, the mailbox and the prompt's clauses, and takes `and <role>=skip` | G1, G3 | a `done` status log written by the conductor — it would fake a run · a `diff.patch`-less hand skip left to release alone — `_unjudged` sends it back to converge |
| [D3](#d3) | A skipped checker's findings file is a stub written by `skip_stub.py`: clean, at `HEAD`, `mode: skipped`, `workers: 0`; converge dispatches the other role alone and rewrites the stub at each freeze, catch-up and before `done` | G2 | `_unjudged` and `_amendable` learning a skipped role — each reader changed and kept apart · by hand, as the by-rule head is — written every round, it must read the same each time |
| [D4](#d4) | The release states `converge: skipped — by plan` for a skipped converge, and `<role>: skipped` for a stub; the rest of its preconditions stand | G2, G3 | a new release parameter — it reads the models file and the stubs already on disk |
| [D5](#d5) | An `AGENTS.md` line `**Converge:** skip`, `conformance skip` or `adversarial skip` pre-fills the models line in `mf-plan` and the cut; `conduct.py` never reads it; the cut warns when an adversarial skip's tasks name a `## Surfaces` file | G4, G6 | `conduct.py` reading it per version — D56, D58 and D60 reject an `AGENTS.md` switch per version · an automatic floor — the person's call, made visible |
| [D6](#d6) | `V` names each Agent call's description `<role> round <N>`, `fix round <N>`, `verify <role> round <N>`; `WORKER` anchors at the description's start | debt `0100·S5` | matching anywhere, as now — a fixer described "Adversarial fix round 1" is booked to adversarial |
| [D7](#d7) | The record: a new decision, D75; D14 and the spec requirement amended; the threat model names a planted skip | G3, G5, G7 | leaving "Converge SHALL always run." standing |

### C rows

The cutter's readings of the brief's decisions, each named where it is built:

| id | reading | because |
|---|---|---|
| C1 | `converge skip` beside a conformance, adversarial, fix or shadow part is refused, as a role's skip is beside its own models | G1 refuses a skip "beside that role's models or `shadow`"; `converge skip` skips every part |
| C2 | The stub is written by `skip_stub.py`, its role read from the path's file name | the by-rule head is a hand edit, written once per fix; a stub is written every round and catch-up, and `conduct.py` and the release parse it |
| C3 | The release reads `.minions/changes/<change-id>/models.toml` for the words `by plan` alone | the files on disk already say skipped; only the reason is the plan's |
| C4 | The cut's default applies when its source names no models; a brief's models line always names `converge`, so an unattended cut writes the brief's | `brief_check.py` requires the part; the default pre-fills the plan's suggestion |
| C5 | `Run.stage` logs `converge skipped — plan` once per version, when it first reads `integrate` or `release` for it | `stage_of` is a pure read, called again for status and reports |
| C6 | The edit to `WORKER` carries `**CORPUS** `review-metrics``; `conduct.py`'s new read of `models.toml` carries none | no corpus case runs `conduct.py` over run data; the fake hosts hold it |
| C7 | The brief's `0101·R6` is no card: Step 8 opens for the one-role check, and this change pays down no `0101` card | `debt:` lists `0100·S5` alone; `0101·S8`'s fix, `checked — round <N+1>` to Step 7, stands in the resume table (`V:204`) |

### D1

- **`B`'s `models()`** — a part is three words, or two with `skip` last and `converge`, `conformance` or `adversarial` its name;
  `names` takes either. The order check stands. The `for name, model, effort in parts` loop reads three-word parts alone. New
  lines, one per refusal, each `item <n> — …`: `a skip takes no model or effort` for a three-word part whose second word is `skip`;
  `a skip is not beside shadow`; `converge skip takes no conformance, adversarial or fix
  part`; `conformance skip and adversarial skip together: write converge skip`. `MODELS` (`B:67-71`) says `each <model> <effort>,
  or skip for converge, conformance and adversarial`.
- **`P:192`** — the `models:` grammar line gains `converge <model> <effort> | converge skip`, `conformance <host/model> <effort>
  | conformance skip` and `adversarial <host/model> <effort> | adversarial skip`, and a sentence: "`skip` takes no model, no effort and
  no `shadow`; both checkers skipped is `converge skip`."
- **`K:416`, `:426`, `:439`** — the dead `skip, read by hand` and `skip = true # mf-ship runs converge anyway` are replaced:
  the Converge bullet and the suggestion block (`K:416`, `:426`) say a person's `skip` is in the brief's models line, and
  *Suggesting models* writes it as D1's `models.toml` form. The template's `[converge]` line (`K:439`) loses its comment, and a
  new comment line after the `# shadow = true` line reads `# skip = true  # from the brief's converge skip: no model, no worker
  tables`.

### D2

- **`C`'s `_skips(runs, change)`** — returns a `frozenset[str]`: every name of `("converge", *WORKERS)` when `[converge]` says
  `skip = true`; else each of `converge.conformance` and `converge.adversarial` whose table says `skip = true`. Only the value `true`
  skips. A models file that fails to parse returns the empty set: `read_plan` and `take` halt it.
- **`_unjudged`** — returns None at its first line for a version whose `_skips` holds `converge`; `_release_tip` and `_check_converge`
  need no edit.
- **`stage_of`** — a skipped converge omits the converge-halt and unfinished-run branches; `_unjudged` is None; the
  release reason reads `converge skipped by plan; <default> is an ancestor`.
- **`Run`** — `self.skipped: dict[str, frozenset[str]]`, filled in `read_plan` beside `shadowed`; `named()` leaves a skipped name's
  plan entry and a skipped checker's shadow; `self.skip_logged: set[str]`, and `Run.stage` writes `self.log.event(change,
  "converge", "skipped — plan")` once, when `_skips` read from the file holds `converge`, [C5](#c-rows). A skip written after
  the plan was read skips converge through `stage_of` and changes no probe: [G5's](#d7) accepted class.
- **`_worker_clause(station, models, converge, skipped=False)`** — `skipped` returns ` and <role>=skip` before any other clause.
  The converge spawn passes `name in skipped`, and opens the mailbox only for an unskipped checker whose executor differs.
- **`skills/mf-ship/SKILL.md`** — its flow diagram (`:22`, `:26`) and the paragraph opening `Converge runs MF's method` (`:115`) say
  that a version whose models file says `[converge] skip = true` skips converge and its catch-up round.
- **Unchanged:** `_amendable`, `_security_blocks`, `_security_held`, `_check_converge`. A stub is clean at `HEAD` and holds
  no card, so none bars a rescue or supervisor.

Fix note (2026-11-09, R1): `Run.stage` logs the event `converge skipped` with the detail `plan`, so the line reads the spec's `converge skipped — plan`; `EVENT` and `EVENTS` take the two-word event.

### D3

`skills/mf-converge/scripts/skip_stub.py <findings-file> <round>`, a `uv` script, `dependencies = []`:

- **Reads** the role from the file's name, `conformance.md` or `adversarial.md`, in a folder holding no link; `head` from `git rev-parse
  HEAD`, `branch` from `git branch --show-current`, `project` from the name of the directory `git rev-parse --git-common-dir`
  names the parent of, `plan` from the folder's name, `reviewed` from today's date.
- **Writes** the findings frontmatter of `W:46-52`, every key: `type`, `plan`, `project`, `branch`, `head`, `reviewed`, `round`,
  `open_blocking: 0`, `verdict: clean`, `mode: skipped`, `workers: 0`, `model: none`, `executor: none`, `packet: skipped: all`; then
  one line, `Skipped by the plan: no worker judged this round.` No card.
- **Exits** 0 printing `skip_stub: <path> at <short head> · round <round>`; 2 printing `skip_stub: cannot stub — <why>` for a
  path that is a link, or not of the form `…/changes/<change-id>/conformance.md` or `…/adversarial.md` (the file need not exist), a round that is no positive integer, or a directory holding no repository.
- **`V`** — a new section `## A skipped checker` after *Shadow round 1*: the parameter `<role>=skip` dispatches no worker for
  that role; `skip_stub.py` runs for it after Step 2's freeze, Step 6's re-freeze, the catch-up's freeze and its By rule write, and
  before Step 10's `done` when its `head:` is not `HEAD`; the round is the one the freeze judges. Step 3 dispatches each role not
  skipped. Step 5 reads a stub for `verdict: clean` and its `head:` alone, with no `verdicts` line. Step 6's fixer rule reads
  "when adversarial is no mailbox role and not skipped". Step 7 runs no `surfaces.py` when adversarial is skipped, and dispatches the
  role not skipped alone. Step 8 item 5's check needs the role not skipped when the other would be needed, and runs `surfaces.py`
  only when adversarial is not skipped. *By rule* item 3 runs `skip_stub.py` in place of its edit for a skipped role's file. A
  `shadow=yes` beside a skip, or both roles `skip`, halts. *Never*'s findings-file exception names the stub. Step 10's sentences
  name each skipped role.
- **`W:51-52`** — `mode: parallel | sequential | by-rule | skipped`, `workers: … 0 by rule or skipped`.
- **`M`'s `_workers`** — reads `mode: skipped` as it reads `by-rule`: a gap.

Fix note (2026-11-09, S1): `skip_stub.py` also exits 2 on an existing file that is no stub and is not clean or holds a card `open`, `fixed` or `wontfix`, so a skip added after a round never erases its cards.

### D4

- **`R:122-130`** — the first row's line reads `converge: skipped — no findings files`, or `converge: skipped — by plan` when the
  models file says `[converge] skip = true`; a new paragraph after the table: "A findings file whose `mode:` is `skipped` is a
  checker the plan skipped: it is clean at `HEAD` like the other, and the report and the release commit state `<role>: skipped`
  (Step 4.4)." `R:238-243` and `:307` name the same line.
- **`skills/mf-integrate/SKILL.md:81-82`** — Ready names no change: a stub is a clean findings file.

### D5

- **`P`** — the paragraph after the `models:` grammar line that points to the cut's *Suggesting models* (`P:196-202`): "A root `AGENTS.md` line `**Converge:** skip`, `conformance skip` or `adversarial skip`
  pre-fills the suggested line with that part; the person confirms or changes it. Read the line for nothing else."
- **`K`** — *Suggesting models*: the same pre-fill when the source names no models for the change; Step 9's show, and unattended a
  line of `cut-notes.md`, carries `surfaces warning — <path> matches <glob>: adversarial is skipped` for each file a task names that
  a `## Surfaces` glob of `THREAT_MODEL.md` matches, when the change's models skip adversarial or converge. The commit goes on.
- **`C`** reads neither; `GATE_FILES` stands.

### D6

- **`V` Steps 3, 6, 7 and 8** — each Agent call's description: `<role> round <N>` for a checker, `fix round <N>` for the
  fixer, `verify <role> round <N>` for a verify worker; Step 8 item 5's `verify round <N> · pickup` stands.
- **`M:96`** — `WORKER = re.compile(r"^(conformance|adversarial|fix|verify)\b.*?\bround (\d+)\b", re.I)`. A description opening with
  another word reads as a gap.

### D7

- **A new decision, D75**, placed after D74 in `docs/decisions.md`, its heading `### D75 · A person may skip converge, or a checker,
  per version`, its text:

  > **A version's models line may say `converge skip`, `conformance skip` or `adversarial skip`; `models.toml` holds it as `skip =
  > true` under `[converge]` or the checker's table. A skipped converge sends a built version from build to integrate and release,
  > the run log naming `converge skipped — plan` and the release `converge: skipped — by plan`. A skipped checker's findings file
  > is a clean stub at `HEAD`, `mode: skipped`, and the release names it. A repo's `**Converge:**` line in `AGENTS.md` only
  > pre-fills the line in `mf-plan` and the cut; `conduct.py` reads `models.toml` alone.**
  >
  > - **Why:** a proof of concept does not earn converge's tokens, and the hand skip D14 allows lived in release alone: the run
  >   sent such a version back to converge.
  > - **Accepts:** no hand read and no debt for a skipped converge, the gate the only floor · no security reader under an
  >   adversarial skip, the release naming it · a planted `skip` in the worker-writable `models.toml`, in the class *Out of scope*
  >   accepts, as the `decide` switch is.
  > - **Rejected:** a `**Converge:**` switch `conduct.py` reads — D56, D58 and D60 reject an `AGENTS.md` switch per version · a floor
  >   under an adversarial skip · `_unjudged` learning a skipped role.
- **The index** (`docs/decisions.md:13`) — the check-loop group's id list gains `D75` after `D74`.
- **D14** (`docs/decisions.md:246-255`) — the first paragraph gains: "A plan may also skip converge, or one checker, on the models
  line; the release then states `converge: skipped — by plan` or `<role>: skipped`."
- **The spec** — *The ship station…*'s "Converge SHALL always run." is the delta's; the fold at release writes it.
- **`THREAT_MODEL.md`** — in `## Out of scope`, after the worker-steering class: a planted `skip` in `models.toml` skips the
  check that would catch the worker that planted it; accepted, as the `decide` switch is; the fix is moving the switches where
  no worker writes.

## Tests

`tests/test_skip_stub.py` is new: no test reaches a new script. Every other step extends a test that reaches its state (`T2`), at
the unit layer (`T1`) — save the ship test's one extra version, which the fake hosts run. No end-to-end browser test: the repo has
none. Converge's prose is held by review ([D42](../../../docs/decisions.md#d42--skill-prose-is-held-by-review-not-by-phrase-scans)),
as `conduct.py` launches converge as one station and runs no round.

| test | gains |
|---|---|
| `test_a_models_line_naming_a_skip` (new, `TB`) | the lines of the delta's scenario: `converge skip` alone, `conformance skip`, `adversarial skip` ready; each refusal of [D1](#d1) naming its item; `adversarial skip claude-opus-5-5` refused |
| `test_a_worker_clause_names_its_model_and_effort` (`T`) | `clause("converge.adversarial", ("claude", None, None), "claude", True) == " and adversarial=skip"`, a skipped Codex checker too ([D2](#d2)) |
| `test_a_checker_on_another_host_is_planned_and_probed` (`T`) | a table `[converge.conformance]` with `executor = "codex"` and `skip = true`: `named()` is `["claude"]`; `[converge] skip = true` beside the worker tables: `executors()` is `["claude"]`; `_skips` reads `skip = false`, a string `"true"` and a bad file as the empty set ([D2](#d2)) |
| `test_a_ready_version_ships_past_a_slow_one` (`T`) | `0002-marks`'s models file says `[converge]\nskip = true\n`: no `converge 0002-marks` call, its release goes first as before, the run log holds `converge skipped — plan` once for it, and the version is released with no findings file ([D2](#d2)) |
| `test_a_stub_is_written` (new, `tests/test_skip_stub.py`) | a repository under `tmp_path`: each key of [D3](#d3)'s frontmatter, `head` at `HEAD`, the line printed ([D3](#d3)) |
| `test_a_stub_it_cannot_write_exits_2` (new, `tests/test_skip_stub.py`) | a link, a path naming `review.md`, a path `x/conformance.md` outside a `changes/<id>/` folder, a round of `0`, a directory with no repository ([D3](#d3)) |
| `test_a_stub_bars_no_rescue` (new, `T`) | `skip_stub.py` run as a subprocess in the primary writes `adversarial.md`; beside a clean `conformance.md` at `HEAD`, `_unjudged` is None, and `_security_blocks` and `_security_held` are False for a halt naming `R1`; with no `adversarial.md`, True, as before ([D2](#d2), [D3](#d3)) |
| `test_a_version_with_adversarial_skipped_ships_on_a_stub` (new, `T`) | one version whose models file says `[converge.adversarial]\nskip = true\n`; `F`'s converge branch runs `skip_stub.py` for each role its prompt holds `=skip` for and writes the other role clean; the version is released, `adversarial.md` says `mode: skipped`, and the run log holds no `converge skipped` line. Why a new ship test (`T2`): no existing one holds a stub, and `_unjudged` reads it only through the real stage loop |
| `test_review_metrics_books_a_worker_by_its_description` (new, `tests/test_review_metrics.py`) | the delta's two scenarios: `fix round 2 · adversarial cards` is role `fix` round 2; `Security station verify round 2` is no role; a front with `mode: skipped` is a gap through `_workers` ([D6](#d6), [D3](#d3)) |

Every line of `skip_stub.py` and each new line of `conduct.py` is reached by these steps, as the gate's diff coverage needs.

**Guards.** `skip_stub.py`'s link refusal is held by the `test_a_stub_it_cannot_write_exits_2` step; its twin is the same step
run with the refusal removed, in the commit body (`W5`, `T6`). `stage_of`'s skip branch is held by the ship test's extra version;
its twin is the same test with `_skips` returning the empty set, in the commit body. `test_a_stub_bars_no_rescue` is green once
the script stands: it holds that no reader of a findings file changed, so it is no step of the red-before-green rule; its twin is
the same test with `_security_held` reading `mode: skipped` as blocking, in the commit body. No test is deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- **A planted skip** → accepted and recorded ([D7](#d7)); the floor is the gate, which release and integrate re-run.
- **No security reader under an adversarial skip** → the release names it, and the cut warns on `## Surfaces` ([D5](#d5)); nothing
  more, as the person's call is made visible.
- **A stub head left stale** → `_unjudged` then sends the version back to converge, and the next round rewrites it; the
  final rewrite before `done` is the guard.
- **A metrics round for a stub** → `_workers` reads it as a gap; its record stays a row of `clean` with no cards.
- **`WORKER` anchored** → a description in an old log that opened with another word reads as a gap; `make corpus` runs the
  reader over the real logs after the edit.
- **0099 and 0104 move the same files** → the build finds each section by its name, and halts on a contradiction.

## Verdict

Ready to build: one feature, the grammar first and the record last. No step is irreversible — a skip is a line in a plan.
