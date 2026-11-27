"""Name the run directory's paths and the home folder's, and the run's old layout.

It runs no git, and reads `HOME` and the environment when asked; a caller keeps a guard.
Why: 0134-run-layout design D1, D2 and D3; 0135-home-layout design D1 and D2.
"""

import hashlib
import os
import re
from pathlib import Path

KEPT_ORIGINS = ".mf-ship-origin"
SCRATCH_PREFIX = ".mf-ship-remote-"
SKILLS = {"claude": ".claude/skills", "codex": ".agents/skills"}
MINIONS = ".minions"
CHANGES = "changes"
RUNS = "runs"
CUTS = "cuts"
GRANTS = "grants"
STATUS_LOG = "status_log.md"
MODELS = "models.toml"
# Each old-layout path of a change, by its name in the change's folder.
# Why: 0080-minions-layout design D1, D4; 0095-converge-roles design D2.
OLD_LAYOUT = {
    "findings/{}_review.md": "conformance.md",
    "findings/{}_security.md": "adversarial.md",
    "findings/{}_status_log.md": "status_log.md",
    "findings/{}_diff.patch": "diff.patch",
    "models/{}.toml": MODELS,
    "integrate/{}.md": "integrate.md",
    "integrate/{}.red": "integrate.red",
    "integrate/{}.resolved": "integrate.resolved",
    "build/{}.done": "build.done",
    "build/{}.halt": "build.halt",
    "build/{}.closing": "build.closing",
    "build/{}.discarded.patch": "build.discarded.patch",
    "rescue/{}.md": "rescue.md",
    "release/{}.held": "release.held",
    "gate-check/{}": "gate-check",
}
# A change folder's old findings names. Why: 0095-converge-roles design D2.
OLD_ROLES = {"review.md": "conformance.md", "security.md": "adversarial.md"}
# An id of any width, as a station's CHANGE_ID reads one.
# Why: 0134-run-layout design D5.
OLD_ID = r"(\d+-[a-z0-9-]+)"
OLD_STAMP = re.compile(r"\d{8}-\d{6}(?:-\d+)?")
OLD_LOG = re.compile(rf"{OLD_ID}_([a-z][a-z-]*?)(-\d+)?\.log")


def primary_of(common: str | Path) -> Path:
    """Return the primary checkout of git's common directory, as git gave it.

    e.g. "<primary>/.git" → <primary>
    """
    return Path(common).parent


def run_dir(primary: Path) -> Path:
    """Return the primary's run directory.

    e.g. <primary> → <primary>/.minions
    """
    return primary / MINIONS


def change_dir(primary: Path, change: str) -> Path:
    """Return the change's folder in the run directory.

    e.g. "0001-todo" → <primary>/.minions/changes/0001-todo
    """
    return run_dir(primary) / CHANGES / change


def status_log(primary: Path, change: str) -> Path:
    """Return the change's status log.

    e.g. "0001-todo" → <primary>/.minions/changes/0001-todo/status_log.md
    """
    return change_dir(primary, change) / STATUS_LOG


def models_file(primary: Path, change: str) -> Path:
    """Return the change's models file.

    e.g. "0001-todo" → <primary>/.minions/changes/0001-todo/models.toml
    Why: 0142-models design D1.
    """
    return change_dir(primary, change) / MODELS


def findings_name(role: str) -> str:
    """Return the name of a checker's findings file in a change's folder.

    e.g. "adversarial" → "adversarial.md"
    """
    return f"{role}.md"


def shadow_name(role: str) -> str:
    """Return the name of a checker's shadow findings file in a change's folder.

    e.g. "adversarial" → "shadow-adversarial.md"
    """
    return f"shadow-{role}.md"


def open_name(role: str) -> str:
    """Return the name of the page of a role's cards a verify judges.

    e.g. "adversarial" → "adversarial.open.md"
    """
    return f"{role}.open.md"


def findings_file(primary: Path, change: str, role: str) -> Path:
    """Return a checker's findings file.

    e.g. "0001-a", "conformance" → <primary>/.minions/changes/0001-a/conformance.md
    Why: 0138-findings design D1.
    """
    return change_dir(primary, change) / findings_name(role)


def runs_dir(primary: Path) -> Path:
    """Return the folder of the runs' logs and their claim."""
    return run_dir(primary) / RUNS


def claim_file(primary: Path) -> Path:
    """Return the live run's claim.

    e.g. <primary> → <primary>/.minions/runs/active
    """
    return runs_dir(primary) / "active"


