"""CLI entry for Stage 9 Hermes bridge modes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.hermes_bridge.planner import llm_configured, run_llm_planner  # noqa: E402
from agents.research_agent.workflow import run_research_workflow  # noqa: E402


DEFAULT_REQUEST = (
    "Research this strategy for Indian equities over the maximum reliable historical period. "
    "Test whether it meets a 70% win-rate target, but prioritize expectancy, risk-adjusted return "
    "and robustness. Do not optimize parameters using the OOS period. Give me the complete "
    "research report in simple language."
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage 9 Hermes bridge")
    parser.add_argument(
        "--mode",
        choices=["deterministic", "llm", "auto"],
        default="auto",
        help="auto uses llm if API key present else deterministic",
    )
    parser.add_argument(
        "--strategy",
        default=str(ROOT / "strategies" / "defs" / "momentum_cross_section_v1.yaml"),
    )
    parser.add_argument("--request", default=DEFAULT_REQUEST)
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()

    mode = args.mode
    if mode == "auto":
        mode = "llm" if llm_configured() else "deterministic"

    if mode == "deterministic":
        result = run_research_workflow(args.strategy, out_dir=args.out_dir)
        print(json.dumps({"mode": "deterministic", **result}, indent=2, default=str))
        return 0

    result = run_llm_planner(args.request, default_strategy_path=args.strategy)
    print(json.dumps(result, indent=2, default=str))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
