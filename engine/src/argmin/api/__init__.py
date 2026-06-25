"""Argmin HTTP API package.

``app`` is the FastAPI application served by ``uvicorn argmin.api:app``. The
pure request → engine mapping lives in :mod:`argmin.api.service`; the wire
contract lives in :mod:`argmin.api.models`.
"""

from __future__ import annotations

from argmin.api.app import app, create_app

__all__ = ["app", "create_app"]
