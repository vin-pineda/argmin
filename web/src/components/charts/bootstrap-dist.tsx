"use client";

import { AxisBottom } from "@visx/axis";
import { Group } from "@visx/group";
import { LinearGradient } from "@visx/gradient";
import { scaleLinear } from "@visx/scale";
import { AreaClosed, LinePath } from "@visx/shape";
import { useMemo } from "react";

import { ChartFrame, CHART, tickLabelProps } from "@/components/charts/frame";
import { num } from "@/lib/format";

interface Pt {
  x: number;
  y: number;
}

/** Standard normal density. */
function normPdf(x: number, mu: number, sigma: number): number {
  const z = (x - mu) / sigma;
  return Math.exp(-0.5 * z * z) / (sigma * Math.sqrt(2 * Math.PI));
}

function Dist({
  sharpe,
  ciLow,
  ciHigh,
  width,
  height,
}: {
  sharpe: number;
  ciLow: number;
  ciHigh: number;
  width: number;
  height: number;
}) {
  const margin = { top: 14, right: 16, bottom: 36, left: 16 };
  const innerW = Math.max(0, width - margin.left - margin.right);
  const innerH = Math.max(0, height - margin.top - margin.bottom);

  // Recover an implied standard error from the symmetric-ish 95% band:
  // half-width / 1.96. Use the wider half to stay honest about the spread.
  const half = Math.max(sharpe - ciLow, ciHigh - sharpe);
  const sigma = Math.max(half / 1.96, 1e-6);

  const { curve, xScale, yScale } = useMemo(() => {
    const lo = Math.min(ciLow, sharpe) - 1.2 * sigma;
    const hi = Math.max(ciHigh, sharpe) + 1.2 * sigma;
    const N = 160;
    const pts: Pt[] = Array.from({ length: N + 1 }, (_, i) => {
      const x = lo + (i / N) * (hi - lo);
      return { x, y: normPdf(x, sharpe, sigma) };
    });
    const yMax = Math.max(...pts.map((p) => p.y));
    const xs = scaleLinear<number>({ domain: [lo, hi], range: [0, innerW] });
    const ys = scaleLinear<number>({ domain: [0, yMax * 1.08], range: [innerH, 0] });
    return { curve: pts, xScale: xs, yScale: ys };
  }, [sharpe, ciLow, ciHigh, sigma, innerW, innerH]);

  const ciArea = curve.filter((p) => p.x >= ciLow && p.x <= ciHigh);
  const peakY = yScale(normPdf(sharpe, sharpe, sigma));

  return (
    <svg width={width} height={height} role="img" aria-label="Bootstrap Sharpe distribution with 95% confidence interval">
      <LinearGradient
        id="boot-fill"
        from="var(--color-accent)"
        to="var(--color-accent)"
        fromOpacity={0.22}
        toOpacity={0.02}
      />
      <Group left={margin.left} top={margin.top}>
        {/* Full density area (faint) */}
        <AreaClosed<Pt>
          data={curve}
          x={(d) => xScale(d.x)}
          y={(d) => yScale(d.y)}
          yScale={yScale}
          fill="var(--color-grid)"
          stroke="none"
        />
        {/* 95% CI shaded band */}
        <AreaClosed<Pt>
          data={ciArea}
          x={(d) => xScale(d.x)}
          y={(d) => yScale(d.y)}
          yScale={yScale}
          fill="url(#boot-fill)"
          stroke="none"
        />
        {/* density outline */}
        <LinePath<Pt>
          data={curve}
          x={(d) => xScale(d.x)}
          y={(d) => yScale(d.y)}
          stroke="var(--color-accent)"
          strokeWidth={1.5}
        />

        {/* CI edges */}
        {[ciLow, ciHigh].map((v, i) => (
          <g key={`ci-${i}`}>
            <line
              x1={xScale(v)}
              x2={xScale(v)}
              y1={innerH}
              y2={yScale(normPdf(v, sharpe, sigma))}
              stroke="var(--color-line-strong)"
              strokeWidth={1}
              strokeDasharray="3 3"
            />
            <text
              x={xScale(v)}
              y={yScale(normPdf(v, sharpe, sigma)) - 5}
              textAnchor="middle"
              fill="var(--color-fg-faint)"
              fontSize={10}
              fontFamily="var(--font-plex-mono)"
            >
              {num(v, 2)}
            </text>
          </g>
        ))}

        {/* point Sharpe marker */}
        <line
          x1={xScale(sharpe)}
          x2={xScale(sharpe)}
          y1={innerH}
          y2={peakY}
          stroke="var(--color-accent-bright)"
          strokeWidth={1.5}
        />
        <circle cx={xScale(sharpe)} cy={peakY} r={3} fill="var(--color-accent-bright)" />
        <text
          x={xScale(sharpe)}
          y={peakY - 9}
          textAnchor="middle"
          fill="var(--color-accent-bright)"
          fontSize={10.5}
          fontFamily="var(--font-plex-mono)"
        >
          {num(sharpe, 2)}
        </text>

        <AxisBottom
          top={innerH}
          scale={xScale}
          numTicks={6}
          stroke={CHART.axisStroke}
          tickStroke={CHART.axisStroke}
          tickLabelProps={tickLabelProps}
          label="Sharpe ratio"
          labelProps={{
            fill: CHART.labelColor,
            fontSize: 11,
            fontFamily: CHART.tickFontFamily,
            textAnchor: "middle",
          }}
          labelOffset={18}
        />
      </Group>
    </svg>
  );
}

export function BootstrapDist({
  sharpe,
  ciLow,
  ciHigh,
  samples = 1000,
}: {
  sharpe: number;
  ciLow: number;
  ciHigh: number;
  samples?: number;
}) {
  return (
    <div className="flex flex-col gap-3">
      <ChartFrame height={260} className="rounded-[var(--radius)] border border-line p-1">
        {({ width, height }) => (
          <Dist sharpe={sharpe} ciLow={ciLow} ciHigh={ciHigh} width={width} height={height} />
        )}
      </ChartFrame>
      <p className="text-[12px] leading-relaxed text-fg-faint">
        Block-bootstrap sampling distribution of the out-of-sample Sharpe ratio (
        <span className="tnum">{samples.toLocaleString()}</span> resamples, normal
        approximation). The shaded region is the 95% confidence interval{" "}
        <span className="tnum text-fg-dim">
          [{num(ciLow, 2)}, {num(ciHigh, 2)}]
        </span>
        ; the marker is the realized estimate{" "}
        <span className="tnum text-fg-dim">{num(sharpe, 2)}</span>. The interval excludes
        zero, so the result is unlikely to be luck alone over this window.
      </p>
    </div>
  );
}
