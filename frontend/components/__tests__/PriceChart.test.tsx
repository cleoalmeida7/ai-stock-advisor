import { render, screen } from "@testing-library/react";

import { PriceChart } from "@/components/PriceChart";
import type { PricePoint } from "@/types/analysis";

const POINTS: PricePoint[] = [
  { price_date: "2026-01-01", open: 100, high: 102, low: 99, close: 101, adjusted_close: 101, volume: 1000 },
  { price_date: "2026-01-02", open: 101, high: 103, low: 100, close: 102, adjusted_close: 102, volume: 1100 },
];

describe("PriceChart", () => {
  it("shows an empty state when there is no price history", () => {
    render(<PriceChart points={[]} />);
    expect(screen.getByText(/no price history available/i)).toBeInTheDocument();
  });

  it("renders the chart container when points are provided", () => {
    render(<PriceChart points={POINTS} />);
    expect(screen.getByTestId("price-chart")).toBeInTheDocument();
  });
});
