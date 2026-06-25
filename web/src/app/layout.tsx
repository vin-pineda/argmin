import type { Metadata } from "next";
import { IBM_Plex_Mono, STIX_Two_Text } from "next/font/google";

import { Footer } from "@/components/shell/footer";
import { Nav } from "@/components/shell/nav";

import "./globals.css";
import { Providers } from "./providers";

const plexMono = IBM_Plex_Mono({
  weight: ["400", "500", "600"],
  subsets: ["latin"],
  variable: "--font-plex-mono",
});

// Serif voice: STIX Two Text is built for scientific/mathematical publishing and
// sits next to Computer Modern (what KaTeX renders), so prose, headlines, and the
// equations read as one typeset document.
const stixSerif = STIX_Two_Text({
  weight: ["400", "500", "600", "700"],
  style: ["normal", "italic"],
  subsets: ["latin"],
  variable: "--font-stix-serif",
});

export const metadata: Metadata = {
  title: "Argmin — Portfolio Optimization, Honestly Backtested",
  description:
    "Seven classical and modern allocation models, evaluated with honest, cost-aware, walk-forward out-of-sample backtests. The math, shown.",
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"),
  openGraph: {
    title: "Argmin — Portfolio Optimization, Honestly Backtested",
    description:
      "Seven allocation models, walk-forward OOS backtests with costs and significance. No login.",
    type: "website",
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${stixSerif.variable} ${plexMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="flex min-h-full flex-col bg-bg text-fg">
        <a
          href="#main-content"
          className="sr-only rounded-[3px] focus:not-sr-only focus:absolute focus:top-3 focus:left-4 focus:z-50 focus:border focus:border-accent focus:bg-elevated focus:px-3 focus:py-2 focus:font-mono focus:text-sm focus:text-fg"
        >
          Skip to content
        </a>
        <Providers>
          <Nav />
          <main id="main-content" tabIndex={-1} className="flex-1 focus:outline-none">
            {children}
          </main>
          <Footer />
        </Providers>
      </body>
    </html>
  );
}
