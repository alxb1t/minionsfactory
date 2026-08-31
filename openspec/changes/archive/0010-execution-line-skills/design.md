## Context

See `proposal.md` — *Why*. What shapes the approach is the state of the tree, not the motivation:

- **Three surfaces already describe one method.** `orchestrator/` + `prompts/` implement a deterministic
  fan-out → converge → release in Python, unit-tested behind `FakeProvider`/`FakeGate` and spec-bound under
  `openspec/specs/{fanout,converge,release}/`; `prompts/reviewer.md` carries its own seven-axis rubric. The
  `v0.9` release, though, was driven **by hand** through pasted prompts that dispatch the *community* skills.
  `.minions/` holds no `events.jsonl`, no `status.json` and no `findings/` today. This change adds the third
  surface knowingly and declares the boundary rather than pretending there is one line.
- **`v0.8` deleted a `skills/` directory** — 1753 lines of planning rubric — for a recorded reason: *"a runner
  whose rubric is a standing maintenance debt costs more than the measurement is worth."* That reason is a live
  constraint on this change, not history.
- **The gate is six commands** declared in `.minions/minions.toml` and mirrored in four places. Nothing here
  touches it.
- **This is the last version.** No `v0.11` follows to correct an overrun, so scope discipline substitutes for a
  maintenance version.

## Goals / Non-Goals

**Goals:**

- Four skills, hand-authored from prompts that each drove a real release, invocable without a paste.
- The *contract* around the review engines is owned here; the review *content* is adopted.
- Every invariant the loop rests on has either a check or a stated obligation — never an unstated hope.
- The new tracked surface is inside the guard that already exists for tracked role prompts.

