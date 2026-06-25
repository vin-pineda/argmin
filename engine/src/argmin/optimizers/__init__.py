"""Optimizer registry. The 7 allocation models + efficient frontier.

Each optimizer satisfies the :class:`argmin.types.Optimizer` protocol
(``optimize(moments, constraints, risk_free) -> OptimizeResult``).
"""

from __future__ import annotations

from argmin.optimizers.black_litterman import BlackLitterman
from argmin.optimizers.frontier import (
    FrontierPoint,
    FrontierResult,
    efficient_frontier,
)
from argmin.optimizers.hrp import HierarchicalRiskParity
from argmin.optimizers.max_diversification import MaxDiversification
from argmin.optimizers.mean_variance import MaxSharpe, MinVariance
from argmin.optimizers.risk_parity import RiskParity
from argmin.types import Optimizer

__all__ = [
    "BlackLitterman",
    "FrontierPoint",
    "FrontierResult",
    "HierarchicalRiskParity",
    "MaxDiversification",
    "MaxSharpe",
    "MinVariance",
    "RiskParity",
    "build_registry",
    "efficient_frontier",
    "get_optimizer",
    "list_optimizers",
]


def build_registry() -> dict[str, Optimizer]:
    """Map method name → a default-constructed optimizer instance."""
    return {
        "max_sharpe": MaxSharpe(),
        "min_variance": MinVariance(),
        "max_diversification": MaxDiversification(),
        "risk_parity": RiskParity(),
        "hrp": HierarchicalRiskParity(),
        "black_litterman": BlackLitterman(),
    }


def list_optimizers() -> list[str]:
    return list(build_registry().keys())


def get_optimizer(name: str) -> Optimizer:
    registry = build_registry()
    if name not in registry:
        raise KeyError(f"Unknown optimizer {name!r}. Available: {sorted(registry)}")
    return registry[name]
