"""The walk-forward backtest engine.

``run_backtest`` simulates a rebalanced strategy with **no look-ahead**: at each
rebalance date it estimates μ, Σ from a point-in-time rolling window
(``date ≤ t``), optimizes target weights, then walks the portfolio forward
day-by-day (weights drift between rebalances) charging linear transaction costs
on turnover. The same OOS dates drive every benchmark, so the comparison is
honest.

Determinism
-----------
The per-rebalance weight vectors are independent given their lookback windows, so
they are computed with :class:`joblib.Parallel`. Parallelism is order-preserving
(results come back in submission order) and the estimators/optimizers are pure
given their inputs, so the result is **identical** across runs for a fixed data
snapshot and seed. ``seed`` is threaded through so that any future stochastic
optimizer stays reproducible.
"""

from __future__ import annotations

import numpy as np
from joblib import Parallel, delayed

from argmin.backtest.benchmarks import (
    DateArray,
    IntArray,
    build_benchmark_track,
    simulate_target_weights,
)
from argmin.backtest.types import BacktestResult, StrategyTrack
from argmin.config import ArgminConfig
from argmin.estimators import get_cov_estimator, get_return_estimator
from argmin.optimizers import get_optimizer
from argmin.types import Constraints, FloatArray, Moments, ReturnsPanel


def _month_key(dates: DateArray) -> IntArray:
    """Integer ``year*12 + month`` for each datetime64 date (for grouping months)."""
    years = dates.astype("datetime64[Y]").astype(np.int64) + 1970
    months = dates.astype("datetime64[M]").astype(np.int64) % 12  # 0..11
    return years * 12 + months


def _first_trading_day_indices(dates: DateArray) -> IntArray:
    """Row index of the first trading day of each calendar month in ``dates``.

    ``dates`` must be sorted ascending. Returns the indices of the rows that open
    a new ``(year, month)`` group — i.e. the first available trading day of each
    month.
    """
    keys = _month_key(dates)
    # A row starts a new month iff its key differs from the previous row's.
    is_new = np.empty(keys.shape[0], dtype=bool)
    is_new[0] = True
    is_new[1:] = keys[1:] != keys[:-1]
    return np.nonzero(is_new)[0].astype(np.int64)


def _compute_weights(
    panel: ReturnsPanel,
    as_of: np.datetime64,
    *,
    lookback_years: int,
    method: str,
    mu_method: str,
    cov_method: str,
    halflife: int,
    constraints: Constraints,
    risk_free: float,
    seed: np.random.SeedSequence,
) -> FloatArray:
    """Estimate μ, Σ from the point-in-time lookback and optimize target weights.

    This is the only place that touches data; it reads **strictly** the
    ``date ≤ as_of`` lookback window, guaranteeing no look-ahead. ``seed`` is a
    per-rebalance child seed reserved for any future stochastic optimizer; the
    current optimizers are deterministic and ignore it.
    """
    _ = seed  # reserved for future stochastic optimizers; keeps runs reproducible
    sub = panel.lookback(as_of, lookback_years)
    mu_estimator = get_return_estimator(mu_method, halflife)
    cov_estimator = get_cov_estimator(cov_method, halflife)
    mu = mu_estimator.estimate(sub.returns, risk_free)
    sigma = cov_estimator.estimate(sub.returns)
    moments = Moments(mu=mu, sigma=sigma, tickers=sub.tickers)
    result = get_optimizer(method).optimize(moments, constraints, risk_free)
    return np.asarray(result.weights, dtype=np.float64).ravel()


