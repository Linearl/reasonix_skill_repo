---
name: invest_analysis
description: "Systematic investment research workflow for A-share and Hong Kong stock markets using AI-powered analysis. Use when conducting sector selection, supply chain analysis, financial report verification, or market sentiment evaluation. 系统化的 A 股/港股投资研究工作流程，适用于赛道筛选、产业链分析、财报验证和市场情绪评估。"
---

# Investment Analysis Skill (A股/港股投资分析技能)

## Overview

This skill provides a systematic AI-powered investment research framework designed for both A-share and Hong Kong stock markets. It helps investors identify promising sectors, analyze supply chains, verify business fundamentals, and evaluate market timing through structured prompts and cross-model validation.

本技能为 A 股与港股市场分析提供系统化的 AI 投研框架，帮助投资者通过结构化的提示词和跨模型验证，识别潜力赛道、分析产业链、验证业务真实性并评估市场时机。

## When to Use

Use this skill when you need to:
- Identify emerging sectors based on upcoming events and policies (赛道筛选)
- Analyze supply chain structure and identify key players (产业链挖掘)
- Verify company fundamentals through financial reports (深度去伪)
- Evaluate market sentiment and timing (择时分析)
- Cross-validate investment thesis across different AI models (交叉验证)

适用场景：
- 基于即将到来的事件和政策识别新兴赛道
- 分析供应链结构并识别关键参与者
- 通过财报验证公司基本面
- 评估市场情绪和介入时机
- 跨 AI 模型交叉验证投资逻辑

## Core Workflow

This skill implements a comprehensive multi-phase workflow for systematic investment research:

### 🚀 Project Initialization (开始前必做)

**Before starting any analysis, complete the following setup**:

1. **Create Project Directory**:
   ```powershell
   # Create project folder with descriptive name
   New-Item -ItemType Directory -Path "AI芯片_2026Q1"
   cd "AI芯片_2026Q1"
   
   # Create all subdirectories
   @('step1', 'step2', 'step2.5', 'step3', 'step3/financials', 'step3/extracts', 
     'step3/analysis', 'step3/report', 'step3.5', 'step3.5/verify', 'step3.5/report',
     'step3.6', 'step4', 'step4/raw_data', 'step4/classified', 'step4/analysis', 
     'step4/report', 'step5', 'step5/raw_data', 'step5/analysis', 'step5/report',
     'step6', 'step6/reports', 'step6/analysis', 'step6/report', 
     'step7', 'step7/analysis', 'step7/reflection', 'step7/final') | 
   ForEach-Object { New-Item -ItemType Directory -Path $_ -Force }
   ```

2. **Copy Checklist Template**:
   ```powershell
   # Copy from skill templates directory to project root
   Copy-Item "../invest_analysis/templates/checklist.md" -Destination "." 
   
   # Open checklist and fill in project info
   code checklist.md
   ```

3. **Initialize Checklist**:
   - Fill in project name, date, analyst name
   - Review directory structure
   - Mark "目录创建完成" checkbox

**⚠️ Critical**: The checklist is your single source of truth for tracking progress. Update it after EVERY step completion.

---

### Phase 1: Sector Selection (Step1 - 赛道筛选)

**Objective**: Use AI's information breadth to identify short-term opportunity sectors based on upcoming events (conferences, policies, seasonal factors).

**Process**:
1. Gather context about current market environment
2. Identify upcoming catalysts (1-2 months outlook based on conferences, policies, seasonal events)
3. Rank 3-5 sectors by importance and certainty
4. Extract core investment thesis (催化逻辑) for each sector
5. Identify 1-2 leading stocks as references per sector

**Output**:
- Document: `01_赛道筛选_YYYYQx_A股或港股潜在爆发行情.md`
- Directory: `step1/`

**Checkpoints**:
- ✅ Is the catalyst source明确?
- ✅ Are representative leading stocks provided?
- ✅ Is the ranking logic explained?

**Recommended Models**: DeepSeek, Gemini Deep Research, ChatGPT

**📋 Checklist Update**: After completing Step1, update `checklist.md`:
- ✅ Mark Step1 file as complete
- Fill in "关键发现" (筛选赛道, 核心催化, 时间窗口)
- Mark "Step1完成" and perform quality check

### Phase 2: Supply Chain Analysis (Step2 - 产业链挖掘)

**Objective**: After identifying target sector, drill down to specific supply chain segments and high-value components (找铲子).

**Process**:
1. Create separate analysis for each sector from Step1
2. Decompose sector into core supply chain components
3. Identify segments with highest value contribution (价值量最高处)
4. Find A-share leaders in each segment
5. Discover "picks and shovels" stocks (铲子股 - universal suppliers)
6. Map competitive landscape and backup candidates

**Output**:
- Documents: `02A~02E_产业链挖掘_{赛道}_YYYYQx.md` (one per sector)
- Stock list: `step2/02_标的清单.yaml` (fields: name, track, code, market)
  - A股: `market: A`, `code`=6 digits
  - 港股: `market: HK`, `code`=5 digits (keep leading zeros)
- Directory: `step2/`

**Checkpoints**:
- ✅ Does it include key segments/value contribution/picks-and-shovels analysis?
- ✅ Are A-share leaders and backups provided?
- ✅ Is the YAML stock list generated for downstream steps?

**📋 Checklist Update**: After completing Step2, update `checklist.md`:
- ✅ Mark all Step2 files as complete
- Fill in "关键发现" (价值量最高环节, 铲子股, 候选股票数)
- **Critical**: Verify YAML format is correct - all subsequent steps depend on this!
- Mark "Step2完成" and perform quality check

### Phase 2.5: Commodity Cycle Positioning (Step2.5 - 商品周期定位 - 资源股必做)

**Objective**: For commodity/resource sectors, identify current position in supply-demand cycle and price cycle to avoid buying at cycle peaks.

**⚠️ Critical Lesson from Real Cases**:
```
白银踏空案例(2025年11月):
- 判断: 结构性牛市中段(56美元/盎司) ✓ 正确
- 策略: 等待回调到52-55美元 ✗ 错误
- 结果: 价格未回调,直接涨到60+ → 完全踏空

教训: 牛市不言顶,逼空不言调
→ 周期定位比静态价格更重要
```

**Process**:
1. **Supply-Demand Fundamentals (5 Key Indicators)**:
   - **Capacity**: Is production capacity at ceiling? (e.g., 铝行业4500万吨天花板)
   - **Inventory**: Current inventory level vs historical percentile (<30% = tight supply)
   - **Utilization Rate**: Operating rate trend (rising = demand strong)
   - **Price Trend**: Is price rising/stable/falling? Duration of trend?
   - **Order Backlog**: Are orders piling up or slowing down?

2. **Cycle Stage Identification (4 Stages)**:
   - **Stage 1 - Bottom (底部)**: Low price, high inventory, low utilization → **Best entry**
   - **Stage 2 - Uptrend (上升)**: Price rising, inventory falling, capacity tight → **Good entry**
   - **Stage 3 - Frenzy (狂热)**: Extreme price, zero inventory, everyone bullish → **Reduce position**
   - **Stage 4 - Collapse (崩塌)**: Price falling, inventory rising, demand gone → **Exit**

3. **Current Position Assessment**:
   - Which stage is current commodity in? (Evidence from Step1 catalyst + supply-demand data)
   - How long has current stage lasted? (Cycles typically 3-5 years)
   - What's the expected duration remaining? (Conservative estimate)

4. **Price Cycle vs Production Cycle Mismatch**:
   - **Key Insight**: Production capacity takes 2-3 years to build, price can spike in months
   - **Opportunity Window**: Identify when supply is constrained but price hasn't peaked
   - **Example**: 铝行业2025-2026Q2 window (国内产能天花板 + 海外产能未释放)

**Output**:
- Cycle analysis: `step2.5/02.5_{赛道}_商品周期定位.md`
- Fields: Current stage, supply-demand indicators, investment window, risk triggers
- Directory: `step2.5/`

**Checkpoints**:
- ✅ Have you identified current cycle stage with evidence?
- ✅ Are supply-demand fundamentals quantified (not just qualitative)?
- ✅ Is the investment window timeframe specified?
- ✅ Are risk triggers defined (what would signal cycle turning)?

**Decision Impact**:
- 🟢 **Stage 1-2 (Bottom/Uptrend)**: Aggressive position building, cycle has years to run
- 🟡 **Stage 2-3 (Uptrend/Frenzy)**: Selective entry, use 3-3-4 staged method, set tight stops
- 🔴 **Stage 3-4 (Frenzy/Collapse)**: Reduce/exit positions, cycle peaking or peaked

**📋 Checklist Update**: After completing Step2.5 (if applicable), update `checklist.md`:
- ✅ Mark Step2.5 file as complete OR mark as "⊗ (非资源股跳过)"
- Fill in "关键判断" (周期阶段, 投资窗口, 风险触发点)
- Mark "Step2.5完成" and perform quality check

**🎯 Phase 1 Milestone Check**: Before proceeding to Step3, review checklist:
- [ ] All sectors have supply chain analysis?
- [ ] YAML format validated?
- [ ] Resource stocks completed cycle positioning?

**⚠️ Avoid These Mistakes**:
- ❌ Waiting for "perfect pullback" in Stage 2 uptrend → Risk of踏空 (missing opportunity)
- ❌ Buying dips in Stage 4 collapse → "Catching falling knife"
- ❌ Using historical PE in Stage 2-3 → Cycle PE adjustment needed (see Step3c)

### Phase 3: Fundamental Verification (Step3 - 深度去伪/财报验证)

**Objective**: Validate investment thesis through financial reports and business fundamentals, distinguish real business from speculation. Separated into 3 layers: automated download/extraction and manual analysis.

#### Step3a: Financial Report Download (财报获取 - 自动化)

**Objective**: Automatically download annual and quarterly reports for all stocks from Step2.

**Process**:
1. Read `step2/02_标的清单.yaml` for stock codes
2. Use CNINFO API to download latest annual/quarterly reports (A-share only)
3. Save reports as PDF files by stock code
4. For HK stocks, manually download from HKEXnews or company IR pages and place into the same directory structure

**Output**:
- Directory: `step3/financials/{代码_名称}/`
- Contents: `{年份}_annual_report.pdf`, `{季度}_quarterly_report.pdf`

**Tools** (automation):
- Download script: `step3/tools/step3a_download_reports.py`
- Config: Input `step2/02_标的清单.yaml`

