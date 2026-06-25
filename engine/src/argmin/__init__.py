"""Argmin — reproducible portfolio optimization & walk-forward backtesting engine.

The package name nods to **argmin** (argument of the minimum): every allocation
model here is, at heart, ``argmin`` of some risk/cost objective over the weight
simplex.
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path

__version__ = "0.1.0"

__all__ = ["__version__", "engine_hash"]


@lru_cache(maxsize=1)
def engine_hash() -> str:
    """A 12-char hash of the package source.

    Used as part of API cache keys so that any logic change invalidates stale
    cached results (Build Checklist: "cache key includes an engine-version hash").
    """
    pkg_dir = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    digest.update(__version__.encode())
    for path in sorted(pkg_dir.rglob("*.py")):
        digest.update(path.relative_to(pkg_dir).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:12]
