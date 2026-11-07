# Converge roles — design

Converge's checkers become conformance and adversarial, each with its own packet; a script picks the debt cards; a verify reads
its open cards. Verdict at the end: ready to build.

## Context

Read at `d11ca6c` (v0.72.0). The brief's `At` commit is `bb4cf51`; its facts cite no repo path, so each was re-read here. `C` is
`skills/mf-ship/scripts/conduct.py`, `S` is `skills/mf-converge/SKILL.md`, `W` is `skills/mf-converge/references/worker.md`.
This change builds `after: [0094-lighter-converge]`, cut and not built at this cut: its `bundle.py`, `surfaces.py`, `WORKERS`,
`_worker_clause`, worker tables, D64 and the sections it adds are read from its `design.md`, and the build finds each by
name, never by line. 0094 builds after `0092-amend-round`, cut, and 0092 after `0090-supervisor-merge`, built: both land
first, read with `git show <id>:openspec/changes/<id>/…`, and this delta's blocks on a requirement they change are their text,
renamed.

The measurement, from the brief's reading of 0072–0089: 130 workers, 37 converge logs, 156 cards rebuilt from the logs.

| measure | value |
|---|---|
| a round-1 review's tool-result tokens | 1,639k over 25 workers |
| of them, `.minions/debt.md` | 11.4%, cited by no blocker |
| the diff, as `diff.patch` and again through `git diff`/`git show` | 15.1% and 8.3% |
| a verify round re-reading its findings file and the method | 40–50% |
| blockers caught by spec conformance as text | 10 of 35 (29%) |
| blockers caught by adversarial correctness | 21 of 35 (60%) |
| issues found by both review and security | 11 |
| tests at this cut | 249 — `git grep -c '^def test_' -- tests/`, summed |

- **F1. The roles in code.** `C`'s `ROLES = ("review", "security")`, `BLOCKS`, `OLD_LAYOUT`'s findings entries, `_unjudged`,
  `_open_blockers`, `_security_blocks` and `_security_held` (both read `security.md`), and `report` (reads `review.md`). The
  halt ids match `\b[RS]\d+\b`.
- **F2. The old-layout readers.** `OLD_LAYOUT` tuples in `skills/mf-converge/scripts/gate_check.py`,
  `skills/mf-integrate/scripts/integrate.py` and `scripts/metrics/run.py`; `integrate.py`'s `unready` reads
  `("review", "security")`; `C`'s `_old_files` feeds `migrate_layout`, `_old_layout` and `report`'s `old layout` line.
- **F3. The metrics.** `run.py`'s `ROLES` and `ROLE` name the role metric ids and the Task description match;
  `metrics/catalogue.toml` declares `review-confirmed`, `security-confirmed`, `review-refuted`, `security-refuted`,
  `review-tokens-per-confirmed` and `security-tokens-per-confirmed`. `skills/mf-review-metrics/scripts/review_metrics.py`'s
  `FILES`, `ROLES`, `_TWO_ROLES`, `_session`, `_filled` and `read_change` read the old names.
- **F4. The references.** `skills/mf-converge/references/generic-review.md` and `generic-security.md`, linked from `S`'s *The
  workers* and `scripts/metrics/reading_set.py`'s `worker` set; `W`'s `## Review and security`, linked as
  `#review-and-security` from `S`'s Step 3.
- **F5. The card.** `W`'s Priority is `<severity> · <role> · <category>`, its categories `security` among them; `W`'s example
  card is `S1`, `medium · security · stability`.
