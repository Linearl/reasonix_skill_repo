# Investment Analysis Skill (A股/港股投资分析技能)

<p align="center">
  <strong>🎯 系统化 AI 投研框架 | Systematic AI-Powered Investment Research</strong>
</p>

---

## 📖 概述 | Overview

Investment Analysis Skill 是专为 A 股与港股市场设计的系统化投资研究技能，提供从赛道筛选到择时分析的完整工作流程。通过结构化的提示词模板和跨模型验证机制，帮助投资者更高效地进行投资研究。

The Investment Analysis Skill is a systematic investment research framework designed for both A-share and Hong Kong stock markets, providing a complete workflow from sector selection to timing analysis. Through structured prompt templates and cross-model validation mechanisms, it helps investors conduct investment research more efficiently.

---

## ✨ 核心功能 | Key Features

### 🔍 1. 赛道筛选 (Sector Selection)
利用 AI 的信息广度，结合即将发生的重大事件（会议、政策、季节性因素），识别短期可能爆发的投资方向。

Leverage AI's information breadth to identify short-term opportunity sectors based on upcoming events (conferences, policies, seasonal factors).

### ⛓️ 2. 产业链挖掘 (Supply Chain Analysis)
深入拆解产业链条，找到价值量最高的环节和"铲子股"（通用供应商），避免只关注概念炒作。

Dissect supply chains to identify high-value segments and "picks and shovels" stocks, avoiding pure speculation.

### 📊 3. 深度去伪 (Fundamental Verification)
通过财报和研报验证业务真实性，区分纯概念炒作与实质性业务，评估关键风险因素。

Verify business fundamentals through financial reports, distinguish speculation from real business, and assess key risks.

### 📈 4. 择时分析 (Timing Analysis)
评估市场情绪和当前价格，判断介入时机是否合理，避免追高。

Evaluate market sentiment and current pricing to determine optimal entry points and avoid chasing highs.

### 🔄 5. 跨模型验证 (Cross-Model Validation)
利用不同 AI 模型的优势互补，交叉验证投资逻辑，减少单一模型的偏差和幻觉。

Cross-validate investment thesis using different AI models to reduce bias and hallucinations.

---

## 🚀 快速开始 | Quick Start

### 使用场景 | Use Cases

使用本技能当你需要：
- ✅ 寻找下一个可能爆发的投资主题
- ✅ 深入了解某个行业的供应链结构
- ✅ 验证一家公司的业务是否真实
- ✅ 评估当前介入某只股票是否合适
- ✅ 对比不同 AI 给出的投资建议

Use this skill when you need to:
- ✅ Identify the next potential investment theme
- ✅ Understand supply chain structure of an industry
- ✅ Verify if a company's business is real
- ✅ Evaluate if current timing is right for entry
- ✅ Compare investment recommendations from different AIs

### 推荐模型 | Recommended Models

| 模型 | 适用场景 | 优势 |
|------|---------|-----|
| **DeepSeek** | A/H 股专项分析 | 中文市场理解深入，A/H 股知识丰富 |
| **Gemini Deep Research** | 综合研究 | 网络搜索能力强，信息覆盖广 |
| **ChatGPT** | 通用分析 | 逻辑推理能力强，结构化输出好 |

---

## 📋 提示词模板 | Prompt Templates

### 模板 1：赛道筛选

**目的**：找到短期可能爆发的投资方向

**替换规则**：
- `[当前年份+月份]` → 如 "2026年2月"
- `[未来1-2个月]` → 如 "2026年3-4月"

```text
我正在进行 A 股/港股短期热点研究。请结合[当前年份+月份]的市场环境，以及[未来 1-2 个月]即将发生的重大事件（如行业大会、政策发布、季节性因素），列出最有可能进行热门炒作的 3-5 个板块。

要求：
1) 按重要度和确定性排序
2) 给出每个板块的核心炒作逻辑（Catalyst）
3) 列出该板块对应的 1-2 个代表性龙头股作为参考
```

