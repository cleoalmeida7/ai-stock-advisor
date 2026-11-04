import pytest

from app.quantitative.drawdown import max_drawdown
from tests.quantitative.fixtures import divergent_series, make_series


def test_drawdown_hand_computed() -> None:
    # peak after bar 2 = 120; trough at bar 3 = 90 -> 90/120 - 1 = -0.25
    bars = make_series([100.0, 120.0, 90.0, 110.0])
    result = max_drawdown(bars)
    assert result.insufficient_data is False
    assert result.value == pytest.approx(-0.25)


def test_drawdown_zero_for_monotonically_rising_series() -> None:
    result = max_drawdown(make_series([100.0, 110.0, 120.0]))
    assert result.value == pytest.approx(0.0)


def test_drawdown_insufficient_data_for_single_bar() -> None:
    result = max_drawdown(make_series([100.0]))
    assert result.insufficient_data is True
    assert result.value is None


def test_drawdown_uses_adjusted_close_not_close() -> None:
    bars = divergent_series()
    result = max_drawdown(bars)
    assert result.value == pytest.approx(-0.05)
