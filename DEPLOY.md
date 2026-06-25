# Deploying Argmin

Two pieces, two hosts:

- **Web** (`web/`) → **Vercel** (free Hobby tier — $0).
- **Engine** (`engine/`) → a **container host** (Fly.io recommended). The engine
  is ~1.7 GB installed (polars' Rust runtime + scipy/sklearn/cvxpy), well over
  Vercel Python's **250 MB** function limit, so it runs as a warm container.
  Fly.io with **scale-to-zero** is the cheapest "real engine": the machine stops
  when idle and wakes on the next request (~2-5 s), so you pay cents, not for a
  24/7 box.

The container image (`engine/Dockerfile`) is host-agnostic — the same image runs
on Fly, Render, or Railway. It binds `0.0.0.0:${PORT:-8000}`.

---

## 1. Engine → Fly.io

```bash
# one-time: install + log in (interactive — in Claude Code, prefix with `! `)
curl -L https://fly.io/install.sh | sh
fly auth login

cd engine
fly launch --no-deploy --copy-config --name argmin-engine   # pick your own name
fly deploy                                                   # builds Dockerfile, pushes

fly status            # note the URL, e.g. https://argmin-engine.fly.dev
curl https://argmin-engine.fly.dev/healthz                   # → {"status":"ok",...}
```

CORS is locked **after** you know the web URL (step 3):

```bash
fly secrets set ARGMIN_CORS_ALLOW_ORIGINS="https://<your-web>.vercel.app"
```

Scale-to-zero is already configured in `fly.toml` (`min_machines_running = 0`,
`auto_stop_machines = "stop"`). Memory is `1gb` (scipy/cvxpy working set).

### Alternative: Render (hard $0, slower wake)

New → **Web Service** → repo, **Root Directory** `engine`, Runtime **Docker**.
Render injects `$PORT` (the CMD honors it). Set env `ARGMIN_CORS_ALLOW_ORIGINS`.
Free instances sleep after 15 min (~30-60 s cold start) and have a monthly hour cap.

---

## 2. Web → Vercel

Project settings:

- **Root Directory:** `web`
- **Framework:** Next.js (auto-detected)
- **Environment variables:**
  - `API_BASE_URL` = `https://argmin-engine.fly.dev` (server-side proxy target;
    never exposed to the browser)
  - `NEXT_PUBLIC_SITE_URL` = `https://<your-web>.vercel.app` (for `metadataBase`)

```bash
# CLI path
npm i -g vercel
cd web
vercel link
vercel env add API_BASE_URL production          # paste the Fly URL
vercel env add NEXT_PUBLIC_SITE_URL production   # paste the Vercel URL
vercel --prod
```

The site works even if the engine is asleep/down: it first-paints from the
committed `default_scenario.json`, and live "Run" buttons degrade gracefully to
the last good result with an "engine unreachable" note.

---

## 3. Lock CORS + verify

1. `fly secrets set ARGMIN_CORS_ALLOW_ORIGINS="https://<your-web>.vercel.app"`
2. Open the Vercel URL → `/explore` → **Run optimize** / **Run backtest**.
   Confirm `200`s in the Network tab and the charts update.
3. Confirm a cross-origin request from any *other* origin is rejected (CORS).

---

## Cost summary (low-traffic portfolio piece)

| Piece | Host | Cost |
|---|---|---|
| Web | Vercel Hobby | $0 |
| Engine | Fly.io, scale-to-zero | ~$0-1/mo (idle ≈ $0) |
| Engine (alt) | Render free | $0 (sleeps, ~50 s cold start) |

## Reproducibility note

The image bakes the committed `engine/data/cache/prices.parquet` snapshot — the
engine never live-fetches market data at runtime. A logic change bumps
`engine_hash`, which invalidates the in-memory response cache automatically.
