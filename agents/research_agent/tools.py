"""Tool layer used by the research agent. Numerical work stays in Python modules."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pandas as pd
import yaml

from analytics.report import build_analytics_report
from backtesting.engine.data import load_bars, resolve_bars_path
from backtesting.engine.engine import BacktestResult, run_backtest
from market_data.validate import build_quality_report
from strategies.loader import load_strategy_spec
from strategies.schema import StrategySpec
from validation.suite import run_validation_suite

ROOT = Path(__file__).resolve().parents[2]


def get_strategy(path: str | Path) -> StrategySpec:
    return load_strategy_spec(path)


def get_data(bars_path: str | Path | None = None) -> pd.DataFrame:
    if bars_path is None:
        return load_bars()
    bars = pd.read_parquet(bars_path)
    bars["Date"] = pd.to_datetime(bars["Date"]).dt.normalize()
    return bars


def get_data_version() -> dict[str, Any]:
    pointer = ROOT / "config" / "latest_dataset.yaml"
    if not pointer.exists():
        return {"dataset_id": None, "status": "MISSING_DATASET_POINTER"}
    return yaml.safe_load(pointer.read_text(encoding="utf-8"))


def validate_data(bars: pd.DataFrame) -> dict[str, Any]:
    frames = {sym: g.copy() for sym, g in bars.groupby("Symbol")}
    # Exclude benchmark from equity OHLC critical path noise if desired; still validate.
    report = build_quality_report(
        frames,
        download_summary={
            "provider": "local_processed",
            "requested": len(frames),
            "downloaded": len(frames),
            "failed": 0,
            "failures": [],
        },
        universe_id="NIFTY50",
        history_start="2015-01-01",
    )
    return report


def run_backtest_tool(spec: StrategySpec, bars: pd.DataFrame, *, cost_multiplier: float = 1.0) -> BacktestResult:
    return run_backtest(spec, bars, cost_multiplier=cost_multiplier)


def calculate_metrics(result: BacktestResult, *, capital: float) -> dict[str, Any]:
    report = build_analytics_report(result, capital=capital, bars=result.bars)
    # Keep enriched trades outside JSON by default
    enriched = report.pop("enriched_trades", pd.DataFrame())
    report["_enriched_trades"] = enriched
    return report


def run_validation_tool(spec: StrategySpec, bars: pd.DataFrame, **kwargs: Any) -> dict[str, Any]:
    return run_validation_suite(spec, bars, **kwargs)


def run_regime_analysis(result: BacktestResult, *, capital: float) -> dict[str, Any]:
    """Simple calendar subperiod performance (not ML regime detection)."""
    eq = result.equity_curve["Equity"].astype(float)
    if eq.empty:
        return {"status": "NO_EQUITY"}

    start, end = eq.index.min(), eq.index.max()
    edges = pd.date_range(start=start, end=end, periods=5)
    periods = []
    for i in range(len(edges) - 1):
        a, b = edges[i], edges[i + 1]
        # last window inclusive of end
        mask = (eq.index >= a) & (eq.index <= b if i == len(edges) - 2 else eq.index < b)
        seg = eq.loc[mask]
        if len(seg) < 5:
            continue
        ret = float(seg.iloc[-1] / seg.iloc[0] - 1.0)
        periods.append(
            {
                "start": str(pd.Timestamp(seg.index.min()).date()),
                "end": str(pd.Timestamp(seg.index.max()).date()),
                "segment_return": ret,
                "ending_equity": float(seg.iloc[-1]),
            }
        )
    signs = [1 if p["segment_return"] > 0 else 0 for p in periods]
    return {
        "status": "OK",
        "method": "equal_calendar_quartiles",
        "periods": periods,
        "positive_segments": int(sum(signs)),
        "n_segments": len(periods),
        "stable_sign": bool(len(periods) >= 3 and sum(signs) >= len(periods) - 1),
    }


def run_bootstrap(result: BacktestResult, *, n: int = 500, seed: int = 7) -> dict[str, Any]:
    """Bootstrap daily returns for Sharpe / CAGR uncertainty (simple IID bootstrap)."""
    import numpy as np

    eq = result.equity_curve["Equity"].astype(float)
    rets = eq.pct_change().dropna().to_numpy()
    if len(rets) < 50:
        return {"status": "INSUFFICIENT_DATA"}

    rng = np.random.default_rng(seed)
    sharpes = []
    terminals = []
    for _ in range(n):
        sample = rng.choice(rets, size=len(rets), replace=True)
        vol = sample.std(ddof=0) * np.sqrt(252)
        sharpe = (sample.mean() * 252 / vol) if vol > 0 else np.nan
        path = np.cumprod(1 + sample)
        terminals.append(float(path[-1]))
        sharpes.append(float(sharpe))

    sharpes_a = np.array(sharpes, dtype=float)
    terminals_a = np.array(terminals, dtype=float)
    return {
        "status": "OK",
        "n": n,
        "method": "iid_daily_return_bootstrap",
        "sharpe_mean": float(np.nanmean(sharpes_a)),
        "sharpe_ci_95": [float(np.nanpercentile(sharpes_a, 2.5)), float(np.nanpercentile(sharpes_a, 97.5))],
        "terminal_wealth_multiple_ci_95": [
            float(np.nanpercentile(terminals_a, 2.5)),
            float(np.nanpercentile(terminals_a, 97.5)),
        ],
        "warnings": ["IID bootstrap ignores autocorrelation and regime dependence."],
    }


def run_monte_carlo(result: BacktestResult, *, n: int = 500, seed: int = 21) -> dict[str, Any]:
    """Monte Carlo by reshuffling trade net PnLs to stress equity paths."""
    import numpy as np

    trades = result.trades
    if trades is None or trades.empty or "net_pnl" not in trades.columns:
        return {"status": "NO_TRADES"}

    pnls = trades["net_pnl"].astype(float).to_numpy()
    capital = float(result.meta.get("capital", 1_000_000))
    rng = np.random.default_rng(seed)
    max_dds = []
    finals = []
    for _ in range(n):
        order = rng.permutation(pnls)
        equity = capital + np.cumsum(order)
        equity = np.concatenate([[capital], equity])
        dd = equity / np.maximum.accumulate(equity) - 1.0
        max_dds.append(float(dd.min()))
        finals.append(float(equity[-1]))

    max_dds_a = np.array(max_dds)
    finals_a = np.array(finals)
    hist_dd = None
    if not result.equity_curve.empty:
        eq = result.equity_curve["Equity"].astype(float)
        hist_dd = float((eq / eq.cummax() - 1.0).min())

    return {
        "status": "OK",
        "n": n,
        "method": "trade_pnl_permutation",
        "historical_max_dd": hist_dd,
        "median_dd": float(np.median(max_dds_a)),
        "dd_95th_percentile": float(np.percentile(max_dds_a, 5)),  # more negative tail ~5th pct
        "final_equity_median": float(np.median(finals_a)),
        "final_equity_5th_pct": float(np.percentile(finals_a, 5)),
        "warnings": ["Trade permutation ignores chronology and clustering of losses."],
    }


def run_bias_check(spec: StrategySpec, data_quality: dict[str, Any], validation: dict[str, Any]) -> dict[str, Any]:
    flags = []
    flags.append(
        {
            "code": "SURVIVORSHIP",
            "severity": "critical",
            "message": "Universe uses current NIFTY50 constituents, not point-in-time membership.",
        }
    )
    if data_quality.get("late_history_start"):
        flags.append(
            {
                "code": "LISTING_AGE",
                "severity": "warning",
                "message": "Some symbols start after the requested research start.",
                "count": len(data_quality.get("late_history_start", [])),
            }
        )
    if validation.get("parameter_sensitivity", {}).get("robustness") == "PEAKY_SURFACE":
        flags.append(
            {
                "code": "OVERFITTING_RISK",
                "severity": "warning",
                "message": "Parameter surface looks peaky on IS grid.",
            }
        )
    if "optimize_on_oos" in (spec.research_objective.forbid or []):
        flags.append(
            {
                "code": "OOS_PROTOCOL_OK",
                "severity": "info",
                "message": "Strategy forbids optimize_on_oos; validation suite keeps grid IS-only.",
            }
        )
    flags.append(
        {
            "code": "LOOKAHEAD_CONTROL",
            "severity": "info",
            "message": "Engine executes next open after close signal; same-bar lookahead fill is not used.",
        }
    )
    return {"status": "OK", "flags": flags}


def TOOL_REGISTRY() -> dict[str, Callable[..., Any]]:
    return {
        "get_strategy": get_strategy,
        "get_data": get_data,
        "validate_data": validate_data,
        "run_backtest": run_backtest_tool,
        "calculate_metrics": calculate_metrics,
        "run_validation": run_validation_tool,
        "run_regime_analysis": run_regime_analysis,
        "run_bootstrap": run_bootstrap,
        "run_monte_carlo": run_monte_carlo,
        "run_bias_check": run_bias_check,
        "get_data_version": get_data_version,
        "resolve_bars_path": resolve_bars_path,
    }
