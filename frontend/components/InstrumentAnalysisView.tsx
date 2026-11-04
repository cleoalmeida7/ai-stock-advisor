"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { MetricsCard } from "@/components/MetricsCard";
import { PriceChart } from "@/components/PriceChart";
import { apiFetch } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";
import type { InstrumentAnalysis, PricePoint } from "@/types/analysis";

const CHART_RANGE_DAYS = 180;

interface InstrumentAnalysisViewProps {
  instrumentId: string;
}

export function InstrumentAnalysisView({ instrumentId }: InstrumentAnalysisViewProps) {
  const [analysis, setAnalysis] = useState<InstrumentAnalysis | null>(null);
  const [history, setHistory] = useState<PricePoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        if (active) {
          setError("Not signed in.");
          setLoading(false);
        }
        return;
      }

      const [analysisRes, historyRes] = await Promise.all([
        apiFetch(`/api/analysis/${instrumentId}`, session.access_token),
        apiFetch(`/api/market/${instrumentId}/history?days=${CHART_RANGE_DAYS}`, session.access_token),
      ]);

      if (!active) return;

      if (!analysisRes.ok || !historyRes.ok) {
        setError("Failed to load analysis.");
        setLoading(false);
        return;
      }

      setAnalysis(await analysisRes.json());
      setHistory(await historyRes.json());
      setLoading(false);
    }

    load();
    return () => {
      active = false;
    };
  }, [instrumentId]);

  if (loading) {
    return <main className="px-4 py-16 text-center text-slate-500">Loading…</main>;
  }

  if (error || !analysis) {
    return <main className="px-4 py-16 text-center text-red-600">{error ?? "Not found."}</main>;
  }

  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-6 px-4 py-12">
      <Link href="/portfolio" className="text-sm text-slate-600 underline">
        ← Back to portfolio
      </Link>

      <div>
        <h1 className="text-xl font-semibold">{analysis.symbol}</h1>
        <p className="text-sm text-slate-500">
          {analysis.as_of_date ? `As of ${analysis.as_of_date}` : "No price data available"}
          {analysis.source ? ` · source: ${analysis.source}` : ""}
        </p>
      </div>

      <PriceChart points={history} />

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <MetricsCard label="Cumulative return" metric={analysis.cumulative_return} format="percent" />
        <MetricsCard label="20-day SMA (adj. close)" metric={analysis.sma_20} format="currency" />
        <MetricsCard label="50-day SMA (adj. close)" metric={analysis.sma_50} format="currency" />
        <MetricsCard label="200-day SMA (adj. close)" metric={analysis.sma_200} format="currency" />
        <MetricsCard label="Momentum (90d)" metric={analysis.momentum} format="percent" />
        <MetricsCard label="Volatility (annualized)" metric={analysis.volatility} format="percent" />
        <MetricsCard label="Max drawdown" metric={analysis.max_drawdown} format="percent" />
      </section>

      <p className="text-xs text-slate-400">Metrics version {analysis.metrics_version}</p>
    </main>
  );
}
