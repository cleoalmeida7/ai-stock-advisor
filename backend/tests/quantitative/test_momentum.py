import pytest

from app.quantitative.momentum import momentum
from tests.quantitative.fixtures import divergent_series, make_series


def test_momentum_hand_computed() -> None:
    bars = make_series([100.0, 110.0, 121.0, 108.9])
    result = momentum(bars, window=4)
    assert result.insufficient_data is False
    assert result.value == pytest.approx(0.089)
    assert result.observations_used == 4


def test_momentum_insufficient_data_when_fewer_rows_than_window() -> None:
    result = momentum(make_series([100.0, 105.0]), window=90)
    assert result.insufficient_data is True
    assert result.value is None


def test_momentum_uses_adjusted_close_not_close() -> None:
    bars = divergent_series()
    result = momentum(bars, window=5)
    assert result.value == pytest.approx(-0.05)
