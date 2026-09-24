"""把一篇已写好的文章分发到微信公众号草稿箱。

这一层不生成内容，只做两步：
  1. 用 wechat-formatter 把 .md 渲染成公众号 HTML（样式由 style/color 决定，默认 科技风/经典蓝）；
  2. 用 wechat-publish 把 HTML + 封面推到草稿箱（只存草稿，不群发）。
"""
from __future__ import annotations

import json
import os

# wechat-formatter 支持的 6 种风格（中文名 / 英文 id 均可作 style 参数）
STYLE_CATEGORIES: dict[str, str] = {
    "minimalist": "极简风",
    "business": "商务风",
    "literary": "文艺风",
    "tech": "科技风",
    "festive": "节庆风",
    "neo-brutalism": "新粗野风",
}

# 12 种配色名（每种风格 × 每种配色 = 一个模板，共 72 个）
COLOR_NAMES: list[str] = [
    "经典", "雅致", "先锋", "深邃", "晨光", "星穹",
    "暖阳", "暮色", "清泉", "破晓", "璀璨", "幽蓝",
]

DEFAULT_STYLE = "科技风"
DEFAULT_COLOR = "经典"


def list_styles() -> dict[str, list[str]]:
    """返回 {风格中文名: 可用配色列表}，供 CLI 的 styles 子命令展示。"""
    return {zh: list(COLOR_NAMES) for zh in STYLE_CATEGORIES.values()}


def _normalize_style(style: str) -> str:
    """把风格参数（中文或英文 id）归一成中文名，非法值直接报错。"""
    style = (style or "").strip()
    # 英文 id（大小写不敏感）→ 中文名
    if style.lower() in STYLE_CATEGORIES:
        return STYLE_CATEGORIES[style.lower()]
    # 中文名（允许带"风"字或不带）
    for zh in STYLE_CATEGORIES.values():
        if style == zh or style == zh.rstrip("风"):
            return zh
    valid = "、".join(STYLE_CATEGORIES.values())
    raise ValueError(f"未知风格 '{style}'，可选：{valid}（或英文 id：{', '.join(STYLE_CATEGORIES)}）")


def _normalize_color(color: str) -> str:
    color = (color or "").strip()
    if color not in COLOR_NAMES:
        raise ValueError(f"未知配色 '{color}'，可选：{'、'.join(COLOR_NAMES)}")
    return color


