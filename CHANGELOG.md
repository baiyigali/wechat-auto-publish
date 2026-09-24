# Changelog

## [1.0.3] - 2026-09-25

- 新增 `draft-multi` 子命令：JSON 清单驱动，一次最多 8 篇文章合成一个多图文草稿
- 凭据解析逻辑重构为 `_resolve_credentials`，`draft` 与 `draft-multi` 行为一致
- README 增加 draft-multi 用法与 manifest 结构说明
- 拷入 AGENTS.md（AI 编程助手协作硬性规则）
- 新增 tests/ 测试套件（18 个用例：渲染/凭据/多图文校验/CLI 分发，不触网）
- 测试整合进 publish.yml：test job（Python 3.10-3.13 矩阵）前置，测试通过才构建发布

## [1.0.2] - 2026-09-23

- 支持 `--appid / --secret / --author` 直接传凭据，单发无需配置文件
- 摘要改为可选，超长自动截到 120 字
- `prompts/pipeline.md` 重写，去掉与内容生成的耦合
- README 重构：快速开始前置，新增相关项目互荐与公众号卡片
