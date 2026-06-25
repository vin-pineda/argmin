"""Build & freeze the committed price snapshot (the reproducibility source).

Run once (needs network): ``uv run argmin snapshot``. Everything else reads the
resulting Parquet file offline. A JSON manifest records per-ticker inception
dates and a SHA-256 of the Parquet bytes so the snapshot is verifiable.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from argmin import __version__
from argmin.config import ArgminConfig, Settings
from argmin.data.loader import snapshot_manifest_path, snapshot_path
from argmin.data.source import DataSource, get_source
from argmin.logging import get_logger

log = get_logger(__name__)


def build_snapshot(
    config: ArgminConfig,
    settings: Settings,
    source: DataSource | None = None,
    tickers: list[str] | None = None,
) -> Path:
    """Fetch prices for the universe and write the frozen Parquet + manifest."""
    src = source or get_source(settings.data_source)
    universe = tickers or config.universe
    log.info("snapshot.fetch", source=src.name, tickers=universe, start=config.data.start)

    prices = src.fetch_prices(universe, config.data.start, config.data.end).sort("date")

    settings.cache_dir.mkdir(parents=True, exist_ok=True)
    path = snapshot_path(settings)
    prices.write_parquet(path)

    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    inception = {t: str(prices.filter(pl.col(t).is_not_null())["date"].min()) for t in universe}
    manifest = {
        "engine_version": __version__,
        "source": src.name,
        "tickers": universe,
        "config_start": config.data.start,
        "config_end": config.data.end,
        "rows": prices.height,
        "first_date": str(prices["date"].min()),
        "last_date": str(prices["date"].max()),
        "per_ticker_inception": inception,
        "price_basis": "adjusted_close_total_return",
        "sha256": sha,
        "created_utc": datetime.now(UTC).isoformat(),
    }
    snapshot_manifest_path(settings).write_text(json.dumps(manifest, indent=2))
    _materialize_duckdb(settings, path)

    log.info("snapshot.done", rows=prices.height, sha256=sha[:12], path=str(path))
    return path


def _materialize_duckdb(settings: Settings, parquet_path: Path) -> None:
    """Mirror the Parquet snapshot into a DuckDB table for ad-hoc SQL."""
    import duckdb  # noqa: PLC0415

    settings.resolved_duckdb_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(settings.resolved_duckdb_path))
    try:
        con.execute(
            "CREATE OR REPLACE TABLE prices AS SELECT * FROM read_parquet(?)",
            [str(parquet_path)],
        )
    finally:
        con.close()
