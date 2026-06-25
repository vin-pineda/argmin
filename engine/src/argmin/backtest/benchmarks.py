"""Benchmark strategies and the shared target-weight simulation core.

A *target-weight stream* is a mapping from rebalance date to a desired weight
vector. The :func:`simulate_target_weights` core takes such a stream and walks it
forward day-by-day: between rebalances weights **drift** with realized returns,
and at each rebalance we snap back to the target, charging
``cost = (bps / 1e4) * turnover`` (where ``turnover = Σ|w_target − w_drifted|``)
on that day's return. The walk-forward strategy engine and every benchmark share
this exact core so their accounting is identical (an honest comparison).

Benchmarks defined here:

* ``equal_weight`` — ``1/N`` across the whole universe, rebalanced each period.
* ``sixty_forty`` — 60% SPY / 40% AGG, rebalanced each period.
* ``spy`` — 100% SPY, bought once and held (no further rebalancing).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import cast

import numpy as np
import numpy.typing as npt

from argmin.backtest.types import StrategyTrack
from argmin.types import FloatArray, ReturnsPanel

# Integer row-index arrays (rebalance indices). Distinct from ``FloatArray`` so
# the helpers stay honestly typed; the ``StrategyTrack`` contract stores dates and
# indices in ``FloatArray`` fields, so they are cast at that boundary.
IntArray = npt.NDArray[np.int64]
DateArray = npt.NDArray[np.datetime64]

# Tickers required by the canonical benchmarks.
_SIXTY_FORTY_EQUITY = "SPY"
_SIXTY_FORTY_BOND = "AGG"
_SPY = "SPY"


def simulate_target_weights(
    name: str,
    panel: ReturnsPanel,
    rebalance_indices: IntArray,
    target_weights: FloatArray,
    *,
    transaction_cost_bps: float,
) -> StrategyTrack:
    """Walk a target-weight stream forward over ``panel`` and build a track.

    Parameters
    ----------
    name:
        Human-readable strategy label stored on the resulting track.
    panel:
        The OOS returns panel; the simulation runs over **all** of its rows.
        ``panel.returns[i]`` are the simple returns *earned on day i*.
    rebalance_indices:
        Sorted integer row indices (into ``panel``) at which the portfolio is
        reset to its target weights. ``rebalance_indices[0]`` must be ``0`` — the
        first row establishes the initial position.
    target_weights:
        ``(R, N)`` array of target weight vectors, one per rebalance index.
    transaction_cost_bps:
        Linear cost in basis points charged against turnover on each rebalance
        day. Pass ``0.0`` for a frictionless run.

    Returns
    -------
    StrategyTrack
        Daily net returns, equity, drawdown, and per-rebalance turnover/weights.
    """
    reb_idx = np.asarray(rebalance_indices, dtype=np.int64)
    targets = np.asarray(target_weights, dtype=np.float64)
    if reb_idx.shape[0] == 0 or reb_idx[0] != 0:
        raise ValueError("rebalance_indices must start at 0")
    if targets.shape[0] != reb_idx.shape[0]:
        raise ValueError("target_weights rows must match rebalance_indices")

    n_days = panel.n_obs
    returns = panel.returns
    cost_rate = transaction_cost_bps / 1e4

    daily_returns = np.empty(n_days, dtype=np.float64)
    turnover = np.empty(reb_idx.shape[0], dtype=np.float64)

    # ``reb_at`` maps a row index → its position in ``reb_idx`` (or -1).
    reb_at = np.full(n_days, -1, dtype=np.int64)
    reb_at[reb_idx] = np.arange(reb_idx.shape[0])

    # ``w`` holds the *current* (drifted) weights carried across days.
    w = np.zeros(panel.n_assets, dtype=np.float64)
    for i in range(n_days):
        r = reb_at[i]
        if r >= 0:
            target = targets[r]
            turnover[r] = float(np.abs(target - w).sum())
            w = target.copy()
            gross = float(w @ returns[i])
            daily_returns[i] = gross - cost_rate * turnover[r]
        else:
            gross = float(w @ returns[i])
            daily_returns[i] = gross

        # Let weights drift with the day's realized returns for tomorrow.
        grown = w * (1.0 + returns[i])
        total = grown.sum()
        w = grown / total if total > 1e-12 else grown

    equity = np.cumprod(1.0 + daily_returns)
    running_max = np.maximum.accumulate(equity)
    drawdown = equity / running_max - 1.0

    return StrategyTrack(
        name=name,
        dates=cast(FloatArray, panel.dates.copy()),
        daily_returns=daily_returns,
        equity=equity,
        drawdown=drawdown,
        rebalance_dates=cast(FloatArray, panel.dates[reb_idx].copy()),
        weights_over_time=targets.copy(),
        turnover=turnover,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Benchmark target-weight rules
# ──────────────────────────────────────────────────────────────────────────────
def _fixed_weight_targets(weights: FloatArray, n_rebalances: int) -> FloatArray:
    """Tile a single weight vector across every rebalance (periodic reset)."""
    return np.tile(weights, (n_rebalances, 1))


def _equal_weight_targets(panel: ReturnsPanel, n_rebalances: int) -> FloatArray:
    n = panel.n_assets
    return _fixed_weight_targets(np.full(n, 1.0 / n), n_rebalances)


def _sixty_forty_targets(panel: ReturnsPanel, n_rebalances: int) -> FloatArray:
    w = np.zeros(panel.n_assets, dtype=np.float64)
    for ticker, weight in ((_SIXTY_FORTY_EQUITY, 0.6), (_SIXTY_FORTY_BOND, 0.4)):
        if ticker not in panel.tickers:
            raise ValueError(
                f"sixty_forty benchmark requires {ticker!r} in the universe; have {panel.tickers}"
            )
        w[panel.tickers.index(ticker)] = weight
    return _fixed_weight_targets(w, n_rebalances)


def _spy_targets(panel: ReturnsPanel, n_rebalances: int) -> FloatArray:
    if _SPY not in panel.tickers:
        raise ValueError(f"spy benchmark requires {_SPY!r} in the universe; have {panel.tickers}")
    w = np.zeros(panel.n_assets, dtype=np.float64)
    w[panel.tickers.index(_SPY)] = 1.0
    # Buy & hold: only set the target on the first day, then let it drift.
    return _fixed_weight_targets(w, n_rebalances)


# Registry: name → callable building (R, N) target weights for the OOS panel.
_BENCHMARK_TARGETS: dict[str, Callable[[ReturnsPanel, int], FloatArray]] = {
    "equal_weight": _equal_weight_targets,
    "sixty_forty": _sixty_forty_targets,
    "spy": _spy_targets,
}


def available_benchmarks() -> tuple[str, ...]:
    """Names of the supported benchmark strategies."""
    return tuple(_BENCHMARK_TARGETS)


def build_benchmark_track(
    name: str,
    panel: ReturnsPanel,
    rebalance_indices: IntArray,
    *,
    transaction_cost_bps: float,
) -> StrategyTrack:
    """Construct a :class:`StrategyTrack` for benchmark ``name`` over ``panel``.

    ``spy`` is a true buy & hold: its target is applied on the first row and then
    allowed to drift, so only the opening rebalance incurs turnover. The other
    benchmarks reset to their fixed target on every rebalance date.
    """
    if name not in _BENCHMARK_TARGETS:
        raise KeyError(f"Unknown benchmark {name!r}. Available: {sorted(_BENCHMARK_TARGETS)}")
    reb_idx = np.asarray(rebalance_indices, dtype=np.int64)

    if name == "spy":
        # Buy & hold: only rebalance once, on the first day.
        reb_idx = reb_idx[:1]

    targets = _BENCHMARK_TARGETS[name](panel, reb_idx.shape[0])
    return simulate_target_weights(
        name,
        panel,
        reb_idx,
        targets,
        transaction_cost_bps=transaction_cost_bps,
    )
