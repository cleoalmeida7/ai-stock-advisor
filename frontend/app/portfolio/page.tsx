"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { HoldingForm, type HoldingFormValues } from "@/components/HoldingForm";
import { apiFetch } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";
import type { Holding, Instrument } from "@/types/holding";

export default function PortfolioPage() {
  const router = useRouter();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async (token: string) => {
    setError(null);
    const [holdingsRes, instrumentsRes] = await Promise.all([
      apiFetch("/api/portfolio/holdings", token),
      apiFetch("/api/instruments/search?q=", token),
    ]);

    if (!holdingsRes.ok || !instrumentsRes.ok) {
      setError("Failed to load portfolio data.");
      return;
    }

    setHoldings(await holdingsRes.json());
    setInstruments(await instrumentsRes.json());
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

      <section>
        <h2 className="mb-2 text-sm font-medium text-slate-600">Holdings</h2>
        {holdings.length === 0 ? (
          <p className="text-sm text-slate-500">No holdings yet. Add one below.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {holdings.map((holding) => (
              <li
                key={holding.id}
                className="flex items-center justify-between rounded border border-slate-200 px-3 py-2"
              >
                <span>
                  <strong>{holding.instrument.symbol}</strong> — {holding.quantity} @ ₹{holding.average_buy_price}
                  <span className="text-slate-500"> (total ₹{holding.total_cost})</span>
                </span>
                <button
                  type="button"
                  onClick={() => handleDelete(holding.id)}
                  className="text-sm text-red-600 underline"
                >
                  Remove
                </button>
              </li>
            ))}
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
