"""Efficient frontier tracing + random portfolio cloud.

Owned by Phase 1B. ``efficient_frontier`` sweeps target returns between the
min-variance and max-return portfolios, solving min-variance s.t. a return
target at each step, and also returns the tangency (max-Sharpe) and min-var
portfolios plus a seeded random long-only cloud for the visx scatter.
"""

from __future__ import annotations

from dataclasses import dataclass

import cvxpy as cp
import numpy as np

from argmin.optimizers.base import (
    clean_weights,
    cvxpy_weight_constraints,
    solve,
)
from argmin.optimizers.mean_variance import MaxSharpe, MinVariance
from argmin.types import (
    Constraints,
    FloatArray,
    Moments,
    OptimizeResult,
    portfolio_moments,
)


@dataclass(frozen=True)
class FrontierPoint:
    target_return: float
    ret: float
    vol: float
    sharpe: float
    weights: FloatArray


@dataclass(frozen=True)
class FrontierResult:
    tickers: tuple[str, ...]
    points: list[FrontierPoint]
    tangency: OptimizeResult
    min_var: OptimizeResult
    random_cloud_vol: FloatArray  # (M,)
    random_cloud_ret: FloatArray  # (M,)


def _min_variance_for_target(
    moments: Moments,
    constraints: Constraints,
    target: float,
) -> FloatArray | None:
    """Solve ``min wᵀΣw s.t. μᵀw ≥ target`` + constraints; ``None`` if infeasible."""
    n = len(moments.tickers)
    w = cp.Variable(n)
    cons = cvxpy_weight_constraints(w, constraints)
    cons.append(moments.mu @ w >= target)
    problem = cp.Problem(cp.Minimize(cp.quad_form(w, cp.psd_wrap(moments.sigma))), cons)
    try:
        solve(problem)
    except RuntimeError:
        return None
    if w.value is None:
        return None
    return clean_weights(np.asarray(w.value, dtype=np.float64))


def efficient_frontier(
    moments: Moments,
    constraints: Constraints,
    risk_free: float,
    n_points: int = 40,
    n_random: int = 1500,
    seed: int = 42,
) -> FrontierResult:
    """Trace the efficient frontier and build a seeded random long-only cloud."""
    min_var = MinVariance().optimize(moments, constraints, risk_free)
    tangency = MaxSharpe().optimize(moments, constraints, risk_free)

    # Sweep target returns from the min-variance return up to (just below) the
    # max single-asset return; below the max keeps the highest target feasible.
    lo = min_var.exp_return
    hi = float(np.max(moments.mu)) * 0.999
    targets = np.linspace(lo, hi, n_points)

    points: list[FrontierPoint] = []
    for target in targets:
        weights = _min_variance_for_target(moments, constraints, float(target))
        if weights is None:
            continue
        ret, vol, sharpe = portfolio_moments(weights, moments, risk_free)
        points.append(
            FrontierPoint(
                target_return=float(target),
                ret=ret,
                vol=vol,
                sharpe=sharpe,
                weights=weights,
            )
        )

    # Seeded random long-only cloud: Dirichlet(ones(N)) draws (sum to 1, w ≥ 0).
    n = len(moments.tickers)
    rng = np.random.default_rng(seed)
    cloud_w = rng.dirichlet(np.ones(n), size=n_random)  # (n_random, N)
    # ``einsum`` rather than ``@``: avoids spurious matmul warnings from the
    # macOS Accelerate BLAS backend (it reads uninitialized SIMD pad lanes).
    cloud_ret = np.einsum("ij,j->i", cloud_w, moments.mu).astype(np.float64)
    cloud_var = np.einsum("ij,jk,ik->i", cloud_w, moments.sigma, cloud_w)
    cloud_vol = np.sqrt(np.clip(cloud_var, 0.0, None)).astype(np.float64)

    return FrontierResult(
        tickers=moments.tickers,
        points=points,
        tangency=tangency,
        min_var=min_var,
        random_cloud_vol=cloud_vol,
        random_cloud_ret=cloud_ret,
    )
