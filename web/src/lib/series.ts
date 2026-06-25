/** Chart series colors + downsampling helpers shared across visx charts. */

export const SERIES_COLORS: Record<string, string> = {
  max_sharpe: "var(--color-series-strategy)",
  min_variance: "var(--color-series-minvar)",
  max_diversification: "var(--color-series-minvar)",
  risk_parity: "var(--color-series-strategy)",
  hrp: "var(--color-series-strategy)",
  black_litterman: "var(--color-series-strategy)",
  equal_weight: "var(--color-series-equalweight)",
  sixty_forty: "var(--color-series-sixtyforty)",
  spy: "var(--color-series-spy)",
};

export const seriesColor = (name: string): string =>
  SERIES_COLORS[name] ?? "var(--color-fg-dim)";

/** Even-stride downsample for long daily series (keeps first + last). */
export function downsample<T>(arr: T[], maxPoints: number): T[] {
  if (arr.length <= maxPoints) return arr;
  const stride = Math.ceil(arr.length / maxPoints);
  const out: T[] = [];
  for (let i = 0; i < arr.length; i += stride) out.push(arr[i]);
  if (out[out.length - 1] !== arr[arr.length - 1]) out.push(arr[arr.length - 1]);
  return out;
}

/** Pair a daily value series with its date axis, downsampled together. */
export function zipSeries(
  dates: string[],
  values: number[],
  maxPoints = 600,
): { date: string; value: number }[] {
  const n = Math.min(dates.length, values.length);
  const offset = dates.length - values.length; // rolling-sharpe is shorter than dates
  const paired = Array.from({ length: n }, (_, i) => ({
    date: dates[i + (offset > 0 ? offset : 0)],
    value: values[i],
  }));
  return downsample(paired, maxPoints);
}
