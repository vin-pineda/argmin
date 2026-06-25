"""Property + correctness tests for the advanced optimizers.

Covers Risk Parity (ERC), Hierarchical Risk Parity, Maximum Diversification, and
Black-Litterman. Property tests are primary; an optional PyPortfolioOpt cross-check
(oracle) is included for HRP and skipped when the oracle is unavailable.
"""

from __future__ import annotations

import numpy as np
import pytest

from argmin.config import BlackLittermanConfig, BLView
from argmin.optimizers.black_litterman import BlackLitterman
from argmin.optimizers.hrp import HierarchicalRiskParity
from argmin.optimizers.max_diversification import MaxDiversification
from argmin.optimizers.risk_parity import RiskParity
from argmin.types import Constraints, Moments, risk_contributions


def _diversification_ratio(w: np.ndarray, sigma: np.ndarray) -> float:
    vol = np.sqrt(np.diag(sigma))
    port_vol = np.sqrt(float(w @ sigma @ w))
    return float(w @ vol) / port_vol


# ──────────────────────────────────────────────────────────────────────────────
# Risk Parity (ERC)
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("fixture", ["toy_moments", "sample_moments"])
def test_erc_equal_risk_contributions(fixture: str, request: pytest.FixtureRequest) -> None:
    moments: Moments = request.getfixturevalue(fixture)
    constraints = Constraints()
    result = RiskParity().optimize(moments, constraints, risk_free=0.0)

    w = result.weights
    assert np.isclose(w.sum(), 1.0, atol=1e-8)
    assert np.all(w > 0.0)

    rc = risk_contributions(w, moments.sigma)
    assert rc.max() - rc.min() < 1e-4
    # Cross-check against the OptimizeResult's stored fractional risk contrib.
    assert np.allclose(rc, result.risk_contrib, atol=1e-10)


# ──────────────────────────────────────────────────────────────────────────────
# Hierarchical Risk Parity
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("fixture", ["toy_moments", "sample_moments"])
def test_hrp_simplex(fixture: str, request: pytest.FixtureRequest) -> None:
    moments: Moments = request.getfixturevalue(fixture)
    result = HierarchicalRiskParity().optimize(moments, Constraints(), risk_free=0.0)
    w = result.weights
    assert np.isclose(w.sum(), 1.0, atol=1e-8)
    assert np.all(w >= 0.0)
    assert np.all(w > 0.0)  # every asset gets a strictly positive share


def test_hrp_deterministic(sample_moments: Moments) -> None:
    r1 = HierarchicalRiskParity().optimize(sample_moments, Constraints(), risk_free=0.0)
    r2 = HierarchicalRiskParity().optimize(sample_moments, Constraints(), risk_free=0.0)
    assert np.array_equal(r1.weights, r2.weights)


def test_hrp_oracle_crosscheck(sample_moments: Moments) -> None:
    pytest.importorskip("pypfopt")
    pd = pytest.importorskip("pandas")
    from pypfopt.hierarchical_portfolio import HRPOpt  # noqa: PLC0415

    # Oracle reads tickers off the covariance DataFrame's labels.
    tickers = list(sample_moments.tickers)
    cov = pd.DataFrame(sample_moments.sigma, index=tickers, columns=tickers)
    oracle = HRPOpt(cov_matrix=cov)
    try:
        oracle.optimize(linkage_method="single")
    except AttributeError as exc:
        # Some PyPortfolioOpt / SciPy version pairs are incompatible (e.g. the
        # removal of ``scipy.cluster.hierarchy._LINKAGE_METHODS``). The oracle
        # check is optional; property tests above are the source of truth.
        pytest.skip(f"PyPortfolioOpt/SciPy version mismatch: {exc}")
    oracle_w = np.array([oracle.clean_weights()[t] for t in sample_moments.tickers])

    ours = HierarchicalRiskParity().optimize(sample_moments, Constraints(), 0.0).weights
    # Same algorithm family; allow a loose tolerance for renormalization/cleaning.
    assert np.allclose(ours, oracle_w, atol=5e-2)


# ──────────────────────────────────────────────────────────────────────────────
# Maximum Diversification
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("fixture", ["toy_moments", "sample_moments"])
def test_max_div_simplex_and_ratio(fixture: str, request: pytest.FixtureRequest) -> None:
    moments: Moments = request.getfixturevalue(fixture)
    result = MaxDiversification().optimize(moments, Constraints(), risk_free=0.0)
    w = result.weights
    assert np.isclose(w.sum(), 1.0, atol=1e-8)
    assert np.all(w >= -1e-9)

    n = len(moments.tickers)
    eq = np.full(n, 1.0 / n)
    dr_opt = _diversification_ratio(w, moments.sigma)
    dr_eq = _diversification_ratio(eq, moments.sigma)
    assert dr_opt >= dr_eq - 1e-8


# ──────────────────────────────────────────────────────────────────────────────
# Black-Litterman
# ──────────────────────────────────────────────────────────────────────────────
def test_bl_no_views_collapses_to_pi(toy_moments: Moments) -> None:
    bl = BlackLitterman(config=BlackLittermanConfig(views=[]))
    result = bl.optimize(toy_moments, Constraints(), risk_free=0.0)

    pi = np.array(result.meta["pi"])
    mu_bl = np.array(result.meta["mu_bl"])
    assert np.allclose(mu_bl, pi, atol=1e-8)
    assert np.isclose(result.weights.sum(), 1.0, atol=1e-8)
    assert np.all(result.weights >= -1e-9)


def test_bl_bullish_view_raises_weight(toy_moments: Moments) -> None:
    base = BlackLitterman(config=BlackLittermanConfig(views=[]))
    base_w = base.optimize(toy_moments, Constraints(), risk_free=0.0).weights

    idx = toy_moments.tickers.index("A")
    pi = np.array(base.optimize(toy_moments, Constraints(), 0.0).meta["pi"])
    # A strong absolute view that asset A beats its equilibrium return.
    view = BLView(picks={"A": 1.0}, value=float(pi[idx]) + 0.15, confidence=0.9)
    bullish = BlackLitterman(config=BlackLittermanConfig(views=[view]))
    bull_w = bullish.optimize(toy_moments, Constraints(), risk_free=0.0).weights

    assert bull_w[idx] > base_w[idx] + 1e-6
    assert np.isclose(bull_w.sum(), 1.0, atol=1e-8)
