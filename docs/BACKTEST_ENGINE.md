# Stage 5 — Backtesting engine (Milestone 1)

## Flow

```text
StrategySpec + processed bars
        ↓
Signal (monthly cross-sectional momentum)
        ↓
Execution (next open)
        ↓
Costs (configurable Indian cash-equity model)
        ↓
Portfolio mark-to-market
        ↓
equity_curve + trades + metrics
```

## Run

```powershell
cd "C:\Users\shiva\OneDrive\Desktop\Trading Agent"
.\.venv\Scripts\Activate.ps1
python scripts/run_backtest.py --strategy strategies/defs/momentum_cross_section_v1.yaml
```

Outputs land in `reports/<strategy>_<timestamp>/`:

- `equity_curve.csv`
- `trades.csv`
- `summary.json`

## Metrics included

Total return, CAGR, volatility, Sharpe, Sortino, max drawdown, drawdown duration, Calmar, trades, win rate, avg win/loss, profit factor, expectancy, holding period, total costs.

## Important research warnings

- Current NIFTY50 membership ⇒ **survivorship bias**
- Example momentum result is **not** a validated edge
- Soft win-rate targets are reported, not optimized for
- Open positions at the end mean closed-trade PnL ≠ full equity change
