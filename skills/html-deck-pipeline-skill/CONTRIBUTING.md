# Contributing

欢迎贡献！以下是一些参与方式：

## 报告问题

使用 GitHub Issues 报告 bug 或提出功能建议。请包含：
- 复现步骤
- 预期行为与实际行为
- 环境信息（Python 版本、浏览器版本）

## 新增主题

1. 在 `container/css/theme/<name>/` 下创建 `tokens.css`，定义全部 30+ 设计令牌
2. 在 `container/css/config.yaml` 中添加主题条目
3. （可选）在 `examples/<name>/` 下创建 style-contract 和 style-showcase
4. 运行 `python scripts/validate_tokens.py --theme <name>` 确认 token 完整

## 新增字号方案

1. 在 `container/css/fontsize/` 下创建 `<name>.css`，定义 `--text-xs` ~ `--text-xl`
2. 在 `container/css/config.yaml` 中添加字号条目

## 代码修改

- **JavaScript**：纯 ES5 IIFE 模块，通过 `window.__xxx` 暴露公共 API
- **Python**：标准库 + PyYAML，serve.py 需保持无外部依赖
- **CSS**：所有样式通过 CSS 自定义属性引用 token，禁止在组件中硬编码颜色/字号

### 编辑器模块约定

- `editor-state.js` — 共享状态（`window.__editorState`），纯数据，不含 DOM 操作
- `editor-undo.js` — 撤销/重做管理器（`window.__undoManager`），Command 模式
- `editor.js` — 编辑器主模块（`window.__editor`），读取 `__editorState` + `__undoManager`

### 运行测试

```bash
# 单元测试
node container/tests/test-editor-unit.js

# E2E 测试
python container/tests/test-editor-e2e.py --target-dir <dir>
```

提交 PR 前请确保所有测试通过。
