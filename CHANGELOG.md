# Changelog

All notable changes to Argmin are recorded here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); the project is pre-1.0.

## [Unreleased]

### M8–M10 — Critique, polish, deploy prep (2026-06-25)
- **M8 critique (Playwright-driven).** Swept `/`, `/explore`, `/math` at 375/768/1440. Deterministic
  de-slop detector clean (0 findings); WCAG-AA contrast clean on all routes; every control labeled and
  keyboard-reachable (Radix); primary action verified live (`/api/optimize` + `/api/frontier` → 200).
- **A11y fixes.** Added an `aria-live="polite"` status region to Explore that announces run progress and
  the resulting numbers (return/vol/Sharpe, chosen strategy + max drawdown) for screen-reader users; a
  skip-to-content link as the first focusable element; defensive nav sizing that removes a ~2 px
  horizontal overflow at 375 px.
- **M9 polish.** Reduced-motion verified under emulation (0 console errors across all routes; hero
  frontier resolves to its static fully-drawn state — no hydration mismatch). Pruned the unused
  `remotion` + `@remotion/player` deps (the hero uses the `HeroFrontier` SVG now), trimming install/CWV
  surface. `tsc` + `eslint` + `next build` all clean.
- **M10 deploy prep.** Determined the engine (~1.7 GB installed; polars Rust runtime + scipy/sklearn/
  cvxpy) exceeds Vercel Python's 250 MB function limit, so it ships as a **container** instead. Added
  `engine/Dockerfile` (runs from source so `engine_root()` path resolution holds; honors `$PORT`),
  `engine/.dockerignore`, and `engine/fly.toml` (Fly.io scale-to-zero — cheapest "real engine"). Built
  + ran the image locally: `healthz`/`optimize`/`frontier` all 200. Added `DEPLOY.md` runbook and
  production env notes. Web → Vercel (free); CORS locks to the deployed origin via
  `ARGMIN_CORS_ALLOW_ORIGINS`.

### Added — Engine (M0–M5)
- **M0 Foundation.** `uv` project (Python 3.12), pydantic config (`ArgminConfig` + env `Settings`),
  structlog. Data layer: yfinance → Polars → Parquet/DuckDB; frozen price snapshot of the 11-ETF
  default universe (committed, the reproducibility source of truth) with a hashed manifest;
  common-start aligned daily returns panel; no-look-ahead `lookback` primitive. `git init`, `LICENSE`,
  `.env.example`.
- **M1 Estimators + core optimizers.** μ (sample / EWMA / CAPM), Σ (sample / Ledoit-Wolf / EWMA) with a
  shrinkage-intensity accessor. Min-Variance, Max-Sharpe (homogeneous convex reformulation), and the
  efficient frontier + random cloud, from scratch in CVXPY. Property + closed-form + oracle tests.
- **M2 Advanced optimizers.** Risk Parity / ERC (Spinu log-barrier, equal-risk-contribution verified),
  Hierarchical Risk Parity (corr → distance → linkage → quasi-diagonalization → recursive bisection),
  Max-Diversification, Black-Litterman (implied equilibrium π → posterior; collapses to π with no views).
- **M3 Walk-forward backtest.** Monthly rebalance, 3-year rolling window, transaction costs (bps ×
  turnover) on strategies and benchmarks (1/N, 60/40, SPY), joblib-parallel weight computation,
  deterministic, no look-ahead.
- **M4 Analytics & significance.** Full tearsheet (return, vol, Sharpe, Sortino, MaxDD, Calmar,
  VaR/CVaR, turnover), Probabilistic & Deflated Sharpe, block-bootstrap Sharpe CIs; cross-checked vs
  `quantstats`.
- **M5 API + CLI + CI.** FastAPI `/optimize` `/backtest` `/frontier` `/healthz` with typed pydantic
  models, universe whitelist, complexity caps, CORS lock, in-memory TTL cache keyed by engine hash,
  per-IP rate limit, typed error contract, OpenAPI. CLI `snapshot` / `info` / `backtest` /
  `default-scenario` / `openapi`. GitHub Actions CI (ruff + ruff format + mypy --strict + pytest).
  Suite: 122 passed, 1 skipped.

