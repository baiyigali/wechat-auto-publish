"""wechat-auto-publish 命令行。

用法：
  wechat-auto-publish draft <文章.md> <封面.png> "<标题>" "<摘要>"
"""
from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="wechat-auto-publish",
        description="把一篇已写好的 md 文章渲染并推到公众号草稿箱。",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("draft", help="渲染 + 推草稿箱")
    p.add_argument("md", help="文章 .md 路径")
    p.add_argument("cover", help="封面 .png 路径")
    p.add_argument("title", help="文章标题")
    p.add_argument("digest", nargs="?", default="", help="摘要（可选，不传由微信自动生成）")
    p.add_argument("--config", default="config.json", help="凭据路径，默认 ./config.json")
    p.add_argument("--account", default=None,
                   help="config.json 里 accounts 下的账号名；不传则用 default 账号")
    p.add_argument("--appid", default=None, help="直接传公众号 App ID（单发时用，免配置文件）")
    p.add_argument("--secret", default=None, help="直接传公众号 App Secret")
    p.add_argument("--author", default=None, help="直接传文章作者名")
    args = parser.parse_args()

    from .pipeline import push_draft
    push_draft(
        args.md, args.cover, args.title, args.digest,
        args.config, args.account,
        args.appid, args.secret, args.author,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