def render(md_path: str, html_path: str, style: str = DEFAULT_STYLE, color: str = DEFAULT_COLOR) -> str:
    """调用 wechat-formatter，把 md 渲染成内联样式 HTML。

    style: 风格名，中文（如"科技风"）或英文 id（如"tech"）均可；
    color: 配色名，12 选 1，默认"经典"。
    """
    with open(md_path, "r", encoding="utf-8") as f:
        md = f.read()

    from wechat_formatter import FormatTweaks, get_template, render_article

    zh_style = _normalize_style(style)
    zh_color = _normalize_color(color)
    template = get_template(zh_style, zh_color)
    tweaks = FormatTweaks(fontSize=17, lineHeight=1.8, paragraphSpacing=18, imageRadius=6)
    body = render_article(md, template, tweaks)

    title = os.path.splitext(os.path.basename(md_path))[0]
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  body {{ margin:0; background:#f2f3f5; padding:24px 0; }}
  .wechat-article {{ max-width:677px; margin:0 auto; background:#fff;
                     padding:24px 16px; box-sizing:border-box; }}
</style>
</head>
<body>
<div class="wechat-article">
{body}
</div>
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    return html_path


def _resolve_account(cfg: dict, account: str | None) -> dict:
    """从 config 里取一个账号的凭据。

    支持两种结构：
    - 多账号：{"default": "程序员白大力", "accounts": {"程序员白大力": {...}, ...}}
    - 单账号（向后兼容）：{"appid": ..., "secret": ..., "author": ...}
    """
    if "accounts" in cfg:
        name = account or cfg.get("default")
        if name not in cfg["accounts"]:
            raise KeyError(
                f"账号 '{name}' 不在 config 的 accounts 里；"
                f"可选：{list(cfg['accounts'])}"
            )
        return cfg["accounts"][name]
    # 旧的单账号扁平结构
    return cfg


def _resolve_credentials(
    config_path: str = "config.json",
    account: str | None = None,
    appid: str | None = None,
    secret: str | None = None,
    author: str | None = None,
) -> dict:
    """凭据来源优先级：直接传入的 appid/secret/author > config 文件里指定账号。"""
    if appid and secret:
        return {"appid": appid, "secret": secret, "author": author or ""}
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    cred = _resolve_account(cfg, account)
    if author:
        cred["author"] = author
    return cred


def push_draft(
    md_path: str,
    cover_path: str,
    title: str,
    digest: str,
    config_path: str = "config.json",
    account: str | None = None,
    appid: str | None = None,
    secret: str | None = None,
    author: str | None = None,
    style: str = DEFAULT_STYLE,
    color: str = DEFAULT_COLOR,
) -> str | None:
    """渲染 + 推草稿。

    凭据来源优先级：直接传入的 appid/secret/author > config 文件里指定账号。
    style/color：渲染样式，见 render()。
    """
    # 摘要超长就截到 120 字，不报错
    if digest:
        digest = digest.strip()[:120]

    html_path = os.path.splitext(md_path)[0] + ".html"
    render(md_path, html_path, style=style, color=color)

    cred = _resolve_credentials(config_path, account, appid, secret, author)

    from wechat_publish import WeChatAPIError, push_articles

    try:
        media_id = push_articles(
            appid=cred["appid"],
            secret=cred["secret"],
            articles=[{
                "html_path": html_path,
                "title": title,
                "cover_path": cover_path,
                "digest": digest,
            }],
            author=cred["author"],
            open_comment=False,
            publish_now=False,  # 个人未认证号无 freepublish 发布权限，发表由人工完成
        )
        print("DRAFT_MEDIA_ID:", media_id)
        return media_id
    except WeChatAPIError as e:
        print("WECHAT_ERROR:", e)
        return None


MAX_ARTICLES = 8


def push_draft_multi(
    manifest_path: str,
    config_path: str = "config.json",
    account: str | None = None,
    appid: str | None = None,
    secret: str | None = None,
    author: str | None = None,
    style: str = DEFAULT_STYLE,
    color: str = DEFAULT_COLOR,
) -> str | None:
    """多图文：把 manifest 里的多篇文章渲染后合成一个草稿推送。

    manifest 为 JSON 文件，结构：
    {
      "articles": [
        {"md": "a.md", "cover": "a.png", "title": "标题A", "digest": "可选，120字内"},
        {"md": "b.md", "cover": "b.png", "title": "标题B", "style": "极简风", "color": "暖阳"}
      ]
    }
    第一篇为头条封面文章；上限 8 篇。
    样式：命令行/函数参数的 style/color 作为整体默认值，
    单篇文章可用 manifest 里的 "style"/"color" 键覆盖。
    凭据来源优先级与 push_draft 相同。
    """
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    articles_spec = manifest.get("articles")
    if not isinstance(articles_spec, list) or not articles_spec:
        raise ValueError("manifest 里必须有非空的 'articles' 数组")
    if len(articles_spec) > MAX_ARTICLES:
        raise ValueError(f"一条草稿最多 {MAX_ARTICLES} 篇，收到 {len(articles_spec)} 篇")

    articles = []
    for i, art in enumerate(articles_spec):
        md_path = art["md"]
        title = art.get("title") or os.path.splitext(os.path.basename(md_path))[0]
        digest = (art.get("digest") or "").strip()[:120]
        html_path = art.get("html_path") or os.path.splitext(md_path)[0] + ".html"
        render(md_path, html_path,
               style=art.get("style", style), color=art.get("color", color))
        articles.append({
            "html_path": html_path,
            "title": title,
            "cover_path": art["cover"],
            "digest": digest,
        })
        print(f"rendered {i + 1}/{len(articles)}: {title}")

    cred = _resolve_credentials(config_path, account, appid, secret, author)

    from wechat_publish import WeChatAPIError, push_articles

    try:
        media_id = push_articles(
            appid=cred["appid"],
            secret=cred["secret"],
            articles=articles,
            author=cred["author"],
            open_comment=False,
            publish_now=False,  # 个人未认证号无 freepublish 发布权限，发表由人工完成
        )
        print("DRAFT_MEDIA_ID:", media_id)
        return media_id
    except WeChatAPIError as e:
        print("WECHAT_ERROR:", e)
        return None
