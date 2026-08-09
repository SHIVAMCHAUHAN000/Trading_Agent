"""CLI: run a StrategySpec through the Stage 5 backtester."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analytics.performance.metrics import compute_performance_metrics  # noqa: E402
from backtesting.engine.engine import run_backtest  # noqa: E402
from strategies.loader import load_strategy_spec  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage 5 backtest runner")
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
    metrics = compute_performance_metrics(
        result.equity_curve,
        result.trades,
        capital=float(spec.capital),
    )

    stamp = pd.Timestamp.now("UTC").strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.out_dir) if args.out_dir else ROOT / "reports" / f"{spec.name}_{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    result.equity_curve.to_csv(out_dir / "equity_curve.csv")
    result.trades.to_csv(out_dir / "trades.csv", index=False)
    payload = {"meta": result.meta, "metrics": metrics}
    (out_dir / "summary.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    print(json.dumps({"out_dir": str(out_dir), **payload}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
