"""CLI: download + validate NIFTY50 / benchmark history into raw + processed Parquet."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from market_data.pipeline import run_historical_pipeline  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage 3 historical data pipeline (yfinance)")
    parser.add_argument("--start", default="2015-01-01", help="History start date YYYY-MM-DD")
    parser.add_argument("--end", default=None, help="Optional history end date YYYY-MM-DD")
    parser.add_argument("--dataset-id", default=None, help="Optional dataset id; default auto timestamp")
    parser.add_argument("--no-benchmark", action="store_true", help="Skip ^NSEI benchmark download")
    args = parser.parse_args()

    result = run_historical_pipeline(
        start=args.start,
        end=args.end,
        include_benchmark=not args.no_benchmark,
        dataset_id=args.dataset_id,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["quality_status"] != "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
