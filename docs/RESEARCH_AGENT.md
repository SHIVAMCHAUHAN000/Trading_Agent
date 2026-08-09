# Stage 8 — AI research agent (deterministic workflow)

Hermes wiring is **Stage 9**. Stage 8 ships the research workflow and tool layer an LLM/Hermes agent will call.

## Workflow

```text
Receive Strategy
 → Validate Data
 → Baseline Backtest
 → Analytics
 → Validation Suite (OOS / WF / sensitivity / costs)
 → Regime + Bootstrap + Monte Carlo
 → Bias Checks
 → Layer-1 + Layer-2 Report
 → Experiment Registry append
```

## Tools

`get_strategy`, `get_data`, `validate_data`, `run_backtest`, `calculate_metrics`, `run_validation`, `run_regime_analysis`, `run_bootstrap`, `run_monte_carlo`, `run_bias_check`, `generate_report` (via workflow).

## Run

```powershell
python scripts/run_research_agent.py --strategy strategies/defs/momentum_cross_section_v1.yaml
```

Outputs:

- `SIMPLE_REPORT.md` — Layer 1
- `research_report.json` — Layer 2 + artifacts
- `equity_curve.csv`, `trades.csv`
- `reports/experiment_registry.jsonl`

## Conclusion policy

Survivorship bias is always flagged critical today, so the agent will **not** emit `VALIDATED_CANDIDATE` until point-in-time membership exists.
