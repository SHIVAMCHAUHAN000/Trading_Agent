# Agent Contract — Indian Market Strategy Research & Backtesting Agent

**Version:** 0.1.0  
**Stage:** 1 — Agent definition  
**Status:** APPROVED (2026-03-29)  
**Scope:** Research and validation only. **No trade execution.**

Frozen V1 decisions live in `config/project_decisions.yaml`.

---

## 1. Purpose

This agent turns a **strategy hypothesis** into a complete, institutional-style **research and validation report** for Indian markets.

It does **not** try to prove a target win rate (e.g. 70%).  
It builds evidence, stress-tests assumptions, and reports whether results are meaningful, robust, and economically plausible — or should be rejected.

---

## 2. One-line job description

> Given a standardized strategy specification and historical market data, produce a reproducible research report covering performance, risk, validation, biases, and a clear research conclusion — without placing any orders.

---

## 3. Non-goals (explicit)

The agent **must not**:

| Non-goal | Reason |
|---|---|
| Place, route, or simulate live broker orders for trading | Execution is out of scope |
| Optimize parameters on out-of-sample data | Prevents leakage / overfitting |
| Guarantee a win-rate or return target | Targets are evaluation criteria, not design objectives |
| Treat win rate as the sole approval metric | Expectancy, risk-adjusted return, and robustness matter more |
| Overwrite raw historical data | Data integrity |
| Claim “edge” without economic rationale + validation | Avoid narrative overfitting |
| Expand to tick/HFT/options in V1 | Scope control |

---

## 4. Input contract

All research runs accept a single **Strategy Research Request**.

### 4.1 Required fields

| Field | Type | Description |
|---|---|---|
| `strategy_name` | string | Unique human-readable name for this experiment |
| `market` | enum | Market context (V1: `Indian_equities`) |
| `universe` | object | What instruments are eligible |
| `timeframe` | enum | V1: `daily` only |
| `entry` | object | Entry rules (machine-readable) |
| `exit` | object | Exit rules (machine-readable) |
| `position_sizing` | object | How capital is allocated |
| `costs` | object | Cost model configuration |
| `capital` | number | Starting capital in INR |
| `period` | object | Research window (`start`, `end`) |

### 4.2 Optional but recommended fields

| Field | Type | Description |
|---|---|---|
| `holding_period` | object | Min/max/target holding constraints |
| `benchmark` | string | Default for equities: `NIFTY50` (or appropriate index) |
| `execution` | object | Signal timing vs fill timing (e.g. close → next open) |
| `research_objective` | object | Soft targets (win rate, Sharpe, max DD) — **evaluation only** |
| `notes` | string | Economic hypothesis / rationale |
| `experiment_tags` | string[] | Labels for registry search |

### 4.3 Canonical example (YAML)

```yaml
strategy_name: momentum_test_001

market: Indian_equities
universe:
  type: NSE_equities
  # later: filters (liquidity, listing age, index membership)

timeframe: daily

entry:
  condition: 12_month_momentum > threshold
  parameters:
    lookback_days: 252
    threshold: 0.10

exit:
  condition: momentum_reversal
  parameters:
    exit_threshold: 0.0

position_sizing:
  method: equal_weight
  max_positions: 10

holding_period:
  # optional constraints; omit if exit rules fully define exits
  max_days: null

execution:
  signal_time: close
  execution_time: next_open

costs:
  brokerage: configured
  slippage_bps: configured
  spread_bps: configured

capital: 1000000

benchmark: NIFTY50

period:
  start: 2006-01-01
  end: 2026-01-01

research_objective:
  # Soft targets for reporting — NOT optimization objectives
  target_win_rate: 0.70
  prioritize:
    - expectancy
    - risk_adjusted_return
    - robustness
  forbid:
    - optimize_on_oos

notes: >
  Hypothesis: 12-month cross-sectional momentum persists in NSE equities
  after costs, with unstable performance across regimes.
```

### 4.4 Input rules

1. Natural language alone is **not** a valid backtest input. It must be compiled into this schema.
2. Missing required fields → reject request with a validation error (do not invent defaults silently for economic parameters).
3. Soft targets (e.g. 70% win rate) may be reported against, never used to auto-tune parameters on OOS.

Machine-readable schema: [`contracts/strategy_research_request.schema.yaml`](../contracts/strategy_research_request.schema.yaml)

---

## 5. Output contract

