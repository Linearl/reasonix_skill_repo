# Step6a 研报下载脚本 - 使用指南

## 📋 概述

Step6a (`step6a_download_research_reports.py`) 是 invest_analysis 技能的 **Step6 (研报交叉验证)** 的自动化工具，用于从巨潮资讯自动搜索和下载各大主流券商对上市公司的研究报告。

| 功能维度 | 说明 |
|---------|------|
| **支持范围** | A股上市公司（6位股票代码） |
| **数据源** | 巨潮资讯（CNINFO）- 官方权威数据源 |
| **券商覆盖** | 16家主流券商（中信、海通、中泰、招商等） |
| **查看周期** | 可配置，默认过去180天（6个月） |
| **输出格式** | PDF报告 + JSON元数据 + YAML索引 + Markdown报告 |

---

## 🚀 快速使用

### 基本用法

```bash
# 使用默认参数
python step6a_download_research_reports.py

# 查看帮助
python step6a_download_research_reports.py --help
```

### 常见场景

```bash
# 快速决策（过去1个月）
python step6a_download_research_reports.py --days 30

# 常规研究（过去6个月，推荐）
python step6a_download_research_reports.py --days 180

# 深度分析（过去1年）
python step6a_download_research_reports.py --days 365
```

---

## 📊 输出文件

运行脚本后的输出结构：

```
step6/reports/
├── 300750_宁德时代/
│   ├── 20260204_中信证券.pdf
│   ├── 20260128_海通证券.pdf
│   └── 20260115_中泰证券.pdf
├── research_reports_metadata.json    # 元数据统计
├── research_reports_index.yaml       # 结构化索引
└── step6a_download_report.md         # 下载日志
```

---

## ⚙️ 参数说明

| 参数 | 简写 | 默认值 | 说明 |
|-----|------|--------|------|
| `--input` | `-i` | `../step2/02_标的清单.yaml` | 输入YAML文件 |
| `--output` | `-o` | `../step6/reports` | 输出目录 |
| `--days` | `-d` | `180` | 查看周期（天） |

---

## 🎯 主要功能

✅ YAML股票清单加载  
✅ A股/港股自动识别  
✅ 巨潮资讯研报搜索  
✅ PDF下载管理  
✅ 元数据统计  
✅ 结构化索引生成  
✅ Markdown报告生成  
✅ 错误处理和日志  

---

## 🐛 常见问题

### 超时或连接错误
重新运行脚本（已存在文件会自动跳过）

### 港股报错
正常行为，脚本仅支持A股自动化，港股需手动补充

### 未找到研报
可能来自非主流券商，需手动从巨潮资讯搜索

---

## 📞 获取帮助

```bash
# 查看脚本帮助
python step6a_download_research_reports.py --help

# 查看生成的报告
cat step6/reports/step6a_download_report.md
```

---

**祝你研究顺利！** 🚀