**Checkpoints**:
- ✅ Are all reports for Step2 stocks downloaded?
- ✅ Are reports organized by stock code and year/quarter?
- ✅ Are missing reports logged for manual intervention?

#### Step3b: Financial Report Content Extraction (财报内容提取 - 自动化)

**Objective**: Extract key sections from downloaded reports using AI or OCR for structured analysis.

**Process**:
1. Read PDF reports from `step3/financials/`
2. Extract key sections: 产品分类、主要客户、订单信息、风险因素、收入和毛利
3. Generate extraction summaries with timestamps
4. Create searchable index for manual review

**Output**:
- Extracts: `step3/extracts/{代码_名称}_annual_extract.txt`, `quarterly_extract.txt`
- Index: `step3/extracts/extraction_index.yaml` (fields: code, name, sections, extraction_date)
- Directory: `step3/extracts/`

**Tools** (automation):
- Extraction script: `step3/tools/step3b_extract_content.py`
- Supports: PDF text extraction, structured data parsing
- Config: Rules for section identification

**Checkpoints**:
- ✅ Are key sections extracted for all reports?
- ✅ Is extracted content organized and searchable?
- ✅ Are extraction timestamps recorded?

#### Step3c: Financial Report Analysis & Verification (财报分析 - 全AI自动)

**Objective**: Automatically analyze extracted financial report content using AI to verify business fundamentals and identify red flags. Complete end-to-end without human intervention.

**Process** (Fully Automated with AI):
1. **AI Content Analysis**: 
   - Read "产品分类" section: Determine if new business is substantial or just R&D
   - Read "主要客户" section: Extract real customer names and order volumes
   - Read "风险因素" section: Identify hidden risks or competitive threats
2. **AI Evidence Extraction**:
   - Evidence-based findings: Cite specific report sections and numbers
   - Risk identification: Extract top 3-5 risks with supporting evidence
   - Business assessment: Classify business as "real", "trial", or "speculation"
3. **Resource Moat Rating (资源护城河评级 - 20% weight)** ⭐ NEW:
   - **5 points**: Global/national monopoly (中国铀业, 盐湖股份97%钾盐)
   - **4 points**: Global top 3 (洛阳钼业钴, 紫金矿业铜金)
   - **3 points**: Regional monopoly (某省某矿独占)
   - **2 points**: Has resources but non-monopoly
   - **1 point**: No resources (pure processing/tech, 汇顶科技)
   - **Key Principle**: 资源垄断 > 技术垄断 > 市场占有率 > 品牌客户关系
4. **Cycle-Adjusted PE (周期PE调整 - for resource/commodity stocks)** ⭐ NEW:
   - Traditional PE = Price / Current EPS (can be misleading at cycle peaks/troughs)
   - **Cycle PE** = Price / Peak Cycle EPS (normalized earnings)
   - **PEG** = PE / Growth Rate (<1 = undervalued, >2 = overvalued)
   - Example: 云铝 PE=22.82 seems high, but PEG=0.91 → actually undervalued
5. **AI Report Generation**: Automatically generate individual analysis reports per stock
6. **AI Summary Table Creation**: Generate consolidated verification table

**Key Advantages of AI-Only Approach**:
- ✅ **Consistency**: Same analysis criteria applied to all stocks
- ✅ **Speed**: All stocks analyzed in parallel, results in minutes
- ✅ **Completeness**: No risk of human oversight or fatigue bias
- ✅ **Traceability**: All conclusions backed by specific evidence references
- ✅ **Scalability**: Can handle 10-100+ stocks without time constraints

**Output**:
- Individual Reports: `step3/analysis/03_{赛道}_{代码}_{名称}.md`
- Summary Table: `step3/report/03_汇总_结论表.md`
  - Fields: Code, Name, Track, Business Reality Score, Key Risks, Revenue Proportion, AI Recommendation
- Detailed Evidence: Each report includes specific evidence references
- Directory: `step3/`

**Tools** (Fully Automated):
- No manual scripts needed - use Claude/GPT directly
- Input: Step3b extracted content (plain text files)
- Output: Structured markdown reports

**Prompts to Use**:
```
请根据以下财报摘要信息，分析这家公司的业务真实性:

公司名称: [NAME]
提取内容:
[EXTRACTED_CONTENT]

请分析以下方面:
1. 核心业务: 是什么业务？规模有多大？
2. 新业务进展: 宣传的新业务实际进展如何？是否有真实收入？
3. 关键客户: 有没有具体的客户名称和订单信息？
4. 主要风险: 财报中提到哪些主要风险因素？
5. 总体评分: 1-10分，这家公司的业务真实性评分是多少？

请输出Markdown格式，包括:
- 业务真实性评分
- 3-5条关键风险
- 具体的财报证据引用
- 推荐评级（看好/中性/看空）
```

**Checkpoints**:
- ✅ Are all stocks from Step2 analyzed?
- ✅ Does each report include specific evidence references?
- ✅ Are business reality scores assigned consistently?
- ✅ Is the summary table complete and sortable?
- ✅ Can recommendations be used for Step4 prioritization?

**📋 Checklist Update**: After completing Step3c, update `checklist.md`:
- ✅ Mark all individual analysis files as complete
- ✅ Mark summary table as complete
- Fill in "关键发现" (高分股票, 红旗股票, 资源护城河评级)
- Mark "Step3c完成" and perform quality check



### Phase 3.5: Supply Chain Verification (Step3.5 - 产业链验证 - 可选但推荐)

**Objective**: Cross-validate Step2's supply chain assumptions using evidence from financial reports and news events. Identify if assumed relationships actually exist in the market.

**Process**:
1. **Financial Report Cross-Check**: 
   - Review Step3c extracted content for customer/supplier relationships
   - Does Company A (identified as supplier in Step2) mention Company B (identified as customer) in their reports?
   - Are order volumes and cooperation status mentioned?
   - Red flag: Assumed relationship but no mutual mention in reports
2. **News Event Verification**:
   - Check Step4 news for partnership announcements between Step2 companies
   - Validate if supply chain relationships have been publicly announced
   - Identify new partnerships not covered in Step2 analysis
3. **Competitive Threat Assessment**:
   - Are there alternative suppliers or competitors emerging?
   - Has any Step2 company lost market share to new entrants?
   - Identify potential disruption to the assumed supply chain structure
4. **Supply Chain Risk Mapping**:
   - Identify bottleneck positions (single supplier or customer dependency)
   - Assess concentration risk: If key company fails, does entire chain collapse?

**Output**:
- Verification report: `step3.5/report/03.5_供应链验证表.md`
- Fields: Company, Role, Assumed Relationships, Evidence Found, Confidence Level, Risks
- Risk mapping: `step3.5/report/03.5_供应链风险地图.md`
- Directory: `step3.5/`

**Tools** (optional automation):
- Verification script: `step3.5/tools/step3.5_supply_chain_verify.py`
- Input: Step2 supply chain structure + Step3c analysis reports + Step4 news data

**Checkpoints**:
- ✅ Are supply chain relationships verified with evidence from financial reports?
- ✅ Have you identified companies mentioned in Step2 but without actual business relationships?
- ✅ Are bottleneck positions clearly marked?
- ✅ Is the confidence level for each relationship documented?

**Impact on Decision**:
- 🔴 Low confidence supply chain → Reduce investment conviction or wait for clearer validation
- 🟡 Moderate confidence → Proceed but monitor news for relationship confirmation
- 🟢 High confidence → Thesis strengthened, ready for Step4 analysis

### Phase 3.6: Geopolitical Risk Assessment (Step3.6 - 地缘风险评估 - 资源股/全球供应链必做)

**Objective**: Systematically assess geopolitical risks for resource stocks and global supply chain exposure.

**⚠️ Critical Context - Deglobalization Revaluation**:
```
传统逻辑(全球化时代):
海外资产 = 风险 → 折价10-20%
鹏欣刚果金矿 → 地缘风险 → 低估

新逻辑(去全球化时代):
海外资产 = 稀缺性 → 溢价20-40%
鹏欣刚果金矿 → 铜钴稀缺 → 战略重估

前提条件:
✓ 供应链中断风险上升
✓ 资源民族主义抬头  
✓ 手握资源即定价权
```

**Process**:
1. **Supply Chain Geopolitics (50% weight)**:
   - Where do critical raw materials come from? (Country/region)
   - Is there sanction risk? (US/EU blacklist, export controls)
   - Are there alternative suppliers? (Backup plan feasibility)
   - **Example**: 中芯国际 DUV光刻机 → 荷兰ASML → 美国制裁风险

2. **Customer Geopolitics (30% weight)**:
   - Where are major customers located? (Concentration by country)
   - Over-reliance on single country? (>50% revenue from one country = high risk)
   - Deglobalization impact? (友岸外包/supply chain bifurcation)
   - **Example**: 某AI芯片公司 → 100%美国客户 → 高风险

3. **Asset Geopolitics (20% weight)**:
   - Percentage of overseas assets? (<20% safe, >50% high risk)
   - Political stability of host country? (Past 10 years: coups, wars, riots)
   - Nationalization risk? (Mining royalty changes, asset seizure)
   - **Example**: 鹏欣资源刚果(金) → 政局不稳 → 资产国有化风险

**Scoring System**:
- **0-3 points**: Extreme geopolitical risk (鹏欣刚果金, 某俄罗斯资产公司)
  - Action: Satellite position only (<10%), strict stop-loss
- **4-6 points**: Moderate geopolitical risk (中芯国际DUV, 洛阳钼业刚果钴)
  - Action: Normal position with hedging strategy
- **7-10 points**: Low geopolitical risk (中国铝业国内, 盐湖股份国内)
  - Action: Core position eligible (30-40%)

**Deglobalization Adjustment (去全球化视角重估)** ⭐:
- If geopolitical risk = resource scarcity opportunity:
  - **Add +1.5 points**: For strategic resources in conflict zones (铜钴锂稀土)
  - **Add +1.0 points**: For import substitution beneficiaries (国产替代)
- If geopolitical risk = pure political chaos:
  - **Deduct -1.0 to -2.0 points**: For unstable regions without strategic value

