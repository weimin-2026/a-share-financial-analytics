"""测试共用的固定小型行情，不访问网络。"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def price_data() -> pd.DataFrame:
    """生成先跌、后涨、再跌的数据，覆盖金叉和死叉。"""
    close = np.concatenate(
        [np.linspace(20, 10, 30), np.linspace(10, 30, 35), np.linspace(30, 12, 35)]
    )
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=len(close), freq="B"),
            "open": close * 1.001,
            "high": close * 1.02,
            "low": close * 0.98,
            "close": close,
            "volume": np.arange(len(close)) + 1000,
        }
    )
