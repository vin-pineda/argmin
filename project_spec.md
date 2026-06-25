# Argmin — Systematic Portfolio Optimization, Backtesting & Interactive Web Platform

> **Project name: `Argmin`.** It alludes to **argmin — "argument of the minimum"** — the operator every
> allocation model in this project ultimately evaluates (each strategy is, at heart, `argmin` of some
> risk/cost objective over the weight simplex). The name is woven into the brand, the landing
> animation, and the codebase (`argmin` package, `argmin` CLI).

**Author persona:** Senior Quantitative Developer / Researcher **+** Senior UI/UX Designer.
**One-liner:** A reproducible, production-grade engine that constructs multi-asset portfolios with
classical *and* modern allocation models and proves them out with honest, cost-aware, walk-forward
out-of-sample backtests — fronted by a **no-login, animated web experience** that *shows the
mathematics* so anyone can click and explore it instantly.

**Why this exists as a portfolio piece:** the clichéd version (download prices → plot one in-sample
frontier) is what every quant recruiter has seen a thousand times. Argmin is the opposite on two
axes: (1) it demonstrates *why naive Markowitz fails out-of-sample* and the modern fixes, with
FAANG-grade engineering; and (2) it presents that depth through a **bespoke, motion-rich, finance-math
web interface** that makes the math legible and beautiful — a senior-designer signal on top of a
senior-quant one.

---

## PART 1 — PRODUCT REQUIREMENTS (What & Why)

### 1.1 Who is this for? (Personas)
1. **The systematic / junior quant researcher** — wants a reproducible sandbox to compare allocation
   models on the same universe under identical, honest evaluation.
2. **The quant PM / risk-aware allocator** — wants to stress-test allocations across regimes (2008,
   2020, 2022) with realistic costs and a clear read on whether outperformance is *statistically real*.
3. **The curious DIY investor** — lands on the site, clicks once, and *sees* a diversified,
   risk-managed portfolio constructed and explained — no signup, no friction.
4. **The real audience: seasoned recruiters & hiring managers** at quant funds and FAANG — judge the
   repo on quant correctness, evaluation honesty, engineering maturity, **and design taste**.

### 1.2 What problems does it solve?
- **Naive allocation is fragile.** Sample-based mean-variance produces extreme, unstable weights that
  look great in-sample and lose out-of-sample (estimation error dominates).
- **Most analyses are dishonest by omission** — they skip OOS validation, transaction costs,
  benchmarks, and significance testing, so "outperformance" is unfalsifiable.
- **Quant work is usually invisible & inaccessible** — buried in notebooks. Argmin makes the methods
  *and the math* interactive and instantly explorable by anyone, with zero setup.

### 1.3 What the product does (capabilities & concrete user workflows)
**Engine capabilities**
- Ingests & caches multi-asset price data; computes a clean returns panel (reproducible offline).
- Robust input estimation: expected returns (sample / EWMA / CAPM-implied) and covariance
  (sample / **Ledoit-Wolf shrinkage** / EWMA).
- **7 allocation models**: Max-Sharpe (tangency), Global Min-Variance, full Efficient Frontier,
  Max-Diversification, Equal-Risk-Contribution (Risk Parity), Hierarchical Risk Parity, Black-Litterman.
- **Walk-forward OOS backtest** with rebalancing + transaction costs, benchmarked vs Equal-Weight
  (1/N), 60/40, and SPY.
- Full **tearsheet** (return, vol, Sharpe, Sortino, MaxDD, Calmar, VaR/CVaR, turnover) + **statistical
  significance** (Probabilistic & Deflated Sharpe, bootstrap CIs).

**Concrete user workflows**
- *Public web app (primary surface):* a visitor opens the site → a **cinematic Remotion intro** plays
  (the `argmin` operator + an efficient frontier being traced). They land on a default scenario that is
  **already computed** (instant). They tweak universe / date range / rebalance frequency / cost (bps) /
  models and hit **Run** → the app calls the engine live (cached + rate-limited) and every chart +
  equation **animates** to the new result. No login, ever. A "Download report" exports the tearsheet.
