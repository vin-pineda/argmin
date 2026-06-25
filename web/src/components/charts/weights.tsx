"use client";

import { AxisBottom, AxisLeft } from "@visx/axis";
import { Group } from "@visx/group";
import { AreaClosed } from "@visx/shape";
import { scaleLinear, scaleTime } from "@visx/scale";
import { useMemo } from "react";

import { ChartFrame, CHART, tickLabelProps, type ChartDims } from "./frame";
import type { StrategyResult } from "@/lib/api/types";
import { ASSET_LABELS } from "@/lib/api/types";
import { pct, year } from "@/lib/format";

const M = { top: 14, right: 18, bottom: 40, left: 46 };

// distinct categorical palette for 11 assets - one amber anchor, rest cool/muted
const ASSET_COLORS = [
  "var(--color-accent)",
  "var(--color-series-spy)",
  "var(--color-series-minvar)",
  "var(--color-series-equalweight)",
  "var(--color-series-sixtyforty)",
  "#7c9cdb",
  "#cf9f6b",
  "#88c0a0",
  "#b48ec9",
  "#d98a8a",
  "#6fb6c4",
];

interface BandPt {
  date: Date;
  y0: number;
  y1: number;
}

function WeightsInner({
  width,
  height,
  tickers,
  strategy,
}: ChartDims & { tickers: string[]; strategy: StrategyResult }) {
  const innerW = Math.max(0, width - M.left - M.right);
  const innerH = Math.max(0, height - M.top - M.bottom);

  const { bands, xScale, yScale } = useMemo(() => {
    const dates = strategy.rebalance_dates.map((d) => new Date(d));
    const rows = strategy.weights_over_time; // [time][asset]
    const nAssets = tickers.length;

    // cumulative stack per timestep
    const series: BandPt[][] = Array.from({ length: nAssets }, () => []);
    for (let t = 0; t < rows.length; t++) {
      let cum = 0;
      for (let a = 0; a < nAssets; a++) {
        const w = rows[t]?.[a] ?? 0;
        series[a].push({ date: dates[t], y0: cum, y1: cum + w });
        cum += w;
      }
    }

    const x = scaleTime<number>({
      domain: [dates[0], dates[dates.length - 1]],
      range: [0, innerW],
    });
    const y = scaleLinear<number>({ domain: [0, 1], range: [innerH, 0] });
    return { bands: series, xScale: x, yScale: y };
  }, [tickers, strategy, innerW, innerH]);

  if (innerW <= 0 || innerH <= 0) return null;

  return (
    <svg width={width} height={height} aria-label="Portfolio weights over time">
      <Group left={M.left} top={M.top}>
        {bands.map((band, a) => (
          <AreaClosed
            key={tickers[a]}
            data={band}
            x={(p) => xScale(p.date)}
            y0={(p) => yScale(p.y0)}
            y1={(p) => yScale(p.y1)}
            yScale={yScale}
            fill={ASSET_COLORS[a % ASSET_COLORS.length]}
            fillOpacity={0.82}
            stroke="var(--color-panel)"
            strokeWidth={0.4}
          />
        ))}

        <AxisLeft
          scale={yScale}
          stroke={CHART.axisStroke}
          tickStroke={CHART.axisStroke}
          numTicks={5}
          tickFormat={(v) => pct(Number(v), 0)}
          tickLabelProps={tickLabelProps}
          label="Weight (%)"
          labelProps={{
            fill: CHART.labelColor,
            fontSize: 11,
            fontFamily: "var(--font-plex-mono)",
            textAnchor: "middle",
          }}
          labelOffset={30}
        />
        <AxisBottom
          top={innerH}
          scale={xScale}
          stroke={CHART.axisStroke}
          tickStroke={CHART.axisStroke}
          numTicks={6}
          tickFormat={(v) => year(new Date(v as number).toISOString())}
          tickLabelProps={tickLabelProps}
        />
      </Group>
    </svg>
  );
}

export function WeightsLegend({ tickers }: { tickers: string[] }) {
  return (
    <div className="flex flex-wrap gap-x-3 gap-y-1.5">
      {tickers.map((t, a) => (
        <div key={t} className="flex items-center gap-1.5">
          <span
            className="inline-block h-2 w-2 rounded-[1px]"
            style={{ background: ASSET_COLORS[a % ASSET_COLORS.length] }}
          />
          <span className="font-mono text-[10px] text-fg-dim">{t}</span>
          <span className="text-[10px] text-fg-faint">{ASSET_LABELS[t] ?? t}</span>
        </div>
      ))}
    </div>
  );
}

export function WeightsChart({
  tickers,
  strategy,
  height = 240,
}: {
  tickers: string[];
  strategy: StrategyResult;
  height?: number;
}) {
  return (
    <ChartFrame height={height}>
      {(dims) => <WeightsInner {...dims} tickers={tickers} strategy={strategy} />}
    </ChartFrame>
  );
}
