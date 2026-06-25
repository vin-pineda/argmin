"""Equal-Risk-Contribution (Risk Parity) via the Spinu log-barrier.

Owned by Phase 1C. We solve the convex Spinu (2013) formulation

    min_{w > 0}  f(w) = ½ wᵀΣw − (1/n) Σ_i ln(w_i)

with analytic gradient ``∇f(w) = Σw − (1/n)/w`` using L-BFGS-B over the box
``(1e-10, None)``, then normalize ``w /= w.sum()`` so ``Σw = 1``. At the optimum
the (unnormalized) first-order condition ``(Σw)_i = (1/n)/w_i`` implies the risk
contributions ``w_i (Σw)_i`` are identical across assets, i.e. true ERC.

Scope notes
-----------
* The portfolio is **long-only by construction** (the log barrier forces
  ``w > 0``); the ``long_only`` constraint is therefore always honoured.
* This optimizer **ignores μ** (it is a pure risk allocator) and **ignores box
  constraints** (``max_weight``/``min_weight``/``leverage_cap``): ERC weights are
  determined entirely by Σ. Those fields on :class:`Constraints` are accepted but
  not enforced — documented limitation for the risk-parity model.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from argmin.optimizers.base import nearest_psd
from argmin.types import Constraints, FloatArray, Moments, OptimizeResult, build_result


class RiskParity:
    """Equal-Risk-Contribution portfolio via the Spinu log-barrier objective."""

    name = "risk_parity"

    def optimize(
        self, moments: Moments, constraints: Constraints, risk_free: float
    ) -> OptimizeResult:
        n = len(moments.tickers)
        # ``nearest_psd`` uses an eigen-recomposition matmul that can raise
        # spurious FPE flags under some BLAS backends (e.g. Apple Accelerate)
        # even for well-conditioned inputs; silence those, the output is exact.
        with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
            sigma = nearest_psd(moments.sigma)

        def objective(w: FloatArray) -> float:
            quad = 0.5 * float(w @ sigma @ w)
            barrier = -float(np.sum(np.log(w))) / n
            return quad + barrier

        def gradient(w: FloatArray) -> FloatArray:
            grad = sigma @ w - (1.0 / n) / w
            return np.asarray(grad, dtype=np.float64)

        # Initialise at inverse-vol weights (well inside the feasible region).
        vols = np.sqrt(np.clip(np.diag(sigma), 1e-12, None))
        w0 = 1.0 / vols
        w0 = w0 / w0.sum()

        res = minimize(
            objective,
            w0,
            method="L-BFGS-B",
            jac=gradient,
            bounds=[(1e-10, None)] * n,
            options={"maxiter": 10_000, "ftol": 1e-15, "gtol": 1e-10},
        )

        w = np.asarray(res.x, dtype=np.float64)
        w = w / w.sum()
        return build_result("risk_parity", w, moments, risk_free)
