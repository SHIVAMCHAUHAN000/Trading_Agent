"""Trade-path analytics: MAE / MFE."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def enrich_trades_with_excursions(trades: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
    """
    For long trades:
      MAE = min(low/entry - 1) over holding window
      MFE = max(high/entry - 1) over holding window
    """
    if trades is None or trades.empty:
        return trades.copy() if trades is not None else pd.DataFrame()

    bars = bars.copy()
    bars["Date"] = pd.to_datetime(bars["Date"]).dt.normalize()
    out = trades.copy()
    maes: list[float] = []
    mfes: list[float] = []

    for _, tr in out.iterrows():
        sym = tr["symbol"]
        entry = pd.Timestamp(tr["entry_date"]).normalize()
        exit_ = pd.Timestamp(tr["exit_date"]).normalize()
        entry_px = float(tr["entry_price"])
        path = bars[(bars["Symbol"] == sym) & (bars["Date"] >= entry) & (bars["Date"] <= exit_)]
        if path.empty or entry_px <= 0:
            maes.append(float("nan"))
            mfes.append(float("nan"))
            continue
        mae = float((path["Low"].astype(float) / entry_px - 1.0).min())
        mfe = float((path["High"].astype(float) / entry_px - 1.0).max())
        maes.append(mae)
        mfes.append(mfe)

    out["mae"] = maes
    out["mfe"] = mfes
    return out


def trade_excursion_summary(trades: pd.DataFrame) -> dict[str, Any]:
    if trades is None or trades.empty or "mae" not in trades.columns:
        return {
            "avg_mae": float("nan"),
            "avg_mfe": float("nan"),
            "median_mae": float("nan"),
            "median_mfe": float("nan"),
            "mae_to_mfe_ratio": float("nan"),
        }
    mae = trades["mae"].astype(float)
    mfe = trades["mfe"].astype(float)
    avg_mae = float(mae.mean())
    avg_mfe = float(mfe.mean())
    ratio = float(abs(avg_mae) / avg_mfe) if avg_mfe and not np.isnan(avg_mfe) and avg_mfe != 0 else float("nan")
    return {
        "avg_mae": avg_mae,
        "avg_mfe": avg_mfe,
        "median_mae": float(mae.median()),
        "median_mfe": float(mfe.median()),
        "mae_to_mfe_ratio": ratio,
    }
