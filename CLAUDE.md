# CLAUDE.md — Argmin

Argmin is a reproducible, production-grade **portfolio optimization + walk-forward backtesting engine**
(Python/FastAPI) fronted by a **no-login, animated Next.js web experience that shows the math**. It's a
portfolio piece judged on quant correctness, evaluation honesty, engineering maturity, and design taste.

> Keep this file lean. The full picture lives in linked docs — read them, don't duplicate them here.

## Source-of-truth docs (read these)
- **[project_spec.md](./project_spec.md)** — the PRD + engineering spec. Goals, personas, milestones
  (§1.4), tech stack (§2.1), **architecture & monorepo layout (§2.2)**, API contract (§2.2),
  numerical correctness notes (§2.2), design pipeline (§2.3), and the **Build Checklist (PART 5)**.
- **[project_status.md](./project_status.md)** — where we left off, milestone status, session log.
  **Update this at the end of any work session.**
- **[.env.example](./.env.example)** — every env var and whether it's required.
- `CHANGELOG.md` — running list of notable changes (create + maintain once code lands).

## Architecture (one-liner; full tree in spec §2.2)
Monorepo: `engine/` (Python/FastAPI — data → estimators(μ,Σ) → 7 optimizers → walk-forward backtest →
analytics → API) and `web/` (Next.js App Router on Vercel — Remotion intro, visx/D3 charts, KaTeX math).
Data flow: `yfinance → Polars → Parquet/DuckDB → estimators → optimizers → backtest → FastAPI → web`.

## Non-negotiable constraints & policies
- **Optimizers are implemented from scratch** (CVXPY/SciPy/NumPy). `PyPortfolioOpt` and `quantstats`
  are **test oracles only** — never ship them as the implementation.
- **The front-end is bespoke, never templated.** No generic component dumps.
- **No login, ever. Stateless, no user DB.** Never add auth, `DATABASE_URL`, `AUTH_SECRET`, or persist
  user runs (out of scope — spec Part 3).
- **Secrets only via env** (`.env`, gitignored). Never hardcode or commit secrets.
- **Reproducibility is sacred.** Tests and offline runs read the **committed Parquet cache** — never
  live-fetch yfinance in tests/CI. Respect fixed RNG seeds.
- **Honesty over flattery in results:** OOS only, transaction costs applied, benchmarks (1/N, 60/40,
  SPY), significance (PSR/DSR + bootstrap). Don't report in-sample numbers as if they're OOS.
- **Public live endpoints must be safe:** validate `universe` against a whitelist, cap backtest
  complexity/timeout, lock CORS to the web origin in prod. (See Build Checklist.)

## Design pipeline (skills — use in this order)
1. `impeccable` → `/shape` (M6) → `/craft` (M7) → `/critique` (M8) → `/polish` (M9)
2. `design-taste-frontend` **v2** (brief→design-system map, dark-mode protocol, block-library schema,
   hard pre-flight check; v1 is fallback only)
3. `emil-design-eng` (motion vocabulary, taste, invisible details)
4. `remotion-best-practices` (intro + animated math)

> **DISABLED — do not invoke:** Anthropic's built-in **`frontend-design`** skill. It conflicts with the
> pipeline above and must not be used for this project. Enforced here and via settings.

**Aesthetic:** dark-mode-first, data-dense, precise — "Bloomberg-terminal-meets-editorial-research-paper."
Hairline rules, graph-paper/grid motifs, monospaced numerics, one restrained accent, equations as
first-class typographic objects.

**MCP tooling — use these, don't work around them:**
- **21st magic MCP** — build/refine **every bespoke UI component** with it first (builder → refiner),
  then adapt to the design system. Don't hand-roll components from scratch when magic can scaffold them.
- **shadcn registry MCP** — accessible primitives.
- **Playwright MCP** — **the front-end testing tool.** ALL web testing runs through Playwright: drive
  the browser for automated visual + a11y + contrast + persona QA (recruiter/quant/DIY) at
  375/768/1440px, in `/critique` and in CI. Don't claim the UI works without a Playwright check.
- **vercel MCP** — deploy.

## Tech stack (rationale in spec §2.1)
- **Engine:** Python 3.12+, `uv`, Polars, DuckDB/Parquet, NumPy/SciPy/**CVXPY** (Clarabel/OSQP),
  scikit-learn, statsmodels, pydantic v2, FastAPI, Typer; structlog logging.
- **Web:** Next.js (App Router) + React + TypeScript, Tailwind + shadcn/ui (Radix), Motion (Framer),
  Remotion + `@remotion/player`, KaTeX, visx/D3 (+ Recharts for simple), TanStack Query, Zustand.

## Commands
**Engine** (run inside `engine/`):
```bash
uv sync                                         # install deps
uv run pytest -q                                # tests (unit + Hypothesis)
uv run ruff check . && uv run ruff format .     # lint + format
uv run mypy --strict src                        # types
uv run argmin backtest --config config/default.yaml   # CLI: figures + tearsheet.csv
uv run uvicorn argmin.api:app --reload          # serve the API locally
```
**Web** (run inside `web/`, pnpm assumed):
```bash
pnpm install
pnpm dev            # local dev server
pnpm lint           # eslint
pnpm typecheck      # tsc --noEmit
pnpm build          # production build
pnpm exec playwright test    # a11y/contrast/visual at 375/768/1440px
```

## Testing
- Engine: property tests (Σw=1, w≥0), closed-form checks, ERC equal-risk-contribution verification,
  metrics cross-checked vs `quantstats` within tolerance, no-look-ahead assertion. CI must be green
  (ruff + mypy + pytest) before anything is considered done.
- Web: lint + typecheck + build + **Playwright (via the playwright MCP) — the required web test tool**
  for breakpoints (375/768/1440px), a11y, contrast, and anti-slop/persona QA. New/changed components
  are scaffolded with the **21st magic MCP**. A UI change isn't "done" until Playwright is green.

## Repo etiquette
- **Not yet a git repo** — `git init` is part of M0. Once initialized:
- **Do not commit or push unless explicitly asked.** When asked, branch off `main` first
  (`feat/…`, `fix/…`, `chore/…`); never push to `main` directly.
- Never commit `.env` or secrets. Commit the **pinned Parquet data snapshot** intentionally (it's the
  reproducibility source of truth) — but no other large/generated artifacts.

## Doc maintenance (do this as you work)
- After finishing a feature/milestone: update **project_status.md** (status + session log + where you
  left off) and add a **CHANGELOG.md** entry.
- When architecture changes materially, update **project_spec.md §2.2** rather than spawning a parallel
  doc.
