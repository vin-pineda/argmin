"""Pure request → engine → response functions (no FastAPI imports).

This module is the single place that maps the wire models in
:mod:`argmin.api.models` onto the engine (estimators → optimizers → frontier →
backtest → analytics). Keeping it framework-free means the CLI can reuse it to
emit the precomputed default-scenario JSON whose shape EXACTLY matches the live
API responses, and it can be unit-tested without spinning up an HTTP app.

Conventions
-----------
* ``as_of`` windows the panel to ``date <= as_of``; optimize/frontier then read
  the most recent ``lookback_years`` slice of that window (no look-ahead).
* All ``datetime64`` values are converted to ISO ``YYYY-MM-DD`` strings.
* Every response carries a :class:`~argmin.api.models.Provenance` envelope.
"""

from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import numpy.typing as npt

from argmin import engine_hash
from argmin.analytics import (
    bootstrap_sharpe_ci,
    compute_tearsheet,
    deflated_sharpe_ratio,
    probabilistic_sharpe_ratio,
    rolling_sharpe,
)
from argmin.api.models import (
    BacktestRequest,
    BacktestResponse,
    FrontierPointModel,
    FrontierPortfolio,
    FrontierResponse,
    OptimizeRequest,
    OptimizeResponse,
    Provenance,
    RandomCloud,
    StrategyResult,
    TearsheetModel,
)
from argmin.backtest import BacktestResult, run_backtest
from argmin.backtest.types import StrategyTrack
from argmin.config import ArgminConfig, Settings
from argmin.estimators import get_cov_estimator, get_return_estimator
from argmin.optimizers import efficient_frontier, get_optimizer
from argmin.types import (
    FloatArray,
    Moments,
    OptimizeResult,
    ReturnsPanel,
)

# Default frontier resolution for the API (kept modest so live responses stay
# snappy; the random cloud doubles as the visx scatter background).
_FRONTIER_POINTS = 40
_FRONTIER_RANDOM = 800
_ROLLING_SHARPE_WINDOW = 252


# ──────────────────────────────────────────────────────────────────────────────
# Small conversion helpers
# ──────────────────────────────────────────────────────────────────────────────
def _iso(value: np.datetime64) -> str:
    """``datetime64`` → ISO ``YYYY-MM-DD`` (UTC date)."""
    return np.datetime_as_string(value, unit="D")


def _iso_list(values: npt.NDArray[np.datetime64] | FloatArray) -> list[str]:
    # ``StrategyTrack`` stores datetime64 dates inside ``FloatArray`` fields (see
    # the backtest types contract), so view them as datetime64 before formatting.
    dates = np.asarray(values).astype("datetime64[ns]")
    return [_iso(v) for v in dates]


def _as_of64(as_of: str | None) -> np.datetime64 | None:
    return np.datetime64(as_of) if as_of else None


def _weights_dict(tickers: tuple[str, ...], weights: FloatArray) -> dict[str, float]:
    return {t: float(w) for t, w in zip(tickers, weights, strict=True)}


def _provenance(
    panel: ReturnsPanel,
    *,
    risk_free: float,
    as_of: str | None,
) -> Provenance:
    """Build the provenance envelope from the (already-windowed) panel."""
    data_start = _iso(panel.dates[0]) if panel.n_obs else None
    data_end = _iso(panel.dates[-1]) if panel.n_obs else None
    return Provenance(
        engine_hash=engine_hash(),
        risk_free=risk_free,
        data_start=data_start,
        data_end=data_end,
        as_of=as_of,
        oos_only=True,
        generated_utc=datetime.now(UTC).isoformat(),
    )


def _estimation_window(
    panel: ReturnsPanel,
    config: ArgminConfig,
    as_of: str | None,
) -> ReturnsPanel:
    """Most-recent ``lookback_years`` window ending at ``as_of`` (default: panel end).

    This is the point-in-time slice optimize/frontier estimate moments from. It
    never reads an observation dated after ``as_of``.
    """
    as_of64 = _as_of64(as_of)
    end = as_of64 if as_of64 is not None else panel.dates[-1]
    return panel.lookback(end, float(config.backtest.lookback_years))


def _moments_for(
    window: ReturnsPanel,
    config: ArgminConfig,
    risk_free: float,
    mu_method: str | None,
    cov_method: str | None,
) -> Moments:
    """Estimate annualized μ, Σ over ``window`` using the requested/default methods."""
    halflife = config.estimators.ewma_halflife_days
    mu_estimator = get_return_estimator(mu_method or config.estimators.mu, halflife)
    cov_estimator = get_cov_estimator(cov_method or config.estimators.cov, halflife)
    mu = mu_estimator.estimate(window.returns, risk_free)
    sigma = cov_estimator.estimate(window.returns)
    return Moments(mu=mu, sigma=sigma, tickers=window.tickers)


