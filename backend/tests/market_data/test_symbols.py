import pytest

from app.market_data.provider import to_yfinance_symbol


def test_nse_symbol_gets_ns_suffix() -> None:
    assert to_yfinance_symbol("NSE", "RELIANCE") == "RELIANCE.NS"


def test_bse_symbol_gets_bo_suffix() -> None:
    assert to_yfinance_symbol("BSE", "RELIANCE") == "RELIANCE.BO"


def test_unknown_exchange_raises() -> None:
    with pytest.raises(ValueError):
        to_yfinance_symbol("NYSE", "AAPL")