**Example Applications**:
```
鹏欣资源:
基础分 3.0 (刚果金极高风险)
地缘溢价 +1.5 (铜钴战略稀缺)
政局折价 -1.0 (政变罢工风险)
调整后 3.5 → 卫星仓10-15%, 严格止损

洛阳钼业:
基础分 5.0 (刚果金+国内混合)
地缘溢价 +1.5 (全球第一钴)
国企背书 +0.5 (央企降低没收风险)
调整后 7.0 → 核心仓20-30%

中国铝业:
基础分 8.0 (主要国内+几内亚)
资源稀缺 +1.0 (几内亚铝土矿战略)
调整后 9.0 → 核心仓30-40%
```

**Output**:
- Geopolitical analysis: `step3.6/03.6_地缘风险评估表.md`
- Fields: Company, Supply Risk, Customer Risk, Asset Risk, Total Score, Deglobalization Adjustment, Position Limit
- Directory: `step3.6/`

**Checkpoints**:
- ✅ Have you identified all overseas exposure (supply/customer/asset)?
- ✅ Is political stability assessed with evidence (past conflicts/policy changes)?
- ✅ Have you applied deglobalization lens (risk vs opportunity)?
- ✅ Are position limits set based on geopolitical score?

**📋 Checklist Update**: After completing Step3.6 (if applicable), update `checklist.md`:
- ✅ Mark Step3.6 file as complete OR mark as "⊗ (国内产业链跳过)"
- Fill in "关键判断" (极高风险股票, 仓位限制, 去全球化受益股)
- Mark "Step3.6完成" and perform quality check

**🎯 Phase 2 Milestone Check**: Before proceeding to Step4, review checklist:
- [ ] All candidate stocks have financial analysis?
- [ ] Business reality scores completed?
- [ ] Supply chain verification completed?
- [ ] Geopolitical risk assessment completed (if applicable)?
- [ ] Low-score/high-risk stocks eliminated?

### Phase 4: News & Events Analysis (Step4 - 消息与新闻检索)

**Objective**: Discover catalysts and risks through systematic news and event analysis.

#### Step4a: News Search & Collection (新闻搜索 - 自动化)

**Objective**: Automatically search and collect announcements, news, and events from multiple sources.

**Process**:
1. Search CNINFO (巨潮资讯) for official announcements from A-share stocks
2. For HK stocks, collect announcements from HKEXnews or company IR pages (manual if needed)
3. Search news platforms for industry news and company news (past 30-60 days)
4. Search event calendars for conferences, earnings announcements, policy releases
5. Collect metadata: source, date, title, URL
6. De-duplicate and organize by date

**Output**:
- Raw news collection: `step4/raw_data/{代码_名称}_news_raw.yaml`
- Fields: date, source, title, url, category (announcement/news/event)
- News index: `step4/raw_data/news_index.yaml`
- Directory: `step4/raw_data/`

**Tools** (automation):
- Search script: `step4/tools/step4a_search_news.py`
- Supports: CNINFO API, news APIs, web scraping
- Config: Search keywords from Step2 stock names

**Checkpoints**:
- ✅ Are all Step2 stocks covered in news search?
- ✅ Is the time window correct (30-60 days)?
- ✅ Are duplicate news items removed?

#### Step4b: News Classification & Tagging (新闻分类与标注 - AI + 人工)

**Objective**: Classify news into catalysts and risks, and tag relevance and impact.

**Process**:
1. **AI-Assisted Classification**:
   - Use AI to read news titles and summaries
   - Classify: Positive Catalyst / Negative Risk / Neutral News / Irrelevant
   - Extract key entities: Company affected, event type, impact area
2. **Human Validation**:
   - Review AI classifications for accuracy
   - Correct misclassifications
   - Add manual notes for ambiguous cases
3. **Time Window Tagging**:
   - When did the event occur? (event_date)
   - When will impact be realized? (impact_date)
   - Any upcoming milestones mentioned? (milestone_date)
4. **Impact Assessment**:
   - High Impact: Could significantly change investment thesis
   - Medium Impact: Notable but not thesis-changing
   - Low Impact: Routine or minor news

**Output**:
- Classified news: `step4/classified/{代码_名称}_news_classified.yaml`
- Fields: date, source, title, classification, impact_level, event_date, impact_date, notes, reviewed
- Summary table: `step4/report/04_汇总_新闻分类表.md`
- Directory: `step4/classified/`

**Tools** (AI assistance):
- Classification script: `step4/tools/step4b_classify_news.py`
- Input: Raw news from Step4a
- Output format: Structured YAML

**Checkpoints**:
- ✅ Have you reviewed AI classifications for accuracy?
- ✅ Are impact levels assigned based on thesis relevance?
- ✅ Are all dates clearly documented?
- ✅ Are ambiguous news items marked for human review?

#### Step4c: News-Technical Conflict Check (新闻与技术面冲突检查)

**Objective**: Cross-check if news timeline aligns with technical analysis to identify inconsistencies.

**Process**:
1. **Timeline Analysis**:
   - Major positive catalyst → Did stock price rise after announcement? If not, red flag
   - Major negative risk → Did stock price fall after announcement? If not, red flag
   - Upcoming catalyst → Is stock price already pricing in expectation?
2. **Conflict Detection**:
   - Stock already rallied 50% but catalyst still 1 month away → Overheating risk
   - Negative news announced but stock price unchanged → Market disagrees, investigate why
   - Gap between news date and stock reaction → Possible delayed impact
3. **Validation Gaps**:
   - Which news items don't match the technical trend?
   - Are there hidden catalysts not captured in news search?
4. **Final News Summary**:
   - List catalysts with timeline and confidence level
   - Highlight conflicts and their implications
   - Recommend: Watch for upcoming catalyst dates, avoid trading before announcements

**Output**:
- Conflict analysis: `step4/analysis/04_新闻技术面冲突分析.md`
- Final news summary: `step4/report/04_汇总_新闻与事件表.md`
- Fields: Stock, Event Type, Event Date, Expected Impact Date, News Catalyst, Technical Signal, Alignment, Risk Notes
- Directory: `step4/`

**Tools** (AI + manual analysis):
- Helper script: `step4/tools/step4c_conflict_check.py` (optional)
- Input: Step4b classified news + Step5a technical data
- Output: Conflict report and recommendations

**Checkpoints**:
- ✅ Are major catalysts aligned with technical trends?
- ✅ Have you identified conflicts and their implications?
- ✅ Is the timeline clear for upcoming catalysts?
- ✅ Are recommendations based on both news and technical signals?

**📋 Checklist Update**: After completing Step4c, update `checklist.md`:
- ✅ Mark all Step4 files as complete
- Fill in "关键发现" (新闻与价格冲突股, 已price-in催化, 未来催化时间表)
- Mark "Step4c完成" and perform quality check

**🎯 Phase 3 Milestone Check**: Before proceeding to Step5, review checklist:
- [ ] All stocks have news search completed?
- [ ] Catalyst timeline is clear?
- [ ] News-technical conflicts investigated?

**Objective**: Search for recent announcements, news, and events to identify catalysts and risks.

### Phase 5: Technical Analysis & Entry Strategy (Step5 - 技术面走势与介入策略)

**Objective**: Combine fundamental and news analysis with technical analysis to formulate final entry strategy.

#### Step5a: Technical Data Collection & Indicator Calculation (技术数据获取与指标计算 - 自动化)

**Objective**: Automatically collect historical price data and calculate technical indicators.

**Process**:
1. Retrieve recent 120 trading days' price data for all stocks
2. Calculate moving averages: MA20, MA60, MA250
3. Calculate high/low points: 20-day/60-day/250-day high and low
4. Calculate volatility metrics: ATR, daily range, amplitude
5. Organize data into time-indexed format

**Output**:
- Technical data: `step5/raw_data/{代码_名称}_technical_data.csv`
- Columns: date, open, close, high, low, volume, ma20, ma60, ma250, h20, l20, h60, l60, h250, l250
- Data index: `step5/raw_data/technical_index.yaml`
- Directory: `step5/raw_data/`

**Tools** (automation):
- Data collection script: `step5/tools/step5a_fetch_technical_data.py`
- Supports: Wind API, Tushare, Yahoo Finance
- Config: Stock codes from Step2 YAML

**Checkpoints**:
- ✅ Are all 120 trading days of data collected?
- ✅ Are all indicators calculated correctly?
- ✅ Are data gaps handled (holidays, missing data)?

#### Step5b: Trend Analysis & Signal Detection (趋势判断与信号检测 - AI + 人工)

**Objective**: Analyze price trends and identify technical signals aligned with fundamental and news analysis.

**Process**:
1. **Trend Assessment** ⭐:
   - Short-term (20-day): Is price above/below MA20? Momentum direction?
   - Medium-term (60-day): Is price above/below MA60? Established trend?
   - Long-term (250-day): Is price above/below MA250? Overall trend?
   - Trend health: Are MAs in proper order (MA20 > MA60 > MA250 for uptrend)?
2. **Support & Resistance**:
   - Recent support: 20-day low, 60-day low
   - Potential resistance: 20-day high, 60-day high, previous highs
   - Breakout zones: If price breaks 60-day high, where's next resistance?
3. **Volatility & Risk**:
   - Average daily range and amplitude
   - Recent volatility vs historical average (high volatility = risk)
   - Gap risk: Overnight gaps that could stop-loss?
4. **Signal Validation with Fundamentals & News**:
   - Does uptrend align with positive catalysts (Step4)?
   - Does downtrend align with negative risks (Step4)?
   - Conflict detection: Stock rallying but negative news → Be cautious
   - Wait for signals: Is price still waiting for announced catalyst?
5. **AI-Generated Signal Report**:
   - Use AI to synthesize: fundamentals + news + technical signals
   - Highlight alignment and conflicts
   - Estimate confidence level for each signal

**Output**:
- Technical analysis: `step5/analysis/05_{赛道}_{代码}_{名称}_technical.md`
- Signal summary: `step5/report/05_汇总_技术信号表.md`
- Fields: Stock, Short-term Trend, Mid-term Trend, Support, Resistance, Signal Strength, Catalyst Alignment, Risk Level
- Directory: `step5/analysis/`

**Tools** (AI assistance):
- Analysis helper: `step5/tools/step5b_trend_analysis.py` (optional)
- Input: Technical data from Step5a + catalyst timeline from Step4c
- Output: Signal report with recommendations

**Checkpoints**:
- ✅ Have you assessed trends at multiple timeframes?
- ✅ Are support/resistance levels clearly identified?
- ✅ Is technical signal aligned with fundamental analysis?
- ✅ Are conflicts with news catalysts documented?

