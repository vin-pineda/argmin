"""Tests for the analytics & significance module.

Covers tearsheet metric correctness, oracle cross-checks against ``quantstats``
(test-oracle only — never shipped), PSR/DSR properties, the seeded block
bootstrap, and the web-chart helpers (equity curve, drawdown, rolling Sharpe).
"""

from __future__ import annotations

from itertools import pairwise

import numpy as np
import pandas as pd
import pytest

from argmin.analytics import (
    Tearsheet,
    bootstrap_sharpe_ci,
    compute_tearsheet,
    deflated_sharpe_ratio,
    drawdown_series,
    equity_curve,
    probabilistic_sharpe_ratio,
    rolling_sharpe,
)
from argmin.analytics.metrics import (
    ann_vol,
    cagr,
    max_drawdown,
    sharpe_ratio,
    sortino_ratio,
    value_at_risk,
)
from argmin.types import ReturnsPanel

PERIODS = 252


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures / helpers
# ──────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def spy_returns(returns_panel: ReturnsPanel) -> np.ndarray:
    """SPY's daily simple returns from the committed Parquet snapshot."""
    idx = returns_panel.tickers.index("SPY")
    return np.asarray(returns_panel.returns[:, idx], dtype=np.float64)


@pytest.fixture
def spy_series(returns_panel: ReturnsPanel, spy_returns: np.ndarray) -> pd.Series:
    """SPY returns as a datetime-indexed pandas Series for quantstats."""
    dates = pd.DatetimeIndex(returns_panel.dates)
    return pd.Series(spy_returns, index=dates, name="SPY")


@pytest.fixture
def positive_returns(rng: np.random.Generator) -> np.ndarray:
    """A clearly-positive-Sharpe daily series (strong drift, modest vol)."""
    return rng.normal(loc=0.0008, scale=0.008, size=1500)


# ──────────────────────────────────────────────────────────────────────────────
# quantstats oracle cross-checks (TEST ORACLE ONLY)
# ──────────────────────────────────────────────────────────────────────────────
def test_sharpe_matches_quantstats(spy_returns: np.ndarray, spy_series: pd.Series) -> None:
    qs = pytest.importorskip("quantstats")
    ours = sharpe_ratio(spy_returns, risk_free=0.0, periods_per_year=PERIODS)
    oracle = float(qs.stats.sharpe(spy_series, rf=0.0, periods=PERIODS))
    np.testing.assert_allclose(ours, oracle, rtol=1e-2)


def test_sortino_matches_quantstats(spy_returns: np.ndarray, spy_series: pd.Series) -> None:
    qs = pytest.importorskip("quantstats")
    ours = sortino_ratio(spy_returns, risk_free=0.0, periods_per_year=PERIODS)
    oracle = float(qs.stats.sortino(spy_series, rf=0.0, periods=PERIODS))
    np.testing.assert_allclose(ours, oracle, rtol=1e-2)


def test_max_drawdown_matches_quantstats(spy_returns: np.ndarray, spy_series: pd.Series) -> None:
    qs = pytest.importorskip("quantstats")
    ours = max_drawdown(spy_returns)
    oracle = float(qs.stats.max_drawdown(spy_series))
    # quantstats injects a phantom baseline row; for a long real series the
    # difference is negligible.
    np.testing.assert_allclose(ours, oracle, rtol=2e-2, atol=1e-3)


def test_cagr_matches_quantstats(spy_returns: np.ndarray, spy_series: pd.Series) -> None:
    qs = pytest.importorskip("quantstats")
    ours = cagr(spy_returns, periods_per_year=PERIODS)
    oracle = float(qs.stats.cagr(spy_series, periods=PERIODS))
    np.testing.assert_allclose(ours, oracle, rtol=1e-2)


