# Stage 9 — Hermes connection

Hermes is **not required** to run research. The quant lab works through deterministic CLIs. Stage 9 adds:

1. In-repo Hermes skill (`hermes/skills/.../SKILL.md`)
2. Tool RPC (`scripts/hermes_tool_rpc.py`)
3. Optional LLM planner (`scripts/run_hermes_bridge.py --mode llm`)
4. Skill installer for `~/.hermes/skills`

## Modes

| Mode | When to use | Command |
|---|---|---|
| Deterministic | Default, no API key | `python scripts/run_hermes_bridge.py --mode deterministic` |
| LLM planner | `OPENAI_API_KEY` or `OPENROUTER_API_KEY` set | `python scripts/run_hermes_bridge.py --mode llm` |
| Hermes Agent | Nous Hermes installed | Install skill, then ask Hermes to research a strategy |

## Install Hermes skill locally

```powershell
cd "C:\Users\shiva\OneDrive\Desktop\Trading Agent"
powershell -ExecutionPolicy Bypass -File scripts\install_hermes_skill.ps1
```

## Install Hermes Agent (optional)

Hermes is not bundled with this repo. If you want the Nous Hermes runtime:

- Docs: https://hermes-agent.org/
- After install, run `scripts\install_hermes_skill.ps1` and start a new Hermes session.

You can also point an OpenAI-compatible Hermes endpoint at the bridge via:

```text
HERMES_API_KEY=...
HERMES_BASE_URL=...
HERMES_BRIDGE_MODEL=...
```

## Tool list

```powershell
python scripts/hermes_tool_rpc.py --list
```
