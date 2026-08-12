---
name: html-deck-pipeline-skill
description: 端到端 HTML 讲稿流水线技能，适用于”上下文过长””分镜拆分””并行生成””风格控制”等超过 10 页的 HTML 演示任务。采用网站骨架输出模式（CSS 三层架构 + hash 路由 + 自适应缩放），支持一键导出 HTML 和 PPTX。强调分镜先行、风格契约、舞台比例可配置（16:9/4:3/16:10/adaptive）、版本递增与样式多样性。
---
## 目录结构

```text
html-deck-pipeline-skill/
├─ SKILL.md
├─ README.md
├─ examples/
│  └─ <style-id>/
│     ├─ style-contract-<style-id>.md
│     └─ style-showcase-<style-id>.html
├─ references/                 # 流程规范与参考文档（详见目录内）
├─ templates/
│  ├─ init_topic/
│  ├─ stage-b/
│  │  └─ B-framework-vXX.md
├─ internal-skill/
│  ├─ scrapling-web-fetch/       # 网页抓取与分析（内置）
│  ├─ html-deck-to-pptx/         # PPTX 导出保底方案（Playwright 截图）
│  ├─ web-style-extraction/      # 网页风格提取辅助技能
│  └─ measure-utilization/       # 页面空间利用率检测
├─ container/
│  ├─ index.html
│  ├─ slides-config.json
│  ├─ serve.py
│  ├─ js/
│  │  └─ deck.js
│  └─ css/
│     ├─ config.yaml                # 主题与字号配置
│     ├─ common/                    # 共享 base.css + components.css
│     ├─ fontsize/                  # 字号配置（standard/high-contrast/large）
│     └─ theme/                     # 主题 tokens（dark-theme/dark-theme-2/light-theme/qclaw-theme）
├─ scripts/
```

当前阶段聚焦创建与优化，不包含安装、测试、打包或发布。

说明：凡由 `scripts/` 覆盖的任务均为必须脚本执行项；除非脚本报错，不读取脚本源码。

## 流水线概览

六阶段流水线，不可越级、不可跳过、每阶段独立门禁：

| 阶段 | 名称 | 核心产出 |
|---|---|---|
| A：问 | 需求问询与对齐 | 目标、受众、页数范围、风格资产、冻结快照 |
| B：架 | 结构规划与版本初始化 | 总分总结构、版本号、框架文档、目录就绪 |
| C：镜 | 分镜与风格应用 | 全部页面分镜稿（含完整文案、Emoji、样式标注） |
| D：页 | HTML 页面生成与预览 | 分页 HTML、网站骨架构建、本地预览、自查改进 |
| E：验 | 验收与发布 | 导出单文件 HTML/PPTX、用户验收、版本冻结 |
| F：归 | 归档与经验总结 | 版本归档、改动清单、经验沉淀 |

## 何时启用

触发条件与典型场景请使用：`references/09-trigger-matrix.md`。

## 强制约束

> **工具名兼容说明**：本技能中所有 `ask_questions` 均指代 Claude Code 中的 `AskUserQuestion` 工具。若目标执行平台的用户交互工具名称不同，请自动映射为平台实际可用的工具名。

- 必须严格按阶段顺序执行：`A → B → C → D → E → F`；禁止跳过、越级或先做后补。
- 必须先做分镜，再生成 HTML；禁止跳过分镜直接批量写最终页。”先写分镜再补问询””先生成 HTML 再补分镜”均属于失败信号。
- 所有版本必须递增管理（如 `v-01`、`v-02`），禁止覆盖旧版。分镜稿、HTML 页面、网站骨架必须使用同一版本号。
- 用户提出修改意见后，必须先更新下一版分镜，再生成下一版 HTML；禁止只改 HTML 不改分镜。
- HTML 修改后必须同步回写分镜稿的”页面完整文案”；分镜文案与 HTML 观众可见文案必须严格一致。分镜稿中的演讲备注、元标注不得进入 HTML。详见 `references/03-storyboard-spec.md` §2.2.0。
- 分镜稿命名：`{part_no:02d}-{part_name}-分镜稿.md`。HTML 页面存放：`slides/<part_id>/<NN-description>.html`，页面清单由 `slides-config.json` 定义。
- 任一阶段若出现”门禁未过但继续推进”，判定为流程失败，回退到上一个已通过阶段。

