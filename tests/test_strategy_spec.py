"""Stage 4 strategy specification tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from strategies.loader import StrategySpecError, load_strategy_spec, parse_strategy_spec
from strategies.schema import StrategySpec

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "strategies" / "defs" / "momentum_cross_section_v1.yaml"


def test_example_strategy_loads():
    spec = load_strategy_spec(EXAMPLE)
    assert isinstance(spec, StrategySpec)
    assert spec.name == "momentum_cross_section_v1"
    assert spec.universe.type.value == "NIFTY50"
    assert spec.execution.long_only is True
    assert spec.timeframe.value == "daily"
    assert "optimize_on_oos" in spec.research_objective.forbid


def test_rejects_short_selling_in_v1():
    data = load_strategy_spec(EXAMPLE).model_dump(mode="json")
    data["execution"]["long_only"] = False
    with pytest.raises(StrategySpecError):
        parse_strategy_spec(data)


def test_rejects_custom_universe_without_symbols():
    data = load_strategy_spec(EXAMPLE).model_dump(mode="json")
    data["universe"] = {"type": "custom_symbols"}
    with pytest.raises(StrategySpecError):
        parse_strategy_spec(data)


def test_rejects_bad_date_format():
    data = load_strategy_spec(EXAMPLE).model_dump(mode="json")
    data["period"]["start"] = "01-01-2015"
    with pytest.raises(StrategySpecError):
        parse_strategy_spec(data)
