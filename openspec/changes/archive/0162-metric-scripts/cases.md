# Metric scripts — the cases

The cases of the region's mutation run, the readings settled and the asserts that turn, which [design](design.md) and [tasks](tasks.md) cite. Phase 1 writes each case on today's side; phases 3 and 4 turn the rows of *The turns*.

## The cases

### Slice R — the run log


**A `_events` day rule (via `events` times, `minutes("build")`)**
- build spawn `10:00:00`, finish `09:59:00` → times 05 10:00 and 05 09:59, `minutes("build")` -1.0. [A32, A33, A54]
- spawn `12:00:00`, finish `00:59:59` (11h00m01s back) → no roll, 05 00:59:59, minutes -660.0. [A32]
- spawn `12:00:00`, finish `00:00:00` (exactly 12h back) → no roll, 05 00:00:00, minutes -720.0. [A32, A54]
- spawn `12:00:01`, finish `00:00:00` (12h and a second back) → rolls, finish on 06 00:00:00. [A33]
- spawn `23:59:00`, finish `00:01:00` → minutes 2.0. [A33]
- `23:59:00`, `00:01:00`, `13:00:00` in one log → days 05, 06, 06 (the third stays on the new day). [A59]
- log `20261105-230000.md`, first line `10:00:00` (13h before the name's time) → day 05 10:00, `minutes("build")` 30.0, `waits()` 0.

**A `_logs` (via `events[].stamp`)**
- logs `…-000000`, `-2`, `-3`, `-9`, `-10`, `-11` → read in that numeric order (bare first, 10 after 9). [A42, A46]
- logs `20261105-100000`, `20261105-090000-2`, `20261104-235959-3`, `20261105-090000` → order 0104-235959-3, 0105-090000, 0105-090000-2, 0105-100000 (time is in the key). [A45, A46]
- beside one good log: `.txt`, a bare `20261106-100000`, `.md.bak`, `x2026…md`, `20261109-100000x.md`, `20261110-100000-2x.md`, `notes.md` → none read; only the good log's two events. [A39, A41]
- log `20261105-250000.md` (hour 25 in the name) → read, events 05 10:00 and 05 10:30 (the time part is never parsed).
- a link to a regular file at a stamp name → followed (its events read, 06 11:00, 06 11:30); `.minions/runs` itself a link to a folder → followed.
- an empty log, and a log of `b"\xff\xfe"`, beside a good log → add nothing; only the good events.
- a log over 262,144 bytes (a 300,000-char line between two good pairs) → read whole, 4 events.
- CRLF line ends → details `build`, `build`, minutes 30.0 (the `\r` is not in the detail).
- `converge skipped` as an event name (a space) → the line is no event; `some-name` (a hyphen) is one. [A10]
- a line `note 10:00:00 · X · halt — build check fail` (clock mid-line) → no event, `halts("build")` 0. [A15]
- a line `\xff\xfe10:00:00 · X · spawn — build` and `x\xff10:00:00 …` (bad bytes before the clock) → no event for those lines. [A15]
- `
` or `\x0b` between two events on one line → one event, `spawn`, detail `build<sep>10:30:00 · X · finish — build`; `spawns == []`, `minutes("build")` 0. [B04]

**A `_versions`, `_names` (via `events`)**
- `run · start — <detail>` with detail `""`, `versions`, `versions none`, `versions 0001-xy`, `executor c · mf v1`, `versions 0002-y · 0001-x` → the start line is not the version's; with `versions 0001-x`, `versions a 0001-x b`, `versions 0002-y 0001-x`, `executor c · versions 0001-x · mf v1` → it is.
- run lines `rejoin — 0001-xy: converge`, `rejoin — 0001-x converge`, `rejoin — x0001-x: converge`, `rejoin — 0001-x: converge` → only the last (colon prefix) is the version's. [A78]

**A/B `spawns`, `stage`, `minutes` (via `spawns`, `minutes`)**
- spawns `probe-codex`, `build`, `converge`, `integrate`, `release`, `rescue`, `supervise`, `other` → stations kept: build, converge, integrate, release, rescue, supervise. [A19, B04]
- spawn stations `converge-conformance`, `converge-shadow-adversarial`, `converge-fix-r2`, `converge-fix-r10` kept; `converge-fix-r2-x`, `converge-fix-r`, `converge-conformance-x`, `converge-fix-rx` dropped. [A25, A36]
- converge `script` spawn, converge spawn, three converge finishes, a build spawn → spawns (converge,1,closed,script), (converge,2,closed,not script), (build,1,open); `minutes("build")` Gap "a build spawn with no finish".
- integrate spawn and converge spawn both at 10:00:00, converge 10:00→10:05, integrate →10:06, converge 10:10→10:12 → converge 5.0, catch-up 2.0, integrate 6.0. [B28]

**B `halts`**
- halt details `build check fail — x`, `build worker exit 1`, `build timed out after 600s`, `build timed out` → `halts("build")` 4; `build check failure`, `build timed outside`, `rescue diagnosed — a build check fail`, `xbuild check fail`, `converge check fail`, `build` → not build (converge 1). [A29, A31, B67]
- `halt` of the version, `run · halt — X: build check fail`, `X · note — build check fail` → `halts("build")` 1.

**B `waits`, `after_waits`**
- halt 10:00, halt 10:05, `run · rejoin — X: build` 10:10 → `waits()` 10.0. [B38]
- halt 10:00, `run · spawn — X: build` 10:02, rejoin 10:10 → 10.0 (a run-line spawn does not end the wait); with `X · spawn — build` 10:02 → 0.0. [B42]
- halt 10:00, `run · grant — X: <tail>` 10:05, rejoin 10:10 with tail `automatic`, `automatically`, `automatic · R1` → 0.0. [B44]
- halt 10:00 then `run · grant — X: one more round` 10:07 → 7.0; then `run · start — versions X` 10:07:30 → 7.5; then `rejoin — X: still halted` → 0.0. [B49]
- `run · wait — X: after 0002-y` 10:00, X spawn 10:05, `X · wait — after 0002-y` 10:10, X spawn 10:12 → `after_waits()` 2.0. [B58]

**Shapes**
- a FIFO at `20261106-090000.md` beside a good log, read in a child process → the child hangs (TimeoutExpired at 8 s).
- a folder at a stamp name → `IsADirectoryError` from `events`; a dangling link there → `FileNotFoundError`.
- `.minions/runs` missing, a regular file, or a dangling link → `Gap("no run log names 0001-x")`.
- line `25:00:00 · X · spawn — build` → `ValueError("hour must be in 0..23")` from `events`; `run.measure(…, ["build-minutes"], env)` raises that ValueError, not Gap.
- log `20261399-250000.md` beside a good log → `ValueError("unconverted data remains")` from `events`.

**Equivalent**
none. A15, A54, B28 (marked maybe-equivalent) are all reachable and killed: A15 by a bad byte or a note before the clock, A54 by a step of exactly 12h, B28 by a converge in the integrate's second. A42/A46 order depends on glob order; the cases use six names so a lucky order is unlikely (red on both).

### Slice S — the status log, the findings, build.done, the proposal


**C `status_runs`, `rounds`, `grants`, `amends` (via `converge-rounds`, `grants`, `amend-rounds`)**
- `trailing-blanks`: `## Run 2 … · catch-up` + 3 trailing spaces, round 3, then `## Run 1` round 1 → rounds 1 (mark read after a trim). [C16]
- `catch-up`: `· catch-up` run with round 5 above `## Run 1` round 2 → rounds 2. [C16]
- `grant-and-amend`: `## Run 3 … · grant` round 2, `## Run 2 … · amend` round 3 → rounds 2, grants 1, amends 1. [C16, C40, C44]
- `ten-beats-nine`: round 10 then round 9 events → 10; `two-digit-only`: round 12 → 12. [C19]
- `empty`, `title-only`, `no-runs` (events with no heading) → rounds gap `no round in the status log`, grants 0, amends 0.
- `odd-runner-heading`: `## Runner` + round 3 → rounds gap. [C03]
- `odd-run-alone-heading`: `## Run` alone round 3, then `## Run 1` round 2 → 3. [C03]
- `odd-second-grant-mark` / `odd-second-amend-mark`: `## Run 2 · a · grant` (`· a · amend`) → grants 1, rounds 3 (amends 1, rounds gap). [C40, C44]
- `odd-amend-in-the-middle`: `## Run 2 · amend · a` → amends 0, round counted. [C44]
- `odd-catch-up-no-dot`: `## Run 2 catch-up` round 5 above `## Run 1` round 2 → 5. [C16]
- `odd-grant-no-dot`, `odd-amend-no-dot`: `## Run 2 grant` + `## Run 3 · grant` → grants 1 (amend likewise 1). [C40, C44]
- `odd-grant-then-amend`: `## Run 4 · grant · amend` → grants 0, amends 1.
- `odd-doubled-round-on-a-line`: `10:00:00 · round 3 · verify — gate exit 0 · round 3 · x` → rounds 3.
- `odd-bare-fragment-no-clock`: a body line `· round 3 ·` with no clock → rounds 3.
- `odd-crlf`: CRLF log with `· grant` and `· amend` runs → rounds 2, grants 1, amends 1; `odd-crlf-verdicts` adds a verdicts line of 7 → blockers 7.

**C `blockers` (via `blockers-round-1`)**
- `today`: one round-1 verdicts line, `open_blocking 2` → 2. [C25]
- `two-digits`: `open_blocking 12` → 12. [C34]
- `two-runs`: Run 2 (5) above Run 1 (2) → 2, the oldest run with the line. [C30]
- `two-lines`: conformance 5 and adversarial 2 in one run → 7. [C37]
- `round-2`, `round-12`: only round 2 / 12 verdicts → gap `no round 1 verdicts with open_blocking`. [C25]
- `r1-newer-r2-older`: Run 2 round 1 (5) above Run 1 round 2 (3) → 5. [C25]
- `halted-run-between`: Run 3 `round 1 · halt`, Run 2 (4), Run 1 (7) → 7. [C30]
- `odd-colon-form`: `open_blocking: 2` → 2. [C33]
- `odd-oldest-run-no-count`: Run 2 (7) above Run 1 `verdicts — conformance clean` → gap.
- `odd-no-count-no-spent-tail`: `verdicts — conformance clean` alone → gap; `odd-no-clock`: `round 1 · verdicts — … open_blocking 7` with no clock → gap.
- `odd-two-counts-on-a-line`: `open_blocking 2 · open_blocking: 3` → 5.
- `odd-role-c-no-spent-tail`: `verdicts — c changes-requested · open_blocking 4` → 4; `odd-no-verdict-word`: `verdicts — conformance · open_blocking 4` → 4.

**C shapes `status_log.md` (via `converge-rounds`, `grants`)**
- missing, folder, dangling link → gap `no 0001-x/status_log.md`; link to a regular file → followed (6, 1); FIFO → same gap, no hang; `b"\xff\xfe"` → `UnicodeDecodeError`; empty → rounds gap, grants 0; 262,200 bytes over → read whole.

**D `cards`, `confirmed`, `refuted` (via `conformance-confirmed`, `conformance-refuted`, `adversarial-*`)**
- `plain`: card + `## Refuted` with two entries, no heading after → [1, 2]. [D24]
- `deeper-heading`: `## Refuted`, `- a`, `### sub`, `- b`, `## X`, `- c` → refuted 2. [D25]
- `odd-dashless-entry`: `-a`, `- b`, `  - nested`, ` * c` → refuted 1. [D39]
- `odd-verdict-only`: titled card with a Verdict and no Priority → confirmed 0. [D34]
- `odd-unanchored-priority`: `  note - **Priority:** high` + Verdict → 0. [D05]
- `no-blank-after-verdict` / `tab-after-verdict` / `backtick-verdict` / `repeat-note` (`confirmed — repeat of 0012·R3`) → confirmed 1; `odd-capital-Confirmed`, `refuted-verdict` → 0. [D06]
- `odd-heading-between-priority-and-verdict`: `## H` between them → 0. [D29]
- `odd-h1-between-two-cards-fields`: a card, `# x`, then a Priority+Verdict pair → 2 [D29]; `heading-above-priority`: `# t` above a Priority+Verdict pair → 1.
- `odd-refused-heading`, `odd-no-section`, `odd-heading-no-newline`, `odd-no-space-heading`, `odd-h3-heading`, `odd-empty-file`, `odd-bad-byte-first` → gap `no ## Refuted in 0001-x/conformance.md`; `empty-section` and `empty-then-heading` → [1, 0]; `heading-with-text` (`## Refuted (3)`) accepted.
- `refuted-twice` → first section only; `card-after-refuted` → [2, 2] (a card after the section counts, its title line is an entry); `card-after-next-heading` → [2, 1]; `odd-priority-at-column-0` → confirmed 1 (the pair is split).
- `no-priority`, `dated-note` → [0, 0]; `dated-note-with-fields` → confirmed 1; `odd-untitled-card` (`- **a**`) → 1; `crlf` → [1, 2]; `bad-byte-in-section` → [1, 2]; `two-cards` → confirmed 2.
- adversarial.md read by the `adversarial-*` ids: two cards, three entries → [2, 3], conformance.md missing stays a gap.

**D shapes `conformance.md`**
- missing, folder, dangling link → gap `no 0001-x/conformance.md`; link → followed; FIFO → gap, no hang; `b"\xff\xfe"` → gap `no ## Refuted`; empty → same; over 262,144 bytes → read whole.

**D `commits` (via `build-commits`, `fix-commits`)**
- `7`, `8`, `40`: `head:` of that many hex of the third commit → [2, 1]. [D74]
- `odd-6-hex`, `odd-41-hex`, `odd-uppercase` → gap `no head in 0001-x/build.done`. [D76]
- `odd-trailing-spaces`, `odd-trailing-tab`, `odd-no-newline`, `odd-crlf` → [2, 1]. [D78]
- `odd-text-after`, `odd-indented`, `odd-two-blanks` (`head:  <sha>`), `odd-tab-after-colon`, `odd-no-blank` (`head:<sha>`), `empty` → no-head gap.
- `odd-over-65536-bytes`, `odd-over-262144-bytes` (head first, then padding lines) and `odd-head-after-65536-bytes` (head after padding) → [2, 1].
- `first-head-wins`: `head: <b>` then `head: <c>` → [1, 2]; `after-other-line` → [2, 1]; `head-at-tip` → [3, 0]; `not-in-history` (0×40) → gap `… head is not in the version's history`.
- shapes: missing, folder, dangling → no-head gap; link → followed; FIFO → no-head gap; `b"\xff\xfe"` → `UnicodeDecodeError`; empty → no-head gap; over 262,144 bytes → read whole.

**D `paid` (via `debt-paid`)**
- `comma-no-space` `debt: [0023·R1,0023·R2]` → 2 [D60]; `spaced-commas` → 2; `empty-item` `[A,,B]` → 3.
- `no-blank-after-colon` `debt:[A]`, `blanks-after-colon` `debt:   [A]` → 1 [D56]; `empty-list` `debt: []` and `blank-list` `debt: [ ]` → 1 [D57].
- `backlog` → 1; `both-keys` → 1 (first line); `indented` → 0; `in-body` → 1; `bare-list`, `backlog-bare`, `empty-key`, `none`, `no-line` → 0; `crlf` → 2; `two-lists` `[A], [B]` → 2; `note-after` → 1.
- `archive-only` (3) → read; both places → the live one; live is a folder → the archive's; none, dangling link, FIFO → gap `no proposal.md for 0001-x`; link → followed; bad byte → `UnicodeDecodeError`; over 262,144 bytes → read whole.

**D `escapes`**
- change `0005-a`, titled card `confirmed — repeat of 0003·R1`, `debt: []` → 1. [D68]
- same repeat only in adversarial.md → 1; both roles → 2. [D71]
- `debt: [0003·R1]` → 0; `debt: [0003·R2, 0004·R1]` → 1. [D68]
- repeat of `0007·R1` or `0005·R1` → 0; `odd-two-repeats-on-one-card` → 1.
- change `0005-a1`, repeat of `0020·R1` → 0. [D64]
- change `alpha`, no proposal → gap `no proposal.md for alpha`.

**E — the old eras, from disk** (test `test_the_old_eras_from_disk`; each log is `## Run 1 — 2026-09-28 12:00` + the lines verbatim; values are `blockers-round-1`, `converge-rounds`; `statuslog.verdicts(parse_event(line))` follows)
- E1 isekai 0037, `verdicts — review changes-requested · open_blocking 2 (R1, R2) · 7 commits 29 files … · stale-claim pass ran` + `verdicts — security clean · open_blocking 0 · 7 commits 29 files (matches freeze)` → blockers 2, rounds 1; verdicts() None for both lines.
- E2 MF 0095, `verdicts — security clean · open_blocking 0 · executor claude · model default · effort default · tokens 167263` + `verdicts — review changes-requested · open_blocking 2 · executor claude · … · tokens 341901` → blockers 2, rounds 1; verdicts() None for both (the role is not conformance/adversarial).
- E3 isekai 0078, `verdicts — review verdict: changes-requested; open_blocking: 2 (R1, R2); scope 8 commits, 43 files;` → blockers 2, rounds 1; verdicts() None.
- E4 isekai 0037, `12:39:01 · round 3 · verify — gate exit 0 · round 3 · fe3f5e6..c82f91b` alone → blockers gap `no round 1 verdicts with open_blocking`, rounds 3; with E2 in the same run → blockers 2, rounds 3 (the doubled round is one hit); verdicts() None (a `verify` event).
- E5 today's form, 0161-viewer lines `verdicts — adversarial clean · open_blocking 0 · executor claude · model claude-sonnet-5-5 · effort high · tokens 2971705` + `verdicts — conformance changes-requested · open_blocking 1 · … · tokens 5852914` → blockers 1, rounds 1; verdicts() `Verdicts(adversarial, claude, claude-sonnet-5-5, high, 2971705, False)` and `Verdicts(conformance, claude, claude-sonnet-5-5, high, 5852914, False)`.

**Equivalent**

- C10 — `re.split` with one capture group returns 1+2k parts, so `parts[1::2]` and `parts[2::2]` always have k items; `strict` never raises.


### Slice W — worker logs, prices, the debt file


**E `_spent`, `_summed`, `MODEL_USAGE` (via `tokens-build`, `cost-usd-build`)**
- build log with one `result` (`total_cost_usd` 1.0), `modelUsage` {a: {inputTokens 1, outputTokens 2, cacheReadInputTokens 4, cacheCreationInputTokens 8}, b: {inputTokens true, outputTokens 3}, c: 5, d: null, e: [1]} → tokens 18, cost 1.0. [E08, E10, E48, E50]
- Codex build log (spawn line, then turns with usage null, "x", [1], 5 and one {input_tokens 9, output_tokens 1}), prices file of my own → `tokens-build` 10. [E08]
- build log holding only a `mf.spawn` line → `cost-usd-build` 0.0 and `tokens-build` 0; the same log empty, `not json`, `{"type":"assistant"}` alone, or whose first line is `{"type":"x"}` → `gap: no result event in 0001-x/logs/20261101-100000-build.log`. [E39]
- build log with one `result`: with no `modelUsage`, with `modelUsage` [1], with no `total_cost_usd`, with the cost "1.0" a string → that gap; cost 2 and `modelUsage` {} → 2. [E46]

**E `Version.checkers` (public method)**
- run log whose converge spawn has no finish, then `converge-conformance` spawned and finished inside it → `checkers("converge")` names `converge-conformance`; `checkers("build")` is empty. [E73]

**E `Version.quota` (via `codex-window-5h`, `codex-window-week`)**
- build spawn with no log at all, a converge log whose first line is no spawn line but holds `mf.quota` five_hour 50.0, a checker log (spawn line, then two quota lines: five_hour 1.0 weekly true, five_hour 2.5 weekly true) → 5h 2.5; week `gap: no mf.quota line in a Codex log`. [E82, E86, E88]

**E `Version.role_tokens` (public method)**
- spawns `converge-conformance-r1` (result 100 tokens) and `converge-conformance-shadow-r1` (50), converge log with a result and no subagent events → `role_tokens("conformance")` 100. [E96]

**E shapes (worker logs, `cost-usd-build`, `tokens-build`, `codex-window-5h`)**
- build log a link to a log with a result → (1.0, 7); a dangling link, `b"\xff\xfe"`, an empty file, a missing file → both `gap: no result event in 0001-x/logs/20261101-100000-build.log`; `b"\xff\xfe\n"` then a result → (1.0, 7). The 5h window is `gap: no mf.quota line in a Codex log` in each.
- `role_tokens("conformance")` with the checker's log missing → `Gap: no 0001-x/logs/…-converge-conformance.log`; empty or `b"\xff\xfe"` → `Gap: no result event in …`.

**F `run._priced`, `review_metrics._prices` (removed by 4.9; pinned as it was), `_codex_spent` (a Codex converge log, same input to each: `Version.spent(("converge",))` and `read_repo`'s `cost_converge`/`tokens_converge`; written (run result, rm result))**
- prices good, one turn input 1,000,000 cached 400,000 output 100,000 → ((2.4, 1100000), (2.4, 1100000)).
- prices file missing → both `raises FileNotFoundError: … '<P>/<dir>/prices.toml'`; not TOML (`not = = toml`) → both `raises TOMLDecodeError: Invalid value (at line 1, column 7)`; `[other]` table only → both `raises KeyError: 'models'`. [F30]
- `models = 5` → both `raises AttributeError: 'int' object has no attribute 'get'`; Codex row without `cached_input` → both `raises KeyError: 'cached_input'`; `input = "2.0"` → both `raises TypeError: can only concatenate str (not "float") to str`.
- Claude row without `cache_write` (Codex log) → both (2.4, 1100000); the Codex row `= 5` → run `raises Gap: no price for model gpt-5.5`, rm `(None, 1100000)`.
- model null, prices good → run `raises Gap: no price for model default`, rm `(None, 1100000)`; model `o9` → `raises Gap: no price for model o9`, rm `(None, 1100000)`; model null and no prices file → run `raises FileNotFoundError`, rm `(None, 1100000)`; model `o9` and no file → both `raises FileNotFoundError`.
- usage counts (one turn): floats 1.0 and 1.0 → run (0.0, 0), rm (1.2e-05, 2.0); bools → both (0.0, 0); input -5 output -3 → both (-4e-05, -8); only `input_tokens` 10 → both (2e-05, 10); input 10 with cached 0 and output 0 → both (2e-05, 10) [F35]; turns [normal, "x", [1], 5, no usage key] → both (2.4, 1100000) [F33].

**F `_usage`, `_priced_worker` (a Claude mailbox log through `main`, workers' (model, tokens, dollars); 1M of each kind, `claude-sonnet-5-5`)**
- good → (sonnet, 5,000,000, 28.05); no file → `raises FileNotFoundError`; not TOML → `raises TOMLDecodeError`; no `[models]` → `raises KeyError: 'models'`; `models = 5` → `raises AttributeError`; row without `cache_write`, `input = "3.0"`, row `= 5` → dollars None; a Codex row lacking `cached_input` beside it → still 28.05. [F30]
- model null or `zzz` → dollars None, tokens 5,000,000; model null and no prices file → `raises FileNotFoundError` (the file is read for every worker); usage floats 1.0 → (2, 1.8e-05); bools → (0, 0.0); input -5 output 3 → (-2, 3e-05); input 10 only → (10, 3e-05).

**F shapes (prices file, both scripts, Codex log)**
- link to a good file, CRLF ends, a file over 262,144 bytes → (2.4, 1100000) in both; dangling → both FileNotFoundError; a folder → both `IsADirectoryError`; `b"\xff\xfe"` → both `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff`; empty → both `KeyError: 'models'`; a FIFO → both scripts block (child process times out at 3 s).

**G `debt.cards`, `debt.py` as a subprocess**
- one file per line: `- **0023·a**`, `- **0023·a` (no ` — `), `- **0023·a — title**` → 1 each; indented `  - **0023·a**`, `- **12345·x`, `- **R1·b**` plus `- **0023-a**` → 0; empty file → 0, script prints `0` exit 0 [G26]; CRLF two cards → 2; 30,000 cards over 262,144 bytes → 30000; the sections file → 6 (every section).
- link to a file → 1; missing, dangling link, folder, FIFO → `cards` None, script exit 1, stderr `no .minions/debt.md`. `b"\xff\xfe"` → `UnicodeDecodeError`, script exit 1, traceback last line `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff…`.
- a directory that is no repo (git ceiling set) → `cards` raises `CalledProcessError`; script exit 1, traceback `subprocess.CalledProcessError: Command '['git', 'rev-parse'…`. [G15]

**G `Version.debt` (via `debt-added`)**
- file `# Debt`, `## 0000-y` (1 card), `### 0001-x` (1), `## 0001-x extra` (1), `## 0001-x` (cards `0023·a — title`, `0024·b`, an indented nested card, `R1·c`, then text), `## 0002-z` (1) → change 0001-x gives 3 [G35, G36]; 0002-z 1; 0000-y 2 (runs over the `###` heading); `0001-x extra` 1; 0009-q 0; `0001` 0; `0001.x` 0 [G31].
- heading `## 0001-x  ` (trailing blanks) → 1; section with no card → 0; `- **R1·b**`, `- **a**`, `- **12345·x` all count → 3; CRLF file → 1; empty file → 0.
- file missing, dangling link, folder → `gap: no .minions/debt.md`; link to a file → 1; `b"\xff\xfe"` → `raises UnicodeDecodeError`.

**Equivalent**
None. G31 (marked maybe-equivalent) is pinned by a change id with a `.`: `0001.x` reads 0 clean, 1 with the id unescaped (a change id with a regex character is not a real id, but the id comes from the env).

## The readings, settled

Each reading of the three slices, settled by K3: on today's side unless a row turns it. "Turned in 3" and "turned in 4"
name the phase that changes the right side; "as today" cases stand as phase 1 wrote them. R1 to W11 are the slices' own
numbers; S11 to S14 and W12 were added after the review. The cases each row turns are listed, by test and key, in *The turns*.

| # | today | settled | by |
|---|---|---|---|
| R1 | a pipe at a run log's name blocks the read for good; every metric of every version stalls | turned in 3: the log yields no event and nothing blocks | H2, Q267 |
| R2 | a log named `20261399-250000.md`, or a line with the clock `25:00:00`, ends every metric of every version in a `ValueError` | turned in 3: the name is no log (Q275); the line is no event (H1) | Q275, H1 |
| R3 | a folder or a dangling link at a log's name escapes as `IsADirectoryError` or `FileNotFoundError` | turned in 3: it yields no event | H2, Q267 |
| R4 | a link to a regular file at a log's name is read; `.minions/runs` may itself be a link | turned in 3 for the file: a link at a log's name yields no event. As today for the folder | H2, Q267 |
| R5 | a line whose clock follows a bad byte or a note is no event | as today: the module reads it so too | — |
| R6 | U+2028 or `\x0b` between two events does not end a line: one event, the second in its detail | as today: the stream ends a line at a newline alone | H2; `viewer`'s B2 |
| R7 | a clock stepping back 12 hours or less is no midnight: minutes of -1.0 and -720.0 | turned in 3: any step back between two events is a day on, so 1439.0 and 720.0 | Q279 |
| R8 | `20261105-250000.md` is a log; a first event 13 hours before the name's time stays on the name's day | turned in 3: the name is no log; the first event is a day on when 12 hours or more before the name's time | Q275, Q279 |
| R9 | a line named `converge skipped` is no event | turned in 3: it is an event of that name. No metric moves by it but `after_waits` when it stands directly after a `wait`, which the conductor never writes | Q267 (M1) |
| R10 | a `start` line with `versions none`, or no name, names no version | as today: the detail stays `run.py`'s | Q277, H2 |
| S1 | a bad byte in `status_log.md`, `build.done` or the proposal ends the metric in a `UnicodeDecodeError` | turned in 3 for the status log: the byte is replaced, the read goes on. Turned in 4 for `build.done`: the gap `no head in …`, as for a file over 65,536 bytes, where today a file of any size is read. As today for the proposal | H3, H5; H4's exemption |
| S2 | the proposal's `debt: []` reads as one card named `""`; `debt: a, b` and `debt: none` as none; `debt: [a], [b]` as `a]` and `[b` | as today: the proposal has no home | H4's exemption |
| S3 | the old role lines on disk (`review`, `security`) and the colon form are counted: 2 for each of the three real logs; today's lines 1 for `0161-viewer`'s | as today in value, through `eras.blocking` for the old forms | H3, Q269 |
| S4 | of two runs with round-1 `verdicts` lines only the oldest counts, even when it holds no count; two lines in a run sum; two counts on one line sum | as today for the run and the sum of lines. Turned in 3 for two counts on one line: an event has one count, the first | H3, H1 |
| S5 | a card after `## Refuted` and before the next `## ` is a card, and its `- ` line a refuted entry | as today | H4 |
| S6 | a `- **Priority:**` line at column 0, or a heading between a card's Priority and Verdict, cuts the card, which is never confirmed | turned in 4 where the cut moves a count: a card is the module's — its title and its indented lines; a line at column 0 ends it, a `#` line too. A titled card so cut is confirmed on neither side, as today | H4, Q267 (M11) |
| S7 | `## Refuted` as the last line with no newline is no section | turned in 4: it is a section with no entry | H1 |
| S8 | a mark counts only as the heading's trailing words: `## Run 4 · grant · amend` is an amend; `## Run 2 grant` no grant | turned in 3: the mark is the text after the first ` · `, whole — `grant · amend` is neither. `## Run 2 grant` as today | H3, Q267 (M7) |
| S9 | `## Runner` is no heading; a link at a file's name is followed; a dangling link, a folder and a pipe read as missing | turned in 3: `## Runner` is a heading with no number; a link at the status log is the gap a missing log is. Turned in 4: a link at a findings file or `build.done` is not followed and is the gap a missing file is. A dangling link, a folder and a pipe as today | H3, H4, H5, Q267 (M6) |
| S10 | `head:` takes the first matching line; uppercase hex and 6 or 41 characters are no head; `head:` with two blanks, a tab or no blank before the digits is no head | turned in 4: two `head:` lines are no head; two blanks, a tab or no blank are a head; a head that stands after the file's first 65,536 bytes is none. Uppercase hex and 6 or 41 characters as today | H5, Q267 (M10) |
| S11 | a round is found by `· round N ·` anywhere in a line; a round-1 `verdicts` line is found with any text before it | turned in 3: a round is an event's — a whole line `HH:MM:SS · round N · <name> — <detail>`; a bare `· round 3 ·` is no event and gives no round. A `verdicts` line with no clock gives no count on either side, as today. A `· round N ·` twice on one line is one event of that round, as today in value | H3, Q267 (M8) |
| S12 | a `verdicts` line counts with any role, with no verdict word and with no spent tail | as today for `conformance` and `adversarial` with no verdict word or no tail (H1), and for `review` and `security` through `eras`. Turned in 3 for any other role: no count | H1, H3 |
| S13 | a card is any piece that holds a `- **Priority:**` line; a Verdict counts only under one; `Confirmed` with a capital is not confirmed | turned in 4: a card is a titled line `- **<id> — ` with its indented lines; an untitled `- **a**` is none; a Verdict needs no Priority line; the word is read with its case folded | H4, Q267 (M11, M12) |
| S14 | a findings file with `## Refused` and no `## Refuted` is the gap `no ## Refuted in …` | turned in 4: the metrics read the section through `eras.refuted`, so the gap becomes the counts | Q280, H4 |
| W1 | a missing, empty, folder, non-TOML or bad-byte `prices.toml` is a traceback in both scripts; a link to a good file and a file over 262,144 bytes are read | turned in 4: each, the link, a dangling link and the big file too, is the gap `prices: <reason>` in `run.py` and the one exception `prices.Unreadable` in `review_metrics.py` | H7, H1 |
| W2 | a pipe at `prices.toml` blocks both scripts; `run.py` reads the file for a log with a null model too | turned in 4: `Unreadable`, nothing blocks. The read for a null model as today | H7 |
| W3 | the same Codex log is priced differently by the two: a float count, a model with no row, a null model; a row that is no table is a gap in `run.py` and None in `review_metrics.py` | as today in each script: a row that is no table is no row (H1), so the gap and the None stand | H7, H1 |
| W4 | a Codex row without `cached_input`, or a price that is a string, is a `KeyError` or `TypeError` in both | turned in 4: a row with a string price is no row — a gap in `run.py`, None in `review_metrics.py`; a row that lacks a key is a gap in `run.py`. As today in `review_metrics.py` for the missing key | H7, H1 |
| W5 | a negative count is priced negative; a bool count is 0 | as today | H7's exemption |
| W6 | `review_metrics.py` reads `prices.toml` for every Claude worker, so a missing file fails there and not for a Codex log with a null model | as today; 5e3's | H14 |
| W7 | `Version.debt` counts any `- **` line under its heading; `debt.py` only `- **NNNN·` | turned in 4: both count the module's card, a title `- **<digits>·<id> — ` | H6, Q267 (M14, M15) |
| W8 | `## 0001-x later` is no heading of `0001-x`; `### 0001-x` is none; a `###` heading's cards join the section above | as today, where `debtfile.count` agrees; where a phase 1 case shows it does not, the module's answer | H6 |
| W9 | a bad byte in the debt file is a `UnicodeDecodeError`; `debt.py` outside a repository a `CalledProcessError` | turned in 4 for the byte: replaced, the count goes on. As today outside a repository | H6 |
| W10 | one bad worker log among a stage's makes the stage's cost and tokens a gap | as today: a worker log has no home | Q270 |
| W11 | a worker log that is a link is followed; a bad first line is passed by | as today | Q270 |
| W12 | a link to a regular file at `.minions/debt.md` is followed and counted | turned in 4: `debt.py` exits with `no .minions/debt.md: it is a link` and `Version.debt` is the gap of the same words | H6 |

**Left as they are, for a later round of the person's** — they look wrong and no row of this version turns them: the
proposal's `debt: []` counted as one paid card (S2); a count of `1.0` worth nothing to `run.py` and 2.0 to
`review_metrics.py`, and a negative count priced negative (W3, W5); `debt.py` ending in a traceback outside a
repository (W9); one bad worker log losing a whole stage's cost (W10); the two line splits of the run log (R6); and one new with Q279: two events written out of order within one second date every later event a day on — no log on disk holds one.

## The turns

Every assert that differs between today's code and a prototype of this plan, built in a scratch clone at
`2a086119` by the reviewer and run over the three slices' cases and the nine test files (361 tests, all green on
today's code): 25 turn in phase 3, 65 more in phase 4, 90 in all, in 48 tests; 313 tests are untouched. `today` is the
right side phase 1 writes, `after` the one its phase writes. A case not listed here does not change (H8). The slice's
test functions land in `tests/test_metric_pins.py` under the same names; the last row is the existing test H6 names,
whose typed lines are retyped so that its 2 stands.

| slice | test function | key or parametrize id | today | after | phase | reading |
|---|---|---|---|---|---|---|
| R | test_clock_stepping_back_under_12h_is_no_midnight | _at(v) | ['05 10:00:00', '05 09:59:00'] | ['05 10:00:00', '06 09:59:00'] | 3 | R7 |
| R | test_clock_stepping_back_under_12h_is_no_midnight | v.minutes('build') | -1.0 | 1439.0 | 3 | R7 |
| R | test_clock_stepping_back_11h_and_a_second_is_no_midnight | _at(v) | ['05 12:00:00', '05 00:59:59'] | ['05 12:00:00', '06 00:59:59'] | 3 | R7 |
| R | test_clock_stepping_back_11h_and_a_second_is_no_midnight | v.minutes('build') | -660.0 | 780.0 | 3 | R7 |
| R | test_clock_stepping_back_exactly_12h_is_no_midnight | _at(v) | ['05 12:00:00', '05 00:00:00'] | ['05 12:00:00', '06 00:00:00'] | 3 | R7 |
| R | test_clock_stepping_back_exactly_12h_is_no_midnight | v.minutes('build') | -720.0 | 720.0 | 3 | R7 |
| R | test_first_event_clock_before_the_log_name_stays_on_the_name_day | _at(v) | ['05 10:00:00', '05 10:30:00'] | ['06 10:00:00', '06 10:30:00'] | 3 | R8 |
| R | test_a_clock_of_25_hours_in_a_line_raises_valueerror | raises ValueError('hour must be in 0..23') | raises ValueError | Gap: no run log names 0001-x | 3 | R2 |
| R | test_a_log_name_with_month_13_raises_valueerror_for_every_version | raises ValueError('unconverted data remains') | raises ValueError | no raise (the name is no log) | 3 | R2 |
| R | test_a_log_name_with_hour_25_is_read_the_time_part_is_unused | _at(v) | ['05 10:00:00', '05 10:30:00'] | Gap: no run log names 0001-x | 3 | R8 |
| R | test_a_folder_named_like_a_log_in_the_runs_folder_is_not_a_log_by_name_only | raises IsADirectoryError | raises IsADirectoryError | no raise | 3 | R3 |
| R | test_a_dangling_link_at_a_log_name_raises_filenotfound | raises FileNotFoundError | raises FileNotFoundError | no raise | 3 | R3 |
| R | test_a_link_to_a_regular_file_is_followed | _at(v) | ['05 10:00:00', '05 10:30:00', '06 11:00:00', '06 11:30:00'] | ['05 10:00:00', '05 10:30:00'] | 3 | R4 |
| R | test_an_event_name_with_a_hyphen_or_a_space | [e.name for e in v.events] | ['some-name', 'halt'] | ['some-name', 'converge skipped', 'halt'] | 3 | R9 |
| R | test_a_fifo_at_a_log_name_hangs_the_read | raises TimeoutExpired | raises TimeoutExpired (the child hangs) | no raise (the child returns) | 3 | R1 |
| R | test_measure_reads_a_bad_clock_as_a_valueerror_not_a_gap | raises ValueError | raises ValueError | Gap: no run log names 0001-x | 3 | R2 |
| S | test_status_log_headings_and_marks | odd-second-grant-mark | [3, 'gap: no round 1 verdicts with open_blocking', 1, 0] | [3, 'gap: no round 1 verdicts with open_blocking', 0, 0] | 3 | S8 |
| S | test_status_log_headings_and_marks | odd-grant-then-amend | ['gap: no round in the status log', 'gap: no round 1 verdicts with open_blocking', 0, 1] | [3, 'gap: no round 1 verdicts with open_blocking', 0, 0] | 3 | S8 |
| S | test_status_log_headings_and_marks | odd-bare-fragment-no-clock | [3, 'gap: no round 1 verdicts with open_blocking', 0, 0] | ['gap: no round in the status log', 'gap: no round 1 verdicts with open_blocking', 0, 0] | 3 | S11 |
| S | test_status_log_headings_and_marks | odd-second-amend-mark | ['gap: no round in the status log', 'gap: no round 1 verdicts with open_blocking', 0, 1] | [3, 'gap: no round 1 verdicts with open_blocking', 0, 0] | 3 | S8 |
| S | test_status_log_headings_and_marks | odd-runner-heading | ['gap: no round in the status log', 'gap: no round 1 verdicts with open_blocking', 0, 0] | [3, 'gap: no round 1 verdicts with open_blocking', 0, 0] | 3 | S9 |
| S | test_blockers_read_the_round_one_verdicts | odd-role-c-no-spent-tail | 4 | 'gap: no round 1 verdicts with open_blocking' | 3 | S12 |
| S | test_blockers_read_the_round_one_verdicts | odd-two-counts-on-a-line | 5 | 2 | 3 | S4 |
| S | test_status_log_file_shapes | link | [6, 1] | ['gap: no 0001-x/status_log.md', 'gap: no 0001-x/status_log.md'] | 3 | S9 |
| S | test_status_log_file_shapes | bad-byte | ['UnicodeDecodeError', 'UnicodeDecodeError'] | ['gap: no round in the status log', 0] | 3 | S1 |
| S | test_findings_cards_and_the_refuted_section | heading-above-priority | [1, 0] | [0, 0] | 4 | S6 |
| S | test_findings_cards_and_the_refuted_section | no-priority | [0, 0] | [1, 0] | 4 | S13 |
| S | test_findings_cards_and_the_refuted_section | odd-unanchored-priority | [0, 0] | [1, 0] | 4 | S13 |
| S | test_findings_cards_and_the_refuted_section | odd-h1-between-two-cards-fields | [2, 0] | [1, 0] | 4 | S6 |
| S | test_findings_cards_and_the_refuted_section | odd-verdict-only | [0, 0] | [1, 0] | 4 | S13 |
| S | test_findings_cards_and_the_refuted_section | odd-untitled-card | [1, 0] | [0, 0] | 4 | S13 |
| S | test_findings_cards_and_the_refuted_section | odd-heading-no-newline | ['gap: no ## Refuted in 0001-x/conformance.md', 'gap: no ## Refuted in 0001-x/conformance.md'] | [1, 0] | 4 | S7 |
| S | test_findings_cards_and_the_refuted_section | odd-refused-heading | ['gap: no ## Refuted in 0001-x/conformance.md', 'gap: no ## Refuted in 0001-x/conformance.md'] | [1, 1] | 4 | S14 |
| S | test_findings_cards_and_the_refuted_section | odd-priority-at-column-0 | [1, 0] | [0, 0] | 4 | S6 |
| S | test_findings_cards_and_the_refuted_section | odd-capital-Confirmed | [0, 0] | [1, 0] | 4 | S13 |
| S | test_findings_file_shapes | link | [1, 1] | ['gap: no 0001-x/conformance.md', 'gap: no 0001-x/conformance.md'] | 4 | S9 |
| S | test_build_done_head | odd-tab-after-colon | ['gap: no head in 0001-x/build.done', 'gap: no head in 0001-x/build.done'] | [2, 1] | 4 | S10 |
| S | test_build_done_head | odd-two-blanks | ['gap: no head in 0001-x/build.done', 'gap: no head in 0001-x/build.done'] | [2, 1] | 4 | S10 |
| S | test_build_done_head | odd-over-65536-bytes | [2, 1] | ['gap: no head in 0001-x/build.done', 'gap: no head in 0001-x/build.done'] | 4 | S1 |
| S | test_build_done_head | odd-over-262144-bytes | [2, 1] | ['gap: no head in 0001-x/build.done', 'gap: no head in 0001-x/build.done'] | 4 | S1 |
| S | test_build_done_head | odd-no-blank | ['gap: no head in 0001-x/build.done', 'gap: no head in 0001-x/build.done'] | [2, 1] | 4 | S10 |
| S | test_build_done_head | odd-head-after-65536-bytes | [2, 1] | ['gap: no head in 0001-x/build.done', 'gap: no head in 0001-x/build.done'] | 4 | S1 |
| S | test_build_done_head | first-head-wins | [1, 2] | ['gap: no head in 0001-x/build.done', 'gap: no head in 0001-x/build.done'] | 4 | S10 |
| S | test_build_done_file_shapes | link | [2, 1] | ['gap: no head in 0001-x/build.done', 'gap: no head in 0001-x/build.done'] | 4 | S9 |
| S | test_build_done_file_shapes | bad-byte | ['UnicodeDecodeError', 'UnicodeDecodeError'] | ['gap: no head in 0001-x/build.done', 'gap: no head in 0001-x/build.done'] | 4 | S1 |
| S | test_build_done_file_shapes | big | [2, 1] | ['gap: no head in 0001-x/build.done', 'gap: no head in 0001-x/build.done'] | 4 | S1 |
| W | test_the_debt_script_counts_cards_of_four_digits_at_a_line_start | - **0023·a**\n: debt.cards(root) | 1 | 0 | 4 | W7 |
| W | test_the_debt_script_counts_cards_of_four_digits_at_a_line_start | - **0023·a**\n: _debt_script(root) | (0, '1\n', '') | (0, '0\n', '') | 4 | W7 |
| W | test_the_debt_script_counts_cards_of_four_digits_at_a_line_start | - **0023·a\n (no closing): debt.cards(root) | 1 | 0 | 4 | W7 |
| W | test_the_debt_script_counts_cards_of_four_digits_at_a_line_start | - **0023·a\n (no closing): _debt_script(root) | (0, '1\n', '') | (0, '0\n', '') | 4 | W7 |
| W | test_the_debt_script_counts_cards_of_four_digits_at_a_line_start | two CRLF cards `- **0023·a**` `- **0024·b**`: debt.cards(root) | 2 | 0 | 4 | W7 |
| W | test_the_debt_script_counts_cards_of_four_digits_at_a_line_start | two CRLF cards `- **0023·a**` `- **0024·b**`: _debt_script(root) | (0, '2\n', '') | (0, '0\n', '') | 4 | W7 |
| W | test_the_debt_script_counts_cards_of_four_digits_at_a_line_start | 30000 x `- **0023·a**`: debt.cards(root) | 30000 | 0 | 4 | W7 |
| W | test_the_debt_script_counts_cards_of_four_digits_at_a_line_start | 30000 x `- **0023·a**`: _debt_script(root) | (0, '30000\n', '') | (0, '0\n', '') | 4 | W7 |
| W | test_the_debt_script_counts_cards_of_four_digits_at_a_line_start | SECTIONS (whole file): debt.cards(root) | 6 | 1 | 4 | W7 |
| W | test_the_debt_script_counts_cards_of_four_digits_at_a_line_start | SECTIONS (whole file): _debt_script(root) | (0, '6\n', '') | (0, '1\n', '') | 4 | W7 |
| W | test_the_debt_script_reads_a_link_and_reports_a_missing_file | link: (debt.cards, _debt_script) | (1, (0, '1\n', '')) | debt.cards exits `no .minions/debt.md: it is a link` | 4 | W12 |
| W | test_a_debt_file_with_a_bad_byte_is_a_traceback | raises UnicodeDecodeError from debt.cards | raises UnicodeDecodeError | returns 0 | 4 | W9 |
| W | test_a_debt_file_with_a_bad_byte_is_a_traceback | (code, out) of the script | (1, '') | (0, '0\n') | 4 | W9 |
| W | test_a_debt_file_with_a_bad_byte_is_a_traceback | stderr starts `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff` | True | False (stderr empty) | 4 | W9 |
| W | test_a_versions_debt_is_the_cards_of_its_own_section | debt-added of 0001-x (SECTIONS) | 3 | 1 | 4 | W7 |
| W | test_a_versions_debt_is_the_cards_of_its_own_section | debt-added of 0002-z | 1 | 0 | 4 | W7 |
| W | test_a_versions_debt_is_the_cards_of_its_own_section | debt-added of 0000-y | 2 | 0 | 4 | W7 |
| W | test_a_versions_debt_is_the_cards_of_its_own_section | debt-added of '0001-x extra' | 1 | 0 | 4 | W7 |
| W | test_a_versions_debt_in_odd_files | '## 0001-x  \n- **0023·a**\n' | 1 | 0 | 4 | W7 |
| W | test_a_versions_debt_in_odd_files | '## 0001-x\n- **R1·b**\n- **a**\n- **12345·x\n' | 3 | 0 | 4 | W7 |
| W | test_a_versions_debt_in_odd_files | '## 0001-x\r\n- **0023·a**\r\n' | 1 | 0 | 4 | W7 |
| W | test_a_versions_debt_file_that_is_missing_a_link_or_has_a_bad_byte | link to a file: debt-added | 1 | 'gap: no .minions/debt.md: it is a link' | 4 | W12 |
| W | test_a_versions_debt_file_that_is_missing_a_link_or_has_a_bad_byte | bad byte: debt-added | 'raises UnicodeDecodeError: ...0xff' | 0 | 4 | W9 |
| W | test_prices_toml_read_by_both_scripts_for_a_codex_log | missing | ("raises FileNotFoundError: [Errno 2] No such file or directory: '<P>/run/prices.toml'", "raises FileNotFoundError: [Errno 2] No such file or directory: '<P>/rm/prices.toml'") | ('raises Gap: prices: No such file or directory', 'raises Unreadable: No such file or directory') | 4 | W1 |
| W | test_prices_toml_read_by_both_scripts_for_a_codex_log | not-toml | ('raises TOMLDecodeError: Invalid value (at line 1, column 7)', 'raises TOMLDecodeError: Invalid value (at line 1, column 7)') | ('raises Gap: prices: Invalid value (at line 1, column 7)', 'raises Unreadable: Invalid value (at line 1, column 7)') | 4 | W1 |
| W | test_prices_toml_read_by_both_scripts_for_a_codex_log | no-models | ("raises KeyError: 'models'", "raises KeyError: 'models'") | ('raises Gap: prices: no models table', 'raises Unreadable: no models table') | 4 | W1 |
| W | test_prices_toml_read_by_both_scripts_for_a_codex_log | models-not-table | ("raises AttributeError: 'int' object has no attribute 'get'", "raises AttributeError: 'int' object has no attribute 'get'") | ('raises Gap: prices: no models table', 'raises Unreadable: no models table') | 4 | W1 |
| W | test_prices_toml_read_by_both_scripts_for_a_codex_log | codex-row-no-cached-input | ("raises KeyError: 'cached_input'", "raises KeyError: 'cached_input'") | ('raises Gap: no price for model gpt-5.5', "raises KeyError: 'cached_input'") | 4 | W4 |
| W | test_prices_toml_read_by_both_scripts_for_a_codex_log | price-string | ('raises TypeError: can only concatenate str (not "float") to str', 'raises TypeError: can only concatenate str (not "float") to str') | ('raises Gap: no price for model gpt-5.5', (None, 1100000)) | 4 | W4 |
| W | test_a_codex_log_whose_model_is_null_or_has_no_row | case 2 (model None, no file) | ("raises FileNotFoundError: [Errno 2] No such file or directory: '<P>/run/prices.toml'", (None, 1100000)) | ('raises Gap: prices: No such file or directory', (None, 1100000)) | 4 | W2 |
| W | test_a_codex_log_whose_model_is_null_or_has_no_row | case 3 (model o9, no file) | ("raises FileNotFoundError: [Errno 2] No such file or directory: '<P>/run/prices.toml'", "raises FileNotFoundError: [Errno 2] No such file or directory: '<P>/rm/prices.toml'") | ('raises Gap: prices: No such file or directory', 'raises Unreadable: No such file or directory') | 4 | W1 |
| W | test_prices_toml_for_a_claude_worker | missing | "raises FileNotFoundError: [Errno 2] No such file or directory: '<P>/repo/prices.toml'" | 'raises Unreadable: No such file or directory' | 4 | W1 |
| W | test_prices_toml_for_a_claude_worker | not-toml | 'raises TOMLDecodeError: Invalid value (at line 1, column 7)' | 'raises Unreadable: Invalid value (at line 1, column 7)' | 4 | W1 |
| W | test_prices_toml_for_a_claude_worker | no-models | "raises KeyError: 'models'" | 'raises Unreadable: no models table' | 4 | W1 |
| W | test_prices_toml_for_a_claude_worker | models-not-table | "raises AttributeError: 'int' object has no attribute 'get'" | 'raises Unreadable: no models table' | 4 | W1 |
| W | test_a_claude_workers_model_and_usage_shapes | case 2: model None, no prices file | "raises FileNotFoundError: [Errno 2] No such file or directory: '<P>/repo/prices.toml'" | 'raises Unreadable: No such file or directory' | 4 | W1 |
| W | test_the_prices_file_as_a_link_a_folder_a_bad_byte_or_empty | link | ((2.4, 1100000), (2.4, 1100000)) | ('raises Gap: prices: it is a link', 'raises Unreadable: it is a link') | 4 | W1 |
| W | test_the_prices_file_as_a_link_a_folder_a_bad_byte_or_empty | dangling | ("raises FileNotFoundError: [Errno 2] No such file or directory: '<P>/run/prices.toml'", "raises FileNotFoundError: [Errno 2] No such file or directory: '<P>/rm/prices.toml'") | ('raises Gap: prices: it is a link', 'raises Unreadable: it is a link') | 4 | W1 |
| W | test_the_prices_file_as_a_link_a_folder_a_bad_byte_or_empty | folder | ("raises IsADirectoryError: [Errno 21] Is a directory: '<P>/run/prices.toml'", "raises IsADirectoryError: [Errno 21] Is a directory: '<P>/rm/prices.toml'") | ('raises Gap: prices: it is not a file', 'raises Unreadable: it is not a file') | 4 | W1 |
| W | test_the_prices_file_as_a_link_a_folder_a_bad_byte_or_empty | badbyte | ("raises UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte", "raises UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte") | ("raises Gap: prices: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte", "raises Unreadable: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte") | 4 | W1 |
| W | test_the_prices_file_as_a_link_a_folder_a_bad_byte_or_empty | empty | ("raises KeyError: 'models'", "raises KeyError: 'models'") | ('raises Gap: prices: no models table', 'raises Unreadable: no models table') | 4 | W1 |
| W | test_the_prices_file_as_a_link_a_folder_a_bad_byte_or_empty | big | ((2.4, 1100000), (2.4, 1100000)) | ('raises Gap: prices: it is over 262144 bytes', 'raises Unreadable: it is over 262144 bytes') | 4 | W1 |
| W | test_a_prices_file_that_is_a_fifo_blocks_both_scripts | run.py: raises TimeoutExpired | raises TimeoutExpired (hangs) | no raise (returns) | 4 | W2 |
| W | test_a_prices_file_that_is_a_fifo_blocks_both_scripts | review_metrics.py: raises TimeoutExpired | raises TimeoutExpired (hangs) | no raise (returns) | 4 | W2 |
| test_metric_scripts | test_the_backlog_is_read_from_the_primary_run_directory | _load('debt').cards(worktree) == 2 | 2 | 2, over its two lines retyped as `- **0023·a — x**` and `- **0024·b — y**` (left as typed it would be 0) | 4 | W7, H6 |
