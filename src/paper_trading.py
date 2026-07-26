"""模拟交易账户工具，不连接任何真实券商或下单接口。"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


def new_account(initial_cash: float = 100_000) -> dict[str, object]:
    """创建仅存在于当前会话中的模拟账户。"""
    if initial_cash <= 0:
        raise ValueError("初始资金必须大于 0。")
    return {
        "initial_cash": float(initial_cash),
        "cash": float(initial_cash),
        "positions": {},
        "trades": [],
        "processed_signal_ids": set(),
    }


def signal_id(symbol: str, signal_date: object, side: str) -> str:
    """生成可重复计算的信号编号，用于防止重复处理。"""
    side = side.upper()
    if side not in {"BUY", "SELL"}:
        raise ValueError("信号类型只能是 BUY 或 SELL。")
    return f"{symbol}-{pd.Timestamp(signal_date).date().isoformat()}-{side}"


def execute_paper_order(
    account: dict[str, object],
    symbol: str,
    name: str,
    side: str,
    price: float,
    order_date: object | None = None,
    fee_rate: float = 0.0005,
    cash_fraction: float = 0.5,
    reason: str = "MA 交叉",
) -> dict[str, object]:
    """执行整手买入或全部卖出的模拟订单，并原地更新账户。"""
    side = side.upper()
    if side not in {"BUY", "SELL"} or price <= 0 or fee_rate < 0:
        raise ValueError("模拟订单参数无效。")
    trade_date = pd.Timestamp(order_date or datetime.now(timezone.utc).date())
    identifier = signal_id(symbol, trade_date, side)
    processed = account["processed_signal_ids"]
    if identifier in processed:
        raise ValueError("该信号已经处理过。")
    positions: dict[str, int] = account["positions"]
    cash = float(account["cash"])
    current = int(positions.get(symbol, 0))
    if side == "BUY":
        if current > 0:
            raise ValueError("已有持仓，不能重复买入。")
        quantity = int((cash * cash_fraction / (price * (1 + fee_rate))) // 100 * 100)
        if quantity < 100:
            raise ValueError("模拟现金不足以买入 100 股。")
        fee = quantity * price * fee_rate
        cash -= quantity * price + fee
        positions[symbol] = quantity
        profit_loss = 0.0
    else:
        if current <= 0:
            raise ValueError("没有持仓，不能卖出。")
        quantity = current
        fee = quantity * price * fee_rate
        cash += quantity * price - fee
        positions[symbol] = 0
        profit_loss = cash - float(account["initial_cash"])
    account["cash"] = max(cash, 0.0)
    processed.add(identifier)
    total_asset = float(account["cash"]) + positions.get(symbol, 0) * price
    order = {
        "date": trade_date,
        "symbol": symbol,
        "name": name,
        "side": side,
        "reason": reason,
        "price": price,
        "quantity": quantity,
        "fee": fee,
        "cash_after": account["cash"],
        "shares_after": positions.get(symbol, 0),
        "total_asset_after": total_asset,
        "profit_loss": profit_loss,
        "is_paper_trade": True,
        "signal_id": identifier,
    }
    account["trades"].append(order)
    return order


def account_summary(
    account: dict[str, object], prices: dict[str, float]
) -> dict[str, float]:
    """按给定最新价格估算模拟账户总资产和累计盈亏。"""
    market_value = sum(
        quantity * prices.get(symbol, 0.0)
        for symbol, quantity in account["positions"].items()
    )
    total = float(account["cash"]) + market_value
    return {
        "cash": float(account["cash"]),
        "market_value": market_value,
        "total_asset": total,
        "profit_loss": total - float(account["initial_cash"]),
    }
