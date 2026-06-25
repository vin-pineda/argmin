"""Tests for the core mean-variance optimizers and the efficient frontier.

Property checks (Σw=1, long-only, max_weight), a GMV closed-form check against
``Σ⁻¹1 / 1ᵀΣ⁻¹1``, Sharpe-dominance of the tangency portfolio, frontier
consistency, and optional cross-checks against the PyPortfolioOpt oracle.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from argmin.optimizers.frontier import efficient_frontier
from argmin.optimizers.mean_variance import MaxSharpe, MinVariance
from argmin.types import Constraints, Moments, portfolio_moments


# ──────────────────────────────────────────────────────────────────────────────
# Property tests
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("method", [MinVariance(), MaxSharpe()])
def test_weights_sum_to_one_and_long_only(
    method: MinVariance | MaxSharpe, sample_moments: Moments
) -> None:
    result = method.optimize(sample_moments, Constraints(), 0.02)
    assert abs(result.weights.sum() - 1.0) < 1e-6
    assert np.all(result.weights >= -1e-8)


@pytest.mark.parametrize("method", [MinVariance(), MaxSharpe()])
def test_max_weight_respected(method: MinVariance | MaxSharpe, sample_moments: Moments) -> None:
    constraints = Constraints(max_weight=0.4)
    result = method.optimize(sample_moments, constraints, 0.02)
    assert abs(result.weights.sum() - 1.0) < 1e-6
    assert np.all(result.weights <= 0.4 + 1e-6)
    assert np.all(result.weights >= -1e-8)


# ──────────────────────────────────────────────────────────────────────────────
# GMV closed form
# ──────────────────────────────────────────────────────────────────────────────
def test_gmv_closed_form(toy_moments: Moments) -> None:
    # Only fully-invested (no box, no long-only) ⇒ unconstrained GMV closed form.
    constraints = Constraints(long_only=False)
    result = MinVariance().optimize(toy_moments, constraints, 0.0)

    ones = np.ones(len(toy_moments.tickers))
    inv = np.linalg.inv(toy_moments.sigma)
    w_closed = inv @ ones / (ones @ inv @ ones)

    np.testing.assert_allclose(result.weights, w_closed, atol=1e-5)


# ──────────────────────────────────────────────────────────────────────────────
# Max-Sharpe dominance
# ──────────────────────────────────────────────────────────────────────────────
def test_max_sharpe_dominates(sample_moments: Moments) -> None:
    rf = 0.02
    tangency = MaxSharpe().optimize(sample_moments, Constraints(), rf)
    min_var = MinVariance().optimize(sample_moments, Constraints(), rf)

    n = len(sample_moments.tickers)
    equal_weight = np.full(n, 1.0 / n)
    _, _, eq_sharpe = portfolio_moments(equal_weight, sample_moments, rf)

    assert tangency.sharpe >= eq_sharpe - 1e-9
    assert tangency.sharpe >= min_var.sharpe - 1e-9


def test_max_sharpe_fallback_when_no_positive_excess() -> None:
    # All excess returns negative ⇒ tangency infeasible ⇒ GMV fallback.
    tickers = ("A", "B")
    mu = np.array([0.01, 0.02])
    sigma = np.array([[0.04, 0.0], [0.0, 0.09]])
    moments = Moments(mu=mu, sigma=sigma, tickers=tickers)

    result = MaxSharpe().optimize(moments, Constraints(), 0.05)
    assert result.meta.get("fallback") == "min_variance"
    assert abs(result.weights.sum() - 1.0) < 1e-6


# ──────────────────────────────────────────────────────────────────────────────
# Efficient frontier
# ──────────────────────────────────────────────────────────────────────────────
def test_efficient_frontier(sample_moments: Moments) -> None:
    rf = 0.02
    n_random = 800
    fr = efficient_frontier(
        sample_moments, Constraints(), rf, n_points=30, n_random=n_random, seed=42
    )

    assert len(fr.points) > 0
    # Tangency is the global Sharpe maximizer over the feasible set.
    max_point_sharpe = max(p.sharpe for p in fr.points)
    assert fr.tangency.sharpe >= max_point_sharpe - 1e-6

    # All frontier points are valid long-only portfolios with positive vol.
    for p in fr.points:
        assert p.vol > 0.0
        assert abs(p.weights.sum() - 1.0) < 1e-6
        assert np.all(p.weights >= -1e-8)

    # Random cloud: right length and finite.
    assert fr.random_cloud_vol.shape == (n_random,)
    assert fr.random_cloud_ret.shape == (n_random,)
    assert np.all(np.isfinite(fr.random_cloud_vol))
    assert np.all(np.isfinite(fr.random_cloud_ret))
    assert np.all(fr.random_cloud_vol > 0.0)


def test_efficient_frontier_random_cloud_deterministic(sample_moments: Moments) -> None:
    rf = 0.02
    a = efficient_frontier(sample_moments, Constraints(), rf, n_points=10, n_random=200, seed=7)
    b = efficient_frontier(sample_moments, Constraints(), rf, n_points=10, n_random=200, seed=7)
    np.testing.assert_array_equal(a.random_cloud_vol, b.random_cloud_vol)
    np.testing.assert_array_equal(a.random_cloud_ret, b.random_cloud_ret)


# ──────────────────────────────────────────────────────────────────────────────
# Oracle cross-checks (PyPortfolioOpt) — TEST ORACLE ONLY
# ──────────────────────────────────────────────────────────────────────────────
def test_min_variance_vs_oracle(sample_moments: Moments) -> None:
    pypfopt = pytest.importorskip("pypfopt")
    EfficientFrontier = pypfopt.EfficientFrontier

    tickers = list(sample_moments.tickers)
    mu = pd.Series(sample_moments.mu, index=tickers)
    S = pd.DataFrame(sample_moments.sigma, index=tickers, columns=tickers)

    ef = EfficientFrontier(mu, S, weight_bounds=(0, 1))
    ef.min_volatility()
    _, oracle_vol, _ = ef.portfolio_performance(risk_free_rate=0.0)

    ours = MinVariance().optimize(sample_moments, Constraints(), 0.0)
    assert abs(ours.exp_vol - oracle_vol) < 1e-3


def test_max_sharpe_vs_oracle(sample_moments: Moments) -> None:
    pypfopt = pytest.importorskip("pypfopt")
    EfficientFrontier = pypfopt.EfficientFrontier

    rf = 0.02
    tickers = list(sample_moments.tickers)
    mu = pd.Series(sample_moments.mu, index=tickers)
    S = pd.DataFrame(sample_moments.sigma, index=tickers, columns=tickers)

    ef = EfficientFrontier(mu, S, weight_bounds=(0, 1))
    ef.max_sharpe(risk_free_rate=rf)
    _, _, oracle_sharpe = ef.portfolio_performance(risk_free_rate=rf)

    ours = MaxSharpe().optimize(sample_moments, Constraints(), rf)
    assert abs(ours.sharpe - oracle_sharpe) < 1e-2
