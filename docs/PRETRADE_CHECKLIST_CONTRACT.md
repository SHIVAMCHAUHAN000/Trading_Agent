# Pre-Trade Knowledge Checklist Agent — Contract (DRAFT, awaiting approval)

**Version:** 0.1.0
**Status:** DRAFT — not yet approved, not yet built
**Relationship to existing stages:** A new, separate agent — not the backtester (Stage 5-8) and not necessarily "Hermes" (Stage 9 in the stage log). Decide at the end of this doc how it should be labeled.

---

## 1. Purpose

Your strategy-testing agent (Stages 1-8) answers: *"Does this strategy idea have edge, historically?"*

This agent answers a different question, asked at the moment of a specific trade: *"Have I checked everything a disciplined trader is supposed to check, right now, before I click buy/sell?"*

It is a **checklist and knowledge-aggregation layer**, not a predictor. It doesn't tell you whether the trade will win. It tells you whether you're taking it with full information — and refuses to let you skip a category silently.

---

## 2. One-line job description

> Given a proposed trade (instrument, direction, entry/stop/target, strategy reference), pull together every category of information a professional trader checks beforehand, flag anything missing or unfavorable, and return a GO / CAUTION / NO-GO verdict with full supporting detail — never a silent pass.

---

## 3. Non-goals (explicit)

| Non-goal | Reason |
|---|---|
| Predict win probability | That's the backtester/research agent's job (Stages 5-8), using historical evidence |
| Place or route any order | Same execution boundary as the rest of this project — research/readiness only |
| Replace your judgment | This surfaces information; you still decide |
| Guarantee you won't miss something novel | It checks known categories; markets can still surprise you |

---

## 4. The knowledge categories (the actual core of this system)

Every trade gets checked against all of these before a verdict is issued. Each category has a pass/warn/fail state.

### 4.1 Setup validity
- Does this trade actually match a defined strategy's entry rules (references the exact strategy spec file, e.g. `gold_multi_tf_range_v1.yaml`)?
- Or is this a discretionary trade with no written rule behind it? (Flag loudly — this is how most bad trades happen.)

### 4.2 Multi-timeframe context
- Trend/range state on higher timeframes (1D, 4H) — is this trade with or against the higher-timeframe structure?
- Key support/resistance levels nearby that could interfere before the target is reached.

### 4.3 Volatility & regime
- Current ATR vs its recent average — is volatility unusually high (news-driven, dangerous for normal stops) or unusually low (breakout risk / stops too tight)?
- Is the market trending or choppy right now — does that match what this strategy needs to work?

### 4.4 Session & liquidity
- Is this the session the strategy was designed for (e.g. NY session 18:30-21:30 IST)?
- Is the spread normal for this instrument/time, or wide (thin liquidity, pre-news, holiday)?

### 4.5 Macro / news calendar
- Any high-impact news scheduled inside the trade's expected holding window (NFP, CPI, FOMC/Fed rate decisions, geopolitical events)? For gold specifically: real yields direction, DXY movement, upcoming central bank meetings.
- This is a genuine data source gap right now — needs an economic calendar feed (see open questions).

### 4.6 Correlation & portfolio risk
- Any other open positions correlated with this one (e.g. already long gold via another setup, or short DXY)?
- Total portfolio risk ("heat") if this trade is added — does it breach a max concurrent risk limit?

### 4.7 Risk & position sizing math
- Stop distance × position size = risk amount — does it actually equal the intended % of capital (e.g. 2%)?
- Reward-to-risk ratio — does it clear your minimum threshold (e.g. at least 1.5:1 or 2:1)?

### 4.8 Trade plan completeness
- Exact entry price, stop price, target price(s) written down — not vague.
- Invalidation condition: what exact price/event proves this idea wrong?
- One-line written thesis: why this trade, in your own words.

### 4.9 Behavioral / psychological check
- Short forced self-check, e.g.: "Am I entering this because of the plan, or because of a recent loss/win?" "Have I already lost my daily limit?" "Am I sized normally, or oversized because I feel confident?"
- This is a checklist for you to answer honestly — the system can't detect your emotional state, but it can force the question every time so it's never skipped.

### 4.10 Broker / execution mechanics
- Correct symbol, correct lot size for the calculated position size, margin available, order type.
- Expected slippage given current spread/volatility.

### 4.11 Post-trade logging requirement
- What must be recorded once the trade is taken (entry rationale, screenshot/chart state, checklist result) so it feeds a trade journal — this is what eventually lets you or Hermes learn from a growing history of decisions, not just backtests.

---

## 5. Output contract

### 5.1 Verdict enum
- `GO` — all categories pass
- `GO_WITH_CAUTION` — passes, but one or more non-critical warnings (e.g. news in 2 hours, slightly wide spread)
- `NO_GO` — a critical category fails (e.g. no written stop, risk math doesn't match intended %, major news in next 15 minutes)

### 5.2 Report layers (same pattern as your Stage 8 research report)
- **Layer 1 — Simple checklist**: pass/warn/fail per category, plain language, verdict.
- **Layer 2 — Full detail**: every number, source, and calculation behind each category, for audit/review.

---

## 6. Open questions before this can be built

1. **Where does this sit?** As its own new agent (e.g. `agents/readiness_agent/`), or as a module Hermes calls before presenting a trade idea to you? Your call.
2. **News calendar data source** — this needs a real economic calendar feed. Free options exist (e.g. Forex Factory calendar scraping, TradingEconomics free tier) but need picking and building.
3. **When does this run?** Only for live/paper trading going forward, or also retroactively checked against historical backtest trades (harder — needs historical news calendar data too)?
4. **Correlation/portfolio check** — only relevant once you're tracking multiple open positions somewhere (needs a simple positions log, likely in your Supabase DB).
5. **Behavioral check** — purely a self-answered form, or do you want it to pull anything automatic (e.g. "3 losses today" from a trade log)?

---

## 7. Suggested build order (once you approve the categories above)

1. Trade plan schema (entry/stop/target/thesis/strategy reference) — the input contract.
2. Risk & position-sizing math check (fully automatable, no external data needed) — quick win.
3. Multi-timeframe + volatility/regime check (reuses data you already pull for backtesting).
4. Session/liquidity check (reuses session logic from `liquidity_sweep_ny_session_v1.yaml`).
5. News calendar integration (new data source — needs your decision from open question 2).
6. Correlation/portfolio check (needs a live positions log).
7. Behavioral checklist + logging (simplest to add, no new data needed).
