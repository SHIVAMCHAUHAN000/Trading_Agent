"""Build Layer-1 simple and Layer-2 technical research reports."""

from __future__ import annotations

from typing import Any

from strategies.schema import StrategySpec


def _pct(x: Any) -> str:
    try:
        if x is None:
            return "n/a"
        return f"{float(x) * 100:.1f}%"
    except Exception:
        return "n/a"


def _num(x: Any, digits: int = 2) -> str:
    try:
        if x is None:
            return "n/a"
        return f"{float(x):.{digits}f}"
    except Exception:
        return "n/a"


def map_conclusion(validation: dict[str, Any], bias: dict[str, Any]) -> tuple[str, str]:
    overall = validation.get("overall_verdict", "INCONCLUSIVE")
    critical_bias = [f for f in bias.get("flags", []) if f.get("severity") == "critical"]

    if overall == "REJECT":
        return "REJECT", "Validation gates failed on OOS and/or walk-forward."
    if critical_bias:
        # Survivorship is always critical today — cap at PROMISING, never VALIDATED_CANDIDATE
        if overall == "PROMISING":
            return (
                "PROMISING",
                "Validation looks constructive, but critical bias flags (especially survivorship) block validated-candidate status.",
            )
        return "INCONCLUSIVE", "Critical bias flags prevent a clean conclusion."
    if overall == "PROMISING":
        return "PROMISING", "OOS/walk-forward/cost checks look constructive under current assumptions."
    return "INCONCLUSIVE", "Evidence is mixed or incomplete."


def build_simple_report(
    spec: StrategySpec,
    *,
    analytics: dict[str, Any],
    validation: dict[str, Any],
    regime: dict[str, Any],
    monte_carlo: dict[str, Any],
    bias: dict[str, Any],
    conclusion: str,
    conclusion_rationale: str,
) -> dict[str, str | list[str]]:
    perf = analytics.get("performance", {})
    trades = analytics.get("trades", {})
    bench = analytics.get("benchmark", {})
    oos = validation.get("out_of_sample", {}).get("out_of_sample", {}).get("metrics", {})
    target_wr = spec.research_objective.target_win_rate

    what = (
        f"{spec.name} is a long-only daily strategy on {spec.universe.type.value} "
        f"using entry `{spec.entry.condition}` and exit `{spec.exit.condition}`, "
        f"equal-weight up to {spec.position.max_positions} names, signal at close and fill at next open."
    )
    why = spec.notes or "No economic hypothesis text was provided in the strategy spec."

    how = (
        f"Full-sample CAGR {_pct(perf.get('cagr'))}, Sharpe {_num(perf.get('sharpe'))}, "
        f"win rate {_pct(trades.get('win_rate'))}, profit factor {_num(trades.get('profit_factor'))}, "
        f"expectancy {_num(trades.get('expectancy'), 0)}. "
        f"OOS CAGR {_pct(oos.get('cagr'))}, OOS Sharpe {_num(oos.get('sharpe'))}, "
        f"OOS win rate {_pct(oos.get('win_rate'))}."
    )
    if target_wr is not None and oos.get("win_rate") is not None:
        meets = float(oos["win_rate"]) >= float(target_wr)
        how += f" Soft win-rate target {_pct(target_wr)} was {'met' if meets else 'not met'} on OOS."

    risk = (
        f"Max drawdown {_pct(perf.get('max_drawdown'))}, recovery ~{perf.get('recovery_time_days')} days, "
        f"volatility {_pct(perf.get('volatility'))}. "
        f"Monte Carlo median DD {_pct(monte_carlo.get('median_dd'))}, "
        f"tail DD {_pct(monte_carlo.get('dd_95th_percentile'))}."
    )

    breaks = []
    if validation.get("cost_stress", {}).get("verdict") == "BREAKS_UNDER_COST_STRESS":
        breaks.append("Higher transaction costs.")
    if validation.get("parameter_sensitivity", {}).get("robustness") == "PEAKY_SURFACE":
        breaks.append("Narrow parameter peak (overfitting risk).")
    if not regime.get("stable_sign", False):
        breaks.append("Performance uneven across subperiods.")
    if not breaks:
        breaks.append("No single automatic break flag dominated; still review survivorship and capacity.")

    robust = (
        f"Validation overall={validation.get('overall_verdict')}; "
        f"parameter surface={validation.get('parameter_sensitivity', {}).get('robustness')}; "
        f"walk-forward={validation.get('walk_forward', {}).get('verdict')}; "
        f"cost stress={validation.get('cost_stress', {}).get('verdict')}."
    )

    warnings = [
        f["message"] for f in bias.get("flags", []) if f.get("severity") in {"critical", "warning"}
    ]
    if bench.get("status") == "OK":
        warnings.append(
            f"Benchmark comparison: excess CAGR {_pct(bench.get('excess_cagr'))}, IR {_num(bench.get('information_ratio'))}."
        )

    return {
        "what_is_the_strategy": what,
        "why_might_it_work": why,
        "how_did_it_perform": how,
        "how_risky_is_it": risk,
        "what_breaks_it": " ".join(breaks),
        "is_result_robust": robust,
        "major_warnings": warnings,
        "research_conclusion_summary": f"{conclusion}. {conclusion_rationale}",
    }


