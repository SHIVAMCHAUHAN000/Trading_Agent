"""
Quantitative Momentum Analysis Engine.
Calculates RSI(14), MACD(12,26,9), Rate of Change (ROC), EMA ribbon alignments,
acceleration/deceleration, and regular/hidden momentum divergences.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Computes Wilder's RSI."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)


def compute_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
    """Computes MACD line, signal line, and histogram."""
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return {"macd": macd_line, "signal": signal_line, "hist": hist}


def analyze_momentum(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes comprehensive quantitative momentum indicators and signals.
    """
    if df.empty or len(df) < 14:
        return {
            "rsi": 50.0,
            "rsi_state": "NEUTRAL",
            "macd": {"line": 0.0, "signal": 0.0, "hist": 0.0, "state": "NEUTRAL"},
            "roc_14": 0.0,
            "acceleration": "FLAT",
            "divergence": "NONE",
            "summary": "Insufficient candles for momentum analysis.",
        }

    close = df["close"]
    rsi_series = compute_rsi(close, period=14)
    current_rsi = round(float(rsi_series.iloc[-1]), 2)
    prev_rsi = round(float(rsi_series.iloc[-2]), 2) if len(rsi_series) > 1 else current_rsi

    # RSI State
    if current_rsi >= 70:
        rsi_state = "OVERBOUGHT"
    elif current_rsi <= 30:
        rsi_state = "OVERSOLD"
    elif current_rsi > 55:
        rsi_state = "BULLISH_MOMENTUM"
    elif current_rsi < 45:
        rsi_state = "BEARISH_MOMENTUM"
    else:
        rsi_state = "NEUTRAL"

    # MACD
    macd_res = compute_macd(close)
    c_macd = round(float(macd_res["macd"].iloc[-1]), 2)
    c_sig = round(float(macd_res["signal"].iloc[-1]), 2)
    c_hist = round(float(macd_res["hist"].iloc[-1]), 2)
    p_hist = round(float(macd_res["hist"].iloc[-2]), 2) if len(macd_res["hist"]) > 1 else c_hist

    if c_hist > 0 and c_hist > p_hist:
        macd_state = "BULLISH_EXPANSION"
        accel = "ACCELERATING_UP"
    elif c_hist > 0 and c_hist <= p_hist:
        macd_state = "BULLISH_DECELERATION"
        accel = "DECELERATING_UP"
    elif c_hist < 0 and c_hist < p_hist:
        macd_state = "BEARISH_EXPANSION"
        accel = "ACCELERATING_DOWN"
    elif c_hist < 0 and c_hist >= p_hist:
        macd_state = "BEARISH_DECELERATION"
        accel = "DECELERATING_DOWN"
    else:
        macd_state = "NEUTRAL"
        accel = "FLAT"

    # Rate of Change (14 periods)
    roc_14 = round(float(((close.iloc[-1] - close.iloc[-14]) / close.iloc[-14]) * 100), 2)

    # EMAs
    ema_9 = round(float(close.ewm(span=9, adjust=False).mean().iloc[-1]), 2)
    ema_21 = round(float(close.ewm(span=21, adjust=False).mean().iloc[-1]), 2)
    ema_50 = round(float(close.ewm(span=50, adjust=False).mean().iloc[-1]), 2) if len(close) >= 50 else None

    ema_alignment = "MIXED"
    if ema_9 > ema_21 and (ema_50 is None or ema_21 > ema_50):
        ema_alignment = "BULLISH_STACK (9 > 21 > 50)"
    elif ema_9 < ema_21 and (ema_50 is None or ema_21 < ema_50):
        ema_alignment = "BEARISH_STACK (9 < 21 < 50)"

    # Divergence check across last 15 candles
    divergence = "NONE"
    if len(close) >= 15:
        sub_price = close.tail(15)
        sub_rsi = rsi_series.tail(15)
        p_now = sub_price.iloc[-1]
        p_min = sub_price.min()
        p_max = sub_price.max()
        rsi_now = sub_rsi.iloc[-1]
        rsi_min = sub_rsi.min()
        rsi_max = sub_rsi.max()

        # Regular Bullish Divergence: Price making lower low while RSI makes higher low
        if p_now <= p_min * 1.002 and rsi_now > rsi_min + 3.0:
            divergence = "BULLISH_DIVERGENCE (Lower Price Low vs Higher RSI Low)"
        # Regular Bearish Divergence: Price making higher high while RSI makes lower high
        elif p_now >= p_max * 0.998 and rsi_now < rsi_max - 3.0:
            divergence = "BEARISH_DIVERGENCE (Higher Price High vs Lower RSI High)"

    summary = (
        f"RSI(14): {current_rsi} ({rsi_state}), MACD Hist: {c_hist} ({accel}), "
        f"EMA Alignment: {ema_alignment}."
    )
    if divergence != "NONE":
        summary += f" Detected {divergence}."

    return {
        "rsi": current_rsi,
        "rsi_state": rsi_state,
        "macd": {
            "macd": c_macd,
            "signal": c_sig,
            "hist": c_hist,
            "state": macd_state,
        },
        "acceleration": accel,
        "roc_14": roc_14,
        "ema_9": ema_9,
        "ema_21": ema_21,
        "ema_50": ema_50,
        "ema_alignment": ema_alignment,
        "divergence": divergence,
        "summary": summary,
    }
