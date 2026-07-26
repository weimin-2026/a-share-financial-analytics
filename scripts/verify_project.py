"""检查项目文件、可导入函数、股票池、测试和风险边界。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.backtest import run_backtest
from src.config import DISCLAIMER_ZH, STOCKS
from src.indicators import add_indicators
from src.paper_trading import execute_paper_order
from src.trend import analyze_trend

REQUIRED = [
    "app.py",
    "README.md",
    "requirements.txt",
    "src/data.py",
    "src/indicators.py",
    "src/backtest.py",
    "src/trend.py",
    "src/paper_trading.py",
    "tests/test_indicators.py",
    "docs/ACCEPTANCE_CHECKLIST.md",
]


def main() -> int:
    """执行可重复的离线项目验收。"""
    errors: list[str] = []
    missing = [path for path in REQUIRED if not (ROOT / path).exists()]
    if missing:
        errors.append(f"缺少文件：{', '.join(missing)}")
    if len(STOCKS) != 10:
        errors.append("股票池不是 10 只股票。")
    if not all(
        callable(item)
        for item in [add_indicators, run_backtest, analyze_trend, execute_paper_order]
    ):
        errors.append("核心函数不可调用。")
    readme = (
        (ROOT / "README.md").read_text(encoding="utf-8")
        if (ROOT / "README.md").exists()
        else ""
    )
    if DISCLAIMER_ZH not in readme:
        errors.append("README 缺少中文风险声明。")
    forbidden = ["xtquant", "easytrader", "insert_order", "broker_password"]
    python_text = "\n".join(
        path.read_text(encoding="utf-8") for path in (ROOT / "src").glob("*.py")
    )
    found = [word for word in forbidden if word in python_text.lower()]
    if found:
        errors.append(f"疑似包含真实交易代码：{', '.join(found)}")
    test = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if test.returncode:
        errors.append(f"pytest 失败：\n{test.stdout}\n{test.stderr}")
    if errors:
        print("\n".join(f"[FAIL] {item}" for item in errors))
        return 1
    print("[OK] 必要文件、核心模块、10 股配置、风险声明和离线测试均通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
