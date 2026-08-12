# HTML Deck 网站骨架

可用于任意 HTML 讲稿项目的可复用骨架。支持懒加载幻灯片、hash 路由、自适应缩放、主题切换、一键导出 HTML/PPTX。

## 项目结构

```
20-html/v-XX/                # 你的讲稿版本目录
├── slides-config.json       # 幻灯片配置（标题、章节、页面列表）
├── slides/
│   ├── ch01/
│   │   ├── 01-cover.html
│   │   └── ...
│   └── ch02/
│       └── ...
├── index.html               # 入口页面（serve.py 从 container/ 直接提供）
├── js/deck.js               # 幻灯片引擎（serve.py 从 container/ 直接提供）
└── css/                     # 主题 CSS（serve.py 从 container/ 直接提供）
    ├── tokens.css
    ├── base.css
    └── components.css
```

## 快速开始

### 1. 创建 slides-config.json

```json
{
  "title": "我的讲稿",
  "parts": {
    "ch01": "开篇",
    "ch02": "主体",
    "ch03": "收尾"
  },
  "partOrder": ["ch01", "ch02", "ch03"],
  "slides": [
    { "part": "ch01", "file": "01-cover.html", "title": "封面" },
    { "part": "ch02", "file": "01-topic.html", "title": "主题" }
  ]
}
```

### 2. 创建幻灯片 HTML

在 `slides/<part>/` 下创建 `.html` 文件，每个文件是一个 `<section class="slide">`：

```html
<section class="slide" data-index="0" aria-labelledby="s0-title">
  <div class="slide-head">
    <span class="eyebrow">第1章 · 封面</span>
    <span class="page-chip" aria-label="第 1 页，共 N 页">01 / 0N</span>
  </div>
  <div class="slide-body">
    <h2 id="s0-title" class="slide-title">标题</h2>
  </div>
</section>
```

### 3. 启动服务

```bash
python container/serve.py <target_dir> --theme dark-theme-2
```

脚本从 container/ 目录直接提供骨架文件，同时将 `slides-config.json` 和 `slides/` 路由到目标目录——无需复制任何文件。

指定端口和禁用浏览器打开：

```bash
python container/serve.py <target_dir> --theme light-theme --port 3000 --no-browser
```

可用主题：`dark-theme`、`dark-theme-2`、`light-theme`、`qclaw-theme`

## 配置说明

`slides-config.json` 由 deck.js 在启动时通过 fetch 读取，包含：

| 字段 | 类型 | 说明 |
|---|---|---|
| `title` | string | 页面标题，会设置 `document.title` |
| `parts` | object | 章节映射，key 为章节 id，value 为显示名称 |
| `partOrder` | array | 章节导航顺序 |
| `slides` | array | 幻灯片列表，每项含 `part`、`file`、`title` |

## 功能说明

### 主题切换

页面底部下拉框支持暗色/亮色主题即时切换，切换后立即生效并持久化到 `localStorage`。

### 导出 HTML

点击「导出 HTML」将全部幻灯片合并为单个静态 HTML 文件，支持 `showSaveFilePicker` 原生保存对话框。

### 导出 PPTX

点击「导出 PPTX」通过 html2canvas + pptxgenjs 直接生成 PowerPoint 文件（纯客户端，首次使用自动加载 CDN 依赖）。保底方案见 `internal-skill/html-deck-to-pptx/`。

### 键盘快捷键

| 键 | 操作 |
|---|---|
| ← ↑ | 上一页 |
| → ↓ Space | 下一页 |
| hash 路由 | `#ch03/02-feedback` 或 `#ch03/2` |

## CSS 架构

容器内置 4 套主题，每套均为三层 CSS：

```
container/css/<theme>/
├── tokens.css        # 设计 Token（颜色、字体、圆角、阴影）
├── base.css          # Reset、Shell 布局、幻灯片骨架、导航栏
└── components.css    # 公共组件：卡片、面板、chip、表格、引语框等
```

## 依赖

- 零外部运行时依赖（html2canvas 和 pptxgenjs 在首次导出 PPTX 时从 CDN 按需加载）
- PPTX Python 导出：`pip install playwright python-pptx && playwright install chromium`
