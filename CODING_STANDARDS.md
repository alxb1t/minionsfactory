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
  `dependencies = []`, save the CommonMark parser `markdown-it-py>=3,<4` in the scripts that read Markdown,
  `brief_check.py` and `conduct.py`; run with `uv run --script`, save the dependency-free helpers converge starts
  (`gate_run.py`, `gate_check.py`, `plan_check.py`), which it runs by the conductor's own Python (0112 D1).
- **The wider lint holds** — the families `pyproject.toml` lists under `extend-select` are the gate's. A blind
  `except` carries `# noqa: BLE001` on its line and `# why: <reason>` on the line above.
- **A docstring is checked** — `scripts/docstrings.py` holds `C7` and `C3` for every docstring of a Python file,
  counting non-blank lines, so a blank line is no line.
