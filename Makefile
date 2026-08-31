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
# directory (`~/.claude/skills/`). A symlink, not a copy: an edit in this tree is live in
# the next session with no re-install, which is what a skill under iteration needs. The
# ordering constraint runs the other way — if these skills are ever deleted, remove the
# symlinks BEFORE deleting the directory they point at, or the install is left dangling.
install-skills:
	@mkdir -p "$(HOME)/.claude/skills"
	@for d in skills/mf-*; do \
		[ -d "$$d" ] || continue; \
		name=$$(basename $$d); \
		ln -sfn "$(CURDIR)/$$d" "$(HOME)/.claude/skills/$$name"; \
		echo "linked ~/.claude/skills/$$name -> $$d"; \
	done

# Remove exactly the symlinks `install-skills` created — and only symlinks, so a real
# directory of the same name in the operator's skills tree is never touched.
uninstall-skills:
	@for d in skills/mf-*; do \
		[ -d "$$d" ] || continue; \
		name=$$(basename $$d); \
		if [ -L "$(HOME)/.claude/skills/$$name" ]; then \
			rm "$(HOME)/.claude/skills/$$name"; \
			echo "removed ~/.claude/skills/$$name"; \
		fi; \
	done
