"""Performance metrics and a portfolio :class:`Tearsheet`.

Every function here consumes a 1-D array of **daily simple returns** ``(T,)``
and annualizes with ``periods_per_year`` (default 252). The conventions are
chosen to line up with the ``quantstats`` test oracle (``rf=0``, ``periods=252``):

* ``ann_return`` / ``ann_vol`` / ``sharpe`` / ``sortino`` are **arithmetic**
  (mean and sample std with ``ddof=1``), annualized by ``× periods`` and
  ``× √periods`` respectively.
* ``cagr`` is **geometric** (compound growth of \\$1), as is ``total_return``.
* ``calmar = cagr / |max_drawdown|`` — matching ``quantstats.stats.calmar``.

Sortino uses the Red Rock downside deviation: ``√(Σ min(r,0)² / T)`` — the sum
of squared negative returns divided by the **total** number of observations
(not just the count of down days), the same convention ``quantstats`` uses.

Sign conventions: ``max_drawdown ≤ 0`` (an underwater fraction) and ``var_95`` /
``cvar_95`` are reported as **negative** returns (a 5% loss is ``-0.05``).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from argmin.types import TRADING_DAYS_PER_YEAR, FloatArray


@dataclass(frozen=True)
class Tearsheet:
    """A bundle of headline performance statistics for one return stream.

    All fields are plain ``float`` (or ``None`` for ``avg_turnover`` when the
    backtest did not supply turnover). See the module docstring for the exact
    definition and sign convention of each field.
    """

    total_return: float
    cagr: float
    ann_return: float  # annualized arithmetic mean × periods
    ann_vol: float  # sample std × √periods
    sharpe: float
    sortino: float
    max_drawdown: float  # ≤ 0 (underwater fraction at the worst point)
    calmar: float
    var_95: float  # historical 95% VaR, reported as a negative return
    cvar_95: float  # expected shortfall beyond VaR₉₅, negative return
    hit_rate: float  # fraction of strictly-positive days
    best_day: float
    worst_day: float
    avg_turnover: float | None  # filled from the backtest when available


def _as_1d(returns: FloatArray) -> FloatArray:
    """Validate and coerce ``returns`` to a 1-D ``float64`` array of length ≥ 1."""
    arr = np.asarray(returns, dtype=np.float64).ravel()
    if arr.ndim != 1:
        raise ValueError("returns must be 1-D (T,)")
    if arr.size < 1:
        raise ValueError("need at least one observation")
    return arr


def equity_curve(returns: FloatArray) -> FloatArray:
    """Compounded growth of \\$1: ``cumprod(1 + r)`` (starts just after \\$1)."""
    arr = _as_1d(returns)
    return np.asarray(np.cumprod(1.0 + arr), dtype=np.float64)


def drawdown_series(returns: FloatArray) -> FloatArray:
    """Underwater curve ``equity / running_max − 1`` (≤ 0 everywhere).

    The running peak is seeded at the \\$1 starting capital, so a series that
    only ever loses money still reports the correct (negative) drawdown.
    """
    arr = _as_1d(returns)
    equity = np.cumprod(1.0 + arr)
    # Seed the running peak at the \\$1 starting capital so an immediate loss
    # registers as a drawdown rather than 0.
    peak = np.maximum.accumulate(np.maximum(equity, 1.0))
    dd = equity / peak - 1.0
    return np.asarray(np.minimum(dd, 0.0), dtype=np.float64)


def total_return(returns: FloatArray) -> float:
    """Total compounded return over the whole window (``∏(1 + r) − 1``)."""
    arr = _as_1d(returns)
    return float(np.prod(1.0 + arr) - 1.0)


def cagr(returns: FloatArray, periods_per_year: int = TRADING_DAYS_PER_YEAR) -> float:
    """Compound annual growth rate from the geometric total return.

    ``years = T / periods_per_year``; ``CAGR = (1 + total_return)^(1/years) − 1``.
    Uses ``|1 + total|`` under the root to mirror ``quantstats`` and avoid
    complex results from a wipe-out (total ≤ −1).
    """
    arr = _as_1d(returns)
    years = arr.size / periods_per_year
    if years <= 0:
        return 0.0
    total = float(np.prod(1.0 + arr))
    return float(np.abs(total) ** (1.0 / years) - 1.0)


def ann_return(returns: FloatArray, periods_per_year: int = TRADING_DAYS_PER_YEAR) -> float:
    """Annualized arithmetic mean return (``mean(r) × periods``)."""
    arr = _as_1d(returns)
    return float(arr.mean() * periods_per_year)


def ann_vol(returns: FloatArray, periods_per_year: int = TRADING_DAYS_PER_YEAR) -> float:
    """Annualized volatility (sample std, ``ddof=1``, ``× √periods``).

    A single observation has no dispersion, so volatility is defined as 0.
    """
    arr = _as_1d(returns)
    if arr.size < 2:
        return 0.0
    return float(arr.std(ddof=1) * np.sqrt(periods_per_year))


def sharpe_ratio(
    returns: FloatArray,
    risk_free: float = 0.0,
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
) -> float:
    """Annualized Sharpe ratio of excess returns.

    ``rf_daily = risk_free / periods``; ``SR = mean(r − rf_daily) / std × √periods``
    with sample std (``ddof=1``). Returns 0 when the series is constant.
    """
    arr = _as_1d(returns)
    if arr.size < 2:
        return 0.0
    rf_daily = risk_free / periods_per_year
    excess = arr - rf_daily
    std = excess.std(ddof=1)
    if std <= 1e-18:
        return 0.0
    return float(excess.mean() / std * np.sqrt(periods_per_year))


def sortino_ratio(
    returns: FloatArray,
    risk_free: float = 0.0,
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
) -> float:
    """Annualized Sortino ratio using Red Rock downside deviation.

    ``downside = √(Σ min(excess, 0)² / T)`` (squared shortfalls averaged over the
    **whole** sample), then ``Sortino = mean(excess) / downside × √periods``.
    """
    arr = _as_1d(returns)
    if arr.size < 1:
        return 0.0
    rf_daily = risk_free / periods_per_year
    excess = arr - rf_daily
    negative = np.minimum(excess, 0.0)
    downside = np.sqrt(np.sum(negative**2) / excess.size)
    if downside <= 1e-18:
        return 0.0
    return float(excess.mean() / downside * np.sqrt(periods_per_year))


def max_drawdown(returns: FloatArray) -> float:
    """Worst peak-to-trough drawdown over the window (``≤ 0``)."""
    dd = drawdown_series(returns)
    return float(dd.min()) if dd.size else 0.0


def calmar_ratio(returns: FloatArray, periods_per_year: int = TRADING_DAYS_PER_YEAR) -> float:
    """``CAGR / |max_drawdown|`` (0 when there is no drawdown)."""
    mdd = max_drawdown(returns)
    if abs(mdd) <= 1e-18:
        return 0.0
    return float(cagr(returns, periods_per_year) / abs(mdd))


def value_at_risk(returns: FloatArray, alpha: float = 0.05) -> float:
    """Historical VaR at confidence ``1 − alpha`` (default 95%).

    The ``alpha`` empirical quantile of the return distribution, reported as a
    **negative** return (a typical loss is negative).
    """
    arr = _as_1d(returns)
    return float(np.quantile(arr, alpha))


def conditional_value_at_risk(returns: FloatArray, alpha: float = 0.05) -> float:
    """Historical CVaR / expected shortfall: mean of returns at or below VaR_α.

    Reported as a **negative** return. Falls back to the single worst return
    when no observation lies strictly below the quantile (tiny samples).
    """
    arr = _as_1d(returns)
    var = np.quantile(arr, alpha)
    tail = arr[arr <= var]
    if tail.size == 0:
        return float(arr.min())
    return float(tail.mean())


def hit_rate(returns: FloatArray) -> float:
    """Fraction of strictly-positive days."""
    arr = _as_1d(returns)
    return float(np.mean(arr > 0.0))


def rolling_sharpe(
    returns: FloatArray,
    window: int = TRADING_DAYS_PER_YEAR,
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
) -> FloatArray:
    """Annualized Sharpe computed over a trailing ``window`` (rf = 0).

    Returns an array of length ``T − window + 1`` (one Sharpe per full window).
    When the series is shorter than ``window`` the result is empty. Windows with
    zero dispersion yield a Sharpe of 0.
    """
    arr = _as_1d(returns)
    if window < 2:
        raise ValueError("window must be at least 2")
    n = arr.size - window + 1
    if n <= 0:
        return np.zeros(0, dtype=np.float64)
    out = np.empty(n, dtype=np.float64)
    sqrt_p = np.sqrt(periods_per_year)
    for i in range(n):
        win = arr[i : i + window]
        std = win.std(ddof=1)
        out[i] = (win.mean() / std * sqrt_p) if std > 1e-18 else 0.0
    return out


def compute_tearsheet(
    returns: FloatArray,
    risk_free: float = 0.0,
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
    avg_turnover: float | None = None,
) -> Tearsheet:
    """Assemble a full :class:`Tearsheet` from a daily-return stream.

    ``risk_free`` is an **annual** rate (converted to per-period internally for
    the Sharpe/Sortino excess returns). ``avg_turnover`` is passed through from
    the backtest when available, otherwise ``None``.
    """
    arr = _as_1d(returns)
    return Tearsheet(
        total_return=total_return(arr),
        cagr=cagr(arr, periods_per_year),
        ann_return=ann_return(arr, periods_per_year),
        ann_vol=ann_vol(arr, periods_per_year),
        sharpe=sharpe_ratio(arr, risk_free, periods_per_year),
        sortino=sortino_ratio(arr, risk_free, periods_per_year),
        max_drawdown=max_drawdown(arr),
        calmar=calmar_ratio(arr, periods_per_year),
        var_95=value_at_risk(arr, 0.05),
        cvar_95=conditional_value_at_risk(arr, 0.05),
        hit_rate=hit_rate(arr),
        best_day=float(arr.max()),
        worst_day=float(arr.min()),
        avg_turnover=avg_turnover,
    )
