import type { Metadata } from "next";

import { ExplorerClient } from "@/components/explore/ExplorerClient";
import { Reveal } from "@/components/landing/reveal";
import { defaultScenario } from "@/lib/api/scenario";

export const metadata: Metadata = {
  title: "Explore - Argmin",
  description:
    "Run seven allocation models live: efficient frontier, walk-forward OOS backtest, costs, drawdowns, and significance - the math, shown.",
};

export default function ExplorePage() {
  return (
    <div>
      <div className="mx-auto max-w-[1400px] px-5 py-8 sm:py-10">
        <Reveal as="div" className="mb-7">
          <header className="flex flex-col gap-3">
            <h1 className="text-2xl font-semibold tracking-tight text-fg sm:text-3xl">
              Explore the allocations
            </h1>
            <p className="max-w-2xl text-[13.5px] leading-relaxed text-fg-dim">
              Pick a model and universe, set constraints and costs, then run it. Optimize is fast
              and refreshes the frontier, weights, and risk decomposition. Run backtest to rebuild
              the walk-forward, out-of-sample equity curve, drawdowns, and significance. Every
              number is computed by the engine - nothing is mocked.
            </p>
          </header>
        </Reveal>

        <ExplorerClient initial={defaultScenario} />
      </div>
    </div>
  );
}
