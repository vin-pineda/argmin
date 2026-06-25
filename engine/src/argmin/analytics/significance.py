r"""Statistical significance of a Sharpe ratio.

Three honesty tools, all operating on a 1-D array of **daily simple returns**:

* :func:`probabilistic_sharpe_ratio` — PSR (Bailey & López de Prado, 2014):
  the probability that the *true* Sharpe ratio exceeds a benchmark, given the
  estimation error of the observed Sharpe and the non-normality (skew & kurtosis)
  of the returns.
* :func:`deflated_sharpe_ratio` — DSR: PSR against a benchmark inflated for the
  number of independent strategy trials, controlling for selection bias.
* :func:`bootstrap_sharpe_ci` — a stationary block bootstrap confidence interval
  for the Sharpe ratio, robust to autocorrelation.

Frequency convention
--------------------
PSR/DSR are computed on the **per-period** (non-annualized) Sharpe ratio, and the
``sr_benchmark`` argument is therefore also interpreted **per period**. This is
the native scale of the Bailey–López de Prado derivation (the √(T−1) standard
error is per observation). The bootstrap, by contrast, reports an **annualized**
Sharpe to match :func:`argmin.analytics.metrics.sharpe_ratio`.
"""

from __future__ import annotations

import math

import numpy as np
import numpy.typing as npt
from scipy import stats

from argmin.types import TRADING_DAYS_PER_YEAR, FloatArray

IntArray = npt.NDArray[np.int64]

# Euler–Mascheroni constant, used in the expected-maximum approximation for DSR.
_EULER_MASCHERONI = 0.5772156649015329


def _as_1d(returns: FloatArray) -> FloatArray:
    """Validate and coerce ``returns`` to a 1-D ``float64`` array of length ≥ 2."""
    arr = np.asarray(returns, dtype=np.float64).ravel()
    if arr.ndim != 1:
        raise ValueError("returns must be 1-D (T,)")
    if arr.size < 2:
        raise ValueError("need at least two observations")
    return arr


def _per_period_sharpe(returns: FloatArray) -> float:
    """Per-period (non-annualized) Sharpe ``mean / std`` with ``ddof=1``."""
    std = returns.std(ddof=1)
    if std <= 1e-18:
        return 0.0
    return float(returns.mean() / std)


def probabilistic_sharpe_ratio(
    returns: FloatArray,
    sr_benchmark: float = 0.0,
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
) -> float:
    r"""Probabilistic Sharpe Ratio (Bailey & López de Prado, 2014).

    Returns ``P[SR_true > sr_benchmark] ∈ [0, 1]`` using the closed form

    .. math::
        \mathrm{PSR} = \Phi\!\left(
            \frac{(\hat{SR} - SR^*)\,\sqrt{T-1}}
                 {\sqrt{1 - \gamma_3\,\hat{SR} + \frac{\gamma_4 - 1}{4}\,\hat{SR}^2}}
        \right)

    where :math:`\hat{SR}` is the observed **per-period** Sharpe, :math:`SR^*` is
    ``sr_benchmark`` (also per period), :math:`\gamma_3` is skewness and
    :math:`\gamma_4` is (non-excess) kurtosis. ``periods_per_year`` is accepted
    for signature symmetry but unused — PSR is frequency-free in this per-period
    formulation.
    """
    arr = _as_1d(returns)
    t = arr.size
    sr = _per_period_sharpe(arr)
    skew = float(stats.skew(arr, bias=True))
    # Non-excess (Pearson) kurtosis: normal → 3.
    kurt = float(stats.kurtosis(arr, fisher=False, bias=True))

    denom_var = 1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr**2
    # The variance estimate can only go non-positive under pathological moments;
    # guard so the statistic stays well defined.
    if denom_var <= 1e-18:
        return 1.0 if sr > sr_benchmark else 0.0
    z = (sr - sr_benchmark) * math.sqrt(t - 1) / math.sqrt(denom_var)
    return float(stats.norm.cdf(z))


