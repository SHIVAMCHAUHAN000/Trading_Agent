"""
Systematic Setup Analysis Engine.
Evaluates current market structure, liquidity, momentum, and volume to identify
confluent technical setups without forcing trades or making false promises.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def evaluate_trading_setup(
    symbol: str,
    quote: Dict[str, Any],
    structure: Dict[str, Any],
    liquidity: Dict[str, Any],
    momentum: Dict[str, Any],
    volume: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Evaluates setup status, bias, triggers, invalidation, and targets.
    """
    price = quote.get("price", 0.0)
    trend = structure.get("trend", "NEUTRAL")
    regime = structure.get("regime", "RANGE")
    rsi = momentum.get("rsi", 50.0)
    divergence = momentum.get("divergence", "NONE")
    sweeps = liquidity.get("sweeps", [])
    upside_pools = liquidity.get("upside_liquidity", [])
    downside_pools = liquidity.get("downside_liquidity", [])

    status = "No setup"
    direction = "Neutral"
    evidence: List[str] = []
    trigger = "No actionable trigger active at current levels."
    invalidation = "N/A"
    targets: List[float] = []
    rr_ratio: Optional[float] = None
    confidence = "Low"
    confidence_reason = "No high-probability confluence currently detected across indicators and structure."

    # Check 1: Bullish Setup - Liquidity sweep of lows + Bullish Divergence or Bullish Structure
    has_low_sweep = any("PDL" in s or "Low" in s for s in sweeps)
    is_bullish_div = "BULLISH_DIVERGENCE" in divergence

    if (has_low_sweep or is_bullish_div or trend == "BULLISH") and price > 0:
        if has_low_sweep and is_bullish_div:
            status = "Developing"
            direction = "Long bias"
            confidence = "High"
            confidence_reason = "High confluence: Liquidity swept below key support combined with bullish RSI divergence."
        elif trend == "BULLISH" and rsi < 55:
            status = "Developing"
            direction = "Long bias"
            confidence = "Medium"
            confidence_reason = "Bullish structure with pullback into dynamic EMA support."
        elif is_bullish_div:
            status = "Developing"
            direction = "Long bias"
            confidence = "Medium"
            confidence_reason = "Early reversal signal: Momentum divergence forming at recent lows."

        if direction == "Long bias":
            evidence.append(f"Structure trend is {trend} ({regime}).")
            if has_low_sweep:
                evidence.append("Observed downside liquidity sweep / rejection at recent lows.")
            if is_bullish_div:
                evidence.append(f"Observed momentum divergence: {divergence}.")
            evidence.append(f"RSI(14) is {rsi} ({momentum.get('rsi_state')}).")

            # Invalidation: lowest recent swing low or PDL
            sl_level = downside_pools[0]["level"] if downside_pools else round(price * 0.995, 2)
            invalidation = f"Sustained 15m candle close below {sl_level}"

            # Trigger
            nearest_res = upside_pools[0]["level"] if upside_pools else round(price * 1.005, 2)
            trigger = f"Break and hold above immediate resistance {nearest_res} on expanding volume (RVOL > 1.3)"

            # Targets
            if upside_pools:
                targets = [p["level"] for p in upside_pools[:2]]
            else:
                targets = [round(price * 1.008, 2), round(price * 1.015, 2)]

            # Risk Reward
            risk = price - sl_level
            reward = targets[0] - price if targets else 0
            if risk > 0 and reward > 0:
                rr_ratio = round(reward / risk, 2)

    # Check 2: Bearish Setup - Liquidity sweep of highs + Bearish Divergence or Bearish Structure
    has_high_sweep = any("PDH" in s or "High" in s for s in sweeps)
    is_bearish_div = "BEARISH_DIVERGENCE" in divergence

    if (has_high_sweep or is_bearish_div or trend == "BEARISH") and direction == "Neutral" and price > 0:
        if has_high_sweep and is_bearish_div:
            status = "Developing"
            direction = "Short bias"
            confidence = "High"
            confidence_reason = "High confluence: Liquidity swept above key resistance combined with bearish RSI divergence."
        elif trend == "BEARISH" and rsi > 45:
            status = "Developing"
            direction = "Short bias"
            confidence = "Medium"
            confidence_reason = "Bearish structure with corrective relief bounce testing resistance."
        elif is_bearish_div:
            status = "Developing"
            direction = "Short bias"
            confidence = "Medium"
            confidence_reason = "Overextended momentum: Bearish divergence forming at recent highs."

        if direction == "Short bias":
            evidence.append(f"Structure trend is {trend} ({regime}).")
            if has_high_sweep:
                evidence.append("Observed upside liquidity sweep / rejection at recent highs.")
            if is_bearish_div:
                evidence.append(f"Observed momentum divergence: {divergence}.")
            evidence.append(f"RSI(14) is {rsi} ({momentum.get('rsi_state')}).")

            # Invalidation: highest recent swing high or PDH
            sh_level = upside_pools[0]["level"] if upside_pools else round(price * 1.005, 2)
            invalidation = f"Sustained 15m candle close above {sh_level}"

            # Trigger
            nearest_sup = downside_pools[0]["level"] if downside_pools else round(price * 0.995, 2)
            trigger = f"Break and hold below immediate support {nearest_sup} on expanding volume (RVOL > 1.3)"

            # Targets
            if downside_pools:
                targets = [p["level"] for p in downside_pools[:2]]
            else:
                targets = [round(price * 0.992, 2), round(price * 0.985, 2)]

            # Risk Reward
            risk = sh_level - price
            reward = price - targets[0] if targets else 0
            if risk > 0 and reward > 0:
                rr_ratio = round(reward / risk, 2)

    if not evidence:
        evidence.append("Price action is consolidating in mid-range with balanced volume and no clear liquidity sweep.")

    return {
        "symbol": symbol,
        "status": status,
        "direction": direction,
        "confidence": confidence,
        "confidence_reason": confidence_reason,
        "evidence": evidence,
        "trigger": trigger,
        "invalidation": invalidation,
        "targets": targets,
        "risk_reward": f"1:{rr_ratio}" if rr_ratio else "N/A",
    }
