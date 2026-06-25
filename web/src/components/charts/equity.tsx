"use client";

import { AxisBottom, AxisLeft } from "@visx/axis";
import { GridRows } from "@visx/grid";
import { Group } from "@visx/group";
import { LinePath, Line } from "@visx/shape";
import { scaleLinear, scaleTime, scaleLog } from "@visx/scale";
import { curveMonotoneX } from "@visx/curve";
import { useTooltip, useTooltipInPortal, defaultStyles } from "@visx/tooltip";
import { bisector } from "d3-array";
import { motion } from "motion/react";
import { useMemo } from "react";

const DRAW_EASE = [0.16, 1, 0.3, 1] as const;

import { ChartFrame, CHART, tickLabelProps, type ChartDims } from "./frame";
import type { BacktestResult } from "@/lib/api/types";
import { METHOD_LABELS } from "@/lib/api/types";
import { seriesColor, zipSeries } from "@/lib/series";
import { money, year } from "@/lib/format";

const M = { top: 16, right: 18, bottom: 40, left: 50 };

interface Pt {
  date: Date;
  value: number;
}
interface SeriesLine {
  name: string;
  points: Pt[];
  color: string;
  chosen: boolean;
}

const bisectDate = bisector<Pt, Date>((d) => d.date).left;

/** Mouse x relative to the owning <svg> (no @visx/event dependency). */
function svgX(e: React.MouseEvent<SVGElement> | React.TouchEvent<SVGElement>): number {
  const target = e.currentTarget as SVGElement;
  const svg = target.ownerSVGElement ?? (target as unknown as SVGSVGElement);
  const rect = svg.getBoundingClientRect();
  const clientX =
    "touches" in e ? (e.touches[0]?.clientX ?? 0) : (e as React.MouseEvent).clientX;
  return clientX - rect.left;
}

