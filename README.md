# Personal Live Quant Brain & Trading Agent

> **24/7 Live-Market Quantitative Intelligence & Decision Support Platform**
> Indian Markets (NSE Indices & Equities) • Global Assets (Gold, Silver, Crude, BTC, FX) • Telegram Bot • MCP Tools • Web Dashboard

For research and market intelligence only. **No trade execution.**

---

## ⚡ Quick Start: Launch Live Quant Brain

### Native Launch (Windows PowerShell)
```powershell
.\start_brain.ps1
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** for the Web Dashboard & AI Quant Chat.

### Native Launch (Linux / macOS)
```bash
./start_brain.sh
```

### Docker Compose
```bash
docker compose up --build -d
```

### Run All 51 Tests
```powershell
.\.venv\Scripts\python.exe -m pytest
```

Full System Guide: [`docs/LIVE_QUANT_BRAIN.md`](docs/LIVE_QUANT_BRAIN.md)

---

## Legacy Research & Backtesting Suite

## Frozen V1 decisions

- **Python:** 3.11
- **Data:** yfinance (`.NS` tickers), NIFTY50 universe from `2015-01-01`
- **Prices:** adjusted close / corporate actions via yfinance
- **Benchmark:** NIFTY50 (`^NSEI`)
- **DB:** Supabase Postgres (credentials later); local Parquet cache allowed
- **Portfolio:** long-only, default capital ₹10,00,000 (**placeholder**)
- **Validation:** 70/30 IS/OOS + walk-forward
- **Costs:** conservative Indian cash-equity defaults in `config/cost_defaults.yaml`
- **Hermes:** skill + RPC bridge (runtime optional)

## Docs / contracts

- [`docs/AGENT_CONTRACT.md`](docs/AGENT_CONTRACT.md)
- [`docs/STAGE_LOG.md`](docs/STAGE_LOG.md)
- [`config/project_decisions.yaml`](config/project_decisions.yaml)
- [`contracts/`](contracts/)

## Setup (after Python 3.11 is installed)

```powershell
cd "C:\Users\shiva\OneDrive\Desktop\Trading Agent"
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
copy .env.example .env
```

## Historical data (Stage 3)

```powershell
python scripts/run_historical_pipeline.py --start 2015-01-01
```

Details: [`docs/DATA_LAYER.md`](docs/DATA_LAYER.md) · latest pointer: [`config/latest_dataset.yaml`](config/latest_dataset.yaml)

## Strategy specification (Stage 4)

Details: [`docs/STRATEGY_SPEC.md`](docs/STRATEGY_SPEC.md) · example: [`strategies/defs/momentum_cross_section_v1.yaml`](strategies/defs/momentum_cross_section_v1.yaml)

## Backtest (Stage 5)

```powershell
python scripts/run_backtest.py --strategy strategies/defs/momentum_cross_section_v1.yaml
```

Details: [`docs/BACKTEST_ENGINE.md`](docs/BACKTEST_ENGINE.md) · analytics: [`docs/ANALYTICS.md`](docs/ANALYTICS.md)

## Validation (Stage 7)

```powershell
python scripts/run_validation.py --strategy strategies/defs/momentum_cross_section_v1.yaml
```

Details: [`docs/VALIDATION.md`](docs/VALIDATION.md)

## Research agent (Stage 8)

```powershell
python scripts/run_research_agent.py --strategy strategies/defs/momentum_cross_section_v1.yaml
```

Details: [`docs/RESEARCH_AGENT.md`](docs/RESEARCH_AGENT.md)

## Hermes bridge (Stage 9)

```powershell
python scripts/run_hermes_bridge.py --mode deterministic
python scripts/hermes_tool_rpc.py --list
powershell -ExecutionPolicy Bypass -File scripts\install_hermes_skill.ps1
```

Details: [`docs/HERMES.md`](docs/HERMES.md)

## Dashboard (Stage 10)

Research runs now write `dashboard.html` next to the JSON/Markdown reports.

```powershell
python scripts/render_dashboard.py reports\_stage9_bridge\research_report.json
```

## Milestone rule

Do not start the next stage until the current stage works and is approved.
