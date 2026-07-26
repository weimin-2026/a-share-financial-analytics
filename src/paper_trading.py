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
        "average_costs": {},
        "realized_profit_loss": 0.0,
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


def execute_replay_order(
    account: dict[str, object],
    symbol: str,
    name: str,
    side: str,
    quantity: int,
    price: float,
    order_date: object,
    fee_rate: float = 0.0005,
) -> dict[str, object]:
    """在历史回放中按指定股数成交，支持分批买入和部分卖出。"""
    side = side.upper()
    if side not in {"BUY", "SELL"} or price <= 0 or fee_rate < 0:
        raise ValueError("历史回放订单参数无效。")
    if quantity <= 0 or quantity % 100 != 0:
        raise ValueError("交易数量必须是大于 0 的 100 股整数倍。")

    positions: dict[str, int] = account["positions"]
    average_costs: dict[str, float] = account.setdefault("average_costs", {})
    cash = float(account["cash"])
    current = int(positions.get(symbol, 0))
    average_cost = float(average_costs.get(symbol, 0.0))
    gross_amount = quantity * price
    fee = gross_amount * fee_rate

    if side == "BUY":
        required_cash = gross_amount + fee
        if required_cash > cash + 1e-9:
            raise ValueError("可用现金不足，无法完成这笔买入。")
        new_quantity = current + quantity
        average_costs[symbol] = (current * average_cost + required_cash) / new_quantity
        positions[symbol] = new_quantity
        cash -= required_cash
        realized_profit_loss = 0.0
    else:
        if quantity > current:
            raise ValueError("卖出数量超过当前持仓。")
        net_proceeds = gross_amount - fee
        realized_profit_loss = net_proceeds - average_cost * quantity
        cash += net_proceeds
        positions[symbol] = current - quantity
        account["realized_profit_loss"] = (
            float(account.get("realized_profit_loss", 0.0)) + realized_profit_loss
        )
        if positions[symbol] == 0:
            average_costs[symbol] = 0.0

    account["cash"] = max(cash, 0.0)
    trade_date = pd.Timestamp(order_date)
    total_asset = float(account["cash"]) + positions.get(symbol, 0) * price
    order = {
        "date": trade_date,
        "symbol": symbol,
        "name": name,
        "side": side,
        "reason": "历史回放手动交易",
        "price": price,
        "quantity": quantity,
        "fee": fee,
        "cash_after": account["cash"],
        "shares_after": positions.get(symbol, 0),
        "average_cost_after": average_costs.get(symbol, 0.0),
        "total_asset_after": total_asset,
        "profit_loss": realized_profit_loss,
        "is_paper_trade": True,
        "signal_id": (
            f"replay-{symbol}-{trade_date.date().isoformat()}-"
            f"{len(account['trades']) + 1}"
        ),
    }
    account["trades"].append(order)
    return order


def replay_snapshot(
    account: dict[str, object],
    symbol: str,
    price: float,
    snapshot_date: object,
) -> dict[str, object]:
    """记录回放某个交易日的账户资产，供收益曲线使用。"""
    summary = account_summary(account, {symbol: price})
    return {
        "date": pd.Timestamp(snapshot_date),
        "price": float(price),
        "cash": summary["cash"],
        "market_value": summary["market_value"],
        "total_asset": summary["total_asset"],
        "profit_loss": summary["profit_loss"],
        "return_rate": summary["profit_loss"] / float(account["initial_cash"]),
    }
