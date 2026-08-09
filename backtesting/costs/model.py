"""Configurable transaction cost model (Indian cash-equity research defaults)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COST_PATH = ROOT / "config" / "cost_defaults.yaml"


@dataclass(frozen=True)
class CostConfig:
    model_id: str
    brokerage_bps: float
    stt_bps: float
    exchange_charges_bps: float
    gst_on_charges_pct: float
    stamp_duty_bps: float
    slippage_bps: float
    spread_bps: float
    multiplier: float = 1.0

    def scaled(self, multiplier: float) -> CostConfig:
        return CostConfig(
            model_id=self.model_id,
            brokerage_bps=self.brokerage_bps,
            stt_bps=self.stt_bps,
            exchange_charges_bps=self.exchange_charges_bps,
            gst_on_charges_pct=self.gst_on_charges_pct,
            stamp_duty_bps=self.stamp_duty_bps,
            slippage_bps=self.slippage_bps,
            spread_bps=self.spread_bps,
            multiplier=self.multiplier * multiplier,
        )


def load_cost_config(
    path: Path | None = None,
    *,
    slippage_bps: float | None = None,
    spread_bps: float | None = None,
    multiplier: float = 1.0,
) -> CostConfig:
    data = yaml.safe_load((path or DEFAULT_COST_PATH).read_text(encoding="utf-8"))
    cfg = CostConfig(
        model_id=str(data.get("cost_model_id", "custom")),
        brokerage_bps=float(data["brokerage_bps"]),
        stt_bps=float(data["stt_bps"]),
        exchange_charges_bps=float(data["exchange_charges_bps"]),
        gst_on_charges_pct=float(data["gst_on_charges_pct"]),
        stamp_duty_bps=float(data["stamp_duty_bps"]),
        slippage_bps=float(data["slippage_bps"] if slippage_bps is None else slippage_bps),
        spread_bps=float(data["spread_bps"] if spread_bps is None else spread_bps),
        multiplier=float(multiplier),
    )
    return cfg


def _bps(notional: float, bps: float) -> float:
    return abs(notional) * (bps / 10_000.0)


def trade_cost(notional: float, side: str, cfg: CostConfig) -> dict[str, float]:
    """
    Estimate cash costs for one fill.
    side: 'buy' | 'sell'
    """
    m = cfg.multiplier
    brokerage = _bps(notional, cfg.brokerage_bps) * m
    exchange = _bps(notional, cfg.exchange_charges_bps) * m
    gst = (brokerage + exchange) * (cfg.gst_on_charges_pct / 100.0)
    slip = _bps(notional, cfg.slippage_bps) * m
    spread = _bps(notional, cfg.spread_bps) * m
    stamp = _bps(notional, cfg.stamp_duty_bps) * m if side == "buy" else 0.0
    stt = _bps(notional, cfg.stt_bps) * m if side == "sell" else 0.0
    total = brokerage + exchange + gst + slip + spread + stamp + stt
    return {
        "brokerage": brokerage,
        "exchange_charges": exchange,
        "gst": gst,
        "slippage": slip,
        "spread": spread,
        "stamp_duty": stamp,
        "stt": stt,
        "total": total,
    }


def cost_config_to_dict(cfg: CostConfig) -> dict[str, Any]:
    return {
        "model_id": cfg.model_id,
        "brokerage_bps": cfg.brokerage_bps,
        "stt_bps": cfg.stt_bps,
        "exchange_charges_bps": cfg.exchange_charges_bps,
        "gst_on_charges_pct": cfg.gst_on_charges_pct,
        "stamp_duty_bps": cfg.stamp_duty_bps,
        "slippage_bps": cfg.slippage_bps,
        "spread_bps": cfg.spread_bps,
        "multiplier": cfg.multiplier,
    }
