# Project Status — Argmin

> Pick-up-where-we-left-off doc. Read this first at the start of a session; update it at the end.
> Full plan: [project_spec.md](./project_spec.md). Working agreements: [CLAUDE.md](./CLAUDE.md).

**Last updated:** 2026-06-25

---

## Where we left off
- **Phase:** **M8 + M9 complete; M10 deploy artifacts built + validated, awaiting account-gated push.**
  The engine (M0–M5) and web (M6–M9) are done and verified; the deploy is prepared (container image
  builds + serves locally) and just needs the interactive Fly/Vercel logins to go live.
- **M8 critique + M9 polish (this session):** Playwright-swept all 3 routes at 375/768/1440 — detector
  clean, WCAG-AA contrast clean, controls labeled + keyboard-reachable, live optimize/frontier 200.
  Added an Explore `aria-live` results announcer, a skip-to-content link, defensive nav sizing (killed a
  2 px overflow at 375). Reduced-motion verified (0 errors, static hero, no hydration mismatch). Pruned
  unused `remotion`/`@remotion/player`. `tsc` + `eslint` + `next build` clean.
- **M10 deploy decision (resolved):** the engine is **too heavy for Vercel Python** (~1.7 GB installed;
  even trimmed it's 349 MB vs the 250 MB function limit). It ships as a **container** instead. Built
  `engine/Dockerfile` + `.dockerignore` + `fly.toml` (Fly.io scale-to-zero, cheapest live engine), ran
  the image locally (healthz/optimize/frontier all 200), wrote `DEPLOY.md`. Web → Vercel (free).
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
1. **M10 — Execute the deploy** (account-gated, see `DEPLOY.md`):
   a. Engine → Fly.io: `cd engine && fly auth login && fly launch --no-deploy --copy-config && fly deploy`.
   b. Web → Vercel: root dir `web`, set `API_BASE_URL` (Fly URL) + `NEXT_PUBLIC_SITE_URL`, `vercel --prod`
      (or drive via the Vercel MCP — account already connected).
   c. Lock CORS: `fly secrets set ARGMIN_CORS_ALLOW_ORIGINS="https://<web>.vercel.app"`; verify a live
      optimize/backtest round-trips 200 from the Vercel origin.
2. Minor: center the `/math` covariance heatmap in its panel; tighten hero vertical rhythm.

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
- [x] **M8** — CRITIQUE done: de-slop pass (STIX serif + Plex Mono; hairline tags / status dots /
      `§NN`) + Playwright a11y/contrast/persona sweep at 375/768/1440 (detector clean, AA contrast
      clean, controls labeled). Fixes: `aria-live` results announcer, skip link, nav overflow.
- [x] **M9** — POLISH done: keyboard/AX (skip link + Radix + focus-visible + live regions),
      reduced-motion verified (0 errors, static hero), micro-interactions tasteful, CWV (static
      prerender, self-hosted fonts, pruned unused remotion). `tsc`+`eslint`+`next build` clean.
- [~] **M10** — Deploy: **artifacts built + validated** (Dockerfile/fly.toml; image serves locally).
      Remaining = the account-gated push (Fly login + deploy, Vercel web deploy, CORS lock).

## Build Checklist status
All 16 items in **[project_spec.md PART 5](./project_spec.md)** are open. They're decisions baked into
the engine/config/API, so they get resolved inside the relevant milestone (mostly M0–M5), not as a
separate pass.

## Open decisions / assumptions to confirm
- **Risk-free rate** — RESOLVED: constant, configurable in `config/default.yaml` (`risk_free.annual_rate`,
  default 2%), surfaced in the API/provenance. T-bill series is a stretch.
- **Web package manager** — RESOLVED: **pnpm** (Next.js 16, React 19, Tailwind v4).
- **Engine hosting** — RESOLVED at M10: **container host (Fly.io, scale-to-zero)**, NOT Vercel Python.
  The engine (~1.7 GB installed; polars Rust runtime + scipy/sklearn/cvxpy) exceeds Vercel's 250 MB
  function limit even trimmed (349 MB). Container = no size limit, warm process for CPU-heavy backtests,
  ~$0 idle via scale-to-zero. Same image runs on Render/Railway. See `DEPLOY.md`.

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
- **2026-06-25 (M8 + M9 finished; M10 deploy prepped)** — Ran the impeccable `critique` methodology
  (driven directly, single-agent) with a Playwright sweep of `/`, `/explore`, `/math` at 375/768/1440:
  de-slop detector clean (0), WCAG-AA contrast clean on all routes, every control labeled + keyboard-
  reachable (Radix), live `/api/optimize`+`/api/frontier` round-trip 200. Verdict ≈ 34/40 — strong;
  findings were a short polish list, not breakage. Applied: an Explore `aria-live="polite"` results
  announcer (run progress + return/vol/Sharpe + chosen strategy/MaxDD for screen readers), a skip-to-
  content link (first focusable, lands focus in `<main>`), and defensive nav sizing (removed a 2 px
  overflow at 375). Verified reduced-motion under emulation: 0 console errors across all routes, hero
  frontier resolves to its static fully-drawn state, no hydration mismatch. Pruned unused
  `remotion`/`@remotion/player` (hero uses the HeroFrontier SVG). `tsc`+`eslint`+`next build` clean.
  **M10:** measured the engine at ~1.7 GB installed (349 MB even trimmed) vs Vercel Python's 250 MB
  limit → resolved hosting to a **container** (Fly.io scale-to-zero, cheapest live engine per the user's
  cost ask). Wrote `engine/Dockerfile` (runs from source so `engine_root()` resolves; honors `$PORT`),
  `.dockerignore`, `fly.toml`; built + ran the image — healthz/optimize/frontier all 200. Authored
  `DEPLOY.md`, updated `.env.example`, `DESIGN.md` (grid/fg-faint drift), `CHANGELOG.md`. Remaining =
  the account-gated push (Fly login, Vercel web deploy, CORS lock).
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
