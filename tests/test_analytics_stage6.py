"""Stage 6 analytics tests."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from analytics.performance.benchmark import compute_benchmark_comparison
from analytics.performance.returns import monthly_returns, return_summary
from analytics.performance.trade_path import enrich_trades_with_excursions
from analytics.report import build_analytics_report
from analytics.risk.drawdown import drawdown_stats
from backtesting.engine.engine import BacktestResult


def test_monthly_and_drawdown_helpers():
    idx = pd.bdate_range("2020-01-01", periods=300)
    eq = pd.Series(np.linspace(100, 150, len(idx)), index=idx)
    # inject a drawdown
    eq.iloc[100:150] = eq.iloc[100:150] * 0.8
    stats = drawdown_stats(eq)
    assert stats["max_drawdown"] < 0
    assert stats["recovery_time_days"] is not None
    monthly = monthly_returns(eq)
    assert len(monthly) >= 1
    summary = return_summary(eq)
    assert "best_month" in summary
    assert "annual_returns" in summary


def test_benchmark_comparison_fields():
    idx = pd.bdate_range("2020-01-01", periods=260)
    strat = pd.Series(np.linspace(100, 160, len(idx)), index=idx)
    bench = pd.Series(np.linspace(100, 130, len(idx)), index=idx)
    out = compute_benchmark_comparison(strat, bench)
    assert out["status"] == "OK"
    assert "beta" in out
    assert "alpha_annualized" in out
    assert "information_ratio" in out
    assert "tracking_error" in out
    assert out["excess_total_return"] > 0


def test_mae_mfe_enrichment():
    bars = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "Symbol": ["A.NS"] * 3,
            "Open": [10, 10, 10],
            "High": [11, 12, 11],
            "Low": [9, 8, 9.5],
            "Close": [10, 10.5, 10.2],
            "AdjClose": [10, 10.5, 10.2],
            "Volume": [100, 100, 100],
        }
    )
    trades = pd.DataFrame(
        [
            {
                "trade_id": "A-1",
                "symbol": "A.NS",
                "entry_date": "2024-01-01",
                "exit_date": "2024-01-03",
                "entry_price": 10.0,
                "exit_price": 10.2,
                "qty": 1,
                "gross_pnl": 0.2,
                "costs": 0.0,
                "net_pnl": 0.2,
                "holding_days": 2,
            }
        ]
    )
    enriched = enrich_trades_with_excursions(trades, bars)
    assert enriched.loc[0, "mae"] == pytest.approx(-0.2)  # low 8 / 10 - 1
    assert enriched.loc[0, "mfe"] == pytest.approx(0.2)  # high 12 / 10 - 1


def test_build_analytics_report_bundle():
    idx = pd.bdate_range("2020-01-01", periods=260)
    equity = pd.DataFrame(
        {
            "Cash": 0.0,
            "MarketValue": np.linspace(1000000, 1200000, len(idx)),
            "Equity": np.linspace(1000000, 1200000, len(idx)),
            "GrossExposure": np.linspace(1000000, 1200000, len(idx)),
            "NetExposure": np.linspace(1000000, 1200000, len(idx)),
            "Positions": 1,
        },
        index=idx,
    )
    result = BacktestResult(
        equity_curve=equity,
        trades=pd.DataFrame(),
        positions_end={},
        meta={},
        benchmark_equity=pd.Series(np.linspace(1000000, 1100000, len(idx)), index=idx),
        bars=None,
    )
    report = build_analytics_report(result, capital=1_000_000, bars=None)
    assert "performance" in report
    assert "trades" in report
    assert "benchmark" in report
    assert report["benchmark"]["status"] == "OK"
