import { ArrowUpRight } from "@phosphor-icons/react/dist/ssr";
import Link from "next/link";

import { cn } from "@/lib/cn";

import { Reveal } from "./reveal";

interface Model {
  id: string;
  name: string;
  tag: string;
  blurb: string;
  feature?: boolean;
  wide?: boolean;
}

/** The seven objects on the bench, laid out as a balanced asymmetric bento:
 *  [Max Sharpe ·2][Frontier ·1] / [Min-Var][Max-Div][Risk Parity] /
 *  [HRP ·2][Black-Litterman ·1]. Two wide anchors per the brief, no empty cells. */
const MODELS: Model[] = [
  {
    id: "max_sharpe",
    name: "Max Sharpe",
    tag: "tangency",
    blurb:
      "The tangency portfolio: the highest risk-adjusted return on the efficient frontier.",
    feature: true,
    wide: true,
  },
  {
    id: "frontier",
    name: "Efficient Frontier",
    tag: "mean-variance",
    blurb: "Every argmin portfolio across the full risk spectrum, traced end to end.",
    feature: true,
  },
  {
    id: "min_variance",
    name: "Min Variance",
    tag: "lowest risk",
    blurb: "The single lowest-volatility mix, ignoring expected return entirely.",
  },
  {
    id: "max_diversification",
    name: "Max Diversification",
    tag: "ratio",
    blurb: "Maximizes weighted-average volatility over portfolio volatility.",
  },
  {
    id: "risk_parity",
    name: "Risk Parity",
    tag: "ERC",
    blurb: "Equalizes each asset's contribution to total risk, not its dollar weight.",
  },
  {
    id: "hrp",
    name: "Hierarchical Risk Parity",
    tag: "clustering",
    blurb: "Clusters assets by correlation, then allocates down the tree, no matrix inverse.",
    wide: true,
  },
  {
    id: "black_litterman",
    name: "Black-Litterman",
    tag: "Bayesian views",
    blurb: "Blends market-implied equilibrium returns with explicit subjective views.",
  },
];

function Tile({ model, index }: { model: Model; index: number }) {
  return (
    <Reveal
      delay={Math.min(index, 4) * 0.04}
      className={cn("min-w-0", model.wide && "lg:col-span-2")}
    >
      <Link
        href="/math"
        className={cn(
          "group relative flex h-full flex-col gap-3 rounded-[var(--radius)] border border-line bg-panel p-5",
          "transition-[transform,border-color,background-color,box-shadow] duration-200 ease-out",
          "hover:-translate-y-0.5 hover:border-line-strong hover:bg-elevated",
        )}
      >
        <div className="flex items-start justify-between gap-3">
          <span className="font-mono text-[11px] tracking-tight text-fg-faint transition-colors group-hover:text-accent/80">
            {model.tag}
          </span>
          <ArrowUpRight
            size={15}
            className="shrink-0 text-fg-faint transition-all duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-accent"
          />
        </div>
        <h3
          className={cn(
            "tracking-[-0.01em] text-fg",
            model.feature ? "text-xl font-semibold" : "text-[17px] font-medium",
          )}
        >
          {model.name}
        </h3>
        <p className="max-w-[46ch] text-[13.5px] leading-relaxed text-fg-dim">{model.blurb}</p>
      </Link>
    </Reveal>
  );
}

/** The seven-model gallery. Tiles link to the methodology page. */
export function ModelGallery() {
  return (
    <section className="border-b border-line">
      <div className="mx-auto max-w-[1400px] px-5 py-16 sm:py-24">
        <Reveal className="flex flex-col gap-3">
          <h2 className="max-w-2xl text-2xl font-semibold tracking-tight text-fg sm:text-3xl">
            Classical and modern allocation, side by side.
          </h2>
          <p className="max-w-xl text-[14px] leading-relaxed text-fg-dim">
            Each is implemented from scratch and run through the same honest, cost-aware
            backtest. Open any one for its full derivation.
          </p>
        </Reveal>

        <div className="mt-10 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {MODELS.map((m, i) => (
            <Tile key={m.id} model={m} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
