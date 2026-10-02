# 0020-architecture-and-decisions — tasks

**In one line:** the principles, the decisions and the autonomous page land from [pages/](pages/); the front door
is rewritten; `mf-cut-change` gains `A7`; the method page is deleted last.

## Progress

- [x] 1 — The principles
- [x] 2 — The decisions
- [ ] 3 — The autonomous page
- [ ] 4 — The front door
- [ ] 5 — A7
- [ ] 6 — The method page retires

## 1 — The principles

The page and the check that holds it ([E2](design.md#e2), [E4](design.md#e4)).

- [x] 1.1 **HALT CHECK** — every test [pages/principles.md](pages/principles.md) names exists. Verify:
  `grep -o 'tests/[a-z_]*\.py::[a-z_0-9]*' openspec/changes/0020-architecture-and-decisions/pages/principles.md | sort -u | while IFS= read -r t; do grep -q "^def ${t##*::}(" "${t%%::*}" || echo "missing $t"; done`
  prints nothing.
- [x] 1.2 Test first: `tests/test_principles.py`, as [the check](design.md#the-check) describes it. Verify:
  `uv run pytest tests/test_principles.py -q` fails, naming `docs/principles.md`.
- [x] 1.3 Write `docs/principles.md` from [pages/principles.md](pages/principles.md), per [E2](design.md#e2).
  Verify: `grep -c '^### ' docs/principles.md` prints `13`.
- [x] 1.4 The check passes. Verify: `uv run pytest tests/test_principles.py -q` exits 0.

## 2 — The decisions

- [x] 2.1 Write `docs/decisions.md` from [pages/decisions.md](pages/decisions.md), per [E2](design.md#e2).
  Verify: `grep -c '^### D[0-9]* · ' docs/decisions.md` prints `35`.
- [x] 2.2 The page holds no history ([E3](design.md#e3)). Verify: `grep -c -E 'v0\.[0-9]|Made by' docs/decisions.md`
  prints `0`.

## 3 — The autonomous page

- [ ] 3.1 Write `docs/autonomous.md` from [pages/autonomous.md](pages/autonomous.md), per [E2](design.md#e2) and
  [E5](design.md#e5). Verify: `grep -c '^## ' docs/autonomous.md` prints `6`.

## 4 — The front door

What each file holds is in [design.md](design.md#what-each-file-of-the-front-door-holds).

- [ ] 4.1 Rewrite `docs/README.md` as [its section](design.md#docsreadmemd) says, keeping the `sdd.md` row.
  Verify: `grep -c 'Obsidian' docs/README.md` prints `0`.
- [ ] 4.2 `docs/architecture.md`: add the banner under the title and delete the sentence at lines 92-94
  ([E6](design.md#e6)). Verify: `grep -c 'Deprecated' docs/architecture.md` prints `1`.
- [ ] 4.3 `docs/modules/provider.md` and `docs/modules/state.md`: the before → after of
  [the pointers](design.md#docsarchitecturemd-and-the-pointers). Verify:
  `grep -c 'vault' docs/architecture.md docs/modules/provider.md docs/modules/state.md` prints `:0` for each file.
- [ ] 4.4 Rewrite `README.md` as [its section](design.md#readmemd) says. Verify:
  `grep -c -E 'sdd\.md|No LLM in the orchestration layer' README.md` prints `0`.
- [ ] 4.5 Rewrite `CLAUDE.md` as [its section](design.md#claudemd) says ([E7](design.md#e7)). Verify:
  `grep -c '^@docs/principles.md$' CLAUDE.md` prints `1`, and `grep -c -E 'sdd\.md|No LLM|Obsidian' CLAUDE.md`
  prints `0`.
- [ ] 4.6 `README.md`, `CLAUDE.md` and `docs/README.md` follow the prose rules ([E12](design.md#e12)), and
  `CLAUDE.md` names them. Verify: `grep -c 'P13' CLAUDE.md` prints `1`.
- [ ] 4.7 `openspec/config.yaml`: the `context:` block of [its section](design.md#openspecconfigyaml). Verify:
  `grep -c 'sdd\.md' openspec/config.yaml` prints `0`.

## 5 — A7

- [ ] 5.1 `skills/mf-cut-change/SKILL.md`: add the [`A7`](design.md#a7) row after `A6` ([E8](design.md#e8)).
  Verify: `grep -c '^| \*\*A7\*\* |' skills/mf-cut-change/SKILL.md` prints `1`.

## 6 — The method page retires

The delete is the last act ([E9](design.md#e9)). `openspec/specs/sdd/spec.md` names the page until the release
folds the delta ([E11](design.md#e11)).

- [ ] 6.1 **HALT CHECK** — the skill lines citing the method page are the ones
  [design.md](design.md#the-skill-sentences-before--after) names. Verify:
  `grep -n 'sdd\.md' skills/*/SKILL.md | cut -d: -f1,2` prints `skills/mf-build/SKILL.md:142`,
  `skills/mf-converge/SKILL.md:153`, `skills/mf-release/SKILL.md:77` and `skills/mf-release/SKILL.md:113`.
- [ ] 6.2 `tests/test_skills.py`: the anchors scan and its twin stop reading the method page, renamed as
  [design.md](design.md#the-skill-sentences-before--after) says. Verify: `grep -c '_METHOD_PAGE' tests/test_skills.py`
  prints `0`.
- [ ] 6.3 `tests/test_conventions.py`: delete `test_the_method_doc_exists_and_the_docs_map_links_it`. Verify:
  `grep -c 'test_the_method_doc_exists' tests/test_conventions.py` prints `0`.
- [ ] 6.4 `skills/mf-build/SKILL.md`, `skills/mf-converge/SKILL.md`, `skills/mf-release/SKILL.md`: the after-text
  of [E10](design.md#e10). Verify: `grep -c 'sdd\.md' skills/mf-build/SKILL.md skills/mf-converge/SKILL.md skills/mf-release/SKILL.md`
  prints `:0` for each file.
- [ ] 6.5 `docs/README.md`: remove the `sdd.md` row. Verify: `grep -c 'sdd\.md' docs/README.md` prints `0`.
- [ ] 6.6 Test first: `tests/test_conventions.py` gains the needle `sdd.md`, its scan
  `test_the_retired_method_page_is_named_nowhere_in_code_prompts_or_docs` and its twin ([E13](design.md#e13)).
  Verify: `uv run pytest tests/test_conventions.py -q` fails, naming `docs/sdd.md`.
- [ ] 6.7 Delete `docs/sdd.md`. Verify: `test ! -e docs/sdd.md`, and
  `git grep -n 'sdd\.md' -- README.md CLAUDE.md docs skills openspec/config.yaml` prints nothing.
- [ ] 6.8 `docs/principles.md`, *A retired word is retired everywhere*: add the new scan to **Held by**. Verify:
  `grep -c 'test_the_retired_method_page' docs/principles.md` prints `1`.
