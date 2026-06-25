"""Result types for the walk-forward backtest.

Kept in their own module so :mod:`argmin.backtest.benchmarks` and
:mod:`argmin.backtest.engine` can both import them without an import cycle.
Field names are part of the public contract (Phase 3 + the web depend on them).
"""

from __future__ import annotations

from dataclasses import dataclass

from argmin.types import FloatArray


@dataclass(frozen=True)
class StrategyTrack:
    """The OOS daily track for one strategy (the engine's or a benchmark's)."""

    name: str
    dates: FloatArray  # (T_oos,) datetime64[ns], daily OOS dates
    daily_returns: FloatArray  # (T_oos,) net-of-cost daily returns
    equity: FloatArray  # (T_oos,) cumulative growth of $1
    drawdown: FloatArray  # (T_oos,) underwater curve (<= 0)
    rebalance_dates: FloatArray  # (R,) datetime64[ns]
    weights_over_time: FloatArray  # (R, N) target weights at each rebalance
    turnover: FloatArray  # (R,) per-rebalance turnover (sum |Δw|)


@dataclass(frozen=True)
class BacktestResult:
    """The full walk-forward result: strategy + benchmarks over the same OOS dates."""

    tickers: tuple[str, ...]
    strategy: StrategyTrack
    benchmarks: dict[str, StrategyTrack]
    transaction_cost_bps: float
    rebalance: str
    lookback_years: int
    method: str
