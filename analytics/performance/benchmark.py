"""Benchmark-relative performance analytics."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _safe_div(a: float, b: float) -> float:
    if b == 0 or np.isnan(b):
        return float("nan")
    return float(a / b)


def align_returns(strategy_equity: pd.Series, benchmark_equity: pd.Series) -> tuple[pd.Series, pd.Series]:
    s = strategy_equity.astype(float).pct_change()
    b = benchmark_equity.astype(float).pct_change()
    both = pd.concat([s, b], axis=1, join="inner").dropna()
    both.columns = ["strategy", "benchmark"]
    return both["strategy"], both["benchmark"]


def compute_benchmark_comparison(
    strategy_equity: pd.Series,
    benchmark_equity: pd.Series,
    *,
    trading_days_per_year: int = 252,
    risk_free: float = 0.0,
) -> dict[str, Any]:
    if benchmark_equity is None or benchmark_equity.empty:
        return {"status": "BENCHMARK_MISSING"}

    s_eq = strategy_equity.astype(float)
    b_eq = benchmark_equity.astype(float).reindex(s_eq.index).ffill().bfill()
    if b_eq.isna().all():
        return {"status": "BENCHMARK_MISSING"}

    # Buy & hold normalized to same start
    b_norm = b_eq / float(b_eq.iloc[0]) * float(s_eq.iloc[0])
    s_rets, b_rets = align_returns(s_eq, b_norm)
    if s_rets.empty:
        return {"status": "BENCHMARK_INSUFFICIENT_OVERLAP"}

    years = max(len(s_eq) - 1, 1) / trading_days_per_year
    s_total = float(s_eq.iloc[-1] / s_eq.iloc[0] - 1.0)
    b_total = float(b_norm.iloc[-1] / b_norm.iloc[0] - 1.0)
    s_cagr = (1 + s_total) ** (1 / years) - 1 if years > 0 and (1 + s_total) > 0 else float("nan")
    b_cagr = (1 + b_total) ** (1 / years) - 1 if years > 0 and (1 + b_total) > 0 else float("nan")

    excess = s_rets - b_rets
    cov = float(np.cov(s_rets, b_rets, ddof=0)[0, 1]) if len(s_rets) > 1 else float("nan")
    var_b = float(np.var(b_rets, ddof=0)) if len(b_rets) else float("nan")
    beta = _safe_div(cov, var_b)
    corr = float(np.corrcoef(s_rets, b_rets)[0, 1]) if len(s_rets) > 1 else float("nan")

    rf_daily = risk_free / trading_days_per_year
    alpha_daily = float((s_rets - rf_daily - beta * (b_rets - rf_daily)).mean()) if np.isfinite(beta) else float("nan")
    alpha_ann = alpha_daily * trading_days_per_year

    te = float(excess.std(ddof=0) * np.sqrt(trading_days_per_year)) if len(excess) else float("nan")
    ir = _safe_div(float(excess.mean() * trading_days_per_year), te)

    return {
        "status": "OK",
        "benchmark": "^NSEI",
        "strategy_total_return": s_total,
        "benchmark_total_return": b_total,
        "excess_total_return": s_total - b_total,
        "strategy_cagr": float(s_cagr),
        "benchmark_cagr": float(b_cagr),
        "excess_cagr": float(s_cagr - b_cagr) if np.isfinite(s_cagr) and np.isfinite(b_cagr) else float("nan"),
        "beta": float(beta),
        "alpha_annualized": float(alpha_ann),
        "correlation": float(corr),
        "tracking_error": float(te),
        "information_ratio": float(ir),
    }
