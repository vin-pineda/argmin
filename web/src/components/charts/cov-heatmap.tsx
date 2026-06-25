"use client";

import { Group } from "@visx/group";
import { scaleBand } from "@visx/scale";
import { useState } from "react";

import { ChartFrame, tickLabelProps } from "@/components/charts/frame";
import { Button } from "@/components/ui/button";
import { num } from "@/lib/format";

/** Diverging color for a correlation value in [-1, 1].
 *  Negative -> cool slate, zero -> neutral panel, positive -> amber (the one accent). */
function corrColor(rho: number): string {
  const t = Math.max(-1, Math.min(1, rho));
  if (t >= 0) {
    // 0 -> faint, 1 -> amber. Lift lightness with magnitude.
    const a = 0.06 + 0.82 * t;
    return `rgba(230, 169, 77, ${a.toFixed(3)})`;
  }
  // 0 -> faint, -1 -> cool slate-blue.
  const a = 0.06 + 0.7 * -t;
  return `rgba(107, 143, 184, ${a.toFixed(3)})`;
}

type Matrix = number[][];

function Heatmap({
  matrix,
  tickers,
  width,
  height,
}: {
  matrix: Matrix;
  tickers: string[];
  width: number;
  height: number;
}) {
  const margin = { top: 6, right: 6, bottom: 22, left: 34 };
  const innerW = Math.max(0, width - margin.left - margin.right);
  const innerH = Math.max(0, height - margin.top - margin.bottom);
  const side = Math.min(innerW, innerH);

  const scale = scaleBand<number>({
    domain: tickers.map((_, i) => i),
    range: [0, side],
    padding: 0.04,
  });
  const cell = scale.bandwidth();

  return (
    <svg width={width} height={height} role="img" aria-label="Correlation matrix heatmap">
      <Group left={margin.left} top={margin.top}>
        {matrix.map((row, i) =>
          row.map((rho, j) => {
            const x = scale(j) ?? 0;
            const y = scale(i) ?? 0;
            return (
              <rect
                key={`${i}-${j}`}
                x={x}
                y={y}
                width={cell}
                height={cell}
                fill={corrColor(rho)}
                stroke="var(--color-bg)"
                strokeWidth={0.5}
              >
                <title>{`${tickers[i]} / ${tickers[j]}: ${num(rho, 3)}`}</title>
              </rect>
            );
          }),
        )}
        {/* Column labels (bottom) */}
        {tickers.map((t, j) => (
          <text
            key={`col-${t}`}
            x={(scale(j) ?? 0) + cell / 2}
            y={side + 14}
            textAnchor="middle"
            {...tickLabelProps()}
          >
            {t}
          </text>
        ))}
        {/* Row labels (left) */}
        {tickers.map((t, i) => (
          <text
            key={`row-${t}`}
            x={-8}
            y={(scale(i) ?? 0) + cell / 2}
            textAnchor="end"
            dominantBaseline="middle"
            {...tickLabelProps()}
          >
            {t}
          </text>
        ))}
      </Group>
    </svg>
  );
}

/** Compact diverging legend: -1 ... 0 ... +1. */
function Legend() {
  const stops = [-1, -0.5, 0, 0.5, 1];
  return (
    <div className="flex items-center gap-2">
      <span className="font-mono text-[10px] text-fg-faint tnum">-1</span>
      <div className="flex h-2.5 overflow-hidden rounded-[2px] border border-line">
        {stops.flatMap((s, idx) =>
          idx === stops.length - 1
            ? []
            : Array.from({ length: 12 }, (_, k) => {
                const rho = s + (k / 12) * (stops[idx + 1] - s);
                return (
                  <div
                    key={`${idx}-${k}`}
                    className="h-full w-1.5"
                    style={{ background: corrColor(rho) }}
                  />
                );
              }),
        )}
      </div>
      <span className="font-mono text-[10px] text-fg-faint tnum">+1</span>
    </div>
  );
}

export function CovHeatmap({
  sample,
  shrunk,
  tickers,
  delta,
}: {
  sample: number[][];
  shrunk: number[][];
  tickers: string[];
  delta: number;
}) {
  const [view, setView] = useState<"sample" | "shrunk">("sample");
  const matrix = view === "sample" ? sample : shrunk;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-2">
        <div
          role="tablist"
          aria-label="Correlation estimator"
          className="inline-flex rounded-[var(--radius)] border border-line p-0.5"
        >
          <Button
            role="tab"
            aria-selected={view === "sample"}
            variant={view === "sample" ? "primary" : "ghost"}
            size="sm"
            onClick={() => setView("sample")}
          >
            Sample S
          </Button>
          <Button
            role="tab"
            aria-selected={view === "shrunk"}
            variant={view === "shrunk" ? "primary" : "ghost"}
            size="sm"
            onClick={() => setView("shrunk")}
          >
            Shrunk &Sigma;&#770;
          </Button>
        </div>
        <Legend />
      </div>

      <ChartFrame height={340} className="rounded-[var(--radius)] border border-line">
        {({ width, height }) => (
          <Heatmap matrix={matrix} tickers={tickers} width={width} height={height} />
        )}
      </ChartFrame>

      <p className="text-[12px] leading-relaxed text-fg-faint">
        Correlation of the {tickers.length}-asset universe. The{" "}
        <span className="text-fg-dim">sample</span> estimate is noisy in its off-diagonal
        entries; Ledoit-Wolf pulls every entry toward the structured target by intensity{" "}
        <span className="tnum text-fg-dim">&delta; = {num(delta, 4)}</span>, shrinking
        extreme correlations toward the average. A low <span className="tnum">&delta;</span>{" "}
        here signals the sample matrix is already well conditioned over this window.
      </p>
    </div>
  );
}
