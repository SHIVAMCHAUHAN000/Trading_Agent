"""
Optional LLM planner over OpenAI-compatible APIs.

If no API key is configured, callers should use deterministic workflow or Hermes skill + terminal RPC.
"""

from __future__ import annotations

import json
import os
from typing import Any

from agents.hermes_bridge.dispatcher import dispatch_tool
from agents.hermes_bridge.tool_schemas import TOOL_SCHEMAS

SYSTEM_PROMPT = """You are the Indian Market Strategy Research Agent orchestrator.
You may ONLY research and validate strategies. Never place trades or suggest live order routing.

Hard rules:
1. Do not optimize parameters using out-of-sample data.
2. Prefer expectancy, risk-adjusted return, and robustness over win rate.
3. A soft win-rate target is a question to answer, not a result to force.
4. Always end by calling run_full_research OR synthesize from prior tool results into a clear conclusion.
5. Mention survivorship bias when using current NIFTY50 membership.

Use tools to gather evidence. Be concise in the final answer.
"""


def llm_configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("HERMES_API_KEY"))


def _client_and_model():
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Install openai package for LLM planner mode: pip install openai") from exc

    if os.getenv("OPENROUTER_API_KEY"):
        client = OpenAI(api_key=os.environ["OPENROUTER_API_KEY"], base_url="https://openrouter.ai/api/v1")
        model = os.getenv("HERMES_BRIDGE_MODEL", "openai/gpt-4o-mini")
    elif os.getenv("HERMES_API_KEY") and os.getenv("HERMES_BASE_URL"):
        client = OpenAI(api_key=os.environ["HERMES_API_KEY"], base_url=os.environ["HERMES_BASE_URL"])
        model = os.getenv("HERMES_BRIDGE_MODEL", "hermes")
    else:
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        model = os.getenv("HERMES_BRIDGE_MODEL", "gpt-4o-mini")
    return client, model


def run_llm_planner(
    user_request: str,
    *,
    default_strategy_path: str,
    max_iterations: int = 8,
) -> dict[str, Any]:
    if not llm_configured():
        return {
            "ok": False,
            "error": "No LLM API key configured. Set OPENAI_API_KEY, OPENROUTER_API_KEY, or HERMES_API_KEY+HERMES_BASE_URL.",
            "fallback": "deterministic",
        }

    client, model = _client_and_model()
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"{user_request}\n\n"
                f"Default strategy path if needed: {default_strategy_path}\n"
                "If the request is broad, call run_full_research."
            ),
        },
    ]
    trace: list[dict[str, Any]] = []

    for i in range(max_iterations):
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )
        msg = resp.choices[0].message
        if msg.tool_calls:
            messages.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in msg.tool_calls
                    ],
                }
            )
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments or "{}")
                if "strategy_path" not in args and tc.function.name not in {"get_data_version", "validate_data"}:
                    args["strategy_path"] = default_strategy_path
                result = dispatch_tool(tc.function.name, args)
                trace.append({"iteration": i + 1, "tool": tc.function.name, "args": args, "ok": result.get("ok")})
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result, default=str)[:120000],
                    }
                )
            continue

        return {
            "ok": True,
            "mode": "llm",
            "model": model,
            "final_answer": msg.content or "",
            "trace": trace,
        }

    return {
        "ok": False,
        "mode": "llm",
        "error": "max_iterations_exceeded",
        "trace": trace,
    }
