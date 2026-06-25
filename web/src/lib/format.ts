/** Formatting helpers — all numerics render monospaced + tabular elsewhere. */

export const pct = (x: number, d = 1): string => `${(x * 100).toFixed(d)}%`;

export const pctSigned = (x: number, d = 1): string =>
  `${x >= 0 ? "+" : ""}${(x * 100).toFixed(d)}%`;

export const num = (x: number, d = 2): string => x.toFixed(d);

export const numSigned = (x: number, d = 2): string => `${x >= 0 ? "+" : ""}${x.toFixed(d)}`;

/** A growth-of-$1 equity value → "$2.41". */
export const money = (x: number, d = 2): string => `$${x.toFixed(d)}`;

/** ISO date "2010-04-12" → "Apr 2010". */
export const monthYear = (iso: string): string => {
  const dt = new Date(iso);
  return dt.toLocaleDateString("en-US", { month: "short", year: "numeric", timeZone: "UTC" });
};

/** ISO date → "2010-04-12" (date only). */
export const dateOnly = (iso: string): string => iso.slice(0, 10);

export const year = (iso: string): string => iso.slice(0, 4);
