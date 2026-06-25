"""Pydantic v2 request/response models for the Argmin HTTP API.

These models are the **wire contract** between the engine and the web client.
They are deliberately JSON-native (plain ``float``/``str``/``list``/``dict``; no
NumPy types, no ``datetime64``) so the same shapes are emitted by
:func:`argmin.cli` for the precomputed default scenario and by the live API —
the web consumes one schema either way.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from argmin.types import Constraints

# ──────────────────────────────────────────────────────────────────────────────
# Shared / provenance
# ──────────────────────────────────────────────────────────────────────────────


class Provenance(BaseModel):
    """Where a result came from — the honesty/reproducibility envelope.

    Carried on every successful response so the web can show *exactly* which
    data window, risk-free rate, and engine revision produced the numbers, and
    assert that the result is out-of-sample.
    """

    model_config = ConfigDict(frozen=True)

    engine_hash: str
    risk_free: float
    data_start: str | None
    data_end: str | None
    as_of: str | None = None
    oos_only: bool = True
    generated_utc: str


class ErrorResponse(BaseModel):
    """Typed error contract. ``error`` is a stable machine code; ``detail`` is human-readable."""

    error: str
    detail: str


# ──────────────────────────────────────────────────────────────────────────────
# /optimize
# ──────────────────────────────────────────────────────────────────────────────


class OptimizeRequest(BaseModel):
    universe: list[str]
    method: str
    constraints: Constraints = Field(default_factory=Constraints)
    as_of: str | None = None
    mu_method: str | None = None
    cov_method: str | None = None
    risk_free: float | None = None


class OptimizeResponse(BaseModel):
    method: str
    tickers: list[str]
    weights: dict[str, float]
    exp_return: float
    exp_vol: float
    sharpe: float
    risk_contrib: dict[str, float]
    as_of: str | None = None
    provenance: Provenance


# ──────────────────────────────────────────────────────────────────────────────
# /backtest
# ──────────────────────────────────────────────────────────────────────────────


class TearsheetModel(BaseModel):
    """JSON-native mirror of :class:`argmin.analytics.metrics.Tearsheet`, plus
    PSR/DSR and a bootstrap Sharpe CI so the web has every headline metric in one
    object."""

    total_return: float
    cagr: float
    ann_return: float
    ann_vol: float
    sharpe: float
    sortino: float
    max_drawdown: float
    calmar: float
    var_95: float
    cvar_95: float
    hit_rate: float
    best_day: float
    worst_day: float
    avg_turnover: float | None = None
    # Significance / honesty tools (filled per strategy track).
    psr: float | None = None
    dsr: float | None = None
    sharpe_ci_low: float | None = None
    sharpe_ci_high: float | None = None


class StrategyResult(BaseModel):
    name: str
    metrics: TearsheetModel
    equity_curve: list[float]
    drawdown: list[float]
    rolling_sharpe: list[float]
    weights_over_time: list[list[float]]
    rebalance_dates: list[str]
    turnover: list[float]


class BacktestRequest(BaseModel):
    universe: list[str]
    method: str
    constraints: Constraints = Field(default_factory=Constraints)
    start: str | None = None
    end: str | None = None
    rebalance: str | None = None
    lookback_years: int | None = None
    transaction_cost_bps: float | None = None
    benchmarks: list[str] | None = None


class BacktestResponse(BaseModel):
    tickers: list[str]
    dates: list[str]
    strategies: dict[str, StrategyResult]
    significance: dict[str, object]
    provenance: Provenance


# ──────────────────────────────────────────────────────────────────────────────
# /frontier
# ──────────────────────────────────────────────────────────────────────────────


class FrontierPointModel(BaseModel):
    ret: float
    vol: float
    sharpe: float


class FrontierPortfolio(BaseModel):
    """A named portfolio on/under the frontier (tangency or min-variance)."""

    method: str
    tickers: list[str]
    weights: dict[str, float]
    exp_return: float
    exp_vol: float
    sharpe: float
    risk_contrib: dict[str, float]


class RandomCloud(BaseModel):
    vol: list[float]
    ret: list[float]


class FrontierResponse(BaseModel):
    tickers: list[str]
    frontier_points: list[FrontierPointModel]
    tangency: FrontierPortfolio
    min_var: FrontierPortfolio
    random_cloud: RandomCloud
    provenance: Provenance


# ──────────────────────────────────────────────────────────────────────────────
# /healthz
# ──────────────────────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
    version: str
    engine_hash: str
    universe: list[str]


class DefaultScenario(BaseModel):
    """The precomputed default-scenario bundle the web loads for instant first paint.

    Reuses the exact API response models so the static JSON and the live
    endpoints are byte-for-byte the same shape.
    """

    optimize: OptimizeResponse
    frontier: FrontierResponse
    backtest: BacktestResponse
