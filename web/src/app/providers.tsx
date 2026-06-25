"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MotionConfig } from "motion/react";
import { useState } from "react";

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { staleTime: 60_000, refetchOnWindowFocus: false, retry: 1 },
        },
      }),
  );
  // `reducedMotion="user"` lets Motion neutralize transform/layout animations for
  // users who ask for it, without us branching on useReducedMotion() in render
  // (that branch caused an SSR/client hydration mismatch).
  return (
    <MotionConfig reducedMotion="user">
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    </MotionConfig>
  );
}
