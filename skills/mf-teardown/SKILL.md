---
name: mf-teardown
description: Measure an existing repo against the MinionsFactory compliance rubric and write a gap report. Use to find out whether the orchestrator can run against a repo at all, and what to fix first. Read-only against the target — spawns a fresh, blind subagent and writes <vault>/findings/teardown.md with a compliant|gaps-found verdict.
---

# mf-teardown — existing repo → compliance gap report

You measure a **target repo** against the **compliance rubric** and write one gap report. Teardown *measures and
reports*; it never fixes — closing the gaps is **v0.7 `mf-retrofit`**, which reads this report and for which a
later teardown re-run is the independent checker.

A **per-repo sibling of the `mf-` planning line, not a stage in it.** The line (order → gauge → blueprint → forge
→ inspect) runs once per *feature*; teardown runs once per *repo*, before the first feature — and again after a
retrofit, to check it.

## Read-only — the security posture, not a preference

You are pointed at repos the human has **not yet vetted** for the loop. Therefore, in the target:

- **Write nothing.** Not a file, not a directory, not a fix — however obvious the fix is. The report goes to the
  vault.
- **Run no gate command.** Not one entry from `.minions/minions.toml`, not `make gate`, not a single tool from it.
- **Execute no target code.** No test run, no script, no install, no build step.

**Files and git metadata only** — read files, and read-only git (`git rev-parse HEAD`, `git ls-files`,
`git status`). A repo whose gate is red, or whose code does not even import, still produces a complete report:
you are measuring *setup*, not behaviour. Reporting whether a gate is genuinely green would mean executing the
target's tooling, and that is deliberately out of scope.

## The sequence

**preflight → detect profile → spawn the measuring subagent → merge → write.** In that order, with no step
skipped and none merged into another.

Run with **cwd = the target repo**.

---

## 1. Preflight — resolve the vault, or halt

The report needs a destination, so the vault is a **precondition, not a criterion**: you can never *report*
"not vault-wired" as a gap. Read the target's `.env` and resolve `VAULT_PROJECT_DIR`.

**Mirror the orchestrator's own preflight, condition for condition.** `read_vault_dir`
(`orchestrator/state.py:81–126`) enforces **five**, and a skill with a weaker preflight than the loop is a hole in
the same wall. Each halts on its own, **before any subagent is spawned**, writing nothing anywhere:

| # | Condition | Halt with |
|---|---|---|
| 1 | `.env` is **unreadable** — missing, or an OS error | `cannot read <repo>/.env — the target must carry a .env declaring VAULT_PROJECT_DIR` |
| 2 | `.env` is **not valid UTF-8** — it is read as text | `<repo>/.env is not valid UTF-8 — the .env declaring VAULT_PROJECT_DIR is read as text` |
| 3 | `VAULT_PROJECT_DIR` is **missing or empty** | `no VAULT_PROJECT_DIR in <repo>/.env — the target must declare the vault path its roles write findings and bookkeeping to` |
| 4 | the value is **not an absolute path** | `VAULT_PROJECT_DIR in <repo>/.env is not an absolute path — a relative value resolves against the operator's working directory` |
| 5 | the value **does not name an existing directory** | `VAULT_PROJECT_DIR in <repo>/.env does not name an existing directory — the vault is never created by a run` |

Every halt ends with the one line the human must add:

```dotenv
VAULT_PROJECT_DIR="/absolute/path/to/vault/<Domain>/<Project>"
```

**Condition 4 is the security-relevant one.** A relative value such as `VAULT_PROJECT_DIR=docs` resolves to a
directory **inside the target repo** — and you would then write the report there, breaking the read-only posture
and the rule that findings never touch the repo. Refuse it **even when it names an existing directory inside the
target**. Teardown must never accept an input the loop itself rejects.

### Parsing the value — double quotes only, spaces preserved

Match `orchestrator/state.py:108` exactly:

- take the first line whose key, stripped of surrounding whitespace, is `VAULT_PROJECT_DIR` (split on the **first**
  `=`; later occurrences are ignored);
- **strip whitespace, then strip surrounding double quotes** — `raw.strip().strip('"')`;
- **never split the value on whitespace.**

