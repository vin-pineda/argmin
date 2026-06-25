"""Data layer: price snapshot → returns panel (reproducible, offline)."""

from __future__ import annotations

from argmin.data.loader import (
    load_prices,
    load_returns_panel,
    snapshot_manifest_path,
    snapshot_path,
)
from argmin.data.snapshot import build_snapshot
from argmin.data.source import DataSource, YFinanceSource

__all__ = [
    "DataSource",
    "YFinanceSource",
    "build_snapshot",
    "load_prices",
    "load_returns_panel",
    "snapshot_manifest_path",
    "snapshot_path",
]
