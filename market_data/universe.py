"""Load V1 universe definitions from config YAML."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_UNIVERSE_PATH = ROOT / "config" / "universe_nifty50.yaml"


def load_universe(path: Path | None = None) -> dict[str, Any]:
    universe_path = path or DEFAULT_UNIVERSE_PATH
    data = yaml.safe_load(universe_path.read_text(encoding="utf-8"))
    if not data or "symbols" not in data:
        raise ValueError(f"Universe file missing symbols: {universe_path}")
    symbols = list(data["symbols"])
    if len(symbols) != len(set(symbols)):
        raise ValueError("Universe contains duplicate symbols")
    return data


def universe_symbols(path: Path | None = None) -> list[str]:
    return list(load_universe(path)["symbols"])


def benchmark_symbol(path: Path | None = None) -> str:
    data = load_universe(path)
    return str(data.get("benchmark_yahoo_symbol", "^NSEI"))
