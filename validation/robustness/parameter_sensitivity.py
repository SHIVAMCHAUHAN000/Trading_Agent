"""
Parameter sensitivity on the IN-SAMPLE window only.

OOS is never used here — prevents accidental optimization leakage.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from strategies.schema import StrategySpec
from validation.helpers import run_segment_metrics
from validation.splits import calendar_split


def run_parameter_sensitivity(
    spec: StrategySpec,
    bars: pd.DataFrame,
    *,
    is_fraction: float = 0.70,
    lookbacks: list[int] | None = None,
    top_ns: list[int] | None = None,
) -> dict[str, Any]:
    lookbacks = lookbacks or [126, 189, 252, 315]
    top_ns = top_ns or [5, 8, 10, 12, 15]

    data_start = pd.Timestamp(spec.period.start)
    data_end = pd.Timestamp(spec.period.end) if spec.period.end else pd.to_datetime(bars["Date"]).max()
    split = calendar_split(data_start, data_end, is_fraction=is_fraction)

    grid: list[dict[str, Any]] = []
    for lb in lookbacks:
        for top_n in top_ns:
            run = run_segment_metrics(
                spec,
                bars,
                start=str(split.is_start.date()),
                end=str(split.is_end.date()),
                entry_overrides={
                    "lookback_days": lb,
                    "top_n": top_n,
                    "skip_days": int(spec.entry.parameters.get("skip_days", 21)),
                    "min_momentum": float(spec.entry.parameters.get("min_momentum", 0.0)),
                },
            )
            m = run["metrics"]
            grid.append(
                {
                    "lookback_days": lb,
                    "top_n": top_n,
                    "sharpe": m.get("sharpe"),
                    "cagr": m.get("cagr"),
                    "max_drawdown": m.get("max_drawdown"),
                    "win_rate": m.get("win_rate"),
                    "n_trades": m.get("n_trades"),
                }
            )

    sharpes = [float(g["sharpe"]) for g in grid if g["sharpe"] is not None and pd.notna(g["sharpe"])]
    if not sharpes:
        robustness = "UNKNOWN"
        plateau_score = float("nan")
    else:
        arr = np.array(sharpes, dtype=float)
        # Fraction of grid within 30% of best Sharpe (robust region proxy)
        best = float(np.nanmax(arr))
        if best <= 0:
            plateau_score = float((arr > 0).mean())
            robustness = "FRAGILE_OR_NEGATIVE"
        else:
            plateau_score = float((arr >= 0.7 * best).mean())
            robustness = "ROBUST_REGION" if plateau_score >= 0.4 else "PEAKY_SURFACE"

    baseline_lb = int(spec.entry.parameters.get("lookback_days", 252))
    baseline_top = int(spec.entry.parameters.get("top_n", spec.position.max_positions))
    baseline = next(
        (g for g in grid if g["lookback_days"] == baseline_lb and g["top_n"] == baseline_top),
        None,
    )

    return {
        "mode": "is_only_parameter_sensitivity",
        "split_used_for_grid": split.to_dict(),
        "oos_used": False,
        "grid": grid,
        "baseline": baseline,
        "plateau_score": plateau_score,
        "robustness": robustness,
        "warnings": [
            "Grid search uses IN-SAMPLE window only.",
            "Do not cherry-pick the best grid cell and retest it on OOS without a pre-registered holdout protocol.",
        ],
    }
