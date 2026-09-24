"""wechat-auto-publish 命令行。

用法：
  wechat-auto-publish draft <文章.md> <封面.png> "<标题>" "<摘要>"
  wechat-auto-publish draft-multi <manifest.json>
"""
from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="wechat-auto-publish",
        description="把已写好的 md 文章渲染并推到公众号草稿箱（支持单篇与多图文）。",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("draft", help="渲染 + 推草稿箱（单篇）")
    p.add_argument("md", help="文章 .md 路径")
    p.add_argument("cover", help="封面 .png 路径")
    p.add_argument("title", help="文章标题")
    p.add_argument("digest", nargs="?", default="", help="摘要（可选，不传由微信自动生成）")
    _add_credential_args(p)

    p = sub.add_parser("draft-multi", help="多图文：把 manifest 里的多篇文章合成一个草稿（上限 8 篇）")
    p.add_argument("manifest", help="JSON 清单路径，结构见 README：{\"articles\": [{md, cover, title, digest?}, ...]}")
    _add_credential_args(p)

    args = parser.parse_args(argv)

    from .pipeline import push_draft, push_draft_multi
    if args.cmd == "draft":
        push_draft(
            args.md, args.cover, args.title, args.digest,
            args.config, args.account,
            args.appid, args.secret, args.author,
        )
    else:
        push_draft_multi(
            args.manifest,
            args.config, args.account,
            args.appid, args.secret, args.author,
        )
    return 0


def _add_credential_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--config", default="config.json", help="凭据路径，默认 ./config.json")
    p.add_argument("--account", default=None,
                   help="config.json 里 accounts 下的账号名；不传则用 default 账号")
    p.add_argument("--appid", default=None, help="直接传公众号 App ID（单发时用，免配置文件）")
    p.add_argument("--secret", default=None, help="直接传公众号 App Secret")
    p.add_argument("--author", default=None, help="直接传文章作者名")


if __name__ == "__main__":
    sys.exit(main())
