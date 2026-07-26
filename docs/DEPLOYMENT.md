# 部署说明

## 本地确认

```bash
pip install -r requirements.txt
python -m pytest -q
ruff check .
python scripts/verify_project.py
streamlit run app.py
```

确认首页和七个导航页可打开；没有 `.env`、Token 或 `secrets.toml`；根目录存在 `app.py` 和 `requirements.txt`。

## Streamlit Community Cloud

1. 登录 Streamlit Community Cloud，并使用 GitHub 授权。
2. 选择本项目仓库和 `main` 分支。
3. Main file path 填 `app.py`。
4. 部署后查看日志；如依赖安装失败，按日志修正版本。
5. 实际打开公网 URL，检查数据错误提示、指标、回测、趋势、模拟交易和免责声明。
6. 验证成功后再把真实 URL 写入 README。

AKShare 通常不需要 API Key。平台休眠、公开数据接口变化或网络限制可能导致首次加载较慢或数据暂不可用。
