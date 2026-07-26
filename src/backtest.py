"""教学型 MA 交叉回测：信号收盘后确认，下一交易日开盘执行。"""

from __future__ import annotations

import math

import pandas as pd

from src.indicators import add_indicators


def maximum_drawdown(equity: pd.Series) -> float:
    """计算资产曲线从历史高点到低点的最大跌幅。"""
    if equity.empty:
        return 0.0
    drawdown = equity / equity.cummax() - 1
    return float(drawdown.min())


def _annualized_return(start: float, end: float, days: int) -> float:
    if start <= 0 or days <= 0:
        return 0.0
    return float((end / start) ** (365.25 / days) - 1)


def run_backtest(
    data: pd.DataFrame,
    initial_cash: float = 100_000,
    short_window: int = 20,
    long_window: int = 60,
    rsi_window: int = 14,
    use_rsi_filter: bool = False,
    fee_rate: float = 0.0005,
    cash_fraction: float = 0.5,
) -> dict[str, object]:
    """运行只做多的 MA 交叉策略并返回指标、曲线和交易明细。

    第 t 日收盘才知道交叉，所以将信号后移一行，在 t+1 日开盘成交，
    以避免使用当时尚不可知的信息。
    """
    if data.empty:
        raise ValueError("回测数据不能为空。")
    required = {"date", "open", "close"}
    if not required.issubset(data.columns):
        raise ValueError("回测数据必须包含 date、open、close。")
    if initial_cash <= 0 or fee_rate < 0 or not 0 < cash_fraction <= 1:
        raise ValueError("资金、费率或仓位比例参数无效。")
    frame = add_indicators(data, short_window, long_window, rsi_window)
    frame = frame.sort_values("date").reset_index(drop=True)
    frame["execute_signal"] = frame["signal"].shift(1, fill_value=0).astype(int)
    if use_rsi_filter:
        # 教学过滤：买入信号日 RSI 不高于 70，卖出信号日 RSI 不低于 30。
        prior_rsi = frame["rsi"].shift(1)
        frame.loc[
            (frame["execute_signal"] == 1) & (prior_rsi > 70), "execute_signal"
        ] = 0
        frame.loc[
            (frame["execute_signal"] == -1) & (prior_rsi < 30), "execute_signal"
        ] = 0

    cash = float(initial_cash)
    shares = 0
    trades: list[dict[str, object]] = []
    equity_values: list[float] = []

    for row in frame.itertuples():
        price = float(row.open) if pd.notna(row.open) else math.nan
        if not math.isfinite(price) or price <= 0:
            equity_values.append(cash + shares * float(row.close))
            continue
        if row.execute_signal == 1 and shares == 0:
            budget = cash * cash_fraction
            quantity = int((budget / (price * (1 + fee_rate))) // 100 * 100)
            if quantity >= 100:
                fee = quantity * price * fee_rate
                cash -= quantity * price + fee
                shares = quantity
                trades.append(
                    {
                        "date": row.date,
                        "side": "BUY",
                        "price": price,
                        "quantity": quantity,
                        "fee": fee,
                        "cash_after": cash,
                        "shares_after": shares,
                    }
                )
        elif row.execute_signal == -1 and shares > 0:
            quantity = shares
            fee = quantity * price * fee_rate
            cash += quantity * price - fee
            shares = 0
            trades.append(
                {
                    "date": row.date,
                    "side": "SELL",
                    "price": price,
                    "quantity": quantity,
                    "fee": fee,
                    "cash_after": cash,
                    "shares_after": shares,
                }
            )
        equity_values.append(cash + shares * float(row.close))

    frame["strategy_equity"] = equity_values
    first_close = float(frame["close"].iloc[0])
    frame["buy_hold_equity"] = initial_cash * frame["close"] / first_close
    final_equity = float(frame["strategy_equity"].iloc[-1])
    days = max(
        (
            pd.Timestamp(frame["date"].iloc[-1]) - pd.Timestamp(frame["date"].iloc[0])
        ).days,
        1,
    )
    metrics = {
        "total_return": final_equity / initial_cash - 1,
        "annualized_return": _annualized_return(initial_cash, final_equity, days),
        "max_drawdown": maximum_drawdown(frame["strategy_equity"]),
        "trade_count": len(trades),
        "final_equity": final_equity,
        "buy_hold_return": float(frame["close"].iloc[-1] / first_close - 1),
    }
    return {"metrics": metrics, "equity": frame, "trades": pd.DataFrame(trades)}


def batch_backtest(
    stocks: dict[str, pd.DataFrame], **parameters: object
) -> pd.DataFrame:
    """逐只运行回测；失败股票以 error 列说明，不中断批量任务。"""
    rows: list[dict[str, object]] = []
    for symbol, data in stocks.items():
        try:
            result = run_backtest(data, **parameters)
            rows.append({"symbol": symbol, **result["metrics"]})
        except (ValueError, TypeError, KeyError) as error:
            rows.append({"symbol": symbol, "error": str(error)})
    return pd.DataFrame(rows)
