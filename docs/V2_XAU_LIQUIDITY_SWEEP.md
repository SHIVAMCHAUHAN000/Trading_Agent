# V2 — XAUUSD NY liquidity-sweep lab

## What shipped

| Piece | Path |
|---|---|
| 1m data pipeline | `market_data/xau_download.py`, `scripts/run_xau_1m_pipeline.py` |
| V2 schema/loader | `strategies/schema_v2.py`, `strategies/loader_v2.py` |
| Sweep engine | `backtesting/engine_v2/liquidity_sweep.py` |
| Research runner | `scripts/run_liquidity_sweep_research.py` |
| Strategy | `strategies/defs/liquidity_sweep_ny_session_v1.yaml` |

## Run

```powershell
cd "C:\Users\shiva\OneDrive\Desktop\Trading Agent"
.\.venv\Scripts\Activate.ps1
python scripts/run_xau_1m_pipeline.py --source yahoo --yahoo-period 7d
python scripts/run_liquidity_sweep_research.py --strategy strategies/defs/liquidity_sweep_ny_session_v1.yaml
```

Then open the printed `dashboard.html`.

## Data reality

- **Yahoo `GC=F` 1m:** works now, ~7 days only → smoke tests / `INCONCLUSIVE`
- **Dukascopy:** preferred for multi-month history; currently rate-limited/unreachable from this network (`503` / timeouts). Downloader is ready: `--source dukascopy --duka-days 30`

## Not done yet (next)

- Multi-month Dukascopy pull when network allows
- Spread/commission cost model for gold
- V2 OOS / walk-forward
- DST-aware NY session mapping