## 风格契约创建模式（按需）

默认流程优先复用已有 `style-id`，不进入”新建风格契约”流程。

仅当用户显式要求”新建/重写风格契约”时，才加载：

- `references/08-style-contract-creation-mode.md`
- `references/06-style-contract-authoring-guide.md`
- `references/01-template-pages-standard.md`（style-showcase 模板页规范）

若用户要求”参考某个网站的风格”或”从网页中提取设计元素”，同时加载：

- `internal-skill/web-style-extraction/SKILL.md`（网页风格提取辅助技能）
- `internal-skill/scrapling-web-fetch/SKILL.md`（网页抓取）

## 样式多样性要求

样式多样性门槛与页面模式清单详见：`references/10-style-diversity-rules.md`。

## 全局交互约定

以下约定适用于所有阶段，各阶段不再逐条重复：

- 🗂️ **交互落盘**：每轮结构化交互必须落盘到 `{work_dir}/00-input/comms/`。文件名格式：`{stage_letter}-round{round_no:02d}-{yyyymmdd}.md`（单文件包含本轮交互上下文与 AI 结构化总结）。禁止保留 `YYYYMMDD` 占位文件名。
- ⏸️ **门禁停顿**：每阶段完成后，必须使用 `ask_questions` 暂停，等待用户确认后方可进入下一阶段。未确认前禁止推进。
- 🔁 **阶段收口**：各阶段收口统一使用 `ask_questions` 确认进入下一阶段；交互记录按上述规则落盘。

## 标准流程（分阶段编号）

### 阶段 A：需求问询与对齐（强制交互）

#### ⚠️ 阶段 A 注意事项（强制）

- 🧭 三个动作 **问询 + 确认 + 冻结** 缺一不可；未完成阶段 A，不得进入阶段 B/C/D。
- 📐 必须冻结 `ratio_mode`（默认 `16:9`，可选 `4:3` / `16:10` / `adaptive`），后续阶段不得中途切换。
- 🎨 必须完成风格资产决策：默认选用已有 `style-id`；仅当用户显式要求时进入风格契约创建模式（见 `references/08-style-contract-creation-mode.md`）。
- 🚫 阶段 A 未完成前，禁止初始化目录、写分镜、写 HTML。

#### 🧩 A.0.1 冻结清单（最小必填）

- 阶段 A 冻结快照至少必须包含：`目标`、`受众`、`页数范围`、`ratio_mode`、`风格资产来源`、`交付格式`、`时间约束`。
- 任一字段缺失时，不得判定阶段 A 完成。

#### 🧭 A.0.2 冲突处理优先级（强制）

- 当新需求与已冻结项冲突时，必须按顺序执行：
  1. 标记冲突项（注明冲突字段与冲突原因）；
  2. 输出影响评估（影响页范围、版本影响、返工成本）；
  3. 使用 `ask_questions` 获取用户确认后，才允许修改冻结项。
- 未完成上述三步前，禁止隐式改写冻结项。

#### 🧪 A.0.3 缺失信息默认策略

- 对非核心缺失项可采用默认值推进，但必须在“结构化理解总结”中单列“默认采用项清单”。
- 默认采用项必须可追溯（字段名、默认值、采用原因）；用户若否决，必须回退并重冻。

#### ✅ A.0.4 阶段 A DoD（完成定义）

- 同时满足以下条件才可判定阶段 A 完成：
  1. 冻结清单字段完整；
  2. 交互记录已落盘且文件名为真实日期；
  3. 用户明确确认“可进入阶段 B”。

#### A.1 结构化问询

- 进入 A.1 前，必须先读取：`references/04-stage-a-question-card.md`。
- 需求收集阶段应尽可能使用 `ask_questions` 与用户交互，而不是一次性自由提问。
- 首轮问询目标：一次拿到范围、风格、结构、交付边界、工作目录、舞台比例策略（`ratio_mode`）与并行策略偏好七类信息。
- 首轮问询必须显式确认是否启用 sub-agent 并行加速；默认选项为“不启用”（原因：sub-agent 需要重新加载大量上下文，实际效率未必高于单线程）。
- 首轮问询必须采集“屏幕分辨率（考虑系统缩放后）”信息；至少拿到物理分辨率 + 缩放比例，或浏览器/投屏后的实际可视区尺寸。
- 首轮问询必须显式确认“中间章节组织模式”：`总分总（导航-主体-总结/行动）` 或 `总分（导航-主体）`；默认 `总分总`。
- 固定 checklist 与二轮追问条件详见 `references/04-stage-a-question-card.md`。

