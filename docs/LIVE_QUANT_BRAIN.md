# Personal Live Quant Brain — System Documentation

## 1. Overview & Architecture

The **Personal Live Quant Brain** is a production-grade live-market intelligence and decision-support platform designed to operate 24/7. It provides real-time quantitative analysis, market structure detection, observable liquidity mapping, multi-timeframe trend reconciliation, and evidence-grounded driver investigation across Indian markets (NSE Indices & Equities) and Global assets (Commodities, Crypto, FX).

```
                      ┌───────────────────────────┐
                      │    TELEGRAM USER CHAT     │
                      └─────────────┬─────────────┘
                                    │
                                    ▼
                      ┌───────────────────────────┐
                      │      FASTAPI GATEWAY      │
                      │       Shared REST API     │
                      └─────────────┬─────────────┘
                                    │
                     ┌──────────────┴──────────────┐
                     ▼                             ▼
        ┌─────────────────────────┐   ┌──────────────────────────┐
        │      AI ORCHESTRATOR    │   │  TRADINGVIEW WEBHOOKS    │
        │   Context Memory & NLP  │   │  Token Validated Alerts  │
        └────────────┬────────────┘   └─────────────┬────────────┘
                     │                              │
                     ▼                              ▼
        ┌────────────────────────────────────────────────────────┐
        │              MCP TOOL REGISTRY & RUNNER                │
        │    13 Registered Tools (Prices, Candles, News...)      │
        └────────────┬──────────────────────────────┬────────────┘
                     │                              │
                     ▼                              ▼
        ┌─────────────────────────┐   ┌──────────────────────────┐
        │    LIVE MARKET DATA     │   │   QUANT ANALYSIS ENGINE  │
        │  YFinance Feed + Cache  │   │  Structure, Liquidity,   │
        │  Session & Freshness    │   │  Momentum, Volatility,   │
        │  Disclaimers (No Fake)  │   │  MTF & Setups            │
        └─────────────────────────┘   └─────────────┬────────────┘
                                                    │
                                                    ▼
                                      ┌──────────────────────────┐
                                      │   PERSISTENT STORAGE     │
                                      │   Async SQLite / Postgres│
                                      │   Snapshots, History, TV │
                                      └──────────────────────────┘
```

---

## 2. Key Capabilities

### A. Real Quantitative Engine
1. **Market Structure**:
   - Identifies fractal swing points (Swing Highs & Swing Lows).
   - Detects Higher Highs (HH) + Higher Lows (HL) for Bullish trends, Lower Highs (LH) + Lower Lows (LL) for Bearish trends.
   - Detects Break of Structure (BOS), Change of Character (CHoCH), and range consolidations.
2. **Observable Liquidity Pools**:
   - Computes Previous Day High (PDH), Previous Day Low (PDL), Previous Week High (PWH), Previous Week Low (PWL).
   - Computes Current Session High and Session Low.
   - Detects Equal Highs (EQH) and Equal Lows (EQL) where resting stop orders pool.
   - Flags Liquidity Sweeps / Spring rejections.
   - Strict language rules: labels pools as "observable stop/liquidity area" or "potential liquidity concentration" rather than unsubstantiated claims.
3. **Momentum & Volume**:
   - RSI(14) with overbought/oversold and momentum regimes.
   - MACD(12,26,9) with acceleration and deceleration states.
   - EMA ribbons (9, 21, 50, 200).
   - Regular and hidden momentum divergence detection.
   - Relative Volume (RVOL) vs 20-period SMA, volume spikes, and volume-price analysis (accumulation vs distribution).
4. **Volatility**:
   - Average True Range (ATR 14) and ATR percentage.
   - Realized Volatility (rolling annualized log return std).
   - Volatility Regime: Compression / Squeeze vs Expansion.
5. **Multi-Timeframe Synthesis**:
   - Synthesizes 5m, 15m, 1h, and Daily timeframes.
   - Resolves conflicts explicitly (e.g., *"Daily trend is bullish, while 15m structure is bearish; consistent with tactical pullback"*).
6. **Market Drivers**:
   - Separates findings into `OBSERVED` (factual data), `INFERRED` (probabilistic transmission), and `UNKNOWN` (unconfirmed factors).
7. **Systematic Setup Evaluator**:
   - Status (`No setup`, `Developing`, `Validated`, `Invalidated`).
   - Bias, Trigger, Invalidation level, Targets, and Risk/Reward.

---

## 3. Supported Instruments & Market Segments

