## MODIFIED Requirements

### Requirement: Converge and the release halt on a gate the cut did not plan

`skills/mf-converge/SKILL.md` and `skills/mf-release/SKILL.md` SHALL each run
`skills/mf-converge/scripts/gate_check.py` before judging or releasing, and SHALL halt on its verdict. The script
SHALL export the base and `HEAD` with `git archive` into fresh directories under `.minions/gate-check/`, run make
there with `MAKEFLAGS` and `MFLAGS` cleared, and remove them when it ends. A **gate makefile** SHALL be any file in
the `MAKEFILE_LIST` or a `Reading makefile` line of `make -pn -r -w -d gate` on either export. When no sub-task in
`tasks.md` as the cut commit holds it names both `Makefile` and `` `gate` ``, a branch that changes a gate makefile,
or the `make -n gate` output, SHALL halt. When such a task exists, the script SHALL show the two exports'
`make -n gate` diff, and SHALL halt on a command line the base prints and the branch does not, and on a gate
makefile line the branch adds with a `-` recipe prefix or a variable leading a recipe, a `.IGNORE` or `.ONESHELL`
target, a `SHELL`, `.SHELLFLAGS` or `.RECIPEPREFIX` assignment, or `-i` in `MAKEFLAGS`, unless that task quotes the
line. An export that lacks a path of its tree, or a dry run that fails on either export, SHALL halt, naming the
side. The cut commit SHALL be the one commit that adds the change's `design.md`; more than one SHALL be a
halt.

#### Scenario: Both stations name the dry-run check
- **WHEN** a branch changes a gate makefile — an included makefile, a sub-make's makefile, a recipe line given a
  `-` prefix, a `.IGNORE` target, or `-i` in `MAKEFLAGS` — or a file that changes the gate's dry run, and no cut task
  names the gate recipe
- **THEN** `mf-converge` halts before judging, and `mf-release` before releasing

#### Scenario: A planned gate change drops a command
- **WHEN** a cut task names the gate recipe, and the base's dry run prints a command line the branch's does not
- **THEN** each station shows the two dry runs' diff and halts, unless that task quotes the line

#### Scenario: A planned change adds an ignore mark
- **WHEN** a cut task names the gate recipe, and the branch adds a `-` recipe prefix — after a tab, after a rule's
  `;` or from a variable — a `.IGNORE` or `.ONESHELL` target, a `SHELL` assignment or `-i` in `MAKEFLAGS` that the
  task does not quote
- **THEN** each station halts, naming the line

#### Scenario: The base's gate reads a file the export lacks
- **WHEN** either export lacks a path of its tree — an `export-ignore` path — or `make -pn -r -w -d gate` or
  `make -n gate` fails in it — an included `.env`
- **THEN** each station halts, naming the side and the failure, and compares nothing in the working tree
