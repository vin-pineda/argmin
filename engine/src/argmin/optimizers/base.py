"""Shared optimizer helpers: CVXPY constraint builder, weight cleanup, solver."""

from __future__ import annotations

import cvxpy as cp
import numpy as np

from argmin.types import Constraints, FloatArray

# Preferred convex solvers, in order (all bundled via the cvxpy extras).
_SOLVERS = [cp.CLARABEL, cp.OSQP, cp.SCS]


def cvxpy_weight_constraints(
    w: cp.Variable, constraints: Constraints
) -> list[cp.constraints.constraint.Constraint]:
    """Translate :class:`Constraints` into a list of CVXPY constraints on ``w``."""
    cons: list[cp.constraints.constraint.Constraint] = []
    if constraints.fully_invested:
        cons.append(cp.sum(w) == 1)
    if constraints.long_only:
        cons.append(w >= 0)
    if constraints.max_weight is not None:
        cons.append(w <= constraints.max_weight)
    if constraints.min_weight is not None:
        cons.append(w >= constraints.min_weight)
    if constraints.leverage_cap is not None:
        cons.append(cp.norm(w, 1) <= constraints.leverage_cap)
    return cons


def solve(problem: cp.Problem) -> None:
    """Solve a CVXPY problem, trying solvers in preference order."""
    last_err: Exception | None = None
    for solver in _SOLVERS:
        try:
            problem.solve(solver=solver)
            if problem.status in {cp.OPTIMAL, cp.OPTIMAL_INACCURATE}:
                return
        except Exception as exc:  # fall through to the next solver
            last_err = exc
    raise RuntimeError(f"All solvers failed (status={problem.status}); last error: {last_err}")


def clean_weights(
    weights: FloatArray, threshold: float = 1e-6, renormalize: bool = True
) -> FloatArray:
    """Zero out dust below ``threshold`` and (optionally) renormalize to sum 1."""
    w = np.asarray(weights, dtype=np.float64).ravel()
    w[np.abs(w) < threshold] = 0.0
    if renormalize:
        s = w.sum()
        if abs(s) > 1e-12:
            w = w / s
    return w


def nearest_psd(sigma: FloatArray) -> FloatArray:
    """Project a symmetric matrix onto the PSD cone (clip negative eigenvalues)."""
    s = (sigma + sigma.T) / 2.0
    vals, vecs = np.linalg.eigh(s)
    vals = np.clip(vals, 0.0, None)
    out = (vecs * vals) @ vecs.T
    return np.asarray((out + out.T) / 2.0, dtype=np.float64)
