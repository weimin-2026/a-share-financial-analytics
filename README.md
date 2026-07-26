# A 股金融数据分析与基础回测平台

一个适合高中生学习、大学申请和面试展示的 Streamlit 项目。它把公开 A 股行情的数据获取、清洗、可视化、MA/RSI 指标、基础回测、线性趋势参考和模拟交易放在一个可解释的应用中。

> 本项目仅用于金融数据学习与申请展示，不构成投资建议。

Historical performance does not guarantee future returns. The trading module is a paper-trading simulation only. The trend model is an educational reference rather than an investment forecast.

## 核心功能

- 10 只 A 股的最新公开行情快照与历史行情
- 首日收盘价归一化为 100 的横向比较
- K 线、成交量、短期/长期 MA 和 RSI
- MA 交叉单股/批量回测，与买入并持有比较
- 累计收益、年化收益、最大回撤、交易次数和明细
- 时间顺序切分的线性回归趋势参考与 MAE
- 基于 `st.session_state` 的会话内模拟交易
- 多处 CSV 下载和网络失败提示

## 技术栈

Python、Streamlit、pandas、NumPy、Plotly、AKShare、scikit-learn、pytest、Ruff。

## 项目结构

```text
app.py                 页面和导航
src/                   数据与核心计算
tests/                 固定离线数据测试
scripts/               数据预取和验收
docs/                  讲解、报告、面试与部署文档
data/cache/            本地历史行情缓存
```

## 安装与运行

推荐 Python 3.12：

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/prefetch_data.py
python -m pytest -q
ruff check .
ruff format --check .
python scripts/verify_project.py
streamlit run app.py
```

预取脚本需要网络；测试不需要网络。网页请求失败时会尝试本地缓存，两者都不可用则明确报错，不会伪造价格。

## 数据与延迟

历史日线和最新行情快照由 AKShare 聚合的第三方公开数据提供。历史价格默认使用前复权 `qfq`，日期升序、去重并转为统一英文列名。最新行情可能延迟，不等同于交易所实时行情；未完成的当日快照不会加入历史回测。

## MA、RSI 与回测规则

MA 是给定窗口内收盘价的简单平均值。RSI 根据上涨和下跌幅度计算并限制在 0–100；30/70 只是常见教学参考。策略在短期 MA 上穿长期 MA 时产生买入信号，下穿时产生卖出信号，只做多、不融资融券。每次默认使用可用现金的 50%，买入数量向下取整到 100 股，卖出时全部卖出，买卖均计简化手续费。

为避免前视偏差，第 t 日收盘后确认的信号只能在第 t+1 个交易日开盘执行。如果当日开盘价缺失，该日不执行。页面同时绘制策略与买入并持有的资产曲线。

## 趋势参考与模拟交易

趋势模块用交易日序号作为唯一特征，按时间顺序切分 80% 训练集与 20% 测试集，不随机打乱。MAE 表示测试价格与线性趋势预测之间的平均绝对误差。它只用于解释最简单的机器学习流程。

模拟账户只保存在当前 Streamlit 会话，不注册用户、不存密码、不连接券商。所谓“自动”只是在用户点击按钮后生成一条模拟记录。

## 测试与部署

`pytest` 覆盖指标、交叉信号、延迟成交、资金/持仓约束、整手数量、手续费、最大回撤、时间切分、MAE 和信号去重。部署到 Streamlit Community Cloud 时选择仓库、`main` 分支和根目录 `app.py`，无需 API Key。详见 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)。

## 局限

本项目未完整模拟滑点、涨跌停、停牌、分红、税费、流动性和退市偏差。股票池是固定教学样本，策略没有证明能在未来盈利。线性回归无法表达复杂市场变化，历史表现也不能代表未来。

## AI 使用说明

本项目使用 AI 辅助生成代码建议、检查和调试。学生应亲自理解、运行并能修改核心代码，不应把 AI 辅助内容描述为完全独立完成。详见 [docs/AI_USAGE_DISCLOSURE.md](docs/AI_USAGE_DISCLOSURE.md)。

## 在线网站

尚未部署；只有公网 URL 实际打开并验证后才会在此填写真实链接。
