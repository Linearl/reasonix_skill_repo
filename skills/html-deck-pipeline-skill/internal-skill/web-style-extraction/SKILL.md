# 网页风格提取辅助技能

> 触发条件：当用户要求"参考某个网站的风格做 deck"、"照着 XX 网站的配色做"、"学习这个网页的视觉风格"时启用。
>
> 本技能是 `html-deck-pipeline-skill` 的子技能，不单独使用。

## 定位

从参考网站中提取视觉设计特征，产出可被 `style-contract` 和 `style-showcase` 直接使用的结构化设计参数。

## 前置依赖

- 网页抓取能力：`internal-skill/scrapling-web-fetch/SKILL.md`
- 风格契约编写规范：`references/06-style-contract-authoring-guide.md`

## 网页抓取策略

当需要补充官网、文档站、文章、列表页、详情页等网页资源时，使用内置 scrapling 技能完成"网页抓取 → 内容清洗 → 结构化提取 → 证据落盘"，减少反复人工审批与逐页确认次数。

### 触发条件

命中以下任一信号时必须切换到 scrapling：批量抓取、列表页递归详情页、401/403、登录限制、Cloudflare、动态渲染、滚动加载、证据链采集。

若只是单个公开静态页面且无需批量抓取，可沿用内置网页读取；一旦出现阻断或需要过程资产，立即回到 scrapling 流程。

## 工作流程

### 1. 抓取参考网站

使用 scrapling 抓取目标网站的关键页面（首页、列表页、详情页），保存为 HTML + 截图：

```bash
python internal-skill/scrapling-web-fetch/scripts/fetch_page.py --url <url> --output process-assets/html/
```

至少抓取 2-3 个页面以覆盖不同页面类型。

### 2. 提取设计 Token

从抓取的 HTML 中提取以下信息：

| 类别 | 提取内容 | 对应 Token |
|------|---------|-----------|
| **配色** | 背景色、文字色、强调色、边框色、阴影 | `--bg`, `--text`, `--accent`, `--border`, `--shadow` |
| **字体** | 字体族、标题/正文字号阶梯、字重 | `--font-main`, `--font-code`, `--text-base`, `--text-hero` |
| **间距** | 内边距、卡片间距、章节间距 | `--panel-pad`, `--space-section` |
| **圆角** | 按钮、卡片、面板的 border-radius | `--radius-sm`, `--radius-md`, `--radius-lg` |
| **组件** | 卡片样式、表格样式、标签/chip 样式、引用样式 | components.css 规则 |

### 3. 生成风格资产

基于提取的 Token 生成两个文件：

**style-contract-{style-id}.md**：描述设计决策、配色体系、字体策略、组件约束、禁止项。

**style-showcase-{style-id}.html**：7 页风格展示页（封面、导航、流程、证据、对比、行动、收口），使用提取的 Token 渲染。

### 4. 注册风格

将生成的文件放入 `examples/{style-id}/`：
- `examples/{style-id}/style-contract-{style-id}.md`
- `examples/{style-id}/style-showcase-{style-id}.html`

## 提取模板

### 配色提取

从页面主要区域采样至少 5 个关键颜色：

```
背景基色 → --bg
卡片/面板背景 → --panel / --surface-1
主文字色 → --text
次要文字色 → --text-sec / --muted
主强调色（链接/按钮/高亮）→ --accent / --brand
语义色（成功/警告/危险，如有）→ --ok / --warn / --risk
边框色 → --border / --line
阴影 → --shadow
```

### 字体提取

从 `<body>` 和内联样式提取字体栈，从标题/正文对比中估算字号阶梯比例。

### 组件模式识别

- 卡片：是否有边框？是否有阴影？圆角多大？
- 表格：是否有斑马纹？表头样式？
- 标签/Chip：是否为胶囊形？有无边框？
- 导航：顶部固定还是侧边？有无背景模糊？

## 质量门禁

- [ ] 所有 Token 有明确的来源页面和元素
- [ ] 配色不依赖猜测——每个颜色都从实际 DOM/CSS 中提取
- [ ] style-showcase 渲染后与参考网站的视觉一致性 ≥ 70%
- [ ] style-contract 和 style-showcase 成对存在
