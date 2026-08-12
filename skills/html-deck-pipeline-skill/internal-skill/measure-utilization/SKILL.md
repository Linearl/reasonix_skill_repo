---
name: measure-utilization
description: 测量 HTML 演示文稿每页的空间利用率，找到过于空旷的页面。使用 Playwright 渲染 + 网格采样方法。当用户想检查页面密度、找空白页面、优化页面布局或询问"空间利用率"时使用。
---

# 空间利用率测量

对 HTML 演示文稿（如 Harness Deck）的每一页，用 Playwright headless Chromium 渲染后网格采样，通过 `elementFromPoint` 检测每个采样点是否命中有意义内容（有背景/边框/文字的元素，排除透明容器 div），计算空间利用率。

## 运行方式

```bash
python "<workspace>/.github/skills/html-deck-pipeline-skill/internal-skill/measure-utilization/_measure_utilization.py" <path/to/deck.html> [--threshold 30] [--json] [--parts parts.json]
```

- `html`：HTML 讲稿文件路径（必填）
- `--threshold` / `-t`：利用率阈值（%），低于该值标记为 `<<<`。默认 30%
- `--json`：输出原始 JSON 而非格式化报告
- `--parts`：可选的 JSON 文件，定义幻灯片章节分组，格式见下方说明

### 示例

```bash
# 基本用法
python "_measure_utilization.py" 20-html/v-01/DECK-HARNESS-合并.html

# 指定阈值
python "_measure_utilization.py" 20-html/v-01/DECK-HARNESS-合并.html -t 25

# 带章节分组
python "_measure_utilization.py" 20-html/v-01/DECK-HARNESS-合并.html --parts parts.json

# JSON 输出（供其他脚本消费）
python "_measure_utilization.py" 20-html/v-01/DECK-HARNESS-合并.html --json
```

### 章节分组文件格式 (--parts)

```json
[
  {"name": "ch01-问题", "start": 0, "end": 2},
  {"name": "ch02-body", "start": 3, "end": 5},
  {"name": "ch03-五维展开", "start": 6, "end": 17},
  {"name": "ch04-总结", "start": 18, "end": 20}
]
```

- `name`：章节名称
- `start`：该章节第一页的索引（从 0 开始）
- `end`：该章节最后一页的索引

不提供 `--parts` 时，报告中不显示章节列，结果仍然有效。

## 测量方法

1. **逐页渲染**：Playwright 打开 HTML 文件，每次只显示一页（`display:flex`）
2. **网格采样**：40×40 网格（1600 个采样点）均匀覆盖整个 slide
3. **内容判定**：每个采样点用 `elementFromPoint(x, y)` 获取顶层元素，沿 DOM 树向上查找，检查是否存在有意义的元素：
   - 有非透明背景色
   - 有可见边框
   - 是内容标签（h1-h6, p, table, img, code, pre, blockquote, button, strong, em 等）
   - 是包含文字的叶子节点且非纯布局标签（div, section, span 等）
4. **利用率计算**：命中内容的采样点 / 总采样点 × 100%

## 结果解读

```
  # |  Util | Flag | Part               | Slide Title
----------------------------------------------------------------------------------------------------
  6 | 17.9% |  <<< | ch03-五维展开[0]    | 📋 五个方案维度
  0 | 21.1% |  <<< | ch01-问题[0]        | 封面
 10 | 31.5% |      | ch03-五维展开[4]    | 信息压缩
  ...
  5 | 65.7% |      | ch02-body[2]        | 约束层 vs 认知层
```

- `< 30%`：标记为 `<<<`，页面严重偏空
- `30-50%`：中等利用率，有优化空间
- `50-65%`：良好利用率
- `> 65%`：密集页面（演示文稿中通常不希望超过 70%，会显得拥挤）

**注意**：封面/导航/章节分隔页通常利用率偏低（10-25%），这是设计预期，不算问题。

## 脚本位置

测量脚本位于本技能目录：`_measure_utilization.py`

## 依赖

- `playwright`（需 `pip install playwright && playwright install chromium`）

## 输出格式要点

- 结果按利用率从低到高排序
- 显示页码（整体索引）、所属章节、章节内页码（提供 `--parts` 时）
- 稀疏页面统计 + 设计豁免提示
