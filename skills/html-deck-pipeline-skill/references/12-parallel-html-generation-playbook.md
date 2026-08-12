---
description: HTML 页面生成作业手册：阶段 D 并行生成要点、文件命名、质量控制与失败回退
---
# HTML 页面生成作业手册

## 生成前准备

- 已完成并冻结分镜
- 已冻结风格资产（`style-contract` + `style-showcase`）
- 已确认版本号与命名规则

## 并行生成要点

- 先读取已冻结风格资产，不得自创风格来源
- 必须同时读取：`style-contract-<style-id>.md` 与 `style-showcase-<style-id>.html`
- 产出前先回传”已读取文件清单”，未回传视为未满足前置条件
- 示例用于对齐风格语言，不是逐页照抄
- 需满足冻结后的 `ratio_mode`（默认 16:9）、可访问性基线、统一版本号

## 文件命名

- HTML 幻灯片存放：`slides/<part_id>/<NN-description>.html`
- 示例：`slides/ch01/01-cover.html`
- 幻灯片清单由 `slides-config.json` 显式定义

## 质量控制

- 页面内容仅保留观众可见信息，讲者提示放备注链路
- 不允许同章节连续复用单一版式骨架
- 每页必须包含 `<section class=”slide”>` 根元素

## 失败回退

- 如出现风格漂移、页序错乱、同质化严重，回退到分镜阶段修正后再生成
