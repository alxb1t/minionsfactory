# Design — 0006-teardown

Technical decisions for v0.6, repo-side. Full rationale lives in the vault PRD (`prd/v0.6_teardown.md`) and the
design proposition (`prd/v0.6_design.md`); this records the *how*.

## 1. Two artifacts: a shared rubric and its reader

`skills/rubrics/compliance.md` carries the standard; `skills/mf-teardown/SKILL.md` reads it. They are separate
because the rubric has **three** consumers across three versions — teardown as its reader (v0.6), `mf-retrofit` as
its writer against an existing repo (v0.7), `mf-stamp` as its writer against a blank one (v0.8). A rubric living
inside its reader cannot be shared with two producers.

The rubric follows the shape `skills/rubrics/README.md` already establishes for the other three: the (M)/(J) tag on
every criterion, an explicit verdict convention, and a row in the *Which skill uses which rubric* table.

**Note on that table.** Its columns are *Producer* / *Checker*, and compliance inverts the usual timing — its
checker ships **first**, its producers do not exist yet. The row names `mf-retrofit` (v0.7) and `mf-stamp` (v0.8) as
forthcoming rather than leaving the producer cell empty.

## 2. Scope: the loop-readiness groups only — 23 criteria

Tier 1 universal: **A · Loop wiring** (6) · **B · SDD layout** (6) · **C · Gate quality** (4). Tier 2 profile:
**`python-uv`** (7). These are the criteria that decide whether the orchestrator can run against a repo at all.

The **project-shape** groups — D · Product record, E · Docs, F · Vault side, G · CI — were drafted and moved to
**v0.8 `mf-stamp`**, which writes exactly those artifacts and so needs the criteria to know what to write. They
appear here as a **"planned — v0.8"** list in its own section *after Tier 2* — named, one line each, no ids, no
severities. Placing them among live criteria is what would invite a measurement against them.

"Group" and "tier" are different axes and the rubric must not conflate them: **tier** means only the universal ⁄
toolchain split, and D–G will be *universal* (Tier 1) criteria when v0.8 gives them ids.

## 3. Profile detection needs a uv signal, not just a manifest

`pyproject.toml` **plus** `uv.lock` tracked or a `[tool.uv]` table → `python-uv`. A bare `pyproject.toml` is not
enough: a poetry or pip-tools repo would fail `py:lockfile` and `py:gate-commands` at `blocking` for using a
toolchain the profile does not describe. Python without a uv signal degrades to the universal tier exactly as an
unrecognised manifest does — the report says `profile: none` and states plainly that toolchain criteria were not
assessed.

**Detection belongs to the outer step, before the spawn** — not to the measuring subagent. It is a mechanical file
check, so it sits in the deterministic half, and R4 forbids *guessing* a profile: a deterministic step that names
the profile to the judgment step is what makes that guarantee structural rather than a hope. It also keeps the
subagent's return exactly what §4 says it is — failing ids and evidence, nothing else.

So the sequence is: **preflight → detect profile → spawn subagent (repo path + rubric + profile name) → merge →
write.** The `profile:` frontmatter field and the not-assessed statement are written by the outer step, which is
the step that owns the report.

## 4. The blind measurement and the outer merge are different steps

- The skill's **outer step** runs preflight, **detects the profile** (§3), then owns the report: read the existing
  one, merge the fresh measurement into it, write — `profile:` included.
- The **measuring subagent** is spawned fresh with only the target repo path, the rubric, and the **detected
  profile name**. It is blind to any prior conversation **and to the existing report**, and returns a pure
  current-state measurement: failing criterion ids with evidence, **no status field and no verdict**. It never
  reads or writes `findings/teardown.md`.

The blindness is load-bearing for v0.7, not decoration: retrofit is the producer and a teardown re-run is its
independent checker. A subagent that could see which gaps it was expected to find would be anchored by them —
the same reason `mf-gauge` and `mf-inspect` spawn blind.

**Status asymmetry:** `fixed` is the producer's word, `verified` is the checker's. v0.7 marks a gap `fixed`; only a
teardown re-run promotes it to `verified`, or sends it back to `open`. Teardown never writes `fixed`. That is what
makes the pair a producer→checker loop rather than one agent grading itself.

## 5. The report is a findings file, and deliberately not loop-readable

`<vault>/findings/teardown.md` — the reserved id `teardown` in the `findings/` home v0.5 established. One stable
path, no discovery logic, overwritten in place.

