"""CLI: run the Stage 8 research agent workflow end-to-end."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.research_agent.workflow import run_research_workflow  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Research a StrategySpec and produce Layer-1 + Layer-2 reports (no trade execution)."
    )
    parser.add_argument(
        "--strategy",
        default=str(ROOT / "strategies" / "defs" / "momentum_cross_section_v1.yaml"),
        help="Path to StrategySpec YAML",
    )
    parser.add_argument("--is-fraction", type=float, default=0.70)
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()

    result = run_research_workflow(
        args.strategy,
        out_dir=args.out_dir,
        is_fraction=args.is_fraction,
    )
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