function EquityInner({
  width,
  height,
  data,
  chosen,
  logScale,
}: ChartDims & { data: BacktestResult; chosen: string; logScale: boolean }) {
  const innerW = Math.max(0, width - M.left - M.right);
  const innerH = Math.max(0, height - M.top - M.bottom);

  const { tooltipData, tooltipLeft, showTooltip, hideTooltip, tooltipOpen } =
    useTooltip<{ date: Date; values: { name: string; value: number; color: string }[] }>();
  const { containerRef, TooltipInPortal } = useTooltipInPortal({ detectBounds: true, scroll: true });

  const series: SeriesLine[] = useMemo(() => {
    return Object.entries(data.strategies).map(([name, s]) => {
      const zipped = zipSeries(data.dates, s.equity_curve, 600);
      return {
        name,
        points: zipped.map((z) => ({ date: new Date(z.date), value: z.value })),
        color: seriesColor(name),
        chosen: name === chosen,
      };
    });
  }, [data, chosen]);

  const { xScale, yScale } = useMemo(() => {
    const allDates = series.flatMap((s) => s.points.map((p) => p.date.getTime()));
    const allVals = series.flatMap((s) => s.points.map((p) => p.value));
    const yMin = Math.min(...allVals);
    const yMax = Math.max(...allVals);
    const x = scaleTime<number>({
      domain: [new Date(Math.min(...allDates)), new Date(Math.max(...allDates))],
      range: [0, innerW],
    });
    const y = logScale
      ? scaleLog<number>({
          domain: [Math.max(0.01, yMin * 0.96), yMax * 1.04],
          range: [innerH, 0],
        })
      : scaleLinear<number>({
          domain: [Math.min(1, yMin) * 0.98, yMax * 1.04],
          range: [innerH, 0],
        });
    return { xScale: x, yScale: y };
  }, [series, innerW, innerH, logScale]);

  if (innerW <= 0 || innerH <= 0) return null;

  // order: benchmarks (muted) first, chosen on top
  const ordered = [...series.filter((s) => !s.chosen), ...series.filter((s) => s.chosen)];

  const handleMove = (e: React.MouseEvent<SVGElement> | React.TouchEvent<SVGElement>) => {
    const px = svgX(e);
    const x0 = xScale.invert(px - M.left);
    const ref = series[0]?.points ?? [];
    const idx = bisectDate(ref, x0, 1);
    const d0 = ref[idx - 1];
    const d1 = ref[idx];
    if (!d0) return;
    const closest =
      d1 && x0.getTime() - d0.date.getTime() > d1.date.getTime() - x0.getTime() ? d1 : d0;
    const targetTime = closest.date.getTime();
    const values = series.map((s) => {
      const match =
        s.points.find((p) => p.date.getTime() === targetTime) ??
        s.points[bisectDate(s.points, closest.date, 1) - 1];
      return { name: s.name, value: match?.value ?? 0, color: s.color };
    });
    showTooltip({
      tooltipLeft: xScale(closest.date) + M.left,
      tooltipData: { date: closest.date, values },
    });
  };

  return (
    <div ref={containerRef} className="relative">
      <svg width={width} height={height} aria-label="Equity curves, growth of $1">
        <Group left={M.left} top={M.top}>
          <GridRows scale={yScale} width={innerW} height={innerH} stroke={CHART.gridStroke} />

          {ordered.map((s, i) => (
            <LinePath
              key={s.name}
              data={s.points}
              x={(p) => xScale(p.date)}
              y={(p) => yScale(p.value)}
              curve={curveMonotoneX}
            >
              {({ path }) => (
                <motion.path
                  d={path(s.points) || ""}
                  fill="none"
                  stroke={s.color}
                  strokeWidth={s.chosen ? 1.9 : 1}
                  strokeOpacity={s.chosen ? 1 : 0.55}
                  strokeLinecap="round"
                  initial={{ pathLength: 0 }}
                  whileInView={{ pathLength: 1 }}
                  viewport={{ once: true, margin: "0px 0px -12% 0px" }}
                  transition={{
                    duration: 1.2,
                    ease: DRAW_EASE,
                    delay: s.chosen ? 0.3 : i * 0.08,
                  }}
                />
              )}
            </LinePath>
          ))}

          {tooltipOpen && tooltipLeft != null ? (
            <Line
              from={{ x: tooltipLeft - M.left, y: 0 }}
              to={{ x: tooltipLeft - M.left, y: innerH }}
              stroke="var(--color-line-strong)"
              strokeWidth={1}
              strokeDasharray="3,3"
              pointerEvents="none"
            />
          ) : null}

          <AxisLeft
            scale={yScale}
            stroke={CHART.axisStroke}
            tickStroke={CHART.axisStroke}
            numTicks={5}
            tickFormat={(v) => money(Number(v), 1)}
            tickLabelProps={tickLabelProps}
            label="Growth of $1"
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

          <rect
            width={innerW}
            height={innerH}
            fill="transparent"
            onMouseMove={handleMove}
            onTouchMove={handleMove}
            onMouseLeave={hideTooltip}
          />
        </Group>
      </svg>

      {tooltipOpen && tooltipData ? (
        <TooltipInPortal
          left={tooltipLeft}
          top={8}
          style={{
            ...defaultStyles,
            background: "var(--color-overlay)",
            border: "1px solid var(--color-line-strong)",
            borderRadius: 4,
            color: "var(--color-fg)",
            padding: "6px 9px",
            fontSize: 11,
            boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
          }}
        >
          <div className="tnum text-[10px] text-fg-faint">{year(tooltipData.date.toISOString())}</div>
          <div className="mt-1 flex flex-col gap-0.5">
            {tooltipData.values.map((v) => (
              <div key={v.name} className="flex items-center gap-2">
                <span
                  className="inline-block h-2 w-2 rounded-[1px]"
                  style={{ background: v.color }}
                />
                <span className="text-[10.5px] text-fg-dim">
                  {METHOD_LABELS[v.name] ?? v.name}
                </span>
                <span className="tnum ml-auto text-[10.5px] text-fg">{money(v.value, 2)}</span>
              </div>
            ))}
          </div>
        </TooltipInPortal>
      ) : null}
    </div>
  );
}

export function EquityChart({
  data,
  chosen,
  logScale = false,
  height = 300,
}: {
  data: BacktestResult;
  chosen: string;
  logScale?: boolean;
  height?: number;
}) {
  return (
    <ChartFrame height={height}>
      {(dims) => <EquityInner {...dims} data={data} chosen={chosen} logScale={logScale} />}
    </ChartFrame>
  );
}
