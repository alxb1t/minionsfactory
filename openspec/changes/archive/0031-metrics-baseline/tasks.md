# Metrics baseline — tasks

Record v0.30.0's data file, per the [design](design.md).

## Progress

- [x] 1 — Record v0.30.0's data file

## 1 — Record v0.30.0's data file

- [x] 1.1 **HALT CHECK** The `v0.30.0` tag holds the collector and the catalogue, the premise of [D1](design.md#d1).
  Verify: `git cat-file -e v0.30.0:skills/mf-build/scripts/metrics.py && git cat-file -e v0.30.0:metrics/catalogue.toml` exits 0.
- [x] 1.2 Run `git worktree add --detach .minions/v0.30.0 v0.30.0`, then `mkdir -p .minions/v0.30.0/.minions && cp .minions/backlog.md .minions/v0.30.0/.minions/`.
  Verify: `git -C .minions/v0.30.0 rev-parse --short HEAD` prints `f0aba0a`, and `test -f .minions/v0.30.0/.minions/backlog.md` exits 0.
- [x] 1.3 From `.minions/v0.30.0`, run `uv run --script skills/mf-build/scripts/metrics.py collect --change 0030-change-impact --base 8c88e90 --out metrics/changes/0030-change-impact.json --value gate-seconds=5 --executor "<what executor selection reported>" --model "<your model, or unidentified>"`, per [D2](design.md#d2).
  Verify: ``uv run python -c 'import json; d = json.load(open(".minions/v0.30.0/metrics/changes/0030-change-impact.json")); assert (d["version"], d["base"], d["analyzed"], d["mf_version"]) == ("v0.30", "8c88e90", "f0aba0a", "v0.30.0"); assert len(d["values"]) == 12 and all("value" in v for v in d["values"].values())'`` exits 0.
- [x] 1.4 Run `mkdir -p metrics/changes && cp .minions/v0.30.0/metrics/changes/0030-change-impact.json metrics/changes/`, then `git worktree remove --force .minions/v0.30.0`.
  Verify: `git worktree list | wc -l` prints `1`, and `grep -cE '/(Users|home)/' metrics/changes/0030-change-impact.json` prints `0`.
- [x] 1.5 Run `uv run --script skills/mf-build/scripts/metrics.py page 0030-change-impact`.
  Verify: `grep -q 'analyzed f0aba0a' .minions/metrics/0030-change-impact.html` exits 0.