- *Show-the-math narrative:* a scroll-driven section renders each method's equation in **KaTeX**,
  **animated** beside its live chart (frontier, covariance heatmap → shrinkage morph, dendrogram build,
  risk-contribution bars, BL prior→views→posterior, walk-forward equity/drawdown/rolling-Sharpe).
- *Engine, headless:* `argmin backtest --config config/default.yaml` runs everything and emits
  figures + `tearsheet.csv`; `POST /optimize` and `POST /backtest` expose it as a service.

### 1.4 Milestones & Definition of Done
**Engine track**
- **M0 — Foundation & Identity.** *DoD:* repo + brand established — **name `Argmin` (= argument of the
  minimum)** locked into package/CLI/brand voice; `uv` project builds; CI green (ruff + mypy + pytest);
  pydantic config validates; data loader → Parquet/DuckDB; returns panel reproducible offline.
- **M1 — Estimators + core optimizers + frontier.** *DoD:* returns/covariance (incl. Ledoit-Wolf)
  unit-tested; Min-Var, Max-Sharpe, Efficient Frontier via CVXPY; property tests (Σw=1, w≥0) pass.
- **M2 — Advanced models.** *DoD:* Risk Parity (ERC), HRP, Max-Diversification, Black-Litterman
  implemented & tested (equal risk-contributions verified; BL→prior when no views).
- **M3 — Walk-forward backtest engine.** *DoD:* rolling rebalancing + transaction costs + benchmarks
  (1/N, 60/40, SPY); joblib-parallel; deterministic given cache.
- **M4 — Analytics & significance.** *DoD:* full tearsheet + PSR/DSR + bootstrap CIs; cross-checked vs
  `quantstats` within tolerance.
- **M5 — Engine API.** *DoD:* FastAPI `/optimize`, `/backtest`, `/frontier`, `/healthz` with typed
  pydantic request/response models; results cacheable & rate-limitable; OpenAPI schema published.

**Front-end / design track** — each milestone is one stage of the design pipeline (§2.3), but the
pipeline is **not a single forward pass**: after the first build, the **CRAFT → CRITIQUE → POLISH loop
runs for several iterations** (≥3 full cycles; protocol in §2.3) before the track is "done." Every pass
produces a versioned snapshot + a critique scorecard, and we advance only when the score improves *and*
the mathematics reads as credible. No stage is one-and-done.
- **M6 — SHAPE.** *DoD:* `impeccable /shape` discovery → a written **design brief** (audience, voice,
  finance-math direction, references) + the Taste **brief interface** filled; reviewed/approved.
- **M7 — CRAFT.** *DoD:* `design-taste-frontend` v2 **brief→design-system map** + **dark-mode
  protocol** + **block-library schema** produce real tokens & components (**components scaffolded /
  refined via the 21st magic MCP**, then adapted to the design system); `emil-design-eng` motion
  vocabulary applied; `impeccable /craft` builds the Next.js app; **Remotion** intro + animated
  equations/charts in place; **no-login instant-try** working against the engine. This is **iteration
  v1** — the design then enters the CRAFT→CRITIQUE→POLISH loop (§2.3), it is not shipped as-is.
- **M8 — CRITIQUE.** *DoD:* `impeccable /critique` scorecard ≥ target; **persona tests**
  (recruiter / quant / DIY) pass; **Playwright** automated detection (375/768/1440px, a11y, contrast,
  anti-slop) green; Taste **hard pre-flight check** passes. Run as **≥3 CRAFT→CRITIQUE→POLISH
  iterations** — each versioned and logged in `web/design/iterations/LOG.md` — and considered done only
  when two consecutive iterations surface no actionable findings and the math credibility bar (§2.3) is
  met.
- **M9 — POLISH.** *DoD:* `impeccable /polish` final pass — Emil micro-interactions & motion timing,
  Core Web Vitals (LCP/CLS/INP) in budget, full keyboard/AX, reduced-motion fallback.
