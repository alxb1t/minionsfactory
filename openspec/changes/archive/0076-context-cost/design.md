# Context cost — design

The review metrics page reads the run logs' cost; a Claude worker starts with no MCP server; converge's workers load a worker
reference in place of the whole skill. Verdict at the end: ready to build.

## Context

Read at `6647909` (v0.61.0); the brief carries no `At` line, so every fact was re-read.

- **F1. The page:** `review_metrics.py`'s `read_change` (`skills/mf-review-metrics/scripts/review_metrics.py:344`) builds one flat
  record per change from the findings and `_status_log` (`:264`); `lacked` (`:499`) lists every key whose value is `None`;
  `render_page` (`:549`) draws `_repo_section` (`:524`) per repo, then `model_table` (`:461`). Tests at
  `tests/test_review_metrics.py:53-345`, inline fixtures through `_front`, `_card`, `_findings`, `_record` (`:28-49`).
- **F2. The run logs:** `conduct.py` writes `runs/<stamp>/<who>_<station>.log` (`skills/mf-ship/scripts/conduct.py:2535`), opened
  `"w"`, so a second spawn in one stamp truncates the first (`:2119`); the run log `runs/<stamp>.md` keeps a `spawn — <station>` and
  a `finish — <station> · exit N · Ns` line per spawn. A log's `result` events: `total_cost_usd` and `modelUsage` cumulative;
  `num_turns`, `duration_ms` and `usage` per segment since the last; 22 of ~120 logs hold 2–9. The probe's log is `run_probe.log`
  or `<who>_probe-<executor>.log`; `agent-<stamp>.log` and `detached.log` are no station's. A Codex log is text, with no result.
- **F3. The worker's command line:** the Claude branch of `argv` (`conduct.py:2058-2073`) ends with `--setting-sources user` and
  `--allowedTools … --disallowedTools …`, the last variadic; `--setting-sources user` stops a project's `.mcp.json` (`0052` design
  D1), but user-scope servers, connectors and plugins' still start. The probe and `agent` take the same `argv`.
  `test_a_claude_worker_starts_in_the_sandbox` (`tests/test_conduct.py:4941`) asserts `--setting-sources user` (`:4978-4980`).
- **F4. The workers' reading:** `generic-review.md:8` and `generic-security.md:8` load `../SKILL.md` — "Steps 3–7, Catch-up scope,
  The card, Rules for tests". `skills/mf-converge/SKILL.md` is 6,631 words; the worker's parts — Step 3's repeat rule, passes table
  and scoping (`:306-320`), Step 4 (`:322-381`), Step 5's station sentences (`:395-398`), Step 7's
  sentences on what a verify-round checker reads and runs (in `:446-452`), Catch-up scope whole (`:220-243`), The card (`:510-548`), Rules
  for tests (`:549-562`) — about 2,100. Step 5's not-clean table (`:386-393`) and Step 7's gate, `gate_check`, dispatch, the inputs it
  passes each checker and its verdict reading are the conductor's, and the living spec keeps them in `SKILL.md` (`openspec/specs/sdd/spec.md:57`,
  `:210`, `:559`). The workers also cite "per Step 5" and "per Step 7" (`generic-review.md:66`, `:71`; `generic-security.md:47`,
  `:52`).
  The fixer reads Rules for tests and the card's Status (`:408-412`).
- **F5. Readers of the moved sections:** `tests/test_skills.py`'s card owner (`:173-195`, hard-wired to `skills/mf-converge/SKILL.md`),
  `_TEST_RULE_CARRIERS` through `_shared_label_problems` (`:61`, `:86`, `:153-168`), `_resource_problems`' link capture with a
  `#fragment` (`:384-402`); `tests/test_review_metrics.py:213-214`'s Priority regex over `skills/mf-converge/SKILL.md`; prose at
  `skills/mf-converge/SKILL.md:513-514`, `:551-552`, `skills/mf-build/SKILL.md:299-300`, `review_metrics.py:40`.
- **F6. The metric:** `scripts/metrics/reading_set.py`'s `SETS` (`:13-22`); `converge-reading-set` (`metrics/catalogue.toml:4-13`)
  is 17,315 words at `6647909`; `test_reading_sets_count_words` (`tests/test_metric_scripts.py:42-58`).
- **F7. The record:** D50 (`docs/decisions.md:264`) names findings and status logs; D51's *Accepts* (`:512`); `THREAT_MODEL.md:21-22`.

## Goals / Non-Goals

**Goals:** a version's cost per station on the page; no MCP server in an unattended worker; the converge part of a review worker's
reading cut by more than half — `SKILL.md`'s 6,631 words to the worker reference's ~2,100; with the shared set, ~18,165 words to
~13,700.

