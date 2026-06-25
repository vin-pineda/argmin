"""structlog configuration for the engine."""

from __future__ import annotations

import logging

import structlog


def configure_logging(level: str = "INFO", json: bool = False) -> None:
    """Configure structlog with a console or JSON renderer."""
    logging.basicConfig(format="%(message)s", level=getattr(logging, level.upper(), logging.INFO))
    renderer: structlog.types.Processor = (
        structlog.processors.JSONRenderer() if json else structlog.dev.ConsoleRenderer()
    )
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "argmin") -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)  # type: ignore[no-any-return]
