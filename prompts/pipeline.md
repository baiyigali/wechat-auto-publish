# 文章发布到公众号

把一篇写好的文章渲染成公众号样式，推到草稿箱。

## 步骤

### 1. 安装

```bash
pip install wechat-auto-publish
# 或 git clone https://github.com/baiyigali/wechat-auto-publish.git && cd wechat-auto-publish && pip install -e .
```

### 2. 准备输入文件

你需要两个文件：

- **文章 Markdown**：`文章.md`
- **封面 PNG**：`封面.png`

外加两个凭据：`appid`、`secret`；作者名 `author` 可选。

### 3. 运行

先读 `.md` 第一行 H1，只去掉行首的 `# `，其余原样作为文章标题（不要删任何后缀或系列名）。

然后运行：

```bash
wechat-auto-publish draft "文章.md" "封面.png" "文章标题" \
  --appid 你的AppID --secret 你的AppSecret --author 作者名
```

- 摘要可选，不传微信会自动生成；
- 常见错误 `40164` = 出口 IP 未加白，如实报告。

## 交付

报告：文章标题、草稿 media_id / 错误信息。提醒用户去公众号后台草稿箱点"发表"。
