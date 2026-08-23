.PHONY: fix gate install-skills uninstall-skills

fix:
	uv run ruff format .
	uv run ruff check --fix .

gate:
	uv run ruff format --check .
	uv run ruff check .
	uv run ty check
	uv run pytest -q
	uv run python -m orchestrator specs check --strict

# symlink the mf- planning skills (+ shared rubrics) into ~/.claude/skills/ (repo edits stay live)
install-skills:
	@mkdir -p "$(HOME)/.claude/skills"
	@for d in skills/mf-* skills/rubrics; do \
		name=$$(basename $$d); \
		ln -sfn "$(CURDIR)/$$d" "$(HOME)/.claude/skills/$$name"; \
		echo "linked ~/.claude/skills/$$name -> $$d"; \
	done

# remove the mf- planning skill (+ rubrics) symlinks from ~/.claude/skills/ (leaves other entries untouched)
uninstall-skills:
	@for d in skills/mf-* skills/rubrics; do \
		name=$$(basename $$d); \
		if [ -L "$(HOME)/.claude/skills/$$name" ]; then \
			rm "$(HOME)/.claude/skills/$$name"; \
			echo "removed ~/.claude/skills/$$name"; \
		fi; \
	done
