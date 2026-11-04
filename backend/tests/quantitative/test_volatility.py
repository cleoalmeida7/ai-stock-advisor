import statistics

import pytest

from app.quantitative.volatility import TRADING_DAYS_PER_YEAR, annualized_volatility
from tests.quantitative.fixtures import divergent_series, flat_series, make_series


def test_zero_variance_series_has_zero_volatility() -> None:
    result = annualized_volatility(flat_series(10), window=9)
    assert result.insufficient_data is False
    assert result.value == pytest.approx(0.0)


def test_insufficient_data_when_too_few_rows() -> None:
    result = annualized_volatility(flat_series(5), window=20)
    assert result.insufficient_data is True
    assert result.value is None


def test_volatility_hand_computed() -> None:
    bars = make_series([100.0, 110.0, 99.0, 108.9])  # daily returns: +10%, -10%, +10%
    result = annualized_volatility(bars, window=3)

    expected_daily_std = statistics.stdev([0.10, -0.10, 0.10])
    assert expected_daily_std == pytest.approx(0.11547005383792515)
    assert result.value == pytest.approx(expected_daily_std * (TRADING_DAYS_PER_YEAR**0.5))
    assert result.observations_used == 3


def test_volatility_uses_adjusted_close_not_close() -> None:
    bars = divergent_series()
    result = annualized_volatility(bars, window=4)
    # close is flat -> would be exactly 0.0 if this read the wrong column.
    assert result.value > 0