#### Step5c: Entry Decision & Strategy Formulation (入场决策与策略制定)

**Objective**: Make final investment decision based on integrated analysis (fundamentals + news + technical).

**Process**:
1. **Integrated Assessment**:
   - Step3c: Is business fundamentally sound? (Business Reality Score: 1-10)
   - Step4c: Are catalysts positive and upcoming? (Catalyst Timeline)
   - Step5b: Is technical setup favorable for entry? (Trend & Signal Quality)
   - Step3.5: Is supply chain thesis validated? (Confidence Level)

2. **Decision Matrix**:
   | Business | Catalyst | Technical | Supply Chain | **Action** |
   |----------|----------|-----------|--------------|-----------|
   | Bullish | Positive | Strong Up | High Conf | **BUY** |
   | Bullish | Positive | Neutral | High Conf | **WAIT for Setup** |
   | Bullish | Neutral | Strong Up | High Conf | **Consider BUY** |
   | Bullish | Negative | Strong Down | High Conf | **WAIT** |
   | Neutral | Positive | Strong Up | Mod Conf | **Monitor** |
   | Bearish | Any | Any | Low Conf | **AVOID** |

3. **Price Target & Risk Management - 3-3-4 Staged Position Building (分批建仓法)** ⭐ NEW:

**⚠️ Critical Lesson - Avoid Complete 踏空 (Missing Opportunity)**:
```
传统错误(等完美买点 = 100%踏空风险):
"等云铝回调12% (32.84→28.80) → 永远等不到 → 仓位0%"
"等白银回调到52-55 → 价格直接60+ → 完全踏空"

问题: 战略看对(牛市逼空) vs 战术执行(等深度回调) → 逻辑割裂
```

**3-3-4 Method (替代传统一次性满仓)**:

**第一批 30%: 现价立即买入 (获取观察权)**
- **Purpose**: Avoid complete踏空, get "skin in the game"
- **When**: Immediately after thesis validated (Step3+4+5 all green)
- **Price**: Current market price (不等回调)
- **Psychological benefit**: 有底仓 → 不焦虑 → 决策更理性
- **Example**: 白银56美元时买30% → 即使涨到60也有底仓,不会完全踏空

**第二批 30%: 挂单5-8%回调 (灵活防守)**
- **Purpose**: Capture pullback if it happens, lower average cost
- **When**: Set limit order 5-8% below current price
- **Rule**: If not filled within 3-5 days → **Cancel order, give up**
- **Key**: Don't stubbornly wait for 10-15% deep pullback (龙头在高景气期"以横代跌")
- **Example**: 云铝32.84时挂28.80(-12%) → 永远等不到 → 应该挂30.50(-7%)并设3天期限

**第三批 40%: 突破前高追加 (右侧确认)**
- **Purpose**: Confirm uptrend strength, ride momentum
- **When**: Price breaks above 20-day or 60-day high on volume
- **Validation**: Must have catalyst confirmation (news/earnings/policy)
- **Psychological**: Overcome "fear of heights" (30元PE=20 < 3元PE=100, 30元更便宜)
- **Example**: 白银突破60美元 + ETF持续流入 → 追加40%, 周期未结束

**Dynamic Stop-Loss (移动止损 - 替代固定止损)**:
- ❌ **Traditional fixed stop**: Entry price -10% (会被正常波动震出)
- ✅ **Moving stop** (2 options):
  - **Option 1**: 20-day MA trailing stop (保护利润,让盈利奔跑)
  - **Option 2**: ATR 2x trailing stop (adaptive to volatility)
- **Example**: 买入10元 → 涨到15元 → 止损线从9元上移到13.5元(20日均线)

**Position Sizing by Conviction**:
- 🎯 **High Conviction** (3 factors aligned): 30%+30%+40% = **Full 3-3-4**
- 🟡 **Medium Conviction** (2 factors aligned): 20%+20%+0% = **40% max**
- 🔴 **Low Conviction** (1 factor only): 10%+0%+0% = **10% starter only**

4. **Psychological Trap Warnings (心理陷阱警示系统)** ⚠️ NEW:

**Trap 1: "Fear of Heights" (恐高心理)**
- **Symptom**: "30元太贵不敢买, 3元便宜敢追高"
- **Reality**: 30元 PE=20倍 < 3元 PE=100倍 (30元更便宜!)
- **Fix**: 看PE/PB不看绝对股价, 看周期PE不看历史PE
- **Real Case**: 云铝30元PE=22.82(低估) vs 怡球3元PE=170.81(高估), 结果买错了

**Trap 2: "Left-Side Order Hanging" (左侧挂单陷阱)**
- **Symptom**: "等回调10-15%再买" → 龙头不深调 → 永远等不到
- **Reality**: 高景气龙头"以横代跌", 不会给深度回调机会
- **Fix**: 3-3-4法则, 30%先上车, 不要100%等完美买点
- **Real Case**: 云铝等-12%永远没来, 神火等-7%永远没来 → 核心仓位0%

**Trap 3: "Static Anchoring" (静态锚定陷阱)**
- **Symptom**: "白银52-55是支撑" → 价格涨到60还在等52 → 完全踏空
- **Reality**: 支撑位是动态的,会随价格上移
- **Fix**: 移动止损法, 20日均线跟踪, 不是固定价格
- **Real Case**: 白银56时等52-55回调 → 价格60+ → 支撑已上移到57-58

**Trap 4: "Allocation Execution Failure" (配置执行失败)**
- **Symptom**: 选对股票(云铝/神火龙头)但仓位0% → 判断再对也白搭
- **Reality**: 配置执行 > 标的选择
- **Fix**: 使用执行checklist, 不能只有"计划"没有"行动"
- **Real Case**: 原定云铝40%+神火20% → 实际0%+0% → 错过主升浪

**Execution Checklist (执行清单 - 强制检查)** ✅:
```
建仓前必查:
□ 第一批30%订单是否已下单? (不能只是"计划")
□ 第二批30%挂单价格是否合理? (5-8%回调,不是15%+)
□ 第二批挂单是否设定期限? (3-5天未成交则取消)
□ 移动止损线是否设定? (20日均线 or ATR 2x)
□ 是否克服"恐高"心理? (看PE不看股价)
□ 是否避免"左侧挂单"陷阱? (不等深度回调)
□ 总仓位是否符合conviction? (高/中/低对应100%/40%/10%)
```

5. **Final Recommendation**:
   - Clear recommendation: Buy (3-3-4 method) / Hold / Avoid
   - Reasoning: 2-3 key reasons from all analysis layers
   - Timeline: When to enter (30% now, 30% within 3-5 days, 40% on breakout)
   - Risk triggers: What would invalidate the thesis?
   - **Execution Plan**: Specific prices for each 3-3-4 batch

**Output**:
- Final strategy table: `step5/report/05_汇总_介入策略表.md`
- Fields: Stock, Business Score, Catalyst, Technical Signal, Supply Chain Conf, Recommendation, Entry Range, Support, Target1/2/3, Risk Triggers, Timeline
- Executive summary: `step5/report/05_汇总_最终决策摘要.md`
- Directory: `step5/`

