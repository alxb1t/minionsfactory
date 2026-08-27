# Design — 0007-pm-side-process-standard

The technical *how* for the v0.7 migration. Every decision below is settled; nothing here is an open question.

## 1. One root replaces another, and the parameter goes

`vault_dir: Path` is threaded from `__main__.py` into `findings.py`, `driver.py`, `fanout.py` and `release.py`.
Every call site that receives it already receives `repo`, so the migration is a **substitution followed by a
deletion**, not a re-plumbing:

| Symbol | Before | After |
|---|---|---|
| `findings_path` | `(vault_dir, change_id, role)` → `<vault>/findings/…` | `(repo, change_id, role)` → `repo/.minions/findings/…` |
| `halt_report_exists` | `(vault_project_dir)` → `<vault>/HALT.md` | `(repo)` → `repo/.minions/HALT.md` |
| `build_inputs_block` | `(…, version, vault_dir)` + a `Context:` line | `(…, version)`, no `Context:` line |
| `prepare_release` | `(verdict, repo, vault_dir, …)` | `(verdict, repo, …)` |
| `read_vault_dir` · `verify_vault_access` | resolve + assert the vault | **deleted** |

The single-resolution-site property `findings_path` exists for is preserved exactly: fan-out, converge and release
keep resolving the identical path for identical inputs, and the location stays one edit away.

**`.minions/` is already ignored** (`.gitignore`: `.minions/*` with `!.minions/minions.toml`), so findings, the
HALT report and the backlog land ignored with no `.gitignore` rule added. The comment above that rule claims
`events.jsonl` would otherwise sweep a vault path into history — false once the Inputs block stops carrying one,
and phase 10 corrects it.

## 2. The preflight is deleted, not made optional

