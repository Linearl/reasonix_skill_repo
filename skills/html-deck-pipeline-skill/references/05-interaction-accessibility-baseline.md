---
description: 交互与无障碍基线：舞台比例、键盘导航、焦点管理、aria-live 播报等可访问性要求
---
# 交互与无障碍基线规范

## 1. 舞台容器基线

- 演示页比例由阶段 A 冻结的 `ratio_mode` 决定：默认 `16:9`，可选 `4:3` / `16:10` / `adaptive`。
- 推荐：
  - `16:9`：`.deck { aspect-ratio: 16 / 9; }`
  - `4:3`：`.deck { aspect-ratio: 4 / 3; }`
  - `16:10`：`.deck { aspect-ratio: 16 / 10; }`
  - `adaptive`：允许自适应高度，但仍需保留安全区和可读性约束。
- 每页 `<section class="slide">` 须支持内部滚动（`overflow: auto`），避免长内容撑破比例。
- 合并兼容结构：`<div class="deck"> ... </div><script>` 的相邻关系必须保持。
- 舞台状态条统一放在底部：页码与交互提示位于 `.deck-chrome.bottom`，顶部不渲染进度条。

## 2. 屏幕适配

- 建议 1：默认按"缩放后有效视口"而不是物理分辨率设计。关键标题、图表与提示框尽量放在舞台中部约 88% 安全区内，避免贴边导致不同缩放下被裁切或显得拥挤。
- 建议 2：当投屏环境未知，或系统缩放达到 125% / 150% 时，优先降低单页信息密度（建议 2~3 个信息块）并增大标题/正文最小字号；宁可拆页，也不要压缩到边缘。
- 建议 3：在阶段 D.2 网站骨架启动后，至少快检一次 100% / 125% / 150% 缩放下的首屏与章节页，重点看底部状态栏、长标题换行与表格是否溢出。

## 3. 键盘行为

| 按键 | 行为 |
|------|------|
| `ArrowRight` / `ArrowDown` | 下一页 |
| `ArrowLeft` / `ArrowUp` | 上一页 |
| `Space` | 下一页 |
| `Home` | 跳至首页 |
| `End` | 跳至末页 |
| `Escape` | 关闭弹出层（如有） |

- 焦点必须可见：使用 `:focus-visible` 而非 `:focus` 绘制焦点环。
- 焦点环颜色须满足 WCAG 2.2 AA 非文本对比度要求（≥ 3:1）。
- 翻页脚本应使用 `keydown` 事件，避免与浏览器默认滚动冲突时使用 `e.preventDefault()`。

## 4. 触摸行为

- 横向滑动（左/右）触发翻页。
- 纵向滚动手势应被忽略或仅用于页内长内容滚动，避免误触翻页。
- 建议设置最小滑动距离阈值（如 50px），防止点击被误判为滑动。

## 5. 可访问性基线（WCAG 2.2 AA）

### 5.1 跳转链接

```html
<a href="#maincontent" class="sr-only">Skip to main</a>
<!-- 放在 <body> 最前 -->
<main id="maincontent">...</main>
```

```css
.sr-only:not(:focus):not(:active) {
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  height: 1px;
  overflow: hidden;
  position: absolute;
  white-space: nowrap;
  width: 1px;
}
```

### 5.2 Live Region（翻页播报）

```html
<div id="liveRegion" aria-live="polite" aria-atomic="true" class="sr-only"></div>
```

- 翻页时更新内容为：`第 N 页，共 M 页 — {当前页标题}`。
- 使用 `aria-live="polite"` 避免打断正在播报的内容。

### 5.3 对比度要求

| 元素类型 | 最低对比度 |
|----------|-----------|
| 正文文本（< 18.5px bold / < 24px regular） | 4.5 : 1 |
| 大文本（≥ 18.5px bold / ≥ 24px regular） | 3 : 1 |
| 非文本控件与图形元素 | 3 : 1 |

- 颜色不得作为传达信息的唯一手段；必须配合文本或图形标识。

### 5.4 图像与 SVG

- 装饰性图像：`<img alt="">` 或 `aria-hidden="true"`。
- 信息性图像：提供简明 `alt` 或 `aria-label`。
- SVG 元素：添加 `role="img"` + `aria-label="..."`。
- 图标字体 / Emoji：包裹 `<span role="img" aria-label="...">` 或标记 `aria-hidden="true"`。

### 5.5 语义结构

- 使用 `<header>`、`<nav>`、`<main>`、`<footer>` 等地标元素划分区域。
- 每页标题使用一致的 heading 层级（如每页 `<h2>` 作为页标题）。
- 页面级 `<title>` 须描述当前讲稿主题。

## 6. 导航辅助控件

| 控件 ID | 用途 | 最低要求 |
|---------|------|---------|
| `#pageNum` | 页码显示 | 格式 `N / M` |
| `#navHint` | 操作提示 | 含键盘与触摸操作说明 |

- `#pageNum`、`#navHint` 应组合在同一个 `.status-panel` 中，避免顶部/底部分裂布局。
- 禁止渲染 `#progress` 或同义进度条元素，避免遮挡内容区域。
- 禁止渲染“上一页 / 下一页”按钮（如 `prevBtn` / `nextBtn`）；翻页统一依赖键盘与触摸手势，减少视觉干扰和误触热点。

### 6.1 推荐结构片段

```html
<div class="deck-chrome bottom">
  <div class="status-panel">
    <span id="pageNum">01 / 12</span>
    <span id="navHint">⌨ ←/→ 或 Space 翻页 · Home/End 跳转 · ⇆ 左右滑动切页</span>
  </div>
</div>
```

## 7. 动效与减弱动画

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

- 所有入场/退场动画须遵循 `prefers-reduced-motion` 媒体查询。
- 无自动播放动画；翻页动画总时长建议 ≤ 300ms。

## 8. 检查清单（交付前）

- [ ] 键盘翻页（ArrowRight / ArrowLeft / Home / End）功能正常
- [ ] 触摸滑动翻页功能正常
- [ ] Skip to main 链接存在且键盘聚焦时可见
- [ ] Live Region 翻页播报正确
- [ ] 焦点环可见且对比度 ≥ 3:1
- [ ] 正文文本对比度 ≥ 4.5:1
- [ ] 所有图像有适当的 alt / aria-label / aria-hidden
- [ ] SVG 使用 `role="img"` + `aria-label`
- [ ] `prefers-reduced-motion` 下动画已禁用
- [ ] `<title>` 准确描述讲稿主题
- [ ] 不存在 `#progress` 或同义进度条元素
- [ ] 不存在 `prevBtn` / `nextBtn` 或同义翻页按钮
