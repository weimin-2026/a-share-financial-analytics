"""验证模拟订单安全边界和去重。"""

import pytest

from src.paper_trading import (
    execute_paper_order,
    execute_replay_order,
    new_account,
    replay_snapshot,
)


def test_paper_order_and_duplicate_id() -> None:
    account = new_account(100_000)
    order = execute_paper_order(
        account, "000001", "平安银行", "BUY", 10.0, "2025-01-02"
    )
    assert order["quantity"] % 100 == 0
    assert order["is_paper_trade"] is True
    assert account["cash"] >= 0
    with pytest.raises(ValueError, match="已经处理"):
        execute_paper_order(account, "000001", "平安银行", "BUY", 10.0, "2025-01-02")


def test_cannot_sell_without_position() -> None:
    account = new_account()
    with pytest.raises(ValueError, match="没有持仓"):
        execute_paper_order(account, "000001", "平安银行", "SELL", 10.0, "2025-01-02")


def test_replay_supports_selected_quantity_and_partial_sell() -> None:
    account = new_account(100_000)
    execute_replay_order(account, "000001", "平安银行", "BUY", 500, 10.0, "2025-01-02")
    execute_replay_order(account, "000001", "平安银行", "BUY", 300, 12.0, "2025-01-02")
    sell_order = execute_replay_order(
        account, "000001", "平安银行", "SELL", 200, 13.0, "2025-02-03"
    )

    assert account["positions"]["000001"] == 600
    assert account["average_costs"]["000001"] > 10
    assert sell_order["quantity"] == 200
    assert sell_order["profit_loss"] > 0
    snapshot = replay_snapshot(account, "000001", 13.0, "2025-02-03")
    assert snapshot["total_asset"] > 100_000


def test_replay_rejects_invalid_quantity_and_overselling() -> None:
    account = new_account()
    with pytest.raises(ValueError, match="100 股整数倍"):
        execute_replay_order(
            account, "000001", "平安银行", "BUY", 50, 10.0, "2025-01-02"
        )
    with pytest.raises(ValueError, match="超过当前持仓"):
        execute_replay_order(
            account, "000001", "平安银行", "SELL", 100, 10.0, "2025-01-02"
        )
