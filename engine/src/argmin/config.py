"""Typed configuration: the scenario config (``default.yaml``) and env Settings."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from argmin.types import Constraints

# ──────────────────────────────────────────────────────────────────────────────
# Scenario config (config/default.yaml)
# ──────────────────────────────────────────────────────────────────────────────
MuMethod = Literal["sample", "ewma", "capm"]
CovMethod = Literal["sample", "ledoit_wolf", "ewma"]


class DataConfig(BaseModel):
    start: str
    end: str
    price_field: str = "adj_close"
    alignment: Literal["common_start"] = "common_start"
    trading_days_per_year: int = 252


class RiskFreeConfig(BaseModel):
    mode: Literal["constant", "series"] = "constant"
    annual_rate: float = 0.02


class EstimatorsConfig(BaseModel):
    mu: MuMethod = "sample"
    cov: CovMethod = "ledoit_wolf"
    ewma_halflife_days: int = 63


class OptimizerConfig(BaseModel):
    method: str = "max_sharpe"
    constraints: Constraints = Field(default_factory=Constraints)


class BLView(BaseModel):
    """A single Black-Litterman view (absolute or relative).

    ``picks`` maps tickers to portfolio weights in the view; ``value`` is the
    view's expected (annualized) return; ``confidence`` in (0, 1] scales Ω.
    """

    picks: dict[str, float]
    value: float
    confidence: float = 0.5


class BlackLittermanConfig(BaseModel):
    delta: float = 2.5
    tau: float = 0.05
    views: list[BLView] = Field(default_factory=list)


class BacktestConfig(BaseModel):
    rebalance: Literal["monthly", "quarterly"] = "monthly"
    lookback_years: int = 3
    transaction_cost_bps: float = 10.0
    benchmarks_bear_costs: bool = True
    benchmarks: list[str] = Field(default_factory=lambda: ["equal_weight", "sixty_forty", "spy"])
    max_years: int = 20
    max_assets: int = 15
    max_models_per_request: int = 7


class SignificanceConfig(BaseModel):
    bootstrap_samples: int = 1000
    bootstrap_block_size: int = 21
    dsr_trials: int = 7


class ArgminConfig(BaseModel):
    """The full scenario configuration loaded from YAML."""

    universe: list[str]
    data: DataConfig
    risk_free: RiskFreeConfig = Field(default_factory=RiskFreeConfig)
    estimators: EstimatorsConfig = Field(default_factory=EstimatorsConfig)
    optimizer: OptimizerConfig = Field(default_factory=OptimizerConfig)
    black_litterman: BlackLittermanConfig = Field(default_factory=BlackLittermanConfig)
    backtest: BacktestConfig = Field(default_factory=BacktestConfig)
    significance: SignificanceConfig = Field(default_factory=SignificanceConfig)
    random_seed: int = 42

    @classmethod
    def load(cls, path: str | Path) -> ArgminConfig:
        raw = yaml.safe_load(Path(path).read_text())
        return cls.model_validate(raw)


def engine_root() -> Path:
    """The ``engine/`` directory (contains ``pyproject.toml`` and ``config/``)."""
    return Path(__file__).resolve().parents[2]


def repo_root() -> Path:
    """The monorepo root (parent of ``engine/``)."""
    return engine_root().parent


def default_config_path() -> Path:
    """Path to the committed ``config/default.yaml`` relative to the package."""
    return engine_root() / "config" / "default.yaml"


def load_default_config() -> ArgminConfig:
    return ArgminConfig.load(default_config_path())


# ──────────────────────────────────────────────────────────────────────────────
# Runtime settings (environment variables, ARGMIN_ prefix)
# ──────────────────────────────────────────────────────────────────────────────
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ARGMIN_", env_file=".env", extra="ignore", case_sensitive=False
    )

    env: Literal["development", "production"] = "development"
    log_level: str = "INFO"
    log_json: bool = False

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_allow_origins: str = "http://localhost:3000"

    data_source: Literal["yfinance", "polygon", "csv"] = "yfinance"
    data_dir: Path = Path("./engine/data")
    duckdb_path: Path = Path("./engine/data/argmin.duckdb")

    random_seed: int = 42
    cache_ttl_seconds: int = 86400
    rate_limit_per_minute: int = 30

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]

    def _resolve(self, p: Path) -> Path:
        """Anchor relative paths to the repo root so they're CWD-independent."""
        return p if p.is_absolute() else (repo_root() / p).resolve()

    @property
    def resolved_data_dir(self) -> Path:
        return self._resolve(self.data_dir)

    @property
    def resolved_duckdb_path(self) -> Path:
        return self._resolve(self.duckdb_path)

    @property
    def cache_dir(self) -> Path:
        return self.resolved_data_dir / "cache"


def get_settings() -> Settings:
    return Settings()
