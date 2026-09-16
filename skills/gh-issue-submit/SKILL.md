---
name: gh-issue-submit
description: 用 gh CLI 提交高质量 GitHub issue 与 Discussion：模板发现、查重（含已关闭 issue 阅读）、源码调研根因、权限切换陷阱、computer use 回退、提交与验证、正文插图、社区投票（Discussions Poll 能力边界与选型）
---

# GitHub Issue 提交技能（gh-issue-submit）

用 `gh` CLI 把功能请求 / bug 报告 / 改进建议提交到任意 GitHub 仓库 issue 的完整流程。包含模板发现、查重、权限陷阱处理和提交验证。

## 适用场景

- 用户要求"给某仓库提个 issue / feature request / bug report"
- 用户给了 issues/new 链接（含 `?template=...` 参数）或直接点名仓库
- 用户要求"帮我写并提交 issue"
- 用户想在社区**征集意见 / 做功能优先级投票** → 见 **5.5**（先看它列的三个边界：≤8 选项、只能单选、**不能用 API 创建**）

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

- 公开仓库可直接 `git clone --depth 1`（需代理时走本机代理）；本地已有源码优先复用（如本机 `%TEMP%
xsrc` 有 DeepSeek-Reasonix 源码），避免重复 clone。
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

### 3.5 正文插图：专用分支 + raw URL（2026-09-16 实战验证）

issue / discussion 正文要配图时，**不要试图走 GitHub 的网页上传接口** —— 那条路（`github.com/upload/policies/assets`）依赖浏览器 session cookie，`gh` 的 token 拿不到，无法脚本化。

**可行且可脚本化的做法：把图 commit 到仓库的一个独立分支，用 raw URL 外链。**

```bash
# 0) 前置检查：仓库必须 PUBLIC —— private 仓库的 raw URL 会 404
gh repo view <owner>/<repo> --json visibility

# 1) 基于远端建独立分支（不污染默认分支）
cd <repo>
git checkout -b <assets-branch> origin/<default-branch>
mkdir -p <dir>                      # 如 discussion-assets/ 或 docs/images/
cp <本地图片> <dir>/01-xxx.png       # 给图起可读的名字，便于正文引用

# 2) 显式路径提交（禁 git add -A / .）
git add <dir>/01-xxx.png <dir>/02-xxx.png
git status --short                  # 核对暂存区只含这些图
git commit -m "docs(assets): screenshots for <用途>"
git push origin <assets-branch>
git checkout <default-branch>       # 切回，别把默认分支留在 assets 分支上
```

正文里这样引用：

```markdown
![说明文字](https://raw.githubusercontent.com/<owner>/<repo>/<assets-branch>/<dir>/01-xxx.png)
```

**提交前必须验证 URL 可访问**（否则帖子里是破图）：

```bash
A="https://raw.githubusercontent.com/<owner>/<repo>/<assets-branch>/<dir>"
for f in 01-xxx.png 02-xxx.png; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$A/$f")
  echo "$code  $f"          # 期望都是 200
done
```

**要点与陷阱**：

