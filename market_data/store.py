"""Immutable raw storage and processed Parquet writes."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data" / "raw" / "yfinance"
PROCESSED_ROOT = ROOT / "data" / "processed" / "yfinance"


def new_dataset_id(prefix: str = "YF") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}_{stamp}"


def raw_dir(dataset_id: str) -> Path:
    return RAW_ROOT / dataset_id


def processed_dir(dataset_id: str) -> Path:
    return PROCESSED_ROOT / dataset_id


def write_raw_frames(
    dataset_id: str,
    frames: dict[str, pd.DataFrame],
    meta: dict[str, Any],
) -> Path:
    """
    Write raw vendor pull once. Refuses if dataset_id already exists.
    Raw data must remain untouched by cleaning steps.
    """
    target = raw_dir(dataset_id)
    if target.exists():
        raise FileExistsError(f"Raw dataset already exists (immutable): {target}")

    target.mkdir(parents=True, exist_ok=False)
    for symbol, frame in frames.items():
        safe = symbol.replace("^", "INDEX_").replace("/", "_")
        frame.to_parquet(target / f"{safe}.parquet", index=False)

    meta_path = target / "META.json"
    meta_path.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
    return target


def write_processed_bundle(
    dataset_id: str,
    bars: pd.DataFrame,
    quality_report: dict[str, Any],
    meta: dict[str, Any],
) -> Path:
    """Write cleaned bars + quality report. Never writes into raw/."""
    target = processed_dir(dataset_id)
    if target.exists():
        raise FileExistsError(f"Processed dataset already exists: {target}")

    target.mkdir(parents=True, exist_ok=False)
    bars.to_parquet(target / "bars.parquet", index=False)
    (target / "data_quality_report.json").write_text(
        json.dumps(quality_report, indent=2, default=str),
        encoding="utf-8",
    )
    (target / "META.json").write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
    return target


def load_raw_frames(dataset_id: str) -> dict[str, pd.DataFrame]:
    target = raw_dir(dataset_id)
    if not target.exists():
        raise FileNotFoundError(target)
    frames: dict[str, pd.DataFrame] = {}
    for path in sorted(target.glob("*.parquet")):
        df = pd.read_parquet(path)
        symbol = str(df["Symbol"].iloc[0]) if not df.empty else path.stem
        frames[symbol] = df
    return frames