### Added — Web (M6 SHAPE + M7 CRAFT v1)
- Design brief (`web/design/brief.md`) and a dark "Bloomberg-terminal-meets-research-paper" design
  system (Tailwind v4 tokens, hairline rules, graph-paper grid, mono tabular numerics, one amber accent).
- Next.js 16 App Router app with three routes: `/` (Remotion cinematic intro, honest OOS result strip,
  seven-model bench), `/explore` (live cockpit: control panel + efficient-frontier / equity / drawdown /
  rolling-Sharpe / weights / risk-contribution visx charts + tearsheet + PSR/DSR + bootstrap), `/math`
  (KaTeX objectives and derivations, literature citations, Ledoit-Wolf shrinkage heatmap, HRP dendrogram,
  bootstrap CI, tearsheet reconciliation, limitations).
- No-login instant first paint from a committed `default_scenario.json`; live runs proxy to the engine
  via same-origin `/api/*` route handlers. TS types generated from the engine OpenAPI schema.
- Web CI job (lint + typecheck + build). Verified responsive at 375/1440, 0 console errors.

### Changed — Web (M8 de-slop pass: typography + box language)
- **Typography overhaul ("most mathematical feeling").** Removed Geist Sans (the primary AI
  tell). New two-voice system: **STIX Two Text** serif for the document (headlines, prose,
  section titles) — it's built for scientific/mathematical publishing and harmonizes with the
  KaTeX/Computer Modern equations so the page reads as one typeset paper — and **IBM Plex Mono**
  for the apparatus (nav, buttons, labels, data, controls). Rule: read in serif, act in mono.
- **De-slopped the "highlighted boxes."** Tinted amber pill badges → hairline tags with an amber
  status dot. Uppercase-mono eyebrow-on-every-panel → sentence-case serif panel titles. Amber-
  filled ticker chips → mono tokens with amber/grey status dots. Amber-fill "chosen"/selected
  row highlights → subtle `bg-elevated` + status dot. Methodology section markers → paper-style
  `§NN`. Amber retained only as ink, markers, and active states (buttons, segmented toggles).
- `PRODUCT.md` + `DESIGN.md` authored at repo root; iteration log at `web/design/iterations/LOG.md`.
- Verified with Playwright: every interactive function (6 optimizers, optimize/backtest, universe
  toggle + min-2 guard, sliders, rebalance, log scale, derivation + heatmap toggles) across
  375/768/1440 with no overflow; engine round-trips 200; 0 console errors; `next build` clean.

### Fixed — Web (M8 page-by-page polish)
- **Landing hero graph rendered blank.** Replaced the fragile autoplay/loop Remotion `<Player>`
  with `HeroFrontier` — an always-visible SVG of the efficient frontier (curve + random cloud +
  min-var + tangency) from real engine geometry, with a CSS draw-on and reduced-motion fallback.
- **Hydration mismatch under reduced motion.** Removed `useReducedMotion()` render branching
  (SSR≠client) in favor of `<MotionConfig reducedMotion="user">` with one consistent initial
  state (Reveal, Hero, Derivation). Reduced-motion renders fully, 0 console errors.
- **Mobile overflow on `/math`.** The covariance-heatmap legend didn't wrap; added `flex-wrap`.
  No horizontal overflow now on any route at 375/768/1440.
- **Methodology figures** were narrow/left-aligned inside the prose column; introduced a two-measure
  layout (readable ≤68ch prose, centered wider figures). Heatmap/dendrogram/bootstrap now centered
  (resolves the old "center the heatmap" note). De-uppercased the dendrogram axis label.
- **Model gallery** rebalanced into a clean asymmetric bento (no empty cells, content top-aligned).

### Changed — Web (motion overhaul + hero graph)
- **Hero graph** rebuilt: larger, with a constantly-traveling comet highlight running min-var →
  tangency, a pulsing tangency marker, an area fill, and the **Capital Market Line** (straight,
  tangent at the max-Sharpe point — touches the curve only there, never crosses it).
