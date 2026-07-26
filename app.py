"""A 股金融数据分析与基础回测平台的 Streamlit 入口。"""

from __future__ import annotations

from datetime import date, datetime, timezone

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.backtest import batch_backtest, run_backtest
from src.charts import (
    drawdown_chart,
    equity_chart,
    normalized_chart,
    price_indicator_chart,
    rsi_chart,
)
from src.config import DISCLAIMER_ZH, DISCLAIMERS_EN, STOCKS
from src.data import fetch_history, fetch_spot, load_stock_pool
from src.indicators import add_indicators
from src.paper_trading import account_summary, execute_paper_order, new_account
from src.trend import analyze_trend
from src.utils import dataframe_to_csv

st.set_page_config(page_title="A 股金融学习平台", page_icon="📊", layout="wide")


@st.cache_data(ttl=21_600, show_spinner=False)
def cached_history(symbol: str) -> tuple[pd.DataFrame, str]:
    """缓存单只股票历史数据六小时。"""
    return fetch_history(symbol)


@st.cache_data(ttl=60, show_spinner=False)
def cached_spot() -> tuple[pd.DataFrame, object, str]:
    """缓存市场快照一分钟。"""
    return fetch_spot()


def stock_selector(label: str = "选择股票") -> str:
    """显示带名称的股票选择器并返回代码。"""
    return st.selectbox(
        label, list(STOCKS), format_func=lambda code: f"{code} {STOCKS[code]}"
    )


def load_or_stop(symbol: str) -> tuple[pd.DataFrame, str] | None:
    """在页面上友好显示数据错误。"""
    try:
        return cached_history(symbol)
    except (RuntimeError, ValueError) as error:
        st.error(str(error))
        return None


def show_disclaimer() -> None:
    """显示所有页面共用的中英文风险说明。"""
    st.warning(DISCLAIMER_ZH)
    st.caption(DISCLAIMERS_EN)


def overview_page() -> None:
    st.title("A 股金融数据分析与基础回测平台")
    st.subheader("A-Share Financial Analytics and Backtesting Platform")
    st.write(
        "这是一个面向学习与申请展示的 Python 项目：从公开数据获取、清洗、"
        "可视化，到 MA/RSI、基础回测、趋势参考和模拟交易。"
    )
    st.markdown(
        "**技术栈：** Python · Streamlit · pandas · Plotly · AKShare · scikit-learn"
    )
    st.info("分析流程：公开行情 → 数据清洗 → 指标计算 → 历史回测 → 风险解释")
    st.subheader("最新行情快照")
    if st.button("刷新最新行情", type="primary"):
        cached_spot.clear()
    try:
        spot, fetched_at, source = cached_spot()
        st.dataframe(spot, width="stretch", hide_index=True)
        st.caption(f"获取时间：{fetched_at:%Y-%m-%d %H:%M:%S}；来源：{source}")
    except (ImportError, OSError, RuntimeError, ValueError, KeyError) as error:
        st.error(f"最新行情暂时不可用：{error}")
    st.caption(
        "最新行情为第三方公开数据源在页面刷新时提供的市场快照，可能存在延迟，"
        "仅用于学习展示。未完成的当日行情不会加入历史回测。"
    )
    st.subheader("教学股票池")
    st.dataframe(
        pd.DataFrame({"股票代码": STOCKS.keys(), "股票名称": STOCKS.values()}),
        hide_index=True,
        width="stretch",
    )
    show_disclaimer()


def comparison_page() -> None:
    st.title("十股对比 Market Comparison")
    with st.spinner("逐只加载公开历史行情……"):
        loaded, errors = load_stock_pool()
    if errors:
        st.warning(f"{len(errors)} 只股票加载失败，其余股票仍可比较。")
        with st.expander("查看失败原因"):
            st.json(errors)
    if not loaded:
        st.error("在线数据和本地缓存均不可用，无法进行比较。")
        return
    summary = []
    for symbol, data in loaded.items():
        summary.append(
            {
                "代码": symbol,
                "名称": STOCKS[symbol],
                "起始日期": data["date"].min().date(),
                "结束日期": data["date"].max().date(),
                "行数": len(data),
                "区间变化": data["close"].iloc[-1] / data["close"].iloc[0] - 1,
            }
        )
    summary_frame = pd.DataFrame(summary)
    st.plotly_chart(normalized_chart(loaded, STOCKS), width="stretch")
    st.caption("归一化图只比较相对变化，不代表实际价格。")
    st.dataframe(
        summary_frame,
        column_config={"区间变化": st.column_config.NumberColumn(format="%.2f%%")},
        hide_index=True,
        width="stretch",
    )
    st.download_button(
        "下载比较 CSV", dataframe_to_csv(summary_frame), "market_comparison.csv"
    )
    show_disclaimer()


