"use client";

import { animate, useReducedMotion } from "motion/react";
import { useEffect, useRef, useState } from "react";

/**
 * Tweens to its target whenever `value` changes (e.g. after a re-run), so
 * headline metrics visibly move instead of snapping. Initial mount does not
 * animate; reduced-motion snaps. Server and client first-render the same string,
 * so no hydration mismatch.
 */
export function AnimatedNumber({
  value,
  format,
  duration = 0.7,
}: {
  value: number;
  format: (v: number) => string;
  duration?: number;
}) {
  const reduced = useReducedMotion();
  const [display, setDisplay] = useState(value);
  const prev = useRef(value);

  useEffect(() => {
    if (prev.current === value) return;
    const from = prev.current;
    prev.current = value;
    const controls = animate(from, value, {
      duration: reduced ? 0 : duration,
      ease: [0.16, 1, 0.3, 1],
      onUpdate: (v) => setDisplay(v),
    });
    return () => controls.stop();
  }, [value, duration, reduced]);

  return <>{format(display)}</>;
}
