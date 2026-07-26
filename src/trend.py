"""用线性回归展示简化趋势，结果不是投资预测。"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error


def analyze_trend(
    data: pd.DataFrame,
    lookback: int = 250,
    train_ratio: float = 0.8,
    future_days: int = 10,
) -> dict[str, object]:
    """按时间顺序切分训练/测试集，并延伸一条教学型趋势线。"""
    if "close" not in data:
        raise ValueError("趋势数据缺少 close 列。")
    if lookback < 20 or future_days <= 0 or not 0.5 <= train_ratio < 1:
        raise ValueError("趋势参数无效。")
    frame = data.tail(lookback).dropna(subset=["close"]).copy().reset_index(drop=True)
    if len(frame) < 20:
        raise ValueError("趋势分析至少需要 20 个交易日。")
    x = np.arange(len(frame), dtype=float).reshape(-1, 1)
    y = frame["close"].to_numpy(dtype=float)
    split = int(len(frame) * train_ratio)
    if split <= 1 or split >= len(frame):
        raise ValueError("训练集和测试集都必须包含数据。")
    model = LinearRegression().fit(x[:split], y[:split])
    predictions = model.predict(x)
    test_mae = float(mean_absolute_error(y[split:], predictions[split:]))
    future_x = np.arange(len(frame), len(frame) + future_days).reshape(-1, 1)
    future = model.predict(future_x)
    future_dates = pd.bdate_range(
        start=pd.Timestamp(frame["date"].iloc[-1]) + pd.offsets.BDay(1),
        periods=future_days,
    )
    relative_slope = float(model.coef_[0] / max(abs(y.mean()), 1e-9))
    direction = (
        "向上"
        if relative_slope > 0.0002
        else "向下"
        if relative_slope < -0.0002
        else "接近平稳"
    )
    result = frame.copy()
    result["trend_fit"] = predictions
    result["set"] = np.where(np.arange(len(frame)) < split, "训练集", "测试集")
    return {
        "history": result,
        "future": pd.DataFrame(
            {
                "date": future_dates,
                "step": range(1, future_days + 1),
                "trend": future,
            }
        ),
        "mae": test_mae,
        "direction": direction,
        "split_index": split,
    }