### 模板 2：产业链挖掘

**目的**：找到产业链中价值量最高的环节和"铲子股"

**替换规则**：
- `[板块名称]` → 如 "人形机器人" / "低空经济" / "固态电池" / "商业航天"

```text
假设我们看好[人形机器人/低空经济/固态电池/商业航天]板块。请像一个专业的行业分析师一样，帮我拆解这个产业的核心供应链：

1) 哪些环节价值量最高？（例如：丝杠、传感器、电池材料）
2) 针对每个核心环节，A 股/港股目前的绝对龙头分别是谁？
3) 有没有那种"铲子股"（不管谁赢，都需要用它的产品）？
```

### 模板 3：财报验证

**目的**：验证公司业务真实性，区分概念炒作与实质业务

**替换规则**：
- `[公司名]` → 如 "优必选" / "小鹏汽车"
- `[业务类型]` → 如 "机器人" / "AI" / "商业航天"

**使用方式**：配合上传财报或研报文件

```text
请仔细阅读这份[公司名]的财报/研报：

1) 这家公司的[机器人/AI/商业航天]业务是纯概念炒作，还是已经有实质性收入？收入占比多少？
2) 报告中是否提到了具体客户（如特斯拉、华为）或明确的量产时间表？
3) 作为投资者，你认为这份报告中最大的风险点是什么？
```

### 模板 4：择时分析

**目的**：评估当前介入时机是否合理

**替换规则**：
- `[公司名1]`、`[公司名2]` → 如 "三六零" / "科大讯飞"
- `[描述走势]` → 如 "一波大涨后的回调" / "连续三个月横盘整理"

```text
[公司名1]、[公司名2]在过去两个月已经经历了[描述走势，如：一波大涨后的回调]。结合当前的市场情绪，现在介入是否属于追高？
```

### 模板 5：跨模型验证

**目的**：用不同 AI 模型交叉验证，避免单一模型偏差

**替换规则**：
- `[股票A]`、`[股票B]` → 如 "宁德时代" / "比亚迪"

```text
有人建议我关注[股票A]和[股票B]作为该板块的龙头。

1) 你是否认同？如果不认同，请给出理由
2) 你的推荐列表中为什么没有这两只？
3) 还有没有被它忽略的、但在供应链中不可或缺的公司？
```

---

## 🔄 标准工作流程 | Standard Workflow

```
赛道筛选（Step1）
    ↓
产业链挖掘（Step2）
  ↓
┌──────────────────────────────────────┐
│ 商品周期定位（Step2.5，资源股必做）  │
│ └─ 供需基本面+周期四阶段识别         │
└──────────────────────────────────────┘
  ↓
┌──────────────────────────────────────┐
│ 财报验证（Step3a/b/c）               │
│ ├─ Step3a：财报获取 [自动]          │
│ ├─ Step3b：内容提取 [自动]          │
│ └─ Step3c：深度分析 [AI+人工] ⭐    │
└──────────────────────────────────────┘
  ↓
┌──────────────────────────────────────┐
│ 产业链验证（Step3.5，可选但推荐）    │
│ └─ 财报+新闻反向验证供应链           │
└──────────────────────────────────────┘
  ↓
┌──────────────────────────────────────┐
│ 地缘风险评估（Step3.6，资源股必做）  │
│ └─ 供应链+客户+资产地缘+去全球化重估 │
└──────────────────────────────────────┘
  ↓
┌──────────────────────────────────────┐
│ 新闻事件分析（Step4a/b/c）           │
│ ├─ Step4a：新闻搜索 [自动]          │
│ ├─ Step4b：分类标注 [AI+人工]       │
│ └─ Step4c：冲突检查 [混合]          │
└──────────────────────────────────────┘
  ↓
┌──────────────────────────────────────┐
│ 技术面与入场（Step5a/b/c）           │
│ ├─ Step5a：数据计算 [自动]          │
│ ├─ Step5b：趋势评估 [AI+人工]       │
│ └─ Step5c：决策执行 [人工] ⭐      │
└──────────────────────────────────────┘
  ↓
┌──────────────────────────────────────┐
│ 研报交叉验证（Step6a/b/c，BUY股必做）│
│ ├─ Step6a：研报检索下载 [半自动]    │
│ ├─ Step6b：研报分析对比 [AI+人工]   │
│ └─ Step6c：最终推荐更新 [人工] ⭐  │
└──────────────────────────────────────┘
  ↓
┌──────────────────────────────────────┐
│ 多视角反思（Step7a/b/c，最终决策必做）│
│ ├─ Step7a：跨模型质疑 [AI+人工]    │
│ ├─ Step7b：对抗性反思 [人工]       │
│ └─ Step7c：最终信心校准 [人工] ⭐⭐ │
└──────────────────────────────────────┘
  ↓
跨模型验证（Bonus，关键步骤）
```

