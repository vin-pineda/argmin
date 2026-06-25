"use client";

import { motion } from "motion/react";
import type { ReactNode } from "react";

const EASE = [0.16, 1, 0.3, 1] as const;

/**
 * Scroll-triggered "open up" reveal. Content stays in the DOM (opacity-based, so
 * it's accessible / indexable); it animates into view as the user scrolls.
 * Transform + opacity only, so it stays smooth. Reduced motion is neutralized by
 * the app-level <MotionConfig reducedMotion="user">; the initial state is the
 * same on server and client, so there's no hydration mismatch.
 */
export function Reveal({
  children,
  delay = 0,
  y = 30,
  className,
  as = "div",
}: {
  children: ReactNode;
  delay?: number;
  y?: number;
  className?: string;
  as?: "div" | "section" | "li";
}) {
  const Tag = motion[as];
  return (
    <Tag
      className={className}
      initial={{ opacity: 0, y, scale: 0.985 }}
      whileInView={{ opacity: 1, y: 0, scale: 1 }}
      viewport={{ once: true, amount: 0.2, margin: "0px 0px -8% 0px" }}
      transition={{ duration: 0.7, ease: EASE, delay }}
    >
      {children}
    </Tag>
  );
}
