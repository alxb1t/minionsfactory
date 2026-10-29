# minions_factory — coding standards

The rules this repo's code and docs follow. Mandatory context, named by [AGENTS.md](AGENTS.md), per
[D46](docs/decisions.md#d46--a-repos-own-rules-live-in-its-coding-standards-and-contribution-guide).

## Baseline

`mf-build`'s rules apply as written: comments `C1`…`C12`, tests `T1`…`T6`, and prose `P1`…`P13` for every
markdown doc and CHANGELOG entry: terse, answer first, things named rather than counted.

## Project rules

- **Python 3.12 or later, typed and documented** — the gate runs ruff's `D` and `ANN` rules and strict types;
  tests are exempt from `D`. The settings are `pyproject.toml`'s.
- **A skill's script is a `uv` script** — a PEP 723 header with `requires-python = ">=3.12"` and
  `dependencies = []`, run with `uv run --script`.
