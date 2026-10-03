# 0022-runner-retires — tasks

**In one line:** the binding stops, the absence tests go, the text stops naming the runner, and the runner is
deleted last ([R11](design.md#r11)).

## Progress

- [x] 1 — The binding stops
- [x] 2 — The absence tests go
- [x] 3 — The text follows
- [ ] 4 — The runner goes

## 1 — The binding stops

The gate stops checking the binding; the checker itself goes in phase 4 ([R1](design.md#r1)).

- [x] 1.1 **HALT CHECK** — the binding runs only as the gate's last command. Verify: `make -n gate | tail -n 1`
  prints `uv run python -m orchestrator specs check --strict`, and `grep -rc 'specs check' .github` prints
  `.github/workflows/ci.yml:0`.
- [x] 1.2 `Makefile`: delete the gate's `specs check` line at `:15`. Verify: `grep -c 'specs check' Makefile`
  prints `0`.
- [x] 1.3 `tests/test_skills.py` and `tests/test_principles.py`: delete every `@pytest.mark.spec(...)` and
  `@pytest.mark.spec_exempt(...)` decorator line ([the tests](design.md#the-tests-and-pyprojecttoml)). Verify:
  `grep -c 'pytest.mark.spec' tests/test_skills.py tests/test_principles.py` prints `tests/test_skills.py:0` and
  `tests/test_principles.py:0`.
- [x] 1.4 `CLAUDE.md` `:30` and `:57-58`, `README.md` `:55-56` and `:68-69`: the phase 1 edits of
  [the front door](design.md#the-front-door). Verify: `grep -c -E 'spec binding|spec-binding' CLAUDE.md README.md`
  prints `CLAUDE.md:0` and `README.md:0`.
- [x] 1.5 `docs/decisions.md`: add D36 after D23, and make the diagram's line `Repo conventions D19…D23, D36`, as
  [the decisions](design.md#the-decisions) says ([R5](design.md#r5)). Verify: `grep -c '^### D36 · ' docs/decisions.md`
  prints `1`, and `grep -c 'D19…D23, D36' docs/decisions.md` prints `1`.

## 2 — The absence tests go

No test asserts an absence ([R4](design.md#r4), D37).

- [x] 2.1 **HALT CHECK** — `tests/test_conventions.py` is named only where this phase edits. Verify:
  `git grep -l test_conventions -- . ':!openspec' ':!CHANGELOG.md'` prints `docs/principles.md` and
  `skills/mf-build/SKILL.md`, and nothing else.
- [x] 2.2 Delete `tests/test_conventions.py`. Verify: `test ! -e tests/test_conventions.py` exits 0.
- [x] 2.3 `docs/principles.md`: the **Held by** of *The repo reaches nothing outside itself*, and *A retired word is
  retired everywhere* whole, as [the principles](design.md#the-principles) says. Verify:
  `grep -c 'test_conventions' docs/principles.md` prints `0`, and `grep -c 'No standing scan' docs/principles.md`
  prints `1`.
- [x] 2.4 `docs/decisions.md`: add D37 after D36, and make the diagram's line `Repo conventions D19…D23, D36, D37`.
  Verify: `grep -c '^### D37 · ' docs/decisions.md` prints `1`, and `grep -c 'D19…D23, D36, D37' docs/decisions.md`
  prints `1`.
- [x] 2.5 `CLAUDE.md` `:38-40` and `skills/mf-build/SKILL.md` `:226`: the phase 2 edits of
  [the front door](design.md#claudemd) and [the skills](design.md#skillsmf-buildskillmd). Verify:
  `grep -c 'retired-vocabulary' CLAUDE.md` prints `0`, and `grep -c 'test_conventions' skills/mf-build/SKILL.md`
  prints `0`.

## 3 — The text follows

No live text names the runner ([R8](design.md#r8), [R10](design.md#r10)).

- [x] 3.1 `CLAUDE.md` `:41`, `:51-59` and `:70-71`: the phase 3 edits of [its section](design.md#claudemd). Verify:
  `grep -c -E 'orchestrator|runner|env\.example' CLAUDE.md` prints `0`.
- [x] 3.2 `README.md` `:64-69`: delete the runner's section. Verify: `grep -c -E 'orchestrator|runner' README.md`
  prints `0`.
- [x] 3.3 `docs/README.md` `:25-29`: delete the `## Deprecated` section. Verify:
  `grep -c -E 'orchestrator|Deprecated|modules/' docs/README.md` prints `0`.
- [x] 3.4 `Makefile` `:7-8`: the comment, as [its section](design.md#makefile) says. Verify:
  `grep -c 'runner' Makefile` prints `0`.
- [x] 3.5 `openspec/config.yaml`: the proposal, design and tasks rules of [its section](design.md#openspecconfigyaml), closing `0020·N3`.
  Verify: `grep -c -E 'seams \(|state\.py|reader requires|progress parser' openspec/config.yaml` prints `0`.
- [x] 3.6 `skills/mf-build/SKILL.md`: the `W2` example at `:126-129` and `C8`'s example at `:220`, as
  [its section](design.md#skillsmf-buildskillmd) says. Verify: `grep -c -E 'orchestrator|the runner' skills/mf-build/SKILL.md`
  prints `0`.
- [x] 3.7 `skills/mf-cut-change/SKILL.md`: `A5`'s example at `:182`, and the harms in the **Converge** bullet at
  `:201-202`, closing `0021·N1`. Verify: `grep -c 'the runner' skills/mf-cut-change/SKILL.md` prints `0`, and
  `grep -c 'data loss' skills/mf-cut-change/SKILL.md` prints `1`.
- [x] 3.8 No live doc, skill or config names the runner. Verify:
  `git grep -n -E 'orchestrator|prompts/|docs/modules|architecture\.md' -- CLAUDE.md README.md docs/README.md docs/principles.md docs/decisions.md docs/autonomous.md skills Makefile openspec/config.yaml .github`
  prints nothing.

## 4 — The runner goes

The delete, last ([R11](design.md#r11), `A4`).

- [ ] 4.1 **HALT CHECK** — outside the runner, only its tests and `.env.example` name it. Verify:
  `git grep -l orchestrator -- . ':!orchestrator' ':!prompts' ':!docs/modules' ':!docs/architecture.md' ':!openspec' ':!CHANGELOG.md'`
  prints `.env.example` and [the runner's tests](design.md#the-runners-tests), and nothing else.
- [ ] 4.2 Delete `orchestrator/`, `prompts/`, `docs/architecture.md`, `docs/modules/`, `.env.example` and
  [the runner's tests](design.md#the-runners-tests) ([R12](design.md#r12)). Verify:
  `test ! -e orchestrator -a ! -e prompts -a ! -e docs/modules -a ! -e docs/architecture.md -a ! -e .env.example`
  exits 0, and `git ls-files tests` prints `tests/test_principles.py` and `tests/test_skills.py`.
- [ ] 4.3 `pyproject.toml`: `dependencies = []`, and delete the `markers` entry; then `uv lock`
  ([R9](design.md#r9)). Verify: `grep -c pydantic pyproject.toml uv.lock` prints `pyproject.toml:0` and
  `uv.lock:0`, and `grep -c 'spec_exempt' pyproject.toml` prints `0`.
- [ ] 4.4 Nothing outside the history and the specs names the runner or the binding. Verify:
  `git grep -n -E 'orchestrator|mark\.spec|spec_exempt|docs/modules|pydantic' -- . ':!CHANGELOG.md' ':!openspec'`
  prints nothing.
