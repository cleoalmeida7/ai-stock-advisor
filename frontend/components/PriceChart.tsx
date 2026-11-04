"use client";

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { PricePoint } from "@/types/analysis";

interface PriceChartProps {
  points: PricePoint[];
}

/**
 * Deliberately charts the unadjusted `close` (the actual quoted price on
 * each day), not `adjusted_close` - a price chart should show what the
 * stock really traded at. The metric cards alongside it are computed from
 * adjusted_close instead; see docs/metrics-and-scoring.md for why each is
 * used where it is.
 */
export function PriceChart({ points }: PriceChartProps) {
  if (points.length === 0) {
    return <p className="text-sm text-slate-500">No price history available.</p>;
  }

  const data = points.map((point) => ({ date: point.price_date, close: point.close }));

  return (
    <div className="h-64 w-full" data-testid="price-chart">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <XAxis dataKey="date" tick={{ fontSize: 10 }} minTickGap={30} />
          <YAxis domain={["auto", "auto"]} tick={{ fontSize: 10 }} width={50} />
          <Tooltip />
          <Line type="monotone" dataKey="close" stroke="#4f46e5" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
