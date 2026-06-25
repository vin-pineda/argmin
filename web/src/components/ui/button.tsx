import { Slot } from "@radix-ui/react-slot";
import * as React from "react";

import { cn } from "@/lib/cn";

type Variant = "primary" | "outline" | "ghost";
type Size = "sm" | "md";

const variants: Record<Variant, string> = {
  primary: "bg-accent text-bg hover:bg-accent-bright font-medium",
  outline: "border border-line-strong text-fg hover:bg-elevated hover:border-fg-faint",
  ghost: "text-fg-dim hover:text-fg hover:bg-elevated",
};

const sizes: Record<Size, string> = {
  sm: "h-7 px-3 text-xs",
  md: "h-9 px-4 text-sm",
};

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "outline", size = "md", asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center gap-2 rounded-[var(--radius)] whitespace-nowrap",
          // the apparatus speaks mono: you read in serif, you act in mono
          "font-mono tracking-[-0.01em]",
          "transition-all duration-200 ease-out active:translate-y-0 active:scale-[0.98]",
          "disabled:pointer-events-none disabled:opacity-45",
          variants[variant],
          sizes[size],
          className,
        )}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";
