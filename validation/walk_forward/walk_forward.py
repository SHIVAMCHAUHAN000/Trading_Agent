"""Walk-forward evaluation with frozen strategy parameters."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from strategies.schema import StrategySpec
from validation.helpers import metric_snapshot, run_segment_metrics
from validation.splits import walk_forward_windows


def run_walk_forward(
    spec: StrategySpec,
    bars: pd.DataFrame,
    *,
    train_years: float = 3.0,
    test_years: float = 1.0,
    step_years: float = 1.0,
) -> dict[str, Any]:
    data_start = pd.Timestamp(spec.period.start)
    data_end = pd.Timestamp(spec.period.end) if spec.period.end else pd.to_datetime(bars["Date"]).max()
    windows = walk_forward_windows(
        data_start,
        data_end,
        train_years=train_years,
        test_years=test_years,
        step_years=step_years,
    )

    folds: list[dict[str, Any]] = []
    for i, w in enumerate(windows, start=1):
        train = run_segment_metrics(spec, bars, start=w["train_start"], end=w["train_end"])
        test = run_segment_metrics(spec, bars, start=w["test_start"], end=w["test_end"])
        folds.append(
            {
                "fold": i,
                "window": w,
                "train": metric_snapshot(train["metrics"]),
                "test": metric_snapshot(test["metrics"]),
            }
        )

    test_sharpes = [f["test"].get("sharpe") for f in folds if f["test"].get("sharpe") is not None]
    test_sharpes_f = [float(x) for x in test_sharpes if pd.notna(x)]
    test_cagrs = [float(f["test"]["cagr"]) for f in folds if f["test"].get("cagr") is not None and pd.notna(f["test"]["cagr"])]
    positive_folds = sum(1 for s in test_sharpes_f if s > 0)

    summary = {
        "n_folds": len(folds),
        "positive_sharpe_folds": positive_folds,
        "mean_test_sharpe": float(np.mean(test_sharpes_f)) if test_sharpes_f else float("nan"),
        "median_test_sharpe": float(np.median(test_sharpes_f)) if test_sharpes_f else float("nan"),
        "min_test_sharpe": float(np.min(test_sharpes_f)) if test_sharpes_f else float("nan"),
        "mean_test_cagr": float(np.mean(test_cagrs)) if test_cagrs else float("nan"),
        "pct_positive_sharpe_folds": (positive_folds / len(folds)) if folds else float("nan"),
    }

    if not folds:
        verdict = "INCONCLUSIVE_NO_FOLDS"
    elif summary["pct_positive_sharpe_folds"] >= 0.6 and summary["mean_test_sharpe"] > 0.3:
        verdict = "PROMISING_WALK_FORWARD"
    elif summary["mean_test_sharpe"] <= 0:
        verdict = "REJECT_WALK_FORWARD"
    else:
        verdict = "MIXED_WALK_FORWARD"

    return {
        "mode": "frozen_parameter_walk_forward",
        "train_years": train_years,
        "test_years": test_years,
        "step_years": step_years,
        "parameters_frozen": spec.entry.parameters,
        "folds": folds,
        "summary": summary,
        "verdict": verdict,
        "warnings": [
            "Parameters are frozen across folds (no per-fold re-optimization in V1).",
            "This is a stability check, not a license to trade.",
        ],
    }
