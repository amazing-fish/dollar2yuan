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

在启动桌面应用前，需要先准备好 [nowapi](https://www.nowapi.com/api/finance.rate_history) 提供的 `appkey` 与 `sign`：

1. **环境变量方式**（推荐）：

   ```bash
   export NOWAPI_APPKEY="你的appkey"
   export NOWAPI_SIGN="你的sign"
   python main.py
   ```

2. **`.env` 文件方式**：在项目根目录创建 `.env`（或复制 `.env.example`）并填入内容，程序启动时会自动读取：

   ```env
   NOWAPI_APPKEY=你的appkey
   NOWAPI_SIGN=你的sign
   ```

   若需在其他环境中复用，也可以搭配 `python-dotenv` 等工具在运行前自动加载。

3. **界面手动输入**：运行程序后，可直接在界面顶部的输入框中填写 `AppKey` 与 `Sign`，点击“查询”按钮即可保存于当前会话。

若凭证未配置或输入，程序会提示用户补全信息。
