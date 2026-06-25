/** Ergonomic types for the engine contract (mirrors engine/src/argmin/api/models.py).
 *  Machine-generated OpenAPI types live alongside in `openapi.d.ts`. */

export interface Provenance {
  engine_hash: string;
  risk_free: number;
  data_start: string;
  data_end: string;
  as_of: string | null;
  oos_only: boolean;
  generated_utc: string;
}

export interface OptimizeResult {
  method: string;
  tickers: string[];
  weights: Record<string, number>;
  exp_return: number;
  exp_vol: number;
  sharpe: number;
  risk_contrib: Record<string, number>;
  as_of?: string | null;
  provenance?: Provenance;
}

export interface Tearsheet {
  total_return: number;
  cagr: number;
  ann_return: number;
  ann_vol: number;
  sharpe: number;
  sortino: number;
  max_drawdown: number;
  calmar: number;
  var_95: number;
  cvar_95: number;
  hit_rate: number;
  best_day: number;
  worst_day: number;
  avg_turnover: number | null;
  psr: number | null;
  dsr: number | null;
  sharpe_ci_low: number | null;
  sharpe_ci_high: number | null;
}

export interface StrategyResult {
  name: string;
  metrics: Tearsheet;
  equity_curve: number[];
  drawdown: number[];
  rolling_sharpe: number[];
  weights_over_time: number[][];
  rebalance_dates: string[];
  turnover: number[];
}

export interface BacktestResult {
  tickers: string[];
  dates: string[];
  strategies: Record<string, StrategyResult>;
  significance: {
    dsr_trials: number;
    bootstrap_samples: number;
    bootstrap_block_size: number;
    strategies: Record<
      string,
      {
        psr: number;
        dsr: number;
        sharpe: number;
        sharpe_ci_low: number;
        sharpe_ci_high: number;
      }
    >;
  };
  provenance: Provenance;
}

export interface FrontierPoint {
  ret: number;
  vol: number;
  sharpe: number;
}

export interface FrontierResult {
  tickers: string[];
  frontier_points: FrontierPoint[];
  tangency: OptimizeResult;
  min_var: OptimizeResult;
  random_cloud: { vol: number[]; ret: number[] };
  provenance: Provenance;
}

export interface DefaultScenario {
  optimize: OptimizeResult;
  frontier: FrontierResult;
  backtest: BacktestResult;
}

export const OPTIMIZER_METHODS = [
  "max_sharpe",
  "min_variance",
  "max_diversification",
  "risk_parity",
  "hrp",
  "black_litterman",
] as const;

export type OptimizerMethod = (typeof OPTIMIZER_METHODS)[number];

export const METHOD_LABELS: Record<string, string> = {
  max_sharpe: "Max Sharpe",
  min_variance: "Min Variance",
  max_diversification: "Max Diversification",
  risk_parity: "Risk Parity (ERC)",
  hrp: "Hierarchical Risk Parity",
  black_litterman: "Black-Litterman",
  equal_weight: "Equal Weight (1/N)",
  sixty_forty: "60/40",
  spy: "SPY (buy & hold)",
};

export const ASSET_LABELS: Record<string, string> = {
  SPY: "US Large Cap",
  QQQ: "US Tech (Nasdaq-100)",
  EFA: "Developed ex-US",
  EEM: "Emerging Markets",
  AGG: "US Aggregate Bonds",
  TLT: "Long Treasuries",
  LQD: "IG Credit",
  HYG: "High-Yield Credit",
  VNQ: "US REITs",
  GLD: "Gold",
  DBC: "Commodities",
};