- **Fixed the comet stutter** (seamless one-period dash loop; removed a per-frame SVG blur
  filter) and the **tangency label colliding with the lines** (repositioned into open space;
  corrected the `r_f` axis label).
- **Scroll-triggered "open up" reveals** across the landing and methodology (sections, equation
  figures, prose, honesty cards, references) via a smooth transform+opacity `Reveal`; content
  stays in the DOM and reduced motion is honored (no hydration mismatch).
- **Constant + interactive motion:** OOS-only status dots ping ("live"); significance metrics
  tween on re-run (`AnimatedNumber`); buttons/tiles/chips lift + glow on hover; explore panels
  stagger in.
- **Nav:** top-right link is now **LinkedIn** (`/in/vincent-pineda8`), not GitHub.

### Changed — Web (scroll + animation overhaul, Explore-focused)
- **Explore cockpit opens up on scroll:** every panel (frontier/risk, equity, drawdown/rolling,
  weights, tearsheet, significance) reveals (fade + slide + scale) as it enters the viewport.
- **Charts draw/grow in** as you reach them: equity lines, frontier curve, rolling-Sharpe, and
  drawdown draw on via `motion.path` pathLength; the drawdown area fades; **risk-contribution
  bars grow and morph** to new widths on every re-run.
- **Live cockpit numbers:** tearsheet cells and panel-header metrics (tan Sharpe, σ) tween on
  re-run (`AnimatedNumber`).
- **Overview:** the headline result strip + table now open up on scroll.
- Removed dead reveal/stagger CSS (replaced by the Framer `Reveal`).

### Changed — Web (unified efficient-frontier graphic)
- The Explore efficient-frontier panel now uses the **same design as the landing hero** — a
  single responsive `FrontierViz` component (curve + area, tangent CML, min-var/tangency markers,
  comet) shared by both pages.
- On Explore it additionally plots the **currently optimized portfolio** as a pulsing marker that
  glides to its new position on every optimize (Max Sharpe → tangency; Min Variance → min-var; etc.),
  so the graph visibly responds to the run. Removed the old `hero-frontier.tsx` and the unused
  visx `FrontierChart`.

### Changed — Web (deeper de-slop: remove the "tasteful-AI-dark" tells)
- Removed the **graph-paper grid** motif everywhere (backgrounds, hero/CTA/explore, feature tiles,
  equation box, heatmap/dendrogram frames) and deleted its CSS.
- Removed the **eyebrow kicker over every section**; serif headlines carry. Reconciliation/honesty
  keep the paper `§NN` marker. Deleted the `Eyebrow` primitive.
- Removed **decorative glows** (button/tile hover shadows) and the **pulsing "live" dot** ping
  (static dot now).
- Dropped a duplicated aphoristic copy tail; removed dead `src/remotion/*`.
- Net effect: a quieter, editorial/academic feel — less generic dark dashboard.

### Fixed — Web (frontier spanning + accessibility/UX audit)
- **Frontier graph now spans its plot.** High-vol random-cloud outliers were stretching the
  x-axis; `FrontierViz` sets the horizontal domain from the frontier + markers and clips the
  outliers, so the curve/area fill the box (hero + Explore).
- **Contrast:** raised `--color-fg-faint` to ~4.9:1 on the background (was ~3.3:1, failing AA for
  small labels/captions/axis ticks).
- **Heading hierarchy:** `PanelHeader` renders `h2` (Explore no longer skips H1→H3).
- **Tap targets:** mobile ticker chips bumped to a 32px min-height.
- **Layout:** the methodology Notation/Contents panels size naturally (`items-start`), removing
  dead space under Notation.

### Notes
- Optimizers are implemented from scratch; `PyPortfolioOpt` / `quantstats` are test oracles only.
- Out of scope for this MVP: the ≥3-iteration CRITIQUE→POLISH design loop (M8–M9) and Vercel deploy (M10).
