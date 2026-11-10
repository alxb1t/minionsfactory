# Gate hardening — design

How the gate takes a wider lint, a timeout rule and a docstring check, and how converge hands every worker the facts a tool
found. Verdict: the gate rules land first, each in the phase that cleans for it; the evidence lands last, and acts from the next
version.

Read [proposal](proposal.md) for why, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the requirements.

## Context

Facts at `8c2ea64`, `HEAD` at the cut. `K` is `skills/mf-converge/scripts/converge.py`, `C` `skills/mf-ship/scripts/conduct.py`,
`W` `skills/mf-converge/references/worker.md`. Lines are `HEAD`'s, from the cut's notes.

| id | fact | where |
|---|---|---|
| F1 | the gate runs `uv sync --locked`, ruff format and check, `ty`, `zizmor`, `betterleaks`, the tests under coverage and `diff-cover --fail-under=100`; `make check` runs the fast steps | `Makefile:13-29` |
| F2 | ruff selects `E F I D ANN B S`; `S603` and `S607` are ignored in `per-file-ignores` `"**"`, `D` and `S101` in `"tests/**"`, so a command-line `--select` keeps them | `pyproject.toml:22-50` |
| F3 | `gate_check.py` reads makefiles and dry runs only: a ruff `select` edit or a new `# noqa` passes it unseen | `skills/mf-converge/scripts/gate_check.py:14-18` |
| F4 | `subprocess.run` calls in `skills/` and `scripts/` mostly pass no `timeout=`; `C` passes one on each call | `scripts/corpus.py:33`, `K:295`, `skills/mf-converge/scripts/gate_run.py:43`, `C:381` |
| F5 | `freeze()` writes `diff.patch`, `bundle.md` and `debt-cards.md`, stamps `freeze`, and runs before any dispatch: round 1, each re-freeze, a catch-up | `K:432-462` |
| F6 | a `## Prompt` is filled from `PLACEHOLDERS`; a name outside the tuple, or a placeholder left unfilled, raises; `test_each_worker_prompt_is_filled_from_its_reference` holds every reference to the tuple | `K:57-63`, `K:475-494`, `K:1946-1987`, `tests/test_converge.py:489-501` |
| F7 | `W` says `converge.py` judges nothing; its stale-claim, test-cost and coverage-trace passes each have a mechanical half and a judgment half; `diff-cover` reads changed lines only, so it cannot carry coverage-trace | `W:12`, `W:15-21`, `Makefile:23` |
| F8 | `plan_check.py` runs at Step 7 and the build's close, and `planned()` after a fix, never before round 1 | `K:1063-1080` |
| F9 | the sandboxed gate runs `uv sync --locked` with `UV_OFFLINE=1` and `UV_CACHE_DIR` the run's `.minions/uv-cache`: a dev dependency not in the cache turns converge's precondition gate red | `C:3318-3319` |
| F10 | the docstring cards `0099·R5`, `0103·R4`, `0106·R3`, `0109·R1` and `0108·R9` share a cause: no check holds `C7`, and `0108·R9` is a dispute over whether a blank line counts | `skills/mf-build/SKILL.md:390` |
| F11 | `conduct.py cut` reads the brief's packages through `_approval`, takes the queue lock, then reserves; its `sandboxed()` runs the gate with no network | `C:7118-7132`, `C:7220-7304`, `C:3291-3342` |

Measured at the cut, on a scratch run of the checks as designed:

| measurement | command | result |
|---|---|---|
| the wider families' hits | `uv run ruff check --extend-select UP,ERA,PERF,SIM,RET,PT,RUF,PLE,PLC,PLR,PLW,BLE --ignore RUF001,RUF002,RUF003,RUF005,PLR0911,PLR0912,PLR0913,PLR0915,PLR0917,PLR2004,PLW1510 --output-format concise --no-cache .` | 162 lines; the rest, outside `PT018` in `tests/`, are the sites to clean: `RUF043` in tests, `BLE001` in `C`, `RET502`, `SIM102`, `PLC0207`, `PLE2515` |
| docstrings over 3 non-blank lines | an `ast` walk, `ast.get_docstring(node, clean=False)`, over `git ls-files '*.py'` | `skills/` 172 · `scripts/` 8 · `tests/` 10 |
| docstrings over 3 lines, a blank line counted | the same walk | `skills/` 336 · `scripts/` 17 · `tests/` 35 |