def _portfolio_model(result: OptimizeResult) -> FrontierPortfolio:
    return FrontierPortfolio(
        method=result.method,
        tickers=list(result.tickers),
        weights=_weights_dict(result.tickers, result.weights),
        exp_return=result.exp_return,
        exp_vol=result.exp_vol,
        sharpe=result.sharpe,
        risk_contrib=_weights_dict(result.tickers, result.risk_contrib),
    )


# ──────────────────────────────────────────────────────────────────────────────
# /optimize
# ──────────────────────────────────────────────────────────────────────────────
def optimize(
    panel: ReturnsPanel,
    config: ArgminConfig,
    settings: Settings,
    req: OptimizeRequest,
) -> OptimizeResponse:
    """Single-shot allocation: estimate moments, run one optimizer, derive stats."""
    _ = settings  # part of the uniform service signature; not needed here
    sub = panel.select(req.universe)
    risk_free = req.risk_free if req.risk_free is not None else config.risk_free.annual_rate
    window = _estimation_window(sub, config, req.as_of)
    moments = _moments_for(window, config, risk_free, req.mu_method, req.cov_method)

    optimizer = get_optimizer(req.method)
    result = optimizer.optimize(moments, req.constraints, risk_free)

    return OptimizeResponse(
        method=result.method,
        tickers=list(result.tickers),
        weights=_weights_dict(result.tickers, result.weights),
        exp_return=result.exp_return,
        exp_vol=result.exp_vol,
        sharpe=result.sharpe,
        risk_contrib=_weights_dict(result.tickers, result.risk_contrib),
        as_of=req.as_of,
        provenance=_provenance(window, risk_free=risk_free, as_of=req.as_of),
    )


# ──────────────────────────────────────────────────────────────────────────────
# /frontier
# ──────────────────────────────────────────────────────────────────────────────
def frontier(
    panel: ReturnsPanel,
    config: ArgminConfig,
    settings: Settings,
    universe: list[str],
    as_of: str | None = None,
) -> FrontierResponse:
    """Trace the efficient frontier + tangency/min-var portfolios + random cloud."""
    _ = settings
    sub = panel.select(universe)
    risk_free = config.risk_free.annual_rate
    window = _estimation_window(sub, config, as_of)
    moments = _moments_for(window, config, risk_free, config.estimators.mu, config.estimators.cov)

    fr = efficient_frontier(
        moments,
        config.optimizer.constraints,
        risk_free,
        n_points=_FRONTIER_POINTS,
        n_random=_FRONTIER_RANDOM,
        seed=config.random_seed,
    )

    return FrontierResponse(
        tickers=list(fr.tickers),
        frontier_points=[
            FrontierPointModel(ret=p.ret, vol=p.vol, sharpe=p.sharpe) for p in fr.points
        ],
        tangency=_portfolio_model(fr.tangency),
        min_var=_portfolio_model(fr.min_var),
        random_cloud=RandomCloud(
            vol=[float(v) for v in fr.random_cloud_vol],
            ret=[float(r) for r in fr.random_cloud_ret],
        ),
        provenance=_provenance(window, risk_free=risk_free, as_of=as_of),
    )


# ──────────────────────────────────────────────────────────────────────────────
# /backtest
# ──────────────────────────────────────────────────────────────────────────────
def _tearsheet_model(
    track: StrategyTrack,
    config: ArgminConfig,
    risk_free: float,
) -> TearsheetModel:
    """Compute the full tearsheet (+ PSR/DSR + bootstrap CI) for one OOS track."""
    returns = track.daily_returns
    avg_turnover = float(np.mean(track.turnover)) if track.turnover.size else None
    sheet = compute_tearsheet(
        returns,
        risk_free=risk_free,
        periods_per_year=config.data.trading_days_per_year,
        avg_turnover=avg_turnover,
    )

    sig = config.significance
    psr = probabilistic_sharpe_ratio(returns)
    dsr = deflated_sharpe_ratio(returns, sig.dsr_trials)
    _, ci_low, ci_high = bootstrap_sharpe_ci(
        returns,
        n_samples=sig.bootstrap_samples,
        block_size=sig.bootstrap_block_size,
        seed=config.random_seed,
        periods_per_year=config.data.trading_days_per_year,
    )

    return TearsheetModel(
        total_return=sheet.total_return,
        cagr=sheet.cagr,
        ann_return=sheet.ann_return,
        ann_vol=sheet.ann_vol,
        sharpe=sheet.sharpe,
        sortino=sheet.sortino,
        max_drawdown=sheet.max_drawdown,
        calmar=sheet.calmar,
        var_95=sheet.var_95,
        cvar_95=sheet.cvar_95,
        hit_rate=sheet.hit_rate,
        best_day=sheet.best_day,
        worst_day=sheet.worst_day,
        avg_turnover=sheet.avg_turnover,
        psr=psr,
        dsr=dsr,
        sharpe_ci_low=ci_low,
        sharpe_ci_high=ci_high,
    )


