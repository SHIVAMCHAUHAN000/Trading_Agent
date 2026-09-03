"""
Quantitative Volume Analysis Engine.
Calculates Relative Volume (RVOL), volume spikes, volume-price relationship,
and volume divergence.
"""

from __future__ import annotations

from typing import Any, Dict
import pandas as pd


def analyze_volume(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyzes volume characteristics, RVOL, volume expansion/contraction,
    and volume-price confirmation.
    """
    if df.empty or "volume" not in df.columns or len(df) < 5:
        return {
            "current_volume": 0,
            "rvol": 1.0,
            "state": "NO_VOLUME_DATA",
            "spike": False,
            "price_volume_relation": "Volume unavailable for this instrument/timeframe",
            "summary": "Volume data unavailable or not provided by exchange for cash index.",
        }

    vol = df["volume"]
    total_vol = vol.sum()

    # Cash index check: If volume is 0 for entire series (common for cash indices like ^NSEI)
    if total_vol == 0:
        return {
            "current_volume": 0,
            "rvol": 1.0,
            "state": "INDEX_NO_VOLUME",
            "spike": False,
            "price_volume_relation": "Cash index lacks direct volume (refer to derivative futures for order flow)",
            "summary": "Cash index lacks direct trading volume; derived volume analysis applies to futures/equities.",
        }

    c_vol = float(vol.iloc[-1])
    vol_sma20 = float(vol.tail(20).mean()) if len(vol) >= 20 else float(vol.mean())
    rvol = round(c_vol / vol_sma20, 2) if vol_sma20 > 0 else 1.0

    # Volume spike detection
    is_spike = rvol >= 2.0
    if rvol >= 2.0:
        state = "CLIMACTIC_VOLUME_SPIKE"
    elif rvol >= 1.3:
        state = "ABOVE_AVERAGE_EXPANSION"
    elif rvol <= 0.7:
        state = "VOLUME_CONTRACTION"
    else:
        state = "AVERAGE_VOLUME"

    # Price-Volume analysis
    close = df["close"]
    price_chg = float(close.iloc[-1] - close.iloc[-2]) if len(close) > 1 else 0.0

    if price_chg > 0 and rvol >= 1.2:
        pv_relation = "Bullish Accumulation: Price advancing on expanding volume"
    elif price_chg > 0 and rvol < 0.8:
        pv_relation = "Weak Advance: Price advancing on declining volume (Volume Divergence)"
    elif price_chg < 0 and rvol >= 1.2:
        pv_relation = "Institutional Distribution: Price falling on heavy volume"
    elif price_chg < 0 and rvol < 0.8:
        pv_relation = "Low-Volume Pullback: Price dipping on light volume (Lack of aggressive sellers)"
    else:
        pv_relation = "Neutral price-volume relationship"

    summary = f"RVOL: {rvol}x ({state}). {pv_relation}."

    return {
        "current_volume": int(c_vol),
        "vol_sma20": int(vol_sma20),
        "rvol": rvol,
        "state": state,
        "spike": is_spike,
        "price_volume_relation": pv_relation,
        "summary": summary,
    }
