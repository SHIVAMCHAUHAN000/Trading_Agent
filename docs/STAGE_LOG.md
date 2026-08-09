# Stage log

## Stage 1 — Define the agent

**Status:** APPROVED  
**Artifacts:**

- `docs/AGENT_CONTRACT.md`
- `contracts/strategy_research_request.schema.yaml`
- `contracts/strategy_research_report.schema.yaml`

## Stage 2 — Set up project

**Status:** COMPLETE (awaiting user approval before Stage 3)  
**Goal:** Repo layout, Python 3.11 project config, GitHub remote, frozen decisions, placeholders only.

**Done:**

- Project path: `C:\Users\shiva\OneDrive\Desktop\Trading Agent`
- Package tree + placeholders
- `pyproject.toml` / `requirements.txt` / `.venv` on Python 3.11
- Frozen decisions + cost defaults + NIFTY50 universe stub
- Supabase schema sketch (`database/schema.sql`)
- Git initialized; remote `origin` → `https://github.com/SHIVAMCHAUHAN000/Trading_Agent.git`
- Stage 2 scaffold tests passing

**Pending from user (does not block Stage 3 start):**

- Supabase connection string / keys (`.env`)
- Confirm real starting capital (currently ₹10,00,000 placeholder)
- Initial git commit + push (say the word)

**Out of scope for Stage 2:**

- Data download / validation pipelines
- Backtest engine
- Hermes
