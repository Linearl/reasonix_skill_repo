---
description: style-showcase 模板页统一规范：7 类强制模板页型、可访问性最低要求、验收清单
---
# 示例模板页统一规范

> 适用范围：`22-html技能开发/html-deck-pipeline-skill-v2/examples/**/style-showcase-*.html`
>
> 目标：统一未来所有示例文件的最小模板页集合，避免示例过于简单、难以复用。

## 1) 当前三套示例已包含页面（现状）

### A. `dark-theme/style-showcase-dark-theme.html`（7页）

- P1：封面页（Cover）
- P2：目录页（Navigation）
- P3：双栏对比页（Compare）
- P4：数据证据页（Evidence）
- P5：流程页（Process）
- P6：行动页（Action）
- P7：底页（Closing）

### B. `light-theme/style-showcase-light-theme.html`（7页）

- P1：封面页（Cover）
- P2：导航页（Route / Navigation）
- P3：方法拆解页（Method）
- P4：证据矩阵页（Matrix / Evidence）
- P5：对比页（Compare）
- P6：行动页（Action）
- P7：底页（Closing）

### C. `qclaw-theme/style-showcase-qclaw-theme.html`（7页）

- P1：封面页（Cover）
- P2：导航页（Navigation）
- P3：流程页（Process）
- P4：证据页（Evidence）
- P5：对比页（Compare）
- P6：行动页（Action）
- P7：底页（Closing）

---

## 2) 未来示例的强制模板页集合（MUST）

所有新示例文件都必须包含以下 7 类模板页（页名可同义替换，但语义不可缺失）：

1. **封面页**（Cover）
2. **导航页**（Navigation / Route / 目录）
3. **方法或流程页**（Method / Process）
4. **证据类页面**（Evidence / Matrix / 数据页）
5. **对比类页面**（Compare）
6. **行动页**（Action）
7. **底页**（Closing / 收口页）

### 统一门槛

- 总页数：不少于 7 页。
- 必须包含封面页与底页。
- 内容模板页不少于 3 类（本规范已提升为 5 类核心内容模板）。
- 页码标识建议统一为 `P1/N ... PN/N`。

---

## 3) 推荐页序（默认）

默认页序建议如下（可局部调整）：

- P1 封面
- P2 导航
- P3 方法/流程
- P4 证据
- P5 对比
- P6 行动
- P7 底页

> 注：允许新增可选页（如章节过渡页、风险清单页、附录页），但不可删除上述 7 类强制页。

---

## 4) 可访问性与语义最低要求（MUST）

- 提供 `Skip to main`（跳到主要内容）链接。
- 使用语义地标（至少 `main`，建议 `header/nav/main/footer`）。
- 键盘操作可达，且焦点可见。
- 隐藏内容不可进入 tab 顺序。
- 若存在页面状态播报，使用 `aria-live="polite"`。
- 不仅用颜色传达信息（需有文本辅助）。

---

## 5) 页面元素特性最低要求（MUST）

为约束后续 HTML 生成质量，每套示例（7 页）至少应出现以下元素：

- 路线图/路径图（导航页）
- 卡片组（至少 2 张）
- 提示框（Tip Box，建议带风险/边界提示）
- 对比块（Compare）

> 说明：元素可根据风格做视觉变体，但语义功能需保留。

---

## 6) 与风格描述文件的联动要求（MUST）

每个风格目录中的 `style-contract-*.md` 必须提供“逐页说明”，并与示例 HTML 一一对应：

- 对应页面编号（P1..Pn）
- 页面名称 / 用途
- 推荐布局
- 必备元素
- 可选元素
- 文案长度建议

若 HTML 页型发生变化，需同步更新 style-contract 的逐页说明，保持一致性。

---

## 7) 快速验收清单（Checklist）

- [ ] 是否包含 7 类强制模板页
- [ ] 是否包含封面页与底页
- [ ] 是否有清晰页码（P1/N）
- [ ] 是否满足可访问性最低要求
- [ ] 是否覆盖路线图、卡片、提示框、对比四类元素
- [ ] `style-contract` 是否逐页对应且页数一致

---

## 8) 当前示例合规结论（2026-03-16）

- `dark-theme`：满足页型与元素要求。
- `light-theme`：满足页型与元素要求。
- `qclaw-theme`：满足页型与元素要求。

---

## 9) 版本说明

- 当前版本：`v1`
- 生效日期：`2026-03-16`
- 维护位置：`22-html技能开发/html-deck-pipeline-skill-v2/references/`
