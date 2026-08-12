# 阶段 A 执行输入快照（冻结）

- 冻结时间：{iso_date}
- 主题代码：`{topic_code}`
- 主题名称：{topic_title}
- 版本：`{version}`
- 风格：`{style_id}`
- 分片：{part_names_cn}
- 原始沟通记录：`00-input/comms/A-raw-round{round_no:02d}-{record_date}.md`
- 总结沟通记录：`00-input/comms/A-summary-round{round_no:02d}-{record_date}.md`

## 阶段边界

- 本轮执行：创建与优化产物，完成分镜与 HTML 链路校验。
- 不执行：安装依赖、打包、发布。
