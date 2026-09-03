"""
Market session timing and state awareness for NSE and Global Markets.
Accounts for Indian Standard Time (IST = UTC+5:30).
"""

from __future__ import annotations

from datetime import datetime, time, timezone, timedelta
from enum import Enum
from typing import Dict

# IST timezone offset (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


class SessionState(str, Enum):
    PRE_MARKET = "PRE_MARKET"
    OPEN = "OPEN"
    POST_MARKET = "POST_MARKET"
    CLOSED = "CLOSED"
    WEEKEND = "WEEKEND"


def get_current_ist_time() -> datetime:
    """Returns current datetime in IST."""
    return datetime.now(timezone.utc).astimezone(IST)


def get_market_session_info(symbol: str) -> Dict[str, str]:
    """
    Returns session state, status description, and opening/closing details for the given symbol.
    """
    from live_data.instruments import MarketSegment, INSTRUMENTS

    inst = INSTRUMENTS.get(symbol.upper())
    now_ist = get_current_ist_time()
    weekday = now_ist.weekday()  # Monday is 0, Sunday is 6
    current_time = now_ist.time()

    # 1. Crypto is always open 24/7
    if inst and inst.segment == MarketSegment.CRYPTO:
        return {
            "session_state": SessionState.OPEN.value,
            "status_description": "24/7 Global Crypto Market Open",
            "is_open": True,
            "session_time_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
        }

    # 2. Indian Equities and Indices (NSE)
    if not inst or inst.segment in (MarketSegment.NSE_INDEX, MarketSegment.NSE_EQUITY):
        # Weekend check
        if weekday in (5, 6):
            return {
                "session_state": SessionState.WEEKEND.value,
                "status_description": "Weekend (NSE Closed - Showing latest closing session)",
                "is_open": False,
                "session_time_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
            }

        pre_start = time(9, 0)
        market_open = time(9, 15)
        market_close = time(15, 30)
        post_close = time(16, 0)

        if pre_start <= current_time < market_open:
            return {
                "session_state": SessionState.PRE_MARKET.value,
                "status_description": "Pre-Market Session (09:00 - 09:15 IST)",
                "is_open": False,
                "session_time_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
            }
        elif market_open <= current_time <= market_close:
            return {
                "session_state": SessionState.OPEN.value,
                "status_description": "Live Regular Trading Session (09:15 - 15:30 IST)",
                "is_open": True,
                "session_time_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
            }
        elif market_close < current_time <= post_close:
            return {
                "session_state": SessionState.POST_MARKET.value,
                "status_description": "Post-Market / Closing Session (15:30 - 16:00 IST)",
                "is_open": False,
                "session_time_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
            }
        else:
            return {
                "session_state": SessionState.CLOSED.value,
                "status_description": "Market Closed (Next session opens at 09:15 IST)",
                "is_open": False,
                "session_time_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
            }

    # 3. Commodities (COMEX / MCX / NYMEX)
    if inst.segment == MarketSegment.COMMODITY:
        if weekday in (5, 6):
            return {
                "session_state": SessionState.WEEKEND.value,
                "status_description": "Weekend (Commodity Markets Closed)",
                "is_open": False,
                "session_time_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
            }
        return {
            "session_state": SessionState.OPEN.value,
            "status_description": "Commodity Trading Active",
            "is_open": True,
            "session_time_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
        }

    # 4. Global Index (SPX)
    if inst.segment == MarketSegment.GLOBAL_INDEX:
        if weekday in (5, 6):
            return {
                "session_state": SessionState.WEEKEND.value,
                "status_description": "Weekend (US Markets Closed)",
                "is_open": False,
                "session_time_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
            }
        return {
            "session_state": SessionState.OPEN.value,
            "status_description": "US Market / Futures Session",
            "is_open": True,
            "session_time_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
        }

    return {
        "session_state": SessionState.OPEN.value,
        "status_description": "Active Market",
        "is_open": True,
        "session_time_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
    }
