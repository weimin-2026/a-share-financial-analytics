"""一次性下载十只教学股票的历史行情到本地缓存。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import STOCKS
from src.data import fetch_history


def main() -> int:
    """逐只下载，最后用退出码表示是否全部成功。"""
    failures = 0
    for symbol, name in STOCKS.items():
        try:
            data, source = fetch_history(symbol)
            print(f"[OK] {symbol} {name}: {len(data)} rows ({source})")
        except (RuntimeError, ValueError) as error:
            failures += 1
            print(f"[FAIL] {symbol} {name}: {error}")
    print(f"完成：成功 {len(STOCKS) - failures}，失败 {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
