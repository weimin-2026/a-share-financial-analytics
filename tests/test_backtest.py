"""验证延迟执行、交易约束、费用和回撤。"""

import pandas as pd

from src.backtest import maximum_drawdown, run_backtest
from src.indicators import add_indicators


def test_signal_executes_next_day(price_data: pd.DataFrame) -> None:
    indicators = add_indicators(price_data, 5, 15, 5)
    result = run_backtest(price_data, short_window=5, long_window=15, rsi_window=5)
    trades = result["trades"]
    assert not trades.empty
    first_signal_index = indicators.index[indicators["signal"] == 1][0]
    assert pd.Timestamp(trades.iloc[0]["date"]) == pd.Timestamp(
        price_data.iloc[first_signal_index + 1]["date"]
    )


def test_cash_shares_lot_and_fee(price_data: pd.DataFrame) -> None:
    result = run_backtest(
        price_data,
        initial_cash=100_000,
        short_window=5,
        long_window=15,
        rsi_window=5,
        fee_rate=0.001,
    )
    trades = result["trades"]
    assert (trades["cash_after"] >= 0).all()
    assert (trades["shares_after"] >= 0).all()
    assert (trades["quantity"] % 100 == 0).all()
    assert (trades["fee"] == trades["quantity"] * trades["price"] * 0.001).all()


def test_maximum_drawdown() -> None:
    equity = pd.Series([100.0, 120.0, 90.0, 110.0])
    assert maximum_drawdown(equity) == -0.25
