"""The review-metrics station: the config, the reader, the page.

Why: 0045-review-metrics design D1…D7.
"""

import importlib.util
import json
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-review-metrics" / "scripts" / "review_metrics.py"


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("review_metrics", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


review_metrics = _load(_SCRIPT)


@pytest.fixture(autouse=True)
def _no_codex_sessions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Read Codex sessions from an empty folder, never the operator's."""
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))


def _front(verdict: str = "clean", **fields: object) -> str:
    keys = {"verdict": verdict, "reviewed": "2026-10-01", "round": 1} | fields
    return "---\n" + "".join(f"{k}: {v}\n" for k, v in keys.items()) + "---\n\n"


def _card(number: int, priority: str, *fields: str) -> str:
    lines = [
        f"- **R{number} — A defect**",
        "  - **Why it's a problem:** a harm.",
        f"  - **Priority:** {priority}",
        *(f"  - {field}" for field in fields),
    ]
    return "\n".join(lines) + "\n\n"


def _findings(root: Path, name: str, text: str) -> None:
    roles = "conformance|adversarial|review|security"
    found = re.fullmatch(rf"(.+?)_((?:shadow-)?(?:{roles})|status_log)\.md", name)
    assert found, name
    folder = root / ".minions" / "changes" / found[1]
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{found[2]}.md").write_text(text, encoding="utf-8")


def _record(root: Path, change: str) -> dict[str, object]:
    return next(r for r in review_metrics.read_repo(root) if r["change"] == change)


def _run_log(root: Path, name: str, *lines: object) -> None:
    _log(root / ".minions" / "runs" / name, *lines)


def _worker_log(root: Path, change: str, name: str, *lines: object) -> None:
    _log(root / ".minions" / "changes" / change / "logs" / name, *lines)


