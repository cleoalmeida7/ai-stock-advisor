import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { HoldingForm } from "@/components/HoldingForm";
import type { Instrument } from "@/types/holding";

const INSTRUMENTS: Instrument[] = [
  { id: "inst-1", exchange: "NSE", symbol: "RELIANCE", company_name: "Reliance Industries Ltd", data_source: "dev_seed" },
  { id: "inst-2", exchange: "NSE", symbol: "TCS", company_name: "Tata Consultancy Services Ltd", data_source: "dev_seed" },
];

describe("HoldingForm", () => {
  it("rejects a zero quantity and does not call onSubmit", async () => {
    const onSubmit = jest.fn();
    render(<HoldingForm instruments={INSTRUMENTS} onSubmit={onSubmit} />);

    await userEvent.type(screen.getByLabelText(/quantity/i), "0");
    await userEvent.type(screen.getByLabelText(/average buy price/i), "100");
    await userEvent.click(screen.getByRole("button", { name: /add holding/i }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(/greater than zero/i);
  });

  it("rejects a negative price and does not call onSubmit", async () => {
    const onSubmit = jest.fn();
    render(<HoldingForm instruments={INSTRUMENTS} onSubmit={onSubmit} />);

    await userEvent.type(screen.getByLabelText(/quantity/i), "5");
    await userEvent.type(screen.getByLabelText(/average buy price/i), "-10");
    await userEvent.click(screen.getByRole("button", { name: /add holding/i }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(/greater than zero/i);
  });

  it("requires an instrument to be selectable when the list is empty", async () => {
    const onSubmit = jest.fn();
    render(<HoldingForm instruments={[]} onSubmit={onSubmit} />);

    await userEvent.type(screen.getByLabelText(/quantity/i), "5");
    await userEvent.type(screen.getByLabelText(/average buy price/i), "100");
    await userEvent.click(screen.getByRole("button", { name: /add holding/i }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(/select an instrument/i);
  });

  it("calls onSubmit with the entered values when input is valid", async () => {
    const onSubmit = jest.fn();
    render(<HoldingForm instruments={INSTRUMENTS} onSubmit={onSubmit} />);

    await userEvent.selectOptions(screen.getByLabelText(/instrument/i), "inst-2");
    await userEvent.type(screen.getByLabelText(/quantity/i), "5");
    await userEvent.type(screen.getByLabelText(/average buy price/i), "3400");
    await userEvent.click(screen.getByRole("button", { name: /add holding/i }));

    expect(onSubmit).toHaveBeenCalledWith({
      instrumentId: "inst-2",
      quantity: "5",
      averageBuyPrice: "3400",
    });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
