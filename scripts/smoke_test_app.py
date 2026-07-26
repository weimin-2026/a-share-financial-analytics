"""用 Streamlit 官方测试接口运行七个导航页面。"""

from __future__ import annotations

import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    """逐页运行应用；发现未处理异常时返回非零退出码。"""
    app = AppTest.from_file(ROOT / "app.py").run(timeout=120)
    options = list(app.sidebar.radio[0].options)
    failures = 0
    for option in options:
        app.sidebar.radio[0].set_value(option)
        app.run(timeout=120)
        page_errors = len(app.exception)
        failures += page_errors
        print(
            f"[{'OK' if page_errors == 0 else 'FAIL'}] {option}: {page_errors} exceptions"
        )
    print(f"完成：{len(options)} 个页面，未处理异常 {failures} 个。")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
