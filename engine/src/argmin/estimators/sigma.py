"""Covariance (Σ) estimators.

All estimators consume a ``(T, N)`` panel of **daily simple returns** and return
an **annualized** covariance matrix of shape ``(N, N)`` (daily Σ × 252), which is
symmetric and positive semi-definite, ``np.float64``.

Three flavours are provided:

* :class:`SampleCov`     — the plain sample covariance.
* :class:`LedoitWolfCov` — Ledoit-Wolf shrinkage toward a scaled identity.
* :class:`EWMACov`       — an exponentially-weighted covariance.

Each satisfies the :class:`argmin.types.CovEstimator` protocol.
"""

from __future__ import annotations

import numpy as np
from sklearn.covariance import LedoitWolf

from argmin.types import TRADING_DAYS_PER_YEAR, FloatArray

# Float-typed annualization factor so dtype stays float64 through arithmetic.
_ANNUALIZE = float(TRADING_DAYS_PER_YEAR)


def _as_2d(returns: FloatArray) -> FloatArray:
    """Validate and coerce the input panel to a contiguous ``(T, N)`` float64 array."""
    arr = np.asarray(returns, dtype=np.float64)
    if arr.ndim != 2:
        raise ValueError("returns must be 2-D (T, N)")
    if arr.shape[0] < 2:
        raise ValueError("need at least 2 observations to estimate Σ")
    return arr


def _symmetrize(sigma: FloatArray) -> FloatArray:
    """Force exact symmetry to wash out tiny floating-point asymmetries."""
    return np.asarray((sigma + sigma.T) / 2.0, dtype=np.float64)


def ledoit_wolf_shrinkage(returns: FloatArray) -> float:
    """Return the Ledoit-Wolf shrinkage intensity δ ∈ [0, 1].

    This is the scalar blend between the sample covariance and the shrinkage
    target (a scaled identity). It is exposed at module level so the web layer
    can "show the derivation" of the shrinkage without re-fitting a full
    estimator. Computed on **daily** returns; scale-invariant, so annualization
    does not affect it.
    """
    arr = _as_2d(returns)
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        estimator = LedoitWolf().fit(arr)
    return float(estimator.shrinkage_)


class SampleCov:
    """Annualized sample covariance: ``np.cov(R, rowvar=False) × 252``."""

    name = "sample"

    def estimate(self, returns: FloatArray) -> FloatArray:
        arr = _as_2d(returns)
        cov = np.cov(arr, rowvar=False)
        cov = np.atleast_2d(np.asarray(cov, dtype=np.float64))
        return _symmetrize(cov * _ANNUALIZE)


class LedoitWolfCov:
    """Annualized Ledoit-Wolf shrinkage covariance.

    Wraps :class:`sklearn.covariance.LedoitWolf` on daily returns and scales the
    result by 252. The fitted shrinkage intensity δ is stored on the instance as
    :attr:`last_shrinkage_` after each :meth:`estimate` call.
    """

    name = "ledoit_wolf"

    def __init__(self) -> None:
        self.last_shrinkage_: float | None = None

    def estimate(self, returns: FloatArray) -> FloatArray:
        arr = _as_2d(returns)
        with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
            estimator = LedoitWolf().fit(arr)
        self.last_shrinkage_ = float(estimator.shrinkage_)
        cov = np.asarray(estimator.covariance_, dtype=np.float64)
        return _symmetrize(cov * _ANNUALIZE)


class EWMACov:
    """Annualized exponentially-weighted covariance.

    Each row's deviation from the EWMA mean is weighted by an exponentially
    decaying factor (recent rows weighted most); ``halflife`` is in trading days
    (default 63 ≈ one quarter). The estimate is a convex combination of rank-1
    outer products, hence symmetric PSD by construction.
    """

    name = "ewma"

    def __init__(self, halflife: int = 63) -> None:
        if halflife <= 0:
            raise ValueError("halflife must be a positive number of days")
        self.halflife = halflife

    def _weights(self, n_obs: int) -> FloatArray:
        decay = 0.5 ** (1.0 / self.halflife)
        ages = np.arange(n_obs - 1, -1, -1, dtype=np.float64)  # oldest → newest
        raw = decay**ages
        return np.asarray(raw / raw.sum(), dtype=np.float64)

    def estimate(self, returns: FloatArray) -> FloatArray:
        arr = _as_2d(returns)
        weights = self._weights(arr.shape[0])
        # Long panels produce tiny (subnormal) EWMA weights; some BLAS backends
        # raise spurious FP-exception warnings on the matmul even though the
        # result is exact. Suppress those false positives locally.
        with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
            mean = weights @ arr  # EWMA mean, (N,)
            demeaned = arr - mean  # (T, N)
            # Weighted covariance: Σ = Σ_t w_t (x_t - μ)(x_t - μ)ᵀ.
            weighted = demeaned * weights[:, None]
            cov = demeaned.T @ weighted  # (N, N)
        cov = np.atleast_2d(np.asarray(cov, dtype=np.float64))
        return _symmetrize(cov * _ANNUALIZE)
