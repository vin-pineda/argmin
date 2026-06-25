"""Walk-forward backtest tests.

The headline guarantee is **no look-ahead**: truncating the panel to end exactly
at a rebalance date ``t`` must yield the *same* target weights at ``t`` as the
full-panel run (estimation can never peek past ``t``). The remaining tests pin the
simulation invariants (positive equity, non-positive drawdown, non-negative
turnover), the effect of transaction costs, the benchmark set, and determinism.

These tests are deliberately self-contained — they never import the analytics
module (built in parallel) — and run on a trimmed universe / window for speed
while still exercising the real walk-forward loop.
"""

from __future__ import annotations

import numpy as np
import pytest

from argmin.backtest import BacktestResult, run_backtest
from argmin.config import ArgminConfig
from argmin.types import ReturnsPanel

# ──────────────────────────────────────────────────────────────────────────────
# Fixtures: a small, fast slice that still exercises the full walk-forward loop.
# ──────────────────────────────────────────────────────────────────────────────
_TICKERS = ["SPY", "AGG", "GLD", "TLT", "QQQ"]


@pytest.fixture(scope="module")
def small_panel(returns_panel: ReturnsPanel) -> ReturnsPanel:
    """A 5-asset, ~2017→end slice: a handful of years of OOS with a 2-yr lookback."""
    sub = returns_panel.select(_TICKERS)
    return sub.window(start=np.datetime64("2017-01-01"))


@pytest.fixture(scope="module")
def fast_config(config: ArgminConfig) -> ArgminConfig:
    """Config override: 2-yr lookback + sample estimators for a quick, real run."""
    raw = config.model_dump()
    raw["backtest"]["lookback_years"] = 2
    raw["estimators"]["mu"] = "sample"
    raw["estimators"]["cov"] = "sample"
    return ArgminConfig.model_validate(raw)


@pytest.fixture(scope="module")
def result(fast_config: ArgminConfig, small_panel: ReturnsPanel) -> BacktestResult:
    return run_backtest(fast_config, small_panel)


# ──────────────────────────────────────────────────────────────────────────────
# No look-ahead (the critical correctness test)
# ──────────────────────────────────────────────────────────────────────────────
def test_no_look_ahead(fast_config: ArgminConfig, small_panel: ReturnsPanel) -> None:
    """Truncating the panel at a rebalance date ``t`` reproduces the weights at ``t``.

    If the estimator peeked past ``t``, removing all rows after ``t`` would change
    the target weights computed at ``t``. They must be identical.
    """
    full = run_backtest(fast_config, small_panel)
    reb_dates = full.strategy.rebalance_dates
    weights = full.strategy.weights_over_time

    # Pick a rebalance comfortably inside the OOS so a real window exists on both
    # sides of the truncation.
    pick = len(reb_dates) // 2
    t = reb_dates[pick]

    truncated = small_panel.window(end=t)
    truncated_run = run_backtest(fast_config, truncated)

    # ``t`` is the *last* date of the truncated panel, hence its final rebalance.
    np.testing.assert_array_equal(truncated_run.strategy.rebalance_dates[-1], t)
    np.testing.assert_allclose(
        truncated_run.strategy.weights_over_time[-1],
        weights[pick],
        atol=1e-10,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Simulation invariants
# ──────────────────────────────────────────────────────────────────────────────
def test_equity_strictly_positive(result: BacktestResult) -> None:
    assert np.all(result.strategy.equity > 0.0)
    for track in result.benchmarks.values():
        assert np.all(track.equity > 0.0)


def test_drawdown_non_positive(result: BacktestResult) -> None:
    assert np.all(result.strategy.drawdown <= 1e-12)
    for track in result.benchmarks.values():
        assert np.all(track.drawdown <= 1e-12)


def test_turnover_non_negative(result: BacktestResult) -> None:
    assert np.all(result.strategy.turnover >= 0.0)
    for track in result.benchmarks.values():
        assert np.all(track.turnover >= 0.0)


def test_equity_matches_daily_returns(result: BacktestResult) -> None:
    strat = result.strategy
    expected = np.cumprod(1.0 + strat.daily_returns)
    np.testing.assert_allclose(strat.equity, expected, rtol=1e-12)


def test_shapes_align(result: BacktestResult) -> None:
    strat = result.strategy
    t_oos = strat.dates.shape[0]
    n_reb = strat.rebalance_dates.shape[0]
    assert strat.daily_returns.shape == (t_oos,)
    assert strat.equity.shape == (t_oos,)
    assert strat.drawdown.shape == (t_oos,)
    assert strat.turnover.shape == (n_reb,)
    assert strat.weights_over_time.shape == (n_reb, len(result.tickers))


# ──────────────────────────────────────────────────────────────────────────────
# Transaction costs
# ──────────────────────────────────────────────────────────────────────────────
def test_costs_reduce_return(fast_config: ArgminConfig, small_panel: ReturnsPanel) -> None:
    """A costed run must end strictly below the same run with zero costs."""
    with_costs = run_backtest(fast_config, small_panel)
    assert with_costs.transaction_cost_bps > 0.0

    raw = fast_config.model_dump()
    raw["backtest"]["transaction_cost_bps"] = 0.0
    free_config = ArgminConfig.model_validate(raw)
    free = run_backtest(free_config, small_panel)

    assert with_costs.strategy.equity[-1] < free.strategy.equity[-1]


# ──────────────────────────────────────────────────────────────────────────────
# Benchmarks
# ──────────────────────────────────────────────────────────────────────────────
def test_all_benchmarks_present(fast_config: ArgminConfig, result: BacktestResult) -> None:
    for name in fast_config.backtest.benchmarks:
        assert name in result.benchmarks


def test_equal_weight_is_one_over_n(result: BacktestResult) -> None:
    ew = result.benchmarks["equal_weight"]
    n = len(result.tickers)
    expected = np.full(n, 1.0 / n)
    for row in ew.weights_over_time:
        np.testing.assert_allclose(row, expected, atol=1e-12)


def test_benchmarks_share_oos_dates(result: BacktestResult) -> None:
    strat_dates = result.strategy.dates
    for track in result.benchmarks.values():
        np.testing.assert_array_equal(track.dates, strat_dates)


def test_spy_is_buy_and_hold(result: BacktestResult) -> None:
    """SPY rebalances once (buy & hold), so it only ever incurs opening turnover."""
    spy = result.benchmarks["spy"]
    assert spy.rebalance_dates.shape[0] == 1
    assert spy.turnover.shape[0] == 1


# ──────────────────────────────────────────────────────────────────────────────
# Determinism
# ──────────────────────────────────────────────────────────────────────────────
def test_deterministic(fast_config: ArgminConfig, small_panel: ReturnsPanel) -> None:
    a = run_backtest(fast_config, small_panel)
    b = run_backtest(fast_config, small_panel)
    np.testing.assert_array_equal(a.strategy.equity, b.strategy.equity)
    np.testing.assert_array_equal(a.strategy.weights_over_time, b.strategy.weights_over_time)