### 详细流程说明

#### **Step1 - 赛道筛选 (Sector Selection)**
- **输入**：时间窗口（如 2026年Q1）、即将发生的事件
- **输出**：3-5个潜力赛道 + 每个赛道的核心催化逻辑 + 代表龙头股
- **文件**：`step1/01_赛道筛选_YYYYQx_A股或港股潜在爆发行情.md`
- **推荐模型**：DeepSeek + Gemini Deep Research

#### **Step2 - 产业链挖掘 (Supply Chain Analysis)**
- **输入**：Step1的赛道清单
- **输出**：每个赛道的供应链分析 + 标的清单YAML
- **文件**：`step2/02A~02E_产业链挖掘_*.md` + `step2/02_标的清单.yaml`
- **分析重点**：价值量最高处、A股/港股龙头、"铲子股"、竞争格局
- **标的清单字段**：`name`、`track`、`code`、`market`
  - A股：`market: A`，`code`=6位
  - 港股：`market: HK`，`code`=5位（前导0保留）

#### **Step2.5 - 商品周期定位 (Commodity Cycle Positioning, 资源股必做)**
- **输入**：Step2产业链 + 行业供需数据
- **输出**：周期阶段判断 + 投资窗口 + 风险触发点
- **文件**：`step2.5/02.5_商品周期定位_YYYYQx.md`
- **关键判断**：周期阶段（1-4）、价格/产能/库存共振、避免高位接飞刀

#### **Step3a - 财报获取 (Financial Report Download) [自动化]**
- **输入**：Step2的标的清单YAML
- **流程**：自动从巨潮资讯下载年报和季报PDF（仅A股）
- **输出**：`step3/financials/{代码_名称}/` 目录中的PDF文件
- **工具**：`step3/tools/step3a_download_reports.py`
- **港股说明**：从 HKEXnews 或公司IR页面手动下载年报/中报/季报，放入同一目录结构

#### **Step3b - 财报内容提取 (Content Extraction) [自动化]**
- **输入**：Step3a下载的PDF文件
- **流程**：自动提取关键信息（产品分类、客户、订单、风险因素）
- **输出**：`step3/extracts/{代码_名称}_annual_extract.txt` 等结构化文本
- **工具**：`step3/tools/step3b_extract_content.py`

#### **Step3c - 财报分析 (Financial Analysis) [全AI自动] ⭐**
- **输入**：Step3b提取的内容
- **流程**：AI自动分析业务真实性、提取关键风险、生成评分和建议
- **输出**：逐股分析报告 + `step3/report/03_汇总_结论表.md`
- **优势**：
  - ✅ 一致性：对所有股票应用相同的分析标准
  - ✅ 高效率：可并行处理10-100+只股票，数分钟完成
  - ✅ 完整性：不存在人工遗漏或疲劳偏差
  - ✅ 可追溯：所有结论都有具体证据支撑

