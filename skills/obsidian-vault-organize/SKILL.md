---
name: obsidian-vault-organize
description: 整理 Obsidian 仓库时保证双向引用不断裂。移动/重命名/归档文件或文件夹后，全 vault 重写 wikilink、markdown 链接、嵌入与 canvas 引用，并用断链校验归零验证。适合批量重组目录、归档旧笔记、统一命名、修复断链、清理孤儿文件。当用户要求"整理 vault"、"移动笔记"、"重命名笔记"、"修复断链"、"归档"时使用。
---

# Obsidian Vault 整理与链接安全操作

在 Obsidian 仓库（vault）里移动、重命名、归档、清理文件时，保证所有链接（双向引用）不失效。本技能提供**确定性流程**：盘点 → 规划 → 执行移动 → 重写引用 → 断链校验归零 → 清理。

## 核心事实（决定一切操作方式）

1. **Obsidian 只在应用内操作（`fileManager.renameFile`，即界面里拖动/重命名）时才会自动重写全库链接**。
2. **外部移动（shell `mv`、脚本、agent 的文件工具、同步软件）不会被自动维护**：Obsidian 的 watcher 能检测到变化（文件树刷新、`vault.on('rename')` 事件），但只是"感知"，不会重写任何链接——该断的链照样断。
3. 因此：**任何经 agent/脚本执行的移动，都必须显式重写引用并校验**，不得依赖 Obsidian 的 watcher。
4. 删除没有自动修复：删除前必须查反向引用（谁链接了它），删除后同步清理引用或改为归档。
5. 破坏性操作遵守安全规范：删除前先 `ls`/`find` 确认清单，批量删除走回收（trash）语义，禁止多目标 `rm -rf` 混用。

## 链接类型清单（扫描与重写必须全覆盖）

| 类型 | 语法示例 | 说明 |
|---|---|---|
| wikilink | `[[Note]]` | 目标不带扩展名 |
| wikilink 别名 | `[[Note\|显示名]]` | 只改目标部分，保留 `\|别名` |
| wikilink 锚点 | `[[Note#标题]]`、`[[Note#^blockid]]` | 只改 `#` 前的路径部分 |
| 嵌入 | `![[Note]]`、`![[img.png]]`、`![[pdf.pdf]]` | 带扩展名的附件按原样匹配路径 |
| markdown 链接 | `[文本](path.md)`、`[文本](../sub/c.md)` | 可能是 vault 绝对（`/` 开头）或相对当前文件的路径；可能有 `%20` 编码 |
| canvas 引用 | `"file": "old.md"`、`"link": "[[old]]"` | `.canvas` 是 JSON |
| properties/frontmatter | `link: "[[old]]"` 或 `link: old.md` | 普通文本扫描即覆盖 |

## 工作流

### Step 1 盘点
- 定位 vault 根：包含 `.obsidian/` 的目录。只操作 vault 内的文件。
- 读 `.obsidian/app.json` 了解链接设置：`newLinkFormat`（`shortest`/`absolute`/`relative`）与 `useMarkdownLinks`——决定新链接的写法风格，尽量沿用原风格。
- 收集全 vault 文件清单（跳过 `.obsidian/`、`.git/`、`.trash/`）。

### Step 2 规划
- 列出移动/重命名清单（旧路径 → 新路径），一次只执行一个明确目标。
- 对每个目标先查反链：grep `[[旧名]]`、旧路径、旧路径的 basename（Obsidian 按文件名解析时，改文件名会打中所有 vault 内引用）。
- 文件夹移动时，所有子路径的链接都受影响（前缀替换）。

### Step 3 执行移动
- 用 `move_file`（单文件）或脚本移动；**不要**用 `mv` 混入多条命令。
- 移动前如果 Obsidian 正打开着相关笔记，提示用户：外部改动会造成缓存/磁盘冲突，建议先关闭或接受 Obsidian 的重新加载提示。

### Step 4 重写引用（核心）
```bash
# 先预览（不落盘）
python "<技能目录>/scripts/relink.py" <vault> <old> <new> --dry-run
# 确认预览无误后执行
python "<技能目录>/scripts/relink.py" <vault> <old> <new>
```
- `old`/`new` 为 vault 相对路径，带不带 `.md` 均可。
- `new` 语义：默认是完整目标路径（如 `notes/b`）；**目标目录意图用尾斜杠表达**（如 `notes/` → 拼成 `notes/b`）；若 `new` 是已存在目录且 `old` 带扩展名（明显是文件，如 `img.png`）也会自动拼接。
- `old` 为文件夹时自动按前缀匹配整棵子树；**子树内文件的相对 markdown 链接会自动重算**（按旧位置解析、按新位置重新渲染），无需手工处理。
- 预览必须人工核对：每个受影响文件、改动行数符合预期才执行。
- relink 只重写**指向移动目标**的引用，不碰其他内容；重复执行是幂等的（无匹配即退出 2）。

