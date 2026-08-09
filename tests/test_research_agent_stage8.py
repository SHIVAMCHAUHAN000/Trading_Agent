"""Stage 8 research agent tests."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from agents.research_agent.report_builder import map_conclusion, render_simple_markdown
from agents.research_agent.tools import run_bias_check, run_bootstrap, run_monte_carlo, run_regime_analysis
from backtesting.engine.engine import BacktestResult
from strategies.schema import StrategySpec


def _result(n: int = 300) -> BacktestResult:
    idx = pd.bdate_range("2018-01-01", periods=n)
    eq = pd.Series(np.linspace(1_000_000, 1_300_000, n), index=idx)
    equity = pd.DataFrame(
        {
            "Cash": 0.0,
            "MarketValue": eq,
            "Equity": eq,
            "GrossExposure": eq,
            "NetExposure": eq,
            "Positions": 1,
        },
        index=idx,
    )
    trades = pd.DataFrame(
        {
            "trade_id": [f"t{i}" for i in range(20)],
            "symbol": ["A.NS"] * 20,
            "entry_date": idx[:20],
            "exit_date": idx[10:30],
            "entry_price": [10.0] * 20,
            "exit_price": [10.5] * 20,
            "qty": [10] * 20,
            "gross_pnl": [50.0] * 20,
            "costs": [1.0] * 20,
            "net_pnl": np.linspace(-20, 40, 20),
            "holding_days": [10] * 20,
        }
    )
    return BacktestResult(
        equity_curve=equity,
        trades=trades,
        positions_end={},
        meta={"capital": 1_000_000},
        benchmark_equity=eq * 0.9,
        bars=None,
    )


def test_map_conclusion_caps_validated_when_survivorship():
    validation = {"overall_verdict": "PROMISING"}
    bias = {"flags": [{"code": "SURVIVORSHIP", "severity": "critical", "message": "x"}]}
    status, _ = map_conclusion(validation, bias)
    assert status == "PROMISING"


def test_regime_bootstrap_monte_carlo_tools():
    result = _result()
    regime = run_regime_analysis(result, capital=1_000_000)
    assert regime["status"] == "OK"
    boot = run_bootstrap(result, n=50)
    assert boot["status"] == "OK"
    assert "sharpe_ci_95" in boot
    mc = run_monte_carlo(result, n=50)
    assert mc["status"] == "OK"
    assert "median_dd" in mc


def test_bias_check_and_simple_markdown():
    spec = StrategySpec.model_validate(
        {
            "name": "x",
            "market": "Indian_equities",
            "universe": {"type": "NIFTY50"},
            "timeframe": "daily",
            "signal": {"type": "cross_sectional_momentum"},
            "entry": {"condition": "rank_by_momentum_desc", "parameters": {"lookback_days": 60, "top_n": 2}},
            "exit": {"condition": "leave_top_n_or_momentum_non_positive", "parameters": {"rebalance": "monthly"}},
            "position": {"method": "equal_weight", "max_positions": 2},
            "execution": {"signal_time": "close", "execution_time": "next_open", "long_only": True},
            "cost_model": {"model_id": "indian_cash_equity_conservative_v1"},
            "capital": 1_000_000,
            "period": {"start": "2015-01-01", "end": "2020-01-01"},
            "research_objective": {"forbid": ["optimize_on_oos"]},
        }
    )
    bias = run_bias_check(spec, {"late_history_start": [{"symbol": "A"}]}, {"parameter_sensitivity": {}})
    assert any(f["code"] == "SURVIVORSHIP" for f in bias["flags"])
    md = render_simple_markdown(
        {
            "what_is_the_strategy": "s",
            "why_might_it_work": "w",
            "how_did_it_perform": "p",
            "how_risky_is_it": "r",
            "what_breaks_it": "b",
            "is_result_robust": "ok",
            "major_warnings": ["warn"],
            "research_conclusion_summary": "PROMISING. because",
        },
        experiment_id="EXP-000001",
    )
    assert "EXP-000001" in md
    assert "Major warnings" in md


def test_experiment_id_format(tmp_path: Path, monkeypatch):
    from agents.research_agent import experiment as exp

    monkeypatch.setattr(exp, "REGISTRY", tmp_path / "registry.jsonl")
    assert exp.next_experiment_id() == "EXP-000001"
    exp.append_experiment({"experiment_id": "EXP-000001", "status": "COMPLETE"})
    assert exp.next_experiment_id() == "EXP-000002"
