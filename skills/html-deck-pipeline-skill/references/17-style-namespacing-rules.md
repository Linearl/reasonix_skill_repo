---
description: 样式命名空间规范：CSS 分层架构、`.part-*` 命名空间规则与分片样式隔离
---
# 样式命名空间与 CSS 分层架构规范

## 1. 命名空间规则（强制）

- 每个分片必须拥有独立命名空间前缀，推荐：`part-ch01`、`part-ch02`、`part-ch03`。
- 分片内自定义样式应挂在命名空间根下，例如：
  - `.part-ch01 .card { ... }`
  - `.part-ch02 .table th { ... }`
- 禁止在分片中直接覆盖高风险通用类（如 `.card`、`.table`、`.tip`、`.grid`）而不加命名空间。
- 旧版命名 `.part-s01` 已废弃，新项目统一使用 `.part-ch0X`（ch = chapter）。

## 2. CSS 分层架构（推荐）

新项目推荐采用四层 CSS 架构，减少重复、便于维护：

```
css/
├── tokens.css       # :root 自定义属性（颜色、字体、间距、阴影、圆角等）
├── base.css         # 重置、body、deck容器、slide外壳、进度条、导航、键盘提示
├── components.css   # 跨章节共享组件（卡片、面板、标签、表格、引用框、高亮等）
└── ch0X.css         # 各章节特有的组件与布局覆盖（按需加载）
```

### 分层原则

| 层级 | 选择器作用域 | 内容 |
|------|-------------|------|
| tokens | `:root` | 全局 CSS 变量，不包含选择器规则 |
| base | 无作用域 / `#deck-shell` / `.deck` / `.slide` | 舞台几何结构、外壳 chrome、必须全局生效的基础规则 |
| components | 无作用域 | `.panel`、`.card`、`.chip`、`table`、`.quote-box` 等跨章节复用组件 |
| ch0X | `.part-ch0X` 作用域 | 仅该章节使用的组件（如 `.section-card`、`.cognition-grid`、`.step-flow`） |

### 关键规则

- `tokens.css` 和 `base.css` 在 `index.html` 中直接 `<link>` 加载。
- `components.css` 在 `index.html` 中直接 `<link>` 加载。
- `ch0X.css` 按需懒加载（首次进入该章节时由 JS 动态注入 `<link>`）。
- 章节特有样式必须挂在 `.part-ch0X` 命名空间下，不得污染全局。

## 3. 选择器约束（强制）

- 优先使用"命名空间 + 组件类"的双层选择器。
- 禁止使用过宽选择器（如 `*`、`div`、`section` 全局覆盖）去改写排版或配色。
- 禁止在分片中重定义舞台级核心结构选择器（如 `.deck > .slide`）的几何约束，除非有明确审批。

## 4. 合并兼容性规则（强制）

- 如需分片容器包裹，容器应使用 `display: contents`，避免影响 `.slide` 尺寸继承。
- 分片样式需兼容"以 part1 为基准样式、part2..N 作用域注入"的合并策略。
- 表格样式必须在分片阶段统一（表头/单元格对齐策略一致），不得等到合并后再修正。

## 5. 网站骨架模式（推荐用于最终交付）

当最终交付物为独立可部署的网站（而非单个 HTML 文件）时，采用以下结构：

```
20-html/v-XX/
├── index.html         # 最小外壳：shell > nav + deck + progress + kbd-hint
├── js/
│   └── deck.js        # 幻灯片加载、hash路由、键盘导航、自适应缩放
├── css/
│   ├── tokens.css
│   ├── base.css
│   ├── components.css
│   └── ch0X.css
└── slides/
    └── ch0X/
        └── XX-slug.html  # 单页 HTML 片段（仅 <section class="slide">）
```

### deck.js 核心能力

- **幻灯片加载**：`fetch()` 拉取 `slides/ch0X/XX-slug.html`，注入 `#deck`
- **Hash 路由**：`#ch03/02-feedback` 格式，支持浏览器前进/后退
- **章节 CSS 懒加载**：首次进入章节时动态创建 `<link>` 加载 `ch0X.css`
- **键盘导航**：ArrowRight/Down/Space 下一页，ArrowLeft/Up 上一页
- **自适应缩放**：`transform: scale(clientHeight / scrollHeight)` 基于纵向空间自动缩放，不改变内部布局；`-1px` 安全边距防止舍入误差产生滚动条；监听 `window.resize` 自动重算
- **章节导航按钮**：自动生成，高亮当前章节

### Deck 容器布局（base.css 固定范式）

```css
body {
  height: 100vh;
  overflow: hidden;           /* 永不出现页面级滚动条 */
}

#deck-shell {
  height: 100vh;
  overflow: hidden;           /* 防止内容溢出产生滚动条 */
  display: grid;
  grid-template-rows: auto 1fr auto auto;  /* 导航 | deck(撑满) | 进度条 | 键盘提示 */
  justify-items: center;
}

.deck {
  width: 100%;
  max-width: 1600px;
  aspect-ratio: 16 / 9;
  max-height: 100%;           /* 由 grid 1fr 行约束 */
  overflow: hidden;
}
```

此方案相比硬编码 `calc(100vh - 152px)` 的优势：deck 自动填满导航和进度条之间的所有可用空间，不受估算误差影响；从高分屏拖到低分屏时缩放自适应，不出现滚动条。

## 6. 自检清单

- [ ] 高风险通用类均已命名空间化。
- [ ] 未出现全局覆盖型选择器污染。
- [ ] 背景样式类型控制在项目约束范围内。
- [ ] 与合并策略兼容（part1 基准 + part2..N 注入）。
- [ ] 若采用网站骨架模式，`body` 和 `#deck-shell` 均设置 `overflow: hidden`。
- [ ] 若采用网站骨架模式，deck.js 中 `applyAutoScale()` 使用 `(clientH - 1) / scrollH` 作为缩放因子。

## 7. 违规处置

- 命中命名冲突风险时，必须在阶段 D 回退修正，不得带病进入阶段 E。
- 修复后需重新执行分片自查，并在 D.3 向用户说明修复影响范围。
