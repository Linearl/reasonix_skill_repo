# html-deck-pipeline-skill

端到端 HTML 讲稿生产流水线 —— 从需求问询到定版归档，输出可独立部署的网站骨架。

## 核心能力

- **六阶段流水线**：A（问询）→ B（架构）→ C（分镜）→ D（生成）→ E（验收）→ F（归档），门禁停顿，不可越级
- **网站骨架输出**：CSS 三层架构 + hash 路由 + 自适应缩放 + 一键导出 HTML/PPTX
- **四主题 + 三字号**：暗色 / 暗色2 / 亮色 / 青律 × 标准 / 高对比 / 大字号，独立切换
- **配置驱动**：`config.yaml` 统一管理主题和字号，新增选项无需改代码

## 目录结构

```text
html-deck-pipeline-skill/
├─ SKILL.md                         # 主流程文档
├─ README.md                        # 本说明
├─ examples/<style-id>/             # 风格资产（style-contract + style-showcase）
├─ references/                      # 规范与门禁参考文档
├─ templates/                       # 初始化模板（init_topic、stage-b）
├─ internal-skill/                  # 内置辅助技能
│  ├─ scrapling-web-fetch/          # 网页抓取
│  ├─ web-style-extraction/         # 风格提取
│  ├─ html-deck-to-pptx/            # PPTX 导出保底方案
│  └─ measure-utilization/          # 页面利用率检测
├─ container/                       # 网站骨架容器
│  ├─ index.html                    # 预览外壳
│  ├─ serve.py                      # 本地开发服务器
│  ├─ js/deck.js                    # 路由/导航/缩放/导出引擎
│  └─ css/
│     ├─ config.yaml                # 主题与字号配置（唯一入口）
│     ├─ common/                    # base.css + components.css（主题共享）
│     ├─ fontsize/                  # 字号方案（standard/high-contrast/large）
│     └─ theme/                     # 主题 tokens（4 套配色）
└─ scripts/                         # 工具脚本
```

## 六阶段流水线

| 阶段 | 名称 | 核心产出 | 门禁 |
| ---- | ---- | -------- | ---- |
| A | 问询与对齐 | 需求冻结快照、风格决策、工作目录 | 用户确认 |
| B | 结构规划 | 总分总结构、版本号、框架文档 | 用户确认 |
| C | 分镜编写 | 全量分镜稿（文案/备注/样式标注） | 质量门禁 + 样式多样性 |
| D | 页面生成 | HTML 页面 + 网站骨架 + 本地预览 | 自查回路 |
| E | 验收发布 | 单文件 HTML + PPTX 定版 | 双向验证 |
| F | 归档总结 | 版本归档、经验沉淀 | 用户确认 |

## 关键约束

1. **阶段顺序强制** — 必须 A→B→C→D→E→F，不得跳过
2. **分镜先行** — 先改分镜再改 HTML，禁止只改 HTML 不改分镜
3. **版本同步** — 分镜、HTML、骨架使用同一版本号（v-01、v-02…）
4. **一页一文件** — 每个 HTML 仅含一个 `<section class="slide">`
5. **定版双输出** — 每次定版同时产出 HTML 和 PPTX，回灌分镜稿
6. **配置驱动** — 主题/字号从 `config.yaml` 读取，JS 动态构建选择器

## CSS 架构

```
```text
加载顺序：tokens.css → fontsize.css → base.css → components.css
                ↑              ↑            ↑            ↑
           css/theme/     css/fontsize/  css/common/  css/common/
          (主题配色)      (字号变量)     (舞台布局)   (组件样式)
```
```

- **tokens.css** — 每个主题一套 CSS 自定义属性（`--bg`、`--text`、`--accent`…）
- **fontsize.css** — 五级字号变量（`--text-xs` ~ `--text-xl`），3 套方案
- **base.css** — 舞台几何、导航、控件样式，4 主题共享
- **components.css** — 面板、卡片、表格、标签等组件，4 主题共享

切换主题仅交换 1 个文件（tokens.css）；切换字号仅交换 1 个文件（fontsize.css）。

## 如何新增配置

编辑 `container/css/config.yaml`：

```yaml
themes:
  - id: new-theme
    label: 新主题
  - id: dark-theme-2
    label: 暗色2
    default: true

fontsizes:
  - id: standard
    label: 标准
    default: true
  - id: xlarge
    label: 超大
```

然后在对应目录下创建 CSS 文件即可，无需修改 JS/HTML。
