"""CLI: Stage 7 validation suite (OOS, walk-forward, sensitivity, cost stress)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backtesting.engine.data import load_bars  # noqa: E402
from strategies.loader import load_strategy_spec  # noqa: E402
from validation.suite import run_validation_suite  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage 7 validation suite")
    parser.add_argument(
        "--strategy",
        default=str(ROOT / "strategies" / "defs" / "momentum_cross_section_v1.yaml"),
    )
    parser.add_argument("--is-fraction", type=float, default=0.70)
    parser.add_argument("--skip-sensitivity", action="store_true")
    parser.add_argument("--skip-walk-forward", action="store_true")
    parser.add_argument("--skip-cost-stress", action="store_true")
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()

    spec = load_strategy_spec(args.strategy)
    bars = load_bars()
    report = run_validation_suite(
        spec,
        bars,
        is_fraction=args.is_fraction,
        include_parameter_sensitivity=not args.skip_sensitivity,
        include_walk_forward=not args.skip_walk_forward,
        include_cost_stress=not args.skip_cost_stress,
    )

    stamp = pd.Timestamp.now("UTC").strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.out_dir) if args.out_dir else ROOT / "reports" / f"validation_{spec.name}_{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "validation_report.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    # Compact console summary
    summary = {
        "out_dir": str(out_dir),
        "overall_verdict": report["overall_verdict"],
        "risk_flags": report["risk_flags"],
        "oos_verdict": report["out_of_sample"].get("verdict"),
        "walk_forward_verdict": report["walk_forward"].get("verdict"),
        "parameter_robustness": report["parameter_sensitivity"].get("robustness"),
        "cost_stress_verdict": report["cost_stress"].get("verdict"),
        "oos": report["out_of_sample"].get("out_of_sample"),
        "wf_summary": report["walk_forward"].get("summary"),
    }
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
