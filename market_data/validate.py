"""Structural and financial validation for daily OHLCV bars."""

from __future__ import annotations

from typing import Any

import pandas as pd

PRICE_COLS = ["Open", "High", "Low", "Close", "AdjClose"]


def _issue(code: str, message: str, severity: str, symbol: str | None = None, count: int | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {
        "code": code,
        "message": message,
        "severity": severity,
    }
    if symbol is not None:
        item["symbol"] = symbol
    if count is not None:
        item["count"] = count
    return item


def validate_symbol_frame(df: pd.DataFrame, symbol: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if df is None or df.empty:
        return [_issue("EMPTY", "No rows downloaded", "critical", symbol)]

    required = ["Date", "Symbol", "Open", "High", "Low", "Close", "Volume"]
    missing_cols = [c for c in required if c not in df.columns]
    if missing_cols:
        return [_issue("MISSING_COLUMNS", f"Missing columns: {missing_cols}", "critical", symbol)]

    if df["Date"].duplicated().any():
        issues.append(
            _issue(
                "DUPLICATE_DATES",
                "Duplicate trading dates present",
                "critical",
                symbol,
                int(df["Date"].duplicated().sum()),
            )
        )

    if not df["Date"].is_monotonic_increasing:
        issues.append(_issue("UNSORTED_DATES", "Dates are not sorted ascending", "warning", symbol))

    for col in PRICE_COLS:
        if col not in df.columns:
            continue
        bad = df[col].isna().sum()
        if bad:
            issues.append(_issue("MISSING_PRICE", f"{col} has missing values", "critical", symbol, int(bad)))
        nonpos = (df[col] <= 0).sum()
        if nonpos:
            issues.append(_issue("NON_POSITIVE_PRICE", f"{col} has non-positive values", "critical", symbol, int(nonpos)))

    ohlc_bad = ~(
        (df["Low"] <= df["Open"])
        & (df["Low"] <= df["Close"])
        & (df["High"] >= df["Open"])
        & (df["High"] >= df["Close"])
        & (df["Low"] <= df["High"])
    )
    if ohlc_bad.any():
        issues.append(
            _issue(
                "INVALID_OHLC",
                "OHLC relationship violated (Low <= Open,Close <= High)",
                "critical",
                symbol,
                int(ohlc_bad.sum()),
            )
        )

    if (df["Volume"] < 0).any():
        issues.append(
            _issue("NEGATIVE_VOLUME", "Negative volume values present", "critical", symbol, int((df["Volume"] < 0).sum()))
        )

    # Abnormal jump check on close-to-close returns
    close = df["Close"].astype(float)
    rets = close.pct_change()
    jump_mask = rets.abs() > 0.35  # 35% single-day move flag for equities research review
    if jump_mask.fillna(False).any():
        issues.append(
            _issue(
                "ABNORMAL_JUMP",
                "Close-to-close return exceeded 35% on one or more days",
                "warning",
                symbol,
                int(jump_mask.fillna(False).sum()),
            )
        )

    zero_vol = (df["Volume"] == 0).sum()
    if zero_vol:
        issues.append(_issue("ZERO_VOLUME", "Zero-volume sessions present", "info", symbol, int(zero_vol)))

    return issues


def clean_symbol_frame(df: pd.DataFrame) -> pd.DataFrame:
    """
    Light cleaning for processed layer.
    Does not mutate raw files. Drops exact duplicate dates; sorts; casts types.
    """
    out = df.copy()
    out["Date"] = pd.to_datetime(out["Date"]).dt.normalize()
    out = out.sort_values("Date").drop_duplicates(subset=["Date"], keep="last")
    for col in PRICE_COLS:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    out["Volume"] = pd.to_numeric(out["Volume"], errors="coerce").fillna(0)
    # Drop rows with invalid core OHLC
    out = out.dropna(subset=["Open", "High", "Low", "Close"])
    valid = (
        (out["Low"] <= out["Open"])
        & (out["Low"] <= out["Close"])
        & (out["High"] >= out["Open"])
        & (out["High"] >= out["Close"])
        & (out["Low"] <= out["High"])
        & (out["Open"] > 0)
        & (out["High"] > 0)
        & (out["Low"] > 0)
        & (out["Close"] > 0)
    )
    out = out.loc[valid].reset_index(drop=True)
    return out


def build_quality_report(
    frames: dict[str, pd.DataFrame],
    *,
    download_summary: dict[str, Any],
    universe_id: str,
    history_start: str,
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    per_symbol: dict[str, Any] = {}

    for symbol, df in frames.items():
        symbol_issues = validate_symbol_frame(df, symbol)
        issues.extend(symbol_issues)
        per_symbol[symbol] = {
            "rows": int(len(df)),
            "start": None if df.empty else str(pd.to_datetime(df["Date"]).min().date()),
            "end": None if df.empty else str(pd.to_datetime(df["Date"]).max().date()),
            "issue_count": len(symbol_issues),
        }

    critical = [i for i in issues if i["severity"] == "critical"]
    warnings = [i for i in issues if i["severity"] == "warning"]

    # Coverage vs requested history start (calendar, not exchange calendar yet)
    coverage = []
    for symbol, stats in per_symbol.items():
        if stats["start"] and stats["start"] > history_start:
            coverage.append(
                {
                    "symbol": symbol,
                    "requested_start": history_start,
                    "actual_start": stats["start"],
                    "note": "Listing or Yahoo history starts after requested research start",
                }
            )

    report = {
        "universe_id": universe_id,
        "provider": download_summary.get("provider", "yfinance"),
        "download_summary": download_summary,
        "symbols_validated": len(frames),
        "critical_issues": len(critical),
        "warning_issues": len(warnings),
        "issues": issues,
        "per_symbol": per_symbol,
        "late_history_start": coverage,
        "bias_notes": [
            "Universe is current NIFTY50 constituents — survivorship bias remains for long backtests.",
            "Point-in-time index membership is not yet implemented.",
            "Exchange holiday calendar gaps are not fully modeled in Stage 3.",
        ],
        "status": "FAIL" if critical or download_summary.get("failed", 0) else "PASS_WITH_WARNINGS" if warnings or coverage else "PASS",
    }
    return report


def concatenate_clean_frames(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    cleaned = [clean_symbol_frame(df) for df in frames.values() if df is not None and not df.empty]
    if not cleaned:
        return pd.DataFrame(columns=["Date", "Symbol", "Open", "High", "Low", "Close", "AdjClose", "Volume"])
    bars = pd.concat(cleaned, ignore_index=True)
    bars = bars.sort_values(["Date", "Symbol"]).reset_index(drop=True)
    return bars
