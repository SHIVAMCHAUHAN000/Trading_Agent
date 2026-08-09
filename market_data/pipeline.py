"""End-to-end historical data pipeline for V1."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from market_data.download import download_universe
from market_data.store import new_dataset_id, write_processed_bundle, write_raw_frames
from market_data.universe import benchmark_symbol, load_universe, universe_symbols
from market_data.validate import build_quality_report, concatenate_clean_frames


def run_historical_pipeline(
    *,
    start: str = "2015-01-01",
    end: str | None = None,
    universe_path: Path | None = None,
    include_benchmark: bool = True,
    dataset_id: str | None = None,
) -> dict[str, Any]:
    """
    Data Provider -> Raw (immutable) -> Validate -> Clean Parquet

    Supabase catalog sync is deferred until credentials are provided.
    """
    universe = load_universe(universe_path)
    symbols = universe_symbols(universe_path)
    bench = benchmark_symbol(universe_path) if include_benchmark else None
    all_symbols = list(symbols)
    if bench and bench not in all_symbols:
        all_symbols.append(bench)

    dsid = dataset_id or new_dataset_id()
    frames, download_summary = download_universe(all_symbols, start=start, end=end, auto_adjust=True)

    raw_meta = {
        "dataset_id": dsid,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "universe_id": universe.get("universe_id", "NIFTY50"),
        "benchmark": bench,
        "symbols_requested": all_symbols,
        "download_summary": download_summary,
        "history_start_requested": start,
        "history_end_requested": end,
        "auto_adjust": True,
        "immutable_raw": True,
    }
    raw_path = write_raw_frames(dsid, frames, raw_meta)

    quality = build_quality_report(
        frames,
        download_summary=download_summary,
        universe_id=str(universe.get("universe_id", "NIFTY50")),
        history_start=start,
    )
    bars = concatenate_clean_frames(frames)

    processed_meta = {
        "dataset_id": dsid,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_raw": str(raw_path),
        "rows": int(len(bars)),
        "symbols": sorted(bars["Symbol"].unique().tolist()) if not bars.empty else [],
        "quality_status": quality["status"],
    }
    processed_path = write_processed_bundle(dsid, bars, quality, processed_meta)

    return {
        "dataset_id": dsid,
        "raw_path": str(raw_path),
        "processed_path": str(processed_path),
        "quality_status": quality["status"],
        "download_summary": download_summary,
        "rows": int(len(bars)),
        "symbols_ok": sorted(frames.keys()),
        "quality_report_path": str(Path(processed_path) / "data_quality_report.json"),
    }
