"""Black-Litterman posterior + self-contained allocation.

Owned by Phase 1C. Steps:

1. **Market proxy.** ``w_mkt`` is ``self.market_weights`` if supplied, else the
   equal-weight portfolio. The equal-weight market proxy is a deliberate
   simplification (we have no market-cap data in-engine); document & accept it.
2. **Implied equilibrium returns** by reverse optimization:
   ``π = δ Σ w_mkt`` with ``δ = self.config.delta``.
3. **Views.** Each :class:`~argmin.config.BLView` contributes one row of ``P``
   (its ``picks`` mapping ticker→weight), one entry of ``Q`` (its ``value``), and
   one diagonal entry of ``Ω``. We use the standard Idzorek-style scaling
   ``Ω_kk = ((1 − conf)/conf) · (P τΣ Pᵀ)_kk`` so confidence → 1 collapses the
   view's uncertainty toward zero and confidence → 0 makes the view ignorable.
4. **Posterior** (Black-Litterman master formula):
   ``μ_BL = [(τΣ)⁻¹ + PᵀΩ⁻¹P]⁻¹ [(τΣ)⁻¹ π + PᵀΩ⁻¹ Q]``.
   With **no views**, ``μ_BL = π`` exactly (asserted in tests).
5. **Allocation** is self-contained (no dependency on ``mean_variance.py``):
   solve the quadratic-utility program
   ``max μ_BLᵀw − (δ/2) wᵀΣw  s.t. cvxpy_weight_constraints(w, constraints)``.

Σ in the posterior is symmetrized/PSD-projected for numerical stability.
"""

from __future__ import annotations

import cvxpy as cp
import numpy as np

from argmin.config import BlackLittermanConfig
from argmin.optimizers.base import (
    clean_weights,
    cvxpy_weight_constraints,
    nearest_psd,
    solve,
)
from argmin.types import Constraints, FloatArray, Moments, OptimizeResult, build_result


class BlackLitterman:
    name = "black_litterman"

    def __init__(
        self,
        config: BlackLittermanConfig | None = None,
        market_weights: FloatArray | None = None,
    ) -> None:
        self.config = config or BlackLittermanConfig()
        self.market_weights = market_weights  # None ⇒ equal-weight market proxy

    def _build_views(
        self, tickers: tuple[str, ...], tau_sigma: FloatArray
    ) -> tuple[FloatArray, FloatArray, FloatArray]:
        """Assemble ``(P, Q, Ω)`` from ``self.config.views``."""
        index = {t: i for i, t in enumerate(tickers)}
        n = len(tickers)
        k = len(self.config.views)
        P = np.zeros((k, n), dtype=np.float64)
        Q = np.zeros(k, dtype=np.float64)
        for row, view in enumerate(self.config.views):
            for ticker, weight in view.picks.items():
                if ticker in index:
                    P[row, index[ticker]] = weight
            Q[row] = view.value

        # Idzorek-style Ω: scale each view's prior variance by inverse confidence.
        prior_var = np.diag(P @ tau_sigma @ P.T)
        omega = np.zeros((k, k), dtype=np.float64)
        for row, view in enumerate(self.config.views):
            conf = min(max(view.confidence, 1e-6), 1.0 - 1e-9)
            omega[row, row] = ((1.0 - conf) / conf) * max(prior_var[row], 1e-12)
        return P, Q, omega

    def optimize(
        self, moments: Moments, constraints: Constraints, risk_free: float
    ) -> OptimizeResult:
        n = len(moments.tickers)
        # ``nearest_psd`` uses an eigen-recomposition matmul that can raise
        # spurious FPE flags under some BLAS backends (e.g. Apple Accelerate)
        # even for well-conditioned inputs; silence those, the output is exact.
        with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
            sigma = nearest_psd(moments.sigma)
        delta = self.config.delta
        tau = self.config.tau

        if self.market_weights is not None:
            w_mkt = np.asarray(self.market_weights, dtype=np.float64).ravel()
        else:
            w_mkt = np.full(n, 1.0 / n, dtype=np.float64)

        # Implied equilibrium (reverse-optimized) returns.
        pi = delta * (sigma @ w_mkt)

        if self.config.views:
            tau_sigma = tau * sigma
            P, Q, omega = self._build_views(moments.tickers, tau_sigma)

            tau_sigma_inv = np.linalg.inv(tau_sigma)
            omega_inv = np.linalg.inv(omega)

            precision = tau_sigma_inv + P.T @ omega_inv @ P
            rhs = tau_sigma_inv @ pi + P.T @ omega_inv @ Q
            mu_bl = np.linalg.solve(precision, rhs)
        else:
            # No views ⇒ posterior collapses to the prior π exactly.
            mu_bl = pi.copy()

        mu_bl = np.asarray(mu_bl, dtype=np.float64).ravel()

        # Self-contained quadratic-utility allocation on (μ_BL, Σ).
        w = cp.Variable(n)
        utility = mu_bl @ w - 0.5 * delta * cp.quad_form(w, cp.psd_wrap(sigma))
        problem = cp.Problem(cp.Maximize(utility), cvxpy_weight_constraints(w, constraints))
        solve(problem)

        weights = clean_weights(np.asarray(w.value, dtype=np.float64))
        return build_result(
            "black_litterman",
            weights,
            moments,
            risk_free,
            meta={"pi": pi.tolist(), "mu_bl": mu_bl.tolist()},
        )
