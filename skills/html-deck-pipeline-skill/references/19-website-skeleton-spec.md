---
description: 网站骨架输出规范：config-driven 模式下的完整网站骨架规范（CSS 三层架构、deck.js、hash 路由、自适应缩放）
---
# 网站骨架输出规范

## 1. 何时选用网站骨架模式

满足以下任一条件时优先选用网站骨架：

- 页数超过 15 页，单文件 HTML 体积过大（>500KB）
- 需要浏览器前进/后退导航（hash 路由）
- 需要按章节懒加载 CSS，减少首屏加载
- 最终交付物需要部署到静态托管（GitHub Pages / Vercel / Netlify 等）
- 需支持多章节独立维护、增量更新

## 2. 目录结构（固定）

```
20-html/v-XX/
├── slides-config.json     # 讲稿配置：title、parts、partOrder、slides 清单
├── index.html             # 入口页面（由 serve.py 从 container/ 复制）
├── js/
│   └── deck.js            # 幻灯片引擎（启动时 fetch slides-config.json）
├── css/
│   ├── tokens.css         # :root 自定义属性（颜色、字体、间距、阴影、圆角）
│   ├── base.css           # 重置、body、shell、deck 容器、slide 外壳、进度条、导航
│   └── components.css     # 共享组件（卡片、面板、标签、表格、引用、高亮等）
├── style/                 # 章节额外样式（按需），如 ch01.css
└── slides/
    └── <part_id>/
        └── <NN-description>.html   # 单页 HTML 片段（仅 <section class="slide">...</section>）
```

## 3. CSS 三层架构

| 层级 | 文件 | 加载方式 | 内容 |
|------|------|---------|------|
| tokens | `css/tokens.css` | index.html `<link>` | `:root` 全局 CSS 变量（双主题） |
| base | `css/base.css` | index.html `<link>` | 重置、舞台几何、外壳 chrome、导航栏 |
| components | `css/components.css` | index.html `<link>` | 共享组件（`.panel`, `.card`, `table`, `.quote-box`, `.tip-card` 等） |

**关键规则**：

- 三层 CSS 均在 `index.html` 中直接 `<link>`，无懒加载
- 主题切换通过 `[data-theme]` 选择器实现，由 `tokens.css` 定义双主题变量
- `container/css/` 下预置 4 套主题（dark-theme、dark-theme-2、light-theme、qclaw-theme）
- 章节附加样式放在 `target_dir/style/`，由 deck.js 按需懒加载；未提供时允许 404 并视为无章节附加样式
- 启动时通过 `--theme` 参数选择主题，`serve.py` 自动复制对应 CSS 到目标目录

## 4. index.html 模板（最小外壳）

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{主题标题}</title>
  <link rel="stylesheet" href="css/tokens.css" />
  <link rel="stylesheet" href="css/base.css" />
  <link rel="stylesheet" href="css/components.css" />
</head>
<body>
  <a href="#deck" class="skip-link">跳转到幻灯片</a>

  <main id="deck-shell" class="part-ch01" aria-label="{讲稿名称}">
    <nav id="part-nav" aria-label="章节导航"></nav>

    <div class="deck" id="deck" role="region" aria-label="幻灯片">
      <div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-faint);">
        <p>加载中…</p>
      </div>
    </div>

    <div id="deck-progress"><div class="bar" style="width:0%"></div></div>
    <div id="kbd-hint">
      <kbd>&larr;</kbd> <kbd>&rarr;</kbd> 切换页面 &nbsp;|&nbsp;
      <kbd>&uarr;</kbd> <kbd>&darr;</kbd> 亦可 &nbsp;|&nbsp;
      点击上方章节标签跳转 &nbsp;|&nbsp;
      <button id="export-btn" title="导出为单文件 HTML">导出 HTML</button>
    </div>
  </main>

  <script src="js/deck.js"></script>
