"""Cost multiplier stress tests on frozen parameters."""

from __future__ import annotations

from typing import Any

import pandas as pd

from strategies.schema import StrategySpec
from validation.helpers import metric_snapshot, run_segment_metrics


def run_cost_stress(
    spec: StrategySpec,
    bars: pd.DataFrame,
    *,
    multipliers: list[float] | None = None,
) -> dict[str, Any]:
    multipliers = multipliers or [1.0, 1.5, 2.0, 3.0]
    start = str(pd.Timestamp(spec.period.start).date())
    end = str((pd.Timestamp(spec.period.end) if spec.period.end else pd.to_datetime(bars["Date"]).max()).date())

    runs: list[dict[str, Any]] = []
    for m in multipliers:
        out = run_segment_metrics(spec, bars, start=start, end=end, cost_multiplier=m)
        runs.append(
            {
                "cost_multiplier": m,
                "metrics": metric_snapshot(out["metrics"]),
            }
        )

    base = runs[0]["metrics"] if runs else {}
    stressed = runs[-1]["metrics"] if runs else {}
    survives = (
        stressed.get("sharpe") is not None
        and pd.notna(stressed.get("sharpe"))
        and float(stressed["sharpe"]) > 0
        and stressed.get("cagr") is not None
        and pd.notna(stressed.get("cagr"))
        and float(stressed["cagr"]) > 0
    )

    return {
        "mode": "cost_multiplier_stress",
        "multipliers": multipliers,
        "runs": runs,
        "baseline_sharpe": base.get("sharpe"),
        "stressed_sharpe": stressed.get("sharpe"),
        "survives_3x_costs": bool(survives) if multipliers[-1] >= 3.0 else None,
        "verdict": "SURVIVES_COST_STRESS" if survives else "BREAKS_UNDER_COST_STRESS",
    }
