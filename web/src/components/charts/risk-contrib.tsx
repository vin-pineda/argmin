"use client";

import { AxisBottom } from "@visx/axis";
import { GridColumns } from "@visx/grid";
import { Group } from "@visx/group";
import { scaleBand, scaleLinear } from "@visx/scale";
import { motion } from "motion/react";
import { useMemo } from "react";

const BAR_EASE = [0.16, 1, 0.3, 1] as const;

import { ChartFrame, CHART, tickLabelProps, type ChartDims } from "./frame";
import type { OptimizeResult } from "@/lib/api/types";
import { pct } from "@/lib/format";

const M = { top: 10, right: 48, bottom: 34, left: 44 };

interface Row {
  ticker: string;
  value: number;
}

function RiskContribInner({
  width,
  height,
  result,
}: ChartDims & { result: OptimizeResult }) {
  const innerW = Math.max(0, width - M.left - M.right);
  const innerH = Math.max(0, height - M.top - M.bottom);

  const rows: Row[] = useMemo(
    () =>
      result.tickers
        .map((t) => ({ ticker: t, value: result.risk_contrib[t] ?? 0 }))
        .sort((a, b) => b.value - a.value),
    [result],
  );

  const { yScale, xScale } = useMemo(() => {
    const maxV = Math.max(0.001, ...rows.map((r) => r.value));
    return {
      yScale: scaleBand<string>({
        domain: rows.map((r) => r.ticker),
        range: [0, innerH],
        padding: 0.22,
      }),
      xScale: scaleLinear<number>({ domain: [0, maxV * 1.08], range: [0, innerW] }),
    };
  }, [rows, innerW, innerH]);

  if (innerW <= 0 || innerH <= 0) return null;

  return (
    <svg width={width} height={height} aria-label="Risk contribution per asset">
      <Group left={M.left} top={M.top}>
        <GridColumns scale={xScale} width={innerW} height={innerH} stroke={CHART.gridStroke} />

        {rows.map((r, i) => {
          const y = yScale(r.ticker) ?? 0;
          const bw = Math.max(0, xScale(r.value));
          const h = yScale.bandwidth();
          return (
            <Group key={r.ticker}>
              <text
                x={-8}
                y={y + h / 2}
                textAnchor="end"
                dominantBaseline="middle"
                fill="var(--color-fg-dim)"
                fontSize={10}
                fontFamily="var(--font-plex-mono)"
              >
                {r.ticker}
              </text>
              {/* bar grows in on mount and morphs to the new width on every re-run */}
              <motion.rect
                x={0}
                y={y}
                height={h}
                fill="var(--color-accent)"
                fillOpacity={0.85}
                rx={1}
                initial={{ width: 0 }}
                animate={{ width: bw }}
                transition={{ duration: 0.8, ease: BAR_EASE, delay: Math.min(i, 8) * 0.03 }}
              />
              <text
                x={bw + 6}
                y={y + h / 2}
                dominantBaseline="middle"
                fill="var(--color-fg)"
                fontSize={10}
                fontFamily="var(--font-plex-mono)"
                className="tnum"
              >
                {pct(r.value, 1)}
              </text>
            </Group>
          );
        })}

        <AxisBottom
          top={innerH}
          scale={xScale}
          stroke={CHART.axisStroke}
          tickStroke={CHART.axisStroke}
          numTicks={5}
          tickFormat={(v) => pct(Number(v), 0)}
          tickLabelProps={tickLabelProps}
          label="Risk contribution (% of total)"
          labelProps={{
            fill: CHART.labelColor,
            fontSize: 11,
            fontFamily: "var(--font-plex-mono)",
            textAnchor: "middle",
          }}
          labelOffset={18}
        />
      </Group>
    </svg>
  );
}

export function RiskContribChart({
  result,
  height = 280,
}: {
  result: OptimizeResult;
  height?: number;
}) {
  return (
    <ChartFrame height={height}>
      {(dims) => <RiskContribInner {...dims} result={result} />}
    </ChartFrame>
  );
}