Every completed run returns a **Strategy Research Report** with two layers.

### 5.1 Layer 1 — Simple report (decision layer)

Plain language, for the human:

1. What is the strategy?
2. Why might it work? (economic story)
3. How did it perform?
4. How risky is it?
5. What breaks it?
6. Is the result robust?
7. Major warnings
8. Research conclusion: `REJECT` / `INCONCLUSIVE` / `PROMISING` / `VALIDATED_CANDIDATE`

### 5.2 Layer 2 — Full technical report (audit layer)

Must include:

| Section | Contents |
|---|---|
| Strategy explanation | Spec + assumptions + economic rationale |
| Data-quality report | Coverage, missingness, OHLC integrity, corporate-action flags |
| Backtest results | Equity curve summary, returns, costs net of model |
| Trade statistics | Trades, win rate, avg win/loss, profit factor, expectancy, holding period |
| Risk statistics | Vol, max DD, DD duration, recovery, downside deviation |
| Benchmark comparison | Excess return, alpha/beta, correlation, IR, tracking error |
| Out-of-sample results | Frozen-spec OOS metrics only |
| Walk-forward results | Rolling train→test summary |
| Parameter sensitivity | Surface / stability region (not a single lucky peak) |
| Cost sensitivity | 1× / 1.5× / 2× / 3× cost shocks |
| Regime analysis | Subperiod and/or regime-conditioned performance |
| Monte Carlo | DD / terminal equity / loss-streak distributions |
| Bootstrap | Confidence intervals around key metrics |
| Stress tests | Delay, remove best trades, vol shock, clustered losses |
| Bias checks | Look-ahead, survivorship, leakage, snooping flags |
| Overfitting assessment | Explicit judgment + evidence |
| Experiment metadata | Experiment ID, data version, code version, timestamps |
| Research conclusion | Decision + conditions + next tests |

### 5.3 Mandatory artifacts (machine outputs)

| Artifact | Description |
|---|---|
| `experiment_id` | e.g. `EXP-000001` |
| `equity_curve` | Timestamped equity series |
| `trade_log` | Entry/exit/PnL/costs/MAE/MFE |
| `metrics_table` | IS / OOS / WF metrics |
| `assumptions_log` | Every modeling assumption used |
| `warnings[]` | Structured warning codes |
| `conclusion` | Enum + rationale |

Machine-readable schema: [`contracts/strategy_research_report.schema.yaml`](../contracts/strategy_research_report.schema.yaml)

---

## 6. Research philosophy (binding)

1. **Evidence over targets.** A 70% win rate is a question to answer, not a result to force.
2. **Expectancy and risk first.** Win rate without payoff asymmetry is incomplete.
3. **Try to break the strategy.** Robustness > peak backtest Sharpe.
4. **Freeze before OOS.** Development data and evaluation data stay separated.
5. **Store failures.** Negative results are first-class experiment records.
6. **No silent magic.** Defaults that change economics must be explicit and logged.
7. **Reproducibility.** Same request + same data version + same code version → same report.

---

## 7. System boundaries

```text
YOU / Research brief
        ↓
Strategy Research Request (this contract)
        ↓
[Later stages] Data → Backtest → Analytics → Validation
        ↓
Strategy Research Report (this contract)
        ↓
YOU (decision) — never auto-trading
```

Hermes / LLM orchestration is **out of Stage 1**. It will sit on top only after the quantitative lab works.

---

## 8. V1 market scope

| In scope (V1) | Out of scope (later) |
|---|---|
| Indian equities / indices | Options strategies |
| Daily bars (OHLCV) | Tick / order-book / HFT |
| Cash equity-style backtests | Live execution / broker APIs |
| Configurable cost model | Full NSE microstructure realism |
| Benchmark comparison vs index | Multi-asset portfolio optimization |

---

## 9. Success criteria for Stage 1 (this document)

Stage 1 is complete when we agree on:

- [x] Agent purpose and non-goals
- [x] Required / optional input fields
- [x] Required output sections (simple + technical)
- [x] Binding research philosophy
- [x] V1 scope boundaries
- [x] Explicit approval to freeze this contract for Stage 2

---

## 10. Next stage

**Stage 2 — Project setup** (in progress after this approval)

- Create full repo layout
- Python 3.11 env, GitHub remote, config skeleton
- Placeholder modules (no full engines yet)
- Supabase schema sketch + local Parquet cache convention
