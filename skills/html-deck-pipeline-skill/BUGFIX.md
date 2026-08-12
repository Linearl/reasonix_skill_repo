# Bug 修复与改进记录

## 2026-05-21：导出 HTML 视口割裂线修复

### 5. 导出 HTML 宽屏视口左右割裂线修复

**现象**：导出的单文件 HTML 在宽屏（>16:9）视口下，deck 左右两侧出现 ~80px 的可见间隙（割裂线）。仅幻灯片 1-6 可见割裂线，7-30 不可见（极具误导性）。

**根因**：导出 CSS 使用"contain"策略——`max-width: calc(100vh * 16 / 9)` 将 deck 约束在视口高度等比宽度内。宽屏时 deck 被居中、两侧留白。ch01 的 slide 背景为纯色渐变（边缘色 `#0a122c`），与 body/shell 背景色（`#050f19`）形成可见对比。ch02+ 的 slide 使用半透明 `--bg-gradient-slide`，间隙仍存在但因半透明混合而肉眼不可见。

**修复**（`container/js/deck.js` `exportToSingleHTML()` 导出 CSS 覆盖块）：

```css
/* 旧版 contain（有间隙） */
.deck { max-width: calc(100vh * 16 / 9); border-radius: 0; box-shadow: none; }

/* 新版 cover（零间隙） */
html, body { background-color: #040812; }
body { background-attachment: scroll; }
.deck { width: max(100vw, calc(100vh * 16 / 9)); height: max(100vh, calc(100vw * 9 / 16)); border-radius: 0; box-shadow: none; max-width: none; }
```

- `width: max(100vw, calc(100vh * 16 / 9))`：宽屏时 deck 撑满宽度，超高时保持 16:9 最小宽度
- `height: max(100vh, calc(100vw * 9 / 16))`：超高时 deck 撑满高度，宽屏时保持 9:16 最小高度
- `overflow: hidden`（shell 上）裁剪溢出方向的多余内容
- `body { background-attachment: scroll }` 修复 `file://` 协议下 `background-attachment: fixed` 渲染失效
- `html, body { background-color: #040812 }` 兜底背景色

### 6. 周边修复

- **页码修复**：导出 HTML 中幻灯片编号重复（如 05/32）→ 修正总页数为 30
- **文件同步**：deck.js 修改同步至 `40.技能改进/html-deck-pipeline-skill-release/`
- **经验回灌**：`references/21-css-layout-pitfalls.md` 新增根因 D（contain vs cover 策略），更新根因 A 交叉引用

---

## 2026-05-18：PPTX 导出 & CSS 渲染修复

### 1. PPTX 导出 SecurityError 修复

**现象**：点击「导出 PPTX」后按钮显示「导出失败」，控制台报 `SecurityError: Must be handling a user gesture to show a file picker`。

**根因**：`showSaveFilePicker()` API 要求在用户手势上下文中调用，但导出流程需遍历全部页面截图（18 页 × 2x 缩放），加上 `pptx.write()` 构建 PPTX，耗时远超用户手势有效期。抛出 `SecurityError` 后，catch 块只静默处理 `AbortError`，其余错误被重新抛出导致整体失败。

**修复**（`container/js/deck.js`）：
- `showSaveFilePicker` 的 catch 块增加 `SecurityError` 静默处理
- 任何 `showSaveFilePicker` 失败（包括 `AbortError`、`SecurityError`）均自动回退到 `<a download>` 下载方式
- `pptx.defineLayout` 的 `height` 参数从字符串 `'7.5'` 改为数字 `7.5`（消除 pptxgenjs 警告）

### 2. 导出图片半透明遮罩修复（经四次迭代）

**现象**：导出的 PPTX 中，部分/全部页面的图片整体呈半透明状态，叠加在白色 PPTX 背景上呈现"蒙雾"效果。且不同页面的遮罩强度不一致。

**根因分析**：透明度来源有两层：

1. slide 级：`--bg-gradient-slide` 包含 `transparent` 停止点（radial-gradient 高光）和 `rgba(..., 0.96)` 的线性渐变
2. 组件级：`.card`、`.panel`、`.quote-box`、`.highlight` 等大量使用 `--surface-glass`（`rgba(255,255,255,0.04)`）等半透明 token

