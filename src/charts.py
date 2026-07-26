"""集中创建页面使用的 Plotly 图表。"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def normalized_chart(
    stocks: dict[str, pd.DataFrame], names: dict[str, str]
) -> go.Figure:
    """绘制首日收盘价归一化为 100 的多股票曲线。"""
    figure = go.Figure()
    for symbol, data in stocks.items():
        if not data.empty:
            figure.add_scatter(
                x=data["date"],
                y=data["close"] / data["close"].iloc[0] * 100,
                mode="lines",
                name=f"{names.get(symbol, symbol)}",
            )
    figure.update_layout(
        title="十股相对表现（首日=100）", xaxis_title="日期", yaxis_title="归一化价格"
    )
    return figure


def price_indicator_chart(data: pd.DataFrame, title: str) -> go.Figure:
    """绘制 K 线、短期 MA 和长期 MA。"""
    figure = go.Figure(
        go.Candlestick(
            x=data["date"],
            open=data["open"],
            high=data["high"],
            low=data["low"],
            close=data["close"],
            name="K线",
        )
    )
    figure.add_scatter(x=data["date"], y=data["ma_short"], name="短期 MA")
    figure.add_scatter(x=data["date"], y=data["ma_long"], name="长期 MA")
    figure.update_layout(
        title=title,
        xaxis_title="日期",
        yaxis_title="价格",
        xaxis_rangeslider_visible=False,
    )
    return figure


def rsi_chart(data: pd.DataFrame) -> go.Figure:
    """绘制 RSI 以及常见教学参考线 30/70。"""
    figure = go.Figure(go.Scatter(x=data["date"], y=data["rsi"], name="RSI"))
    figure.add_hline(y=70, line_dash="dash", line_color="red")
    figure.add_hline(y=30, line_dash="dash", line_color="green")
    figure.update_layout(
        title="RSI（30/70 仅为教学参考）", xaxis_title="日期", yaxis_title="RSI"
    )
    return figure


def equity_chart(data: pd.DataFrame) -> go.Figure:
    """绘制策略与买入并持有资产曲线。"""
    figure = go.Figure()
    figure.add_scatter(x=data["date"], y=data["strategy_equity"], name="MA 策略")
    figure.add_scatter(x=data["date"], y=data["buy_hold_equity"], name="买入并持有")
    figure.update_layout(
        title="资产曲线比较", xaxis_title="日期", yaxis_title="模拟资产"
    )
    return figure


def drawdown_chart(data: pd.DataFrame) -> go.Figure:
    """绘制策略回撤曲线。"""
    drawdown = data["strategy_equity"] / data["strategy_equity"].cummax() - 1
    figure = go.Figure(
        go.Scatter(x=data["date"], y=drawdown, fill="tozeroy", name="回撤")
    )
    figure.update_layout(title="策略回撤", xaxis_title="日期", yaxis_title="回撤率")
    return figure