- **图片分支不要删** —— 帖子的图直接指向它，**删分支 = 图全部 404**；要清理先迁图并更新帖子链接。
- **给图起语义化文件名**（`01-recovery-copies.png`），比 `clipboard-20260916-134424.566995-000003.png` 便于后续维护。
- **正文与图片分两步走更稳**：先把正文写成独立文件（`--body-file` / `-F body=@file`），再单独处理图片，避免长正文 + 图片混在一条命令里出转义问题。
- **不愿建分支时的替代方案**：在 issue/discussion 编辑器里**手动粘贴/拖入**图片 —— GitHub 会转成 `https://github.com/user-attachments/assets/<uuid>` 托管，代价是**必须人工操作，无法脚本化**。
- **隐私自检**：截图常带真实路径、会话名、项目名 —— 发帖前逐张过一遍，必要时打码或换图。

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
- **无 gh CLI / 无 keyring OAuth 凭据时的直接获取（GitHub OAuth device flow，2026-08-12 实测）**：不依赖 gh 安装，直接用设备授权码流程拿 `gho_` token（client_id 用 VSCode 的公开 OAuth App id `01ab8ac9400c4e429b23`）：
  1. 请求设备码（本机有代理就带 `-x http://127.0.0.1:10808`）：
     ```bash
     curl -s -H "Accept: application/json"        -d "client_id=01ab8ac9400c4e429b23&scope=repo read:user user:email"        https://github.com/login/device/code
     ```
     返回 `user_code`（形如 `0FBF-BCC0`）、`device_code`、`verification_uri`、`interval`；
  2. 让用户浏览器打开 `https://github.com/login/device` 输入 `user_code` 并点 Authorize（设备码约 15 分钟有效）；
  3. 轮询换 token（error=authorization_pending 时按 interval 继续等，约 5s；slow_down 时加倍）：
     ```bash
     curl -s -H "Accept: application/json"        -d "client_id=01ab8ac9400c4e429b23&device_code=<device_code>&grant_type=urn:ietf:params:oauth:grant-type:device_code"        https://github.com/login/oauth/access_token
     ```
  4. 拿到 `access_token`（`gho_` 前缀，scope 含 `repo`）后持久化到 User 级环境变量（PowerShell：`[Environment]::SetEnvironmentVariable('GITHUB_TOKEN', $tok, 'User')`），或用临时文件→`export`，**用完删除含明文的临时文件**；
  5. 验证：`curl -s -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/user` 返回 login 即成功；token 明文只在授权那一刻返回一次。
  6. 管理入口：OAuth 授权**不会**出现在 `github.com/settings/tokens`（那是 PAT 页面），记录在 `github.com/settings/applications`（显示为 "Visual Studio Code"），撤销在那里 Revoke access，撤销后环境变量里的 token 立即失效。
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

除 issue 外，**Discussion 也能用 `gh` 提交**（GraphQL mutation，2026-09-16 实测；`gh issue create` 不支持 discussion）：

```bash
# 先取 repo id 与目标分类 id（分类名如 "Show and tell" / "General"）
env -u GITHUB_TOKEN gh api graphql -f query='
{ repository(owner:"<owner>", name:"<repo>") {
    id
    discussionCategories(first:12) { nodes { id name } } } }'

# 长正文写成独立文件，用 -F body=@file 传入（避开 shell 转义）
env -u GITHUB_TOKEN gh api graphql   -f query='mutation($repo:ID!,$cat:ID!,$title:String!,$body:String!){
    createDiscussion(input:{repositoryId:$repo,categoryId:$cat,title:$title,body:$body}){
      discussion{ url number } } }'   -f repo='<R_...>' -f cat='<DIC_...>'   -f title='<标题>' -F body=@<正文文件路径>
```

- **分类选择**：`Q&A` 提问 / `Ideas` 功能建议 / **`Show and tell` 展示自己的作品（分享 fork、工具、脚本等用这个）** / `Polls` 投票（⚠️ **不能用 API 创建，只能网页建**，见 **5.5**） / `General` 其它。
- 正文里的图片同样走 **3.5 的专用分支 + raw URL** 方案。
- 同样适用「**6.5 提交后更正：直接改正文**」—— `updateDiscussion` mutation 改正文，不要追加更正评论。

### 5.5 社区投票：Discussions Poll 的能力边界（2026-09-17 调研）

想"从 N 个候选里选出用户最需要的 M 个"时，**先看这张边界表** —— 它直接决定方案怎么选：

| 项 | 事实 | 依据 |
|---|---|---|
| **选项上限** | **最多 8 个** | GitHub Blog 2022-04-12 原文 *"You can add up to eight polling options"*；2026-08 社区仍在抱怨未放开 |
| **选择方式** | **只能单选，不支持多选** | 官方文档的 poll 创建步骤里**没有**多选勾选项；社区 feature request *"Polls: support multiple choices"* #52039 至今未实现 |
| **谁能投** | **仅登录用户** | 官方 blog |
| **分类要求** | 必须发在 **format=Poll** 的 category（默认名 `Polls`） | 官方文档「In the list of categories, click **Polls**」 |
| **截止时间** | **未验证** —— 不要向用户断言可设截止 | 官方文档未载，未实测 |

**⚠️ API 覆盖度（GraphQL introspection 实测，2026-09-17）—— 只有「查」和「投」，没有「建」：**

