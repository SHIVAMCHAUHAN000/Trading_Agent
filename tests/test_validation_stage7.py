"""Stage 7 validation tests."""

from __future__ import annotations

import numpy as np
import pandas as pd

from strategies.schema import StrategySpec
from validation.out_of_sample.oos import run_oos_validation
from validation.splits import calendar_split, walk_forward_windows
from validation.robustness.parameter_sensitivity import run_parameter_sensitivity
from validation.suite import run_validation_suite


def _bars(n_days: int = 1600, n_symbols: int = 6) -> pd.DataFrame:
    dates = pd.bdate_range("2015-01-01", periods=n_days)
    rows = []
    rng = np.random.default_rng(11)
    for i in range(n_symbols):
        sym = f"S{i}.NS"
        rets = rng.normal(0.0004 + i * 0.0002, 0.012, size=n_days)
        close = 100 * np.cumprod(1 + rets)
        open_ = np.concatenate([[close[0]], close[:-1]])
        for dt, o, c in zip(dates, open_, close):
            rows.append(
                {
                    "Date": dt,
                    "Symbol": sym,
                    "Open": float(o),
                    "High": float(max(o, c) * 1.01),
                    "Low": float(min(o, c) * 0.99),
                    "Close": float(c),
                    "AdjClose": float(c),
                    "Volume": 10000,
                }
            )
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


def _spec() -> StrategySpec:
    return StrategySpec.model_validate(
        {
            "name": "synth_mom_val",
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
            "period": {"start": "2015-01-01", "end": "2020-12-31"},
            "research_objective": {
                "target_win_rate": 0.70,
                "prioritize": ["expectancy", "risk_adjusted_return", "robustness"],
                "forbid": ["optimize_on_oos"],
            },
        }
    )


def test_calendar_split_70_30():
    split = calendar_split("2015-01-01", "2024-12-31", is_fraction=0.70)
    assert split.oos_start > split.is_end
    assert split.is_start == pd.Timestamp("2015-01-01")


def test_walk_forward_windows_non_empty():
    windows = walk_forward_windows("2015-01-01", "2024-12-31", train_years=3, test_years=1, step_years=1)
    assert len(windows) >= 3
    assert windows[0]["train_start"] == "2015-01-01"


def test_oos_does_not_change_parameters():
    bars = _bars()
    spec = _spec()
    out = run_oos_validation(spec, bars, is_fraction=0.70)
    assert out["parameters_frozen"] == spec.entry.parameters
    assert out["mode"] == "frozen_parameter_oos"
    assert "out_of_sample" in out


def test_parameter_sensitivity_is_only():
    bars = _bars()
    spec = _spec()
    out = run_parameter_sensitivity(
        spec,
        bars,
        is_fraction=0.70,
        lookbacks=[40, 60],
        top_ns=[2, 3],
    )
    assert out["oos_used"] is False
    assert len(out["grid"]) == 4


def test_validation_suite_smoke():
    bars = _bars()
    spec = _spec()
    report = run_validation_suite(
        spec,
        bars,
        is_fraction=0.70,
        include_parameter_sensitivity=True,
        include_walk_forward=True,
        include_cost_stress=True,
        lookbacks=[60],
        top_ns=[2],
    )
    assert report["overall_verdict"] in {"REJECT", "PROMISING", "INCONCLUSIVE"}
    assert "out_of_sample" in report
