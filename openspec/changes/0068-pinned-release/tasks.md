# Pinned release — tasks

Build the settled [design](design.md), one phase at a time. Every `Makefile` line a task adds or removes is quoted.

## Progress

- [ ] 1 — The install
- [ ] 2 — The conductor
- [ ] 3 — The version
- [ ] 4 — The record

## 1 — The install

- [ ] 1.1 Write `skills/mf-ship/scripts/pin.py` with `install`, `uninstall` and `move`, and `tests/test_pin.py`, per
  [D1](design.md#d1), [D2](design.md#d2) and [D3](design.md#d3).
  Verify: `uv run pytest -q tests/test_pin.py` reports no failure.
- [ ] 1.2 Call it from the install recipes in `Makefile`, the `gate` recipe untouched and the blank lines between the blocks kept,
  per [D1](design.md#d1):
  ```diff
  - # Symlink the mf- execution-line skills into the operator's personal skills
  - # directory — `SKILLS_DIR`, which defaults to `~/.agents/skills` and is the ONE place
  - # that directory is named (no skill names it; see the change's design note on where
  - # paths may appear). Override it to install elsewhere, or to exercise these targets
  - # against a scratch destination. A symlink, not a copy: an edit in this tree is live in
  - # the next session with no re-install, which is what a skill under iteration needs. The
  - # ordering constraint runs the other way — if this checkout is ever deleted, remove the
  - # symlinks BEFORE deleting it, or the install is left dangling.
  - SKILLS_DIR ?= $(HOME)/.agents/skills
  - # Two rules make this an install rather than a claim about one. The loop is joined with
  - # `&&`, not `;`: a `;`-joined loop reports the exit status of its trailing `echo`, so a
  - # failed `ln` is swallowed and the target exits 0 announcing links it did not
  - # create. And a destination that already exists and is NOT a symlink is refused, never
  - # overwritten: `ln -f` will not unlink a directory, so it would silently create the link
  - # one level INSIDE it — invisible to the harness, and out of reach of `uninstall-skills`,
  - # whose symlink guard sees only the real directory — while on a regular file the same
  - # `-f` would delete the operator's file with no message at all. The `echo` follows a
  - # successful `ln`, so the success line reports a fact rather than an attempt.
  - install-skills:
  - 	@mkdir -p "$(SKILLS_DIR)"
  - 	@for d in skills/mf-*; do \
  - 		[ -d "$$d" ] || continue; \
  - 		name=$$(basename "$$d"); \
  - 		dest="$(SKILLS_DIR)/$$name"; \
  - 		if [ -e "$$dest" ] && [ ! -L "$$dest" ]; then \
  - 			echo "refusing: $$dest exists and is not a symlink" >&2; \
  - 			exit 1; \
  - 		fi; \
  - 		ln -sfn "$(CURDIR)/$$d" "$$dest" && echo "linked $$dest -> $$d" || exit 1; \
  - 	done
  - # Remove every `mf-*` symlink in the skills directory that points into this checkout's
  - # `skills/` — a link to a skill since deleted included — and leave a link into another
  - # checkout, and anything not a symlink, alone. `&&`-joined for the same reason the
  - # install is: a failed `rm` must fail the target rather than be reported as a removal.
  - uninstall-skills:
  - 	@for dest in "$(SKILLS_DIR)"/mf-*; do \
  - 		[ -L "$$dest" ] || continue; \
  - 		case "$$(readlink "$$dest")" in \
  - 			"$(CURDIR)/skills/"*) rm "$$dest" && echo "removed $$dest" || exit 1 ;; \
  - 		esac; \
  - 	done
  + # Install a pinned MF release: `pin.py` exports a tag's `skills/` tree into the data folder and
  + # links every `mf-*` on both hosts there. Bare, the newest tag `origin` holds; TAG=<tag> holds
  + # that tag; TAG=live links this checkout. The rules live in the script, not here.
  + TAG ?=
  + install-skills:
  + 	uv run --script skills/mf-ship/scripts/pin.py install $(TAG)
  + # Remove every `mf-*` link on both hosts that points into a tree pin.py installed or this checkout.
  + uninstall-skills:
  + 	uv run --script skills/mf-ship/scripts/pin.py uninstall
  ```
  Verify: `grep -n 'SKILLS_DIR' Makefile` prints nothing, and `make -n install-skills` prints `uv run --script skills/mf-ship/scripts/pin.py install`.

## 2 — The conductor

- [ ] 2.1 Write the live mark first in `run()` and remove it in its claimed `finally`, call `pin.move()` there when no other mark
  stands, and name the release in `ship()`'s `start` line, in `skills/mf-ship/scripts/conduct.py`; add `test_a_run_marks_itself_live` and
  `test_the_last_run_moves_the_links` to `tests/test_conduct.py`, per [D2](design.md#d2), [D3](design.md#d3) and [D4](design.md#d4).
  Verify: `uv run pytest -q tests/test_conduct.py -k "marks_itself_live or last_run_moves_the_links"` reports `2 passed`.
- [ ] 2.2 Check one tree in `_unlinked`, with the mixed install's step in `test_a_missing_skill_stops_a_run`, per [D5](design.md#d5).
  Verify: `uv run pytest -q tests/test_conduct.py -k missing_skill_stops_a_run` reports `1 passed`.

## 3 — The version

- [ ] 3.1 Read `VERSION` in `mf_version` in `skills/mf-build/scripts/metrics.py`, with its step in `tests/test_metrics.py`, per
  [D4](design.md#d4).
  Verify: `grep -n 'VERSION' skills/mf-build/scripts/metrics.py` prints a line, and `uv run pytest -q tests/test_metrics.py` reports no failure.

## 4 — The record

- [ ] 4.1 Add the decision to `docs/decisions.md`, the exceptions to `docs/principles.md`, the gaps to `THREAT_MODEL.md`, and the
  pin to `README.md` — its install section, the symlink line at `README.md:38`, the relink step — `AGENTS.md` and
  `skills/mf-ship/SKILL.md`, per [D6](design.md#d6).
  Verify: `grep -n 'One pinned MF release per machine' docs/decisions.md` prints a line, and `grep -n 'SKILLS_DIR' README.md` prints nothing.
