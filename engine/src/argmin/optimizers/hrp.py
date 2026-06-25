"""Hierarchical Risk Parity (López de Prado, 2016) — from scratch.

Owned by Phase 1C. Pipeline:

1. **Correlation** ρ from Σ (``ρ = Σ / (σ σᵀ)``).
2. **Distance** ``d_ij = √(½(1 − ρ_ij))`` (a proper metric on correlations).
3. **Hierarchical linkage** on the condensed distance matrix (scipy is permitted
   for building the dendrogram only).
4. **Quasi-diagonalization** — recover the leaf order from the linkage matrix by
   recursively expanding cluster ids, so correlated assets sit adjacently.
5. **Recursive bisection** — split the ordered list in two, allocate between the
   two clusters by **inverse cluster variance**, and recurse.

The linkage matrix is the only thing borrowed from scipy; quasi-diagonalization
and the bisection/allocation are hand-rolled. The result is deterministic: the
same Σ always yields the same weights. Long-only by construction (all weights are
products of positive inverse-variance ratios). μ and box constraints are ignored
(HRP is a pure covariance allocator — documented limitation).
"""

from __future__ import annotations

import numpy as np
from scipy.cluster.hierarchy import linkage
from scipy.spatial.distance import squareform

from argmin.optimizers.base import nearest_psd
from argmin.types import Constraints, FloatArray, Moments, OptimizeResult, build_result


def _quasi_diag(link: FloatArray, n_leaves: int) -> list[int]:
    """Recover the leaf ordering implied by a scipy linkage matrix.

    Cluster ids ``>= n_leaves`` reference rows of ``link`` (id ``n_leaves + k``
    is row ``k``); ids ``< n_leaves`` are original assets. We start from the root
    (the last merge) and iteratively expand any non-leaf id into its two
    children, preserving order, until only leaves remain.
    """
    root = n_leaves + link.shape[0] - 1
    order: list[int] = [root]
    while max(order) >= n_leaves:
        expanded: list[int] = []
        for node in order:
            if node < n_leaves:
                expanded.append(node)
            else:
                row = link[node - n_leaves]
                expanded.append(int(row[0]))
                expanded.append(int(row[1]))
        order = expanded
    return order


def _inverse_variance_weights(cov: FloatArray) -> FloatArray:
    """Inverse-variance portfolio weights for a covariance sub-block."""
    ivp = 1.0 / np.diag(cov)
    return np.asarray(ivp / ivp.sum(), dtype=np.float64)


def _cluster_variance(cov: FloatArray, idx: list[int]) -> float:
    """Variance of the inverse-variance portfolio over the assets in ``idx``."""
    sub = cov[np.ix_(idx, idx)]
    w = _inverse_variance_weights(sub)
    return float(w @ sub @ w)


def _recursive_bisection(cov: FloatArray, order: list[int]) -> FloatArray:
    """Allocate weights down the quasi-diagonal ordering via inverse cluster var."""
    n = cov.shape[0]
    weights = np.ones(n, dtype=np.float64)
    clusters: list[list[int]] = [order]
    while clusters:
        next_clusters: list[list[int]] = []
        for cluster in clusters:
            if len(cluster) <= 1:
                continue
            half = len(cluster) // 2
            left = cluster[:half]
            right = cluster[half:]
            var_left = _cluster_variance(cov, left)
            var_right = _cluster_variance(cov, right)
            alpha = 1.0 - var_left / (var_left + var_right)
            for i in left:
                weights[i] *= alpha
            for i in right:
                weights[i] *= 1.0 - alpha
            next_clusters.append(left)
            next_clusters.append(right)
        clusters = next_clusters
    return weights


class HierarchicalRiskParity:
    """López de Prado HRP allocator built from scratch on a scipy dendrogram."""

    name = "hrp"

    def optimize(
        self, moments: Moments, constraints: Constraints, risk_free: float
    ) -> OptimizeResult:
        n = len(moments.tickers)
        # ``nearest_psd`` uses an eigen-recomposition matmul that can raise
        # spurious FPE flags under some BLAS backends (e.g. Apple Accelerate)
        # even for well-conditioned inputs; silence those, the output is exact.
        with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
            sigma = nearest_psd(moments.sigma)

        if n == 1:
            return build_result("hrp", np.ones(1, dtype=np.float64), moments, risk_free)

        vols = np.sqrt(np.clip(np.diag(sigma), 1e-18, None))
        corr = sigma / np.outer(vols, vols)
        corr = np.clip(corr, -1.0, 1.0)

        dist = np.sqrt(np.clip(0.5 * (1.0 - corr), 0.0, None))
        np.fill_diagonal(dist, 0.0)
        condensed = squareform(dist, checks=False)

        link = np.asarray(linkage(condensed, method="single"), dtype=np.float64)
        order = _quasi_diag(link, n)
        weights = _recursive_bisection(sigma, order)
        weights = weights / weights.sum()

        return build_result("hrp", weights, moments, risk_free)
