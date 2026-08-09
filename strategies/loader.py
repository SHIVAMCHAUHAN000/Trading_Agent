"""Load and validate StrategySpec YAML/JSON files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from strategies.schema import StrategySpec

ROOT = Path(__file__).resolve().parents[1]
STRATEGIES_DIR = ROOT / "strategies"


class StrategySpecError(ValueError):
    """Raised when a strategy file is missing or invalid."""


def load_strategy_dict(path: str | Path) -> dict[str, Any]:
    strategy_path = Path(path)
    if not strategy_path.exists():
        raise StrategySpecError(f"Strategy file not found: {strategy_path}")
    data = yaml.safe_load(strategy_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise StrategySpecError("Strategy file must be a YAML/JSON object")
    return data


def parse_strategy_spec(data: dict[str, Any]) -> StrategySpec:
    try:
        return StrategySpec.model_validate(data)
    except ValidationError as exc:
        raise StrategySpecError(str(exc)) from exc


def load_strategy_spec(path: str | Path) -> StrategySpec:
    return parse_strategy_spec(load_strategy_dict(path))


def strategy_to_dict(spec: StrategySpec) -> dict[str, Any]:
    return spec.model_dump(mode="json")


def list_strategy_files(directory: str | Path | None = None) -> list[Path]:
    root = Path(directory) if directory else STRATEGIES_DIR / "defs"
    if not root.exists():
        return []
    return sorted(root.glob("*.yaml")) + sorted(root.glob("*.yml"))
