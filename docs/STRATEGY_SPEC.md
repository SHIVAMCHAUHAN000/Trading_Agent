# Stage 4 — Strategy specification

Every strategy must be a validated `StrategySpec` before it can enter the backtester.

## Why

- The engine must not interpret free-form natural language.
- Research agents compile hypotheses into this contract.
- Soft targets (e.g. 70% win rate) are evaluation-only and cannot authorize OOS optimization.

## Location

| Path | Role |
|---|---|
| `strategies/schema.py` | Pydantic model (source of truth) |
| `strategies/loader.py` | YAML load + validation |
| `strategies/defs/*.yaml` | Strategy definitions |
| `contracts/strategy_spec.schema.yaml` | Human/machine schema mirror |

## Example

```powershell
python -c "from strategies import load_strategy_spec; print(load_strategy_spec('strategies/defs/momentum_cross_section_v1.yaml'))"
```

## V1 constraints

- `timeframe: daily`
- `execution.long_only: true`
- `market: Indian_equities`
