"use client";

import { ParentSize } from "@visx/responsive";

import { cn } from "@/lib/cn";

/** Shared axis/grid styling constants so every chart reads as one system. */
export const CHART = {
  axisStroke: "var(--color-line-strong)",
  gridStroke: "var(--color-grid)",
  tickColor: "var(--color-fg-faint)",
  tickFontSize: 10,
  tickFontFamily: "var(--font-plex-mono)",
  labelColor: "var(--color-fg-dim)",
} as const;

export interface ChartDims {
  width: number;
  height: number;
}

/** Responsive wrapper: gives children measured width/height. Reserves space
 *  (fixed height) to avoid CLS. */
export function ChartFrame({
  height,
  className,
  children,
}: {
  height: number;
  className?: string;
  children: (dims: ChartDims) => React.ReactNode;
}) {
  return (
    <div className={cn("w-full", className)} style={{ height }}>
      <ParentSize>{({ width }) => (width > 0 ? children({ width, height }) : null)}</ParentSize>
    </div>
  );
}

/** Shared visx tick label props. */
export const tickLabelProps = () =>
  ({
    fill: CHART.tickColor,
    fontSize: CHART.tickFontSize,
    fontFamily: CHART.tickFontFamily,
  }) as const;