</body>
</html>
```

**结构要点**：

- `<main id="deck-shell">` 初始 class 为 `part-ch01`（匹配首章）
- `<nav id="part-nav">` 由 deck.js 动态生成按钮
- `.deck` 容器内初始为加载占位，deck.js 初始化时替换为第一页 slide
- CSS 只加载 tokens/base/components，章节 CSS 由 JS 懒加载

## 5. Deck 容器布局规范（base.css 固定范式）

### 5.1 视口占用策略

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

**设计原理**：Grid `1fr` 行自动填满导航和进度条之间的所有可用空间，无需硬编码 `calc(100vh - Npx)`。

### 5.2 禁止事项

- 禁止在 `body` 上使用 `min-height`（必须 `height: 100vh`）
- 禁止在 slide 层修改 `.deck` 的 `width`/`height`/`aspect-ratio`
- 禁止在章节 CSS 中覆盖 `body` / `#deck-shell` / `.deck` 的几何属性
- 禁止使用 `100vw` 或 `100vh` 给内部元素设尺寸

## 6. deck.js 规范

### 6.1 幻灯片数据结构

幻灯片清单通过 `slides-config.json` 定义，deck.js 启动时 fetch 读取：

```json
{
  "title": "讲稿标题",
  "parts": { "ch01": "第一章", "ch02": "第二章" },
  "partOrder": ["ch01", "ch02"],
  "slides": [
    { "part": "ch01", "file": "01-cover.html", "title": "封面" }
  ]
}
```

### 6.2 核心能力（必须实现）

| 能力 | 实现方式 | 约束 |
|------|---------|------|
| **配置加载** | `fetch('slides-config.json')` 启动时读取 | 加载失败展示错误，不得静默失败 |
| **幻灯片加载** | `fetch('slides/{part}/{file}')` → `deck.innerHTML = html` | 加载失败展示错误信息 |
| **Hash 路由** | `#ch03/02-feedback` 格式 | 支持浏览器前进/后退，支持 `#ch03/2`（章节内序号） |
| **键盘导航** | ArrowRight/Down/Space 下一页，ArrowLeft/Up 上一页 | 不拦截 INPUT/TEXTAREA 中的按键 |
| **自适应缩放** | 见 §7 | 缩放因子仅基于纵向空间 |
| **章节导航** | 从 config.parts 自动生成按钮，高亮当前章节 | 按钮绑定 `goToPart(part)` |
| **进度条** | `(currentIdx + 1) / SLIDES.length * 100` | 过渡动画 300ms |
| **主题切换** | `[data-theme]` 选择器 + localStorage | 下拉选择，即时生效 |
| **章节样式加载** | `style/{part}.css`（按需） | 从 `target_dir/style/` 加载，不属于主题目录 |
| **Resize 响应** | 监听 `window.resize`，触发 `applyAutoScale()` | 使用 rAF 防抖 |

### 6.3 Part class 切换

```javascript
function setPart(part) {
  PART_ORDER.forEach(p => deckShell.classList.remove(`part-${p}`));
  deckShell.classList.add(`part-${part}`);
}
```

通过切换 `#deck-shell` 上的 class 来激活章节对应的 CSS 变量或样式。

章节附加样式若存在，统一放在 `target_dir/style/<part_id>.css`，并由 `serve.py` 将 `/style/*` 路由到目标目录。

### 6.4 导出单文件 HTML

deck.js 必须包含 `exportToSingleHTML()` 函数，由"导出 HTML"按钮触发：

**导出逻辑**：
1. `fetch()` 所有 CSS 文件（tokens + base + components + `style/<part>.css` 章节附加样式）
2. `fetch()` 所有 slide HTML 文件
3. 将所有 CSS 内联到 `<style>` 标签
4. 将所有 slide 内联到 DOM（仅首张 `.active`）
5. 内联主题切换 JS + 键盘导航 JS
6. 生成 Blob 并触发下载（支持 `showSaveFilePicker`）

**导出文件要求**：
- 脱离服务器可直接用 `file://` 协议打开
- 翻页、主题切换、自适应缩放均可用
- 无任何外部资源请求（404-free）
- 文件名格式：`{title}-export.html`

### 6.5 导出 PPTX

