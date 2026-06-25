"use client";

import { useMutation } from "@tanstack/react-query";

import type { BacktestResult, FrontierResult, OptimizeResult } from "./types";

export interface ConstraintsInput {
  long_only?: boolean;
  fully_invested?: boolean;
  max_weight?: number | null;
  min_weight?: number | null;
  leverage_cap?: number | null;
}

export interface OptimizeParams {
  universe: string[];
  method: string;
  constraints?: ConstraintsInput;
  as_of?: string | null;
  mu_method?: string | null;
  cov_method?: string | null;
  risk_free?: number | null;
}

export interface BacktestParams {
  universe: string[];
  method: string;
  constraints?: ConstraintsInput;
  start?: string | null;
  end?: string | null;
  rebalance?: string | null;
  lookback_years?: number | null;
  transaction_cost_bps?: number | null;
  benchmarks?: string[] | null;
}

async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(path, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await r.json();
  if (!r.ok) {
    throw new Error(data?.detail ?? data?.error ?? `Request to ${path} failed (${r.status})`);
  }
  return data as T;
}

async function getFrontier(universe: string[], asOf?: string | null): Promise<FrontierResult> {
  const qs = new URLSearchParams({ universe: universe.join(",") });
  if (asOf) qs.set("as_of", asOf);
  const r = await fetch(`/api/frontier?${qs.toString()}`);
  const data = await r.json();
  if (!r.ok) throw new Error(data?.detail ?? data?.error ?? "Frontier request failed");
  return data as FrontierResult;
}

export const useOptimize = () =>
  useMutation({ mutationFn: (p: OptimizeParams) => postJSON<OptimizeResult>("/api/optimize", p) });

export const useBacktest = () =>
  useMutation({ mutationFn: (p: BacktestParams) => postJSON<BacktestResult>("/api/backtest", p) });

export const useFrontier = () =>
  useMutation({
    mutationFn: (p: { universe: string[]; asOf?: string | null }) =>
      getFrontier(p.universe, p.asOf),
  });
