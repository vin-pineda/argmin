"""Shared pytest fixtures.

These fixtures read the **committed Parquet snapshot** — tests never live-fetch
yfinance. Optimizer/analytics tests can depend on ``sample_moments`` /
``toy_moments`` without importing the estimators module, keeping modules
decoupled for parallel development.
"""

from __future__ import annotations

import numpy as np
import pytest

from argmin.config import ArgminConfig, Settings, get_settings, load_default_config
from argmin.data import load_returns_panel
from argmin.types import Moments, ReturnsPanel


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="session")
def config() -> ArgminConfig:
    return load_default_config()


@pytest.fixture(scope="session")
def returns_panel(config: ArgminConfig, settings: Settings) -> ReturnsPanel:
    return load_returns_panel(config, settings)


@pytest.fixture
def rng() -> np.random.Generator:
    return np.random.default_rng(42)


@pytest.fixture(scope="session")
def sample_moments(returns_panel: ReturnsPanel) -> Moments:
    """Realistic annualized Moments from the most recent 3-yr window (sample)."""
    sub = returns_panel.lookback(returns_panel.dates[-1], 3.0)
    R = sub.returns
    mu = R.mean(axis=0) * 252.0
    sigma = np.cov(R, rowvar=False) * 252.0
    return Moments(mu=mu, sigma=sigma, tickers=returns_panel.tickers)


@pytest.fixture
def toy_moments() -> Moments:
    """Deterministic 3-asset PSD toy for closed-form / property checks."""
    tickers = ("A", "B", "C")
    mu = np.array([0.08, 0.10, 0.12])
    corr = np.array([[1.0, 0.2, 0.1], [0.2, 1.0, 0.3], [0.1, 0.3, 1.0]])
    vol = np.array([0.10, 0.15, 0.20])
    sigma = corr * np.outer(vol, vol)
    return Moments(mu=mu, sigma=sigma, tickers=tickers)
