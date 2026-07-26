# 项目协作说明

## 目标
构建一个适合高中生学习和展示的 A 股金融数据分析与基础回测平台。

## 结构
- `app.py`：Streamlit 页面与导航
- `src/`：数据、指标、回测、趋势、模拟交易和图表
- `tests/`：不依赖网络的单元测试
- `scripts/`：数据预取与项目验收
- `docs/`：讲解、报告、面试与部署资料

## 命令
- 运行：`streamlit run app.py`
- 测试：`python -m pytest -q`
- 代码检查：`ruff check . && ruff format --check .`
- 验收：`python scripts/verify_project.py`

## 编码规范
公共函数使用类型注解与 docstring；注释解释“为什么”；代码保持简单、可读。

## 安全边界
禁止接入真实券商和真实下单接口。本项目只做历史分析和模拟交易，不提供投资建议。

## 完成条件
核心功能可运行，测试和 Ruff 通过，网页可打开，文档与风险声明完整。