def analysis_page() -> None:
    st.title("个股分析 Stock Analysis")
    symbol = stock_selector()
    loaded = load_or_stop(symbol)
    if loaded is None:
        return
    data, source = loaded
    st.caption(
        f"数据来源：{source}；范围：{data['date'].min().date()} 至 {data['date'].max().date()}"
    )
    left, right = st.columns(2)
    short = left.slider("短期 MA", 5, 50, 20)
    long = right.slider("长期 MA", max(short + 1, 20), 200, max(60, short + 1))
    rsi_window = st.slider("RSI 周期", 5, 30, 14)
    current_year = datetime.now(timezone.utc).year
    start = st.date_input(
        "分析开始日期",
        value=max(data["date"].min().date(), date(current_year - 3, 1, 1)),
    )
    selected = data[data["date"] >= pd.Timestamp(start)].copy()
    try:
        indicators = add_indicators(selected, short, long, rsi_window)
    except ValueError as error:
        st.error(str(error))
        return
    st.plotly_chart(
        price_indicator_chart(indicators, f"{symbol} {STOCKS[symbol]} 价格与 MA"),
        width="stretch",
    )
    volume = go.Figure(
        go.Bar(x=indicators["date"], y=indicators["volume"], name="成交量")
    )
    volume.update_layout(title="成交量", xaxis_title="日期", yaxis_title="成交量")
    st.plotly_chart(volume, width="stretch")
    st.plotly_chart(rsi_chart(indicators), width="stretch")
    st.dataframe(indicators.tail(20), width="stretch", hide_index=True)
    st.download_button(
        "下载个股数据 CSV", dataframe_to_csv(indicators), f"{symbol}_analysis.csv"
    )
    show_disclaimer()


def backtest_page() -> None:
    st.title("策略回测 Backtesting")
    symbol = stock_selector()
    loaded = load_or_stop(symbol)
    if loaded is None:
        return
    data, source = loaded
    c1, c2, c3 = st.columns(3)
    initial_cash = c1.number_input(
        "初始资金", 10_000.0, 10_000_000.0, 100_000.0, 10_000.0
    )
    short = c2.number_input("短期 MA", 2, 100, 20)
    long = c3.number_input("长期 MA", short + 1, 250, max(60, short + 1))
    fee = st.number_input("单边手续费率", 0.0, 0.01, 0.0005, 0.0001, format="%.4f")
    use_rsi = st.checkbox("启用 RSI 教学过滤（默认关闭）")
    if not st.button("运行单股回测", type="primary"):
        st.info("信号在收盘后确认，并延迟到下一交易日开盘成交，以避免前视偏差。")
        return
    try:
        result = run_backtest(
            data,
            initial_cash=initial_cash,
            short_window=short,
            long_window=long,
            fee_rate=fee,
            use_rsi_filter=use_rsi,
        )
    except ValueError as error:
        st.error(str(error))
        return
    metrics = result["metrics"]
    cols = st.columns(6)
    cols[0].metric("累计收益", f"{metrics['total_return']:.2%}")
    cols[1].metric("年化收益", f"{metrics['annualized_return']:.2%}")
    cols[2].metric("最大回撤", f"{metrics['max_drawdown']:.2%}")
    cols[3].metric("交易次数", metrics["trade_count"])
    cols[4].metric("最终总资产", f"¥{metrics['final_equity']:,.0f}")
    cols[5].metric("买入持有", f"{metrics['buy_hold_return']:.2%}")
    st.caption(f"数据来源：{source}。手续费是教学型简化费率，不包含全部真实交易成本。")
    st.plotly_chart(equity_chart(result["equity"]), width="stretch")
    st.plotly_chart(drawdown_chart(result["equity"]), width="stretch")
    st.subheader("模拟交易明细")
    st.dataframe(result["trades"], width="stretch", hide_index=True)
    st.download_button(
        "下载交易明细 CSV",
        dataframe_to_csv(result["trades"]),
        f"{symbol}_backtest_trades.csv",
    )
    if st.checkbox("同时批量回测十股"):
        loaded_pool, errors = load_stock_pool()
        batch = batch_backtest(
            loaded_pool,
            initial_cash=initial_cash,
            short_window=short,
            long_window=long,
            fee_rate=fee,
            use_rsi_filter=use_rsi,
        )
        st.dataframe(batch, width="stretch", hide_index=True)
        st.download_button(
            "下载批量结果 CSV", dataframe_to_csv(batch), "batch_backtest.csv"
        )
        if errors:
            st.caption(f"另有 {len(errors)} 只股票因数据不可用未参加回测。")
    show_disclaimer()


