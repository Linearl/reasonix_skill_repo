# Reasonix 实用技能包

> 面向 **Reasonix**（兼容 Claude Code 等支持 Agent Skills 的客户端）的实战技能集合：18 个技能，覆盖**专利检索、知识加工、网页抓取、本地 OCR、项目管理、笔记整理、远程部署**七大场景，全部来自真实项目实战沉淀。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Skills](https://img.shields.io/badge/Skills-18-blue)](#-技能清单)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)](#-安装)

每个技能是一个自包含目录（`SKILL.md` + 配套脚本/参考文档），复制即用，无框架依赖。

---

## 📦 技能清单

| # | 技能 | 作用 | 说明 |
|---|------|------|------|
| 1 | [patent-search](skills/patent-search/) | innojoy + Google Patents 自动化检索、检索式设计、对比文件分级、新颖性/创造性评估、交底书撰写 | ⚠️ **需 innojoy 账号**（登录凭据自行配置） |
| 2 | [book-to-skill](skills/book-to-skill/) | 把 PDF / EPUB / DOCX / HTML / Markdown 等文档提炼成可复用的 agent 技能（框架、心智模型、原则、反模式），附完整 Python 工具链 | 开源项目技能化（MIT，原作者保留版权）；**上游 [virgiliojr94/book-to-skill](https://github.com/virgiliojr94/book-to-skill)** |
| 3 | [web-scraping](skills/web-scraping/) | 任意网页抓取整理为 Markdown：探测 SSR/API、处理限流（-509 等）、CDP 复用 Chrome 登录态、图片本地化 | 基于 B 站专栏文集实战（22 篇、1912 张图、0 失败）；wbi 签名参考 [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler)（自行拉取） |
| 4 | [image-ocr-to-docs](skills/image-ocr-to-docs/) | 批量图片 OCR 转可检索文档：PaddleOCR + 放大预处理，输出同名 .md 或汇总清单，含双引擎交叉验证 | 纯本地推理，数据不出内网 |
| 5 | [migrate-reasonix-project](skills/migrate-reasonix-project/) | 移动/重命名 Reasonix（及 Claude Code）项目目录时保留全部对话历史 | 覆盖会话文件、meta 路径改写、检查点与子代理元数据 |
| 6 | [obsidian-markdown](skills/obsidian-markdown/) | Obsidian 风格 Markdown 语法规范：wikilink / embeds / callouts / properties / frontmatter | 笔记整理基础；**源自 [obsidianmd/obsidian-help](https://github.com/obsidianmd/obsidian-help) 官方文档** |
| 7 | [obsidian-bases](skills/obsidian-bases/) | Obsidian Bases（.base 文件）视图语法：表格/卡片视图、过滤器、公式、汇总 | 需要 Obsidian 1.10+；**源自 [obsidianmd/obsidian-help](https://github.com/obsidianmd/obsidian-help) 官方文档** |
| 8 | [obsidian-cli](skills/obsidian-cli/) | vault CLI 操作：创建/搜索/管理笔记、任务、属性；插件与主题开发调试 | 需要 Obsidian CLI；**源自 [obsidianmd/obsidian-help](https://github.com/obsidianmd/obsidian-help) 官方文档** |
| 9 | [obsidian-vault-organize](skills/obsidian-vault-organize/) | vault 批量整理：移动/重命名/归档后全 vault 重写引用，断链校验归零 | 整理流水线收尾环节 |
| 10 | [onenote-to-obsidian](skills/onenote-to-obsidian/) | OneNote .one 文件本地解析为 Markdown 并导入 Obsidian（OneNote COM API，**不依赖同步**） | 适合同步失败/分区丢失的本地恢复；Windows only |
| 11 | [reasonix-remote-linux-setup](skills/reasonix-remote-linux-setup/) | 在 Linux 远程主机（含绿联 NAS 等魔改系统）上部署 reasonix serve 并打通 Windows 桌面版远程连接 | 含全部已知坑（SSH/SFTP 虚拟视图等），基于绿联 DX4600PRO 实战验证 |
| 12 | [reasonix-sync-deploy](skills/reasonix-sync-deploy/) | 新机器接入 reasonix-sync 多机同步体系：环境探测、OneDrive 始终保留提示、定时任务创建、首次推送验证 | 多机共用一套技能与记忆；需先有同步体系 |
| 13 | [gh-issue-submit](skills/gh-issue-submit/) | 用 gh CLI 向任意 GitHub 仓库提交 issue：模板发现（分支差异）、查重、权限切换陷阱、提交与验证 | 自研（GitHub 工作流；依赖 gh CLI 登录态） |
| 14 | [github-issue-triage](skills/github-issue-triage/) | 自己仓库的 issue 自动化闭环：收集→分析→修复→验证→关闭，关闭前证据硬门槛、先评论后关闭 | 自研（依赖 github-mcp-server 与 Issues 读写权限） |
| 15 | [html-deck-pipeline-skill](skills/html-deck-pipeline-skill/) | 端到端 HTML 讲稿流水线：网站骨架 + WYSIWYG 编辑器 + 4 主题 × 3 字号 + 一键导出 HTML/PPTX，分镜先行/风格契约/质量门 | 自研（2026-08-11 从 linearleaf_skill_repo 迁移） |
| 16 | [invest_analysis](skills/invest_analysis/) | A股/港股系统化投资研究：赛道筛选、供应链验证、财报核验、研报交叉验证（附数据工具链） | 自研（2026-08-11 从 linearleaf_skill_repo 迁移；仅方法论，不构成投资建议） |
| 17 | [code-audit-fix](skills/code-audit-fix/) | 全流程代码审计：缺陷扫描、分优先级批量修复、多轮交叉复核、CI 非交互执行与结果契约 | 自研（2026-08-11 从 linearleaf_skill_repo 迁移） |
| 18 | [session-context-restore](skills/session-context-restore/) | 新会话快速恢复前序工作上下文：git / memory / 任务包三源扫描（<30s）、恢复报告模板、触发词防误触发设计 | 自研（2026-08-12 加入，源自 data_platform 技能库沉淀） |

**来源标注**：4 个技能从其他位置复制而来（经 B 站图文攻略整理流水线沉淀，与 Claude Code 通用），上游链接如下：
- **obsidian-markdown / obsidian-bases / obsidian-cli**：内容整理自 [Obsidian 官方帮助文档仓库 obsidianmd/obsidian-help](https://github.com/obsidianmd/obsidian-help)（help.obsidian.md 的源码）
- **book-to-skill**：上游开源项目 [virgiliojr94/book-to-skill](https://github.com/virgiliojr94/book-to-skill)（MIT，原作者保留版权；本项目为技能化复用）

其余 14 个为本人工作实战自研沉淀。

**组合流水线**：网页抓取（3）→ obsidian-markdown 规范化（6）→ obsidian-vault-organize 整理（9）；OneNote 旧笔记用（10）导入后同流水线整理。

---

## 🚀 快速开始

### 安装（二选一）

**Reasonix（推荐）**——复制到用户级技能目录：

```bash
# Windows
Copy-Item -Recurse skills\* $env:APPDATA\reasonix\skills\
# Linux / macOS
cp -r skills/* ~/.reasonix/skills/
```

**Claude Code**：

```bash
cp -r skills/* ~/.claude/skills/
```

重启客户端后，技能出现在技能索引中，可直接用 `/技能名` 或让 agent 自动调用。详细步骤见 [docs/安装指南.md](docs/安装指南.md)。

### 验证安装

| 触发示例 | 对应技能 |
|---------|---------|
| 「检索一下 XX 技术的现有专利，评估新颖性」 | patent-search |
| 「把这份 PDF 提炼成技能」 | book-to-skill |
| 「抓取这个 B 站文集的全部文章，图片本地保存」 | web-scraping |
| 「把这个图片文件夹全部 OCR 成 markdown」 | image-ocr-to-docs |
| 「我要把项目文件夹从 A 移到 B，保留对话历史」 | migrate-reasonix-project |
| 「整理这个 Obsidian vault，检查断链」 | obsidian-vault-organize |
| 「把 OneNote 的 .one 文件导入 vault」 | onenote-to-obsidian |
| 「在 NAS 上部署 reasonix 并打通桌面版远程连接」 | reasonix-remote-linux-setup |
| 「把这台新电脑接入同步体系」 | reasonix-sync-deploy |

---

## 📁 目录结构

```
reasonix-skills/
├── README.md                  # 本文件
├── LICENSE                    # MIT
├── docs/
│   ├── 安装指南.md             # 安装 / 更新 / 验证 / 排障
│   ├── 技能使用说明.md         # 每个技能的详细使用说明
│   └── 安全与合规.md           # 凭据、账号边界、抓取合规、数据隐私
└── skills/
    ├── patent-search/          # 12 个技能目录，每个含 SKILL.md + 配套脚本
    ├── book-to-skill/
    └── ...
```

---

## ⚠️ 重要提示

- **patent-search** 需要 innojoy 账号，登录凭据自行配置，凭据不要提交到任何仓库。
- **web-scraping** 涉及网页抓取，请遵守目标站点服务条款与所在地区法规；MediaCrawler 参考项目请从 [官方仓库](https://github.com/NanmiCoder/MediaCrawler) 拉取（本仓库不附带其代码）。
- **image-ocr-to-docs / book-to-skill** 首次使用需安装 Python 依赖，详见各技能 SKILL.md。
- **onenote-to-obsidian** 仅 Windows（依赖 OneNote 桌面版 COM API）。
- 各技能会随使用沉淀改进，收到更新后**直接覆盖对应目录**即可升级，不影响已保存的会话历史。
- 完整安全与合规说明见 [docs/安全与合规.md](docs/安全与合规.md)。

---

## 📄 许可

本仓库整体以 [MIT](LICENSE) 协议发布。各技能目录保留其自身来源的许可与版权声明：

| 目录 | 许可 |
|------|------|
| book-to-skill | MIT（上游开源项目） |
| MediaCrawler（web-scraping 引用） | MIT（上游开源项目，本仓库不附带） |
| 其余技能 | MIT（本仓库） |

---

## 🙏 致谢

- [Reasonix](https://github.com/esengine/DeepSeek-Reasonix) —— 技能运行时的核心客户端
- [book-to-skill](https://github.com/thinkinmachine/book-to-skill) —— 文档技能化工具链
- [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) —— 多平台爬虫参考实现
