"""wechat-auto-publish 命令行。

用法：
  wechat-auto-publish styles                                 # 查看全部风格 × 配色
  wechat-auto-publish draft <文章.md> <封面.png> "<标题>" "<摘要>" --style 科技风 --color 经典
  wechat-auto-publish draft-multi <manifest.json> --style 商务风 --color 暖阳
"""
from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="wechat-auto-publish",
        description="把已写好的 md 文章渲染并推到公众号草稿箱（支持单篇与多图文，可选渲染风格与配色）。",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("styles", help="列出全部可用渲染风格与配色（6 风格 × 12 配色 = 72 模板）")

    p = sub.add_parser("draft", help="渲染 + 推草稿箱（单篇）")
    p.add_argument("md", help="文章 .md 路径")
    p.add_argument("cover", help="封面 .png 路径")
    p.add_argument("title", help="文章标题")
    p.add_argument("digest", nargs="?", default="", help="摘要（可选，不传由微信自动生成）")
    _add_credential_args(p)
    _add_style_args(p)

    p = sub.add_parser("draft-multi", help="多图文：把 manifest 里的多篇文章合成一个草稿（上限 8 篇）")
    p.add_argument("manifest", help='JSON 清单路径，结构见 README：{"articles": [{md, cover, title, digest?, style?, color?}, ...]}')
    _add_credential_args(p)
    _add_style_args(p)

    args = parser.parse_args(argv)

    if args.cmd == "styles":
        from .pipeline import list_styles
        colors = "、".join(next(iter(list_styles().values())))
        print("可用配色（12 种，全风格通用）：")
        print(f"  {colors}")
        print("可用风格（6 种，中文名或英文 id 均可传）：")
        for cat_id, zh in _style_category_pairs():
            print(f"  {zh:<6} ({cat_id})")
        print(f"共 6 × 12 = 72 个模板。用法：--style <风格> --color <配色>")
        return 0

    from .pipeline import push_draft, push_draft_multi
    if args.cmd == "draft":
        push_draft(
            args.md, args.cover, args.title, args.digest,
            args.config, args.account,
            args.appid, args.secret, args.author,
            style=args.style, color=args.color,
        )
    else:
        push_draft_multi(
            args.manifest,
            args.config, args.account,
            args.appid, args.secret, args.author,
            style=args.style, color=args.color,
        )
    return 0


def _style_category_pairs() -> list[tuple[str, str]]:
    from .pipeline import STYLE_CATEGORIES
    return list(STYLE_CATEGORIES.items())


def _add_credential_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--config", default="config.json", help="凭据路径，默认 ./config.json")
    p.add_argument("--account", default=None,
                   help="config.json 里 accounts 下的账号名；不传则用 default 账号")
    p.add_argument("--appid", default=None, help="直接传公众号 App ID（单发时用，免配置文件）")
    p.add_argument("--secret", default=None, help="直接传公众号 App Secret")
    p.add_argument("--author", default=None, help="直接传文章作者名")


def _add_style_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--style", default="科技风",
                   help="渲染风格：极简风/商务风/文艺风/科技风/节庆风/新粗野风（或 minimalist/business/literary/tech/festive/neo-brutalism），默认 科技风；draft-multi 里可被 manifest 的 \"style\" 键逐篇覆盖")
    p.add_argument("--color", default="经典",
                   help="渲染配色：经典/雅致/先锋/深邃/晨光/星穹/暖阳/暮色/清泉/破晓/璀璨/幽蓝，默认 经典；draft-multi 里可被 manifest 的 \"color\" 键逐篇覆盖（详见 styles 子命令）")


if __name__ == "__main__":
    sys.exit(main())
