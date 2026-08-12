# 容器引擎规范 (Container Engine Specification)

## 1. 架构概览

```
index.html
  ├── js/logger.js          # 调试日志（最先加载）
  ├── js/deck.js            # 幻灯片引擎
  ├── js/editor.js          # WYSIWYG 样式编辑器
  └── css/
      ├── config.yaml        # 主题/字号注册表
      ├── theme/<name>/tokens.css   # 设计令牌（仅1文件）
      ├── fontsize/<name>.css       # 字号方案
      └── common/
          ├── base.css       # 外壳布局、幻灯片几何
          ├── components.css # 20+ 共享组件类
          └── editor.css     # 编辑器 UI 样式
```

**加载顺序（强制）：**
1. tokens.css → 2. fontsize.css → 3. base.css → 4. components.css → 5. editor.css
6. logger.js → 7. deck.js → 8. editor.js

## 2. deck.js — 幻灯片引擎

### 2.1 公开 API (`window.__deckAPI`)

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `getCurrentSlideKey()` | `string` | 当前 slide 的路径标识，如 `ch02/my-slide.html` |
| `getCurrentSlideEl()` | `Element` | 当前 `.slide.active` 元素 |
| `getCurrentIdx()` | `number` | 当前 slide 在 SLIDES 数组中的索引 |
| `applyAutoScale()` | `void` | 检测纵向溢出，通过 CSS transform 缩放适应 |
| `onSlideLoaded` | `function` | editor 设置的 slide 加载回调 |

### 2.2 路由与导航

- Hash 路由：`#ch03/02-slug` 或 `#ch03/2`（索引模式）
- 键盘：`←→↑↓` 翻页，`Space` 前进，`Ctrl+E` 切换编辑器
- 导航栏：自动从 `slides-config.json` 的 `parts` 生成

### 2.3 主题/字号切换

- 主题切换：替换 `<link href="css/theme/<name>/tokens.css">`，持久化到 `localStorage`
- 字号切换：替换 `<link href="css/fontsize/<name>.css">`，持久化到 `localStorage`
- 候选列表从 `css/config.yaml` 读取

### 2.4 导出

| 功能 | 方法 | 说明 |
|------|------|------|
| 导出 HTML | `exportToSingleHTML()` | 内联所有 CSS/JS/幻灯片，生成单文件 |
| 导出 PPTX | `exportToPPTX()` | html2canvas 截图 + pptxgenjs 组装，失败时回落 Playwright |

## 3. editor.js — WYSIWYG 编辑器

### 3.1 公开 API (`window.__editor`)

| 方法 | 说明 |
|------|------|
| `toggle()` | 切换编辑器开关 |
| `isActive()` | 是否处于编辑模式 |
| `getCSSOverrides()` | 获取所有 CSS 修改的 CSS 文本（用于导出） |
| `getModifications()` | 获取 CSS 修改 Map |
| `getDomModifications()` | 获取 DOM 结构修改 Map |
| `getDeletions()` | 获取删除记录 Map |

### 3.2 全局配置 (`window.__CONFIG`)

从 `config.json` 注入，编辑器启动时读取：

```json
{
  "editor": {
    "panelWidth": 300,
    "autoSaveOnDeactivate": false,
    "confirmBeforeExit": true,
    "maxUndoStack": 50
  }
}
```

### 3.3 编辑功能清单

| 功能 | 操作 | 持久化 |
|------|------|--------|
| 样式编辑 | 点击选中 → 面板修改 CSS 属性 | CSS override 文件 |
| 文本编辑 | 双击文字 → contentEditable | HTML 文件 |
| 拖拽重排 | 拖动卡片/面板交换位置 | HTML 文件 |
| 添加组件 | 面板底部的组件面板 | HTML 文件 |
| 多选对齐 | Shift+点击 → 对齐工具栏 | CSS override 文件 |
| 水平/垂直分布 | 多选后点击分布按钮 | 父容器 justify-content/align-content |
| 容器布局切换 | 选中容器 → 切换列数/排列方向 | CSS override 文件 |
| 删除元素 | 选中 → 删除按钮 | HTML 文件 |
| 保存 | 保存按钮 / 退出时确认 | POST /save → 写回源文件 |

### 3.4 数据结构

**modifications** — CSS 修改：
```
Map<slideKey, Map<elementPath, Map<property, value>>>
```
例：`{"ch02/slide.html" → {"div.card:nth-of-type(1) > h3" → {"color" → "#ff4444"}}}`

