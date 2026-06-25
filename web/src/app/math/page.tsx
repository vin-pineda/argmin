import type { Metadata } from "next";

import { BootstrapDist } from "@/components/charts/bootstrap-dist";
import { CovHeatmap } from "@/components/charts/cov-heatmap";
import { Dendrogram, type HrpNode } from "@/components/charts/dendrogram";
import { Reveal } from "@/components/landing/reveal";
import { Cite, References } from "@/components/math/Citation";
import { Derivation } from "@/components/math/Derivation";
import { ModelSection } from "@/components/math/ModelSection";
import { Equation } from "@/components/ui/equation";
import { Badge, Hairline, Panel, PanelHeader, Stat } from "@/components/ui/primitives";
import mathExtrasJson from "@/data/math-extras.json";
import { defaultScenario } from "@/lib/api/scenario";
import { pct, num } from "@/lib/format";

interface MathExtras {
  tickers: string[];
  corr_sample: number[][];
  corr_shrunk: number[][];
  shrinkage_delta: number;
  hrp_tree: HrpNode;
  hrp_order: string[];
  data_start: string;
  data_end: string;
}

const mathExtras = mathExtrasJson as MathExtras;

export const metadata: Metadata = {
  title: "Methodology",
  description:
    "The math behind Argmin: mean-variance, shrinkage, risk parity, HRP, max-diversification, Black-Litterman, and deflated significance, on live data.",
};

const TOC = [
  { id: "mean-variance", label: "01 Mean-variance & frontier" },
  { id: "shrinkage", label: "02 Ledoit-Wolf shrinkage" },
  { id: "risk-parity", label: "03 Risk parity (ERC)" },
  { id: "hrp", label: "04 Hierarchical risk parity" },
  { id: "max-div", label: "05 Maximum diversification" },
  { id: "black-litterman", label: "06 Black-Litterman" },
  { id: "significance", label: "07 PSR / DSR significance" },
  { id: "reconciliation", label: "08 Reconciliation" },
  { id: "honesty", label: "09 Honesty & limitations" },
  { id: "references", label: "References" },
];

