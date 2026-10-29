# Repository standards — design

A repo's own rules get a coding-standards file and a contribution guide every station reads; the bootstrap writes
them, MF adopts them, and the comment rules default to none. Verdict: ready to build. Scope is [the proposal](proposal.md); behaviour is
[the delta](specs/sdd/spec.md).

## Context

Premises were re-checked on `main` at `193a550` (v0.33.0) before the cut.

| evidence at the cut | implication |
|---|---|
| Every station but the bootstrap reads root `AGENTS.md` "and the mandatory context it names" (`skills/mf-build/SKILL.md:12-13`, `skills/mf-converge/SKILL.md:15-16`); converge hands each worker the same (`:223`), and Step 7 reuses Step 3's inputs (`:377-378`) | naming the files in `AGENTS.md` reaches every station; the fallback read goes in build and Step 3 only ([D1](#d1)) |
| `skills/mf-converge/references/generic-review.md:12` and `generic-security.md:11` list "the target's `AGENTS.md` and mandatory context"; `generic-review.md:22` checks "the target's standards" with no file named | [D1](#d1) |
| `skills/mf-build/SKILL.md:293-321` holds `C1`–`C12`; `C1` "Say why, not what" `:299`, `C2` "Comment the surprise only" `:300`; no test holds the `C` ids; `scripts/metrics/rule_ids.py:14` counts them | `C1` and `C2` rewritten in place ([D2](#d2)) |
| `skills/mf-bootstrap/SKILL.md`: description `:3`, file table `:24-28`, collision precondition `:45-46`; templates in `skills/mf-bootstrap/templates/`; `AGENTS.md.tmpl` has no mandatory-context block, and *How a change is cut here* at `:24-27` | [D3](#d3) |
| D18 (`docs/decisions.md:238-260`) names `CHANGELOG.md` and `README.md` as also written `:240-241`; README copies its tree at `README.md:63-70` | [D4](#d4) |
| `tests/test_skills.py`: the Tests-section guard `:217-242`; the layout scan `:245-336`, `_ALSO_WRITTEN` `:251` | [D5](#d5) |
| MF's `AGENTS.md:14-15` names the principles and decisions; `:17-19` holds the prose-rules and the cut bullets, `:20-21` the patch rule | [D6](#d6) |
| `scripts/metrics/reading_set.py:13` `SHARED`; `scripts/metrics/references.py:48` the files it reads; their tests `tests/test_metric_scripts.py:42-55`, `:121-140`; `converge-reading-set` 11,166 at 0037, watch 10,500 | [D7](#d7) |
| `uv run pytest --collect-only -q \| tail -1` prints `58 tests collected` | [Tests](#tests) |

## Goals / Non-Goals

**Goal:** every repo the line works on has one place for its coding rules and one for how a change lands, and
every station reads them.

**Non-goals:** see [the exclusions](proposal.md#not-in-this-change).

## Decisions

The grilling settled these choices (the brief's Q1–Q18); the build does not reopen them.

### D1

| id | decision | because | rejected |
|---|---|---|---|
| D1 | The build and converge's Step 3 also read a root `CODING_STANDARDS.md`, `CODE_STANDARDS.md` or `CONTRIBUTING.md` that `AGENTS.md` does not name; review cards a contradiction between them as `drift`, the build halts on one that decides its phase's code | Existing repos keep working unmigrated; no filename wins | A precedence between the coding filenames; a read in every station |

`skills/mf-build/SKILL.md:12-13`, before:

```markdown
Before work, read root `AGENTS.md` — the gate, the conventions and seams, the guardrails — and the mandatory
context it names: what is *true* of the repository, not a script. The change itself is authoritative. Missing root `AGENTS.md` → **halt**, naming it.
```

After:

```markdown
Before work, read root `AGENTS.md` — the gate, the conventions and seams, the guardrails — the mandatory context it
names, and a root `CODING_STANDARDS.md`, `CODE_STANDARDS.md` or `CONTRIBUTING.md` it does not name: what is *true*
of the repository, not a script. The change itself is authoritative. Missing root `AGENTS.md` → **halt**, naming
it. A contradiction between those files that decides a phase's code → **halt**, naming both.
```

`skills/mf-converge/SKILL.md` Step 3's input line, before → after:

```markdown
- root `AGENTS.md` and its mandatory context, and the change's proposal, design and tasks under
- root `AGENTS.md`, its mandatory context, a root `CODING_STANDARDS.md`, `CODE_STANDARDS.md` or `CONTRIBUTING.md`
  it does not name, and the change's proposal, design and tasks under
```

In `generic-review.md:12` and `generic-security.md:11`: `the target's \`AGENTS.md\` and mandatory context` →
`the target's \`AGENTS.md\`, its mandatory context and its root standards files`. `generic-review.md:22`, before →
after:

```markdown
2. Check correctness, spec compliance, the target's standards and test proofs. Trace a concrete trigger to its
2. Check correctness, spec compliance, the target's standards files and test proofs; a contradiction between
   standards files is a `drift` card. Trace a concrete trigger to its
```

### D2

| id | decision | because | rejected |
|---|---|---|---|
| D2 | `C1` and `C2` rewritten in place; a standards rule that names a `C` rule replaces it | A comment is a second source that goes stale; `rule-ids` stays flat | New ids; a comment-count lint |

`skills/mf-build/SKILL.md:295`, after the existing sentence, add:
`A rule in the repo's coding standards that names a \`C\` rule replaces it.`

The rows, after:

```markdown
| **C1** | **No explanatory comment** — names, types, structure and tests say what code does; a comment is one of `C2`'s exceptions | delete `# increment the counter`; rename `n` to `retries` |
| **C2** | **The exceptions only** — a short why or a pointer for a constraint code cannot express, a contract or required docstring (`C3`), a tool directive or header | `# why: 0011 design D1` · `# noqa: E501` · `#!/usr/bin/env python3` |
```

### D3

| id | decision | because | rejected |
|---|---|---|---|
| D3 | The bootstrap writes both files from small language-neutral templates, `<name>` the one placeholder; the `AGENTS.md` template names both mandatory context; it halts on any of `CODING_STANDARDS.md`, `CODE_STANDARDS.md` and `CONTRIBUTING.md` | No stack input; one source per rule; the never-overwrite boundary | Generated stack rules; adopting an existing file |

`skills/mf-bootstrap/SKILL.md`:

- `:3`: `write the gate, openspec/, AGENTS.md, CHANGELOG.md, README.md and .gitignore` → `write the gate, openspec/,
  AGENTS.md, CODING_STANDARDS.md, CONTRIBUTING.md, CHANGELOG.md, README.md and .gitignore`.
- `:26`: the halt row gains `` · `CODING_STANDARDS.md` · `CONTRIBUTING.md` `` after `` `CHANGELOG.md` ``.
- `:45`: `no \`openspec/\` directory, and no target path` → `no \`openspec/\` directory, no \`CODE_STANDARDS.md\`, and
  no target path`.

`skills/mf-bootstrap/templates/AGENTS.md.tmpl`: after the blockquote at `:5`, add:

```markdown
## Read first

**Before work, read [the coding standards](CODING_STANDARDS.md) and [the contribution guide](CONTRIBUTING.md):
mandatory shared context.**
```

and in *How a change is cut here*, `Each version is one change, cut, built, checked and released with the
MinionsFactory \`mf-*\` skills.` → `How a change lands is in [the contribution guide](CONTRIBUTING.md).`

`skills/mf-bootstrap/templates/CODING_STANDARDS.md.tmpl`:

```markdown
# <name> — coding standards

The rules this repo's code follows. Mandatory context, named by [AGENTS.md](AGENTS.md).

## Baseline

The MinionsFactory `mf-build` skill's rules apply as written: comments `C1`…`C12`, tests `T1`…`T6`, prose
`P1`…`P13`. Formatter and linter settings stay in their own config files.

## Project rules

None yet. Add one when the project decides it; a rule that names a `C` rule replaces it.
```

`skills/mf-bootstrap/templates/CONTRIBUTING.md.tmpl`:

````markdown
# Contributing to <name>

How a change lands here, and the evidence it carries. Mandatory context, named by [AGENTS.md](AGENTS.md).

## How a change lands

Each version is one change, made with the MinionsFactory skills:

```
mf-plan ──▶ mf-cut-change ──▶ mf-build ──▶ mf-converge ──▶ mf-release
```

`mf-converge` may be skipped; the release then says so.

## The evidence a change carries

- **Its change directory** under `openspec/changes/`: proposal, design, tasks and spec delta.
- **Each `Verify:`**, run by the build before its box is ticked.
- **A green `make gate`** at every phase's commit.
- **A `Change: <change-id>` trailer** on every commit but the bootstrap's.
- **The check loop's findings**, in `.minions/findings/`, when converge ran.
````

### D4

| id | decision | because | rejected |
|---|---|---|---|
| D4 | Both files are also written, outside D18's tree; D18's line names them; a new D46 records where a repo's own rules live | Existing repos stay compliant; the rule outlives the version | The files in D18's tree; no decision |

`docs/decisions.md:240-241`: `with \`CHANGELOG.md\` and \`README.md\`` → `with \`CHANGELOG.md\`, \`README.md\`,
\`CODING_STANDARDS.md\` and \`CONTRIBUTING.md\` ([D46](#d46--a-repos-own-rules-live-in-its-coding-standards-and-contribution-guide))`.

D46, after D18 in `docs/decisions.md`:

```markdown
### D46 · A repo's own rules live in its coding standards and contribution guide

**`CODING_STANDARDS.md` holds a repo's coding rules, `CONTRIBUTING.md` how a change lands and the evidence it
carries; `AGENTS.md` names both mandatory context. `mf-build`'s rules are the portable default: a project rule that
names one replaces it. `mf-bootstrap` writes both; an existing repo adopts them by hand, and the build and converge
read a root `CODING_STANDARDS.md`, `CODE_STANDARDS.md` or `CONTRIBUTING.md` its `AGENTS.md` does not name.**

- **Why:** a rule needs one home every station reads; where none is written, an agent invents one.
- **Rejected:** one combined file · the rules in `AGENTS.md` · a precedence between the coding filenames ·
  migrating existing repos.
```

`README.md`, after the tree at `:63-70`, add:

```markdown
`mf-bootstrap` also writes `CHANGELOG.md`, `README.md`, `CODING_STANDARDS.md` and `CONTRIBUTING.md`; a repo without
them still works ([D46](docs/decisions.md#d46--a-repos-own-rules-live-in-its-coding-standards-and-contribution-guide)).
```

### D5

| id | decision | because | rejected |
|---|---|---|---|
| D5 | The layout scan covers both templates through `_ALSO_WRITTEN`; the Tests-section guard also requires the `AGENTS.md` template to link both files | Extend before adding (`T2`); a template is structure a test may hold (D42) | A new test function |

`tests/test_skills.py:251`: `_ALSO_WRITTEN = ("CHANGELOG.md", "README.md")` →
`_ALSO_WRITTEN = ("CHANGELOG.md", "README.md", "CODING_STANDARDS.md", "CONTRIBUTING.md")`. In
`test_the_layout_scan_reports_every_breach`, the expected list gains
`f"{_TEMPLATES}: no template for \`CODING_STANDARDS.md\`"` and `f"{_TEMPLATES}: no template for \`CONTRIBUTING.md\`"`
after the `README.md` line.

The guard, `tests/test_skills.py:217-228`, after:

```python
# A new repo starts under the rules for tests and reads its standards: the bootstrap's
# `AGENTS.md` states the one and links the other.
# Why: 0026-test-cost design B13; 0039-repository-standards design D5.
_AGENTS_TEMPLATE = "skills/mf-bootstrap/templates/AGENTS.md.tmpl"
_TEMPLATE_TESTS = "## Tests"
_TEMPLATE_LINKS = ("(CODING_STANDARDS.md)", "(CONTRIBUTING.md)")


def _template_tests_problems(base: Path) -> list[str]:
    """Return a line per missing `## Tests` or standards link in the `AGENTS.md` template."""
    text = (base / _AGENTS_TEMPLATE).read_text()
    problems = (
        []
        if _TEMPLATE_TESTS in text.splitlines()
        else [f"{_AGENTS_TEMPLATE}: no `{_TEMPLATE_TESTS}` line"]
    )
    return problems + [
        f"{_AGENTS_TEMPLATE}: no link `{link}`"
        for link in _TEMPLATE_LINKS
        if link not in text
    ]
```

In `test_the_template_tests_scan_reports_a_wrong_heading`, the expected list gains
`f"{_AGENTS_TEMPLATE}: no link \`(CODING_STANDARDS.md)\`"` and `f"{_AGENTS_TEMPLATE}: no link \`(CONTRIBUTING.md)\`"`.

### D6

| id | decision | because | rejected |
|---|---|---|---|
| D6 | MF adopts both files, thin and mostly links; `AGENTS.md` names them and drops the prose-rules and cut bullets they now hold; the patch rule stays | MF uses the layout it generates; `A6` and the release read the patch rule in `AGENTS.md` | Moving the principles or the patch rule |

`AGENTS.md:14-19`, after:

```markdown
**Before work, read [the principles](docs/principles.md), [the decisions in force](docs/decisions.md),
[the coding standards](CODING_STANDARDS.md) and [the contribution guide](CONTRIBUTING.md): mandatory shared
context.**

- **A patch** (`vX.Y.Z`) fixes what the line already does — …
```

The bullets `**Docs are written to \`mf-build\`'s prose rules**…` and `**A change is cut** with the \`mf-cut-change\`
skill.` are deleted; the patch bullet is kept word for word.

`CODING_STANDARDS.md`:

```markdown
# minions_factory — coding standards

The rules this repo's code and docs follow. Mandatory context, named by [AGENTS.md](AGENTS.md), per
[D46](docs/decisions.md#d46--a-repos-own-rules-live-in-its-coding-standards-and-contribution-guide).

## Baseline

`mf-build`'s rules apply as written: comments `C1`…`C12`, tests `T1`…`T6`, and prose `P1`…`P13` for every
markdown doc and CHANGELOG entry: terse, answer first, things named rather than counted.

## Project rules

- **Python 3.12 or later, typed and documented** — the gate runs ruff's `D` and `ANN` rules and strict types;
  tests are exempt from `D`. The settings are `pyproject.toml`'s.
- **A skill's script is a `uv` script** — a PEP 723 header with `requires-python = ">=3.12"` and
  `dependencies = []`, run with `uv run --script`.
```

`CONTRIBUTING.md`:

````markdown
# Contributing to MinionsFactory

How a change lands here, and the evidence it carries: MF is built the way it builds. Mandatory context, named by
[AGENTS.md](AGENTS.md).

## How a change lands

```
mf-plan ──▶ mf-cut-change ──▶ mf-build ──▶ mf-converge or a hand read ──▶ mf-release
```

- **Planned** with `mf-plan` to a hard brief, then cut
  ([D5](docs/decisions.md#d5--a-change-is-planned-with-mf-plan-and-written-with-the-openspec-cli)).
- **Converge or a hand read** — a change of skill text alone may skip converge and be read by hand; the release
  states the skip ([D14](docs/decisions.md#d14--converge-is-optional-and-a-skip-is-stated)).
- **Side by side** — each version in its own worktree; `mf-integrate` merges a moved base in
  ([D44](docs/decisions.md#d44--versions-run-side-by-side-in-worktrees-one-primary-merges-them),
  [D45](docs/decisions.md#d45--one-station-merges-the-default-branch-into-the-next-version)).

## The evidence a change carries

- **Its change directory** under `openspec/changes/`: proposal, design, tasks and spec delta.
- **Each `Verify:`**, run by the build before its box is ticked.
- **A green `make gate`** at every phase's commit.
- **A `Change: <change-id>` trailer** on every commit
  ([D21](docs/decisions.md#d21--every-commit-names-its-change)).
- **The check loop's findings**, in `.minions/findings/`, when converge ran. `.minions/backlog.md` holds only
  check-loop findings ([D16](docs/decisions.md#d16--deferred-work-is-a-card-in-the-repos-backlog)).
````

`docs/README.md`, before the `AGENTS.md` row of *Where the rest lives*:

```markdown
| [`CODING_STANDARDS.md`](../CODING_STANDARDS.md) | the rules this repo's code and docs follow |
| [`CONTRIBUTING.md`](../CONTRIBUTING.md) | how a change lands, and the evidence it carries |
```

### D7

| id | decision | because | rejected |
|---|---|---|---|
| D7 | `SHARED` gains both files; `references.py` reads them; the watch breach is accepted | An honest count and checked links; converge's reading load is a later change's | Leaving the files uncounted; trimming converge here |

`scripts/metrics/reading_set.py:13`, after:

```python
SHARED = (
    "AGENTS.md",
    "docs/principles.md",
    "docs/decisions.md",
    "CODING_STANDARDS.md",
    "CONTRIBUTING.md",
)
```

`scripts/metrics/references.py`: the docstring's first line names `` `CODING_STANDARDS.md`, `CONTRIBUTING.md` ``
beside `AGENTS.md` and `README.md`, and `:48` reads
`files = [root / name for name in ("AGENTS.md", "README.md", "CODING_STANDARDS.md", "CONTRIBUTING.md")]` followed by
`*sorted(root.glob("docs/*.md"))`.

`tests/test_metric_scripts.py`: `test_reading_sets_count_words` adds `"CODING_STANDARDS.md": "eleven"` and
`"CONTRIBUTING.md": "twelve thirteen"`, and expects `9` for `shared` and `13` for `converge`;
`test_broken_references_find_files_headings_and_ids` adds `"CONTRIBUTING.md": "[gone](nowhere.md)\n"` and expects
`4`.

## Tests

No test function is added or removed. The layout scan, the Tests-section guard and both metric-script tests are
extended ([D5](#d5), [D7](#d7)).

| layer | at cut | added | removed | proof |
|---|---:|---:|---:|---|
| Unit test functions | 58 | 0 | 0 | `uv run pytest --collect-only -q \| tail -1` prints `58 tests collected` at the cut and after |
| Integration tests | 0 | 0 | 0 | — |
| End-to-end runs | 0 | 0 | 0 | — |

The scratch bootstrap in phase 4 is the person's, outside the gate.

## Dependencies

None.

## Risks / Trade-offs

- **The installed skills are `main`'s** → phase 4 runs this branch's bootstrap by path, not `/mf-bootstrap`.
- **`converge-reading-set` grows past its watch** → accepted; MF's standards and guide stay near 300 words.
- **0038 ships first and edits `README.md` and the sdd spec** → different sections; `mf-integrate` merges it in
  before this release.

## Migration Plan

```
1 the stations read the standards ─▶ 2 the bootstrap writes them ─▶ 3 MF adopts them ─▶ 4 HUMAN: a scratch bootstrap
```

Each phase ends on a green gate. Nothing is irreversible.

## Verdict

Ready to build. Acceptance: the bootstrap writes and links both files and halts on any existing standards file; the build
and converge read them; `C1` and `C2` state the default; MF's `AGENTS.md` names its own; 58 tests stay green.
