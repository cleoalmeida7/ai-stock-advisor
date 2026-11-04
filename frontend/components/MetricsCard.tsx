import type { MetricResponse } from "@/types/analysis";

export type MetricFormat = "percent" | "currency" | "number";

interface MetricsCardProps {
  label: string;
  metric: MetricResponse;
  format?: MetricFormat;
}

function formatValue(value: number, format: MetricFormat): string {
  if (format === "percent") return `${(value * 100).toFixed(2)}%`;
  if (format === "currency") return `₹${value.toFixed(2)}`;
  return value.toFixed(2);
}

/**
 * insufficient_data is an explicit, first-class state from the backend
 * (app/quantitative/types.py MetricValue) - rendered here as its own
 * message, never silently shown as 0 or omitted. See docs/metrics-and-scoring.md.
 */
export function MetricsCard({ label, metric, format = "number" }: MetricsCardProps) {
  const isInsufficient = metric.insufficient_data || metric.value === null;

  return (
    <div className="rounded-lg border border-slate-200 p-3 dark:border-slate-700">
      <p className="text-xs text-slate-500">{label}</p>
      {isInsufficient ? (
        <p className="text-sm text-slate-400">Insufficient data ({metric.observations_used} available)</p>
      ) : (
        <p className="text-lg font-semibold">{formatValue(metric.value as number, format)}</p>
      )}
    </div>
  );
}
