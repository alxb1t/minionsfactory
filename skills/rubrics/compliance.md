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
