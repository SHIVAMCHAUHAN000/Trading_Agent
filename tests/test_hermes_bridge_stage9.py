"""Stage 9 Hermes bridge tests."""

from __future__ import annotations

import json
from pathlib import Path

from agents.hermes_bridge.dispatcher import dispatch_tool
from agents.hermes_bridge.planner import llm_configured
from agents.hermes_bridge.tool_schemas import TOOL_SCHEMAS, list_tool_names

ROOT = Path(__file__).resolve().parents[1]
STRATEGY = ROOT / "strategies" / "defs" / "momentum_cross_section_v1.yaml"
SKILL = ROOT / "hermes" / "skills" / "quant-research" / "indian-market-strategy-research" / "SKILL.md"


def test_tool_schemas_cover_expected_names():
    names = set(list_tool_names())
    for required in [
        "get_strategy",
        "run_backtest",
        "run_oos_test",
        "run_walk_forward",
        "run_parameter_test",
        "run_cost_stress",
        "run_full_research",
        "generate_report",
    ]:
        assert required in names
    assert len(TOOL_SCHEMAS) >= 10


def test_dispatch_get_strategy_and_data_version():
    out = dispatch_tool("get_strategy", {"strategy_path": str(STRATEGY)})
    assert out["ok"] is True
    assert out["result"]["name"] == "momentum_cross_section_v1"

    ver = dispatch_tool("get_data_version", {})
    assert ver["ok"] is True
    assert "dataset_id" in ver["result"]


def test_dispatch_unknown_tool():
    out = dispatch_tool("not_a_real_tool", {})
    assert out["ok"] is False


def test_hermes_skill_file_exists_and_has_frontmatter():
    text = SKILL.read_text(encoding="utf-8")
    assert text.startswith("---")
    assert "name: indian-market-strategy-research" in text
    assert "Never place trades" in text or "never place trades" in text.lower()


def test_llm_configured_helper_is_bool():
    assert isinstance(llm_configured(), bool)


def test_tool_names_json_serializable():
    assert "run_full_research" in json.dumps(list_tool_names())
