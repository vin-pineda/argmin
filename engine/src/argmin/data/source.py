"""Pluggable price sources behind a ``DataSource`` protocol.

Only used to *build* the committed snapshot. Tests and offline runs read the
frozen Parquet cache and never touch a live source (spec: reproducibility).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import polars as pl


@runtime_checkable
class DataSource(Protocol):
    """Fetch a wide price frame: a ``date`` column plus one column per ticker."""

    name: str

    def fetch_prices(self, tickers: list[str], start: str, end: str) -> pl.DataFrame: ...


class YFinanceSource:
    """Free, cacheable source. ``auto_adjust=True`` ⇒ total-return (adj close)."""

    name = "yfinance"

    def fetch_prices(self, tickers: list[str], start: str, end: str) -> pl.DataFrame:
        import pandas as pd  # noqa: PLC0415 — heavy, only for snapshot building
        import yfinance as yf  # noqa: PLC0415

        raw = yf.download(
            tickers,
            start=start,
            end=end,
            auto_adjust=True,  # dividends reinvested ⇒ total-return basis
            progress=False,
            group_by="column",
            threads=False,  # avoid yfinance tz-cache "database is locked" races
        )
        if raw is None or len(raw) == 0:
            raise RuntimeError("yfinance returned no data — check tickers/connectivity")

        close = raw["Close"] if "Close" in raw.columns.get_level_values(0) else raw
        if isinstance(close, pd.Series):
            close = close.to_frame(name=tickers[0])
        # keep requested order; tolerate missing tickers by raising clearly
        missing = [t for t in tickers if t not in close.columns]
        if missing:
            raise RuntimeError(f"yfinance did not return tickers: {missing}")
        close = close[tickers].copy()
        close.index.name = "date"
        pdf = close.reset_index()
        pdf["date"] = pd.to_datetime(pdf["date"]).dt.tz_localize(None)
        return pl.from_pandas(pdf)


def get_source(name: str) -> DataSource:
    if name == "yfinance":
        return YFinanceSource()
    raise ValueError(f"Unknown / unsupported data source: {name!r}")
