## ADDED Requirements

### Requirement: The release ships only a reviewed head

When converge ran, `skills/mf-release/SKILL.md` SHALL halt unless `HEAD` equals the `head:` of both findings files.
`skills/mf-converge/SKILL.md` SHALL offer a **catch-up round**: when both findings files are clean and their `head:`
is an ancestor of `HEAD` but not `HEAD`, it runs one verify round over `head..HEAD`, counted against the cap, with no
pickup.

#### Scenario: The release compares HEAD with the judged head, and converge names the catch-up round
- **Key:** `sdd:converge-audit:reviewed-head`
- **Layers:** unit
- **WHEN** `skills/mf-release/SKILL.md` and `skills/mf-converge/SKILL.md` are scanned
- **THEN** `mf-release` names the check `HEAD equals the head:`
- **AND** `mf-converge` names `catch-up round`

### Requirement: Anchored harms block, and drift has its own tier

`skills/mf-converge/SKILL.md` SHALL name the **anchors** — data loss or an irreversible delete, spend, exposure of
personal data or secrets, silent wrong output — and SHALL grade an anchored finding `blocking` in review and at least
`high` in security. Review SHALL grade `blocking | drift | nit`, where `drift` is docs, comments, README or CHANGELOG
text the code contradicts; `drift` SHALL NOT block. A spec scenario the code contradicts SHALL stay `blocking`.
`docs/sdd.md` SHALL state the same vocabulary.

#### Scenario: Converge and the method page name the anchors and the drift tier
- **Key:** `sdd:converge-audit:anchors-and-drift`
- **Layers:** unit
- **WHEN** `skills/mf-converge/SKILL.md` and `docs/sdd.md` are scanned
- **THEN** each names `blocking | drift | nit`
- **AND** `mf-converge` names each anchor: `data loss`, `spend`, `exposure`, `silent wrong output`

### Requirement: A repeated finding escalates

Each station SHALL read `.minions/backlog.md`. A finding that repeats a backlog card SHALL name that card's id in its
**Related** field as `repeat of <id>`, and SHALL go up one level: security by one step, a review `nit` or `drift` to
`blocking`.

#### Scenario: Converge names the repeat rule
- **Key:** `sdd:converge-audit:repeats-escalate`
- **Layers:** unit
- **WHEN** `skills/mf-converge/SKILL.md` is scanned
- **THEN** it names `repeat of`
- **AND** it names `up one level`

### Requirement: Review searches for stale claims

The review station SHALL run a **stale-claim pass** after its engine: every path, symbol, verb, route or count the
diff renames, deletes or changes is searched across the rest of the tree, and each mention the change made false is
carded as `drift`. The station SHALL say in its Summary that the pass ran, and `skills/mf-converge/SKILL.md` SHALL
check that it did.

#### Scenario: Converge names the stale-claim pass
- **Key:** `sdd:converge-audit:stale-claim-pass`
- **Layers:** unit
- **WHEN** `skills/mf-converge/SKILL.md` is scanned
- **THEN** it names `stale-claim pass` at least twice: where the station runs it and where the conductor checks it

### Requirement: A fix's test fails without the fix

For a card whose fix size includes `a test`, the fix station SHALL paste the new test's failing run from before the
fix into the card's **Status** note. The verify pass SHALL reopen the card when that run is missing, or when the test
does not exercise the card's **When you'd hit it** scenario. Fixes to docs only are exempt.

#### Scenario: Converge names the red run and the verifier's check
- **Key:** `sdd:converge-audit:red-before-green`
- **Layers:** unit
- **WHEN** `skills/mf-converge/SKILL.md` is scanned
- **THEN** it names `failing run from before the fix`
- **AND** it names `When you'd hit it` in the verify step

## MODIFIED Requirements

### Requirement: Converge keeps deferred work in one repository backlog

`skills/mf-converge/SKILL.md` SHALL write every non-blocking card it does not fix to one file, `.minions/backlog.md`,
under a heading for its change. After both verdicts are clean, and only while a round remains under the cap, it
SHALL pick up this run's non-blocking cards whose fix is sized `one line` or `a test`, and every `drift` card, fix
them, and verify them in a normal round. It SHALL NOT name a per-version backlog file. It SHALL delete a backlog card
only when a verified repeat of it was fixed and the card's **Still true?** check shows the defect gone.

#### Scenario: Converge names the one backlog file and the pickup sizes
- **Key:** `sdd:repo-backlog:converge-writes-one-file`
- **Layers:** unit
- **WHEN** `skills/mf-converge/SKILL.md` is scanned
- **THEN** it names `.minions/backlog.md`
- **AND** it names both pickup sizes, `one line` and `a test`
- **AND** it does not name `_backlog.md`