#### **Step3.5 - 产业链验证 (Supply Chain Verification) [可选但推荐]**
- **输入**：Step2假设供应链 + Step3c财报分析 + Step4新闻
- **流程**：反向验证 Step2 中的产业链关系是否真实存在
- **输出**：`step3.5/report/03.5_供应链验证表.md` + 风险地图
- **检查重点**：
  - ✅ 供应关系有没有在财报中被证实？
  - ✅ 是否存在新兴竞争对手或替代方案？
  - ✅ 有没有"单点风险"（关键公司失败整链崩溃）？

#### **Step3.6 - 地缘风险评估 (Geopolitical Risk, 资源股必做)**
- **输入**：Step3c结果 + 海外供应/客户/资产信息
- **输出**：地缘风险评分 + 仓位上限建议
- **文件**：`step3.6/03.6_地缘风险评估_YYYYQx.md`

#### **Step4a - 新闻搜索 (News Collection) [自动化]**
- **输入**：标的清单
- **流程**：自动搜索CNINFO公告（仅A股）、新闻网站、事件日历（过去30-60天）
- **输出**：`step4/raw_data/` 目录中的原始新闻数据
- **工具**：`step4/tools/step4a_search_news.py`
- **港股说明**：公告建议从 HKEXnews 拉取或手工补录到同一YAML

#### **Step4b - 新闻分类 (Classification & Tagging) [AI + 人工]**
- **输入**：Step4a搜索的原始新闻
- **流程**：AI初步分类 + 人工验证 → 标注为正面催化/负面风险/中性/无关
- **输出**：`step4/classified/` 目录 + `step4/report/04_汇总_新闻分类表.md`
- **关键字段**：日期、分类、影响级别、预期兑现时间

#### **Step4c - 新闻-技术面冲突检查 (Conflict Detection)**
- **输入**：Step4b分类新闻 + Step5a技术数据
- **流程**：对比新闻催化与股价走势，检测不匹配情况
  - 大利好宣布但股价未涨 → 为什么？
  - 股价已涨50%但催化还在1个月后 → 过热风险？
- **输出**：`step4/report/04_汇总_新闻与事件表.md`

#### **Step5a - 技术数据获取 (Data Collection) [自动化]**
- **输入**：标的清单
- **流程**：自动获取120个交易日的历史数据，计算MA、高低点、波动率
- **输出**：`step5/raw_data/{代码_名称}_technical_data.csv`
- **工具**：`step5/tools/step5a_fetch_technical_data.py`

#### **Step5b - 趋势分析 (Trend Analysis) [AI + 人工]**
- **输入**：Step5a技术数据 + Step4c新闻催化 + Step3c基本面评分
- **流程**：
  - 评估趋势：短期/中期/长期走势？
  - 识别支撑/压力：在哪些位置容易反弹/回调？
  - 交叉验证：技术面是否与基本面和新闻逻辑一致？
- **输出**：`step5/analysis/05_{赛道}_{代码}_{名称}_technical.md` + 信号汇总表

#### **Step5c - 入场决策 (Entry Decision) [人工] ⭐**
- **输入**：所有前面步骤的分析
- **流程**：综合评分决策
  - 基本面好吗？(Step3c评分)
  - 有没有催化？(Step4c时间线)
  - 技术面支持吗？(Step5b信号)
  - 供应链靠谱吗？(Step3.5确定度)
- **输出**：`step5/report/05_汇总_介入策略表.md`
- **最终建议**：推荐买入/观望/规避 + 入场价格 + 止损位 + 目标价

#### **Step6 - 研报交叉验证 (Research Report Cross-Validation, BUY股必做)**
- **输入**：Step5c的BUY标的
- **流程**：检索券商研报 → 对比观点 → 更新推荐与风险触发
- **输出**：`step6/report/06_最终推荐(研报验证后).md`

#### **Step7 - 多视角反思 (Multi-Perspective Reflection, 最终决策必做)**
- **输入**：Step6更新后推荐
- **流程**：跨模型质疑 → 对抗性反思 → 最终信心校准
- **输出**：`step7/final/07_执行摘要.md` + `07_投资论证(一页纸).md`

