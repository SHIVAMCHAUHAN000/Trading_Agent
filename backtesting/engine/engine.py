"""Daily long-only backtest engine (signal close → execute next open)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from backtesting.costs.model import CostConfig, load_cost_config, trade_cost
from backtesting.engine.data import benchmark_close, load_bars, to_price_panel
from backtesting.engine.signals import build_target_weights
from strategies.schema import StrategySpec


@dataclass
class BacktestResult:
    equity_curve: pd.DataFrame
    trades: pd.DataFrame
    positions_end: dict[str, float]
    meta: dict[str, Any]
    benchmark_equity: pd.Series | None = None
    bars: pd.DataFrame | None = None


def _next_trading_day(dates: pd.DatetimeIndex, signal_dt: pd.Timestamp) -> pd.Timestamp | None:
    loc = dates.searchsorted(signal_dt, side="right")
    if loc >= len(dates):
        return None
    return dates[loc]


def run_backtest(
    spec: StrategySpec,
    bars: pd.DataFrame | None = None,
    *,
    cost_multiplier: float = 1.0,
    warmup_calendar_days: int = 400,
) -> BacktestResult:
    if spec.execution.execution_time.value != "next_open":
        raise ValueError("V1 engine supports execution_time=next_open only")
    if spec.execution.signal_time.value != "close":
        raise ValueError("V1 engine supports signal_time=close only")
    if not spec.execution.long_only:
        raise ValueError("V1 engine is long-only")

    bars_all = load_bars() if bars is None else bars.copy()
    bars_all["Date"] = pd.to_datetime(bars_all["Date"]).dt.normalize()

    start = pd.Timestamp(spec.period.start)
    end = pd.Timestamp(spec.period.end) if spec.period.end else bars_all["Date"].max()
    warmup_start = start - pd.Timedelta(days=int(warmup_calendar_days))

    # Keep pre-period history for signals; simulate portfolio only in [start, end].
    bars_signal = bars_all[(bars_all["Date"] >= warmup_start) & (bars_all["Date"] <= end)].copy()
    open_px = to_price_panel(bars_signal, "Open")
    close_px = to_price_panel(bars_signal, "Close")
    all_dates = close_px.index
    sim_dates = all_dates[(all_dates >= start) & (all_dates <= end)]
    if len(all_dates) < 120:
        raise ValueError("Insufficient history for momentum lookback / backtest")
    if len(sim_dates) < 20:
        raise ValueError("Evaluation window too short for backtest metrics")

    targets = build_target_weights(spec, close_px)
    exec_plan: dict[pd.Timestamp, pd.Series] = {}
    for signal_dt, weights in targets.iterrows():
        exec_dt = _next_trading_day(all_dates, signal_dt)
        if exec_dt is None or exec_dt < start or exec_dt > end:
            continue
        exec_plan[exec_dt] = weights

    cost_cfg = load_cost_config(
        slippage_bps=spec.cost_model.slippage_bps,
        spread_bps=spec.cost_model.spread_bps,
        multiplier=cost_multiplier,
    )

    cash = float(spec.capital)
    shares: dict[str, int] = {}
    open_lots: dict[str, dict[str, Any]] = {}
    trades: list[dict[str, Any]] = []
    equity_rows: list[dict[str, Any]] = []

    for dt in sim_dates:
        if dt in exec_plan:
            cash, shares, open_lots, day_trades = _rebalance_at_open(
                dt=dt,
                target_weights=exec_plan[dt],
                open_px=open_px.loc[dt],
                cash=cash,
                shares=shares,
                open_lots=open_lots,
                cost_cfg=cost_cfg,
            )
            trades.extend(day_trades)

        mtm = 0.0
        for sym, qty in shares.items():
            px = close_px.at[dt, sym]
            if pd.notna(px):
                mtm += qty * float(px)
        equity = cash + mtm
        equity_rows.append(
            {
                "Date": dt,
                "Cash": cash,
                "MarketValue": mtm,
                "Equity": equity,
                "GrossExposure": mtm,
                "NetExposure": mtm,
                "Positions": sum(1 for q in shares.values() if q > 0),
            }
        )

    equity_curve = pd.DataFrame(equity_rows).set_index("Date")
    trades_df = pd.DataFrame(trades)
    if trades_df.empty:
        trades_df = pd.DataFrame(
            columns=[
                "trade_id",
                "symbol",
                "entry_date",
                "exit_date",
                "entry_price",
                "exit_price",
                "qty",
                "gross_pnl",
                "costs",
                "net_pnl",
                "holding_days",
            ]
        )

    bars_eval = bars_all[(bars_all["Date"] >= start) & (bars_all["Date"] <= end)].copy()
    bench = benchmark_close(bars_signal).reindex(equity_curve.index).ffill()
    if not bench.empty and pd.notna(bench.iloc[0]) and float(bench.iloc[0]) != 0:
        benchmark_equity = bench / float(bench.iloc[0]) * float(spec.capital)
    else:
        benchmark_equity = pd.Series(dtype=float)

    meta = {
        "strategy_name": spec.name,
        "capital": float(spec.capital),
        "start": str(start.date()),
        "end": str(end.date()),
        "warmup_start": str(warmup_start.date()),
        "cost_model_id": cost_cfg.model_id,
        "cost_multiplier": cost_multiplier,
        "n_trades": int(len(trades_df)),
        "symbols_traded": sorted({t["symbol"] for t in trades}) if trades else [],
        "benchmark_points": int(bench.notna().sum()),
        "execution": "signal_close_to_next_open",
        "assumptions": [
            "Integer share quantities",
            "Equal-weight monthly rebalance among top momentum names",
            "Costs deducted in cash at fill time",
            "Current NIFTY50 membership universe (survivorship bias)",
            "Benchmark is buy-and-hold ^NSEI scaled to starting capital",
            "Signal warmup uses pre-period history; portfolio simulation starts at period.start",
        ],
    }
    return BacktestResult(
        equity_curve=equity_curve,
        trades=trades_df,
        positions_end=shares,
        meta=meta,
        benchmark_equity=benchmark_equity,
        bars=bars_eval,
    )


def _rebalance_at_open(
    *,
    dt: pd.Timestamp,
    target_weights: pd.Series,
    open_px: pd.Series,
    cash: float,
    shares: dict[str, int],
    open_lots: dict[str, dict[str, Any]],
    cost_cfg: CostConfig,
) -> tuple[float, dict[str, int], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    trades: list[dict[str, Any]] = []

    # Current equity at open for target notional
    mtm = 0.0
    for sym, qty in shares.items():
        px = open_px.get(sym, np.nan)
        if pd.notna(px):
            mtm += qty * float(px)
    equity = cash + mtm

    desired_qty: dict[str, int] = {}
    for sym, w in target_weights.items():
        if w <= 0:
            continue
        px = open_px.get(sym, np.nan)
        if pd.isna(px) or float(px) <= 0:
            continue
        desired_qty[sym] = int(np.floor((equity * float(w)) / float(px)))

    # Sell names not desired or oversized
    all_syms = set(shares) | set(desired_qty)
    for sym in sorted(all_syms):
        cur = int(shares.get(sym, 0))
        tgt = int(desired_qty.get(sym, 0))
        if cur > tgt:
            sell_qty = cur - tgt
            px = open_px.get(sym, np.nan)
            if pd.isna(px) or sell_qty <= 0:
                continue
            notional = sell_qty * float(px)
            costs = trade_cost(notional, "sell", cost_cfg)["total"]
            cash += notional - costs
            shares[sym] = cur - sell_qty
            if shares[sym] == 0:
                shares.pop(sym, None)

            lot = open_lots.get(sym)
            if lot is not None:
                # Close full remaining lot if flat; otherwise proportional close not tracked in V1 lots
                if sym not in shares:
                    entry_px = float(lot["entry_price"])
                    qty = int(lot["qty"])
                    gross = (float(px) - entry_px) * qty
                    total_costs = float(lot["entry_costs"]) + costs
                    trades.append(
                        {
                            "trade_id": lot["trade_id"],
                            "symbol": sym,
                            "entry_date": lot["entry_date"],
                            "exit_date": dt,
                            "entry_price": entry_px,
                            "exit_price": float(px),
                            "qty": qty,
                            "gross_pnl": gross,
                            "costs": total_costs,
                            "net_pnl": gross - total_costs,
                            "holding_days": int((dt - pd.Timestamp(lot["entry_date"])).days),
                        }
                    )
                    open_lots.pop(sym, None)
                else:
                    # Partial reduce: keep lot open with reduced qty; attribute sell costs to lot
                    lot["qty"] = shares[sym]
                    lot["entry_costs"] = float(lot["entry_costs"]) + costs

    # Buys / adds
    for sym, tgt in desired_qty.items():
        cur = int(shares.get(sym, 0))
        if tgt <= cur:
            continue
        buy_qty = tgt - cur
        px = open_px.get(sym, np.nan)
        if pd.isna(px) or buy_qty <= 0:
            continue
        notional = buy_qty * float(px)
        costs = trade_cost(notional, "buy", cost_cfg)["total"]
        # Ensure enough cash
        if cash < notional + costs:
            affordable = int(np.floor(cash / (float(px) * (1 + 0.002))))  # rough buffer
            buy_qty = max(0, min(buy_qty, affordable))
            if buy_qty <= 0:
                continue
            notional = buy_qty * float(px)
            costs = trade_cost(notional, "buy", cost_cfg)["total"]
            if cash < notional + costs:
                continue

        cash -= notional + costs
        shares[sym] = cur + buy_qty
        if sym not in open_lots:
            open_lots[sym] = {
                "trade_id": f"{sym}-{dt.date()}",
                "entry_date": dt,
                "entry_price": float(px),
                "qty": buy_qty,
                "entry_costs": costs,
            }
        else:
            lot = open_lots[sym]
            old_qty = int(lot["qty"])
            new_qty = old_qty + buy_qty
            lot["entry_price"] = (float(lot["entry_price"]) * old_qty + float(px) * buy_qty) / new_qty
            lot["qty"] = new_qty
            lot["entry_costs"] = float(lot["entry_costs"]) + costs

    return cash, shares, open_lots, trades
