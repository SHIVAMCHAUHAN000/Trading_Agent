"""V2 strategy schema for single-symbol intraday / multi-market research."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class UniverseV2(BaseModel):
    type: str
    symbol: str | None = None
    symbols: list[str] | None = None

    @model_validator(mode="after")
    def _symbol_required(self) -> UniverseV2:
        if self.type in {"single_symbol", "XAUUSD"} and not self.symbol:
            raise ValueError("universe.symbol required for single_symbol")
        return self


class SessionSpec(BaseModel):
    name: str = "New_York_session"
    timezone: str = "Asia/Kolkata"
    start: str  # HH:MM
    end: str  # HH:MM


class RuleBlockV2(BaseModel):
    condition: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    # allow alternate exit shapes from draft YAMLs
    target: str | None = None
    stop_loss: dict[str, Any] | None = None


class PositionV2(BaseModel):
    method: str = "risk_based_sizing"
    risk_per_trade_pct: float = 2.0
    max_positions: int = 1
    parameters: dict[str, Any] = Field(default_factory=dict)


class PeriodV2(BaseModel):
    start: str | None = None
    end: str | None = None

    @field_validator("start", "end")
    @classmethod
    def _date_or_none(cls, value: str | None) -> str | None:
        if value is None or value in {"", "TBD", "null"}:
            return None
        if len(value) >= 10 and value[4] == "-" and value[7] == "-":
            return value[:10]
        raise ValueError("dates must be YYYY-MM-DD or null/TBD")


class StrategySpecV2(BaseModel):
    name: str
    version: str = "0.1.0"
    market: str
    asset_class: str | None = None
    universe: UniverseV2
    timeframe: str | None = None
    timeframes: dict[str, Any] = Field(default_factory=dict)
    session: SessionSpec | None = None
    liquidity_marking: dict[str, Any] = Field(default_factory=dict)
    sweep_definition: dict[str, Any] = Field(default_factory=dict)
    entry_sequence: dict[str, Any] = Field(default_factory=dict)
    entry: RuleBlockV2
    exit: RuleBlockV2 | dict[str, Any]
    position: PositionV2 = Field(default_factory=PositionV2)
    capital: float = 500_000
    benchmark: str | None = None
    period: PeriodV2 = Field(default_factory=PeriodV2)
    data_source: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _normalize_exit(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        exit_block = data.get("exit")
        if isinstance(exit_block, dict) and "condition" not in exit_block:
            # draft YAML uses target/stop_loss instead of condition
            data = dict(data)
            data["exit"] = {
                "condition": exit_block.get("target", "opposite_liquidity_level"),
                "parameters": {
                    "target": exit_block.get("target"),
                    "stop_loss": exit_block.get("stop_loss"),
                },
                "target": exit_block.get("target"),
                "stop_loss": exit_block.get("stop_loss"),
            }
        return data
