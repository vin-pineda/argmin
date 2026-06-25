import { ArrowRight } from "@phosphor-icons/react/dist/ssr";
import Link from "next/link";

import { Button } from "@/components/ui/button";

import { Reveal } from "./reveal";

/** Closing band: send the reader into the live explorer. */
export function CtaBand() {
  return (
    <section>
      <div className="mx-auto max-w-[1400px] px-5 py-20 sm:py-28">
        <Reveal className="flex flex-col items-start gap-6 sm:items-center sm:text-center">
          <h2 className="max-w-xl text-balance text-2xl font-semibold tracking-tight text-fg sm:text-4xl">
            Build a portfolio, backtested out-of-sample.
          </h2>
          <p className="max-w-md text-[14px] leading-relaxed text-fg-dim">
            Pick a universe, choose a model, and step through the walk-forward run with
            costs, benchmarks, and significance tests in view.
          </p>
          <Button asChild variant="primary" className="h-10 px-5">
            <Link href="/explore">
              Open the explorer
              <ArrowRight size={16} weight="bold" />
            </Link>
          </Button>
        </Reveal>
      </div>
    </section>
  );
}