`read_vault_dir` reads an absolute path out of a target's `.env` and hands it to code that writes there. A guard
would narrow the hole; deletion closes it. The entry point's two call sites go with the functions, and `minions
run` against a repo with no `.env`, no key and no settings grant proceeds straight to the change-state read.

`.env` and `.env.example` **keep their shape as empty scaffolding** — the files stay, the key and its comment
block go, and `.env.example` declares zero keys. `.claude/settings.local.json` is untracked, so removing its vault
grant is an operator edit this change documents and cannot test.

## 3. The release gate's deferred-work predicate reverses, deliberately

Today the backlog guard **fails closed**: a missing current-release section blocks, because a vault backlog is a
long-lived document whose absence means something went wrong. The new file is per-version and lives in ephemeral
`.minions/`, where **absence means nothing was deferred** — the common case. So the predicate becomes: *any list
line in `.minions/<version>_backlog.md` blocks the release*, checkbox state irrelevant, and a missing file passes.

An item leaves that file by being fixed and removed, or exported by the human. The residual is accepted and
stated: a wiring bug that silently stopped writing the file would read as clean, mitigated because the file's
contents are read by a human at release time.

## 4. Needle sets get their own root sets

The retired-vocabulary guard already ships two needle sets with two root sets, and the file argues why: one set's
exclusions were reasoned for its own needle and do not transfer. This change adds a third — six retired **vault**
symbols — over `("orchestrator", "prompts", "docs", "README.md")` **plus `skills/`**.

One root set crossed with all needles cannot go green: `implementation_plans` is a live needle of the *plan* set,
and `skills/rubrics/compliance.md` legitimately names it in check text this change keeps.

The needles are the six **dead symbols** — `VAULT_PROJECT_DIR`, `vault_dir`, `vault_project_dir`,
`read_vault_dir`, `verify_vault_access`, `release_log`. `vault_project_dir` is listed separately although
`vault_dir` looks like a substring of it: it is not, and without it a doc could ship a stale
`halt_report_exists(vault_project_dir)` signature and pass. The word *vault* and the token `<vault>/` are **not**
needles — the vault still exists, and the vault-side skills must be able to name what they resolve.

**Recommended widening, carried from the blueprint:** the root set should also cover `CLAUDE.md` and
`.env.example`. Both are cleared by requirements in this change, but they sit outside the root allowlist while
falling inside the whole-tree grep the success criteria state, so a later regression into either would be caught
by nothing.

## 5. The scan lands in stage C, and no carve-out is ever declared

`skills/mf-teardown/` holds twelve `VAULT_PROJECT_DIR` lines plus a `read_vault_dir` reference until phase 16
clears them, so a scan closing stage B would go red against the build-order rule this change otherwise follows —
*no phase asserts the absence of a needle while a live dependent still names it.*

The alternative was a dated `skills/mf-teardown/` exclusion in stage B that stage C deletes. It was **declined**: a
suppression that must be remembered to be removed is the failure mode the scan exists to catch. Instead stage B
performs the deletions and stage C extends the scan **once**, over the full root set, already clean.

**Accepted cost:** phases 14–16 carry deletions nothing asserts. They are caught by phase 17, before the tag, and
never reach the default branch.

## 6. The audit skill's report moves into the repo it measures

`mf-teardown`'s report lands at `.minions/findings/teardown.md` — the same home as every other findings file, under
the reserved id `teardown`. This reverses a property three documents advertise, and each is rewritten with it: the
README's read-only claim and its report home, the skill's own *"the report is never written in a repo being
measured"*, and — the copy that actually steers a run — the compliance rubric's report section.

The skill's preflight condition 6 (*"the report is never written inside the repo being measured"*) is retired **by
decision, not by moot-ness**, because its three named outcomes do not dissolve evenly:

1. *the report written inside the target, voiding the read-only guarantee* — now true **by design**; the documents
   selling the old guarantee are rewritten rather than left standing.
2. *overwriting another project's report via a traversing path* — genuinely gone: the path derives from the vault's
   `repo:` with no operator-supplied string to traverse.
3. *a re-run's merge reading placed markdown as prior state* — **real, and accepted.** Every target is the
   operator's own repo, so whoever can write `.minions/` can already write the code being measured: the report is
   not a new trust boundary but inside an existing one. Bounded further by the sequence — the measuring subagent is
   spawned **blind to the existing report**, so seeded prose can reach the merge and the gap history, never the
   measurement. **Revisit if the skill is ever pointed at a repo the operator did not write.**

The skill stays read-only where it matters: it makes no change to the target's **tracked** tree, runs no gate
command and executes no target code. The documents say that, instead of claiming it writes nothing at all.

**The redaction rule outlives the criteria that motivated it.** The evidence-redaction constraint — *never
reproduce a value read from a target's `.env` or settings file, never an absolute filesystem path; cite the shape
and the verdict* — exists **twice**: in the audit skill, and in the compliance rubric, which is the copy the
measuring subagent actually follows. Both teach it through worked examples built on `wiring:env-example` and
`wiring:vault-perms`, the two criteria this change deletes. **The examples are rewritten; the rule is not
touched.** It does not rest on the target being untrusted — it rests on **destination**: values and home-directory
paths do not belong in a report the human keeps and may commit, whoever wrote the repo they came from. That reason
survives both the criteria and this change's move of the report into the target's own working tree.

## 7. Two notes for whoever executes this

- **Phase 10 must stay one phase.** `specs check --strict` reports a dangling key for any test marker whose
  scenario is gone, so splitting the spec removal from its fourteen test deletions puts the gate red at the
  boundary.
- **The emptied capability.** Removing the vault-write preflight leaves `openspec/specs/change-state/` holding no
  requirement. The checker derives orphans from shipped scenarios, so an empty spec file is green either way;
  this change leaves the file in place as a **tombstone**, matching how it already records the reader deleted in
  the previous version, rather than deleting the capability directory.

## 8. The change id derives from the version, and the collision rule forks

`mf-forge` computed `NNNN` by scanning `openspec/changes/` for the highest existing number and adding one. Read
from a vault-rooted session that scan crosses the seam and restarts numbering at `0001`, so it had to go — and it
is **deleted rather than re-rooted**, because it only ever implemented a coincidence: `NNNN = (major × 100) +
minor`, zero-padded, reproduces every shipped id, stays monotonic past the 1.0 boundary so `select_change`'s
"highest numeric id wins" survives, and needs no repo read at all.

Deriving the number means it can already be taken, and the first rule written here was a blanket halt: **stop
rather than increment past it**, because a directory holding this version's number means two changes claim one
version, which nothing downstream can resolve — the `Change:` trailer, the change directory and the folded delta
all key on the same id. That rationale is right and is what the rule still protects. The blanket halt was not:
phase 3's review found it dead-ends the routine fix pass that `mf-line` and `mf-inspect` both prescribe, where
`mf-forge` re-renders a change and halts on the directory it wrote itself.

So the rule **forks**, and each arm preserves the same reasoning. HALT on some other `NNNN-*` holding the number,
and HALT on a different change at the same path — both are two changes claiming one version. HALT on anything
under `archive/`: that change has shipped, its delta is folded, and it is the only artifact its trailer traces
back to. **Proceed** only when re-rendering *this* change live, replacing the directory's own prior contents —
re-rendering one change does not make two changes claim one version, so the halt has nothing to protect there.
