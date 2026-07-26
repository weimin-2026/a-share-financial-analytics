"""项目常量：股票池、字段名和免责声明。"""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT_DIR / "data" / "cache"

STOCKS = {
    "000001": "平安银行",
    "000333": "美的集团",
    "000651": "格力电器",
    "000858": "五粮液",
    "600030": "中信证券",
    "600036": "招商银行",
    "600276": "恒瑞医药",
    "600519": "贵州茅台",
    "600900": "长江电力",
    "601318": "中国平安",
}

DISCLAIMER_ZH = "本项目仅用于金融数据学习与申请展示，不构成投资建议。"
DISCLAIMERS_EN = (
    "Historical performance does not guarantee future returns. "
    "The trading module is a paper-trading simulation only. "
    "The trend model is an educational reference rather than an investment forecast."
)
