"use client";

import { Play, ChartLine, Warning, ArrowClockwise } from "@phosphor-icons/react";
import { useMemo, useState } from "react";

import { Reveal } from "@/components/landing/reveal";
import { AnimatedNumber } from "@/components/ui/animated-number";
import { Button } from "@/components/ui/button";
import { Panel, PanelHeader, Hairline } from "@/components/ui/primitives";
import { Select, Slider, Switch } from "@/components/ui/controls";
import { cn } from "@/lib/cn";

import { FrontierViz } from "@/components/charts/frontier-viz";
import { EquityChart } from "@/components/charts/equity";
import { DrawdownChart } from "@/components/charts/drawdown";
import { RollingSharpeChart } from "@/components/charts/rolling-sharpe";
import { WeightsChart, WeightsLegend } from "@/components/charts/weights";
import { RiskContribChart } from "@/components/charts/risk-contrib";

import { TearsheetTable } from "./TearsheetTable";
import { SignificancePanel } from "./SignificancePanel";
import { ProvenanceBar } from "./ProvenanceBar";

import {
  useOptimize,
  useFrontier,
  useBacktest,
  type ConstraintsInput,
} from "@/lib/api/client";
import type {
  DefaultScenario,
  OptimizeResult,
  FrontierResult,
  BacktestResult,
} from "@/lib/api/types";
import { OPTIMIZER_METHODS, METHOD_LABELS, ASSET_LABELS } from "@/lib/api/types";
import { seriesColor } from "@/lib/series";
import { pct, num } from "@/lib/format";

const UNIVERSE = [
  "SPY",
  "QQQ",
  "EFA",
  "EEM",
  "AGG",
  "TLT",
  "LQD",
  "HYG",
  "VNQ",
  "GLD",
  "DBC",
] as const;

const METHOD_OPTIONS = OPTIMIZER_METHODS.map((m) => ({ value: m, label: METHOD_LABELS[m] }));
const REBALANCE_OPTIONS = [
  { value: "monthly", label: "Monthly" },
  { value: "quarterly", label: "Quarterly" },
];

/** A bordered control row: label on the left, control on the right. */
function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-baseline justify-between">
        <span className="font-mono text-[11.5px] tracking-tight text-fg-dim">{label}</span>
        {hint ? <span className="tnum text-[11px] text-fg">{hint}</span> : null}
      </div>
      {children}
    </div>
  );
}

