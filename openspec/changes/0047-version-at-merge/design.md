# Version at merge — design

How a version gets its identity from its change id, and its number from its release. Verdict at the end: ready to build.

## Context

- The number reaches the code through the branch name and `proposal.md`'s `version:`: `change_of`
  (`skills/mf-integrate/scripts/integrate.py:105`), `Version` (`skills/mf-ship/scripts/conduct.py:213`), `_change_on`
  (`:242`), `find_version` (`:295`), `change_version` (`skills/mf-build/scripts/metrics.py:220`).
- `Version.tag` (`conduct.py:227`) feeds `stage_of`, `_check_release`, `advance` and `report`. A release's commit is
  `chore(release): <tag>`, and the branch is kept after the merge, so its tip names the tag.
- `v*` finds open versions in `conduct.py:275`, `:295`, `integrate.py:172`, `mf-cut-change`'s Step 1 and
  `mf-release`'s precondition 10.
- The build draws a page before any number exists (`skills/mf-build/SKILL.md:196`), and `change_version` exits without a
  `version:`. The release collects at its Step 4.2b, after the archive.
- `plan: vX.Y` in a findings file is read by nothing.

## Goals / Non-Goals

**Goals:** no number exists before the release; the branch name carries no number; a tag is computed, never chosen.

**Non-Goals:** the merge order, which stays cut order; dependencies; a `major` bump.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The branch is the change id, and open versions are found by that shape | the id is unique and never renamed, so this removes a coupling and adds nothing | a new ticket id; a slug with a number |
| [D2](#d2) | `next_tag.py <bump>` computes the tag | a fixed rule is not an agent's arithmetic | the cut choosing the number; prose steps at the release |
| [D3](#d3) | `conduct.py` reads the tag from the branch tip | no number exists anywhere until the release | storing it in `.minions/` |
| [D4](#d4) | `change_version` returns `unreleased`, above every release | the draft page's baseline is the highest tracked release | skipping the draft page |
| [D5](#d5) | The skills' text follows, and the cut takes `bump` | one word per thing | keeping `version` as an option beside `bump` |
| [D6](#d6) | D19, D20 and D44 are edited where they live | A7 | a new decision |

### D1

`Version` holds `change` and `tree`. `branch`, `version` and `tag` go, and every `version.branch` becomes
`version.change`. `_change_on` goes.

```python
def _tag_of(primary: Path, change: str) -> str | None:
    """Return the tag the branch's tip names, or None before a release."""
    found = RELEASE.fullmatch(_subject(primary, change))
    return found[1] if found else None


def _holds(primary: Path, change: str) -> bool:
    """Return whether a branch holds its change, active or just released."""
    folder = f"openspec/changes/{change}"
    active = _show(primary, change, f"{folder}/proposal.md") is not None
    return active or _tag_of(primary, change) is not None
```

`open_versions` lists with `"--list", "[0-9]*"`, and keeps a name that `CHANGE_ID.fullmatch`es, has a linked worktree
that is not the primary, and passes `_holds`. `find_version` returns `Version(change, trees.get(change))` when
`refs/heads/<change>` exists and `CHANGE_ID.fullmatch`es, else None.

`integrate.py`: `change_of` goes. `next_version` lists with the same pattern, takes the lowest id among the names that
`CHANGE_ID.fullmatch`, and prints `next: <change-id> · <worktree> · ready`. `unready` becomes `unready(cwd, change, tree)`.

`status` prints `<change-id> · <stage>`.

### D2

`skills/mf-release/scripts/next_tag.py`, a stdlib `uv` script with the repo's PEP 723 header. It takes `minor` or
`patch`, reads `git tag --list 'v*'` in the cwd, and prints one line. Any other bump, or a failing git, exits 2.

| highest `vX.Y.Z` tag | `minor` | `patch` |
|---|---|---|
| `v0.40.0` | `v0.41.0` | `v0.40.1` |
| `v0.9.2` beside `v0.10.0` | `v0.11.0` | `v0.10.1` |
| none | `v0.1.0` | `v0.1.0` |

The comparison is numeric, per tag part. A tag of another form, such as `v1` or `nightly`, is ignored.

### D3

`stage_of`: `tag = _tag_of(primary, change)`; `tag` set and `_tagged` → `released`, the reason as today.

`_check_release`: after the merge check, `tag` None → `<change> has no release commit`; then the tag and push checks
as today. `advance` appends `_tag_of` after a passing check. `report` shows the tag when `_tag_of` is set and `_tagged`,
else `no tag`.

A run's log, once this ships, names versions on `v*` branches `report` no longer finds: that one report prints
`<change> · no version branch`, until the next run.

### D4

```python
UNRELEASED = "unreleased"
```

`change_version` returns it when the proposal holds no `version:`, in place of its `SystemExit`. `version_key` opens
`if version == UNRELEASED: return (sys.maxsize,)`, so `_below` keeps every tracked release.

### D5

`mf-cut-change`, parameters table: the `version` row → `| `bump` | yes | `minor`, or `patch` |`, and "not the version from
the id" → "not the bump from the id". Step 1: "each `git branch --no-merged <default-branch> --list '[0-9]*'` names", and
the "version is free" bullet goes. Step 4 opens: "The branch is the change id." The slug sentence goes, the worktree
command is `git worktree add -b <change-id> <path>/<change-id> <default-branch>`, and the switch is
`git switch -c <change-id>`. Step 6: "`proposal.md` opens with `bump: <bump>` frontmatter". Step 11 is unchanged.

**I1**, in `mf-build` and `mf-cut-change`, the change-must column: "be committed, on its own branch, named by its change
id and cut from the default branch; the tree is clean after the cut commit". **I13**, both: "open `proposal.md` with
`bump:` frontmatter — `minor`, or `patch`". In `mf-cut-change`, "writing it from the `bump` parameter; reading it". In
`mf-build` Step 1: "`proposal.md` opens with frontmatter holding a `bump:` key."

The inference rule, in `mf-build`, `mf-converge` and `mf-release`, item 2, after: "The candidate's branch is its change
id. The current branch differs → **halt**, naming both." In `mf-simplify`: "Its branch is its change id; the current
branch differs → **halt**, naming both."

`mf-converge`: "The release version is the change's `proposal.md` `version:` frontmatter." goes, and `plan: vX.Y` →
`plan: <change-id>`.

`mf-release`, the paragraph on the release version, after:

> **The tag** comes from the change's `bump:`, read from the leading frontmatter of its `proposal.md`: anything but
> `minor` or `patch` → **halt**. `uv run --script <this package>/scripts/next_tag.py <bump>` prints `<tag>`,
> `<this package>` resolved from this installed skill, e.g. `minor` after `v0.40.0` → `v0.41.0`. A failure or a missing
> `uv` → **halt**. `<version>` is `<tag>` with a trailing `.0` dropped: `v0.41.0` → `v0.41`, `v0.41.1` → itself.

Its precondition 10 lists with `--list '[0-9]*'`, and "(match its version and slug to the branch)" goes. Step 3 opens:
"Write `version: <version>` below `bump:` in `openspec/changes/<change-id>/proposal.md`."

`mf-plan`, the `the release can ship it` row → `| the bump | `minor` or `patch`, a patch against what root `AGENTS.md`
says one may hold; a mismatch goes to the person |`; its close-out line → `Next: /mf-cut-change <id> <bump> brief=<path>`.

`mf-integrate`, Step 2: `next: <change-id> · <worktree> · ready`, and "The branch is the change id."

`mf-ship`, the `status` row: `<change-id> · <stage>`. Its stage A line, paying `0046·R3`: "a halt stops only its version;
a crash stops the run".

`tests/test_skills.py`'s `_METRICS_SCRIPTS` gains `("mf-release", "scripts/next_tag.py")`.

### D6

`docs/decisions.md`:

- **D19**, the bold paragraph opens "A change's version, assigned at its release, the `CHANGELOG.md` release, the
  annotated tag and the project's version file are one value." Add a line under the table: "The cut declares
  `bump: minor` or `bump: patch`; `next_tag.py` computes the tag, and the release writes `version:` into the proposal it
  archives."
- **D20**, the bold paragraph, before → after: "`<digits>-<slug>`, never renamed once cut." → "`<digits>-<slug>`, never
  renamed once cut, and the name of its branch."; "a version is numbered at its cut, so planned work carries a name, not a
  number" → "a version is numbered at its release, so work carries a name, then an id, and a number last". The example:
  "`0011-cut-and-gate`, on the branch `0011-cut-and-gate`." Its **Why**: "A number given before the cut" → "A number given
  before the release".
- **D44**, before → after: "Ids and versions are reserved at the cut" → "Ids are reserved at the cut".

`openspec/config.yaml`, the `proposal.md` line: "`proposal.md` opens with `bump: minor` or `bump: patch` frontmatter. The
skills read it, and the CLI neither emits nor checks it."

`README.md`, the tree: `0033-<slug>/` and `0034-<slug>/`.

## Tests

`next_tag.py` gets one unit test, in a scratch repo (`T1`). Metrics gets a step in the test that already reaches the state
(`T2`). The run tests keep their flows, and lose the version argument.

| layer | at cut | added | removed | proof |
|---|---:|---:|---:|---|
| Unit test functions | 75 | 1 | 0 | `uv run pytest --collect-only -q \| tail -1` prints `75 tests collected` at the cut, `76 tests collected` after |
| Integration tests | 0 | 0 | 0 | — |
| End-to-end runs | 0 | 0 | 0 | — |

| test | holds |
|---|---|
| `test_next_tag_follows_the_bump` | every row of [D2](#d2)'s table, a tag of another form ignored, a bad bump exits 2 |

Tests edited:

| test | edit |
|---|---|
| `test_previous_is_the_highest_version_below` | a step: `previous_release(tmp_path, "unreleased")` is the highest tracked; a proposal with no `version:` reads `unreleased` |
| every test in `tests/test_conduct.py` | `_version(root, change, progress)` cuts `change` on a branch of that name, its proposal `bump: minor`; `status` lines are `<change-id> · <stage>`; branch names in subjects and messages are the change id |
| `test_each_check_passes_only_on_disk_evidence` | a step for `<change> has no release commit` |
| every test in `tests/test_integrate.py` | `_version(root, change, ticked)`; `next: 0009-early · …` |

`_fake`'s `release` takes `v0.<n>.0`, `<n>` being one more than the count of `git tag -l`. No test is deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- **The change ships under the rules it replaces** → its branch and `version:` follow today's skills, which the run reads
  from the primary. The next cut is the first under the new rules, and the live proof.
- **A branch named like an id that is not a version** → `_holds` drops it: it holds no change folder and no release
  commit.
- **`report` on the last old run prints `no version branch`** → once, and only that line.
- **A release recovered by hand** → the recovery drops the tag and the release commit, so the next release computes the
  number again.

## Migration Plan

```
1 next_tag and metrics ─▶ 2 identity ─▶ 3 skill text ─▶ 4 the record ─▶ release
```

Each phase ends on a green gate. Nothing is irreversible. No compatibility path: old `v*` branches are merged history,
archived proposals keep `version:`, and no version is open when this one lands.

## Verdict

Ready to build. Acceptance: `next_tag.py` covers its table; a draft page reads `unreleased`; the run and integrate tests
pass on branches named by the change id; no `v<version>_` is left in `skills/` or `docs/`; D19, D20 and D44 say so.
