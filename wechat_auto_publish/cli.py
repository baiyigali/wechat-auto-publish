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
    p = sub.add_parser("draft", help="渲染 + 推草稿箱（只跑一次）")
    p.add_argument("md", help="文章 .md 路径")
    p.add_argument("cover", help="封面 .png 路径")
    p.add_argument("title", help="文章标题")
    p.add_argument("digest", help="摘要（120 字内）")
    p.add_argument("--config", default="config.json", help="凭据路径，默认 ./config.json")
    p.add_argument("--account", default=None,
                   help="config.json 里 accounts 下的账号名；不传则用 default 账号")
    args = parser.parse_args()

    from .pipeline import push_draft
    push_draft(args.md, args.cover, args.title, args.digest, args.config, args.account)
    return 0


if __name__ == "__main__":
    sys.exit(main())
