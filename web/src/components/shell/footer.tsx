import Link from "next/link";

import { defaultScenario } from "@/lib/api/scenario";
import { dateOnly } from "@/lib/format";

export function Footer() {
  const prov = defaultScenario.optimize.provenance!;
  return (
    <footer className="mt-24 border-t border-line">
      <div className="mx-auto max-w-[1400px] px-5 py-10">
        <div className="flex flex-col gap-8 md:flex-row md:items-start md:justify-between">
          <div className="max-w-md">
            <div className="font-mono text-sm font-semibold text-fg">argmin</div>
            <p className="mt-2 text-[13px] leading-relaxed text-fg-dim">
              The argument of the minimum. Every allocation model here is the{" "}
              <span className="text-fg">argmin</span> of a risk or cost objective over the weight
              simplex, evaluated out-of-sample with transaction costs.
            </p>
            <p className="mt-3 text-[12px] leading-relaxed text-fg-faint">
              Not investment advice. All results are historical, out-of-sample backtests for
              research and demonstration only. Past performance does not predict future returns.
            </p>
          </div>

          <div className="flex gap-12">
            <div className="flex flex-col gap-2 text-[13px]">
              <span className="font-mono text-[11px] tracking-tight text-fg-faint">
                Navigate
              </span>
              <Link href="/" className="text-fg-dim hover:text-fg">
                Overview
              </Link>
              <Link href="/explore" className="text-fg-dim hover:text-fg">
                Explore
              </Link>
              <Link href="/math" className="text-fg-dim hover:text-fg">
                Methodology
              </Link>
            </div>
            <div className="flex flex-col gap-2 text-[13px]">
              <span className="font-mono text-[11px] tracking-tight text-fg-faint">
                Provenance
              </span>
              <span className="tnum text-[12px] text-fg-dim">
                data {dateOnly(prov.data_start)} → {dateOnly(prov.data_end)}
              </span>
              <span className="tnum text-[12px] text-fg-dim">rf {(prov.risk_free * 100).toFixed(1)}%</span>
              <span className="tnum text-[12px] text-fg-dim">engine {prov.engine_hash}</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
