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
from src.config import STOCKS
from src.data import fetch_history, fetch_spot, load_stock_pool
from src.indicators import add_indicators
from src.paper_trading import (
    account_summary,
    execute_paper_order,
    execute_replay_order,
    new_account,
    replay_snapshot,
)
from src.trend import analyze_trend
from src.utils import dataframe_to_csv

st.set_page_config(page_title="A 股金融学习平台", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
    :root {
        --ink: #14213d;
        --muted: #64748b;
        --line: #e2e8f0;
        --blue: #2563eb;
        --soft-blue: #eff6ff;
    }
    .stApp {
        background:
            radial-gradient(circle at 90% 0%, rgba(219, 234, 254, .68), transparent 24rem),
            #f8fafc;
    }
    .block-container {
        max-width: 1280px;
        padding-top: 2.2rem;
        padding-bottom: 4rem;
    }
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, .92);
        border-right: 1px solid var(--line);
    }
    h1, h2, h3 {
        color: var(--ink);
        letter-spacing: -0.02em;
    }
    .hero {
        padding: 2.1rem 2.3rem;
        margin-bottom: 1.6rem;
        border: 1px solid #dbeafe;
        border-radius: 22px;
        background: linear-gradient(135deg, #ffffff 0%, #eff6ff 100%);
        box-shadow: 0 14px 36px rgba(37, 99, 235, .08);
    }
    .hero-kicker {
        color: var(--blue);
        font-size: .82rem;
        font-weight: 700;
        letter-spacing: .12em;
        text-transform: uppercase;
    }
    .hero h1 {
        margin: .45rem 0 .55rem;
        font-size: clamp(2rem, 4vw, 3.35rem);
        line-height: 1.08;
    }
    .hero p {
        max-width: 720px;
        margin: 0;
        color: var(--muted);
        font-size: 1.05rem;
        line-height: 1.8;
    }
    .status-pill {
        display: inline-block;
        padding: .38rem .8rem;
        border: 1px solid #bfdbfe;
        border-radius: 999px;
        background: var(--soft-blue);
        color: #1d4ed8;
        font-size: .82rem;
        font-weight: 700;
    }
    [data-testid="stMetric"] {
        min-height: 116px;
        padding: 1rem 1.1rem;
        border: 1px solid var(--line);
        border-radius: 16px;
        background: rgba(255, 255, 255, .9);
        box-shadow: 0 8px 24px rgba(15, 23, 42, .045);
    }
    [data-testid="stMetricLabel"] {
        color: var(--muted);
    }
    [data-testid="stMetricValue"] {
        font-size: clamp(1.35rem, 2.2vw, 1.9rem);
        letter-spacing: -0.02em;
    }
    [data-testid="stDataFrame"],
    [data-testid="stPlotlyChart"] {
        overflow: hidden;
        border: 1px solid var(--line);
        border-radius: 16px;
        background: #ffffff;
    }
    div.stButton > button,
    div.stDownloadButton > button {
        border-radius: 10px;
        font-weight: 650;
    }
    div[data-testid="stExpander"] {
        border: 1px solid var(--line);
        border-radius: 14px;
        background: rgba(255, 255, 255, .75);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


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


def overview_page() -> None:
    st.markdown(
        """
        <section class="hero">
            <div class="hero-kicker">A-Share Analytics</div>
            <h1>A 股金融数据分析平台</h1>
            <p>观察十只代表性股票的市场表现，探索技术指标、历史策略和模拟账户。</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    title_col, action_col = st.columns([5, 1])
    title_col.subheader("最新行情快照")
    if action_col.button("刷新行情", type="primary", width="stretch"):
        cached_spot.clear()
    try:
        spot, fetched_at, source = cached_spot()
        display_spot = spot.rename(
            columns={
                "symbol": "代码",
                "name": "名称",
                "latest": "最新价",
                "change": "涨跌额",
                "change_pct": "涨跌幅(%)",
                "volume": "成交量",
            }
        )
        st.dataframe(
            display_spot,
            width="stretch",
            hide_index=True,
            column_config={
                "最新价": st.column_config.NumberColumn(format="%.2f"),
                "涨跌额": st.column_config.NumberColumn(format="%+.2f"),
                "涨跌幅(%)": st.column_config.NumberColumn(format="%+.2f%%"),
            },
        )
        st.caption(f"更新于 {fetched_at:%Y-%m-%d %H:%M:%S} · {source}")
    except (ImportError, OSError, RuntimeError, ValueError, KeyError) as error:
        st.error(f"最新行情暂时不可用：{error}")
    st.subheader("股票池")
    st.dataframe(
        pd.DataFrame({"股票代码": STOCKS.keys(), "股票名称": STOCKS.values()}),
        hide_index=True,
        width="stretch",
    )


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


def trend_page() -> None:
    st.title("趋势参考 Trend Reference")
    symbol = stock_selector()
    loaded = load_or_stop(symbol)
    if loaded is None:
        return
    data, _ = loaded
    control_left, control_right = st.columns(2)
    lookback = control_left.slider(
        "历史观察窗口", 60, min(750, len(data)), min(250, len(data))
    )
    future_days = control_right.slider("趋势延伸天数", 5, 30, 10)
    try:
        result = analyze_trend(data, lookback=lookback, future_days=future_days)
    except ValueError as error:
        st.error(str(error))
        return
    history = result["history"]
    split_index = int(result["split_index"])
    train = history.iloc[:split_index]
    test = history.iloc[split_index:]
    future = result["future"]

    figure = go.Figure()
    figure.add_scatter(
        x=history["date"],
        y=history["close"],
        name="真实收盘价",
        line={"color": "#334155", "width": 2},
    )
    figure.add_scatter(
        x=train["date"],
        y=train["trend_fit"],
        name="训练拟合",
        line={"color": "#2563eb", "width": 2, "dash": "dot"},
    )
    figure.add_scatter(
        x=test["date"],
        y=test["trend_fit"],
        name="测试预测",
        line={"color": "#f59e0b", "width": 2, "dash": "dash"},
    )
    future_line = pd.concat(
        [
            pd.DataFrame(
                {
                    "date": [history["date"].iloc[-1]],
                    "trend": [history["trend_fit"].iloc[-1]],
                }
            ),
            future[["date", "trend"]],
        ],
        ignore_index=True,
    )
    figure.add_scatter(
        x=future_line["date"],
        y=future_line["trend"],
        name=f"未来 {future_days} 日延伸",
        line={"color": "#10b981", "width": 3, "dash": "dash"},
    )
    figure.update_layout(
        height=520,
        margin={"l": 20, "r": 20, "t": 70, "b": 20},
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.08, "x": 0},
        xaxis={
            "title": "日期",
            "type": "date",
            "rangeslider": {"visible": True, "thickness": 0.07},
            "showgrid": False,
        },
        yaxis={"title": "价格", "gridcolor": "#e2e8f0"},
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
    )
    st.plotly_chart(figure, width="stretch")
    c1, c2, c3 = st.columns(3)
    c1.metric("测试集 MAE", f"{result['mae']:.3f}")
    c2.metric("趋势方向", result["direction"])
    c3.metric("训练 / 测试", f"{split_index} / {len(history) - split_index} 天")
    with st.expander("如何理解这张图？"):
        st.write(
            "蓝色虚线是训练阶段拟合，橙色虚线是留出的测试阶段预测，"
            "绿色虚线是在同一日期轴上的趋势延伸。MAE 越小表示测试区间平均误差越小。"
        )


def _latest_paper_page() -> None:
    st.caption("账户数据保存在当前浏览器会话中，刷新会话后可重新初始化。")

    initial = 100_000.0
    if "paper_account" not in st.session_state:
        st.session_state.paper_account = new_account(initial)
    if "paper_prices" not in st.session_state:
        st.session_state.paper_prices = {}

    with st.expander("账户与交易设置", expanded=False):
        setting_one, setting_two, setting_three = st.columns(3)
        initial = setting_one.number_input(
            "初始资金",
            10_000.0,
            10_000_000.0,
            float(st.session_state.paper_account["initial_cash"]),
            10_000.0,
        )
        allocation = setting_two.slider("单次买入资金比例", 10, 100, 50, 5) / 100
        fee_rate = setting_three.number_input(
            "单边手续费率",
            0.0,
            0.01,
            0.0005,
            0.0001,
            format="%.4f",
        )
        if st.button("重新初始化账户"):
            st.session_state.paper_account = new_account(initial)
            st.session_state.paper_prices = {}
            st.toast("模拟账户已重新初始化。")

    account = st.session_state.paper_account

    st.subheader("交易面板")
    symbol = stock_selector("选择交易股票")
    loaded = load_or_stop(symbol)
    if loaded is None:
        return
    data, source = loaded

    parameter_one, parameter_two = st.columns(2)
    short = parameter_one.number_input("短期 MA", 2, 100, 20, key="paper_short")
    long = parameter_two.number_input(
        "长期 MA", short + 1, 250, max(60, short + 1), key="paper_long"
    )
    indicators = add_indicators(data, short, long, 14)
    latest = indicators.iloc[-1]
    latest_price = float(latest["close"])
    st.session_state.paper_prices[symbol] = latest_price

    for position_symbol, quantity in account["positions"].items():
        if quantity <= 0 or position_symbol in st.session_state.paper_prices:
            continue
        position_data = load_or_stop(position_symbol)
        if position_data is not None:
            st.session_state.paper_prices[position_symbol] = float(
                position_data[0]["close"].iloc[-1]
            )

    summary = account_summary(account, st.session_state.paper_prices)
    initial_cash = float(account["initial_cash"])
    return_rate = summary["profit_loss"] / initial_cash
    active_positions = sum(quantity > 0 for quantity in account["positions"].values())

    cols = st.columns(4)
    cols[0].metric("可用现金", f"¥{summary['cash']:,.2f}")
    cols[1].metric("持仓市值", f"¥{summary['market_value']:,.2f}")
    cols[2].metric("账户总资产", f"¥{summary['total_asset']:,.2f}")
    cols[3].metric(
        "累计盈亏",
        f"¥{summary['profit_loss']:,.2f}",
        delta=f"{return_rate:+.2%}",
    )

    signal = int(latest["signal"])
    signal_text = (
        "MA 金叉" if signal == 1 else "MA 死叉" if signal == -1 else "暂无新交叉"
    )
    current_shares = int(account["positions"].get(symbol, 0))
    affordable_quantity = int(
        (float(account["cash"]) * allocation / (latest_price * (1 + fee_rate)))
        // 100
        * 100
    )

    trade_tab, account_tab = st.tabs(["模拟下单", "持仓与记录"])
    with trade_tab:
        market_col, order_col = st.columns([1.15, 0.85])
        with market_col:
            st.plotly_chart(
                price_indicator_chart(
                    indicators.tail(180),
                    f"{symbol} {STOCKS[symbol]} · 近 180 个交易日",
                ),
                width="stretch",
                key="paper_price_chart",
            )
        with order_col:
            st.subheader(f"{symbol} {STOCKS[symbol]}")
            st.metric("最近收盘价", f"¥{latest_price:,.2f}")
            detail_one, detail_two = st.columns(2)
            detail_one.metric("当前持仓", f"{current_shares:,} 股")
            detail_two.metric("可买数量", f"{affordable_quantity:,} 股")
            st.caption(
                f"数据日期：{pd.Timestamp(latest['date']):%Y-%m-%d} · "
                f"最新条件：{signal_text} · {source}"
            )

            buy_col, sell_col = st.columns(2)
            buy_clicked = buy_col.button(
                "模拟买入",
                type="primary",
                width="stretch",
                disabled=current_shares > 0 or affordable_quantity < 100,
            )
            sell_clicked = sell_col.button(
                "模拟卖出",
                width="stretch",
                disabled=current_shares <= 0,
            )

            if buy_clicked or sell_clicked:
                side = "BUY" if buy_clicked else "SELL"
                reason = "手动模拟买入" if buy_clicked else "手动模拟卖出"
                try:
                    order = execute_paper_order(
                        account,
                        symbol,
                        STOCKS[symbol],
                        side,
                        latest_price,
                        latest["date"],
                        fee_rate=fee_rate,
                        cash_fraction=allocation,
                        reason=reason,
                    )
                    st.success(
                        f"已完成模拟{('买入' if side == 'BUY' else '卖出')}："
                        f"{order['quantity']:,} 股"
                    )
                    st.rerun()
                except ValueError as error:
                    st.warning(str(error))

            if st.button("按最新 MA 条件检查并执行", width="stretch"):
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
                            fee_rate=fee_rate,
                            cash_fraction=allocation,
                            reason="最新 MA 金叉" if side == "BUY" else "最新 MA 死叉",
                        )
                        st.success(f"已生成模拟记录：{order['quantity']:,} 股。")
                        st.rerun()
                    except ValueError as error:
                        st.warning(str(error))

    with account_tab:
        positions = pd.DataFrame(
            [
                {
                    "股票代码": code,
                    "股票名称": STOCKS.get(code, code),
                    "持仓数量": shares,
                    "参考价格": st.session_state.paper_prices.get(code, 0.0),
                    "持仓市值": shares * st.session_state.paper_prices.get(code, 0.0),
                }
                for code, shares in account["positions"].items()
                if shares > 0
            ]
        )
        trades = pd.DataFrame(account["trades"])
        holding_title, holding_count = st.columns([4, 1])
        holding_title.subheader("当前持仓")
        holding_count.metric("持仓股票", active_positions)
        if positions.empty:
            st.info("当前没有模拟持仓。")
        else:
            st.dataframe(
                positions,
                hide_index=True,
                width="stretch",
                column_config={
                    "参考价格": st.column_config.NumberColumn(format="¥%.2f"),
                    "持仓市值": st.column_config.NumberColumn(format="¥%.2f"),
                },
            )

        st.subheader("交易记录")
        if trades.empty:
            st.info("还没有模拟交易记录。")
        else:
            display_trades = trades.rename(
                columns={
                    "date": "日期",
                    "symbol": "代码",
                    "name": "名称",
                    "side": "方向",
                    "reason": "原因",
                    "price": "价格",
                    "quantity": "数量",
                    "fee": "手续费",
                    "cash_after": "交易后现金",
                    "shares_after": "交易后持仓",
                }
            )
            visible_columns = [
                "日期",
                "代码",
                "名称",
                "方向",
                "原因",
                "价格",
                "数量",
                "手续费",
                "交易后现金",
                "交易后持仓",
            ]
            st.dataframe(
                display_trades[visible_columns],
                hide_index=True,
                width="stretch",
            )
            st.download_button(
                "下载模拟交易记录",
                dataframe_to_csv(trades),
                "paper_trades.csv",
            )


def _save_replay_snapshot(state: dict[str, object], row: pd.Series) -> None:
    """写入当前交易日权益；同一天交易后覆盖旧快照。"""
    snapshot = replay_snapshot(
        state["account"],
        str(state["symbol"]),
        float(row["close"]),
        row["date"],
    )
    equity_curve: list[dict[str, object]] = state["equity_curve"]
    if equity_curve and equity_curve[-1]["date"] == snapshot["date"]:
        equity_curve[-1] = snapshot
    else:
        equity_curve.append(snapshot)


def _new_replay_state(
    symbol: str,
    data: pd.DataFrame,
    start_date: date,
    initial_cash: float,
) -> dict[str, object]:
    """按所选日期创建一局历史回放。"""
    candidates = data.index[data["date"].dt.date >= start_date]
    if candidates.empty:
        raise ValueError("所选日期之后没有可用交易日。")
    start_index = int(candidates[0])
    state: dict[str, object] = {
        "symbol": symbol,
        "requested_start_date": start_date,
        "start_date": pd.Timestamp(data.iloc[start_index]["date"]).date(),
        "start_index": start_index,
        "current_index": start_index,
        "account": new_account(initial_cash),
        "equity_curve": [],
    }
    _save_replay_snapshot(state, data.iloc[start_index])
    return state


def _advance_replay(
    state: dict[str, object], data: pd.DataFrame, target_index: int
) -> None:
    """把回放向前推进并逐日记录账户权益，不允许倒退。"""
    current_index = int(state["current_index"])
    target_index = min(max(target_index, current_index), len(data) - 1)
    for index in range(current_index + 1, target_index + 1):
        _save_replay_snapshot(state, data.iloc[index])
    state["current_index"] = target_index


def _history_replay_page() -> None:
    st.markdown("#### 选择历史起点")
    setup_one, setup_two, setup_three = st.columns([1.2, 1, 1])
    symbol = setup_one.selectbox(
        "回放股票",
        list(STOCKS),
        format_func=lambda code: f"{code} {STOCKS[code]}",
        key="replay_symbol",
    )
    loaded = load_or_stop(symbol)
    if loaded is None:
        return
    data, source = loaded
    first_date = pd.Timestamp(data["date"].iloc[0]).date()
    last_date = pd.Timestamp(data["date"].iloc[-1]).date()
    default_index = max(0, len(data) - 252)
    default_date = pd.Timestamp(data["date"].iloc[default_index]).date()
    start_date = setup_two.date_input(
        "回放开始日期",
        value=default_date,
        min_value=first_date,
        max_value=last_date,
        key=f"replay_start_{symbol}",
    )
    initial_cash = setup_three.number_input(
        "回放初始资金",
        min_value=10_000.0,
        max_value=10_000_000.0,
        value=100_000.0,
        step=10_000.0,
        key="replay_initial_cash",
    )

    setup_signature = (symbol, start_date.isoformat(), float(initial_cash))
    state = st.session_state.get("history_replay")
    state_signature = None
    if state is not None:
        state_signature = (
            state["symbol"],
            state["requested_start_date"].isoformat(),
            float(state["account"]["initial_cash"]),
        )
    start_clicked = st.button(
        "开始 / 重新开始回放",
        type="primary",
        key="start_history_replay",
    )
    if start_clicked or state is None:
        state = _new_replay_state(symbol, data, start_date, initial_cash)
        st.session_state.history_replay = state
        state_signature = setup_signature
    if state_signature != setup_signature:
        st.info("回放设置已改变，请点击“开始 / 重新开始回放”应用新设置。")
        return

    current_index = int(state["current_index"])
    start_index = int(state["start_index"])
    current = data.iloc[current_index]
    current_date = pd.Timestamp(current["date"])
    current_price = float(current["close"])
    account = state["account"]
    summary = account_summary(account, {symbol: current_price})
    shares = int(account["positions"].get(symbol, 0))
    average_cost = float(account["average_costs"].get(symbol, 0.0))
    fee_rate = 0.0005
    progress = (current_index - start_index + 1) / (len(data) - start_index)

    st.progress(
        progress,
        text=(
            f"回放日期：{current_date:%Y-%m-%d}　"
            f"第 {current_index - start_index + 1} / {len(data) - start_index} 个交易日"
        ),
    )
    metrics = st.columns(5)
    metrics[0].metric("当日收盘价", f"¥{current_price:,.2f}")
    metrics[1].metric("可用现金", f"¥{summary['cash']:,.2f}")
    metrics[2].metric("持仓", f"{shares:,} 股")
    metrics[3].metric("账户总资产", f"¥{summary['total_asset']:,.2f}")
    metrics[4].metric(
        "累计盈亏",
        f"¥{summary['profit_loss']:,.2f}",
        delta=f"{summary['profit_loss'] / float(account['initial_cash']):+.2%}",
    )

    chart_col, order_col = st.columns([1.35, 0.65])
    with chart_col:
        indicators = add_indicators(data, 20, 60, 14)
        visible_data = indicators.iloc[: current_index + 1].tail(180)
        st.plotly_chart(
            price_indicator_chart(
                visible_data,
                f"{symbol} {STOCKS[symbol]} · 截至 {current_date:%Y-%m-%d}",
            ),
            width="stretch",
            key="replay_price_chart",
        )
        st.caption("图表只显示当前回放日期及以前的数据，后面的行情尚未揭晓。")

    with order_col:
        st.markdown("#### 当日模拟下单")
        max_buy = int(
            (float(account["cash"]) / (current_price * (1 + fee_rate))) // 100 * 100
        )
        order_quantity = st.number_input(
            "交易数量（100 股的整数倍）",
            min_value=100,
            value=100,
            step=100,
            key="replay_order_quantity",
        )
        detail_one, detail_two = st.columns(2)
        detail_one.metric("最多可买", f"{max_buy:,} 股")
        detail_two.metric("持仓成本", f"¥{average_cost:,.2f}")
        buy_col, sell_col = st.columns(2)
        buy_clicked = buy_col.button(
            "买入",
            type="primary",
            width="stretch",
            disabled=int(order_quantity) > max_buy,
            key="replay_buy",
        )
        sell_clicked = sell_col.button(
            "卖出",
            width="stretch",
            disabled=int(order_quantity) > shares,
            key="replay_sell",
        )
        if buy_clicked or sell_clicked:
            side = "BUY" if buy_clicked else "SELL"
            try:
                order = execute_replay_order(
                    account,
                    symbol,
                    STOCKS[symbol],
                    side,
                    int(order_quantity),
                    current_price,
                    current_date,
                    fee_rate,
                )
                _save_replay_snapshot(state, current)
                st.toast(
                    f"{current_date:%Y-%m-%d} 已模拟"
                    f"{'买入' if side == 'BUY' else '卖出'} "
                    f"{order['quantity']:,} 股"
                )
                st.rerun()
            except ValueError as error:
                st.warning(str(error))
        st.caption(f"成交价使用当日收盘价 · 单边手续费率 {fee_rate:.04%}")

    st.markdown("#### 推进时间")
    next_col, fast_col, jump_col = st.columns([0.8, 0.9, 1.5])
    at_end = current_index >= len(data) - 1
    if next_col.button(
        "下一个交易日",
        width="stretch",
        disabled=at_end,
        key="replay_next_day",
    ):
        _advance_replay(state, data, current_index + 1)
        st.rerun()
    fast_days = fast_col.selectbox(
        "快速推进",
        [5, 10, 20],
        format_func=lambda value: f"{value} 个交易日",
        key="replay_fast_days",
        disabled=at_end,
    )
    if fast_col.button(
        "执行推进",
        width="stretch",
        disabled=at_end,
        key="replay_fast_forward",
    ):
        _advance_replay(state, data, current_index + int(fast_days))
        st.rerun()

    jump_default_index = min(current_index + 20, len(data) - 1)
    jump_date = jump_col.date_input(
        "直接推进到日期",
        value=pd.Timestamp(data.iloc[jump_default_index]["date"]).date(),
        min_value=current_date.date(),
        max_value=last_date,
        key=f"replay_jump_{current_index}",
        disabled=at_end,
    )
    if jump_col.button(
        "推进到所选日期",
        width="stretch",
        disabled=at_end,
        key=f"replay_jump_button_{current_index}",
    ):
        candidates = data.index[data["date"].dt.date >= jump_date]
        target_index = int(candidates[0]) if not candidates.empty else len(data) - 1
        _advance_replay(state, data, target_index)
        st.rerun()
    if at_end:
        st.success("历史行情已经回放到最后一个交易日，可查看最终成绩或重新开始。")

    result_tab, trade_tab = st.tabs(["账户收益曲线", "回放交易记录"])
    with result_tab:
        equity = pd.DataFrame(state["equity_curve"])
        figure = go.Figure()
        figure.add_scatter(
            x=equity["date"],
            y=equity["total_asset"],
            mode="lines+markers",
            name="账户总资产",
        )
        figure.add_hline(
            y=float(account["initial_cash"]),
            line_dash="dash",
            line_color="#94a3b8",
            annotation_text="初始资金",
        )
        figure.update_layout(
            xaxis_title="回放日期",
            yaxis_title="账户资产",
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            height=360,
        )
        st.plotly_chart(figure, width="stretch", key="replay_equity_chart")
    with trade_tab:
        trades = pd.DataFrame(account["trades"])
        if trades.empty:
            st.info("还没有交易。选择股数并在某个回放日期买入或卖出。")
        else:
            display_trades = trades.rename(
                columns={
                    "date": "日期",
                    "side": "方向",
                    "price": "成交价",
                    "quantity": "数量",
                    "fee": "手续费",
                    "cash_after": "交易后现金",
                    "shares_after": "交易后持仓",
                    "profit_loss": "本次实现盈亏",
                }
            )
            display_trades["方向"] = display_trades["方向"].map(
                {"BUY": "买入", "SELL": "卖出"}
            )
            st.dataframe(
                display_trades[
                    [
                        "日期",
                        "方向",
                        "成交价",
                        "数量",
                        "手续费",
                        "交易后现金",
                        "交易后持仓",
                        "本次实现盈亏",
                    ]
                ],
                hide_index=True,
                width="stretch",
            )
            st.download_button(
                "下载回放交易记录",
                dataframe_to_csv(trades),
                "history_replay_trades.csv",
            )
    st.caption(f"行情来源：{source}。历史回放只用于学习，不连接真实券商。")


def paper_page() -> None:
    st.title("模拟交易 Paper Trading")
    st.markdown('<span class="status-pill">● 模拟账户</span>', unsafe_allow_html=True)
    latest_tab, replay_tab = st.tabs(["最新行情模拟", "历史回放模式"])
    with latest_tab:
        _latest_paper_page()
    with replay_tab:
        _history_replay_page()


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
PAGES[selected_page]()
