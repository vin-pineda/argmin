# Project Status — Argmin

> Pick-up-where-we-left-off doc. Read this first at the start of a session; update it at the end.
> Full plan: [project_spec.md](./project_spec.md). Working agreements: [CLAUDE.md](./CLAUDE.md).

**Last updated:** 2026-06-22

---

## Where we left off
- **Phase:** **MVP complete** — full engine (M0–M5) **and** web v1 (M6 SHAPE + M7 CRAFT). The agreed
  MVP scope (engine + a real bespoke front-end, excluding the ≥3-iteration design loop M8–M9 and
  Vercel deploy M10) is done and verified end-to-end.
- **Engine:** data → estimators → 7 optimizers → walk-forward backtest → analytics/significance →
  FastAPI + CLI. Green: ruff + mypy --strict (31 files) + pytest **122 passed, 1 skipped**.
- **Web (`web/`):** Next.js 16 (App Router) + Tailwind v4 + visx + KaTeX + Remotion + TanStack Query.
  Three routes — `/` (Remotion intro, honest OOS result strip, 7-model bench), `/explore` (live
  cockpit: control panel + frontier/equity/drawdown/rolling-Sharpe/weights/risk-contrib charts +
  tearsheet + PSR/DSR + bootstrap), `/math` (KaTeX derivations, citations, Ledoit-Wolf heatmap, HRP
  dendrogram, reconciliation). Dark "terminal-meets-research-paper" design system. Instant first
  paint from the committed `default_scenario.json`; live runs proxy to the engine. TS types generated
  from `engine/openapi.json`. Verified: `tsc` + `eslint` + `next build` clean; live `/api/optimize`
  + `/api/frontier` round-trip 200; 0 console errors; responsive 375/1440; Playwright-checked.
- **Local dev:** engine on **:8008** (`:8000` was occupied), web on **:3000**. `web/.env.local` points
  the proxy at 8008.

## Next up
1. **M8 — CRITIQUE.** Run the ≥3-iteration CRAFT→CRITIQUE→POLISH loop: impeccable `/critique` scorecard,
   persona tests, Playwright a11y/contrast suite at 375/768/1440, Taste hard pre-flight. Log iterations
   in `web/design/iterations/LOG.md`.
2. **M9 — POLISH.** Emil micro-interactions, Core Web Vitals budget, full keyboard/AX, reduced-motion.
3. **M10 — Deploy.** Web → Vercel; engine → Vercel Python / Fly.io. Lock CORS to the deployed origin.
4. Minor: center the `/math` covariance heatmap in its panel; tighten hero vertical rhythm.

---

## Milestone status
Legend: `[ ]` not started · `[~]` in progress · `[x]` done

**Engine track**
- [x] **M0** — Foundation & Identity (uv build, CI, pydantic config, data loader → Parquet/DuckDB)
- [x] **M1** — Estimators + core optimizers + frontier (Ledoit-Wolf, Min-Var, Max-Sharpe, frontier)
- [x] **M2** — Advanced models (Risk Parity/ERC, HRP, Max-Diversification, Black-Litterman)
- [x] **M3** — Walk-forward backtest engine (rebalancing, tx-costs, benchmarks, joblib-parallel)
- [x] **M4** — Analytics & significance (tearsheet, PSR/DSR, bootstrap CIs vs quantstats)
- [x] **M5** — Engine API (FastAPI `/optimize` `/backtest` `/frontier` `/healthz`, OpenAPI) + CLI + CI

**Front-end / design track**
- [x] **M6** — SHAPE (design brief in `web/design/brief.md` + design read/dials)
- [x] **M7** — CRAFT v1 (dark token system, visx charts on live engine, KaTeX math, Remotion intro,
      no-login instant-try; `tsc`+`eslint`+`next build` green)
- [~] **M8** — CRITIQUE/POLISH de-slop pass done: typography overhaul (STIX Two Text serif +
      Plex Mono, Geist removed) + box-language rework (tinted pills/eyebrows/chips → hairline
      tags, status dots, serif titles, `§NN` markers). Playwright-tested every function at
      375/768/1440; `next build` clean. Remaining: persona scorecard + a11y/contrast sweep.
