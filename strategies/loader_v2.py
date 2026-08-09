"""Load V2 strategy YAML files."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from strategies.schema_v2 import StrategySpecV2


class StrategySpecV2Error(ValueError):
    pass


def load_strategy_spec_v2(path: str | Path) -> StrategySpecV2:
    p = Path(path)
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise StrategySpecV2Error("Strategy file must be a mapping")
    try:
        return StrategySpecV2.model_validate(data)
    except ValidationError as exc:
        raise StrategySpecV2Error(str(exc)) from exc
