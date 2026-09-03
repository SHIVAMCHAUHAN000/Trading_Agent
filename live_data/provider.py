"""
Abstract Base Class for Market Data Providers.
Allows swapping data vendors (e.g. yfinance, Zerodha Kite, Upstox, Interactive Brokers) seamlessly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import pandas as pd


class MarketDataProvider(ABC):
    """Abstract interface for market data connectors."""

    @abstractmethod
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Fetch current quote, price, change, and freshness metadata."""
        pass

    @abstractmethod
    async def get_candles(
        self,
        symbol: str,
        interval: str = "15m",
        period: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch OHLCV historical/intraday candles as a pandas DataFrame.
        Columns: ['open', 'high', 'low', 'close', 'volume'] with DatetimeIndex in UTC/IST.
        """
        pass

    @abstractmethod
    async def get_market_breadth(self) -> Dict[str, Any]:
        """Fetch advancing/declining count, top movers, and market sentiment."""
        pass

    @abstractmethod
    async def get_macro_overview(self) -> Dict[str, Any]:
        """Fetch key macro assets: USDINR, Gold, Silver, Crude, SPX, India VIX."""
        pass
