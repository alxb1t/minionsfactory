.PHONY: fix gate check corpus install-skills uninstall-skills

# A stacked build's base is its dependency's built head: 0099-stacked-builds design D5.
STACKED_ON = $(shell git rev-parse --verify --quiet "$$(grep -sxE '[0-9a-f]{40}' "$$(git rev-parse --path-format=absolute --git-common-dir)/../.minions/changes/$$(git branch --show-current)/stacked-on")^{commit}")
DIFF_BASE ?= $(or $(STACKED_ON),main)

fix:
	uv run ruff format .
	uv run ruff check --fix .

# The gate — this repo's ONLY list of gate commands. The mf-* skills and CI run
# `make gate`; docs name it and never copy its commands.
gate:
	uv sync --locked
	uv run ruff format --check .
	uv run ruff check .
	uv run --script scripts/docstrings.py
	uv run ty check
	uv run zizmor .github/workflows/ci.yml
	betterleaks dir . --no-banner --redact
	uv run coverage run -m pytest -q -n auto --junitxml=.minions/test-report.xml
	uv run coverage combine -q
	uv run coverage xml -q
	uv run diff-cover coverage.xml --compare-branch=$(DIFF_BASE) --fail-under=100

check:
	uv run ruff format --check .
	uv run ruff check .
	uv run --script scripts/docstrings.py
	uv run ty check
	uv run pytest -q -n auto -m "not slow"

# The readers of run data over this checkout's run directory; no gate runs it.
corpus:
	uv run --script scripts/corpus.py

# Install a pinned MF release: `pin.py` exports a tag's `skills/` tree into the data folder and
# links every `mf-*` on both hosts there. Bare, the newest tag `origin` holds; TAG=<tag> holds
# that tag; TAG=live links this checkout. The rules live in the script, not here.
TAG ?=

install-skills:
	uv run --script skills/mf-ship/scripts/pin.py install $(TAG)

# Remove every `mf-*` link on both hosts that points into a tree pin.py installed or this checkout.
uninstall-skills:
	uv run --script skills/mf-ship/scripts/pin.py uninstall