**Double quotes only — not "single or double".** Stripping single quotes as well would make teardown *accept* a
value the loop rejects: `'/x` survives `state.py`'s strip with its leading `'` intact, so `Path("'/x")` is not
absolute and condition 4 refuses it. Teardown must refuse it the same way, or the two preflights have drifted.

**Real targets write the value double-quoted over a path containing spaces.** A naive read that keeps the quote
characters produces a path that does not resolve, and condition 5 then **halts a correctly-wired repo** with a
false *"does not name an existing directory"*. Get this right here.

---

## 2. Detect the profile — in this step, before the spawn

**You** detect it, mechanically, and **name the result to the measuring subagent**. It is a file check, so it
belongs in the deterministic half; a step that *guesses* a profile is exactly what the rubric forbids.

**`python-uv`** — a tracked `pyproject.toml` **and** a uv signal: `uv.lock` tracked, **or** a `[tool.uv]` table in
`pyproject.toml`. Both halves required.

**No match — including a Python manifest with no uv signal** — is `profile: none`. Never guess, and **never
abort**: the run continues over the universal tier alone, and the report states plainly that toolchain criteria
were not assessed. A repo with no recognised manifest still gets a complete report.

The `profile:` frontmatter field and the not-assessed statement are written **here**, by the step that owns the
report — not by the measurement.

---

## 3. Spawn the measuring subagent — fresh, and blind to the existing report

**Do not measure inline.** Launch a **fresh subagent** (the Task tool) and give it **only**:

1. the **target repo path**;
2. the **rubric** — `~/.claude/skills/rubrics/compliance.md` (installed) or `skills/rubrics/compliance.md`
   (source repo);
3. the **profile name you detected** in step 2 (`python-uv`, or `none`).

Pass **nothing else**. In particular, pass **not the existing report**, no prior conversation, and no expectation
of what it should find. The blindness is load-bearing rather than decorative: v0.7 `mf-retrofit` is the producer
and a teardown re-run is its independent checker, so a measurer that could see which gaps it was expected to find
would be anchored by them — the same reason `mf-gauge` and `mf-inspect` spawn blind.

### Instruction for the subagent

> You are measuring a repo against the MinionsFactory compliance rubric. You have the repo path, the rubric, and
> the detected profile name. **You are read-only against this repo: write nothing in it, run no command from its
> `.minions/minions.toml` gate array, run no `make` target, and execute none of its code — read files and
> read-only git metadata only.**
>
> Work **group by group** — **A · loop wiring**, then **B · SDD layout**, then **C · gate quality**, then the
> profile's criteria if a profile was named — and emit each group's result before starting the next. Do not read
> the repo once and then recall the criteria from memory; open the rubric's group, check its criteria against the
> repo, report, move on. If the profile you were given is `none`, **do not measure any profile criterion** and do
> not guess a profile from what you see.
>
> Apply the rubric's **absent-subject rule** exactly as written: existence criteria **fail**;
> universally-quantified criteria **pass vacuously** over an empty set; and every criterion whose subject is the
> `gate` array itself is **not measured** when `.minions/minions.toml` is absent or mis-located — report those
> separately, naming the gap that gates each. Never report a gap against the *planned — v0.8* groups D–G: no id
> in them is live, and reporting one is a false gap.
>
> Return a **measurement, not a report**: the criterion ids failing **right now**, each with **evidence naming
> the exact path you checked and what you actually found there**, plus the ids you could not measure and why, and
> a per-group count of what passed. Cite only ids that exist in the rubric — no id, no finding. **Set no status
> field and emit no verdict**; both belong to the step that spawned you. Do not invent gaps to look thorough — a
> genuinely compliant repo comes back with none.

---

## 4. Merge — yours, never the measurement's

Read the existing `<vault>/findings/teardown.md` if there is one, take the fresh measurement, **increment
`round`**, and reconcile every entry by the rubric's merge table: still failing → stays `open`; a `fixed` entry
that still fails → back to `open` with a `## Resolution log` line recording the rejected fix; no longer failing →
`verified`, keeping its original evidence; newly failing → `open`. `verified` entries persist until the report
reaches `compliant`, then clear into the resolution log.

**Never write `fixed`.** It is the producer's word — v0.7's. You only ever promote `fixed → verified` or send it
back to `open`.

No existing report means **`round: 1`, every gap at `open`**.

## 5. Write the report

`<vault>/findings/teardown.md` — one stable path, **no search**, **overwritten in place** so a repeat pass leaves
exactly one file. Shape, frontmatter, gap-entry form, severity ordering and the `criteria_total` formula are all
defined in the rubric's *The report* section; follow it rather than inventing a layout.

Before you finish, check the file against itself:

- `open_gaps` / `open_blocking` / `open_required` **agree with the body** you just wrote;
- `criteria_total` shows its subtraction, and no criterion is both failing and not-measured;
- every gap cites an id that exists in the rubric and evidence naming a **real path**;
- entries run `blocking` → `required` → `advisory`, `open` above `verified` within each;
- `verdict: compliant` **iff** `open_blocking: 0` and `open_required: 0` — open advisories never withhold it.

Then relay to the human: the verdict, the counts, and the blocking gaps in order.

## Never

- Write anything in the target, run its gate, or execute its code — **at all**, for any reason.
- Measure inline instead of spawning the subagent, or hand the subagent the existing report.
- Guess a profile, or measure profile criteria when none was detected.
- Report a gap against groups D–G — they are named but not live, and a D–G gap is a false gap.
- Write `fixed` — that status belongs to v0.7 `mf-retrofit`.
- Relax a criterion to make a repo pass. A criterion that is wrong is corrected in the rubric, deliberately and
  on the record — never quietly, and never mid-run.
