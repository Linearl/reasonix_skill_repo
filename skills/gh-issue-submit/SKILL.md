---
name: gh-issue-submit
description: 用 gh CLI 提交 GitHub issue 的完整流程：模板发现（分支差异）、查重、权限切换陷阱、提交与验证
---

# GitHub Issue 提交技能（gh-issue-submit）

用 `gh` CLI 把功能请求 / bug 报告 / 改进建议提交到任意 GitHub 仓库 issue 的完整流程。包含模板发现、查重、权限陷阱处理和提交验证。

## 适用场景

- 用户要求"给某仓库提个 issue / feature request / bug report"
- 用户给了 issues/new 链接（含 `?template=...` 参数）或直接点名仓库
- 用户要求"帮我写并提交 issue"

## 核心步骤

### 1. 解析目标仓库与模板

- 从链接或用户描述提取 `owner/repo`。
- **模板位置因默认分支而异**：先查仓库默认分支和分支列表：
  ```bash
  gh api repos/<owner>/<repo>/branches --jq '.[].name'
  gh api repos/<owner>/<repo> --jq '.default_branch'
  ```
- 列出 ISSUE_TEMPLATE 目录（分别在默认分支和 main-v2/v2 等分支下找）：
  ```bash
  gh api "repos/<owner>/<repo>/contents/.github/ISSUE_TEMPLATE?ref=<branch>" --jq '.[].name'
  ```
- **注意格式差异**：有的仓库用 `.md` 模板（GitHub 自动表单），有的用 `.yml` form 模板（Version line dropdown / textarea 字段）。用户给的 `?template=xxx.yml` 链接可能与实际文件名不符（如 v1 分支是 `feature_request.md`、v2 分支是 `feature_request.yml`）——以实际文件为准。
- 读取模板内容了解必填字段：
  ```bash
  gh api "repos/<owner>/<repo>/contents/.github/ISSUE_TEMPLATE/<file>?ref=<branch>" --jq '.content' | base64 -d
  ```

### 2. 查重（必做，避免重复 issue）

```bash
gh api "search/issues?q=repo:<owner>/<repo>+is:issue+in:title+<关键词>" --jq '.items[] | {number, title, state}'
```
- 用多个关键词组合搜（功能名、症状、中英文都试）。
- 找到相关 open issue 时：**不重复提交**——要么在已有 issue 下评论补充，要么新 issue 明确区分视角并引用旧 issue 编号（如"这是 #XXXX 提到的 follow-up"）。

### 3. 撰写正文

- **按模板字段组织**：yaml form 模板用 `### <字段 label>` 作为 markdown 标题分隔（GitHub 提交后表单渲染依赖这些标题）。
- 结构建议（通用）：
  - 现状/问题：谁遇到、当前行为、为什么是问题
  - 期望/方案：命令、UX 草图、API 草图、实现草图（引用仓库内模块路径更佳）
  - 范围界定：什么不做 / 与相邻 issue 的关系
- **用仓库社区语言**：国际开源项目用英文，中文优先项目用中文。
- 写完后存到工作区临时文件（如 `issue-<简述>.md`），避免 shell 转义问题。

### 4. 权限检查与账号切换（⚠️ 最容易踩坑）

**GITHUB_TOKEN 环境变量会覆盖 gh 的所有账号管理！**

```bash
gh auth status
```
- 若 active 账号的 token 是 `github_pat_...`（fine-grained PAT），**通常没有 `issues: write` 权限**，提交会报 `GraphQL: Resource not accessible by personal access token (createIssue)`。
- 查看所有账号及 scope：`gh auth status` 会列出 keyring 账号。有 `repo` scope 的 OAuth token（`gho_...`）可以写 issues。
- 切换账号前必须先清掉环境变量（否则切不动）：
  ```bash
  unset GITHUB_TOKEN
  gh auth switch --user <用户名>
  ```
- 注意：`unset GITHUB_TOKEN` 只在当前 shell 命令内生效，每条命令都要带上（如 `unset GITHUB_TOKEN; gh issue create ...`），或者用 `env -u GITHUB_TOKEN gh ...`。

### 5. 提交

```bash
unset GITHUB_TOKEN
gh issue create --repo <owner>/<repo> \
  --title "[Feature]: <一句话标题>" \
  --body-file <正文文件路径>
```
- `--body-file` 优于 `--body`（长正文免转义）。
- 返回的 URL 即 issue 地址。

### 6. 验证

```bash
unset GITHUB_TOKEN
gh issue view <编号> --repo <owner>/<repo> --json number,title,state,url --jq '{number,title,state,url}'
```
- 确认 state=OPEN、作者、标题正确。把 URL 汇报给用户。

## 注意事项

- **version line 类下拉字段**：模板若有版本选择（如 "v2 — Go rewrite" / "v1 — Legacy"），优先选活跃开发线；用户说"提交到 v2"时选 main-v2 对应项。
- **标签**：默认模板自带 `enhancement` 等 label，无需手动加；除非用户要求。
- **不要替换用户的账号凭据**：只用 `gh auth switch` 切换已登录账号，不要读写 token 明文。
- 正文文件属于临时产物，提交成功后保留在 `global-workspace` 即可（用户可能想复用）。