#### A.1.1 屏幕一致性建议

屏幕适配的三条具体建议详见 `references/05-interaction-accessibility-baseline.md` §屏幕适配。

#### A.2 输出理解并等待用户确认（强制附加交互）

- 每轮问询结束后，必须输出“我对需求的结构化理解总结”。
- 总结至少覆盖：目标、范围、结构、风格资产、版本策略、工作目录、边界条件。
- 总结中必须单列“中间章节组织模式（总分总 / 总分）”结论。
- 必须要求用户进行二次确认或补充；未确认前不进入下一步。

#### A.3 分析并判断是否仍有未明确项

- 对当前反馈做归类：**已明确 / 部分明确 / 未明确**。
- 满足任一条件即判定“仍有未明确项”：
  - 核心输入缺失（主题、受众、范围、版本号）
  - 工作目录未明确（既无用户指定，也未同意按标准创建）
  - 结构未冻结（总分总中的“分”不清楚）
  - 约束冲突（如页数要求与内容深度冲突）
  - 验收标准不可执行（只有方向，没有检查口径）
  - 风格资产不可执行（未确定选用或新建）

#### A.4 分支执行：二轮询问或初始化并冻结

- 编号与目录结构详见 `references/02-numbering-rules.md`。
- 若**有未明确项**：发起第二轮问询（仅追问未明确项），然后回到 A.2 再次“总结 + 确认”。
- 若**无未明确项且用户明确同意进入下一阶段**：执行以下收尾动作并冻结需求：

  - 初始化目录必须执行脚本（除非脚本报错，不得手工替代）：

```powershell
python scripts/init_topic_folder.py \
  --workspace-root "<workspace_root>" \
  --topic-folder "<topic_folder>" \
  --topic-code "<topic_code>" \
  --topic-title "<topic_title>" \
  --version "v-XX" \
  --style-id "<style_id>" \
  --scheme-name "<scheme_name>" \
  --record-date "YYYYMMDD"
```

- 初始化工作目录（目录结构与编号规则详见 `references/02-numbering-rules.md`）
  - `{work_dir}/00-input/`
  - `{work_dir}/10-storyboards/v-XX/`
  - `{work_dir}/20-html/v-XX/`
  - `{work_dir}/90-tests/`
- 落盘沟通记录：按全局交互约定格式，每轮一个 `{stage_letter}-round{round_no:02d}-{yyyymmdd}.md`。
- 输出并冻结“本轮执行输入快照”（含风格资产路径、工作目录路径、结构冻结结果、`ratio_mode`）
- 阶段 A 未完成上述收尾，不进入阶段 B。

#### A.5 阶段收口确认（强制）

按全局交互约定执行，确认”可进入阶段 B”。未确认前只能继续补充 A 阶段材料，不得开始 B 阶段工作。

### 阶段 B：结构规划与版本初始化

#### ⚠️ 阶段 B 注意事项（强制）

- 📐 阶段 B 必须冻结版本号、总分总结构和章节拆分方案，冻结后不得跨阶段修改。

#### 🧾 B.0.1 版本号与命名规则（强制）

- 阶段 B 必须冻结当前版本号（如 `v-01`）。
- 分镜稿、HTML 页面、网站骨架必须使用同一版本号；若跨文件出现版本号不一致，判定 B 门禁失败。
- 命名必须遵循编号规则：分镜 `{part_no:02d}-{part_name}-分镜稿.md`、HTML 页面 `slides/<part_id>/<NN-description>.html`、网站骨架目录 `v-XX/`。

#### 📁 B.0.2 目录初始化完成清单（强制）