**Non-Goals:** Codex's MCP servers and tokens; the other levers the brief parks.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | `_cost_logs` reads each station's log into the change's record; `cost_table` draws it | Q2 | a separate page |
| [D2](#d2) | `--strict-mcp-config` in the Claude `argv`, before `--allowedTools` | Q3, Q7 | a deny list of `mcp__*` |
| [D3](#d3) | The worker's parts move into `references/worker.md`; `SKILL.md` links them | Q4 | a copy, with no drift guard |
| [D4](#d4) | `converge-worker-reading-set`, and `worker.md` in the `converge` set | Q4 | — |
| [D5](#d5) | The record: D50, D51, `THREAT_MODEL.md` | Q2, Q3 | — |

### D1

`_cost_logs(repo, change) -> dict[str, Any]`: for each `repo/.minions/runs/*/<change>_<station>.log` — build, converge, integrate,
release, rescue — the last `result` event's `total_cost_usd` and `modelUsage` summed over models, and `num_turns` and `duration_ms`
summed over the result events; tokens are `inputTokens + outputTokens + cacheReadInputTokens + cacheCreationInputTokens` over
`modelUsage`'s models; per station, over every stamp: `cost_<station>`, `turns_<station>`, `tokens_<station>`, `seconds_<station>`,
each `None` with no log or no result event — a line that is not JSON is skipped, so a Codex text log is a gap. `spawns_<station>`
counts the run logs' `· <change> · spawn — <station>` lines; above the logs found, the cell reads `<logs> of <spawns>`. `read_change` spreads it in; a repo
with no `runs/` gives gaps, never a halt. `cost_table(records)`: per repo, one row per change, a column per station, `$`, turns,
tokens, seconds; `_repo_section` draws it under `<h3>cost</h3>`. `skills/mf-review-metrics/SKILL.md`'s description and Report name cost.

### D2

`*("--strict-mcp-config",)` follows `*("--setting-sources", "user")`, its comment: no MCP server starts, the operator's own
included. No `--mcp-config` is passed.

### D3

`skills/mf-converge/references/worker.md` opens with one line — what a review, security or fix worker reads — then F4's worker parts,
moved whole, under their headings: `## Review and security` (Step 3's rules and Step 4, the anchors with it), `## Not clean`
(Step 5's station sentences), `## The verify pass` (Step 7's sentences on what a checker reads and runs, citing "the passes
above"), `## Catch-up scope` (whole: the enumeration, the checks and the checker paragraphs), `## The card`, `## Rules for tests`.
`SKILL.md` keeps the conductor's parts, each moved part a link: `[the card](references/worker.md#the-card)`, and The workers
(`:108`) tells the conductor to load `references/worker.md` too, for the frontmatter keys Step 5 reads and By rule writes, and the
card's size and Status Steps 8 and 9 read. `generic-review.md:8` and `generic-security.md:8` load
`[converge's worker reference](worker.md)`: Review and security, Not clean, The verify pass, Catch-up scope, The card and — for
review — Rules for tests, and their "per Step 5" and "per Step 7" (`generic-review.md:66`, `:71`;
`generic-security.md:47`, `:52`) name `## Not clean` and `## The verify pass`; `SKILL.md:108-109`, `:301` and Step 6
(`:408-412`) name it. Every anchor in `SKILL.md` to a moved heading is repointed to `references/worker.md#<heading>`: `#the-card` (`:301`, `:345`,
`:471`), `#rules-for-tests` (`:315`, `:412`), `#catch-up-scope` (`:187`, `:196`, `:207`, `:292`); the moved `:397`'s and `:319`'s
stay in `worker.md`, where `#catch-up-scope` resolves. The readers F5 names follow
the moves: the card owner and the converge test-rule carrier read `references/worker.md`; `_resource_problems` strips a
`#fragment` before it resolves a target; `tests/test_review_metrics.py:213-214` reads the worker reference; the prose lines name it.

### D4

`SETS["worker"] = (*SHARED, "THREAT_MODEL.md", "skills/mf-converge/references/worker.md",
"skills/mf-converge/references/generic-review.md")`, and `worker.md` joins `SETS["converge"]`, so the conductor's set stays whole.
`metrics/catalogue.toml` gains `id = "converge-worker-reading-set"`, `title = "Converge worker's reading set"`, `group =
"instruction load"`, `unit = "words"`, `better = "lower"`, `noise = 50`, `script = "scripts/metrics/reading_set.py"`, `args =
["worker"]` — `title` is required (`skills/mf-build/scripts/metrics.py:33`). The script's docstring names the `worker` set.

### D5

D50 reads "the findings files, status logs and run logs". D51's *Accepts* gains "a Claude worker starts no MCP server, the
operator's own included". `THREAT_MODEL.md:21-22` reads "…a project's settings and `.mcp.json` start nothing, and no MCP server
starts, the operator's own included; a Codex worker still starts the operator's `mcp_servers`."

## Tests

`git grep -c '^def test_' 6647909 -- tests/test_review_metrics.py tests/test_skills.py tests/test_metric_scripts.py` counts the
files at the cut. Added: `test_run_logs_give_cost_turns_and_tokens_per_station` (`tests/test_review_metrics.py`) — `T2`: no test
reads a run log — over a `_run_log` helper writing JSON lines: a converge log with two result events, a build log with none, a
Codex text log, and a run log naming two converge spawns. Extended: `test_the_page_draws_charts_and_lists_gaps` with the cost
table, its `lacked` lines re-read; `test_a_claude_worker_starts_in_the_sandbox` with `--strict-mcp-config` and no `--mcp-config`;
`test_reading_sets_count_words` with the `worker` set and the `converge` set's new count; the card-owner, test-rule and resource
scans' planted twins, at the new path. None deleted.

## Dependencies

None.

## Risks / Trade-offs

- **A worker misses a section it used:** generic-review's own list (`:8`) names what it loads; the review method's calibration is
  not re-run here.
- **The page's cost is list price:** the runs are on a subscription; the numbers rank, they do not bill.

## Verdict

Ready to build.
