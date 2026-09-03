"""
Multi-Timeframe (MTF) Quantitative Synthesis Engine.
Coordinates analysis across 1m, 5m, 15m, 1h, and Daily timeframes.
Reconciles higher-timeframe context with lower-timeframe tactical execution.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
import pandas as pd

from quant.market_structure import analyze_market_structure
from quant.momentum import analyze_momentum
from quant.volatility import analyze_volatility
from quant.volume import analyze_volume


async def analyze_multi_timeframe(
    symbol: str,
    candles_dict: Dict[str, pd.DataFrame],
) -> Dict[str, Any]:
    """
    Synthesizes multi-timeframe analysis across available timeframes.
    `candles_dict` is a mapping of timeframe string (e.g. '5m', '15m', '1h', '1d') to pd.DataFrame.
    """
    results: Dict[str, Dict[str, Any]] = {}

    for tf, df in candles_dict.items():
        if df.empty or len(df) < 5:
            continue
        ms = analyze_market_structure(df)
        mom = analyze_momentum(df)
        volat = analyze_volatility(df)
        volum = analyze_volume(df)

        results[tf] = {
            "trend": ms["trend"],
            "regime": ms["regime"],
            "structure_desc": ms["structure"],
            "rsi": mom["rsi"],
            "rsi_state": mom["rsi_state"],
            "ema_alignment": mom["ema_alignment"],
            "atr": volat["atr"],
            "volatility_regime": volat["regime"],
            "rvol": volum["rvol"],
        }

    # Identify primary HTF (Daily or 1h) and primary LTF (15m or 5m)
    htf_key = "1d" if "1d" in results else ("1h" if "1h" in results else None)
    ltf_key = "15m" if "15m" in results else ("5m" if "5m" in results else None)

    htf_trend = results[htf_key]["trend"] if htf_key else "UNKNOWN"
    ltf_trend = results[ltf_key]["trend"] if ltf_key else "UNKNOWN"

    conflict_explanation = ""
    overall_bias = "NEUTRAL"

    if htf_trend == "BULLISH" and ltf_trend == "BULLISH":
        overall_bias = "STRONG_BULLISH"
        conflict_explanation = "Complete multi-timeframe trend alignment: Both HTF and LTF are in bullish structures."
    elif htf_trend == "BEARISH" and ltf_trend == "BEARISH":
        overall_bias = "STRONG_BEARISH"
        conflict_explanation = "Complete multi-timeframe trend alignment: Both HTF and LTF are in bearish structures."
    elif htf_trend == "BULLISH" and ltf_trend == "BEARISH":
        overall_bias = "TACTICAL_PULLBACK_IN_BULL_TREND"
        conflict_explanation = (
            f"Daily/HTF trend is bullish, while the {ltf_key} structure is bearish. "
            "Current evidence is more consistent with a short-term tactical pullback unless HTF support breaks."
        )
    elif htf_trend == "BEARISH" and ltf_trend == "BULLISH":
        overall_bias = "COUNTER_TREND_BOUNCE_IN_BEAR_TREND"
        conflict_explanation = (
            f"Daily/HTF trend is bearish, while the {ltf_key} structure is showing a tactical bullish bounce. "
            "Evidence suggests a relief rally into overhead resistance rather than a confirmed macro trend reversal."
        )
    else:
        overall_bias = "NEUTRAL_OR_RANGING"
        conflict_explanation = f"Mixed signals across timeframes. HTF is {htf_trend}, LTF is {ltf_trend}."

    matrix = {
        tf: {
            "trend": data["trend"],
            "regime": data["regime"],
            "rsi": data["rsi"],
            "rvol": data["rvol"],
        }
        for tf, data in results.items()
    }

    return {
        "symbol": symbol,
        "overall_bias": overall_bias,
        "htf_trend": htf_trend,
        "ltf_trend": ltf_trend,
        "conflict_explanation": conflict_explanation,
        "matrix": matrix,
        "timeframe_details": results,
    }