- **F6. The prose.** The old names stand in `S`, `W`, the `SKILL.md` of `mf-build`, `mf-cut-change`, `mf-integrate`,
  `mf-release`, `mf-rescue` and `mf-supervise`, `docs/principles.md`, `docs/decisions.md` (D11, D12, D13, D15, D36, D37, D39,
  D48's *Why*, D49, D56, D57 and the check-loop diagram), `README.md`, `docs/README.md` and `THREAT_MODEL.md`; 0094 adds them
  to D64, `S`'s Step 7 surfaces run, resume table, status log's `by rule` row and *Never*, `THREAT_MODEL.md`'s `## Surfaces` —
  its `generic-security.md` glob among them — and *Out of scope*, `docs/principles.md`'s recomputed head and the bootstrap's
  `THREAT_MODEL.md.tmpl`.
- **F6b. Two slow tests read `_unjudged`'s line.** `test_each_check_passes_only_on_disk_evidence` and
  `test_a_release_cut_short_is_recovered` assert `no review findings file`; `make check` skips them, the gate does not.
- **F6c. 0092's tests.** 0092 renames `test_a_drift_amend_goes_on_by_rule` to `test_a_drift_amend_answers_its_halt` and
  `test_a_fix_after_a_cap_halt_converges_afresh` to `test_a_fix_after_a_cap_halt_gets_one_round`, adds
  `test_an_amend_past_the_judged_head_gets_one_round`, asserting `review.md` holds `round: 2`, and has the fake's `amends`,
  `amend-halts` and `verify-fails` modes read review's `head:`. Its added requirement says "Review SHALL keep the full plan".
- **F7. The debt.** `S`'s Step 3 hands every worker `.minions/debt.md`; `W`'s repeat rule matches "a defect already carded in
  the debt".
- **F8. Verify.** `S`'s Step 7 re-dispatches both roles with Step 3's inputs, their findings file and the fix diff; `W`'s
  `## The verify pass` and each reference's `## Verify freshly` hold the method.
- **F9. What stays.** `CHANGELOG.md`, `openspec/changes/archive/**`, `metrics/changes/*.json`, `Why: 00NN-…` citations, old-name
  fixtures in tests of an old-name reader, "review" as the activity — converge's review, the plan review, `mf-review-metrics`,
  `review-metrics.json`, D42's and D45's "review", `docs/principles.md`'s opening line, `THREAT_MODEL.md`'s "review holds it",
  `mf-simplify`'s notes for review — and "security" as a concern: a security card, the threat model, a security pattern.

## Goals / Non-Goals

**Goals:** each checker reads what its job needs; no worker reads the debt file; the diff read once; a verify reads its open
cards; one rule for every old name.

**Non-Goals:** a third checker; the conductor's own reading set; new card ids; a metric for verify's reading set.

The cut decided these under the brief's switch, each logged in the brief's `## Decisions`:

| id | decision | because |
|---|---|---|
| C1 | a fixer sent a blocking card runs on adversarial's model | 0094's D3 put it on review's, the strongest tier; R12 gives that tier to adversarial |
| C2 | a hand-run station on a folder holding `review.md` or `security.md` halts naming `/mf-ship`; `review_metrics.py` and an old `[converge.review]` or `[converge.security]` table read the old names; `run.py` reads the new alone, a gap without them | D57 rejects reading both layouts in the stage machine; the history readers keep their past; a version converged on the old pin keeps its other run metrics |
| C3 | card ids stay `R` for conformance and `S` for adversarial | debt ids, halt lines and `C`'s id match carry them |
| C4 | a **security card** is an adversarial card whose Priority's category is `security` | D60 and D61 bar security harms; barring every adversarial `high` would take most blockers from the self-healing |
| C5 | the role metrics and the reading sets take the new names; past data files keep theirs | a checker that judges differently starts its own series |
| C6 | conformance's packet keeps root `AGENTS.md` and the standards files; neither role reads `docs/principles.md`; adversarial's adds `AGENTS.md` and the bundle's debt cards | D46 holds the standards for converge; R10's repeat rule needs the cards |
| C7 | the packet test reads each reference's `## The packet` table as structure | D42: a test checks structure, never that a sentence exists |
| C8 | a catch-up's judge round dispatches the role references; only a Step 7 round after a fix takes `verify.md` | a catch-up judges new commits no card describes |
| C9 | every live mention of the old names leaves in phase 1, docs and decisions included; phase 4 keeps D66, D48 and the reading sets | *A retired word is retired everywhere* asks for one commit |

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | `conformance`/`conformance.md`, `adversarial`/`adversarial.md`; the card's role, ids and security card | R4, R8 | four checkers |
| [D2](#d2) | `conduct.py` takes the new names, moves the old ones at a run's start, and reads an old worker table | R8, R12 | a one-off migration |
| [D3](#d3) | Every old-layout reader halts on the old names; `surfaces.py` reads `adversarial.md` | R8 | reading both names in the stage machine |
| [D4](#d4) | The run metrics take the new names; `review_metrics.py` reads both | R8 | keeping the metric ids |
| [D5](#d5) | `generic-conformance.md` and `generic-adversarial.md`, each with a `## The packet` table; `W` renamed | R9 | one shared packet |
| [D6](#d6) | The skills take the new names and the packets | R8, R9 | — |
| [D7](#d7) | The docs and decisions take the new names; D12 rewritten | R8 | a sweep in phase 4 |
| [D8](#d8) | `debt_match.py` appends the debt cards on the diff's files to the bundle | R5, R10 | workers grepping the debt |
| [D9](#d9) | No worker reads `.minions/debt.md`; `diff.patch` read once | R5, R6 | — |
| [D10](#d10) | `open_cards.py` and `references/verify.md` for a verify round | R7, R11 | the whole findings file |
| [D11](#d11) | Conformance's default moves to the mid tier · high | R12 | — |
| [D12](#d12) | D66; D48 amended; `AGENTS.md`'s worker line | R13 | — |
| [D13](#d13) | The reading set per role | R13 | one worker set |

### D1

**Conformance** judges the code against the change's own spec delta, design, tasks and the decisions it cites; it grades
`blocking` · `drift` · `nit`. **Adversarial** tries to break the change — races, edge cases, exploits, security; it grades
`critical` · `high` · `medium` · `low`, `high` a bug that would block. Their files are `.minions/changes/<change-id>/conformance.md`
and `adversarial.md`, their findings frontmatter `type: conformance | adversarial`.

- A card's Priority is `<severity> · conformance · <category>` or `<severity> · adversarial · <category>`. Conformance's ids are
  `R<n>`, adversarial's `S<n>` (C3).
- A **security card** is an adversarial card whose Priority's category is `security` (C4): the card D60 and D61 keep from the
  rescue and the supervisor.

### D2

In `C`:

- `ROLES = ("conformance", "adversarial")`; `BLOCKS = {"conformance": ("blocking",), "adversarial": ("critical", "high")}`.
- `OLD_LAYOUT`'s `"findings/{}_review.md"` maps to `"conformance.md"`, `"findings/{}_security.md"` to `"adversarial.md"`.
- `OLD_ROLES = {"review.md": "conformance.md", "security.md": "adversarial.md"}`, its comment naming this design.
  `_old_files` also yields, for each folder under `.minions/changes/`, each `OLD_ROLES` name it holds, as `(path, new)`; its
  docstring gains `changes/0001-x/review.md → conformance.md`.
- `migrate_layout`'s check, before any move, also halts when two old files of one change name one new path:
  `<old> and <other> both name <new>: a person settles which to keep`, both relative to the primary.
- `_category(card)` returns the Priority's third ` · ` part, before any ` — `, stripped of backticks, in lower case, and `""`
  when the Priority has fewer parts: `"high · adversarial · security — why"` → `"security"`. `_security_blocks` and
  `_security_held` read `adversarial.md`, and a card counts when its severity is in `BLOCKS["adversarial"]` and `_category` is
  `security` or `""`: a card whose category cannot be read bars, as an unread file does. Their docstrings say
  `adversarial.md`.
- `report` reads `conformance.md` for the round.
- 0094's `WORKERS` becomes `("converge.conformance", "converge.adversarial", "converge.fix")`, so `_worker_clause` writes
  `conformance=` and `adversarial=`. `OLD_WORKERS = {"converge.conformance": "converge.review", "converge.adversarial":
  "converge.security"}`: `_models`, for a worker whose table `_table` does not find, reads its `OLD_WORKERS` table (C2).

### D3

- `gate_check.py`'s and `integrate.py`'s `OLD_LAYOUT` gain `"changes/{}/review.md"` and `"changes/{}/security.md"`, so a
  hand-run station halts on them, naming `/mf-ship`, as on any old path (C2). `run.py`'s stays: it reads the new names alone,
  so a version converged on the old pin records its role metrics as gaps and every other run metric as before.
- `integrate.py`'s `unready` reads `("conformance", "adversarial")`.
- 0094's `skills/mf-converge/scripts/surfaces.py` takes `<adversarial.md>`; its reasons read `adversarial.md is not clean` and
  `adversarial card <id> is <status>`. Its docstring and `tests/test_surfaces.py` follow.

### D4

- `run.py`: `ROLES = ("conformance", "adversarial")`; `ROLE = re.compile(r"\b(conformance|adversarial)\b", re.IGNORECASE)`. The
  role metric ids follow `ROLES` (C5).
- `metrics/catalogue.toml`: the role entries take ids `conformance-confirmed`, `adversarial-confirmed`,
  `conformance-refuted`, `adversarial-refuted`, `conformance-tokens-per-confirmed` and `adversarial-tokens-per-confirmed`, each
  entry's `args` its new id, and titles "Conformance's …" and "Adversarial's …" for "Review's …" and "Security's …".
- `review_metrics.py`: `ROLES = ("conformance", "adversarial")` and `OLD_ROLES = ("review", "security")`. `FILES` gains
  `conformance.md` and `adversarial.md`. A role name is matched in both tuples by `_role_tokens`, `_session` and `_filled`, and
  recorded as written; `_TWO_ROLES`' forms, the old era's, return `OLD_ROLES`' pairs. `read_change` reads `conformance.md`, else
  `review.md`, with `("blocking",)`, and `adversarial.md`, else `security.md`, with `("critical", "high")`.

### D5

`git mv` `skills/mf-converge/references/generic-review.md` to `generic-conformance.md` and `generic-security.md` to
`generic-adversarial.md`; each is then rewritten for its role, keeping *Inputs and contract*, an inspect section, *The bar a
finding clears*, *Write* and *Verify freshly*.

- **`## The packet`**, in each, a table `| input | what it is for |`, one input per row (C6, C7). Conformance's first cells,
  in order, are exactly: `` `<base>..<head>` ``, `` `diff.patch` ``, `` `refactor(<change-id>): simplify` ``,
  `` `proposal.md` ``, `` `design.md` ``, `` `tasks.md` ``, `` `specs/` ``, `` `bundle.md` ``, `` `AGENTS.md` ``,
  `` `CODING_STANDARDS.md` ``, `` `CODE_STANDARDS.md` ``, `` `CONTRIBUTING.md` ``, `` `ARCHITECTURE.md` `` and
  `` `docs/adr/*.md` ``. Adversarial's are `` `<base>..<head>` ``, `` `diff.patch` ``, `the source and tests around each hunk`,
  `` `THREAT_MODEL.md` `` and `` `AGENTS.md` ``.
- **Conformance inspects**, one section each: *Spec* — the delta and the bundle's living requirements, the requirement line
  quoted; *Plan* — each task built as written, each `design.md` decision held; *Architecture* — the bundle's decisions, and one
  the index names that the diff reaches, opened in `docs/decisions.md`; *Standards* — as review's today; *Gate integrity* — as
  review's today. It reads no code beyond the diff's hunks, save `git grep` for its stale-claim pass over the tree, the living
  spec and the decisions.
- **Adversarial inspects**: *The threat model first*, as security's today; *Break it* — for each hunk, input at and past its
  bounds, empty and huge, Unicode and path edges, concurrent and repeated runs, partial failure and ordering, each removed
  guard's invariant; the callers of a changed return shape or error; every consumer of a changed enum; a finding a class, its
  sibling sites grepped; *Security* — each input traced across a boundary into a sink, security's classes and tuple today. Its
  bar is its own: the change introduced it, a concrete scenario, the line quoted, and for a security card a reachable entry
  point and a harm the threat model names or an anchor; security's trust precedents and do-not-flag list stay.
- `W`: its title says conformance, adversarial or fix worker; `## Review and security` → `## Conformance and adversarial`;
  "Review runs these passes" → "Conformance runs these passes"; *Scoping*'s "with surrounding source, by the loaded role
  resource" → "conformance with no source beyond the hunks, adversarial with the source around them"; the frontmatter's `type:`; the grades table; the anchors'
  "`blocking` in conformance and at least `high` in adversarial"; the verify pass's and catch-up scope's "the review"; the
  card's Priority row naming the roles and ids (D1); the writing limits' "the conformance and adversarial files"; the example
  `S1`'s Priority → `medium · adversarial · stability`; *Rules for tests*' "conformance's test-cost pass".
- `scripts/metrics/reading_set.py`'s `worker` set names `skills/mf-converge/references/generic-conformance.md`, the file it read
  under its old name, until [D13](#d13) splits the set.

### D6

**The old-layout lists** of `S`, `skills/mf-release/SKILL.md`, `skills/mf-build/SKILL.md` and `skills/mf-integrate/SKILL.md`
each gain, after `.minions/gate-check/<change-id>/`, the words "or `.minions/changes/<change-id>/review.md` or `security.md`"
(C2), and keep their old `_review.md` and `_security.md` names.

- `S`: the description's "fan out conformance and adversarial"; *The workers*' links to `generic-conformance.md` and
  `generic-adversarial.md`; the status log example's roles; Step 3's "The stations are **conformance** and **adversarial**",
  its "so review judges them" → "so conformance and adversarial judge them", its list replaced by "the packet its
  reference's `## The packet` table names", then its mode, its findings path, the card,
  and the debt bullet as it stands — [D9](#d9) drops it in phase 2 — with links to `worker.md#conformance-and-adversarial`;
  Step 5's rows "is conformance's" and its non-blocking tiers; Step 6's "Conformance checks for exactly this"; 0094's **Worker
  models** paragraph's `conformance=` and `adversarial=`; 0094's Step 6 dispatch line → "on `adversarial=`'s model when any
  card it is sent is blocking" (C1); Step 7's roles; 0094's surfaces run → `.minions/changes/<change-id>/adversarial.md`, its
  paragraph's "the adversarial file" and "dispatch conformance alone"; 0094's resume row → "Step 7's conformance dispatch",
  its status log `by rule` row and *Never*'s "Step 7's adversarial head". Step 3's simplify body stays "for review", as
  `mf-simplify` writes its notes.
- `skills/mf-release/SKILL.md`: the paths block, preconditions 2 and 3 (**conformance is clean**, **adversarial is clean**) and
  precondition 4's "the conformance and adversarial stations judged its edits".
- `skills/mf-build/SKILL.md`: *Why inside the build*'s "the conformance and adversarial stations" and "conformance reads a
  diff"; `P12`'s example "the conformance and adversarial files"; *Never*'s "no fan-out, conformance or adversarial pass, or
  converge loop".
- `skills/mf-cut-change/SKILL.md`: `P12`'s example as above; 0094's Converge bullet, worker-table sentence and TOML template —
  `[converge.conformance]`, `[converge.adversarial]`, "conformance and adversarial on the strongest tier · high".
- `skills/mf-rescue/SKILL.md` and `skills/mf-supervise/SKILL.md`: their read tables' `conformance.md` and `adversarial.md`, and
  under each read table one line: "A **security card** is an adversarial card whose category is `security`."

### D7

- `docs/principles.md`: *Words* — Station "cut, build, conformance, adversarial, fix, release", Checker "conformance,
  adversarial"; the check-loop diagram; *A checker is a fresh reader* — "Conformance and adversarial run as new instances";
  *Nothing reads as clean* — "A conformance file without its stale-claim pass is not clean", and 0094's sentence → "an
  adversarial head … with no adversarial card awaiting its checker";
  *No station verifies its own work*'s *Held by* — "conformance"; *Never weaken the gate*'s *Held by* — "conformance reads the
  diff", "conformance's coverage-trace pass"; *A retired word*'s *Held by* — "conformance's stale-claim pass".
- `docs/decisions.md`: the check-loop diagram; D11's "the conformance and adversarial references"; D12 →
  `### D12 · Conformance, adversarial and simplify are kept apart`, its bold text "Conformance looks for what the plan asks and
  the code lacks, adversarial for what breaks it, simplify for too much. Each is its own pass."; D13's "so converge's checkers
  judge them"; D15's table rows `conformance` and `adversarial`; D48's *Why* — "adversarial falls back on generic categories"; D36's "conformance judges whether a test proves it"; D37's and
  D39's "Conformance"; D49's "The conformance and adversarial files"; D56's "conformance's `blocking`, adversarial's
  `critical` and `high`"; D57's `conformance.md`, `adversarial.md`, and its move naming a folder's old `review.md` and
  `security.md`; 0094's D64 — `[converge.conformance]`, `[converge.adversarial]`, "its conformance and adversarial workers",
  "on adversarial's model", "Conformance reads `bundle.md`", "with no adversarial card awaiting its checker", "its adversarial
  head".
- `AGENTS.md`'s opening note: "review the branch diff, run a security pass" → "check the diff's conformance, run an adversarial
  pass".
- `README.md`: the diagram and the `mf-converge` row's "conformance ‖ adversarial"; *Execution*'s "conformance and adversarial at
  one depth" and 0094's converge sentence. `docs/README.md`: the diagram. `THREAT_MODEL.md` and the bootstrap's
  `THREAT_MODEL.md.tmpl`: 0094's `## Surfaces` and *Out of scope* lines — the glob
  `skills/mf-converge/references/generic-adversarial.md` for `generic-security.md`, "the adversarial head" on one line, "the
  adversarial file's cards", "an adversarial verify".

### D8

`skills/mf-converge/scripts/debt_match.py`, a `uv` script, run from the repository root:
`debt_match.py <debt.md> <diff.patch> <bundle.md>`. It prints `debt: <n> cards on the diff's files` and exits 0, or prints
`debt: cannot match — <why>` and exits 2, writing nothing.

- **The paths.** Each `diff --git a/<x> b/<y>` line of the patch gives `<x>` and `<y>`. A missing or unreadable patch exits 2.
- **The cards.** A card is a line `- **<id> — …**`, through the line before the next such line or `#` heading. It matches when
  a backticked span of its `- **What it affects:**` line, a `:<line>` or `:<from>-<to>` suffix dropped, is one of the paths. A
  missing debt file matches none.
- **The write.** It drops a `## Debt cards on the diff's files` section the bundle already holds, to its end, then appends
  that heading and each matched card verbatim, or `None.`. It writes through a staged `.tmp` with `O_NOFOLLOW`, as `bundle.py`
  does; a missing bundle exits 2, a link `<path> is a link`.
- `tests/test_skills.py`'s `_METRICS_SCRIPTS` gains `("mf-converge", "scripts/debt_match.py")`.

### D9

- `S`: 0094's **Write the bundle** step and Step 6's re-freeze each run, after `bundle.py`,
  `uv run --script <this package>/scripts/debt_match.py .minions/debt.md .minions/changes/<change-id>/diff.patch .minions/changes/<change-id>/bundle.md`,
  else an old `.minions/backlog.md` in place of the debt; exit 2, or `uv` missing → **halt**, naming what it printed. Step 3's
  debt bullet goes.
- `W`'s repeat rule: "a defect already carded in the debt" → "a defect a debt card in the bundle's
  `## Debt cards on the diff's files` holds".
- Adversarial's packet gains `` `bundle.md` `` — its debt cards section alone. Each packet's `` `diff.patch` `` row says: read
  once; `git diff` or `git show` only for a file's context the patch does not hold.

### D10

`skills/mf-converge/scripts/open_cards.py`, a `uv` script: `open_cards.py <findings.md> <out.md>`. It prints
`open cards: <n> of <findings name>` and exits 0, or prints `open cards: cannot read — <why>` and exits 2, writing nothing.

- It writes `# <findings name> — the cards a verify judges`, then each card, parsed as D8 parses one, whose `**Status:**` reads
  `open`, `fixed` or `wontfix`, backticks dropped, verbatim; `None.` when none. A missing findings file exits 2; it writes
  through a staged `.tmp` with `O_NOFOLLOW`, a link at `<out.md>` exiting 2.
- `tests/test_skills.py`'s `_METRICS_SCRIPTS` gains `("mf-converge", "scripts/open_cards.py")`.
- **`skills/mf-converge/references/verify.md`**, new: what a verify worker gets — its `<role>.open.md`, the fix diff
  `diff.patch`, its findings path and, for conformance, the design's `## Tests` section; and what it does — `fixed` →
  `verified` or `open` with a reason, `wontfix` → `accepted` or `open`, an amend card's `wontfix` staying `wontfix`, a `a test`
  card reopened with no fitting red run, a regression a new card in [the card](worker.md#the-card)'s shape, the frontmatter's
  `head`, `round`, `reviewed`, `open_blocking` and `verdict` rewritten, each transition appended to `## Resolution log`, and the
  Summary's counts; conformance also runs its stale-claim, test-cost and coverage-trace passes over the fix diff. It reads the
  findings file only where it edits, and edits nothing else.
- `W`'s `## The verify pass` keeps its heading, its text moved to `verify.md`, and says "A verify round loads
  [verify](verify.md)". Each role reference's *Verify freshly* says the same.
- `S`'s Step 7, after `gate_check.py`: for each checker it dispatches, run
  `uv run --script <this package>/scripts/open_cards.py .minions/changes/<change-id>/<role>.md .minions/changes/<change-id>/<role>.open.md`;
  exit 2, or `uv` missing → **halt**. Each fresh worker gets [verify](references/verify.md), linked so, its open cards, the fix diff, its findings
  path and, for conformance, the design's `## Tests` section — never Step 3's packet. A catch-up's judge round dispatches Step
  3's inputs (C8); its fix round's verify is a Step 7 round after a fix.

### D11

- `skills/mf-cut-change/SKILL.md`'s Converge bullet: "conformance and adversarial on the strongest tier · high" →
  "conformance on the mid tier · high, adversarial on the strongest tier · high".
- D64's "its conformance and adversarial workers on the strongest tier · high" → "its conformance worker on the mid tier ·
  high, its adversarial worker on the strongest tier · high".
- `README.md`'s converge sentence says conformance runs on the mid tier, adversarial on the strongest.

### D12

`docs/decisions.md` gains, in *The check loop and the release* after D64:

```
### D66 · Two checkers: conformance and adversarial

**Converge runs two checkers. Conformance judges the code against the change's own spec, design, tasks and the decisions it
cites, from the change's artifacts, its bundle and the diff, reading no code beyond the diff's hunks; it grades `blocking` ·
`drift` · `nit`, on the mid tier. Adversarial tries to break the change — races, edge cases, exploits, security — from the diff,
the source and tests around it and the threat model; it grades `critical` · `high` · `medium` · `low`, `high` a bug that would
block, on the strongest tier. Each reads `diff.patch` once. `debt_match.py` bundles the debt cards on the diff's files, and no
worker reads `.minions/debt.md`. A verify round after a fix reads its open cards, the fix diff and `references/verify.md`.**

- **Why:** of 0072–0089's blockers, spec conformance as text caught 29% and adversarial correctness 60%; review and security
  found 11 issues twice; the debt was 11.4% of a round-1 review's reads, cited by no blocker; a verify spent 40–50% re-reading
  its file and the method.
- **Accepts:** conformance misses every race and parser edge, which adversarial owns · a security card is known by its
  category, which the checker writes.
- **Rejected:** four checkers — two earn their cost · a checker judging the deterministic checks — the gate, `gate_check.py`,
  the `Verify:` lines and coverage stay scripts · the old names: "security" read as security only.
```

- The map's check-loop list gains `D66`.
- D48's 0094 text "and converge hands every worker the threat model and its bundle: of the decisions, those the change cites,
  in full, and an index of all" → "and converge hands its conformance worker its bundle — of the decisions, those the change
  cites, in full, and an index of all — and its adversarial worker the threat model".
- `AGENTS.md`'s 0094 worker line → "**Converge's conformance worker reads, of the decisions, those its change cites, in full,
  and an index of all — its `bundle.md` — in place of the whole page; its adversarial worker reads the threat model.**"

### D13

`scripts/metrics/reading_set.py`'s `worker` set gives way to `conformance` — `AGENTS.md`, `CODING_STANDARDS.md`,
`CONTRIBUTING.md`, 0094's `INDEX`, `W` and `generic-conformance.md` — and `adversarial` — `AGENTS.md`, `THREAT_MODEL.md`, `W`
and `generic-adversarial.md` (C5, C6). The docstring names `converge`, `conformance`, `adversarial` or `shared`, and this
design. `metrics/catalogue.toml`'s `converge-worker-reading-set` gives way to `converge-conformance-reading-set` ("Converge
conformance worker's reading set", `args = ["conformance"]`) and `converge-adversarial-reading-set` ("Converge adversarial
worker's reading set", `args = ["adversarial"]`), each `watch = 10500`, as the worker set's.

## Tests

249 tests at the cut (`git grep -c '^def test_' -- tests/`, summed); 0090, 0092 and 0094 add theirs before this build. Added: 5 unit tests, 4 of them in 2
new files. No browser layer exists; no engine runs; no end-to-end test is added.

- `test_the_packets_hold_what_each_role_reads` (new, `tests/test_skills.py`) — a `_packet(path)` helper returns the first cell
  of each row under `## The packet`, backticks dropped; conformance's list equals [D5](#d5)'s, in order, and adversarial's holds
  `THREAT_MODEL.md`. Phase 2 adds: adversarial's holds `bundle.md`.
- `tests/test_debt_match.py` (new, loaded with `importlib` as `tests/test_stamp.py` loads its script):
  - `test_debt_match_bundles_the_cards_on_the_diffs_files` — a debt with a card naming `` `src/a.py:12` ``, one naming
    `` `src/b.py` `` and one under another change naming `` `docs/x.md` ``; a patch changing `src/a.py` and `docs/x.md`: the
    bundle's section holds the first and third cards and not the second; a second run leaves one section; no debt file writes
    `None.`.
  - `test_debt_match_refuses_what_it_cannot_read` — a bundle that is a link, a missing bundle and a missing patch each exit 2
    with its `debt: cannot match — …` line, and the link's target is unchanged.
- `tests/test_open_cards.py` (new, loaded the same way):
  - `test_open_cards_extract_what_a_verify_judges` — a findings file with cards `open`, `` `fixed` ``, `wontfix — why`,
    `verified` and `accepted`: the out file holds the first three verbatim and not the others; a file with none writes `None.`.
  - `test_open_cards_refuse_what_they_cannot_read` — a missing findings file, and an out path that is a link: each exits 2,
    and the link's target is unchanged.
- A line of `debt_match.py` or `open_cards.py` these leave uncovered gets a step in its phase's named tests, never a new test.

Extended or edited:

| test | gains |
|---|---|
| `tests/fake_worker.py` | every findings file the new names, 0092's `amends`, `amend-halts` and `verify-fails` modes reading conformance's `head:`; `_cards`' and `_amend_needed`'s Priorities `· conformance · stability` for `R` and `· adversarial · security` for `S`; 0094's `fix-surfaces` mode writes `adversarial.md` |
| `test_a_run_moves_an_old_layout` (`tests/test_conduct.py`) | a change folder's `review.md` and `security.md` move to `conformance.md` and `adversarial.md`; `review.md` beside `conformance.md` halts naming both; `findings/<id>_review.md` beside `changes/<id>/review.md` halts naming both and `conformance.md` |
| `test_a_rescue_amends_at_amend_needed` | beside its direct `_security_blocks` calls, an `adversarial.md` whose `S1` reads `high · adversarial · stability`: the halt naming `S1` returns False; one reading `high · adversarial` alone returns True |
| `test_a_supervisor_amend_outside_the_change_halts` | its `_security_held` card reads `high · adversarial · security` in `adversarial.md`; then the same card `· stability`, open, bars nothing |
| `test_each_check_passes_only_on_disk_evidence`, `test_a_release_cut_short_is_recovered` | `no conformance findings file` |
| `test_a_ready_version_ships_past_a_slow_one`, 0092's `test_a_drift_amend_answers_its_halt`, `test_a_dead_converge_halts_and_a_rerun_finishes_it`, 0092's `test_a_fix_after_a_cap_halt_gets_one_round` | the new file names |
| 0092's `test_an_amend_past_the_judged_head_gets_one_round` | `conformance.md` holds `round: 2` |
| `test_a_small_cap_is_granted_automatically` | the new file names; its backticked-Priority step replaces `blocking · conformance · stability` |
| 0094's `test_a_worker_clause_names_its_model_and_effort`, `test_a_station_runs_on_its_executor`, `test_the_plan_is_read_once`, `test_a_worker_carries_the_allowlist_and_a_denial_is_named` | the clauses `conformance=` and `adversarial=`; `_models` of `converge.conformance` reads an old `[converge.review]` |
| 0094's `test_a_fix_reaching_no_surface_takes_security_by_rule` | renamed `test_a_fix_reaching_no_surface_takes_adversarial_by_rule`, `adversarial.md`'s `mode:` checked; the same assertions |
| 0094's `tests/test_surfaces.py` | the `adversarial.md` reasons |
| `test_gate_check_halts_on_an_old_layout` (`tests/test_gate_check.py`) | a change folder's `review.md` halts naming it |
| `test_a_hand_run_station_halts_on_an_old_layout`, `test_next_picks_the_named_or_the_lowest_ready_id` (`tests/test_integrate.py`) | a change folder's `security.md` halts; the new file names |
| `test_run_metrics_read_cost_and_review_yield`, `test_reading_sets_count_words` (`tests/test_metric_scripts.py`) | the new files, metric ids and Task descriptions; the reference's new path, then the role sets ([D13](#d13)) |
| `test_both_layouts_are_read`, `test_tokens_are_read_per_role`, `test_codex_sessions_fill_the_rounds` (`tests/test_review_metrics.py`) | a folder with `conformance.md` and `adversarial.md` beside one with the old names; a `verdicts` line naming `conformance`; a session path naming `adversarial` |
| `test_the_metrics_script_scan_reports_a_missing_script` (`tests/test_skills.py`) | `debt_match.py`'s and `open_cards.py`'s `not named` lines in each expected list |

No test is deleted or merged; the one renamed keeps its assertions.

## Dependencies

None.

## Risks / Trade-offs

- A security harm graded under another category escapes the rescue's bar → the category is the checker's word, in the class
  *Out of scope* accepts; D66 accepts it by name.
- Conformance misses a race or a parser edge → adversarial owns them, on the strongest tier.
- A fix touching no surface skips adversarial's verify though it fixed a conformance card → `surfaces.py` still verifies any
  adversarial card awaiting its checker, and conformance verifies the fix.
- A card whose **What it affects** names no backticked path is never bundled → `W`'s card asks for `path:line` there; a
  missed repeat costs one level of grade.
- This change, and a version converged on the old pin and released after it in the same run, records its role metrics as gaps:
  the pinned converge writes `review.md` and `security.md` → `run.py` keeps no old-layout halt for them, so every other run
  metric stands, and the next run moves the files.
- The dependent merge-in flags each MODIFIED requirement 0090, 0092 and 0094 changed, since a rename changes their lines →
  each block here is their text renamed, so the settle keeps this delta's block; the supervisor settles it under the switch.
- A "prints nothing" search misses a mention wrapped across lines → each site is named in [D6](#d6) and [D7](#d7), and
  conformance's stale-claim pass reads the diff for it.
- 0094's converge or rescue reshapes a symbol this plan names → each task names it by symbol and section, and the build halts
  on one it cannot find.

## Verdict

Ready to build.