def _expected_max_sharpe(n_trials: int, sr_std: float) -> float:
    r"""Expected maximum of ``n_trials`` i.i.d. estimated Sharpe ratios.

    Uses the standard extreme-value approximation for the maximum of ``N``
    standard normals, scaled by the cross-trial Sharpe dispersion ``sr_std``:

    .. math::
        E[\max] \approx \mathrm{sr\_std}\left[
            (1-\gamma)\,\Phi^{-1}\!\left(1 - \tfrac{1}{N}\right)
            + \gamma\,\Phi^{-1}\!\left(1 - \tfrac{1}{N e}\right)
        \right]

    with :math:`\gamma` the Euler–Mascheroni constant.
    """
    if n_trials < 1:
        raise ValueError("n_trials must be at least 1")
    if n_trials == 1:
        return 0.0
    gamma = _EULER_MASCHERONI
    q1 = stats.norm.ppf(1.0 - 1.0 / n_trials)
    q2 = stats.norm.ppf(1.0 - 1.0 / (n_trials * math.e))
    return float(sr_std * ((1.0 - gamma) * q1 + gamma * q2))


def deflated_sharpe_ratio(
    returns: FloatArray,
    n_trials: int,
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
    sr_std: float | None = None,
) -> float:
    r"""Deflated Sharpe Ratio (Bailey & López de Prado, 2014).

    DSR is :func:`probabilistic_sharpe_ratio` evaluated against a benchmark equal
    to the **expected maximum** Sharpe across ``n_trials`` independent trials, so
    a strategy selected as the best of many must clear a higher bar.

    ``sr_std`` is the standard deviation of the per-period Sharpe estimates across
    trials; when ``None`` it defaults to the single-strategy estimation standard
    error :math:`1/\sqrt{T-1}` (the dispersion you would see from sampling noise
    alone). Because the benchmark is non-negative and grows with ``n_trials``,
    ``DSR ≤ PSR(0)`` and is strictly decreasing in ``n_trials``.
    """
    arr = _as_1d(returns)
    if sr_std is None:
        sr_std = 1.0 / math.sqrt(arr.size - 1)
    sr_benchmark = _expected_max_sharpe(n_trials, sr_std)
    return probabilistic_sharpe_ratio(arr, sr_benchmark, periods_per_year)


def _stationary_bootstrap_indices(
    n: int,
    block_size: int,
    rng: np.random.Generator,
) -> IntArray:
    """Sample ``n`` indices via the Politis–Romano stationary bootstrap.

    Each step continues the current block with probability ``1 − 1/block_size``
    (wrapping circularly) or jumps to a fresh uniform start otherwise, giving
    geometrically-distributed block lengths with mean ``block_size``.
    """
    p = 1.0 / block_size
    idx = np.empty(n, dtype=np.int64)
    current = int(rng.integers(0, n))
    for i in range(n):
        current = int(rng.integers(0, n)) if i == 0 or rng.random() < p else (current + 1) % n
        idx[i] = current
    return idx


def bootstrap_sharpe_ci(
    returns: FloatArray,
    n_samples: int = 1000,
    block_size: int = 21,
    ci: float = 0.95,
    seed: int = 42,
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
) -> tuple[float, float, float]:
    r"""Stationary block-bootstrap confidence interval for the **annualized** Sharpe.

    Resamples the return series ``n_samples`` times with the stationary bootstrap
    (mean block length ``block_size``, preserving short-range autocorrelation),
    recomputes the annualized Sharpe on each resample, and returns

    ``(point_estimate, ci_low, ci_high)``

    where ``point_estimate`` is the annualized Sharpe of the original series and
    the bounds are the empirical ``(1 ± ci)/2`` percentiles of the bootstrap
    distribution. Seeded, hence deterministic.
    """
    arr = _as_1d(returns)
    if not 0.0 < ci < 1.0:
        raise ValueError("ci must be in (0, 1)")
    if block_size < 1:
        raise ValueError("block_size must be at least 1")
    if n_samples < 1:
        raise ValueError("n_samples must be at least 1")

    sqrt_p = math.sqrt(periods_per_year)

    def ann_sharpe(sample: FloatArray) -> float:
        std = sample.std(ddof=1)
        if std <= 1e-18:
            return 0.0
        return float(sample.mean() / std * sqrt_p)

    point = ann_sharpe(arr)
    rng = np.random.default_rng(seed)
    stats_arr = np.empty(n_samples, dtype=np.float64)
    n = arr.size
    for s in range(n_samples):
        idx = _stationary_bootstrap_indices(n, block_size, rng)
        stats_arr[s] = ann_sharpe(arr[idx])

    lower_q = (1.0 - ci) / 2.0
    upper_q = 1.0 - lower_q
    ci_low = float(np.quantile(stats_arr, lower_q))
    ci_high = float(np.quantile(stats_arr, upper_q))
    return point, ci_low, ci_high
