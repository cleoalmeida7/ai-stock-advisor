"use client";

import { useState, type FormEvent } from "react";

import type { Instrument } from "@/types/holding";

export interface HoldingFormValues {
  instrumentId: string;
  quantity: string;
  averageBuyPrice: string;
}

interface HoldingFormProps {
  instruments: Instrument[];
  onSubmit: (values: HoldingFormValues) => void;
  submitting?: boolean;
}

// Explicit light/dark background + text on every field - native <select>/
// <option>/<input> boxes don't follow the page's dark background on their
// own, they need their own colors or they stay white regardless of theme.
const FIELD_CLASS =
  "rounded border border-slate-300 bg-white px-2 py-1 text-slate-900 " +
  "dark:border-slate-600 dark:bg-gray-900 dark:text-slate-100 " +
  "focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400";

const OPTION_CLASS = "bg-white text-slate-900 dark:bg-gray-900 dark:text-slate-100";

export function HoldingForm({ instruments, onSubmit, submitting = false }: HoldingFormProps) {
  const [instrumentId, setInstrumentId] = useState(instruments[0]?.id ?? "");
  const [quantity, setQuantity] = useState("");
  const [averageBuyPrice, setAverageBuyPrice] = useState("");
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();

    if (!instrumentId) {
      setError("Select an instrument.");
      return;
    }

    const qty = Number(quantity);
    if (!Number.isFinite(qty) || qty <= 0) {
      setError("Quantity must be greater than zero.");
      return;
    }

    const price = Number(averageBuyPrice);
    if (!Number.isFinite(price) || price <= 0) {
      setError("Average buy price must be greater than zero.");
      return;
    }

    setError(null);
    onSubmit({ instrumentId, quantity, averageBuyPrice });
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-3 rounded-lg border border-slate-200 p-4 dark:border-slate-700"
    >
      <label className="flex flex-col gap-1 text-sm">
        Instrument
        <select
          value={instrumentId}
          onChange={(event) => setInstrumentId(event.target.value)}
          className={`theme-aware ${FIELD_CLASS}`}
        >
          {instruments.map((instrument) => (
            <option key={instrument.id} value={instrument.id} className={OPTION_CLASS}>
              {instrument.symbol} — {instrument.company_name}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1 text-sm">
        Quantity
        <input
          type="number"
          step="any"
          value={quantity}
          onChange={(event) => setQuantity(event.target.value)}
          className={FIELD_CLASS}
        />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        Average buy price (INR)
        <input
          type="number"
          step="any"
          value={averageBuyPrice}
          onChange={(event) => setAverageBuyPrice(event.target.value)}
          className={FIELD_CLASS}
        />
      </label>

      {error && (
        <p role="alert" className="text-sm text-red-600">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={submitting}
        className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {submitting ? "Adding…" : "Add holding"}
      </button>
    </form>
  );
}
