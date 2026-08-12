---
description: 风格契约创建模式：按需触发的新建/重写风格契约流程与一致性门禁
---
# 风格契约创建模式（按需触发）

> 触发条件：仅当用户**显式要求**“新建风格契约/重写风格契约”时启用。
>
> 默认流程不进入本模式，优先复用已有 `style-id`。

## 触发判定

满足任一条件才进入本模式：

- 用户明确提出“新建风格”或“重写现有风格契约”。
- 现有 `style-id` 无法满足业务约束（且用户确认不复用旧风格）。
- 风格资产缺失且无法从 `examples/<style-id>/` 复制。

## 最小输入

- 新风格 `style-id`
- 适用主题与目标受众
- 风格禁止项
- 至少 5 类页面模式需求

## 创建步骤

1. 生成 `style-contract-<style-id>.md`。
2. 生成 `style-showcase-<style-id>.html`（至少包含封面、导航、对比、流程、行动、收口）。
3. 在阶段 A 冻结中记录新风格资产路径。
4. 阶段 C / D 严格使用该 `style-id`，不得临时切换。

## 一致性门禁

- `style-id` 在分镜 Frontmatter、HTML 分片、合并稿、冻结快照中一致。
- 风格描述文件与展示文件成对存在，缺一不可。
- 不允许只改展示文件不改契约，或只改契约不改展示文件。

## 参考

- 模板页规范：`references/01-template-pages-standard.md`
- 详细编写规则：`references/06-style-contract-authoring-guide.md`
- 问询卡片：`references/04-stage-a-question-card.md`
- 质量门禁：`references/07-quality-gate-patterns.md`
