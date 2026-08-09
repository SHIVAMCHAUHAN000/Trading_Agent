# Stage 3 — Historical data layer

## Pipeline

```text
yfinance
   ↓
data/raw/yfinance/<dataset_id>/   (immutable Parquet + META.json)
   ↓
validator (structural + financial checks)
   ↓
data/processed/yfinance/<dataset_id>/bars.parquet
   + data_quality_report.json
```

## Commands

```powershell
cd "C:\Users\shiva\OneDrive\Desktop\Trading Agent"
.\.venv\Scripts\Activate.ps1
python scripts/run_historical_pipeline.py --start 2015-01-01
```

## Rules

1. Never overwrite an existing raw `dataset_id`.
2. Cleaning writes only to `data/processed/`.
3. Current NIFTY50 membership ≠ point-in-time membership (survivorship bias flagged in quality report).
4. Supabase is for catalog/experiments later; local Parquet is the Stage 3 source of truth.

## Latest dataset

See `config/latest_dataset.yaml`.