**It cannot collide with the loop machinery**, and this was verified rather than assumed:
`findings_path(vault_dir, change_id, role)` (`orchestrator/findings.py:12`) is the single resolution site; its only
callers build paths from an **explicit role list** (`orchestrator/__main__.py:96`, `orchestrator/fanout.py:91`);
and **nothing globs `findings/`** — the package's only `rglob` calls are `orchestrator/specs.py:123,133,224` and
`orchestrator/release.py:521`, over `spec.md` / `test_*.py`.

**Consequence to know:** `FindingsState` (`orchestrator/findings.py:24`) validates
`verdict: Literal["clean", "changes-requested"]`, and teardown emits `compliant | gaps-found`, so
`read_findings_state` would raise on this file. That is correct — teardown is not a role and must never gate a
release — but **v0.7 reads the file itself rather than through the orchestrator.**

**When a criterion's subject is absent, three rules — so one defect is reported once.** Without this, a repo like
isekai (no `openspec/` tree; `minions.toml` at the root where the loop cannot read it) yields different
`open_gaps` depending on how the measurer feels about cascading, which breaks the counts-agree clause and makes two
runs incomparable:

1. **Existence criteria** — the ones asserting a path or file is there (`sdd:specs-tree`, `sdd:changes-tree`,
   `wiring:gate-config`) → **fail**. Genuinely unsatisfied.
2. **Universally-quantified criteria** — "*any* active change carries…", "*shipped* scenarios carry…"
   (`sdd:active-change-contract`, `sdd:scenario-shape`, `sdd:test-binding`) → **vacuously pass** over an empty set.
   The emptiness is already reported by its own existence criterion in rule 1; failing both counts one defect
   twice and would send v0.7 chasing a gap that closes itself.
3. **Criteria whose subject *is* an unreadable file** — `gate:covers-axes`, `gate:contract-agrees` and
   `sdd:checker-in-gate` (its subject is the gate array too), when
   `.minions/minions.toml` is absent or mis-located → **not measured**, each naming the blocking gap that gates
   it. Excluded from `open_gaps` and from `criteria_total`, listed in their own section. Measuring the content of a
   file the orchestrator cannot read would report gaps that evaporate the moment the file moves.

**Rule 3 is deliberately narrow, and the boundary is load-bearing.** It covers *only* criteria whose subject is the
unreadable file itself. It explicitly does **not** cover:

- **`gate:make-mirrors`** — its subject is a **`Makefile`**, not the gate config. An absent `Makefile` `gate`
  target **fails** under rule 1, whatever the gate config is doing; only the *mirror comparison* is unmeasurable,
  and only when a `Makefile` target exists but the array cannot be read. This matters concretely: isekai has
  **no `Makefile` at all**, and R11's acceptance, phase 6 and `proposal.md`'s success criteria all require that
  reported. A rule that silenced it would delete a PRD-required gap.
- **`gate:no-gaming`** — its subject is **tool config** (ruff/ty settings), which is readable regardless of where
  `minions.toml` sits. Never gated by it.

Rule 3 composes with the verdict rule: the gating gap is itself `blocking`, so a repo with not-measured criteria
can never read `compliant` on their account.

**`criteria_total` counts the criteria actually assessed on this run** — the **tier baseline minus rule-3
not-measured criteria**:

```
criteria_total = (23 if a profile matched else 16) − (criteria marked not measured under rule 3)
```

Both halves matter. Counting all 23 on a degraded run would make the report look like it measured seven profile
criteria it never assessed; counting the baseline while rule 3 silently withholds others would make
`open_gaps / criteria_total` mean two different things across reports. The report shows the subtraction next to
the not-assessed statement, so any two runs are comparable.

**Verdict rule:** `compliant` iff `open_blocking: 0` **and** `open_required: 0`. Open `advisory` gaps are listed
and counted in `open_gaps` but do not withhold the verdict, because `sdd:checker-in-gate` is knowingly
unsatisfiable by any target today — a zero-gaps-of-any-severity rule would make `compliant` unreachable for every
repo, minionsfactory included, and the verdict would carry no information.

## 6. `sdd:checker-in-gate` ships `advisory`, with its reason inline

