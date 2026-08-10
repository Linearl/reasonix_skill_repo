---
name: onenote-to-obsidian
description: 把 OneNote 分区文件（.one）解析为 Markdown 并导入 Obsidian。当用户需要从 OneNote 导出笔记、把 .one 转 md、OneNote 同步失败需要本地恢复、或导入 OneNote 分区到 vault 时使用。不依赖 OneNote 同步/云端，直接解析本地 .one 文件（经 OneNote COM API）。
---

# OneNote .one 文件 → Obsidian Markdown 导入

把 OneNote 分区文件（.one，本地导出或缓存副本）解析为 Markdown，按季度/分区组织导入 Obsidian vault。**不依赖 OneNote 同步状态**——适合同步失败、分区被服务器删除、importer 漏导等场景的本地恢复。

## 核心原理

- 用 **OneNote 桌面版 COM API**（`OneNote.Application`，PowerShell 调用）打开本地 .one 文件：
  - `OpenHierarchy(path, '', [ref]hier, 0)` —— **第 4 参数必须 0（cftLocal）**，其他值报 0x80042018
  - `GetHierarchy(hier, 1, [ref]xml)` —— **scope 必须 1（hsChildren）**，3 会返回 0 页面，2 报 0x80042014
  - 逐页 `GetPageContent(pageId, [ref]xml, 0)` —— 第 3 参数 0=piBasic（纯文本），1=piBinaryData（含图片二进制，慢约 2 倍）
- PowerShell 逐页导出为 XML 文件 + index.tsv，Python 解析 XML → Markdown（剥 span 富文本、checkbox 还原、嵌套缩进）

## 前置条件（本机已具备）

- OneNote 桌面版（`C:\Program Files\Microsoft Office\root\Office16\ONENOTE.EXE`）
- PowerShell 5.1+（Windows 自带）
- Python 3（标准库即可）

## 常见故障：导出 .one 不完整（页面缺失）

**现象**：导出的 .one 文件页面数远少于客户端显示的页面数（如 759MB 文件只有 11 页；同步报错的分区导出后缺大量周报）。

**根因（实战确认）**：**未同步（0xE0000063/0xE000006A）的页面在迁移/导出流程中被跳过**——剪贴分区时同步失败的页面不会迁移成功，导出 .one 时这些页面连页面条目都不会写入文件（不只是内容缺失）。客户端能看到（缓存）≠ 文件里有。

**解决**：
1. 先修复同步：OneNote 中右键分区 → 立即同步，等报错消失（或把内容剪贴到同步健康的新分区，待新分区完全同步）
2. **重新导出 .one** 后再解析——同步修复后重新导出的文件才是完整的（实战：19-20.one 28 页 → 重新导出 169 页；21~23Q1.one 1 页 → 305 页）
3. 判断导出是否完整：`GetHierarchy` 页面数 ≈ 客户端显示的页面数；或抽查报错列表中的页面名是否出现在页面列表里

**教训**：文件大小与内容完整性无关（759MB 空壳 vs 72MB 完整）；"客户端能看到"不能证明导出文件完整。

## 常见故障：COM 报"库没有注册"（0x8002801D）

现象：`New-Object -ComObject OneNote.Application` 成功，但任何方法调用报 `-2147319779 库没有注册`；或 pywin32 报 `AttributeError: OneNote.Application.OpenHierarchy`。

原因：OneNote 的类型库注册损坏/缺失（Office 安装残留）——GetIDsOfNames 内部按 `LoadRegTypeLib` 找类型库失败。

修复（**需要管理员 PowerShell 运行一次**）：
```powershell
# 15.0 类型库（真实版本 1.1，资源 3）
$base = 'HKLM:\SOFTWARE\Classes\TypeLib\{0EA692EE-BB50-4E3C-AEF0-356D91732725}\1.1'
New-Item -Path $base -Force | Out-Null
Set-ItemProperty -Path $base -Name '(default)' -Value 'Microsoft OneNote 15.0 Type Library'
New-Item -Path ($base + '\0\Win64') -Force | Out-Null
Set-ItemProperty -Path ($base + '\0\Win64') -Name '(default)' -Value 'C:\Program Files\Microsoft Office\Root\Office16\ONENOTE.EXE\3'
New-Item -Path ($base + '\0\Win32') -Force | Out-Null
Set-ItemProperty -Path ($base + '\0\Win32') -Name '(default)' -Value 'C:\Program Files\Microsoft Office\Root\Office16\ONENOTE.EXE\3'
# 12.0 类型库（兼容接口，资源 2）
$base = 'HKLM:\SOFTWARE\Classes\TypeLib\{F2A7EE29-8BF6-4A6D-83F1-098E366C709C}\1.0'
New-Item -Path $base -Force | Out-Null
Set-ItemProperty -Path $base -Name '(default)' -Value 'Microsoft OneNote 12.0 Type Library'
New-Item -Path ($base + '\0\Win64') -Force | Out-Null
Set-ItemProperty -Path ($base + '\0\Win64') -Name '(default)' -Value 'C:\Program Files\Microsoft Office\Root\Office16\ONENOTE.EXE\2'
New-Item -Path ($base + '\0\Win32') -Force | Out-Null
Set-ItemProperty -Path ($base + '\0\Win32') -Name '(default)' -Value 'C:\Program Files\Microsoft Office\Root\Office16\ONENOTE.EXE\2'
New-Item -Path ($base + '\Flags') -Force | Out-Null
Set-ItemProperty -Path ($base + '\Flags') -Name '(default)' -Value '0'
New-Item -Path ($base + '\HelpDir') -Force | Out-Null
```
执行后**杀 OneNote 进程**（`taskkill /IM ONENOTE.EXE /F`）再重试。

