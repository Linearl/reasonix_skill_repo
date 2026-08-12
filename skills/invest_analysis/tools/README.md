# Investment Analysis Tools (投资分析工具集)

本目录包含了 invest_analysis 技能的各个步骤的自动化工具脚本。自动化目前对 A 股支持更完整，港股部分环节需要手动补充。

## 🎯 工具概览

**标的清单字段建议**：`name`、`track`、`code`、`market`
- A股：`market: A`，`code`=6位
- 港股：`market: HK`，`code`=5位（前导0保留）

### Step3a: Financial Report Download (财报下载)

**文件**: `step3a_download_reports.py`

**功能**: 从巨潮资讯自动下载 A 股上市公司的年报和季报（港股需手动）

**使用方法**:
```bash
python step3a_download_reports.py \
    --input ../step2/02_标的清单.yaml \
    --output ../step3/financials
```

**输出**:
- `step3/financials/{代码_名称}/` - 下载的PDF报告
- `step3/financials/download_metadata.json` - 下载元数据
- `step3/financials/step3a_download_report.md` - 下载报告

**依赖**:
- `pyyaml` - 读取YAML配置
- (可选) 根据实际API实现需要的HTTP库 (requests, selenium, etc.)

**注意**: 当前为框架实现，需要根据实际数据源（巨潮资讯API、Web爬取等）补充具体API调用代码

---

### Step6a: Research Report Download (研报下载) ⭐

**文件**: `step6a_download_research_reports.py`

**功能**: 从巨潮资讯自动搜索和下载各大券商的研究报告（A股上市公司）

**使用方法**:
```bash
# 默认6个月
python step6a_download_research_reports.py

# 自定义周期
python step6a_download_research_reports.py --days 90
```

**输出**:
- `step6/reports/{代码_名称}/` - 下载的PDF研报
- `step6/reports/research_reports_metadata.json` - 元数据
- `step6/reports/research_reports_index.yaml` - 结构化索引
- `step6/reports/step6a_download_report.md` - 下载报告

**依赖**: `pyyaml`、`requests`

**覆盖**: 16家主流券商，A股自动化，港股需手动补充

**文档**: 见 `STEP6A_GUIDE.md`

---

### Step3b: Financial Report Content Extraction (财报内容提取)

**文件**: `step3b_extract_content.py` (待开发)

**功能**: 从下载的PDF报告中提取关键信息（产品分类、客户、订单、风险因素等）

**使用方法**:
```bash
python step3b_extract_content.py \
    --input ../step3/financials/ \
    --output ../step3/extracts/
```

**输出**:
- `step3/extracts/{代码_名称}_annual_extract.txt` - 提取的年报内容
- `step3/extracts/{代码_名称}_quarterly_extract.txt` - 提取的季报内容
- `step3/extracts/extraction_index.yaml` - 提取索引

**依赖**:
- `pdfplumber` 或 `pypdf` - PDF文本提取
- (可选) `pytesseract` - 图片文字识别 (OCR)

---

### Step3.5: Supply Chain Verification (产业链验证)

**文件**: `step3.5_supply_chain_verify.py`

**功能**: 交叉验证 Step2 的产业链假设是否在财报和新闻中得到确认

**使用方法**:
```bash
python step3.5_supply_chain_verify.py \
    --supply-chain ../step2/02_产业链挖掘_人形机器人_YYYYQx.md \
    --analysis ../step3/analysis/ \
    --news ../step4/classified/ \
    --output ../step3.5/
```

**输出**:
- `step3.5/report/03.5_供应链验证表.md` - 验证结果表格
- `step3.5/report/03.5_供应链风险地图.md` - 风险地图

**依赖**:
- `pyyaml` - 读取YAML配置
- 标准库：re, logging, json

**特点**:
- ✅ 验证供应关系是否在财报中被提及
- ✅ 检查新闻中的合作确认
- ✅ 识别瓶颈位置（单一供应商/客户）
- ✅ 生成置信度评分 (0-100%)

---

### Step4a: News Search & Collection (新闻搜索)

**文件**: `step4a_search_news.py`

**功能**: 从多个数据源自动搜索和收集 A 股/港股新闻、公告和事件（CNINFO公告仅A股）

**使用方法**:
```bash
# 默认搜索过去60天
python step4a_search_news.py \
    --input ../step2/02_标的清单.yaml \
    --output ../step4/raw_data/

# 自定义搜索周期
python step4a_search_news.py \
    --input ../step2/02_标的清单.yaml \
    --output ../step4/raw_data/ \
    --days 30
```

