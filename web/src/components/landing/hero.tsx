"use client";

import { ArrowRight, BookOpen } from "@phosphor-icons/react";
import { motion } from "motion/react";
import Link from "next/link";

import { Badge } from "@/components/ui/primitives";
import { Button } from "@/components/ui/button";
import { FrontierViz } from "@/components/charts/frontier-viz";
import type { FrontierResult } from "@/lib/api/types";

const EASE = [0.16, 1, 0.3, 1] as const;

export function Hero({
  frontier,
  dataStart,
  dataEnd,
}: {
  frontier: FrontierResult;
  dataStart: string;
  dataEnd: string;
}) {
  // Same initial on server + client (reduced motion handled by MotionConfig),
  // so there's no hydration mismatch.
  const enter = (delay: number) => ({
    initial: { opacity: 0, y: 14 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.7, ease: EASE, delay },
  });

  return (
    <section className="relative min-h-[100dvh] border-b border-line">
      <div className="mx-auto grid max-w-[1400px] grid-cols-1 items-center gap-10 px-5 pb-16 pt-10 lg:min-h-[calc(100dvh-3.5rem)] lg:grid-cols-[0.92fr_1.18fr] lg:gap-16 lg:pb-0 lg:pt-0">
        {/* Left: thesis + actions */}
        <div className="flex flex-col">
          <motion.div {...enter(0)} className="flex flex-wrap items-center gap-2.5">
            <Badge tone="accent" dot>
              OOS-only
            </Badge>
            <span className="tnum text-[12px] text-fg-dim">
              walk-forward {dataStart} &rarr; {dataEnd}
            </span>
          </motion.div>

          <motion.h1
            {...enter(0.08)}
            className="mt-6 max-w-xl text-balance text-[2.6rem] leading-[1.06] font-semibold text-fg sm:text-[3.4rem]"
          >
            Naive in-sample frontiers lie.
            <span className="block text-fg-dim italic">This one is tested honestly.</span>
          </motion.h1>

          <motion.p
            {...enter(0.16)}
            className="mt-5 max-w-md text-[16px] leading-relaxed text-fg-dim"
          >
            Seven allocation models, evaluated out-of-sample with transaction costs,
            benchmarks, and significance tests. The math, shown.
          </motion.p>

          <motion.div {...enter(0.24)} className="mt-8 flex flex-wrap items-center gap-3">
            <Button asChild variant="primary">
              <Link href="/explore">
                Open the explorer
                <ArrowRight size={16} weight="bold" />
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link href="/math">
                <BookOpen size={16} />
                Read the methodology
              </Link>
            </Button>
          </motion.div>
        </div>

        {/* Right: the efficient frontier, drawn from real engine geometry */}
        <motion.div
          {...enter(0.2)}
          className="relative aspect-[16/11] w-full overflow-hidden rounded-[var(--radius)] border border-line bg-panel sm:aspect-[16/10] lg:aspect-auto lg:h-[min(72vh,620px)]"
        >
          <div className="absolute inset-0 p-3 pb-9 sm:p-4 sm:pb-10">
            <FrontierViz data={frontier} />
          </div>
          <div className="pointer-events-none absolute inset-x-0 bottom-0 flex items-center justify-between border-t border-line bg-bg/70 px-3 py-1.5 backdrop-blur-sm">
            <span className="font-mono text-[11px] tracking-tight text-fg-faint">
              mean-variance frontier
            </span>
            <span className="font-mono text-[11px] text-fg-faint">
              argmin&#8201;w&#7488;&#931;w
            </span>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
