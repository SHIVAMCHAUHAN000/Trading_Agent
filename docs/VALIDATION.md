# Stage 7 — Validation & anti-overfitting

## What runs

| Module | Window used for fitting/search | Window used for score |
|---|---|---|
| OOS (70/30) | None (params frozen) | IS metrics + OOS metrics |
| Walk-forward | None (params frozen in V1) | Each test fold |
| Parameter sensitivity | **IS only** | IS grid surface |
| Cost stress | None | Full sample at 1×/1.5×/2×/3× |

## Hard rules

1. Parameter grid search **never** sees OOS.
2. Soft targets (e.g. 70% win rate) are reported, not optimized.
3. `PROMISING` ≠ approved for trading.
4. Survivorship bias remains until point-in-time membership exists.

## Run

```powershell
python scripts/run_validation.py --strategy strategies/defs/momentum_cross_section_v1.yaml
```

Output: `reports/validation_<strategy>_<timestamp>/validation_report.json`
