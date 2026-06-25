"""Expected-return (μ) estimators.

All estimators consume a ``(T, N)`` panel of **daily simple returns** and return
an **annualized** μ vector of shape ``(N,)`` (daily mean × 252), ``np.float64``.

Three flavours are provided:

* :class:`SampleMu`  — the historical (sample) mean.
* :class:`EWMAMu`    — an exponentially-weighted mean (recent obs weighted most).
* :class:`CAPMMu`    — CAPM-implied μ using an equal-weight market proxy.

Each satisfies the :class:`argmin.types.ReturnEstimator` protocol.
"""

from __future__ import annotations

import numpy as np

from argmin.types import TRADING_DAYS_PER_YEAR, FloatArray


def _as_2d(returns: FloatArray) -> FloatArray:
    """Validate and coerce the input panel to a contiguous ``(T, N)`` float64 array."""
    arr = np.asarray(returns, dtype=np.float64)
    if arr.ndim != 2:
        raise ValueError("returns must be 2-D (T, N)")
    if arr.shape[0] < 2:
        raise ValueError("need at least 2 observations to estimate μ")
    return arr


def _ewma_weights(n_obs: int, halflife: int) -> FloatArray:
    """Normalized EWMA weights of length ``n_obs`` (most recent row weighted most).

    The decay factor ``λ = 0.5 ** (1 / halflife)`` gives observation ``t`` (with
    ``t = 0`` the oldest row) a raw weight ``λ ** (n_obs - 1 - t)`` so the final
    (most recent) row carries weight ``λ ** 0 = 1``. Weights sum to 1.
    """
    if halflife <= 0:
        raise ValueError("halflife must be a positive number of days")
    decay = 0.5 ** (1.0 / halflife)
    ages = np.arange(n_obs - 1, -1, -1, dtype=np.float64)  # oldest → newest
    raw = decay**ages
    return np.asarray(raw / raw.sum(), dtype=np.float64)


class SampleMu:
    """Annualized sample mean of daily returns: ``mean(R, axis=0) × 252``."""

    name = "sample"

    def estimate(self, returns: FloatArray, risk_free: float = 0.0) -> FloatArray:
        arr = _as_2d(returns)
        mu = arr.mean(axis=0) * TRADING_DAYS_PER_YEAR
        return np.asarray(mu, dtype=np.float64)


class EWMAMu:
    """Annualized exponentially-weighted mean of daily returns.

    The most recent observation is weighted most heavily; ``halflife`` is in
    trading days (default 63 ≈ one quarter).
    """

    name = "ewma"

    def __init__(self, halflife: int = 63) -> None:
        if halflife <= 0:
            raise ValueError("halflife must be a positive number of days")
        self.halflife = halflife

    def estimate(self, returns: FloatArray, risk_free: float = 0.0) -> FloatArray:
        arr = _as_2d(returns)
        weights = _ewma_weights(arr.shape[0], self.halflife)
        # Long panels produce tiny (subnormal) EWMA weights; some BLAS backends
        # raise spurious FP-exception warnings on the matmul even though the
        # result is exact. Suppress those false positives locally.
        with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
            mu = (weights @ arr) * TRADING_DAYS_PER_YEAR
        return np.asarray(mu, dtype=np.float64)


class CAPMMu:
    """CAPM-implied expected returns.

    The market proxy is the **equal-weight portfolio of the panel's assets**
    (a deliberate, documented simplification — the engine has no exogenous index
    in-panel). For each asset ``i``::

        β_i  = cov(r_i, r_mkt) / var(r_mkt)        # on daily returns
        μ_i  = rf + β_i (μ_mkt − rf)               # annualized

    where ``μ_mkt`` is the annualized mean of the equal-weight proxy and ``rf``
    is the annualized risk-free rate passed to :meth:`estimate`.
    """

    name = "capm"

    def estimate(self, returns: FloatArray, risk_free: float = 0.0) -> FloatArray:
        arr = _as_2d(returns)
        # Equal-weight market proxy (daily) and its annualized mean.
        r_mkt = arr.mean(axis=1)  # (T,)
        mu_mkt = float(r_mkt.mean()) * TRADING_DAYS_PER_YEAR
        var_mkt = float(r_mkt.var(ddof=1))
        if var_mkt <= 1e-18:
            # Degenerate market: every asset gets the risk-free rate.
            return np.full(arr.shape[1], float(risk_free), dtype=np.float64)
        # cov(r_i, r_mkt) for every asset i, in one shot. ``np.errstate`` guards
        # against spurious BLAS FP-exception warnings on long panels.
        demeaned = arr - arr.mean(axis=0, keepdims=True)
        mkt_demeaned = r_mkt - r_mkt.mean()
        with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
            cov_i_mkt = (demeaned.T @ mkt_demeaned) / (arr.shape[0] - 1)  # (N,)
        beta = cov_i_mkt / var_mkt
        mu = risk_free + beta * (mu_mkt - risk_free)
        return np.asarray(mu, dtype=np.float64)
