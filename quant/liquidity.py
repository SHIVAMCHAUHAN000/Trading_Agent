"""
Quantitative Liquidity Analysis Engine.
Calculates observable structural levels where liquidity (stop orders, breakout orders) pools:
PDH, PDL, PWH, PWL, Session High/Low, Equal Highs (EQH), Equal Lows (EQL), and Liquidity Sweeps.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np
from quant.market_structure import identify_swings


def find_equal_levels(prices: List[float], tolerance_pct: float = 0.0015) -> List[Dict[str, Any]]:
    """Identifies clusters of swing points at nearly equal prices (EQH or EQL)."""
    if len(prices) < 2:
        return []

    clusters = []
    sorted_p = sorted(prices)
    current_cluster = [sorted_p[0]]

    for p in sorted_p[1:]:
        if (p - current_cluster[-1]) / current_cluster[-1] <= tolerance_pct:
            current_cluster.append(p)
        else:
            if len(current_cluster) >= 2:
                clusters.append({
                    "avg_level": round(float(np.mean(current_cluster)), 2),
                    "touch_count": len(current_cluster),
                    "levels": current_cluster,
                })
            current_cluster = [p]

    if len(current_cluster) >= 2:
        clusters.append({
            "avg_level": round(float(np.mean(current_cluster)), 2),
            "touch_count": len(current_cluster),
            "levels": current_cluster,
        })
    return clusters


def analyze_liquidity(
    intraday_df: pd.DataFrame,
    daily_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """
    Computes observable liquidity zones, session levels, and potential stop-run areas.
    """
    if intraday_df.empty:
        return {
            "upside_liquidity": [],
            "downside_liquidity": [],
            "session_levels": {},
            "sweeps": [],
            "summary": "Insufficient intraday data for liquidity analysis.",
        }

    current_price = float(intraday_df["close"].iloc[-1])

    # 1. Current Session High & Low
    session_high = round(float(intraday_df["high"].max()), 2)
    session_low = round(float(intraday_df["low"].min()), 2)

    # 2. Daily Reference Levels (PDH, PDL, PWH, PWL)
    pdh, pdl, pwh, pwl = None, None, None, None
    if daily_df is not None and len(daily_df) >= 2:
        prev_day = daily_df.iloc[-2]
        pdh = round(float(prev_day["high"]), 2)
        pdl = round(float(prev_day["low"]), 2)
        if len(daily_df) >= 6:
            prev_week = daily_df.tail(6).head(5)
            pwh = round(float(prev_week["high"].max()), 2)
            pwl = round(float(prev_week["low"].min()), 2)

    # 3. Swing levels and Equal Highs/Lows
    shs, sls = identify_swings(intraday_df, lookback=2)
    sh_prices = [s.price for s in shs]
    sl_prices = [s.price for s in sls]

    eq_highs = find_equal_levels(sh_prices)
    eq_lows = find_equal_levels(sl_prices)

    # 4. Upside Liquidity Concentrations (Resting above current price)
    upside_pools = []
    if pdh and pdh > current_price:
        upside_pools.append({
            "level": pdh,
            "type": "Previous Day High (PDH)",
            "description": "Observable buy-stop liquidity pool above previous day high",
            "distance_pct": round((pdh - current_price) / current_price * 100, 2),
        })
    if session_high > current_price:
        upside_pools.append({
            "level": session_high,
            "type": "Session High",
            "description": "Observable intraday liquidity pool above current session high",
            "distance_pct": round((session_high - current_price) / current_price * 100, 2),
        })
    for eqh in eq_highs:
        if eqh["avg_level"] > current_price:
            upside_pools.append({
                "level": eqh["avg_level"],
                "type": f"Equal Highs (EQH - {eqh['touch_count']} touches)",
                "description": "Likely stop liquidity concentration resting above repeated rejections",
                "distance_pct": round((eqh["avg_level"] - current_price) / current_price * 100, 2),
            })
    for sh in reversed(sh_prices):
        if sh > current_price and not any(abs(sh - p["level"]) / sh < 0.001 for p in upside_pools):
            upside_pools.append({
                "level": sh,
                "type": "Swing High",
                "description": "Potential liquidity area above recent structural swing high",
                "distance_pct": round((sh - current_price) / current_price * 100, 2),
            })
            if len(upside_pools) >= 3:
                break

    # Sort upside pools by price ascending (nearest first)
    upside_pools.sort(key=lambda x: x["level"])

    # 5. Downside Liquidity Concentrations (Resting below current price)
    downside_pools = []
    if pdl and pdl < current_price:
        downside_pools.append({
            "level": pdl,
            "type": "Previous Day Low (PDL)",
            "description": "Observable sell-stop liquidity pool below previous day low",
            "distance_pct": round((current_price - pdl) / current_price * 100, 2),
        })
    if session_low < current_price:
        downside_pools.append({
            "level": session_low,
            "type": "Session Low",
            "description": "Observable intraday liquidity pool below current session low",
            "distance_pct": round((current_price - session_low) / current_price * 100, 2),
        })
    for eql in eq_lows:
        if eql["avg_level"] < current_price:
            downside_pools.append({
                "level": eql["avg_level"],
                "type": f"Equal Lows (EQL - {eql['touch_count']} touches)",
                "description": "Likely stop liquidity concentration resting below repeated bounces",
                "distance_pct": round((current_price - eql["avg_level"]) / current_price * 100, 2),
            })
    for sl in reversed(sl_prices):
        if sl < current_price and not any(abs(sl - p["level"]) / sl < 0.001 for p in downside_pools):
            downside_pools.append({
                "level": sl,
                "type": "Swing Low",
                "description": "Potential liquidity area below recent structural swing low",
                "distance_pct": round((current_price - sl) / current_price * 100, 2),
            })
            if len(downside_pools) >= 3:
                break

    # Sort downside pools by price descending (nearest first)
    downside_pools.sort(key=lambda x: x["level"], reverse=True)

    # 6. Sweeps / Stop Runs in recent 5 candles
    sweeps = []
    recent = intraday_df.tail(5)
    for idx, row in recent.iterrows():
        c_high = float(row["high"])
        c_low = float(row["low"])
        c_close = float(row["close"])
        # High sweep
        if pdh and c_high > pdh and c_close < pdh:
            sweeps.append(f"Potential PDH Liquidity Sweep: Wick reached {round(c_high, 2)} above PDH {pdh} but closed back inside")
        # Low sweep
        if pdl and c_low < pdl and c_close > pdl:
            sweeps.append(f"Potential PDL Liquidity Sweep: Wick pierced {round(c_low, 2)} below PDL {pdl} but closed back inside")

    nearest_up = f"{upside_pools[0]['level']} ({upside_pools[0]['type']})" if upside_pools else "No immediate overhead levels"
    nearest_down = f"{downside_pools[0]['level']} ({downside_pools[0]['type']})" if downside_pools else "No immediate downside levels"

    summary = (
        f"Nearest potential upside liquidity concentration: {nearest_up}. "
        f"Nearest potential downside liquidity concentration: {nearest_down}."
    )

    return {
        "current_price": round(current_price, 2),
        "session_levels": {
            "session_high": session_high,
            "session_low": session_low,
            "pdh": pdh,
            "pdl": pdl,
            "pwh": pwh,
            "pwl": pwl,
        },
        "upside_liquidity": upside_pools[:4],
        "downside_liquidity": downside_pools[:4],
        "equal_highs": eq_highs,
        "equal_lows": eq_lows,
        "sweeps": sweeps,
        "summary": summary,
    }
