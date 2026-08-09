"""Download daily OHLCV from yfinance. Does not write files."""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
import yfinance as yf

REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


def _normalize_frame(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["Date", "Symbol", *REQUIRED_COLUMNS, "AdjClose"])

    out = df.copy()
    if isinstance(out.columns, pd.MultiIndex):
        out.columns = out.columns.get_level_values(0)

    # yfinance auto_adjust=True folds adjustments into OHLC; keep AdjClose alias.
    if "Adj Close" in out.columns:
        out = out.rename(columns={"Adj Close": "AdjClose"})
    elif "Close" in out.columns and "AdjClose" not in out.columns:
        out["AdjClose"] = out["Close"]

    out = out.reset_index()
    date_col = "Date" if "Date" in out.columns else out.columns[0]
    out = out.rename(columns={date_col: "Date"})
    out["Date"] = pd.to_datetime(out["Date"], utc=True).dt.tz_convert(None).dt.normalize()
    out["Symbol"] = symbol

    cols = ["Date", "Symbol", "Open", "High", "Low", "Close", "AdjClose", "Volume"]
    missing = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c not in out.columns]
    if missing:
        raise ValueError(f"{symbol}: missing columns from yfinance: {missing}")
    if "AdjClose" not in out.columns:
        out["AdjClose"] = out["Close"]

    out = out[cols].sort_values("Date").drop_duplicates(subset=["Date"], keep="last")
    out["Volume"] = out["Volume"].fillna(0)
    return out.reset_index(drop=True)


def download_symbol(
    symbol: str,
    start: str | date,
    end: str | date | None = None,
    *,
    auto_adjust: bool = True,
) -> pd.DataFrame:
    """Fetch one symbol. Returns normalized daily bars (may be empty)."""
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=str(start), end=None if end is None else str(end), auto_adjust=auto_adjust)
    return _normalize_frame(df, symbol)


def download_universe(
    symbols: list[str],
    start: str | date,
    end: str | date | None = None,
    *,
    auto_adjust: bool = True,
) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    """
    Download many symbols sequentially.

    Returns:
      frames: symbol -> DataFrame
      summary: download metadata / failures
    """
    frames: dict[str, pd.DataFrame] = {}
    failures: list[dict[str, str]] = []

    for symbol in symbols:
        try:
            frame = download_symbol(symbol, start=start, end=end, auto_adjust=auto_adjust)
            if frame.empty:
                failures.append({"symbol": symbol, "error": "empty_history"})
            else:
                frames[symbol] = frame
        except Exception as exc:  # noqa: BLE001 - collect provider errors for report
            failures.append({"symbol": symbol, "error": str(exc)})

    summary = {
        "requested": len(symbols),
        "downloaded": len(frames),
        "failed": len(failures),
        "failures": failures,
        "start": str(start),
        "end": str(end) if end else None,
        "auto_adjust": auto_adjust,
        "provider": "yfinance",
    }
    return frames, summary
