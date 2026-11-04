from datetime import date, datetime, timedelta, timezone

import pytest

from app.market_data.provider import PriceBar
from app.quantitative.portfolio_metrics import STALENESS_THRESHOLD_DAYS, compute_portfolio_metrics
from app.schemas.holding import HoldingRead
from app.schemas.instrument import InstrumentRead

TODAY = date(2026, 11, 4)


def make_instrument(instrument_id: str, symbol: str, sector: str | None = None) -> InstrumentRead:
    return InstrumentRead(
        id=instrument_id,
        exchange="NSE",
        symbol=symbol,
        company_name=f"{symbol} Ltd",
        data_source="dev_seed",
        sector=sector,
    )


def make_holding(holding_id: str, instrument: InstrumentRead, quantity: float, average_buy_price: float) -> HoldingRead:
    return HoldingRead(
        id=holding_id,
        quantity=quantity,
        average_buy_price=average_buy_price,
        total_cost=quantity * average_buy_price,
        source="manual",
        created_at=datetime.now(timezone.utc),
        instrument=instrument,
    )


def make_bar(close: float, adjusted_close: float | None = None, days_old: int = 0) -> PriceBar:
    return PriceBar(
        price_date=TODAY - timedelta(days=days_old),
        open=close,
        high=close,
        low=close,
        close=close,
        adjusted_close=adjusted_close if adjusted_close is not None else close,
        volume=1000,
    )


def test_basic_valuation_two_holdings_different_sectors() -> None:
    reliance = make_instrument("inst-1", "RELIANCE", sector="Energy")
    tcs = make_instrument("inst-2", "TCS", sector="Information Technology")
    holdings = [
        make_holding("h1", reliance, quantity=10, average_buy_price=2500),
        make_holding("h2", tcs, quantity=5, average_buy_price=3000),
    ]
    prices = {"inst-1": make_bar(2600), "inst-2": make_bar(3200)}

    result = compute_portfolio_metrics(holdings, prices, as_of=TODAY)

    assert result.valuation_complete is True
    assert result.unpriced_holdings == []
    assert result.total_value == pytest.approx(10 * 2600 + 5 * 3200)
    assert result.total_cost_basis == pytest.approx(10 * 2500 + 5 * 3000)
    assert result.unrealized_pl == pytest.approx(result.total_value - result.total_cost_basis)
    assert result.overall_return == pytest.approx(result.unrealized_pl / result.total_cost_basis)

    weights = {h.symbol: h.weight for h in result.holdings}
    assert sum(weights.values()) == pytest.approx(1.0)

    assert result.sector_concentration["Energy"] == pytest.approx(26000 / result.total_value)
    assert result.sector_concentration["Information Technology"] == pytest.approx(16000 / result.total_value)


def test_missing_price_is_flagged_not_silently_dropped() -> None:
    reliance = make_instrument("inst-1", "RELIANCE")
    tcs = make_instrument("inst-2", "TCS")
    holdings = [
        make_holding("h1", reliance, quantity=10, average_buy_price=2500),
        make_holding("h2", tcs, quantity=5, average_buy_price=3000),
    ]
    # no price at all for inst-2 (tcs)
    prices = {"inst-1": make_bar(2600)}

    result = compute_portfolio_metrics(holdings, prices, as_of=TODAY)

    assert result.valuation_complete is False
    assert len(result.unpriced_holdings) == 1
    assert result.unpriced_holdings[0].symbol == "TCS"
    assert result.unpriced_holdings[0].reason == "no_price_data"
    # excluded from the computed total entirely, not counted as 0
    assert result.total_value == pytest.approx(10 * 2600)
    assert len(result.holdings) == 1


def test_stale_price_is_flagged_and_excluded() -> None:
    reliance = make_instrument("inst-1", "RELIANCE")
    holdings = [make_holding("h1", reliance, quantity=10, average_buy_price=2500)]
    prices = {"inst-1": make_bar(2600, days_old=STALENESS_THRESHOLD_DAYS + 1)}

    result = compute_portfolio_metrics(holdings, prices, as_of=TODAY)

    assert result.valuation_complete is False
    assert result.unpriced_holdings[0].reason == "stale_price"
    assert result.total_value == pytest.approx(0.0)


def test_price_within_staleness_threshold_is_still_used() -> None:
    reliance = make_instrument("inst-1", "RELIANCE")
    holdings = [make_holding("h1", reliance, quantity=10, average_buy_price=2500)]
    prices = {"inst-1": make_bar(2600, days_old=STALENESS_THRESHOLD_DAYS)}

    result = compute_portfolio_metrics(holdings, prices, as_of=TODAY)

    assert result.valuation_complete is True
    assert result.total_value == pytest.approx(26000)


def test_missing_sector_is_grouped_as_unclassified() -> None:
    reliance = make_instrument("inst-1", "RELIANCE", sector=None)
    holdings = [make_holding("h1", reliance, quantity=10, average_buy_price=2500)]
    prices = {"inst-1": make_bar(2600)}

    result = compute_portfolio_metrics(holdings, prices, as_of=TODAY)

    assert result.sector_concentration == {"Unclassified": pytest.approx(1.0)}


def test_empty_portfolio_is_trivially_complete() -> None:
    result = compute_portfolio_metrics([], {}, as_of=TODAY)

    assert result.valuation_complete is True
    assert result.total_value == 0.0
    assert result.overall_return is None
    assert result.holdings == []
    assert result.unpriced_holdings == []


def test_valuation_uses_unadjusted_close_not_adjusted_close() -> None:
    # Deliberately different from close - using adjusted_close here (the
    # opposite bug from every other quantitative module) would misstate
    # today's actual market value.
    reliance = make_instrument("inst-1", "RELIANCE")
    holdings = [make_holding("h1", reliance, quantity=10, average_buy_price=2000)]
    prices = {"inst-1": make_bar(close=2600.0, adjusted_close=1300.0)}

    result = compute_portfolio_metrics(holdings, prices, as_of=TODAY)

    assert result.total_value == pytest.approx(26000.0)
    assert result.holdings[0].market_price == pytest.approx(2600.0)
