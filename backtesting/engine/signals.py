"""Signal generators that map StrategySpec rules to target portfolios."""

from __future__ import annotations

import pandas as pd

from strategies.schema import StrategySpec


def month_end_signal_dates(close: pd.DataFrame) -> pd.DatetimeIndex:
    """Last available trading date in each calendar month."""
    s = pd.Series(close.index, index=close.index)
    return pd.DatetimeIndex(s.groupby(close.index.to_period("M")).max().values)


def cross_sectional_momentum_targets(
    close: pd.DataFrame,
    *,
    lookback_days: int,
    skip_days: int,
    top_n: int,
    min_momentum: float,
    signal_dates: pd.DatetimeIndex | None = None,
) -> pd.DataFrame:
    """
    12-1 style cross-sectional momentum.
    Momentum = close[t-skip]/close[t-lookback] - 1
    Target: equal weight among top_n names with momentum >= min_momentum.
    """
    dates = signal_dates if signal_dates is not None else month_end_signal_dates(close)
    # shift by skip_days so we don't use the most recent skip window
    end_px = close.shift(skip_days)
    start_px = close.shift(lookback_days)
    momentum = end_px / start_px - 1.0

    rows: list[dict[str, float]] = []
    index: list[pd.Timestamp] = []
    for dt in dates:
        if dt not in momentum.index:
            continue
        scores = momentum.loc[dt].dropna()
        scores = scores[scores >= min_momentum]
        if scores.empty:
            index.append(dt)
            rows.append({})
            continue
        chosen = scores.sort_values(ascending=False).head(top_n)
        weight = 1.0 / len(chosen)
        rows.append({sym: weight for sym in chosen.index})
        index.append(dt)

    if not index:
        return pd.DataFrame(index=close.index[:0], columns=close.columns).fillna(0.0)

    targets = pd.DataFrame(rows, index=pd.DatetimeIndex(index)).reindex(columns=close.columns).fillna(0.0)
    return targets


def build_target_weights(spec: StrategySpec, close: pd.DataFrame) -> pd.DataFrame:
    entry = spec.entry.parameters
    signal_type = str(spec.signal.get("type", ""))
    if signal_type != "cross_sectional_momentum" and spec.entry.condition != "rank_by_momentum_desc":
        raise ValueError(
            f"Unsupported strategy signal/entry for V1 engine: signal={signal_type}, entry={spec.entry.condition}"
        )

    lookback = int(entry.get("lookback_days", spec.signal.get("lookback_days", 252)))
    skip = int(entry.get("skip_days", spec.signal.get("skip_days", 21)))
    top_n = int(entry.get("top_n", spec.position.max_positions))
    min_momentum = float(entry.get("min_momentum", 0.0))

    rebalance = str(spec.exit.parameters.get("rebalance", "monthly")).lower()
    if rebalance != "monthly":
        raise ValueError("V1 engine currently supports exit.parameters.rebalance=monthly only")

    return cross_sectional_momentum_targets(
        close,
        lookback_days=lookback,
        skip_days=skip,
        top_n=top_n,
        min_momentum=min_momentum,
    )
