"""Load the frozen price snapshot and build the daily returns panel.

Alignment rule (Build Checklist): **common-start** — restrict to the window
where every requested ticker has data (latest inception), then assert no
internal gaps. Returns are **daily simple returns** on the total-return
(adjusted-close) price series.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl

from argmin.config import ArgminConfig, Settings
from argmin.types import ReturnsPanel


def snapshot_path(settings: Settings) -> Path:
    return settings.cache_dir / "prices.parquet"


def snapshot_manifest_path(settings: Settings) -> Path:
    return settings.cache_dir / "snapshot_manifest.json"


def load_prices(
    settings: Settings,
    tickers: list[str] | None = None,
) -> pl.DataFrame:
    """Read the committed Parquet snapshot (wide: ``date`` + ticker columns)."""
    path = snapshot_path(settings)
    if not path.exists():
        raise FileNotFoundError(
            f"Price snapshot not found at {path}. Build it once with "
            "`uv run argmin snapshot` (requires network)."
        )
    df = pl.read_parquet(path).sort("date")
    if tickers is not None:
        missing = [t for t in tickers if t not in df.columns]
        if missing:
            raise ValueError(f"Tickers not in snapshot: {missing}")
        df = df.select(["date", *tickers])
    return df


def prices_to_returns(prices: pl.DataFrame, tickers: list[str]) -> ReturnsPanel:
    """Common-start align then compute daily simple returns → :class:`ReturnsPanel`."""
    cols = ["date", *tickers]
    px = prices.select(cols).sort("date")
    # common-start: drop rows before every ticker has data (pre-inception = null)
    px = px.drop_nulls()
    if px.height < 2:
        raise ValueError("Not enough overlapping price history to compute returns")

    ret = px.select([pl.col("date"), *[pl.col(t).pct_change().alias(t) for t in tickers]]).slice(
        1
    )  # first row is null after pct_change

    # no internal NaNs after alignment
    null_counts = ret.select(pl.col(tickers).is_null().sum()).row(0)
    if any(c > 0 for c in null_counts):
        raise ValueError("Internal NaNs remain after common-start alignment")

    dates = ret["date"].to_numpy().astype("datetime64[ns]")
    matrix = ret.select(tickers).to_numpy().astype(np.float64)
    return ReturnsPanel(dates=dates, tickers=tuple(tickers), returns=matrix)


def load_returns_panel(
    config: ArgminConfig,
    settings: Settings,
    tickers: list[str] | None = None,
) -> ReturnsPanel:
    """Load the returns panel for ``tickers`` (default: the config universe)."""
    universe = tickers if tickers is not None else config.universe
    prices = load_prices(settings, universe)
    # apply the configured data window
    prices = prices.filter(
        (pl.col("date") >= pl.lit(config.data.start).str.to_datetime())
        & (pl.col("date") <= pl.lit(config.data.end).str.to_datetime())
    )
    return prices_to_returns(prices, universe)
