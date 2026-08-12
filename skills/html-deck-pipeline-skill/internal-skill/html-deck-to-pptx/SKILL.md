---
name: html-deck-to-pptx
description: "将HTML幻灯片演示文稿截图并生成PPTX文件。当用户需要把HTML slides导出为PPT、将HTML演示文稿转成PPTX、对HTML幻灯片逐页截图打包时激活。Convert HTML slide decks to PPTX by screenshotting each slide and assembling into a PowerPoint file. Activates when user needs to export HTML slides to PPT, convert HTML deck to .pptx, screenshot HTML presentation pages."
allowed-tools: Bash
---

# HTML Deck to PPTX | HTML幻灯片转PPTX

## Overview | 概述

将基于HTML的幻灯片演示文稿（通过左右键翻页）逐页截图，然后生成PPTX文件，每页一张截图铺满。

- 使用 Playwright 打开HTML文件并自动翻页截图
- 使用 python-pptx 将截图组装为16:9宽屏PPT
- 支持自定义视口尺寸、总页数、翻页键

## Prerequisites | 前提条件

```bash
pip install playwright python-pptx
playwright install chromium
```

## Important: Timing | 时间间隔注意事项

HTML Deck 的幻灯片切换涉及 CSS 动画（slideFade 220ms）、字体加载、auto-scale 计算和背景渐变渲染，截图过快会截到过渡画面或未就绪状态。

**推荐等待策略：**
1. 导航后等待 `.slide.active` 存在
2. 等待 `getComputedStyle(slide).opacity === '1'`（确保 fade-in 动画完成）
3. 额外等待 500ms（字体渲染 + auto-scale + 背景渐变）
4. 总计每页间隔约 **800-1000ms**

**Playwright 检查代码示例：**
```python
page.wait_for_selector(".slide.active", timeout=10000)
page.wait_for_function("""
    () => {
        const s = document.querySelector('.slide.active');
        if (!s) return false;
        const cs = getComputedStyle(s);
        return cs.opacity === '1' && cs.display !== 'none';
    }
""", timeout=5000)
page.wait_for_timeout(500)  # 字体与渐变渲染余量
```

**html2canvas 的已知局限：**
- CSS `mask-image` 不渲染（deck::before 网格纹理丢失）
- CSS 自定义属性（`var(--bg-gradient-*)`）中的渐变解析不稳定
- 复杂 `linear-gradient` 多色标可能丢失
- 截图画布尺寸可能偏离 16:9，导致 PPTX 拉伸

**推荐：** 优先使用本技能的 Playwright 截图方案（真实浏览器渲染，渐变/mask/伪元素完整保留）；html2canvas 仅作快速预览。

## Workflow Steps | 工作流步骤

### Step 1: 确认参数 | Confirm Parameters

在运行前确认以下信息（可通过读取HTML源码中的JS逻辑自动检测）：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `html_file` | （必填） | HTML幻灯片文件路径 |
| `output_dir` | `<html所在目录>/screenshot` | 截图输出目录 |
| `output_pptx` | `<html所在目录>/<html文件名>.pptx` | PPTX输出路径 |
| `total_slides` | （必填） | 幻灯片总页数 |
| `viewport_width` | 1600 | 视口宽度（16:9 精确比例） |
| `viewport_height` | 900 | 视口高度（16:9 精确比例） |
| `next_key` | ArrowRight | 下一页按键 |
| `selector` | .deck | 截图目标CSS选择器 |
| `quality` | 95 | JPEG质量(1-100) |
| `wait_ms` | 800 | 翻页后等待毫秒数（含动画完成） |

**自动检测总页数**：在HTML源码中搜索 `.slide` 的数量或JS中的 total 变量。

### Step 2: 运行截图脚本 | Run Screenshot Script

使用 `scripts/screenshot_slides.py`：

```bash
python scripts/screenshot_slides.py \
  --html "/path/to/slides.html" \
  --output-dir "/path/to/screenshot" \
  --total 30 \
  --viewport-width 1536 \
  --viewport-height 960 \
  --next-key ArrowRight \
  --selector .deck \
  --quality 95 \
  --wait-ms 300
```

最低限度只需：
```bash
python scripts/screenshot_slides.py --html "/path/to/slides.html" --total 30
```

### Step 3: 运行PPT生成脚本 | Run PPTX Builder

使用 `scripts/create_pptx.py`：

```bash
python scripts/create_pptx.py \
  --screenshot-dir "/path/to/screenshot" \
  --output "/path/to/output.pptx" \
  --total 30 \
  --aspect 16:9
```

最低限度只需：
```bash
python scripts/create_pptx.py --screenshot-dir "/path/to/screenshot" --output "/path/to/output.pptx"
```

### Step 4: 验证输出 | Verify Output

确认：
1. screenshot 目录中有 1.jpg ~ N.jpg，共 N 张
2. PPTX 文件可以正常打开，共 N 页，每页图片铺满

## Troubleshooting | 故障排除

| 问题 | 排查 |
|------|------|
| 截图为白屏/空白 | 增大 `--wait-ms`，或检查 `--selector` 是否匹配正确的容器元素 |
| 截图只截到部分 | 调整 `--viewport-width/height`，或更换 `--selector` 为更大容器 |
| 翻页无效 | 检查 `--next-key` 是否与HTML中的keydown绑定一致 |
| PPT图片变形 | 检查 `--aspect` 是否匹配HTML幻灯片比例（常见 16:9 或 4:3） |
| 找不到.slide元素 | 部分HTML用其他class名，需读取源码确认选择器 |

## References | 参考

- Playwright 文档: https://playwright.dev/python/
- python-pptx 文档: https://python-pptx.readthedocs.io/
