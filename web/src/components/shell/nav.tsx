"use client";

import { LinkedinLogo } from "@phosphor-icons/react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/cn";

const links = [
  { href: "/", label: "Overview" },
  { href: "/explore", label: "Explore" },
  { href: "/math", label: "Methodology" },
];

export function Nav() {
  const pathname = usePathname();
  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-bg/85 backdrop-blur-md">
      <nav className="mx-auto flex h-14 max-w-[1400px] items-center justify-between px-5">
        <Link href="/" className="flex items-baseline gap-2" aria-label="Argmin home">
          <span className="font-mono text-sm font-semibold tracking-tight text-fg">argmin</span>
          <span className="hidden font-mono text-[10px] text-fg-faint sm:inline">
            arg&thinsp;min&nbsp;f(w)
          </span>
        </Link>

        <div className="flex items-center gap-0.5">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={cn(
                "rounded-[3px] px-3 py-1.5 font-mono text-[12.5px] tracking-tight transition-colors",
                isActive(l.href) ? "text-accent" : "text-fg-dim hover:text-fg",
              )}
            >
              {l.label}
            </Link>
          ))}
          <a
            href="https://www.linkedin.com/in/vincent-pineda8"
            target="_blank"
            rel="noreferrer"
            aria-label="Vincent Pineda on LinkedIn"
            className="ml-1 rounded-[3px] p-1.5 text-fg-dim transition-all duration-200 hover:-translate-y-px hover:text-accent"
          >
            <LinkedinLogo size={18} weight="fill" />
          </a>
        </div>
      </nav>
    </header>
  );
}
