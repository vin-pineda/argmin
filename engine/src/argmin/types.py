"""Shared contracts for the Argmin engine.

Every estimator, optimizer, backtest and API module codes against the types and
protocols defined here. Keeping them in one module lets the engine modules be
built independently without import cycles.

Conventions
-----------
* ``returns`` arrays are **daily simple returns**, shape ``(T, N)`` (rows = time,
  cols = assets), aligned to a fixed ``tickers`` ordering.
* ``mu`` and ``sigma`` are **annualized** (mu * 252, Sigma * 252).
* Weights are a 1-D array of length ``N`` aligned to the same ``tickers`` ordering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

import numpy as np
import numpy.typing as npt
from pydantic import BaseModel, ConfigDict, Field, model_validator

FloatArray = npt.NDArray[np.float64]

TRADING_DAYS_PER_YEAR = 252


# ──────────────────────────────────────────────────────────────────────────────
# Core data structures
# ──────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class ReturnsPanel:
    """An immutable panel of daily simple returns aligned to ``tickers``."""

    dates: npt.NDArray[np.datetime64]  # (T,)
    tickers: tuple[str, ...]
    returns: FloatArray  # (T, N)

    def __post_init__(self) -> None:
        if self.returns.ndim != 2:
            raise ValueError("returns must be 2-D (T, N)")
        if self.returns.shape[0] != self.dates.shape[0]:
            raise ValueError("dates length must match returns rows")
        if self.returns.shape[1] != len(self.tickers):
            raise ValueError("tickers length must match returns columns")

    @property
    def n_obs(self) -> int:
        return int(self.returns.shape[0])

    @property
    def n_assets(self) -> int:
        return int(self.returns.shape[1])

    def select(self, tickers: list[str] | tuple[str, ...]) -> ReturnsPanel:
        """Return a sub-panel restricted to ``tickers`` (preserving their order)."""
        idx = [self.tickers.index(t) for t in tickers]
        return ReturnsPanel(self.dates, tuple(tickers), self.returns[:, idx])

    def window(
        self,
        start: np.datetime64 | None = None,
        end: np.datetime64 | None = None,
    ) -> ReturnsPanel:
        """Slice rows to ``start <= date <= end`` (inclusive)."""
        mask = np.ones(self.n_obs, dtype=bool)
        if start is not None:
            mask &= self.dates >= start
        if end is not None:
            mask &= self.dates <= end
        return ReturnsPanel(self.dates[mask], self.tickers, self.returns[mask])

    def lookback(self, as_of: np.datetime64, years: float) -> ReturnsPanel:
        """Point-in-time window: rows with ``date <= as_of`` within ``years``.

        This is the no-look-ahead primitive used by the backtest — it never
        returns any observation dated after ``as_of``.
        """
        days = round(years * TRADING_DAYS_PER_YEAR)
        sub = self.window(end=as_of)
        if sub.n_obs > days:
            sub = ReturnsPanel(sub.dates[-days:], sub.tickers, sub.returns[-days:])
        return sub


@dataclass(frozen=True)
class Moments:
    """Annualized expected returns ``mu`` (N,) and covariance ``sigma`` (N, N)."""

    mu: FloatArray
    sigma: FloatArray
    tickers: tuple[str, ...]

    def __post_init__(self) -> None:
        n = len(self.tickers)
        if self.mu.shape != (n,):
            raise ValueError("mu must have shape (N,)")
        if self.sigma.shape != (n, n):
            raise ValueError("sigma must have shape (N, N)")


@dataclass(frozen=True)
class OptimizeResult:
    """Output of any optimizer: weights plus derived portfolio statistics."""

    method: str
    tickers: tuple[str, ...]
    weights: FloatArray  # (N,)
    exp_return: float  # annualized
    exp_vol: float  # annualized
    sharpe: float
    risk_contrib: FloatArray  # (N,), fractional, sums to 1
    meta: dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────────────
# Constraints (validated; shared by engine core + API)
# ──────────────────────────────────────────────────────────────────────────────
class Constraints(BaseModel):
    """Allocation constraints for ``/optimize`` and every optimizer.

    Defaults encode the canonical long-only, fully-invested portfolio.
    """

    model_config = ConfigDict(frozen=True)

    long_only: bool = True
    fully_invested: bool = True
    max_weight: float | None = Field(default=None, gt=0.0, le=1.0)
    min_weight: float | None = Field(default=None, ge=0.0, le=1.0)
    leverage_cap: float | None = Field(default=None, gt=0.0)

    @model_validator(mode="after")
    def _check(self) -> Constraints:
        if (
            self.max_weight is not None
            and self.min_weight is not None
            and self.min_weight > self.max_weight
        ):
            raise ValueError("min_weight cannot exceed max_weight")
        return self


# ──────────────────────────────────────────────────────────────────────────────
# Protocols (the engine contracts)
# ──────────────────────────────────────────────────────────────────────────────
@runtime_checkable
class ReturnEstimator(Protocol):
    """Maps a ``(T, N)`` daily-returns panel to ``(N,)`` annualized μ."""

    name: str

    def estimate(self, returns: FloatArray, risk_free: float = 0.0) -> FloatArray: ...


@runtime_checkable
class CovEstimator(Protocol):
    """Maps a ``(T, N)`` daily-returns panel to ``(N, N)`` annualized Σ."""

    name: str

    def estimate(self, returns: FloatArray) -> FloatArray: ...


@runtime_checkable
class Optimizer(Protocol):
    """Maps ``(Moments, Constraints, risk_free)`` to an ``OptimizeResult``."""

    name: str

    def optimize(
        self, moments: Moments, constraints: Constraints, risk_free: float
    ) -> OptimizeResult: ...


# ──────────────────────────────────────────────────────────────────────────────
# Shared portfolio math (used to build consistent OptimizeResults)
# ──────────────────────────────────────────────────────────────────────────────
def portfolio_moments(
    weights: FloatArray, moments: Moments, risk_free: float
) -> tuple[float, float, float]:
    """Return ``(annualized return, annualized vol, Sharpe)`` for ``weights``."""
    ret = float(weights @ moments.mu)
    var = float(weights @ moments.sigma @ weights)
    vol = float(np.sqrt(max(var, 0.0)))
    sharpe = (ret - risk_free) / vol if vol > 1e-12 else 0.0
    return ret, vol, sharpe


def risk_contributions(weights: FloatArray, sigma: FloatArray) -> FloatArray:
    """Fractional risk contributions ``w_i (Σw)_i / wᵀΣw`` (sum to 1)."""
    port_var = float(weights @ sigma @ weights)
    if port_var <= 1e-18:
        n = weights.shape[0]
        return np.full(n, 1.0 / n)
    contrib = weights * (sigma @ weights)
    return np.asarray(contrib / port_var, dtype=np.float64)


def build_result(
    method: str,
    weights: FloatArray,
    moments: Moments,
    risk_free: float,
    meta: dict[str, Any] | None = None,
) -> OptimizeResult:
    """Assemble a uniform :class:`OptimizeResult` from a weight vector.

    Every optimizer should compute ``weights`` and return ``build_result(...)``
    so portfolio statistics are derived identically across models.
    """
    weights = np.asarray(weights, dtype=np.float64).ravel()
    ret, vol, sharpe = portfolio_moments(weights, moments, risk_free)
    return OptimizeResult(
        method=method,
        tickers=moments.tickers,
        weights=weights,
        exp_return=ret,
        exp_vol=vol,
        sharpe=sharpe,
        risk_contrib=risk_contributions(weights, moments.sigma),
        meta=meta or {},
    )
