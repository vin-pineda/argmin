"""M0 data-layer tests: snapshot integrity, alignment, no-look-ahead."""

from __future__ import annotations

import numpy as np

from argmin.config import ArgminConfig, Settings
from argmin.data import load_returns_panel, snapshot_path
from argmin.types import ReturnsPanel


def test_snapshot_exists(settings: Settings) -> None:
    assert snapshot_path(settings).exists(), "committed price snapshot must exist"


def test_panel_shape_and_universe(returns_panel: ReturnsPanel, config: ArgminConfig) -> None:
    assert returns_panel.n_assets == len(config.universe)
    assert tuple(config.universe) == returns_panel.tickers
    assert returns_panel.n_obs > 252 * 10  # >10y of history


def test_no_nans_after_alignment(returns_panel: ReturnsPanel) -> None:
    assert not np.isnan(returns_panel.returns).any()


def test_common_start_alignment(returns_panel: ReturnsPanel) -> None:
    # common-start ⇒ first date is the latest inception (HYG, Apr 2007)
    assert returns_panel.dates[0] >= np.datetime64("2007-01-01")
    assert (returns_panel.dates[1:] > returns_panel.dates[:-1]).all()  # strictly increasing


def test_returns_are_finite_and_reasonable(returns_panel: ReturnsPanel) -> None:
    R = returns_panel.returns
    assert np.isfinite(R).all()
    # daily ETF returns should never exceed ±50% (sanity on adjusted-close basis)
    assert np.abs(R).max() < 0.5


def test_no_look_ahead(returns_panel: ReturnsPanel) -> None:
    """lookback(as_of) must never return an observation dated after as_of."""
    as_of = returns_panel.dates[2000]
    lb = returns_panel.lookback(as_of, years=3.0)
    assert lb.n_obs > 0
    assert (lb.dates <= as_of).all()
    assert lb.n_obs <= round(3.0 * 252) + 1


def test_reproducible_offline(config: ArgminConfig, settings: Settings) -> None:
    """Re-loading the panel twice yields byte-identical arrays (deterministic)."""
    a = load_returns_panel(config, settings)
    b = load_returns_panel(config, settings)
    assert np.array_equal(a.returns, b.returns)
    assert np.array_equal(a.dates, b.dates)
