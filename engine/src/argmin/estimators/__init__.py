"""Estimator registry: μ (expected returns) and Σ (covariance) estimators.

Each estimator consumes a ``(T, N)`` daily-simple-returns panel and returns an
**annualized** quantity. μ estimators satisfy :class:`argmin.types.ReturnEstimator`;
Σ estimators satisfy :class:`argmin.types.CovEstimator`. Registry names match the
config string values exactly (see :class:`argmin.config.EstimatorsConfig`).
"""

from __future__ import annotations

from argmin.estimators.mu import CAPMMu, EWMAMu, SampleMu
from argmin.estimators.sigma import (
    EWMACov,
    LedoitWolfCov,
    SampleCov,
    ledoit_wolf_shrinkage,
)
from argmin.types import CovEstimator, ReturnEstimator

__all__ = [
    "CAPMMu",
    "EWMACov",
    "EWMAMu",
    "LedoitWolfCov",
    "SampleCov",
    "SampleMu",
    "get_cov_estimator",
    "get_return_estimator",
    "ledoit_wolf_shrinkage",
]


def get_return_estimator(name: str, halflife: int = 63) -> ReturnEstimator:
    """Construct a μ estimator by config name (``sample``/``ewma``/``capm``)."""
    if name == "sample":
        return SampleMu()
    if name == "ewma":
        return EWMAMu(halflife=halflife)
    if name == "capm":
        return CAPMMu()
    raise KeyError(f"Unknown return estimator {name!r}. Available: ['capm', 'ewma', 'sample']")


def get_cov_estimator(name: str, halflife: int = 63) -> CovEstimator:
    """Construct a Σ estimator by config name (``sample``/``ledoit_wolf``/``ewma``)."""
    if name == "sample":
        return SampleCov()
    if name == "ledoit_wolf":
        return LedoitWolfCov()
    if name == "ewma":
        return EWMACov(halflife=halflife)
    raise KeyError(f"Unknown cov estimator {name!r}. Available: ['ewma', 'ledoit_wolf', 'sample']")