Verified against the code: `pyproject.toml` has **no `[build-system]`** and the package runs from source
(`pythonpath = ["."]`), so the orchestrator cannot be installed into a target's venv and no target can run
`specs check` in its gate today. MF itself satisfies the criterion — `.minions/minions.toml` ends with
`uv run python -m orchestrator specs check --strict`, mirrored in the `Makefile` `gate` target — precisely because
it runs from source. A `blocking` criterion no human could close would be a defect in the report. Making the
checker distributable is its own work → backlog.

## 7. Read-only is the security posture, not a preference

Teardown is pointed at repos the human has **not yet vetted for the loop**. It reads files and git metadata only:
no writes in the target, no gate command executed, no target code run. A repo whose gate is red still produces a
complete report. The skill's own instructions must forbid running the target's tooling — the constraint has to
live where the agent reads it, not only in this document.

The report goes to the vault, never the repo. A repo with no vault wiring is **halted** at preflight, not written
to — which means teardown can never *report* "not vault-wired" as a gap; for an unwired repo the human adds that
one `.env` line by hand first. Accepted deliberately.

**Preflight mirrors the orchestrator's, condition for condition.** `read_vault_dir` (`orchestrator/state.py:81–126`)
already enforces five — `.env` unreadable · not valid UTF-8 · key missing or empty · **value not absolute** · value
not an existing directory — and the fourth is spec-bound
(`change-state:vault-preflight:relative-vault-refused`). Teardown mirrors all five rather than the three an earlier
draft named, because **a skill with a weaker preflight than the loop is a hole in the same wall**: a relative value
such as `VAULT_PROJECT_DIR=docs` resolves to a directory **inside the target repo**, and the outer step would write
the report there — breaking §7's own read-only posture and the never-write-to-the-repo constraint. Teardown cannot
import `read_vault_dir` (it is a skill, and the change adds no code), so it restates the conditions; they are
listed here so the two cannot drift silently.

**Parsing `.env` — strip quotes, keep spaces.** Real targets write the value **double-quoted**, and the vault path
**contains spaces**: `/Users/alexey/Developer/AI_Engineering/isekai/.env:6` is
`VAULT_PROJECT_DIR="/Users/…/Notebook/Lab/isekai"`, and MF's own `.env` is quoted the same way. A naive read that
keeps the quote characters produces a path that does not resolve — which R7 would then report as *"the path does
not resolve to an existing directory"* and **halt**, on a correctly-wired repo. So the resolver strips surrounding
**double** quotes before resolving, and must not split the value on whitespace. This is a false-halt bug waiting in
phase 6's isekai run specifically; it is called out here so the skill is written correctly the first time rather
than debugged during a proving run.

**Double quotes only — matching `orchestrator/state.py:108` exactly** (`raw.strip().strip('"')`). Not "single or
double": stripping single quotes too would make teardown **accept a value the loop's own preflight rejects**, which
is precisely the drift this section exists to prevent. A single-quoted value survives `state.py`'s strip with its
leading `'` intact, so `Path("'/x")` is not absolute and condition 4 refuses it — teardown must refuse it the same
way.

## 8. Trailer convention

Every phase commit carries `Change: 0006-teardown`, **contiguous** with `Co-Authored-By:` — no blank line between,
since git parses the trailer block as the last paragraph.

## 9. Carried caveats (from the feasibility spike)

The blueprint hand-measured minionsfactory against all 23 criteria and reported **A 6/6, B 6/6, C 4/4,
`python-uv` 5/7** — two gaps. **`mf-inspect` round 5 found a third the blueprint missed:** `gate:contract-agrees`
(M, required). Corrected tally: **A 6/6, B 6/6, C 3/4, `python-uv` 5/7 — three gaps.** Four caveats travel with
this change:

**C1 — `py:gate-commands` is the one blocking gap against MF, and the two proving targets disagree about it.** MF's
gate array starts at `ruff format --check` — there is **no `uv sync --locked` step** in `.minions/minions.toml`.
The argument for calling the criterion mis-drafted is that `uv sync` is environment setup rather than a quality
axis. **But the other proving target contradicts that:** isekai's gate array *leads* with `uv sync --locked`
(`isekai/minions.toml:2`), so the criterion as drafted is **satisfied by isekai and failed only by MF** — which
makes MF the outlier rather than the criterion the defect. R11 forbids leaving a blocking gap open, so **phase 6
must decide it on the evidence of both runs**: add the step to MF's array (the likelier resolution now), or correct
the criterion. It was deliberately **not** pre-settled during planning — R11's three-cause resolution exists to
decide it from real runs rather than from a hand-measurement of one repo.

