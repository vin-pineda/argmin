# Argmin

**Portfolio optimization, backtested honestly.** Seven classical and modern allocation models, built
from scratch, evaluated with cost-aware, walk-forward, out-of-sample backtests, and explained through a
no-login web experience that *shows the mathematics*.

> The name nods to **argmin** (argument of the minimum): every allocation model here is the `argmin` of
> a risk or cost objective over the weight simplex.

## Why this isn't the clichéd in-sample frontier

The version every quant recruiter has seen a thousand times: download prices, plot one in-sample
efficient frontier, declare victory. That chart is the model marking its own homework. Argmin is the
opposite:

- **Out-of-sample only.** Every reported number comes from a walk-forward backtest (monthly rebalance,
  3-year rolling estimation window) on data the model never saw. No look-ahead (asserted in tests).
- **Costs and benchmarks applied.** Transaction costs (bps × turnover) are charged on every rebalance,
  for the strategies *and* the benchmarks (1/N, 60/40, SPY).
- **Significance, not vibes.** Probabilistic and Deflated Sharpe Ratios (trial-count adjusted) plus a
  block-bootstrap confidence interval, so "outperformance" is falsifiable.
- **Honest by default.** The headline finding is that naive max-Sharpe beats 1/N on risk-adjusted
  return and cuts drawdown, but does *not* beat SPY on raw return out-of-sample. We report both.

The seven models: Max-Sharpe (tangency), Global Min-Variance, Efficient Frontier, Max-Diversification,
Equal-Risk-Contribution (Risk Parity), Hierarchical Risk Parity, and Black-Litterman. Optimizers are
implemented from scratch in NumPy / SciPy / CVXPY. `PyPortfolioOpt` and `quantstats` are used **only**
as test oracles.

## Architecture

```
yfinance → Polars → Parquet/DuckDB → estimators (μ, Σ) → 7 optimizers
                                                              │
                                  walk-forward backtest (joblib, tx-costs)
                                                              │
                                    analytics (tearsheet, PSR/DSR, bootstrap)
                                                              │
                              FastAPI (/optimize /backtest /frontier /healthz)
                                                              │
                       Next.js web app  ──  Remotion intro · visx charts · KaTeX math
```

- `engine/` — Python 3.12 / FastAPI. Data, estimators, optimizers, backtest, analytics, API, CLI.
- `web/` — Next.js 16 (App Router) on Vercel. Landing, `/explore` (live cockpit), `/math` (methodology).

See [project_spec.md](./project_spec.md) for the full PRD/engineering spec and
[project_status.md](./project_status.md) for current status.

## Quickstart

**Engine** (Python, [`uv`](https://docs.astral.sh/uv/)):

```bash
cd engine
uv sync                                  # install (pins Python 3.12)
uv run argmin snapshot                   # one-time: freeze the price snapshot (needs network)
uv run pytest -q                         # tests (read the frozen snapshot; never live-fetch)
uv run argmin backtest                   # → engine/outputs/tearsheet.csv + figures
uv run uvicorn argmin.api:app --port 8000  # serve the API
```

**Web** (Node, pnpm):

```bash
cd web
pnpm install
pnpm gen:types                           # regenerate TS types from engine/openapi.json
pnpm dev                                 # http://localhost:3000
```

The web app paints instantly from a committed `default_scenario.json`; custom runs call the engine live
through a same-origin `/api/*` proxy. Point it at your engine with `API_BASE_URL` in `web/.env.local`.

## Reproducibility

Tests and offline runs read the **committed Parquet snapshot** (`engine/data/cache/prices.parquet`) and
never live-fetch yfinance. RNG seeds are fixed; offline re-runs are deterministic.

## Not investment advice

All results are historical, out-of-sample backtests for research and demonstration only. Past
performance does not predict future returns. Nothing here is investment advice.

## License

[MIT](./LICENSE).
