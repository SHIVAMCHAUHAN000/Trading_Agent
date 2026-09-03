"""
Core MCP Market Tools registered with the Quant Brain.
Exposes live market data, quantitative calculations, and TradingView signals.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
import yfinance as yf
import pandas as pd

from mcp_tools.registry import mcp_registry
from live_data import market_data_provider, resolve_symbol, INSTRUMENTS
from quant import (
    analyze_market_structure,
    analyze_liquidity,
    analyze_momentum,
    analyze_volume,
    analyze_volatility,
    analyze_multi_timeframe,
    analyze_market_drivers,
    evaluate_trading_setup,
    get_market_session_info,
)
from storage.repository import QuantBrainRepository


# Tool Handlers
async def handle_get_current_price(symbol: str) -> Dict[str, Any]:
    """Fetch current price, change, and freshness."""
    canonical = resolve_symbol(symbol) or symbol.upper()
    quote = await market_data_provider.get_quote(canonical)
    session_info = get_market_session_info(canonical)
    quote["session_info"] = session_info
    return quote


async def handle_get_historical_candles(
    symbol: str,
    interval: str = "15m",
    period: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetch candlestick data for charting or analysis."""
    canonical = resolve_symbol(symbol) or symbol.upper()
    df = await market_data_provider.get_candles(canonical, interval=interval, period=period)
    if df.empty:
        return {"symbol": canonical, "candles": [], "count": 0, "message": "No candle data returned"}

    candles = []
    for idx, row in df.iterrows():
        candles.append({
            "time": str(idx),
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


async def handle_get_market_structure(symbol: str, timeframe: str = "15m") -> Dict[str, Any]:
    """Analyze higher/lower swings, BOS, CHoCH, trend, and regime."""
    canonical = resolve_symbol(symbol) or symbol.upper()
    df = await market_data_provider.get_candles(canonical, interval=timeframe)
    res = analyze_market_structure(df)
    res["symbol"] = canonical
    res["timeframe"] = timeframe
    return res


async def handle_get_liquidity_zones(symbol: str, timeframe: str = "15m") -> Dict[str, Any]:
    """Calculate PDH, PDL, Session High/Low, Equal Highs/Lows, and resting liquidity pools."""
    canonical = resolve_symbol(symbol) or symbol.upper()
    intraday_df = await market_data_provider.get_candles(canonical, interval=timeframe)
    daily_df = await market_data_provider.get_candles(canonical, interval="1d")
    res = analyze_liquidity(intraday_df, daily_df)
    res["symbol"] = canonical
    res["timeframe"] = timeframe
    return res


async def handle_get_momentum_and_volume(symbol: str, timeframe: str = "15m") -> Dict[str, Any]:
    """Calculate RSI, MACD, EMAs, divergence, and RVOL."""
    canonical = resolve_symbol(symbol) or symbol.upper()
    df = await market_data_provider.get_candles(canonical, interval=timeframe)
    mom = analyze_momentum(df)
    vol = analyze_volume(df)
    return {
        "symbol": canonical,
        "timeframe": timeframe,
        "momentum": mom,
        "volume": vol,
    }


async def handle_get_volatility_metrics(symbol: str, timeframe: str = "15m") -> Dict[str, Any]:
    """Calculate ATR, realized volatility, and squeeze/expansion regime."""
    canonical = resolve_symbol(symbol) or symbol.upper()
    df = await market_data_provider.get_candles(canonical, interval=timeframe)
    res = analyze_volatility(df)
    res["symbol"] = canonical
    res["timeframe"] = timeframe
    return res


async def handle_get_multi_timeframe_analysis(symbol: str) -> Dict[str, Any]:
    """Fetch candles across 5m, 15m, 1h, and 1d to produce MTF synthesis."""
    canonical = resolve_symbol(symbol) or symbol.upper()
    timeframes = ["5m", "15m", "1h", "1d"]
    candles_tasks = [market_data_provider.get_candles(canonical, interval=tf) for tf in timeframes]
    dfs = await asyncio.gather(*candles_tasks)
    candles_dict = {tf: df for tf, df in zip(timeframes, dfs) if not df.empty}
    return await analyze_multi_timeframe(canonical, candles_dict)


async def handle_get_market_breadth() -> Dict[str, Any]:
    """Fetch advancing/declining metrics for top Indian components."""
    return await market_data_provider.get_market_breadth()


async def handle_get_macro_overview() -> Dict[str, Any]:
    """Fetch macro context: USDINR, Gold, Silver, Crude, SPX, India VIX."""
    return await market_data_provider.get_macro_overview()


async def handle_get_tradingview_signals(symbol: str) -> Dict[str, Any]:
    """Retrieve recent alerts received from TradingView webhooks for this symbol."""
    canonical = resolve_symbol(symbol) or symbol.upper()
    alerts = await QuantBrainRepository.get_recent_tv_alerts(symbol=canonical, limit=5)
    return {
        "symbol": canonical,
        "alerts_count": len(alerts),
        "recent_alerts": [
            {
                "alert_name": a.alert_name,
                "timeframe": a.timeframe,
                "signal": a.signal,
                "price": a.price,
                "indicator": a.indicator,
                "received_at": a.received_at.isoformat(),
            }
            for a in alerts
        ],
    }


async def handle_get_market_drivers(symbol: str) -> Dict[str, Any]:
    """Investigate potential drivers into OBSERVED vs INFERRED vs UNKNOWN."""
    canonical = resolve_symbol(symbol) or symbol.upper()
    quote = await market_data_provider.get_quote(canonical)
    df = await market_data_provider.get_candles(canonical, interval="15m")
    structure = analyze_market_structure(df)
    momentum = analyze_momentum(df)
    volume = analyze_volume(df)
    volatility = analyze_volatility(df)
    breadth = await market_data_provider.get_market_breadth()
    macro = await market_data_provider.get_macro_overview()

    return analyze_market_drivers(
        symbol=canonical,
        quote=quote,
        structure=structure,
        momentum=momentum,
        volume=volume,
        volatility=volatility,
        breadth=breadth,
        macro=macro,
    )


async def handle_get_trading_setup(symbol: str) -> Dict[str, Any]:
    """Systematically evaluate setup status, bias, trigger, invalidation, and targets."""
    canonical = resolve_symbol(symbol) or symbol.upper()
    quote = await market_data_provider.get_quote(canonical)
    intraday_df = await market_data_provider.get_candles(canonical, interval="15m")
    daily_df = await market_data_provider.get_candles(canonical, interval="1d")
    structure = analyze_market_structure(intraday_df)
    liquidity = analyze_liquidity(intraday_df, daily_df)
    momentum = analyze_momentum(intraday_df)
    volume = analyze_volume(intraday_df)

    return evaluate_trading_setup(
        symbol=canonical,
        quote=quote,
        structure=structure,
        liquidity=liquidity,
        momentum=momentum,
        volume=volume,
    )


async def handle_get_market_news(symbol: str) -> Dict[str, Any]:
    """Fetch legitimate news headlines for symbol via yfinance."""
    canonical = resolve_symbol(symbol) or symbol.upper()
    meta = INSTRUMENTS.get(canonical)
    ticker_str = meta.ticker if meta else canonical

    def _sync_news():
        try:
            t = yf.Ticker(ticker_str)
            news_list = getattr(t, "news", [])
            items = []
            for item in (news_list or [])[:5]:
                content = item.get("content", {})
                title = content.get("title") or item.get("title")
                pub_date = content.get("pubDate") or item.get("providerPublishTime")
                publisher = (
                    content.get("provider", {}).get("displayName")
                    if isinstance(content.get("provider"), dict)
                    else item.get("publisher")
                )
                link = content.get("canonicalUrl", {}).get("url") if isinstance(content.get("canonicalUrl"), dict) else item.get("link")
                if title:
                    items.append({
                        "title": title,
                        "publisher": publisher or "Market News",
                        "published_at": str(pub_date),
                        "url": link,
                    })
            return items
        except Exception:
            return []

    items = await asyncio.to_thread(_sync_news)
    return {
        "symbol": canonical,
        "news_count": len(items),
        "headlines": items,
        "note": "Verified headlines from connected financial sources" if items else "No breaking headlines found in current cycle",
    }


def register_all_market_tools() -> None:
    """Registers all standard tools into the MCP tool registry."""
    mcp_registry.register(
        name="get_current_price",
        description="Fetch current price, session change, high, low, and verified freshness metadata for an instrument.",
        parameters={
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Symbol such as NIFTY, BANKNIFTY, GOLD, BTC, RELIANCE"},
            },
            "required": ["symbol"],
        },
        handler=handle_get_current_price,
    )

    mcp_registry.register(
        name="get_historical_candles",
        description="Fetch OHLCV candlestick data for charting or analysis across intervals (1m, 5m, 15m, 1h, 1d).",
        parameters={
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Symbol name"},
                "interval": {"type": "string", "description": "Candle interval: 1m, 5m, 15m, 1h, 1d", "default": "15m"},
                "period": {"type": "string", "description": "Lookback period e.g. 1d, 5d, 1mo", "default": "5d"},
            },
            "required": ["symbol"],
        },
        handler=handle_get_historical_candles,
    )

    mcp_registry.register(
        name="get_market_structure",
        description="Analyze market structure: detects Higher Highs, Higher Lows, Lower Highs, Lower Lows, Break of Structure (BOS), Change of Character (CHoCH), and trend vs range.",
        parameters={
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Symbol name"},
                "timeframe": {"type": "string", "description": "Timeframe e.g. 5m, 15m, 1h, 1d", "default": "15m"},
            },
            "required": ["symbol"],
        },
        handler=handle_get_market_structure,
    )

    mcp_registry.register(
        name="get_liquidity_zones",
        description="Calculate observable structural liquidity pools: Previous Day High (PDH), Previous Day Low (PDL), Session High/Low, Equal Highs (EQH), Equal Lows (EQL), and Liquidity Sweeps.",
        parameters={
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Symbol name"},
                "timeframe": {"type": "string", "description": "Timeframe e.g. 15m", "default": "15m"},
            },
            "required": ["symbol"],
        },
        handler=handle_get_liquidity_zones,
    )

    mcp_registry.register(
        name="get_momentum_and_volume",
        description="Calculate RSI(14), MACD, EMA alignments, momentum divergence, and Relative Volume (RVOL).",
        parameters={
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Symbol name"},
                "timeframe": {"type": "string", "description": "Timeframe e.g. 15m", "default": "15m"},
            },
            "required": ["symbol"],
        },
        handler=handle_get_momentum_and_volume,
    )

    mcp_registry.register(
        name="get_volatility_metrics",
        description="Calculate ATR, Realized Volatility, and Volatility Regime (Squeeze / Compression vs Expansion).",
        parameters={
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Symbol name"},
                "timeframe": {"type": "string", "description": "Timeframe e.g. 15m", "default": "15m"},
            },
            "required": ["symbol"],
        },
        handler=handle_get_volatility_metrics,
    )

    mcp_registry.register(
        name="get_multi_timeframe_analysis",
        description="Perform simultaneous analysis across multiple timeframes (5m, 15m, 1h, 1d) and resolve trend conflicts.",
        parameters={
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Symbol name"},
            },
            "required": ["symbol"],
        },
        handler=handle_get_multi_timeframe_analysis,
    )

    mcp_registry.register(
        name="get_market_breadth",
        description="Fetch market breadth: advance/decline ratio, top moving heavyweights, and overall sector participation.",
        parameters={"type": "object", "properties": {}},
        handler=handle_get_market_breadth,
    )

    mcp_registry.register(
        name="get_macro_overview",
        description="Fetch macro indicators: USD/INR, Gold, Silver, Crude Oil, SPX, and India VIX.",
        parameters={"type": "object", "properties": {}},
        handler=handle_get_macro_overview,
    )

    mcp_registry.register(
        name="get_tradingview_signals",
        description="Retrieve recent signals and alerts ingested from TradingView webhooks.",
        parameters={
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Symbol name"},
            },
            "required": ["symbol"],
        },
        handler=handle_get_tradingview_signals,
    )

    mcp_registry.register(
        name="get_market_drivers",
        description="Investigate market drivers: categorizes findings into OBSERVED (factual data), INFERRED (logical transmission), and UNKNOWN (unverified factors).",
        parameters={
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Symbol name"},
            },
            "required": ["symbol"],
        },
        handler=handle_get_market_drivers,
    )

    mcp_registry.register(
        name="get_trading_setup",
        description="Evaluate if a high-probability technical setup exists (Status, Direction, Evidence, Trigger, Invalidation, Targets, R:R).",
        parameters={
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Symbol name"},
            },
            "required": ["symbol"],
        },
        handler=handle_get_trading_setup,
    )

    mcp_registry.register(
        name="get_market_news",
        description="Fetch verified recent headlines from connected financial sources.",
        parameters={
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Symbol name"},
            },
            "required": ["symbol"],
        },
        handler=handle_get_market_news,
    )


# Automatically register on import
register_all_market_tools()
