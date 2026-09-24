# wechat-auto-publish

把写好的 Markdown 文章排版成公众号样式，一键推到微信公众号草稿箱。

## 快速开始（Hello World）

### 方式一：对话式自动生成并发布

复制下面这段，粘贴到豆包新会话里：

```text
开启一个全新的会话，严格执行下面的指令。

# 公众号自动发文 · 执行提示词

1. **文章生成**：严格按内容生成提示词执行
   - 内容生成提示词：https://github.com/baiyigali/opp_radar/blob/main/prompts/dev.md （可换成你自己的）
   - 输出目录：~/articles/wechat/ （可换成你自己的，平铺不建子文件夹）

2. **发布**：严格按发布流水线执行
   - 发布流水线：https://github.com/baiyigali/wechat-auto-publish/blob/main/prompts/pipeline.md
   - appid：（填你自己的公众号App ID）
   - secret：（填你自己的公众号app secret）
   - author：（填你自己的文章作者）

3. **完成后报告**：文章标题、主名、发到哪个账号、草稿 media_id，
   以及输出目录下本次生成的文件清单；遇到错误原样报告。
```

### 方式二：命令行手动发布已有文章

```bash
# 安装
pip install wechat-auto-publish

# 把现成的 .md + 封面推到草稿箱
wechat-auto-publish draft "文章.md" "封面.png" "文章标题" \
  --appid 你的AppID --secret 你的AppSecret --author 作者名
# digest 摘要可省略，微信会自动生成
# 可选渲染样式：--style 科技风 --color 经典（6 风格 × 12 配色，见下方"渲染样式"）
```


## 它做了什么

```
opp-radar          →  生成文章（.md + 封面 .png）
wechat-formatter   →  .md 渲染成公众号内联样式 HTML
wechat-publish     →  HTML + 封面推到公众号草稿箱
```

| 组件 | 仓库 / 包 | 职责 |
|---|---|---|
| 生成 | [opp_radar](https://github.com/baiyigali/opp_radar) | 机会雷达，按领域提示词产出渠道无关的文章 |
| 排版 | [wechat-formatter](https://github.com/baiyigali/wechat-formatter) | Markdown → 公众号内联样式 HTML（6 风格 × 12 配色 = 72 模板） |
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

## 测试

测试套件在 `tests/`，全部为本地逻辑测试（清单解析、渲染、凭据解析、参数校验），**不触网、不调用微信 API**：

```bash
pip install -e . pytest
pytest tests/ -v
```

覆盖范围：

| 模块 | 覆盖内容 |
|---|---|
| `render` | md → 内联样式 HTML 生成、风格/配色参数渲染差异、非法值报错 |
| 样式归一化 | 中文风格名 / 英文 id / 省略"风"字 / 12 配色合法性校验 |
| `_resolve_credentials` | 直传凭据优先级 / 单账号 / 多账号 / `--author` 覆盖 |
| `push_draft` / `push_draft_multi` | 8 篇上限、空清单、缺 `articles` 键、digest 截断、title 默认取文件名、style/color 转发与 manifest 逐篇覆盖 |
| CLI | `draft` / `draft-multi` / `styles` 参数解析、分发与默认值 |

CI 在 GitHub Actions 上跑（`.github/workflows/publish.yml`）：push main / PR 先跑 Python 3.10–3.13 测试矩阵，通过后才构建发布（TestPyPI / 正式 PyPI）。

## 配置

复制 `config.example.json` 为 `config.json`，填入公众号凭据。支持多账号：`default` 指定默认号，`accounts` 下可放多个公众号；发指定号时命令加 `--account <账号名>`。`config.json` 已 gitignore，不进版本库。

## 用法

### 命令行：把一篇已写好的文章推到草稿箱

```bash
wechat-auto-publish draft "文章.md" "封面.png" "标题" [摘要] \
  --style 科技风 --color 经典
```

摘要可省略，微信会自动生成。`--style` / `--color` 可省略，默认 科技风/经典。

### 渲染样式（--style / --color）

排版层基于 [wechat-formatter](https://github.com/baiyigali/wechat-formatter) 的模板体系，**风格名称 + 配色名称**两个参数控制全部 72 个模板：

| 参数 | 可选值 |
|---|---|
| `--style` | 极简风 / 商务风 / 文艺风 / 科技风 / 节庆风 / 新粗野风（中文或英文 id：minimalist / business / literary / tech / festive / neo-brutalism 均可） |
| `--color` | 经典 / 雅致 / 先锋 / 深邃 / 晨光 / 星穹 / 暖阳 / 暮色 / 清泉 / 破晓 / 璀璨 / 幽蓝 |

随时用 `styles` 子命令查看全部可用值：

```bash
wechat-auto-publish styles
```

非法的风格/配色名会直接报错并列出可选项，不会渲染出错误样式。

### 命令行：多图文（一条草稿最多 8 篇）

写一个 JSON 清单 `manifest.json`（每篇可用 `"style"` / `"color"` 覆盖全局样式）：

```json
{
  "articles": [
    {"md": "文章A.md", "cover": "文章A.png", "title": "标题A", "digest": "摘要A（可选，120字内）", "style": "商务风", "color": "暖阳"},
    {"md": "文章B.md", "cover": "文章B.png", "title": "标题B"}
  ]
}
```

然后一条命令推送：

```bash
wechat-auto-publish draft-multi manifest.json \
  --appid 你的AppID --secret 你的AppSecret --author 作者名 \
  --style 科技风 --color 经典
```

- 第一篇为头条封面文章；上限 8 篇；title ≤32 字、digest ≤120 字、author ≤16 字
- 每篇的 `.md` 会先渲染成公众号样式 HTML（`--style`/`--color` 为全局默认，manifest 单篇键可覆盖），无需手动渲染
- `title` 可省略，默认取 md 文件名；凭据参数与 `draft` 完全一致（或走 `config.json`）

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
- 如遇报错，如实报告错误信息。

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
