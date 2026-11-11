# Cut diet — design

The cut gets one context pack and a scaffold from a script, waits on its reviews in the foreground, and drops the 1-hour cache. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The cut is the line's largest station, and most of its cost is reading and re-reading. Before it writes the proposal it reads the instructions of each artifact, archived changes as examples, the cited decisions, the living spec and the brief, and `cut_check.py`'s output twice. Its thinking is most of what it writes, and a third of its visible output reworks `design.md` and `tasks.md`.

The proposal restates the brief in a large part of its lines; the design's Context, Goals and Decisions table and `tasks.md`'s Progress lines and headings restate it too. The D sections, `## Tests`, Risks, sub-tasks, `Verify:` lines and spec scenarios are new. The design cannot point at the brief: build and converge workers cannot reach it, and a change may not name its path.

The cut runs on the 1-hour cache, set for waits on long Opus reviews. The reviews now run on Sonnet and take a few minutes. A review run in the background wakes the cut more than once, and each wake re-reads the whole context.

The code, read at `HEAD`:

```
facts.py        brief_facts(brief), place_all(facts, at), where(cite), write_notes(notes, lines, fresh)
bundle.py       decisions_text(plan, decisions)           [--decisions <file>]
debt_match.py   cards(debt), matched(card, changed)
brief_check.py  sections(brief), chosen(lines, name), main()  [--facts | --models <slug>]
cut_check.py    _selected(text, plan), row_v2(change, plan)
conduct.py      CACHE_HOUR = ("cut",); argv(): ttl = hour if station in CACHE_HOUR else 5-minute
SKILL.md        Step 2 gather · Step 6 write · Step 8.5 plan review (names no foreground or background)
```

## Goals / Non-Goals

**Goals:** a cut that reads one file for its context, writes only what the brief does not say, and wakes once; a cache that fits the waits it has.

