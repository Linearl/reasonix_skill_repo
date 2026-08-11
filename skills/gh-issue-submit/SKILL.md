---
name: gh-issue-submit
description: 用 gh CLI 提交高质量 GitHub issue：模板发现、查重（含已关闭 issue 阅读）、源码调研根因、权限切换陷阱、computer use 回退、提交与验证
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
- **搜索限制**：`search/issues` 的 q 中 OR/AND 操作符合计不能超过 5 个（超限报 422 Validation Failed），多关键词拆成多个查询分别搜（如会话排序 / 会话分组各搜一次）。
- **已关闭的旧 issue 也要读**：搜到相关但已 closed 的 issue 时，用 `gh issue view <编号> --comments` 读关闭原因与维护者评论——
  - 若维护者留下"场景未覆盖可开 focused issue"之类的口子：新 issue 明确回应它并引用编号，采纳率显著提升（实例：#3177 关闭时维护者邀请 focused issue → #8194 精准切入）；
  - 若维护者明确拒绝某方案：新 issue 必须说明视角差异（如"仅 UI 层组织视图，不引入第二套手工层级"），否则大概率被同理由关闭。

### 2.5 源码调研（有源码则必做，feature 与 bug 一视同仁）

- 公开仓库可直接 `git clone --depth 1`（需代理时走本机代理）；本地已有源码优先复用（如本机 `%TEMP%xsrc` 有 DeepSeek-Reasonix 源码），避免重复 clone。
- **bug**：定位问题链路的三环节——写入端（标题/状态何时落盘）/ 事件发送端（是否发事件）/ 前端刷新端（监听是否覆盖目标 UI）。每环节给 file:line 证据，再给分级修复建议（最小改动优先，贴现状代码）。能写出"写入端无延迟、事件已发、前端漏刷"这类定位，维护者可直接动手。
- **feature**：读现有实现（相关模块路径、数据结构、既有事件/API），正文引用模块路径与现状代码，方案说明与现状的衔接点（改哪里、复用哪个函数）——"可照单开发"的规格书比空泛需求采纳率高得多。
- 无法 clone / 无源码时：正文明确标注"未做源码调研"，避免误导维护者。

### 3. 撰写正文

- **按模板字段组织**：yaml form 模板用 `### <字段 label>` 作为 markdown 标题分隔（GitHub 提交后表单渲染依赖这些标题）。
- **标题规范**：`[Feature]:` / `[Bug]:` 前缀 + 一句话概括 + 副标题式补充（可带根因关键词，利于检索），如 `[Bug]: 会话内改名后侧边栏延迟更新——事件未刷新列表快照`。
- **bug 报告结构**：复现步骤（编号列表，含反例对照）/ 期望行为 / 实际行为 / **根因分析**（读源码后给 file:line 证据）/ 建议修复（分档：最小改动优先，贴现状代码 + 改动点）。
- **feature 报告结构**：要解决的问题（真实场景 + 反例）/ 建议方案（含可选增强）/ 范围界定（什么不做）。
- 正文的根因/现状部分**必须来自 2.5 的源码调研**，禁止凭空猜测实现细节。
- **关联策略**：与既有 issue 的关系写明"互补但不依赖"或"follow-up of #XXXX"，避免被合并；明确区分视角（如"即使 #XXXX 修复，本场景仍存在"）。
- **语言**：默认直接中文正文；国际项目可英文正文 + 中文评论双版（先问用户）。
- 写完后存到工作区临时文件（如 `issue-<简述>.md`），避免 shell 转义问题。

### 4. 权限检查与账号切换（⚠️ 最容易踩坑）