deck.js 包含 `exportToPPTX()` 函数，纯客户端实现：
- 使用 `html2canvas` 逐页截图（2x 分辨率）
- 使用 `pptxgenjs` 生成 16:9 PPTX
- 库文件首次使用时从 CDN 按需加载
- 支持 `showSaveFilePicker` 原生保存对话框

## 7. 自适应缩放规范

### 7.1 触发时机

- 每次 slide 加载完成后
- 每次 `window.resize` 事件

### 7.2 缩放算法（固定）

```javascript
let _scaleRAF = 0;
function applyAutoScale() {
  cancelAnimationFrame(_scaleRAF);
  _scaleRAF = requestAnimationFrame(() => {
    const slideEl = deck.querySelector('.slide.active');
    if (!slideEl) return;
    slideEl.style.transform = '';
    slideEl.style.transformOrigin = '';
    const scrollH = slideEl.scrollHeight;
    const clientH = slideEl.clientHeight;
    if (scrollH > clientH) {
      const scale = (clientH - 1) / scrollH;   // -1px 安全边距，防止舍入滚动条
      slideEl.style.transform = `scale(${scale})`;
      slideEl.style.transformOrigin = 'top center';
    }
  });
}
```

### 7.3 设计要点

- 缩放因子**仅基于纵向空间**：`(clientH - 1) / scrollH`
- `-1px` 安全边距防止浮点舍入导致残留滚动条
- `transform: scale()` 不影响布局计算，内部元素保持原始尺寸
- `transform-origin: top center` 确保缩放后内容顶部对齐
- 使用 `requestAnimationFrame` 等待浏览器完成布局后再测量
- 使用 `cancelAnimationFrame` 防抖 resize 事件

## 8. Slide HTML 片段格式

### 8.1 单页 slide 模板

```html
<section class="slide" role="region" aria-label="{页面标题}">
  <div class="slide-head">
    <span class="eyebrow">{章节 · 页面主题}</span>
    <span class="page-chip">{全局页码} / {总页数}</span>
  </div>

  <div class="slide-body">
    <!-- 页面内容：标题、表格、卡片等 -->
  </div>
</section>
```

### 8.2 强制约束

- 每个 slide 文件只包含 `<section class="slide">` 元素，不含 `<html>`/`<body>`/`<style>`/`<script>`
- slide 内不使用 `<style>` 标签（所有样式在 CSS 层中统一管理）
- slide 内不使用 `<script>` 标签
- 类名优先使用 components.css 中的共享组件类
- 章节特有类必须确认已在对应 `ch0X.css` 中定义
- **页眉统一使用 `.slide-head` + `.eyebrow`**（不再使用 `.slide-header` / `.section-tag`）
- **eyebrow 文案为单行，格式 `章节 · 页面主题`**，禁止使用两条标签
- **不再使用 `.slide-foot` 页脚**，页面内容由 slide-body 承载
- 全局页码由构建脚本或 deck.js 运行时注入；若在分片中硬编码，需保持与 SLIDES 数组一致

## 9. 字号规范（五级阶梯）

全文统一使用五级字号阶梯，禁止引入阶梯外的 rem 值。级差 ~0.13rem，人眼可辨。

| 层级 | 字号 | 用途 |
|------|------|------|
| **XS** | 0.72rem | 脚注、卡片微字、flow-step 小型标注 |
| **S** | 0.82rem | 正文、表格内容、卡片描述、barrel 正文 |
| **M** | 0.95rem | 卡片标题、强调段落、mini-chip 标题 |
| **L** | 1.10rem | panel/card 标题、核心结论、引述文字 |
| **XL** | clamp(...) | 页面大标题（h2），保持弹性字号，不做映射 |

**落点规则**：
- S/M 系定义在 `components.css` 的基础组件类中（`table`, `.panel`, `.card`, `.tip-card` 等）
- L 系定义在各章节 CSS 的组件标题规则中（`.panel > strong` 等）
- XL 系定义在 `base.css` 的 `.slide-title` 规则中
- 章节 CSS 只做微调覆盖（不超过 ±1 级），不定义独立字号体系
- 所有内联 `font-size` 必须落在阶梯值上；清洗时就近取整

