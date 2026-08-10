---
name: github-issue-triage
description: 自己的 GitHub 仓库 issue 自动化闭环：收集→分析→修复→验证→关闭，含关闭前证据硬门槛与安全护栏（依赖 github-mcp-server）
---

# GitHub Issue 自动分诊修复技能（github-issue-triage）

对**自己的仓库**执行"收集 issue → 分析 → 修复 → 验证 → 关闭"完整闭环。依赖 github-mcp-server（44 个 `mcp__github__*` 工具），token 需已开 Issues: Read and write 权限（见记忆 [[github-mcp-server-install]]）。

## 何时使用

用户要求"处理我仓库的 issues""把 open issues 清一清""修复后关闭 issue""issue 自动化管理"等。仅限用户**自己有写权限**的仓库；对别人的仓库只做只读分析，绝不关闭。

## 流程（五步闭环）

### 1. 收集
- `list_issues(state=open, owner, repo)` 或 `search_issues(query="repo:owner/repo is:issue is:open")` 拉全量 open issues
- 按影响面分类：bug（可复现？）/ feature / question / duplicate；统计总数，先给用户一个清单概览再动手
- 标注疑似重复：先 `search_issues` 查同类 issue，确认重复后合并评论并关闭（state_reason=duplicate）

### 2. 分析（读全再动手）
- 每条 issue：`issue_read(get)` 读 body + `issue_read(get_comments)` 读讨论
- 判断：a) 能修复 b) 缺信息需询问 c) 不是 bug（用法问题）d) 重复 e) 超出范围
- 缺信息 → 评论列出需要的复现步骤/版本/日志，加 label（如 `needs-info`），**不要关闭**
- 环境信息核对：检查 body 里的版本号/OS/复现步骤是否齐全

### 3. 修复
- 仓库已在本地工作区 → 直接在本地改；否则先 `git clone` 到临时目录（走代理）
- 遵守仓库既有约定（CLAUDE.md/AGENTS.md/REASONIX.md 优先）
- 提交纪律：`git add <明确路径>`（禁止 `git add -A`），`git status --short` 核对后再 commit
- 需要推送时确认远端和分支正确；push 走 https（如需代理按本机网络配置）

### 4. 验证（关闭前的硬门槛）
- 运行最相关的测试/构建，**必须能复现修复效果**（前后对照）
- 无法验证的修复不得声称完成；如实说明验证到什么程度
- 修复未落地（未 commit/未 push）**禁止关闭 issue**

### 5. 关闭（带状态原因）
- 修复完成：先评论（`add_issue_comment`）说明"修了什么、验证结果、版本号/commit"，再 `issue_write(method=update, state=closed, state_reason=completed)`
- 重复：评论链接原 issue 后关闭（state_reason=duplicate）
- 不计划修复：评论理由后关闭（state_reason=not_planned）
- 每处理一条，向用户汇报一条（处理了 #N：结论 + 证据链接）

## 安全护栏（违反即停）

1. **只动有写权限的仓库**；公共仓库/他人仓库只读
2. **关闭前必须有证据**：修复 commit 已推送 + 验证命令已跑，缺一不可
3. **先评论后关闭**：用户和 reporter 都能看到结论，禁止静默关闭
4. 批量处理前先给用户清单确认；涉及删除文件/强制操作的按"删除/破坏性操作安全"教训执行（先 ls 确认、单目标、回收语义）
5. 403 报错 = token 权限不够，提醒用户去 GitHub token 编辑页加权限，不要绕过
6. 不确定是否该关闭的 issue，保留 open 并评论说明，把决定权交给用户

## 参考
- 工具：`mcp__github__*`（list_issues / issue_read / issue_write / add_issue_comment / search_issues）
- 配置与排错：[[github-mcp-server-install]]
- 提交 issue 的上游流程：`gh-issue-submit` 技能（本技能是"管理自己的仓库"，那个是"向任意仓库提交"）
