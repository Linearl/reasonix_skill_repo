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
python "<技能目录>/scripts/check_links.py" <vault>
```
- 输出所有断链（文件:行:链接 + 原因），退出码 1 表示有断链。
- 校验通过标准：**0 断链**。有残留就回到 Step 4/5 循环（漏掉的链接类型、路径风格差异、大小写问题）。
- 提示用户在 Obsidian 里看一眼图（graph view）确认。

### Step 6 清理（可选，谨慎）
- 孤儿文件 = 未被任何链接/嵌入引用、且不是 `.obsidian/` 配置的文件。
- 先 `check_links.py` 全绿，再列孤儿清单给人核对，**移到回收目录**而非直接删除（见安全规范），确认无误后再清空回收目录。

## 注意事项与坑

1. **wikilink 不带扩展名，markdown 链接可能带 `.md`**：匹配时两种形式都要覆盖；附件（图片/PDF）保持原扩展名。
2. **相对路径链接**：以所在文件目录为基准解析；重写时保持原风格（原来相对就生成新的相对路径，原来 `/` 绝对就生成新的绝对形式）。
3. **URL 编码**：markdown 链接里的空格可能写成 `%20`；重写时按原编码风格逐段 `quote`。
4. **同名文件歧义**：vault 里不同目录可存在同名笔记，Obsidian 用最短路径消歧。重写时保留原有的消歧形式（如 `[[sub/Note]]` 不要简化为 `[[Note]]`）。
5. **`#锚点` / `^块引用`**：只替换路径前缀，锚点原样保留；锚点指向的标题没变就不用管。
6. **大小写**：Obsidian 链接解析与文件系统行为相关，默认精确匹配；Windows 上若有大小写不一致的历史链接，用 `--case-insensitive` 复核。
7. **不要动 `.obsidian/` 内的配置**（除非任务明确要求）；插件数据（如 Claudian 的会话记录）不在链接修复范围内。
8. **Obsidian 开着 ≠ 链接安全**：watcher 只感知不修复（见核心事实 2）；移动已打开的文件还可能冲突，操作后让用户手动触发 Obsidian 的"检测到外部变更"重载即可。
9. **批量重命名目录**：先跑一次 dry-run 覆盖所有受影响文件，人工核对清单后再执行。
10. 校验脚本会跳过代码块（``` 围栏）内的伪链接，避免误报。

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