| 操作 | 能否 API 化 | 证据 |
|---|---|---|
| **创建 Poll** | ❌ **不能，只能网页手工建** | `CreateDiscussionInput` 只有 5 个字段：`clientMutationId / repositoryId / title / body / categoryId`，**无任何 poll 字段** |
| **查询票数** | ✅ 能 | `Discussion.poll : DiscussionPoll` 存在 |
| **投票** | ✅ 能（`addDiscussionPollVote`） | 全部 259 个 mutation 中唯一含 poll 者 |

**前置：仓库必须先启用 Discussions** —— 未启用时 `discussionCategories` 返回**空数组**（不报错，容易误判成"没有分类"）：

```bash
env -u GITHUB_TOKEN gh api -X PATCH repos/<owner>/<repo> -f has_discussions=true
# 验证（返回 false ⇒ 立刻能看出没开）
env -u GITHUB_TOKEN gh api repos/<owner>/<repo> --jq '.has_discussions'
```

**读票数（脚本统计用；字段名已实测）：**

```bash
env -u GITHUB_TOKEN gh api graphql -f query='
{ repository(owner:"<owner>", name:"<repo>") {
    discussion(number:<编号>) {
      title
      poll {
        question
        totalVoteCount
        viewerHasVoted
        options(first:10) { totalCount nodes { option totalVoteCount } }
      } } } }'
```

- `DiscussionPoll` 字段：`discussion / id / options / question / totalVoteCount / viewerCanVote / viewerHasVoted`
- `DiscussionPollOption` 字段：`id / option（选项文本）/ poll / totalVoteCount / viewerHasVoted`
- `options` 是标准 connection（`edges / nodes / pageInfo / totalCount`）。
- **没有 poll 时 `poll` 返回 `null`**，不报错。

**方案选型：N 个候选怎么投**

| 候选数 | 要不要「每人限票」 | 方案 |
|---|---|---|
| **≤8** | 不限（看热度排序取 top M） | **1 个 Poll**，单选即得票排序 —— **最省事** |
| **≤8** | 要「每人 M 票」 | **M 轮加权 Poll**：*第 1 优先 / 第 2 优先 / …* 各发一个，**每个都单选** ⇒ 每人天然只投 M 次；计分按 **M : M-1 : … : 1** 加权 |
| **>8** | — | **Poll 装不下** ⇒ 改用 **👍 reaction 计数**：一条 discussion（或 issue）正文列出候选，**每个候选一条 comment**，各自计 👍。**⚠️ 不能写成「一个候选一种 emoji」** —— GitHub 只有 8 种 reaction，同样撞 8 的墙 |

**受众策略（容易忽略）**：投票只有发在**自己拥有/维护的仓库**才合适；发到第三方仓库属于越界。若想让上游用户参与，正确做法是**在自己仓库开投票 + 在上游发 announcement 引流**，而不是把投票发到上游。

### ⚠️ 已知限制：创建 Poll 必须由用户手工完成，不要尝试自动化

**2026-09-17 实测：四条自动化路线全部受阻 —— 不要再走一遍，直接走下面的「正确做法」。**

| 尝试 | 结果 |
|---|---|
| GraphQL API 创建 Poll | ❌ `CreateDiscussionInput` 无 poll 字段 |
| Chrome 直接开调试端口（默认 profile） | ❌ Chrome 136+ 报 `DevTools remote debugging requires a non-default data directory` |
| 复制最小 profile（`Local State` + `Network/Cookies`）给 playwright 用 | ❌ 登录态丢失、页面跳 `/login` —— Chrome 127+ 的 **App-Bound 加密**使 cookie 无法跨 profile 解密 |
| robocopy 完整复制 profile 到非默认目录 | ❌ 体量过大，2 分钟超时 |
| `computer-use` MCP 走浏览器自动化 | ❌ 本机启动失败（`tools/list: invalid request`） |

**⇒ 正确做法（唯一可行）：给用户可直接粘贴的文案，请用户自己登录并提交。**

1. **准备三段内容**：标题、正文、选项文案（每个 ≤8 个）—— 逐条给纯文本，方便逐项复制；
2. **给出直达链接**：`https://github.com/<owner>/<repo>/discussions/new?category=polls`；
3. **写清操作步骤**：选 `Polls` 分类 → 填 Poll question → 逐条填选项（点 **Add an option** 增加）→ **Start poll**；
4. **用户提交后，自己用上面那段 GraphQL 读回结果作验证**（**读这一步能自动化，务必做**）。