**输出**:
- `step4/raw_data/{代码_名称}_news_raw.yaml` - 原始新闻数据
- `step4/raw_data/news_index.yaml` - 新闻索引
- `step4/raw_data/step4a_collection_report.md` - 收集报告

**依赖**:
- `pyyaml` - YAML处理
- 标准库：logging, json, datetime

**数据源**:
- 巨潮资讯 (CNINFO) - 官方公告
- 新闻平台 - 新闻媒体
- 事件日历 - 重要事件

**注意**: 当前为框架实现，需要集成真实数据源

---

### Step5a: Technical Data Collection (技术数据获取)

**文件**: `step5a_fetch_technical_data.py` (待开发)

**功能**: 获取历史价格数据并计算技术指标

**使用方法**:
```bash
python step5a_fetch_technical_data.py \
    --input ../step2/02_标的清单.yaml \
    --output ../step5/raw_data/ \
    --days 120
```

**输出**:
- `step5/raw_data/{代码_名称}_technical_data.csv` - 技术数据
- `step5/raw_data/technical_index.yaml` - 技术数据索引

**依赖**:
- `pandas` - 数据处理
- `yfinance` 或 `tushare` - 行情数据获取

**计算指标**:
- MA20, MA60, MA250 - 均线
- 20/60/250 日高低点
- ATR, 日涨跌幅 - 波动率指标

---

## 🛠️ 快速开始

### 环境配置

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install pyyaml requests
# 根据需要安装其他依赖
```

### 完整工作流运行

```bash
# 假设你已经完成了 Step1 和 Step2，有了 02_标的清单.yaml

# Step3a: 下载财报
python step3a_download_reports.py \
    --input ../step2/02_标的清单.yaml \
    --output ../step3/financials

# Step3.5: 验证产业链
python step3.5_supply_chain_verify.py \
    --supply-chain ../step2/02_产业链挖掘_YYYYQx.md \
    --analysis ../step3/analysis/ \
    --news ../step4/classified/ \
    --output ../step3.5/

# Step4a: 搜索新闻
python step4a_search_news.py \
    --input ../step2/02_标的清单.yaml \
    --output ../step4/raw_data/ \
    --days 60
```

---

## 📝 开发指南

### 如何扩展现有工具

已内置基础数据源（CNINFO公告 + Bing News RSS）。如需更高质量数据源，可自行扩展接入。

### 添加新的数据源

在 `NewsCollector` 中添加新方法：

```python
def search_custom_source(self, code: str) -> List[Dict]:
    """从自定义数据源搜索新闻"""
    # 实现你的搜索逻辑
    pass
```

---

## 🧰 API不可用时的替代方案

当CNINFO或新闻源不可访问时，可使用以下手动/半自动流程：

1) **财报下载（Step3a）**
    - A股：手动在巨潮资讯搜索公司公告 → 下载PDF到 `step3/financials/{代码_名称}/`
    - 港股：在 HKEXnews 或公司IR页面下载年报/中报/季报 → 放入同目录
    - 文件命名建议：`YYYYMMDD_annual.pdf` / `YYYYMMDD_q1.pdf`

2) **新闻收集（Step4a）**
    - A股：交易所公告页/公司投资者关系页面
    - 港股：HKEXnews公告页 + 公司IR页面
    - 通过搜索引擎检索关键词（公司名+"公告"/"业绩"/"订单"/"合作"）
    - 统一整理为 `step4/raw_data/{代码_名称}_news_raw.yaml`

3) **事件日历**
    - 财报披露日期、股东大会、业绩说明会可来自公司公告或IR页面
    - 记录在同一YAML文件中，category设为 `event`

---

## ⚠️ 注意事项

1. **API密钥**: 某些数据源可能需要API密钥，请妥善管理
2. **速率限制**: 批量数据抓取可能触发速率限制，建议添加延迟
3. **法律合规**: 请确保web爬取符合相关网站的robots.txt和服务条款
4. **数据准确性**: 自动化工具获得的数据需人工验证

---

## 🤝 贡献

欢迎提交改进建议或贡献代码！请注意：
- 保持代码格式一致
- 添加适当的错误处理和日志
- 更新本README中的说明

---

## 📜 许可证

与主项目相同 (MIT License)

