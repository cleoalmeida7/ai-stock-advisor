import { render, screen } from "@testing-library/react";

import { MetricsCard } from "@/components/MetricsCard";
import type { MetricResponse } from "@/types/analysis";

describe("MetricsCard", () => {
  it("renders an insufficient-data message when insufficient_data is true", () => {
    const metric: MetricResponse = { value: null, insufficient_data: true, observations_used: 3 };
    render(<MetricsCard label="20-day SMA" metric={metric} format="currency" />);

    expect(screen.getByText(/insufficient data/i)).toHaveTextContent("3 available");
    expect(screen.queryByText(/₹/)).not.toBeInTheDocument();
  });

  it("renders an insufficient-data message when value is null even if the flag is somehow false", () => {
    const metric: MetricResponse = { value: null, insufficient_data: false, observations_used: 0 };
    render(<MetricsCard label="Momentum" metric={metric} format="percent" />);

    expect(screen.getByText(/insufficient data/i)).toBeInTheDocument();
  });

  it("formats a percent metric correctly", () => {
    const metric: MetricResponse = { value: 0.0567, insufficient_data: false, observations_used: 90 };
    render(<MetricsCard label="Momentum" metric={metric} format="percent" />);

    expect(screen.getByText("5.67%")).toBeInTheDocument();
  });

  it("formats a currency metric correctly", () => {
    const metric: MetricResponse = { value: 1234.5, insufficient_data: false, observations_used: 20 };
    render(<MetricsCard label="20-day SMA" metric={metric} format="currency" />);

    expect(screen.getByText("₹1234.50")).toBeInTheDocument();
  });

  it("formats a plain number metric correctly by default", () => {
    const metric: MetricResponse = { value: -0.251, insufficient_data: false, observations_used: 120 };
    render(<MetricsCard label="Max drawdown" metric={metric} />);

    expect(screen.getByText("-0.25")).toBeInTheDocument();
  });
});