def _log(path: Path, *lines: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(
        (line if isinstance(line, str) else json.dumps(line)) + "\n" for line in lines
    )
    path.write_text(text, encoding="utf-8")


def _result(cost: float, turns: int, ms: int, **tokens: dict[str, int]) -> object:
    return {
        "type": "result",
        "total_cost_usd": cost,
        "num_turns": turns,
        "duration_ms": ms,
        "modelUsage": tokens,
    }


def test_no_config_exits_2_naming_the_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    before = sorted(tmp_path.rglob("*"))

    assert review_metrics.main([]) == 2

    looked_for = tmp_path / "minionsfactory" / "review-metrics.toml"
    assert str(looked_for) in capsys.readouterr().err
    assert sorted(tmp_path.rglob("*")) == before


def test_every_repo_a_run_started_in(tmp_path: Path) -> None:
    config, named, started, bare, third = (
        tmp_path / name for name in ("config.toml", "named", "started", "bare", "third")
    )
    for repo in (named, started, third):
        (repo / ".minions").mkdir(parents=True)
    bare.mkdir()
    config.write_text('repos = ["named"]\nout = "page.html"\n', encoding="utf-8")
    record = review_metrics.recorded()
    record.parent.mkdir()
    # A repo the config names is read once; one with no `.minions/`, not at all.
    record.write_text(f"{named}\n{started}\n{bare}\n\n{started}\n", encoding="utf-8")

    repos, _ = review_metrics.settings(config, [], None)
    assert repos == [named.resolve(), started.resolve()]

    # `--repo` reads no record.
    repos, _ = review_metrics.settings(config, [third], None)
    assert repos == [third.resolve()]

    # A record alone names the repos.
    config.write_text('out = "page.html"\n', encoding="utf-8")
    repos, _ = review_metrics.settings(config, [], None)
    assert repos == [named.resolve(), started.resolve()]


def test_each_era_parses_with_gaps(tmp_path: Path) -> None:
    bullets = "- **severity:** blocking\n- **severity:** `nit`\n- **severity:** nit\n"
    _findings(
        tmp_path,
        "0008-old_review.md",
        _front("changes-requested", reviewed="2026-01-02", round=2) + bullets,
    )

    _findings(tmp_path, "0009-clean_review.md", _front(reviewed="2026-02-01"))

    cards = _card(1, "`medium · security (integrity)` — why · and why")
    cards += _card(2, "high · security")
    _findings(
        tmp_path,
        "0014-carded_security.md",
        _front("changes-requested", reviewed="2026-03-01") + cards,
    )

    verdicts = _card(
        1,
        "blocking · review · functional correctness — why",
        "**Evidence:** `x` at `a.py:1` · read.",
        "**Verdict:** confirmed.",
        "**Status:** open",
    )
    verdicts += _card(
        2,
        "nit · review · maintainability — why",
        "**Evidence:** `y` · read.",
        "**Verdict:** plausible — a run would confirm it.",
        "**Status:** verified — held.",
    )
    verdicts += _card(
        3,
        "nit · review · maintainability — why",
        "**Evidence:** `z` · read.",
        "**Verdict:** plausible — a run would confirm it.",
        "**Status:** open",
    )
    judged = _front(
        "changes-requested",
        reviewed="2026-10-30",
        round=3,
        tier="high",
        mode="parallel",
        workers=7,
        model="some-model",
        packet="proposal.md, design.md, tasks.md; skipped: threat model",
    )
    summary = "## Refuted\n\n- a candidate\n- another\n\n## Summary\n\n"
    summary += "Threat model: inconclusive, not written yet.\nAll else read.\n"
    summary += "Spec: none, no other section is inconclusive.\n"
    _findings(tmp_path, "0042-judged_review.md", judged + verdicts + summary)
    _findings(
        tmp_path,
        "0042-judged_security.md",
        _front(reviewed="2026-10-30", round=3, workers=5, model="other-model")
        + "## Refuted\n\nNone.\n",
    )

    old = _record(tmp_path, "0008-old")
    assert (old["repo"], old["reviewed"]) == (tmp_path.name, "2026-01-02")
    assert (old["rounds"], old["findings"], old["blocking"]) == (2, 3, 1)
    assert old["severity"] == {"blocking": 1, "nit": 2}
    assert (old["model"], old["workers"]) == (None, None)
    assert (old["confirmed"], old["verified"], old["inconclusive"]) == (
        None,
        None,
        None,
    )

    clean = _record(tmp_path, "0009-clean")
    assert (clean["findings"], clean["blocking"]) == (0, 0)
    assert clean["confirmed"] is None

    carded = _record(tmp_path, "0014-carded")
    assert (carded["findings"], carded["blocking"]) == (2, 1)
    assert carded["severity"] == {"medium": 1, "high": 1}
    assert carded["categories"] == {"integrity": 1}

    rich = _record(tmp_path, "0042-judged")
    assert (rich["mode"], rich["model"]) == ("parallel", "some-model")
    assert (rich["rounds"], rich["workers"]) == (3, 12)
    assert (rich["packet_included"], rich["packet_skipped"]) == (3, 1)
    assert (rich["findings"], rich["blocking"]) == (3, 1)
    assert rich["categories"] == {"functional correctness": 1, "maintainability": 2}
    assert (rich["confirmed"], rich["plausible"], rich["plausible_verified"]) == (
        1,
        2,
        1,
    )
    assert (rich["refuted"], rich["inconclusive"]) == (2, 1)
    assert rich["duration"] is None

    # A catch-up by rule writes `workers: 0` under the judged round's model: a gap.
    for role in ("review", "security"):
        by_rule = _front(round=2, mode="by-rule", workers=0, model="some-model")
        _findings(tmp_path, f"0045-caught_{role}.md", by_rule)
    caught = _record(tmp_path, "0045-caught")
    assert (caught["mode"], caught["model"], caught["workers"]) == (
        "by-rule",
        "some-model",
        None,
    )

    _findings(
        tmp_path,
        "0043-quoted_review.md",
        _front(
            reviewed="2026-10-30",
            model='"quoted-model"',
            packet='"proposal.md, design.md; skipped: none"',
        )
        + "## Refuted\n\nNone.\n\n## Summary\n\nNo section is inconclusive.\n",
    )
    unquoted = _record(tmp_path, "0043-quoted")
    assert unquoted["model"] == "quoted-model"
    assert (unquoted["packet_included"], unquoted["packet_skipped"]) == (2, 0)
    assert unquoted["inconclusive"] == 0

    # Twin: an old tier line, and no `## Refuted`, leaves `inconclusive` a gap.
    _findings(
        tmp_path,
        "0044-escape_review.md",
        _front(reviewed="2026-10-30", model="a\x1b[2Jb", tier="standard")
        + "## Summary\n\nThreat model: inconclusive.\n",
    )
    escape = _record(tmp_path, "0044-escape")
    assert (escape["model"], escape["inconclusive"]) == ("a[2Jb", None)

    _findings(
        tmp_path,
        "0020-half_review.md",
        _front("changes-requested") + _card(1, "nit · review"),
    )
    _findings(tmp_path, "0020-half_security.md", _front("changes-requested"))
    assert _record(tmp_path, "0020-half")["findings"] is None

    quoted = _card(1, 'nit · review · "when none is" · why')
    quoted += _card(2, 'nit · review ("every card … shall carry them")')
    quoted += _card(3, "nit · review (t4)")
    _findings(tmp_path, "0021-quoted_review.md", _front("changes-requested") + quoted)
    prose = _record(tmp_path, "0021-quoted")
    assert (prose["findings"], prose["categories"]) == (3, {})
    assert not any("tier" in record for record in review_metrics.read_repo(tmp_path))

    worker = _REPO / "skills" / "mf-converge" / "references" / "worker.md"
    listed = re.search(r"category one of (.*?);", worker.read_text(encoding="utf-8"))
    assert listed
    assert tuple(re.findall(r"`([^`]+)`", listed.group(1))) == (
        review_metrics.CATEGORIES
    )


def test_the_resolution_log_counts_verified_and_reopened(tmp_path: Path) -> None:
    log = """## Resolution log

- 2026-10-30 · round 2 · R1 `fixed` → `verified` at head `20338c2`.
- 2026-10-30 · round 2 · R2 fixed → verified.
- 2026-10-30 · round 2 · R3 fixed → open: the regression stands.
- 2026-10-30 · round 3 · R4 wontfix → open: not justified.
- 2026-10-30 · round 3 · R5 wontfix → accepted; nothing reopened.
"""
    _findings(tmp_path, "0030-x_review.md", _front() + log)
    calm = "## Resolution log\n\n- 2026-10-30 · round 1 · nothing reopened.\n"
    _findings(tmp_path, "0031-y_review.md", _front() + calm)
    _findings(tmp_path, "0032-z_review.md", _front())

    first = _record(tmp_path, "0030-x")
    assert (first["verified"], first["reopened"]) == (2, 2)
    second = _record(tmp_path, "0031-y")
    assert (second["verified"], second["reopened"]) == (0, 0)
    third = _record(tmp_path, "0032-z")
    assert (third["verified"], third["reopened"]) == (None, None)


def test_the_status_log_gives_duration_tokens_and_the_cap(tmp_path: Path) -> None:
    capped = """# 0030-capped — converge status

## Run 2 — 2026-10-30 23:58
00:01:00 · round 2 · done — converged in 2 rounds · 3 cards to debt · gate exit 0
23:59:00 · round 1 · verdicts — review clean · tokens unavailable
23:58:30 · round 1 · start — base a · head b · 3 commits · engine: generic

## Run 1 — 2026-10-29 14:00
14:31:00 · round 3 · halt — cap reached, R3 open
14:10:00 · round 1 · verdicts — review clean · tokens 1200
14:05:00 · round 1 · verdicts — security clean · tokens 300
14:00:00 · round 1 · start — base a · head b · engine generic
"""
    one_card = """# 0031-one — converge status

## Run 1 — 2026-10-30 10:00
10:21:40 · round 1 · done — converged in 1 round · 1 card to backlog
10:09:02 · round 1 · verdicts — review clean · security clean · tokens unavailable
10:04:12 · round 1 · start — base a · head b · engine generic
"""
    no_count = """# 0032-none — converge status

## Run 1 — 2026-10-30 10:00
10:21:40 · round 1 · done — converged in 1 round
10:04:12 · round 1 · halt — the gate is red, not the capacity
"""
    _findings(tmp_path, "0030-capped_status_log.md", capped)
    _findings(tmp_path, "0031-one_status_log.md", one_card)
    _findings(tmp_path, "0032-none_status_log.md", no_count)

    first = _record(tmp_path, "0030-capped")
    assert first["duration"] == 150 + 1860
    assert (first["tokens"], first["capped"], first["to_backlog"]) == (1500, 1, 3)
    assert first["engine"] == "generic"
    assert (first["findings"], first["reviewed"]) == (None, None)

    second = _record(tmp_path, "0031-one")
    assert (second["tokens"], second["capped"], second["to_backlog"]) == (None, 0, 1)
    assert second["engine"] == "generic"

    third = _record(tmp_path, "0032-none")
    assert (third["capped"], third["to_backlog"], third["engine"]) == (0, None, None)

    # The JSON keeps each run, round and role; a line naming both roles and no
    # figure is a gap for each.
    rows = [
        (r["change"], r["run"], r["round"], r["role"], r["tokens"])
        for r in review_metrics.round_data(tmp_path)
    ]
    assert rows == [
        ("0030-capped", 2, 1, "review", None),
        ("0030-capped", 1, 1, "review", 1200),
        ("0030-capped", 1, 1, "security", 300),
        ("0031-one", 1, 1, "review", None),
        ("0031-one", 1, 1, "security", None),
    ]


def test_tokens_are_read_per_role(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("TZ", raising=False)
    both = "verdicts — review clean · security clean · tokens"
    claude = "executor claude · model opus · effort high"
    codex = "executor codex · model default · effort default"
    log = f"""# 0040-roles — converge status

## Run 2 — 2026-10-31 23:58
00:05:00 · round 6 · verdicts — adversarial clean · tokens unavailable
00:04:00 · round 6 · verdicts — conformance clean · tokens 11
00:03:00 · round 5 · {both} 5000
00:02:00 · round 4 · verdicts — review clean · {claude} · tokens 97960
00:01:00 · round 4 · verdicts — security clean · {codex} · tokens unavailable
00:00:30 · round 4 · fan-out — review and security dispatched · 2 workers
23:59:00 · round 4 · freeze — a..b · 1 commit · 1 file

## Run 1
10:04:00 · round 3 · {both} 7 review, 8 security
10:03:00 · round 2 · {both} 115k (review 63k, security 52k)
10:02:00 · round 1 · {both} 128126 + 115356
10:01:00 · round 1 · {both} review 45426, security 41346
"""
    _findings(tmp_path, "0040-roles_status_log.md", log)

    rows = review_metrics.round_data(tmp_path)
    figures = [(r["run"], r["round"], r["role"], r["tokens"]) for r in rows]
    # Each role's figure is its own, under either era's name; a line naming both
    # roles and one figure is recorded under `both`, credited to neither.
    assert figures == [
        (2, 6, "adversarial", None),
        (2, 6, "conformance", 11),
        (2, 5, "both", 5000),
        (2, 4, "review", 97960),
        (2, 4, "security", None),
        (1, 3, "review", 7),
        (1, 3, "security", 8),
        (1, 2, "review", 63000),
        (1, 2, "security", 52000),
        (1, 1, "review", 128126),
        (1, 1, "security", 115356),
        (1, 1, "review", 45426),
        (1, 1, "security", 41346),
    ]
    # D1's tail names the executor, model and effort; `default` is a gap.
    named = [(r["executor"], r["model"], r["effort"]) for r in rows[3:5]]
    assert named == [("claude", "opus", "high"), ("codex", None, None)]
    assert {(r["sessions"], r["source"]) for r in rows} == {(None, "status-log")}
    # The chart's tokens are the change's sum, each figure once.
    assert _record(tmp_path, "0040-roles")[
        "tokens"
    ] == 11 + 5000 + 97960 + 15 + 115000 + (128126 + 115356 + 45426 + 41346)
    # With no `$TZ`, a window is the system's local time in UTC.
    local = review_metrics.datetime(2026, 11, 1, 0, 0, 30)
    assert review_metrics._utc(local) == local.astimezone(review_metrics.UTC)


def _session(root: Path, name: str, meta: object, *lines: object) -> None:
    folder = root / "codex-home" / "sessions" / "2026" / "11" / "05"
    folder.mkdir(parents=True, exist_ok=True)
    text = [line if isinstance(line, str) else json.dumps(line) for line in lines]
    first = meta if isinstance(meta, str) else json.dumps(meta)
    (folder / name).write_text("".join(f"{line}\n" for line in [first, *text]))


def _meta(
    started: str, cwd: str, url: str, agent: str | None = None, parent: str = "P"
) -> dict[str, Any]:
    spawn = {"parent_thread_id": parent, "agent_path": agent}
    source = {"subagent": {"thread_spawn": spawn}} if agent else "cli"
    payload = {"id": agent or "P", "timestamp": started, "cwd": cwd, "source": source}
    git = {"repository_url": url}
    return {"type": "session_meta", "payload": payload | {"git": git}}


def _worked(model: str, effort: str, *totals: int) -> list[object]:
    context = {"type": "turn_context", "payload": {"model": model, "effort": effort}}
    counts = [
        {
            "type": "event_msg",
            "payload": {"type": "token_count", "info": {"total_token_usage": t}},
        }
        for t in ({"total_tokens": total} for total in totals)
    ]
    return [context, *counts]


def test_codex_sessions_fill_the_rounds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TZ", "Europe/Berlin")
    repo, tree = tmp_path / "repo", tmp_path / "0001-x"
    repo.mkdir()
    url = "git@example.invalid:o/r.git"
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "remote", "add", "origin", url], cwd=repo, check=True)
    git = ["git", "-c", "user.name=mf", "-c", "user.email=mf@example.invalid"]
    commit = [*git, "commit", "-q", "--allow-empty", "-m", "base"]
    subprocess.run(commit, cwd=repo, check=True)
    worktree = ["git", "worktree", "add", "-q", "-b", "0001-x", str(tree)]
    subprocess.run(worktree, cwd=repo, check=True)
    claude = "executor claude · model opus · effort high"
    log = f"""# 0001-x — converge status

## Run 1 — 2026-11-05 10:00
10:45:00 · round 3 · verdicts — adversarial clean · tokens unavailable
10:40:00 · round 3 · fan-out — adversarial dispatched · 1 worker
10:35:00 · round 3 · freeze — b..c · 1 commit · 1 file
10:30:00 · round 2 · verdicts — review clean · {claude} · tokens 900
10:29:00 · round 2 · verdicts — security clean · tokens unavailable
10:20:00 · round 2 · fan-out — review and security dispatched · 2 workers
10:20:00 · round 1 · freeze — a..b · 1 commit · 1 file
10:10:00 · round 1 · verdicts — review clean · security clean · tokens unavailable
10:01:00 · round 1 · fan-out — review and security dispatched · 2 workers
10:00:30 · round 1 · freeze — a..b · 2 commits · 3 files
"""
    _findings(repo, "0001-x_status_log.md", log)
    # A version whose round overlaps 0001-x's round 1, run on Claude.
    parallel = f"""# 0002-y — converge status

## Run 1 — 2026-11-05 10:02
10:09:00 · round 1 · verdicts — security clean · {claude} · tokens unavailable
10:03:00 · round 1 · fan-out — security dispatched · 1 worker
10:02:00 · round 1 · freeze — c..d · 1 commit · 1 file
"""
    _findings(repo, "0002-y_status_log.md", parallel)
    other = "git@example.invalid:o/other.git"
    # The conductor ran in the version's worktree; its review worker in another URL.
    _session(
        tmp_path, "a-parent.jsonl", _meta("2026-11-05T09:00:40Z", str(tree), other)
    )
    # Conductors in the primary and in 0002-y's worktree.
    for parent, cwd in (("R", repo), ("Y", tmp_path / "0002-y")):
        conductor = _meta("2026-11-05T09:00:00Z", str(cwd), url)
        conductor["payload"]["id"] = parent
        _session(tmp_path, f"a-{parent}.jsonl", conductor)
    # The primary's worker while 0002-y's round overlaps, 0002-y's own, and one
    # whose parent is no session are none of 0001-x's; the primary's worker in
    # round 2, with no overlap, is.
    for name, started, parent, total in (
        ("k-primary", "09:07:00", "R", 40),
        ("l-0002-y", "09:08:00", "Y", 50),
        ("n-orphan", "09:09:00", "Q", 70),
        ("m-primary", "09:25:00", "R", 60),
    ):
        meta = _meta(f"2026-11-05T{started}Z", "/w", url, "/root/security_r", parent)
        _session(tmp_path, f"{name}.jsonl", meta, *_worked("g6", "low", total))
    # A worker of the new era is matched by its name as written.
    adversarial = _meta("2026-11-05T09:42:00Z", "/w", url, "/root/adversarial_r3", "R")
    _session(tmp_path, "o-adversarial.jsonl", adversarial, *_worked("g7", "low", 80))
    reviewer = _meta("2026-11-05T09:05:00Z", "/x", other, "/root/review_round1")
    noise = ['{"type": "token_count", cut', '["token_count"]']
    _session(
        tmp_path, "b-review.jsonl", reviewer, *noise, *_worked("g1", "high", 9, 500)
    )
    for name, started, total in (("c-s1", "09:02:00", 100), ("d-s2", "09:06:00", 200)):
        meta = _meta(f"2026-11-05T{started}Z", "/y", url, "/root/security_r1")
        _session(tmp_path, f"{name}.jsonl", meta, *_worked("g2", "low", total))
    # A guardian, a fix worker, one outside the repo, one past the window, and
    # files that hold no session read as none.
    guardian = _meta("2026-11-05T09:03:00Z", "/z", url)
    guardian["payload"] |= {"id": "G", "source": {"subagent": {"other": "guardian"}}}
    _session(tmp_path, "e-guardian.jsonl", guardian, *_worked("g3", "low", 7))
    _session(
        tmp_path,
        "f-fix.jsonl",
        _meta("2026-11-05T09:04:00Z", "/z", url, "/root/fix_r1"),
    )
    outside = _meta("2026-11-05T09:05:00Z", "/z", other, "/root/review_x", "nobody")
    _session(tmp_path, "g-outside.jsonl", outside, *_worked("g4", "low", 7))
    late = _meta("2026-11-05T09:25:00Z", "/z", url, "/root/review_round2")
    _session(tmp_path, "h-late.jsonl", late, *_worked("g5", "low", 7))
    _session(tmp_path, "i-undated.jsonl", _meta("never", "/z", url, "/root/review_1"))
    _session(tmp_path, "j-broken.jsonl", "not json")
    out = tmp_path / "site" / "page.html"

    assert review_metrics.main(["--repo", str(repo), "--out", str(out)]) == 0

    data = json.loads((tmp_path / "site" / "review-metrics.json").read_text())
    assert re.fullmatch(
        r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d[+-]\d\d:\d\d", data["generated"]
    )
    assert data["records"] == [
        {
            "repo": "repo",
            "change": "0001-x",
            "run": 1,
            "round": 3,
            "role": "adversarial",
            "executor": "codex",
            "model": "g7",
            "effort": "low",
            "tokens": 80,
            "sessions": 1,
            "source": "codex-session",
            "dollars": None,
        },
        {
            "repo": "repo",
            "change": "0001-x",
            "run": 1,
            "round": 2,
            "role": "review",
            "executor": "claude",
            "model": "opus",
            "effort": "high",
            "tokens": 900,
            "sessions": None,
            "source": "status-log",
            "dollars": None,
        },
        {
            "repo": "repo",
            "change": "0001-x",
            "run": 1,
            "round": 2,
            "role": "security",
            "executor": "codex",
            "model": "g6",
            "effort": "low",
            "tokens": 60,
            "sessions": 1,
            "source": "codex-session",
            "dollars": None,
        },
        {
            "repo": "repo",
            "change": "0001-x",
            "run": 1,
            "round": 1,
            "role": "review",
            "executor": "codex",
            "model": "g1",
            "effort": "high",
            "tokens": 500,
            "sessions": 1,
            "source": "codex-session",
            "dollars": None,
        },
        {
            "repo": "repo",
            "change": "0001-x",
            "run": 1,
            "round": 1,
            "role": "security",
            "executor": "codex",
            "model": "g2",
            "effort": "low",
            "tokens": 300,
            "sessions": 2,
            "source": "codex-session",
            "dollars": None,
        },
        {
            "repo": "repo",
            "change": "0002-y",
            "run": 1,
            "round": 1,
            "role": "security",
            "executor": "claude",
            "model": "opus",
            "effort": "high",
            "tokens": None,
            "sessions": None,
            "source": "status-log",
            "dollars": None,
        },
    ]