- 阶段 B 进入分镜前，必须确认以下目录/文件已就绪：
  - `{work_dir}/00-input/`（含阶段交互记录）
  - `{work_dir}/10-storyboards/v-XX/`
  - `{work_dir}/20-html/v-XX/`
  - `{work_dir}/90-tests/`
  - `B-framework-v-XX.md`（由模板复制并填充）
- 缺任一项时，不得进入阶段 C。

#### B.1 总分总框架硬约束

- 大章节拆分补充规则与规模经验值详见 `references/11-scope-sizing-and-splitting.md`。
- 演示总体结构必须采用”总分总”。
- 开头章节与结尾章节是必需项，且必须独立存在。
- 中间章节的组织方式（例如按模块、按阶段、按问题域）必须在阶段 A 沟通并冻结。
- 若中间章节组织方式未明确，不得进入分镜生成。
- 参考实践：`11-组内分享/docs/4.01主题开发` 已采用该思路。

#### B.2 拆分方案产出与确认（含大章节补充规则）

- 必须先产出拆分方案与页数估算，并使用 `ask_questions` 与用户确认。
- 在 `ask_questions` 之前，必须先输出”细化到页码级别的规划大纲”（至少包含：页码、所属章节、页面类型、该页核心信息），确保用户有足够信息做决策。
- 用户不认可时必须重拆并再次确认。
- 大章节拆分补充规则、规模经验值与提问模板详见：`references/11-scope-sizing-and-splitting.md`。

#### B.3 框架文档落盘（强制）

- 在 B.2 获得用户确认后，必须通过“复制模板 → 编辑填充 → 落盘”完成框架文档。
- 模板路径（固定）：`templates/stage-b/B-framework-vXX.md`
- 建议路径：`{work_dir}/10-storyboards/v-XX/B-framework-v-XX.md`。
- 框架文档最低包含：
  - 总分总章节清单
  - 章节边界与页数估算
  - 页码级规划大纲（按章节列出）
  - 并行策略与页面组织顺序
  - 用户确认记录摘要（本轮确认结论）
- 复制模板后必须按本轮实际参数替换占位符（主题、版本、style-id、part 映射等）。
- 不允许跳过模板直接手写框架文档。
- 阶段 B 的交互记录必须落盘为 `B-raw...` / `B-summary...`，并作为阶段 C 输入资产。
- 未完成框架文档落盘，不得进入阶段 C。

#### B.4 版本初始化

- 明确当前版本号，例如 `v-01`。
- 确保后续分镜、HTML、风格文件使用同一版本号。

#### B.5 阶段收口确认（强制）

按全局交互约定执行，确认"可进入阶段 C"。

### 阶段 C：分镜编写

阶段 C 聚焦于**内容和结构**，不负责视觉风格决策——视觉由主题 CSS 自动渲染。分镜稿描述”页面上有什么、以什么结构组织”。

#### ⚠️ 阶段 C 注意事项（强制）

- 📄 阶段 C 产出分镜稿（内容 + 结构），不产出 HTML。
- 🎨 视觉风格由主题 CSS 自动处理，分镜稿无需描述颜色、字体、阴影等 CSS 细节。

#### C.1 读取风格资产

- 进入 C.1 前，必须先读取：`references/03-storyboard-spec.md` 与 `references/07-quality-gate-patterns.md`。
- 阶段 C 应参考风格描述文件（`style-contract-<style-id>.md`）和风格展示文件（`style-showcase-<style-id>.html`），了解可用组件类名与布局模式。
- 阶段 C 不负责新建或修改风格契约。

#### C.2 分镜编写

- 分镜稿结构与字段规范详见 `references/03-storyboard-spec.md`。
- 分镜至少包含：**页面目标、页面完整文案、演讲备注**。
- 页面完整文案必须达到”可直接转成 HTML”的密度，禁止只写 1~2 行口号式占位。
- 每页分镜需标注”页面模式类型”（导航页/对比页/流程页/矩阵页/行动页），用于样式多样性校验。
- 分镜需描述”界面元素布局”：明确表格/卡片/流程/提示框等模块的组织关系和信息分工。
- 对比页至少给出 3~4 组对比项；方法页/流程页至少包含结论标题 + 结构化内容块 + 提示框。
- 行动页至少包含：触发条件、关键动作、验收信号。
- 章节导航页与章节总结页均应保留，每页建议 2~4 个信息块。
- Emoji/符号美化在分镜稿中直接写入并冻结，不在 HTML 阶段再补。
- 分镜稿**不需要**描述：CSS 颜色值、字体大小 rem 值、阴影参数、圆角像素、渐变方向——这些由主题 CSS 自动处理。
- 分镜稿应标注所使用的 `style-id`。