## 10. PPTX 导出

**优先**：浏览器端一键导出（点击"导出 PPTX"按钮，通过 html2canvas + pptxgenjs 客户端生成）。

**保底**：若浏览器端导出失败，使用内置 `internal-skill/html-deck-to-pptx/` 的 Playwright 截图方案——逐页截图后通过 python-pptx 组装。详见该子技能的 SKILL.md。

## 11. 构建与启动流程（config-driven）

### 11.1 输入

- `slides/<part_id>/<NN-description>.html` — 阶段 D 产出的单页 HTML
- `slides-config.json` — 讲稿配置

### 11.2 构建步骤

1. **确认 slides/ 就绪**：所有页面 HTML 按 `slides/<part_id>/<NN-description>.html` 组织
2. **编写 slides-config.json**：填入 title、parts 映射、partOrder、slides 清单
3. **运行启动脚本**：
   ```bash
   python container/serve.py <target_dir> --theme dark-theme-2
   ```
  脚本直接从 `container/` 提供骨架文件，将 `/css/*` 路由到所选主题目录，并将 `/style/*`、`/slides/*`、`/slides-config.json` 路由到 `target_dir`
4. **deck.js 读取配置**：启动时 fetch `slides-config.json`，自动填充幻灯片列表、章节导航、页面标题
5. **验证**：打开浏览器确认翻页、路由、缩放、导出均正常

### 11.3 命名规则

- Slide 文件：`slides/<part_id>/<NN-description>.html`，如 `slides/ch03/02-feedback.html`
- 每个章节内序号独立编号（从 01 开始）
- slug 使用小写英文+连字符，描述页面核心内容

## 12. 与单文件导出模式的关系

| 维度 | 单文件导出 HTML | 网站骨架 |
|------|---------------|---------|
| 输出 | 1 个 HTML 文件（含所有 CSS/JS） | index.html + CSS/JS/slides 目录 |
| 样式管理 | 内联所有 CSS | CSS 三层架构 |
| 导航 | 键盘翻页 | Hash 路由 + 键盘导航 + 章节导航 + 进度条 |
| 缩放 | 自适应缩放 | 自适应缩放 |
| 适用场景 | 离线分发、邮件附件 | 在线浏览、静态托管 |
| 部署 | 浏览器直接打开 | 需静态服务（localhost 亦可） |
| 导出 PPTX | 通过导出 HTML 后 Python 转换 | 浏览器直接导出（html2canvas + pptxgenjs） |

## 13. 自检清单

- [ ] `body` 和 `#deck-shell` 均设置 `overflow: hidden`
- [ ] `.deck` 使用 `aspect-ratio: 16/9` + `max-height: 100%`
- [ ] tokens.css / base.css / components.css 在 index.html 中直接 `<link>`
- [ ] `slides-config.json` 配置完整（title、parts、partOrder、slides）
- [ ] `python container/serve.py <target_dir>` 可正常启动
- [ ] 导出 HTML 和导出 PPTX 按钮均可用
- [ ] 主题下拉切换正常
- [ ] 所有章节特有样式挂在 `.part-ch0X` 命名空间下，并按需放在 `style/ch0X.css`
- [ ] `applyAutoScale()` 使用 `(clientH - 1) / scrollH` 作为缩放因子
- [ ] resize 事件监听已注册且带 rAF 防抖
- [ ] slide 文件仅含 `<section class="slide">`，无 `<style>`/`<script>`
- [ ] hash 路由格式为 `#ch0X/XX-slug`
- [ ] 章节导航按钮自动生成且高亮当前章节
- [ ] 键盘导航不拦截输入框中的按键
- [ ] 加载失败时展示错误信息，不静默失败
- [ ] "导出 HTML" 按钮可见且可点击
- [ ] 导出文件可脱离服务器直接用 `file://` 协议打开
- [ ] 导出文件含全部 20+ slides 且键盘翻页正常
- [ ] 导出文件无外部资源请求（Network 面板确认 404-free）
