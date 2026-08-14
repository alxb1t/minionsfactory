# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0/).

## [Unreleased]

### Added

- Project scaffolding: role-independent `CLAUDE.md`, vault wiring (`.env` → `VAULT_PROJECT_DIR`), `.gitignore`, `.env.example`, and this changelog.
- Minimal `pyproject.toml` (uv-managed, run-from-source, no runtime deps) + committed `uv.lock`; the strict quality gate lands in P1.
