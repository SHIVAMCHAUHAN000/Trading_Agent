"""Drawdown and recovery analytics."""

from __future__ import annotations

from typing import Any

import pandas as pd


def drawdown_series(equity: pd.Series) -> pd.Series:
    eq = equity.astype(float)
    return eq / eq.cummax() - 1.0


def drawdown_stats(equity: pd.Series) -> dict[str, Any]:
    dd = drawdown_series(equity)
    if dd.empty:
        return {
            "max_drawdown": float("nan"),
            "max_drawdown_duration_days": 0,
            "recovery_time_days": None,
            "time_underwater_pct": float("nan"),
        }

    max_dd = float(dd.min())
    trough_idx = int(dd.argmin())
    trough_date = dd.index[trough_idx]
    pre_peak = equity.iloc[: trough_idx + 1]
    peak_date = pre_peak.idxmax()

    # Recovery: first date after trough where equity regains the peak value
    peak_val = float(equity.loc[peak_date])
    after = equity.iloc[trough_idx:]
    recovered = after[after >= peak_val]
    if recovered.empty:
        recovery_time_days = None
        duration_to_trough = int((trough_date - peak_date).days)
        max_duration = duration_to_trough  # still open
    else:
        recovery_date = recovered.index[0]
        recovery_time_days = int((recovery_date - trough_date).days)
        max_duration = int((recovery_date - peak_date).days)

    # Longest underwater spell in trading days
    underwater = dd < 0
    longest = 0
    cur = 0
    for flag in underwater:
        if flag:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 0

    return {
        "max_drawdown": max_dd,
        "max_drawdown_peak_date": str(pd.Timestamp(peak_date).date()),
        "max_drawdown_trough_date": str(pd.Timestamp(trough_date).date()),
        "max_drawdown_duration_days": int(max(longest, max_duration)),
        "recovery_time_days": recovery_time_days,
        "time_underwater_pct": float(underwater.mean()),
    }
