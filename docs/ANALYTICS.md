# Stage 6 — Performance / risk analytics + benchmark comparison

## What it adds

On top of Milestone 1 core metrics:

| Block | Contents |
|---|---|
| Returns | Monthly mean/median, best/worst month, annual returns, rolling 1Y, skew/kurtosis |
| Risk | Max DD peak/trough dates, recovery time, time underwater %, downside deviation |
| Trades | MAE/MFE, profit concentration (best 5 / top 20%) |
| Benchmark | Excess return/CAGR, beta, alpha, correlation, tracking error, information ratio |

## Run

```powershell
python scripts/run_backtest.py --strategy strategies/defs/momentum_cross_section_v1.yaml
```

`summary.json` now contains `analytics.performance`, `analytics.trades`, and `analytics.benchmark`.

## Interpretation rule

Benchmark-beating CAGR on **current** NIFTY50 membership is not validation. Survivorship bias and lack of OOS/walk-forward still apply until Stage 7.