def run_backtest(
    config: ArgminConfig,
    panel: ReturnsPanel,
    *,
    method: str | None = None,
    constraints: Constraints | None = None,
    risk_free: float | None = None,
    seed: int = 42,
) -> BacktestResult:
    """Run the walk-forward backtest for ``method`` over ``panel``.

    Parameters
    ----------
    config:
        Scenario config supplying estimators, the backtest schedule, costs, and
        the benchmark list.
    panel:
        Full daily-returns panel. Only point-in-time lookbacks are read at each
        rebalance, so there is no look-ahead.
    method:
        Optimizer name; defaults to ``config.optimizer.method``.
    constraints:
        Allocation constraints; defaults to ``config.optimizer.constraints``.
    risk_free:
        Annualized risk-free rate; defaults to ``config.risk_free.annual_rate``.
    seed:
        RNG seed threaded through for reproducibility of any stochastic step.

    Returns
    -------
    BacktestResult
        The strategy track plus every configured benchmark over the same OOS
        dates.
    """
    method = method if method is not None else config.optimizer.method
    constraints = constraints if constraints is not None else config.optimizer.constraints
    risk_free = risk_free if risk_free is not None else config.risk_free.annual_rate

    bt = config.backtest
    lookback_years = bt.lookback_years

    dates = panel.dates
    if panel.n_obs == 0:
        raise ValueError("cannot backtest an empty panel")

    # The OOS period opens once a full lookback window is available, i.e. once the
    # earliest date is at least ``lookback_years`` before the candidate date.
    first_date = dates[0]
    min_oos_date = first_date + np.timedelta64(365 * lookback_years, "D")

    month_starts = _first_trading_day_indices(dates)
    rebalance_rows = month_starts[dates[month_starts] >= min_oos_date]
    if rebalance_rows.shape[0] == 0:
        raise ValueError(
            "panel too short for the requested lookback: no rebalance dates "
            "have a full lookback window available"
        )

    # OOS runs from the first rebalance day to the end of the panel. Within this
    # sub-panel the rebalance rows are re-indexed to start at 0.
    oos_start = int(rebalance_rows[0])
    oos_panel = ReturnsPanel(
        dates[oos_start:].copy(),
        panel.tickers,
        panel.returns[oos_start:].copy(),
    )
    oos_reb_idx = (rebalance_rows - oos_start).astype(np.int64)

    rebalance_dates = dates[rebalance_rows]

    # Compute every rebalance's target weights in parallel. ``Parallel`` returns
    # results in submission order and the estimators/optimizers are pure given
    # their inputs, so the output is identical across runs for a fixed snapshot.
    # ``seed`` is consumed here so determinism is explicit and any future
    # stochastic optimizer inherits a reproducible per-rebalance seed.
    seeds = np.random.SeedSequence(seed).spawn(len(rebalance_dates))
    weight_jobs = (
        delayed(_compute_weights)(
            panel,
            as_of,
            lookback_years=lookback_years,
            method=method,
            mu_method=config.estimators.mu,
            cov_method=config.estimators.cov,
            halflife=config.estimators.ewma_halflife_days,
            constraints=constraints,
            risk_free=risk_free,
            seed=child_seed,
        )
        for as_of, child_seed in zip(rebalance_dates, seeds, strict=True)
    )
    weight_list = Parallel(n_jobs=-1)(weight_jobs)
    target_weights = np.vstack([np.asarray(w, dtype=np.float64) for w in weight_list])

    strategy = simulate_target_weights(
        method,
        oos_panel,
        oos_reb_idx,
        target_weights,
        transaction_cost_bps=bt.transaction_cost_bps,
    )

    benchmark_cost = bt.transaction_cost_bps if bt.benchmarks_bear_costs else 0.0
    benchmarks: dict[str, StrategyTrack] = {
        name: build_benchmark_track(
            name,
            oos_panel,
            oos_reb_idx,
            transaction_cost_bps=benchmark_cost,
        )
        for name in bt.benchmarks
    }

    return BacktestResult(
        tickers=panel.tickers,
        strategy=strategy,
        benchmarks=benchmarks,
        transaction_cost_bps=bt.transaction_cost_bps,
        rebalance=bt.rebalance,
        lookback_years=lookback_years,
        method=method,
    )
