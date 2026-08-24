# Rubric — repo compliance (is this repo MinionsFactory-ready?)

The definition of "done" for a **target repo**: is it wired well enough for the orchestrator to run against it at
all, and is its spec-driven layout the shape the loop expects? **`mf-teardown`** measures a repo against this
rubric and writes a gap report; **`mf-retrofit`** (v0.7) and **`mf-stamp`** (v0.8) are its writers. See
[README](README.md) for the (M)/(J) split.

Unlike the three planning rubrics, this one's **checker ships first** — v0.6 delivers the reader and the producers
follow. That is why the rubric lives here rather than inside `mf-teardown`: three skills across three versions
consume it, and a rubric living inside its reader cannot be shared with two producers.

**Scope at v0.6 — loop readiness only.** Tier 1 groups **A · Loop wiring**, **B · SDD layout** and **C · Gate
quality**, plus the Tier 2 **`python-uv`** profile. The project-shape criteria (product record, docs, vault side,
CI) are named under *Planned — v0.8* and are **not measured** here; a repo failing every one of them is still
`compliant` at v0.6.

## How a criterion is written

Every criterion carries exactly these fields, none empty:

- a **stable id** — `group:slug`, unique file-wide, and it does not change once published (gap reports, the
  backlog and v0.7's resolution log all cite it by id);
- an **(M) / (J) tag** — mechanical, judgment, or **(M+J)** for a mechanical floor with a judgment layer on top
  (the split is defined in [README](README.md));
- a **severity** — `blocking` · `required` · `advisory`, defined below, never unset;
- a **what is checked** line naming the **exact path or key** measured — so two runs of an unchanged repo measure
  the same thing;
- a **fix pointer** — one line on what closes the gap.

## Verdict + severities

A run emits **`verdict: compliant | gaps-found`** — not the `clean | changes-requested` the planning rubrics use,
because compliance is graded over three severities rather than `blocking | nit`:

- **`blocking`** — the orchestrator cannot run against this repo at all.
- **`required`** — below standard: the loop runs, but the repo is not compliant.
- **`advisory`** — a nit. Listed and counted, but it never withholds the verdict.

**`compliant` iff zero `blocking` and zero `required` gaps are open.** Open `advisory` gaps do not withhold it:
`sdd:checker-in-gate` is knowingly unsatisfiable by every target today, so a zero-gaps-of-any-severity rule would
put `compliant` out of reach for every repo — MinionsFactory included — and the verdict would carry no
information.

## Tier 1 — universal criteria (language-agnostic)

Nothing in Tier 1 names a language, a toolchain or a tool. Everything toolchain-specific lives in Tier 2, so a
second toolchain is a new Tier-2 section and no edit here.

### A · Loop wiring — can the orchestrator start at all?

- **`wiring:git-repo`** · (M) · `blocking`
  - **Checked:** the repo root holds a `.git/` and `git rev-parse HEAD` resolves to a commit — the driver diffs
    every phase against `HEAD` and detects an advance from it.
  - **Fix:** `git init` and land one commit before pointing the loop at the repo.
- **`wiring:gate-config`** · (M) · `blocking`
  - **Checked:** `.minions/minions.toml` exists **at that path** (not the repo root), is **tracked**
    (`git ls-files .minions/minions.toml` returns it), and declares a non-empty `gate` array.
  - **Fix:** move or create the file at `.minions/minions.toml` and commit it — the orchestrator reads that path
    and no other, so a root-level `minions.toml` is invisible to it and the gate is unreadable.
- **`wiring:vault-perms`** · (M) · `blocking`
  - **Checked:** `.claude/settings.local.json` — `permissions.allow` carries `Read(...)`, `Edit(...)` and
    `Write(...)` globs over the vault project dir, and `permissions.additionalDirectories` lists that dir or an
    ancestor of it.
  - **Fix:** add the three globs and the `additionalDirectories` entry; a role denied the vault cannot write its
    findings file, and a findings file that never lands reads as not-clean.
- **`wiring:claude-md`** · (M+J) · `blocking`
  - **Checked:** a root `CLAUDE.md` exists; **(M)** it carries no unfilled `{{placeholder}}` and no absolute vault
    path (the path belongs in `.env` only); **(J)** it describes the contract the repo actually runs — it names no
    retired `implementation_plans/` model, and its account of where progress lives matches the repo.
  - **Fix:** fill the placeholders, move any vault path into `.env`, and rewrite stale sections onto the in-tree
    `openspec/changes/<id>/` contract.
- **`wiring:env-example`** · (M) · `required`
  - **Checked:** `.env.example` is tracked, declares the **same keys** as `.env` (`VAULT_PROJECT_DIR` at minimum),
    and every value is a placeholder — no real path, no secret.
  - **Fix:** commit `.env.example` with placeholder values; the real values stay in the gitignored `.env`.
- **`wiring:gitignore`** · (M) · `required`
  - **Checked:** `.gitignore` ignores `.env`; ignores `.minions/*` with a `!.minions/minions.toml` negation (run
    artifacts out, gate config in); and does **not** ignore the lockfile.
  - **Fix:** add the `.env` line and the `.minions/*` + `!.minions/minions.toml` pair; drop any lockfile entry —
    the lock is tracked so an environment can be reproduced from it.

### B · SDD layout

- **`sdd:specs-tree`** · (M) · `blocking`
  - **Checked:** `openspec/specs/` exists and holds at least one `<capability>/spec.md`.
  - **Fix:** create `openspec/specs/<capability>/spec.md` describing behaviour the repo already has — the living
    spec is what a change's delta folds into.
- **`sdd:changes-tree`** · (M) · `blocking`
  - **Checked:** `openspec/changes/` exists and holds an `archive/` subdirectory.
  - **Fix:** create `openspec/changes/archive/` and commit it; a released change is moved there, not deleted.
- **`sdd:active-change-contract`** · (M) · `blocking`
  - **Checked:** every active change — each `openspec/changes/<id>/` that is not `archive/` — carries all four
    artifacts (`proposal.md` · `design.md` · `tasks.md` · `specs/`), a `## Progress` checklist in `tasks.md`, and
    a `version: vX.Y` key in `proposal.md`'s leading frontmatter. A repo with **no** active change passes with
    nothing to measure — its empty `openspec/changes/` is reported by `sdd:changes-tree`, not here.
  - **Fix:** add the missing artifact, the `## Progress` checklist or the `version:` key — the orchestrator's
    preflight refuses the run without them, before any role is spawned.
- **`sdd:scenario-shape`** · (M) · `required`
  - **Checked:** every `#### Scenario:` in `openspec/specs/**/spec.md` carries a `- **Key:**` bullet and a
    `- **Layers:**` bullet.
  - **Fix:** add the missing bullets; the key is what binds a scenario to the test that proves it.
- **`sdd:test-binding`** · (M) · `required`
  - **Checked:** tests carry a `spec(<key>)` marker binding them to a scenario, or a `spec_exempt(<reason>)`
    marker declaring them structural, and **both** marker names are registered in the project's test-runner
    manifest — an unregistered marker is silently ignored and binds nothing.
  - **Fix:** register both markers in the manifest, then mark each test with one of them.
- **`sdd:checker-in-gate`** · (M) · `advisory`
  - **Checked:** the **last** entry of the `gate` array in `.minions/minions.toml` invokes the spec-binding
    checker, so a broken scenario↔test binding fails the gate rather than being found by a human.
  - **Fix:** add the checker as the final gate command.
  - **Why `advisory`, stated inline:** MinionsFactory is **not distributable today** — it ships no packaging
    metadata and runs from its own source tree — so no target repo can install the checker into its environment,
    and no target can satisfy this criterion however willing its owner is. A `blocking` criterion nobody could
    close would be a defect in the report rather than a finding, so it ships `advisory` and does not withhold
    `compliant`. MinionsFactory itself satisfies it precisely because it runs the checker from source. Making the
    checker distributable is its own work → backlog; the severity is revisited when it lands.

### C · Gate quality

- **`gate:covers-axes`** · (M+J) · `blocking`
  - **Checked:** the `gate` array in `.minions/minions.toml` covers all four quality axes — **format** ·
    **lint** · **typecheck** · **test**. **(M)** each axis maps to at least one array entry (one may serve two).
    **(J)** the mapping is genuine: a formatter run in rewrite mode is not the format *check*, a command that
    reports findings without failing does not cover its axis, and a linter is not counted as the type checker.
  - **Fix:** add a command for each uncovered axis. A gate missing an axis still exits `0`, so the loop advances
    on it and the missing axis is never enforced again.
- **`gate:contract-agrees`** · (M) · `required`
  - **Checked:** every place `CLAUDE.md` or `README.md` declares the gate **as commands** matches the `gate` array
    in `.minions/minions.toml` **command-for-command** — the same commands, in the same order, with the same
    flags. A flag difference is a mismatch: two commands that differ in their arguments are two different
    commands, and the human types the one the doc shows.
  - **Boundary — what counts as a declaration (the (M) line):** **only a literal command block** — a fenced code
    block, or a list whose items are command lines. A **prose axis list** — one that names the quality *axes*
    rather than the commands (*"tests pass"*, *"format + lint clean"*, *"strict type-check clean"*) — is
    **out of scope for this criterion.** Command-for-command is a mechanical comparison and it needs commands on
    both sides; grading prose against an array would turn an (M) criterion into a judgment call that can decide
    differently on two runs of an unchanged repo, which is the rubric defect this rubric refuses to ship. Prose is
    not left unchecked, it is checked by the criteria that own it: `gate:covers-axes` owns whether the axes are
    the right ones, and `wiring:claude-md`'s (J) layer owns whether `CLAUDE.md` describes the contract the repo
    actually runs.
  - **Fix:** rewrite the declaring block to the array verbatim, or delete the block and point at
    `.minions/minions.toml` — one source of truth, quoted or referenced, never paraphrased.
- **`gate:make-mirrors`** · (M+J) · `required`
  - **Checked:** a root `Makefile` declares a `gate` target whose recipe runs the same commands, in the same
    order, as the `gate` array in `.minions/minions.toml`. **(M)** the target exists and its command lines are
    compared against the array. **(J)** a difference in *form* that runs the same command — a variable in place
    of a literal, a line continuation — is not a mismatch; a missing, extra or reordered check is.
    **A repo with no `Makefile`, or one with no `gate` target, fails this criterion outright** — there is nothing
    to mirror with, and the human's gate and the orchestrator's have no way to stay in step.
  - **Fix:** add or correct the `Makefile` `gate` target so the gate a human types and the gate the orchestrator
    runs cannot drift apart.
- **`gate:no-gaming`** · (J) · `required`
  - **Checked:** every waiver in the tool configuration the gate's commands read — an ignore, an exclude, a
    per-path override, a severity downgrade — is **declared and defensible**: it scopes a rule where the rule
    adds no value, and never hides a defect. Read each one and ask what it lets through. Relaxing a **docstring**
    rule over a **test tree** is defensible — the test names are the documentation. Switching a whole check off
    repo-wide, excluding the very package the gate exists to check, or downgrading an error to a warning so the
    command exits `0`, is not.
  - **Fix:** delete the waiver and fix what it was hiding, or narrow it to the smallest scope that earns it and
    record why it is there — an undeclared waiver is how a gate goes quietly green.

## Tier 2 — toolchain profiles

A profile describes what the **toolchain** must look like. Exactly **one** profile is measured per run — the one
the reader's outer step detects mechanically *before* the measurement starts — and its criteria are added to the
Tier-1 set. No profile criterion restates a universal one: Tier 1 asks whether a gate exists, is declared
consistently and covers the four axes; a profile asks whether the toolchain-specific files and commands are the
ones that toolchain requires.

### Profile `python-uv`

**Detection rule (mechanical).** A tracked `pyproject.toml` **and** a uv signal — `uv.lock` tracked, **or** a
`[tool.uv]` table in `pyproject.toml`. Both halves are required. A `pyproject.toml` alone is not enough: a poetry
or pip-tools repo would then fail `py:lockfile` and `py:gate-commands` at `blocking` for using a toolchain this
profile does not describe. A Python repo with **no** uv signal therefore degrades to the universal tier exactly as
an unrecognised manifest does — `profile: none`, toolchain criteria not assessed, and the report says so.

- **`py:manifest`** · (M) · `blocking`
  - **Checked:** `pyproject.toml` declares the project — a `[project]` table with a `name` — and a
    `requires-python` constraint.
  - **Fix:** add the `[project]` table with `name` and `requires-python`; nothing resolves the environment
    without them.
- **`py:lockfile`** · (M) · `blocking`
  - **Checked:** `uv.lock` exists at the repo root and is **tracked** (`git ls-files uv.lock` returns it).
  - **Fix:** `uv lock`, then commit the file — an untracked lock cannot reproduce the environment a gate ran in,
    so a green gate proves nothing about the next machine.
- **`py:gate-commands`** · (M+J) · `blocking`
  - **Checked:** the `gate` array in `.minions/minions.toml` is the **uv form** — `uv sync --locked` ·
    `ruff format --check` · `ruff check` · `ty check` · `pytest` — each invoked through `uv run` where the tool
    needs the project environment. **(M)** all five are present as array entries. **(J)** arguments may differ
    (`pytest -q`, an explicit path) as long as the entry is the same check.
  - **Fix:** bring the array to the uv form; a missing `uv sync --locked` means the gate runs against whatever
    the environment happens to hold rather than the lock.
- **`py:pinned-runtime`** · (M) · `required`
  - **Checked:** `.python-version` exists at the repo root and pins a concrete interpreter version consistent
    with `pyproject.toml`'s `requires-python`.
  - **Fix:** write the pin into `.python-version` and commit it, so every machine and CI resolve the same
    interpreter.
- **`py:lint-select`** · (M) · `required`
  - **Checked:** the ruff lint `select` list — `[tool.ruff.lint] select` in `pyproject.toml`, or the equivalent
    in `ruff.toml` — includes at least `E`, `F` and `I`.
  - **Fix:** add the missing codes; without them the lint axis passes on code it never looked at.
- **`py:dev-deps-isolated`** · (M) · `required`
  - **Checked:** the lint, type-check and test tooling sits in `[dependency-groups] dev` (or the project's
    declared dev group), **never** in `[project] dependencies`.
  - **Fix:** move the tooling out of the runtime dependency list — a consumer installing the package should not
    be made to install its test tools.
- **`py:import-resolution`** · (M+J) · `required`
  - **Checked:** the package resolves for the test runner **and** the type checker by exactly **one** declared
    mechanism — a src layout with an editable install, **or** a `[tool.pytest.ini_options] pythonpath` entry —
    not both. **(M)** which mechanisms `pyproject.toml` declares. **(J)** the declared one actually resolves the
    package the gate checks, and the type checker sees the same tree the test runner does.
  - **Fix:** pick one mechanism, delete the other, and confirm both tools still resolve the package — two
    mechanisms is how a repo passes locally and fails in CI.

### Adding a profile (the extension rule)

A second toolchain is a **new Tier-2 section** — not an edit to Tier 1, and not a change to the skill:

1. add a `### Profile <name>` section here with its own **detection rule**: the mechanical file signals that
   identify the toolchain, specific enough that no repo can match two profiles;
2. give it criteria in the same field convention as everything above, with ids in the profile's own namespace
   (`py:` belongs to `python-uv`);
3. change **no Tier-1 criterion** — a would-be profile criterion that turns out to be language-agnostic belongs
   in Tier 1 instead, and moves there rather than being written twice;
4. change **no skill logic** — the reader detects a profile, names it to the measurement, and reports
   `profile: none` when nothing matches. A new profile adds a detection rule to this file, not a branch to the
   skill.

## Planned — v0.8: groups D–G, named but not measured

Four further groups are drafted and belong to **v0.8 `mf-stamp`**, which writes exactly those artifacts and so
owns the criteria that describe them. **No id in these groups is live.** They carry **no ids, no severities and
no measurement** at v0.6, and `mf-teardown` never reports a gap against them:

- **D · Product record** — a changelog in a known format, a version line aligned across the change, the changelog,
  the manifest and the tag, change-id commit trailers, and a README that says what the project is.
- **E · Docs** — the documented docs layout, the module-doc shape, freshness against the code it describes, and
  anti-bloat.
- **F · Vault side** — the vault project dir's own layout, and a product-requirement doc present for the version
  in flight.
- **G · CI** — the gate runs on every push.

**A repo failing every one of these is still `compliant` at v0.6.** The verdict is taken over the live criteria
only — loop readiness — and reporting a D–G gap at v0.6 is a false gap, not thoroughness.

These are **groups, not a tier**: "tier" means only the universal ⁄ toolchain split above, and D–G will be
**universal (Tier 1)** criteria once v0.8 gives them ids.
