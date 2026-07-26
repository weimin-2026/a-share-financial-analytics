"""验证趋势模块按时间切分并正确计算 MAE。"""

import pytest

from src.trend import analyze_trend


def test_time_split_and_mae(price_data) -> None:
    result = analyze_trend(price_data, lookback=80, train_ratio=0.8, future_days=10)
    history = result["history"]
    split = result["split_index"]
    assert (history.iloc[:split]["set"] == "训练集").all()
    assert (history.iloc[split:]["set"] == "测试集").all()
    assert result["mae"] >= 0
    assert len(result["future"]) == 10
    assert result["future"]["date"].min() > history["date"].max()


def test_empty_trend_rejected(price_data) -> None:
    with pytest.raises(ValueError):
        analyze_trend(price_data.iloc[:5], lookback=20)
