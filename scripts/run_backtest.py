"""CLI: run a StrategySpec through the backtester and Stage 6 analytics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analytics.report import build_analytics_report  # noqa: E402
from backtesting.engine.engine import run_backtest  # noqa: E402
from strategies.loader import load_strategy_spec  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Backtest runner with Stage 6 analytics")
    parser.add_argument(
        "--strategy",
        default=str(ROOT / "strategies" / "defs" / "momentum_cross_section_v1.yaml"),
        help="Path to StrategySpec YAML",
    )
    parser.add_argument("--cost-multiplier", type=float, default=1.0)
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Output directory (default: reports/<strategy>_<timestamp>)",
    )
    args = parser.parse_args()

    spec = load_strategy_spec(args.strategy)
    result = run_backtest(spec, cost_multiplier=args.cost_multiplier)
    report = build_analytics_report(result, capital=float(spec.capital), bars=result.bars)

    enriched_trades = report.pop("enriched_trades")

    stamp = pd.Timestamp.now("UTC").strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.out_dir) if args.out_dir else ROOT / "reports" / f"{spec.name}_{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    result.equity_curve.to_csv(out_dir / "equity_curve.csv")
    if result.benchmark_equity is not None and not result.benchmark_equity.empty:
        result.benchmark_equity.to_csv(out_dir / "benchmark_equity.csv", header=["BenchmarkEquity"])
    enriched_trades.to_csv(out_dir / "trades.csv", index=False)

    payload = {"meta": result.meta, "analytics": report}
    (out_dir / "summary.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    # Compact stdout: avoid dumping full annual return maps twice
    print(json.dumps({"out_dir": str(out_dir), **payload}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
