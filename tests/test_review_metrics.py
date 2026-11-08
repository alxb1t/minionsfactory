"""The review-metrics station: the config, the reader, the page.

Why: 0045-review-metrics design D1…D7.
"""

import importlib.util
import json
import re
import subprocess
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

    record = _record(tmp_path, "0050-x")
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
            "$4.80 · 2200000 tokens",
            "—",
            "— · 3300000 tokens",
            "$2.40 · 1100000 tokens",
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
    assert row in "\n".join(printed)
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
