"""NY-session liquidity-sweep / double-sweep trap engine (XAUUSD 1m)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from strategies.schema_v2 import StrategySpecV2


@dataclass
class SweepEvent:
    side: str  # 'high' or 'low'
    level: float
    sweep_time: pd.Timestamp
    extreme: float


@dataclass
class V2BacktestResult:
    equity_curve: pd.DataFrame
    trades: pd.DataFrame
    meta: dict[str, Any]


def _ensure_utc(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["DateTime"] = pd.to_datetime(out["DateTime"], utc=True)
    return out.sort_values("DateTime").reset_index(drop=True)


def filter_session(bars: pd.DataFrame, *, timezone: str, start: str, end: str) -> pd.DataFrame:
    tz = "Asia/Kolkata" if timezone.upper() in {"IST", "INDIA"} else timezone
    local = bars.copy()
    local["Local"] = local["DateTime"].dt.tz_convert(tz)
    sh, sm = map(int, start.split(":"))
    eh, em = map(int, end.split(":"))
    mins = local["Local"].dt.hour * 60 + local["Local"].dt.minute
    start_m = sh * 60 + sm
    end_m = eh * 60 + em
    if start_m <= end_m:
        mask = (mins >= start_m) & (mins < end_m)
    else:
        mask = (mins >= start_m) | (mins < end_m)
    return local.loc[mask].copy()


def to_15m(bars_1m: pd.DataFrame) -> pd.DataFrame:
    x = bars_1m.set_index("DateTime")
    ohlc = x.resample("15min").agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    ).dropna()
    return ohlc.reset_index()


def find_equal_levels(
    bars_15m: pd.DataFrame,
    *,
    tolerance_pct: float,
    min_touches: int = 2,
    include_swings: bool = True,
) -> dict[str, list[float]]:
    """Mark clustered swing highs/lows as liquidity pools."""
    if len(bars_15m) < 3:
        return {"highs": [], "lows": []}
    highs = bars_15m["High"].astype(float).to_numpy()
    lows = bars_15m["Low"].astype(float).to_numpy()

    swing_highs = []
    swing_lows = []
    # Use a smaller swing window on short session samples
    left = 1 if len(bars_15m) < 8 else 2
    right = left
    for i in range(left, len(bars_15m) - right):
        if highs[i] >= np.max(highs[i - left : i + right + 1]):
            swing_highs.append(float(highs[i]))
        if lows[i] <= np.min(lows[i - left : i + right + 1]):
            swing_lows.append(float(lows[i]))

    def cluster(levels: list[float], need: int) -> list[float]:
        if not levels:
            return []
        levels = sorted(levels)
        groups: list[list[float]] = [[levels[0]]]
        for lv in levels[1:]:
            ref = float(np.mean(groups[-1]))
            if abs(lv - ref) / max(ref, 1e-9) * 100.0 <= tolerance_pct:
                groups[-1].append(lv)
            else:
                groups.append([lv])
        out = [float(np.mean(g)) for g in groups if len(g) >= need]
        if include_swings and not out:
            # fallback: individual swings still act as resting liquidity
            out = [float(np.mean(g)) for g in groups]
        return out

    return {
        "highs": cluster(swing_highs, min_touches),
        "lows": cluster(swing_lows, min_touches),
    }


def detect_sweep(
    bars_1m: pd.DataFrame,
    *,
    level: float,
    side: str,
    close_back_within_bars: int,
) -> SweepEvent | None:
    """Wick through level then close back inside within N bars."""
    for i in range(len(bars_1m) - close_back_within_bars):
        row = bars_1m.iloc[i]
        if side == "high":
            if float(row["High"]) > level and float(row["Close"]) <= level:
                # already closed back on same bar
                return SweepEvent("high", level, row["DateTime"], float(row["High"]))
            if float(row["High"]) > level:
                window = bars_1m.iloc[i : i + close_back_within_bars + 1]
                if (window["Close"].astype(float) <= level).any():
                    return SweepEvent("high", level, row["DateTime"], float(row["High"]))
        else:
            if float(row["Low"]) < level and float(row["Close"]) >= level:
                return SweepEvent("low", level, row["DateTime"], float(row["Low"]))
            if float(row["Low"]) < level:
                window = bars_1m.iloc[i : i + close_back_within_bars + 1]
                if (window["Close"].astype(float) >= level).any():
                    return SweepEvent("low", level, row["DateTime"], float(row["Low"]))
    return None


def run_liquidity_sweep_backtest(spec: StrategySpecV2, bars_1m: pd.DataFrame) -> V2BacktestResult:
    bars = _ensure_utc(bars_1m)
    if spec.period.start:
        bars = bars[bars["DateTime"] >= pd.Timestamp(spec.period.start, tz="UTC")]
    if spec.period.end:
        bars = bars[bars["DateTime"] <= pd.Timestamp(spec.period.end, tz="UTC") + pd.Timedelta(days=1)]

    if bars.empty:
        raise ValueError("No 1m bars available for requested period")

    session = spec.session
    if session is None:
        raise ValueError("session block required for liquidity_sweep engine")

    tol = float(spec.liquidity_marking.get("tolerance_pct", 0.1))
    close_back = int(spec.sweep_definition.get("parameters", {}).get("close_back_within_bars", 3))
    risk_pct = float(spec.position.risk_per_trade_pct) / 100.0
    capital = float(spec.capital)
    cash = capital
    equity_rows = []
    trades: list[dict[str, Any]] = []

    # Process day by day in session timezone
    sess = filter_session(bars, timezone=session.timezone, start=session.start, end=session.end)
    if sess.empty:
        raise ValueError("No bars inside configured NY session window")

    sess["SessionDate"] = sess["Local"].dt.date
    position = None
    history_15: list[pd.DataFrame] = []

    for day, day_1m in sess.groupby("SessionDate"):
        day_1m = day_1m.sort_values("DateTime").reset_index(drop=True)
        day_15 = to_15m(day_1m)
        history_15.append(day_15)
        # Liquidity from current + prior sessions (equal highs often form across days)
        lookback_15 = pd.concat(history_15[-5:], ignore_index=True)
        levels = find_equal_levels(lookback_15, tolerance_pct=tol, min_touches=2, include_swings=True)
        if not levels["highs"] and not levels["lows"]:
            last = day_1m.iloc[-1]
            equity_rows.append({"DateTime": last["DateTime"], "Equity": cash, "Cash": cash, "Position": 0})
            continue

        sweeps: list[SweepEvent] = []
        for lvl in levels["highs"]:
            ev = detect_sweep(day_1m, level=lvl, side="high", close_back_within_bars=close_back)
            if ev:
                sweeps.append(ev)
        for lvl in levels["lows"]:
            ev = detect_sweep(day_1m, level=lvl, side="low", close_back_within_bars=close_back)
            if ev:
                sweeps.append(ev)
        sweeps = sorted(sweeps, key=lambda e: e.sweep_time)

        # Need opposite-side double sweep
        first = None
        second = None
        for ev in sweeps:
            if first is None:
                first = ev
                continue
            if ev.side != first.side and ev.sweep_time > first.sweep_time:
                second = ev
                break
        if first is None or second is None or position is not None:
            last = day_1m.iloc[-1]
            mtm = 0.0
            if position is not None:
                mtm = position["qty"] * (float(last["Close"]) - position["entry"]) * (1 if position["side"] == "long" else -1)
            equity_rows.append({"DateTime": last["DateTime"], "Equity": cash + mtm, "Cash": cash, "Position": 0 if position is None else 1})
            continue

        # Direction: after sweeping both sides, fade the most recent sweep
        # If last sweep was high (stops above taken), expect reversal down -> short
        # If last sweep was low, expect reversal up -> long
        direction = "short" if second.side == "high" else "long"
        entry_level = second.level
        entry_candidates = day_1m[day_1m["DateTime"] > second.sweep_time]
        entry_row = None
        for _, row in entry_candidates.iterrows():
            if direction == "long" and float(row["Close"]) >= entry_level:
                entry_row = row
                break
            if direction == "short" and float(row["Close"]) <= entry_level:
                entry_row = row
                break
        if entry_row is None:
            last = day_1m.iloc[-1]
            equity_rows.append({"DateTime": last["DateTime"], "Equity": cash, "Cash": cash, "Position": 0})
            continue

        entry_px = float(entry_row["Close"])
        stop_px = second.extreme * (1.0005 if direction == "short" else 0.9995)
        risk_per_unit = abs(entry_px - stop_px)
        if risk_per_unit <= 0:
            continue
        risk_amount = capital * risk_pct
        qty = risk_amount / risk_per_unit

        # Target: opposite liquidity cluster if available else 1R
        if direction == "long":
            targets = [h for h in levels["highs"] if h > entry_px]
            target_px = min(targets) if targets else entry_px + risk_per_unit
        else:
            targets = [l for l in levels["lows"] if l < entry_px]
            target_px = max(targets) if targets else entry_px - risk_per_unit

        position = {
            "side": direction,
            "entry": entry_px,
            "stop": stop_px,
            "target": target_px,
            "qty": qty,
            "entry_time": entry_row["DateTime"],
            "day": day,
        }

        # Manage within remaining session bars
        rest = day_1m[day_1m["DateTime"] > entry_row["DateTime"]]
        exit_row = None
        exit_px = None
        exit_reason = "session_close"
        for _, row in rest.iterrows():
            hi, lo, cl = float(row["High"]), float(row["Low"]), float(row["Close"])
            if direction == "long":
                if lo <= stop_px:
                    exit_row, exit_px, exit_reason = row, stop_px, "stop"
                    break
                if hi >= target_px:
                    exit_row, exit_px, exit_reason = row, target_px, "target"
                    break
            else:
                if hi >= stop_px:
                    exit_row, exit_px, exit_reason = row, stop_px, "stop"
                    break
                if lo <= target_px:
                    exit_row, exit_px, exit_reason = row, target_px, "target"
                    break
        if exit_row is None:
            exit_row = day_1m.iloc[-1]
            exit_px = float(exit_row["Close"])
            exit_reason = "session_close"

        sign = 1 if direction == "long" else -1
        pnl = sign * (float(exit_px) - entry_px) * qty
        cash += pnl
        trades.append(
            {
                "trade_id": f"{day}-{direction}",
                "symbol": "XAUUSD",
                "side": direction,
                "entry_date": position["entry_time"],
                "exit_date": exit_row["DateTime"],
                "entry_price": entry_px,
                "exit_price": float(exit_px),
                "qty": qty,
                "gross_pnl": pnl,
                "costs": 0.0,
                "net_pnl": pnl,
                "holding_days": max(1, int((pd.Timestamp(exit_row["DateTime"]) - pd.Timestamp(position["entry_time"])).total_seconds() // 60)),
                "exit_reason": exit_reason,
                "stop": stop_px,
                "target": target_px,
            }
        )
        position = None
        equity_rows.append({"DateTime": exit_row["DateTime"], "Equity": cash, "Cash": cash, "Position": 0})

    equity = pd.DataFrame(equity_rows).drop_duplicates("DateTime").sort_values("DateTime")
    if equity.empty:
        equity = pd.DataFrame(
            [{"DateTime": bars["DateTime"].iloc[0], "Equity": capital, "Cash": capital, "Position": 0}]
        )
    equity = equity.set_index("DateTime")
    trades_df = pd.DataFrame(trades)
    meta = {
        "strategy_name": spec.name,
        "engine": "liquidity_sweep_ny_session_v2",
        "capital": capital,
        "n_trades": int(len(trades_df)),
        "session": session.model_dump(),
        "bars": int(len(bars)),
        "session_bars": int(len(sess)),
        "assumptions": [
            "Equal high/low clusters from 15m swings (>=2 touches)",
            "Sweep = wick through level + close back within N 1m bars",
            "Entry fades the second opposite-side sweep on close reclaim",
            "Risk-based sizing; costs not yet modeled in V2 smoke",
            "IST fixed window ignores US DST shift unless session config updated",
            "Yahoo GC=F 1m coverage is short; treat results as smoke unless Dukascopy history is loaded",
        ],
    }
    return V2BacktestResult(equity_curve=equity, trades=trades_df, meta=meta)
