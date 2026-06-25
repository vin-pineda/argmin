"""The Argmin FastAPI service.

Endpoints
---------
* ``POST /optimize``  — single-shot allocation for a universe + method.
* ``POST /backtest``  — walk-forward OOS backtest (strategy + benchmarks).
* ``GET  /frontier``  — efficient frontier + tangency/min-var + random cloud.
* ``GET  /healthz``   — liveness + version/engine-hash + whitelist.

Safety (public live endpoints)
-------------------------------
* **Universe whitelist** — requested tickers must be a subset of the scenario
  universe; otherwise ``422 invalid_universe``.
* **Complexity caps** — ``len(universe) <= max_assets`` and backtest span
  ``<= max_years``; otherwise ``422 request_too_heavy``.
* **CORS** — locked to ``settings.cors_origins`` (no ``*`` in production).
* **TTL response cache** — keyed by ``(endpoint, normalized params, engine_hash)``
  so a logic change (new ``engine_hash``) misses stale entries.
* **Rate limit** — in-memory per-IP sliding window (``rate_limit_per_minute``);
  ``429 rate_limited`` when exceeded. *Production story: Vercel BotID + IP.*
* **Typed errors** — validation/value/key errors → ``422``; anything unexpected
  → ``500 internal_error``. Tracebacks are never leaked to the client.
"""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from threading import Lock
from typing import TYPE_CHECKING, Any, cast

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from argmin import __version__, engine_hash
from argmin.api import service
from argmin.api.models import (
    BacktestRequest,
    BacktestResponse,
    ErrorResponse,
    FrontierResponse,
    HealthResponse,
    OptimizeRequest,
    OptimizeResponse,
)
from argmin.config import ArgminConfig, Settings, get_settings, load_default_config
from argmin.data import load_returns_panel

if TYPE_CHECKING:
    from argmin.types import ReturnsPanel


# ──────────────────────────────────────────────────────────────────────────────
# Typed application state (loaded once at startup)
# ──────────────────────────────────────────────────────────────────────────────
class AppState:
    """Long-lived engine objects + the in-memory cache / rate-limiter."""

    def __init__(self, config: ArgminConfig, settings: Settings, panel: ReturnsPanel) -> None:
        self.config = config
        self.settings = settings
        self.panel = panel
        self.cache = TTLCache(ttl_seconds=settings.cache_ttl_seconds)
        self.rate_limiter = RateLimiter(settings.rate_limit_per_minute)


# ──────────────────────────────────────────────────────────────────────────────
# In-memory TTL cache (response payloads keyed by normalized params + engine hash)
# ──────────────────────────────────────────────────────────────────────────────
class TTLCache:
    """A tiny thread-safe TTL cache for serialized response payloads.

    Keys embed :func:`argmin.engine_hash` so that any engine source change
    invalidates every prior entry (stale entries simply never match).
    """

    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[float, dict[str, Any]]] = {}
        self._lock = Lock()

    def get(self, key: str) -> dict[str, Any] | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, payload = entry
            if time.monotonic() >= expires_at:
                self._store.pop(key, None)
                return None
            return payload

    def set(self, key: str, payload: dict[str, Any]) -> None:
        with self._lock:
            self._store[key] = (time.monotonic() + self._ttl, payload)


def _cache_key(endpoint: str, params: dict[str, Any]) -> str:
    """Stable cache key from endpoint + normalized params + engine hash."""
    import json  # noqa: PLC0415 — local import keeps module import cheap

    normalized = json.dumps(params, sort_keys=True, default=str)
    return f"{endpoint}|{engine_hash()}|{normalized}"


# ──────────────────────────────────────────────────────────────────────────────
# In-memory per-IP sliding-window rate limiter
# ──────────────────────────────────────────────────────────────────────────────
class RateLimiter:
    """Sliding-window limiter: at most ``per_minute`` requests per IP per 60s.

    This is a *single-process* guard for the demo/dev deployment. In production
    the durable story is Vercel BotID + edge IP rate limiting; this is the
    defense-in-depth fallback so a direct hit on the API is still bounded.
    """

    def __init__(self, per_minute: int) -> None:
        self._per_minute = per_minute
        self._hits: dict[str, deque[float]] = {}
        self._lock = Lock()

    def allow(self, client: str) -> bool:
        if self._per_minute <= 0:
            return True
        now = time.monotonic()
        window_start = now - 60.0
        with self._lock:
            hits = self._hits.setdefault(client, deque())
            while hits and hits[0] < window_start:
                hits.popleft()
            if len(hits) >= self._per_minute:
                return False
            hits.append(now)
            return True


