"""Local experiment ID registry (file-backed until Supabase credentials arrive)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "reports" / "experiment_registry.jsonl"


def next_experiment_id() -> str:
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    if not REGISTRY.exists():
        return "EXP-000001"
    n = sum(1 for _ in REGISTRY.open("r", encoding="utf-8") if _.strip())
    return f"EXP-{n + 1:06d}"


def append_experiment(record: dict[str, Any]) -> None:
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    record = {
        **record,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    with REGISTRY.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, default=str) + "\n")
