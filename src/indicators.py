"""计算移动平均线和 RSI，仅用于教学分析。"""

from __future__ import annotations

import numpy as np
import pandas as pd


def calculate_sma(
    data: pd.DataFrame, window: int, price_column: str = "close"
) -> pd.Series:
    """计算简单移动平均线；数据不足的开头位置保留为空。"""
    if window <= 0:
        raise ValueError("MA 周期必须大于 0。")
    if price_column not in data:
        raise ValueError(f"缺少价格列：{price_column}")
    return pd.to_numeric(data[price_column], errors="coerce").rolling(window).mean()


def calculate_rsi(
    data: pd.DataFrame, window: int = 14, price_column: str = "close"
) -> pd.Series:
    """计算 0 到 100 的 RSI；连续上涨为 100，连续不变为 50。"""
    if window <= 0:
        raise ValueError("RSI 周期必须大于 0。")
    if price_column not in data:
        raise ValueError(f"缺少价格列：{price_column}")
    prices = pd.to_numeric(data[price_column], errors="coerce")
    change = prices.diff()
    gains = change.clip(lower=0)
    losses = -change.clip(upper=0)
    average_gain = gains.rolling(window, min_periods=window).mean()
    average_loss = losses.rolling(window, min_periods=window).mean()
    strength = average_gain / average_loss.replace(0, np.nan)
    rsi = 100 - 100 / (1 + strength)
    rsi = rsi.mask((average_loss == 0) & (average_gain > 0), 100)
    rsi = rsi.mask((average_loss == 0) & (average_gain == 0), 50)
    return rsi.clip(0, 100)


def add_indicators(
    data: pd.DataFrame,
    short_window: int = 20,
    long_window: int = 60,
    rsi_window: int = 14,
) -> pd.DataFrame:
    """复制数据并加入短期 MA、长期 MA、RSI 和交叉信号。"""
    if short_window <= 0 or long_window <= 0 or rsi_window <= 0:
        raise ValueError("所有指标周期必须大于 0。")
    if short_window >= long_window:
        raise ValueError("短期 MA 必须小于长期 MA。")
    if len(data) < long_window:
        raise ValueError(f"数据不足：至少需要 {long_window} 行。")
    result = data.copy()
    result["ma_short"] = calculate_sma(result, short_window)
    result["ma_long"] = calculate_sma(result, long_window)
    result["rsi"] = calculate_rsi(result, rsi_window)
    above = result["ma_short"] > result["ma_long"]
    result["signal"] = np.select(
        [
            above & ~above.shift(1, fill_value=False),
            ~above & above.shift(1, fill_value=False),
        ],
        [1, -1],
        default=0,
    )
    return result
