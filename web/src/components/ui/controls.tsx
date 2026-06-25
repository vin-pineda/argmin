"use client";

import * as SelectPrimitive from "@radix-ui/react-select";
import * as SliderPrimitive from "@radix-ui/react-slider";
import * as SwitchPrimitive from "@radix-ui/react-switch";
import { CaretDown, Check } from "@phosphor-icons/react";

import { cn } from "@/lib/cn";

export function Slider({
  value,
  onValueChange,
  min = 0,
  max = 100,
  step = 1,
  className,
  "aria-label": ariaLabel,
}: {
  value: number;
  onValueChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
  className?: string;
  "aria-label"?: string;
}) {
  return (
    <SliderPrimitive.Root
      className={cn("relative flex h-5 w-full touch-none items-center select-none", className)}
      value={[value]}
      onValueChange={(v) => onValueChange(v[0])}
      min={min}
      max={max}
      step={step}
      aria-label={ariaLabel}
    >
      <SliderPrimitive.Track className="relative h-[3px] grow rounded-full bg-line-strong">
        <SliderPrimitive.Range className="absolute h-full rounded-full bg-accent" />
      </SliderPrimitive.Track>
      <SliderPrimitive.Thumb className="block h-3.5 w-3.5 rounded-full border border-accent bg-bg shadow-[0_0_0_3px_var(--color-accent-soft)] transition-transform hover:scale-110 focus-visible:outline-none" />
    </SliderPrimitive.Root>
  );
}

export function Switch({
  checked,
  onCheckedChange,
  "aria-label": ariaLabel,
}: {
  checked: boolean;
  onCheckedChange: (v: boolean) => void;
  "aria-label"?: string;
}) {
  return (
    <SwitchPrimitive.Root
      checked={checked}
      onCheckedChange={onCheckedChange}
      aria-label={ariaLabel}
      className={cn(
        "relative h-[18px] w-8 shrink-0 cursor-pointer rounded-full border border-line-strong transition-colors",
        "data-[state=checked]:border-accent data-[state=checked]:bg-accent-soft",
      )}
    >
      <SwitchPrimitive.Thumb className="block h-3 w-3 translate-x-[3px] rounded-full bg-fg-dim transition-transform data-[state=checked]:translate-x-[15px] data-[state=checked]:bg-accent" />
    </SwitchPrimitive.Root>
  );
}

export interface SelectOption {
  value: string;
  label: string;
}

export function Select({
  value,
  onValueChange,
  options,
  ariaLabel,
  className,
}: {
  value: string;
  onValueChange: (v: string) => void;
  options: SelectOption[];
  ariaLabel?: string;
  className?: string;
}) {
  return (
    <SelectPrimitive.Root value={value} onValueChange={onValueChange}>
      <SelectPrimitive.Trigger
        aria-label={ariaLabel}
        className={cn(
          "inline-flex h-9 w-full items-center justify-between gap-2 rounded-[var(--radius)] border border-line-strong bg-elevated px-3 text-sm text-fg",
          "hover:border-fg-faint focus-visible:outline-none data-[placeholder]:text-fg-dim",
          className,
        )}
      >
        <SelectPrimitive.Value />
        <SelectPrimitive.Icon>
          <CaretDown size={13} className="text-fg-dim" />
        </SelectPrimitive.Icon>
      </SelectPrimitive.Trigger>
      <SelectPrimitive.Portal>
        <SelectPrimitive.Content
          position="popper"
          sideOffset={4}
          className="z-50 overflow-hidden rounded-[var(--radius)] border border-line-strong bg-overlay shadow-2xl"
        >
          <SelectPrimitive.Viewport className="p-1">
            {options.map((opt) => (
              <SelectPrimitive.Item
                key={opt.value}
                value={opt.value}
                className="relative flex cursor-pointer items-center rounded-[3px] py-1.5 pr-8 pl-3 text-sm text-fg-dim select-none data-[highlighted]:bg-elevated data-[highlighted]:text-fg data-[highlighted]:outline-none data-[state=checked]:text-accent"
              >
                <SelectPrimitive.ItemText>{opt.label}</SelectPrimitive.ItemText>
                <SelectPrimitive.ItemIndicator className="absolute right-2.5">
                  <Check size={13} />
                </SelectPrimitive.ItemIndicator>
              </SelectPrimitive.Item>
            ))}
          </SelectPrimitive.Viewport>
        </SelectPrimitive.Content>
      </SelectPrimitive.Portal>
    </SelectPrimitive.Root>
  );
}
