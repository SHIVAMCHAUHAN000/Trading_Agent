"""Download XAUUSD 1m bars (Yahoo GC=F short history; Dukascopy optional)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from market_data.xau_download import (  # noqa: E402
    download_dukascopy_m1_range,
    download_gc_futures_1m,
    save_xau_dataset,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["yahoo", "dukascopy", "auto"], default="auto")
    parser.add_argument("--yahoo-period", default="7d")
    parser.add_argument("--duka-days", type=int, default=3, help="Dukascopy lookback days (slow)")
    args = parser.parse_args()

    source = args.source
    bars = None
    meta = {}

    if source in {"yahoo", "auto"}:
        bars = download_gc_futures_1m(period=args.yahoo_period)
        meta = {"source": "yfinance_GC=F", "yahoo_period": args.yahoo_period}
        if bars.empty and source == "yahoo":
            print(json.dumps({"ok": False, "error": "yahoo_empty"}))
            return 2

    if (bars is None or bars.empty) and source in {"dukascopy", "auto"}:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=args.duka_days)
        bars, summary = download_dukascopy_m1_range(start, end, max_hours=args.duka_days * 24)
        meta = summary

    if bars is None or bars.empty:
        print(json.dumps({"ok": False, "error": "no_bars_downloaded", "meta": meta}, indent=2))
        return 2

    paths = save_xau_dataset(bars, meta=meta)
    print(json.dumps({"ok": True, **paths, "rows": int(len(bars)), "meta": meta}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