- [ ] **M9** — POLISH (micro-interactions, Core Web Vitals, keyboard/AX, reduced-motion)
- [ ] **M10** — Deploy & stretch (live on Vercel, engine deployed; stretch goals)

## Build Checklist status
All 16 items in **[project_spec.md PART 5](./project_spec.md)** are open. They're decisions baked into
the engine/config/API, so they get resolved inside the relevant milestone (mostly M0–M5), not as a
separate pass.

## Open decisions / assumptions to confirm
- **Risk-free rate** — RESOLVED: constant, configurable in `config/default.yaml` (`risk_free.annual_rate`,
  default 2%), surfaced in the API/provenance. T-bill series is a stretch.
- **Web package manager** — RESOLVED: **pnpm** (Next.js 16, React 19, Tailwind v4).
- **Engine hosting:** Vercel Python (Fluid Compute) vs. separate Fly.io/Railway service — decide at M10.

---

## Tooling (MCP servers & skills)
- **MCP servers (all user/global scope, connected):** `magic` (21st), `playwright`, `shadcn` registry,
  `plugin:vercel:vercel`, `claude_design`. `shadcn` added 2026-06-22; the rest pre-existed.
- **Skills (global):** `impeccable`, `design-taste-frontend` (+`-v1` fallback), `emil-design-eng`,
  `remotion-best-practices`, `shadcn` — all present.
- **`frontend-design` DISABLED for this project** via `.claude/settings.json` (plugin off +
  skillOverride off). Note: takes effect next `claude` session / config reload; the new `shadcn` MCP is
  likewise available next session.

## Session log
- **2026-06-22 (M9 cont.: deeper de-slop)** — Stripped the remaining "tasteful-AI-dark" tells the
  user kept reacting to: removed the graph-paper grid motif everywhere (+ its CSS), the eyebrow
  kicker over every section (+ the `Eyebrow` primitive; reconciliation/honesty use `§NN`),
  decorative button/tile glows, and the pulsing "live" dot ping. De-duplicated an aphoristic copy
  tail; removed dead `src/remotion/*`. Quieter editorial/academic feel. 0 console errors (normal +
  reduced motion), no overflow at 390, `next build` clean, dev fresh on :3000.
- **2026-06-22 (M9 cont.: unified frontier graphic)** — Extracted the hero efficient-frontier
  into a shared responsive `components/charts/frontier-viz.tsx` used by BOTH the landing hero and
  the Explore frontier panel (identical design: curve + area, tangent CML, min-var/tangency,
  comet). Explore additionally plots the currently optimized portfolio as a pulsing marker that
  glides to its position on each optimize (responds to the run). Removed old `hero-frontier.tsx`
  + unused visx `FrontierChart`. 0 console errors, no overflow at 390, `next build` clean.
- **2026-06-22 (M9 motion: scroll overhaul, Explore-focused)** — Made the cockpit + overview
  feel alive on scroll. Explore: every panel opens up on scroll (Framer `Reveal`); the visx
  charts draw/grow in as you reach them (equity/frontier/rolling/drawdown via `motion.path`
  pathLength; risk bars grow + morph on re-run); tearsheet + header metrics tween on re-run.
  Overview: result strip headline/table open up on scroll (thesis/gallery/CTA/math already do).
  Removed dead reveal CSS. Verified: scroll-through reveals all charts (opacity 1), re-run
  200s + bars morph, 0 console errors, no overflow at 390, `next build` clean, dev fresh on :3000.
- **2026-06-22 (M8 page-by-page polish, round 2)** — "Keep iterating until perfect," page by page.
  Fixed the reported **landing hero graph not showing**: replaced the blank/fragile Remotion
  `<Player>` with `HeroFrontier` (always-visible efficient-frontier SVG from real geometry, CSS
  draw-on, reduced-motion aware). Rebalanced the model gallery bento (no empty cells). Centered +
  widened the methodology figures (heatmap/dendrogram/bootstrap) via a two-measure layout (≤68ch
  prose + centered figures); de-uppercased the dendrogram axis label. Fixed a **reduced-motion
  hydration mismatch** (→ `<MotionConfig reducedMotion="user">`, consistent initial state in
  Reveal/Hero/Derivation). Fixed a **mobile `/math` horizontal overflow** (heatmap legend now
  wraps). Restarted the dev server clean after an earlier `next build` had staled its CSS compile.
  Verified: 0 console errors on all 3 routes; no overflow at 375/768/1440; live optimize/backtest
  200; `next build` clean. Engine untouched.