**Non-Goals:** a cut model in code (a brief's models line carries the trial); the plan-metrics defects; a pack for a conversation source, which has no brief to read.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | the version holds the measured levers alone, a minor on debt `0113·S4` | each is a saving on every cut | more levers in one version |
| [D2](#d2) | Step 8.5 runs each plan review in the foreground and waits | a background review wakes the cut, and each wake re-reads its context | a background review with a poll |
| [D3](#d3) | the cut runs on the 5-minute cache, `CACHE_HOUR` goes, D80 and D70 are amended | the Sonnet reviews take minutes, and no gap of the cut passed the cache | the 1-hour cache |
| [D4](#d4) | `cut_context.py <brief> <change-id>` writes one context pack the cut reads once | the reads of the gather step become one | the cut reading each part |
| [D5](#d5) | `cut_context.py --scaffold` writes what the brief already says into the artifacts | workers cannot reach the brief, and a script cannot drift from it | the cut writing the parts again |
| [D6](#d6) | a Sonnet · medium cut trial rides in the next briefs' models lines, with no code | thinking is most of the cut's output | a cut model in code |
| [D7](#d7) | row `V2` evaluates a `-k` expression against each changed test name (`C1`, debt `0113·S4`) | the card is open for want of a red run, and a nested negation still halts | a regex that drops `not` and its operand |
| [D8](#d8) | `brief_check.py --sections` prints the brief's sections as JSON | `cut_context.py` stays free of a Markdown dependency | a `markdown-it-py` header on `cut_context.py` |
| [D9](#d9) | the skill's Steps 2, 6 and 8.5 follow the pack, the scaffold and the foreground rule | the scripts help only when the skill runs them | a script the skill never names |
| [D10](#d10) | `docs/decisions.md` amends D77, D80 and D70 where they live | [A7](../../../skills/mf-cut-change/SKILL.md#rules-for-the-artifacts): a decision in force is edited where it lives | a new decision beside them |

### D1

The levers are the measured ones: the context the cut gathers, the parts it writes again, and the waits on its reviews. The person's ledger holds the hypotheses, outside this repository, so no task builds them.

- **H21:** converge's plan-side blockers stay within the ledger's threshold under the Sonnet · medium trial, else the cut goes back to high.
- **H22:** a cut costs at most the ledger's target over the versions that follow.

### D2

Step 8.5 says each plan review runs in the foreground: the cut starts the worker and its next act is the result. A review that returns the host's background handle is not a review. The cut starts no background task for it, so nothing wakes it after its turn ends.

### D3

[`conduct.py`](../../../skills/mf-ship/scripts/conduct.py) drops `CACHE_HOUR` and the `ENABLE_PROMPT_CACHING_1H=1` string; every station that has one takes `FORCE_PROMPT_CACHING_5M=1`, the cut among them. The cut's subagents inherit it. D80 and D70 each name the cut's cache, and [D10](#d10) edits them.

### D4

The pack is `<run dir>/changes/<change-id>/context.md`, written by `cut_context.py <brief> <change-id>` from the worktree root, and `cut-notes.md` goes beside it. The run directory is `git rev-parse --path-format=absolute --git-common-dir` and `/../.minions`, the primary's from every worktree. A cite that fits no file at `HEAD` says so in the pack; every subprocess carries a timeout, as the gate's rule asks.

The script loads `facts.py` and `debt_match.py` as modules by `importlib`, as the tests load a script, and sets the loaded `facts.RUNNER` to its own, so one swap reaches both. A `facts.Stop` ends the run with its own code and message.

| part | from | form |
|---|---|---|
| `## The brief` | the brief file | verbatim |
| `## The facts at HEAD` | `facts.py`'s `brief_facts` and `place_all` | a `### <state> · <fact text>` heading, then each placed cite's lines at `HEAD` from `git show`, numbered, cut at `SLICE_LINES = 80` with a line saying where |
| `## The decisions` | `bundle.py --decisions <brief>` | its stdout, verbatim |
| `## The requirements the brief names` | `openspec/specs/*/spec.md` | each `### Requirement:` block whose title the brief holds, case apart; `None.` when none |
| `## Every requirement` | the same files | one line `<capability>:<line> · <title>` each, so the cut reads a block by its line |
| `## Debt cards` | the run directory's `debt.md`, through `debt_match.py`'s `cards` and `matched` | each card whose `What it affects` names a path a fact cites, and each card whose id the brief's item lists; `None.` when none or no file |
| `## The skeletons` | the `SKELETONS` constants | the A1 headings of the proposal, the design, the tasks and the spec delta, in order, and the OpenSpec form of a requirement and a scenario |

It writes `cut-notes.md` afresh through `facts.py`'s `write_notes`, a line a fact in the form of `facts.py place`, and prints `cut_context: pack — <path> · <n> facts, <k> unplaced`. Exit 0 when every fact is placed, 1 when one is unplaced, 2 when a file cannot be read or `brief_check.py` fails. The unplaced fact's cited lines are in the pack, so the cut reads it there; a helper starts only where those lines do not settle it.

The brief's item is the `## For the cut` item whose first part, stripped of `*` and backticks, is the change id without its number; its parts split on ` · `.

### D5

`cut_context.py <brief> <change-id> --scaffold` writes the files below in `openspec/changes/<change-id>/`, and none names the brief's path. It writes none and exits 1 when one of them exists or a phase has no rating. The title is the slug's words, the first capitalised: `cut-diet` → `Cut diet`.

| file | it writes | from |
|---|---|---|
| `proposal.md` | `bump:` frontmatter, then `after:`, `beside:`, `debt:` when the item lists one that is not `none`, as `[a, b]`; `# <Title>`; the brief's one line; `## Not in this change` | the item's parts; the bold line under the brief's title; the items of `## Not in this` |
| `design.md` | `# <Title> — design`; `## Decisions` with `\| id \| decision \| because \| rejected \|` and a row `\| [D<n>](#d<n>) \| <decision> \| <reason> \| — \|` for each `Q` or `C` row, a blank cell as `—`, a `—` row left out; `## Dependencies` | the brief's `## Decisions` and `## Dependencies` |
| `tasks.md` | `# <Title> — tasks`; `## Progress`, a line `- [ ] <n> — <title> · <rating>` per phase; a `## <n> — <title>` heading per phase | the brief's `## Phases` |

A phase starts at a line `<n>  <text>` in the brief's `## Phases` fence and runs over the lines indented below it; its title is those words with one space between them, up to a last ` · hard` or ` · moderate`. `## Dependencies` is `None.` when the brief's says so or lists no row for the slug, else the rows for the slug as `\| package \| constraint \| why \|`.

The cut writes the rest by `Edit`: the reading map, Why, What Changes, Capabilities and Impact before `## Not in this change`; the one line, Context and Goals around `## Decisions`; the `### D<n>` sections, `## Tests`, Risks and Verdict around `## Dependencies`; the sub-tasks under each phase heading. Rows the cut rewords or drops follow `K3`: the table and the `### D` headings keep one order.

### D6

No task. A brief's models line names the cut's model as `cut <model> <effort>`; the briefs planned after this change carry `cut claude-sonnet-5-5 medium` until the ledger says otherwise. **H21** of [D1](#d1) puts it back to high on evidence.

### D7

`_selected(text, plan)` returns the `-k` expression of each `pytest` command of a sub-task text. A new `selects(expression, name)` in `cut_check.py` returns whether the expression picks the test `name` by a positive match, and `row_v2` halts when it does for a `test_` name in the text of a later sub-task that adds, removes, merges or renames.

- **Reading:** an identifier is true when the lowercased name holds it; `not` binds tighter than `and`, and `and` tighter than `or`; parentheses group, to any depth.
- **A positive match:** the expression is true for the name, and an identifier outside every `not` holds in it. `not widget` therefore picks no later test, while `not widget and gadget` picks `test_gadget`.
- **Unparsable:** an expression it cannot parse picks nothing, and the reviewer reads it.
- **The message:** `<task>: \`-k <expression>\` selects a test that <later> changes`.

The card's own case, `not widget`, already passes at `HEAD`: a fix commit dropped the negated term for one level of parentheses. A nested case still fails: `not (a and (b) and d)` leaves `d` behind, so a later `test_d` halts. The new tests go through `row_v2`, so that case is red at `HEAD`; the build records that red run in the phase's commit body, as [T6](../../../skills/mf-cut-change/SKILL.md#rules-for-tests) asks.

### D8

`brief_check.py --sections <brief>` joins `--facts` and `--models` in the mutually exclusive group and prints `json.dumps(sections(brief))`: an object from each `# ` or `## ` heading line to the lines under it. It returns beside `--facts`, before `main` requires `verify_check.py` and `conduct.py`. The first key that starts `# ` holds the bold one line. `cut_context.py` runs it by `RUNNER` as `facts.py` runs `--facts`, and a test swaps `RUNNER` for the interpreter.

### D9

`skills/mf-cut-change/SKILL.md` changes its reading step and Steps 2, 6 and 8.5.

- **Reading step:** for a brief, the pack holds the cited decisions and the index that `bundle.py --decisions` prints, and the step keeps naming that command.
- **Step 2:** for a brief the cut runs `cut_context.py <brief> <change-id>` in place of `facts.py place`, reads the pack once, and reads the code of an unplaced fact from it.
- **Step 6:** the cut runs `cut_context.py <brief> <change-id> --scaffold` first, writes the rest into the files, and takes the skeletons from the pack in place of `openspec instructions` and archived changes read as examples.
- **Step 8.5:** each review runs in the foreground.
- **A conversation source** has no brief, so it keeps the old reading and `facts.py place`.

### D10

Edits to `docs/decisions.md`, each where the decision lives.

- **D77** names the context the cut reads and the scaffold of its artifacts among the scripts, and adds a rejected line: the cut reading archived changes as examples.
- **D80** replaces its last bold sentence, `The cut keeps the 1-hour cache.`, with `Each review runs in the foreground, the cut waiting on it, and the cut runs on the 5-minute cache with its reviews.`; its rejected line drops the 5-minute cache and names a background review and the 1-hour cache.
- **D70** reads `Every station asks for the 5-minute cache.` in place of its sentence `The cut asks for the 1-hour cache, every other station the 5-minute one.`, its Why reads `no station's wait outlasts 5 minutes`, and it accepts that a review past the cache's lapse re-writes the cut's context.

## Tests

All new tests are unit tests, in scratch repositories and with `RUNNER` swapped for the interpreter, as the facts tests do; no end-to-end run is added and none is deleted. [T1](../../../skills/mf-cut-change/SKILL.md#rules-for-tests) puts each at the lowest layer.

| file | added | by |
|---|---|---|
| `tests/test_cut_context.py` | a test for each part of the pack, the pack's exit codes, each artifact of the scaffold and its refusals | [D4](#d4), [D5](#d5) |
| `tests/test_brief_check.py` | `test_the_sections_flag_prints_each_section_as_json` | [D8](#d8) |
| `tests/test_cut_check.py` | `test_a_k_expression_selects_by_pytests_rules`, and a nested and a negated case through `row_v2` | [D7](#d7) |

Existing tests the change turns red, and the tasks mend them:

- `tests/test_conduct.py`'s `test_every_station_starts_lean` expects the cut on `ENABLE_PROMPT_CACHING_1H=1`: it expects `FORCE_PROMPT_CACHING_5M=1` ([D3](#d3)).
- `tests/test_cut_check.py`'s `test_a_search_names_its_literal_needle` asserts on the words `_selected` returned: its assertions assert the expressions it now returns, and `test_a_k_expression_selects_by_pytests_rules` carries the same cases as a selection ([D7](#d7)).
- `tests/test_skills.py` requires each station to name its scripts: `cut_context.py` joins its list and the unnamed-script lists ([D9](#d9)).

## Dependencies

None.

## Risks / Trade-offs

- A pack read at `HEAD` is stale if `HEAD` moves before the commit. The cut is short and the run holds the worktree, and the plan review reads `HEAD`'s sha.
- The scaffold copies a brief's row text, numbers included; a `P12` count there is the cut's to rewrite, and `cut_check.py` still judges it.
- The skeleton replaces `openspec instructions`; a change in the CLI's artifact form is caught by `openspec validate --strict` at Step 7, as before.
- A review that runs past the 5-minute cache re-writes the cut's context once at the dearer rate; **H22** of [D1](#d1) measures it.

## Verdict

Ready: every file the phases edit exists at `HEAD`, every script they call exists, and no decision of the brief is left open. The cutter's `C1`, which [D7](#d7) carries, is the item a person may want to read.
