"""Analytics & significance: tearsheet metrics and Sharpe-ratio honesty tools.

All functions consume 1-D arrays of **daily simple returns** ``(T,)`` and
annualize with ``periods_per_year`` (default 252). Metric definitions are chosen
to match the ``quantstats`` test oracle; see :mod:`argmin.analytics.metrics` and
:mod:`argmin.analytics.significance` for the exact conventions and sign rules.
"""

from __future__ import annotations

from argmin.analytics.metrics import (
    Tearsheet,
    compute_tearsheet,
    drawdown_series,
    equity_curve,
    rolling_sharpe,
)
from argmin.analytics.significance import (
    bootstrap_sharpe_ci,
    deflated_sharpe_ratio,
    probabilistic_sharpe_ratio,
)

__all__ = [
    "Tearsheet",
    "bootstrap_sharpe_ci",
    "compute_tearsheet",
    "deflated_sharpe_ratio",
    "drawdown_series",
    "equity_curve",
    "probabilistic_sharpe_ratio",
    "rolling_sharpe",
]
