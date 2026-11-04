"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import Link from "next/link";

import { HoldingForm, type HoldingFormValues } from "@/components/HoldingForm";
import { apiFetch } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";
import type { PortfolioMetrics } from "@/types/analysis";
import type { Holding, Instrument } from "@/types/holding";

export default function PortfolioPage() {
  const router = useRouter();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [metrics, setMetrics] = useState<PortfolioMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async (token: string) => {
    setError(null);
    const [holdingsRes, instrumentsRes, metricsRes] = await Promise.all([
      apiFetch("/api/portfolio/holdings", token),
      apiFetch("/api/instruments/search?q=", token),
      apiFetch("/api/portfolio/metrics", token),
    ]);

    if (!holdingsRes.ok || !instrumentsRes.ok || !metricsRes.ok) {
      setError("Failed to load portfolio data.");
      return;
    }

    setHoldings(await holdingsRes.json());
    setInstruments(await instrumentsRes.json());
    setMetrics(await metricsRes.json());
  }, []);

  useEffect(() => {
    const supabase = createClient();

    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) {
        router.push("/login");
        return;
      }
      setAccessToken(session.access_token);
      loadData(session.access_token).finally(() => setLoading(false));
    });
  }, [router, loadData]);

  async function handleAddHolding(values: HoldingFormValues) {
    if (!accessToken) return;
    setSubmitting(true);
    setError(null);

    const response = await apiFetch("/api/portfolio/holdings", accessToken, {
      method: "POST",
      body: JSON.stringify({
        instrument_id: values.instrumentId,
        quantity: values.quantity,
        average_buy_price: values.averageBuyPrice,
      }),
    });

    setSubmitting(false);

    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: "Request failed." }));
      setError(body.detail ?? "Request failed.");
      return;
    }

    await loadData(accessToken);
  }

  async function handleDelete(holdingId: string) {
    if (!accessToken) return;
    const response = await apiFetch(`/api/portfolio/holdings/${holdingId}`, accessToken, { method: "DELETE" });
    if (response.ok) {
      await loadData(accessToken);
    }
  }

  async function handleSignOut() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
  }

  if (loading) {
    return <main className="px-4 py-16 text-center text-slate-500">Loading…</main>;
  }

  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-6 px-4 py-12">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Portfolio</h1>
        <button type="button" onClick={handleSignOut} className="text-sm text-slate-600 underline">
          Sign out
        </button>
      </div>

      {error && (
        <p role="alert" className="text-sm text-red-600">
          {error}
        </p>
      )}

      {metrics && holdings.length > 0 && (
        <section className="rounded-lg border border-slate-200 p-4 dark:border-slate-700">
          <h2 className="mb-2 text-sm font-medium text-slate-600">Valuation</h2>
          <div className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
            <div>
              <p className="text-xs text-slate-500">Value</p>
              <p className="font-semibold">₹{metrics.total_value.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Cost basis</p>
              <p className="font-semibold">₹{metrics.total_cost_basis.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Unrealized P/L</p>
              <p className="font-semibold">₹{metrics.unrealized_pl.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Return</p>
              <p className="font-semibold">
                {metrics.overall_return === null ? "—" : `${(metrics.overall_return * 100).toFixed(2)}%`}
              </p>
            </div>
          </div>
          {!metrics.valuation_complete && (
            <p role="alert" className="mt-2 text-xs text-amber-600">
              Value based on {holdings.length - metrics.unpriced_holdings.length} of {holdings.length} holdings —{" "}
              {metrics.unpriced_holdings.map((u) => u.symbol).join(", ")} {metrics.unpriced_holdings.length === 1 ? "has" : "have"} no current price.
            </p>
          )}
        </section>
      )}

      <section>
        <h2 className="mb-2 text-sm font-medium text-slate-600">Holdings</h2>
        {holdings.length === 0 ? (
          <p className="text-sm text-slate-500">No holdings yet. Add one below.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {holdings.map((holding) => {
              const valuation = metrics?.holdings.find((h) => h.holding_id === holding.id);
              return (
                <li
                  key={holding.id}
                  className="flex items-center justify-between rounded border border-slate-200 px-3 py-2"
                >
                  <span>
                    <Link href={`/instruments/${holding.instrument.id}`} className="font-semibold underline">
                      {holding.instrument.symbol}
                    </Link>{" "}
                    — {holding.quantity} @ ₹{holding.average_buy_price}
                    <span className="text-slate-500"> (cost ₹{holding.total_cost})</span>
                    {valuation && (
                      <span className="text-slate-500">
                        {" "}
                        · now ₹{valuation.market_price.toFixed(2)} · value ₹{valuation.market_value.toFixed(2)} ·{" "}
                        {(valuation.weight * 100).toFixed(1)}% of portfolio
                      </span>
                    )}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleDelete(holding.id)}
                    className="text-sm text-red-600 underline"
                  >
                    Remove
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      <section>
        <h2 className="mb-2 text-sm font-medium text-slate-600">Add a holding</h2>
        <HoldingForm instruments={instruments} onSubmit={handleAddHolding} submitting={submitting} />
      </section>
    </main>
  );
}
