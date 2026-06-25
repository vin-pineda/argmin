"""Tests for the μ and Σ estimators.

Covers shapes/dtypes, symmetry/PSD, Ledoit-Wolf shrinkage bounds, EWMA recency,
CAPM finiteness, the registries, and oracle cross-checks against ``PyPortfolioOpt``
(test-oracle only — never shipped as the implementation).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from argmin.estimators import (
    CAPMMu,
    EWMACov,
    EWMAMu,
    LedoitWolfCov,
    SampleCov,
    SampleMu,
    get_cov_estimator,
    get_return_estimator,
    ledoit_wolf_shrinkage,
)
from argmin.types import (
    TRADING_DAYS_PER_YEAR,
    CovEstimator,
    ReturnEstimator,
    ReturnsPanel,
)

MU_ESTIMATORS = [SampleMu(), EWMAMu(halflife=63), CAPMMu()]
COV_ESTIMATORS = [SampleCov(), LedoitWolfCov(), EWMACov(halflife=63)]


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def synthetic_returns(rng: np.random.Generator) -> np.ndarray:
    """A small ``(T, N)`` panel of daily simple returns with realistic moments."""
    T, N = 500, 5
    return rng.normal(loc=0.0004, scale=0.011, size=(T, N))


def _price_frame(returns: np.ndarray) -> pd.DataFrame:
    """Build a price frame whose ``pct_change`` reproduces ``returns`` exactly.

    A base row of 100 is prepended so the first ``pct_change`` equals
    ``returns[0]`` — making ``PyPortfolioOpt`` (which derives returns from prices)
    line up with our return-native estimators to floating-point precision.
    """
    _, N = returns.shape
    base = np.full((1, N), 100.0)
    body = 100.0 * np.cumprod(1.0 + returns, axis=0)
    prices = np.vstack([base, body])
    cols = [f"A{i}" for i in range(N)]
    return pd.DataFrame(prices, columns=cols)


def _min_eig(sigma: np.ndarray) -> float:
    return float(np.linalg.eigvalsh(sigma).min())


# ──────────────────────────────────────────────────────────────────────────────
# Shapes, dtypes, protocol conformance
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("est", MU_ESTIMATORS, ids=lambda e: e.name)
def test_mu_shape_dtype_finite(est: ReturnEstimator, synthetic_returns: np.ndarray) -> None:
    mu = est.estimate(synthetic_returns)
    n = synthetic_returns.shape[1]
    assert mu.shape == (n,)
    assert mu.dtype == np.float64
    assert np.all(np.isfinite(mu))


@pytest.mark.parametrize("est", COV_ESTIMATORS, ids=lambda e: e.name)
def test_cov_shape_dtype_finite(est: CovEstimator, synthetic_returns: np.ndarray) -> None:
    sigma = est.estimate(synthetic_returns)
    n = synthetic_returns.shape[1]
    assert sigma.shape == (n, n)
    assert sigma.dtype == np.float64
    assert np.all(np.isfinite(sigma))


@pytest.mark.parametrize("est", COV_ESTIMATORS, ids=lambda e: e.name)
def test_cov_symmetric_psd(est: CovEstimator, synthetic_returns: np.ndarray) -> None:
    sigma = est.estimate(synthetic_returns)
    assert np.allclose(sigma, sigma.T, atol=1e-12)
    assert _min_eig(sigma) >= -1e-8


def test_mu_estimators_satisfy_protocol() -> None:
    for est in MU_ESTIMATORS:
        assert isinstance(est, ReturnEstimator)


def test_cov_estimators_satisfy_protocol() -> None:
    for est in COV_ESTIMATORS:
        assert isinstance(est, CovEstimator)


# ──────────────────────────────────────────────────────────────────────────────
# Real-data smoke tests (committed Parquet snapshot via returns_panel fixture)
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("est", MU_ESTIMATORS, ids=lambda e: e.name)
def test_mu_real_data(est: ReturnEstimator, returns_panel: ReturnsPanel) -> None:
    mu = est.estimate(returns_panel.returns, risk_free=0.02)
    assert mu.shape == (returns_panel.n_assets,)
    assert np.all(np.isfinite(mu))


@pytest.mark.parametrize("est", COV_ESTIMATORS, ids=lambda e: e.name)
def test_cov_real_data(est: CovEstimator, returns_panel: ReturnsPanel) -> None:
    sigma = est.estimate(returns_panel.returns)
    assert sigma.shape == (returns_panel.n_assets, returns_panel.n_assets)
    assert np.allclose(sigma, sigma.T, atol=1e-12)
    assert _min_eig(sigma) >= -1e-8


# ──────────────────────────────────────────────────────────────────────────────
# SampleMu / SampleCov correctness (closed-form, independent of oracle)
# ──────────────────────────────────────────────────────────────────────────────
def test_sample_mu_equals_annualized_mean(synthetic_returns: np.ndarray) -> None:
    expected = synthetic_returns.mean(axis=0) * TRADING_DAYS_PER_YEAR
    np.testing.assert_allclose(SampleMu().estimate(synthetic_returns), expected, atol=1e-12)


def test_sample_cov_equals_npcov(synthetic_returns: np.ndarray) -> None:
    expected = np.cov(synthetic_returns, rowvar=False) * TRADING_DAYS_PER_YEAR
    np.testing.assert_allclose(SampleCov().estimate(synthetic_returns), expected, atol=1e-12)


# ──────────────────────────────────────────────────────────────────────────────
# EWMA recency sanity
# ──────────────────────────────────────────────────────────────────────────────
def test_ewma_mu_weights_recent_more(rng: np.random.Generator) -> None:
    # Single asset: 0% for the first half, then a +1%/day regime for the second.
    T = 400
    returns = np.zeros((T, 1))
    returns[T // 2 :, 0] = 0.01
    sample_mu = float(SampleMu().estimate(returns)[0])
    ewma_mu = float(EWMAMu(halflife=21).estimate(returns)[0])
    # The recent positive regime dominates EWMA → it exceeds the flat sample mean.
    assert ewma_mu > sample_mu


def test_ewma_mu_short_halflife_more_recency_sensitive() -> None:
    T = 400
    returns = np.zeros((T, 1))
    returns[T // 2 :, 0] = 0.01
    fast = float(EWMAMu(halflife=10).estimate(returns)[0])
    slow = float(EWMAMu(halflife=120).estimate(returns)[0])
    # A shorter halflife leans harder into the recent regime.
    assert fast > slow


def test_ewma_cov_weights_recent_more() -> None:
    # Volatility regime change: calm first half, volatile second half.
    rng = np.random.default_rng(7)
    T = 600
    calm = rng.normal(0.0, 0.005, size=(T // 2, 1))
    wild = rng.normal(0.0, 0.03, size=(T // 2, 1))
    returns = np.vstack([calm, wild])
    sample_var = float(SampleCov().estimate(returns)[0, 0])
    ewma_var = float(EWMACov(halflife=21).estimate(returns)[0, 0])
    # Recent high-vol regime dominates EWMA variance vs the blended sample.
    assert ewma_var > sample_var


def test_ewma_mu_constant_series_recovers_mean() -> None:
    # A constant daily return must annualize identically for sample and EWMA.
    returns = np.full((300, 3), 0.001)
    np.testing.assert_allclose(
        EWMAMu(halflife=63).estimate(returns),
        SampleMu().estimate(returns),
        atol=1e-12,
    )


# ──────────────────────────────────────────────────────────────────────────────
# CAPM
# ──────────────────────────────────────────────────────────────────────────────
def test_capm_shape_and_finite(synthetic_returns: np.ndarray) -> None:
    mu = CAPMMu().estimate(synthetic_returns, risk_free=0.02)
    assert mu.shape == (synthetic_returns.shape[1],)
    assert np.all(np.isfinite(mu))


def test_capm_market_beta_consistency(rng: np.random.Generator) -> None:
    # If every asset is identical, each β = 1 and μ_i = μ_mkt.
    base = rng.normal(0.0005, 0.01, size=(400, 1))
    returns = np.repeat(base, 4, axis=1)
    rf = 0.03
    mu = CAPMMu().estimate(returns, risk_free=rf)
    mu_mkt = float(base.mean()) * TRADING_DAYS_PER_YEAR
    np.testing.assert_allclose(mu, np.full(4, mu_mkt), atol=1e-9)


def test_capm_degenerate_market_returns_rf() -> None:
    # Zero-variance market → CAPM falls back to the risk-free rate for all assets.
    returns = np.zeros((100, 3))
    mu = CAPMMu().estimate(returns, risk_free=0.025)
    np.testing.assert_allclose(mu, np.full(3, 0.025), atol=1e-12)


# ──────────────────────────────────────────────────────────────────────────────
# Ledoit-Wolf
# ──────────────────────────────────────────────────────────────────────────────
def test_ledoit_wolf_shrinkage_in_unit_interval(synthetic_returns: np.ndarray) -> None:
    delta = ledoit_wolf_shrinkage(synthetic_returns)
    assert 0.0 <= delta <= 1.0


def test_ledoit_wolf_records_shrinkage(synthetic_returns: np.ndarray) -> None:
    est = LedoitWolfCov()
    assert est.last_shrinkage_ is None
    est.estimate(synthetic_returns)
    assert est.last_shrinkage_ is not None
    assert 0.0 <= est.last_shrinkage_ <= 1.0
    # The standalone helper and the estimator agree on δ.
    np.testing.assert_allclose(
        est.last_shrinkage_, ledoit_wolf_shrinkage(synthetic_returns), atol=1e-12
    )


def test_ledoit_wolf_psd_and_symmetric(synthetic_returns: np.ndarray) -> None:
    sigma = LedoitWolfCov().estimate(synthetic_returns)
    assert np.allclose(sigma, sigma.T, atol=1e-12)
    assert _min_eig(sigma) >= -1e-8


def test_ledoit_wolf_real_data_strictly_interior(returns_panel: ReturnsPanel) -> None:
    # On real, correlated market data the shrinkage is strictly interior.
    delta = ledoit_wolf_shrinkage(returns_panel.returns)
    assert 0.0 < delta < 1.0
    sigma = LedoitWolfCov().estimate(returns_panel.returns)
    assert _min_eig(sigma) >= -1e-8


# ──────────────────────────────────────────────────────────────────────────────
# Registries
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    ("name", "cls"),
    [("sample", SampleMu), ("ewma", EWMAMu), ("capm", CAPMMu)],
)
def test_get_return_estimator(name: str, cls: type) -> None:
    est = get_return_estimator(name)
    assert isinstance(est, cls)
    assert est.name == name


@pytest.mark.parametrize(
    ("name", "cls"),
    [("sample", SampleCov), ("ledoit_wolf", LedoitWolfCov), ("ewma", EWMACov)],
)
def test_get_cov_estimator(name: str, cls: type) -> None:
    est = get_cov_estimator(name)
    assert isinstance(est, cls)
    assert est.name == name


def test_get_return_estimator_passes_halflife() -> None:
    est = get_return_estimator("ewma", halflife=10)
    assert isinstance(est, EWMAMu)
    assert est.halflife == 10


def test_get_cov_estimator_passes_halflife() -> None:
    est = get_cov_estimator("ewma", halflife=10)
    assert isinstance(est, EWMACov)
    assert est.halflife == 10


def test_get_return_estimator_unknown_raises() -> None:
    with pytest.raises(KeyError):
        get_return_estimator("nope")


def test_get_cov_estimator_unknown_raises() -> None:
    with pytest.raises(KeyError):
        get_cov_estimator("nope")


# ──────────────────────────────────────────────────────────────────────────────
# Oracle cross-checks (PyPortfolioOpt) — TEST ORACLE ONLY
# ──────────────────────────────────────────────────────────────────────────────
def test_sample_mu_matches_pypfopt(synthetic_returns: np.ndarray) -> None:
    pypfopt = pytest.importorskip("pypfopt")

    prices = _price_frame(synthetic_returns)
    oracle = pypfopt.expected_returns.mean_historical_return(
        prices, frequency=TRADING_DAYS_PER_YEAR, compounding=False
    ).to_numpy()
    ours = SampleMu().estimate(synthetic_returns)
    np.testing.assert_allclose(ours, oracle, atol=1e-8)


def test_sample_cov_matches_pypfopt(synthetic_returns: np.ndarray) -> None:
    pypfopt = pytest.importorskip("pypfopt")

    prices = _price_frame(synthetic_returns)
    oracle = pypfopt.risk_models.sample_cov(prices, frequency=TRADING_DAYS_PER_YEAR).to_numpy()
    ours = SampleCov().estimate(synthetic_returns)
    assert np.linalg.norm(ours - oracle) < 1e-6


def test_ledoit_wolf_oracle_properties(synthetic_returns: np.ndarray) -> None:
    pypfopt = pytest.importorskip("pypfopt")

    est = LedoitWolfCov()
    ours = est.estimate(synthetic_returns)
    # Property checks: PSD + δ within the unit interval.
    assert _min_eig(ours) >= -1e-8
    assert est.last_shrinkage_ is not None
    assert 0.0 <= est.last_shrinkage_ <= 1.0

    # Loose oracle comparison (different shrinkage targets/derivations → loose tol).
    prices = _price_frame(synthetic_returns)
    cov_shrinkage = pypfopt.risk_models.CovarianceShrinkage(prices, frequency=TRADING_DAYS_PER_YEAR)
    oracle = cov_shrinkage.ledoit_wolf().to_numpy()
    assert oracle.shape == ours.shape
    assert np.linalg.norm(ours - oracle) < 1e-1
