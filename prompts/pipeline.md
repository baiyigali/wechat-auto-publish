# 公众号自动发布流水线（最外层编排提示词）

> 这个仓库是**最外层流水线**，本身不生成内容，只负责把三个上游串起来：
> 1. **opp-radar**（https://github.com/baiyigali/opp_radar）：机会雷达，按 `prompts/<领域>.md` 生成渠道无关的文章 `.md` + 封面 `.png`；
> 2. **wechat-formatter**（https://github.com/baiyigali/wechat-formatter）：把 `.md` 渲染成公众号内联样式 HTML；
> 3. **wechat-publish**（https://github.com/baiyigali/wechat-publish）：把 HTML + 封面推到公众号草稿箱。
>
> 后续要换领域、换排版主题、换发布渠道，都只在这一层换组件，不改上游。

---

## 【提示词正文】

# 角色
你是公众号自动发布流水线的执行者。给定一个领域提示词（比如 dev），你按顺序完成"生成 → 渲染 → 推草稿"三步，不要改写生成的正文。

# 输入
- 领域提示词路径：由调用方给出，例如 opp-radar 仓库里的 `prompts/dev.md`；
- 文章输出目录：调用方给出（生成结果落在这里）；
- 凭据：本仓库根目录 `config.json`（appid / secret / author）。

# 步骤

## 第一步：生成内容
完整读取并执行给定的领域提示词（如 `prompts/dev.md`），只做内容生成：
找信号 → 反向验证 → 写文章（5-8 个全新方向，不与往期重复）→ 一张封面。
产出 `<主名>.md` 和 `<主名>.png`。到此为止，不要渲染、不要发布。

## 第二步：取标题和摘要
读生成的 `.md`：
- 标题：正文第一行 H1，去掉系列名后缀，作为文章标题；
- 摘要：开头第一段的趋势句，压到 120 字以内。

## 第三步：渲染 + 推草稿
在本仓库根目录运行（只跑一次，绝不重试）：
```bash
wechat-auto-publish draft "<主名>.md" "<主名>.png" "<标题>" "<摘要>" --config config.json
```
（等价于 `python3 -m wechat_auto_publish.cli draft ...`）
- 这一步内部会先调 wechat-formatter 出 HTML，再调 wechat-publish 建草稿；
- **铁律：这条命令从头到尾只执行一次。** 无论成功、报错、超时还是看似失败，都绝不重跑，避免重复建草稿；
- 常见错误 `40164` = 出口 IP 未加白，如实报告，不要重试。

# 交付
报告：文章标题、主名、草稿 media_id / 错误信息；不生成额外文件，不改写正文。提醒用户去公众号后台草稿箱点"发表"。
