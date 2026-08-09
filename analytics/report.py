"""Assemble Stage 6 analytics bundle from a backtest result."""

from __future__ import annotations

from typing import Any

import pandas as pd

from analytics.performance.benchmark import compute_benchmark_comparison
from analytics.performance.metrics import compute_performance_metrics, compute_trade_stats
from analytics.performance.returns import return_summary
from analytics.performance.trade_path import enrich_trades_with_excursions, trade_excursion_summary
from analytics.risk.drawdown import drawdown_series, drawdown_stats
from backtesting.engine.engine import BacktestResult


def build_analytics_report(
    result: BacktestResult,
    *,
    capital: float,
    bars: pd.DataFrame | None = None,
) -> dict[str, Any]:
    equity = result.equity_curve["Equity"].astype(float)
    core = compute_performance_metrics(result.equity_curve, result.trades, capital=capital)
    dd = drawdown_stats(equity)
    rets = return_summary(equity)

    trades = result.trades
    if bars is not None and not trades.empty:
        trades = enrich_trades_with_excursions(trades, bars)

    trade_stats = compute_trade_stats(trades)
    excursions = trade_excursion_summary(trades)

    benchmark = compute_benchmark_comparison(
        equity,
        result.benchmark_equity if result.benchmark_equity is not None else pd.Series(dtype=float),
    )

    # Profit concentration: share of net profits from best N trades
    concentration: dict[str, Any] = {"status": "NO_TRADES"}
    if trades is not None and not trades.empty:
        net = trades["net_pnl"].astype(float).sort_values(ascending=False)
        total_pos = float(net[net > 0].sum())
        best5 = float(net.head(5).sum())
        concentration = {
            "status": "OK",
            "best_5_trades_net_pnl": best5,
            "best_5_share_of_positive_pnl": (best5 / total_pos) if total_pos > 0 else float("nan"),
            "top_20pct_trade_share_of_positive_pnl": (
                float(net.head(max(1, int(len(net) * 0.2))).sum() / total_pos) if total_pos > 0 else float("nan")
            ),
        }

    dd_curve = drawdown_series(equity)

    return {
        "performance": {
            **{k: core[k] for k in core if k not in trade_stats},
            **rets,
            **{k: dd[k] for k in dd if k != "max_drawdown"},  # max_drawdown already in core
            "max_drawdown": dd["max_drawdown"],
        },
        "trades": {**trade_stats, **excursions, "profit_concentration": concentration},
        "benchmark": benchmark,
        "drawdown_curve_tail": {
            "last_date": str(dd_curve.index.max().date()) if len(dd_curve) else None,
            "current_drawdown": float(dd_curve.iloc[-1]) if len(dd_curve) else float("nan"),
        },
        "enriched_trades": trades,
    }
