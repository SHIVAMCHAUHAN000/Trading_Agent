"""Stage 7 validation suite orchestration."""

from __future__ import annotations

from typing import Any

import pandas as pd

from backtesting.engine.data import load_bars
from strategies.schema import StrategySpec
from validation.out_of_sample.oos import run_oos_validation
from validation.robustness.parameter_sensitivity import run_parameter_sensitivity
from validation.stress.cost_stress import run_cost_stress
from validation.walk_forward.walk_forward import run_walk_forward


def run_validation_suite(
    spec: StrategySpec,
    bars: pd.DataFrame | None = None,
    *,
    is_fraction: float = 0.70,
    include_parameter_sensitivity: bool = True,
    include_walk_forward: bool = True,
    include_cost_stress: bool = True,
    lookbacks: list[int] | None = None,
    top_ns: list[int] | None = None,
) -> dict[str, Any]:
    bars = load_bars() if bars is None else bars.copy()
    bars["Date"] = pd.to_datetime(bars["Date"]).dt.normalize()

    oos = run_oos_validation(spec, bars, is_fraction=is_fraction)
    wf = run_walk_forward(spec, bars) if include_walk_forward else {"skipped": True}
    sens = (
        run_parameter_sensitivity(
            spec,
            bars,
            is_fraction=is_fraction,
            lookbacks=lookbacks,
            top_ns=top_ns,
        )
        if include_parameter_sensitivity
        else {"skipped": True}
    )
    costs = run_cost_stress(spec, bars) if include_cost_stress else {"skipped": True}

    # Conservative combined gate — not a trading approval.
    flags = []
    if oos.get("verdict") == "REJECT_OOS":
        flags.append("oos_reject")
    if isinstance(wf, dict) and wf.get("verdict") == "REJECT_WALK_FORWARD":
        flags.append("walk_forward_reject")
    if isinstance(costs, dict) and costs.get("verdict") == "BREAKS_UNDER_COST_STRESS":
        flags.append("cost_stress_fail")
    if isinstance(sens, dict) and sens.get("robustness") == "PEAKY_SURFACE":
        flags.append("peaky_parameters")

    if "oos_reject" in flags or "walk_forward_reject" in flags:
        overall = "REJECT"
    elif not flags and oos.get("verdict") == "PROMISING_OOS":
        overall = "PROMISING"
    else:
        overall = "INCONCLUSIVE"

    return {
        "strategy_name": spec.name,
        "is_fraction": is_fraction,
        "out_of_sample": oos,
        "walk_forward": wf,
        "parameter_sensitivity": sens,
        "cost_stress": costs,
        "risk_flags": flags,
        "overall_verdict": overall,
        "notes": [
            "Validation suite does not optimize parameters on OOS.",
            "PROMISING is not APPROVED — bias checks / Monte Carlo still pending.",
            "Soft win-rate targets are reported, never used as the sole gate.",
        ],
    }
