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

二选一：

**A. 从 PyPI 安装**（已发布后）：
```bash
pip install wechat-auto-publish
```

**B. 本地 clone 后安装**（开发或未发布时）：
```bash
git clone https://github.com/baiyigali/wechat-auto-publish.git
cd wechat-auto-publish
pip install -e .
```

依赖三个上游包（见 `pyproject.toml`）。

## 配置

复制 `config.example.json` 为 `config.json`，填入公众号凭据。支持多账号：`default` 指定默认号，`accounts` 下可放多个公众号；发指定号时命令加 `--account <账号名>`。`config.json` 已 gitignore，不进版本库。

## 用法

### 命令行：把一篇已写好的文章推到草稿箱

```bash
wechat-auto-publish draft "文章.md" "封面.png" "标题" "120字内摘要"
```

这条命令只跑一次，绝不重试，避免重复建草稿。

### 编排：生成 + 发布一条龙

给 AI agent 说："按 `prompts/pipeline.md` 跑一期"。它会先读"生成"那一环的领域提示词产出文章，再调用本仓库推到草稿箱。生成环节以 [opp-radar](https://github.com/baiyigali/opp_radar)（机会雷达）为例，可换成任意自己的生成流程。

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

## CI / 自动发布

仓库自带 GitHub Actions（`.github/workflows/publish.yml`），与常见开源 Python 包一致：

- **push 到 `main`** → 编译 sdist + wheel，自动发布到 **TestPyPI**（官方测试源，验证打包流程不污染正式版）；
- **打 tag `v*`**（如 `v0.1.0`）→ 编译后发布到**正式 PyPI**；
- 也支持在 Actions 页面手动触发（`workflow_dispatch`），只编译不发布。

免密推送：在 PyPI / TestPyPI 后台把本仓库配置为 **Trusted Publisher（OIDC）**，workflow 里 `id-token: write` 自动换取临时凭据，不需要任何 `PYPI_API_TOKEN`。

## 相关项目

- [opp_radar](https://github.com/baiyigali/opp_radar)：机会雷达，按领域提示词自动生成文章内容
- [wechat-formatter](https://github.com/baiyigali/wechat-formatter)：Markdown → 公众号内联样式 HTML（科技风/经典蓝）
- [wechat-publish](https://github.com/baiyigali/wechat-publish)：公众号草稿箱/群发接口，图片自动转存微信 CDN
- [legal_prompts](https://github.com/baiyigali/legal_prompts)：法律领域提示词合集
- [gov-site-list](https://github.com/baiyigali/gov-site-list)：中国政府网站 URL 清单（中央 + 省级 + 部委）
- [gov-monitor](https://github.com/baiyigali/gov-monitor)：政府网站通知监测工具，自动发现新政策并落库

## 技术交流

扫码添加微信，交流使用问题、定制与合作：

<p align="center">
  <img src="docs/images/wechat-contact-qr.jpg" alt="微信二维码" width="240" />
</p>

## 项目赞助

本项目由以下微信公众号提供赞助，感谢支持：

**「程序员白大力」** —— 法律科技 / 自动化内容创作

<p align="center">
  <img src="docs/images/wechat-official-account-qr.png" alt="程序员白大力公众号二维码" width="240" />
</p>

**「法啊」** —— 法律科普 / 普法内容

<p align="center">
  <img src="docs/images/fa-official-account-qr.png" alt="法啊公众号二维码" width="240" />
</p>

**「极速法考」** —— 法考备考 / 法律职业资格考试

<p align="center">
  <img src="docs/images/jisu-fakao-official-account-qr.png" alt="极速法考公众号二维码" width="240" />
</p>

## License

MIT
