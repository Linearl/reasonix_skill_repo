---
name: migrate-reasonix-project
description: 迁移 Reasonix（及 Claude Code）项目目录时保留对话历史的完整流程
---

---
name: "migrate-reasonix-project"
description: "迁移 Reasonix 项目目录时保留对话历史的完整流程（含 Claude Code 历史联动迁移）。当用户移动、重命名项目文件夹时使用此技能。"
---

# Reasonix 项目迁移技能

当用户需要移动、重命名项目目录时使用此技能。覆盖 Reasonix 与 Claude Code 两套对话历史的迁移。

## 核心知识

### Reasonix 对话历史存储位置

历史存储在 `%APPDATA%\reasonix\projects\<encoded-path>\sessions\`（Windows，如 `<local-home>\AppData\Roaming\reasonix\projects\`）。每个项目一个目录，`sessions/` 内含：

- `<session-id>.jsonl` — 会话记录（**历史内容，迁移时禁止改动**）
- `<session-id>.jsonl.meta` — 会话元数据 JSON（含 `workspace_root` 字段，**必须更新为新路径**）
- `<session-id>.events.jsonl` / `.event-index.json` / `.telemetry.json` / `.conflicts.jsonl` / `.recovery.json` / `.goal-state.json`
- `<session-id>.ckpt/` — 检查点目录（turn-*.json）
- `subagents/*.meta.json` — 子代理元数据（含 `workspaceRoot` 字段，**必须更新**）
- 隐藏文件：`.display.json`（消息哈希→文本映射）、`.display.json.lock`、`.topic-indexes-repaired-v2`、`.topics-migrated-v2` — 普通 `ls` 看不到，复制必须用 `robocopy /E` 或 `cp -r`（含隐藏文件）

### Reasonix 路径编码规则（与 Claude Code 不同！）

| 规则 | Reasonix | Claude Code |
|------|----------|-------------|
| 驱动器 `D:` | `d--`（大小写不敏感，历史目录 `D--`/`d--` 都有） | `D--` |
| 分隔符 `\` | `-` | `-` |
| 点 `.` | **保留** | 转 `-` |
| 下划线 `_` | **保留** | 转 `-` |
| 中文字符 | 保留原样 | 每个字转 `-` |

示例：`<work-dir>\video_compensation` → `d--1.workspace-video_compensation`；`D:\1.工作空间\03-方太快连` → `D--1.工作空间-03-方太快连`。

**不要猜测编码**：最可靠的方法是查现有 `projects/` 目录名，并读 `.jsonl.meta` 的 `workspace_root` 字段确认真实路径对应关系。

### Claude Code 对话历史存储位置（联动迁移）

`~/.claude/projects/<encoded-path>/`，编码规则：下划线转连字符（`video_compensation` → `video-compensation`）。内含 `<session-uuid>.jsonl`、`<session-uuid>/` 子代理目录、`memory/`。同一项目文件夹往往同时存在两套历史，需都迁移。

## 迁移步骤

### Step 1: 解除文件锁

- 关闭所有打开该项目文件的编辑器（Typora/VS Code 等）和浏览该目录的资源管理器窗口
- 若无法重命名（Permission denied），用 `Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match '<旧路径名>' }` 定位锁定进程
- 优先用 PowerShell `Move-Item`（Git Bash 的 `mv` 对 Windows 句柄处理更脆弱）

### Step 2: 移动项目文件夹

```powershell
Move-Item -LiteralPath '<work-dir>\video_compensation' -Destination '<work-dir>\video_comprehension'
```

### Step 3: 复制会话文件（先复制，验证后再删）

用 robocopy（注意 Git Bash 下需 `MSYS_NO_PATHCONV=1`，否则 `/E` 会被转成路径；或直接用 PowerShell）：

```bash
MSYS_NO_PATHCONV=1 robocopy "<local-home>\AppData\Roaming\reasonix\projects\<旧编码>" "<local-home>\AppData\Roaming\reasonix\projects\<新编码>" /E /COPY:DAT /R:2 /W:1 /NFL /NDL /NP
# Claude Code 同理：~/.claude/projects/<旧编码> → <新编码>
```

### Step 4: 更新结构元数据中的路径（仅 meta，不动会话内容）

用 Python 脚本精确替换（**注意 JSON 文件内是双反斜杠转义** `D:\\1.workspace\\video_compensation`）：

```python
# 目标：*.jsonl.meta 的 "workspace_root" 和 subagents/*.meta.json 的 "workspaceRoot"
old = r'D:\\1.workspace\\video_compensation'   # 注意双反斜杠
new = r'D:\\1.workspace\\video_comprehension'
```

禁止替换 `.jsonl` / `.events.jsonl` / `.ckpt/turn-*.json` 等会话内容中的路径——那是历史记录。

### Step 5: 验证

- 两侧文件数一致：`ls -a <新旧目录>/sessions/ | wc -l`（含隐藏文件）
- `grep -rl <旧路径> <新目录> | grep -E "\.meta|\.display"` 无输出
- Claude Code 侧：`diff <(cd src && find . | sort) <(cd dst && find . | sort)` + `cmp` 逐文件

### Step 6: 清理源目录

确认完整复制后，删除源目录（单目标、先 `ls` 核对）。删除 Claude 历史源目录与 Reasonix projects 源目录。

### Step 7: 更新桌面端项目列表（如有）

`%APPDATA%\reasonix\desktop-projects.json` 中 `projects[].root` 若指向旧路径需更新。**若 reasonix-desktop 正在运行，修改可能被其保存覆盖**——改后需重启桌面端验证。

### Step 8: 更新项目内引用

`grep -rn <旧名> <项目根> --include="*.md" --include="*.py" --include="*.sh" --include="*.yaml" --include="*.yml" --include="*.txt"`，把文档/脚本/配置里的旧目录名替换为新名（注释、绝对路径、目录树等）。`__pycache__/*.pyc` 是编译缓存，无需处理。

## 常见陷阱

1. **Reasonix 与 Claude Code 编码规则不同** — Reasonix 保留 `.`/`_`/中文，Claude Code 全转 `-`
2. **不要改会话内容** — 只更新 `.jsonl.meta` 的 `workspace_root` 和 subagents meta 的 `workspaceRoot`；JSON 内路径是双反斜杠转义
3. **隐藏文件** — `.display.json`、`.topics-migrated-v2` 等要用 robocopy /E 或 ls -a 检查
4. **先复制再删除** — 验证一致前绝不删源
5. **文件锁** — 编辑器/资源管理器/reasonix 桌面端打开项目会阻止重命名；Git Bash mv 失败时换 PowerShell Move-Item
6. **Git Bash 路径转换** — robocopy 参数前加 `MSYS_NO_PATHCONV=1`
7. **Reasonix 状态文件冲突** — 应用运行中外部修改可能生成 conflict 副本，看起来"没生效"；优先在应用空闲时操作
8. **Syncthing** — 项目内 `.stfolder-*`/`.stignore` 是同步标记，重命名同步文件夹后需同步更新 Syncthing 配置

## 实战参考

2026-08-07 成功迁移案例：`<work-dir>\video_compensation` → `video_comprehension`（Reasonix 27 个会话 + Claude Code 13 个会话，5 处 meta 更新，12 处项目内引用更新）。
