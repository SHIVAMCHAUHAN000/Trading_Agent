"""Storage immutability tests for Stage 3."""

from __future__ import annotations

import pandas as pd
import pytest

from market_data.store import write_processed_bundle, write_raw_frames


def test_raw_write_is_immutable(tmp_path, monkeypatch):
    monkeypatch.setattr("market_data.store.RAW_ROOT", tmp_path / "raw")
    monkeypatch.setattr("market_data.store.PROCESSED_ROOT", tmp_path / "processed")

    df = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-01-01"]),
            "Symbol": ["TEST.NS"],
            "Open": [1.0],
            "High": [1.0],
            "Low": [1.0],
            "Close": [1.0],
            "AdjClose": [1.0],
            "Volume": [10],
        }
    )
    write_raw_frames("DS1", {"TEST.NS": df}, {"dataset_id": "DS1"})
    with pytest.raises(FileExistsError):
        write_raw_frames("DS1", {"TEST.NS": df}, {"dataset_id": "DS1"})


def test_processed_never_uses_raw_root(tmp_path, monkeypatch):
    monkeypatch.setattr("market_data.store.RAW_ROOT", tmp_path / "raw")
    monkeypatch.setattr("market_data.store.PROCESSED_ROOT", tmp_path / "processed")
    df = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-01-01"]),
            "Symbol": ["TEST.NS"],
            "Open": [1.0],
            "High": [1.0],
            "Low": [1.0],
            "Close": [1.0],
            "AdjClose": [1.0],
            "Volume": [10],
        }
    )
    path = write_processed_bundle("DS2", df, {"status": "PASS"}, {"dataset_id": "DS2"})
    assert "processed" in str(path)
    assert "raw" not in path.parts[-3:]
