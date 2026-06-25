"""Walk-forward backtesting: rebalanced strategies, benchmarks, OOS tracks.

``run_backtest`` simulates a rebalanced portfolio with no look-ahead (point-in-time
estimation, drifting weights between rebalances, linear transaction costs on
turnover) and reports it alongside the configured benchmarks over identical OOS
dates. :class:`StrategyTrack` / :class:`BacktestResult` are the public result
contracts consumed by the analytics layer, the API, and the web.
"""

from __future__ import annotations

from argmin.backtest.benchmarks import (
    available_benchmarks,
    build_benchmark_track,
    simulate_target_weights,
)
from argmin.backtest.engine import run_backtest
from argmin.backtest.types import BacktestResult, StrategyTrack

__all__ = [
    "BacktestResult",
    "StrategyTrack",
    "available_benchmarks",
    "build_benchmark_track",
    "run_backtest",
    "simulate_target_weights",
]
