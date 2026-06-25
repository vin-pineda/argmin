"use client";

import { AnimatedNumber } from "@/components/ui/animated-number";
import { cn } from "@/lib/cn";
import type { BacktestResult } from "@/lib/api/types";
import { METHOD_LABELS } from "@/lib/api/types";
import { pct, num } from "@/lib/format";

type Tone = "pos" | "neg" | "neutral";
type Metrics = BacktestResult["strategies"][string]["metrics"];

interface Col {
  key: string;
  label: string;
  get: (m: Metrics) => number | null;
  fmt: (v: number) => string;
  tone?: (m: Metrics) => Tone;
}

const p1 = (v: number) => pct(v, 1);
const n2 = (v: number) => num(v, 2);

const COLS: Col[] = [
  { key: "cagr", label: "CAGR", get: (m) => m.cagr, fmt: p1, tone: (m) => sign(m.cagr) },
  { key: "vol", label: "Vol", get: (m) => m.ann_vol, fmt: p1 },
  { key: "sharpe", label: "Sharpe", get: (m) => m.sharpe, fmt: n2, tone: (m) => sign(m.sharpe) },
  { key: "sortino", label: "Sortino", get: (m) => m.sortino, fmt: n2, tone: (m) => sign(m.sortino) },
  { key: "maxdd", label: "MaxDD", get: (m) => m.max_drawdown, fmt: p1, tone: () => "neg" },
  { key: "calmar", label: "Calmar", get: (m) => m.calmar, fmt: n2 },
  { key: "var95", label: "VaR95", get: (m) => m.var_95, fmt: p1, tone: () => "neg" },
  { key: "turnover", label: "Turnover", get: (m) => m.avg_turnover ?? null, fmt: p1 },
  { key: "psr", label: "PSR", get: (m) => m.psr ?? null, fmt: p1 },
  { key: "dsr", label: "DSR", get: (m) => m.dsr ?? null, fmt: p1 },
];

function sign(x: number): Tone {
  return x > 0 ? "pos" : x < 0 ? "neg" : "neutral";
}

const toneClass: Record<Tone, string> = {
  pos: "text-pos",
  neg: "text-neg",
  neutral: "text-fg",
};

export function TearsheetTable({
  data,
  chosen,
}: {
  data: BacktestResult;
  chosen: string;
}) {
  // chosen first, then benchmarks in scenario order
  const names = [chosen, ...Object.keys(data.strategies).filter((n) => n !== chosen)].filter(
    (n) => data.strategies[n],
  );

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-[12px]">
        <thead>
          <tr className="border-b border-line">
            <th className="px-3 py-2 text-left font-mono text-[10.5px] uppercase tracking-[0.1em] text-fg-faint">
              Strategy
            </th>
            {COLS.map((c) => (
              <th
                key={c.key}
                className="px-3 py-2 text-right font-mono text-[10.5px] uppercase tracking-[0.1em] text-fg-faint"
              >
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {names.map((name) => {
            const m = data.strategies[name].metrics;
            const isChosen = name === chosen;
            return (
              <tr
                key={name}
                className={cn(
                  "border-b border-line/60 last:border-0",
                  isChosen && "bg-elevated/50",
                )}
              >
                <th
                  scope="row"
                  className={cn(
                    "px-3 py-2 text-left text-[12px] font-normal whitespace-nowrap",
                    isChosen ? "text-accent" : "text-fg-dim",
                  )}
                >
                  {isChosen ? (
                    <span className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-accent align-middle" />
                  ) : null}
                  {METHOD_LABELS[name] ?? name}
                </th>
                {COLS.map((c) => {
                  const tone = c.tone ? c.tone(m) : "neutral";
                  const v = c.get(m);
                  return (
                    <td
                      key={c.key}
                      className={cn(
                        "tnum px-3 py-2 text-right",
                        isChosen ? "text-fg" : toneClass[tone],
                      )}
                    >
                      {v == null ? "-" : <AnimatedNumber value={v} format={c.fmt} />}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