- **M10 — Deploy & stretch.** *DoD:* web app live on **Vercel** (public, no login) + engine deployed;
  stretch: Fama-French 5+momentum factor attribution, MkDocs docs, distributed backtest (Ray).

---

## PART 2 — ENGINEERING REQUIREMENTS (How)

### 2.1 Tech Stack (explicit, with rationale)

**Engine (Python)**
| Layer | Choice | Why |
|---|---|---|
| Language / env | **Python 3.12+**, **uv**, `pyproject.toml` | Quant lingua franca; fastest modern tooling. |
| DataFrames / store | **Polars** + **DuckDB/Parquet** (Arrow) | Modern, columnar, reproducible. |
| Data source | **yfinance** behind a `DataSource` protocol | Free + cacheable; swappable to Polygon/Bloomberg. |
| Numerics / opt | **NumPy + SciPy + CVXPY** (Clarabel/OSQP) | Convex modeling = the portfolio-optimization signal. |
| ML / stats | **scikit-learn** (Ledoit-Wolf, clustering), **statsmodels** | Credible estimators. |
| Config / quality | **pydantic v2**, **pytest + Hypothesis**, **ruff**, **mypy --strict**, **structlog** | Typed, property-tested, production discipline. |
| Service | **FastAPI** + **Typer** CLI | Typed microservice powering the web app. |

