# dollar2yuan

基于 Alpha Vantage 汇率接口构建的现代化桌面工具，聚焦「美元兑人民币」行情的查询、分析与可视化。应用以 Tkinter 打造主界面，并通过内嵌 ECharts 的浏览器视图呈现交互式走势图，兼顾易用性与可扩展性。

![桌面端界面示意](https://github.com/amazing-fish/dollar2yuan/assets/71763696/464fbc31-24d7-4bba-9122-b0b00fe96327)

## 核心功能

- **一键拉取最新行情**：调用 Alpha Vantage `FX_DAILY` 接口获取 USD/CNY 日线数据，支持 `compact`（近 100 个交易日）与 `full`（完整历史）两种模式。
- **本地快照缓存**：将数据以 JSON 存放于 `data/usd_cny_base.json`，离线也能回看上一次成功同步的行情。
- **桌面级可视化体验**：嵌入式 ECharts 图表提供多序列折线、振幅曲线、范围缩放与图像导出等能力。
- **智能指标摘要**：界面右侧自动计算最新收盘价、当日区间、振幅与数据覆盖天数，方便快速洞察。
- **灵活配置凭证**：支持环境变量、`.env` 文件或界面输入三种方式配置 API Key，并允许自定义抓取天数。

## 项目进展速览

- ✅ Tkinter 主界面与 ECharts 可视化联动已经落地。
- ✅ 实现基础数据仓储（JSON 缓存）、异常处理与错误提示。
- ✅ 支持从 `.env`、环境变量与 UI 输入多渠道加载配置。
- 🔄 计划中的增强项包含多货币支持、自动刷新与更多导出能力。

## 快速上手

### 1. 环境准备

- Python 3.10+（macOS 自带的 Tk 版本过旧时，建议安装新版 Python）
- 依赖：`requests`、`pywebview`、`python-dotenv`（可选，用于加载 `.env`）

```bash
pip install requests pywebview python-dotenv
```

> Windows 用户需提前安装 [WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) 以确保嵌入式浏览器正常工作。

### 2. 凭证配置

申请 [Alpha Vantage](https://www.alphavantage.co/documentation/#fx-daily) 的免费 API Key，并在运行前选择以下任意方式设置：

| 方式 | 操作示例 |
| --- | --- |
| 环境变量（推荐） | `export ALPHAVANTAGE_API_KEY="你的apikey"`
| `.env` 文件 | 复制 `.env.example` 为 `.env` 并填入 `ALPHAVANTAGE_API_KEY`
| 界面输入 | 启动应用后直接在界面顶部的输入框填写 |

如需调整输出规模，可将 `ALPHAVANTAGE_OUTPUTSIZE` 设置为 `full` 以获取完整历史。

Alpha Vantage 免费额度为 **每分钟 5 次请求**、**每天 500 次请求**。触发限流后会返回 `Note`，需等待额度刷新。

### 3. 启动应用

```bash
python main.py
```

首次进入界面时会自动加载 `data/usd_cny_base.json` 中的快照数据。点击“刷新基础数据”可在提供有效 API Key 后同步最新行情，并自动写回缓存。

## 项目结构

```
dollar2yuan/
├── app/
│   ├── config.py              # 全局配置、路径解析、.env 默认值
│   ├── main.py                # 应用工厂与入口
│   ├── models/                # 汇率实体与转换工具
│   ├── repository/            # JSON 仓储实现
│   ├── services/              # Alpha Vantage 客户端与业务逻辑
│   └── ui/                    # Tkinter + ECharts 界面
├── data/usd_cny_base.json     # 默认缓存数据
├── main.py                    # 启动脚本（调用 app.main.main）
└── README.md
```

## 开发提示

- 建议在本地创建虚拟环境管理依赖，例如 `python -m venv .venv && source .venv/bin/activate`。
- 如果需要调试 `.env`，可在根目录执行 `cp .env.example .env` 并填充键值。
- 运行 `python -m app.ui.webview` 可在交互式环境下快速验证图表渲染。

## 后续规划（精炼待办）

1. 支持多货币对切换与自定义收藏列表。
2. 引入后台定时刷新与桌面提醒，及时感知汇率波动。
3. 增加数据导出（CSV、PNG）与共享功能。
4. 在界面内提供技术指标模块（均线、MACD 等）。
5. 针对异常网络或 API 状态提供更详细的诊断信息页。
6. 引入自动化测试与 CI 流程，保障核心流程稳定性。