**Non-Goals (design-level, beyond the proposal's scope):**

- No behaviour of `orchestrator/` changes, and no prompt under `prompts/` is edited. The two lines coexist.
- No rubric is written for review, security or simplify.
- No plugin or marketplace packaging; no second-repo run inside this version.
- `docs/sdd.md` is not edited. It states the method the orchestrator implements; a skill's deviation from it is
  declared **in the skill**, because editing the page to match a skill would make it contradict shipped code —
  the defect class this project has already paid once to fix.
- No skill for the grill or cut stations. Those stay an interactive session and a paste.

## Decisions

### D1 — Two declared lines, not one resolved line

`skills/mf-*` is the human-invoked line that ships releases; `orchestrator/` + `prompts/` is the automated line
under construction. **Measurement:** collapsing them would mean rewriting `prompts/{reviewer,security,simplify}.md`
to dispatch community skills, which the headless read-only role profile may not be able to run — unprovable in a
doc-only change, so it would be invention. The cost accepted is that one review axis has two rubrics
(`prompts/reviewer.md` and `/code-review`). **Alternative rejected:** ship only export + release and keep the
check loop in `python -m orchestrator run` — that contradicts what `v0.9` actually did. The boundary is declared
in `CLAUDE.md`, in one place, additively.

### D2 — Constants resolve from disk; the gate never guesses

`mf-converge` and `mf-release` read the gate command list from `.minions/minions.toml`'s `gate` array and **halt**
naming the file if it is absent or empty. Never ask, never infer. **Measurement:** an inferred gate is the one
wrong guess that is *invisible* — a discovered `make test` exits 0 and the loop converges on nothing.
`docs/sdd.md` Part II already makes a tracked `.minions/minions.toml` a blocking readiness item, so a fallback
would contradict the method. `<version_file>` and `<binding_check>` are legitimately absent in many repos and
degrade to "none" with a stated skip rather than a halt.

### D3 — Personal skills, installed by symlink

`skills/mf-*/SKILL.md` is tracked here; `make install-skills` symlinks each into the operator's personal skills
directory. **Measurement:** a symlink means an edit in the tree is live in the next session with no re-install,
which is what an experiment the operator is iterating on needs. **Alternative rejected:** packaging the repo as a
plugin marketplace — tracked and versioned, but the install *copies*, so every edit needs a re-install; wrong for
a version whose purpose is to iterate and observe. `v0.8` removed symlink targets before deleting the directory
they pointed at; that ordering is a constraint on any future deletion, not an argument against symlinks.

### D4 — `openspec validate` stays out of the gate

The evidence `v0.9` owed came in **green**: `openspec validate --all --strict` reports `Totals: 10 passed, 0
failed`, exit 0, once the `change-state` tombstone was deleted. That settles validity and moves the blocker:
`openspec` is unpinned operator tooling on `PATH`, and `.github/workflows/ci.yml` has **no Node step at all**.
Adding it would mean a Node install plus a pin in CI and four mirror edits, and a bad upstream release would turn
CI red in a version with nothing after it to fix it. **Decision: no.** Recorded here because the reason is now
supply-chain cost, not validity, and that is the finding a real project should inherit.

### D5 — Four skills; the seam test is a failure prevented

A boundary earns its place only if the failure it prevents can be named:

| boundary | failure prevented |
| --- | --- |
| `mf-build` ∥ `mf-converge` | the producer judging its own work |
| `mf-converge` ∥ its subagents | three opinions from one reader — stations in the conductor's context verify nothing |
| `mf-backlog-export` ∥ `mf-release` | a vault absolute path loaded into the session that commits and tags; a release station clearing its own precondition |
| `mf-converge` ∥ `mf-release` | the loop that declared convergence also archiving and tagging on it |

And the boundary **deliberately not drawn**: the fix pass is a station *inside* `mf-converge`, not a skill and
not a mode on `mf-build`. A build∥fix seam prevents nothing — both produce, both commit, neither judges — so it
would buy a fourth skill's worth of duplicated conventions text for no failure prevented. This also matches the
proven shape: `v0.9`'s conductor dispatched the fix as Station 2, between reading verdicts and verifying.

### D6 — `/simplify` runs inside `mf-build`, first, fixing in place

`mf-build` closes with a `/simplify` pass, re-gates, and commits it separately. Review and security then fan out
over a diff that **includes** those edits. **Measurement:** this is simpler than holding `/simplify` to
report-only *and* it preserves the top invariant — review verifies simplify's work, so no station verifies its
own. **Alternative rejected:** running simplify last, after convergence — it would land unreviewed edits after
the final station has spoken, breaking the invariant silently rather than loudly. Two consequences are accepted
explicitly: there is **no simplify findings file at all**, and `mf-release` therefore **declares simplify out by
name** rather than tolerating an absent file, so that *a missing findings file is not clean* does not erode into
*a missing file is fine*. This is a declared deviation from `docs/sdd.md`'s three-read-only-station *Check*, and
the deviation is stated in `mf-converge` and `mf-release` themselves.

### D7 — The frozen diff, and what actually reads it

`mf-converge` writes `.minions/findings/<change-id>_diff.patch`: round 1 holds `<base>..HEAD`, and each verify
round **overwrites** it with the scoped fix range `<previous head>..<new head>` — the verify pass judges the fix,
not the branch again. **Measurement of who reads it:** the built-in `/code-review` takes a target (current diff,
a PR number, a branch or a path) and `/security-review` takes none at all, so **neither parses a patch file**;
the *station subagent* does, as fallback material. The subagent scopes its skill to the range, and only if what
it reviewed was empty or clearly wrong does it read the patch and review that — stating in its Summary which it
did. Mandating the patch as the sole channel was rejected: it strips the file context `/code-review`'s own
blame/history/comment agents depend on, degrading the very engine being adopted. Per-round patch files were also
rejected — the per-round record already exists as each findings file's `head:` field plus the append-only
`## Resolution log`, and a second record drifts.

### D8 — `/security-review` on a clean tree: measured, not assumed

Its scope statement is *"pending changes on the current branch"*, which after `mf-build` commits every phase
could be read as an empty working tree. **Measurement:** `.minions/v0.9_backlog.md:3` records the `v0.9` fan-out
at head `043645f`, which `git log` shows is phase 3's **commit** — so the tree was clean — and that fan-out
produced findings **S1 and S2**, both carried and exported. It reviewed committed branch work on a clean tree.
The caveat in the source note is a hedge, not an observed failure; the fallback in D7 stays because the failure
mode is silent, and D9 is what actually closes it.

### D9 — An empty review is not clean

Twin of *a missing findings file is not clean*. A station that resolved zero files **must not** write
`verdict: clean`; it writes `changes-requested` with one finding — scope resolution failed — and `mf-converge`
halts on it. Each station states the file and commit count it actually reviewed, and the conductor compares that
against the count it printed when it froze the diff. **Measurement:** this is the only hole where a clean verdict
is indistinguishable from a real one, and it is the one machine-checkable sibling available for the
self-verification invariant, which left the acceptance table for being unforceable.

### D10 — `mf-converge` preconditions, all halts

Tree clean · **every `## Progress` box in `tasks.md` ticked** · derived range non-empty · `.minions/minions.toml`
present with a non-empty `gate` · gate green before round 1. The progress check is load-bearing: an unticked box
means the build halted or was interrupted, and reviewing that state yields a verdict about a change that does not
exist yet. The gate-green check is the one usually skipped: without it a red gate at round 1 is attributed to a
station's findings instead of to the build, and the fix pass chases the wrong thing. The base is derived
(`git merge-base` against the default branch) and the run **halts if base equals HEAD** — an empty range is the
worst available failure, because every station returns clean over nothing.

### D11 — Round cap 3, then halt with the state intact

On exhaustion `mf-converge` halts, leaves every findings file exactly as it stands, and reports which blockers
are still `open` by id. No auto-escalation, no widened fix pass, no third opinion: a loop that cannot converge in
three rounds is a plan problem, and the halt *is* the finding.

### D12 — The change id is an explicit, required parameter

Every skill that takes an id takes it explicitly and halts without it — never `max()` over the directory
numbers, never "there is only one so it must be that". **Measurement:** the id keys both the findings path and
the commit trailer, so a wrong id makes the loop read a *different* change's verdicts and converge anyway.
`orchestrator/state.py:101-122` (`select_change`) does infer from the highest numeric prefix; that is the
automated line and is deliberately left alone here. The two lines disagree on this point, and the skills are the
side that is right.

### D13 — `mf-build` ships unattested, deliberately

Its source prompt carries no *Proven on* section — unlike the other three, each of which records a real run. This
version is doc-only and has no build phases, so `mf-build` cannot be attested here and is named as such in the
non-goals. **Alternative rejected:** letting `mf-build` build this change's own last mechanical phases. Evidence
from markdown-writing phases would not transfer to building code, and evidence that looks like proof while giving
none is worse than none; it would also force an install-mid-change ordering dependency into `tasks.md`.

### D14 — `skills/` becomes the tenth scanned root

**Measurement:** `skills/` *was* a scanned root under `v0.7`'s seven-root set and left the tuple in `v0.8` only
because the directory was deleted. Re-creating it without re-adding it re-opens a gap already closed once, and a
skill is a role prompt. The deciding argument is elsewhere, though: `v0.9`'s fold was a **no-op** (`skip_specs`;
the archive move carried the whole step), so `mf-release`'s most intricate step — MODIFIED replaces the whole
requirement matched by title, preamble preserved verbatim, verify-after-fold, fold-and-archive in one commit —
has **never run against a real delta**. One `MODIFIED` block exercises all of it in the run already planned. The
cost is one test edit and one phase; the return is the only evidence that step will ever get.

