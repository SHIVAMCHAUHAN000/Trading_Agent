"""Core performance / trade analytics for Milestone 1."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _safe_div(a: float, b: float) -> float:
    if b == 0 or np.isnan(b):
        return float("nan")
    return float(a / b)


def compute_performance_metrics(
    equity_curve: pd.DataFrame,
    trades: pd.DataFrame,
    *,
    capital: float,
    trading_days_per_year: int = 252,
) -> dict[str, Any]:
    if equity_curve.empty:
        raise ValueError("equity_curve is empty")

    eq = equity_curve["Equity"].astype(float)
    rets = eq.pct_change().dropna()
    start_eq = float(eq.iloc[0])
    end_eq = float(eq.iloc[-1])
    n_days = max(len(eq) - 1, 1)
    years = n_days / trading_days_per_year

    total_return = end_eq / capital - 1.0 if capital else end_eq / start_eq - 1.0
    cagr = (end_eq / capital) ** (1 / years) - 1.0 if years > 0 and capital > 0 and end_eq > 0 else float("nan")
    vol = float(rets.std(ddof=0) * np.sqrt(trading_days_per_year)) if len(rets) else float("nan")
    sharpe = _safe_div(float(rets.mean() * trading_days_per_year), vol) if vol else float("nan")

    downside = rets[rets < 0]
    downside_dev = float(downside.std(ddof=0) * np.sqrt(trading_days_per_year)) if len(downside) else float("nan")
    sortino = _safe_div(float(rets.mean() * trading_days_per_year), downside_dev)

    drawdown = eq / eq.cummax() - 1.0
    max_dd = float(drawdown.min()) if len(drawdown) else float("nan")
    calmar = _safe_div(cagr, abs(max_dd)) if max_dd < 0 else float("nan")

    # Drawdown duration
    underwater = drawdown < 0
    dd_duration = 0
    cur = 0
    for flag in underwater:
        if flag:
            cur += 1
            dd_duration = max(dd_duration, cur)
        else:
            cur = 0

    trade_stats = compute_trade_stats(trades)

    return {
        "start_date": str(eq.index.min().date()),
        "end_date": str(eq.index.max().date()),
        "start_equity": start_eq,
        "end_equity": end_eq,
        "total_return": float(total_return),
        "cagr": float(cagr),
        "volatility": vol,
        "sharpe": float(sharpe),
        "sortino": float(sortino),
        "max_drawdown": max_dd,
        "max_drawdown_duration_days": int(dd_duration),
        "calmar": float(calmar),
        **trade_stats,
    }


def compute_trade_stats(trades: pd.DataFrame) -> dict[str, Any]:
    if trades is None or trades.empty:
        return {
            "n_trades": 0,
            "win_rate": float("nan"),
            "avg_win": float("nan"),
            "avg_loss": float("nan"),
            "profit_factor": float("nan"),
            "expectancy": float("nan"),
            "avg_holding_days": float("nan"),
            "total_net_pnl": 0.0,
            "total_costs": 0.0,
        }

    net = trades["net_pnl"].astype(float)
    wins = net[net > 0]
    losses = net[net <= 0]
    gross_wins = float(wins.sum()) if len(wins) else 0.0
    gross_losses = float((-losses).sum()) if len(losses) else 0.0

    return {
        "n_trades": int(len(trades)),
        "win_rate": float(len(wins) / len(trades)) if len(trades) else float("nan"),
        "avg_win": float(wins.mean()) if len(wins) else float("nan"),
        "avg_loss": float(losses.mean()) if len(losses) else float("nan"),
        "profit_factor": _safe_div(gross_wins, gross_losses),
        "expectancy": float(net.mean()),
        "avg_holding_days": float(trades["holding_days"].astype(float).mean()),
        "total_net_pnl": float(net.sum()),
        "total_costs": float(trades["costs"].astype(float).sum()),
    }
