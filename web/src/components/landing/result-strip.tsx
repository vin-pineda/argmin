import { Reveal } from "@/components/landing/reveal";
import { Badge } from "@/components/ui/primitives";
import { defaultScenario } from "@/lib/api/scenario";
import { METHOD_LABELS } from "@/lib/api/types";
import { cn } from "@/lib/cn";
import { dateOnly, pct } from "@/lib/format";

const ROWS = ["max_sharpe", "spy", "sixty_forty", "equal_weight"] as const;

/** Headline out-of-sample result: the chosen Max-Sharpe portfolio against the
 *  three benchmarks. Honest framing: better Sharpe + far smaller drawdown, but
 *  SPY carries higher raw CAGR. */
export function ResultStrip() {
  const { backtest } = defaultScenario;
  const prov = backtest.provenance;
  const strat = backtest.strategies;

  const best = strat.max_sharpe.metrics;
  const spy = strat.spy.metrics;

  return (
    <section className="border-b border-line">
      <div className="mx-auto max-w-[1400px] px-5 py-16 sm:py-20">
        <Reveal as="div" className="flex flex-col gap-3">
          <h2 className="max-w-2xl text-2xl font-semibold tracking-tight text-fg sm:text-3xl">
            Diversification buys a smoother ride, not always more return.
          </h2>
          <p className="max-w-xl text-[14px] leading-relaxed text-fg-dim">
            Over the full walk-forward window, Max Sharpe beats SPY on risk-adjusted
            return and cuts the worst drawdown by a third. SPY still wins on raw CAGR.
            Both are true; we report both.
          </p>
        </Reveal>

        {/* compact hairline table - mono tabular numerics */}
        <Reveal as="div" delay={0.1} className="mt-10 overflow-x-auto rounded-[var(--radius)] border border-line bg-panel">
          <table className="w-full min-w-[640px] border-collapse text-left">
            <thead>
              <tr className="border-b border-line text-fg-dim">
                <th className="px-4 py-3 font-mono text-[11px] font-normal uppercase tracking-[0.12em]">
                  Strategy
                </th>
                <th className="px-4 py-3 text-right font-mono text-[11px] font-normal uppercase tracking-[0.12em]">
                  CAGR
                </th>
                <th className="px-4 py-3 text-right font-mono text-[11px] font-normal uppercase tracking-[0.12em]">
                  Ann. Vol
                </th>
                <th className="px-4 py-3 text-right font-mono text-[11px] font-normal uppercase tracking-[0.12em]">
                  Sharpe
                </th>
                <th className="px-4 py-3 text-right font-mono text-[11px] font-normal uppercase tracking-[0.12em]">
                  Max DD
                </th>
              </tr>
            </thead>
            <tbody>
              {ROWS.map((key) => {
                const m = strat[key].metrics;
                const isBest = key === "max_sharpe";
                return (
                  <tr
                    key={key}
                    className={cn(
                      "border-b border-line last:border-b-0",
                      isBest && "bg-elevated/50",
                    )}
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span
                          className={cn(
                            "inline-block h-2 w-2 rounded-full",
                            isBest ? "bg-accent" : "bg-fg-faint",
                          )}
                          aria-hidden
                        />
                        <span
                          className={cn(
                            "text-[13px]",
                            isBest ? "font-medium text-fg" : "text-fg-dim",
                          )}
                        >
                          {METHOD_LABELS[key]}
                        </span>
                        {isBest ? (
                          <Badge tone="accent" dot>
                            chosen
                          </Badge>
                        ) : null}
                      </div>
                    </td>
                    <td className="tnum px-4 py-3 text-right text-[13px] text-fg">{pct(m.cagr)}</td>
                    <td className="tnum px-4 py-3 text-right text-[13px] text-fg-dim">
                      {pct(m.ann_vol)}
                    </td>
                    <td
                      className={cn(
                        "tnum px-4 py-3 text-right text-[13px]",
                        isBest ? "text-accent" : "text-fg",
                      )}
                    >
                      {m.sharpe.toFixed(2)}
                    </td>
                    <td className="tnum px-4 py-3 text-right text-[13px] text-neg">
                      {pct(m.max_drawdown)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Reveal>

        {/* honest one-liner pinned to the comparison */}
        <p className="mt-4 max-w-2xl text-[12.5px] leading-relaxed text-fg-faint">
          Max Sharpe: Sharpe{" "}
          <span className="tnum text-fg-dim">{best.sharpe.toFixed(2)}</span> vs SPY{" "}
          <span className="tnum text-fg-dim">{spy.sharpe.toFixed(2)}</span>, max drawdown{" "}
          <span className="tnum text-pos">{pct(best.max_drawdown)}</span> vs{" "}
          <span className="tnum text-neg">{pct(spy.max_drawdown)}</span> - a smoother ride
          at the cost of {pct(spy.cagr - best.cagr)} of annual return.
        </p>

        {/* provenance row */}
        <div className="mt-6 flex flex-wrap items-center gap-x-5 gap-y-2 text-[12px] text-fg-faint">
          <Badge tone="accent" dot>
            OOS-only
          </Badge>
          <span className="tnum">
            data {dateOnly(prov.data_start)} &rarr; {dateOnly(prov.data_end)}
          </span>
          <span className="tnum">rf {pct(prov.risk_free)}</span>
          <span className="tnum">costs applied</span>
          <span className="tnum">engine {prov.engine_hash}</span>
        </div>
      </div>
    </section>
  );
}