### D15 — Where paths may appear

No `SKILL.md` contains an absolute path, a `~/` expansion, or any path outside the repository it is invoked in.
The *installer* names the destination directory — that is `Makefile`'s and `README.md`'s job, not a skill's. The
one exception is `mf-backlog-export`, which takes the vault path as an **explicit parameter with no default**,
resolves nothing itself, searches for nothing, and commits nothing. The vault reaches the repo; the repo never
reaches the vault.

## Seams

This change adds no code seam. It is tested at three that already exist:

- **`tests/test_conventions.py`'s scan seam** — the shared root tuple, asserted verbatim in both scan tests, with
  both reintroduction tests planting every needle in every root. Widening it to ten is the only test edit.
- **`.minions/minions.toml`'s `gate` array** — the skills read the gate from the same declaration the
  orchestrator reads it from, so a target repo needs no skill edit.
- **The findings contract on disk** — `.minions/findings/<change-id>_<role>.md`, frontmatter shape-validated,
  verdicts read from disk and never from a station's report. The skills write into the contract
  `orchestrator/findings.py` already parses; nothing new is invented.

## Risks / Trade-offs

- **Two lines are maintained where one method exists** → declared in `CLAUDE.md` rather than resolved, and no
  version follows to resolve it. Accepted openly; this is the version's largest honest cost.