function ChartSkeleton({ height }: { height: number }) {
  return (
    <div
      className="w-full animate-pulse rounded-[var(--radius)] bg-elevated/50"
      style={{ height }}
      aria-hidden
    />
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  const unreachable = message.includes("engine_unreachable") || message.includes("unreachable");
  return (
    <div className="flex flex-col items-start gap-2 px-4 py-5 text-[12.5px]">
      <div className="flex items-center gap-2 text-neg">
        <Warning size={15} weight="bold" />
        <span className="font-mono text-[12px] tracking-tight">request failed</span>
      </div>
      <p className="text-fg-dim">
        {unreachable
          ? "The engine API is unreachable. Showing the last good result."
          : message}
      </p>
      {onRetry ? (
        <Button size="sm" variant="outline" onClick={onRetry}>
          <ArrowClockwise size={13} /> Retry
        </Button>
      ) : null}
    </div>
  );
}

export function ExplorerClient({ initial }: { initial: DefaultScenario }) {
  // ---- control state ----
  const [method, setMethod] = useState<string>(initial.optimize.method);
  const [selected, setSelected] = useState<string[]>([...UNIVERSE]);
  const [maxWeight, setMaxWeight] = useState<number>(0.4);
  const [costBps, setCostBps] = useState<number>(10);
  const [rebalance, setRebalance] = useState<string>("monthly");
  const [logScale, setLogScale] = useState<boolean>(false);

  // ---- result state (seeded from the precomputed scenario) ----
  const [optimize, setOptimize] = useState<OptimizeResult>(initial.optimize);
  const [frontier, setFrontier] = useState<FrontierResult>(initial.frontier);
  const [backtest, setBacktest] = useState<BacktestResult>(initial.backtest);

  const optimizeMut = useOptimize();
  const frontierMut = useFrontier();
  const backtestMut = useBacktest();

  const riskFree = backtest.provenance.risk_free;

  const constraints: ConstraintsInput = useMemo(
    () => ({ long_only: true, fully_invested: true, max_weight: maxWeight }),
    [maxWeight],
  );

  const universe = useMemo(
    () => UNIVERSE.filter((t) => selected.includes(t)),
    [selected],
  );
  const universeValid = universe.length >= 2;

  // ---- actions ----
  function toggleAsset(ticker: string) {
    setSelected((prev) => {
      if (prev.includes(ticker)) {
        const next = prev.filter((t) => t !== ticker);
        return next.length >= 2 ? next : prev; // enforce min 2
      }
      return [...prev, ticker];
    });
  }

  function runOptimize() {
    if (!universeValid) return;
    optimizeMut.mutate(
      { universe, method, constraints, risk_free: riskFree },
      { onSuccess: (res) => setOptimize(res) },
    );
    frontierMut.mutate({ universe }, { onSuccess: (res) => setFrontier(res) });
  }

  function runBacktest() {
    if (!universeValid) return;
    backtestMut.mutate(
      {
        universe,
        method,
        constraints,
        transaction_cost_bps: costBps,
        rebalance,
      },
      { onSuccess: (res) => setBacktest(res) },
    );
  }

  // chosen strategy key - the backtest result keys the chosen by its method
  const chosen = backtest.strategies[method] ? method : Object.keys(backtest.strategies)[0];
  const chosenStrategy = backtest.strategies[chosen];

  const optimizePending = optimizeMut.isPending || frontierMut.isPending;

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-[300px_minmax(0,1fr)]">
      {/* ===================== CONTROL PANEL ===================== */}
      <aside className="lg:sticky lg:top-[72px] lg:self-start">
        <Panel className="overflow-hidden">
          <PanelHeader label="Controls" hint="configure & run" />
          <div className="flex flex-col gap-5 p-4">
            <Field label="Method">
              <Select
                value={method}
                onValueChange={setMethod}
                options={METHOD_OPTIONS}
                ariaLabel="Optimizer method"
              />
            </Field>

            <Field label="Universe" hint={`${universe.length} / ${UNIVERSE.length}`}>
              <div className="flex flex-wrap gap-1.5">
                {UNIVERSE.map((t) => {
                  const on = selected.includes(t);
                  return (
                    <button
                      key={t}
                      type="button"
                      onClick={() => toggleAsset(t)}
                      aria-pressed={on}
                      title={ASSET_LABELS[t]}
                      className={cn(
                        "inline-flex min-h-[32px] items-center gap-1.5 rounded-[3px] border px-2.5 py-1.5 font-mono text-[11px] tracking-tight transition-all duration-150 ease-out hover:-translate-y-px active:scale-95",
                        on
                          ? "border-line-strong text-fg"
                          : "border-line text-fg-faint hover:border-line-strong hover:text-fg-dim",
                      )}
                    >
                      <span
                        className={cn(
                          "h-1.5 w-1.5 rounded-full transition-colors",
                          on ? "bg-accent" : "bg-line-strong",
                        )}
                        aria-hidden
                      />
                      {t}
                    </button>
                  );
                })}
              </div>
              {!universeValid ? (
                <span className="text-[11px] text-neg">Select at least 2 assets.</span>
              ) : null}
            </Field>

            <Field label="Max weight" hint={pct(maxWeight, 0)}>
              <Slider
                value={maxWeight}
                onValueChange={setMaxWeight}
                min={0.1}
                max={1}
                step={0.05}
                aria-label="Maximum weight per asset"
              />
            </Field>

            <Field label="Transaction cost" hint={`${costBps} bps`}>
              <Slider
                value={costBps}
                onValueChange={setCostBps}
                min={0}
                max={50}
                step={1}
                aria-label="Transaction cost in basis points"
              />
            </Field>

            <Field label="Rebalance">
              <Select
                value={rebalance}
                onValueChange={setRebalance}
                options={REBALANCE_OPTIONS}
                ariaLabel="Rebalance frequency"
              />
            </Field>

            <Field label="Risk-free (read-only)" hint={pct(riskFree, 1)}>
              <div className="flex h-9 items-center rounded-[var(--radius)] border border-line bg-elevated/40 px-3 text-[12px] text-fg-faint">
                annualized, fixed at {pct(riskFree, 1)}
              </div>
            </Field>

            <Hairline />

            <div className="flex flex-col gap-2">
              <Button
                variant="primary"
                onClick={runOptimize}
                disabled={!universeValid || optimizePending}
                className="w-full"
              >
                {optimizePending ? (
                  <ArrowClockwise size={14} className="animate-spin" />
                ) : (
                  <Play size={14} weight="fill" />
                )}
                Run optimize
              </Button>
              <Button
                variant="outline"
                onClick={runBacktest}
                disabled={!universeValid || backtestMut.isPending}
                className="w-full"
              >
                {backtestMut.isPending ? (
                  <ArrowClockwise size={14} className="animate-spin" />
                ) : (
                  <ChartLine size={14} />
                )}
                Run backtest
              </Button>
              <p className="text-[11px] leading-relaxed text-fg-faint">
                Optimize refreshes the frontier, weights and risk. Backtest reruns the
                walk-forward (slower).
              </p>
            </div>
          </div>
        </Panel>
      </aside>

      {/* ===================== CHART GRID ===================== */}
      <div className="flex min-w-0 flex-col gap-5">
        <Reveal>
          <Panel>
            <ProvenanceBar
              provenance={backtest.provenance}
              rebalance={rebalance}
              costBps={costBps}
            />
          </Panel>
        </Reveal>

        {/* frontier + risk row */}
        <Reveal className="grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)]">
          <Panel>
            <PanelHeader
              label="Efficient frontier"
              hint="random cloud · frontier · tangency"
              right={
                <span className="tnum text-[11px] text-fg-dim">
                  tan Sharpe{" "}
                  <AnimatedNumber value={frontier.tangency.sharpe} format={(v) => num(v, 2)} />
                </span>
              }
            />
            <div className="p-3">
              {frontierMut.error ? (
                <ErrorState message={String(frontierMut.error.message)} onRetry={runOptimize} />
              ) : frontierMut.isPending ? (
                <ChartSkeleton height={360} />
              ) : (
                <div key={universe.join(",")} className="aspect-[16/10] w-full">
                  <FrontierViz
                    data={frontier}
                    portfolio={{
                      vol: optimize.exp_vol,
                      ret: optimize.exp_return,
                      label: METHOD_LABELS[optimize.method] ?? optimize.method,
                    }}
                  />
                </div>
              )}
            </div>
          </Panel>

          <Panel>
            <PanelHeader
              label="Risk contribution"
              hint={METHOD_LABELS[optimize.method] ?? optimize.method}
              right={
                <span className="tnum text-[11px] text-fg-dim">
                  σ <AnimatedNumber value={optimize.exp_vol} format={(v) => pct(v, 1)} />
                </span>
              }
            />
            <div className="p-3">
              {optimizeMut.error ? (
                <ErrorState message={String(optimizeMut.error.message)} onRetry={runOptimize} />
              ) : optimizeMut.isPending ? (
                <ChartSkeleton height={280} />
              ) : (
                <RiskContribChart result={optimize} />
              )}
            </div>
          </Panel>
        </Reveal>

        {/* equity */}
        <Reveal>
          <Panel>
          <PanelHeader
            label="Growth of $1"
            hint="out-of-sample, net of costs"
            right={
              <label className="flex cursor-pointer items-center gap-2">
                <span className="font-mono text-[11px] tracking-tight text-fg-faint">log</span>
                <Switch
                  checked={logScale}
                  onCheckedChange={setLogScale}
                  aria-label="Log scale"
                />
              </label>
            }
          />
          <div className="p-3">
            {backtestMut.error ? (
              <ErrorState message={String(backtestMut.error.message)} onRetry={runBacktest} />
            ) : backtestMut.isPending ? (
              <ChartSkeleton height={300} />
            ) : (
              <EquityChart data={backtest} chosen={chosen} logScale={logScale} />
            )}
            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1.5 px-1">
              {Object.keys(backtest.strategies).map((name) => (
                <LegendDot key={name} name={name} chosen={name === chosen} />
              ))}
            </div>
          </div>
          </Panel>
        </Reveal>

        {/* drawdown + rolling sharpe */}
        <Reveal className="grid grid-cols-1 gap-5 xl:grid-cols-2">
          <Panel>
            <PanelHeader label="Drawdown" hint={`${METHOD_LABELS[chosen] ?? chosen}`} />
            <div className="p-3">
              {backtestMut.isPending ? (
                <ChartSkeleton height={200} />
              ) : (
                <DrawdownChart dates={backtest.dates} strategy={chosenStrategy} />
              )}
            </div>
          </Panel>
          <Panel>
            <PanelHeader label="Rolling Sharpe" hint="252-day window" />
            <div className="p-3">
              {backtestMut.isPending ? (
                <ChartSkeleton height={200} />
              ) : (
                <RollingSharpeChart
                  dates={backtest.dates}
                  strategy={chosenStrategy}
                  name={chosen}
                />
              )}
            </div>
          </Panel>
        </Reveal>

        {/* weights */}
        <Reveal>
          <Panel>
          <PanelHeader label="Weights over time" hint={`${METHOD_LABELS[chosen] ?? chosen}`} />
          <div className="p-3">
            {backtestMut.isPending ? (
              <ChartSkeleton height={240} />
            ) : (
              <WeightsChart tickers={backtest.tickers} strategy={chosenStrategy} />
            )}
            <div className="mt-2 px-1">
              <WeightsLegend tickers={backtest.tickers} />
            </div>
          </div>
          </Panel>
        </Reveal>

        {/* tearsheet */}
        <Reveal>
          <Panel>
          <PanelHeader label="Tearsheet" hint="chosen vs benchmarks" />
          {backtestMut.isPending ? (
            <div className="p-3">
              <ChartSkeleton height={180} />
            </div>
          ) : (
            <TearsheetTable data={backtest} chosen={chosen} />
          )}
          </Panel>
        </Reveal>

        {/* significance */}
        <Reveal>
          <Panel>
          <PanelHeader label="Significance" hint="PSR · DSR · bootstrap CI" />
          {backtestMut.isPending ? (
            <div className="p-3">
              <ChartSkeleton height={120} />
            </div>
          ) : (
            <SignificancePanel data={backtest} chosen={chosen} />
          )}
          </Panel>
        </Reveal>
      </div>
    </div>
  );
}

function LegendDot({ name, chosen }: { name: string; chosen: boolean }) {
  return (
    <div className={cn("flex items-center gap-1.5", !chosen && "opacity-70")}>
      <span
        className="inline-block h-2 w-2 rounded-[1px]"
        style={{ background: seriesColor(name) }}
      />
      <span className={cn("text-[10.5px]", chosen ? "text-accent" : "text-fg-dim")}>
        {METHOD_LABELS[name] ?? name}
      </span>
    </div>
  );
}
