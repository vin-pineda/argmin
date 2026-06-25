# Argmin — Design Brief (M6 / SHAPE)

> The discovery artifact for the front-end. Anchors the CRAFT build and every
> later critique pass. Source aesthetic seed: project_spec.md §2.3.

## Design read
Reading this as a **quant-research landing + interactive explorer** for **recruiters,
quant reviewers, and curious DIY investors**, with a **Bloomberg-terminal-meets-editorial-
research-paper** language, leaning toward **Tailwind v4 + Geist Sans / IBM Plex Mono**, a
**dark-locked** theme, **one restrained amber signal accent**, and **data-dense** layouts.

## Dials
- **DESIGN_VARIANCE: 6** — structured grids with deliberate asymmetry; not chaotic. Data
  must read as precise and trustworthy.
- **MOTION_INTENSITY: 5** — motion is *motivated*: the Remotion intro (argmin operator +
  frontier trace), chart enter transitions, KaTeX reveal-on-scroll, value transitions on
  re-run. Everything honors `prefers-reduced-motion`.
- **VISUAL_DENSITY: 7** — cockpit-leaning. Hairline rules instead of cards where possible,
  monospaced tabular numerics, generous spacing *around* dense data blocks.

## Audience & jobs
1. **Recruiter / hiring manager** — needs to grasp depth + taste in 20 seconds: a credible
   headline result, honest framing, obvious engineering maturity.
2. **Quant reviewer** — needs to trace each method to its math + citation, confirm OOS
   honesty (costs, benchmarks, significance), and see numbers reconcile.
3. **DIY investor** — lands, sees a real diversified portfolio constructed + explained, with
   zero signup.

## Voice
Precise, declarative, honest. No hype verbs ("elevate", "seamless", "unleash"). State what the
engine does and what the numbers mean. Surface limitations openly (OOS-only badge, "not
investment advice").

## Aesthetic system
- **Theme:** dark-locked. `bg #0a0b0d`, panels `#0d0f12`, hairlines `rgba(255,255,255,.08)`.
- **Accent:** a single amber signal `#e6a94d` — used for the chosen strategy, the tangency
  point, primary CTAs, active states. Benchmarks render in cool/muted hues so the strategy
  pops. The accent never changes mid-page (Color Consistency Lock).
- **Type:** Geist Sans for prose + headlines; IBM Plex Mono for all numerics, labels, axes,
  equations context. Tabular numerics everywhere data appears.
- **Motifs:** graph-paper grid backdrop, hairline frames, equations as first-class
  typographic objects (KaTeX), provenance shown inline near the numbers.
- **Shape:** near-sharp corners (radius 4px), consistent across the page.

## Routes (block library)
- **`/` Overview** — Remotion intro → hero (the argmin thesis) → headline OOS result strip
  (chosen strategy vs 1/N / 60/40 / SPY) → "why naive in-sample frontiers lie" narrative →
  the 7-model gallery → CTA to Explore.
- **`/explore`** — control panel (universe, method, rebalance, cost bps, max-weight) bound to
  the precomputed default scenario for instant paint; **Run** calls the live engine. Charts:
  efficient frontier (+ random cloud, tangency, min-var), equity curves, underwater drawdown,
  rolling Sharpe, weights over time, risk contributions, tearsheet table, PSR/DSR + bootstrap.
- **`/math` Methodology** — each model's objective in KaTeX with a "show derivation"
  affordance, literature citations inline (Markowitz 1952, Ledoit-Wolf 2004, Black-Litterman
  1992, López de Prado 2016, Bailey & López de Prado 2014), covariance shrinkage heatmap, HRP
  dendrogram, and an honesty/limitations section. Numbers reconcile with the tearsheet.

## Honesty surfaces (non-negotiable)
OOS-only badge, data window, rebalance rule, cost (bps), risk-free source, and the
engine-version hash sit *visibly near the numbers*, not in a footnote. Benchmarks bear the
same transaction costs. "Not investment advice" in the footer.

## Anti-slop guardrails (from the taste pre-flight)
Zero em-dashes; one accent; dark theme locked across all sections; eyebrows rationed; mono
numerics; no fake-precise invented stats (every number binds to live engine output); real
data only; reduced-motion fallback; WCAG AA contrast on all text and controls.