def _strategy_result(
    track: StrategyTrack,
    config: ArgminConfig,
    risk_free: float,
) -> StrategyResult:
    rolling = rolling_sharpe(
        track.daily_returns,
        window=_ROLLING_SHARPE_WINDOW,
        periods_per_year=config.data.trading_days_per_year,
    )
    return StrategyResult(
        name=track.name,
        metrics=_tearsheet_model(track, config, risk_free),
        equity_curve=[float(x) for x in track.equity],
        drawdown=[float(x) for x in track.drawdown],
        rolling_sharpe=[float(x) for x in rolling],
        weights_over_time=[[float(w) for w in row] for row in track.weights_over_time],
        rebalance_dates=_iso_list(track.rebalance_dates),
        turnover=[float(x) for x in track.turnover],
    )


def _significance_summary(
    result: BacktestResult,
    config: ArgminConfig,
) -> dict[str, object]:
    """Top-level significance block: per-strategy PSR/DSR/CI + the DSR trial count."""
    sig = config.significance
    per_strategy: dict[str, dict[str, float]] = {}
    tracks: dict[str, StrategyTrack] = {result.strategy.name: result.strategy, **result.benchmarks}
    for name, track in tracks.items():
        returns = track.daily_returns
        point, lo, hi = bootstrap_sharpe_ci(
            returns,
            n_samples=sig.bootstrap_samples,
            block_size=sig.bootstrap_block_size,
            seed=config.random_seed,
            periods_per_year=config.data.trading_days_per_year,
        )
        per_strategy[name] = {
            "psr": probabilistic_sharpe_ratio(returns),
            "dsr": deflated_sharpe_ratio(returns, sig.dsr_trials),
            "sharpe": point,
            "sharpe_ci_low": lo,
            "sharpe_ci_high": hi,
        }
    return {
        "dsr_trials": sig.dsr_trials,
        "bootstrap_samples": sig.bootstrap_samples,
        "bootstrap_block_size": sig.bootstrap_block_size,
        "strategies": per_strategy,
    }


def backtest(
    panel: ReturnsPanel,
    config: ArgminConfig,
    settings: Settings,
    req: BacktestRequest,
) -> BacktestResponse:
    """Walk-forward backtest of ``req.method`` plus every benchmark over OOS dates."""
    _ = settings
    sub = panel.select(req.universe)
    start = np.datetime64(req.start) if req.start else None
    end = np.datetime64(req.end) if req.end else None
    if start is not None or end is not None:
        sub = sub.window(start=start, end=end)

    risk_free = config.risk_free.annual_rate

    # Apply per-request overrides on top of the scenario config without mutating
    # the shared default (frozen-ish) config object.
    bt_overrides = config.backtest.model_dump()
    if req.rebalance is not None:
        bt_overrides["rebalance"] = req.rebalance
    if req.lookback_years is not None:
        bt_overrides["lookback_years"] = req.lookback_years
    if req.transaction_cost_bps is not None:
        bt_overrides["transaction_cost_bps"] = req.transaction_cost_bps
    if req.benchmarks is not None:
        bt_overrides["benchmarks"] = req.benchmarks
    run_config = config.model_copy(
        update={"backtest": config.backtest.model_copy(update=bt_overrides)}
    )

    result = run_backtest(
        run_config,
        sub,
        method=req.method,
        constraints=req.constraints,
        risk_free=risk_free,
        seed=run_config.random_seed,
    )

    # Strategy first, then benchmarks — all in one ``strategies`` map.
    tracks: dict[str, StrategyTrack] = {
        result.strategy.name: result.strategy,
        **result.benchmarks,
    }
    strategies = {
        name: _strategy_result(track, run_config, risk_free) for name, track in tracks.items()
    }

    dates = _iso_list(result.strategy.dates)

    return BacktestResponse(
        tickers=list(result.tickers),
        dates=dates,
        strategies=strategies,
        significance=_significance_summary(result, run_config),
        provenance=_provenance(sub, risk_free=risk_free, as_of=req.end),
    )


__all__ = [
    "backtest",
    "frontier",
    "optimize",
]
