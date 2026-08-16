---
name: reasonix-sync-review
title: Reasonix 技能/记忆同步审查
description: 审查 reasonix-sync 待审清单（review.md），净化机器特定内容、提炼经验教训、去重，输出整理稿 draft 供 sync-publish 发布。每周主力机同步流程使用。
---

# reasonix-sync-review

## 何时使用

主力机每周同步流程的任务 B-2：`sync-organize.py` 已生成待审清单
`<OneDrive>\ReasonixSync\work\review\<周>\review.md`，需要逐条审查整理。

## 输入

- 待审清单：`<OneDrive>\ReasonixSync\work\review\<周>\review.md`

## 输出（写入 review 同目录的 `draft\` 子目录）

1. `draft\<name>.md` —— 每条确认保留的全局记忆 fact 的整理稿，**每个文件一条**
2. `draft\deleted.txt` —— 应删除的 dist fact 文件名（每行一个，可用 `#` 注释）
3. `draft\skills\` —— 需要更新进 dist 的技能目录（有更新/冲突裁决时）

完成后执行：`python sync-publish.py --week <周>`（会打印清单并交互确认）。

## 整理规则（铁律）

0. **技能脱敏原则（2026-08-16 定）**：dist 中的技能 = **脱敏版，与 GitHub `reasonix_skill_repo` 对应技能保持一致**（GitHub 是权威脱敏源）。技能里出现机器特定内容（本机路径/IP/凭据/端口/工作区名）→ **迁移到本机记忆**（如 `local-env-notes`）或删除，技能本身保持脱敏；引用本机信息用占位符（`<local-home>`/`<本地代理端口>`）。
0b. **凭据收口（2026-08-16 定）**：**明文凭据（密码/令牌/密钥）只允许存在于 `global-workspace\credential\` 目录**；记忆与技能中出现明文凭据 → 迁移到 credential 目录（记忆改为引用路径）；审查 dist 记忆/技能时如发现明文凭据，一律退回或净化。
1. **净化机器特定内容**：盘符路径、IP 地址、计算机名、端口号、密码/令牌/凭据（含密文）→
   改写为通用表述（如 `D:\data\` → `<项目数据目录>`）或整句删除。这类内容绝不允许进全局记忆。
2. **经验提炼**：清单"三、项目记忆提炼候选"里的内容只有**可迁移的教训/方法/偏好**才能升为全局记忆；
   项目独有事实（进度、数据规模、机器专属配置）不收录。
3. **去重合并**：与 dist 已有记忆重复或近义 → 并入已有条目（draft 里覆盖同名文件）或写入 deleted.txt。
4. **体例**：沿用全局记忆格式 —— `**Why:**`（背景/教训由来）+ `**How to apply:**`（可执行步骤）；
   简体中文；正文控制在 10~30 行；超长拆分多条。
5. **frontmatter 必须完整**：
   - `id`：清单里已标原 id 的沿用；新条目生成 `mem-` + 32 位 hex
   - `name`：短横线小写 slug，与文件名一致（如 `destructive-command-safety`）
   - `title` / `description`（一句话索引，含关键词）
   - `metadata.type`：feedback | user | project | reference
   - `metadata.scope`：global
   - `created_at` / `updated_at`：ISO 8601 带时区
6. 技能裁决：同名冲突时以**功能完整 + 通用化**的版本为准；机器特定路径写进技能脚本的，改为环境变量/探测。

## 输出模板

```markdown
---
id: mem-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
revision: 1
created_at: "2026-08-14T00:00:00+08:00"
updated_at: "2026-08-14T00:00:00+08:00"
name: my-lesson
title: 我的教训标题
description: 一句话索引（含关键词）
metadata:
  type: feedback
  scope: global
---

## 我的教训标题（YYYY-MM-DD 经验来源）

**Why:** ...

**How to apply:**
1. ...
```

## 关联

- 同步体系：`<OneDrive>\ReasonixSync\README.md`（架构、定时任务、首次部署）
- 脚本：`sync-push.py`（各机推送）、`sync-organize.py`（生成清单）、`sync-publish.py`（发布）、`sync-pull.py`（各机拉取）