def trend_page() -> None:
    st.title("趋势参考 Trend Reference")
    symbol = stock_selector()
    loaded = load_or_stop(symbol)
    if loaded is None:
        return
    data, _ = loaded
    lookback = st.slider("观察交易日", 60, min(750, len(data)), min(250, len(data)))
    try:
        result = analyze_trend(data, lookback=lookback)
    except ValueError as error:
        st.error(str(error))
        return
    history = result["history"]
    figure = go.Figure()
    figure.add_scatter(x=history["date"], y=history["close"], name="真实价格")
    figure.add_scatter(x=history["date"], y=history["trend_fit"], name="线性趋势")
    future = result["future"]
    figure.add_scatter(
        x=future["step"], y=future["trend"], name="未来 10 日趋势延伸", line_dash="dash"
    )
    figure.update_layout(
        title="线性回归教学趋势", xaxis_title="历史日期 / 未来步数", yaxis_title="价格"
    )
    st.plotly_chart(figure, width="stretch")
    c1, c2 = st.columns(2)
    c1.metric("测试集 MAE", f"{result['mae']:.3f}")
    c2.metric("趋势方向", result["direction"])
    st.info(
        "MAE 是测试集平均绝对误差。误差较小不代表未来准确；线性回归只是一条简化趋势参考，"
        "不显示买卖建议、目标价或收益保证。"
    )
    show_disclaimer()


def paper_page() -> None:
    st.title("模拟交易 Paper Trading")
    st.error("本页只生成模拟记录，不连接真实券商，也不会真实下单。")
    initial = st.number_input(
        "模拟初始资金", 10_000.0, 10_000_000.0, 100_000.0, 10_000.0
    )
    if "paper_account" not in st.session_state:
        st.session_state.paper_account = new_account(initial)
    c1, c2 = st.columns(2)
    if c1.button("初始化 / 重置模拟账户"):
        st.session_state.paper_account = new_account(initial)
    if c2.button("清空账户"):
        st.session_state.paper_account = new_account(initial)
    account = st.session_state.paper_account
    symbol = stock_selector()
    loaded = load_or_stop(symbol)
    if loaded is None:
        return
    data, _ = loaded
    short = st.number_input("短期 MA", 2, 100, 20, key="paper_short")
    long = st.number_input(
        "长期 MA", short + 1, 250, max(60, short + 1), key="paper_long"
    )
    indicators = add_indicators(data, short, long, 14)
    latest = indicators.iloc[-1]
    latest_price = float(latest["close"])
    if st.button("检查最新条件", type="primary"):
        signal = int(latest["signal"])
        if signal == 0:
            st.info("最近一个交易日没有出现新的 MA 交叉。")
        else:
            side = "BUY" if signal == 1 else "SELL"
            try:
                order = execute_paper_order(
                    account,
                    symbol,
                    STOCKS[symbol],
                    side,
                    latest_price,
                    latest["date"],
                    reason="最新 MA 金叉" if side == "BUY" else "最新 MA 死叉",
                )
                st.success(f"已生成模拟 {side} 记录：{order['quantity']} 股。")
            except ValueError as error:
                st.warning(str(error))
    summary = account_summary(account, {symbol: latest_price})
    cols = st.columns(4)
    cols[0].metric("模拟现金", f"¥{summary['cash']:,.2f}")
    cols[1].metric("当前持仓市值", f"¥{summary['market_value']:,.2f}")
    cols[2].metric("模拟总资产", f"¥{summary['total_asset']:,.2f}")
    cols[3].metric("累计盈亏", f"¥{summary['profit_loss']:,.2f}")
    positions = pd.DataFrame(
        [
            {"symbol": code, "name": STOCKS.get(code, code), "shares": shares}
            for code, shares in account["positions"].items()
        ]
    )
    trades = pd.DataFrame(account["trades"])
    st.subheader("模拟持仓")
    st.dataframe(positions, hide_index=True, width="stretch")
    st.subheader("模拟交易日志")
    st.dataframe(trades, hide_index=True, width="stretch")
    st.download_button("下载模拟日志 CSV", dataframe_to_csv(trades), "paper_trades.csv")
    show_disclaimer()


def methodology_page() -> None:
    st.title("方法与风险 Methodology & Risks")
    st.markdown(
        """
### 数据
历史行情来自 AKShare 聚合的公开数据。页面优先在线获取，失败时读取本地 CSV 缓存；
两者都不可用便明确报错，不生成假数据。

### 指标
MA 是一段时间收盘价的算术平均；RSI 用上涨和下跌幅度描述相对强弱。
30 和 70 只是常见教学参考线。

### 回测
MA 金叉产生买入信号，死叉产生卖出信号。第 t 日收盘后才能确认交叉，
因此第 t+1 个交易日开盘才模拟成交。这能避免用未来信息交易的前视偏差。

### 限制
手续费被简化；没有考虑滑点、涨跌停、停牌、分红税费和流动性冲击。
历史回测可能过度拟合，线性趋势也无法可靠预测未来。
"""
    )
    show_disclaimer()


PAGES = {
    "项目首页 Overview": overview_page,
    "十股对比 Market Comparison": comparison_page,
    "个股分析 Stock Analysis": analysis_page,
    "策略回测 Backtesting": backtest_page,
    "趋势参考 Trend Reference": trend_page,
    "模拟交易 Paper Trading": paper_page,
    "方法与风险 Methodology & Risks": methodology_page,
}

st.sidebar.title("导航 Navigation")
selected_page = st.sidebar.radio("选择页面", list(PAGES))
st.sidebar.caption("所有交易均为模拟。")
PAGES[selected_page]()
