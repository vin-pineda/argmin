import { Reveal } from "@/components/landing/reveal";
import { Equation } from "@/components/ui/equation";
import { cn } from "@/lib/cn";

/** A methodology section: index eyebrow, title, the governing objective rendered
 *  as a first-class KaTeX block, prose, then any extra content (charts,
 *  derivations, callouts) passed as children. */
export function ModelSection({
  id,
  index,
  title,
  subtitle,
  objective,
  objectiveLabel = "Objective",
  children,
  className,
}: {
  id: string;
  index: string;
  title: string;
  subtitle?: string;
  objective: string;
  objectiveLabel?: string;
  children?: React.ReactNode;
  className?: string;
}) {
  return (
    <section
      id={id}
      className={cn("scroll-mt-20 border-t border-line pt-10", className)}
      aria-labelledby={`${id}-title`}
    >
      <Reveal>
        <div className="flex items-baseline gap-3">
          <span className="font-mono text-[12px] tracking-tight text-fg-faint">&sect;&thinsp;{index}</span>
          {subtitle ? (
            <span className="font-mono text-[11px] text-fg-faint">{subtitle}</span>
          ) : null}
        </div>
        <h2 id={`${id}-title`} className="mt-2 text-[1.7rem] leading-tight font-semibold text-fg">
          {title}
        </h2>
      </Reveal>

      {/* Governing equation as a typographic object. */}
      <Reveal delay={0.08}>
        <figure className="mt-5 rounded-[var(--radius)] border border-line bg-elevated/40 px-5 py-4">
          <figcaption className="mb-2 font-mono text-[11px] tracking-tight text-fg-faint">
            {objectiveLabel}
          </figcaption>
          <div className="overflow-x-auto text-fg">
            <Equation tex={objective} display />
          </div>
        </figure>
      </Reveal>

      {/* Prose stays at a readable measure; figures (charts) break wider and
          center via `.fig` so they don't sit narrow and left-aligned. */}
      <Reveal
        delay={0.14}
        className="model-prose mt-5 space-y-4 text-[15px] leading-relaxed text-fg-dim"
      >
        {children}
      </Reveal>
    </section>
  );
}