def debt_file(primary: Path) -> Path:
    """Return the repo's debt file."""
    return run_dir(primary) / "debt.md"


def debt_lock(primary: Path) -> Path:
    """Return the lock a writer of the debt file holds."""
    return run_dir(primary) / "debt.lock"


def backlog_file(primary: Path) -> Path:
    """Return the debt file's old name, read when no debt file stands."""
    return run_dir(primary) / "backlog.md"


def backlog_lock(primary: Path) -> Path:
    """Return the debt lock's old name."""
    return run_dir(primary) / "backlog.lock"


def gate_dir(primary: Path) -> Path:
    """Return the folder of the gate's green records."""
    return run_dir(primary) / "gate"


def cuts_dir(primary: Path) -> Path:
    """Return the folder of the cuts' reservations.

    e.g. <primary> → <primary>/.minions/cuts
    """
    return run_dir(primary) / CUTS


def grants_dir(primary: Path) -> Path:
    """Return the folder of a person's grants.

    e.g. <primary> → <primary>/.minions/grants
    """
    return run_dir(primary) / GRANTS


def cut_reservation(primary: Path, change: str) -> Path:
    """Return the file that reserves a change's id for its cut.

    e.g. "0001-todo" → <primary>/.minions/cuts/0001-todo
    """
    return cuts_dir(primary) / change


def metrics_page(primary: Path, change: str) -> Path:
    """Return the change's metrics page.

    e.g. "0001-todo" → <primary>/.minions/metrics/0001-todo.html
    """
    return run_dir(primary) / "metrics" / f"{change}.html"


def old_files(primary: Path) -> dict[str, list[tuple[Path, str]]]:
    """Return each change's old-layout files, each with its path in the change's folder.

    Why: 0080-minions-layout design D4; 0095-converge-roles design D2.
    """
    minions = run_dir(primary)
    found: dict[str, list[tuple[Path, str]]] = {}
    for old, new in OLD_LAYOUT.items():
        folder, name = old.split("/")
        pattern = re.compile(re.escape(name).replace(re.escape("{}"), OLD_ID))
        listed = (minions / folder).iterdir() if (minions / folder).is_dir() else ()
        for path in listed:
            if matched := pattern.fullmatch(path.name):
                found.setdefault(matched[1], []).append((path, new))
    changes = minions / CHANGES
    folders = sorted(changes.iterdir()) if changes.is_dir() else []
    for folder in (f for f in folders if f.is_dir()):
        for name, new in OLD_ROLES.items():
            if os.path.lexists(folder / name):
                found.setdefault(folder.name, []).append((folder / name, new))
    runs = runs_dir(primary)
    stamps = runs.iterdir() if runs.is_dir() else ()
    for stamp in (s for s in stamps if OLD_STAMP.fullmatch(s.name) and s.is_dir()):
        for path in stamp.iterdir():
            if matched := OLD_LOG.fullmatch(path.name):
                change, station, n = matched[1], matched[2], matched[3] or ""
                new = f"logs/{stamp.name}-{station}{n}.log"
                found.setdefault(change, []).append((path, new))
    return found


def old_layout(primary: Path, change: str) -> str | None:
    """Return the change's first old-layout file, relative to the primary, or None.

    Why: 0080-minions-layout design D4.
    """
    held = sorted(path for path, _ in old_files(primary).get(change, []))
    return str(held[0].relative_to(primary)) if held else None


def kept_dir() -> Path:
    """Return the conductor's folder in the home folder, where no worker writes."""
    return Path.home() / KEPT_ORIGINS


def digest(primary: Path) -> str:
    """Return the name the primary's files take in the kept folder, from its path.

    e.g. any link to <primary> → the first 16 hex digits of sha256(<primary resolved>)
    """
    return hashlib.sha256(str(primary.resolve()).encode()).hexdigest()[:16]


def kept_file(primary: Path) -> Path:
    """Return the file holding the URLs a run kept for the primary.

    Why: 0052-security-hardening design D9.
    """
    return kept_dir() / digest(primary)


def released_dir(primary: Path) -> Path:
    """Return the release ledger's folder: one file per change, holding its head.

    Why: 0053-sandbox-patch design D2.
    """
    return kept_dir() / f"{digest(primary)}.released"


def default_file(primary: Path) -> Path:
    """Return the file holding the default branch's name a run kept for the primary."""
    return kept_dir() / f"{digest(primary)}.default"


def pushed_file(primary: Path) -> Path:
    """Return the offline base's file: the default branch's sha origin last listed.

    Why: 0062-offline-origin design D1.
    """
    return kept_dir() / f"{digest(primary)}.pushed"