def test_ann_vol_matches_quantstats(spy_returns: np.ndarray, spy_series: pd.Series) -> None:
    qs = pytest.importorskip("quantstats")
    ours = ann_vol(spy_returns, periods_per_year=PERIODS)
    oracle = float(qs.stats.volatility(spy_series, periods=PERIODS))
    np.testing.assert_allclose(ours, oracle, rtol=1e-2)


def test_var_matches_quantstats(spy_returns: np.ndarray, spy_series: pd.Series) -> None:
    qs = pytest.importorskip("quantstats")
    ours = value_at_risk(spy_returns, alpha=0.05)
    # quantstats value_at_risk uses a Gaussian (mean - z*sigma) parametric VaR by
    # default, while ours is historical (empirical quantile). They agree only
    # loosely; assert same sign and rough magnitude rather than tight equality.
    oracle = float(qs.stats.value_at_risk(spy_series))
    assert ours < 0.0
    assert oracle < 0.0
    np.testing.assert_allclose(ours, oracle, atol=5e-3)


# ──────────────────────────────────────────────────────────────────────────────
# Tearsheet structure & sign conventions
# ──────────────────────────────────────────────────────────────────────────────
def test_compute_tearsheet_fields(spy_returns: np.ndarray) -> None:
    ts = compute_tearsheet(spy_returns, risk_free=0.0, periods_per_year=PERIODS)
    assert isinstance(ts, Tearsheet)
    assert ts.max_drawdown <= 0.0
    assert ts.var_95 <= 0.0
    assert ts.cvar_95 <= ts.var_95  # tail mean is at least as bad as the quantile
    assert 0.0 <= ts.hit_rate <= 1.0
    assert ts.worst_day <= ts.best_day
    assert ts.avg_turnover is None
    assert np.isfinite(
        [ts.total_return, ts.cagr, ts.ann_return, ts.ann_vol, ts.sharpe, ts.sortino, ts.calmar]
    ).all()


def test_compute_tearsheet_passes_turnover(spy_returns: np.ndarray) -> None:
    ts = compute_tearsheet(spy_returns, avg_turnover=0.12)
    assert ts.avg_turnover == pytest.approx(0.12)


def test_calmar_is_cagr_over_maxdd(spy_returns: np.ndarray) -> None:
    ts = compute_tearsheet(spy_returns)
    expected = ts.cagr / abs(ts.max_drawdown)
    np.testing.assert_allclose(ts.calmar, expected, rtol=1e-12)


def test_sharpe_risk_free_lowers_sharpe(positive_returns: np.ndarray) -> None:
    sr0 = sharpe_ratio(positive_returns, risk_free=0.0)
    sr_rf = sharpe_ratio(positive_returns, risk_free=0.05)
    assert sr_rf < sr0


# ──────────────────────────────────────────────────────────────────────────────
# Significance: PSR / DSR
# ──────────────────────────────────────────────────────────────────────────────
def test_psr_in_unit_interval(spy_returns: np.ndarray, positive_returns: np.ndarray) -> None:
    for series in (spy_returns, positive_returns):
        psr = probabilistic_sharpe_ratio(series)
        assert 0.0 <= psr <= 1.0


def test_psr_high_for_positive_sharpe(positive_returns: np.ndarray) -> None:
    psr = probabilistic_sharpe_ratio(positive_returns, sr_benchmark=0.0)
    assert psr > 0.95


def test_psr_increases_with_lower_benchmark(positive_returns: np.ndarray) -> None:
    low = probabilistic_sharpe_ratio(positive_returns, sr_benchmark=0.0)
    high = probabilistic_sharpe_ratio(positive_returns, sr_benchmark=0.1)
    assert low >= high


def test_dsr_le_psr(positive_returns: np.ndarray) -> None:
    psr0 = probabilistic_sharpe_ratio(positive_returns, sr_benchmark=0.0)
    dsr = deflated_sharpe_ratio(positive_returns, n_trials=10)
    assert dsr <= psr0 + 1e-12