# ──────────────────────────────────────────────────────────────────────────────
# Domain errors → typed HTTP errors
# ──────────────────────────────────────────────────────────────────────────────
class ApiError(Exception):
    """A client-facing error with a stable machine code and HTTP status."""

    def __init__(self, status_code: int, error: str, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.error = error
        self.detail = detail


def _error_response(status_code: int, error: str, detail: str) -> JSONResponse:
    body = ErrorResponse(error=error, detail=detail)
    return JSONResponse(status_code=status_code, content=body.model_dump())


def _state(request: Request) -> AppState:
    return cast("AppState", request.app.state.engine)


def _validate_universe(universe: list[str], config: ArgminConfig) -> None:
    """Whitelist + complexity-cap guard shared by every data endpoint."""
    if not universe:
        raise ApiError(422, "invalid_universe", "universe must not be empty")
    allowed = set(config.universe)
    bad = [t for t in universe if t not in allowed]
    if bad:
        raise ApiError(
            422,
            "invalid_universe",
            f"tickers not in whitelist: {sorted(bad)}; allowed: {sorted(allowed)}",
        )
    if len(set(universe)) > config.backtest.max_assets:
        raise ApiError(
            422,
            "request_too_heavy",
            f"universe of {len(set(universe))} exceeds max_assets={config.backtest.max_assets}",
        )


def _client_ip(request: Request) -> str:
    if request.client is not None:
        return request.client.host
    return "anonymous"


# ──────────────────────────────────────────────────────────────────────────────
# Lifespan: load config/settings/panel ONCE
# ──────────────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    config = load_default_config()
    settings = get_settings()
    panel = load_returns_panel(config, settings)
    app.state.engine = AppState(config, settings, panel)
    yield


def create_app() -> FastAPI:
    """Construct the FastAPI app (factory so tests/CLI can build it cleanly)."""
    settings = get_settings()

    app = FastAPI(
        title="Argmin API",
        version=__version__,
        summary="Portfolio optimization + walk-forward backtesting (stateless, no login).",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # ── Rate-limit middleware (per client IP) ─────────────────────────────────
    @app.middleware("http")
    async def _rate_limit(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # ``/healthz`` and docs are exempt so liveness checks never trip the limit.
        if request.url.path not in {"/healthz", "/openapi.json", "/docs", "/redoc"}:
            limiter = cast("AppState", request.app.state.engine).rate_limiter
            if not limiter.allow(_client_ip(request)):
                return _error_response(429, "rate_limited", "too many requests; slow down")
        return await call_next(request)

    # ── Exception handlers → typed ErrorResponse (no traceback leakage) ───────
    @app.exception_handler(ApiError)
    async def _on_api_error(_request: Request, exc: ApiError) -> JSONResponse:
        return _error_response(exc.status_code, exc.error, exc.detail)

    @app.exception_handler(RequestValidationError)
    async def _on_validation(_request: Request, exc: RequestValidationError) -> JSONResponse:
        return _error_response(422, "validation_error", str(exc.errors()))

    @app.exception_handler(ValueError)
    async def _on_value_error(_request: Request, exc: ValueError) -> JSONResponse:
        return _error_response(422, "invalid_request", str(exc))

    @app.exception_handler(KeyError)
    async def _on_key_error(_request: Request, exc: KeyError) -> JSONResponse:
        return _error_response(422, "invalid_request", str(exc))

    @app.exception_handler(Exception)
    async def _on_unexpected(_request: Request, _exc: Exception) -> JSONResponse:
        return _error_response(500, "internal_error", "an unexpected error occurred")

    # ── Endpoints ─────────────────────────────────────────────────────────────
    @app.get("/healthz", response_model=HealthResponse)
    async def healthz(request: Request) -> HealthResponse:
        state = _state(request)
        return HealthResponse(
            status="ok",
            version=__version__,
            engine_hash=engine_hash(),
            universe=list(state.config.universe),
        )

    @app.post(
        "/optimize",
        response_model=OptimizeResponse,
        responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    )
    async def optimize(request: Request, body: OptimizeRequest) -> JSONResponse:
        state = _state(request)
        _validate_universe(body.universe, state.config)
        key = _cache_key("optimize", body.model_dump())
        cached = state.cache.get(key)
        if cached is not None:
            return JSONResponse(content=cached)
        result = service.optimize(state.panel, state.config, state.settings, body)
        payload = result.model_dump()
        state.cache.set(key, payload)
        return JSONResponse(content=payload)

    @app.post(
        "/backtest",
        response_model=BacktestResponse,
        responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    )
    async def backtest(request: Request, body: BacktestRequest) -> JSONResponse:
        state = _state(request)
        _validate_universe(body.universe, state.config)
        _check_backtest_span(body, state.config)
        key = _cache_key("backtest", body.model_dump())
        cached = state.cache.get(key)
        if cached is not None:
            return JSONResponse(content=cached)
        result = service.backtest(state.panel, state.config, state.settings, body)
        payload = result.model_dump()
        state.cache.set(key, payload)
        return JSONResponse(content=payload)

    @app.get(
        "/frontier",
        response_model=FrontierResponse,
        responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    )
    async def frontier(
        request: Request,
        universe: str,
        as_of: str | None = None,
    ) -> JSONResponse:
        state = _state(request)
        tickers = [t.strip().upper() for t in universe.split(",") if t.strip()]
        _validate_universe(tickers, state.config)
        key = _cache_key("frontier", {"universe": tickers, "as_of": as_of})
        cached = state.cache.get(key)
        if cached is not None:
            return JSONResponse(content=cached)
        result = service.frontier(state.panel, state.config, state.settings, tickers, as_of)
        payload = result.model_dump()
        state.cache.set(key, payload)
        return JSONResponse(content=payload)

    return app


def _check_backtest_span(body: BacktestRequest, config: ArgminConfig) -> None:
    """Reject backtests whose requested span exceeds ``max_years``."""
    if body.start is None or body.end is None:
        return
    try:
        import numpy as np  # noqa: PLC0415 — only needed on this guarded path

        start = np.datetime64(body.start)
        end = np.datetime64(body.end)
    except (ValueError, TypeError) as exc:
        raise ApiError(422, "invalid_request", f"invalid start/end date: {exc}") from exc
    span_days = (end - start) / np.timedelta64(1, "D")
    if span_days > config.backtest.max_years * 366:
        raise ApiError(
            422,
            "request_too_heavy",
            f"backtest span exceeds max_years={config.backtest.max_years}",
        )


app = create_app()

__all__ = ["app", "create_app"]