def queue_dir(primary: Path) -> Path:
    """Return the repo's queue in the kept folder.

    e.g. `~/.mf-ship-origin/<digest>.queue`. Why: 0082-cut-station design D2.
    """
    return kept_dir() / f"{digest(primary)}.queue"


def queue_lock(primary: Path) -> Path:
    """Return the lock a writer of the queue holds.

    Why: 0082-cut-station design D2.
    """
    return queue_dir(primary) / "lock"


def queue_cuts(primary: Path) -> Path:
    """Return the folder of the queued cuts' entries."""
    return queue_dir(primary) / "cuts"


def queue_rejoin(primary: Path) -> Path:
    """Return the folder of the live run's rejoin requests.

    Why: 0063-rejoin design D2.
    """
    return queue_dir(primary) / "rejoin"


def queue_briefs(primary: Path) -> Path:
    """Return the folder of the brief paths the passed cuts recorded.

    Why: 0090-supervisor-merge design D1.
    """
    return queue_dir(primary) / "briefs"


def queue_supervised(primary: Path) -> Path:
    """Return the folder of the merges a supervisor was spawned on.

    Why: 0090-supervisor-merge design D2.
    """
    return queue_dir(primary) / "supervised"


def gate_approval(primary: Path, change: str) -> Path:
    """Return the file holding the hash a person approved for the change's gate.

    e.g. "0001-todo" → `~/.mf-ship-origin/<digest>.gate/0001-todo`.
    Why: 0060-gate-planning design D4.
    """
    return kept_dir() / f"{digest(primary)}.gate" / change


def live_dir() -> Path:
    """Return the folder of the live runs' marks."""
    return kept_dir() / "live"


def live_mark(primary: Path) -> Path:
    """Return the primary's live mark, which holds its run's pid.

    Why: 0068-pinned-release design D2.
    """
    return live_dir() / digest(primary)


def repos_file() -> Path:
    """Return the list of repos a run started in.

    Why: 0100-worker-diet design C1, D12.
    """
    return kept_dir() / "repos"


def probe_mark(executor: str, pid: int) -> Path:
    """Return the mark a probe of the executor writes, for the run's pid.

    e.g. ("codex", 41) → `~/.mf-ship-origin/probe-codex-41`
    """
    return kept_dir() / f"probe-{executor}-{pid}"


def scratch_parent() -> Path:
    """Return the folder a scratch folder is made in, which no worker can write."""
    return Path.home()


def pin_source() -> Path:
    """Return the pin's file naming the primary an install ran in."""
    return kept_dir() / "source"


def pin_pending() -> Path:
    """Return the pin's file naming the release the links wait to move to."""
    return kept_dir() / "pending"


def pin_hold() -> Path:
    """Return the pin's file naming the release the links are held at."""
    return kept_dir() / "hold"


def pin_checkout() -> Path:
    """Return the pin's file naming the checkout a live install links."""
    return kept_dir() / "checkout"


def config_dir() -> Path:
    """Return the operator's config folder, under `XDG_CONFIG_HOME` or `~/.config`."""
    base = os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"
    return Path(base) / "minionsfactory"


def ship_file() -> Path:
    """Return the operator's `ship.toml`.

    Why: 0132-cloud-run design D1.
    """
    return config_dir() / "ship.toml"


def review_metrics_file() -> Path:
    """Return the review metrics' config, `review-metrics.toml`."""
    return config_dir() / "review-metrics.toml"


def ui_file() -> Path:
    """Return the viewer's config, `ui.toml`."""
    return config_dir() / "ui.toml"


def data_dir() -> Path:
    """Return the folder every release is exported into, under `XDG_DATA_HOME`."""
    base = os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share"
    return Path(base) / "minionsfactory"


def state_dir() -> Path:
    """Return the viewer's state folder, under `XDG_STATE_HOME` or `~/.local/state`."""
    base = os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state"
    return Path(base) / "minionsfactory"


def skills_dir(executor: str) -> Path:
    """Return the folder the executor's host reads its skills from.

    e.g. "codex" → `~/.agents/skills`
    """
    return Path.home() / SKILLS[executor]


def codex_home() -> Path:
    """Return Codex's home folder: `CODEX_HOME`, else `~/.codex`."""
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def claude_home() -> Path:
    """Return Claude's settings folder: `CLAUDE_CONFIG_DIR`, else `~/.claude`.

    Why: 0100-worker-diet design D2.
    """
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
