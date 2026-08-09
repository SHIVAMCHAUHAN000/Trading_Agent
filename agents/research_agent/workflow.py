"""
Deterministic research workflow for Stage 8.

Hermes/LLM orchestration comes in Stage 9. This workflow already exposes the
same tool steps an LLM agent should call.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from agents.research_agent.experiment import append_experiment, next_experiment_id
from agents.research_agent.report_builder import (
    build_simple_report,
    build_technical_report,
    map_conclusion,
    render_simple_markdown,
)
from agents.research_agent import tools
from reports_ui.render_dashboard import write_dashboard

ROOT = Path(__file__).resolve().parents[2]


def run_research_workflow(
    strategy_path: str | Path,
    *,
    out_dir: str | Path | None = None,
    is_fraction: float = 0.70,
) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    experiment_id = next_experiment_id()

    def _step(name: str, status: str, detail: Any = None) -> None:
        steps.append({"step": name, "status": status, "detail": detail})

    # 1) Receive / understand strategy
    spec = tools.get_strategy(strategy_path)
    _step("understand_strategy", "OK", {"name": spec.name})

    # 2) Data
    data_version = tools.get_data_version()
    bars = tools.get_data()
    _step("check_required_data", "OK", {"rows": int(len(bars)), "dataset_id": data_version.get("dataset_id")})

    # 3) Validate data
    data_quality = tools.validate_data(bars)
    if data_quality.get("status") == "FAIL":
        _step("validate_data", "FAIL", {"critical_issues": data_quality.get("critical_issues")})
        raise RuntimeError("Data validation failed; refusing to continue research workflow.")
    _step("validate_data", "OK", {"status": data_quality.get("status")})

    # 4) Baseline backtest
    result = tools.run_backtest_tool(spec, bars)
    _step("run_baseline_backtest", "OK", {"n_trades": result.meta.get("n_trades")})

    # 5) Analytics
    analytics = tools.calculate_metrics(result, capital=float(spec.capital))
    enriched_trades = analytics.pop("_enriched_trades")
    _step("analyze_results", "OK", {"benchmark": analytics.get("benchmark", {}).get("status")})

    # 6-10) Validation suite (costs, params, OOS, walk-forward)
    validation = tools.run_validation_tool(spec, bars, is_fraction=is_fraction)
    _step("run_validation_suite", "OK", {"overall": validation.get("overall_verdict")})

    # If hard reject, still complete report (store failures) but mark failed gate
    hard_fail = validation.get("overall_verdict") == "REJECT"
    if hard_fail:
        _step("validation_gate", "FAIL", {"risk_flags": validation.get("risk_flags")})
    else:
        _step("validation_gate", "OK", {"risk_flags": validation.get("risk_flags")})

    # 11) Regime / stats / MC / bias
    regime = tools.run_regime_analysis(result, capital=float(spec.capital))
    bootstrap = tools.run_bootstrap(result)
    monte_carlo = tools.run_monte_carlo(result)
    bias = tools.run_bias_check(spec, data_quality, validation)
    _step("run_statistical_and_bias_checks", "OK", None)

    conclusion, rationale = map_conclusion(validation, bias)
    assumptions = list(result.meta.get("assumptions", [])) + [
        f"IS/OOS fraction={is_fraction}",
        "Research agent workflow is deterministic in Stage 8 (Hermes later).",
        "No trade execution.",
    ]

    simple = build_simple_report(
        spec,
        analytics=analytics,
        validation=validation,
        regime=regime,
        monte_carlo=monte_carlo,
        bias=bias,
        conclusion=conclusion,
        conclusion_rationale=rationale,
    )
    technical = build_technical_report(
        spec,
        experiment_id=experiment_id,
        data_version=data_version,
        data_quality=data_quality,
        analytics=analytics,
        validation=validation,
        regime=regime,
        bootstrap=bootstrap,
        monte_carlo=monte_carlo,
        bias=bias,
        conclusion=conclusion,
        conclusion_rationale=rationale,
        assumptions=assumptions,
    )

    stamp = pd.Timestamp.now("UTC").strftime("%Y%m%dT%H%M%SZ")
    out = Path(out_dir) if out_dir else ROOT / "reports" / f"research_{spec.name}_{experiment_id}_{stamp}"
    out.mkdir(parents=True, exist_ok=True)

    result.equity_curve.to_csv(out / "equity_curve.csv")
    if result.benchmark_equity is not None and not result.benchmark_equity.empty:
        result.benchmark_equity.to_csv(out / "benchmark_equity.csv", header=["BenchmarkEquity"])
    enriched_trades.to_csv(out / "trades.csv", index=False)

    payload = {
        "experiment_id": experiment_id,
        "strategy_name": spec.name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "request_snapshot": spec.model_dump(mode="json"),
        "workflow_steps": steps,
        "simple_report": simple,
        "technical_report": technical,
        "warnings": bias.get("flags", []),
        "conclusion": {"status": conclusion, "rationale": rationale},
        "artifacts": {
            "equity_curve_ref": str(out / "equity_curve.csv"),
            "trade_log_ref": str(out / "trades.csv"),
            "metrics_table_ref": str(out / "research_report.json"),
            "assumptions_log": assumptions,
        },
    }
    report_json = out / "research_report.json"
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    (out / "SIMPLE_REPORT.md").write_text(render_simple_markdown(simple, experiment_id=experiment_id), encoding="utf-8")
    dashboard_path = write_dashboard(report_json, out / "dashboard.html")

    append_experiment(
        {
            "experiment_id": experiment_id,
            "strategy_name": spec.name,
            "status": "COMPLETE",
            "conclusion": conclusion,
            "overall_validation": validation.get("overall_verdict"),
            "out_dir": str(out),
            "failed_gate": hard_fail,
            "dashboard": str(dashboard_path),
        }
    )

    return {
        "experiment_id": experiment_id,
        "out_dir": str(out),
        "conclusion": conclusion,
        "validation_overall": validation.get("overall_verdict"),
        "simple_report_path": str(out / "SIMPLE_REPORT.md"),
        "research_report_path": str(report_json),
        "dashboard_path": str(dashboard_path),
        "workflow_steps": steps,
    }
