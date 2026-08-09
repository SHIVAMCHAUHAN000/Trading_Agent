"""Time-based research splits. OOS is evaluation-only."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class TimeSplit:
    is_start: pd.Timestamp
    is_end: pd.Timestamp
    oos_start: pd.Timestamp
    oos_end: pd.Timestamp
    is_fraction: float

    def to_dict(self) -> dict[str, str | float]:
        return {
            "is_start": str(self.is_start.date()),
            "is_end": str(self.is_end.date()),
            "oos_start": str(self.oos_start.date()),
            "oos_end": str(self.oos_end.date()),
            "is_fraction": self.is_fraction,
        }


def calendar_split(
    start: str | pd.Timestamp,
    end: str | pd.Timestamp,
    *,
    is_fraction: float = 0.70,
) -> TimeSplit:
    if not 0.5 <= is_fraction < 1.0:
        raise ValueError("is_fraction must be in [0.5, 1.0)")
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    if end_ts <= start_ts:
        raise ValueError("end must be after start")
    delta = end_ts - start_ts
    cut = start_ts + delta * is_fraction
    # IS ends day before OOS starts
    oos_start = cut.normalize()
    is_end = oos_start - pd.Timedelta(days=1)
    return TimeSplit(
        is_start=start_ts.normalize(),
        is_end=is_end,
        oos_start=oos_start,
        oos_end=end_ts.normalize(),
        is_fraction=float(is_fraction),
    )


def walk_forward_windows(
    start: str | pd.Timestamp,
    end: str | pd.Timestamp,
    *,
    train_years: float = 3.0,
    test_years: float = 1.0,
    step_years: float = 1.0,
) -> list[dict[str, str]]:
    """Expanding/rolling style: fixed train length, then test, step forward."""
    start_ts = pd.Timestamp(start).normalize()
    end_ts = pd.Timestamp(end).normalize()
    train_days = int(train_years * 365)
    test_days = int(test_years * 365)
    step_days = int(step_years * 365)

    windows: list[dict[str, str]] = []
    cursor = start_ts
    while True:
        train_start = cursor
        train_end = train_start + pd.Timedelta(days=train_days)
        test_start = train_end + pd.Timedelta(days=1)
        test_end = test_start + pd.Timedelta(days=test_days)
        if test_end > end_ts:
            break
        windows.append(
            {
                "train_start": str(train_start.date()),
                "train_end": str(train_end.date()),
                "test_start": str(test_start.date()),
                "test_end": str(test_end.date()),
            }
        )
        cursor = cursor + pd.Timedelta(days=step_days)
        if cursor >= end_ts:
            break
    return windows
