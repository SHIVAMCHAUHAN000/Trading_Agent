"""
Data freshness monitoring, stale data detection, and timestamp integrity.
Ensures zero data fabrication and explicit data lineage.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional
from config.quant_brain_config import settings
from quant.session import IST, get_current_ist_time, get_market_session_info


class FreshnessStatus:
    LIVE = "LIVE"
    DELAYED = "DELAYED"
    STALE = "STALE"
    SESSION_CLOSED = "SESSION_CLOSED"
    UNAVAILABLE = "UNAVAILABLE"


def evaluate_data_freshness(
    symbol: str,
    last_timestamp: Optional[datetime],
    is_live_feed: bool = True,
    delay_minutes: int = 15,
) -> Dict[str, Any]:
    """
    Evaluates whether market data is live, delayed, stale, closed, or unavailable.
    """
    if last_timestamp is None:
        return {
            "status": FreshnessStatus.UNAVAILABLE,
            "disclaimer": "Market data unavailable from the connected source.",
            "is_usable": False,
            "age_seconds": None,
            "timestamp_str": "N/A",
        }

    now = datetime.now(timezone.utc)
    if last_timestamp.tzinfo is None:
        # Assume UTC if naive
        last_timestamp = last_timestamp.replace(tzinfo=timezone.utc)

    age = (now - last_timestamp).total_seconds()
    session_info = get_market_session_info(symbol)
    is_market_open = session_info["is_open"]
    timestamp_ist = last_timestamp.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S IST")

    # If the market is closed or weekend, older data is normal (it's the official closing print)
    if not is_market_open:
        return {
            "status": FreshnessStatus.SESSION_CLOSED,
            "disclaimer": f"Market is currently closed. Showing verified closing session data as of {timestamp_ist}.",
            "is_usable": True,
            "age_seconds": age,
            "timestamp_str": timestamp_ist,
            "session_info": session_info,
        }

    # If market is open, check age
    stale_threshold_seconds = settings.MAX_STALE_MINUTES * 60

    if age <= 60:
        return {
            "status": FreshnessStatus.LIVE,
            "disclaimer": f"Verified fresh live data as of {timestamp_ist}.",
            "is_usable": True,
            "age_seconds": age,
            "timestamp_str": timestamp_ist,
            "session_info": session_info,
        }
    elif age <= (delay_minutes * 60 + 120):
        return {
            "status": FreshnessStatus.DELAYED,
            "disclaimer": f"Data is delayed by ~{int(age // 60)} minutes (Source timestamp: {timestamp_ist}).",
            "is_usable": True,
            "age_seconds": age,
            "timestamp_str": timestamp_ist,
            "session_info": session_info,
        }
    elif age <= stale_threshold_seconds:
        return {
            "status": FreshnessStatus.DELAYED,
            "disclaimer": f"Data is delayed (Timestamp: {timestamp_ist}).",
            "is_usable": True,
            "age_seconds": age,
            "timestamp_str": timestamp_ist,
            "session_info": session_info,
        }
    else:
        return {
            "status": FreshnessStatus.STALE,
            "disclaimer": f"WARNING: Market data is stale ({int(age // 60)} min old, timestamp {timestamp_ist}). Conclusions should be treated with caution.",
            "is_usable": True,
            "age_seconds": age,
            "timestamp_str": timestamp_ist,
            "session_info": session_info,
        }
