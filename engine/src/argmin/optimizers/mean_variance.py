"""Core mean-variance optimizers: Global Min-Variance and Max-Sharpe (tangency).

Both are implemented from scratch with CVXPY (CVXPY is the modelling layer, not a
portfolio library). Outputs are assembled via :func:`argmin.types.build_result`
so portfolio statistics are derived identically across every model.

Max-Sharpe via convex reformulation (spec §2.2): the tangency portfolio that
maximizes ``(μ − rf)ᵀw / sqrt(wᵀΣw)`` is found by solving a convex QP in a
homogeneous variable ``y ≥ 0``::

    min  yᵀΣy   s.t.  (μ − rf)ᵀy = 1   (+ box constraints, linear in y)

and recovering ``w = y / 1ᵀy``. Box constraints on ``w`` are encoded linearly in
``y`` because ``w = y / 1ᵀy`` (e.g. ``w_i ≤ c`` ⇔ ``y_i ≤ c · 1ᵀy``).
"""

from __future__ import annotations

import cvxpy as cp
import numpy as np

from argmin.optimizers.base import (
    clean_weights,
    cvxpy_weight_constraints,
    solve,
)
from argmin.types import Constraints, Moments, OptimizeResult, build_result


class MinVariance:
    """Global Minimum-Variance portfolio: ``min wᵀΣw`` subject to constraints."""

    name = "min_variance"

    def optimize(
        self, moments: Moments, constraints: Constraints, risk_free: float
    ) -> OptimizeResult:
        n = len(moments.tickers)
        w = cp.Variable(n)
        objective = cp.Minimize(cp.quad_form(w, cp.psd_wrap(moments.sigma)))
        problem = cp.Problem(objective, cvxpy_weight_constraints(w, constraints))
        solve(problem)
        weights = clean_weights(np.asarray(w.value, dtype=np.float64))
        return build_result("min_variance", weights, moments, risk_free)


class MaxSharpe:
    """Tangency (max-Sharpe) portfolio via the homogeneous convex reformulation."""

    name = "max_sharpe"

    def optimize(
        self, moments: Moments, constraints: Constraints, risk_free: float
    ) -> OptimizeResult:
        n = len(moments.tickers)
        excess = moments.mu - risk_free

        # If no asset has positive excess return, the tangency problem is
        # infeasible (cannot normalize (μ−rf)ᵀy = 1 with y ≥ 0). Fall back to GMV.
        if not bool(np.any(excess > 0.0)):
            result = MinVariance().optimize(moments, constraints, risk_free)
            return build_result(
                "max_sharpe",
                result.weights,
                moments,
                risk_free,
                meta={"fallback": "min_variance", "reason": "no_positive_excess_return"},
            )

        y = cp.Variable(n)
        cons: list[cp.constraints.constraint.Constraint] = [excess @ y == 1.0]

        # Box/sign constraints, expressed linearly in y (w = y / sum(y)).
        sum_y = cp.sum(y)
        if constraints.long_only:
            cons.append(y >= 0)
        if constraints.max_weight is not None:
            cons.append(y <= constraints.max_weight * sum_y)
        if constraints.min_weight is not None:
            cons.append(y >= constraints.min_weight * sum_y)

        objective = cp.Minimize(cp.quad_form(y, cp.psd_wrap(moments.sigma)))
        problem = cp.Problem(objective, cons)

        try:
            solve(problem)
        except RuntimeError:
            # Numerically infeasible under the supplied constraints: fall back.
            result = MinVariance().optimize(moments, constraints, risk_free)
            return build_result(
                "max_sharpe",
                result.weights,
                moments,
                risk_free,
                meta={"fallback": "min_variance", "reason": "infeasible"},
            )

        y_val = np.asarray(y.value, dtype=np.float64)
        total = float(y_val.sum())
        if abs(total) <= 1e-12:
            result = MinVariance().optimize(moments, constraints, risk_free)
            return build_result(
                "max_sharpe",
                result.weights,
                moments,
                risk_free,
                meta={"fallback": "min_variance", "reason": "degenerate_solution"},
            )

        weights = clean_weights(y_val / total)
        return build_result("max_sharpe", weights, moments, risk_free)
