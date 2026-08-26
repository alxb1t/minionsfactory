# vault-pm — the planning-side vault structure (template)

A worked example of the **PM / planning vault** a MinionsFactory-managed project keeps — the private,
tool-agnostic (local markdown) side where features are thought through *before* they cross into the repo as
openspec changes. `mf-stamp` (v0.12) will stamp this layout; the `mf-` planning skills read and write it.

This example is a fictional project — **Tasknip**, a tiny CLI to-do manager — filled in so you can see the shape,
not empty placeholders. Copy the structure, replace the content.

## Layout

- `overview.md` — the one-screen "where is this project" (current state, key decisions, links).
- `roadmap.md` — the version sequence (one small feature per version).
- `planning/vX.Y/` — one directory per version, holding that version's PRD (`vX.Y_<name>.md`): the source of
  truth `mf-order` writes and `mf-forge` renders into the repo's `openspec/changes/`. The blueprint's design
  proposition lands beside it (`vX.Y_design.md`), plus the planning findings (`vX.Y_gauge.md`,
  `vX.Y_inspect.md`).
- `backlog.md` — deferred work (two sections: current-release loose ends, and future/unversioned).
- `log.md` — the narrative session log, newest first.
- `decisions.md` — the ADR-style record of settled calls.

The repo consumes only the sanitized `openspec/changes/<id>/`; everything here stays private in the vault.
