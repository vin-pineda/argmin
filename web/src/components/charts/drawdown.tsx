"use client";

import { AxisBottom, AxisLeft } from "@visx/axis";
import { GridRows } from "@visx/grid";
import { Group } from "@visx/group";
import { AreaClosed, LinePath } from "@visx/shape";
import { scaleLinear, scaleTime } from "@visx/scale";
import { curveMonotoneX } from "@visx/curve";
import { LinearGradient } from "@visx/gradient";
import { motion } from "motion/react";
import { useMemo } from "react";

const DRAW_EASE = [0.16, 1, 0.3, 1] as const;

import { ChartFrame, CHART, tickLabelProps, type ChartDims } from "./frame";
import type { StrategyResult } from "@/lib/api/types";
import { zipSeries } from "@/lib/series";
import { pct, year } from "@/lib/format";

const M = { top: 14, right: 18, bottom: 40, left: 50 };

interface Pt {
  date: Date;
  value: number;
}

function DrawdownInner({
  width,
  height,
  dates,
  strategy,
}: ChartDims & { dates: string[]; strategy: StrategyResult }) {
  const innerW = Math.max(0, width - M.left - M.right);
  const innerH = Math.max(0, height - M.top - M.bottom);

  const points: Pt[] = useMemo(
    () =>
      zipSeries(dates, strategy.drawdown, 600).map((z) => ({
        date: new Date(z.date),
        value: Math.min(0, z.value),
      })),
    [dates, strategy],
  );

  const { xScale, yScale } = useMemo(() => {
    const times = points.map((p) => p.date.getTime());
    const minDd = Math.min(...points.map((p) => p.value));
    return {
      xScale: scaleTime<number>({
        domain: [new Date(Math.min(...times)), new Date(Math.max(...times))],
        range: [0, innerW],
      }),
      yScale: scaleLinear<number>({
        domain: [minDd * 1.06, 0],
        range: [innerH, 0],
      }),
    };
  }, [points, innerW, innerH]);

  if (innerW <= 0 || innerH <= 0) return null;

  return (
    <svg width={width} height={height} aria-label="Drawdown underwater area">
      <LinearGradient
        id="dd-fill"
        from="var(--color-accent)"
        to="var(--color-accent)"
        fromOpacity={0.04}
        toOpacity={0.26}
        x1="0"
        y1="0"
        x2="0"
        y2="1"
      />
      <Group left={M.left} top={M.top}>
        <GridRows scale={yScale} width={innerW} height={innerH} stroke={CHART.gridStroke} />

        <AreaClosed data={points} x={(p) => xScale(p.date)} y={(p) => yScale(p.value)} yScale={yScale} curve={curveMonotoneX}>
          {({ path }) => (
            <motion.path
              d={path(points) || ""}
              fill="url(#dd-fill)"
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true, margin: "0px 0px -12% 0px" }}
              transition={{ duration: 0.9, ease: DRAW_EASE, delay: 0.25 }}
            />
          )}
        </AreaClosed>
        <LinePath data={points} x={(p) => xScale(p.date)} y={(p) => yScale(p.value)} curve={curveMonotoneX}>
          {({ path }) => (
            <motion.path
              d={path(points) || ""}
              fill="none"
              stroke="var(--color-accent)"
              strokeWidth={1.2}
              strokeOpacity={0.8}
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
          numTicks={4}
          tickFormat={(v) => pct(Number(v), 0)}
          tickLabelProps={tickLabelProps}
          label="Drawdown (%)"
          labelProps={{
            fill: CHART.labelColor,
            fontSize: 11,
            fontFamily: "var(--font-plex-mono)",
            textAnchor: "middle",
          }}
          labelOffset={34}
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

export function DrawdownChart({
  dates,
  strategy,
  height = 200,
}: {
  dates: string[];
  strategy: StrategyResult;
  height?: number;
}) {
  return (
    <ChartFrame height={height}>
      {(dims) => <DrawdownInner {...dims} dates={dates} strategy={strategy} />}
    </ChartFrame>
  );
}
