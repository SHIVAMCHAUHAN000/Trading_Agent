"""
Frozen in-sample / out-of-sample evaluation.

Rules:
- Parameters are taken from the StrategySpec as-is (already frozen).
- OOS metrics are computed only on the OOS window.
- This module never searches parameters using OOS data.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from validation.helpers import metric_snapshot, run_segment_metrics
from validation.splits import calendar_split
from strategies.schema import StrategySpec


def run_oos_validation(
    spec: StrategySpec,
    bars: pd.DataFrame,
    *,
    is_fraction: float = 0.70,
) -> dict[str, Any]:
    if "optimize_on_oos" not in (spec.research_objective.forbid or []):
        # Soft enforcement: always treat OOS as frozen evaluation in this module.
        pass

    data_start = pd.Timestamp(spec.period.start)
    data_end = pd.Timestamp(spec.period.end) if spec.period.end else pd.to_datetime(bars["Date"]).max()
    split = calendar_split(data_start, data_end, is_fraction=is_fraction)

    is_run = run_segment_metrics(
        spec,
        bars,
        start=str(split.is_start.date()),
        end=str(split.is_end.date()),
    )
    oos_run = run_segment_metrics(
        spec,
        bars,
        start=str(split.oos_start.date()),
        end=str(split.oos_end.date()),
    )

    is_sharpe = is_run["metrics"].get("sharpe")
    oos_sharpe = oos_run["metrics"].get("sharpe")
    degradation = None
    if is_sharpe is not None and oos_sharpe is not None and pd.notna(is_sharpe) and abs(float(is_sharpe)) > 1e-9:
        degradation = float(oos_sharpe) / float(is_sharpe)

    soft_targets = {
        "target_win_rate": spec.research_objective.target_win_rate,
        "oos_win_rate": oos_run["metrics"].get("win_rate"),
        "meets_target_win_rate": (
            None
            if spec.research_objective.target_win_rate is None or oos_run["metrics"].get("win_rate") is None
            else bool(float(oos_run["metrics"]["win_rate"]) >= float(spec.research_objective.target_win_rate))
        ),
    }

    verdict = "INCONCLUSIVE"
    if oos_run["metrics"].get("n_trades", 0) < 10:
        verdict = "INCONCLUSIVE_LOW_TRADES"
    elif oos_run["metrics"].get("sharpe") is not None and float(oos_run["metrics"]["sharpe"]) > 0.5:
        if degradation is not None and degradation > 0.5:
            verdict = "PROMISING_OOS"
        else:
            verdict = "WEAK_OOS_DEGRADATION"
    elif oos_run["metrics"].get("sharpe") is not None and float(oos_run["metrics"]["sharpe"]) <= 0:
        verdict = "REJECT_OOS"

    return {
        "mode": "frozen_parameter_oos",
        "split": split.to_dict(),
        "parameters_frozen": spec.entry.parameters,
        "in_sample": {"metrics": metric_snapshot(is_run["metrics"]), "n_trades": is_run["n_trades"]},
        "out_of_sample": {"metrics": metric_snapshot(oos_run["metrics"]), "n_trades": oos_run["n_trades"]},
        "sharpe_oos_over_is": degradation,
        "soft_targets": soft_targets,
        "verdict": verdict,
        "warnings": [
            "Parameters were not optimized on OOS in this module.",
            "Current-constituent universe implies survivorship bias in both IS and OOS.",
        ],
    }