## Goals / Non-Goals

**Goals:** each rule a tool can hold is a line of the gate, with its sites cleaned in the phase that adds it; each fact a tool
can find reaches the checkers in one file; the offline sandboxed gate finds the new dependency.

**Non-Goals:** a checker that judges less than it does now (the judgment halves stay, [D8](#d8)); a gate that reads
`pyproject.toml` for a ratchet; `TRY`, `C901` and `PLR09` as gates; the plan review diet.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | `pyproject.toml` gains `extend-select = ["UP", "ERA", "PERF", "SIM", "RET", "PT", "RUF", "PLE", "PLC", "PLR", "PLW", "BLE"]` under `[tool.ruff.lint]`. The ignores go in `per-file-ignores`, as F2's comment says: `"**"` gains `RUF001 RUF002 RUF003 RUF005 PLR0911 PLR0912 PLR0913 PLR0915 PLR0917 PLR2004 PLW1510`, `"tests/**"` gains `PT018`. Each site is cleaned in the phase that turns it on; each deliberate `except Exception` carries `# noqa: BLE001` on its line and `# why: <reason>` on the line above | the measured hits are real (`RUF043`: a test regex with an unescaped dot matches more than it says; `BLE001`: a swallowed error in `C`) and the noise is ignored by name; `C2` allows a comment for a tool directive and its why | `select` for the ignores: a command-line `--select` would drop them · `TRY`: churn against `Stop(f"…")` · `C901` as a gate: a [D43](../../../docs/decisions.md#d43--project-health-is-measured-per-change-from-the-repos-own-catalogue) metric |
| <a id="d2"></a>**D2** | `scripts/docstrings.py` is a `uv` script that reads each tracked or new Python file (`git ls-files --cached --others --exclude-standard -- '*.py'`) by the `ast` and prints `<path>:<line>: <what>` for each docstring of a module, class or function that **runs over 3 non-blank lines** (`C7`) or whose **first line is not one sentence** (`C3`: it reads `. ` then a capital before its last character); exit 1 on any, 0 on none. The gate and `make check` run it; `CODING_STANDARDS.md` says how it counts | a blank line is spacing, not text, so the fixer's reading of `0108·R9` stands and the script ends the dispute; `D` and `ANN` already hold the first line's period and mood | counting a blank line: it flags many sites that read short · ruff's `pydocstyle`: it has no line limit · a scan of comments: the cards are about docstrings |
| <a id="d3"></a>**D3** | `ast-grep-cli>=0.51.1,<0.52` is a dev dependency. `sgconfig.yml` names the rule folder `sg-rules/`, and its one rule, `subprocess-run-needs-timeout` (`severity: error`, files `skills/**` and `scripts/**`), matches a `subprocess.run(…)` call with no `timeout=` keyword. The gate and `make check` run `uv run ast-grep scan`. Each site gets `timeout=` of a module constant `TIMEOUT_SECONDS = 600`, reusing a module's own, save the `make gate` call of `gate_run.py`, which gets `GATE_SECONDS = 3600`. A timeout is not caught at a site: it ends the script with a traceback instead of a hang. The ratchet is a convention: a repeat card of a syntactic class becomes a rule at the next paydown | ruff cannot say it, and an unattended run hangs on a call with no timeout; a new handler is a new changed line, and each would need a test under `diff-cover`'s 100% | a ruff rule: none exists for `timeout=` · a `grep` in a test: it reads no syntax · a handler at every site: it is churn, and `C` already maps its timeouts to `Stop` |
| <a id="d4"></a>**D4** | `conduct.py cut` calls `_prefetch(primary, rows)` after `primary_of` and before the queue lock. For each approved row it checks the package against `[A-Za-z0-9][A-Za-z0-9._-]*` and the constraint against a plain specifier (it starts with `<`, `>`, `=`, `!` or `~` and holds `[<>=!~,.0-9A-Za-z*+ -]` alone, no `@`, `:` or `/`), and refuses the rest, a bare version such as `1.3.0` included — joined to the name it would read as another package — exit 2, naming the row. It runs `uv pip install --no-config --no-build --default-index https://pypi.org/simple --target <scratch> <package><constraint>` with `UV_CACHE_DIR` the primary's `.minions/uv-cache`, no `UV_*` or `PIP_*` name of the person's environment, and `timeout=PREFETCH_SECONDS` (600); a non-zero exit stops with 2, naming the package, before any reservation. The scratch is under `.minions/tmp` and removed after | the person is present and approving at the cut; a sandboxed worker has no network (F11), so the cache must hold the wheel first; `--no-build` runs no package code; the index, `--no-config` and the scrubbed environment keep the fetch on PyPI's hosts | a fetch in the sandboxed gate: no network there · a URL allowed on `files.pythonhosted.org`: a plain name needs none · a prefetch at `rejoin`: [Not in this change](proposal.md#not-in-this-change) |
| <a id="d5"></a>**D5** | `skills/mf-converge/scripts/gate_integrity.py` reads a patch and prints one line for each fact below, `<kind> · <path>:<line> · <text>` (text stripped, cut at 120 characters), or `None.`; `lines(patch)` returns them, and `main` prints them, exit 0, and 2 on an unreadable patch. A line removed and added again in the same file is a move: no line. The kinds, of an **added** line: `noqa` (`# noqa`), `type-ignore` (`# type: ignore`, `# ty: ignore`), `no-cover` (`# pragma: no cover`), `skip` (`pytest.mark.skip`, `pytest.mark.skipif`, `pytest.skip(`), `xfail` (`pytest.mark.xfail`, `pytest.xfail(`), `allowlist` (a line of `.betterleaks.toml` that is no blank or comment), `swallow` (an `except …:` followed by a `pass`, on one line or the next); of a **removed** line: `test-removed` (`def test_`), `assert-removed` (`assert`); of either: `pyproject` (a line of `pyproject.toml` that is no dependency, no `version =` and no blank). The case `gate-integrity` of `scripts/corpus.toml` runs it over each frozen patch of the run directory | `gate_check.py` cannot see these (F3), and conformance's gate-integrity section was a hand search for them; `0034·R9`'s class is a gate setting the check cannot see | a parser of `pyproject.toml`: the patch holds the changed lines already · counting the lines in `converge.py`: it judges nothing ([D8](#d8)) |
| <a id="d6"></a>**D6** | `skills/mf-converge/scripts/evidence.py` builds the rest of `evidence.md` from the patch and from the commands `converge.py` runs, and `freeze()` writes the file after `debt-cards.md` and before the stamp, in the shape under *The shape of `evidence.md`*. It runs `plan_check.py --change <id> --base <context.base>` and, when a candidate name stands, one `git grep -n -w -F` over the candidate names, each through `_captured`, so each runs sandboxed and in the command log; a command's exit is no halt, its output the section. Each section holds at most `LIMIT` lines, then `… <n> more`. The test seconds are read from `.minions/test-report.xml` by a pattern, never an XML parser (`S314`) | every round's checkers start from the same facts (F5); a freeze is the one place all of them pass, round 1 and each re-freeze | an LLM step to gather them: it is what the script replaces · a new freeze event: the status log's events stay as they are |
| <a id="d7"></a>**D7** | `evidence` joins `PLACEHOLDERS`, and its value is the path of `evidence.md`, given by `checker_prompt`, `verify_prompt` and `fixer`; each of `generic-conformance.md`, `generic-adversarial.md`, `verify.md` and `fix.md` names `{evidence}` in its `## Prompt`, one line each | a placeholder must reach the tuple, every template and every builder at once, or F6's test fails; the fixer's line costs a path | the checkers' prompts alone: `verify.md` and `fix.md` would go without the path |
| <a id="d8"></a>**D8** | The decision [D79](../../../docs/decisions.md#d79--a-tool-finds-a-checker-judges), **A tool finds, a checker judges**, is added to `docs/decisions.md` in the group *The check loop and the release*, after D78, and to the group line of its header: what a tool can find goes to the gate or to `evidence.md`, the checkers judge the rest. It extends [D66](../../../docs/decisions.md#d66--two-checkers-conformance-and-adversarial), D77 and D78; `W:12` gains that the evidence holds facts a tool found. The references tell the checkers to start from `evidence.md`, never re-derive a line it holds, and judge its judgment half; coverage-trace stays, D39 is unchanged. `CONTRIBUTING.md` states the ratchet | F7: the passes keep their judgment half, and `diff-cover` cannot see a removed test's proofs | folding the passes into the gate: it cannot judge a retired proof · a new principle: a choice that could go another way is a decision |
| <a id="d9"></a>**D9** | The lint, the docstring check and the timeout rule take effect on this version's own gate, each turned on in the phase that cleans for it. `gate_integrity.py`, the evidence step and `{evidence}` act from the next version: a run uses the pinned release's converge, so this version's own converge runs without them. Each gate line is quoted in the phase that adds it, for `gate_check.py` | self-hosting: a stricter gate binds the code that adds it; a converge from the pin cannot read what the branch adds | holding those rules until the evidence lands: the cleanup would wait on a change that cannot act yet |

**The shape of `evidence.md`.** A title, a line, and each section's heading, in this order:

```
# Evidence — <change-id> · <base7>..<head7>

Facts a tool found, not verdicts. Start from them; judge them.

## Gate integrity
noqa · skills/x/a.py:12 · x = f()  # noqa: BLE001
test-removed · tests/test_a.py:30 · def test_a() -> None:

## Plan check
plan: clean

## Stale-claim candidates
old_name · docs/guide.md:41: call old_name to start

## Test cost
added · tests/test_b.py:9 · test_b · 0.31 s
slow · tests/test_b.py:8 · @pytest.mark.slow
boot · tests/test_b.py:20 · _main(conduct, root, "run")
removed · test_a · named in ## Tests
```

A section with nothing reads `None.`. `gate_integrity.py`'s lines fill *Gate integrity* as they are; `plan_check.py`'s output
fills *Plan check* whole, `plan: clean` included.

## Tests

The change adds the tests below, extends those marked, edits the expectations of those named after the table, and removes none.

| layer | file | test | does | why here |
|---|---|---|---|---|
| unit | `tests/test_docstrings.py` | `test_a_docstring_over_three_non_blank_lines_is_flagged`, `test_a_first_line_of_two_sentences_is_flagged`, `test_a_clean_file_prints_nothing` | `check` on source text and `main` on a temp tree: each flag, the exit codes, a blank line not counted | the lowest layer that can fail for the rule (`T1`) |
| unit | `tests/test_ast_grep.py` | `test_the_timeout_rule_flags_a_run_with_no_timeout` | the venv's `ast-grep scan` in a temp project holding the repo's `sgconfig.yml` and rule: a call with no `timeout=` exits 1 naming file and line; one with it, and one under `tests/`, exit 0 | the rule is a file; only the tool reads it |
| unit | `tests/test_gate_integrity.py` | one test for each kind of [D5](#d5), and `test_a_moved_line_is_no_line` | `lines` on patch text; `main` on a patch file and on a missing one | the lowest layer (`T1`) |
| unit | `tests/test_evidence.py` | `test_the_candidates_are_the_names_a_patch_removes`, `test_a_test_is_read_with_its_seconds`, `test_a_removed_test_is_read_against_the_design`, `test_a_section_is_capped` | the builders on patch, junit and design text | the lowest layer (`T1`) |
| integration | `tests/test_converge.py` | `test_the_freeze_writes_the_patch_the_bundle_and_the_debt_cards`, extended | a step: `evidence.md` stands after the freeze, with each heading of the shape above, its plan-check section the fake host's output | the test that already freezes (`T2`) |
| integration | `tests/test_converge.py` | `test_a_blocker_is_fixed_verified_and_cleared`, extended | a step: the re-freeze rewrites `evidence.md` for the fix range, and each worker prompt of the next round names its path | the test that already re-freezes (`T2`) |
| integration | `tests/test_converge.py` | `test_each_worker_prompt_is_filled_from_its_reference`, unchanged | it holds `evidence` in each reference and in the tuple | F6 |
| integration | `tests/test_conduct.py` | `test_a_cut_prefetches_its_approved_wheels`, new | `_prefetch` with a fake `uv` on `PATH`: one wheels-only fetch for an approved row, its argv and environment; a URL row, a path row, a bare-version row and a failing fetch exit 2 and reserve nothing; a brief with no row runs none | no test reaches `_prefetch` (`T2`); `cut` is the seam |

Edited expectations, each listing the sandboxed commands a freeze now runs, `plan_check.py` after each freeze and `git` after one whose patch removes a name:
`test_a_clean_round_converges_with_no_fix`, `test_a_blocker_is_fixed_verified_and_cleared`,
`test_round_one_pickup_rides_with_the_fix`, `test_a_pickup_check_runs_on_the_needed_role` in `tests/test_converge.py`. `_swap_runner`
of `tests/test_conduct.py` gains a no-op `_prefetch`, so the tests that cut a brief with rows fetch nothing.

End-to-end runs added: none; the `conduct.py` tests stay at `cut`, and no test adds an `_main(…"run"…)` boot. `I16` table: none removed.

## Dependencies

| package | constraint | why |
|---|---|---|
| ast-grep-cli | >=0.51.1,<0.52 | the `subprocess-run-needs-timeout` gate rule and the ratchet ([D3](#d3)) |

## Risks / Trade-offs

| risk | mitigation |
|---|---|
| the offline sandboxed gate finds no `ast-grep-cli` in `.minions/uv-cache` and its precondition gate goes red (F9) | [D4](#d4) fetches it at the queue for every later cut; for this version the cache is warmed by hand before ship ([Migration Plan](#migration-plan)) |
| the docstring cleanup rewrites many docstrings, and a `Why:` pointer could be lost | a docstring keeps its summary and its `Why:` line, and the design or document that line cites holds the rest; `make check` holds the check after each file |
| a timeout ends a script with a traceback instead of a hang | each constant is generous — 600 s, the gate 3600 s; `C` already maps its own timeouts to `Stop` |
| a test that fakes `subprocess.run` with a fixed signature rejects the new `timeout=` | the phase names its file in the build's check: `uv run pytest -q` goes red there, and the fake takes `**kwargs` |
| the rule reaches `subprocess.run` alone, so `0108·S4` (`sandboxed()`'s unbounded `process.wait()`) and `0104·S7` (a probe killed on what is left of the deadline) stay open | C1 of the brief drops them from `debt:`; each is paid by a change that bounds that path |
| `0034·R9`'s mechanism, a file read at parse time hiding a `-` in a recipe, is not found by `gate_integrity.py` | it finds the gate's configuration and suppressions, the class the brief names; the card's own **Still true?** stays for a reader to judge at the release |
| a line that moves between files shows as a removed `assert` and an added one | the evidence lists it; the checker judges it, and a move is the common reason |
| the evidence's `plan_check.py` re-runs the plan's `Verify:` commands at each freeze, and again at `planned()` after a fix | the cost is one command run a round; `plan_check.py` stays the one checker of the plan |
| `evidence.md` grows large on a wide diff | each section holds at most `LIMIT` lines ([D6](#d6)) |

## Migration Plan

Nothing migrates at the release: the rules apply to the next change at once, and `gate_integrity.py` and the evidence act from
the version after this one ([D9](#d9)).

Before `/mf-ship`, in the primary checkout, once, by hand — the cache that [D4](#d4) will fill for later cuts:

```
UV_CACHE_DIR=.minions/uv-cache uv pip install --no-build --target .minions/tmp/prefetch 'ast-grep-cli>=0.51.1,<0.52'
```

Then `rm -r .minions/tmp/prefetch`. The build's `uv add --dev` and the sandboxed gate's `uv sync --locked` read that cache offline.

## Verdict

Build in phases, each green on its own: the lint, the docstring check, the timeout rule, the prefetch, `gate_integrity.py`,
the evidence step, the prose.