#### C.3 分镜质量门禁

- 执行分镜质量门禁检查，详见 `references/07-quality-gate-patterns.md` §1。
- 执行样式多样性检查，详见 `references/10-style-diversity-rules.md`。
- 分镜门禁校验必须执行脚本：

```powershell
python scripts/validate_storyboards_generic.py \
  --storyboards-dir “<storyboards_dir>” \
  --version “v-XX”
```

- `source-coverage-strike.md` 由 AI 生成，并输出覆盖率自评估（默认门禁阈值 70%）。
- 人工审核确认通过后，才允许进入阶段 D。

#### C.4 阶段收口确认（强制）

按全局交互约定执行，总结分镜状态，确认"可进入阶段 D"。

### 阶段 D：HTML 页面生成

阶段 D 将分镜稿转化为实际的 HTML 页面，构建网站骨架并启动本地预览，确保 AI 和用户能即时查看渲染效果。

#### ⚠️ 阶段 D 注意事项（强制）

- 📄 **一页一文件**：每个 HTML 文件只包含一个 `<section class=”slide”>`。
- 📁 **按章节存放**：`slides/<part_id>/<NN-description>.html`。
- 🎨 CSS 由主题自动处理，页面 HTML 不嵌入 `<style>` 块。

#### D.1 生成 HTML 页面

- 进入 D.1 前，必须先读取：`references/19-website-skeleton-spec.md` §8（slide 模板格式）。
- 按分镜逐页生成 HTML 文件，输出到 `slides/<part_id>/<NN-description>.html`。模板格式见 `templates/init_topic/slide_section.html`。
- 每个文件只包含一个 `<section class=”slide”>` 根元素，不含 `<html>`/`<body>`/`<style>`。
- 页面使用 `components.css` 中已有的组件 class（`.panel`、`.card`、`.chip`、`table`、`.quote-box` 等）。
- 页面内容仅保留观众可见信息，演讲备注不进入 HTML。
- 每生成一页 HTML，同步更新 `slides-config.json` 的 `slides` 数组（config 中每项含 `part`、`file`、`title`；`parts` 和 `partOrder` 在阶段 B 已冻结，D 阶段不修改）。模板格式见 `templates/init_topic/slides-config.json`。
- 禁止在 HTML 中出现以下标签文本：`页面模式类型`、`背景呈现策略`、`界面元素布局`、`示例锚点`、`执行约束`、`中间章节组织模式`、`演讲备注`、`过渡句`。
- 禁止在 HTML 中保留仅供生产流程使用的元属性（如 `data-layout`）；最终页面仅保留播放必需属性（如 `data-index`）。
- 若使用 sub-agent 并行生成，派发指令中必须包含并要求优先读取：
  - `style-contract-<style-id>.md`
  - `style-showcase-<style-id>.html`
- sub-agent 产出前必须先回传”已读取文件清单”，未回传不得进入构建环节。
- 可使用 sub-agent 并行生成 HTML 页面，但建议一轮最多启用 **3 个** sub-agent。
- 并行作业提示词与失败回退流程详见：`references/12-parallel-html-generation-playbook.md`。
- 键盘/触屏交互与无障碍基线详见 `references/05-interaction-accessibility-baseline.md`。

#### D.2 构建网站骨架并本地预览（强制）

- 所有页面 HTML 生成完成后，启动预览以便 AI 和用户查看渲染效果：
  1. **确认 slides/ 就绪**：所有页面 HTML 已按 `slides/<part>/<NN-desc>.html` 放好。
  2. **确认 slides-config.json 完整**：title、parts 映射、partOrder、slides 清单均已填入。
  3. **运行启动脚本**：`python container/serve.py <target_dir> --theme <theme_name>`，脚本从 container/ 直接提供骨架文件，同时将 `slides-config.json` 和 `slides/` 路由到目标目录——无需复制任何文件。
