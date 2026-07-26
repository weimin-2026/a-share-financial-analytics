"""通用的小工具函数。"""

from __future__ import annotations

import pandas as pd


def dataframe_to_csv(data: pd.DataFrame) -> bytes:
    """将表格转为带 UTF-8 BOM 的 CSV，便于 Excel 正确显示中文。"""
    if data.empty:
        return b""
    return data.to_csv(index=False).encode("utf-8-sig")


def validate_date_range(start: object, end: object) -> None:
    """验证开始日期不晚于结束日期。"""
    if pd.Timestamp(start) > pd.Timestamp(end):
        raise ValueError("开始日期不能晚于结束日期。")
