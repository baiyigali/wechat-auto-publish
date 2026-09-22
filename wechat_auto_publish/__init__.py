"""wechat-auto-publish：最外层公众号发布流水线。

只做分发编排，不生成内容。依赖三个上游：
  - opp-radar       ：机会雷达，负责产出渠道无关的 .md + 封面
  - wechat-formatter：把 .md 渲染成公众号内联样式 HTML
  - wechat-publish  ：把 HTML+封面推到公众号草稿箱
后续要换底层包/换领域时，只动这里的组合，不改上游。
"""

__version__ = "0.1.0"
