.PHONY: fix gate

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

