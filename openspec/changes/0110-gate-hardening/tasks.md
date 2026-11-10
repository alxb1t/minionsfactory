# Gate hardening — tasks

Build the settled [design](design.md), one phase at a time; each test step goes red before its code. `K` is
`skills/mf-converge/scripts/converge.py`, `C` is `skills/mf-ship/scripts/conduct.py`, `W` is
`skills/mf-converge/references/worker.md`. Inside a phase a sub-task's `Verify:` is its own; only the phase's end is green.

## Progress

- [x] 1 — The wider lint, its sites cleaned · moderate
- [x] 2 — The docstring check, its sites fixed · moderate
- [x] 3 — The timeout rule, its sites fixed · hard
- [x] 4 — `conduct.py cut` prefetches the approved wheels · hard
- [x] 5 — `gate_integrity.py` · hard
- [x] 6 — The evidence at every freeze · hard
- [x] 7 — The references, the ratchet and D79 · hard

## 1 — The wider lint, its sites cleaned

- [x] 1.1 **HALT CHECK** The base stands as the design's [Context](design.md#context) reads it.
  Verify: `git grep -n -e '^select = ' -e '"S603"' -e '"tests/\*\*"' -- pyproject.toml` prints a line for each.
- [x] 1.2 In `pyproject.toml`, under `[tool.ruff.lint]`, add `extend-select` as [D1](design.md#d1) lists it; in `per-file-ignores`
  add the ignores of D1 to `"**"` and `PT018` to `"tests/**"`, each beside the comment style the file keeps.
  Verify: `git grep -n -e '^extend-select = ' -e '"PLW1510"' -e '"PT018"' -- pyproject.toml` prints a line for each.
- [x] 1.3 Run `uv run ruff check --fix .`, then clear by hand each site it leaves in `skills/` and `scripts/`, `C` aside:
  `RUF007`, `RUF021`, `PLC0207`, `SIM102`, `PLW2901`, `SIM109`, `PLR1714`, each as ruff's message says.
  Verify: `uv run ruff check skills scripts --exclude skills/mf-ship/scripts/conduct.py` exits 0.
- [x] 1.4 Clear each site in `C` that is no `BLE001`: `SIM105`, `SIM102`, `PLC0207`, `RET502`, `SIM300`; the `PLC0415` site is the lazy import in `_markdown`,
  which stays: add `# noqa: PLC0415` to its import line, the docstring above it being the reason.
  Verify: `uv run ruff check skills/mf-ship/scripts/conduct.py --ignore BLE001,RUF100` exits 0.
- [x] 1.5 For each `BLE001` site in `C`, add `# noqa: BLE001` on its `except` line and `# why: <the reason the code goes on past any
  failure>` on the line above; the reasons are the docstring or the lines around each site.
  Verify: `uv run ruff check skills/mf-ship/scripts/conduct.py` exits 0.
- [x] 1.6 Clear each site in `tests/`: `RUF043` by a raw string in each `match=` with each literal metacharacter escaped, `\.` for a dot, `PLE2515` by the escape the message names, `RUF007`, `PERF401`,
  `PLC0207`, each as ruff's message says; `RUF059` at `built` in `tests/test_conduct.py` by naming it `_built`; `BLE001` at `except BaseException` in `tests/test_conduct.py` as 1.5 says.
  Verify: `uv run ruff check tests` exits 0.
- [x] 1.7 In `CODING_STANDARDS.md`, under *Project rules*, add one bullet: the lint families of D1 hold, and a blind `except`
  carries `# noqa: BLE001` and its reason.
  Verify: `git grep -n 'BLE001' -- CODING_STANDARDS.md` prints a line.

## 2 — The docstring check, its sites fixed

- [x] 2.1 **HALT CHECK** The base holds the scripts' folder and the standards file the check reads.
  Verify: `git grep -n -e '^TIMEOUT_SECONDS = ' -- scripts/corpus.py` prints a line; `git grep -n -e '^## Project rules' -- CODING_STANDARDS.md` prints a line.
- [x] 2.2 Add `tests/test_docstrings.py` with the tests of [the Tests table](design.md#tests), loading the script by `importlib.util`
  as `tests/test_corpus.py` does.
  Verify: `git grep -n 'def test_a_docstring_over_three_non_blank_lines_is_flagged' -- tests/test_docstrings.py` prints a line.
- [x] 2.3 Add `scripts/docstrings.py` to [D2](design.md#d2): a `uv` script (PEP 723 header, `dependencies = []`) with `check(source, name)`
  returning `<path>:<line>: <what>` lines.
  Verify: `git grep -n '^def check(' -- scripts/docstrings.py` prints a line.
- [x] 2.4 Add `main(argv)` to it: the files from `git ls-files --cached --others --exclude-standard -- '*.py'`, run with `timeout=TIMEOUT_SECONDS`,
  its own constant `TIMEOUT_SECONDS = 600`; exit 1 on any line, 0 on none.
  Verify: `uv run pytest -q tests/test_docstrings.py` exits 0.
- [x] 2.5 In `CODING_STANDARDS.md`, under *Project rules*, add one bullet: `scripts/docstrings.py` holds `C7` and `C3` for every
  docstring of a Python file, counting non-blank lines, so a blank line is no line.
  Verify: `git grep -n 'scripts/docstrings.py' -- CODING_STANDARDS.md` prints a line.
- [x] 2.6 Fix each site `uv run --script scripts/docstrings.py` prints, in every file it names: cut the docstring to at most 3 non-blank lines, keeping
  its summary and its `Why:` line when it has one, and cut a first line of two sentences to its first sentence.
  Verify: `uv run --script scripts/docstrings.py` exits 0.
- [x] 2.7 Edit the `gate` and `check` recipes of `Makefile`: add the docstring check after the lint line of each; its lines
  are quoted below for `gate_check.py`.
  ```diff
  + 	uv run --script scripts/docstrings.py
  ```
  Verify: `git grep -c 'uv run --script scripts/docstrings.py' -- Makefile` prints `Makefile:2`.

## 3 — The timeout rule, its sites fixed

- [x] 3.1 **HALT CHECK** The base holds the calls the rule reads, and no `ast-grep` file.
  Verify: `git grep -n 'subprocess.run(' -- skills/mf-converge/scripts/gate_run.py` prints a line; `git ls-files -- sgconfig.yml sg-rules` prints nothing.
- [x] 3.2 Add the dependency of [the design](design.md#dependencies): run `uv add --dev --offline 'ast-grep-cli>=0.51.1,<0.52'`,
  which writes `pyproject.toml`'s `dev` group and `uv.lock`; the cache of the migration plan holds the wheel.
  Verify: `git grep -n -F 'ast-grep-cli' -- pyproject.toml uv.lock` prints a line in each.
- [x] 3.3 Add `tests/test_ast_grep.py` with `test_the_timeout_rule_flags_a_run_with_no_timeout` ([Tests](design.md#tests)): it runs the
  `ast-grep` in the interpreter's own folder, in a temp project holding copies of `sgconfig.yml` and the rule file.
  Verify: `git grep -n 'def test_the_timeout_rule_flags_a_run_with_no_timeout' -- tests/test_ast_grep.py` prints a line.
- [x] 3.4 Add `sgconfig.yml` (`ruleDirs: [sg-rules]`) and `sg-rules/subprocess-run-needs-timeout.yml` to [D3](design.md#d3): language
  `python`, `severity: error`, files `skills/**` and `scripts/**`, a `subprocess.run($$$ARGS)` call with no `timeout=` argument.
  Verify: `uv run pytest -q tests/test_ast_grep.py` exits 0.
- [x] 3.5 Give each site `uv run ast-grep scan` prints a `timeout=` of its module's `TIMEOUT_SECONDS`, adding `TIMEOUT_SECONDS = 600`
  to a module that has none; `skills/mf-converge/scripts/gate_run.py`'s `make gate` call takes `GATE_SECONDS = 3600`.
  Verify: `uv run ast-grep scan` exits 0; `uv run pytest -q -m "not slow"` exits 0.
- [x] 3.6 Edit the `gate` and `check` recipes of `Makefile`: add `ast-grep` after the docstring line of each; its lines
  are quoted below for `gate_check.py`.
  ```diff
  + 	uv run ast-grep scan
  ```
  Verify: `git grep -c 'uv run ast-grep scan' -- Makefile` prints `Makefile:2`.
- [x] 3.7 In `CONTRIBUTING.md`, under *The evidence a change carries*, add the ratchet: a repeat card of a syntactic class becomes a rule of
  `sg-rules/` at the next paydown.
  Verify: `git grep -n 'sg-rules' -- CONTRIBUTING.md` prints a line.

## 4 — `conduct.py cut` prefetches the approved wheels

- [x] 4.1 **HALT CHECK** The base stands as the design's [Context](design.md#context) reads it.
  Verify: `git grep -n -e '^def _approval(' -e '^def cut(' -e '^def _write_models(' -- skills/mf-ship/scripts/conduct.py` prints a line for each.
- [x] 4.2 Add `test_a_cut_prefetches_its_approved_wheels` to `tests/test_conduct.py` ([Tests](design.md#tests)): a fake `uv` on `PATH` records argv
  and environment of each fetch a case of [D4](design.md#d4) makes, and none for a refused row; it calls `_swap_runner`, then sets `_prefetch` back to `conduct["_prefetch"]`.
  Verify: `git grep -n 'def test_a_cut_prefetches_its_approved_wheels' -- tests/test_conduct.py` prints a line.
- [x] 4.3 Make `_swap_runner` in `tests/test_conduct.py` set `_prefetch` to a no-op in the globals of `conduct["main"]`, so a test that cuts a brief with rows fetches nothing.
  Verify: `git grep -n '"_prefetch"' -- tests/test_conduct.py` prints a line.
- [x] 4.4 In `C` add `PYPI_INDEX = "https://pypi.org/simple"` and `PREFETCH_SECONDS = 600`, and `_prefetch(primary, rows)` to [D4](design.md#d4):
  one `uv pip install` for each row, `UV_CACHE_DIR` set, every `UV_*` and `PIP_*` name dropped, the scratch removed after.
  Verify: `git grep -n -e '^PYPI_INDEX = ' -e '^def _prefetch(' -- skills/mf-ship/scripts/conduct.py` prints a line for each.
- [x] 4.5 In `_prefetch` stop with exit 2 on a row [D4](design.md#d4) refuses and on a failed fetch, naming the row or the package, then in `cut` of `C`
  call it after `primary = primary_of(cwd)` and before `with _queue_lock(primary)`.
  Verify: `uv run pytest -q tests/test_conduct.py -k "prefetch or parallel_cuts or queues_its_models"` exits 0.

## 5 — `gate_integrity.py`

- [x] 5.1 **HALT CHECK** The base holds the converge scripts folder and `gate_check.py`'s stated reach.
  Verify: `git grep -n -e 'makefiles or dry run' -- skills/mf-converge/scripts/gate_check.py` prints a line.
- [x] 5.2 Add `tests/test_gate_integrity.py`: one test for each kind of [D5](design.md#d5) over patch text, `test_a_moved_line_is_no_line`,
  and `main` on a patch file and on a missing one (exit 2).
  Verify: `git grep -n 'def test_a_moved_line_is_no_line' -- tests/test_gate_integrity.py` prints a line.
- [x] 5.3 Add the case `gate-integrity` to `scripts/corpus.toml`, in the form of its `debt-match` case: `each = ["changes/*/diff.patch"]`, `argv` the
  script of 5.4 on `{input}`, `reads` saying it reads a frozen diff patch to the lines a worker starts from.
  Verify: `git grep -n 'name = "gate-integrity"' -- scripts/corpus.toml` prints a line.
- [x] 5.4 Add `skills/mf-converge/scripts/gate_integrity.py` to [D5](design.md#d5): a `uv` script with `lines(patch)`, the kinds and the line form
  of the design, a moved line dropped.
  Verify: `git grep -n '^def lines(' -- skills/mf-converge/scripts/gate_integrity.py` prints a line.
- [x] 5.5 Add `main(argv)` to it: print each line, or `None.` for a patch that holds nothing; exit 0 for any readable patch, 2 for an unreadable one.
  Verify: `uv run pytest -q tests/test_gate_integrity.py` exits 0.

## 6 — The evidence at every freeze

- [x] 6.1 **HALT CHECK** The base stands as the design's [Context](design.md#context) reads it.
  Verify: `git grep -n -e '^PLACEHOLDERS = ' -e '^def freeze(' -e '^def checker_prompt(' -e '^def verify_prompt(' -e '^def fixer(' -- skills/mf-converge/scripts/converge.py` prints a line for each.
- [x] 6.2 Add `tests/test_evidence.py` with the tests of [the Tests table](design.md#tests) over patch, junit and design text.
  Verify: `git grep -n 'def test_a_section_is_capped' -- tests/test_evidence.py` prints a line.
- [x] 6.3 Add `skills/mf-converge/scripts/evidence.py` to [D6](design.md#d6): `LIMIT`, `candidates(patch)`, `stale(names, found, changed)`,
  `test_cost(patch, report, design)` and `render(change, base, head, sections)`, the shape of the design's *The shape of `evidence.md`*.
  Verify: `uv run pytest -q tests/test_evidence.py` exits 0.
- [x] 6.4 Extend `test_the_freeze_writes_the_patch_the_bundle_and_the_debt_cards` and `test_a_blocker_is_fixed_verified_and_cleared` in
  `tests/test_converge.py` with the steps of [the Tests table](design.md#tests), each after the test's own.
  Verify: `git grep -n 'evidence.md' -- tests/test_converge.py` prints a line.
- [x] 6.5 In `K` load `evidence.py` and `gate_integrity.py` by `runpy` beside the other scripts, and add `"evidence"` to `PLACEHOLDERS`.
  Verify: `git grep -n -e '"evidence"' -e 'gate_integrity.py' -- skills/mf-converge/scripts/converge.py` prints a line for each.
- [x] 6.6 In `freeze` of `K` write `evidence.md` after `debt-cards.md` and before the stamp, running `plan_check.py` and one `git grep` through `_captured`, as [D6](design.md#d6) says;
  with no candidate name, no `git grep` runs and *Stale-claim candidates* reads `None.`.
  Verify: `git grep -n 'evidence.md' -- skills/mf-converge/scripts/converge.py` prints a line.
- [x] 6.7 In `K` give `evidence=` to `checker_prompt`, `verify_prompt` and `fixer`, the path of `evidence.md`.
  Verify: `git grep -c 'evidence=' -- skills/mf-converge/scripts/converge.py` prints `skills/mf-converge/scripts/converge.py:3`.
- [x] 6.8 In the `## Prompt` of `generic-conformance.md`, `generic-adversarial.md`, `verify.md` and `fix.md` add one packet or input line naming `evidence.md` at `{evidence}`.
  Verify: `git grep -l -F '{evidence}' -- skills/mf-converge/references/` prints each of the four.
- [x] 6.9 Edit the lists of sandboxed commands in `test_a_clean_round_converges_with_no_fix`, `test_a_blocker_is_fixed_verified_and_cleared`,
  `test_round_one_pickup_rides_with_the_fix` and `test_a_pickup_check_runs_on_the_needed_role`: each gains `plan_check.py` after each freeze, and `git` after one whose patch removes a name.
  Verify: `uv run pytest -q -m "not slow"` exits 0.

## 7 — The references, the ratchet and D79

- [x] 7.1 **HALT CHECK** The base holds the decision group and the worker reference's line the decision amends.
  Verify: `git grep -n -e '^### D78 · ' -e 'converge.py. judges nothing' -- docs/decisions.md skills/mf-converge/references/worker.md` prints a line for each.
- [x] 7.2 In `docs/decisions.md` add `### D79 · A tool finds, a checker judges` after D78, in the form of its neighbours (a bold decision, **Why:**, **Accepts:**,
  **Rejected:**), with a new **Extends:** line naming D66, D77 and D78, edited nowhere else, and add D79 to the ids of *The check loop and the release* in the header diagram, as [D8](design.md#d8) says.
  Verify: `git grep -n 'A tool finds, a checker judges' -- docs/decisions.md` prints its heading.
- [x] 7.3 In `W` add to the sentence that says `converge.py` judges nothing: `evidence.md` holds facts a tool found, never a verdict.
  Verify: `git grep -n -F 'never a verdict' -- skills/mf-converge/references/worker.md` prints a line.
- [x] 7.4 In `W`'s passes table, say that the stale-claim and test-cost passes start from `evidence.md`'s sections and judge their lines, and that coverage-trace stays the worker's.
  Verify: `git grep -n -e 'start from .evidence.md' -- skills/mf-converge/references/worker.md` prints a line.
- [x] 7.5 In `generic-conformance.md` section 5 (*Gate integrity*), `generic-adversarial.md` section 3 and `verify.md`, tell the worker to start from `evidence.md`,
  never re-derive a line it holds, and judge its judgment half; the words `never re-derive` stand in each.
  Verify: `git grep -l 'never re-derive' -- skills/mf-converge/references/` prints each of the three.
- [x] 7.6 In `CONTRIBUTING.md`, under *The evidence a change carries*, add one bullet: **`evidence.md`**, in `.minions/changes/<change-id>/`, holds the facts a tool found;
  a rule a tool can hold goes to the gate, as D79 says.
  Verify: `git grep -n 'evidence.md' -- CONTRIBUTING.md` prints a line.