#### **跨模型验证 (Cross-Model Validation) - 可选但推荐**
- **何时使用**：在关键决策点（特别是Step1、Step2、Step5c）
- **方法**：用DeepSeek/Gemini/ChatGPT分别分析，对比结果
- **收益**：减少单个模型偏差，提高置信度

### ✅ Checklist使用建议
- 开始前从 `invest_analysis/templates/checklist.md` 复制到工作目录
- 每完成一个步骤，更新对应checkbox与关键发现
- 每个阶段结束进行milestone检查，确保质量达标

---

## 📁 输出目录结构 | Directory Structure

运行完整工作流后，你的项目目录应该看起来如下：

```
project_root/
│
├── step1/                          # Step1 输出：赛道筛选
│   └── 01_赛道筛选_YYYYQx_*.md
│
├── step2/                          # Step2 输出：产业链挖掘
│   ├── 02A_产业链挖掘_赛道1_YYYYQx.md
│   ├── 02B_产业链挖掘_赛道2_YYYYQx.md
│   └── 02_标的清单.yaml            # ⭐ 关键输入文件（给Step3/4/5使用）
│
├── step2.5/                         # Step2.5 输出：商品周期定位（资源股必做）
│   └── 02.5_商品周期定位_YYYYQx.md
│
├── step3/                          # Step3 输出：财报验证
│   ├── financials/                 # Step3a 生成：PDF下载目录
│   │   ├── 000001_平安银行/
│   │   │   ├── 2025_annual_report.pdf
│   │   │   └── 2025_Q3_quarterly_report.pdf
│   │   └── 000858_五粮液/
│   │       ├── 2025_annual_report.pdf
│   │       └── ...
│   │
│   ├── extracts/                   # Step3b 生成：提取的内容
│   │   ├── 000001_平安银行_annual_extract.txt
│   │   ├── 000001_平安银行_quarterly_extract.txt
│   │   └── extraction_index.yaml
│   │
│   ├── analysis/                   # Step3c 生成：分析报告
│   │   ├── 03_银行_000001_平安银行.md
│   │   ├── 03_银行_000858_五粮液.md
│   │   └── ...
│   │
│   └── report/
│       └── 03_汇总_结论表.md       # Step3c 生成：汇总评估
│
├── step3.5/                        # Step3.5 输出：产业链验证 [可选]
│   ├── analysis/
│   │   └── 03.5_供应链验证_*.md    # 验证供应关系
│   │
│   └── report/
│       ├── 03.5_供应链验证表.md     # 验证结果汇总
│       └── 03.5_供应链风险地图.md   # 风险识别
│
├── step3.6/                        # Step3.6 输出：地缘风险评估（资源股必做）
│   └── 03.6_地缘风险评估_YYYYQx.md
│
├── step4/                          # Step4 输出：新闻与事件
│   ├── raw_data/                   # Step4a 生成：原始新闻
│   │   ├── 000001_平安银行_news_raw.yaml
│   │   └── news_index.yaml
│   │
│   ├── classified/                 # Step4b 生成：分类新闻
│   │   ├── 000001_平安银行_news_classified.yaml
│   │   └── ...
│   │
│   ├── analysis/
│   │   └── 04_新闻技术面冲突分析.md
│   │
│   └── report/
│       ├── 04_汇总_新闻分类表.md   # Step4b 生成
│       └── 04_汇总_新闻与事件表.md # Step4c 生成
│
├── step5/                          # Step5 输出：技术面与入场策略
│   ├── raw_data/                   # Step5a 生成：技术数据
│   │   ├── 000001_平安银行_technical_data.csv
│   │   └── technical_index.yaml
│   │
│   ├── analysis/                   # Step5b 生成：趋势分析
│   │   ├── 05_银行_000001_平安银行_technical.md
│   │   └── ...
│   │
│   └── report/
│       ├── 05_汇总_技术信号表.md    # Step5b 生成
│       └── 05_汇总_介入策略表.md    # Step5c 生成 ⭐ 最终推荐
│
├── step6/                          # Step6 输出：研报交叉验证（BUY股必做）
│   ├── analysis/
│   │   └── 06_*_研报交叉验证.md
│   └── report/
│       └── 06_最终推荐(研报验证后).md
│
├── step7/                          # Step7 输出：多视角反思与最终决策
│   └── final/
│       ├── 07_执行摘要.md
│       ├── 07_投资论证(一页纸).md
│       └── 07_最终组合配置.md
│
└── tools/                          # [可选] 自动化脚本
    ├── step3a_download_reports.py
    ├── step3b_extract_content.py
    ├── step3.5_supply_chain_verify.py
    ├── step4a_search_news.py
    ├── step4b_classify_news.py
    └── step5a_fetch_technical_data.py
```

