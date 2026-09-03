"""
Market Data & Quant Analysis API Routes.
Exposes quotes, candles, market structure, liquidity zones, and watchlist.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from live_data import (
    market_data_provider,
    resolve_symbol,
    INSTRUMENTS,
)
from quant import (
    analyze_market_structure,
    analyze_liquidity,
    analyze_momentum,
    analyze_volume,
    analyze_volatility,
    analyze_multi_timeframe,
    evaluate_trading_setup,
    get_market_session_info,
)
from storage.repository import QuantBrainRepository

router = APIRouter(prefix="/api/v1/market", tags=["Market Data & Quant"])


@router.get("/summary")
async def get_market_summary():
    """Returns overview of primary tracked Indian & global instruments."""
    tracked_symbols = ["NIFTY", "BANKNIFTY", "GOLD", "SILVER", "CRUDEOIL", "BTC", "USDINR", "RELIANCE", "HDFCBANK"]
    quotes_tasks = [market_data_provider.get_quote(s) for s in tracked_symbols]
    quotes = await asyncio.gather(*quotes_tasks, return_exceptions=True)

    summary_list = []
    for s, q in zip(tracked_symbols, quotes):
        if isinstance(q, dict) and q.get("price") is not None:
            session = get_market_session_info(s)
            summary_list.append({
                "symbol": q["symbol"],
                "name": q["name"],
                "currency": q["currency"],
                "price": q["price"],
                "change": q["change"],
                "change_pct": q["change_pct"],
                "high": q["high"],
                "low": q["low"],
                "volume": q["volume"],
                "timestamp": q["timestamp"],
                "freshness": q["freshness"],
                "session_state": session["session_state"],
                "session_desc": session["status_description"],
            })

    breadth = await market_data_provider.get_market_breadth()
    return {
        "count": len(summary_list),
        "instruments": summary_list,
        "breadth": breadth,
    }


@router.get("/instrument/{symbol}")
async def get_instrument_analysis(symbol: str, timeframe: str = Query(default="15m")):
    """Full deep-dive quantitative analysis for an instrument."""
    canonical = resolve_symbol(symbol) or symbol.upper()
    quote = await market_data_provider.get_quote(canonical)
    if not quote or quote.get("price") is None:
        raise HTTPException(status_code=404, detail=f"Market data unavailable for {canonical}.")

    # Fetch 15m and Daily candles concurrently
    intraday_df = await market_data_provider.get_candles(canonical, interval=timeframe)
    daily_df = await market_data_provider.get_candles(canonical, interval="1d")

    structure = analyze_market_structure(intraday_df)
    liquidity = analyze_liquidity(intraday_df, daily_df)
    momentum = analyze_momentum(intraday_df)
    volume = analyze_volume(intraday_df)
    volatility = analyze_volatility(intraday_df)
    setup = evaluate_trading_setup(canonical, quote, structure, liquidity, momentum, volume)
    session_info = get_market_session_info(canonical)

    return {
        "symbol": canonical,
        "name": quote.get("name"),
        "timeframe": timeframe,
        "quote": quote,
        "session_info": session_info,
        "structure": structure,
        "liquidity": liquidity,
        "momentum": momentum,
        "volume": volume,
        "volatility": volatility,
        "setup": setup,
    }


@router.get("/candles/{symbol}")
async def get_candles(
    symbol: str,
    interval: str = Query(default="15m", pattern="^(1m|5m|15m|30m|1h|1d)$"),
    period: Optional[str] = Query(default=None),
):
    """Returns formatted candlestick data for charting."""
    canonical = resolve_symbol(symbol) or symbol.upper()
    df = await market_data_provider.get_candles(canonical, interval=interval, period=period)
    if df.empty:
        return {"symbol": canonical, "candles": [], "count": 0}

    candles = []
    for idx, row in df.iterrows():
        # Convert timestamp to unix seconds
        ts_sec = int(idx.timestamp()) if hasattr(idx, "timestamp") else 0
        candles.append({
            "time": ts_sec,
            "datetime": str(idx),
            "open": round(float(row["open"]), 2),
            "high": round(float(row["high"]), 2),
            "low": round(float(row["low"]), 2),
            "close": round(float(row["close"]), 2),
            "volume": int(row.get("volume", 0)),
        })

    return {
        "symbol": canonical,
        "interval": interval,
        "count": len(candles),
        "candles": candles,
    }


class WatchlistRequest(BaseModel):
    symbol: str


@router.get("/watchlist")
async def get_watchlist_data():
    """Returns watchlist with live metrics."""
    symbols = await QuantBrainRepository.get_watchlist()
    quotes_tasks = [market_data_provider.get_quote(s) for s in symbols]
    quotes = await asyncio.gather(*quotes_tasks, return_exceptions=True)

    items = []
    for s, q in zip(symbols, quotes):
        if isinstance(q, dict) and q.get("price") is not None:
            items.append(q)
        else:
            items.append({"symbol": s, "price": None, "change_pct": 0.0, "status": "Unavailable"})

    return {"watchlist": items}


@router.post("/watchlist")
async def add_to_watchlist(req: WatchlistRequest):
    """Add a symbol to the watchlist."""
    canonical = resolve_symbol(req.symbol) or req.symbol.upper()
    await QuantBrainRepository.add_to_watchlist(canonical)
    return {"message": f"Added {canonical} to watchlist", "symbol": canonical}


@router.delete("/watchlist/{symbol}")
async def remove_from_watchlist(symbol: str):
    """Remove a symbol from the watchlist."""
    canonical = resolve_symbol(symbol) or symbol.upper()
    await QuantBrainRepository.remove_from_watchlist(canonical)
    return {"message": f"Removed {canonical} from watchlist", "symbol": canonical}