`html2canvas` 忠实保留所有 alpha 通道，产出的 PNG 中几乎所有像素都 alpha < 255。PNG 贴到 PPTX 白色背景上时，半透明深色与白色混合，产生"蒙雾"效果。

不同页面遮罩强度不一的原因：各页面使用的半透明组件密度不同。

**四次迭代过程**：

| 版本 | 方案 | 结果 |
|------|------|------|
| v1 | `backgroundColor: null` | 仅 ch01 后两页明显，封面偶然避过 |
| v2 | `backgroundColor: themeBg`（仅 html2canvas 参数） | 封面以外全有遮罩 |
| v3 | `backgroundColor: themeBg` + `slide.style.backgroundColor = themeBg` | 全部页面都有遮罩 |
| v4 | Canvas 2D 合成：先填充 `themeBg` 实底，再 `drawImage` 合成截图 | 全部页面 100% opaque（已验证） |
| v5 | 临时修改 `slide.style.background` 注入 opaque 色 | 全部页面 0% opaque（回退） |

v1-v3 失败原因：html2canvas 的 `backgroundColor` 仅填充 canvas 背景，不影响元素自身的 CSS `background` 渲染。渐变中的 `transparent` 和 `rgba()` 停止点仍产生 canvas 级透明像素。

v5 失败原因：用 JS 拼接 `background` shorthand（`themeBg + ' ' + bgImage`）后，浏览器和 html2canvas 均不按预期将该颜色作为渐变底层——CSS `background` 多层的 compositing 规则与 Canvas 2D 不同。

**最终修复**（`container/js/deck.js`）：
- html2canvas 保持 `backgroundColor: null` 正常截图
- 截图前移除 auto-scale transform 以确保 canvas 尺寸一致
- 将截图绘制到一个预先填充了主题色 `--bg` 的不透明 canvas 上
- Canvas 2D 的 `drawImage` 会将原图的半透明像素与目标 canvas 的不透明白底做标准 alpha 混合，保证输出完全 opaque
- 全 4 章 slide 验证：raw 100% semi-transparent → composite 100% opaque
- 视觉一致：半透明 alpha 仅 2-4%，合成后肉眼无法分辨色差（合成颜色 ≈ `--bg` 深度方向 ±2 色阶）

### 3. 静态资源缓存优化

**现象**：PPTX 导出时每加载一页 slide，浏览器重新请求全部 10+ 个 CSS 文件，18 页产生 ~200 次冗余请求，严重拖慢导出速度。

**根因**：`serve.py` 未设置 `Cache-Control` 响应头，浏览器无法缓存静态资源。

**修复**（`container/serve.py`）：
- `_serve_from()` 和 `_serve_index_with_config()` 添加 `Cache-Control: public, max-age=3600`
- CSS/JS/字体等静态资源在 1 小时内从浏览器缓存加载，大幅减少导出耗时

### 4. CSS 章节样式恢复

**现象**：v-04 版本的幻灯片样式严重丢失，ch03 等多页布局错乱。

**根因**：v-04 的 `style/ch0X.css` 文件为手工临时创建，缺少 `.part-ch0X` 命名空间和大量精细调校样式。

**修复**：从 v-03 恢复全部 4 个章节 CSS 文件（ch01.css 209 行、ch02.css 109 行、ch03.css 228 行、ch04.css 180 行），包含：
- Cover 带渐变背景、3+2 五环错排（6 列网格）、pillar-row、question-cards、summary-table 等
- Layer cards（五层卡片）、barrel cards、deck-table、cross-path-table、halves-mini-table
- Nav grid、s03-table、step flow、spiral flow、path compare、glass row、tree block、big stats、formula、highlight/quote/tip 覆盖
- Review body、hierarchy stack、stage strip、recap table、halves table、closing quote、data table

---

## 2026-05-14：WYSIWYG 编辑器增强（P0-P3）

详见 [CHANGELOG.md](CHANGELOG.md) v1.1.0 条目。主要包括：

- **P0**：状态提取重构（`editor-state.js`）、撤销/重做系统（`editor-undo.js`）
- **P1**：自定义退出确认对话框（替代原生 confirm）
- **P2**：元素复制、自动化测试套件（106 单元测试 + E2E）、serve.py `--watch` 热重载、主题 token 校验脚本
- **P3**：富文本工具栏（粗体/斜体/下划线/颜色）、图片组件、serve.py 缓存优化
