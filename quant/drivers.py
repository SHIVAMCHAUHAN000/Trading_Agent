"""
Market-Driver Quantitative Investigation Engine.
Separates findings into:
- OBSERVED: Factual, verifiable numbers and price action.
- INFERRED: Probabilistic transmission mechanisms and likely catalysts.
- UNKNOWN: Unverified drivers, pending news, or missing data.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def analyze_market_drivers(
    symbol: str,
    quote: Dict[str, Any],
    structure: Dict[str, Any],
    momentum: Dict[str, Any],
    volume: Dict[str, Any],
    volatility: Dict[str, Any],
    breadth: Optional[Dict[str, Any]] = None,
    macro: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Constructs an evidence-grounded driver breakdown:
    OBSERVED vs INFERRED vs UNKNOWN.
    """
    price = quote.get("price", 0.0)
    change_pct = quote.get("change_pct", 0.0)
    currency = quote.get("currency", "INR")

    observed: List[str] = []
    inferred: List[str] = []
    unknown: List[str] = []

    # 1. Direct Observed Price Action & Structure
    direction_word = "up" if change_pct > 0 else ("down" if change_pct < 0 else "unchanged")
    observed.append(f"{symbol} is trading at {price} {currency}, {direction_word} {abs(change_pct)}% for the session.")

    if structure.get("key_events"):
        for event in structure["key_events"]:
            observed.append(f"Structure Event: {event}")
    else:
        observed.append(f"Structure Regime: {structure.get('regime')} with trend classified as {structure.get('trend')}.")

    # Volume & Volatility Observation
    observed.append(f"Volume behavior: RVOL is {volume.get('rvol')}x ({volume.get('state')}).")
    observed.append(f"Volatility regime: ATR is {volatility.get('atr')} ({volatility.get('regime')}).")

    # 2. Sector and Component Breadth Observation
    if breadth and "sample_stocks" in breadth:
        observed.append(
            f"Market Breadth: {breadth.get('advances')} advances vs {breadth.get('declines')} declines "
            f"(A/D Ratio: {breadth.get('adv_dec_ratio')})."
        )
        # Check heavyweights
        heavyweights = [s for s in breadth["sample_stocks"] if s["symbol"] in ("RELIANCE", "HDFCBANK", "ICICIBANK")]
        if heavyweights:
            hw_str = ", ".join([f"{h['symbol']}: {h['change_pct']}%" for h in heavyweights])
            observed.append(f"Key Heavyweights: {hw_str}.")

    # 3. Macro Observations
    if macro and "macro_assets" in macro:
        assets = macro["macro_assets"]
        macro_points = []
        if "USDINR" in assets:
            macro_points.append(f"USD/INR at {assets['USDINR']['price']} ({assets['USDINR']['change_pct']}%)")
        if "CRUDEOIL" in assets:
            macro_points.append(f"Crude Oil at ${assets['CRUDEOIL']['price']} ({assets['CRUDEOIL']['change_pct']}%)")
        if "GOLD" in assets:
            macro_points.append(f"Gold at ${assets['GOLD']['price']} ({assets['GOLD']['change_pct']}%)")
        if "INDIAVIX" in assets:
            macro_points.append(f"India VIX at {assets['INDIAVIX']['price']} ({assets['INDIAVIX']['change_pct']}%)")
        if macro_points:
            observed.append(f"Macro context: {'; '.join(macro_points)}.")

    # 4. Inferred Mechanisms (Hypotheses grounded in observed correlations)
    if change_pct < -0.4:
        if breadth and breadth.get("declines", 0) > breadth.get("advances", 0):
            inferred.append(
                "Broad-based institutional distribution across major benchmark components rather than an isolated stock-specific drop."
            )
        if macro and "USDINR" in macro.get("macro_assets", {}):
            usdinr_chg = macro["macro_assets"]["USDINR"]["change_pct"]
            if usdinr_chg > 0.2:
                inferred.append("Currency pressure from a strengthening USD/INR is likely creating headwind for domestic equities.")
        if macro and "CRUDEOIL" in macro.get("macro_assets", {}):
            crude_chg = macro["macro_assets"]["CRUDEOIL"]["change_pct"]
            if crude_chg > 1.5:
                inferred.append("Rising crude prices may be putting pressure on Indian fiscal balance and import-heavy sectors.")
    elif change_pct > 0.4:
        if breadth and breadth.get("advances", 0) > breadth.get("declines", 0):
            inferred.append("Widespread buying participation with positive market breadth validating the rally.")
        if momentum.get("rsi", 50) > 60:
            inferred.append("Strong momentum expansion driving short covering above key resistance levels.")
    else:
        inferred.append("Consolidation inside established range; market participants awaiting new directional macro triggers.")

    # 5. Unknowns (What cannot be confirmed without specific news or order book depth)
    unknown.append("Specific proprietary institutional order book depth and block-deal motivations are unobservable via public feeds.")
    unknown.append("Breaking unscheduled corporate disclosures or geopolitical headlines in the last 15 minutes cannot be verified without real-time news wire access.")
    unknown.append("Exact options dealer gamma positioning thresholds cannot be definitively confirmed without full tick-level NSE derivatives feed.")

    return {
        "symbol": symbol,
        "observed": observed,
        "inferred": inferred,
        "unknown": unknown,
    }