def build_technical_report(
    spec: StrategySpec,
    *,
    experiment_id: str,
    data_version: dict[str, Any],
    data_quality: dict[str, Any],
    analytics: dict[str, Any],
    validation: dict[str, Any],
    regime: dict[str, Any],
    bootstrap: dict[str, Any],
    monte_carlo: dict[str, Any],
    bias: dict[str, Any],
    conclusion: str,
    conclusion_rationale: str,
    assumptions: list[str],
) -> dict[str, Any]:
    oos_wr = (
        validation.get("out_of_sample", {})
        .get("out_of_sample", {})
        .get("metrics", {})
        .get("win_rate")
    )
    target_wr = spec.research_objective.target_win_rate
    meets_wr = None if target_wr is None or oos_wr is None else bool(float(oos_wr) >= float(target_wr))

    return {
        "strategy_explanation": {
            "spec": spec.model_dump(mode="json"),
            "notes": spec.notes,
        },
        "data_quality": data_quality,
        "backtest_results": {
            "performance": analytics.get("performance", {}),
            "data_version": data_version,
        },
        "trade_statistics": analytics.get("trades", {}),
        "risk_statistics": {
            k: analytics.get("performance", {}).get(k)
            for k in [
                "volatility",
                "max_drawdown",
                "max_drawdown_duration_days",
                "recovery_time_days",
                "downside_deviation",
                "time_underwater_pct",
            ]
        },
        "benchmark_comparison": analytics.get("benchmark", {}),
        "out_of_sample": validation.get("out_of_sample", {}),
        "walk_forward": validation.get("walk_forward", {}),
        "parameter_sensitivity": validation.get("parameter_sensitivity", {}),
        "cost_sensitivity": validation.get("cost_stress", {}),
        "regime_analysis": regime,
        "monte_carlo": monte_carlo,
        "bootstrap": bootstrap,
        "stress_tests": {
            "cost_stress": validation.get("cost_stress", {}),
            "notes": "Additional delay/vol-cluster stresses can be expanded later.",
        },
        "bias_checks": bias,
        "overfitting_assessment": {
            "parameter_robustness": validation.get("parameter_sensitivity", {}).get("robustness"),
            "plateau_score": validation.get("parameter_sensitivity", {}).get("plateau_score"),
            "oos_protocol": "frozen_parameters_is_only_grid",
            "judgment": (
                "Elevated overfitting risk"
                if validation.get("parameter_sensitivity", {}).get("robustness") == "PEAKY_SURFACE"
                else "No single-peak IS surface detected; still not proof against data snooping."
            ),
        },
        "research_conclusion": {
            "status": conclusion,
            "rationale": conclusion_rationale,
            "meets_soft_targets": {
                "target_win_rate": target_wr,
                "oos_win_rate": oos_wr,
                "meets_target_win_rate": meets_wr,
            },
            "next_tests": [
                "Point-in-time index membership / delisting handling",
                "Broker-specific cost schedule",
                "Capacity / liquidity constraints",
                "Hermes-orchestrated multi-strategy experiment registry in Supabase",
            ],
        },
        "experiment_metadata": {
            "experiment_id": experiment_id,
            "assumptions_log": assumptions,
        },
    }


def render_simple_markdown(simple: dict[str, Any], *, experiment_id: str) -> str:
    warnings = simple.get("major_warnings") or []
    warn_lines = "\n".join(f"- {w}" for w in warnings) if warnings else "- None"
    return f"""# Research Report (Simple) — {experiment_id}

## What is the strategy?
{simple['what_is_the_strategy']}

## Why might it work?
{simple['why_might_it_work']}

## How did it perform?
{simple['how_did_it_perform']}

## How risky is it?
{simple['how_risky_is_it']}

## What breaks it?
{simple['what_breaks_it']}

## Is the result robust?
{simple['is_result_robust']}

## Major warnings
{warn_lines}

## Research conclusion
{simple['research_conclusion_summary']}
"""
