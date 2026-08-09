"""Stage 2 smoke checks — project scaffold only."""

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_required_paths_exist():
    required = [
        "docs/AGENT_CONTRACT.md",
        "contracts/strategy_research_request.schema.yaml",
        "contracts/strategy_research_report.schema.yaml",
        "config/project_decisions.yaml",
        "config/cost_defaults.yaml",
        "config/universe_nifty50.yaml",
        "database/schema.sql",
        "pyproject.toml",
        ".env.example",
        "data/raw/.gitkeep",
    ]
    missing = [p for p in required if not (ROOT / p).exists()]
    assert missing == [], f"Missing Stage 2 files: {missing}"


def test_project_decisions_match_checklist():
    data = yaml.safe_load((ROOT / "config/project_decisions.yaml").read_text(encoding="utf-8"))
    assert data["project"]["python"] == "3.11"
    assert data["data"]["source"] == "yfinance"
    assert data["data"]["universe_v1"] == "NIFTY50"
    assert data["data"]["history_start"] == "2015-01-01"
    assert data["storage"]["database"] == "supabase_postgres"
    assert data["agent"]["trade_execution"] is False
    assert data["agent"]["long_only_v1"] is True
    assert data["research_defaults"]["is_oos_split"] == "70/30"
    assert data["orchestration"]["hermes"] in {"later", "skill_bridge"}
