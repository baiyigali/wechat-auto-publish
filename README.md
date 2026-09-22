# wechat-auto-publish

公众号自动发布的**最外层流水线**。它自己不生成内容，只把三个上游组件串成一条命令：

```
opp-radar          →  生成文章（.md + 封面 .png）
wechat-formatter   →  .md 渲染成公众号内联样式 HTML
wechat-publish     →  HTML + 封面推到公众号草稿箱
```

| 组件 | 仓库 / 包 | 职责 |
|---|---|---|
| 生成 | [opp_radar](https://github.com/baiyigali/opp_radar) | 机会雷达，按领域提示词产出渠道无关的文章 |
| 排版 | [wechat-formatter](https://github.com/baiyigali/wechat-formatter) | Markdown → 科技风经典蓝 HTML |
| 发布 | [wechat-publish](https://github.com/baiyigali/wechat-publish) | 草稿箱接口，图片自动转存微信 CDN |

换领域、换排版主题、换发布渠道时，只在这一层换组件，不改上游。

## 安装

```bash
pip install -e .
# 或 pip install wechat-auto-publish
```

依赖三个上游包（见 `pyproject.toml`）。

## 配置

复制 `config.example.json` 为 `config.json`，填入公众号 appid / secret / author。`config.json` 已 gitignore，不进版本库。

## 用法

### 命令行：把一篇已写好的文章推到草稿箱

```bash
wechat-auto-publish draft "文章.md" "封面.png" "标题" "120字内摘要"
```

这条命令只跑一次，绝不重试，避免重复建草稿。

### 编排：生成 + 发布一条龙

给 AI agent 说："按 `prompts/pipeline.md` 跑一期"。它会先读 opp-radar 里对应领域的提示词生成文章，再调用本仓库把文章推到草稿箱。

## 目录

```
wechat-auto-publish/
  prompts/pipeline.md          # 最外层编排提示词
  wechat_auto_publish/         # 包：render + push
  config.example.json
  pyproject.toml
```

## 说明

- 只存草稿，不群发。个人未认证号无 `freepublish/submit` 权限，发表动作在公众号后台手动点。
- 发布命令只执行一次：微信接口可能"已成功但返回像失败"，重试会重复建草稿。
