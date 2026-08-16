---
name: reasonix-sync-deploy
title: Reasonix 同步体系部署（新机器接入）
description: 在新电脑上完成 reasonix-sync 部署：探测环境、提示设置 OneDrive 始终保留、创建定时任务、首次推送并验证。用于把新机器接入 OneDrive 多机同步体系。
---

# reasonix-sync-deploy

## 目标

把当前机器接入 `OneDrive\ReasonixSync` 多机同步体系（用户级技能 + 全局记忆每周同步）。
全程**无需管理员权限**；所有命令以当前用户执行。

## 前置检查

1. 定位脚本目录 `<SCRIPTS>`（按优先级取第一个存在的）：
   - 本技能目录同级 `scripts\`（技能自带脚本，分享包/独立场景）
   - `%USERPROFILE%\OneDrive\ReasonixSync\scripts\`（已接入同步体系的机器）
   - 都不存在 → 告诉用户"脚本未就位：分享包解压不完整，或 OneDrive 还在同步，等 1~2 分钟再让我重试"。
2. 探测 OneDrive 根目录（仅当走 `OneDrive\ReasonixSync` 路径时需要，依次尝试）：
   - `%USERPROFILE%\OneDrive`
   - `%USERPROFILE%\OneDrive - <名称>`（企业/多账号重命名）
   - 用 `dir %USERPROFILE%\OneDrive*` 列出候选
3. 探测 Python：`where pythonw`（找不到则告知用户安装 Python，或让其编辑 `install-tasks.ps1` 顶部的候选路径列表）。
4. 机器名不需要配置：脚本自动取 `COMPUTERNAME`，首次推送时自动创建 `inbox\<计算机名>\` 子目录。

## 部署步骤（按顺序执行）

### 第 1 步：提示用户设置 OneDrive"始终保留在此设备"

OneDrive 客户端设置 AI 无法代劳，**明确请用户操作**（仅同步体系场景需要）：
> 请右键 `OneDrive\ReasonixSync` 文件夹 → 选择"始终保留在此设备上"。

等用户确认完成再继续。

### 第 2 步：创建定时任务

用 PowerShell 执行（脚本含 `StartWhenAvailable` 错过补跑）：

```
powershell -NoProfile -ExecutionPolicy Bypass -File "<SCRIPTS>\install-tasks.ps1"
```

**先询问用户"这台机器是主力机吗？"**：
- 是 → 加 `-Organizer` 参数（额外创建每周五的 Organize 任务）
- 否 → 不加（只有 Push 每天 10:00 + Pull 周一 10:30）

创建后验证（任务应全部 `Ready`，且 `StartWhenAvailable=True`）：

```
powershell -NoProfile -Command "Get-ScheduledTask -TaskPath '\ReasonixSync\' | Select-Object TaskName, State"
```

### 第 3 步：首次推送

```
python "<SCRIPTS>\sync-push.py"
```

预期输出：`== push: <本机计算机名> -> ...\inbox\<本机计算机名>\`，随后列出技能/事实数量。

### 第 4 步：验证

1. `dir <SCRIPTS>\..\inbox\<本机计算机名>` 下应出现 `memory\global\` 且非空。
   `skills\` **只有本机装有用户级技能（`%APPDATA%\reasonix\skills\`）时才会出现**，新机器/未装过技能时没有是正常现象。
2. 告知用户当前状态：
   - 同步体系场景：快照已进入中央 inbox；主力机周五组织时会把本机纳入审查；本机周一 10:30 Pull 后自动获得 dist 的全部技能与全局记忆（含 `reasonix-sync-review` 审查技能），此后 Push 也会带上本机技能。
   - 独立/分享场景：本机定时任务已建立，技能+记忆快照会持续写入本地 `inbox\` 镜像（无主力机时仅保留本机快照，仍可用于后续接入体系）。

## 排障

| 现象 | 处理 |
|---|---|
| `<SCRIPTS>` 定位失败 | 分享包解压不完整（缺 `scripts\`）或 OneDrive 未同步完；检查后重试 |
| 任务创建后复核发现缺失（OneDrive 同步竞态） | OneDrive 尚未同步完时运行安装脚本，可能漏建个别任务（实战踩坑）。**复核命令**：`powershell -NoProfile -Command "Get-ScheduledTask -TaskPath '\ReasonixSync\' | Select-Object TaskName, State"`，缺哪个就重跑一次安装脚本 |
| `pythonw` 找不到 | 安装 Python，或编辑 `install-tasks.ps1` 的候选路径列表 |
| 任务创建失败 | 确认不是管理员窗口；`schtasks /Query /TN "ReasonixSync\Push"` 查状态 |
| push 报错 | 查看日志 `%LOCALAPPDATA%\reasonix-sync\logs\push.log`（UTF-8） |
| push 提示"未发现本机用户级技能" | 正常：本机未装过技能时 skills 目录不会出现；Pull 一次后（dist 技能会装到本机）再 Push 就有技能了 |

## 注意事项

- 不修改 `<SCRIPTS>` 下的任何文件（同步体系场景：改一个全体系生效，需谨慎，只由主力机维护者改）。
- 不触碰 `.env` / `credentials` / `config.toml` / `heartbeat-tasks.json` / `desktop-*.json` 等（脚本已硬编码排除，无需人工干预）。
- 部署是幂等的：重复执行不会产生问题（任务 `-Force` 覆盖、快照内容相同跳过）。
- 完成部署后无需其他机器配合；本机经验在下次 Push 时自动进入体系。
