"use client";

import "katex/dist/katex.min.css";
import katex from "katex";
import { useMemo } from "react";

import { cn } from "@/lib/cn";

/** Render a TeX string with KaTeX, themed to inherit the page foreground. */
export function Equation({
  tex,
  display = false,
  className,
}: {
  tex: string;
  display?: boolean;
  className?: string;
}) {
  const html = useMemo(
    () =>
      katex.renderToString(tex, {
        displayMode: display,
        throwOnError: false,
        output: "html",
      }),
    [tex, display],
  );
  return (
    <span
      className={cn(display && "block", className)}
      // KaTeX output is sanitized by the library
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