### 关键输入/输出文件

| 文件 | 生成步骤 | 用途 |
|------|---------|------|
| `step2/02_标的清单.yaml` | Step2 | ⭐ 关键：Step3/4/5都需要读取这个文件 |
| `step2.5/02.5_商品周期定位_YYYYQx.md` | Step2.5 | 资源股周期定位与风险窗口 |
| `step3/report/03_汇总_结论表.md` | Step3c | 基本面评估结果，Step5c需要 |
| `step3.5/report/03.5_供应链验证表.md` | Step3.5 | 产业链置信度评分，Step5c参考 |
| `step3.6/03.6_地缘风险评估_YYYYQx.md` | Step3.6 | 资源股地缘风险与仓位上限 |
| `step4/report/04_汇总_新闻与事件表.md` | Step4c | 催化催物和时间线，Step5c需要 |
| `step5/raw_data/` | Step5a | 技术数据CSV，Step5b/c需要 |
| `step5/report/05_汇总_介入策略表.md` | Step5c | **最终推荐**：买入/观望/规避 |
| `step6/report/06_最终推荐(研报验证后).md` | Step6c | 研报交叉验证后的更新结论 |
| `step7/final/07_执行摘要.md` | Step7c | 最终执行摘要（最高优先级） |
| `templates/checklist.md` | 模板 | 阶段性产出追踪与质量检查 |

---

## ⚠️ 重要提示 | Important Disclaimers

### 风险警示

- ❌ **本技能不构成投资建议**
- ❌ **AI 可能产生幻觉或提供过时信息**
- ❌ **务必通过官方渠道验证所有信息**
- ❌ **市场有风险，入市需谨慎**

### 最佳实践

- ✅ 将 AI 作为研究助手，而非决策者
- ✅ 始终进行独立尽职调查
- ✅ 使用多个模型交叉验证
- ✅ 验证所有关键信息的来源
- ✅ 了解自己的风险承受能力

---

## 📚 学习资源 | Resources

### 推荐数据源

- **东方财富网** (eastmoney.com): A 股行情、财报数据
- **巨潮资讯网** (cninfo.com.cn): 官方信息披露平台
- **同花顺** (10jqka.com.cn): 财经资讯、研报
- **Wind 终端**: 专业金融数据库

### 补充阅读

- 《证券分析》(Benjamin Graham)
- 《聪明的投资者》(Benjamin Graham)
- 《投资最重要的事》(Howard Marks)

---

## 🤝 贡献 | Contributing

欢迎提交改进建议和使用案例！

Contributions and use cases are welcome!

---

## 📜 许可证 | License

MIT License - 详见 [LICENSE](../LICENSE)

---

<p align="center">
  <strong>⚠️ 市场有风险，投资需谨慎 | Markets Carry Risks - Invest Wisely</strong>
</p>

<p align="center">
  <em>本技能仅供学习研究使用，不构成任何投资建议</em><br>
  <em>This skill is for educational and research purposes only, not investment advice</em>
</p>
