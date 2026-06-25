# Design

## Theme
Dark-locked, "quant research note typeset in a journal, meets a terminal." No section
inverts. Near-sharp corners (4px). Hairline rules and a faint graph-paper grid are the
structural motif; boxed panels are used only where dense data needs a container.

## Typography (the de-slop core)
Two voices, no generic sans:

- **Serif — `--font-serif` = STIX Two Text.** Headlines, hero, all prose, section titles,
  derivation text. STIX is built for scientific/mathematical publishing and sits next to
  Computer Modern (what KaTeX renders), so the page reads as one typeset document.
- **Mono — `--font-mono` = IBM Plex Mono.** Every numeric, axis tick, ticker, label,
  provenance value, table cell, and control. Tabular figures everywhere data appears
  (`.tnum`). This is the "computation/terminal" voice.
- **Geist Sans: removed.** It was the primary AI tell.

Rules: headline tracking no tighter than -0.02em (serifs don't want it); body 16px / ~1.6;
line length capped ~70ch; uppercase reserved for short mono labels only, never prose.
Hierarchy via serif weight + scale contrast, not via more families.

## Color
- `--color-bg #0a0b0d`, `--color-panel #0d0f12`, `--color-elevated #14171c`.
- Hairlines `rgba(255,255,255,.08)` / strong `.14`; grid `.035`.
- Ink: `--color-fg #e8eaed`, dim `#969ba4`, faint `#5f636c`.
- **One signal accent — amber `#e6a94d`.** Used as ink and markers (chosen strategy,
  tangency point, primary CTA, active nav) — *not* as decorative tinted fills. The old
  `bg-accent-soft` pill/chip/row fills are removed; emphasis comes from accent ink, a
  filled status dot, or a hairline tag.
- Semantics: pos `#5bbf86`, neg `#e0655b`. Chart series: strategy = amber, benchmarks
  cool/muted so the strategy reads first.

## Components (box language, de-slopped)
- **Panel** — hairline-framed surface, used sparingly. No drop-shadow + border pairing.
- **SectionLabel** (replaces the uppercase mono eyebrow) — sentence-case serif title with
  an optional hint and a hairline rule. One deliberate label per region, not an eyebrow on
  every block.
- **Tag** (replaces tinted Badge) — hairline border, mono, no fill; or a leading status
  dot + plain label (e.g. `● OOS-only`). Amber only as the dot/ink.
- **Ticker tokens** — mono cells in a hairline grid; selected = accent ink + filled dot,
  not an amber background. Echoed as a set `{ SPY, QQQ, … }` where it reads naturally.
- **Buttons** — primary = solid amber on bg; outline = hairline; no border+softshadow combo.
- **Equations** — KaTeX, first-class, inheriting `--color-fg`; meaningful equation/section
  numbering only (it is a paper), never `01/02/03` scaffolding on every section.

## Motion
Motivated only: Remotion intro (argmin operator + frontier trace), chart enter transitions,
value transitions on re-run, KaTeX reveal-on-scroll. Ease-out (expo/quart), no bounce.
Every animation has a `prefers-reduced-motion: reduce` fallback.

## Layout
Max width 1400px, 20px gutters. Explore = sticky control rail + responsive chart grid.
Verified at 375 / 768 / 1440px with no horizontal overflow.
