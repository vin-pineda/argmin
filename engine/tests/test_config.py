"""M0 config tests: YAML loads, constraint validation, engine hash stability."""

from __future__ import annotations

import pytest
import yaml
from pydantic import ValidationError

import argmin
from argmin.config import ArgminConfig, load_default_config
from argmin.types import Constraints


def test_default_config_loads() -> None:
    cfg = load_default_config()
    assert len(cfg.universe) == 11
    assert cfg.risk_free.annual_rate >= 0.0
    assert cfg.backtest.transaction_cost_bps > 0.0
    assert cfg.estimators.cov in {"sample", "ledoit_wolf", "ewma"}


def test_constraints_defaults() -> None:
    c = Constraints()
    assert c.long_only and c.fully_invested
    assert c.max_weight is None


def test_constraints_reject_inconsistent() -> None:
    with pytest.raises(ValidationError):
        Constraints(min_weight=0.5, max_weight=0.2)


def test_constraints_reject_out_of_range() -> None:
    with pytest.raises(ValidationError):
        Constraints(max_weight=1.5)


def test_engine_hash_is_stable_and_short() -> None:
    h = argmin.engine_hash()
    assert isinstance(h, str) and len(h) == 12
    assert argmin.engine_hash() == h  # cached / deterministic


def test_config_roundtrip(tmp_path) -> None:  # type: ignore[no-untyped-def]
    cfg = load_default_config()
    p = tmp_path / "cfg.yaml"
    p.write_text(cfg_to_yaml(cfg))
    reloaded = ArgminConfig.load(p)
    assert reloaded.universe == cfg.universe


def cfg_to_yaml(cfg: ArgminConfig) -> str:
    return yaml.safe_dump(cfg.model_dump(mode="json"))
