.PHONY: fix gate install-skills uninstall-skills

fix:
	uv run ruff format .
	uv run ruff check --fix .

gate:
	uv sync --locked
	uv run ruff format --check .
	uv run ruff check .
	uv run ty check
	uv run pytest -q
	uv run python -m orchestrator specs check --strict

# Symlink the four mf- execution-line skills into the operator's personal skills
# directory — `SKILLS_DIR`, which defaults to `~/.claude/skills` and is the ONE place
# that directory is named (no skill names it; see the change's design note on where
# paths may appear). Override it to install elsewhere, or to exercise these targets
# against a scratch destination. A symlink, not a copy: an edit in this tree is live in
# the next session with no re-install, which is what a skill under iteration needs. The
# ordering constraint runs the other way — if these skills are ever deleted, remove the
# symlinks BEFORE deleting the directory they point at, or the install is left dangling.
SKILLS_DIR ?= $(HOME)/.claude/skills

# Two rules make this an install rather than a claim about one. The loop is joined with
# `&&`, not `;`: a `;`-joined loop reports the exit status of its trailing `echo`, so a
# failed `ln` is swallowed and the target exits 0 announcing four links it did not
# create. And a destination that already exists and is NOT a symlink is refused, never
# overwritten: `ln -f` will not unlink a directory, so it would silently create the link
# one level INSIDE it — invisible to the harness, and out of reach of `uninstall-skills`,
# whose symlink guard sees only the real directory — while on a regular file the same
# `-f` would delete the operator's file with no message at all. The `echo` follows a
# successful `ln`, so the success line reports a fact rather than an attempt.
install-skills:
	@mkdir -p "$(SKILLS_DIR)"
	@for d in skills/mf-*; do \
		[ -d "$$d" ] || continue; \
		name=$$(basename "$$d"); \
		dest="$(SKILLS_DIR)/$$name"; \
		if [ -e "$$dest" ] && [ ! -L "$$dest" ]; then \
			echo "refusing: $$dest exists and is not a symlink" >&2; \
			exit 1; \
		fi; \
		ln -sfn "$(CURDIR)/$$d" "$$dest" && echo "linked $$dest -> $$d" || exit 1; \
	done

# Remove symlinks of these names from the skills directory — and only symlinks, so a
# real directory of the same name in the operator's tree is never touched. `&&`-joined
# for the same reason the install is: a failed `rm` must fail the target rather than be
# reported as a removal.
uninstall-skills:
	@for d in skills/mf-*; do \
		[ -d "$$d" ] || continue; \
		name=$$(basename "$$d"); \
		dest="$(SKILLS_DIR)/$$name"; \
		if [ -L "$$dest" ]; then \
			rm "$$dest" && echo "removed $$dest" || exit 1; \
		fi; \
	done
