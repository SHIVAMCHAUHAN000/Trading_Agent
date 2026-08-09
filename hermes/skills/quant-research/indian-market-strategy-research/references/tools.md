# Research tool reference

Invoke via:

```powershell
python scripts/hermes_tool_rpc.py --tool <name> --args '<json>'
```

Print machine schemas:

```powershell
python scripts/hermes_tool_rpc.py --schemas
```

## Tools

| Tool | Purpose | OOS-safe? |
|---|---|---|
| `get_strategy` | Load StrategySpec | yes |
| `get_data_version` | Latest dataset pointer | yes |
| `validate_data` | Data quality report | yes |
| `run_backtest` | Baseline simulator | yes |
| `calculate_metrics` | Performance/risk/benchmark | yes |
| `run_oos_test` | Frozen 70/30 OOS | yes (eval only) |
| `run_walk_forward` | Frozen WF folds | yes |
| `run_parameter_test` | Parameter grid | **IS only** |
| `run_cost_stress` | 1x–3x costs | yes |
| `run_monte_carlo` | Trade permutation MC | yes |
| `run_bootstrap` | Return bootstrap CIs | yes |
| `run_regime_analysis` | Subperiod stability | yes |
| `run_bias_check` | Bias flags | yes |
| `run_full_research` / `generate_report` | End-to-end dual report | yes |

## Example args

```json
{
  "strategy_path": "strategies/defs/momentum_cross_section_v1.yaml",
  "is_fraction": 0.7
}
```
