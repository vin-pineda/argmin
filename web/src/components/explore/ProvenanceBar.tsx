"use client";

import { Badge } from "@/components/ui/primitives";
import type { Provenance } from "@/lib/api/types";
import { dateOnly, pct } from "@/lib/format";

/** Inline provenance strip - keeps the numbers honest and self-describing. */
export function ProvenanceBar({
  provenance,
  rebalance,
  costBps,
}: {
  provenance: Provenance;
  rebalance: string;
  costBps: number;
}) {
  const items: { label: string; value: string }[] = [
    {
      label: "window",
      value: `${dateOnly(provenance.data_start)} → ${dateOnly(provenance.data_end)}`,
    },
    { label: "rebalance", value: rebalance },
    { label: "cost", value: `${costBps} bps` },
    { label: "risk-free", value: pct(provenance.risk_free, 1) },
    { label: "engine", value: provenance.engine_hash },
  ];

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-2.5 text-[11px]">
      <Badge tone="accent" dot>
        OOS-only
      </Badge>
      {items.map((it) => (
        <div key={it.label} className="flex items-baseline gap-1.5">
          <span className="font-mono tracking-tight text-fg-faint">{it.label}</span>
          <span className="tnum text-fg-dim">{it.value}</span>
        </div>
      ))}
    </div>
  );
}
