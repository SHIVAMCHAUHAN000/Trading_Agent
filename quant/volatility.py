"""
Quantitative Volatility Analysis Engine.
Calculates Average True Range (ATR), Realized Volatility, Bollinger Band width,
and Volatility Regime (Compression / Squeeze vs Expansion).
"""

from __future__ import annotations

from typing import Any, Dict
import numpy as np
import pandas as pd


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculates Average True Range."""
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    return atr


def analyze_volatility(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyzes volatility characteristics, ATR, regime (squeeze vs expansion).
    """
    if df.empty or len(df) < 14:
        return {
            "atr": 0.0,
            "atr_pct": 0.0,
            "realized_vol": 0.0,
            "regime": "NORMAL",
            "state": "Insufficient data",
            "summary": "Insufficient candles for volatility analysis.",
        }

    close = df["close"]
    current_price = float(close.iloc[-1])
    atr_series = compute_atr(df, period=14)
    c_atr = round(float(atr_series.iloc[-1]), 2)
    p_atr = round(float(atr_series.iloc[-5]), 2) if len(atr_series) >= 5 else c_atr
    atr_pct = round((c_atr / current_price) * 100, 2) if current_price > 0 else 0.0

    # Realized Volatility (annualized rolling std of log returns)
    log_ret = np.log(close / close.shift(1)).dropna()
    realized_vol = round(float(log_ret.std() * np.sqrt(252 * (len(df) / 10 if len(df) > 10 else 1))) * 100, 2)

    # Bollinger Band width for squeeze detection
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    bb_width = ((sma20 + 2 * std20) - (sma20 - 2 * std20)) / sma20
    c_bb_w = float(bb_width.iloc[-1]) if not bb_width.empty and not pd.isna(bb_width.iloc[-1]) else 0.0
    min_bb_w = float(bb_width.tail(20).min()) if len(bb_width) >= 20 else c_bb_w

    if c_bb_w <= min_bb_w * 1.05 and c_atr <= p_atr:
        regime = "VOLATILITY_SQUEEZE"
        state = "Volatility Compression: Tight range contracting; potential explosive breakout pending"
    elif c_atr > p_atr * 1.2:
        regime = "VOLATILITY_EXPANSION"
        state = "Volatility Expansion: Range widening aggressively"
    else:
        regime = "NORMAL_VOLATILITY"
        state = "Stable Volatility Regime"

    summary = f"ATR(14): {c_atr} ({atr_pct}% of price). {state}."

    return {
        "atr": c_atr,
        "atr_pct": atr_pct,
        "realized_vol": realized_vol,
        "regime": regime,
        "state": state,
        "summary": summary,
    }
