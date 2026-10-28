# Release patches — design

`mf-release` names one `<tag>` for minors and patches, `AGENTS.md` says what a patch holds, and six cards are paid
down. Verdict: ready to build. Scope is [the proposal](proposal.md); behaviour is [the delta](specs/sdd/spec.md).

## Context

Premises were re-checked on `main` at `577dba5` (v0.31.0) before the cut.

| evidence at the cut | implication |
|---|---|
| `skills/mf-release/SKILL.md` writes `<version>.0` at `:39,89,136,169,177,183,204,224,228` | each becomes `<tag>` ([D1](#d1)) |
| D19's line (`docs/decisions.md:271`) knows `vX.Y` only | it gains the patch form ([D1](#d1)) |
| v0.30.1 shipped as tag `v0.30.1`, heading `[0.30.1]`, subject `chore(release): v0.30.1` (`08cfb5f`) — not the text's `.0` | the text catches up with what shipped |
| A6 (`skills/mf-cut-change/SKILL.md:219`) defers to `AGENTS.md`, which says nothing about patches | [D2](#d2) |
| `I16` (`skills/mf-build/SKILL.md:60`, `skills/mf-cut-change/SKILL.md:162`), `T5` (`skills/mf-build/SKILL.md:258`, `skills/mf-cut-change/SKILL.md:205`, `skills/mf-converge/SKILL.md:446`) and the coverage-trace row (`skills/mf-converge/SKILL.md:209`) accept *the decision that retires it*, wherever it was added; D39 (`docs/decisions.md:336`) and *Never weaken the gate to pass* (`docs/principles.md:96`) say *a named decision* | `0028·S1` ([D3](#d3)) |
| `skills/mf-bootstrap/templates/AGENTS.md.tmpl:21-22`: a removed test is *mapped to the test that carries its proofs* | `0028·R3` ([D3](#d3)) |
| `_inside` (`skills/mf-build/scripts/metrics.py:66-70`) passes `--quiet`, and `metric_argv` (`:56-58`) hands it to `uv` as an option | `0030·S2` ([D4](#d4)) |
| `_scrubbed` (`skills/mf-build/scripts/metrics.py:153-162`) blocks a match after `/` and before anything but `/ \ ' " whitespace :` — so `file:///Users/…`, `(/Users/…)`, `HOME=/Users/…;` and `/Users/….` pass unscrubbed | `0030·R12` ([D4](#d4)) |
| `tests/test_metrics.py:133-134,159` assert `/opt<root>/c` stays unscrubbed — the `t` of `opt` precedes the root's `/` | the expectation holds under D4; the test only gains cases ([D4](#d4)) |
| `skills/mf-plan/SKILL.md:38` names no way to find the default branch | `0032·N1` ([D5](#d5)) |
| `README.md:53` links `openspec/changes/0027-migrate-to-agents/design.md#smoke-evidence`; the change is under `openspec/changes/archive/` | `broken-references` = 1 in `metrics/changes/0032-mf-plan.json` ([D5](#d5)) |
| `0023·R7`'s fix edits `openspec/changes/archive/0023-backlog-paydown/design.md` | closed as moot ([D6](#d6)) |
| `uv run pytest --collect-only -q \| tail -1` prints `38 tests collected` | [Tests](#tests) |

## Goals / Non-Goals

**Goal:** a patch is cut, built and released as itself by the text, and the line's small known defects are gone.

**Non-goals:** see [the exclusions](proposal.md#not-in-this-change).

## Decisions

The grilling settled these choices (the brief's Q2–Q10); the build does not reopen them.

### D1

| id | decision | because | rejected |
|---|---|---|---|
| D1 | `mf-release` names `<tag>` once and uses it everywhere it wrote `<version>.0` | One value; minors unchanged | A separate patch path through the skill |

`skills/mf-release/SKILL.md:39`, after:

```markdown
derive it from a filename. Below, `<version>` is that value — `vX.Y`, or `vX.Y.Z` for a patch — and `<tag>` is
`<version>.0` for `vX.Y`, `<version>` itself for `vX.Y.Z`: `v0.31` → `v0.31.0`, `v0.31.1` → `v0.31.1`.
```

Every other `<version>.0` becomes `<tag>`; the CHANGELOG heading becomes `## [<tag> without the leading v>] -
<today>`. The version file is bumped to `<tag>` without the `v`.

`docs/decisions.md` D19's diagram, after:

```
proposal.md `version: vX.Y`    =  CHANGELOG `## [X.Y.0]`  =  tag `vX.Y.0`  =  the version file
proposal.md `version: vX.Y.Z`  =  CHANGELOG `## [X.Y.Z]`  =  tag `vX.Y.Z`  =  the version file
```

### D2

| id | decision | because | rejected |
|---|---|---|---|
| D2 | `AGENTS.md` states what a patch may hold | A6 defers to it; this change is then a patch the text allows | A rule in the cut alone |

`AGENTS.md`, a bullet under *The record*:

```markdown
- **A patch** (`vX.Y.Z`) fixes what the line already does — backlog cards, a rule that misstates the behaviour, a
  defect. It adds no station, parameter, decision or requirement, and may modify a requirement to correct it.
```

### D3

| id | decision | because | rejected |
|---|---|---|---|
| D3 | A test is retired only by a decision **in force at the base** | A branch must not certify its own test's removal (`0028·S1`) | A decision the same branch adds; a carve-out by test kind |

The phrase *the decision that retires it* becomes *a decision in force at the base that retires it* in `I16` (both
carriers) and `T5` (all three); the coverage-trace row's *no decision in force retires* becomes *no decision in
force at the base retires*; D39's and the principle's *a named decision* become *a decision in force at the base*.
D42 is in force at the base, so a phrase scan is retired as before. The template's bullet, after:

```markdown
- **Deleted or merged only as a change's `## Tests` table names it** — each removed test mapped to the test that
  carries its proofs, or to a decision in force at the base that retires it.
```

### D4

| id | decision | because | rejected |
|---|---|---|---|
| D4 | `_inside` refuses a `script` starting with `-`; the scrub blocks a match only on a name character | `uv` reads a leading `-` as an option (`0030·S2`); a home after `//`, `(` or `=`, or before `.`, `;` or `)`, is still a home (`0030·R12`) | `--` in `metric_argv`, untested with `uv run --script`; a `file://` special case |

`_inside`: `script.startswith("-")` → not inside, so the catalogue is broken (exit 2), with the existing message.

`_scrubbed`'s pattern, after: a match is blocked only when a name character touches it —

```
(?<![\w.~-])<the path>(?![\w-]|\.\w)
```

so `<root>s/a` and `<home>ice/b` stay as they are, `<home>.bak` stays, and these are scrubbed:
`file://<home>/x` → `file://~/x` · `(<home>)` → `(~)` · `HOME=<home>;` → `HOME=~;` · `<home>.` → `~.`.
`/opt<root>/c` stays as it is — the `t` of `opt` is a name character — so no expectation in `tests/test_metrics.py`
changes; the test gains the cases above.

### D5

| id | decision | because | rejected |
|---|---|---|---|
| D5 | `mf-plan` names its default branch as the bootstrap does; `README.md` links the archived 0027 design | `0032·N1`; `broken-references` back to 0 | — |

`skills/mf-plan/SKILL.md:38`, after:

```markdown
- the default branch is the one `git symbolic-ref --short refs/remotes/origin/HEAD` names after `origin/`, or
  `main` when that fails; `<ref>` is that branch, `<sha>` is `git rev-parse --short <ref>`;
```

`README.md:53`'s target becomes `openspec/changes/archive/0027-migrate-to-agents/design.md#smoke-evidence`.

### D6

| id | decision | because | rejected |
|---|---|---|---|
| D6 | `0023·R7` is closed as moot; converge runs | An archive is never repaired; the collector and a test-retirement rule change | Editing the archived design; a hand read |

`0023·R7` is listed under `backlog:` so the release deletes it; its design stays as archived.

## Tests

The gate stays offline. No test is added, removed or merged: existing tests are extended (`T2`).

| layer | at cut | added | removed | proof |
|---|---:|---:|---:|---|
| Unit test functions | 38 | 0 | 0 | `uv run pytest --collect-only -q \| tail -1` prints `38 tests collected` at the cut and after |
| Integration tests | 0 | 0 | 0 | — |
| End-to-end runs | 0 | 0 | 0 | — |

| test, extended | file | gains |
|---|---|---|
| `test_a_broken_catalogue_exits_2_naming_the_entry` | `tests/test_metrics.py` | a `script = "--quiet"` entry, exit 2 |
| `test_a_failing_metric_is_unavailable_with_its_reason` | the same | the `paths` metric also prints the `file://`, `(…)`, `HOME=…;` and trailing-`.` cases, each expected scrubbed; its existing expectations hold |

## Dependencies

None.

## Risks / Trade-offs

- **A test retired by a decision now waits a version** → the decision lands first; D42's phrase scans are
  unaffected.
- **The scrub matches after `/`, `(` or `=`** → over-scrubbing a tracked reason is harmless; leaking a home is not.
- **The links are live** → other projects see the edited skills during the build, unless the operator freezes them.

## Migration Plan

```
1 the patch form ─▶ 2 who retires a test ─▶ 3 the collector ─▶ 4 the small text ─▶ simplify ─▶ converge ─▶ release
```

Each phase ends on a green gate. Nothing is irreversible. This change's own release runs the edited `mf-release`
through the live links and tags `v0.31.1`.

## Verdict

Ready to build. Acceptance: no `<version>.0` left in `mf-release`; `AGENTS.md` states the patch rule; every
retirement rule says *in force at the base*; the extended tests pass; `mf-plan` names `symbolic-ref`; README's
link resolves.
