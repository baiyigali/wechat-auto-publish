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


def push_draft(
    md_path: str,
    cover_path: str,
    title: str,
    digest: str,
    config_path: str = "config.json",
    account: str | None = None,
) -> str | None:
    """渲染 + 推草稿。无论成功/报错都只调用一次，绝不重试。"""
    html_path = os.path.splitext(md_path)[0] + ".html"
    render(md_path, html_path)

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    cred = _resolve_account(cfg, account)

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
