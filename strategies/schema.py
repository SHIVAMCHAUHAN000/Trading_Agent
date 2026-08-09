"""Canonical Strategy Specification for the research lab (Stage 4)."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class Market(str, Enum):
    INDIAN_EQUITIES = "Indian_equities"


class Timeframe(str, Enum):
    DAILY = "daily"


class UniverseType(str, Enum):
    NSE_EQUITIES = "NSE_equities"
    NSE_INDEX = "NSE_index"
    CUSTOM_SYMBOLS = "custom_symbols"
    NIFTY50 = "NIFTY50"


class PositionSizingMethod(str, Enum):
    EQUAL_WEIGHT = "equal_weight"
    FIXED_FRACTION = "fixed_fraction"
    VOLATILITY_TARGET = "volatility_target"
    CUSTOM = "custom"


class SignalTime(str, Enum):
    CLOSE = "close"
    OPEN = "open"


class ExecutionTime(str, Enum):
    SAME_CLOSE = "same_close"
    NEXT_OPEN = "next_open"
    NEXT_CLOSE = "next_close"


class UniverseSpec(BaseModel):
    type: UniverseType
    symbols: list[str] | None = None
    filters: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _custom_requires_symbols(self) -> UniverseSpec:
        if self.type == UniverseType.CUSTOM_SYMBOLS and not self.symbols:
            raise ValueError("universe.symbols required when type=custom_symbols")
        return self


class RuleBlock(BaseModel):
    """Machine-readable entry/exit rule. Natural language alone is not valid."""

    condition: str = Field(..., min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)


class PositionSizingSpec(BaseModel):
    method: PositionSizingMethod = PositionSizingMethod.EQUAL_WEIGHT
    max_positions: int = Field(default=10, ge=1)
    parameters: dict[str, Any] = Field(default_factory=dict)


class HoldingPeriodSpec(BaseModel):
    min_days: int | None = Field(default=None, ge=0)
    max_days: int | None = Field(default=None, ge=1)
    target_days: int | None = Field(default=None, ge=1)


class ExecutionSpec(BaseModel):
    signal_time: SignalTime = SignalTime.CLOSE
    execution_time: ExecutionTime = ExecutionTime.NEXT_OPEN
    long_only: bool = True


class CostModelSpec(BaseModel):
    """References cost config; concrete defaults live in config/cost_defaults.yaml."""

    model_id: str = "indian_cash_equity_conservative_v1"
    brokerage: str | float | None = "configured"
    slippage_bps: float | None = None
    spread_bps: float | None = None
    overrides: dict[str, Any] = Field(default_factory=dict)


class PeriodSpec(BaseModel):
    start: str
    end: str | None = None

    @field_validator("start", "end")
    @classmethod
    def _date_like(cls, value: str | None) -> str | None:
        if value is None:
            return value
        # Light check; full calendar validation belongs to the engine.
        if len(value) != 10 or value[4] != "-" or value[7] != "-":
            raise ValueError("dates must be YYYY-MM-DD")
        return value


class ResearchObjectiveSpec(BaseModel):
    """Soft evaluation targets only — never used to optimize on OOS."""

    target_win_rate: float | None = Field(default=None, ge=0, le=1)
    prioritize: list[str] = Field(
        default_factory=lambda: ["expectancy", "risk_adjusted_return", "robustness"]
    )
    forbid: list[str] = Field(default_factory=lambda: ["optimize_on_oos"])


class StrategySpec(BaseModel):
    """
    Standardized strategy contract consumed by the backtester.

    The research agent may draft this from a hypothesis, but the engine
    only accepts this structured form.
    """

    name: str = Field(..., min_length=1)
    version: str = "0.1.0"
    market: Market = Market.INDIAN_EQUITIES
    universe: UniverseSpec
    timeframe: Timeframe = Timeframe.DAILY
    signal: dict[str, Any] = Field(default_factory=dict)
    entry: RuleBlock
    exit: RuleBlock
    position: PositionSizingSpec = Field(default_factory=PositionSizingSpec)
    holding_period: HoldingPeriodSpec | None = None
    execution: ExecutionSpec = Field(default_factory=ExecutionSpec)
    cost_model: CostModelSpec = Field(default_factory=CostModelSpec)
    capital: float = Field(default=1_000_000, gt=0)
    benchmark: str = "NIFTY50"
    period: PeriodSpec
    research_objective: ResearchObjectiveSpec = Field(default_factory=ResearchObjectiveSpec)
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _v1_constraints(self) -> StrategySpec:
        if self.timeframe != Timeframe.DAILY:
            raise ValueError("V1 only supports timeframe=daily")
        if not self.execution.long_only:
            raise ValueError("V1 is long-only; set execution.long_only=true")
        return self


StrategySpecDict = dict[str, Any]
