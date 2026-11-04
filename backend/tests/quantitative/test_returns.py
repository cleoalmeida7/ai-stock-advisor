import pytest

from app.quantitative.returns import cumulative_return, daily_returns
from tests.quantitative.fixtures import divergent_series, make_series


def test_daily_returns_hand_computed() -> None:
    bars = make_series([100.0, 110.0, 99.0])
    assert daily_returns(bars) == pytest.approx([0.10, -0.10])


def test_daily_returns_empty_for_single_bar() -> None:
    assert daily_returns(make_series([100.0])) == []


def test_daily_returns_empty_for_no_bars() -> None:
    assert daily_returns([]) == []


def test_cumulative_return_hand_computed() -> None:
    result = cumulative_return(make_series([100.0, 121.0]))
    assert result.insufficient_data is False
    assert result.value == pytest.approx(0.21)
    assert result.observations_used == 2


def test_cumulative_return_insufficient_data_for_single_bar() -> None:
    result = cumulative_return(make_series([100.0]))
    assert result.insufficient_data is True
    assert result.value is None


def test_returns_use_adjusted_close_not_close() -> None:
    bars = divergent_series()
    rets = daily_returns(bars)
    # close is flat (would give 0.0 everywhere if this read the wrong
    # column); adjusted_close has a real -5% move on day 2 only.
    assert rets[0] == pytest.approx(-0.05)
    assert rets[1:] == pytest.approx([0.0, 0.0, 0.0])

    cum = cumulative_return(bars)
    assert cum.value == pytest.approx(-0.05)