### Step 5 断链校验（必须归零）
```bash
python "<技能目录>/scripts/check_links.py" <vault路径> --exclude .claudian --json > out.json
```
- `--json` 输出 `issues[]`（kind: `markdown`/`wikilink`；markdown 且 target 含 `Exported` 系列时是 importer 漏导/源损坏的图片断链）
- 修复图片断链的完整方法论见 [[onenote-import-pipeline]]（pageInfo=1 提取 base64、配对规则、在线分区下载）

### Step 6 清理
- 删除残留空目录、临时文件；提交 git 时用显式路径（禁 `git add -A`，见全局教训）。

## 常见故障：Remotely Save 同步报错（ERR_INCOMPLETE_CHUNKED_ENCODING）

**现象**：Obsidian 的 Remotely Save 插件同步报 `net::ERR_INCOMPLETE_CHUNKED_ENCODING`（响应流被中途截断），或 onedrive.live.com 请求超时。2026-08-12 实测。

**根因**：**本机代理软件（v2rayN/sing-box/Clash 等）与 OneDrive 的链路问题**——Obsidian（Electron）走系统代理（常见 `127.0.0.1:10808`），小请求能通，但 vault 首次全量同步（GB 级大流量）经代理节点时 chunked 响应被截断。国内网络下 onedrive.live.com 直连被墙、graph.microsoft.com 可直连。

**排查步骤**：
```bash
tasklist | grep -iE "v2ray|clash|sing-box|xray"        # 1. 代理进程是否运行
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" | grep -iE "ProxyEnable|ProxyServer"  # 2. 系统代理
curl -s -o /dev/null -w "%{http_code} (%{time_total}s)\n" --max-time 20 https://graph.microsoft.com/v1.0/   # 3. 直连 Graph API（应 200）
curl -s -o /dev/null -w "%{http_code}\n" --proxy http://127.0.0.1:10808 --max-time 20 https://onedrive.live.com/  # 4. 经代理（403 = 通）
```

**解决（按优先级）**：
1. **关闭代理**（实测立竿见影，同步恢复正常）
2. 或 v2rayN 分流规则把微软域名加 DIRECT 直连：`graph.microsoft.com`、`*.sharepoint.com`、`*.1drv.ms`、`onedrive.live.com`、`login.microsoftonline.com`
3. 换稳定代理节点
4. 仍断则降并发（Remotely Save 设置）或临时排除大目录（如 `0-attachments/`）先同步核心笔记

**其他判断**：
- 配置/授权问题 vs 网络问题的分水岭：**插件能发出请求（有响应、哪怕是 403）说明凭据正常**；密钥丢失的特征是启动即报解密错误
- Remotely Save 的 `data.json` 是加密配置（localStorage 按 vault 分区存密钥）；vault 迁移（换路径/换 vault id）后 localStorage 分区清空会导致解密失败——**vault 迁移后需重新配置/授权**

## 脚本位置

本技能自带三个脚本（Python 3，标准库）：
- `scripts/check_links.py` — 断链校验（也用于任何时刻的健康检查，不限于移动后）
- `scripts/relink.py` — 移动/重命名后重写引用（old→new 路径映射）
- `scripts/fix_broken_links.py` — 按文件名修复"文件被移走后断掉的附件引用"（图片/PDF 等；断链引用在全库找同名文件 → 改写为 `![[路径]]` 嵌入；找不到的记入缺失清单不动；笔记引用（.md/无扩展名）不处理）

技能目录查找：`glob("**/obsidian-vault-organize/scripts/*.py")`；典型安装位置 `%APPDATA%\reasonix\skills\obsidian-vault-organize\scripts\`（Windows）或 `~/.reasonix/skills/obsidian-vault-organize/scripts/`（Linux/macOS）。

## 相关技能

- [[obsidian-markdown]] — wikilink/嵌入/callouts/properties 语法规范（写新链接时参考）
- [[obsidian-cli]] — vault 的 CLI 操作
- [[book-to-skill]] — 文档→技能流水线（其断链校验思路与本技能一致）
- [[onenote-import-pipeline]] — OneNote 断链图片修复方法论（Exported 系列断链）
