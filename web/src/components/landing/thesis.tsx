import { Hairline } from "@/components/ui/primitives";
import { Equation } from "@/components/ui/equation";

import { Reveal } from "./reveal";

/** Why naive in-sample frontiers lie - the core argument, with the mean-variance
 *  objective as a first-class typographic object and inline literature anchors. */
export function Thesis() {
  return (
    <section className="border-b border-line">
      <div className="mx-auto max-w-[1400px] px-5 py-16 sm:py-24">
        <div className="grid grid-cols-1 gap-12 lg:grid-cols-[0.85fr_1.15fr] lg:gap-20">
          {/* left rail: the objective */}
          <Reveal className="flex flex-col gap-5">
            <p className="text-[15px] leading-relaxed text-fg-dim">
              Mean-variance optimization trades expected return against variance through a
              single risk-aversion knob{" "}
              <span className="tnum text-fg">&gamma;</span>:
            </p>
            <div className="rounded-[var(--radius)] border border-line bg-panel px-6 py-7">
              <Equation
                display
                tex="\max_{w}\;\; \mu^{\top} w \;-\; \tfrac{\gamma}{2}\, w^{\top}\Sigma\, w \quad \text{s.t.}\;\; \mathbf{1}^{\top} w = 1,\; w \ge 0"
              />
            </div>
            <p className="text-[13px] leading-relaxed text-fg-faint">
              The frontier is the set of <span className="text-fg-dim">argmin</span> portfolios
              over every risk level. Solve it on the same data you score on, and you have
              fit the noise.
            </p>
          </Reveal>

          {/* right: three short blocks */}
          <div className="flex flex-col gap-8">
            <Reveal delay={0.05} className="flex flex-col gap-2">
              <h3 className="text-lg font-semibold tracking-tight text-fg">
                The inputs are estimated, not given.
              </h3>
              <p className="text-[14px] leading-relaxed text-fg-dim">
                Markowitz (1952) gave us the frontier, but it assumes the true{" "}
                <span className="tnum text-fg">&mu;</span> and{" "}
                <span className="tnum text-fg">&Sigma;</span> are known. In practice both are
                sampled from a short, noisy history. Small estimation errors in{" "}
                <span className="tnum text-fg">&mu;</span> get amplified into extreme,
                concentrated weights.
              </p>
            </Reveal>

            <Hairline />

            <Reveal delay={0.1} className="flex flex-col gap-2">
              <h3 className="text-lg font-semibold tracking-tight text-fg">
                In-sample frontiers are optimistic by construction.
              </h3>
              <p className="text-[14px] leading-relaxed text-fg-dim">
                The optimizer rewards whatever happened to look good in the window it was fit
                on. Report that curve as a result and you are quoting the model marking its
                own homework. Honest evaluation only counts returns the model never saw.
              </p>
            </Reveal>

            <Hairline />

            <Reveal delay={0.15} className="flex flex-col gap-2">
              <h3 className="text-lg font-semibold tracking-tight text-fg">
                Shrinkage and structure tame the covariance.
              </h3>
              <p className="text-[14px] leading-relaxed text-fg-dim">
                Ledoit-Wolf (2004) shrinkage pulls the sample covariance toward a structured
                target, trading a little bias for far less variance. It is one of several
                priors here - alongside risk parity, hierarchical clustering, and
                Black-Litterman views - that make weights survive contact with new data.
              </p>
            </Reveal>
          </div>
        </div>
      </div>
    </section>
  );
}
