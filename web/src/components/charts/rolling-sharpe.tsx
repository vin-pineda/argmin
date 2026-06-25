"use client";

import { AxisBottom, AxisLeft } from "@visx/axis";
import { GridRows } from "@visx/grid";
import { Group } from "@visx/group";
import { LinePath, Line } from "@visx/shape";
import { scaleLinear, scaleTime } from "@visx/scale";
import { curveMonotoneX } from "@visx/curve";
import { motion } from "motion/react";
import { useMemo } from "react";

const DRAW_EASE = [0.16, 1, 0.3, 1] as const;

import { ChartFrame, CHART, tickLabelProps, type ChartDims } from "./frame";
import type { StrategyResult } from "@/lib/api/types";
import { seriesColor, zipSeries } from "@/lib/series";
import { num, year } from "@/lib/format";

const M = { top: 14, right: 18, bottom: 40, left: 50 };

interface Pt {
  date: Date;
  value: number;
}

function RollingSharpeInner({
  width,
  height,
  dates,
  strategy,
  name,
}: ChartDims & { dates: string[]; strategy: StrategyResult; name: string }) {
  const innerW = Math.max(0, width - M.left - M.right);
  const innerH = Math.max(0, height - M.top - M.bottom);

  const points: Pt[] = useMemo(
    () =>
      zipSeries(dates, strategy.rolling_sharpe, 600).map((z) => ({
        date: new Date(z.date),
        value: z.value,
      })),
    [dates, strategy],
  );

  const { xScale, yScale } = useMemo(() => {
    const times = points.map((p) => p.date.getTime());
    const vals = points.map((p) => p.value);
    const yMin = Math.min(0, ...vals);
    const yMax = Math.max(0, ...vals);
    const pad = (yMax - yMin) * 0.08 || 0.1;
    return {
      xScale: scaleTime<number>({
        domain: [new Date(Math.min(...times)), new Date(Math.max(...times))],
        range: [0, innerW],
      }),
      yScale: scaleLinear<number>({
        domain: [yMin - pad, yMax + pad],
        range: [innerH, 0],
      }),
    };
  }, [points, innerW, innerH]);

  if (innerW <= 0 || innerH <= 0) return null;

  const zeroY = yScale(0);

  return (
    <svg width={width} height={height} aria-label="Rolling 252-day Sharpe ratio">
      <Group left={M.left} top={M.top}>
        <GridRows scale={yScale} width={innerW} height={innerH} stroke={CHART.gridStroke} />

        {/* zero baseline */}
        <Line
          from={{ x: 0, y: zeroY }}
          to={{ x: innerW, y: zeroY }}
          stroke="var(--color-line-strong)"
          strokeWidth={1}
          strokeDasharray="2,3"
        />

        <LinePath data={points} x={(p) => xScale(p.date)} y={(p) => yScale(p.value)} curve={curveMonotoneX}>
          {({ path }) => (
            <motion.path
              d={path(points) || ""}
              fill="none"
              stroke={seriesColor(name)}
              strokeWidth={1.4}
              strokeLinecap="round"
              initial={{ pathLength: 0 }}
              whileInView={{ pathLength: 1 }}
              viewport={{ once: true, margin: "0px 0px -12% 0px" }}
              transition={{ duration: 1.1, ease: DRAW_EASE }}
            />
          )}
        </LinePath>

        <AxisLeft
          scale={yScale}
          stroke={CHART.axisStroke}
          tickStroke={CHART.axisStroke}
          numTicks={5}
          tickFormat={(v) => num(Number(v), 1)}
          tickLabelProps={tickLabelProps}
          label="Rolling Sharpe (252d)"
          labelProps={{
            fill: CHART.labelColor,
            fontSize: 11,
            fontFamily: "var(--font-plex-mono)",
            textAnchor: "middle",
          }}
          labelOffset={32}
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

export function RollingSharpeChart({
  dates,
  strategy,
  name,
  height = 200,
}: {
  dates: string[];
  strategy: StrategyResult;
  name: string;
  height?: number;
}) {
  return (
    <ChartFrame height={height}>
      {(dims) => <RollingSharpeInner {...dims} dates={dates} strategy={strategy} name={name} />}
    </ChartFrame>
  );
}
