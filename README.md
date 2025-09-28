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

## 常见问题：如何解决合并冲突？

当在拉取最新代码或合并分支时遇到大量冲突，可按照以下步骤逐一处理：

1. **同步远端分支**：

   ```bash
   git checkout main
   git pull origin main --rebase
   git checkout <feature-branch>
   git rebase main  # 或 git merge main
   ```

   先把 `main` 拉到最新可以大幅降低冲突风险，再将工作分支与最新的 `main` 对齐。若在对齐过程中冲突过多无法继续，可使用 `git rebase --abort` 或 `git merge --abort` 回退并重新规划。

2. **查看冲突文件**：

   ```bash
   git status
   ```

   所有标记为 `both modified` 的文件都需要手动处理。

3. **逐个文件解决冲突**：打开有冲突的文件，定位 `<<<<<<<`、`=======`、`>>>>>>>` 标记，保留正确代码并删除标记。若不确定哪段逻辑有效，可参考提交历史或运行测试验证。

4. **标记为已解决并继续流程**：

   ```bash
   git add <file1> <file2> ...
   ```

   对于 rebase 流程执行 `git rebase --continue`，若是 merge 则可直接 `git commit`。

5. **确认结果并运行测试**：完成所有冲突处理后，再次执行 `git status` 确保干净，然后运行项目测试或关键脚本确认行为正常。

通过以上步骤即可系统性地解决冲突，避免遗漏或引入新的问题。
