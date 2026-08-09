"""Shared helpers for validation runs."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pandas as pd

from analytics.performance.metrics import compute_performance_metrics
from backtesting.engine.engine import run_backtest
from strategies.schema import StrategySpec


def clone_spec(spec: StrategySpec, *, start: str, end: str, **entry_overrides: Any) -> StrategySpec:
    data = spec.model_dump(mode="json")
    data["period"] = {"start": start, "end": end}
    if entry_overrides:
        params = dict(data["entry"].get("parameters") or {})
        params.update(entry_overrides)
        data["entry"]["parameters"] = params
        # Keep signal block loosely in sync for momentum
        for key in ("lookback_days", "skip_days", "top_n"):
            if key in entry_overrides:
                data.setdefault("signal", {})[key] = entry_overrides[key]
        if "top_n" in entry_overrides:
            data["position"]["max_positions"] = int(entry_overrides["top_n"])
    return StrategySpec.model_validate(data)


def run_segment_metrics(
    spec: StrategySpec,
    bars: pd.DataFrame,
    *,
    start: str,
    end: str,
    cost_multiplier: float = 1.0,
    entry_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seg_spec = clone_spec(spec, start=start, end=end, **(entry_overrides or {}))
    result = run_backtest(seg_spec, bars, cost_multiplier=cost_multiplier)
    metrics = compute_performance_metrics(result.equity_curve, result.trades, capital=float(spec.capital))
    return {
        "start": start,
        "end": end,
        "cost_multiplier": cost_multiplier,
        "parameters": deepcopy(seg_spec.entry.parameters),
        "metrics": metrics,
        "n_trades": int(metrics.get("n_trades", 0)),
    }


def metric_snapshot(metrics: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "total_return",
        "cagr",
        "sharpe",
        "sortino",
        "max_drawdown",
        "calmar",
        "win_rate",
        "profit_factor",
        "expectancy",
        "n_trades",
    ]
    return {k: metrics.get(k) for k in keys}