**⚠️ 不要承诺「我帮你建成」「我自动发」** —— 在当前 Chrome / GitHub 的安全策略下做不到，说了就是给用户一个必然失败的预期。

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
### 6.5 提交后更正：直接改正文，勿追加「更正评论」（2026-08-21 实测）

issue **正文可编辑**——任何内容更正都应**直接改正文**，而不是在评论区追加一句"更正：上文第 X 节写错了…"。

- **改正文**：
  ```bash
  gh issue edit <编号> --repo <owner>/<repo> --title "<新标题>" --body-file <正文文件>
  ```
  `--title` 与 `--body-file` 可单用或并用；若只需改某一段，取当前 body（`gh issue view <编号> --json body --jq '.body'`）改后写回。
- **为什么不要追加"更正评论"**：正文一旦被编辑掉，那条更正评论就成了**指向已不存在旧文的过时评论**，反而制造"正文 vs 评论区对不上号"的混淆。
- **清除已过时的更正评论**（GitHub 无 gh 子命令，用 REST DELETE）：
  ```bash
  gh api -X DELETE repos/<owner>/<repo>/issues/comments/<comment_id>
  ```
  评论 ID 见 `gh issue view <编号> --json comments --jq '.comments[]|{id,createdAt}'`。
- 判断是否动手：**以正文为唯一权威**；除非是「保留讨论痕迹/回应某人」这类社交意图，更正一律走正文编辑。

### 7. PR 冲突处置：先查 supersede，再 rebase（2026-08-16 教训）

PR 显示 `dirty`/`CONFLICTING` 时，**第一步永远是检查是否已被开发者自己合入/整合**——上游维护者常做"整合 PR"（把多个 open PR 的功能合并进自己的分支），此时相关 PR 应**关闭**而非 rebase，否则白干一场。

**检查三步（按顺序）：**
1. `git fetch upstream main-v2 && git log --oneline -20 upstream/main-v2`——看最近合入的提交标题是否覆盖我们的功能
2. `env -u GITHUB_TOKEN -u GH_TOKEN gh api "repos/<owner>/<repo>/pulls?state=closed&per_page=30"` 或 GitHub 搜索 `repo:<owner>/<repo> is:pr is:merged "Fixes #<我们的issue>"` / `"Refs #<N>"`——找"Fixes/Refs 我们的 issue 编号"的已合并 PR
3. 确认后读该 PR body 的 Source/Integration 表——看是否带我们的 Co-authored-by trailer（GitHub 会记录贡献）

**若被 supersede：**
- 发关闭评论（说明去向：被 #N 整合、功能已进上游、带 Co-authored-by）→ `gh api --method PATCH pulls/<n> -f state=closed`
- 同时确认对应 issue：被 Fixes 自动关闭则验证 state=completed；未自动关闭则评论+关闭（state_reason=completed）
- 不必纠结"白做"——维护者整合时会保留贡献署名

**确认未被合入，才 rebase：**
```bash
git fetch upstream main-v2   # 注意：origin=fork 的 main-v2 不会同步上游！必须 fetch upstream
git rebase upstream/main-v2
# 解决冲突后：go build/test 或 tsc + 相关单测 → git push --force（确认远程无第三方提交后）
```
- rebase 冲突中若上游已重构我们依赖的 API（删字段/改格式），做**最小适配**（只保留我们功能的核心），必要时同步改测试
- 多个 PR 全 dirty 时按依赖顺序处理（叠加分支先底层后上层）


## 注意事项

- **version line 类下拉字段**：模板若有版本选择（如 "v2 — Go rewrite" / "v1 — Legacy"），优先选活跃开发线；用户说"提交到 v2"时选 main-v2 对应项。
- **标签**：默认模板自带 `enhancement` 等 label，无需手动加；除非用户要求。
- **不要替换用户的账号凭据**：只用 `gh auth switch` 切换已登录账号，不要读写 token 明文。
- 正文文件属于临时产物，提交成功后保留在 `global-workspace` 即可（用户可能想复用）。