| Symbol | Name | Exchange | Segment | Currency |
|---|---|---|---|---|
| `NIFTY` | Nifty 50 Benchmark Index | NSE | Equity Index | INR |
| `BANKNIFTY` | Nifty Bank Index | NSE | Equity Index | INR |
| `FINNIFTY` | Nifty Financial Services | NSE | Equity Index | INR |
| `RELIANCE` | Reliance Industries Ltd | NSE | Equity | INR |
| `HDFCBANK` | HDFC Bank Ltd | NSE | Equity | INR |
| `ICICIBANK` | ICICI Bank Ltd | NSE | Equity | INR |
| `INFY` | Infosys Ltd | NSE | Equity | INR |
| `TCS` | Tata Consultancy Services | NSE | Equity | INR |
| `GOLD` | Gold Continuous Futures | COMEX/MCX | Commodity | USD |
| `SILVER` | Silver Continuous Futures | COMEX/MCX | Commodity | USD |
| `CRUDEOIL` | Light Sweet Crude Oil | NYMEX | Commodity | USD |
| `BTC` | Bitcoin USD | Global | Crypto | USD |
| `USDINR` | US Dollar to Indian Rupee | FX Spot | Forex | INR |
| `SPX` | S&P 500 Index | US | Global Index | USD |
| `INDIAVIX` | India Volatility Index | NSE | Volatility | INR |

---

## 4. How to Launch and Deploy

### Option 1: Native Process (Windows)
Double-click or run from PowerShell:
```powershell
.\start_brain.ps1
```
This starts the unified server at `http://127.0.0.1:8000`.

### Option 2: Native Process (Linux / macOS)
```bash
./start_brain.sh
```

### Option 3: Docker & Docker Compose
```bash
docker compose up --build -d
```
The application will start with restart policy `unless-stopped`, healthy container checks, and persistent SQLite storage mounted at `./data`.

---

## 5. Telegram Bot Setup

1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow the prompts to create your bot. Copy the HTTP API token.
3. Open your `.env` file and set:
   ```env
   TELEGRAM_BOT_TOKEN=your_token_here
   ```
4. Secure your bot by allowing only your Telegram account:
   - Message [@userinfobot](https://t.me/userinfobot) to find your numeric User ID.
   - Add your ID to `.env`:
     ```env
     AUTHORIZED_TELEGRAM_USERS=123456789
     ```
   - Unauthorized users attempting to interact with the bot will receive a polite access restricted rejection and their attempt will be logged in the security audit table.
5. Start or restart the platform (`.\start_brain.ps1` or `docker compose restart`).
6. Open your bot in Telegram and type `/start`.

---

## 6. TradingView Webhook Setup

TradingView alerts can be forwarded directly into the Quant Brain:

1. In TradingView, create an Alert on any chart.
2. In the Alert Actions, enable **Webhook URL** and enter:
   ```
   http://YOUR_SERVER_IP:8000/api/v1/tradingview/webhook
   ```
3. Set the Alert Message to JSON format:
   ```json
   {
     "secret": "tv_secret_webhook_pass_123",
     "symbol": "NIFTY",
     "timeframe": "15m",
     "signal": "BOS_BULLISH",
     "price": 24850.50,
     "indicator": "Smart Money Concepts",
     "message": "15m Bullish BOS confirmed above 24800"
   }
   ```
4. The Quant Brain validates the secret token, logs the alert, and makes it available to the AI reasoning engine via `get_tradingview_signals`.

---

## 7. MCP Tools Catalog

The AI Quant Brain routes queries through 13 Model Context Protocol tools:

1. `get_current_price`: Live quote, session change, day high/low, freshness metadata.
2. `get_historical_candles`: OHLCV series for 1m, 5m, 15m, 1h, 1d intervals.
3. `get_market_structure`: Swing highs/lows, BOS, CHoCH, trend regime.
4. `get_liquidity_zones`: PDH, PDL, session levels, equal highs/lows, sweeps.
5. `get_momentum_and_volume`: RSI(14), MACD, EMA alignments, RVOL, volume spikes.
6. `get_volatility_metrics`: ATR(14), realized volatility, squeeze/expansion regime.
7. `get_multi_timeframe_analysis`: Cross-timeframe trend matrix and conflict explanation.
8. `get_market_breadth`: Advance/decline count and ratio for benchmark universe.
9. `get_macro_overview`: USD/INR, Gold, Silver, Crude, SPX, India VIX.
10. `get_tradingview_signals`: Recent alerts ingested from TradingView webhooks.
11. `get_market_drivers`: Evidence investigation into Observed vs Inferred vs Unknown.
12. `get_trading_setup`: Systematic setup evaluation (Status, Bias, Trigger, Targets, R:R).
13. `get_market_news`: Verified headlines from connected financial sources.

---

## 8. Verification & Test Suite

Run the full automated test suite:
```powershell
.\.venv\Scripts\python.exe -m pytest
```
All 51 unit, integration, and quantitative tests pass, covering:
- Market structure detection and swing identification
- Observable liquidity pool calculations
- Momentum, RSI, MACD, and divergence calculations
- Volume RVOL and volume-price confirmation
- Volatility ATR and compression detection
- Market session awareness (IST market hours, pre-market, closed, weekend)
- Data freshness monitoring and stale-data prevention
- API endpoints (`/health`, `/connections`, `/chat`, `/market/summary`, `/tradingview/webhook`, `/market/watchlist`)
- Legacy research agent backtesting and analytics suite
