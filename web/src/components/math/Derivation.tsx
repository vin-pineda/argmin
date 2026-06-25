"use client";

import { CaretRight } from "@phosphor-icons/react";
import { AnimatePresence, motion } from "motion/react";
import { useId, useState } from "react";

import { cn } from "@/lib/cn";

/** A "show derivation" disclosure. Button toggles a height/opacity reveal of the
 *  derivation steps. Reduced motion shows/hides instantly. */
export function Derivation({
  label = "Show derivation",
  children,
  className,
}: {
  label?: string;
  children: React.ReactNode;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const panelId = useId();

  return (
    <div className={cn("mt-3", className)}>
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "-ml-1.5 inline-flex items-center gap-1.5 rounded-[3px] px-1.5 py-1",
          "font-mono text-[12px] tracking-tight",
          "text-accent/85 transition-colors hover:text-accent",
        )}
      >
        <motion.span
          animate={{ rotate: open ? 90 : 0 }}
          transition={{ duration: 0.18, ease: "easeOut" }}
          className="inline-flex"
          aria-hidden
        >
          <CaretRight size={12} weight="bold" />
        </motion.span>
        {open ? "Hide derivation" : label}
      </button>

      <AnimatePresence initial={false}>
        {open ? (
          <motion.div
            id={panelId}
            key="content"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.24, ease: [0.22, 1, 0.36, 1] }}
            className="overflow-hidden"
          >
            <div className="mt-2 border-l border-line pl-4 text-[13.5px] leading-relaxed text-fg-dim">
              {children}
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}
