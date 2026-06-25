# Argmin web — de-slop iteration log

Goal: remove the "AI slop" feel (Geist Sans, tinted-pill badges, uppercase-mono
eyebrow-on-every-panel, identical bordered card grid) while keeping the IA. Direction the
user chose: **"the most mathematical feeling."** → a typeset-paper system: **STIX Two Text**
serif (built for scientific/mathematical publishing, harmonizes with the KaTeX/Computer
Modern equations) for the *document*; **IBM Plex Mono** for the *apparatus*. One amber
signal, used as ink/markers/active-states only — never as decorative fills. See
`/DESIGN.md`, `/PRODUCT.md`.

Method per pass: change with the impeccable methodology → Playwright test the affected user
functions across 375/768/1440 → screenshot → verify engine round-trips + clean console →
fix. Type duality rule that emerged: **you read in serif, you act in mono.**

---

## 1 — Type foundation
Dropped Geist Sans entirely. Base body + headings → STIX serif (16px/1.6, balanced wrap,
-0.012em heading tracking, lining figures). Mono retained for data. tsc+eslint clean.

## 2 — Box language (primitives)
`Badge`: amber tinted pill → hairline tag + optional amber status dot. `PanelHeader`:
uppercase-mono eyebrow → sentence-case serif title + mono hint. `Eyebrow`: amber uppercase
tracked → quiet hairline rule + mono kicker. `Stat`: mono label.

## 3 — Landing
Hero: serif title + italic second line, dotted OOS tag, 16px serif lede. Result strip:
chosen row amber fill → subtle `bg-elevated/50` + amber status dot + "chosen" tag. Model
gallery tags → quiet mono (was amber uppercase). Tested `/` @1440: reads as a paper.

## 4 — Cockpit (`/explore`)
Field labels off uppercase; ticker pills (amber fill) → mono tokens with amber/grey status
dots; provenance + error + log labels de-uppercased. **Live tests:** Max Sharpe & Min
Variance optimize → `/api/optimize`+`/api/frontier` 200, risk-contrib + σ update correctly
(Min Var σ→7.1%, lowest). Universe toggle → grey/amber dots, counter, min-2 guard. Backtest
→ `/api/backtest` 200, tearsheet/equity/drawdown/rolling/weights update. Log switch toggles
log axis. Method dropdown popover clean. Slider (keyboard + click) updates value. 0 console
errors.

## 5 — Methodology (`/math`)
Section markers → paper-style `§NN`; figcaptions + derivation toggles de-uppercased; honesty
card titles → serif. KaTeX symbols now sit inside serif prose as one typeset document.
**Tests:** derivation disclosure toggles; covariance heatmap Sample↔Shrunk toggle re-renders.

## 6 — Type duality
Committed fully: nav links, buttons, field labels → mono (the apparatus); titles + prose →
serif (the document). Sharper hierarchy, coherent "research terminal" top bar.

## 7 — Breakpoints + build
375 / 768 / 1440: no horizontal overflow on any route. Production `next build` clean (no
GeistSans/reference errors); dev server verified serving the serif with 0 errors.

---

## Kept deliberately (not slop)
- Amber-filled primary buttons + active segmented toggles (brief: amber = active states).
- Uppercase **short** mono table column heads (CAGR/Vol/…): a real tabular convention, ≤4
  words — within the allowed uppercase usage, reads as data not as an eyebrow.
- Hairline-framed chart panels: figure containers in a paper, not generic cards. Format kept
  per the user ("the format is fine").

## Follow-ups (optional)
- `geist` is still an (unused) dependency in `web/package.json` — safe to drop on next install.
- `remotion` / `@remotion/player` are now unused (hero no longer uses the Player); the
  `web/src/remotion/*` files are dead code that can be removed on a later cleanup.

---

# Round 2 — page-by-page, "keep iterating until perfect" (≥10 passes)

User flagged the landing "overview graph" not showing. Worked page by page fixing load +
spacing/placement. Each pass Playwright-tested at the relevant breakpoints.

## 1 — Landing hero graph (the reported bug)
Root cause: the hero used a Remotion `<Player autoPlay loop>` that rendered **blank** (fragile
runtime; also hid the frontier for most of the loop). Replaced with `HeroFrontier`, a
self-contained always-visible SVG built from real engine geometry (frontier curve + random
cloud + min-var + tangency + axes), CSS stroke-dash draw-on, reduced-motion aware. Always
loads; no Player runtime.

## 2 — Landing model gallery rebalanced
Feature tiles were full-width with content only on the left (big empty bands) and a dead
`justify-between` gap. Rebalanced to a clean asymmetric bento (`[MaxSharpe·2][Frontier·1]` /
3-equal / `[HRP·2][BL·1]`, no empty cells) and grouped tile content at the top.

## 3 — Landing thesis / CTA / footer reviewed — spacing reads as editorial; no changes.

## 4 — Explore verified: all 6 charts have geometry loaded; live optimize/backtest 200; OK.

