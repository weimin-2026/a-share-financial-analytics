"""验证 MA、RSI、参数和输入不变性。"""

import pandas as pd
import pytest

from src.indicators import add_indicators, calculate_rsi, calculate_sma


def test_sma_known_values() -> None:
    data = pd.DataFrame({"close": [1, 2, 3, 4]})
    assert calculate_sma(data, 2).tolist()[1:] == [1.5, 2.5, 3.5]


def test_rsi_stays_in_range() -> None:
    data = pd.DataFrame({"close": [1, 2, 1, 3, 2, 4, 3, 5, 4, 6]})
    values = calculate_rsi(data, 3).dropna()
    assert values.between(0, 100).all()


def test_indicator_validation_and_copy(price_data: pd.DataFrame) -> None:
    original = price_data.copy(deep=True)
    with pytest.raises(ValueError):
        add_indicators(price_data, 20, 10, 14)
    result = add_indicators(price_data, 5, 15, 5)
    pd.testing.assert_frame_equal(price_data, original)
    assert {1, -1}.issubset(set(result["signal"]))
