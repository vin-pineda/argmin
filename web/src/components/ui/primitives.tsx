import * as React from "react";

import { cn } from "@/lib/cn";

/** A bordered surface tile. Used only where dense data needs a container —
 *  hairlines do the rest of the separating. No border + soft-shadow pairing. */
export function Panel({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("rounded-[var(--radius)] border border-line bg-panel", className)}
      {...props}
    >
      {children}
    </div>
  );
}

/** A panel/region title: sentence-case serif (the paper voice), with an optional
 *  mono hint and a right slot, divided by a hairline. Replaces the old
 *  uppercase-mono eyebrow that sat on every block. */
export function PanelHeader({
  label,
  hint,
  right,
}: {
  label: string;
  hint?: string;
  right?: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-2.5">
      <div className="flex items-baseline gap-2.5">
        <h2 className="text-[15px] leading-none font-medium tracking-[-0.01em] text-fg">{label}</h2>
        {hint ? (
          <span className="font-mono text-[11px] tracking-tight text-fg-faint">{hint}</span>
        ) : null}
      </div>
      {right}
    </div>
  );
}

/** A labelled metric: dim mono label, large mono value, optional caption. */
export function Stat({
  label,
  value,
  caption,
  tone = "neutral",
  className,
}: {
  label: string;
  value: React.ReactNode;
  caption?: React.ReactNode;
  tone?: "neutral" | "pos" | "neg" | "accent";
  className?: string;
}) {
  const toneClass =
    tone === "pos"
      ? "text-pos"
      : tone === "neg"
        ? "text-neg"
        : tone === "accent"
          ? "text-accent"
          : "text-fg";
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <span className="font-mono text-[11px] tracking-tight text-fg-dim">{label}</span>
      <span className={cn("tnum text-2xl leading-none", toneClass)}>{value}</span>
      {caption ? <span className="text-[12px] text-fg-faint">{caption}</span> : null}
    </div>
  );
}

export function Hairline({ className }: { className?: string }) {
  return <div className={cn("h-px w-full bg-line", className)} />;
}

/** A hairline tag (no fill). Emphasis comes from a leading status dot in the
 *  signal color, not a tinted background. Replaces the old amber pill badge. */
export function Badge({
  children,
  tone = "neutral",
  dot = false,
  className,
}: {
  children: React.ReactNode;
  tone?: "neutral" | "accent" | "pos";
  dot?: boolean;
  className?: string;
}) {
  const dotColor =
    tone === "accent" ? "bg-accent" : tone === "pos" ? "bg-pos" : "bg-fg-faint";
  const textColor = tone === "accent" ? "text-fg" : tone === "pos" ? "text-fg" : "text-fg-dim";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-[3px] border border-line-strong px-2 py-[3px]",
        "font-mono text-[10.5px] tracking-tight whitespace-nowrap",
        textColor,
        className,
      )}
    >
      {dot ? <span className={cn("h-1.5 w-1.5 rounded-full", dotColor)} aria-hidden /> : null}
      {children}
    </span>
  );
}