## 5 — Methodology figures centered + widened
Charts were capped inside the 68ch prose column (narrow, left-aligned, big right gap). Added a
two-measure layout: prose stays ≤68ch (readable), figures get `.fig` (centered, wider). Heatmap
640 / dendrogram 860 / bootstrap 720, all centered. Resolves the old "center the heatmap" note.
De-uppercased the dendrogram "linkage distance" axis label.

## 6 — Significance / reconciliation / honesty reviewed (bootstrap now centered; OK).

## INFRA — dev-server CSS had gone stale
New globals.css rules (`.model-prose`, `.fig`) weren't compiling — the earlier production
`next build` had polluted the shared `.next`. Killed the dev server, cleared `.next`, restarted
clean. CSS then compiled correctly.

## 7 — Mobile (375) sweep + overflow fix
Hero graph shows on mobile; gallery stacks. Found + fixed a real horizontal overflow on `/math`:
the covariance-heatmap legend (`-1 [gradient] +1`) didn't wrap — added `flex-wrap` to its header.

## 8 — Tablet (768) sweep — no overflow on any route.

## 9 — Reduced motion: fixed a hydration mismatch
`useReducedMotion()` branching made SSR (non-reduced) ≠ client (reduced) → React hydration
error. Switched to `<MotionConfig reducedMotion="user">` with a single consistent initial
state (removed the branches in `Reveal`, `Hero`, `Derivation`). Reduced-motion now renders
fully with 0 console errors.

## 10 — Final clean-console pass: `/`, `/explore`, `/math` → 0 errors each.

## 11 — Full functional smoke + production build
Live Risk-Parity optimize + backtest → `frontier/optimize/backtest` all 200. `next build`
clean (all routes). Dev server restarted clean afterward so the local environment still works.

---

# Round 4 — motion overhaul ("insane, premium, alive") + graph fixes + LinkedIn

User asks: bigger constantly-animated hero graph (done R3); fix comet stutter + tangency
label colliding with lines; LinkedIn (not GitHub) top-right; scroll-triggered "open up"
everywhere; constant motion on important things; premium/alive feel.

## 1 — Nav: GitHub → LinkedIn
Top-right icon is now LinkedIn (`linkedin.com/in/vincent-pineda8`), amber hover + lift.

## 2 — Hero comet stutter fixed
The loop wasn't seamless (dashoffset traveled 1.16 periods then jumped) AND the glow used an
SVG `feGaussianBlur` that re-rasterized every frame. Fix: dash sums to the normalized
pathLength and the keyframe shifts exactly one period (1→0) = seamless; replaced the blurred
glow with a wide low-opacity stroke (no filter) = smooth.

## 3 — Tangency label no longer runs into lines
Moved the "tangency" label up-and-left (textAnchor end) into open space, clear of the CML
(rises up-right) and the curve. Fixed the risk-free axis label (`rₑ` → `r_f`).

## 4 — Scroll-triggered reveals ("open up on scroll")
Rewrote `Reveal` to a smooth whileInView open-up (opacity + slide + slight scale, transform/
opacity only so it stays buttery; no blur to avoid jank). Content stays in the DOM
(accessible/indexable); MotionConfig handles reduced motion; consistent SSR/client initial =
no hydration mismatch. Verified: sections sit hidden until scrolled, then animate to opacity 1.

## 5 — Reveals applied across the narrative
Methodology: every `ModelSection` (header / equation figure / prose) opens up staggered on
scroll; the notation+contents grid, honesty cards (staggered), and references too. Landing
thesis/gallery/CTA already use `Reveal` → now scroll-triggered.

## 6 — Constant motion on "important" elements
Hero: comet travels min-var→tangency forever + tangency pulse. OOS-only status dots now do a
gentle radar "live" ping (`.live-dot`) on every page. Significance metrics tween on re-run.

## 7 — Verify
0 console errors on `/`, `/explore`, `/math` (normal + reduced motion). No mobile overflow at
390 on any route. Scroll reveals fire (landing gallery/CTA + math sections → opacity 1 on
scroll). `next build` clean; dev restarted clean. Comet smooth (no filter), seamless loop.

---

# Round 5 — scroll + animation overhaul, focused on Explore

## 1 — Explore panels open up on scroll
Every cockpit panel (provenance, frontier/risk row, equity, drawdown/rolling row, weights,
tearsheet, significance) is wrapped in the Framer `Reveal` — they fade + slide + scale in as
they enter the viewport (replaced the load-only `chart-rise`, now removed with its dead CSS).

## 2 — Charts draw/grow in (scroll-triggered)
Converted visx line/area charts to `motion.path` with `whileInView` pathLength draw-on:
**equity** (each strategy line, chosen last), **frontier** curve, **rolling Sharpe**, **drawdown**
(line draws + area fades). **Risk-contribution bars** use `animate` width so they grow on mount
AND smoothly morph to new widths on every re-run. Charts are client-only (visx ParentSize), so
no SSR/hydration concerns.

## 3 — Live numbers in the cockpit
`AnimatedNumber` now tweens the **tearsheet** cells and the panel-header metrics (tan Sharpe, σ)
on every re-run, alongside the significance panel.

