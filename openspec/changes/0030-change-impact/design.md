# Change impact — design

A repository that declares its metrics gets them measured at every change by one deterministic script, kept as one
data file per release, and charted on a generated page. Verdict: ready to build. Scope is
[the proposal](proposal.md); behaviour is [the delta](specs/sdd/spec.md).

## Context

Premises were re-checked on `main` at `8c88e90` (v0.29.0) before the cut.

| evidence at the cut | implication |
|---|---|
| MF has no `metrics/`, no `scripts/` and no shipped code: `git ls-files metrics scripts` prints nothing | every path below is new ([D1](#d1)) |
| `skills/mf-build/SKILL.md:168` *Step 3 — Close with the simplify pass*, `:183` *Step 4 — Report, then stop*, its sentences at `:188-189` | the build's metrics step is a new `## Step 3.5`, so no step renumbers ([D6](#d6)) |
| `skills/mf-release/SKILL.md:134` *Step 4 — Cut the version line*: item 2 the version file (`:151`), item 3 the gate (`:154`), item 4 the commit (`:160`); `Step 4.1`, `4.3` and `4.4` are cited at `:69,131,200,207` | the release's step is item **2b**, so every cited number holds ([D6](#d6)) |
| D2 (`docs/decisions.md:30-36`): *the stations install nothing into the repo they work on* | a script bundled in a skill package is new; D2 says it may be ([D8](#d8)) |
| D18's tree (`docs/decisions.md:224-231`) is parsed by `_layout_entries` (`tests/test_skills.py:252`), and each entry needs a bootstrap template | `metrics/` is named in a line under the tree, not in it ([D8](#d8)) |
| `requires-python = ">=3.12"`; `uv` 0.12.19 runs the gate; `python3` on `PATH` is 3.14, `/usr/bin/python3` 3.9 | the script is a `uv` script pinned to `>=3.12`, never the system Python ([D2](#d2)) |
| The installed `mf-*` skills under `~/.agents/skills/` and `~/.claude/skills/` are frozen copies of `v0.29.0`, made 2026-10-27 | this change's build and release run v0.29.0's stations; the build demonstrates the collector itself ([D9](#d9)) |
| `uv run pytest --collect-only -q \| tail -1` prints `18 tests collected` | the test count before ([Tests](#tests)) |

## Goals / Non-Goals

**Goal:** a person opens one page per change and sees which measured property moved, and whether this change or
older debt put it past its line — every number printed by a command, none by an agent.

**Non-goals:** see [the exclusions](proposal.md#not-in-this-change).

## Decisions

The grilling settled these choices; the build does not reopen them.

### D1

| id | decision | because | rejected |
|---|---|---|---|
| D1 | The catalogue is the switch; the build's values are a draft in `.minions/`, the release's are the record in `metrics/changes/`; the page is generated, never tracked | Opt in once; the release measures what ships, so no freshness check; data is the record, the page a view | Defaults run uninvited; a tracked page; a freshness check on stale values |

```
<target>/
├── metrics/catalogue.toml               what this repo measures — present ⇔ it has adopted
├── metrics/changes/<change-id>.json     the shipped values, one per release, written once
└── .minions/metrics/<change-id>.json    the build's draft · <change-id>.html, the page — gitignored
```

### D2

| id | decision | because | rejected |
|---|---|---|---|
| D2 | One collector, `skills/mf-build/scripts/metrics.py`, standard library only, run as `uv run --script`, its PEP 723 header pinning `requires-python = ">=3.12"` | An agent transcribing values or drawing SVG eventually invents a number; one pinned Python everywhere | The system `python3`; Node; a script per station |

**Interface:**

```
metrics.py collect --change <id> --base <rev> --out <path> [--value <metric-id>=<number> …]
                   [--executor <text>] [--model <text>]
metrics.py page <id> [--data <path>] [--out <path>]
     --data defaults to metrics/changes/<id>.json; --out to .minions/metrics/<id>.html
```

| exit | means | the station |
|---|---|---|
| 0 | written | carries on |
| 2 | the catalogue is broken; stderr names the entry | halts, naming it |
| 3 | no `metrics/catalogue.toml`; stdout `metrics: none — no catalogue` | states the line, skips the step |
| any other | the collector crashed | halts |

**The seam:** `metric_argv(script, args)` builds `["uv", "run", "--script", script, *args]`; unit tests replace it
with `[sys.executable, script, *args]`, and one test runs the real `uv` path.

### D3

| id | decision | because | rejected |
|---|---|---|---|
| D3 | A `[[metric]]` declares `id`, `title`, `group`, `unit`, `better`, optional `watch` and `noise`, and `script` + `args` or `source = "station"`. A metric script is Python, run without a shell from the root, 300 s timeout; the last stdout line is the number, anything else `unavailable` with its reason | The same on every machine; a failing metric never fails the station | A shell command; any program; a metric failing the station |

```toml
[[metric]]
id = "converge-reading-set"
title = "Converge conductor's reading set"
group = "instruction load"
unit = "words"
better = "lower"
watch = 10500
noise = 50
script = "scripts/metrics/reading_set.py"
args = ["converge"]
```

**A metric script sees** `MF_METRICS_CHANGE` (the change id), `MF_METRICS_BASE` and `MF_METRICS_HEAD` in its
environment. **`unavailable`'s reason** is the first stderr line, else `exit <code>`, `no number on the last line`
or `timed out after 300 s`.

**Station values** (`source = "station"`): `gate-seconds` is passed with `--value`, from the release's precondition
1 run; the build passes none, so its draft records it `unavailable` — *not passed by the station*. `diff-lines`
(insertions plus deletions over `<base>..HEAD`, `metrics/` excluded), `diff-files` and `phases` (the `## Progress`
lines of the change's `tasks.md`, active or archived) are derived by the collector itself from `--base`: the cut
settles this detail of Q39, so no station copies a number by hand.

**A broken catalogue:** TOML that does not parse; a missing required field; an `id` repeated; `better` other than
`lower` or `higher`; both or neither of `script` and `source`.

### D4

| id | decision | because | rejected |
|---|---|---|---|
| D4 | The data file records its revisions and provenance; a missing value is `unavailable` with why, never dropped and never zero | The data must say where it came from; a gap is honest | Values only; `0` for missing |

```json
{
  "change": "0030-change-impact", "version": "v0.30",
  "base": "8c88e90", "analyzed": "<HEAD's short sha>", "measured_on": "local",
  "collected_at": "2026-10-27T16:40:00+02:00",
  "mf_version": "v0.29.0-14-g<sha>", "executor": "native (Claude Code)", "model": "claude-opus-5-5",
  "values": {
    "converge-reading-set": { "value": 10031 },
    "gate-seconds": { "status": "unavailable", "why": "not passed by the station" }
  }
}
```

`version` is read from the change's `proposal.md` (`openspec/changes/<id>/`, else `openspec/changes/archive/<id>/`).
`mf_version` is `git describe --tags --always --dirty` in the directory the collector's own path resolves to, else
`unknown`. `executor` is what executor selection reported; `model` is the station's own report, else
`unidentified`. `measured_on` is `local` in this version.

### D5

| id | decision | because | rejected |
|---|---|---|---|
| D5 | Each metric is classified against the previous release; the page leads with what moved, then a line per metric | Movement apart from level; the table says where to look, the chart explains it | A score; charts first |

**Previous** is the tracked data file in `metrics/changes/` whose `version` is the highest below this change's,
versions compared as numbers (`v0.9` < `v0.10`).

| state | when |
|---|---|
| **crossed here** | the previous value on the good side of `watch`, this one past it |
| **worsened** | the change beyond `noise`, the wrong way by `better` |
| **over** | both past `watch` |
| **back under** | the previous past `watch`, this one on the good side |
| **improved** | the change beyond `noise`, the right way |
| **steady** | \|Δ\| ≤ `noise` (`0` when unset) |
| **new** | no previous value |

A metric past `watch` is classified by its watch state first — crossed here, over, back under — then by movement.
*What moved* lists crossed here, worsened, over, then the rest.

**The page** — one HTML file, inline SVG, no script, no network: a header (change, version, base, analyzed,
provenance, links to `proposal.md` and `design.md`, the archive path once released); *what moved* (metric,
previous, now, Δ, state); then per `group`, a small line chart per metric — x by version, `watch` dashed, this
change highlighted, an `unavailable` value a gap.

### D6

| id | decision | because | rejected |
|---|---|---|---|
| D6 | The build collects a draft at a new Step 3.5 and names the page; the release collects at item 2b of Step 4 and commits the file | The person decides before converge; the release records what ships, inside its gated commit | Collection in converge; a release that renders only |

**`skills/mf-build/SKILL.md`** — a new section between *Step 3 — Close with the simplify pass* and
*Step 4 — Report, then stop*:

```markdown
## Step 3.5 — Collect the metrics

No `metrics/catalogue.toml` → state `metrics: none — no catalogue` in your report, and skip this step. Otherwise,
after Step 3's commit or no-op, from the repository root:

1. `uv run --script <this package>/scripts/metrics.py collect --change <change-id> --base <base>
   --out .minions/metrics/<change-id>.json --executor "<what executor selection reported>"
   --model "<your model, or unidentified>"`, where `<base>` is `git merge-base <default-branch> HEAD`.
2. `uv run --script <this package>/scripts/metrics.py page <change-id> --data .minions/metrics/<change-id>.json`
   writes `.minions/metrics/<change-id>.html`.

| exit | then |
|---|---|
| 0 | carry on |
| 3 | state `metrics: none — no catalogue` |
| 2 | **halt**, naming the entry it printed |
| any other, or `uv` missing | **halt**, naming it |

A metric `unavailable` is not a halt, and **a watch never halts the build**: the page is the person's, who decides
before converge.
```

Its *Your sentences* gain: *the metrics page and its counts of crossed here and worsened, or `metrics: none — no
catalogue`*.

**`skills/mf-release/SKILL.md`** — in *Step 4 — Cut the version line*, after item 2:

```markdown
   **2b. Metrics.** No `metrics/catalogue.toml` → record `metrics: none — no catalogue`. Otherwise, from the
   repository root: `uv run --script ../mf-build/scripts/metrics.py collect --change <change-id> --base <base>
   --out metrics/changes/<change-id>.json --value gate-seconds=<precondition 1's seconds>
   --executor "<what you identified>" --model "<your model, or unidentified>"` — `../mf-build/` resolved from this
   skill's package, `<base>` as in precondition 8. Exit 2, any other non-zero exit, a missing script or a missing
   `uv` → **halt**, nothing committed. Stage `metrics/changes/<change-id>.json` by name.
```

Item 4's list gains *the metrics data file*; *Your sentences* in Step 6 gain *the metrics data file, or `metrics:
none — no catalogue`*.

### D7

| id | decision | because | rejected |
|---|---|---|---|
| D7 | MF's catalogue: instruction load, the contract, proof, clarity, conformance, debt; its scripts in `scripts/metrics/`, standard library, PEP 723 headers, unit-tested | MF's product is instructions; these say whether they stay clear, small and followed | Undefined terms (not deterministic); converge rounds (dropped at the grilling) |

| id | group | unit | better | watch · noise | how |
|---|---|---|---|---|---|
| `converge-reading-set` | instruction load | words | lower | 10500 · 50 | `reading_set.py converge`: words of `AGENTS.md`, `docs/principles.md`, `docs/decisions.md`, `skills/mf-converge/SKILL.md` |
| `shared-context` | instruction load | words | lower | — · 50 | `reading_set.py shared`: the first three |
| `rule-ids` | contract | ids | lower | — | `rule_ids.py`: distinct bold first-cell ids `I`, `P`, `T`, `W`, `C`, `A` across `skills/*/SKILL.md` |
| `tests-collected` | proof | tests | higher | — | `tests_collected.py`: `uv run pytest --collect-only -q`, the number before `tests collected` |
| `gate-seconds` | proof | seconds | lower | — · 5 | `source = "station"` |
| `hedge-words` | clarity | words | lower | — | `prose.py hedge`: *should*, *might*, *appropriately*, *as needed*, *if possible*, *etc.*, *probably*, *typically*, *generally*, *various* — whole words, any case |
| `long-sentences` | clarity | sentences | lower | — | `prose.py long`: sentences over 30 words |
| `broken-references` | clarity | references | lower | 0 | `references.py`: links in `AGENTS.md`, `README.md` and `docs/*.md` to a missing file or heading; and `D<n>` cited in `AGENTS.md` and `docs/*.md` with no `### D<n> ·` heading |
| `commits-without-trailer` | conformance | commits | lower | 0 | `conformance.py trailer`: commits in `<base>..HEAD` whose `Change` trailer is not the change id |
| `minions-files-tracked` | conformance | files | lower | 0 | `conformance.py minions`: `git ls-files .minions` |
| `amends` | conformance | commits | lower | — | `conformance.py amends`: subjects `docs(<id>): amend the change directory` in `<base>..HEAD` |
| `open-backlog-cards` | debt | cards | lower | 10 | `backlog.py`: lines `- **<4 digits>·` in `.minions/backlog.md`; no file → `unavailable` |

`prose.py` reads `skills/*/SKILL.md` and `skills/*/references/*.md`, outside fenced code, inline code and table
rows; a sentence ends at `.`, `!` or `?` before a space or the paragraph's end. Skill text's example links —
`[design](design.md)` — are not references, so `references.py` reads the docs, not the skills.

### D8

| id | decision | because | rejected |
|---|---|---|---|
| D8 | Record it where it lives: D43 for the design; D2 allows a bundled script; D18 names `metrics/` optional; `AGENTS.md`, `README.md` and `docs/README.md` name the new paths | `A7`; `W6` | A design-only record |

D43, in *The check loop and the release*, after D40; the overview's `D11…D17, D40` becomes `D11…D17, D40, D43`:

```markdown
### D43 · Project health is measured per change, from the repo's own catalogue

**A repo that adopts declares its metrics in `metrics/catalogue.toml`. The build collects a draft after simplify,
for the person to read before converge; the release collects on its final tree and commits
`metrics/changes/<change-id>.json`. One bundled script collects and renders; each metric is a Python script it
runs without a shell; the page is generated from the data, never tracked. No catalogue, no metrics, and the
station says so.**

- **Why:** the gate proves a project works, not where it is heading; every number comes from a command, never from
  an agent.
- **Rejected:** an analysis platform — the repo would report outward · a narrative report — a prose copy drifts ·
  a tracked page — a view is regenerable · metrics run on a repo that declared none.
```

D2's bold sentence gains: *A skill may bundle a standard-library script, run from its own package and never copied
into the target ([D43](#d43--project-health-is-measured-per-change-from-the-repos-own-catalogue)).* D18 gains, under
its tree: *`metrics/` is optional: a repo that adopts holds its catalogue and its data files there (D43); the
bootstrap writes none.*

`AGENTS.md`'s layout gains `metrics/` (MF's catalogue and data files) and `scripts/metrics/` (its metric scripts),
and records `uv` as what runs the bundled script, as it records the OpenSpec CLI. `README.md`'s *What a target repo
needs* names `metrics/catalogue.toml` as optional; `docs/README.md`'s *Where the rest lives* gains `metrics/` and
`scripts/metrics/`, and its `skills/` row the bundled metrics script.

### D9

| id | decision | because | rejected |
|---|---|---|---|
| D9 | MF adopts itself; the build demonstrates the collector and the page on MF; MF's first tracked data file comes with the release after the skill links are reinstalled. Converge runs | The installed stations are v0.29.0's until then; a new code path earns the check loop | Reinstalling the links mid-change, which shows unreleased skills to other projects |

## Tests

The gate stays offline: the unit tests use `tmp_path` repositories and replace `metric_argv`; one test runs the
real `uv run --script` path over a metric script with no dependency.

| layer | at cut | added | removed | proof |
|---|---:|---:|---:|---|
| Unit test functions | 18 | 17 | 0 | `uv run pytest --collect-only -q \| tail -1` prints `18 tests collected` at the cut, `35 tests collected` after |
| Integration tests | 0 | 0 | 0 | — |
| End-to-end runs | 0 | 0 | 0 | — |

| test, added | file | holds |
|---|---|---|
| `test_collect_writes_a_value_per_metric` | `tests/test_metrics.py` | each declared metric gets a value; the real `uv run --script` path |
| `test_a_failing_metric_is_unavailable_with_its_reason` | the same | non-zero exit, no number, timeout |
| `test_no_catalogue_exits_3_and_says_so` | the same | the switch |
| `test_a_broken_catalogue_exits_2_naming_the_entry` | the same | parse, missing field, repeated id, bad `better`, both or neither of `script` and `source` |
| `test_station_values_are_passed_or_derived` | the same | `--value`, the git-derived ones, an unpassed one `unavailable` |
| `test_the_states_against_the_previous_release` | the same | every row of D5's table |
| `test_previous_is_the_highest_version_below` | the same | `v0.9` < `v0.10`; no previous → new |
| `test_the_page_leads_with_what_moved_and_shows_gaps` | the same | the order; a gap, never zero; no `<script>` |
| `test_provenance_is_recorded_never_guessed` | the same | `unknown`, `unidentified`, the revisions |
| `test_reading_sets_count_words` | `tests/test_metric_scripts.py` | `reading_set.py` |
| `test_rule_ids_are_counted_once` | the same | `rule_ids.py` |
| `test_prose_skips_code_and_tables` | the same | `prose.py`: hedge words, long sentences |
| `test_broken_references_find_files_headings_and_ids` | the same | `references.py` |
| `test_conformance_counts_trailers_amends_and_minions` | the same | `conformance.py`, in a `tmp_path` git repo |
| `test_backlog_cards_are_unavailable_without_a_backlog` | the same | `backlog.py` |
| `test_the_stations_run_the_bundled_metrics_script` | `tests/test_skills.py` | `mf-build` names `scripts/metrics.py` and `mf-release` names `../mf-build/scripts/metrics.py`, each resolving to a nonempty file |
| `test_the_metrics_script_scan_reports_a_missing_script` | the same | its twin (`W5`, `T6`) |

Planned addition count: ``grep -cE '^\| `test_[a-z0-9_]+` \| `?(tests/|the same)' openspec/changes/0030-change-impact/design.md`` prints `17`.

## Dependencies

None.

## Risks / Trade-offs

- **A metric script is code the station runs** → it is the repo's own, reviewed like the gate's recipe, and runs
  without a shell; a branch that loosens a metric shows in the reviewed diff.
- **Local values are not comparable with CI's** → `measured_on` is `local` in this version; the page compares like
  with like.
- **The page renders charts by hand-written SVG** → one function per chart, unit-tested on structure; no chart
  library.
- **`tests-collected` runs pytest inside the collector** → seconds on MF; a slow metric hits its timeout and is
  `unavailable`, never a halt.
- **The stations run v0.29.0 during this change** → the build demonstrates on MF itself (phase 4); the first
  tracked data file waits for the reinstall.

## Migration Plan

```
1 the collector + its tests ─▶ 2 MF's catalogue + metric scripts ─▶ 3 the stations' steps
  ─▶ 4 the records + the demonstration ─▶ simplify ─▶ converge ─▶ release
```

Each phase ends on a green gate. Nothing is irreversible: a phase reverts with its commit.

## Verdict

Ready to build. Acceptance: the tests above, a draft data file and a page for this change on MF itself, and the
stations' new steps naming the bundled script.