def test_dsr_strictly_decreasing_in_trials(positive_returns: np.ndarray) -> None:
    dsr_values = [
        deflated_sharpe_ratio(positive_returns, n_trials=n) for n in (2, 5, 20, 100, 1000)
    ]
    for earlier, later in pairwise(dsr_values):
        assert later < earlier


def test_dsr_single_trial_equals_psr(positive_returns: np.ndarray) -> None:
    # n_trials=1 → expected-max benchmark is 0 → DSR == PSR(0).
    psr0 = probabilistic_sharpe_ratio(positive_returns, sr_benchmark=0.0)
    dsr1 = deflated_sharpe_ratio(positive_returns, n_trials=1)
    np.testing.assert_allclose(dsr1, psr0, rtol=1e-12)


# ──────────────────────────────────────────────────────────────────────────────
# Significance: block bootstrap
# ──────────────────────────────────────────────────────────────────────────────
def test_bootstrap_ci_brackets_point(spy_returns: np.ndarray) -> None:
    point, lo, hi = bootstrap_sharpe_ci(spy_returns, n_samples=500, seed=7)
    assert lo <= point <= hi
    assert lo < hi


def test_bootstrap_deterministic(spy_returns: np.ndarray) -> None:
    a = bootstrap_sharpe_ci(spy_returns, n_samples=300, seed=42)
    b = bootstrap_sharpe_ci(spy_returns, n_samples=300, seed=42)
    assert a == b


def test_bootstrap_point_matches_annualized_sharpe(spy_returns: np.ndarray) -> None:
    point, _, _ = bootstrap_sharpe_ci(spy_returns, n_samples=100)
    direct = sharpe_ratio(spy_returns, risk_free=0.0, periods_per_year=PERIODS)
    np.testing.assert_allclose(point, direct, rtol=1e-12)


# ──────────────────────────────────────────────────────────────────────────────
# Web-chart helpers
# ──────────────────────────────────────────────────────────────────────────────
def test_equity_curve_compounds(spy_returns: np.ndarray) -> None:
    eq = equity_curve(spy_returns)
    assert eq.shape == spy_returns.shape
    np.testing.assert_allclose(eq[0], 1.0 + spy_returns[0], rtol=1e-12)
    np.testing.assert_allclose(eq[-1], np.prod(1.0 + spy_returns), rtol=1e-10)


def test_equity_curve_monotone_for_positive_returns() -> None:
    r = np.full(50, 0.01)
    eq = equity_curve(r)
    assert np.all(np.diff(eq) > 0)


def test_drawdown_series_non_positive(spy_returns: np.ndarray) -> None:
    dd = drawdown_series(spy_returns)
    assert dd.shape == spy_returns.shape
    assert np.all(dd <= 1e-12)
    np.testing.assert_allclose(dd.min(), max_drawdown(spy_returns), rtol=1e-12)


def test_drawdown_zero_for_monotone_growth() -> None:
    r = np.full(30, 0.005)
    dd = drawdown_series(r)
    np.testing.assert_allclose(dd, 0.0, atol=1e-12)


def test_drawdown_immediate_loss() -> None:
    # A first-day loss must register against the $1 starting capital.
    r = np.array([-0.1, 0.0, 0.0])
    dd = drawdown_series(r)
    np.testing.assert_allclose(dd[0], -0.1, rtol=1e-12)


def test_rolling_sharpe_length(spy_returns: np.ndarray) -> None:
    window = 252
    rs = rolling_sharpe(spy_returns, window=window, periods_per_year=PERIODS)
    assert rs.shape == (spy_returns.size - window + 1,)
    assert np.all(np.isfinite(rs))


def test_rolling_sharpe_short_series_empty() -> None:
    rs = rolling_sharpe(np.full(10, 0.001), window=252)
    assert rs.size == 0


def test_rolling_sharpe_constant_window_is_finite() -> None:
    # A constant window has zero dispersion → Sharpe defined as 0, not inf/nan.
    rs = rolling_sharpe(np.full(60, 0.001), window=21)
    assert np.all(np.isfinite(rs))