**Front-end & design**
| Layer | Choice | Why |
|---|---|---|
| Framework / host | **Next.js (App Router) + React + TypeScript** on **Vercel** | Industry-standard, Vercel-native, fast. |
| Styling / components | **Tailwind CSS + shadcn/ui** (Radix) | Composable, accessible, design-system friendly. |
| UI motion | **Motion** (Framer Motion) | Micro-interactions / transitions (Emil's domain). |
| Cinematic + math motion | **Remotion** + `@remotion/player` | Landing intro + animated equations/graphs in-page. |
| Equations | **KaTeX** | Crisp math typesetting, animated via Motion/Remotion. |
| Charts | **visx / D3** (bespoke), Recharts (simple) | Quant-grade, non-templated, fully controllable. |
| Data / state | **TanStack Query** → FastAPI; **Zustand** (light) | Clean async + minimal state. |

**Design pipeline (skills & MCP)**
- **Skills, in order:** `impeccable` (**/shape → /craft → /critique → /polish**) · `design-taste-frontend`
  **v2** (brief interface, brief→design-system map, dark-mode protocol, redesign protocol, block-library
  schema, **hard pre-flight check**; v1 fallback only) · `emil-design-eng` (motion vocabulary + taste +
  invisible details) · `remotion-best-practices`.
- **Disabled:** Anthropic's built-in **`frontend-design`** skill (conflicts with the above) — must not
  be invoked for this project; enforced via project `CLAUDE.md` + settings.
- **MCP servers (required tooling — use them, don't hand-roll around them):**
  - **21st magic** — generate, get inspiration for, and refine **all bespoke UI components**. Reach for
    it *first* when building a new component (builder → refiner), then adapt; don't hand-write
    components from scratch when magic can scaffold them.
  - **shadcn registry** — accessible primitives.
  - **playwright** — **the front-end testing tool.** Every web test runs through Playwright (driven via
    the playwright MCP): automated visual + a11y + contrast + persona QA (recruiter/quant/DIY) at
    375/768/1440px, in `/critique` (M8) and in CI.
  - **vercel** — deploy.
  - Install any missing (ask first).

> *Engineering stance:* engine optimizers are implemented **from scratch** (CVXPY/SciPy/NumPy);
> `PyPortfolioOpt`/`quantstats` are **test oracles only**. The front-end is **bespoke**, not a template.

### 2.2 Technical Architecture

**System data flow**
```
yfinance ─▶ Polars ─▶ Parquet/DuckDB ─▶ estimators (μ,Σ) ─▶ optimizers (7 models)
                                                                   │
                                              walk-forward backtest (joblib, tx-costs)
                                                                   │
                                                    analytics (tearsheet, PSR/DSR, bootstrap)
                                                                   │
                                           ┌───────── FastAPI (/optimize /backtest /frontier) ─────────┐
                                           │                                                           │
                                  precomputed default JSON                                    live (cached + rate-limited)
                                           └───────────────▶  Next.js web app (Vercel)  ◀──────────────┘
                                                              ├─ Remotion intro + animated math
                                                              ├─ visx/D3 interactive charts
                                                              └─ KaTeX equations (Motion-animated)
```

**Monorepo layout**
```
argmin/
├── project_spec.md   README.md   CLAUDE.md   .github/workflows/ci.yml
├── engine/                              # Python (FastAPI) — the Argmin engine
│   ├── pyproject.toml  Dockerfile
│   ├── config/default.yaml
│   └── src/argmin/{config,data,estimators,optimizers,backtest,analytics,api,cli}.py …
└── web/                                 # Next.js front-end (Vercel)
    ├── app/                             # routes: landing, /explore, /math
    ├── components/                      # shadcn-based + bespoke chart blocks
    ├── design/                          # design brief, tokens, block-library schema (Taste v2)
    ├── remotion/                        # intro composition + animated equation/graph comps
    └── lib/                             # api client (TanStack Query), formatting, math
```

**Engine API (the web contract)**
- `POST /optimize` {universe, method, constraints, as_of} → {weights, exp_return, exp_vol, sharpe, risk_contrib}
- `POST /backtest` {config} → {metrics, equity_curve, drawdown, rolling_sharpe, weights_over_time}
- `GET /frontier` {universe, as_of} → {frontier_points, tangency, min_var, random_cloud}
- `GET /healthz`. Typed pydantic models; OpenAPI auto-doc; responses cache-keyed by params.

**Key numerical correctness notes**
- Daily simple returns; annualize μ×252, Σ×252. **Max-Sharpe** via convex reformulation (min wᵀΣw s.t.
  (μ−rf)ᵀw=1, w≥0, renormalize). **Risk Parity** via Spinu log-barrier; verify equal risk contributions.
  **HRP** from scratch (corr→dist→linkage→quasi-diag→recursive bisection). **Black-Litterman**
  π=δΣw_mkt → posterior. **Backtest** monthly rebalance, 3-yr rolling lookback, tx-cost = bps×turnover.
  **Significance** PSR/DSR (trial-count adjusted) + bootstrap CIs.

### 2.3 Front-End Experience & Design System (the design pipeline)

**Aesthetic direction (seed for /shape, finalized by Taste):** dark-mode-first, data-dense, precise —
"Bloomberg-terminal-meets-editorial-research-paper." Hairline rules, graph-paper/grid motifs,
monospaced numerics, one restrained signal accent, generous spacing around dense data, equations
treated as first-class typographic objects.

**Pipeline (stage = milestone):**
1. **/shape (M6)** — discovery, not guesswork: produce a design **brief** (audience, voice, references,
   finance-math direction) and fill the Taste **brief interface**.
2. **CRAFT (M7)** — Taste v2 **brief→design-system map** generates tokens; **dark-mode protocol** sets
   the default theme; **block-library schema** defines reusable sections (hero, control panel, chart
   block, equation block, tearsheet table); `emil-design-eng` supplies motion vocabulary; `impeccable
   /craft` builds the Next.js components; **Remotion** builds the intro + animated math.
3. **/critique (M8)** — scoring + **persona tests** (recruiter / quant / DIY) + **Playwright**
   automated detection (breakpoints, a11y, contrast, anti-slop); Taste **hard pre-flight check**.
4. **/polish (M9)** — Emil micro-interactions, motion timing/easing, reduced-motion fallback, Core Web
   Vitals, full keyboard/AX.

**Iteration loop (non-negotiable — the design must go through several passes):** the pipeline above is
the *first* lap, not the whole race. After the v1 CRAFT build, run **CRAFT → CRITIQUE → POLISH as a
loop, ≥3 full iterations**, until the critique scorecard plateaus at/above target *and* every persona
test passes. Each iteration:
- produces a **versioned snapshot** (`v1`, `v2`, …) kept in `web/design/iterations/`, with before/after
  screenshots at 375/768/1440px captured via the Playwright MCP;
- is scored against the `/critique` scorecard + Taste **hard pre-flight**, and the **delta vs. the prior
  iteration is logged** (what changed, why, how the score moved) in `web/design/iterations/LOG.md`;
- must not regress a passing dimension to lift another.
Stop only when two consecutive iterations show no actionable findings. The iteration log is a reviewable
artifact — it *demonstrates* the work was refined, not generated once.

**Mathematical credibility & documentation (the differentiator — the site must *earn* trust, not assert
it):**
- **Equations are first-class objects, never decoration.** Every model renders its objective in KaTeX
  with correct notation and a **"show derivation"** affordance that expands the key steps (tangency from
  the Lagrangian; ERC from the Spinu log-barrier; the Black-Litterman posterior blend; Ledoit-Wolf
  shrinkage intensity).
- **Cite the literature** so a quant reviewer can trace every method to source: Markowitz (1952),
  Ledoit-Wolf (2004), Black-Litterman (1992), López de Prado HRP (2016), Bailey & López de Prado
  PSR/DSR (2014). References surface inline next to the relevant equation/chart.
- **Show real, relevant graphs** beside each equation (the full animated set is enumerated below). Axes
  are labeled, units stated, no toy/placeholder data — **every chart binds to live engine output**.
- **Expose provenance & honesty inline:** data window, rebalance rule, cost (bps), risk-free source,
  an **OOS-only** badge, and the **engine-version hash** sit visibly *near the numbers*, not buried in a
  footnote.
- **A methodology page (`/math`)** documents assumptions, estimators, and limitations in a research-paper
  register (with the "Not investment advice" note), and its numbers reconcile exactly with the engine
  tearsheet.

**Show-the-math requirement (must render in the site, animated):** mean-variance objective + efficient
frontier traced; Sharpe/CAL/tangency; Ledoit-Wolf shrinkage (sample→shrunk covariance heatmap morph);
risk-parity log-barrier + equal-risk-contribution bars; HRP dendrogram build + quasi-diagonalization;
Black-Litterman prior→views→posterior blend; walk-forward equity curves + underwater drawdown + rolling
Sharpe; PSR/DSR + bootstrap distribution.

**No-login UX decision:** fully anonymous, stateless, no auth, no user DB. Instant first paint via a
**precomputed default scenario** baked as static JSON; custom runs call the engine **live**, with
responses **cached** (Vercel Runtime Cache, keyed by params) and **rate-limited** (Vercel BotID / IP) to
prevent abuse. *(Stretch: optional Pyodide/WASM client-side compute for zero-backend instant tweaks.)*

### 2.4 Infrastructure & Provisioning
- **Web:** Vercel (Next.js), public URL, no login. **Engine:** FastAPI on Vercel Python (Fluid Compute)
  or a separate service (Fly.io/Railway) — Dockerized.
- **CI:** GitHub Actions — engine (ruff + mypy + pytest) and web (lint + typecheck + build + Playwright).
- **Reproducibility:** Parquet cache + fixed RNG seeds; default scenario JSON regenerated by the engine.

---

## PART 3 — Out of scope (v1)
User accounts/login, persistence of user runs, live trading/broker execution, intraday data,
options/derivatives, tax-lot accounting.

## PART 4 — How a reviewer will judge success
1. **Quant correctness** (closed-form + property tests). 2. **Evaluation honesty** (OOS, costs,
benchmarks, significance). 3. **Engineering maturity** (typed, tested, containerized, CI-green).
4. **Design taste** (bespoke, motion-rich, finance-math feel; refined across **several logged
iterations**; passes Taste pre-flight + impeccable critique). 5. **Mathematical credibility** (equations,
derivations, citations, and live graphs shown — never decorative; provenance + OOS honesty surfaced
inline; `/math` reconciles with the tearsheet). 6. **Accessibility & instant access** (no login, fast,
a11y-clean, the math is *shown*).

## Universe (default)
Cross-asset ETFs, ~2007→present daily (spans 2008 GFC, 2020 COVID, 2022 selloff):
`SPY, QQQ, EFA, EEM, AGG, TLT, LQD, HYG, VNQ, GLD, DBC`.

## Build verification (end-to-end)
- **Engine:** `uv run pytest -q` green (unit + Hypothesis); `uv run argmin backtest …` emits figures +
  `tearsheet.csv`; metrics cross-checked vs quantstats; offline re-run is byte-stable.
- **API:** `/optimize`, `/backtest`, `/frontier` return typed, finite results; OpenAPI loads.
- **Web:** loads instantly with the default scenario; custom runs animate live; every listed
  equation + chart renders animated; passes Taste hard pre-flight + impeccable critique scoring;
  Playwright a11y/contrast green at 375/768/1440px; deploys to a public Vercel URL **with no login**.
```

## PART 5 — Build Checklist (resolve every item during the build)

These are gaps/decisions the spec above leaves implicit. Every box must be ticked before the
project is considered done — treat this as the master TODO for the build.

**Reproducibility & data**
- [ ] **Freeze the data snapshot.** Commit the Parquet cache (or a hashed snapshot manifest) as the
      single source of truth; offline re-runs read the cache and **never** re-fetch yfinance. This is
      what makes "byte-stable offline re-run" actually true.
- [ ] **Total-return basis stated & implemented:** adjusted close, dividends reinvested.
- [ ] **Panel alignment rule for unequal ETF inception dates** (e.g. common-start ≈ latest inception,
      or per-asset with explicit NaN handling). Document the chosen rule; assert it in a test.
- [ ] **Point-in-time / no look-ahead guarantee:** estimators and rebalances use only data with
      `date ≤ as_of`; add a test that fails on any look-ahead leak.

**Numerical correctness**
- [ ] **Define the risk-free rate** explicitly (constant vs. T-bill series e.g. `^IRX`/DGS3MO). Put it
      in `config/default.yaml`, surface it in the API, and use it consistently across Max-Sharpe,
      Sharpe, Sortino, PSR/DSR.
- [ ] **Define the constraint schema** for `/optimize` `{constraints}`: long-only (`w≥0`), fully
      invested (`Σw=1`), optional per-asset max-weight / box bounds, optional leverage cap. Validate
      via pydantic; document defaults per model.
- [ ] **Benchmarks bear transaction costs** (1/N and 60/40 rebalancing pay the same bps×turnover) — or
      explicitly mark them frictionless. State and implement which.

**Public engine safety & ops (no-login live endpoint)**
- [ ] **Universe whitelist:** `/optimize`, `/backtest`, `/frontier` validate `universe` against a
      curated allowlist; reject arbitrary tickers (no unbounded yfinance calls via stranger input).
- [ ] **Backtest complexity caps:** bound years, asset count, and models-per-request so a single live
      run can't exceed the serverless timeout; return a clear "too heavy" error past the cap.
- [ ] **Typed API error contract:** documented error responses for validation failures, timeouts, and
      upstream-data errors (not just the happy path).
- [ ] **Cache key includes an engine-version hash** so logic changes invalidate stale cached results.
- [ ] **Lock CORS to the deployed web origin in production** (no `*`); engine has its own rate limit if
      hosted separately.

**Contract integrity & repo polish**
- [ ] **Generate TS types from the published OpenAPI** (`openapi-typescript`) so the web↔engine
      contract can't silently drift; wire it into CI.
- [ ] **`LICENSE` file** committed.
- [ ] **README** with the "why this isn't the clichéd in-sample frontier" hook, a demo GIF/screenshots,
      the live URL, and a one-command quickstart for both `engine/` and `web/`.
- [ ] **"Not investment advice" disclaimer** in the web footer and README (DIY-investor persona).