def test_run_logs_give_cost_turns_and_tokens_per_station(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _findings(tmp_path, "0050-x_review.md", _front())
    prices = tmp_path / "prices.toml"
    prices.write_text(
        '[models]\n"gpt-5.5" = { input = 2.0, cached_input = 0.5, output = 10.0 }\n'
        '"default" = { input = 2.0, cached_input = 0.5, output = 10.0 }\n'
    )
    monkeypatch.setattr(review_metrics, "PRICES", prices)
    usage = {"input_tokens": 1_000_000, "cached_input_tokens": 400_000}
    turn = {"type": "turn.completed", "usage": usage | {"output_tokens": 100_000}}

    def spawn(model: str | None) -> object:
        return {"type": "mf.spawn", "executor": "codex", "model": model, "effort": None}

    # A Codex log's turns are priced at its spawn line's model; a later spawn line
    # names nothing, and a model with no row is a dollar gap, its tokens read.
    _worker_log(tmp_path, "0050-x", "A-integrate.log", spawn("gpt-5.5"), turn, turn)
    _worker_log(tmp_path, "0050-x", "A-rescue.log", turn, spawn("gpt-5.5"), turn)
    _worker_log(tmp_path, "0050-x", "B-rescue.log", spawn("o9"), turn)
    _worker_log(tmp_path, "0050-x", "C-rescue.log", spawn("gpt-5.5"))
    first = _result(0.5, 10, 60000, m={"inputTokens": 10, "outputTokens": 20})
    last = _result(
        1.25,
        4,
        30000,
        m={
            "inputTokens": 20,
            "outputTokens": 40,
            "cacheReadInputTokens": 300,
            "cacheCreationInputTokens": 10,
        },
        h={"inputTokens": 1, "outputTokens": 1},
    )
    noise = ('{"type": "result", cut', {"type": "assistant"}, ["result"])
    _worker_log(tmp_path, "0050-x", "A-converge.log", *noise, first, last)
    # A later spawn in the stamp keeps its own log; a station named `converge-x` is
    # no converge's.
    one_more = _result(0.5, 2, 2000, m={"inputTokens": 4})
    _worker_log(tmp_path, "0050-x", "A-converge-2.log", one_more)
    _worker_log(tmp_path, "0050-x", "A-converge-x.log", last)
    _worker_log(tmp_path, "0050-x", "A-build.log", {"type": "assistant"})
    _worker_log(tmp_path, "0050-xy", "A-rescue.log", last)
    # A checker the mailbox started is a cost cell of its own, none of converge's.
    conformance = "A-converge-conformance.log"
    _worker_log(tmp_path, "0050-x", conformance, spawn("gpt-5.5"), turn)
    _run_log(
        tmp_path,
        "A.md",
        "10:00:00 · 0050-x · spawn — converge · model default",
        "10:05:00 · 0050-x · finish — converge · exit 0 · 300s",
        "10:06:00 · 0050-x · spawn — converge · model default · effort high",
        "10:07:00 · 0050-xy · spawn — converge · model default",
        "10:08:00 · 0050-x · spawn — converge-x · model default",
        "10:08:30 · 0050-x · spawn — converge-conformance · model gpt-5.5",
        "10:09:00 · 0050-x · spawn — converge · model default",
    )
    one = _result(0.25, 1, 1000, m=dict.fromkeys(review_metrics.TOKENS, 1))
    _worker_log(tmp_path, "0050-x", "B-converge.log", one)
    _worker_log(tmp_path, "0050-x", "B-release.log", "codex: a text log")
    _run_log(tmp_path, "B.md", "11:00:00 · 0050-x · spawn — converge · model m")
    # The cut and the supervisor are stations; a log's first turn ends its cell.
    # Why: 0100-worker-diet design D12.
    context = {
        "input_tokens": 3,
        "cache_read_input_tokens": 15000,
        "cache_creation_input_tokens": 4000,
    }
    opening = {"type": "assistant", "message": {"usage": context}}
    later = {"type": "assistant", "message": {"usage": {"input_tokens": 9}}}
    _worker_log(tmp_path, "0050-x", "A-cut.log", opening, later, one)
    _worker_log(tmp_path, "0050-x", "A-supervise.log", one)

    record = _record(tmp_path, "0050-x")
    assert (record["first_cut"], record["first_supervise"]) == (19003, None)
    assert record["first_integrate"] == 1_000_000
    assert review_metrics._spent([])["first"] is None
    assert (record["cost_converge"], record["turns_converge"]) == (2.0, 17)
    assert (record["tokens_converge"], record["seconds_converge"]) == (380, 93)
    assert (record["logs_converge"], record["spawns_converge"]) == (3, 4)
    for station in ("build", "release"):
        assert record[f"cost_{station}"] is None
        assert record[f"tokens_{station}"] is None
    assert (record["logs_build"], record["logs_integrate"]) == (1, 1)
    assert record["cost_integrate"] == 2 * 2.4
    assert (record["turns_integrate"], record["seconds_integrate"]) == (None, None)
    assert record["cost_rescue"] is None
    assert record["tokens_rescue"] == 3 * 1_100_000
    assert (record["logs_rescue"], record["read_rescue"]) == (3, 2)

    headers, rows = review_metrics.cost_table([record])
    assert headers == ["change", *review_metrics.STATIONS]
    assert rows == [
        [
            "0050-x",
            "—",
            "$2.00 · 17 turns · 380 tokens · 93 s · 3 of 4",
            "$4.80 · 2200000 tokens · first 1000000",
            "—",
            "— · 3300000 tokens · first 1000000",
            "$0.25 · 1 turns · 4 tokens · 1 s · first 19003",
            "$0.25 · 1 turns · 4 tokens · 1 s",
            "$2.40 · 1100000 tokens · first 1000000",
            "—",
            "—",
            "—",
        ]
    ]

    bare = tmp_path / "bare"
    _findings(bare, "0051-y_review.md", _front())
    assert _record(bare, "0051-y")["cost_converge"] is None

    timed_out = tmp_path / "timed-out"
    _findings(timed_out, "0052-z_review.md", _front())
    _worker_log(timed_out, "0052-z", "A-converge.log", {"type": "assistant"})
    _run_log(timed_out, "A.md", "10:00:00 · 0052-z · spawn — converge · model m")
    _worker_log(timed_out, "0052-z", "B-converge.log", one)
    _run_log(timed_out, "B.md", "11:00:00 · 0052-z · spawn — converge · model m")
    _, rows = review_metrics.cost_table([_record(timed_out, "0052-z")])
    assert rows[0][2] == "$0.25 · 1 turns · 4 tokens · 1 s · 1 of 2"

    # A spawn line naming no model is a dollar gap, though a `default` row exists.
    nameless = tmp_path / "nameless"
    _findings(nameless, "0054-v_review.md", _front())
    _worker_log(nameless, "0054-v", "A-converge.log", spawn(None), turn)
    record = _record(nameless, "0054-v")
    assert record["cost_converge"] is None
    assert record["tokens_converge"] == 1_100_000

    # A field one read log lacks is the station's gap, never the other logs' sum.
    mixed = tmp_path / "mixed"
    _findings(mixed, "0053-w_review.md", _front())
    _worker_log(mixed, "0053-w", "A-converge.log", one)
    _worker_log(mixed, "0053-w", "B-converge.log", spawn("o9"), turn)
    record = _record(mixed, "0053-w")
    assert (record["cost_converge"], record["turns_converge"]) == (None, None)
    assert record["seconds_converge"] is None
    assert record["read_converge"] == 2
    _, rows = review_metrics.cost_table([record])
    assert rows[0][2] == "— · 1100004 tokens"


def _said(
    parent: str | None, message: str, model: str, at: str | None = None, **usage: object
) -> object:
    # The CLI's stream-json: one event per content block, each with the usage the
    # message's stream opened with, `stop_reason` null and `output_tokens` a
    # placeholder; no event carries the message's final count.
    held = {"id": message, "model": model, "stop_reason": None, "usage": usage}
    said = {"type": "assistant", "parent_tool_use_id": parent, "message": held}
    return said | ({"timestamp": at} if at else {})


def _answered(tool: str, **last: int) -> object:
    # The Agent tool's result: `totalTokens` and `usage` are its last turn's alone.
    done = {"status": "completed", "totalTokens": sum(last.values()), "usage": last}
    content = [{"type": "tool_result", "tool_use_id": tool, "content": "done"}]
    return {
        "type": "user",
        "parent_tool_use_id": None,
        "message": {"role": "user", "content": content},
        "tool_use_result": done,
    }


def test_the_claude_rows_price_a_worker() -> None:
    rows = review_metrics._prices()
    # A million tokens of each kind, as a Claude message's usage names them.
    usage = review_metrics._usage(
        {
            "input_tokens": 1_000_000,
            "cache_read_input_tokens": 1_000_000,
            "cache_creation_input_tokens": 2_000_000,
            "cache_creation": {"ephemeral_1h_input_tokens": 1_000_000},
            "output_tokens": 1_000_000,
        }
    )
    assert usage is not None
    priced = review_metrics._priced_worker
    assert priced(rows["claude-opus-5-5"], usage) == pytest.approx(37.2)
    assert priced(rows["claude-sonnet-5-5"], usage) == pytest.approx(18.6)
    # Twin: a model with no row, a Codex one, is a gap.
    assert priced(rows.get("gpt-6.1-sol"), usage) is None


def test_review_metrics_books_a_worker_by_its_description() -> None:
    # Why: 0105-converge-switches design D6, D3.
    book = review_metrics.WORKER
    for description, role, round_ in (
        ("fix round 2 · adversarial cards", "fix", "2"),
        ("Adversarial round 1: break it", "Adversarial", "1"),
        ("verify conformance round 3", "verify", "3"),
    ):
        named = book.search(description)
        assert named
        assert (named[1], named[2]) == (role, round_)
    assert book.search("Security station verify round 2") is None
    assert book.search("Explore the parser") is None

    # A stub's `workers: 0` is a gap, as a by-rule file's is.
    assert review_metrics._workers({"mode": "skipped", "workers": "0"}) is None
    assert review_metrics._workers({"mode": "parallel", "workers": "4"}) == 4


def test_review_metrics_books_a_worker_by_its_log_name(tmp_path: Path) -> None:
    # Why: 0108-converge-script design D10; the delta's scenarios.
    _findings(tmp_path, "0001-x_conformance.md", _front())
    sonnet = "claude-sonnet-5-5"
    claude = (
        _said(None, "f1", sonnet, input_tokens=4),
        {"type": "result", "usage": {"input_tokens": 10, "output_tokens": 5}},
    )
    _worker_log(tmp_path, "0001-x", "20261109-101500-converge-fix-r2.log", *claude)
    # A repeat of the spawn is the same role and round.
    _worker_log(
        tmp_path, "0001-x", "20261109-101500-converge-conformance-r1-2.log", *claude
    )
    spawn = {"type": "mf.spawn", "executor": "codex", "model": "gpt-6.1-sol"}
    usage = {"input_tokens": 1000, "cached_input_tokens": 400, "output_tokens": 100}
    _worker_log(
        tmp_path,
        "0001-x",
        "20261109-101500-converge-verify-pickup-r3.log",
        spawn,
        {"type": "turn.completed", "usage": usage},
    )
    # A log of another form is booked to no role, as a gap.
    _worker_log(tmp_path, "0001-x", "20261109-101500-converge-extra.log", *claude)
    # An older converge log and a mailbox checker's are read as before, and once.
    _worker_log(tmp_path, "0001-x", "A-converge.log", *claude)
    _worker_log(tmp_path, "0001-x", "A-converge-adversarial.log", *claude)

    keys = ("role", "round", "model", "tokens", "source")
    booked = [
        tuple(w[k] for k in keys)
        for w in review_metrics._converge_workers(tmp_path, "0001-x")
    ]
    assert booked == [
        ("adversarial", None, sonnet, 15, "mailbox"),
        ("conformance", 1, sonnet, 15, "log"),
        (None, None, sonnet, 15, "log"),
        ("fix", 2, sonnet, 15, "log"),
        ("verify-pickup", 3, "gpt-6.1-sol", 1100, "log"),
    ]


def test_workers_are_priced_per_round_and_role(tmp_path: Path) -> None:
    # A round's record sums its own run's workers alone, never another run's of
    # the same round number; a worker placed in no run joins no record.
    row = {"repo": "repo", "change": "0001-x", "round": 1, "role": "conformance"}
    rows = [row | {"run": 1}, row | {"run": 2}, row | {"run": None}]
    spent = [row | {"run": run, "dollars": 2.0} for run in (1, 2, None)]
    priced = review_metrics._priced_rounds(rows, spent)
    assert [r["dollars"] for r in priced] == [2.0, 2.0, None]

    repo = tmp_path / "repo"
    claude = "executor claude · model m · effort high · tokens 9"
    fanned = "fan-out — conformance and adversarial dispatched · 2 workers"
    # An amend run restarts at round 1.
    log = (
        "# 0001-x — converge status\n\n## Run 2 — 2026-11-05 12:00\n"
        f"12:10:00 · round 1 · verdicts — conformance clean · {claude}\n"
        f"12:00:30 · round 1 · {fanned}\n"
        "12:00:10 · round 1 · freeze — a..b · 1 commit · 1 file\n\n"
        "## Run 1 — 2026-11-05 10:00\n"
        f"10:10:00 · round 1 · verdicts — adversarial clean · {claude}\n"
        f"10:10:00 · round 1 · verdicts — conformance clean · {claude}\n"
        f"10:00:30 · round 1 · {fanned}\n"
        "10:00:10 · round 1 · freeze — a..b · 1 commit · 1 file\n"
    )
    _findings(repo, "0001-x_status_log.md", log)
    prices = repo / ".minions" / "prices.toml"
    prices.write_text(
        "[models]\n"
        '"claude-sonnet-5-5" = { input = 3.0, cached_input = 0.3, cache_write = 3.75,'
        " cache_write_1h = 6.0, output = 15.0 }\n"
        '"claude-opus-5-5" = { input = 5.0, cached_input = 0.5, output = 25.0 }\n'
        '"gpt-6.1-sol" = { input = 2.0, cached_input = 0.5, output = 10.0 }\n'
    )

    def task(tool: str, description: str) -> object:
        return {
            "type": "system",
            "subtype": "task_started",
            "tool_use_id": tool,
            "description": description,
        }

    sonnet, opus = "claude-sonnet-5-5", "claude-opus-5-5"
    written = {"ephemeral_5m_input_tokens": 100, "ephemeral_1h_input_tokens": 200}
    reading = {
        "input_tokens": 10,
        "cache_read_input_tokens": 1000,
        "cache_creation_input_tokens": 300,
        "cache_creation": written,
        "output_tokens": 8,
    }
    at = "2026-11-05T10:01:00.000Z"
    _worker_log(
        repo,
        "0001-x",
        "A-converge.log",
        _said(None, "c0", sonnet, input_tokens=2, cache_read_input_tokens=20000),
        task("t1", "conformance round 1"),
        _said("t1", "m1", sonnet, at, **reading),
        _said("t1", "m1", sonnet, at, **reading),
        _said("t1", "m1", sonnet, at, **reading),
        _said("t1", "m2", sonnet, at, input_tokens=5, output_tokens=5),
        _answered("t1", input_tokens=5, output_tokens=30_000),
        task("t2", "Adversarial round 1: break it"),
        _said("t2", "a1", opus, "2026-11-05T10:02:00Z", input_tokens=1_000_000),
        task("t3", "fix round 1"),
        _said("t3", "f1", "claude-haiku-5-5", "2026-11-05T10:12:00Z", input_tokens=7),
        task("t4", "Explore the parser"),
        {"type": "assistant", "parent_tool_use_id": "t4", "message": {"id": "e0"}},
        _said("t4", "e1", sonnet, at, input_tokens=1),
        _said("t9", "n1", sonnet, input_tokens=1),
        '{"type": "assistant", cut',
        _result(1.5, 9, 60000, m={"inputTokens": 2}),
    )
    # The amend run's conformance worker, at round 1 again.
    again = "2026-11-05T12:01:00Z"
    _worker_log(
        repo,
        "0001-x",
        "B-converge.log",
        task("t5", "conformance round 1"),
        _said("t5", "m5", sonnet, again, input_tokens=3, output_tokens=2),
    )
    # A mailbox checker's log is a worker of its own, its round a gap; a Claude
    # one's tokens are its `result`'s totals, and with no `result`, a gap.
    spawn = {"type": "mf.spawn", "executor": "codex", "model": "gpt-6.1-sol"}
    usage = {"input_tokens": 1000, "cached_input_tokens": 400, "output_tokens": 100}
    turn = {"type": "turn.completed", "usage": usage}
    bare = {"type": "turn.completed"}
    _worker_log(repo, "0001-x", "A-converge-conformance.log", spawn, turn, bare)
    opened = _said(None, "x1", sonnet, input_tokens=4, cache_read_input_tokens=10)
    # Its cache write splits as the CLI writes it: the 5-minute 100 at
    # `cache_write`, the 1-hour 200 at `cache_write_1h`.
    totals = {
        "input_tokens": 9,
        "cache_creation_input_tokens": 300,
        "cache_read_input_tokens": 90,
        "output_tokens": 3000,
        "cache_creation": written,
    }
    _worker_log(
        repo,
        "0001-x",
        "A-converge-adversarial.log",
        opened,
        _said(None, "x2", sonnet, input_tokens=5, output_tokens=2),
        {"type": "result", "total_cost_usd": 0.1, "usage": totals},
    )
    _worker_log(repo, "0001-x", "A-converge-shadow-adversarial.log", opened)
    out = tmp_path / "site" / "page.html"
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(review_metrics, "PRICES", prices)
        patch.setenv("TZ", "UTC")
        assert review_metrics.main(["--repo", str(repo), "--out", str(out)]) == 0

    data = json.loads(out.with_name("review-metrics.json").read_text())
    keys = ("role", "round", "run", "model", "tokens", "first", "source")
    shown = [tuple(w[k] for k in keys) for w in data["workers"]]
    # A subagent's tokens are a gap: its events hold no final output count, and
    # its Agent result only its last turn's.
    assert shown == [
        ("conformance", 1, 1, sonnet, None, 1310, "subagent"),
        ("adversarial", 1, 1, opus, None, 1_000_000, "subagent"),
        ("fix", 1, None, "claude-haiku-5-5", None, 7, "subagent"),
        (None, None, None, sonnet, None, 1, "subagent"),
        ("conformance", 1, 2, sonnet, None, 3, "subagent"),
        ("conformance", None, None, "gpt-6.1-sol", 1100, 1000, "mailbox"),
        ("adversarial", None, None, sonnet, 3399, 14, "mailbox"),
        ("shadow-adversarial", None, None, sonnet, None, 14, "mailbox"),
    ]
    dollars = [worker["dollars"] for worker in data["workers"]]
    # The Claude checker's 0.046629: 9 x 3.0, 90 x 0.3, 3000 x 15.0, and its
    # cache write 100 x 3.75 and 200 x 6.0, a million each.
    expected = [None, None, None, None, None, 0.0024, 0.046629, None]
    assert dollars == [pytest.approx(d) if d else d for d in expected]
    assert {w["repo"] for w in data["workers"]} == {"repo"}
    assert {w["change"] for w in data["workers"]} == {"0001-x"}
    # Each round and role's record holds its workers' dollars: here a gap each.
    held = [(r["run"], r["role"], r["dollars"]) for r in data["records"]]
    assert held == [
        (2, "conformance", None),
        (1, "adversarial", None),
        (1, "conformance", None),
    ]
    assert {s["station"]: s["first"] for s in data["stations"]} == {
        "converge": 20002,
        "converge-conformance": 1000,
        "converge-adversarial": 14,
        "converge-shadow-adversarial": None,
    }
    [converge] = (s for s in data["stations"] if s["station"] == "converge")
    assert (converge["dollars"], converge["turns"], converge["seconds"]) == (1.5, 9, 60)

    # No row, or a row lacking a price a held kind needs, is a gap; none held, none.
    row = {"input": 1.0}
    assert review_metrics._priced_worker(None, {"input": 1}) is None
    assert review_metrics._priced_worker(row, {"input": 1, "output": 2}) is None
    assert review_metrics._priced_worker(row, {"input": 2, "output": 0}) == 2e-6


def test_the_page_draws_charts_and_lists_gaps(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    alpha, beta = tmp_path / "alpha", tmp_path / "beta"
    _findings(
        alpha,
        "0001-a_review.md",
        _front(
            "changes-requested",
            reviewed="2026-01-01",
            round=2,
            tier="high",
            workers=4,
            model="<b>m</b>",
        )
        + _card(1, "blocking · review · correctness — why", "**Verdict:** confirmed."),
    )
    log = """## Run 1 — 2026-01-01 10:00
10:02:00 · round 1 · done — converged in 1 round · 1 card to backlog
10:01:00 · round 1 · verdicts — review clean · tokens 1234567
10:00:00 · round 1 · start — base a · head b · engine generic
"""
    _findings(alpha, "0001-a_status_log.md", log)
    spent = _result(2, 3, 4000, m={"outputTokens": 5})
    _worker_log(alpha, "0001-a", "20260101-100000-converge.log", spent)
    _findings(alpha, "0002-b_review.md", _front(reviewed="2026-01-02"))
    _findings(beta, "0003-c_review.md", _front(reviewed="2026-02-01", round=3))
    before = sorted(tmp_path.rglob("*"))
    out = tmp_path / "site" / "page.html"

    code = review_metrics.main(
        ["--repo", str(alpha), "--repo", str(beta), "--out", str(out)]
    )

    assert code == 0
    assert sorted(path for path in tmp_path.rglob("*") if "site" not in path.parts) == (
        before
    )
    page = out.read_text(encoding="utf-8")
    assert "repos read 2 · changes read 3" in page
    assert page.count('\n<section class="repo">\n') == 2
    assert "1.5 (n=2)" in page
    assert "<tr><td>blocking</td><td>1</td></tr>" in page
    assert "<td>unknown</td>" in page
    assert page.count("<svg") == 2 * len(review_metrics.CHARTS)
    assert page.count("<h3>cost</h3>") == 2
    assert "<td>$2.00 · 3 turns · 5 tokens · 4 s</td>" in page
    assert "<li>beta: capped 1 · confirmed 1 · cost_build 1 · " in page
    assert "&lt;b&gt;m&lt;/b&gt;" in page
    assert "<b>m" not in page
    assert "<script" not in page
    assert "<h2>role, executor and model</h2>" in page

    printed = capsys.readouterr().out.splitlines()
    assert printed[:2] == [str(out.resolve()), "repos: 2 · changes: 3"]
    assert printed[2].startswith("| role | executor | model | changes |")
    row = "| review | unknown | unknown | 1 | 2 (n=1) | 1 (n=1) | 1 (n=1) | 4 (n=1) |"
    # Each role's change's median duration and tokens follow its workers.
    # Why: 0100-worker-diet design D12 (`0097·R4`).
    row += " 120 (n=1) | 1234567 (n=1) |"
    assert row in "\n".join(printed)
    assert "| median workers | median duration (s) | median tokens |" in printed[2]
    assert "<th>median duration (s)</th><th>median tokens</th>" in page
    assert "<b>m" not in "\n".join(printed)
    assert printed[-1].startswith(
        "lacked: capped 2 · confirmed 2 · cost_build 3 · cost_converge 2 · "
    )


def _blocker(card: str, affects: str, *fields: str) -> str:
    role = "adversarial" if card.startswith("S") else "conformance"
    grade = "high" if role == "adversarial" else "blocking"
    lines = [
        f"- **{card} — A defect**",
        f"  - **What it affects:** `{affects}`",
        f"  - **Priority:** {grade} · {role} · stability — why.",
        *(f"  - {field}" for field in fields),
    ]
    return "\n".join(lines) + "\n\n"


def test_the_cross_model_numbers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    prices = tmp_path / "prices.toml"
    prices.write_text(
        '[models]\n"gpt-6.1-sol" = { input = 2.0, cached_input = 0.5, output = 10.0 }\n'
    )
    monkeypatch.setattr(review_metrics, "PRICES", prices)
    # Conformance on Codex, a Claude shadow: both catch R1, the shadow alone R2.
    fixed = _blocker(
        "R1",
        "total.py:12",
        "**Verdict:** confirmed.",
        "**Round:** 1",
        "**Status:** verified — held.",
    )
    log = "\n## Resolution log\n\n- 2026-11-08 · R1 fixed → verified\n"
    _findings(
        repo,
        "0010-a_conformance.md",
        _front("clean", executor="codex", model="gpt-6.1-sol") + fixed + log,
    )
    _findings(repo, "0010-a_adversarial.md", _front(executor="codex"))
    shadow = _blocker("R1", "total.py:14") + _blocker("R2", "README.md")
    _findings(
        repo,
        "0010-a_shadow-conformance.md",
        _front("changes-requested", executor="claude") + shadow,
    )
    _findings(repo, "0010-a_shadow-adversarial.md", _front(executor="claude"))
    usage = {"input_tokens": 1_000_000, "cached_input_tokens": 400_000}
    turn = {"type": "turn.completed", "usage": usage | {"output_tokens": 100_000}}
    spawn = {"type": "mf.spawn", "executor": "codex", "model": "gpt-6.1-sol"}
    _worker_log(repo, "0010-a", "A-converge.log", _result(0.6, 2, 1000, m={}))
    _worker_log(repo, "0010-a", "A-converge-conformance.log", spawn, turn)
    _run_log(
        repo,
        "A.md",
        "10:00:00 · 0010-a · spawn — converge · model m",
        "10:01:00 · 0010-a · spawn — converge-conformance · model gpt-6.1-sol",
    )
    # A later change repeats the first's card, and its own; one more has no converge
    # log.
    repeat = _card(1, "nit · conformance · stability — why", "**Related:** repeat of")
    repeat = repeat.replace("repeat of", "repeat of `0010·R1`, and repeat of 0011·R9")
    _findings(repo, "0011-b_conformance.md", _front(executor="claude") + repeat)
    status = "## Run 1 — 2026-11-08 10:00\n"
    status += "10:01:00 · round 1 · verdicts — adversarial clean · open_blocking 0"
    status += " · executor claude · model m · effort high · tokens 9\n"
    _findings(repo, "0011-b_adversarial.md", _front())
    _findings(repo, "0011-b_status_log.md", status)
    _worker_log(repo, "0011-b", "A-converge.log", _result(0.5, 1, 1000, m={}))
    _findings(repo, "0012-c_conformance.md", _front(executor="claude"))
    out = tmp_path / "site" / "page.html"

    assert review_metrics.main(["--repo", str(repo), "--out", str(out)]) == 0

    data = json.loads(out.with_name("review-metrics.json").read_text())
    roles = {(r["change"], r["role"]): r for r in data["roles"]}
    assert {key: r["executor"] for key, r in roles.items()} == {
        ("0010-a", "conformance"): "codex",
        ("0010-a", "adversarial"): "codex",
        # A file naming none takes its round 1 `verdicts` line's executor.
        ("0011-b", "conformance"): "claude",
        ("0011-b", "adversarial"): "claude",
        ("0012-c", "conformance"): "claude",
    }
    first = roles["0010-a", "conformance"]
    assert (first["model"], first["confirmed_blockers"]) == ("gpt-6.1-sol", 1)
    assert (first["first_verified"], first["first_reopened"]) == (1, 0)
    assert roles["0011-b", "conformance"]["first_verified"] is None
    assert data["shadow"] == [
        {
            "repo": "repo",
            "change": "0010-a",
            "role": "conformance",
            "shared": 1,
            "primary_alone": 0,
            "shadow_alone": 1,
            "shared_blockers": 1,
            "primary_blockers": 0,
            "shadow_blockers": 1,
            "primary_executor": "codex",
            "shadow_executor": "claude",
        },
        {
            "repo": "repo",
            "change": "0010-a",
            "role": "adversarial",
            "shared": 0,
            "primary_alone": 0,
            "shadow_alone": 0,
            "shared_blockers": 0,
            "primary_blockers": 0,
            "shadow_blockers": 0,
            "primary_executor": "codex",
            "shadow_executor": "claude",
        },
    ]
    assert data["escapes"] == [
        {
            "repo": "repo",
            "change": "0011-b",
            "card": "R1",
            "earlier": "0010·R1",
            "role": "conformance",
            "executor": "codex",
        }
    ]
    # The Codex pairing's converge and checker dollars over its one confirmed blocker.
    assert data["headline"] == {
        "unique_blocker_share": {"claude": 0.5, "codex": 0.0},
        "escapes_per_version": round(1 / 3, 4),
        "dollars_per_confirmed_blocker": {"codex": 3.0},
        "first_verify_pass_rate": {"codex": 1.0},
    }
    page = out.read_text(encoding="utf-8")
    assert "<h2>headline</h2>" in page
    for row in (
        ["unique blocker share", "claude", "0.50"],
        ["escapes per version", "—", "0.33"],
        ["dollars per confirmed blocker", "codex", "3.00"],
        ["first verify pass rate", "codex", "1.00"],
    ):
        assert "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" in page
    assert "<th>role</th><th>executor</th><th>model</th>" in page
    capsys.readouterr()

    # With no shadow, cost or first verify, each number is null.
    bare = tmp_path / "bare"
    _findings(bare, "0001-x_conformance.md", _front())
    out = tmp_path / "bare-site" / "page.html"
    assert review_metrics.main(["--repo", str(bare), "--out", str(out)]) == 0
    data = json.loads(out.with_name("review-metrics.json").read_text())
    assert data["headline"] == {
        "unique_blocker_share": None,
        "escapes_per_version": 0.0,
        "dollars_per_confirmed_blocker": None,
        "first_verify_pass_rate": None,
    }
    assert "<tr><td>unique blocker share</td><td>—</td><td>—</td></tr>" in (
        out.read_text(encoding="utf-8")
    )


def test_overrides_win_over_the_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    home = tmp_path / "home"
    named, other = home / "named", tmp_path / "other"
    _findings(named, "0001-a_review.md", _front())
    _findings(other, "0002-b_review.md", _front())
    _findings(other, "0003-c_review.md", _front())
    config = home / "config.toml"
    config.write_text('repos = ["named"]\nout = "page.html"\n', encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert review_metrics.main(["--config", str(config)]) == 0
    assert (home / "page.html").is_file()
    assert "repos: 1 · changes: 1" in capsys.readouterr().out

    (home / "page.html").unlink()
    assert (
        review_metrics.main(
            ["--config", str(config), "--repo", "other", "--out", "here.html"]
        )
        == 0
    )
    assert "repos: 1 · changes: 2" in capsys.readouterr().out
    assert (tmp_path / "here.html").is_file()
    assert not (home / "page.html").exists()

    blocked = ["--config", str(config), "--out", str(config / "page.html")]
    assert review_metrics.main(blocked) == 2
    assert "cannot write" in capsys.readouterr().err

    gone = ["--repo", "missing", "--out", "gone.html"]
    assert review_metrics.main(gone) == 2
    err = capsys.readouterr().err
    assert str((tmp_path / "missing").resolve()) in err
    assert "no .minions/changes or .minions/findings directory" in err
    assert not (tmp_path / "gone.html").exists()


def test_both_layouts_are_read(tmp_path: Path) -> None:
    moved, unmoved = tmp_path / "moved", tmp_path / "unmoved"
    spent = _result(2, 3, 4000, m={"outputTokens": 5})
    log = "## Run 1 — 2026-01-01 10:00\n10:01:00 · round 1 · verdicts — review clean\n"
    _findings(moved, "0001-a_review.md", _front(reviewed="2026-01-01"))
    _findings(moved, "0001-a_status_log.md", log)
    _worker_log(moved, "0001-a", "20260101-100000-converge.log", spent)
    unmoved_findings = unmoved / ".minions" / "findings"
    unmoved_findings.mkdir(parents=True)
    (unmoved_findings / "0002-b_review.md").write_text(_front(reviewed="2026-01-02"))
    (unmoved_findings / "0002-b_status_log.md").write_text(log)
    _run_log(unmoved, "20260102-100000/0002-b_converge.log", spent)
    _run_log(unmoved, "20260102-100000/0002-bc_converge.log", spent)
    # A folder holding the checkers' names reads as one holding the old names.
    named = "## Run 1 — 2026-01-04 10:00\n"
    named += "10:01:00 · round 1 · verdicts — conformance clean\n"
    _findings(moved, "0004-d_conformance.md", _front(reviewed="2026-01-04"))
    _findings(moved, "0004-d_adversarial.md", _front(reviewed="2026-01-05"))
    _findings(moved, "0004-d_status_log.md", named)
    # Per change, the new folder wins over a file left at its old path.
    _findings(moved, "0003-c_review.md", _front(reviewed="2026-01-03"))
    old = moved / ".minions" / "findings"
    old.mkdir()
    (old / "0003-c_review.md").write_text(_front(reviewed="2025-01-01"))
    before = sorted(tmp_path.rglob("*"))

    records = review_metrics.read_repo(moved) + review_metrics.read_repo(unmoved)
    read = {r["change"]: (r["reviewed"], r["cost_converge"]) for r in records}
    assert read == {
        "0001-a": ("2026-01-01", 2.0),
        "0002-b": ("2026-01-02", 2.0),
        "0003-c": ("2026-01-03", None),
        "0004-d": ("2026-01-04", None),
    }
    rounds = review_metrics.round_data(moved) + review_metrics.round_data(unmoved)
    assert sorted({row["change"] for row in rounds}) == ["0001-a", "0002-b", "0004-d"]
    assert {row["role"] for row in rounds if row["change"] == "0004-d"} == {
        "conformance"
    }
    assert sorted(tmp_path.rglob("*")) == before


def _at(second: int) -> str:
    return f"2026-11-05T10:00:{second:02d}Z"


def _when(second: int) -> datetime:
    return datetime(2026, 11, 5, 10, 0, second, tzinfo=UTC)


def _line(kind: str, time: str, **message: object) -> object:
    return {"type": kind, "timestamp": time, "message": message}


def _turn(id: str, time: str, usage: dict[str, int], model: str) -> object:
    return _line("assistant", time, id=id, model=model, usage=usage)


def _tool(id: str, time: str, name: str, **input: object) -> object:
    blocks = [{"type": "tool_use", "id": id, "name": name, "input": input}]
    return _line("assistant", time, id=f"msg-{id}", content=blocks)


def _written(folder: Path, session: str, *lines: object) -> Path:
    path = folder / f"{session}.jsonl"
    _log(path, *lines)
    return path


def _plan_call(id: str = "t1", second: int = 1) -> object:
    return _tool(id, _at(second), "Skill", skill="mf-plan", args="brief=/b/x.md")


def test_the_sessions_key_names_the_folders(tmp_path: Path) -> None:
    config = tmp_path / "conf" / "review-metrics.toml"
    config.parent.mkdir()
    config.write_text('sessions = ["a", "b"]\n', encoding="utf-8")

    folders = review_metrics.session_folders(config)
    assert folders == [(config.parent / "a").resolve(), (config.parent / "b").resolve()]

    # Twin: no key, and no file, name no folder.
    config.write_text('out = "page.html"\n', encoding="utf-8")
    assert review_metrics.session_folders(config) == []
    assert review_metrics.session_folders(tmp_path / "missing.toml") == []

    config.write_text('sessions = "a"\n', encoding="utf-8")
    with pytest.raises(review_metrics.CannotRun, match="`sessions` is not a list"):
        review_metrics.session_folders(config)


def test_a_transcript_is_reduced_to_numbers_and_ids(tmp_path: Path) -> None:
    usage = {"input_tokens": 3, "output_tokens": 2}
    text = [{"type": "text", "text": "PLANTED-text"}]
    answer = [
        {
            "type": "tool_result",
            "tool_use_id": "t3",
            "content": "cut: queued 0001-x\nPLANTED-result",
        }
    ]
    path = _written(
        tmp_path,
        "s1",
        _line("user", _at(0), content="PLANTED-chat"),
        _line("assistant", _at(1), id="m1", model="m", usage=usage, content=text),
        _tool(
            "t1",
            _at(2),
            "Skill",
            skill="mf-plan",
            args="x brief=/b/./x.md from=/b/y.md PLANTED-args",
        ),
        _line(
            "assistant",
            _at(9),
            id="msg-t1",
            content=[{"type": "tool_use", "id": "t0", "name": "Bash", "input": {}}],
        ),
        _tool("t2", _at(3), "Write", file_path="/b/x.md", content="PLANTED-body"),
        _tool(
            "t3",
            _at(4),
            "Bash",
            command="uv run --script conduct.py cut s minor brief=/b/x.md PLANTED-cmd",
        ),
        _line("user", _at(5), content=answer),
    )

    events = review_metrics._transcript(path)

    assert events[0] == {
        "event": "message",
        "id": "m1",
        "time": _when(1),
        "model": "m",
        "usage": review_metrics._usage(usage),
    }
    calls = {e["id"]: e for e in events if e["event"] == "call"}
    base: dict[str, object] = {"event": "call", "mf": False, "conduct": False}
    base |= {"plan": False, "cut": False, "brief": None, "origin": None}
    base |= {"touched": None}
    assert calls["t1"] == base | {
        "id": "t1",
        "time": _when(2),
        "mf": True,
        "plan": True,
        "brief": "/b/x.md",
        "origin": "/b/y.md",
    }
    assert calls["t2"] == base | {"id": "t2", "time": _when(3), "touched": "/b/x.md"}
    assert calls["t3"] == base | {
        "id": "t3",
        "time": _when(4),
        "conduct": True,
        "cut": True,
        "brief": "/b/x.md",
    }
    # A call is at the time of its message's first line.
    assert calls["t0"]["time"] == _when(2)
    assert events[-1] == {"event": "result", "call": "t3", "ids": ["0001-x"]}
    assert "PLANTED" not in str(events)

    # A quoted path with a space and a quoted script name still parse.
    quoted = _written(
        tmp_path,
        "s2",
        _tool("q1", _at(1), "Skill", skill="mf-plan", args='brief="/b/my plan.md"'),
        _tool(
            "q2",
            _at(2),
            "Bash",
            command='uv run --script "/pkg path/conduct.py" cut s minor brief=/b/x.md',
        ),
    )
    found = {e["id"]: e for e in review_metrics._transcript(quoted)}
    assert found["q1"]["brief"] == "/b/my plan.md"
    assert found["q2"]["cut"] is True
    assert found["q2"]["brief"] == "/b/x.md"

    # An unbalanced quote falls back to plain words.
    broken = _written(
        tmp_path,
        "s3",
        _tool(
            "q3",
            _at(1),
            "Bash",
            command='conduct.py cut s minor brief=/b/z.md "open',
        ),
    )
    (call,) = (e for e in review_metrics._transcript(broken) if e["event"] == "call")
    assert (call["cut"], call["brief"]) == (True, "/b/z.md")


def test_an_unreadable_transcript_is_a_gap(tmp_path: Path) -> None:
    # A folder named like a transcript cannot be opened as one.
    (tmp_path / "bad.jsonl").mkdir()
    _written(tmp_path, "good", _plan_call("t1", 1))

    sessions = review_metrics._sessions([tmp_path], set())

    assert [s["id"] for s in sessions] == ["good"]


def test_a_session_with_no_marker_is_not_read(tmp_path: Path) -> None:
    usage = {"input_tokens": 3}
    plain = [
        _line("user", _at(0), content="hello"),
        _turn("m1", _at(1), usage, "m"),
        _tool("t1", _at(2), "Bash", command="ls"),
    ]
    assert review_metrics._transcript(_written(tmp_path, "a", *plain)) == []

    marked = _written(tmp_path, "b", *plain, _plan_call("t2", 3))
    assert any(e["plan"] for e in review_metrics._transcript(marked) if "plan" in e)


def test_a_message_is_priced_once_by_its_id(tmp_path: Path) -> None:
    usage = {"input_tokens": 1_000_000, "output_tokens": 1_000_000}
    path = _written(
        tmp_path,
        "s",
        _turn("m1", _at(1), usage, "claude-sonnet-5-5"),
        _turn("m1", _at(2), {"input_tokens": 9}, "claude-sonnet-5-5"),
        _turn("m2", _at(3), {}, "claude-sonnet-5-5"),
        _plan_call(),
        _turn("m3", _at(4), {"input_tokens": 4}, "no-such-model"),
    )
    messages = [e for e in review_metrics._transcript(path) if e["event"] == "message"]
    assert [m["id"] for m in messages] == ["m1", "m2", "msg-t1", "m3"]

    row = review_metrics._prices()["claude-sonnet-5-5"]
    spend = review_metrics._spend(messages[:3])
    assert spend["dollars"] == pytest.approx(row["input"] + row["output"])
    assert (spend["turns"], spend["tokens"]) == (1, 2_000_000)
    # The same ids again are the same turns.
    assert review_metrics._spend([*messages[:3], *messages[:3]]) == spend

    # Twin: a model with no row is a gap, its tokens and turns stand.
    spend = review_metrics._spend(messages)
    assert spend == {"dollars": None, "turns": 2, "tokens": 2_000_004}


def test_a_subagent_is_read_with_its_launching_call(tmp_path: Path) -> None:
    _written(tmp_path, "s1", _plan_call())
    folder = tmp_path / "s1" / "subagents"
    _log(
        folder / "agent-a.jsonl",
        _turn("a1", _at(5), {"input_tokens": 3}, "m"),
        _tool("ta", _at(6), "Bash", command="ls"),
    )
    meta = {"toolUseId": "t1", "agentType": "PLANTED-type", "description": "PLANTED"}
    (folder / "agent-a.meta.json").write_text(json.dumps(meta), encoding="utf-8")
    # A meta file with no transcript beside it is no subagent.
    (folder / "agent-b.meta.json").write_text("{}", encoding="utf-8")

    found = review_metrics._subagents(tmp_path, "s1")

    assert [(s["launch"], [m["id"] for m in s["messages"]]) for s in found] == [
        ("t1", ["a1", "msg-ta"])
    ]
    assert "PLANTED" not in str(found)
    assert review_metrics._subagents(tmp_path, "none") == []


def test_a_station_session_is_skipped(tmp_path: Path) -> None:
    repo, folder = tmp_path / "repo", tmp_path / "sessions"

    def init(session: str) -> object:
        return {"type": "system", "subtype": "init", "session_id": session}

    _worker_log(repo, "0001-x", "20260101-100000-build.log", init("s1"))
    _run_log(repo, "20260101-100000/0002-y_cut.log", init("s3"))
    # An init past the log's first lines is no station's.
    late = [{"type": "assistant"}] * 5
    _worker_log(repo, "0001-x", "20260101-100000-cut.log", *late, init("s4"))
    # A log that cannot be opened names no session.
    (repo / ".minions" / "changes" / "0001-x" / "logs" / "gone.log").mkdir()
    for session in ("s1", "s2", "s3", "s4"):
        _written(folder, session, _plan_call())
    _written(folder, "s5", _tool("t1", _at(1), "Bash", command="ls"))
    _log(folder / "s1" / "subagents" / "agent-a.jsonl", _plan_call())
    (folder / "s1" / "subagents" / "agent-a.meta.json").write_text("{}")

    skipped = review_metrics._station_sessions([repo])
    assert skipped == {"s1", "s3"}

    found = review_metrics._sessions([folder, tmp_path / "none"], skipped)
    assert [session["id"] for session in found] == ["s2", "s4"]
    assert found[0]["subagents"] == []
    assert found[0]["events"] == review_metrics._transcript(folder / "s2.jsonl")


def _subagent(
    folder: Path, session: str, name: str, launch: str, *lines: object
) -> None:
    base = folder / session / "subagents"
    _log(base / f"agent-{name}.jsonl", *lines)
    meta = base / f"agent-{name}.meta.json"
    meta.write_text(json.dumps({"toolUseId": launch}), encoding="utf-8")


def _used(id: str, second: int, tokens: int = 1) -> object:
    return _turn(id, _at(second), {"input_tokens": tokens}, "claude-sonnet-5-5")


def _write(id: str, second: int, path: str) -> object:
    return _tool(id, _at(second), "Write", file_path=path)


def _cut_log(repo: Path, change: str, second: int) -> None:
    """Write the change's folder and a cut log last written at `second`."""
    _findings(repo, f"{change}_status_log.md", "")
    name = "20261105-100003-cut.log"
    _worker_log(repo, change, name, _result(0.5, 2, 3000))
    log = repo / ".minions" / "changes" / change / "logs" / name
    stamp = _when(second).timestamp()
    os.utime(log, (stamp, stamp))


def _cut(id: str, second: int, brief: str) -> object:
    command = f"uv run --script conduct.py cut s minor brief={brief}"
    return _tool(id, _at(second), "Bash", command=command)


def _queue_answer(call: str, *ids: str) -> object:
    text = "".join(f"cut: queued {ident}\n" for ident in ids)
    block = [{"type": "tool_result", "tool_use_id": call, "content": text}]
    return _line("user", _at(0), content=block)


def _messages(found: list[dict[str, Any]]) -> list[str]:
    return [m["id"] for m in found]


def test_a_plan_span_runs_from_the_skill_to_the_last_write(tmp_path: Path) -> None:
    _written(
        tmp_path,
        "s1",
        _used("m0", 1),
        _plan_call("t1", 2),
        _used("m1", 3),
        _write("t2", 4, "/b/x.md"),
        _used("m2", 5),
        _write("t3", 6, "/b/./x.md"),
        _used("m3", 7),
        _tool("tx", _at(8), "Skill", skill="mf-plan", args=""),
        _tool("t9", _at(9), "Bash", command="ls"),
    )
    _subagent(tmp_path, "s1", "a", "t2", _used("a1", 40))
    _subagent(tmp_path, "s1", "b", "t9", _used("b1", 4))
    _subagent(tmp_path, "s1", "c", "nope", _used("c1", 4))
    # A write before the opening does not close the span; the opening alone does.
    _written(
        tmp_path,
        "s2",
        _write("w", 3, "/b/x.md"),
        _tool("t1", _at(5), "Skill", skill="mf-plan", args="brief=/b/x.md"),
    )
    # Of two spans that hold a message, the one opened latest does.
    _written(
        tmp_path,
        "s3",
        _plan_call("t1", 1),
        _tool("t2", _at(3), "Skill", skill="mf-plan", args="brief=/b/y.md"),
        _used("m4", 4),
        _write("t3", 5, "/b/y.md"),
        _write("t4", 8, "/b/x.md"),
    )

    sessions = review_metrics._sessions([tmp_path], set())
    spans = review_metrics._spans(sessions)

    found = {
        (s["session"], s["chain"]): (s["open"], s["close"], _messages(s["messages"]))
        for s in spans
    }
    assert found == {
        ("s1", 0): (
            _when(2),
            _when(6),
            ["msg-t1", "m1", "msg-t2", "m2", "msg-t3", "a1"],
        ),
        ("s2", 0): (_when(5), _when(5), ["msg-t1"]),
        ("s3", 0): (_when(1), _when(8), ["msg-t1", "msg-t4"]),
        ("s3", 1): (_when(3), _when(5), ["msg-t2", "m4", "msg-t3"]),
    }


def test_a_continuation_joins_the_plan(tmp_path: Path) -> None:
    _written(tmp_path, "s1", _plan_call("t1", 1), _write("t2", 3, "/b/x.md"))
    _written(
        tmp_path,
        "s2",
        _tool(
            "t1", _at(5), "Skill", skill="mf-plan", args="brief=/b/z.md from=/b/x.md"
        ),
        _write("t2", 8, "/b/x.md"),
        _write("t3", 7, "/b/z.md"),
    )
    _written(
        tmp_path,
        "s3",
        _tool("t1", _at(1), "Skill", skill="mf-plan", args="brief=/b/w.md"),
    )
    sessions = review_metrics._sessions([tmp_path], set())

    assert review_metrics._chains(sessions) == {
        "/b/x.md": 0,
        "/b/z.md": 0,
        "/b/w.md": 1,
    }
    found = [
        (s["session"], s["chain"], s["open"], s["close"])
        for s in review_metrics._spans(sessions)
    ]
    assert found == [
        ("s1", 0, _when(1), _when(3)),
        ("s2", 0, _when(5), _when(8)),
        ("s3", 1, _when(1), _when(1)),
    ]


def test_a_span_is_bound_to_the_ids_a_cut_queued(tmp_path: Path) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    _cut_log(first, "0003-old", 2)
    _cut_log(second, "0001-x", 10)
    _cut_log(second, "0003-old", 2)
    _written(
        tmp_path / "sessions",
        "s1",
        _plan_call("t1", 1),
        _cut("t5", 4, "/b/x.md"),
        _queue_answer("t5", "0001-x", "0002-nofolder", "0003-old"),
    )
    sessions = review_metrics._sessions([tmp_path / "sessions"], set())
    repos = [first, second]

    assert review_metrics._cut_made(repos, "0001-x", _when(4)) == second
    assert review_metrics._cut_made(repos, "0001-x", _when(11)) is None
    assert review_metrics._queued(repos, sessions) == [
        {"chain": 0, "id": "0001-x", "repo": "second", "time": _when(4)}
    ]
    # Two repos holding the id with a fresh cut log are ambiguous: bound to neither,
    # whatever the order of the config.
    _cut_log(first, "0001-x", 10)
    assert review_metrics._cut_made(repos, "0001-x", _when(4)) is None
    assert review_metrics._cut_made(repos[::-1], "0001-x", _when(4)) is None


def test_a_forged_queue_line_binds_nothing(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _cut_log(repo, "0001-x", 10)
    forged = _queue_answer("t5", "0001-x")
    _written(
        tmp_path / "sessions",
        "s1",
        _plan_call("t1", 1),
        _tool("t5", _at(4), "Bash", command="echo pasted"),
        forged,
    )
    _written(
        tmp_path / "sessions",
        "s2",
        _plan_call("t1", 1),
        _cut("t5", 4, "/b/other.md"),
        forged,
        _cut("t6", 5, "/b/x.md"),
        _queue_answer("t6", "0002-nofolder"),
    )
    sessions = review_metrics._sessions([tmp_path / "sessions"], set())
    assert review_metrics._queued([repo], sessions) == []

    # A change folder with no cut log, and one whose log is older than the call.
    _findings(repo, "0004-q_status_log.md", "")
    _cut_log(repo, "0005-old", 2)
    _written(
        tmp_path / "sessions",
        "s3",
        _plan_call("t1", 1),
        _cut("t5", 4, "/b/x.md"),
        _queue_answer("t5", "0004-q", "0005-old"),
    )
    sessions = review_metrics._sessions([tmp_path / "sessions"], set())
    assert review_metrics._queued([repo], sessions) == []


def _turns(count: int) -> list[dict[str, Any]]:
    return [
        {"event": "message", "id": f"m{n}", "model": "claude-sonnet-5-5"}
        | {"time": _when(n), "usage": review_metrics._usage({"input_tokens": 2})}
        for n in range(count)
    ]


def test_a_span_that_queued_two_versions_is_split_equally() -> None:
    messages = _turns(5)
    spans = [
        {"chain": 0, "open": _when(1), "close": _when(6), "messages": messages},
        {"chain": 0, "open": _when(10), "close": _when(13), "messages": []},
    ]
    queued = [
        {"chain": 0, "id": "0001-x", "repo": "r", "time": _when(4)},
        {"chain": 0, "id": "0002-y", "repo": "r", "time": _when(4)},
        {"chain": 1, "id": "0003-z", "repo": "r", "time": _when(4)},
    ]
    whole = review_metrics._spend(messages)

    rows = review_metrics._plan_rows(spans, queued)

    assert [(r["repo"], r["change"], r["station"]) for r in rows] == [
        ("r", "0001-x", "plan"),
        ("r", "0002-y", "plan"),
    ]
    for row in rows:
        assert row["turns"] == 2.5
        assert row["tokens"] == 5
        assert row["seconds"] == 4.0
        assert row["dollars"] == pytest.approx(whole["dollars"] / 2)
        assert row["first"] is None
    # One id keeps the figures whole.
    (row,) = review_metrics._plan_rows(spans, queued[:1])
    assert (row["turns"], row["tokens"], row["seconds"]) == (5, 10, 8)


def test_a_plan_never_queued_is_unbooked() -> None:
    spans = [
        {"chain": 0, "open": _when(1), "close": _when(4), "messages": _turns(2)},
        {"chain": 1, "open": _when(1), "close": _when(4), "messages": []},
    ]
    queued = [{"chain": 2, "id": "0003-z", "repo": "r", "time": _when(4)}]

    rows = review_metrics._plan_rows(spans, queued)

    assert [(r["repo"], r["change"], r["station"], r["turns"]) for r in rows] == [
        (None, None, "plan", 2)
    ]
    assert review_metrics._plan_rows([], queued) == []


def test_operator_work_is_booked_to_the_nearest_mark(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TZ", "UTC")
    repo = tmp_path / "repo"
    _run_log(
        repo,
        "20261105-100000.md",
        "10:00:00 · run · start — executor claude",
        "10:00:10 · 0002-y · spawn — build · model m",
        "10:00:40 · 0002-y · removed — a worktree",
    )
    _run_log(
        repo,
        "20261105-235900.md",
        "23:59:50 · 0004-w · spawn — build · model m",
        "00:00:10 · 0005-v · spawn — build · model m",
        "13:00:00 · 0007-t · spawn — build · model m",
        "00:30:00 · 0008-s · spawn — build · model m",
    )
    # A run log that cannot be read holds no mark.
    (repo / ".minions" / "runs" / "20261105-120000.md").mkdir()
    # A log whose name is no stamp has no date, so no mark.
    _run_log(repo, "notes.md", "10:00:20 · 0006-q · spawn — build · model m")
    _written(
        tmp_path / "sessions",
        "s1",
        _used("mA", 0, 1),
        _plan_call("t1", 1),
        _used("mB", 2, 100),
        _write("t2", 3, "/b/x.md"),
        _used("mC", 5, 2),
        _tool("tL", _at(6), "Bash", command="conduct.py status"),
        _used("mD", 20, 4),
        _used("mE", 50, 8),
        _line("assistant", "2026-11-06T00:00:20Z", id="mF", usage={"input_tokens": 32}),
    )
    _subagent(tmp_path / "sessions", "s1", "a", "tL", _used("a1", 55, 16))
    sessions = review_metrics._sessions([tmp_path / "sessions"], set())
    spans = review_metrics._spans(sessions)
    queued = [{"chain": 0, "id": "0001-x", "repo": "repo", "time": _when(2)}]

    marks = review_metrics._marks([repo], queued)

    assert [(m["change"], m["time"]) for m in marks] == [
        ("0001-x", _when(2)),
        ("0002-y", _when(10)),
        (None, _when(40)),
        ("0004-w", datetime(2026, 11, 5, 23, 59, 50, tzinfo=UTC)),
        ("0005-v", datetime(2026, 11, 6, 0, 0, 10, tzinfo=UTC)),
        ("0007-t", datetime(2026, 11, 6, 13, 0, 0, tzinfo=UTC)),
        ("0008-s", datetime(2026, 11, 7, 0, 30, 0, tzinfo=UTC)),
    ]
    rows = review_metrics._operator(sessions, spans, marks)
    assert [(r["repo"], r["change"], r["station"], r["tokens"]) for r in rows] == [
        (None, None, "operator", 9),
        ("repo", "0001-x", "operator", 18),
        ("repo", "0002-y", "operator", 4),
        ("repo", "0005-v", "operator", 32),
    ]
    assert all(r["seconds"] is None for r in rows)


def test_a_subagent_books_where_its_call_was_launched(tmp_path: Path) -> None:
    folder = tmp_path / "sessions"
    _written(
        folder,
        "s1",
        _plan_call("t1", 1),
        _tool("tL", _at(6), "Bash", command="ls"),
        _tool("tM", _at(30), "Bash", command="ls"),
    )
    _subagent(folder, "s1", "a", "tL", _used("a1", 55, 16))
    _subagent(folder, "s1", "b", "tM", _used("b1", 31, 32))
    sessions = review_metrics._sessions([folder], set())
    spans = review_metrics._spans(sessions)
    marks = [
        {"time": _when(2), "repo": "r", "change": "0001-x"},
        {"time": _when(20), "repo": "r", "change": "0002-y"},
    ]

    rows = review_metrics._operator(sessions, spans, marks)

    # a1 ran at 55, after the second mark, but was launched at 6.
    assert [(r["change"], r["tokens"]) for r in rows] == [
        ("0001-x", 16),
        ("0002-y", 32),
    ]


def test_booked_rows_have_the_keys_of_a_station_row(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _cut_log(repo, "0001-x", 30)
    _written(
        tmp_path / "sessions",
        "s1",
        _plan_call("t1", 1),
        _used("m1", 2, 4),
        _write("t2", 3, "/b/x.md"),
        _cut("t3", 4, "/b/x.md"),
        _queue_answer("t3", "0001-x"),
        _used("m2", 40, 8),
    )
    station = review_metrics._stations(_record(repo, "0001-x"))[0]

    rows = review_metrics.booked([repo], [tmp_path / "sessions"])

    assert [(r["station"], r["change"], r["tokens"]) for r in rows] == [
        ("plan", "0001-x", 4),
        ("operator", "0001-x", 8),
    ]
    assert all(set(row) == set(station) for row in rows)
    assert review_metrics.booked([repo], []) == []


def _booking(tmp_path: Path) -> tuple[Path, Path]:
    """Write a repo, three sessions and a config naming them; return both paths."""
    repo = tmp_path / "repo"
    _cut_log(repo, "0001-x", 30)
    _cut_log(repo, "0002-y", 30)
    folder = tmp_path / "sessions"
    _written(
        folder,
        "s1",
        _plan_call("t1", 1),
        _used("m1", 2, 4),
        _write("t2", 3, "/b/x.md"),
        _cut("t3", 4, "/b/x.md"),
        _queue_answer("t3", "0001-x"),
        _used("m2", 40, 8),
    )
    _written(
        folder,
        "s2",
        _used("u0", 0, 2),
        _tool("t1", _at(1), "Skill", skill="mf-plan", args="brief=/b/y.md"),
        _used("u1", 2, 16),
    )
    _written(
        folder,
        "s3",
        _tool("t1", _at(10), "Skill", skill="mf-plan", args="brief=/b/z.md"),
        _used("z1", 11, 2),
        _write("t2", 12, "/b/z.md"),
        _cut("t3", 13, "/b/z.md"),
        _queue_answer("t3", "0001-x"),
    )
    config = tmp_path / "config.toml"
    config.write_text('sessions = ["sessions"]\n', encoding="utf-8")
    return repo, config


def test_the_plan_and_operator_rows_reach_the_data_and_the_page(tmp_path: Path) -> None:
    repo, config = _booking(tmp_path)
    out = tmp_path / "site" / "page.html"
    args = ["--config", str(config), "--repo", str(repo), "--out", str(out)]

    assert review_metrics.main(args) == 0

    data = json.loads(out.with_name("review-metrics.json").read_text())
    found = [
        (r["change"], r["station"], r["turns"], r["tokens"])
        for r in data["stations"]
        if r["station"] in ("plan", "operator")
    ]
    assert sorted(found, key=repr) == sorted(
        [
            ("0001-x", "plan", 1, 4),
            ("0001-x", "plan", 1, 2),
            (None, "plan", 0, 0),
            ("0001-x", "operator", 1, 8),
            (None, "operator", 2, 18),
        ],
        key=repr,
    )
    assert {r["repo"] for r in data["stations"] if r["change"] is None} == {None}

    page = out.read_text(encoding="utf-8").splitlines()
    assert page[page.index("<h3>cost</h3>") + 2].endswith(
        "<th>plan</th><th>operator</th></tr>"
    )
    row = next(line for line in page if line.startswith("<tr><td>0001-x</td>"))
    plan, operator = "$0.00 · 2 turns · 6 tokens · 4 s", "$0.00 · 1 turns · 8 tokens"
    assert row.endswith(f"<td>{plan}</td><td>{operator}</td></tr>")
    row = next(line for line in page if line.startswith("<tr><td>0002-y</td>"))
    assert row.endswith("<td>—</td><td>—</td></tr>")
    unbooked = page[page.index("<h2>unbooked</h2>") + 1 :]
    assert "<tr><td>plan</td><td>— · 0 turns · 0 tokens · 0 s</td></tr>" in unbooked
    assert "<tr><td>operator</td><td>$0.00 · 2 turns · 18 tokens</td></tr>" in unbooked

    # Twin: a config with no `sessions` key books no row, no column and no table.
    config.write_text('out = "page.html"\n', encoding="utf-8")
    bare = tmp_path / "bare" / "page.html"
    args = ["--config", str(config), "--repo", str(repo), "--out", str(bare)]
    assert review_metrics.main(args) == 0
    data = json.loads(bare.with_name("review-metrics.json").read_text())
    assert {r["station"] for r in data["stations"]} == {"cut"}
    plain = bare.read_text(encoding="utf-8")
    assert "<th>plan</th>" not in plain
    assert "unbooked" not in plain


def test_a_secret_in_a_transcript_is_never_written(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    secret, brief = "PLANTED-sk-0123456789", "/vault/PLANTED-brief/x.md"
    repo = tmp_path / "repo"
    _cut_log(repo, "0001-x", 30)
    said = [{"type": "text", "text": secret}]
    answer = [
        {
            "type": "tool_result",
            "tool_use_id": "t3",
            "content": f"cut: queued 0001-x\n{secret}",
        }
    ]
    command = f"uv run --script conduct.py cut s minor brief={brief} {secret}"
    session = _written(
        tmp_path / "sessions",
        "s1",
        _turn("m0", _at(0), {"input_tokens": 3}, "claude-sonnet-5-5"),
        _line("assistant", _at(0), id="m0", content=said),
        _tool("t1", _at(1), "Skill", skill="mf-plan", args=f"brief={brief} {secret}"),
        _write("t2", 3, brief),
        _tool("t3", _at(4), "Bash", command=command),
        _line("user", _at(5), content=answer),
        _line("user", _at(6), content=secret),
    )
    config = tmp_path / "config.toml"
    config.write_text('sessions = ["sessions"]\n', encoding="utf-8")
    out = tmp_path / "site" / "page.html"
    args = ["--config", str(config), "--repo", str(repo), "--out", str(out)]

    assert review_metrics.main(args) == 0

    data = out.with_name("review-metrics.json").read_text(encoding="utf-8")
    stations = {row["station"] for row in json.loads(data)["stations"]}
    assert {"plan", "operator"} <= stations
    assert secret in session.read_text(encoding="utf-8")
    written = [out.read_text(encoding="utf-8"), data, capsys.readouterr().out]
    for text in written:
        for planted in (secret, brief, "PLANTED", "vault"):
            assert planted not in text
