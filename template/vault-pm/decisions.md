---
type: decisions
updated: 2026-01-01
---

# Tasknip — Key decisions

## Storage
**Decision:** a single local JSON file (`~/.tasknip/tasks.json`).
**Date:** 2026-01-01
**Why:** zero dependencies, trivially inspectable; a database is overkill for a personal to-do CLI.

## CLI framework
**Decision:** stdlib `argparse`.
**Date:** 2026-01-01
**Why:** no new dependency (the framework gates dependency additions); argparse covers add / list / done.
