from datetime import date, timedelta

from scripts.ingest_prices import BACKFILL_DAYS, REFRESH_WINDOW_DAYS, determine_start_date, run
from app.market_data.provider import PriceBar
from tests.market_data.fakes import FakeIngestionStore, FakeMarketDataProvider

RELIANCE = {"id": "inst-1", "exchange": "NSE", "symbol": "RELIANCE"}
TCS = {"id": "inst-2", "exchange": "NSE", "symbol": "TCS"}


def make_bar(day: date, close: float = 100.0, adjusted_close: float = 99.0) -> PriceBar:
    return PriceBar(price_date=day, open=close, high=close, low=close, close=close, adjusted_close=adjusted_close, volume=1000)


def test_determine_start_date_backfills_when_no_existing_data() -> None:
    store = FakeIngestionStore([RELIANCE], existing_latest_dates={})
    start = determine_start_date(store, "inst-1")
    assert start == date.today() - timedelta(days=BACKFILL_DAYS)


def test_determine_start_date_uses_overlapping_refresh_window_when_data_exists() -> None:
    latest = date(2026, 1, 20)
    store = FakeIngestionStore([RELIANCE], existing_latest_dates={"inst-1": latest})
    start = determine_start_date(store, "inst-1")
    # Must re-fetch a trailing window BEFORE the latest date, not latest+1 -
    # this is what catches retroactively-adjusted historical prices.
    assert start == latest - timedelta(days=REFRESH_WINDOW_DAYS)
    assert start < latest


def test_run_upserts_bars_for_every_instrument() -> None:
    store = FakeIngestionStore([RELIANCE, TCS])
    provider = FakeMarketDataProvider(
        bars_by_symbol={
            "RELIANCE.NS": [make_bar(date(2026, 1, 1))],
            "TCS.NS": [make_bar(date(2026, 1, 1)), make_bar(date(2026, 1, 2))],
        }
    )

    results = run(store, provider)

    assert results["total_rows"] == 3
    assert results["failed_symbols"] == []
    assert len(store.upserted["inst-1"]) == 1
    assert len(store.upserted["inst-2"]) == 2


def test_run_continues_after_one_instrument_permanently_fails() -> None:
    store = FakeIngestionStore([RELIANCE, TCS])
    provider = FakeMarketDataProvider(
        bars_by_symbol={"TCS.NS": [make_bar(date(2026, 1, 1))]},
        fail_counts={"RELIANCE.NS": -1},  # always fails
    )

    results = run(store, provider)

    assert results["failed_symbols"] == ["RELIANCE"]
    assert "inst-1" not in store.upserted
    assert len(store.upserted["inst-2"]) == 1
    assert results["total_rows"] == 1


def test_single_transient_failure_is_retried_and_succeeds(monkeypatch) -> None:
    import scripts.ingest_prices as ingest_module

    monkeypatch.setattr(ingest_module.time, "sleep", lambda _seconds: None)

    store = FakeIngestionStore([RELIANCE])
    provider = FakeMarketDataProvider(
        bars_by_symbol={"RELIANCE.NS": [make_bar(date(2026, 1, 1))]},
        fail_counts={"RELIANCE.NS": 1},  # fails once, then succeeds
    )

    results = run(store, provider)

    assert results["failed_symbols"] == []
    assert len(store.upserted["inst-1"]) == 1
    assert len(provider.calls) == 2  # the failed attempt + the retry


def test_failure_beyond_max_attempts_is_reported_not_raised(monkeypatch) -> None:
    import scripts.ingest_prices as ingest_module

    monkeypatch.setattr(ingest_module.time, "sleep", lambda _seconds: None)

    store = FakeIngestionStore([RELIANCE])
    provider = FakeMarketDataProvider(fail_counts={"RELIANCE.NS": 5})

    results = run(store, provider)

    assert results["failed_symbols"] == ["RELIANCE"]
    assert "inst-1" not in store.upserted
