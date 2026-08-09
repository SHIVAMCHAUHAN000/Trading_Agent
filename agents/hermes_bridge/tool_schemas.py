"""OpenAI-compatible tool schemas for Hermes / LLM planners."""

from __future__ import annotations

from typing import Any

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_strategy",
            "description": "Load and validate a StrategySpec YAML file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "strategy_path": {"type": "string", "description": "Path to strategy YAML"}
                },
                "required": ["strategy_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_data_version",
            "description": "Return the latest local historical dataset pointer/metadata.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "validate_data",
            "description": "Run structural/financial validation on the processed bars dataset.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_backtest",
            "description": "Run the daily long-only backtest for a StrategySpec.",
            "parameters": {
                "type": "object",
                "properties": {
                    "strategy_path": {"type": "string"},
                    "cost_multiplier": {"type": "number", "default": 1.0},
                },
                "required": ["strategy_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_metrics",
            "description": "Compute Stage 6 analytics for a strategy backtest (includes benchmark).",
            "parameters": {
                "type": "object",
                "properties": {
                    "strategy_path": {"type": "string"},
                    "cost_multiplier": {"type": "number", "default": 1.0},
                },
                "required": ["strategy_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_oos_test",
            "description": "Frozen-parameter 70/30 in-sample vs out-of-sample evaluation. Never optimizes on OOS.",
            "parameters": {
                "type": "object",
                "properties": {
                    "strategy_path": {"type": "string"},
                    "is_fraction": {"type": "number", "default": 0.7},
                },
                "required": ["strategy_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_walk_forward",
            "description": "Walk-forward validation with frozen strategy parameters.",
            "parameters": {
                "type": "object",
                "properties": {"strategy_path": {"type": "string"}},
                "required": ["strategy_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_parameter_test",
            "description": "IS-only parameter sensitivity grid. Must never use OOS for search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "strategy_path": {"type": "string"},
                    "is_fraction": {"type": "number", "default": 0.7},
                },
                "required": ["strategy_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_cost_stress",
            "description": "Stress the strategy at 1x/1.5x/2x/3x transaction costs.",
            "parameters": {
                "type": "object",
                "properties": {"strategy_path": {"type": "string"}},
                "required": ["strategy_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_monte_carlo",
            "description": "Trade-PnL permutation Monte Carlo drawdown/terminal equity analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "strategy_path": {"type": "string"},
                    "n": {"type": "integer", "default": 500},
                },
                "required": ["strategy_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_bootstrap",
            "description": "Bootstrap confidence intervals for Sharpe and terminal wealth multiple.",
            "parameters": {
                "type": "object",
                "properties": {
                    "strategy_path": {"type": "string"},
                    "n": {"type": "integer", "default": 500},
                },
                "required": ["strategy_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_regime_analysis",
            "description": "Calendar subperiod regime stability check on the equity curve.",
            "parameters": {
                "type": "object",
                "properties": {"strategy_path": {"type": "string"}},
                "required": ["strategy_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_bias_check",
            "description": "Static/heuristic bias flags (survivorship, listing age, peaky params, lookahead controls).",
            "parameters": {
                "type": "object",
                "properties": {"strategy_path": {"type": "string"}},
                "required": ["strategy_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_full_research",
            "description": "Run the full deterministic research workflow and write Layer-1 + Layer-2 reports.",
            "parameters": {
                "type": "object",
                "properties": {
                    "strategy_path": {"type": "string"},
                    "is_fraction": {"type": "number", "default": 0.7},
                    "out_dir": {"type": "string"},
                },
                "required": ["strategy_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_report",
            "description": "Alias for run_full_research — produce the complete institutional research report.",
            "parameters": {
                "type": "object",
                "properties": {
                    "strategy_path": {"type": "string"},
                    "is_fraction": {"type": "number", "default": 0.7},
                    "out_dir": {"type": "string"},
                },
                "required": ["strategy_path"],
            },
        },
    },
]


def list_tool_names() -> list[str]:
    return [t["function"]["name"] for t in TOOL_SCHEMAS]
