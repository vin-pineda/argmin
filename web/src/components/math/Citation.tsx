import { cn } from "@/lib/cn";

/** A single bibliographic reference. */
export interface Reference {
  id: string;
  authors: string;
  year: number;
  title: string;
  venue: string;
}

/** Ordered reference registry for the methodology page. The index in this list
 *  (1-based) is the superscript number rendered inline by <Cite />. */
export const REFERENCES: Reference[] = [
  {
    id: "markowitz1952",
    authors: "Markowitz, H.",
    year: 1952,
    title: "Portfolio Selection",
    venue: "The Journal of Finance 7(1), 77-91",
  },
  {
    id: "ledoitwolf2004",
    authors: "Ledoit, O. & Wolf, M.",
    year: 2004,
    title: "A Well-Conditioned Estimator for Large-Dimensional Covariance Matrices",
    venue: "Journal of Multivariate Analysis 88(2), 365-411",
  },
  {
    id: "spinu2013",
    authors: "Spinu, F.",
    year: 2013,
    title: "An Algorithm for Computing Risk Parity Weights",
    venue: "SSRN Working Paper 2297383",
  },
  {
    id: "blacklitterman1992",
    authors: "Black, F. & Litterman, R.",
    year: 1992,
    title: "Global Portfolio Optimization",
    venue: "Financial Analysts Journal 48(5), 28-43",
  },
  {
    id: "choueifaty2008",
    authors: "Choueifaty, Y. & Coignard, Y.",
    year: 2008,
    title: "Toward Maximum Diversification",
    venue: "The Journal of Portfolio Management 35(1), 40-51",
  },
  {
    id: "lopezdeprado2016",
    authors: "López de Prado, M.",
    year: 2016,
    title: "Building Diversified Portfolios that Outperform Out of Sample",
    venue: "The Journal of Portfolio Management 42(4), 59-69",
  },
  {
    id: "bailey2014",
    authors: "Bailey, D. H. & López de Prado, M.",
    year: 2014,
    title: "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality",
    venue: "The Journal of Portfolio Management 40(5), 94-107",
  },
];

const indexOf = (id: string): number => REFERENCES.findIndex((r) => r.id === id);

/** Inline superscript citation marker. Accepts one or more reference ids. */
export function Cite({ ids, className }: { ids: string | string[]; className?: string }) {
  const list = Array.isArray(ids) ? ids : [ids];
  const nums = list
    .map((id) => indexOf(id))
    .filter((i) => i >= 0)
    .map((i) => i + 1);
  if (nums.length === 0) return null;
  return (
    <sup className={cn("ml-0.5 font-mono text-[10px] text-accent/85 tnum", className)}>
      [{nums.join(",")}]
    </sup>
  );
}

/** The references block: numbered list keyed to the inline markers. */
export function References({ className }: { className?: string }) {
  return (
    <ol className={cn("flex flex-col gap-2.5", className)}>
      {REFERENCES.map((r, i) => (
        <li key={r.id} id={r.id} className="flex gap-3 text-[13px] leading-relaxed">
          <span className="shrink-0 font-mono text-[11px] text-accent/80 tnum">
            [{i + 1}]
          </span>
          <span className="text-fg-dim">
            <span className="text-fg">{r.authors}</span> ({r.year}).{" "}
            <span className="italic">{r.title}.</span>{" "}
            <span className="text-fg-faint">{r.venue}.</span>
          </span>
        </li>
      ))}
    </ol>
  );
}
