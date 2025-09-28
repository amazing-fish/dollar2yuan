# dollar2yuan
## 美元兑人民币汇率查看工具
### 特点
- 使用api获取汇率数据
- 直接查找近x天的历史
- 使用echarts和tkinter可视化
### 展示:
- 近十年每月的汇率折线图

![echarts](https://github.com/amazing-fish/dollar2yuan/assets/71763696/464fbc31-24d7-4bba-9122-b0b00fe96327)

## 凭证配置方式

在启动桌面应用前，需要先准备好 [Alpha Vantage](https://www.alphavantage.co/documentation/#fx-daily) 提供的 `API Key`：

1. **环境变量方式**（推荐）：

   ```bash
   export ALPHAVANTAGE_API_KEY="你的apikey"
   python main.py
   ```

2. **`.env` 文件方式**：在项目根目录创建 `.env`（或复制 `.env.example`）并填入内容，程序启动时会自动读取：

   ```env
   ALPHAVANTAGE_API_KEY=你的apikey
   # 可选：调整请求窗口大小（compact/full）
   # ALPHAVANTAGE_OUTPUTSIZE=compact
   ```

   若需在其他环境中复用，也可以搭配 `python-dotenv` 等工具在运行前自动加载。

3. **界面手动输入**：运行程序后，可直接在界面顶部的输入框中填写 `API Key`，并按需选择 `Output Size`（`compact` 为最新 100 个交易日，`full` 为全部历史）。点击“查询”按钮即可保存于当前会话。

Alpha Vantage 免费额度为 **每分钟 5 次请求、每天 500 次请求**。若超过额度，API 会返回 `Note` 提示，需要等待额度刷新后再试。

若凭证未配置或输入，程序会提示用户补全信息。

5. **确认结果并运行测试**：完成所有冲突处理后，再次执行 `git status` 确保干净，然后运行项目测试或关键脚本确认行为正常。

通过以上步骤即可系统性地解决冲突，避免遗漏或引入新的问题。
