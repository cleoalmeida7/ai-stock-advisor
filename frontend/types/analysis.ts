export interface MetricResponse {
  value: number | null;
  insufficient_data: boolean;
  observations_used: number;
}

export interface InstrumentAnalysis {
  instrument_id: string;
  symbol: string;
  as_of_date: string | null;
  source: string | null;
  metrics_version: string;
  cumulative_return: MetricResponse;
  sma_20: MetricResponse;
  sma_50: MetricResponse;
  sma_200: MetricResponse;
  momentum: MetricResponse;
  volatility: MetricResponse;
  max_drawdown: MetricResponse;
}

export interface PricePoint {
  price_date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number;
  adjusted_close: number;
  volume: number | null;
}

export interface UnpricedHolding {
  holding_id: string;
  instrument_id: string;
  symbol: string;
  reason: string;
}

export interface HoldingValuation {
  holding_id: string;
  instrument_id: string;
  symbol: string;
  sector: string | null;
  quantity: number;
  market_price: number;
  market_value: number;
  cost_basis: number;
  unrealized_pl: number;
  weight: number;
}

export interface PortfolioMetrics {
  total_value: number;
  total_cost_basis: number;
  unrealized_pl: number;
  overall_return: number | null;
  valuation_complete: boolean;
  unpriced_holdings: UnpricedHolding[];
  holdings: HoldingValuation[];
  sector_concentration: Record<string, number>;
}
