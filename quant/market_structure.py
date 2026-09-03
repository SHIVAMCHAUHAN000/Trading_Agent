"""
Quantitative Market Structure Analysis Engine.
Detects swing highs/lows, trend/range regimes, Break of Structure (BOS),
Change of Character (CHoCH), and level reclaims/losses.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


@dataclass
class SwingPoint:
    index: int
    timestamp: str
    price: float
    type: str  # 'HIGH' or 'LOW'


def identify_swings(df: pd.DataFrame, lookback: int = 3) -> Tuple[List[SwingPoint], List[SwingPoint]]:
    """
    Identifies fractal swing highs and swing lows.
    A swing high is a high greater than `lookback` candles to the left and right.
    """
    if len(df) < lookback * 2 + 1:
        return [], []

    highs = df["high"].values
    lows = df["low"].values
    timestamps = [str(ts) for ts in df.index]

    swing_highs: List[SwingPoint] = []
    swing_lows: List[SwingPoint] = []

    for i in range(lookback, len(df) - lookback):
        # Check swing high
        is_high = True
        for j in range(1, lookback + 1):
            if highs[i] <= highs[i - j] or highs[i] < highs[i + j]:
                is_high = False
                break
        if is_high:
            swing_highs.append(SwingPoint(i, timestamps[i], round(float(highs[i]), 2), "HIGH"))

        # Check swing low
        is_low = True
        for j in range(1, lookback + 1):
            if lows[i] >= lows[i - j] or lows[i] > lows[i + j]:
                is_low = False
                break
        if is_low:
            swing_lows.append(SwingPoint(i, timestamps[i], round(float(lows[i]), 2), "LOW"))

    return swing_highs, swing_lows


def analyze_market_structure(df: pd.DataFrame, lookback: int = 3) -> Dict[str, Any]:
    """
    Analyzes market structure (HH/HL/LH/LL, BOS, CHoCH, trend vs range).
    """
    if df.empty or len(df) < 10:
        return {
            "regime": "INSUFFICIENT_DATA",
            "trend": "NEUTRAL",
            "structure": "Insufficient candles for structural analysis",
            "swing_highs": [],
            "swing_lows": [],
            "key_events": [],
            "last_swing_high": None,
            "last_swing_low": None,
        }

    current_price = float(df["close"].iloc[-1])
    swing_highs, swing_lows = identify_swings(df, lookback=lookback)

    # If few swings found with lookback=3, try lookback=2
    if (len(swing_highs) < 2 or len(swing_lows) < 2) and len(df) >= 7:
        swing_highs, swing_lows = identify_swings(df, lookback=2)

    last_sh = swing_highs[-1].price if swing_highs else round(float(df["high"].max()), 2)
    last_sl = swing_lows[-1].price if swing_lows else round(float(df["low"].min()), 2)
    prev_sh = swing_highs[-2].price if len(swing_highs) >= 2 else last_sh
    prev_sl = swing_lows[-2].price if len(swing_lows) >= 2 else last_sl

    key_events = []
    regime = "RANGE"
    trend = "NEUTRAL"

    # Analyze sequence
    is_higher_high = last_sh > prev_sh * 1.0005
    is_lower_high = last_sh < prev_sh * 0.9995
    is_higher_low = last_sl > prev_sl * 1.0005
    is_lower_low = last_sl < prev_sl * 0.9995

    # Break of Structure / Change of Character detection
    if current_price > last_sh:
        key_events.append(f"Bullish Breakout / BOS above recent swing high ({last_sh})")
    elif current_price < last_sl:
        key_events.append(f"Bearish Breakdown / BOS below recent swing low ({last_sl})")

    if is_higher_high and is_higher_low:
        regime = "TRENDING_BULLISH"
        trend = "BULLISH"
        structure_desc = f"Bullish Market Structure (Higher High at {last_sh} and Higher Low at {last_sl})"
    elif is_lower_high and is_lower_low:
        regime = "TRENDING_BEARISH"
        trend = "BEARISH"
        structure_desc = f"Bearish Market Structure (Lower High at {last_sh} and Lower Low at {last_sl})"
    elif is_higher_high and is_lower_low:
        regime = "EXPANDING_RANGE"
        trend = "NEUTRAL / VOLATILE"
        structure_desc = f"Broadening Structure (Expanding swings: HH {last_sh}, LL {last_sl})"
    else:
        regime = "CONSOLIDATION_RANGE"
        trend = "NEUTRAL"
        structure_desc = f"Consolidation / Range-bound between support {last_sl} and resistance {last_sh}"

    # Check for potential failed breakout
    recent_high = float(df["high"].tail(5).max())
    if recent_high > last_sh and current_price < last_sh:
        key_events.append(f"Potential Failed Breakout above {last_sh} (wick rejection back inside)")

    recent_low = float(df["low"].tail(5).min())
    if recent_low < last_sl and current_price > last_sl:
        key_events.append(f"Potential Liquidity Sweep / Spring below {last_sl} (reclaimed inside)")

    return {
        "regime": regime,
        "trend": trend,
        "structure": structure_desc,
        "current_price": round(current_price, 2),
        "last_swing_high": last_sh,
        "last_swing_low": last_sl,
        "prev_swing_high": prev_sh,
        "prev_swing_low": prev_sl,
        "swing_highs": [{"price": s.price, "timestamp": s.timestamp} for s in swing_highs[-4:]],
        "swing_lows": [{"price": s.price, "timestamp": s.timestamp} for s in swing_lows[-4:]],
        "key_events": key_events,
    }
