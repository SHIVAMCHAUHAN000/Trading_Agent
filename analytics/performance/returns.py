"""Return decomposition helpers."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def daily_returns(equity: pd.Series) -> pd.Series:
    return equity.astype(float).pct_change().dropna()


def monthly_returns(equity: pd.Series) -> pd.Series:
    eq = equity.astype(float)
    monthly = eq.resample("ME").last().dropna()
    return monthly.pct_change().dropna()


def annual_returns(equity: pd.Series) -> pd.Series:
    eq = equity.astype(float)
    annual = eq.resample("YE").last().dropna()
    return annual.pct_change().dropna()


def rolling_returns(equity: pd.Series, window_days: int = 252) -> pd.Series:
    eq = equity.astype(float)
    return eq / eq.shift(window_days) - 1.0


def return_summary(equity: pd.Series, *, trading_days_per_year: int = 252) -> dict[str, Any]:
    rets = daily_returns(equity)
    monthly = monthly_returns(equity)
    annual = annual_returns(equity)
    roll = rolling_returns(equity, trading_days_per_year).dropna()

    return {
        "monthly_return_mean": float(monthly.mean()) if len(monthly) else float("nan"),
        "monthly_return_median": float(monthly.median()) if len(monthly) else float("nan"),
        "monthly_positive_pct": float((monthly > 0).mean()) if len(monthly) else float("nan"),
        "best_month": float(monthly.max()) if len(monthly) else float("nan"),
        "worst_month": float(monthly.min()) if len(monthly) else float("nan"),
        "annual_returns": {str(k.year): float(v) for k, v in annual.items()},
        "rolling_1y_return_mean": float(roll.mean()) if len(roll) else float("nan"),
        "rolling_1y_return_min": float(roll.min()) if len(roll) else float("nan"),
        "rolling_1y_return_max": float(roll.max()) if len(roll) else float("nan"),
        "daily_return_skew": float(rets.skew()) if len(rets) > 2 else float("nan"),
        "daily_return_kurtosis": float(rets.kurtosis()) if len(rets) > 3 else float("nan"),
        "downside_deviation": (
            float(rets[rets < 0].std(ddof=0) * np.sqrt(trading_days_per_year))
            if (rets < 0).any()
            else float("nan")
        ),
    }
