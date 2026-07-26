"""通过 AKShare 获取并清洗 A 股公开行情，失败时使用本地缓存。"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.config import CACHE_DIR, STOCKS

HISTORY_COLUMNS = {
    "日期": "date",
    "股票代码": "symbol",
    "开盘": "open",
    "收盘": "close",
    "最高": "high",
    "最低": "low",
    "成交量": "volume",
    "成交额": "amount",
    "换手率": "turnover_rate",
    "turnover": "turnover_rate",
}
NUMERIC_COLUMNS = ["open", "close", "high", "low", "volume", "amount", "turnover_rate"]


def clean_history(raw: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """统一 AKShare 历史行情字段并清除无效、重复和乱序记录。"""
    if raw is None or raw.empty:
        raise ValueError(f"{symbol} 未返回历史数据。")
    data = raw.rename(columns=HISTORY_COLUMNS).copy()
    required = {"date", "open", "close", "high", "low", "volume"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"{symbol} 缺少字段：{', '.join(sorted(missing))}")
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data["symbol"] = symbol
    for column in NUMERIC_COLUMNS:
        if column in data:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna(subset=["date", "open", "close", "high", "low"])
    return data.drop_duplicates("date").sort_values("date").reset_index(drop=True)


def cache_path(symbol: str, cache_dir: Path = CACHE_DIR) -> Path:
    """返回单只股票的缓存路径。"""
    return cache_dir / f"{symbol}.csv"


def read_cache(symbol: str, cache_dir: Path = CACHE_DIR) -> pd.DataFrame:
    """读取本地 CSV；损坏或为空时给出明确错误。"""
    path = cache_path(symbol, cache_dir)
    if not path.exists():
        raise FileNotFoundError(f"没有 {symbol} 的本地缓存。")
    try:
        raw = pd.read_csv(path)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as error:
        raise ValueError(f"{symbol} 缓存文件损坏：{error}") from error
    return clean_history(raw, symbol)


def fetch_history(
    symbol: str,
    start_date: str = "20160101",
    end_date: str | None = None,
    adjust: str = "qfq",
    cache_dir: Path = CACHE_DIR,
) -> tuple[pd.DataFrame, str]:
    """先在线获取历史行情，失败时读取本地缓存；绝不生成假数据。"""
    if symbol not in STOCKS:
        raise ValueError(f"股票代码不在教学股票池：{symbol}")
    end_date = end_date or datetime.now(timezone.utc).strftime("%Y%m%d")
    online_errors: list[str] = []
    try:
        import akshare as ak

        raw = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust=adjust,
        )
        data = clean_history(raw, symbol)
        cache_dir.mkdir(parents=True, exist_ok=True)
        data.to_csv(cache_path(symbol, cache_dir), index=False)
        return data, "在线 AKShare（东方财富）"
    except (ImportError, OSError, RuntimeError, ValueError, KeyError) as error:
        online_errors.append(f"东方财富：{error}")
    try:
        import akshare as ak

        exchange_prefix = "sh" if symbol.startswith("6") else "sz"
        raw = ak.stock_zh_a_daily(
            symbol=f"{exchange_prefix}{symbol}",
            start_date=start_date,
            end_date=end_date,
            adjust=adjust,
        )
        data = clean_history(raw, symbol)
        cache_dir.mkdir(parents=True, exist_ok=True)
        data.to_csv(cache_path(symbol, cache_dir), index=False)
        return data, "在线 AKShare（新浪财经回退）"
    except (ImportError, OSError, RuntimeError, ValueError, KeyError) as error:
        online_errors.append(f"新浪财经：{error}")
    try:
        return read_cache(symbol, cache_dir), "本地缓存"
    except (FileNotFoundError, ValueError) as cache_error:
        raise RuntimeError(
            f"{symbol} 在线获取失败（{'；'.join(online_errors)}），"
            f"本地缓存也不可用（{cache_error}）。"
        ) from cache_error


def fetch_spot(
    symbols: list[str] | None = None,
) -> tuple[pd.DataFrame, datetime, str]:
    """获取股票池的市场快照。数据可能延迟，不等同于交易所实时行情。"""
    import akshare as ak

    symbols = symbols or list(STOCKS)
    try:
        raw = ak.stock_zh_a_spot_em()
        source = "AKShare（东方财富）"
        renamed = raw.rename(
            columns={
                "代码": "symbol",
                "名称": "name",
                "最新价": "latest",
                "涨跌额": "change",
                "涨跌幅": "change_pct",
                "成交量": "volume",
            }
        )
    except (OSError, RuntimeError, ValueError, KeyError):
        raw = ak.stock_zh_a_spot_tx()
        source = "AKShare（腾讯行情回退）"
        renamed = raw.rename(
            columns={
                "code": "symbol",
                "zxj": "latest",
                "zd": "change",
                "zdf": "change_pct",
            }
        )
    if raw is None or raw.empty:
        raise ValueError("最新行情接口返回空数据。")
    needed = ["symbol", "name", "latest", "change", "change_pct", "volume"]
    missing = set(needed) - set(renamed.columns)
    if missing:
        raise ValueError(f"最新行情缺少字段：{', '.join(sorted(missing))}")
    result = renamed[needed].copy()
    result["symbol"] = (
        result["symbol"]
        .astype(str)
        .str.removeprefix("sh")
        .str.removeprefix("sz")
        .str.zfill(6)
    )
    fetched_at = datetime.now(timezone.utc).astimezone()
    filtered = result[result["symbol"].isin(symbols)].reset_index(drop=True)
    return filtered, fetched_at, source


def load_stock_pool() -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    """逐只加载股票，单只失败不会影响其他股票。"""
    loaded: dict[str, pd.DataFrame] = {}
    errors: dict[str, str] = {}
    for symbol in STOCKS:
        try:
            loaded[symbol] = fetch_history(symbol)[0]
        except (RuntimeError, ValueError) as error:
            errors[symbol] = str(error)
    return loaded, errors