验证：PowerShell `New-Object -ComObject OneNote.Application` 后能调 `OpenHierarchy`（报参数错误也算通——比"库没有注册"好）。

## 执行流程

### Step 1 确认输入
- .one 文件路径（用户提供或从 `%LOCALAPPDATA%\Microsoft\OneNote` 缓存找）
- 文件头是 GUID（非 `\x00\x01`）即为新版 OneStore 格式，COM 可读

### Step 2 导出（PowerShell）
```bash
powershell -ExecutionPolicy Bypass -File "<技能目录>/scripts/onenote_export.ps1" -OnePath "<文件.one>" -OutDir "<导出目录>" [-PageInfo 0]
```
- 产出：`<OutDir>/pages/NNNN.xml` + `<OutDir>/index.tsv`（序号、页面ID、页面名）
- 303 页约 5-10 分钟；进度每 25 页打印一次
- 注意：**脚本文件必须是 UTF-8 with BOM**（PowerShell 5.1 无 BOM 按 GBK 解码，中文路径会乱码报 0x80042006）；脚本内**不要用 `$pid` 变量**（PowerShell 保留变量）
- 如果 OneNote 实例还开着旧文件，先 `taskkill /IM ONENOTE.EXE /F`（单实例会锁文件，报 0x80042006）

### Step 3 转 Markdown（Python）
```bash
python "<技能目录>/scripts/parse_onenote_xml.py" <导出目录> [输出md目录]
```
- 默认输出到 `<导出目录>/md/`，文件名 `NNNN_页面名.md`
- 特性：Title → `# 标题`；Outline OE 逐段输出；checkbox（Tag indicator 1-18，≥10 勾选）→ `- [x]/[ ]`；嵌套 OE 两级空格缩进；富文本 span 剥离；图片（piBasic 时）→ `![图片]()` 占位
- **index.tsv 首行可能带 BOM**，解析器已处理

### Step 4 导入 Obsidian（可选，按需）
- 按页面名自动归类：`MMDD-MMDD` → 周报；含"年工作日志（" → 节封面；"小结" → 月小结
- 参考现有 vault 结构 `OneNote/工作笔记/工作日志/<季度目录>/`，新建缺失季度
- 导入后跑 `obsidian-vault-organize` 的 check_links.py 校验

### Step 5 图片补充（可选）
- 需要图片时用 `-PageInfo 1` 重新导出（piBinaryData，页面 XML 内嵌 base64 图片）
- 解析时把 `<one:Data>` base64 落盘为图片文件，md 引用本地路径

## 注意事项

1. `.one` 可能是"空壳"（分区头无页面）——GetHierarchy(scope=1) 页面数为 0 时，说明导出时 OneNote 本地缓存没有页面数据，需换同步正常的副本
2. 页面 XML 的 `<one:T>` 文本在 CDATA 内且含 `<span>` 富文本——解析必须剥标签
3. 同名页面（如多个"山头简况"）靠序号区分文件名
4. 大文件（几百 MB）导出期间保持 OneNote 前台空闲；导出完成后杀进程释放文件锁
5. 不修改 .one 原文件（只读打开）

## 脚本位置

- `scripts/onenote_export.ps1` — COM 导出（PowerShell，UTF-8 BOM）
- `scripts/parse_onenote_xml.py` — XML → Markdown（Python 标准库）

技能目录查找：`glob("**/onenote-to-obsidian/scripts/*")`；典型安装位置 `%APPDATA%\reasonix\skills\onenote-to-obsidian\scripts\`。

## 相关技能

- [[obsidian-vault-organize]] — 导入后断链校验、引用维护
- [[obsidian-markdown]] — 生成的 md 语法规范