- **2026-06-22 (M8 de-slop: type + boxes)** — Reworked the web visual system to kill the
  "AI slop" feel per user direction ("most mathematical feeling"). Dropped **Geist Sans**;
  introduced a two-voice system — **STIX Two Text** serif (document: headlines/prose/titles,
  harmonizes with the KaTeX equations) + **IBM Plex Mono** (apparatus: nav/buttons/labels/data).
  De-slopped the boxes: tinted amber pill badges → hairline tags + amber status dots;
  uppercase-mono eyebrows → sentence-case serif panel titles; amber-fill ticker chips → mono
  tokens w/ status dots; amber-fill chosen/selected row highlights → subtle elevated + dot;
  methodology section markers → paper-style `§NN`. Amber kept only as ink/markers/active states.
  Authored `PRODUCT.md` + `DESIGN.md` (root) and `web/design/iterations/LOG.md`. Playwright-
  verified every user function (6 optimizers, optimize/backtest, universe toggle + min-2 guard,
  sliders, rebalance, log toggle, derivation + cov-heatmap toggles) across 375/768/1440 with no
  overflow; live engine round-trips 200; 0 console errors; `next build` clean. Engine untouched.
- **2026-06-22 (M6–M7 / web v1)** — Built the entire web app in `web/`. Scaffolded Next.js 16
  (App Router, TS, Tailwind v4, pnpm); installed Motion, visx, KaTeX, TanStack Query, Zustand, Radix,
  Phosphor, Remotion. Authored the design brief (`web/design/brief.md`) + a dark "terminal-meets-
  research-paper" token system (`globals.css`), UI primitives, shell (nav/footer w/ "not investment
  advice"). Baked `default_scenario.json` for instant paint + generated TS types from
  `engine/openapi.json` (openapi-typescript) + `math-extras.json` (sample/shrunk correlation + HRP
  tree). Built three routes via parallel sub-agents: `/` (Remotion intro + honest result strip +
  7-model bench), `/explore` (live cockpit, 6 visx charts + tearsheet + significance, wired to the
  engine via same-origin `/api/*` proxy routes), `/math` (KaTeX derivations, citations, Ledoit-Wolf
  heatmap, HRP dendrogram, bootstrap CI, reconciliation, limitations). Verified with Playwright:
  `tsc`+`eslint`+`next build` clean, live optimize/frontier round-trip 200, 0 console errors,
  responsive at 375/1440. Enabled the web CI job. Engine ran on :8008 locally (:8000 taken).
- **2026-06-22 (M5)** — Built the engine HTTP service + CLI + CI. Added `engine/src/argmin/api/`
  (`models.py` wire contract, `service.py` pure request→engine mapping, `app.py` FastAPI with lifespan
  panel load, universe whitelist, `max_assets`/`max_years` complexity caps, CORS from settings, in-memory
  TTL response cache keyed by engine_hash, per-IP sliding-window rate limit, typed `ErrorResponse`
  exception handlers). Extended `cli.py` with `backtest` (tearsheet.csv + 4 PNGs, Agg backend),
  `default-scenario` (reuses `service.py` so JSON == API shape), and `openapi` (dumps schema for web TS
  types). Added `.github/workflows/ci.yml` (engine job: ruff + ruff format --check + mypy + pytest on the
  committed snapshot, no network; commented web-job stub). Added `tests/test_api.py` (7 tests). Full
  suite: 122 passed, 1 skipped; ruff + mypy --strict clean.
- **2026-06-22** — Drafted `.env.example` (engine + web, no-DB/no-auth by design). Added **PART 5 Build
  Checklist** to `project_spec.md` (16 items covering reproducibility, numerical correctness, public
  endpoint safety, repo polish). Created `CLAUDE.md` and this `project_status.md`. Made magic/Playwright
  MCP usage directive in spec + CLAUDE.md. Installed `shadcn` registry MCP (user scope); created
  `.claude/settings.json` disabling `frontend-design`. No code yet.
