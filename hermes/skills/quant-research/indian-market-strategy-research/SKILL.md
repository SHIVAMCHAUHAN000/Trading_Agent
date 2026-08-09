---
name: indian-market-strategy-research
description: >
  Use when the user asks to research, backtest, validate, or stress-test an Indian
  equities strategy hypothesis (NIFTY50/NSE), including win-rate/expectancy/robustness
  questions. Produces institutional research reports without placing trades.
version: 1.0.0
metadata:
  hermes:
    tags: [quant, backtest, india, nifty50, research, no-execution]
    category: quant-research
---

# Indian Market Strategy Research

## When to Use

Use this skill when the user wants research/validation for an Indian-market strategy:

- "Research this momentum strategy on NIFTY50"
- "Does this have a 70% win rate after costs?"
- "Run OOS / walk-forward / robustness checks"
- "Give me a simple + technical research report"

**Never place trades. Research and validation only.**

## Project root

```text
C:\Users\shiva\OneDrive\Desktop\Trading Agent
```

Activate the project venv before commands:

```powershell
cd "C:\Users\shiva\OneDrive\Desktop\Trading Agent"
.\.venv\Scripts\Activate.ps1
```

## Hard research rules

1. Do **not** optimize parameters on out-of-sample data.
2. Prefer expectancy, risk-adjusted return, and robustness over win rate.
3. Treat 70% win rate as an evaluation question, not a design target.
4. Always mention survivorship bias when universe = current NIFTY50.
5. Store failures; do not hide negative results.

## Preferred procedure

### Fast path (recommended)

Run the full deterministic research workflow:

```powershell
python scripts/run_research_agent.py --strategy strategies/defs/momentum_cross_section_v1.yaml
```

Or via Hermes bridge:

```powershell
python scripts/run_hermes_bridge.py --mode deterministic --strategy strategies/defs/momentum_cross_section_v1.yaml
```

Read and present:

1. `SIMPLE_REPORT.md` (Layer 1 — plain language)
2. Key fields from `research_report.json` (Layer 2 — technical)

### Tool RPC path (step-by-step)

List tools:

```powershell
python scripts/hermes_tool_rpc.py --list
```

Call one tool:

```powershell
python scripts/hermes_tool_rpc.py --tool run_oos_test --args "{\"strategy_path\":\"strategies/defs/momentum_cross_section_v1.yaml\",\"is_fraction\":0.7}"
```

Useful tools:

- `validate_data`
- `run_backtest`
- `calculate_metrics`
- `run_oos_test`
- `run_walk_forward`
- `run_parameter_test`  (IS only)
- `run_cost_stress`
- `run_monte_carlo`
- `run_bootstrap`
- `run_bias_check`
- `run_full_research` / `generate_report`

For schema details, load: `references/tools.md`

## Output contract

Always return:

1. Simple conclusion (`REJECT` / `INCONCLUSIVE` / `PROMISING` / rarely `VALIDATED_CANDIDATE`)
2. Whether soft win-rate target was met on OOS
3. Major warnings (especially survivorship)
4. Paths to report artifacts

`VALIDATED_CANDIDATE` is blocked while survivorship bias remains unresolved.

## Pitfalls

- Missing dataset: run `python scripts/run_historical_pipeline.py --start 2015-01-01`
- Dead Yahoo tickers: refresh `config/universe_nifty50.yaml`
- LLM planner mode needs `OPENAI_API_KEY` or `OPENROUTER_API_KEY` (optional)
- Do not cherry-pick best IS parameter cell and silently retest on OOS

## Verification

```powershell
python scripts/hermes_tool_rpc.py --tool get_data_version
python -m pytest -q
```
