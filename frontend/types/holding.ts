export interface Instrument {
  id: string;
  exchange: string;
  symbol: string;
  company_name: string;
  data_source: string;
  sector: string | null;
}

export interface Holding {
  id: string;
  quantity: string;
  average_buy_price: string;
  total_cost: string;
  source: string;
  created_at: string;
  instrument: Instrument;
}
