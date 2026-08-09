"""Stage 5 backtest engine tests."""

from __future__ import annotations

import numpy as np
import pandas as pd

from analytics.performance.metrics import compute_performance_metrics
from backtesting.costs.model import load_cost_config, trade_cost
from backtesting.engine.engine import run_backtest
from backtesting.engine.signals import cross_sectional_momentum_targets
from strategies.schema import StrategySpec


def _synthetic_bars(n_days: int = 400, n_symbols: int = 5) -> pd.DataFrame:
    dates = pd.bdate_range("2018-01-01", periods=n_days)
    rows = []
    rng = np.random.default_rng(7)
    for i, sym in enumerate([f"S{i}.NS" for i in range(n_symbols)]):
        # Give later symbols stronger drift so momentum ranking is deterministic-ish
        rets = rng.normal(0.0005 + i * 0.0003, 0.01, size=n_days)
        close = 100 * np.cumprod(1 + rets)
        open_ = np.concatenate([[close[0]], close[:-1]])
        for dt, o, c in zip(dates, open_, close):
            high = max(o, c) * 1.01
            low = min(o, c) * 0.99
            rows.append(
                {
                    "Date": dt,
                    "Symbol": sym,
                    "Open": o,
                    "High": high,
                    "Low": low,
                    "Close": c,
                    "AdjClose": c,
                    "Volume": 10000,
                }
            )
    # Tiny benchmark series
    for dt in dates:
        rows.append(
            {
                "Date": dt,
                "Symbol": "^NSEI",
                "Open": 1000.0,
                "High": 1001.0,
                "Low": 999.0,
                "Close": 1000.0,
                "AdjClose": 1000.0,
                "Volume": 0,
            }
        )
    return pd.DataFrame(rows)


def test_trade_cost_buy_sell_components():
    cfg = load_cost_config()
    buy = trade_cost(100_000, "buy", cfg)
    sell = trade_cost(100_000, "sell", cfg)
    assert buy["total"] > 0
    assert sell["total"] > 0
    assert buy["stamp_duty"] > 0
    assert sell["stt"] > 0
    assert buy["stt"] == 0


def test_momentum_targets_sum_to_one_or_zero():
    bars = _synthetic_bars()
    close = bars[bars["Symbol"] != "^NSEI"].pivot(index="Date", columns="Symbol", values="Close")
    targets = cross_sectional_momentum_targets(
        close, lookback_days=60, skip_days=5, top_n=2, min_momentum=-1.0
    )
    assert not targets.empty
    sums = targets.sum(axis=1)
    assert ((((sums - 1.0).abs() < 1e-9) | sums.eq(0)).all())


def test_run_backtest_produces_equity_and_metrics():
    bars = _synthetic_bars()
    spec = StrategySpec.model_validate(
        {
            "name": "synth_mom",
            "market": "Indian_equities",
            "universe": {"type": "custom_symbols", "symbols": ["S0.NS", "S1.NS"]},
            "timeframe": "daily",
            "signal": {"type": "cross_sectional_momentum", "lookback_days": 60, "skip_days": 5},
            "entry": {
                "condition": "rank_by_momentum_desc",
                "parameters": {"lookback_days": 60, "skip_days": 5, "top_n": 2, "min_momentum": -1.0},
            },
            "exit": {
                "condition": "leave_top_n_or_momentum_non_positive",
                "parameters": {"top_n": 2, "rebalance": "monthly"},
            },
            "position": {"method": "equal_weight", "max_positions": 2},
            "execution": {"signal_time": "close", "execution_time": "next_open", "long_only": True},
            "cost_model": {"model_id": "indian_cash_equity_conservative_v1"},
            "capital": 1_000_000,
            "period": {"start": "2018-01-01", "end": "2019-12-31"},
        }
    )
    result = run_backtest(spec, bars)
    assert not result.equity_curve.empty
    assert "Equity" in result.equity_curve.columns
    metrics = compute_performance_metrics(result.equity_curve, result.trades, capital=1_000_000)
    assert "cagr" in metrics
    assert "sharpe" in metrics
    assert "max_drawdown" in metrics
    assert "win_rate" in metrics
    assert "profit_factor" in metrics
    assert "expectancy" in metrics
