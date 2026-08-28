# kb-retriever 技能 — 来源说明

## 原始来源
- **仓库**: [ConardLi/garden-skills](https://github.com/ConardLi/garden-skills)（11.5k ⭐，MIT 协议）
- **原始路径**: `skills/kb-retriever/`
- **获取时间**: 2026-08-24

## 修改说明
**无修改** — 直接复制自原始仓库，未做任何改动。

## 功能
面向本地知识库目录的检索和问答助手。核心流程：分层索引导航 → 遇到 PDF/Excel 时先读取 references 学习处理方法 → 处理文件后再检索。

## 依赖
```bash
pip install pdfplumber pandas
```

## 许可证
MIT © ConardLi（原始作者）
