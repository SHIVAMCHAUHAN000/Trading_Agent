"""Dispatch Hermes/LLM tool calls onto the quant research lab."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agents.hermes_bridge.tool_schemas import list_tool_names
from agents.research_agent import tools as research_tools
from agents.research_agent.workflow import run_research_workflow
from validation.out_of_sample.oos import run_oos_validation
from validation.robustness.parameter_sensitivity import run_parameter_sensitivity
from validation.stress.cost_stress import run_cost_stress
from validation.walk_forward.walk_forward import run_walk_forward

ROOT = Path(__file__).resolve().parents[2]


def _jsonable(obj: Any) -> Any:
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    try:
        json.dumps(obj)
        return obj
    except TypeError:
        return json.loads(json.dumps(obj, default=str))


def dispatch_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    args = arguments or {}
    if name not in list_tool_names():
        return {"ok": False, "error": f"Unknown tool: {name}", "available": list_tool_names()}

    try:
        if name == "get_strategy":
            spec = research_tools.get_strategy(args["strategy_path"])
            return {"ok": True, "tool": name, "result": spec.model_dump(mode="json")}

        if name == "get_data_version":
            return {"ok": True, "tool": name, "result": research_tools.get_data_version()}

        if name == "validate_data":
            bars = research_tools.get_data()
            return {"ok": True, "tool": name, "result": research_tools.validate_data(bars)}

        if name in {"run_full_research", "generate_report"}:
            out = run_research_workflow(
                args["strategy_path"],
                out_dir=args.get("out_dir"),
                is_fraction=float(args.get("is_fraction", 0.70)),
            )
            return {"ok": True, "tool": name, "result": out}

        strategy_path = args.get("strategy_path")
        if strategy_path is None and name not in {"get_data_version", "validate_data"}:
            return {"ok": False, "error": "strategy_path is required"}

        spec = research_tools.get_strategy(strategy_path)
        bars = research_tools.get_data()
        cost_mult = float(args.get("cost_multiplier", 1.0))

        if name == "run_backtest":
            result = research_tools.run_backtest_tool(spec, bars, cost_multiplier=cost_mult)
            return {
                "ok": True,
                "tool": name,
                "result": {
                    "meta": result.meta,
                    "equity_tail": result.equity_curve.tail(3).reset_index().to_dict(orient="records"),
                    "n_trades": int(len(result.trades)),
                },
            }

        if name == "calculate_metrics":
            result = research_tools.run_backtest_tool(spec, bars, cost_multiplier=cost_mult)
            metrics = research_tools.calculate_metrics(result, capital=float(spec.capital))
            metrics.pop("_enriched_trades", None)
            return {"ok": True, "tool": name, "result": _jsonable(metrics)}

        if name == "run_oos_test":
            out = run_oos_validation(spec, bars, is_fraction=float(args.get("is_fraction", 0.70)))
            return {"ok": True, "tool": name, "result": _jsonable(out)}

        if name == "run_walk_forward":
            return {"ok": True, "tool": name, "result": _jsonable(run_walk_forward(spec, bars))}

        if name == "run_parameter_test":
            out = run_parameter_sensitivity(spec, bars, is_fraction=float(args.get("is_fraction", 0.70)))
            return {"ok": True, "tool": name, "result": _jsonable(out)}

        if name == "run_cost_stress":
            return {"ok": True, "tool": name, "result": _jsonable(run_cost_stress(spec, bars))}

        if name in {"run_monte_carlo", "run_bootstrap", "run_regime_analysis"}:
            result = research_tools.run_backtest_tool(spec, bars)
            if name == "run_monte_carlo":
                out = research_tools.run_monte_carlo(result, n=int(args.get("n", 500)))
            elif name == "run_bootstrap":
                out = research_tools.run_bootstrap(result, n=int(args.get("n", 500)))
            else:
                out = research_tools.run_regime_analysis(result, capital=float(spec.capital))
            return {"ok": True, "tool": name, "result": _jsonable(out)}

        if name == "run_bias_check":
            quality = research_tools.validate_data(bars)
            # Lightweight validation summary for bias context
            from validation.suite import run_validation_suite

            validation = run_validation_suite(
                spec,
                bars,
                include_parameter_sensitivity=True,
                include_walk_forward=False,
                include_cost_stress=False,
                lookbacks=[int(spec.entry.parameters.get("lookback_days", 252))],
                top_ns=[int(spec.entry.parameters.get("top_n", spec.position.max_positions))],
            )
            out = research_tools.run_bias_check(spec, quality, validation)
            return {"ok": True, "tool": name, "result": _jsonable(out)}

        return {"ok": False, "error": f"Unhandled tool: {name}"}
    except Exception as exc:  # noqa: BLE001 - surface tool errors to Hermes/LLM
        return {"ok": False, "tool": name, "error": str(exc)}