**Checklist Before Decision** ⭐:
- ✅ Have you personally reviewed all analysis? (Don't just rely on AI synthesis)
- ✅ Is the recommendation clear and backed by 2-3 key reasons?
- ✅ Are risk triggers defined (what would change your mind)?
- ✅ Are timeline expectations clear (when to buy, when to sell)?
- ✅ Does entry price make sense given current technical setup?
- ✅ Can you explain your thesis to someone else clearly?

**Implementation Notes**:
- 🎯 **High Conviction**: Business + Catalyst + Technical all aligned → **3-3-4 full position (100%)**
  - 30% immediate, 30% pullback order (3-5 day limit), 40% breakout追加
- 🟡 **Medium Conviction**: 2 of 3 factors aligned → **Partial 3-3-4 (40% max)**
  - 20% immediate, 20% pullback order, skip breakout追加
- 🔴 **Low Conviction**: Only 1 factor favorable → **Starter only (10%)**
  - 10% immediate for monitoring, no追加
- ⛔ **No Setup**: Thesis broken or factors misaligned → **Avoid or close position**

**心理陷阱最后检查** (Before executing):
- ❌ Am I waiting for "perfect pullback" and risking踏空? → Use 3-3-4 instead
- ❌ Am I anchored to absolute stock price instead of PE? → Check周期PE
- ❌ Do I have execution plan or just "配置方案"? → Use execution checklist
- ❌ Is my stop-loss fixed or dynamic? → Must use moving stop-loss

**📋 Checklist Update**: After completing Step5c, update `checklist.md`:
- ✅ Mark all Step5 files as complete
- Fill in "最终推荐" (BUY/HOLD/AVOID stocks)
- Fill in "3-3-4建仓计划" (verify all 4 items checked)
- Mark "Step5c完成" and perform quality check

**🎯 Phase 4 Milestone Check**: Before proceeding to Step6, review checklist:
- [ ] All stocks have technical analysis completed?
- [ ] BUY/HOLD/AVOID decisions are clear?
- [ ] 3-3-4 position building plan is complete?
- [ ] Risk triggers defined?

### Phase 6: Research Report Cross-Validation (Step6 - 研报交叉验证 - BUY推荐股必做)

**Objective**: For stocks with "BUY" recommendation from Step5c, retrieve and analyze recent broker research reports to cross-validate investment thesis and identify blind spots.

**⚠️ Critical Purpose - Avoid Confirmation Bias**:
```
问题: 前5步都是我们自己的分析 → 可能存在盲点、偏见、信息缺失
解决: 专业机构研报 → 不同视角、独立调研、行业深度

价值:
1. 发现我们遗漏的风险点
2. 验证我们的核心假设
3. 获取一手调研数据(产能/订单/价格)
4. 了解机构共识(一致预期 vs 分歧点)
```

#### Step6a: Research Report Search & Download (研报检索与下载 - 半自动)

**Objective**: Search and download recent research reports from major brokers for BUY-recommended stocks.

**Process**:
1. **Filter Target Stocks**:
   - Read Step5c output: `step5/report/05_汇总_介入策略表.md`
   - Select stocks with "BUY" recommendation
   - Priority: High conviction stocks first

2. **Research Report Search**:
   - **Time window**: Recent 3-6 months (注意时效性!)
   - **Sources**: Major brokers (中信证券、国泰君安、华泰证券、中金公司、招商证券)
   - **Platforms**: 
     - 东方财富研报中心 (http://data.eastmoney.com/report/)
     - 同花顺研报 (http://stockpage.10jqka.com.cn/)
     - 巨潮资讯研报 (http://www.cninfo.com.cn/)
     - Wind/Choice (if available)
   - **Keywords**: Stock code + stock name

3. **Report Filtering Criteria**:
   - ✅ **Must-have**: Published within 3-6 months
   - ✅ **Prefer**: Top-tier brokers (中信/中金/华泰/国泰君安)
   - ✅ **Prefer**: Industry in-depth reports (行业深度) or company research (公司研究)
   - ❌ **Avoid**: Morning briefings (晨会速递), event comments without new info
   - ❌ **Avoid**: Reports older than 6 months (outdated)

4. **Download & Organization**:
   - Download 2-3 most recent reports per stock
   - Save as PDF: `step6/reports/{代码_名称}/{YYYYMMDD}_{券商}_{报告标题}.pdf`
   - Create index: `step6/reports/research_report_index.yaml`

**Output**:
- Research reports: `step6/reports/{代码_名称}/`
- Report index: `step6/reports/research_report_index.yaml`
  - Fields: stock_code, stock_name, report_date, broker, title, rating, target_price, file_path
- Directory: `step6/reports/`

**Tools** (semi-automated):
- Manual search on platforms (most reliable)
- Optional helper script: `step6/tools/step6a_search_reports.py` (web scraping)

**Checkpoints**:
- ✅ Are all BUY-recommended stocks covered?
- ✅ Are reports recent (within 3-6 months)?
- ✅ Are top-tier brokers represented?
- ✅ Is the report index complete with metadata?

#### Step6b: Research Report Analysis & Comparison (研报分析与对比 - AI + 人工)

**Objective**: Extract key insights from research reports and compare with our own analysis to identify alignment and conflicts.

**Process**:
1. **AI-Assisted Content Extraction** (for each report):
   - **Investment Rating**: 买入/增持/中性 (Buy/Overweight/Neutral)
   - **Target Price**: Price target and upside potential
   - **Core Thesis**: Why bullish/bearish? (2-3 key reasons)
   - **Financial Forecasts**: Revenue/EPS projections for 2026-2027
   - **Key Risks**: What risks did broker identify?
   - **Valuation Method**: DCF/PE/PB/EV/EBITDA?
   - **Unique Insights**: Any proprietary research/channel checks/management interviews?

2. **Cross-Validation Matrix** (Our Analysis vs Broker Reports):

   | Dimension | Our View (Step1-5) | Broker Consensus | Alignment? | Action |
   |-----------|-------------------|------------------|------------|--------|
   | **Core Catalyst** | [Our catalyst] | [Broker catalyst] | ✅/⚠️/❌ | Validate/Investigate/Challenge |
   | **Business Quality** | [Score 1-10] | [Rating] | ✅/⚠️/❌ | Validate/Investigate/Challenge |
   | **Valuation** | [Our PE/PB] | [Broker PE/PB] | ✅/⚠️/❌ | Validate/Investigate/Challenge |
   | **Target Price** | [Our target] | [Broker target] | ✅/⚠️/❌ | Validate/Investigate/Challenge |
   | **Key Risks** | [Our risks] | [Broker risks] | ✅/⚠️/❌ | Validate/Investigate/Challenge |

3. **Conflict Analysis** (重点关注分歧点):
   - **Type 1 - We Bullish, Brokers Bearish**: 🚨 RED FLAG
     - Action: Re-examine our thesis, identify what we missed
     - Question: Do brokers have information we don't have?
   - **Type 2 - We Bearish, Brokers Bullish**: ⚠️ OPPORTUNITY or TRAP?
     - Action: Check if brokers are outdated or have newer catalysts
     - Question: Are we too conservative?
   - **Type 3 - Same Direction, Different Magnitude**: 🟡 CALIBRATION
     - Action: Adjust position sizing or target price
     - Question: Are we too aggressive/conservative on upside?
   - **Type 4 - Different Risk Assessment**: ⚠️ BLIND SPOT
     - Action: Incorporate missed risks into Step5 risk management
     - Question: What risk factors did we overlook?

4. **Broker Coverage Consensus**:
   - **High Coverage (5+ reports)**: Crowded trade, may be priced in
   - **Medium Coverage (2-4 reports)**: Normal attention
   - **Low Coverage (0-1 reports)**: Under-the-radar opportunity OR red flag

5. **Update Our Thesis**:
   - Incorporate valid broker insights
   - Adjust conviction level if major conflicts found
   - Update risk assessment with newly identified risks
   - Revise target price if broker valuations more rigorous

**Output**:
- Cross-validation analysis: `step6/analysis/06_{代码}_{名称}_研报交叉验证.md`
- Summary table: `step6/report/06_汇总_研报对比表.md`
  - Fields: Stock, Our Rating, Broker Consensus, Alignment Level, Key Conflicts, Action
- Updated recommendation: `step6/report/06_更新后推荐.md` (revised from Step5)
- Directory: `step6/`

**Checkpoints**:
- ✅ Have you identified major conflicts between our view and brokers?
- ✅ Have you investigated reasons for conflicts (not just ignored them)?
- ✅ Have you updated risk assessment with broker-identified risks?
- ✅ Is the conviction level adjusted based on cross-validation?

**Decision Framework After Cross-Validation**:

```
情况1: 高度一致 (Alignment >80%)
我们: 买入 | 券商: 买入/增持 | 核心逻辑一致
→ 行动: 维持BUY推荐，按原3-3-4计划执行
→ 风险: 可能是拥挤交易，已被市场price-in

情况2: 部分一致 (Alignment 50-80%)
我们: 买入 | 券商: 买入 | 但目标价/风险评估不同
→ 行动: 调整目标价或仓位，整合双方风险点
→ 风险: 需要clarify分歧来源

情况3: 方向一致但时间差 (Time Lag)
我们: 买入(基于最新催化) | 券商: 增持(报告2-3个月前)
→ 行动: 验证催化剂是否仍有效，券商可能未更新
→ 风险: 我们的催化可能已失效

情况4: 重大分歧 (Alignment <50%)
我们: 买入 | 券商: 中性/减持 OR 我们关注的风险券商未提及
→ 行动: 🚨 STOP! 深入调研分歧原因
→ 风险: 可能存在重大盲点，暂缓建仓

情况5: 无研报覆盖 (No Coverage)
我们: 买入 | 券商: 无人关注
→ 行动: 两种可能 - Under-the-radar gem OR 有问题股票
→ 风险: 需extra验证，小仓位试探
```

#### Step6c: Final Recommendation Update (最终推荐更新)

**Objective**: Integrate research report insights and issue updated final recommendation.

**Process**:
1. **Conviction Level Adjustment**:
   - **Upgrade** (Medium → High): Broker reports strongly support our thesis + add new bullish points
   - **Maintain**: Broker reports align with our view, no major new info
   - **Downgrade** (High → Medium): Broker reports identify risks we missed
   - **Downgrade to HOLD/AVOID**: Major conflicts, broker consensus bearish

2. **Position Sizing Adjustment**:
   - If broker consensus bullish + our thesis confirmed → Full 3-3-4 (100%)
   - If minor conflicts → Reduce to 2-2-2 (60%)
   - If major conflicts → Starter position only (10-20%) pending clarification

3. **Risk Management Update**:
   - Add broker-identified risks to risk trigger list
   - Set stricter stop-loss if new risks discovered
   - Monitor broker rating changes (downgrade = exit signal)

4. **Generate Updated Report**:
   - Combine Step5 + Step6 insights
   - Clear statement: What changed after reading research reports?
   - Updated 3-3-4 execution plan with revised conviction

**Output**:
- Updated strategy: `step6/report/06_最终推荐(研报验证后).md`
- Changes summary: `step6/report/06_相比Step5的调整说明.md`
- Fields: Stock, Original Rating (Step5), Updated Rating (Step6), Key Changes, Broker Insights Incorporated

**Checkpoints**:
- ✅ Have you read at least 2-3 recent research reports per BUY stock?
- ✅ Have you investigated major conflicts (not ignored them)?
- ✅ Have you updated risk triggers based on broker insights?
- ✅ Is the updated conviction level justified?
- ✅ Are position sizes adjusted appropriately?
- ✅ Can you explain what changed and why?

**📋 Checklist Update**: After completing Step6c, update `checklist.md`:
- ✅ Mark all Step6 files as complete
- Fill in "Conviction调整" (升级, 降级, 放弃 and reasons)
- Mark "Step6c完成" and perform quality check

**🎯 Phase 5 Milestone Check**: Before proceeding to Step7, review checklist:
- [ ] All BUY stocks have research report validation?
- [ ] Major divergences investigated?
- [ ] Conviction levels adjusted?

**⚠️ Critical Reminder**:
```
研报不是gospel (福音书)，也可能错:
1. 券商可能滞后(2-3个月前的判断)
2. 券商可能有利益冲突(投行部门关系)
3. 券商可能跟风(从众心理)

但研报提供valuable second opinion:
1. 专业团队调研数据
2. 不同视角看问题
3. 帮助发现盲点

最终决策: 独立思考 > 盲从研报
```

### Phase 7: Multi-Perspective Reflection (Step7 - 多视角反思与"斗蛊" - 最终决策前必做)

**Objective**: Before final investment decision, use multiple AI models to cross-challenge our thesis, identify blind spots, and force adversarial thinking.

**⚠️ Critical Purpose - Avoid Groupthink and Single-Model Bias**:
```
问题: 前6步可能都用同一个AI模型 → 模型偏见、幻觉、知识盲区
解决: 跨模型"斗蛊" → 利用不同模型的盲区互相纠错

核心思想:
1. DeepSeek: A/H股数据库强、本土化好
2. ChatGPT: 逻辑推理强、全球视野
3. Gemini: 搜索能力强、实时信息

最大价值: 让AI互相攻击我们的论证 → 暴露最弱环节
```

#### Step7a: Cross-Model Challenge (跨模型质疑 - AI+人工)

**Objective**: Use different AI models to challenge our stock selection and core thesis.

**Process**:
1. **Model 1 (e.g., DeepSeek) - Initial Analysis**:
   - Use our Step1-6 conclusion as baseline
   - Ask: "Based on my research, I plan to buy [股票A] and [股票B]. Do you agree?"

2. **Model 2 (e.g., ChatGPT) - Adversarial Challenge**:
   - Present same thesis to different model
   - Ask adversarial questions (use Template 11)

3. **Model 3 (e.g., Gemini Deep Research) - Fresh Perspective**:
   - No prior context, ask for independent analysis
   - Compare: "Gemini thinks [股票C] is better, but I chose [股票A]. Why the difference?"

4. **Conflict Matrix** (关键分歧点对比):

   | Stock | Model 1 (Our Pick) | Model 2 Challenge | Model 3 Independent | Consensus? | Action |
   |-------|-------------------|-------------------|---------------------|------------|--------|
   | 股票A | BUY (核心30%) | Neutral (风险X) | AVOID (理由Y) | ❌ NO | 重新评估 |
   | 股票B | BUY (核心30%) | BUY (一致) | BUY (一致) | ✅ YES | 维持 |
   | 股票C | NOT SELECTED | Neutral | BUY (强推) | ⚠️ BLIND SPOT | 补充调研 |

5. **Key Divergence Investigation**:
   - For each "NO consensus" stock: Why did models disagree?
   - For each "BLIND SPOT" stock: Should we replace one of our picks?

**Output**:
- Cross-model challenge report: `step7/analysis/07_跨模型质疑对比.md`
- Directory: `step7/`

**Checkpoints**:
- ✅ Have you used at least 2-3 different AI models?
- ✅ Have you asked adversarial questions (not just confirmation)?
- ✅ Have you investigated reasons for disagreement?

#### Step7b: Adversarial Reflection (对抗性反思 - 人工)

**Objective**: Force ourselves to argue AGAINST our own thesis.

**Process**:
1. **Devil's Advocate Exercise** (魔鬼代言人):
   - For each BUY recommendation, write down:
     - **3 reasons why we SHOULD NOT buy this stock**
     - **What would make this investment fail?**

2. **Kill Criteria** (杀死标准):
   - Define specific triggers that would immediately invalidate our thesis:
     ```
     如果出现以下情况,立即清仓:
     □ [核心客户]取消订单 or 占比从30%降至10%
     □ [核心产品]出现技术替代方案
     □ [核心催化剂]放缓/取消(如政策变化)
     □ 股价跌破[关键支撑位] and 无新催化剂
     □ 券商集体下调评级 to 中性/减持
     ```

**Output**:
- Bear case analysis: `step7/reflection/07_看空理由分析.md`
- Kill criteria: `step7/reflection/07_杀死标准.md`

#### Step7c: Final Conviction Calibration (最终信心校准)

**Objective**: Recalibrate conviction levels and finalize investment decision.

**Process**:
1. **Conviction Scoring Matrix**:

   | Stock | Original | Cross-Model | Bear Case | **Final** | Action |
   |-------|---------|------------|-----------|----------|--------|
   | 股票A | High | 2/3 agree | Weak | **High** | 维持100% |
   | 股票B | High | 1/3 agree | Strong | **Medium** ↓ | 降至60% |

2. **Final Investment Thesis (One-Page Summary)**:
   ```
   [股票名] - [仓位%] - [信心级别]
   
   核心逻辑: [一句话描述]
   支持论据: [Step3/4/6关键发现]
   最大风险: [风险X] → 对冲: [策略Y]
   杀死标准: [具体触发条件]
   
   3-3-4计划:
   - 30% @ [价格1] 立即执行
   - 30% @ [价格2] 挂单(3天期限)
   - 40% @ [价格3] 突破追加
   - 止损: 20日均线
   ```

3. **Final Checklist Before Execution** ⭐⭐⭐:
   ```
   执行前最后检查:
   □ 已经过至少 2-3 个 AI 模型质疑?
   □ 已经写下看空理由并可以反驳?
   □ 已经设定明确的kill criteria?
   □ Expected Value > 15%?
   □ 仓位分配符合conviction级别?
   □ 3-3-4计划已经具体化(不是只有"计划")?
   □ 移动止损已设定(不是固定止损)?
   □ 可以用一句话向朋友解释这个逻辑?
   □ 如果今天不买明天涨停,会后悔吗? (test commitment)
   ```

**Output**:
- Final conviction table: `step7/final/07_最终信心评级表.md`
- One-page thesis: `step7/final/07_投资论证(一页纸).md` (每只股票一份)
- Portfolio allocation: `step7/final/07_最终组合配置.md`
- Executive summary: `step7/final/07_执行摘要.md` ⭐⭐⭐ (Highest Priority)
- Directory: `step7/`

**Checkpoints**:
- ✅ Have you completed cross-model challenge (Step7a)?
- ✅ Have you completed adversarial reflection (Step7b)?
- ✅ Have you recalibrated conviction levels?
- ✅ Is the final portfolio balanced (diversification + concentration)?
- ✅ Is Expected Value > 15% for all picks?
- ✅ Can you defend your thesis to a skeptic?

**📋 Checklist Update**: After completing Step7c, update `checklist.md`:
- ✅ Mark all Step7 files as complete
- Fill in "最终组合" (High/Medium/Low conviction allocations)
- Fill in "Expected Value检查" (all > 15%?)
- **Complete "执行前最后检查" (9-item checklist)**
- Mark "Step7c完成" and perform quality check

**🎯 Phase 6 FINAL Milestone Check**: Before executing trades, review checklist:
- [ ] Cross-model challenge completed?
- [ ] Adversarial reflection completed?
- [ ] Kill criteria defined for each BUY stock?
- [ ] Final conviction calibration completed?
- [ ] **ALL 9 items in execution checklist passed?**

**🎯 FINAL DELIVERABLES CHECK**: Review "最终交付清单" section in checklist:
- [ ] `07_执行摘要.md` completed? (Highest priority)
- [ ] `07_投资论证(一页纸).md` for each final BUY stock?
- [ ] `07_最终组合配置.md` with 3-3-4 plan?
- [ ] `07_杀死标准.md` with clear exit triggers?

**✅ QUALITY SCORECARD**: Fill in "质量评分卡" in checklist (Target: Average > 8/10)

**⚠️ Critical Mindset**:
```
最大敌人 = 自己的确认偏差

Step7的目的: 主动找错误,而非证明自己对

如果经过Step7后论证依然站得住 → 信心大增
如果经过Step7后发现重大缺陷 → 感谢在买前发现,避免损失

最糟糕的情况: 跳过Step7,盲目自信 → 市场会教你做人
```

### Bonus: Cross-Model Validation (跨模型验证)

**Objective**: Use different AI models to cross-validate findings and avoid single-model bias.

**Process**:
1. Run same analysis through multiple models (DeepSeek, Gemini, ChatGPT)
2. Compare recommendations and identify discrepancies
3. Challenge assumptions and reasoning
4. Identify potential blind spots
5. Synthesize final conclusion

**Best Practice**: Apply cross-model validation at any step (especially Step1 and Step2) for critical decisions.

**When to Apply Cross-Validation**:
- Step1 sector selection: Different models may identify different macro trends
- Step2 supply chain analysis: Different models may emphasize different segments
- Step3c business verification: Ask different models to challenge your conclusions
- Step5c final decision: Get second opinion on entry strategy before committing capital

## Complete Workflow Architecture

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

## Prompt Templates

### Template 1: Sector Selection

```
I am conducting A-share short-term opportunity research. Based on the market environment in [CURRENT_YEAR + MONTH], and major events occurring in [NEXT_1-2_MONTHS] (such as industry conferences, policy releases, seasonal factors), please list 3-5 sectors most likely to experience active trading.

Requirements:
1) Rank by importance and certainty
2) Provide core catalyst for each sector
3) List 1-2 representative leading stocks for reference

我正在进行 A 股短期热点研究。请结合[当前年份+月份]的市场环境，以及[未来 1-2 个月]即将发生的重大事件（如行业大会、政策发布、季节性因素），列出最有可能进行热门炒作的 3-5 个板块。

要求：
1) 按重要度和确定性排序
2) 给出每个板块的核心炒作逻辑（Catalyst）
3) 列出该板块对应的 1-2 个代表性龙头股作为参考
```

### Template 2: Supply Chain Analysis

```
Assuming we are bullish on [SECTOR: humanoid robots/low-altitude economy/solid-state batteries/commercial space], please act as a professional industry analyst and help me dissect this industry's core supply chain:

1) Which segments have the highest value contribution? (e.g., ball screws, sensors, battery materials)
2) For each core segment, who are the absolute leaders in A-shares?
3) Are there any "picks and shovels" stocks (companies needed regardless of who wins)?

假设我们看好[人形机器人/低空经济/固态电池/商业航天]板块。请像一个专业的行业分析师一样，帮我拆解这个产业的核心供应链：

1) 哪些环节价值量最高？（例如：丝杠、传感器、电池材料）
2) 针对每个核心环节，A 股目前的绝对龙头分别是谁？
3) 有没有那种"铲子股"（不管谁赢，都需要用它的产品）？
```

### Template 3: Financial Report Verification

```
Please carefully review this financial/research report from [COMPANY_NAME]:

1) Is this company's [robots/AI/commercial space] business pure speculation, or does it have substantial revenue? What's the revenue proportion?
2) Does the report mention specific customers (such as Tesla, Huawei) or clear mass production timeline?
3) As an investor, what do you think is the biggest risk in this report?

请仔细阅读这份[公司名]的财报/研报：

1) 这家公司的[机器人/AI/商业航天]业务是纯概念炒作，还是已经有实质性收入？收入占比多少？
2) 报告中是否提到了具体客户（如特斯拉、华为）或明确的量产时间表？
3) 作为投资者，你认为这份报告中最大的风险点是什么？
```

### Template 4: Supply Chain Verification

```
I previously identified [COMPANY_A] as a supplier of [COMPONENT] to [COMPANY_B]. Please review their latest financial reports and find evidence of:

1) Does [COMPANY_A]'s annual report mention [COMPANY_B] as a customer or mention [COMPONENT] sales?
2) What percentage of [COMPANY_A]'s revenue comes from [COMPANY_B] and similar customers?
3) Are there any risks to this supply relationship (e.g., customer concentration, alternative suppliers)?

我之前识别[公司A]是[部件]供应商到[公司B]。请根据最新财报验证：

1) [公司A]的年报中是否提到[公司B]作为客户，或提到[部件]销售？
2) [公司A]来自[公司B]和类似客户的收入占比多少？
3) 这个供应关系有哪些风险（如客户集中度、替代供应商）？
```

### Template 5: News-Technical Conflict Analysis

```
[COMPANY_NAME] announced [POSITIVE/NEGATIVE EVENT] on [DATE], but the stock price [describe movement, e.g., "continued falling instead of rising"]. 

1) What could explain this disconnect between news and price action?
2) Is the market disagreeing with the event's importance, or is there hidden negative news?
3) Should I wait for further price action confirmation before entering?

[公司名]在[日期]宣布了[正面/负面事件]，但股价[描述走势，例如："没有上涨反而继续下跌"]。

1) 这种新闻和股价的脱节可能说明什么？
2) 市场是在否定这个事件的重要性，还是存在隐藏的负面消息？
3) 我应该等待进一步的价格确认再介入吗？
```

### Template 6: Technical Setup Validation

```
Stock [STOCK_CODE] is currently at [PRICE], with:
- 20-day MA: [MA20]
- 60-day MA: [MA60]  
- 20-day high: [H20], low: [L20]
- Recent news: [CATALYST]

Given this technical setup and fundamental thesis, is [PRICE] a good entry point? When should I enter?

股票[代码]目前价格[价格]，技术面：
- 20日均线[MA20]
- 60日均线[MA60]
- 20日高[H20]、低[L20]
- 最近事件[催化]

考虑到技术面和基本面，[价格]是好的入场点吗？我应该什么时候入场？
```

### Template 7: Decision Review (Self-Challenging)

```
I have decided to buy [STOCK_NAME] at [PRICE] based on:
- Catalyst: [CATALYST]
- Business: [THESIS]
- Technical: [SETUP]

Please challenge my thesis:
1) What are the top 3 ways my analysis could be wrong?
2) What would make you avoid this stock?
3) If this stock drops 20%, would you still believe in the thesis?

我决定以[价格]买入[股票]，基于：
- 催化[催化逻辑]
- 基本面[论证]
- 技术面[设置]

请质疑我的逻辑：
1) 我的分析可能出错的前3个方面是什么？
2) 你会因为什么而回避这只股票？
3) 如果股价下跌20%，你还会相信这个论证吗？
```

### Template 8: Commodity Cycle Positioning (Step2.5)

```
For [COMMODITY SECTOR: aluminum/copper/silver/lithium], please analyze current supply-demand cycle:

1) **Supply-Demand Fundamentals**:
   - Current production capacity and utilization rate?
   - Inventory level vs historical percentile?
   - Major supply changes expected (new mines, capacity expansions)?
   - Demand drivers and growth rate?

2) **Cycle Stage Identification**:
   - Which stage: Bottom/Uptrend/Frenzy/Collapse?
   - How long has current stage lasted?
   - Expected duration remaining?

3) **Investment Window**:
   - Is this a good time to enter? (Stage 1-2 = yes, Stage 3-4 = no)
   - What's the risk/reward ratio at current prices?
   - What would signal cycle turning?

针对[商品板块: 铝/铜/白银/锂]，请分析当前供需周期：

1) **供需基本面**:
   - 当前产能和开工率?
   - 库存水平处于历史分位数?
   - 重大供给变化(新矿投产/产能扩张)?
   - 需求驱动因素和增速?

2) **周期阶段识别**:
   - 当前阶段: 底部/上升/狂热/崩塌?
   - 当前阶段已持续多久?
   - 预计还能持续多久?

3) **投资窗口**:
   - 现在是好的入场时机吗? (阶段1-2=是, 阶段3-4=否)
   - 当前价格的风险收益比?
   - 什么信号会预示周期转向?
```

### Template 9: 3-3-4 Position Building Execution

```
I want to build position in [STOCK_NAME] using 3-3-4 method. Current price is [PRICE].

**Thesis**: [Business + Catalyst + Technical summary]

**Conviction Level**: High/Medium/Low

Please help me plan:

1) **First 30% (Immediate Entry)**:
   - Entry price: Current market [PRICE]
   - Rationale: Avoid踏空, get observation rights
   - Check: Am I avoiding "waiting for perfect pullback" trap?

2) **Second 30% (Pullback Order)**:
   - Limit order price: [PRICE * 0.92-0.95] (5-8% pullback)
   - Time limit: 3-5 days, cancel if not filled
   - Check: Am I avoiding "left-side hanging" trap (not waiting for 15%+ pullback)?

3) **Third 40% (Breakout Confirmation)**:
   - Trigger: Price breaks [20-day high] on [catalyst news]
   - Check: Am I overcoming "fear of heights" (looking at PE not price)?

4) **Moving Stop-Loss**:
   - Method: 20-day MA or ATR 2x trailing
   - Check: Not using fixed stop-loss?

5) **Psychological Trap Check**:
   - □ Not anchored to absolute stock price?
   - □ Not waiting for deep pullback on strong stocks?
   - □ Have execution plan, not just allocation plan?

我想用3-3-4法建仓[股票名]，当前价格[价格]。

**投资逻辑**: [基本面+催化+技术面摘要]

**Conviction**: 高/中/低

请帮我规划:

1) **第一批30%(立即入场)**:
   - 入场价: 市价[价格]
   - 理由: 避免踏空,获取观察权
   - 检查: 是否避免了"等完美买点"陷阱?

2) **第二批30%(回调挂单)**:
   - 挂单价: [价格*0.92-0.95] (5-8%回调)
   - 期限: 3-5天未成交则取消
   - 检查: 是否避免了"左侧挂单"陷阱(不是等15%+深调)?

3) **第三批40%(突破确认)**:
   - 触发: 突破[20日高点] + [催化消息]
   - 检查: 是否克服了"恐高"心理(看PE不看价格)?

4) **移动止损**:
   - 方法: 20日均线 or ATR 2倍跟踪
   - 检查: 不是固定止损?

5) **心理陷阱检查**:
   - □ 没有锚定绝对股价?
   - □ 没有在强势股上等深度回调?
   - □ 有执行计划不只是配置方案?
```

### Template 10: Research Report Cross-Validation (Step6)

```
I have decided to BUY [STOCK_NAME] based on my Step1-5 analysis. I found [X] recent research reports from brokers. Please help me cross-validate:

**My Thesis**:
- Core Catalyst: [CATALYST]
- Business Score: [X/10]
- Target Price: [PRICE]
- Key Risks: [RISK1, RISK2, RISK3]

**Broker Reports Summary**:
Report 1: [券商名] ([日期])
- Rating: [买入/增持/中性]
- Target Price: [PRICE]
- Core Thesis: [SUMMARY]
- Key Risks: [RISKS]

Report 2: [券商名] ([日期])
- Rating: [买入/增持/中性]
- Target Price: [PRICE]
- Core Thesis: [SUMMARY]
- Key Risks: [RISKS]

**Cross-Validation Questions**:
1) **Alignment Check**: Where do my thesis and broker reports align? Where do they conflict?
2) **Blind Spot Detection**: Did brokers identify risks I missed? Are these material?
3) **Valuation Gap**: Why is there a difference in target price (if any)? Whose assumptions are more reasonable?
4) **Conviction Adjustment**: Should I upgrade/maintain/downgrade my conviction based on broker insights?
5) **Action Plan**: Should I proceed with full 3-3-4 position, reduce size, or wait for clarification?

我决定买入[股票名]，基于我的Step1-5分析。我找到了[X]份最近的券商研报。请帮我交叉验证:

**我的论证**:
- 核心催化: [催化]
- 业务评分: [X/10]
- 目标价: [价格]
- 关键风险: [风险1, 风险2, 风险3]

**券商研报摘要**:
研报1: [券商名] ([日期])
- 评级: [买入/增持/中性]
- 目标价: [价格]
- 核心逻辑: [摘要]
- 关键风险: [风险]

研报2: [券商名] ([日期])
- 评级: [买入/增持/中性]
- 目标价: [价格]
- 核心逻辑: [摘要]
- 关键风险: [风险]

**交叉验证问题**:
1) **一致性检查**: 我的论证和券商研报哪里一致?哪里冲突?
2) **盲点检测**: 券商是否发现了我遗漏的风险?这些风险重要吗?
3) **估值差异**: 目标价为何不同(如果有)?谁的假设更合理?
4) **信心调整**: 基于券商洞察,我应该提升/维持/降低我的conviction吗?
5) **行动计划**: 我应该执行完整3-3-4仓位、减少规模、还是等待澄清?
```

### Template 11: Multi-Perspective Reflection (Step7 - 跨模型斗蛊)

```
**For Cross-Model Challenge (Step7a)**:

有人建议我关注[股票A]和[股票B]作为[板块]的龙头。

1) 你是否认同？如果不认同，请给出理由。
2) 你的推荐列表中为什么没有这两只？
3) 还有没有被它忽略的、但在供应链中不可或缺的公司？

---

**For Adversarial Reflection (Step7b)**:

I have decided to BUY [STOCK_NAME] at [PRICE]. Now I want you to argue AGAINST this decision.

1) **Devil's Advocate**: Give me 3 strong reasons why I SHOULD NOT buy this stock.
2) **Failure Scenario**: What's the most likely scenario where this investment loses 30%+?
3) **Hidden Risk**: What risk am I probably overlooking or underestimating?
4) **Bear Case**: If you were shorting this stock, what would be your thesis?

我决定以[价格]买入[股票名]。现在请你反对这个决定。

1) **魔鬼代言人**: 给我 3 个强有力的理由，说明为什么不应该买这只股票。
2) **失败场景**: 这个投资损夁30%+的最可能场景是什么？
3) **隐藏风险**: 我可能忽略或低估了哪个风险？
4) **看空逻辑**: 如果你要做空这只股票，你的逻辑是什么？

---

**For Final Conviction Calibration (Step7c)**:

After cross-model challenge and adversarial reflection, help me recalibrate:

**Original Thesis**: [SUMMARY from Step1-6]

**Cross-Model Feedback**:
- Model 1: [AGREE/DISAGREE + reasons]
- Model 2: [AGREE/DISAGREE + reasons]
- Model 3: [AGREE/DISAGREE + reasons]

**Bear Case Arguments**: [Top 3 counter-arguments from Step7b]

**Questions**:
1) Given the above feedback, should I upgrade/maintain/downgrade my conviction?
2) Which counter-arguments are most valid? Can I defend against them?
3) Should I adjust position size from [X]% to [Y]%?
4) What's the Expected Value now: Base Case [A]% * 50% + Bull Case [B]% * 25% + Bear Case [-C]% * 25% = ?
5) If Expected Value < 15%, should I abandon this trade?

经过跨模型质疑和对抗性反思后，帮我重新校准：

**原始论证**: [Step1-6摘要]

**跨模型反馈**:
- 模型1: [认同/不认同 + 理由]
- 模型2: [认同/不认同 + 理由]
- 模型3: [认同/不认同 + 理由]

**看空论据**: [Step7b的前3个反驳]

**问题**:
1) 基于以上反馈，我应该提升/维持/降低我的conviction吗？
2) 哪些反驳最有效？我能反驳吗？
3) 我应该调整仓位从[X]%到[Y]%吗？
4) 现在的Expected Value: 基准情况[A]% * 50% + 看多情况[B]% * 25% + 看空情况[-C]% * 25% = ?
5) 如果Expected Value < 15%，我应该放弃这个交易吗？
```

## Best Practices

### Model Selection Strategy
- **Step1 (Sector Selection)**: DeepSeek (best A-share knowledge) → Gemini Deep Research (validation)
- **Step2 (Supply Chain)**: ChatGPT or Gemini (detailed reasoning) → DeepSeek (A-share specifics)
- **Step3c (Financial Analysis)**: DeepSeek (reports/fundamentals) → ChatGPT (second opinion on risks)
- **Step4b (News Classification)**: Gemini Deep Research (web search + classification)
- **Step5c (Final Decision)**: Use Template 7 with multiple models for self-challenge

### Research Workflow Best Practices
1. **Start Broad, Verify Narrow**: Begin with sector (macro) → supply chain (meso) → companies (micro)
2. **Separate Automation from Judgment**: 
   - Automate: Data collection, extraction, initial classification
   - Human review: Financial interpretation, relationship validation, final decision
3. **Document Everything**: Keep notes on what you found, what changed your mind, what surprised you
4. **Cross-Check Systematically**: 
   - Financial reports vs news (Step3c vs Step4b)
   - News timeline vs technical moves (Step4c)
   - Fundamentals vs technical setup (Step5b vs Step5c)
5. **Question Your Assumptions**:
   - Use Template 7 before every major decision
   - Ask "What would prove me wrong?"
   - Build in a 20% margin of safety

### Risk Management Rules
- **Position Sizing**: Never risk more than 2% of portfolio on single thesis
- **Stop Loss**: Set before entering, not after losing
- **Catalyst Timing**: Know when catalyst should be realized; if not by then, exit
- **Thesis Invalidation**: If any major assumption changes, reconsider position
- **Overheating**: If stock has rallied >30% since your thesis began, reassess entry

### Time Investment Estimates
- **Step1**: 1-2 hours (sector scanning)
- **Step2**: 2-3 hours per sector (supply chain research)
- **Step3a/b**: 30-60 minutes (automatic download & extraction)
- **Step3c**: 3-5 hours per company (manual deep reading)
- **Step3.5**: 1-2 hours per supply chain (validation)
- **Step4a/b**: 1-2 hours per stock (news search & classification)
- **Step4c**: 30 minutes (conflict analysis)
- **Step5a**: 15 minutes (automatic data fetch)
- **Step5b/c**: 1-2 hours (trend analysis + decision)
- **Step6a/b/c**: 2-3 hours per BUY stock (research report search, analysis, cross-validation)
- **Step7a/b/c**: 2-4 hours (cross-model challenge, adversarial reflection, final calibration)
- **Total for 5-10 stocks**: 30-60 hours (realistic for quality research with multi-perspective validation)
- Always verify information with official sources
- Use AI as a research assistant, not a decision maker
- Understand that past performance doesn't guarantee future results
- Consider your own risk tolerance and investment horizon

## Important Disclaimers

⚠️ **Critical Reminders**:
- This skill is for **research assistance only**, not investment advice
- AI models can hallucinate or provide outdated information
- Always verify information through official channels
- Market conditions change rapidly; recent AI training data may be outdated
- Conduct your own due diligence before making investment decisions
- Past performance is not indicative of future results

**风险提示**：
- 本技能仅供研究辅助，不构成投资建议
- AI 模型可能产生幻觉或提供过时信息
- 务必通过官方渠道验证信息
- 市场瞬息万变，AI 训练数据可能滞后
- 投资前请进行独立尽职调查
- 过往表现不代表未来收益

## Integration Points

This skill works best when combined with:
- Financial data platforms (东方财富, 同花顺, Wind)
- Official company disclosures (巨潮资讯网)
- Industry research reports
- Real-time market data

## Examples

See [examples/](examples/) directory for:
- Sample sector analysis workflow
- Supply chain mapping example
- Financial report verification case study
- Cross-model validation demonstration

## Version History

- **v2.1.0** (2026-02-03): Critical Enhancements Based on Real Battle Lessons (基于实战教训的关键改进)
  - **Step2.5 (Commodity Cycle Positioning)**: NEW mandatory step for resource stocks
    - 5-indicator supply-demand framework (capacity/inventory/utilization/price/orders)
    - 4-stage cycle identification (bottom/uptrend/frenzy/collapse)
    - Avoid "waiting for pullback at cycle peak" trap (白银踏空案例)
  - **Step3c Enhancement (Resource Moat Rating)**: NEW 20% weight dimension
    - Resource monopoly > Technology monopoly > Market share > Brand/customer
    - 5-tier rating system (national monopoly = 5, pure tech = 1)
    - Cycle-adjusted PE calculation (vs misleading historical PE)
  - **Step3.6 (Geopolitical Risk)**: NEW assessment for resource/global supply chain stocks
    - 3-dimension risk scoring (supply chain 50% + customer 30% + asset 20%)
    - Deglobalization revaluation logic (overseas assets can be opportunity not just risk)
    - Position limit guidelines (0-3 points = satellite 10%, 7-10 points = core 30-40%)
  - **Step5c Revolution (3-3-4 Position Building)**: Replacing traditional "wait for perfect entry"
    - **30% immediate**: Avoid complete踏空, get observation rights
    - **30% pullback order**: 5-8% limit with 3-5 day deadline (not stubborn 15%+ waiting)
    - **40% breakout confirmation**: Right-side追加 on catalyst + technical alignment
    - Moving stop-loss (20-day MA or ATR 2x) replacing fixed stop-loss
  - **Psychological Trap Warning System**: 4 traps identified from real失败 cases
    - Trap 1: Fear of heights (30元PE=20 vs 3元PE=100, 30元更便宜)
    - Trap 2: Left-side order hanging (等回调12%永远等不到 → 仓位0%)
    - Trap 3: Static anchoring (支撑位动态上移, 不是固定价格)
    - Trap 4: Allocation execution failure (选对股票但仓位0% = 判断再对也白搭)
  - **Execution Checklist**: Mandatory pre-trade verification
    - Force execution of allocation plan (not just "planning" but "doing")
    - 7-item checklist before building position
  - **Real Battle Case Studies**: 3 detailed reports integrated
    - 白银踏空 (correct thesis, zero profit due to waiting for pullback)
    - 铝龙头踏空 (100% win rate but missed main rally, 0% core position)
    - 铜金资源 (geopolitical risk vs deglobalization opportunity)
  - **New Templates**: 2 additional templates
    - Template 8: Commodity cycle positioning (Step2.5)
    - Template 9: 3-3-4 position building execution plan
  - **Architecture Update**: Workflow diagram updated with Step2.5 and Step3.6
  - **Step6 (Research Report Cross-Validation)**: NEW mandatory step for BUY-recommended stocks
    - Step6a: Search and download recent research reports (3-6 months, top-tier brokers)
    - Step6b: Cross-validate our thesis vs broker consensus, identify conflicts and blind spots
    - Step6c: Update final recommendation and adjust conviction level
    - Avoid confirmation bias by incorporating independent professional research
    - Template 10: Research report cross-validation framework
  - **Step7 (Multi-Perspective Reflection)**: NEW mandatory step before final decision (斗蛊与反思)
    - Step7a: Cross-model challenge - use 2-3 different AI models to question our picks
    - Step7b: Adversarial reflection - argue AGAINST our own thesis, pre-mortem analysis
    - Step7c: Final conviction calibration - adjust position sizes based on expected value
    - Avoid groupthink and single-model bias
    - Force adversarial thinking before committing capital
    - Template 11: Multi-perspective reflection framework
    - Kill criteria definition and failure scenario planning

- **v2.0.0** (2026-02-03): Comprehensive workflow restructuring
  - **Step3 (Fundamentals)**: Split into 3 layers - Download/Extract/Analysis
    - Step3a: Automated financial report download
    - Step3b: Automated content extraction with OCR/AI
    - Step3c: Manual deep-reading + AI assistance for analysis
  - **Step3.5 (Supply Chain Verification)**: New optional verification step
    - Cross-validate supply chain relationships with financial reports
    - Identify bottleneck positions and concentration risks
  - **Step4 (News & Events)**: Split into 3 layers - Search/Classification/Validation
    - Step4a: Automated news collection from multiple sources
    - Step4b: AI-assisted classification + human validation
    - Step4c: News-technical alignment check to detect conflicts
  - **Step5 (Technical Analysis)**: Split into 3 layers - Data/Trend/Decision
    - Step5a: Automated technical data collection and indicator calculation
    - Step5b: Trend analysis with fundamental & news cross-check
    - Step5c: Integrated decision-making with risk management
  - **New prompt templates**: 4 additional templates for Step3.5-5 validation
  - **New tools development**: Scripts for automation at layers a (data collection)
  - **Architecture diagram**: Complete workflow visualization added

- **v1.0.0** (2026-02-03): Initial release
  - Core 5-phase workflow
  - 5 prompt templates for different research stages
  - Cross-model validation framework
  - Risk disclaimers and best practices
  - Core 5-phase workflow
  - 5 prompt templates for different research stages
  - Cross-model validation framework
  - Risk disclaimers and best practices

---

**Note**: Markets carry inherent risks. This skill provides a systematic research framework but does not guarantee investment success. Always make decisions based on your own analysis and risk tolerance.

**注**：市场有风险，入市需谨慎。本技能提供系统化的研究框架，但不保证投资成功。请基于自身分析和风险承受能力做出决策。