- **`mf-build` is unproven** → named in the non-goals; its first real-project run is its evidence.
- **`/simplify` fixes in place, unheld** → its edits are verified by review, not by being read-only, and the
  deviation from `docs/sdd.md` is declared in the skills that carry it.
- **A community skill's behaviour can change under us** → the contract layer (`mf-converge`) is what this repo
  owns, and each station must declare the scope it reviewed, so a behaviour change surfaces as a visible report
  line rather than a silent clean verdict.
- **`skills/` re-appears under a name `v0.8` deleted** → the change says so explicitly; the deletion reason was
  1753 lines of rubric for a process no longer run, and it does not apply to four files of conduct for the
  process that is.
- **The end-of-change run corrects the very skills it runs** → correction is bounded by *file set*, not by
  count: text-only inside `skills/`, and every other divergence is a one-line field note in this file. A numeric
  cap was rejected as an invitation to bundle.

## Verdict

**`feasible-with-caveats`.** Three caveats, carried and named as such:

1. **`mf-build` ships unattested** (D13) — deliberate; its evidence is a real project.
2. **The two lines coexist** (D1) — declared, not resolved, with no version after this one to resolve it.
3. **`/simplify` runs unheld inside `mf-build`** (D6) — a declared deviation from `docs/sdd.md`'s
   three-read-only-station *Check*, mitigated by review verifying its edits.

## Acceptance corrections — converge round 1

Review round 1 (R1, R2, R5) removed behaviour that three of this change's **ticked** acceptance lines had
specified. `mf-release` archives `openspec/changes/<change-id>/` whole as this change's permanent record and
nothing gates `tasks.md`, so a later author — or a fresh `mf-build` resuming from `tasks.md` + git, the resume
path `CLAUDE.md` mandates — would read those lines as the specification and re-introduce the defect. The
corrections are stated here once and the three task lines point at this section rather than being rewritten:
what was accepted stays legible, and what superseded it is one clause away.

- **2.7 — the fix station does *not* carry the nits.** As accepted, the fix station carried non-blocking findings
  to `.minions/<version>_backlog.md`. R1 found that Step 5 routes a both-clean round straight to the report, so
  on the *normal* round-1 outcome no fix station runs and nothing is carried anywhere. The carry became a
  **conductor** step in Step 5, run on every round whatever the verdicts, and the fix station's bullet was
  inverted to a prohibition, so exactly one writer owns that file. The rest of 2.7 — the frontmatter-counter
  prohibition, the scoped re-freeze — stands as written.
- **2.6 — the count comparison's baseline is *this round's* freeze, not 2.3's.** As accepted, the conductor
  compared each station's reported counts against the counts printed at the round-1 freeze. R2 found that Step 6
  re-freezes to the scoped range `<previous head>..<new head>`, so a round-2 station correctly reporting one file
  over a one-file fix range read as a scope failure and halted a loop one step from converging. The baseline is
  now the freeze the round under judgement was frozen from, and Step 6 prints its own numbers before any station
  speaks. The two fail-closed rules themselves are unchanged.
- **4.6 — the closing does *not* re-run the gate.** As accepted, `mf-release`'s closing re-ran the gate on the
  released tree. R5 found that this put the gate *after* the release commit and the annotated tag, over a tree
  the station has no permission to repair. The gate moved to Step 4.3 — after the changelog cut, before the
  commit and the tag — and Step 5 now says outright not to re-run it. The report contents 4.6 accepted, and its
  prohibition on merging and pushing, stand as written.

One further acceptance line is stale for a reason **not yet fixed**: 5.1's *"removes exactly those"* describes
`uninstall-skills` as removing exactly the symlinks `install-skills` created, while the target matches on **name**
and checks no link target. That is review finding R9 — non-blocking, still open, carried to
`.minions/v0.10_backlog.md`. It is recorded here so the archived record does not carry the claim unqualified.

## Field notes

<!-- Filled during the end-of-change run: one line per divergence between what a skill says and what happened,
     for the real projects that inherit these practices. Empty until the run. -->
