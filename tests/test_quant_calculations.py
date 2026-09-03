"""
Unit tests for Quantitative Engine calculations:
Market structure, liquidity pools, momentum, volume, volatility, session awareness, and freshness.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

from quant.market_structure import identify_swings, analyze_market_structure
from quant.liquidity import find_equal_levels, analyze_liquidity
from quant.momentum import compute_rsi, compute_macd, analyze_momentum
from quant.volume import analyze_volume
from quant.volatility import compute_atr, analyze_volatility
from quant.session import get_market_session_info, SessionState, IST
from live_data.freshness import evaluate_data_freshness, FreshnessStatus


def create_synthetic_df(trend: str = "bullish", length: int = 50) -> pd.DataFrame:
    """Creates synthetic OHLCV data for testing."""
    times = [datetime(2026, 9, 3, 9, 15, tzinfo=IST) + timedelta(minutes=15 * i) for i in range(length)]
    base_price = 24000.0

    prices = []
    current = base_price
    for i in range(length):
        if trend == "bullish":
            delta = 10.0 + np.sin(i / 2) * 5.0
        elif trend == "bearish":
            delta = -10.0 + np.sin(i / 2) * 5.0
        else:
            delta = np.sin(i / 2) * 15.0
        current += delta
        prices.append(current)

    data = []
    for p in prices:
        high = p + 15.0
        low = p - 12.0
        open_p = p - 5.0
        close_p = p
        vol = 100000 + int(np.random.randint(1000, 50000))
        data.append({"open": open_p, "high": high, "low": low, "close": close_p, "volume": vol})

    df = pd.DataFrame(data, index=times)
    return df


def test_swing_identification():
    df = create_synthetic_df(trend="bullish", length=40)
    sh, sl = identify_swings(df, lookback=2)
    assert isinstance(sh, list)
    assert isinstance(sl, list)
    if sh:
        assert sh[0].type == "HIGH"
    if sl:
        assert sl[0].type == "LOW"


def test_market_structure_bullish():
    df = create_synthetic_df(trend="bullish", length=40)
    res = analyze_market_structure(df)
    assert "regime" in res
    assert "trend" in res
    assert res["current_price"] > 24000.0


def test_market_structure_bearish():
    df = create_synthetic_df(trend="bearish", length=40)
    res = analyze_market_structure(df)
    assert "regime" in res
    assert "trend" in res


def test_liquidity_analysis():
    df = create_synthetic_df(trend="bullish", length=30)
    daily_df = create_synthetic_df(trend="bullish", length=10)
    res = analyze_liquidity(df, daily_df)
    assert "session_levels" in res
    assert "upside_liquidity" in res
    assert "downside_liquidity" in res
    assert res["session_levels"]["session_high"] is not None
    assert res["session_levels"]["session_low"] is not None


def test_momentum_rsi_and_macd():
    df = create_synthetic_df(trend="bullish", length=35)
    res = analyze_momentum(df)
    assert "rsi" in res
    assert 0.0 <= res["rsi"] <= 100.0
    assert "macd" in res
    assert "acceleration" in res


def test_volume_analysis():
    df = create_synthetic_df(trend="bullish", length=30)
    res = analyze_volume(df)
    assert "rvol" in res
    assert res["rvol"] > 0
    assert "state" in res


def test_volatility_analysis():
    df = create_synthetic_df(trend="bullish", length=30)
    res = analyze_volatility(df)
    assert "atr" in res
    assert res["atr"] > 0
    assert "regime" in res


def test_session_awareness():
    info_nifty = get_market_session_info("NIFTY")
    assert "session_state" in info_nifty
    assert "status_description" in info_nifty

    info_btc = get_market_session_info("BTC")
    assert info_btc["is_open"] is True
    assert info_btc["session_state"] == SessionState.OPEN.value


def test_freshness_evaluation():
    now_utc = datetime.now(timezone.utc)
    fresh = evaluate_data_freshness("BTC", now_utc)
    assert fresh["status"] == FreshnessStatus.LIVE
    assert fresh["is_usable"] is True

    none_eval = evaluate_data_freshness("NIFTY", None)
    assert none_eval["status"] == FreshnessStatus.UNAVAILABLE
    assert "Market data unavailable from the connected source" in none_eval["disclaimer"]