- 构建完成后必须执行以下验证：
  - 浏览器打开后首张 slide 正常加载；
  - 键盘导航（ArrowKeys）可正常翻页；
  - 章节导航按钮可正确跳转；
  - Hash 路由正常（`#ch0X/XX-slug`）；
  - `applyAutoScale()` 正常触发，无纵向滚动条；
  - “导出 HTML” 和 “导出 PPTX” 按钮可见且可点击；
  - 主题下拉切换正常。
- 验证失败必须回退修正，不得带病进入 D.3。

#### D.3 自查与改进环节（强制）

- 在 D.2 骨架预览正常运行后，必须执行一次”页面自查回路”。
- D.3 自查重点至少包含：
  - 样式是否美观（视觉层次、对齐、留白、可读性）；
  - 信息密度是否合理（避免”信息过薄”或”单页过载”）；
  - 空白区域是否超标——运行利用率检测脚本量化评估（详见 `internal-skill/measure-utilization/SKILL.md`）：
    ```bash
    python scripts/measure_utilization.py http://localhost:8080 [--threshold 30]
    ```
    脚本通过 Playwright 对每页 slide 执行 40×40 网格采样，检测有效内容（文本/背景/边框/图片等）的占比；利用率低于阈值（默认 30%）的页面将被标记为稀疏（sparse），需调整字号/密度/卡片排布。结果同时支持 `--json` 输出落盘到 `90-tests/<version>/`。
  - 布局多样性是否达标（避免连续同骨架、主导骨架占比过高）；
  - 背景样式是否统一（全稿背景样式类型不超过 3 种，且章节内保持一致）。
- slide 片段不含 `<style>`/`<script>` 标签；components.css 仅含跨章节共享规则。
- 自查必须输出”问题清单（按优先级排序）+ 拟修改方案”。
- **查出问题后，在修改前必须使用 `ask_questions` 获取用户确认**（确认是否修改、先改哪些项、接受的取舍边界）。
- 未获得用户确认前，不得开始修改页面。
- 用户确认后，按确认范围执行修改并复查。
- 自查回路至少执行 1 轮，最多 3 轮；超过 3 轮仍失败，必须暂停并向用户报告阻塞点与备选方案。
- 自查结果建议落盘到 `90-tests/<version>/`。
- CSS 布局问题排查时，务必检查 inherited `display` 属性（尤其是 `display: grid` 对文本宽度的约束），详见 `references/21-css-layout-pitfalls.md`。
- CSS 修改后需硬刷新浏览器（`Ctrl+Shift+R`）或用带时间戳的 URL 验证，避免缓存干扰。

#### D.4 用户反馈与修改

- 自查通过后，使用 `ask_questions` 提示用户在浏览器中查看完整 deck 效果，收集修改意见。
- 用户在 D.4 可直接提出对页面 HTML 的修改要求；AI 必须先更新对应页面 HTML，再进入下一步确认。
- 当用户提出”增加信息密度”时，允许并建议从原稿中提取相关信息补入 HTML，但必须保持与主题边界和风格约束一致。
- 如果用户反馈涉及某章节需要主题 CSS 之外的额外样式，按需在 `v-XX/style/<part_id>.css` 中添加章节样式（使用 `.part-<part_id>` 命名空间，优先使用已有组件和 token 变量）。模板格式见 `templates/init_topic/style_part.css`。
- D.4 提问建议优先复用：`references/18-d4-review-question-card.md`。
- HTML 修改后必须同步回写对应分镜稿的文案（同版本、同页面编号），确保”分镜-HTML”一致。

#### D.5 阶段收口确认（强制）

按全局交互约定执行，确认”可进入阶段 E”。收口仅做确认，不在此环节进行额外修改。

### 阶段 E：构建验收与发布

阶段 E 聚焦于导出静态文件、用户最终验收与版本冻结。网站骨架已在阶段 D.2 构建并启动，阶段 E 不再重复构建。

#### ⚠️ 阶段 E 注意事项（强制）

- 📦 阶段 E 每次执行即代表一次定版，必须同时产出 HTML 和 PPTX 两个文件。

#### E.1 导出与定版（强制）

