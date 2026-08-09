# Trading Agent

**Indian Market Strategy Research & Backtesting Agent**

Research and validation only. **No trade execution.**

## Status

| Stage | Description | Status |
|---|---|---|
| 1 | Define the agent (contract) | **Done / APPROVED** |
| 2 | Set up project | **Done** |
| 3 | Historical-data system | **Done (awaiting approval)** |
| 4 | Strategy specification | Not started |
| 5 | Backtesting engine | Not started |
| 6 | Performance / risk analytics | Not started |
| 7 | Validation & anti-overfitting | Not started |
| 8 | AI research agent | Not started |
| 9 | Connect through Hermes | Later |
| 10 | Research dashboard / report | Not started |

## Frozen V1 decisions

- **Python:** 3.11
- **Data:** yfinance (`.NS` tickers), NIFTY50 universe from `2015-01-01`
- **Prices:** adjusted close / corporate actions via yfinance
- **Benchmark:** NIFTY50 (`^NSEI`)
- **DB:** Supabase Postgres (credentials later); local Parquet cache allowed
- **Portfolio:** long-only, default capital ₹10,00,000 (**placeholder**)
- **Validation:** 70/30 IS/OOS + walk-forward
- **Costs:** conservative Indian cash-equity defaults in `config/cost_defaults.yaml`
- **Hermes:** deferred

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

## Milestone rule

Do not start the next stage until the current stage works and is approved.
