# Argmin Engine

Python/FastAPI engine: data → estimators (μ, Σ) → 7 optimizers → walk-forward
backtest → analytics → API. Optimizers are implemented **from scratch**
(CVXPY/SciPy/NumPy); `PyPortfolioOpt`/`quantstats` are **test oracles only**.

## Quickstart

```bash
uv sync                                    # install deps (pins Python 3.12)
uv run argmin snapshot                     # one-time: freeze the price snapshot (needs network)
uv run pytest -q                           # tests (read the frozen snapshot, never live-fetch)
uv run ruff check . && uv run mypy src     # lint + types
uv run argmin backtest                     # figures + tearsheet.csv  (M3/M5)
uv run uvicorn argmin.api:app --reload     # serve the API            (M5)
```

## Layout

```
src/argmin/
├── types.py          # shared contracts (Moments, Constraints, OptimizeResult, Protocols)
├── config.py         # ArgminConfig (YAML) + Settings (env)
├── data/             # snapshot freezer + returns-panel loader  (M0)
├── estimators/       # μ (sample/EWMA/CAPM) + Σ (sample/Ledoit-Wolf/EWMA)  (M1)
├── optimizers/       # min-var, max-sharpe, frontier, ERC, HRP, max-div, BL  (M1/M2)
├── backtest/         # walk-forward engine + benchmarks  (M3)
├── analytics/        # tearsheet + PSR/DSR + bootstrap  (M4)
├── api/              # FastAPI app  (M5)
└── cli.py            # Typer CLI
```

Reproducibility: the engine reads the committed Parquet snapshot
(`data/cache/prices.parquet`) and never live-fetches yfinance in tests/CI.
