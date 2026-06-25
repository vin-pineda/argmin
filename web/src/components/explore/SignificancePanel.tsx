"use client";

import { AnimatedNumber } from "@/components/ui/animated-number";
import { Stat } from "@/components/ui/primitives";
import type { BacktestResult } from "@/lib/api/types";
import { METHOD_LABELS } from "@/lib/api/types";
import { pct, num } from "@/lib/format";

/** PSR / DSR / bootstrap Sharpe CI with a one-line plain-language read.
 *  All numbers come straight from backtest.significance.strategies[chosen]. */
export function SignificancePanel({
  data,
  chosen,
}: {
  data: BacktestResult;
  chosen: string;
}) {
  const sig = data.significance.strategies[chosen];
  const trials = data.significance.dsr_trials;
  const label = METHOD_LABELS[chosen] ?? chosen;

  if (!sig) {
    return (
      <div className="px-4 py-6 text-[12px] text-fg-dim">
        No significance data for {label}.
      </div>
    );
  }

  const psrTone = sig.psr >= 0.95 ? "pos" : sig.psr >= 0.5 ? "accent" : "neg";
  const dsrTone = sig.dsr >= 0.95 ? "pos" : sig.dsr >= 0.5 ? "accent" : "neg";
  const ciPositive = sig.sharpe_ci_low > 0;

  return (
    <div className="flex flex-col gap-4 px-4 py-4">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Stat
          label="PSR"
          value={<AnimatedNumber value={sig.psr} format={(v) => pct(v, 1)} />}
          tone={psrTone}
          caption="P(Sharpe > 0)"
        />
        <Stat
          label="DSR"
          value={<AnimatedNumber value={sig.dsr} format={(v) => pct(v, 1)} />}
          tone={dsrTone}
          caption={`deflated, ${trials} trials`}
        />
        <Stat
          label="Sharpe"
          value={<AnimatedNumber value={sig.sharpe} format={(v) => num(v, 2)} />}
          caption="point estimate"
        />
        <Stat
          label="95% CI"
          value={
            <span className="text-base">
              <AnimatedNumber value={sig.sharpe_ci_low} format={(v) => num(v, 2)} /> to{" "}
              <AnimatedNumber value={sig.sharpe_ci_high} format={(v) => num(v, 2)} />
            </span>
          }
          tone={ciPositive ? "pos" : "neutral"}
          caption={`${data.significance.bootstrap_samples.toLocaleString()} block-bootstrap`}
        />
      </div>

      <p className="text-[12.5px] leading-relaxed text-fg-dim">
        The true Sharpe is positive with{" "}
        <span className="tnum text-fg">~{pct(sig.psr, 0)}</span> probability (PSR). Deflating for{" "}
        <span className="tnum text-fg">{trials}</span> strategy trials, that confidence holds at{" "}
        <span className="tnum text-fg">{pct(sig.dsr, 0)}</span> (DSR). The block-bootstrap 95%
        interval for the Sharpe is{" "}
        <span className="tnum text-fg">
          [{num(sig.sharpe_ci_low, 2)}, {num(sig.sharpe_ci_high, 2)}]
        </span>
        {ciPositive ? ", which excludes zero." : ", which still includes zero."}
      </p>
    </div>
  );
}