## 4 — Overview scroll polish
Result strip headline + table now open up on scroll (Reveal). (Thesis / gallery / CTA / math
already scroll-reveal from round 4.)

## 5 — Cleanup + verify
Removed dead `.reveal-up` / `.chart-rise` / `rise-in` CSS. Verified: scroll through `/explore`
→ all 6 charts draw on and reach opacity 1; re-run optimize+backtest → frontier/optimize/
backtest 200, bars morph, 0 console errors, no overflow; `next build` clean; dev restarted clean.

---

# Round 6 — unify the frontier graph (landing == explore)

User: make the Explore efficient-frontier identical to the landing one, but have the Explore
one respond more to the optimize.

## 1 — Shared `FrontierViz`
Extracted the hero graph into `components/charts/frontier-viz.tsx` — one responsive component
(visx ParentSize) used by BOTH the landing hero and the Explore frontier panel, so the design
is identical: amber curve + area fill, dashed teal CML tangent at the max-Sharpe point, r_f
anchor, min-var + tangency markers, the looping comet. Removed the old `hero-frontier.tsx` and
the now-dead visx `frontier.tsx` (`FrontierChart`).

## 2 — Explore responds to the optimize
On Explore, `FrontierViz` also takes `portfolio` = the currently optimized portfolio
(`optimize.exp_vol/return` + method label). It's drawn as a pulsing white/amber marker that
**glides to its new position on every optimize** (Framer-animated `translate`); the frontier
re-draws when the universe changes (keyed by universe). Verified: Max Sharpe → marker sits on
the tangency; Min Variance → marker glides down onto the min-var point; labels + σ update.

## 3 — Verify
Landing hero + Explore frontier render the identical design; explore marker tracks the optimize
(optimize/frontier 200). 0 console errors on all routes; no overflow at 390; `next build` clean;
dev restarted clean on :3000.

---

# Round 7 — deeper de-slop (kill the remaining "tasteful-AI-dark" tells)

User still felt the *feel* was AI-slop. Per the impeccable second-order category-reflex check,
"terminal-dark + editorial-serif + warm accent + graph-paper + glows + pulsing dots" IS the
current tasteful-AI family. Kept the mathematical core; stripped the tells:

- **Graph-paper motif removed everywhere** — section/hero/CTA/explore backgrounds, gallery
  feature tiles, the thesis equation box, and the heatmap/dendrogram chart frames. Deleted the
  `.graph-paper` / `.graph-paper-fine` CSS. (It was a data-product cliché.)
- **Eyebrows removed** — the kicker over every section ("Interactive", "Out-of-sample result",
  "The objective", "Seven models…", "Methodology", "References"). Serif headlines now carry.
  Deleted the `Eyebrow` primitive. Reconciliation/honesty use the paper `§NN` marker (kept,
  legitimate sequence).
- **Decorative glows removed** — primary-button hover glow + model-tile hover glow (kept subtle
  lifts).
- **Pulsing "live" dot removed** — the OOS-only radar ping (a dashboard cliché); the dot is now
  static. Deleted `.live-dot` CSS.
- **Copy tic** — dropped the duplicated aphoristic "…honestly." tail on the CTA headline.
- **Dead code** — removed the unused `src/remotion/*` (replaced by FrontierViz) and the unused
  visx frontier chart earlier.

Verified: 0 console errors on `/`, `/explore`, `/math` (normal + reduced motion); no overflow at
390; `next build` clean; dev restarted clean. Result: quieter, editorial/academic feel — less
"AI dark dashboard," more "typeset research note."

---

# Round 8 — frontier "spans the space" + a11y/UX audit pass

## 1 — Frontier graph fills its plot
A few high-vol random-cloud outliers were stretching the x-axis, leaving the right ~40% of the
plot empty. `FrontierViz` now sets the horizontal domain from the **efficient frontier + markers**
(not the full cloud) and clips out-of-domain cloud points; vertical domain uses the visible cloud.
Both the hero and Explore frontier now span their boxes (curve arcs corner-to-corner, area fills).

## 2 — Audit-driven UI fixes (impeccable `audit` + Web Interface Guidelines lens)
Ran a Playwright audit (tap targets, accessible names, heading order) and fixed the real issues:
- **Contrast:** `--color-fg-faint` was #5f636c (~3.3:1 on bg — fails AA for the small labels/
  captions/axis ticks that use it). Bumped to #7c818b (~4.9:1) while staying dimmer than fg-dim.
- **Heading hierarchy:** Explore jumped H1→H3 (panel titles were h3 with no h2). `PanelHeader`
  now renders `h2`; Explore is H1→H2 throughout, math stays consistent (h2 sections, h3 cards).
- **Tap targets:** mobile ticker chips were 28px tall; bumped to a 32px min-height (more
  comfortable; already WCAG 2.2-compliant). No missing accessible names found.
- **Layout:** the Notation panel had dead bottom space (stretched to the taller Contents panel);
  the grid is now `items-start` so each sizes naturally.

Verified: 0 console errors (normal + reduced motion) and no overflow on all 3 routes at
1440/390; Explore headings H1→H2 (no skip); `next build` clean; dev restarted clean on :3000.
