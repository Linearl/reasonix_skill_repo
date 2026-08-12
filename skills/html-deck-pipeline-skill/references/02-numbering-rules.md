---
description: 文件编号与命名规则：版本号管理、slides/ 目录结构、slides-config.json 格式
---
# 编号与命名规则

适用范围：`html-deck-pipeline-skill-v2` 全流程。

## 目标

- 文件可稳定排序、可并行生成、可自动合并
- 版本迭代清晰（`v-01`、`v-02`...）
- 沟通记录可追溯（真实日期）

## 一、目录结构（固定）

- `{work_dir}/00-input/`
- `{work_dir}/10-storyboards/v-XX/`
- `{work_dir}/20-html/v-XX/`
- `{work_dir}/90-tests/`

其中 `v-XX` 为两位版本目录（如 `v-01`、`v-02`）。

## 二、核心编号规则

### 1) 版本号

- 格式：`v-XX`
- 规则：分镜、HTML、合并稿必须同版本。

### 2) 分片号

- 格式：`{part_no:02d}`，从 `01` 递增。
- 推荐分片名：`开头/基础篇/进阶篇/收官篇/结尾`（可按需调整）。

### 3) 分镜命名（强制）

- 格式：`{part_no:02d}-{part_name}-分镜稿.md`
- 示例：`01-开头-分镜稿.md`

### 4) HTML 幻灯片命名（强制）

- 存放路径：`slides/<part_id>/<NN-description>.html`
- `<part_id>` 对应 `slides-config.json` 中的章节键（如 `ch01`）
- `<NN>` 为两位数字前缀，`<description>` 为英文 slug
- 示例：`slides/ch01/01-cover.html`、`slides/ch02/02-architecture.html`

### 4.1) slides-config.json 配置

- 幻灯片清单不通过文件名推断，由 `slides-config.json` 显式定义
- 每项包含 `part`（章节键）、`file`（文件名）、`title`（显示标题）
- deck.js 启动时通过 fetch 读取此配置

### 4.2) 页内右上角编号规则

- 每页 HTML 内的 `page-chip` 使用章节内局部编号（如 `01 / 03`）。
- deck.js 自动处理全局编号映射。

### 5) 沟通记录命名（强制真实日期）

- 原始记录：`{stage}-raw-round{round_no:02d}-{yyyymmdd}.md`
- 总结记录：`{stage}-summary-round{round_no:02d}-{yyyymmdd}.md`
- 冻结快照：`{stage}-freeze-input-snapshot-{yyyymmdd}.md`
- `{stage}` 为阶段标识：`A`（问）、`B`（架）、`C`（镜）、`D`（页）、`E`（验）、`F`（归）

示例：

- `A-raw-round01-20260316.md`
- `A-summary-round01-20260316.md`
- `A-freeze-input-snapshot-20260316.md`

> 禁止保留 `YYYYMMDD` 占位名。

## 三、合并稿命名（推荐）

- 格式：`{topic_code}-{scheme_name}-合并.html`
- 说明：合并稿可保留 `topic_code / scheme_name`，便于多方案并存。

## 四、测试记录命名（推荐）

- 格式：`{topic_code}-90-技能测试记录_{yyyymmdd}.md`

## 五、执行注意

1. 阶段 A 结束后立即完成真实日期重命名/落盘。
2. 阶段 C/D 生成文件时必须检查编号连续性（01,02,03...）。
3. 文件名必须保留数字前缀，避免中文排序错位。
4. 进入 `v-(n+1)` 时，先升级分镜，再生成同版本 HTML。
