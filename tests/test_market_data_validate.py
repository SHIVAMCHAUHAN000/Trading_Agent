"""Unit tests for Stage 3 market-data validation/cleaning."""

from __future__ import annotations

import pandas as pd

from market_data.validate import (
    build_quality_report,
    clean_symbol_frame,
    concatenate_clean_frames,
    validate_symbol_frame,
)


def _bars(**overrides):
    base = {
        "Date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
        "Symbol": ["TEST.NS"] * 3,
        "Open": [10.0, 11.0, 12.0],
        "High": [11.0, 12.0, 13.0],
        "Low": [9.0, 10.0, 11.0],
        "Close": [10.5, 11.5, 12.5],
        "AdjClose": [10.5, 11.5, 12.5],
        "Volume": [1000, 1100, 1200],
    }
    base.update(overrides)
    return pd.DataFrame(base)


def test_valid_ohlc_passes():
    issues = validate_symbol_frame(_bars(), "TEST.NS")
    critical = [i for i in issues if i["severity"] == "critical"]
    assert critical == []


def test_invalid_ohlc_flagged():
    df = _bars(High=[8.0, 12.0, 13.0])  # first high < open/close
    issues = validate_symbol_frame(df, "TEST.NS")
    assert any(i["code"] == "INVALID_OHLC" for i in issues)


def test_duplicate_dates_flagged_and_cleaned():
    df = _bars()
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    issues = validate_symbol_frame(df, "TEST.NS")
    assert any(i["code"] == "DUPLICATE_DATES" for i in issues)
    cleaned = clean_symbol_frame(df)
    assert cleaned["Date"].duplicated().sum() == 0


def test_quality_report_status_fail_on_empty_download():
    frames = {"X.NS": _bars()}
    summary = {"provider": "yfinance", "failed": 1, "failures": [{"symbol": "Y.NS", "error": "empty_history"}]}
    report = build_quality_report(frames, download_summary=summary, universe_id="NIFTY50", history_start="2015-01-01")
    assert report["status"] == "FAIL"


def test_concatenate_clean_frames():
    frames = {"A.NS": _bars(Symbol=["A.NS"] * 3), "B.NS": _bars(Symbol=["B.NS"] * 3)}
    bars = concatenate_clean_frames(frames)
    assert len(bars) == 6
    assert set(bars["Symbol"]) == {"A.NS", "B.NS"}
