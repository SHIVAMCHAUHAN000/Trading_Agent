"""Load processed bars into panels for the backtester."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]


def resolve_bars_path(dataset_pointer: Path | None = None) -> Path:
    pointer = dataset_pointer or (ROOT / "config" / "latest_dataset.yaml")
    meta = yaml.safe_load(pointer.read_text(encoding="utf-8"))
    path = ROOT / meta["bars_path"]
    if not path.exists():
        raise FileNotFoundError(f"Processed bars not found: {path}. Run Stage 3 pipeline first.")
    return path


def load_bars(bars_path: Path | None = None) -> pd.DataFrame:
    path = bars_path or resolve_bars_path()
    bars = pd.read_parquet(path)
    bars["Date"] = pd.to_datetime(bars["Date"]).dt.normalize()
    bars = bars.sort_values(["Date", "Symbol"]).reset_index(drop=True)
    return bars


def to_price_panel(bars: pd.DataFrame, field: str, *, exclude_benchmark: bool = True) -> pd.DataFrame:
    frame = bars.copy()
    if exclude_benchmark:
        frame = frame[frame["Symbol"] != "^NSEI"]
    panel = frame.pivot(index="Date", columns="Symbol", values=field).sort_index()
    return panel


def benchmark_close(bars: pd.DataFrame, symbol: str = "^NSEI") -> pd.Series:
    bench = bars.loc[bars["Symbol"] == symbol, ["Date", "Close"]].drop_duplicates("Date")
    if bench.empty:
        return pd.Series(dtype=float)
    return bench.set_index("Date")["Close"].sort_index()
