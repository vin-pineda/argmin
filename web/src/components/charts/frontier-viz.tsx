"use client";

import { ParentSize } from "@visx/responsive";
import { motion } from "motion/react";

import { cn } from "@/lib/cn";
import type { FrontierResult } from "@/lib/api/types";

const MARK_EASE = [0.16, 1, 0.3, 1] as const;

/**
 * The efficient-frontier graphic — one shared design used by both the landing
 * hero and the Explore cockpit (so they are identical). Real engine geometry:
 *   • the frontier curve (dim) + soft area fill,
 *   • a constantly-traveling "comet" highlight running min-var → tangency,
 *   • the Capital Market Line, tangent at the max-Sharpe (tangency) portfolio,
 *   • pulsing min-var + tangency markers.
 * Responsive: fills whatever box it's given (visx ParentSize), so the same
 * component looks right in the tall hero box and the wide cockpit panel.
 *
 * On Explore we additionally pass `portfolio` — the *currently optimized*
 * portfolio — which is plotted as a pulsing marker, so the graph visibly
 * responds to each optimize run.
 */

export interface FrontierPortfolioMark {
  vol: number;
  ret: number;
  label: string;
}

function FrontierVizInner({
  width,
  height,
  data,
  portfolio,
}: {
  width: number;
  height: number;
  data: FrontierResult;
  portfolio?: FrontierPortfolioMark | null;
}) {
  const rf = data.provenance?.risk_free ?? 0.02;
  const M = { top: 16, right: 62, bottom: 30, left: 54 };
  const innerW = Math.max(0, width - M.left - M.right);
  const innerH = Math.max(0, height - M.top - M.bottom);

  const fp = data.frontier_points;

  // Horizontal extent is set by the efficient frontier + markers, NOT the full
  // random cloud: a few high-vol cloud outliers were stretching the x-axis and
  // leaving the right side of the plot empty. The frontier now spans the width.
  const keyVols = [
    ...fp.map((p) => p.vol),
    data.tangency.exp_vol,
    data.min_var.exp_vol,
    ...(portfolio ? [portfolio.vol] : []),
  ];
  const vMin = Math.min(...keyVols);
  const vMax = Math.max(...keyVols);
  const vPad = (vMax - vMin) * 0.06 || 0.01;
  const domVMin = vMin - vPad;
  const domVMax = vMax + vPad;

  // cloud: subsampled, then clipped to the horizontal domain so outliers neither
  // stretch the axis nor draw outside the plot.
  const cloud = data.random_cloud.vol
    .map((v, i) => ({ v, r: data.random_cloud.ret[i] }))
    .filter((_, i) => i % 3 === 0)
    .filter((p) => p.v >= domVMin && p.v <= domVMax);

  // Vertical extent from the frontier + markers + the *visible* cloud + rf.
  const keyRets = [
    ...fp.map((p) => p.ret),
    data.tangency.exp_return,
    data.min_var.exp_return,
    ...(portfolio ? [portfolio.ret] : []),
    ...cloud.map((p) => p.r),
    rf,
  ];
  const rMin = Math.min(...keyRets);
  const rMax = Math.max(...keyRets);
  const rPad = (rMax - rMin) * 0.1 || 0.01;
  const dom = { vMin: domVMin, vMax: domVMax, rMin: rMin - rPad, rMax: rMax + rPad };
  const sx = (v: number) => ((v - dom.vMin) / (dom.vMax - dom.vMin)) * innerW;
  const sy = (r: number) => innerH - ((r - dom.rMin) / (dom.rMax - dom.rMin)) * innerH;

  if (innerW <= 0 || innerH <= 0) return null;

  const toPath = (pts: { vol: number; ret: number }[]) =>
    pts.map((p, i) => `${i === 0 ? "M" : "L"}${sx(p.vol).toFixed(1)},${sy(p.ret).toFixed(1)}`).join(" ");

  const fullCurve = toPath(fp);

  const upToTan = fp.filter((p) => p.vol <= data.tangency.exp_vol + 1e-9);
  if (
    upToTan.length === 0 ||
    Math.abs(upToTan[upToTan.length - 1].vol - data.tangency.exp_vol) > 1e-6
  ) {
    upToTan.push({ vol: data.tangency.exp_vol, ret: data.tangency.exp_return, sharpe: data.tangency.sharpe });
  }
  const highlightPath = toPath(upToTan);

  const slope = (data.tangency.exp_return - rf) / data.tangency.exp_vol;
  const cmlV0 = dom.vMin;
  const cmlV1 = Math.min(data.tangency.exp_vol * 1.22, dom.vMax);
  const cml = { x1: sx(cmlV0), y1: sy(rf + slope * cmlV0), x2: sx(cmlV1), y2: sy(rf + slope * cmlV1) };

  const tan = { x: sx(data.tangency.exp_vol), y: sy(data.tangency.exp_return) };
  const mv = { x: sx(data.min_var.exp_vol), y: sy(data.min_var.exp_return) };
  const rfY = sy(rf);
  const pf = portfolio ? { x: sx(portfolio.vol), y: sy(portfolio.ret) } : null;

  const axisFont = "var(--font-plex-mono)";

  return (
    <svg
      width={width}
      height={height}
      role="img"
      aria-label="Efficient frontier with the capital market line tangent at the maximum-Sharpe portfolio."
      className="hero-frontier"
    >
      <defs>
        <linearGradient id="fv-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--color-accent)" stopOpacity="0.16" />
          <stop offset="100%" stopColor="var(--color-accent)" stopOpacity="0" />
        </linearGradient>
      </defs>

      <g transform={`translate(${M.left},${M.top})`}>
        {/* axes */}
        <line x1={0} y1={0} x2={0} y2={innerH} stroke="var(--color-line-strong)" strokeWidth={1} />
        <line x1={0} y1={innerH} x2={innerW} y2={innerH} stroke="var(--color-line-strong)" strokeWidth={1} />
        <text x={-12} y={4} textAnchor="end" fill="var(--color-fg-faint)" fontSize={12} fontFamily={axisFont}>return</text>
        <text x={innerW} y={innerH + 22} textAnchor="end" fill="var(--color-fg-faint)" fontSize={12} fontFamily={axisFont}>risk (vol)</text>

        {/* risk-free anchor */}
        <line x1={-4} y1={rfY} x2={4} y2={rfY} stroke="var(--color-fg-faint)" strokeWidth={1} />
        <text x={-12} y={rfY + 4} textAnchor="end" fill="var(--color-fg-faint)" fontSize={10.5} fontFamily={axisFont}>r_f</text>

        {/* random cloud */}
        <g className="hf-cloud">
          {cloud.map((p, i) => (
            <circle key={i} cx={sx(p.v)} cy={sy(p.r)} r={1.7} fill="var(--color-fg-faint)" fillOpacity={0.3} />
          ))}
        </g>

        {/* Capital Market Line — tangent at the tangency point */}
        <line className="hf-cml" x1={cml.x1} y1={cml.y1} x2={cml.x2} y2={cml.y2} stroke="var(--color-series-minvar)" strokeWidth={1.4} strokeDasharray="5 5" strokeOpacity={0.7} />
        <text x={cml.x2 + 6} y={cml.y2 + 2} fill="var(--color-series-minvar)" fontSize={11} fontFamily={axisFont} opacity={0.85}>CML</text>

        {/* soft area under the frontier */}
        <path className="hf-area" d={`${fullCurve} L${sx(fp[fp.length - 1].vol).toFixed(1)},${innerH.toFixed(1)} L${sx(fp[0].vol).toFixed(1)},${innerH.toFixed(1)} Z`} fill="url(#fv-fill)" />

        {/* frontier curve (dim base) */}
        <path className="hf-curve" d={fullCurve} pathLength={1} fill="none" stroke="var(--color-accent)" strokeOpacity={0.4} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />

        {/* traveling comet highlight: min-var → tangency, looping */}
        <path className="hf-comet-glow" d={highlightPath} pathLength={1} fill="none" stroke="var(--color-accent-bright)" strokeWidth={7} strokeOpacity={0.18} strokeLinecap="round" strokeLinejoin="round" />
        <path className="hf-comet" d={highlightPath} pathLength={1} fill="none" stroke="var(--color-accent-bright)" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" />

        {/* min-variance marker */}
        <g className="hf-mark hf-mark-mv">
          <circle cx={mv.x} cy={mv.y} r={4.5} fill="var(--color-series-minvar)" stroke="var(--color-bg)" strokeWidth={1.5} />
          <text x={mv.x + 10} y={mv.y + 16} fill="var(--color-series-minvar)" fontSize={12} fontFamily={axisFont}>min-var</text>
        </g>

        {/* tangency marker */}
        <g className="hf-mark hf-mark-tan">
          <circle className="hf-pulse" cx={tan.x} cy={tan.y} r={7} fill="none" stroke="var(--color-accent)" strokeWidth={1.25} />
          <circle cx={tan.x} cy={tan.y} r={6} fill="var(--color-accent-bright)" stroke="var(--color-bg)" strokeWidth={1.5} />
          <text x={tan.x - 13} y={tan.y - 14} textAnchor="end" fill="var(--color-accent)" fontSize={12.5} fontFamily={axisFont}>tangency</text>
        </g>

        {/* the currently optimized portfolio (Explore only) — pulses, and glides
            to its new spot on every optimize so the graph responds to the run */}
        {pf ? (
          <motion.g
            className="hf-mark hf-mark-pf"
            initial={{ x: pf.x, y: pf.y }}
            animate={{ x: pf.x, y: pf.y }}
            transition={{ duration: 0.7, ease: MARK_EASE }}
          >
            <circle className="hf-pulse" cx={0} cy={0} r={8} fill="none" stroke="var(--color-fg)" strokeWidth={1.25} />
            <circle cx={0} cy={0} r={5.5} fill="var(--color-fg)" stroke="var(--color-bg)" strokeWidth={1.5} />
            <circle cx={0} cy={0} r={2.4} fill="var(--color-accent)" />
            <text x={11} y={15} fill="var(--color-fg)" fontSize={12} fontFamily={axisFont}>
              {portfolio?.label}
            </text>
          </motion.g>
        ) : null}
      </g>
    </svg>
  );
}

export function FrontierViz({
  data,
  portfolio,
  className,
}: {
  data: FrontierResult;
  portfolio?: FrontierPortfolioMark | null;
  className?: string;
}) {
  return (
    <div className={cn("h-full w-full", className)}>
      <ParentSize>
        {({ width, height }) =>
          width > 0 && height > 0 ? (
            <FrontierVizInner width={width} height={height} data={data} portfolio={portfolio} />
          ) : null
        }
      </ParentSize>
    </div>
  );
}