**C2 — `py:pinned-runtime` costs one file.** MF ships no `.python-version`. Closable by editing a tracked file, so
the closability rule closes it inside this change. Pick a pin consistent with `requires-python`.

**C3 — `sdd:active-change-contract` passes vacuously today, and this change makes it live.** MF has no active change
(all three are in `openspec/changes/archive/`), so a criterion about active-change shape currently has nothing to
measure. The moment `0006-teardown/` exists it becomes live and **must satisfy its own criterion** — four artifacts,
a `## Progress` checklist in `tasks.md`, `version: v0.6` in `proposal.md` frontmatter. Phase 6's MF run therefore
measures a repo that phases 1–5 changed.

**C4 — `gate:contract-agrees` fails against MF, and the gate declarations are coupled.** Measured at source:
`.minions/minions.toml` holds **five** commands, `Makefile:7–12` mirrors them exactly, but `README.md:66–69`
declares only **four** — it omits `uv run python -m orchestrator specs check --strict` and writes `uv run pytest`
where the array says `uv run pytest -q`. So the criterion ("the gate written in `CLAUDE.md` / `README.md` matches
`.minions/minions.toml` command-for-command") fails at `required`. Closable by editing a tracked file → closed
inside v0.6.

**This couples to C1.** MF declares its gate in **four** places — `.minions/minions.toml`, `Makefile:7–12`,
`README.md:66–69`, and **`CLAUDE.md:56–65`** ("## The quality gate") — and two criteria police the agreement
(`gate:make-mirrors`, `gate:contract-agrees`). So if phase 6 resolves C1 by adding `uv sync --locked` to the array,
adding it *only there* **breaks `gate:make-mirrors`**, which currently passes. Any change to the gate array lands
in every declaration in the same commit. Phase 6 should treat C1 and C4 as one edit, not two.

**One boundary phase 2 must settle first:** `CLAUDE.md:56–65` states its gate as **prose axes** ("`pytest` — all
tests pass"; "`ruff format --check` + `ruff check`"), not a command list, while `README.md:66–69` is a literal
`bash` block. Whether a prose declaration is in `gate:contract-agrees`' scope decides whether MF has one failing
declaration or two — so the criterion states its own (M) boundary (phase 2) before phase 6 measures against it.

**Also worth knowing:** all three MF gaps are closable by editing a tracked file, so **the closability rule's
backlog branch has no live instance at v0.6.** Its motivating example — `record:change-trailer` on the trailer-less
merge commit `6149a64` — left for v0.8 with group D. The rule is insurance, not a planned path.

**And a density note:** **6 of the 23** criteria are (J)/(M+J) at blocking or required severity
(`wiring:claude-md`, `gate:covers-axes`, `gate:make-mirrors`, `gate:no-gaming`, `py:gate-commands`,
`py:import-resolution`) — a *higher* proportion than the pre-rescope draft, since judgment-heavy group C stayed
while `docs:freshness` left. Group C is where this version's judgment risk concentrates. R5's rule applies: a (J)
criterion that flips pass/fail across two runs of an unchanged repo is a **rubric defect** — sharpen it until it
decides the same way twice, or drop it to `advisory`.

## 10. A resolved disagreement with the vault design proposition

`prd/v0.6_design.md` originally stated the change would ship "**no** `specs/` subdir". That was wrong:
`validate_change` **requires** the directory to be present, so omitting it would fail preflight, and the cited
`0004-planning-skills` precedent in fact ships `specs/README.md`
(`openspec/changes/archive/0004-planning-skills/specs/README.md`) rather than omitting the directory. The change
ships `specs/README.md` marking the delta N-A, and **the vault proposition was corrected in place at `mf-inspect`
round 1** — so the two agree and no divergence remains. Recorded here because the four-artifact contract beating a
blueprint claim is the kind of call that should stay visible after the documents stop disagreeing.

## 11. Rubric size and the one-context bound

23 criteria × 4 required fields puts `compliance.md` at roughly 110–140 lines — about 3× the largest existing
rubric (39/41/44). The measuring subagent must hold the rubric *and* scan a whole repo, so the skill instructs it to
work **group by group (A → B → C, then the profile)** and emit per-group results, rather than reading the repo once
and recalling 23 criteria from memory.
