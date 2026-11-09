# Cut scripts — design

The cut's preconditions, fact placement, reader search, self-check rows and models file become scripts; the cut's LLM writes
the plan and judges the rest. Five scripts or edits, then the record. Verdict at the end: ready to build.

## Context

Read at `HEAD` `ccfa6a1`, the brief's sha: `git diff --name-only ccfa6a1..HEAD --no-renames` prints nothing, so every brief fact
stands and no helper read one ([C1](#c-rows) is the one premise that failed). Lines below are `ccfa6a1`'s, from the cut's notes,
`.minions/changes/0106-cut-scripts/cut-notes.md`. See [the proposal](proposal.md) for why.

`B` is `skills/mf-plan/scripts/brief_check.py`, `C` `skills/mf-ship/scripts/conduct.py`, `K` `skills/mf-cut-change/SKILL.md`,
`P` `skills/mf-plan/SKILL.md`, `T` `tests/test_conduct.py`, `TB` `tests/test_brief_check.py`, `TS` `tests/test_skills.py`.

- **F1. What the cut does by hand.** Step 1 is a list of commands, one turn each; Step 2 reads each fact's moved state by a
  rule (`K:62-135`); Step 3 runs `git grep -nw` per name (`K:146-147`); Step 8 builds a table of every input-contract row
  (`K:195-221`). The last cut's main session was $3.39 of $6.99, its helpers and plan reviews the rest (the efficiency ledger,
  kept outside the repository).
- **F2. The brief's parser.** `B` reads sections through CommonMark; `items()` joins an item's wrapped lines (`B:133-154`);
  `models()` and `fields()` check the models line and the heads (`B:220-309`); `main` has one positional and no flags
  (`B:473-528`). It never reads `## Facts`, and its `At` check already refuses a brief with no `At` line (`B:498-499`).
- **F3. Two copies of one prefix test.** `headed()` ends a section at an HTML block that starts `<h1` or `<h2` (`B:113-114`),
  and `_boundary()` does the same (`C:6982-6988`): `<h12>` and `<h2-widget>` end a section they are no heading of. Card
  `0103·S3` names both. `INLINE_HEADING` already holds the tag boundary `<h[1-6](?:[\s/>]|$)` (`B:52`, `C:96`).
- **F4. The queue and the models file.** `cut()` takes a brief and a slug, reserves an id, writes the entry (`C:7115-7195`); the
  cutter writes `models.toml` after its commit (`K:303-305`; the fake cutter `tests/fake_worker.py:458-460`); `_check_cut`
  needs only that the file stands (`C:794-796`); `_write_in_change` writes a change file through no link (`C:692-704`);
  `CUT_KEYS` is the entry's required keys (`C:94`). Card `0085·S2`: the file is worker-writable.
- **F5. Docstrings over the limit.** Card `0103·R3` names `scripts/corpus.py:5`, `skills/mf-converge/scripts/plan_check.py:5`,
  `headed()` (`B:98`), and `_headed` and `_rows` of `C` (`C:6937`, `C:6991`; the card's `:6326` and `:6380` before 0104 and
  0105 moved them). `C7` allows 3 lines.
- **F6. The scripts' conventions.** Every skill script is a `uv` script with `dependencies = []` save `B` and `C`
  (`CODING_STANDARDS.md:15-17`); scripts load each other by `runpy` (`B:35-41`); script tests load by `importlib` and call
  `main([...])` in a `tmp_path` git repository (`tests/test_verify_check.py:18-50`); `TS` requires each script a skill
  names to exist and be named (`tests/test_skills.py:503-545`).
- **F7. Decision ids.** D75 and D76 stand (`docs/decisions.md:479`, `:821`). The new decision is D77 ([C1](#c-rows)).
- **F8. What the plan check is called.** `plan_check.py` holds the name "plan check"; `K:200` calls `gate_check.py --tasks`
  the same. `TS` lists no pair for the cut's `gate_check.py`.

## Goals / Non-Goals

**Goals:** the brief's acceptance — the new test files pass under `make gate`; `K` names `cut_pre.py`, `facts.py` and
`cut_check.py`; `C` names `--models`; D77 stands; `brief_check.py` refuses a `## Facts` line citing a basename, a bare `:N` or
a legend, and a brief with no `At` line. Also debt `0085·S2`, `0103·S3` and `0103·R3`.

**Non-Goals:** the converge conductor as a script and the evidence step; a hash check after the cut passes; a corpus case
([D8](#d8)); rewriting a brief in the old form ([D1](#d1)); the efficiency ledger's hypothesis H14 — the scripted cut's main
session at $2.40 or less, minus 30% of $3.39, over two cuts, plan reviews apart — which the person records outside the repository.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | `brief_check.py` refuses a `## Facts` item not ending ``(`<path>:<line>[-<line>]`[, `<path>:<line>…`] at `<sha>`)``; `--facts` prints the facts as JSON | Q2, Q4, Q16 | a path of one component with no `./` — a basename the repository cannot tell from a root file · grandfathering the old form |
| [D2](#d2) | `brief_check.py --models <brief> <slug>` prints the item's models file as TOML; it is the only reader of the models line | Q4 | a second parser in `conduct.py` or the cut |
| [D3](#d3) | A tag ends a section only when its name is exactly `h1` or `h2`, in `headed()` and `_boundary()`; the docstrings of card `0103·R3` shrink to 3 lines | Q13 | patching `headed()` alone — the card names both readers |
| [D4](#d4) | `facts.py place <brief>` places each fact: **stands**, **moved**, or **unplaced**; `facts.py readers <name>…` prints Step 3's `git grep -nw` hits; both write the cut's notes | Q3, Q9, Q10, Q18 | a helper per fact · a line-by-line diff reader |
| [D5](#d5) | `cut_pre.py <id> [--unattended] [--after <ids>]` runs every precondition, one line a check | Q6 | halting the unattended cut on the first failure only — one run shows every failed check |
| [D6](#d6) | `cut_check.py <id> [--bump <bump>]` decides the mechanical rows, folds in the checks named below, and prints the judgment rows | Q7, Q8, Q11, Q12 | a script judging `I5`–`I10` — a checker judging deterministic checks stays out ([D66](../../../docs/decisions.md#d66--two-checkers-conformance-and-adversarial)); the reverse holds too |
| [D7](#d7) | `conduct.py cut` writes `models.toml` from `--models` at queue time and keeps the text in the entry; the run writes it again before each cutter; `_check_cut` compares hashes | Q5 | recording the hash alone — a rejoin could not restore the file · reading the brief again at a rejoin — the cutter can edit it ([D62](../../../docs/decisions.md#d62--a-queued-cuts-packages-are-approved-at-the-plan)) |
| [D8](#d8) | No corpus case: `cut_pre.py` lists the names in `.minions/cuts/` and `conduct.py` reads `models.toml`'s bytes; neither parses a run data format | the cut's corpus rule | a case that runs `cut_pre.py` over the real run directory — it halts on a dirty tree, so it proves nothing |
| [D9](#d9) | The record: D77 in `docs/decisions.md`, amending its D40, D41 and [D7](../../../docs/decisions.md#d7--the-cut-writes-to-the-builds-input-contract); the skills call the scripts; `TS` lists them | Q11, Q12, Q17, Q18 | prose only, with no pair in `TS` — a script no skill names is dead |

### C rows

| id | decision | reason |
|---|---|---|
| C1 | the new decision is D77, not D75, and the acceptance names its heading: the brief's Q17 and Acceptance read so by the time of the commit | D75 and D76 stand in `docs/decisions.md`; an id in force is never reused |

### D1

**The citation grammar.** One regular expression, `FACT`, matches the item's end:
``\((`PATH:N(-M)?`(, `PATH:N(-M)?`)*) at `SHA`\)$``.

- `PATH` is components of `[A-Za-z0-9._-]+` joined by `/`, none `.` or `..`, with a `/` or a leading `./`; `N` and `M` are
  digits; `SHA` is 7 to 40 characters of `0-9a-f`.
- A root file is written `./AGENTS.md`: a path of one component is a basename and is refused, `C:4357-4406` and `:49` too.
- An item is the lines of `items()`, so a wrapped fact is one. A line out of grammar prints
  `brief: halt — ## Facts: fact <k> — <text>` and exits 1.
- `--facts` prints `[{"fact": "<text>", "cites": [{"path": "<p>", "start": N, "end": M}], "sha": "<sha>"}]`, a path's `./`
  dropped; no `## Facts` section prints `[]`. The `At` line stays required; the facts take their own sha.

### D2

**The models file.** `--models <brief> <slug>` finds the `## For the cut` item whose head names `<slug>`, and prints, in order:

- `decide = "recommended"` when the head has `decide: recommended`.
- `[build]`, `[build.moderate]`, `[converge]`, `[converge.conformance]`, `[converge.adversarial]`, `[converge.fix]` and
  `[release]`, each with `model` and `effort`, and `executor` when the part's model names a host
  (`codex/gpt-6.1-sol` → `executor = "codex"`, `model = "gpt-6.1-sol"`).
- A `skip` part is `skip = true` alone, and `converge skip` writes no worker table; `shadow` is `shadow = true` under `[converge]`.
- The `cut` part is the cutter's own and is written nowhere.

A line out of shape prints the item's halts and exits 1; no item of that slug exits 2. The shape follows
`.minions/changes/0105-converge-switches/models.toml` and `K`'s *Suggesting models*.

### D3

**The tag boundary.** `BLOCK_HEADING = re.compile(r"<h[12](?:[\s/>]|$)", re.IGNORECASE)`, matched at the start of the block's
lstripped content, replaces `startswith(("<h1", "<h2"))` in `headed()` and in `_boundary()`. Each file defines its own,
beside its `INLINE_HEADING`: `conduct.py` does not load `brief_check.py`.

- `<h2 id="x">` and `<H1/>` still end a section; `<h12>` and `<h2-widget>` do not.
- The docstrings of `headed()`, `_headed`, `_rows`, and the module docstrings of `corpus.py` and `plan_check.py` shrink to 3
  lines each, each keeping its `Why:` citation: cite where the reason lives (`C6`).

### D4

**Placement.** `facts.py place <brief> [--notes <file>]` runs `uv run --script <B> --facts <brief>` in `brief_facts` (the
runner is a module constant a test swaps), then `place_all` places each fact on its own sha, a cite at a time. The placement
tests feed facts straight to `place_all`; one test runs `main` with the runner swapped:

```
sha not 7-40 hex, or no commit        ─▶ unplaced (no git command takes a non-hex sha)
path not in git diff --name-only --no-renames <sha>..HEAD ─▶ stands
else map both ends through the hunks of git diff -U0 --no-renames <sha>..HEAD -- <path>
   a line inside a hunk's old range   ─▶ unplaced
   mapped length differs (an insertion inside the range) ─▶ unplaced
   mapped range == the cited range    ─▶ stands
   else                               ─▶ moved to <path>:<a>-<b>
```

- A fact is `unplaced` when any cite is, else `moved` when any cite moved, else `stands`. A rename or a deletion reads as a
  touched path with every line in a hunk: unplaced.
- One line prints per fact: `<state> · <fact text> · <path:line…>`. The exit is 0 with none unplaced, 1 with one, 2 when the
  brief or git cannot be read.
- With `--notes`, the file is written afresh with the title `# <id> — cut notes`, `<id>` the notes file's folder name, then the
  lines in the notes' form `<fact> — <answer> · <path:line>`.
- `facts.py readers <name>…` prints, per name, each hit of `git grep -nw -e <name> HEAD --` as
  `readers of <name> — <text> · <path>:<line>`, or `readers of <name> — none · HEAD`, and with `--notes` appends them.
- The cut starts a helper only for a fact left unplaced, up to four; a design question is the cut's own read.

Fix note (2026-11-09, S3): `place` takes `--at <rev>`, `HEAD` by default, and planning passes its `<ref>`; the diffs and the printed ranges use that commit.

### D5

**The preconditions.** Each check prints `cut_pre: ok — <check>` or `cut_pre: halt — <check>: <why>`; the exit is 0 with no
halt, 1 with one, 2 when git is missing or the id is not `<digits>-<slug>`. By hand and unattended differ as the skill's Step 1
says:

| check | by hand | unattended |
|---|---|---|
| `agents` | root `AGENTS.md` stands | the same |
| `tree` | on the default branch, `git status --porcelain` prints nothing | in a linked worktree, on branch `<id>`, `HEAD` an ancestor of the default branch, clean |
| `openspec` | `openspec --version` exits 0 | the same |
| `gate` | `make -n gate` exits 0 and prints a command that is not `is up to date` or `Nothing to be done` | the same |
| `reserved` | `.minions/cuts/<id>` does not stand, else the halt `<id> is queued for the cut station: answer it in the brief, then conduct.py rejoin <id>` | it stands |
| `id` | the number is above each id under `openspec/changes/` and `openspec/changes/archive/` on the default branch and on each unmerged `[0-9]*` branch, and above each name in `.minions/cuts/` | not run |
| `after` | each id is an unmerged `[0-9]*` branch, its number below `<id>`'s | the same |

- The default branch is `origin/HEAD`'s, else `main`; the run directory is the primary checkout's `.minions/`, that is
  `<git-common-dir>/../.minions`, the same from every worktree.
- `Workspace setup:` stays the cut's own step: it runs a command the repository names, not a check.

### D6

**The mechanical rows.** `cut_check.py` runs from the repository root, reads `openspec/changes/<id>/`, and prints
`cut_check: halt — <row> — <why>` per failed row, `cut_check: match — <sub-task>: <path>:<line>: <text>` per match the search
script prints, `cut_check: judge — <row> — <what to read>` per row left to judgment, and a last line
`cut_check: ready — <met> rows met, <judge> to judge` or `cut_check: halt — <k> rows failed`. Exit 0 ready, 1 a row failed, 2
`openspec` or a script cannot run. Each row's check:

| row | holds when |
|---|---|
| `I2` | the proposal, design and tasks stand; `specs/*/spec.md` stands, or `.openspec.yaml` has `skip_specs: true`, `specs/.gitkeep` stands and no spec file does |
| `I3`, `I18`, `I19` | `openspec validate <id> --strict` exits 0; `gate_check.py --tasks` exits 0; `verify_check.py` exits 0 — each folded, its lines printed under its row |
| `I4` | `tasks.md` opens a title, one line, `## Progress`; each line is `- [ ] N — Title · moderate` or `· hard`, or holds `**HUMAN`, its box ticked or not; each has a `## N — Title`; each `- [ ] N.M` holds `Verify:` |
| `I11` | `design.md`'s `## Dependencies` is `None.` or a table headed package, constraint, why |
| `I12` | no sub-task of a phase not marked `**HUMAN` opens with a ritual of another station: run `make gate` or `make check` or an `mf-` skill, add a CHANGELOG entry, tick, commit, tag, archive, release |
| `I13` | `proposal.md` opens `---` frontmatter holding `bump: minor` or `patch`, equal to `--bump` when given |
| `I14` | each `**HUMAN` phase holds a sub-task with `Verify:` |
| `I17` | each `after:` id of the frontmatter is an unmerged `[0-9]*` branch, its number lower |
| `A1`, `A2` | the headings of each file stand in the order `A1` gives, `## Tests` after `## Decisions`; the proposal's last `## ` is `## Not in this change` |
| `P9` | each id the design defines, cited in `tasks.md` or `proposal.md` outside a code span, sits in a link `[D3](design.md#d3)` |
| `P13` | each sub-task, its line and wrapped lines, holds 3 lines at most |
| corpus | `plan_check.py`'s `check_corpus` over the sub-tasks prints nothing |

- The judgment rows are `I5`, `I6`, `I7`, `I8`, `I9`, `I10`, `I15`, `I16`, `P12` and `P13`'s paragraphs.
- `P12` lists each line matching a number word or digits before a plural noun of things; `P13` lists each paragraph past 3
  sentences. Each prints `path:line` as the candidate, and the cut or the reviewer judges it.
- The siblings load by `runpy`: `cut_pre.py` for the default branch and the open versions, `plan_check.py` for `subtasks` and
  `check_corpus`. `verify_check.py` and `gate_check.py` run as `sys.executable <script>`: they need no `uv`.
- The review packet carries the output; the reviewer takes each met row as settled
  ([D71](../../../docs/decisions.md#d71--the-cut-and-converge-read-what-changed)).

### D7

**The models file at queue time.**

- In `cut()`, after the brief's packages are read and before the lock, `conduct.py` runs
  `UV_RUN brief_check.py --models <brief> <slug>` (`UV_RUN = ("uv", "run", "--script")`, a module constant a test swaps), 60 s
  at most. An exit other than 0, or text `tomllib` refuses, is `Stop(2, "cut: cannot run — …")`, reserving nothing.
- Under the lock, after the id is chosen and before the reservation, `_write_in_change` writes the text to
  `.minions/changes/<id>/models.toml`, and the entry gains `"models": <text>`.
- `CUT_KEYS` is unchanged: an entry with no `models` was queued before this change, and `_check_cut` keeps its present test
  for it.
- At the start of `cutting()`, before its test of the branch, the same write restores the file from the entry. A rejoin after
  a changed file then finds the committed branch, skips the cutter, and the check passes on the restored file.
- `_check_cut(primary, change, tree)` keeps its signature: it reads the entry's text from the queue, reads `models.toml`
  through no link, and fails `changes/<id>/models.toml changed since the cut was queued` when `sha256` of the file's bytes is
  not `sha256` of that text. The brief's "records its hash" is met by the entry's text, from which the hash follows.
- The hash is checked at the cut alone: a later plant is the class `THREAT_MODEL.md` accepts, with card `0105·S2`.

### D8

**No corpus case.** `scripts/corpus.toml`'s cases run a reader over run data the repository's own runs wrote: findings files,
status logs, run logs, Codex sessions.

- `cut_pre.py` reads the file names of `.minions/cuts/`; `conduct.py` reads one file's bytes and compares a hash.
- Neither parses a format a worker or a run writes, so no sub-task carries `**CORPUS**`.

### D9

**The record.** D77 · *A mechanical step is a script* is added to `docs/decisions.md`'s Planning group, after D69, and to that
group's index line. It amends the page's D7, D40 and D41, each edited where it lives, per `A7`.

- In `K`: Step 1 runs `cut_pre.py`; Step 2 runs `facts.py place` and starts helpers for unplaced facts; Step 3 runs
  `facts.py readers`; Step 8 runs `cut_check.py` and holds its summary line and judgment rows; Step 8.5's packet adds its output.
- In `K`, too: Step 11 and *Suggesting models* say that `conduct.py` wrote the unattended file and a hand cut writes what
  `--models` prints; `gate_check.py --tasks` is "the gate-edit check".
- In `P`: the `## Facts` line of the template is the grammar of [D1](#d1), and the re-measure row runs `facts.py`.
- In `TS`: `_METRICS_SCRIPTS` gains the cut's `gate_check.py`, `cut_pre.py`, `cut_check.py` and `facts.py`, and `mf-plan`'s
  `facts.py`; each scan's expected list gains their `not named` lines.

The text of D77, placed after D69:

```markdown
### D77 · A mechanical step is a script

**The cut's preconditions, the placing of the brief's facts, the readers of a deleted name, the self-check's mechanical rows
and the models file are scripts; the cut's LLM writes the plan and judges what no script can check. `conduct.py cut` writes
`models.toml` from `brief_check.py --models` when it queues the cut, and a cut halts on a changed file.**

- **Why:** the cut's main session was $3.39 of a $6.99 cut, most of it turns that ran a rule: the preconditions, a fact's
  moved state, the self-check table. A script holds a rule the same way each run.
- **Accepts:** the file is checked at the cut alone; a later plant stays the class the threat model accepts.
- **Rejected:** a checker that judges the deterministic rows ([D66](#d66--two-checkers-conformance-and-adversarial)) · the
  cut's LLM writing the models file, which a worker can edit.
- **Amends:** D7, D40 and D41, each edited where it lives.
```

The edits, in the page's own D7, D40 and D41, before → after:

- `### D7`: "It re-checks the facts whose files moved since the brief's `At` line, and its helpers read them." → "`facts.py` places
  the brief's facts at `HEAD`, its helpers read the unplaced ones, and `cut_check.py` decides the self-check's mechanical rows
  ([D77](#d77--a-mechanical-step-is-a-script))."
- `### D40`: "answering in the cut's thread and writing no file" gains "and read only a fact `facts.py` left unplaced".
- `### D41`: "the cut writes those ([D58](#d58--a-settled-brief-is-cut-by-a-conductor-station))" → "`conduct.py` writes those when it
  queues the cut ([D58](#d58--a-settled-brief-is-cut-by-a-conductor-station)), and a cut by hand writes what
  `brief_check.py --models` prints".

## Tests

No end-to-end browser test: the repository has none, and each step is a unit or integration test at the lowest layer that can
fail (`T1`). The new test files are the scripts' own, as no test reaches a new script (`T2`); every other step extends a test
that reaches its state. The slow ship tests run on the fake hosts and are skipped by `make check`.

Counts at `HEAD`: `git grep -c "^def test_" -- tests/test_brief_check.py tests/test_conduct.py tests/test_skills.py` prints 4, 160
and 21. The rows marked new below are the added unit tests, each file's count the same command run over it once built; no
end-to-end run is added, and no test is removed.

| test | gains |
|---|---|
| `test_a_fact_citing_a_path_and_a_line_is_ready` (new, `TB`) | the tail forms of [D1](#d1): one cite, two cites, `./AGENTS.md`, a wrapped item; `--facts` prints their JSON; no `## Facts` prints `[]` |
| `test_a_fact_out_of_grammar_halts` (new, `TB`) | a basename, a bare `:12`, the legend `C:4357-4406`, a `..` path, an absolute path, no `at <sha>`, a short sha, a trailing sentence: each exit 1 naming `fact <k>`; `--facts` prints no JSON |
| `test_models_prints_the_items_toml` (new, `TB`) | [D2](#d2): every part, a host, a skip, `converge skip`, `shadow`, `decide`; the output read by `tomllib`; a line out of shape exits 1, an unknown slug 2 |
| `test_a_custom_tag_opens_no_section` (new, `TB`) | [D3](#d3): `<h12>` and `<h2-widget>` end no section; `<h2 id="x">` and `<H1/>` do |
| `test_a_fact_on_an_untouched_path_stands` (new, `tests/test_facts.py`) | a path outside the diff: stands, in a scratch repository |
| `test_a_fact_whose_lines_shifted_is_moved` (new, same) | lines added above: moved to the new range; a pure insertion between two cited lines: unplaced |
| `test_a_fact_on_a_changed_line_is_unplaced` (new, same) | a changed line, a deleted file, a renamed file: unplaced |
| `test_a_fact_with_no_commit_or_a_bad_sha_is_unplaced` (new, same) | `--output=x` runs no git command; an unknown sha is unplaced |
| `test_readers_print_each_hit_or_none` (new, same) | a name with two hits, a name with none, a name starting `-` |
| `test_the_notes_file_is_written_and_appended` (new, same) | `place --notes` writes afresh with the title, `readers --notes` appends |
| `test_what_cannot_be_read_exits_2` (new, same) | no brief, not a repository, a brief whose facts are out of grammar |
| `test_the_brief_reaches_the_placer` (new, same) | `place` through `brief_check.py --facts` with the runner swapped to this interpreter |
| `test_every_precondition_holds_by_hand` (new, `tests/test_cut_pre.py`) | a scratch repository with a gate: one line per check, exit 0 |
| `test_each_failed_precondition_is_named` (new, same) | a dirty tree, a branch off the default, a taken id, a reservation, an empty gate, a missing `AGENTS.md`, an `after` not open or not lower |
| `test_unattended_preconditions` (new, same) | a linked worktree on the branch, the reservation standing; each way it fails |
| `test_what_cannot_be_checked_exits_2` (new, same) | a bad id; a directory with no repository |
| `test_a_clean_change_prints_its_judgment_rows` (new, `tests/test_cut_check.py`) | a minimal change directory under a fake `openspec`: exit 0, each judgment row, a summary line starting `cut_check: ready`; no count is asserted |
| `test_each_mechanical_row_fails_by_name` (new, same) | parametrized by row, the ids the row names (`I2`, `I4`, `I11`, `I12`, `I13`, `I14`, `I17`, `A1`, `A2`, `P9`, `P13`): one defect of [D6](#d6), the row named in the output, exit 1 |
| `test_the_folded_checks_report_their_failures` (new, same) | `openspec`, the gate-edit check and the search script failing; the corpus check on a missing case |
| `test_what_cannot_be_checked_exits_2` (new, same) | no change directory; `openspec` not on `PATH` |
| `test_a_cut_queues_its_models_file` (new, `T`) | `cut()` with the runner swapped: the file, the entry's text, exit 2 with no item and nothing reserved |
| `test_parallel_cuts_reserve_apart_and_start_one_run` (`T`) | the briefs hold an item per slug; the entry holds `models` |
| `test_a_queued_cut_is_cut_then_built` (`T`, slow) | an entry with `models` and the fake mode `cut-bare`: the cut passes with the file the queue wrote |
| `test_a_cut_halt_is_shown_and_rejoin_cuts_again` (`T`, slow) | an entry with `models`, the cutter writing other text: halt `changes/<id>/models.toml changed since the cut was queued`; a rejoin restores the file; a custom `<h12>` block above a package table is neither `None.` nor one table, and a real `<h2 id="x">` after `None.` ends the section |
| `test_the_metrics_script_scan_reports_a_missing_script` (`TS`) | the new pairs, each `not named` in both expected lists |
| `test_the_stations_run_the_bundled_metrics_script` (`TS`) | the new pairs name a script that stands |

**Guards.** The hash check's twin is the slow test with `_check_cut` skipping the hash, in the commit body (`T6`). `facts.py`'s
non-hex refusal is held by its test step; its twin is the step with the hex check removed, in the commit body. No test is deleted
or merged, so no `I16` table.

## Dependencies

None.

## Risks / Trade-offs

- **A fact in the old form** → `brief_check.py` refuses it, and the person rewrites it at the next `mf-plan from=` ([D1](#d1)).
- **A root file needs `./`** → the one oddity the grammar costs; the alternative reads `C:4357-4406` as a path.
- **A line map is not a meaning check** → a fact whose cited lines moved intact is `moved`; a fact whose lines are unchanged
  but whose claim a nearby change falsified is `stands`. The brief's old rule had the same bound: it judged files, not claims.
- **A script's judgment rows read thin** → `P12` and `P13` list candidates only; the cut and the plan reviewer judge them.
- **A changed models file is checked at the cut only** → a later plant is the accepted class of `THREAT_MODEL.md` and card
  `0105·S2` ([D7](#d7)); debt `0085·S2` is closed for the cut, as the brief says.
- **`uv` at queue time** → `cut()` runs `uv run --script`; `conduct.py` is itself a `uv` script and its worker tools list `uv`.
- **H14 may miss** → the cut's main session stays above $2.40; the line stays: *converge script* and *evidence step* carry the
  rest, and the person's ledger records the miss.

## Verdict

Ready to build: one feature, the parser first, the scripts next, the prose and the record last. No step is irreversible: each
script is a file, and a queued cut with no `models` text still passes as before.
