"""验证模拟订单安全边界和去重。"""

import pytest

from src.paper_trading import execute_paper_order, new_account


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
