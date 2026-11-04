import pytest

from app.quantitative.moving_averages import simple_moving_average
from tests.quantitative.fixtures import divergent_series, flat_series, make_series


def test_sma_hand_computed() -> None:
    result = simple_moving_average(make_series([10.0, 20.0, 30.0, 40.0]), window=4)
    assert result.insufficient_data is False
    assert result.value == pytest.approx(25.0)
    assert result.observations_used == 4


def test_sma_uses_only_the_most_recent_window() -> None:
    # The leading 1000.0 must be excluded from a 3-bar window.
    bars = make_series([1000.0, 10.0, 20.0, 30.0])
    result = simple_moving_average(bars, window=3)
    assert result.value == pytest.approx(20.0)


def test_sma_insufficient_data_when_fewer_rows_than_window() -> None:
    result = simple_moving_average(flat_series(5), window=20)
    assert result.insufficient_data is True
    assert result.value is None
    assert result.observations_used == 5


def test_sma_uses_adjusted_close_not_close() -> None:
    bars = divergent_series()  # adjusted_close ends flat at 95.0; close stays flat at 100.0
    result = simple_moving_average(bars, window=4)
    assert result.value == pytest.approx(95.0)
