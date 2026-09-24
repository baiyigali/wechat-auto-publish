"""wechat-auto-publish 测试套件。

不触网：所有用例只覆盖清单解析、渲染、凭据解析、参数校验等本地逻辑。
运行：pytest tests/ -v
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from wechat_auto_publish.pipeline import (  # noqa: E402
    MAX_ARTICLES,
    _resolve_account,
    _resolve_credentials,
    push_draft_multi,
    render,
)
from wechat_auto_publish.cli import main as cli_main  # noqa: E402

SAMPLE_MD = """# 测试标题

这是第一段。

## 小节

- 列表项一
- 列表项二
"""


# ---------- render ----------

class TestRender:
    def test_render_creates_html(self, tmp_path: Path):
        md = tmp_path / "a.md"
        md.write_text(SAMPLE_MD, encoding="utf-8")
        html_path = tmp_path / "a.html"

        result = render(str(md), str(html_path))

        assert result == str(html_path)
        content = html_path.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "测试标题" in content
        assert "wechat-article" in content  # 公众号样式容器

    def test_render_inline_styles(self, tmp_path: Path):
        """渲染出的 HTML 必须是内联样式（公众号不接受外部 CSS 链接）。"""
        md = tmp_path / "b.md"
        md.write_text(SAMPLE_MD, encoding="utf-8")
        html_path = tmp_path / "b.html"
        render(str(md), str(html_path))
        content = html_path.read_text(encoding="utf-8")
        assert "style=" in content


# ---------- 凭据解析 ----------

class TestCredentials:
    def test_direct_credentials_win(self, tmp_path: Path):
        """直接传 appid/secret 时优先于 config 文件。"""
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text(json.dumps({
            "appid": "cfg-id", "secret": "cfg-secret", "author": "配置作者",
        }), encoding="utf-8")
        cred = _resolve_credentials(
            str(cfg_file), appid="direct-id", secret="direct-secret", author="直传作者",
        )
        assert cred == {"appid": "direct-id", "secret": "direct-secret", "author": "直传作者"}

    def test_config_single_account(self, tmp_path: Path):
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text(json.dumps({
            "appid": "cfg-id", "secret": "cfg-secret", "author": "配置作者",
        }), encoding="utf-8")
        cred = _resolve_credentials(str(cfg_file))
        assert cred["appid"] == "cfg-id"
        assert cred["author"] == "配置作者"

    def test_config_multi_account(self, tmp_path: Path):
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text(json.dumps({
            "default": "账号B",
            "accounts": {
                "账号A": {"appid": "a-id", "secret": "a-secret", "author": "A"},
                "账号B": {"appid": "b-id", "secret": "b-secret", "author": "B"},
            },
        }), encoding="utf-8")
        # 不指定 account → 用 default
        cred = _resolve_credentials(str(cfg_file))
        assert cred["appid"] == "b-id"
        # 显式指定 account
        cred = _resolve_credentials(str(cfg_file), account="账号A")
        assert cred["appid"] == "a-id"
        # 不存在的账号报错
        with pytest.raises(KeyError):
            _resolve_credentials(str(cfg_file), account="不存在的号")

    def test_author_override(self, tmp_path: Path):
        """--author 只覆盖作者名，appid/secret 仍走 config。"""
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text(json.dumps({
            "appid": "cfg-id", "secret": "cfg-secret", "author": "配置作者",
        }), encoding="utf-8")
        cred = _resolve_credentials(str(cfg_file), author="覆盖作者")
        assert cred["appid"] == "cfg-id"
        assert cred["author"] == "覆盖作者"

    def test_resolve_account_flat(self):
        assert _resolve_account({"appid": "x", "secret": "y"}, None)["appid"] == "x"


# ---------- push_draft_multi 清单校验（不触网部分） ----------

def _make_manifest(tmp_path: Path, n: int, prefix: str = "a") -> str:
    articles = []
    for i in range(n):
        md = tmp_path / f"{prefix}{i}.md"
        md.write_text(SAMPLE_MD, encoding="utf-8")
        cover = tmp_path / f"{prefix}{i}.png"
        cover.write_bytes(b"\x89PNG fake")
        articles.append({
            "md": str(md),
            "cover": str(cover),
            "title": f"标题{i}",
            "digest": f"摘要{i}",
        })
    manifest = tmp_path / f"manifest_{prefix}.json"
    manifest.write_text(json.dumps({"articles": articles}, ensure_ascii=False), encoding="utf-8")
    return str(manifest)


class TestPushDraftMultiValidation:
    """校验逻辑在触网（拿 access_token）之前执行，可安全测试。"""

    def test_over_limit_raises(self, tmp_path: Path):
        manifest = _make_manifest(tmp_path, MAX_ARTICLES + 1)  # 9 篇
        with pytest.raises(ValueError, match="最多"):
            push_draft_multi(manifest, appid="fake", secret="fake")

    def test_empty_articles_raises(self, tmp_path: Path):
        manifest = tmp_path / "empty.json"
        manifest.write_text(json.dumps({"articles": []}), encoding="utf-8")
        with pytest.raises(ValueError, match="非空"):
            push_draft_multi(str(manifest))

    def test_missing_articles_key_raises(self, tmp_path: Path):
        manifest = tmp_path / "bad.json"
        manifest.write_text(json.dumps({"foo": 1}), encoding="utf-8")
        with pytest.raises(ValueError, match="articles"):
            push_draft_multi(str(manifest))

    def test_max_articles_constant(self):
        assert MAX_ARTICLES == 8

    def test_digest_truncated_to_120(self, tmp_path: Path, monkeypatch):
        """digest 超长应在组装 articles 阶段截到 120 字。"""
        manifest = _make_manifest(tmp_path, 1)
        captured = {}

        def fake_push(appid, secret, articles, **kwargs):
            captured["articles"] = articles
            return "fake-media-id"

        import wechat_publish
        monkeypatch.setattr(wechat_publish, "push_articles", fake_push)
        # push_draft_multi 内部是延迟 import，需要 patch 源模块属性
        long_digest = "超" * 300
        m = json.load(open(manifest, encoding="utf-8"))
        m["articles"][0]["digest"] = long_digest
        json.dump(m, open(manifest, "w", encoding="utf-8"), ensure_ascii=False)

        media_id = push_draft_multi(manifest, appid="fake", secret="fake")
        assert media_id == "fake-media-id"
        assert len(captured["articles"][0]["digest"]) == 120

    def test_title_default_from_filename(self, tmp_path: Path, monkeypatch):
        """manifest 里不写 title 时，默认取 md 文件名。"""
        md = tmp_path / "我的文件名标题.md"
        md.write_text(SAMPLE_MD, encoding="utf-8")
        cover = tmp_path / "c.png"
        cover.write_bytes(b"\x89PNG fake")
        manifest = tmp_path / "m.json"
        manifest.write_text(json.dumps({"articles": [
            {"md": str(md), "cover": str(cover)},
        ]}, ensure_ascii=False), encoding="utf-8")

        captured = {}
        import wechat_publish
        monkeypatch.setattr(wechat_publish, "push_articles",
                            lambda appid, secret, articles, **kw: captured.update(articles=articles) or "mid")
        push_draft_multi(str(manifest), appid="fake", secret="fake")
        assert captured["articles"][0]["title"] == "我的文件名标题"


# ---------- CLI ----------

class TestCli:
    def test_draft_multi_help(self, capsys):
        with pytest.raises(SystemExit) as e:
            cli_main(["draft-multi", "--help"])
        assert e.value.code == 0
        assert "manifest" in capsys.readouterr().out

    def test_draft_help(self, capsys):
        with pytest.raises(SystemExit) as e:
            cli_main(["draft", "--help"])
        assert e.value.code == 0

    def test_missing_subcommand(self):
        with pytest.raises(SystemExit):
            cli_main([])

    def test_draft_multi_dispatch(self, tmp_path: Path, monkeypatch):
        """draft-multi 应把参数正确转发给 push_draft_multi。"""
        manifest = _make_manifest(tmp_path, 1)
        calls = {}

        import wechat_auto_publish.pipeline as pipeline
        monkeypatch.setattr(pipeline, "push_draft_multi",
                            lambda *a, **kw: calls.update(a=a, kw=kw) or 0)
        rc = cli_main([
            "draft-multi", manifest,
            "--appid", "id1", "--secret", "s1", "--author", "白大力",
        ])
        assert rc == 0
        assert calls["a"][0] == manifest
        # cli 按位置传参：manifest, config, account, appid, secret, author
        assert calls["a"][3] == "id1"
        assert calls["a"][4] == "s1"
        assert calls["a"][5] == "白大力"

    def test_draft_dispatch(self, tmp_path: Path, monkeypatch):
        md = tmp_path / "x.md"
        md.write_text(SAMPLE_MD, encoding="utf-8")
        cover = tmp_path / "x.png"
        cover.write_bytes(b"\x89PNG fake")
        calls = {}

        import wechat_auto_publish.pipeline as pipeline
        monkeypatch.setattr(pipeline, "push_draft",
                            lambda *a, **kw: calls.update(a=a) or 0)
        rc = cli_main(["draft", str(md), str(cover), "标题T", "摘要D",
                       "--appid", "id2", "--secret", "s2"])
        assert rc == 0
        assert calls["a"][2] == "标题T"
        assert calls["a"][3] == "摘要D"
