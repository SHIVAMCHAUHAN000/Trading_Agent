"""Render a self-contained HTML research dashboard from research_report.json."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def _esc(x: Any) -> str:
    return html.escape("" if x is None else str(x))


def _pct(x: Any) -> str:
    try:
        return f"{float(x) * 100:.1f}%"
    except Exception:
        return "n/a"


def _num(x: Any, d: int = 2) -> str:
    try:
        return f"{float(x):.{d}f}"
    except Exception:
        return "n/a"


def render_dashboard_html(report: dict[str, Any]) -> str:
    simple = report.get("simple_report", {})
    tech = report.get("technical_report", {})
    conclusion = report.get("conclusion", {})
    perf = tech.get("backtest_results", {}).get("performance", {})
    trades = tech.get("trade_statistics", {})
    bench = tech.get("benchmark_comparison", {})
    oos = tech.get("out_of_sample", {}).get("out_of_sample", {}).get("metrics", {})
    wf = tech.get("walk_forward", {}).get("summary", {})
    bias = tech.get("bias_checks", {}).get("flags", [])
    warnings = simple.get("major_warnings") or []

    warn_html = "".join(f"<li>{_esc(w)}</li>" for w in warnings) or "<li>None listed</li>"
    bias_html = "".join(
        f"<li><strong>{_esc(f.get('severity'))}</strong> [{_esc(f.get('code'))}] {_esc(f.get('message'))}</li>"
        for f in bias
    ) or "<li>None</li>"

    status = conclusion.get("status", "INCONCLUSIVE")
    status_class = {
        "REJECT": "bad",
        "INCONCLUSIVE": "warn",
        "PROMISING": "ok",
        "VALIDATED_CANDIDATE": "great",
    }.get(status, "warn")

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Research Dashboard — {_esc(report.get('experiment_id'))}</title>
  <style>
    :root {{
      --ink: #14213d;
      --muted: #5c6778;
      --paper: #f7f4ef;
      --card: #ffffff;
      --line: #d9d2c5;
      --ok: #1b7f5a;
      --warn: #9a6b00;
      --bad: #9b2226;
      --great: #0b525b;
      --accent: #c46b2b;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
      color: var(--ink);
      background:
        radial-gradient(1200px 500px at 10% -10%, #efe3d3 0%, transparent 55%),
        radial-gradient(900px 400px at 100% 0%, #e7eef5 0%, transparent 50%),
        var(--paper);
    }}
    main {{ max-width: 980px; margin: 0 auto; padding: 2rem 1.25rem 4rem; }}
    header {{ margin-bottom: 1.75rem; }}
    .eyebrow {{ color: var(--muted); letter-spacing: 0.08em; text-transform: uppercase; font-size: 0.78rem; font-family: ui-sans-serif, system-ui, sans-serif; }}
    h1 {{ font-size: clamp(1.8rem, 4vw, 2.6rem); line-height: 1.15; margin: 0.35rem 0; }}
    .sub {{ color: var(--muted); max-width: 48rem; }}
    .badge {{
      display: inline-block; margin-top: 0.8rem; padding: 0.35rem 0.75rem; border-radius: 999px;
      font-family: ui-sans-serif, system-ui, sans-serif; font-size: 0.85rem; font-weight: 700;
      border: 1px solid var(--line); background: #fff;
    }}
    .badge.ok {{ color: var(--ok); }}
    .badge.warn {{ color: var(--warn); }}
    .badge.bad {{ color: var(--bad); }}
    .badge.great {{ color: var(--great); }}
    .grid {{ display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); margin: 1.5rem 0; }}
    .metric {{ background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 1rem; }}
    .metric .label {{ font-family: ui-sans-serif, system-ui, sans-serif; font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }}
    .metric .value {{ font-size: 1.35rem; margin-top: 0.35rem; }}
    section {{ background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 1.25rem 1.35rem; margin: 1rem 0; }}
    h2 {{ margin: 0 0 0.75rem; font-size: 1.2rem; }}
    p, li {{ line-height: 1.55; }}
    ul {{ padding-left: 1.2rem; }}
    .two {{ display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }}
    footer {{ margin-top: 2rem; color: var(--muted); font-size: 0.9rem; font-family: ui-sans-serif, system-ui, sans-serif; }}
    code {{ background: #f0ebe3; padding: 0.1rem 0.35rem; border-radius: 4px; }}
  </style>
</head>
<body>
  <main>
    <header>
      <div class="eyebrow">Indian Market Strategy Research</div>
      <h1>{_esc(report.get('strategy_name', 'Strategy'))}</h1>
      <p class="sub">{_esc(simple.get('what_is_the_strategy'))}</p>
      <div class="badge {status_class}">{_esc(status)}</div>
      <div class="eyebrow" style="margin-top:0.7rem">{_esc(report.get('experiment_id'))} · {_esc(report.get('created_at'))}</div>
    </header>

    <div class="grid">
      <div class="metric"><div class="label">CAGR</div><div class="value">{_pct(perf.get('cagr'))}</div></div>
      <div class="metric"><div class="label">Sharpe</div><div class="value">{_num(perf.get('sharpe'))}</div></div>
      <div class="metric"><div class="label">Max DD</div><div class="value">{_pct(perf.get('max_drawdown'))}</div></div>
      <div class="metric"><div class="label">Win Rate</div><div class="value">{_pct(trades.get('win_rate'))}</div></div>
      <div class="metric"><div class="label">OOS Sharpe</div><div class="value">{_num(oos.get('sharpe'))}</div></div>
      <div class="metric"><div class="label">Info Ratio</div><div class="value">{_num(bench.get('information_ratio'))}</div></div>
    </div>

    <section>
      <h2>Simple conclusion</h2>
      <p>{_esc(simple.get('research_conclusion_summary'))}</p>
      <p><strong>Why it might work:</strong> {_esc(simple.get('why_might_it_work'))}</p>
      <p><strong>Performance:</strong> {_esc(simple.get('how_did_it_perform'))}</p>
      <p><strong>Risk:</strong> {_esc(simple.get('how_risky_is_it'))}</p>
      <p><strong>What breaks it:</strong> {_esc(simple.get('what_breaks_it'))}</p>
      <p><strong>Robustness:</strong> {_esc(simple.get('is_result_robust'))}</p>
    </section>

    <div class="two">
      <section>
        <h2>Major warnings</h2>
        <ul>{warn_html}</ul>
      </section>
      <section>
        <h2>Bias flags</h2>
        <ul>{bias_html}</ul>
      </section>
    </div>

    <section>
      <h2>Validation snapshot</h2>
      <ul>
        <li>OOS win rate: {_pct(oos.get('win_rate'))}</li>
        <li>Walk-forward positive Sharpe folds: {_esc(wf.get('positive_sharpe_folds'))} / {_esc(wf.get('n_folds'))}</li>
        <li>Mean test Sharpe: {_num(wf.get('mean_test_sharpe'))}</li>
        <li>Parameter robustness: {_esc(tech.get('parameter_sensitivity', {}).get('robustness'))}</li>
        <li>Cost stress: {_esc(tech.get('cost_sensitivity', {}).get('verdict'))}</li>
        <li>Benchmark excess CAGR: {_pct(bench.get('excess_cagr'))}</li>
      </ul>
    </section>

    <footer>
      Research only — no trade execution. Full machine report lives beside this file as <code>research_report.json</code>.
    </footer>
  </main>
</body>
</html>
"""


def write_dashboard(report_path: str | Path, out_path: str | Path | None = None) -> Path:
    report_path = Path(report_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    out = Path(out_path) if out_path else report_path.parent / "dashboard.html"
    out.write_text(render_dashboard_html(report), encoding="utf-8")
    return out