**凭据来源（先搞清楚手上有哪两种凭据）**：
- `github_pat_...`（fine-grained PAT）：你自己在 GitHub 设置的，存于环境变量 GITHUB_TOKEN/GH_TOKEN；写权限**仅限自己拥有的仓库**（All repositories 不含第三方仓库）——即使勾了 Issues: write，对第三方仓库提交也报 403，**改 token 权限无法解决**。
- `gho_...`（OAuth user token）：`gh auth login` 走浏览器 OAuth 流程时生成，存入系统凭据管理器（Windows Credential Manager，即 gh 的 keyring）；scopes 默认含 `repo`，权限等同于网页会话——**可以对任意公开仓库提 issue**（无需 collaborator）。
- 判定：`gh auth status` 看 active 凭据前缀与 scope。
- **向第三方仓库提交前，若 active 凭据是 `github_pat_`（fine-grained PAT），不要硬提交（必 403）——主动向用户请求 OAuth 令牌**：
  1. 先检查 keyring 是否已有 OAuth 凭据：`gh auth status` 中是否列出 `gho_` 开头的 keyring 账号；
  2. 若有：提示用户确认使用该凭据（`env -u GITHUB_TOKEN -u GH_TOKEN gh auth switch` 场景），并说明 fine-grained PAT 对第三方仓库无效；
  3. 若没有：请求用户执行浏览器 OAuth 授权（一次性，之后常驻 keyring）：
     ```bash
     gh auth login -h github.com -p https -w   # 浏览器授权后生成 gho_ 令牌
     ```
     向用户说明这是 gh CLI 官方 OAuth App 的授权页，点 Authorize 即可，不会暴露令牌值；
  4. 授权完成后再继续提交。目标仓库是**用户自己拥有**时，fine-grained PAT 即可，无需 OAuth。
- **若用户不希望提供 OAuth 令牌（拒绝授权 / 不想动凭据）→ 回退到 computer use 浏览器自动化**（利用浏览器已有登录态，网页会话天然有提 issue 能力）：
  1. computer-use 打开 `https://github.com/<owner>/<repo>/issues/new/choose`（先确认浏览器已登录目标账号）；
  2. 选对应模板（如 `feature_request.yml`），填标题与正文后提交；
  3. 长正文先写工作区临时文件，经剪贴板（`Get-Content -Raw -Encoding UTF8 <file> | Set-Clipboard`）后 `Ctrl+V` 粘贴，避免长文本逐字输入不稳；
  4. 提交后从页面 URL 提取 issue 编号，`gh issue view <编号>`（或网页）验证状态；
  5. 注意：键盘注入被拒时先点击窗口激活（窗口焦点问题），UIA 捕获不到表单控件时用坐标点击。

**GITHUB_TOKEN / GH_TOKEN 环境变量会覆盖 gh 的所有账号管理！**

```bash
gh auth status
```
- 若 active 账号的 token 是 `github_pat_...`（fine-grained PAT），**通常没有 `issues: write` 权限**，提交会报 `GraphQL: Resource not accessible by personal access token (createIssue)`。
- 查看所有账号及 scope：`gh auth status` 会列出 keyring 账号。有 `repo` scope 的 OAuth token（`gho_...`）可以写 issues。
- 切换账号前必须先清掉环境变量（否则切不动）：
  ```bash
  unset GITHUB_TOKEN GH_TOKEN
  gh auth switch --user <用户名>
  ```
- 注意：环境变量名有 `GITHUB_TOKEN` 和 `GH_TOKEN` 两个，都要清。`unset` 只在当前 shell 命令内生效，每条命令都要带上（如 `unset GITHUB_TOKEN GH_TOKEN; gh issue create ...`），或者用 `env -u GITHUB_TOKEN -u GH_TOKEN gh ...`。

### 5. 提交

```bash
unset GITHUB_TOKEN GH_TOKEN
gh issue create --repo <owner>/<repo> \
  --title "[Feature]: <一句话标题>" \
  --body-file <正文文件路径>
```
- `--body-file` 优于 `--body`（长正文免转义）。
- 返回的 URL 即 issue 地址。

### 6. 验证

```bash
unset GITHUB_TOKEN GH_TOKEN
gh issue view <编号> --repo <owner>/<repo> --json number,title,state,url --jq '{number,title,state,url}'
```
- 确认 state=OPEN、作者、标题正确。把 URL 汇报给用户。

## 注意事项

- **version line 类下拉字段**：模板若有版本选择（如 "v2 — Go rewrite" / "v1 — Legacy"），优先选活跃开发线；用户说"提交到 v2"时选 main-v2 对应项。
- **标签**：默认模板自带 `enhancement` 等 label，无需手动加；除非用户要求。
- **不要替换用户的账号凭据**：只用 `gh auth switch` 切换已登录账号，不要读写 token 明文。
- 正文文件属于临时产物，提交成功后保留在 `global-workspace` 即可（用户可能想复用）。
