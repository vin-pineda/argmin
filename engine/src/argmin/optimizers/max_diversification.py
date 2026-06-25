"""Maximum Diversification portfolio (Choueifaty & Coignard, 2008).

Owned by Phase 1C. Maximize the diversification ratio

    DR(w) = (wᵀσ) / √(wᵀΣw),     σ = √diag(Σ),

subject to long-only and full-investment. DR is scale-invariant in ``w``, so the
problem is solved via the equivalent convex QP

    min wᵀΣw   s.t.   σᵀw = 1,   w ≥ 0,

and the solution is renormalized to ``Σw = 1``. Fixing ``σᵀw = 1`` removes the
scale degree of freedom and turns the ratio maximization into a standard QP.

μ is ignored (this is a pure risk/diversification allocator) and box constraints
beyond long-only are not enforced — documented limitation for this model.
"""

from __future__ import annotations

import cvxpy as cp
import numpy as np

from argmin.optimizers.base import clean_weights, nearest_psd, solve
from argmin.types import Constraints, Moments, OptimizeResult, build_result


class MaxDiversification:
    """Choueifaty & Coignard most-diversified portfolio via a convex QP."""

    name = "max_diversification"

    def optimize(
        self, moments: Moments, constraints: Constraints, risk_free: float
    ) -> OptimizeResult:
        n = len(moments.tickers)
        # ``nearest_psd`` uses an eigen-recomposition matmul that can raise
        # spurious FPE flags under some BLAS backends (e.g. Apple Accelerate)
        # even for well-conditioned inputs; silence those, the output is exact.
        with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
            sigma = nearest_psd(moments.sigma)
        vol = np.sqrt(np.clip(np.diag(sigma), 1e-18, None))

        w = cp.Variable(n)
        objective = cp.Minimize(cp.quad_form(w, cp.psd_wrap(sigma)))
        cons = [vol @ w == 1.0, w >= 0]
        problem = cp.Problem(objective, cons)
        solve(problem)

        raw = np.asarray(w.value, dtype=np.float64)
        weights = clean_weights(raw / raw.sum())
        return build_result("max_diversification", weights, moments, risk_free)