export default function MathPage() {
  const m = defaultScenario.backtest.strategies.max_sharpe.metrics;
  const prov = defaultScenario.backtest.provenance;
  const sig = defaultScenario.backtest.significance;
  const ms = sig.strategies.max_sharpe;

  return (
    <main className="mx-auto max-w-[1100px] px-5 py-12 md:py-16">
      {/* Header */}
      <header className="max-w-[72ch]">
        <h1 className="text-4xl font-semibold tracking-tight text-fg md:text-5xl">
          The math, shown.
        </h1>
        <p className="mt-4 text-[16px] leading-relaxed text-fg-dim">
          Every optimizer in Argmin is implemented from scratch in NumPy, SciPy, and
          CVXPY - no portfolio library does the work for us. This page states each model
          as a convex program, derives the closed forms where they exist, and renders the
          intermediate objects (shrunk covariance, linkage tree, bootstrap distribution)
          from the same engine output that drives the backtest. Numbers here reconcile
          with the tearsheet on a single fixed window.
        </p>
        <div className="mt-5 flex flex-wrap items-center gap-2">
          <Badge tone="accent" dot>
            Out-of-sample only
          </Badge>
          <Badge>
            {mathExtras.data_start} → {mathExtras.data_end}
          </Badge>
          <Badge>
            {mathExtras.tickers.length}-asset universe
          </Badge>
          <Badge>
            r<sub>f</sub> = {pct(prov.risk_free, 0)}
          </Badge>
          <Badge>engine {prov.engine_hash}</Badge>
        </div>
      </header>

      {/* Notation + TOC */}
      <Reveal className="mt-10 grid items-start gap-4 md:grid-cols-[1.4fr_1fr]">
        <Panel>
          <PanelHeader label="Notation" hint="used throughout" />
          <div className="grid grid-cols-1 gap-x-6 gap-y-2.5 px-4 py-4 text-[13.5px] text-fg-dim sm:grid-cols-2">
            {[
              { t: "w \\in \\mathbb{R}^{n}", d: "portfolio weights" },
              { t: "\\mu", d: "expected excess returns" },
              { t: "\\Sigma", d: "return covariance matrix" },
              { t: "\\sigma", d: "vector of asset volatilities" },
              { t: "\\mathbf{1}", d: "vector of ones" },
              { t: "r_f", d: "risk-free rate" },
              { t: "\\delta", d: "risk-aversion / shrinkage intensity" },
              { t: "\\rho_{ij}", d: "asset correlation" },
            ].map((row) => (
              <div key={row.t} className="flex items-baseline gap-2">
                <span className="text-fg">
                  <Equation tex={row.t} />
                </span>
                <span className="text-fg-faint">{row.d}</span>
              </div>
            ))}
          </div>
        </Panel>
        <Panel>
          <PanelHeader label="Contents" />
          <nav className="flex flex-col px-2 py-2">
            {TOC.map((t) => (
              <a
                key={t.id}
                href={`#${t.id}`}
                className="rounded-[3px] px-2 py-1.5 font-mono text-[12px] text-fg-dim transition-colors hover:bg-elevated hover:text-fg"
              >
                {t.label}
              </a>
            ))}
          </nav>
        </Panel>
      </Reveal>

      <div className="mt-4">
        {/* 01 - Mean-variance & frontier */}
        <ModelSection
          id="mean-variance"
          index="01"
          subtitle="Markowitz / tangency"
          title="Mean-variance & the efficient frontier"
          objective={
            "\\min_{w}\\; w^{\\top}\\Sigma w \\quad \\text{s.t.}\\quad \\mathbf{1}^{\\top}w = 1,\\; w \\ge 0"
          }
        >
          <p>
            Markowitz<Cite ids="markowitz1952" /> casts allocation as a trade-off between
            return and variance. Tracing the minimum-variance weight for each attainable
            return level sweeps out the efficient frontier. The long-only, fully-invested
            program above is a convex quadratic program; Argmin solves it with CVXPY
            (Clarabel/OSQP).
          </p>
          <p>
            The tangency (max-Sharpe) portfolio is the frontier point that maximizes the
            reward-to-risk ratio relative to the risk-free asset:
          </p>
          <Equation
            display
            tex={
              "S(w) = \\frac{(\\mu - r_f\\mathbf{1})^{\\top}w}{\\sqrt{w^{\\top}\\Sigma w}}"
            }
          />
          <Derivation label="Show derivation - GMV closed form">
            <p className="mb-2">
              Drop the no-short constraint and minimize variance subject only to the budget
              constraint. The Lagrangian is
            </p>
            <Equation
              display
              tex={
                "\\mathcal{L}(w,\\lambda) = \\tfrac12\\, w^{\\top}\\Sigma w - \\lambda(\\mathbf{1}^{\\top}w - 1)."
              }
            />
            <p className="my-2">
              Stationarity gives <Equation tex={"\\Sigma w = \\lambda \\mathbf{1}"} />, hence{" "}
              <Equation tex={"w = \\lambda\\,\\Sigma^{-1}\\mathbf{1}"} />. Enforcing{" "}
              <Equation tex={"\\mathbf{1}^{\\top}w = 1"} /> pins{" "}
              <Equation tex={"\\lambda = 1/(\\mathbf{1}^{\\top}\\Sigma^{-1}\\mathbf{1})"} />,
              so the global minimum-variance portfolio is
            </p>
            <Equation
              display
              tex={
                "w_{\\text{GMV}} = \\frac{\\Sigma^{-1}\\mathbf{1}}{\\mathbf{1}^{\\top}\\Sigma^{-1}\\mathbf{1}}."
              }
            />
            <p className="mt-2">
              The tangency portfolio follows analogously with{" "}
              <Equation tex={"w \\propto \\Sigma^{-1}(\\mu - r_f\\mathbf{1})"} />, then
              renormalized to the budget. Argmin uses the constrained QP rather than the
              raw inverse to honor <Equation tex={"w \\ge 0"} /> and stay numerically stable
              when <Equation tex={"\\Sigma"} /> is near-singular.
            </p>
          </Derivation>
        </ModelSection>

        {/* 02 - Ledoit-Wolf shrinkage */}
        <ModelSection
          id="shrinkage"
          index="02"
          subtitle="covariance estimation"
          title="Ledoit-Wolf shrinkage"
          objectiveLabel="Shrinkage estimator"
          objective={"\\hat{\\Sigma} = \\delta\\,F + (1-\\delta)\\,S"}
        >
          <p>
            The sample covariance <Equation tex={"S"} /> is unbiased but ill-conditioned
            when the number of assets is comparable to the sample length: its extreme
            eigenvalues are systematically distorted, which mean-variance amplifies into
            unstable weights. Ledoit and Wolf<Cite ids="ledoitwolf2004" /> shrink{" "}
            <Equation tex={"S"} /> toward a structured target <Equation tex={"F"} /> (here a
            constant-correlation matrix) by an intensity{" "}
            <Equation tex={"\\delta \\in [0,1]"} /> chosen to minimize expected Frobenius
            loss in closed form.
          </p>
          <p>
            On this window the optimal intensity is{" "}
            <span className="tnum text-fg">&delta; = {num(mathExtras.shrinkage_delta, 4)}</span>
            . A small <Equation tex={"\\delta"} /> means the sample matrix is already
            well-conditioned over 2007-2024; the estimator still removes the noisiest
            off-diagonal extremes, as the side-by-side below shows.
          </p>
          <div className="fig not-prose mt-6 max-w-[640px]">
            <CovHeatmap
              sample={mathExtras.corr_sample}
              shrunk={mathExtras.corr_shrunk}
              tickers={mathExtras.tickers}
              delta={mathExtras.shrinkage_delta}
            />
          </div>
        </ModelSection>

        {/* 03 - Risk parity (ERC) */}
        <ModelSection
          id="risk-parity"
          index="03"
          subtitle="equal risk contribution"
          title="Risk parity (ERC)"
          objective={
            "\\min_{w > 0}\\; \\tfrac12\\, w^{\\top}\\Sigma w - \\frac{1}{n}\\sum_{i=1}^{n}\\ln w_i"
          }
        >
          <p>
            Risk parity targets equal risk contributions rather than equal capital. The
            marginal risk of asset <Equation tex={"i"} /> is{" "}
            <Equation tex={"(\\Sigma w)_i"} />, so its risk contribution is{" "}
            <Equation tex={"\\text{RC}_i = w_i (\\Sigma w)_i"} />. The equal-risk-contribution
            portfolio satisfies
          </p>
          <Equation
            display
            tex={
              "w_i (\\Sigma w)_i = w_j (\\Sigma w)_j \\;=\\; \\text{const}, \\quad \\forall\\, i,j."
            }
          />
          <p>
            Argmin solves this through Spinu&apos;s<Cite ids="spinu2013" /> convex
            log-barrier formulation above: the unique interior minimizer has equal risk
            contributions after normalization, and the log term acts as a smooth barrier
            keeping every weight strictly positive.
          </p>
          <Derivation label="Show derivation - why the log-barrier yields ERC">
            <p className="mb-2">
              Setting the gradient of the objective to zero gives, component-wise,
            </p>
            <Equation display tex={"(\\Sigma w)_i - \\frac{1}{n\\,w_i} = 0 \\;\\Longrightarrow\\; w_i(\\Sigma w)_i = \\tfrac{1}{n}."} />
            <p className="mt-2">
              Every asset&apos;s risk contribution equals{" "}
              <Equation tex={"1/n"} /> of the total at the optimum, which is exactly the ERC
              condition. Rescaling to <Equation tex={"\\mathbf{1}^{\\top}w = 1"} /> preserves
              the equality, so the barrier solution is the budget-constrained risk-parity
              portfolio.
            </p>
          </Derivation>
        </ModelSection>

        {/* 04 - HRP */}
        <ModelSection
          id="hrp"
          index="04"
          subtitle="López de Prado 2016"
          title="Hierarchical risk parity"
          objectiveLabel="Correlation distance"
          objective={"d_{ij} = \\sqrt{\\tfrac12\\,(1 - \\rho_{ij})}"}
        >
          <p>
            HRP<Cite ids="lopezdeprado2016" /> avoids inverting{" "}
            <Equation tex={"\\Sigma"} /> entirely - the step that makes mean-variance
            fragile. It proceeds in three stages: (1) convert correlations to the distance
            metric above and build a hierarchical clustering tree; (2){" "}
            <em>quasi-diagonalize</em> by reordering assets so the most-correlated sit
            adjacent; (3) allocate top-down by{" "}
            <em>recursive bisection</em>, splitting each cluster&apos;s budget in inverse
            proportion to its variance.
          </p>
          <p>
            The dendrogram below is the actual linkage tree estimated on this universe;
            leaf order is the quasi-diagonal sequence the bisection then walks.
          </p>
          <div className="fig not-prose mt-6 max-w-[860px]">
            <Dendrogram tree={mathExtras.hrp_tree} order={mathExtras.hrp_order} />
          </div>
          <Derivation label="Show derivation - recursive bisection split">
            <p className="mb-2">
              For a cluster split into sub-clusters{" "}
              <Equation tex={"C_1, C_2"} /> with inverse-variance weighted variances{" "}
              <Equation tex={"\\tilde V_1, \\tilde V_2"} />, the fraction allocated to{" "}
              <Equation tex={"C_1"} /> is
            </p>
            <Equation display tex={"\\alpha = 1 - \\frac{\\tilde V_1}{\\tilde V_1 + \\tilde V_2},"} />
            <p className="mt-2">
              so the lower-variance branch receives the larger share. Applying this
              recursively down the tree yields the final weights without ever forming{" "}
              <Equation tex={"\\Sigma^{-1}"} />, which is why HRP is far more robust to
              estimation error out of sample.
            </p>
          </Derivation>
        </ModelSection>

        {/* 05 - Max diversification */}
        <ModelSection
          id="max-div"
          index="05"
          subtitle="Choueifaty & Coignard 2008"
          title="Maximum diversification"
          objectiveLabel="Diversification ratio"
          objective={
            "\\mathrm{DR}(w) = \\frac{w^{\\top}\\sigma}{\\sqrt{w^{\\top}\\Sigma w}}"
          }
        >
          <p>
            The diversification ratio<Cite ids="choueifaty2008" /> is the weighted average
            of asset volatilities divided by the portfolio volatility. It equals one only
            when assets are perfectly correlated and grows as the portfolio harvests
            diversification, so maximizing it,
          </p>
          <Equation
            display
            tex={
              "\\max_{w \\ge 0,\\, \\mathbf{1}^{\\top}w = 1}\\; \\frac{w^{\\top}\\sigma}{\\sqrt{w^{\\top}\\Sigma w}},"
            }
          />
          <p>
            produces the &ldquo;most diversified portfolio.&rdquo; The objective is
            scale-invariant; Argmin solves the equivalent convex problem of minimizing{" "}
            <Equation tex={"w^{\\top}\\Sigma w"} /> subject to{" "}
            <Equation tex={"w^{\\top}\\sigma = 1"} /> and then renormalizing.
          </p>
        </ModelSection>

        {/* 06 - Black-Litterman */}
        <ModelSection
          id="black-litterman"
          index="06"
          subtitle="Black & Litterman 1992"
          title="Black-Litterman"
          objectiveLabel="Posterior expected returns"
          objective={
            "\\mu_{\\text{BL}} = \\big[(\\tau\\Sigma)^{-1} + P^{\\top}\\Omega^{-1}P\\big]^{-1}\\big[(\\tau\\Sigma)^{-1}\\pi + P^{\\top}\\Omega^{-1}Q\\big]"
          }
        >
          <p>
            Black-Litterman<Cite ids="blacklitterman1992" /> starts from market-implied
            equilibrium returns obtained by reverse optimization,
          </p>
          <Equation display tex={"\\pi = \\delta\\,\\Sigma\\, w_{\\text{mkt}},"} />
          <p>
            where <Equation tex={"\\delta"} /> is the market risk-aversion and{" "}
            <Equation tex={"w_{\\text{mkt}}"} /> the market-cap weights. Investor views are
            encoded as <Equation tex={"P\\mu = Q"} /> with uncertainty{" "}
            <Equation tex={"\\Omega"} />, and the posterior above is the precision-weighted
            blend of the prior <Equation tex={"\\pi"} /> and the views{" "}
            <Equation tex={"Q"} />. With no views it collapses to{" "}
            <Equation tex={"\\mu_{\\text{BL}} = \\pi"} />, recovering the equilibrium
            portfolio - which is the regularized prior that tames mean-variance&apos;s
            sensitivity to noisy <Equation tex={"\\mu"} />.
          </p>
          <p className="text-[14px] text-fg-faint">
            Note: Argmin uses an equal-weight market proxy (no live market-cap feed), so{" "}
            <Equation tex={"\\pi"} /> reflects a 1/N reference rather than true float
            weights. This is stated again in the limitations.
          </p>
        </ModelSection>

        {/* 07 - Significance */}
        <ModelSection
          id="significance"
          index="07"
          subtitle="Bailey & López de Prado 2014"
          title="Probabilistic & deflated Sharpe"
          objectiveLabel="Probabilistic Sharpe ratio"
          objective={
            "\\widehat{\\text{PSR}}(S^{*}) = \\Phi\\!\\left(\\frac{(\\hat S - S^{*})\\sqrt{T-1}}{\\sqrt{1 - \\hat\\gamma_3\\,\\hat S + \\frac{\\hat\\gamma_4 - 1}{4}\\,\\hat S^{2}}}\\right)"
          }
        >
          <p>
            A Sharpe ratio is itself an estimate with sampling error, and that error is
            larger for skewed, fat-tailed returns. The probabilistic Sharpe
            ratio<Cite ids="bailey2014" /> gives the probability that the true Sharpe
            exceeds a benchmark <Equation tex={"S^{*}"} />, adjusting for skewness{" "}
            <Equation tex={"\\hat\\gamma_3"} /> and kurtosis{" "}
            <Equation tex={"\\hat\\gamma_4"} /> of the returns.
          </p>
          <p>
            When many strategies are tried, the best in-sample Sharpe is upward-biased. The
            deflated Sharpe ratio corrects for this multiple-testing by raising the
            benchmark to the expected maximum of <Equation tex={"N"} /> trials:
          </p>
          <Equation
            display
            tex={
              "S^{*} = \\sqrt{\\widehat{\\mathrm{Var}}(\\hat S)}\\,\\Big[(1-\\gamma)\\,\\Phi^{-1}\\!\\big(1 - \\tfrac1N\\big) + \\gamma\\,\\Phi^{-1}\\!\\big(1 - \\tfrac{1}{N}e^{-1}\\big)\\Big]"
            }
          />
          <p>
            Here <Equation tex={"\\gamma"} /> is the Euler-Mascheroni constant and{" "}
            <Equation tex={"N"} /> the number of trials. Argmin deflates over{" "}
            <span className="tnum text-fg">{sig.dsr_trials}</span> candidate strategies. We
            also report a block-bootstrap confidence interval (block size{" "}
            <span className="tnum text-fg">{sig.bootstrap_block_size}</span> days,{" "}
            <span className="tnum text-fg">{sig.bootstrap_samples.toLocaleString()}</span>{" "}
            resamples) to preserve autocorrelation in the resampled returns.
          </p>
          <div className="fig not-prose mt-6 max-w-[720px]">
            <BootstrapDist
              sharpe={ms.sharpe}
              ciLow={ms.sharpe_ci_low}
              ciHigh={ms.sharpe_ci_high}
              samples={sig.bootstrap_samples}
            />
          </div>
          <div className="fig not-prose mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Panel className="px-4 py-3">
              <Stat label="PSR" value={pct(m.psr ?? 0, 1)} tone="accent" />
            </Panel>
            <Panel className="px-4 py-3">
              <Stat label="DSR" value={pct(m.dsr ?? 0, 1)} tone="accent" />
            </Panel>
            <Panel className="px-4 py-3">
              <Stat label="Sharpe (OOS)" value={num(m.sharpe, 2)} />
            </Panel>
            <Panel className="px-4 py-3">
              <Stat
                label="95% CI"
                value={
                  <span className="text-[15px]">
                    [{num(ms.sharpe_ci_low, 2)}, {num(ms.sharpe_ci_high, 2)}]
                  </span>
                }
              />
            </Panel>
          </div>
        </ModelSection>

        {/* 08 - Reconciliation */}
        <section
          id="reconciliation"
          className="mt-10 scroll-mt-20 border-t border-line pt-10"
        >
          <span className="font-mono text-[12px] tracking-tight text-fg-faint">&sect;&thinsp;08</span>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-fg">
            Reconciliation with the tearsheet
          </h2>
          <p className="mt-4 max-w-[68ch] text-[15px] leading-relaxed text-fg-dim">
            The same max-Sharpe strategy headline numbers shown on{" "}
            <a href="/explore" className="text-accent hover:underline">
              /explore
            </a>{" "}
            are reproduced below verbatim from the backtest tearsheet. They are out-of-sample,
            net of transaction costs, on the {mathExtras.data_start} → {mathExtras.data_end}{" "}
            window.
          </p>
          <Panel className="mt-5">
            <PanelHeader
              label="Max Sharpe - out-of-sample"
              hint={`engine ${prov.engine_hash} · generated ${prov.generated_utc.slice(0, 10)}`}
            />
            <div className="grid grid-cols-2 gap-x-6 gap-y-5 px-5 py-5 sm:grid-cols-4">
              <Stat label="CAGR" value={pct(m.cagr, 1)} tone="pos" />
              <Stat label="Ann. vol" value={pct(m.ann_vol, 1)} />
              <Stat label="Sharpe" value={num(m.sharpe, 2)} tone="accent" />
              <Stat label="Sortino" value={num(m.sortino, 2)} />
              <Stat label="Max drawdown" value={pct(m.max_drawdown, 1)} tone="neg" />
              <Stat label="Calmar" value={num(m.calmar, 2)} />
              <Stat
                label="Avg turnover"
                value={m.avg_turnover != null ? pct(m.avg_turnover, 1) : "-"}
              />
              <Stat label="Hit rate" value={pct(m.hit_rate, 1)} />
            </div>
            <Hairline />
            <div className="flex flex-wrap items-center gap-x-6 gap-y-1.5 px-5 py-3 font-mono text-[11px] text-fg-faint">
              <span>
                total return <span className="tnum text-fg-dim">{pct(m.total_return, 1)}</span>
              </span>
              <span>
                VaR<sub>95</sub> <span className="tnum text-fg-dim">{pct(m.var_95, 2)}</span>
              </span>
              <span>
                CVaR<sub>95</sub> <span className="tnum text-fg-dim">{pct(m.cvar_95, 2)}</span>
              </span>
              <span>
                r<sub>f</sub> <span className="tnum text-fg-dim">{pct(prov.risk_free, 0)}</span>
              </span>
              <span className="text-fg-faint">
                oos_only = {String(prov.oos_only)}
              </span>
            </div>
          </Panel>
        </section>

        {/* 09 - Honesty & limitations */}
        <section id="honesty" className="mt-10 scroll-mt-20 border-t border-line pt-10">
          <span className="font-mono text-[12px] tracking-tight text-fg-faint">&sect;&thinsp;09</span>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-fg">
            Honesty & limitations
          </h2>
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            {[
              {
                h: "Not investment advice",
                b: "This is a research and engineering portfolio piece. Nothing here is a recommendation to buy or sell any security. Past performance does not predict future results.",
              },
              {
                h: "Estimation error dominates",
                b: "Expected returns are notoriously hard to estimate; small errors in μ swing mean-variance weights sharply. Shrinkage, risk parity, and HRP exist precisely to blunt this, and we still report deflated, not raw, significance.",
              },
              {
                h: "Equal-weight market proxy",
                b: "Black-Litterman equilibrium returns π use a 1/N market proxy rather than live market-cap weights, since the engine ships no live cap feed. Treat the BL prior as illustrative.",
              },
              {
                h: "Constant risk-free rate",
                b: `A flat ${pct(prov.risk_free, 0)} risk-free rate is assumed over the whole window rather than a rolling short-rate series. This slightly biases Sharpe levels but not the relative ranking of strategies.`,
              },
              {
                h: "Out-of-sample, with costs",
                b: "All reported metrics come from a walk-forward backtest: parameters are fit on a rolling lookback and evaluated only on subsequent, unseen returns, net of transaction costs. In-sample numbers are never reported as if they were OOS.",
              },
              {
                h: "Single fixed window",
                b: `Results are one realization on ${mathExtras.data_start} to ${mathExtras.data_end}. They are not bootstrapped across alternative universes or regimes; the confidence interval quantifies sampling uncertainty within this window only.`,
              },
            ].map((card, i) => (
              <Reveal key={card.h} delay={(i % 2) * 0.08} y={24}>
                <Panel className="h-full px-5 py-4 transition-colors duration-200 hover:border-line-strong">
                  <h3 className="text-[16px] font-medium tracking-[-0.01em] text-fg">{card.h}</h3>
                  <p className="mt-2 text-[13.5px] leading-relaxed text-fg-dim">{card.b}</p>
                </Panel>
              </Reveal>
            ))}
          </div>
        </section>

        {/* References */}
        <section id="references" className="mt-10 scroll-mt-20 border-t border-line pt-10">
          <h2 className="text-2xl font-semibold tracking-tight text-fg">Sources</h2>
          <Reveal className="mt-5 max-w-[80ch]">
            <References />
          </Reveal>
        </section>
      </div>
    </main>
  );
}
