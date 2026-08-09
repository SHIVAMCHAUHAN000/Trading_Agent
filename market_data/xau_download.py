"""XAUUSD / gold intraday data downloaders for V2."""

from __future__ import annotations

import json
import struct
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import lzma
import pandas as pd
import requests
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data" / "raw" / "xauusd"
PROCESSED_ROOT = ROOT / "data" / "processed" / "xauusd"


def download_gc_futures_1m(period: str = "7d") -> pd.DataFrame:
    """Yahoo GC=F 1-minute bars (typically ~last 7 trading days only)."""
    df = yf.download("GC=F", period=period, interval="1m", progress=False, auto_adjust=True)
    if df is None or df.empty:
        return pd.DataFrame(columns=["DateTime", "Open", "High", "Low", "Close", "Volume"])
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    out = df.reset_index()
    dt_col = "Datetime" if "Datetime" in out.columns else out.columns[0]
    out = out.rename(columns={dt_col: "DateTime"})
    out["DateTime"] = pd.to_datetime(out["DateTime"], utc=True).dt.tz_convert("UTC")
    out["Symbol"] = "XAUUSD"
    out["Source"] = "yfinance_GC=F"
    cols = ["DateTime", "Symbol", "Open", "High", "Low", "Close", "Volume", "Source"]
    return out[cols].dropna(subset=["Open", "High", "Low", "Close"]).sort_values("DateTime").reset_index(drop=True)


def _duka_point(symbol: str = "XAUUSD") -> float:
    # Dukascopy integer price scale for XAUUSD is commonly 1000
    return 1000.0


def download_dukascopy_hour_ticks(dt: datetime, *, symbol: str = "XAUUSD", session: requests.Session | None = None) -> pd.DataFrame:
    """Download one UTC hour of Dukascopy ticks; returns empty frame on miss/rate-limit."""
    session = session or requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 TradingAgent/2.0",
            "Accept": "*/*",
            "Referer": "https://www.dukascopy.com/",
        }
    )
    url = (
        f"https://datafeed.dukascopy.com/datafeed/{symbol}/"
        f"{dt.year}/{dt.month - 1:02d}/{dt.day:02d}/{dt.hour:02d}h_ticks.bi5"
    )
    try:
        r = session.get(url, timeout=45)
    except requests.RequestException:
        return pd.DataFrame()
    if r.status_code != 200 or len(r.content) < 50:
        return pd.DataFrame()
    try:
        raw = lzma.decompress(r.content)
    except lzma.LZMAError:
        return pd.DataFrame()

    point = _duka_point(symbol)
    base = datetime(dt.year, dt.month, dt.day, dt.hour, tzinfo=timezone.utc)
    rows = []
    for i in range(0, len(raw) // 20 * 20, 20):
        ms, ask, bid, ask_vol, bid_vol = struct.unpack(">IIIff", raw[i : i + 20])
        ts = base + timedelta(milliseconds=ms)
        rows.append(
            {
                "DateTime": ts,
                "Bid": bid / point,
                "Ask": ask / point,
                "BidVol": bid_vol,
                "AskVol": ask_vol,
            }
        )
    return pd.DataFrame(rows)


def ticks_to_m1(ticks: pd.DataFrame) -> pd.DataFrame:
    if ticks.empty:
        return pd.DataFrame(columns=["DateTime", "Open", "High", "Low", "Close", "Volume"])
    t = ticks.copy()
    t["DateTime"] = pd.to_datetime(t["DateTime"], utc=True)
    t["Mid"] = (t["Bid"] + t["Ask"]) / 2.0
    t = t.set_index("DateTime").sort_index()
    ohlc = t["Mid"].resample("1min").ohlc()
    vol = (t["BidVol"].fillna(0) + t["AskVol"].fillna(0)).resample("1min").sum()
    out = ohlc.join(vol.rename("Volume")).dropna(subset=["open"])
    out = out.reset_index().rename(
        columns={"open": "Open", "high": "High", "low": "Low", "close": "Close"}
    )
    return out


def download_dukascopy_m1_range(
    start: datetime,
    end: datetime,
    *,
    symbol: str = "XAUUSD",
    sleep_s: float = 0.35,
    max_hours: int | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Best-effort Dukascopy M1 download. May be rate-limited (503/429).
    Returns bars + download summary.
    """
    session = requests.Session()
    start = start.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
    end = end.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
    hours = []
    cur = start
    while cur < end:
        hours.append(cur)
        cur += timedelta(hours=1)
        if max_hours is not None and len(hours) >= max_hours:
            break

    frames = []
    ok = 0
    fail = 0
    for i, hour in enumerate(hours):
        ticks = download_dukascopy_hour_ticks(hour, symbol=symbol, session=session)
        if ticks.empty:
            fail += 1
        else:
            ok += 1
            frames.append(ticks_to_m1(ticks))
        time.sleep(sleep_s)
        if (i + 1) % 24 == 0:
            time.sleep(2.0)

    if not frames:
        bars = pd.DataFrame(columns=["DateTime", "Symbol", "Open", "High", "Low", "Close", "Volume", "Source"])
    else:
        bars = pd.concat(frames, ignore_index=True)
        bars["Symbol"] = symbol
        bars["Source"] = "dukascopy"
        bars = bars.drop_duplicates("DateTime").sort_values("DateTime").reset_index(drop=True)

    summary = {
        "provider": "dukascopy",
        "symbol": symbol,
        "hours_requested": len(hours),
        "hours_ok": ok,
        "hours_failed": fail,
        "rows": int(len(bars)),
    }
    return bars, summary


def save_xau_dataset(bars: pd.DataFrame, *, dataset_id: str | None = None, meta: dict[str, Any] | None = None) -> dict[str, str]:
    dsid = dataset_id or datetime.now(timezone.utc).strftime("XAU_%Y%m%dT%H%M%SZ")
    raw_dir = RAW_ROOT / dsid
    proc_dir = PROCESSED_ROOT / dsid
    raw_dir.mkdir(parents=True, exist_ok=True)
    proc_dir.mkdir(parents=True, exist_ok=True)
    bars.to_parquet(raw_dir / "bars_1m.parquet", index=False)
    bars.to_parquet(proc_dir / "bars_1m.parquet", index=False)
    meta = {
        "dataset_id": dsid,
        "symbol": "XAUUSD",
        "timeframe": "1m",
        "rows": int(len(bars)),
        "start": None if bars.empty else str(bars["DateTime"].min()),
        "end": None if bars.empty else str(bars["DateTime"].max()),
        **(meta or {}),
    }
    (proc_dir / "META.json").write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
    pointer = {
        "dataset_id": dsid,
        "bars_path": str(proc_dir / "bars_1m.parquet").replace(str(ROOT) + "\\", "").replace("\\", "/"),
        "meta": meta,
    }
    (ROOT / "config" / "latest_xau_dataset.yaml").write_text(
        "\n".join(
            [
                f"dataset_id: {dsid}",
                "symbol: XAUUSD",
                "timeframe: 1m",
                f"bars_path: {pointer['bars_path']}",
                f"rows: {meta['rows']}",
                f"start: {meta['start']}",
                f"end: {meta['end']}",
                f"source: {meta.get('source', bars['Source'].iloc[0] if not bars.empty else 'unknown')}",
                "note: Yahoo 1m history is short; Dukascopy preferred when reachable.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {"dataset_id": dsid, "processed_path": str(proc_dir), "bars_path": str(proc_dir / "bars_1m.parquet")}
