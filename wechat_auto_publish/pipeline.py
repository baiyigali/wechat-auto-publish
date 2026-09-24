"""把一篇已写好的文章分发到微信公众号草稿箱。

这一层不生成内容，只做两步：
  1. 用 wechat-formatter 把 .md 渲染成公众号 HTML（科技风/经典蓝）；
  2. 用 wechat-publish 把 HTML + 封面推到草稿箱（只存草稿，不群发）。
"""
from __future__ import annotations

import json
import os


def render(md_path: str, html_path: str) -> str:
    """调用 wechat-formatter，把 md 渲染成内联样式 HTML。"""
    with open(md_path, "r", encoding="utf-8") as f:
        md = f.read()

    from wechat_formatter import FormatTweaks, get_template, render_article

    template = get_template("科技风", "经典")  # 经典蓝 #2563eb
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
) -> str | None:
    """渲染 + 推草稿。

    凭据来源优先级：直接传入的 appid/secret/author > config 文件里指定账号。
    """
    # 摘要超长就截到 120 字，不报错
    if digest:
        digest = digest.strip()[:120]

    html_path = os.path.splitext(md_path)[0] + ".html"
    render(md_path, html_path)

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
) -> str | None:
    """多图文：把 manifest 里的多篇文章渲染后合成一个草稿推送。

    manifest 为 JSON 文件，结构：
    {
      "articles": [
        {"md": "a.md", "cover": "a.png", "title": "标题A", "digest": "可选，120字内"},
        {"md": "b.md", "cover": "b.png", "title": "标题B"}
      ]
    }
    第一篇为头条封面文章；上限 8 篇。
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
        render(md_path, html_path)
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