- 网站骨架已在阶段 D.2 构建并验证，E.1 每次执行即代表一次定版，必须同时产出 HTML 和 PPTX 两个文件。
- **导出 HTML**（单文件静态）：
  - 点击”导出 HTML”按钮或调用 `exportToSingleHTML()` 函数；
  - 生成的文件包含：所有 slide 内联、所有 CSS 内联（tokens + base + components）、最小化键盘导航 JS；
  - 导出文件可脱离服务器直接用 `file://` 协议打开且功能正常（翻页、进度条、自适应缩放均可用）；
  - 导出文件名格式：`{主题}-{版本}.html`，落盘到 `20-html/v-XX/`。
- **导出 PPTX**：
  - 优先使用浏览器端导出：点击”导出 PPTX”按钮或调用 `exportToPPTX()` 函数；
  - **保底方案**：若浏览器端导出失败（如跨域限制、内存不足），使用内置 `internal-skill/html-deck-to-pptx/` 的 Playwright 截图方案——逐页截图后组装 PPTX，详见该子技能的 SKILL.md。
  - 导出文件名格式：`{主题}-{版本}.pptx`，落盘到 `20-html/v-XX/`。
- 导出后必须实际打开 HTML 和 PPTX 文件，验证：
  - 所有页面可正常显示；
  - 键盘翻页正常（HTML）；
  - 无缺失样式或 404 资源请求；
  - 文件体积合理（HTML 通常 < 200KB）。
- 验证失败必须回退到阶段 D 修正，不得跳过。
- **定版后回灌分镜稿（强制）**：HTML 和 PPTX 导出验证通过后，必须以本轮 HTML 的实际最终文案为准，一次性批量回写 `10-storyboards/v-XX/` 下的对应分镜稿，确保分镜稿文案与定版 HTML 严格一致。

#### E.2 Preview → Formal 发布（强制）

- E.1 门禁通过后，产物位于 `20-html/v-XX/` 目录（含 HTML、PPTX 及全部 slides 源文件）。
- 将导出的 HTML 和 PPTX 文件提供给用户进行最终验收。
- 用户验收通过后，将 `20-html/v-XX/` 目录整体作为正式版本冻结。
- 正式版本冻结后，建议至少快检 `100% / 125% / 150%` 三种缩放下的首屏与章节页。

**版本升级（定版后新需求）**：定版冻结后若用户提出新想法或修改需求，视为新版本启动：

1. 确定新版本号（如 `v-03` → `v-04`）。
2. 复制 `20-html/v-{旧版本}/` 全部内容到 `20-html/v-{新版本}/`。
3. 复制 `10-storyboards/v-{旧版本}/` 全部内容到 `10-storyboards/v-{新版本}/`。
4. 启动新版本骨架预览：`python container/serve.py <新版本target_dir> --theme <theme_name>`。
5. 回到阶段 **D.4**（用户反馈与修改）开始新版本迭代——无需重新执行 D.1~D.3（HTML 已从旧版本复制、骨架已验证、自查已通过）。

#### E.3 阶段收口确认（强制）

按全局交互约定执行，确认”本轮收口”或”进入阶段 F 归档总结”。未确认前不得私自启动重构或风格重写。

### 阶段 F：归档与经验总结

#### F.1 版本归档与经验总结（唯一子步骤）

- F.1 必须完成：
  - 版本资产归档（分镜、HTML、测试报告、关键沟通记录）；
  - 本轮总结（改动清单、验证结果、遗留风险、后续建议）；
  - 经验教训总结（可复用做法 / 失误模式 / 下轮规避建议）；
  - 关键文件路径清单与可追溯记录。
- F.1 完成后，必须使用 `ask_questions` 询问用户“是否将经验教训回传到技能目录（`SKILL.md` / `references/`）”。

## 执行与验收附录

- 执行清单：`references/13-run-checklist.md`
- 失败信号与纠偏：`references/14-failure-signals-and-recovery.md`
- 成功判据：`references/15-acceptance-criteria.md`
- 交付原则：`references/16-delivery-principles.md`
- 样式命名规范：`references/17-style-namespacing-rules.md`
- 网站骨架规范：`references/19-website-skeleton-spec.md`
- CSS 布局陷阱与调试经验：`references/21-css-layout-pitfalls.md`