**domModifications** — DOM 结构修改：
```
Map<slideKey, {appended: [htmlString, ...], reordered: {parentPath: [childFingerprint, ...]}}>
```

**textChanges** — 文本修改：
```
Map<slideKey, Map<selector, newInnerHTML>>
```

**deletions** — 删除记录：
```
Map<slideKey, Set<selector>>
```

## 4. logger.js — 日志系统

### 4.1 API (`window.__logger`)

| 方法 | 说明 |
|------|------|
| `debug/info/warn/error(action, detail)` | 记录日志 |
| `getEntries()` | 获取所有日志条目 |
| `count()` | 当前条目数 |
| `unsent()` | 未发送到服务器的条目数 |
| `flushToDisk()` | 增量发送到服务器 |
| `saveToDisk()` | 全量保存（强制新文件） |
| `clear()` | 清空内存日志 |
| `startTimer()` / `stopTimer()` | 控制定时自动保存 |

### 4.2 行为

- 每 30 秒自动增量 flush
- 页面关闭时 `sendBeacon` 可靠发送
- 内存上限与文件上限一致（默认 2000 条）
- 服务器端按文件轮转

## 5. serve.py — 开发服务器

### 5.1 路由

| 路径 | 来源 |
|------|------|
| `/css/common/*`, `/css/theme/*`, `/css/fontsize/*` | container/css/ |
| `/css/config.yaml` | container/css/config.yaml |
| `/slides-config.json`, `/slides/*`, `/style/*` | 目标目录（如 `28-信息压缩效率思考/20-html/v-01/`） |
| `/js/*`, 其他路径 | container/ |

### 5.2 POST 端点

**POST /save** — 保存编辑器修改

```json
{
  "cssRules": [{"slideKey": "ch02/slide.html", "selector": "h3", "props": {"color": "#f00"}}],
  "domChanges": {"ch02/slide.html": {"appended": ["<div>..."], "reordered": {".grid": ["fp1","fp2"]}}},
  "textChanges": {"ch02/slide.html": {"h3": "new text"}},
  "deletions": {"ch02/slide.html": ["div.card:nth-of-type(2)"]}
}
```

**POST /log** — 保存日志

```json
{
  "url": "http://localhost:8080/#ch01/cover",
  "ua": "Mozilla/5.0 ...",
  "entries": [{"ts": "...", "level": "info", "action": "xxx", "detail": {...}}],
  "full": false
}
```

## 6. CSS 架构

### 6.1 设计令牌（tokens.css）

每个主题必须定义以下 30+ 语义变量：

**背景层**：`--bg`, `--surface-1`, `--surface-2`, `--surface-3`
**文字层**：`--text`, `--text-sec`, `--text-faint`
**强调色**：`--accent`, `--accent-strong`, `--brand`
**语义色**：`--ok`, `--warn`, `--risk`, `--info`
**边框**：`--border-subtle`, `--border-soft`
**特效**：`--surface-glass`, `--surface-glow`, `--surface-hover`
**阴影**：`--shadow-soft`, `--shadow-strong`
**渐变**：`--bg-gradient-body`, `--bg-gradient-deck`, `--bg-gradient-slide`
**排版**：`--font-main`, `--font-code`, `--text-xs` ~ `--text-xl`
**间距/圆角**：`--radius-sm`, `--radius-md`, `--radius-lg`, `--transition-fast`

### 6.2 字号方案（fontsize）

每套方案定义 5 级字号变量：`--text-xs` ~ `--text-xl`。所有组件通过变量引用字号，不由组件直接写 rem 值。

### 6.3 命名空间规则

- 跨章节共享规则 → `common/components.css`
- 章节特定覆盖 → `style/<part_id>.css`，使用 `.part-<part_id>` 命名空间
- 编辑器用户覆盖 → `style/editor-overrides.css`，使用 `[data-slide-key="..."]` 作用域

## 7. 扩展指南

### 7.1 新增主题

1. 创建 `css/theme/<name>/tokens.css`（含全部 30+ token）
2. 在 `css/config.yaml` 的 `themes` 列表中添加条目
3. 可选：创建 `examples/<name>/style-contract-<name>.md` + `style-showcase-<name>.html`

### 7.2 新增字号方案

1. 创建 `css/fontsize/<name>.css`（定义 `--text-xs` ~ `--text-xl`）
2. 在 `css/config.yaml` 的 `fontsizes` 列表中添加条目

### 7.3 新增组件类型

1. 在 `components.css` 中添加组件样式
2. 在 `config.json` 的 `editor.components.customTemplates` 中添加 HTML 模板
