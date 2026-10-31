"""The review-metrics station: the config, the reader, the page.

Why: 0045-review-metrics design D1…D7.
"""

import importlib.util
import re
from pathlib import Path
from types import ModuleType

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
    folder = root / ".minions" / "findings"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(text, encoding="utf-8")


def _record(root: Path, change: str) -> dict[str, object]:
    return next(r for r in review_metrics.read_repo(root) if r["change"] == change)


def test_no_config_exits_2_naming_the_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    assert review_metrics.main([]) == 2

    looked_for = tmp_path / "minionsfactory" / "review-metrics.toml"
    assert str(looked_for) in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


def test_each_era_parses_with_gaps(tmp_path: Path) -> None:
    bullets = "- **severity:** blocking\n- **severity:** `nit`\n- **severity:** nit\n"
    _findings(
        tmp_path,
        "0008-old_review.md",
        _front("changes-requested", reviewed="2026-01-02", round=2) + bullets,
    )

    _findings(tmp_path, "0009-clean_review.md", _front(reviewed="2026-02-01"))

    no_tier = _card(1, "`medium · security (integrity)` — why · and why")
    no_tier += _card(2, "high · security")
    _findings(
        tmp_path,
        "0014-carded_security.md",
        _front("changes-requested", reviewed="2026-03-01") + no_tier,
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
    tiered = _front(
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
    _findings(tmp_path, "0042-tiered_review.md", tiered + verdicts + summary)
    _findings(
        tmp_path,
        "0042-tiered_security.md",
        _front(
            reviewed="2026-10-30", round=3, tier="high", workers=5, model="other-model"
        )
        + "## Refuted\n\nNone.\n",
    )

    old = _record(tmp_path, "0008-old")
    assert (old["repo"], old["reviewed"]) == (tmp_path.name, "2026-01-02")
    assert (old["rounds"], old["findings"], old["blocking"]) == (2, 3, 1)
    assert old["severity"] == {"blocking": 1, "nit": 2}
    assert (old["tier"], old["model"], old["workers"]) == (None, None, None)
    assert (old["confirmed"], old["verified"], old["inconclusive"]) == (
        None,
        None,
        None,
    )

    clean = _record(tmp_path, "0009-clean")
    assert (clean["findings"], clean["blocking"]) == (0, 0)
    assert clean["confirmed"] is None

    carded = _record(tmp_path, "0014-carded")
    assert (carded["findings"], carded["blocking"], carded["tier"]) == (2, 1, None)
    assert carded["severity"] == {"medium": 1, "high": 1}
    assert carded["categories"] == {"integrity": 1}

    tier = _record(tmp_path, "0042-tiered")
    assert (tier["tier"], tier["mode"], tier["model"]) == (
        "high",
        "parallel",
        "some-model",
    )
    assert (tier["rounds"], tier["workers"]) == (3, 12)
    assert (tier["packet_included"], tier["packet_skipped"]) == (3, 1)
    assert (tier["findings"], tier["blocking"]) == (3, 1)
    assert tier["categories"] == {"functional correctness": 1, "maintainability": 2}
    assert (tier["confirmed"], tier["plausible"], tier["plausible_verified"]) == (
        1,
        2,
        1,
    )
    assert (tier["refuted"], tier["inconclusive"]) == (2, 1)
    assert tier["duration"] is None

    _findings(
        tmp_path,
        "0043-quoted_review.md",
        _front(
            reviewed="2026-10-30",
            tier='"standard"',
            model='"quoted-model"',
            packet='"proposal.md, design.md; skipped: none"',
        )
        + "## Summary\n\nNo section is inconclusive.\n",
    )
    unquoted = _record(tmp_path, "0043-quoted")
    assert (unquoted["tier"], unquoted["model"]) == ("standard", "quoted-model")
    assert (unquoted["packet_included"], unquoted["packet_skipped"]) == (2, 0)
    assert unquoted["inconclusive"] == 0

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

    skill = _REPO / "skills" / "mf-converge" / "SKILL.md"
    listed = re.search(r"category one of (.*?);", skill.read_text(encoding="utf-8"))
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
00:01:00 · round 2 · done — converged in 2 rounds · 3 cards to backlog · gate exit 0
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
    assert "<li>beta: capped 1 · " in page
    assert "&lt;b&gt;m&lt;/b&gt;" in page
    assert "<b>m" not in page
    assert "<script" not in page

    printed = capsys.readouterr().out.splitlines()
    assert printed[:2] == [str(out.resolve()), "repos: 2 · changes: 3"]
    assert printed[2].startswith("| tier | model | engine | changes |")
    assert "| high | <b>m</b> | generic | 1 | 2 (n=1) |" in "\n".join(printed)
    assert printed[-1].startswith("lacked: capped 2 · confirmed 2 · ")


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
