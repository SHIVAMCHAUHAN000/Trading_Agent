"""Run V2 liquidity-sweep research and write dashboard."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analytics.performance.metrics import compute_performance_metrics  # noqa: E402
from backtesting.engine_v2.liquidity_sweep import run_liquidity_sweep_backtest  # noqa: E402
from reports_ui.render_dashboard import write_dashboard  # noqa: E402
from strategies.loader_v2 import load_strategy_spec_v2  # noqa: E402


def _load_bars() -> tuple[pd.DataFrame, dict]:
    pointer = ROOT / "config" / "latest_xau_dataset.yaml"
    if not pointer.exists():
        raise FileNotFoundError("No XAU dataset. Run scripts/run_xau_1m_pipeline.py first.")
    meta = yaml.safe_load(pointer.read_text(encoding="utf-8"))
    path = ROOT / meta["bars_path"]
    bars = pd.read_parquet(path)
    bars["DateTime"] = pd.to_datetime(bars["DateTime"], utc=True)
    return bars, meta


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--strategy",
        default=str(ROOT / "strategies" / "defs" / "liquidity_sweep_ny_session_v1.yaml"),
    )
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()

    spec = load_strategy_spec_v2(args.strategy)
    bars, data_meta = _load_bars()

    # Fill TBD period from available data
    if spec.period.start is None:
        spec.period.start = str(pd.Timestamp(bars["DateTime"].min()).date())
    if spec.period.end is None:
        spec.period.end = str(pd.Timestamp(bars["DateTime"].max()).date())

    result = run_liquidity_sweep_backtest(spec, bars)
    eq = result.equity_curve.copy()
    if result.trades.empty:
        metrics = {
            **{k: float("nan") for k in ["cagr", "sharpe", "max_drawdown", "win_rate", "profit_factor", "expectancy"]},
            "n_trades": 0,
            "total_return": float(eq["Equity"].iloc[-1] / float(spec.capital) - 1.0),
            "end_equity": float(eq["Equity"].iloc[-1]),
        }
    else:
        metrics = compute_performance_metrics(eq, result.trades, capital=float(spec.capital))

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path(args.out_dir) if args.out_dir else ROOT / "reports" / f"research_{spec.name}_{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    result.equity_curve.to_csv(out / "equity_curve.csv")
    result.trades.to_csv(out / "trades.csv", index=False)

    short_history = int(data_meta.get("rows", 0)) < 5000
    conclusion = "INCONCLUSIVE" if short_history or metrics.get("n_trades", 0) < 5 else ("PROMISING" if (metrics.get("expectancy") or 0) > 0 else "REJECT")
    if short_history:
        rationale = "Smoke run only — Yahoo 1m history is too short for statistical validation."
    elif metrics.get("n_trades", 0) < 5:
        rationale = "Too few trades in available window."
    else:
        rationale = "Preliminary V2 engine result; still needs multi-month Dukascopy history + costs."

    simple = {
        "what_is_the_strategy": (
            f"{spec.name}: NY-session (IST {spec.session.start}-{spec.session.end}) "
            "liquidity sweep double-trap on XAUUSD 1m/15m."
        ),
        "why_might_it_work": spec.notes or "Stop-hunt / liquidity-sweep reversal hypothesis.",
        "how_did_it_perform": (
            f"Trades={metrics.get('n_trades')}, total_return={metrics.get('total_return')}, "
            f"win_rate={metrics.get('win_rate')}, expectancy={metrics.get('expectancy')}, "
            f"data_rows={data_meta.get('rows')} source={data_meta.get('source')}."
        ),
        "how_risky_is_it": f"Max DD={metrics.get('max_drawdown')}; risk per trade ~{spec.position.risk_per_trade_pct}% capital.",
        "what_breaks_it": "Short free 1m history, DST session drift, missing cost model, parameter defaults.",
        "is_result_robust": "Not yet — need Dukascopy multi-month/year sample + OOS/walk-forward V2.",
        "major_warnings": [
            "V2 smoke engine; not institutional validation.",
            "Yahoo GC=F 1m is a gold futures proxy, not pure XAUUSD spot.",
            "US DST can shift the IST 18:30-21:30 window vs NY open.",
            *(result.meta.get("assumptions") or [])[:2],
        ],
        "research_conclusion_summary": f"{conclusion}. {rationale}",
    }

    report = {
        "experiment_id": f"EXP-V2-{stamp}",
        "strategy_name": spec.name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "simple_report": simple,
        "technical_report": {
            "backtest_results": {"performance": metrics, "meta": result.meta, "data": data_meta},
            "trade_statistics": {
                "n_trades": metrics.get("n_trades"),
                "win_rate": metrics.get("win_rate"),
                "expectancy": metrics.get("expectancy"),
                "profit_factor": metrics.get("profit_factor"),
            },
            "benchmark_comparison": {"status": "NOT_IMPLEMENTED_V2_SMOKE"},
            "out_of_sample": {"status": "NOT_IMPLEMENTED_V2_SMOKE"},
            "walk_forward": {"summary": {}},
            "parameter_sensitivity": {"robustness": "NOT_RUN"},
            "cost_sensitivity": {"verdict": "NOT_RUN"},
            "bias_checks": {
                "flags": [
                    {"severity": "critical" if short_history else "warning", "code": "SHORT_1M_HISTORY", "message": "Insufficient 1m history for inference."},
                    {"severity": "warning", "code": "FUTURES_PROXY", "message": "Yahoo GC=F used as XAUUSD proxy when Dukascopy unavailable."},
                    {"severity": "warning", "code": "NO_COSTS", "message": "V2 smoke path does not yet deduct spread/commission."},
                ]
            },
            "research_conclusion": {"status": conclusion, "rationale": rationale},
        },
        "conclusion": {"status": conclusion, "rationale": rationale},
    }
    (out / "research_report.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    (out / "SIMPLE_REPORT.md").write_text(
        "\n".join(
            [
                f"# Research Report (Simple) — {report['experiment_id']}",
                "",
                "## What is the strategy?",
                simple["what_is_the_strategy"],
                "",
                "## Why might it work?",
                simple["why_might_it_work"],
                "",
                "## How did it perform?",
                simple["how_did_it_perform"],
                "",
                "## How risky is it?",
                simple["how_risky_is_it"],
                "",
                "## What breaks it?",
                simple["what_breaks_it"],
                "",
                "## Is the result robust?",
                simple["is_result_robust"],
                "",
                "## Major warnings",
                *[f"- {w}" for w in simple["major_warnings"]],
                "",
                "## Research conclusion",
                simple["research_conclusion_summary"],
                "",
            ]
        ),
        encoding="utf-8",
    )
    dash = write_dashboard(out / "research_report.json", out / "dashboard.html")
    print(json.dumps({"out_dir": str(out), "dashboard": str(dash), "conclusion": conclusion, "metrics": metrics, "meta": result.meta}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
