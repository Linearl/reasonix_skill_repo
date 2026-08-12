# run_result.json 字段契约

定义 `run_result.json` 的字段含义与约束，供 CI、报表和自动化消费。

Schema 文件：`config/run_result.schema.json`

## 顶层字段

- `status`: `pass` | `blocked`
- `mode`: `interactive` | `non_interactive`
- `config`: 配置来源信息
- `summary`: 修复统计
- `quality`: 质量闸门数据
- `blocking_reasons`: 阻塞原因列表
- `artifacts`: 产物路径映射
- `timestamp`: ISO 时间字符串

## quality 约束

- `tests`: `pass` | `fail` | `skip`
- `format`: `pass` | `fail` | `skip`
- `perf_regression_pct`: number
- `perf_threshold_pct`: number

## blocking_reasons 约束

每项应包含：
- `code`: 见 `docs/block_reason_codes.md`
- `message`: 人类可读说明
- `location`: 可选，相关文件或流程节点

## 判定规则

- `status=pass`：`blocking_reasons` 应为空
- `status=blocked`：`blocking_reasons` 应非空

## 校验建议

1. 先做 JSON 语法校验。
2. 再用 `config/run_result.schema.json` 做结构校验。
3. 若 `status=blocked`，`blocking_reasons[*].code` 必须来自 `docs/block_reason_codes.md`。
