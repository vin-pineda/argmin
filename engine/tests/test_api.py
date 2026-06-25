"""API tests for the Argmin FastAPI service.

These drive the app through :class:`fastapi.testclient.TestClient` (so the
lifespan loads config/settings/panel from the **committed snapshot** — no
network). Universes/spans are kept small so the suite stays fast.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from argmin import engine_hash
from argmin.api import app

# A small, fast subset of the whitelist (3 assets, includes SPY/AGG for benchmarks).
SMALL_UNIVERSE = ["SPY", "AGG", "GLD"]


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    # ``with`` triggers the lifespan (loads the returns panel once).
    with TestClient(app) as c:
        yield c


def test_healthz(client: TestClient) -> None:
    resp = client.get("/healthz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["version"]
    assert body["engine_hash"] == engine_hash()
    assert "SPY" in body["universe"]


def test_optimize_happy_path(client: TestClient) -> None:
    resp = client.post(
        "/optimize",
        json={"universe": SMALL_UNIVERSE, "method": "max_sharpe"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["method"] == "max_sharpe"
    assert set(body["tickers"]) == set(SMALL_UNIVERSE)
    # Weights sum to ~1 (fully invested) and every field is present.
    assert sum(body["weights"].values()) == pytest.approx(1.0, abs=1e-6)
    assert set(body["risk_contrib"]) == set(SMALL_UNIVERSE)
    for field in ("exp_return", "exp_vol", "sharpe", "provenance"):
        assert field in body
    assert body["provenance"]["engine_hash"] == engine_hash()
    assert body["provenance"]["oos_only"] is True


def test_optimize_off_whitelist_is_422(client: TestClient) -> None:
    resp = client.post(
        "/optimize",
        json={"universe": ["SPY", "NOTREAL"], "method": "max_sharpe"},
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "invalid_universe"


def test_frontier(client: TestClient) -> None:
    resp = client.get("/frontier", params={"universe": "SPY,AGG,GLD"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["frontier_points"]) > 0
    for key in ("ret", "vol", "sharpe"):
        assert key in body["frontier_points"][0]
    assert body["tangency"]["method"]
    assert body["min_var"]["method"]
    assert len(body["random_cloud"]["vol"]) == len(body["random_cloud"]["ret"]) > 0


def test_backtest_with_benchmarks_and_significance(client: TestClient) -> None:
    resp = client.post(
        "/backtest",
        json={
            "universe": SMALL_UNIVERSE,
            "method": "max_sharpe",
            "start": "2015-01-01",
            "end": "2020-12-31",
            "lookback_years": 2,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    strategies = body["strategies"]
    # The strategy itself plus all three benchmarks.
    assert "max_sharpe" in strategies
    for bench in ("equal_weight", "sixty_forty", "spy"):
        assert bench in strategies
    # Each strategy carries a full tearsheet + curves.
    strat = strategies["max_sharpe"]
    assert strat["metrics"]["sharpe"] is not None
    assert strat["metrics"]["psr"] is not None
    assert len(strat["equity_curve"]) == len(body["dates"]) > 0
    # Top-level significance summary.
    assert body["significance"]["dsr_trials"] >= 1
    assert "max_sharpe" in body["significance"]["strategies"]


def test_backtest_oversized_span_is_422(client: TestClient) -> None:
    resp = client.post(
        "/backtest",
        json={
            "universe": ["SPY", "AGG"],
            "method": "max_sharpe",
            "start": "1990-01-01",
            "end": "2024-12-31",
        },
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "request_too_heavy"


def test_optimize_cache_hit_returns_identical_payload(client: TestClient) -> None:
    payload = {"universe": SMALL_UNIVERSE, "method": "min_variance"}
    first = client.post("/optimize", json=payload)
    second = client.post("/optimize", json=payload)
    assert first.status_code == second.status_code == 200
    # The second hit comes from the TTL cache and must be byte-identical
    # (generated_utc included — the cached payload is reused verbatim).
    assert first.json() == second.json()
