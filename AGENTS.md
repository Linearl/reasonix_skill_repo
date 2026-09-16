# reasonix_skill_repo — 维护约定（给维护者与 AI agent）

本仓库是 Reasonix 的用户级技能集合（**PUBLIC**）。技能在 `skills/<name>/SKILL.md`，部分技能带 `references/`、`scripts/` 等子目录。

---

## 一、这个仓库与「Reasonix 技能目录」是两份拷贝

| 位置 | 作用 |
|---|---|
| **本仓库**：`github-repo/reasonix_skill_repo/skills/` | 版本源、公开分发 |
| **Reasonix 运行时**：`%APPDATA%\reasonix\skills\<name>/` | agent 实际加载的那份 |

**两者不会自动同步**，改完必须手动对齐：

```bash
# 仓库 → 技能目录
# （技能目录不在工作区，write_file / edit_file 写不了，用 bash 或 python 改）
cp github-repo/reasonix_skill_repo/skills/<name>/SKILL.md \
   "$APPDATA/reasonix/skills/<name>/SKILL.md"

# 验证
diff -q --strip-trailing-cr <仓库版> <技能目录版>
```

**比对务必加 `--strip-trailing-cr`** —— 两侧行尾（CRLF / LF）常不同，普通 `diff` 会报「全文不同」，把它误判成内容差异。2026-09-16 实测：8 个「不一致」里 6 个只是行尾。

**反向也要留意**：技能目录那份可能比仓库新（本地改完没同步回来）。判断方向看**文件时间 + git log**，不要只看行数。

---

## 二、脱敏约定（公开仓库必做）

本仓库是 **PUBLIC**，向它同步带本地信息的技能时**必须脱敏**：

- **本地绝对路径**（如 `D:\1.workspace\...`）→ 改成仓库名或相对路径；
- **账号 / 密码 / token** → 改成 `<账号>` / `<密码>` 之类占位符。

### ⚠️ 脱敏后必须检查格式

**历史上出过一次事故**：脱敏时把

```
参考 `D:\1.workspace\media_crawler\MediaCrawler-main\media_platform\bilibili\help.py` 的 `BilibiliSign`
```

改成了**反引号不配对**的

```
参考 `MediaCrawler 的 `media_platform/bilibili/help.py`` 的 `BilibiliSign`
```

markdown 渲染坏掉，且**长期没被发现**（直到 2026-09-16 比对时才发现）。

⇒ **改完请检查行内代码的反引号是否成对**。正确写法示例：

```
参考 MediaCrawler 仓库的 `media_platform/bilibili/help.py` 里的 `BilibiliSign`
```

### 两侧有意不同，不算「不同步」

**技能目录那份可以保留本地绝对路径**（离线可用性优先）。**因此同一个技能在两处内容不同是预期行为**，不必强行拉齐 —— 只在语义有实质变化时才需要双向同步。

---

## 三、与「分享包 A」的同步规则

存在一个精简分享包（**12 个聚焦技能**，面向分发）。同步是**单向且有约束**的：

- **本仓库 → 分享包 A**：**只同步同名技能的内容**（文件级覆盖）；
- **绝不要**把本仓库的新增技能带进 A —— A 的技能清单是固定的。

---

## 四、提交纪律

- **禁止 `git add -A` / `git add .`** —— 只用**显式路径**；提交前 `git status --short` 核对暂存区；
- 提交信息用**英文 + conventional 前缀**：`feat(skills):` / `fix(skill):` / `docs(skills):` / `chore:`；
- 需要代理时：`https_proxy=http://127.0.0.1:10808 git push origin main`。

---

## 五、目录结构

```
skills/<name>/SKILL.md   # 技能正文（frontmatter: name / description）
skills/<name>/...        # 可选：references/ scripts/ 等
docs/                    # 仓库级文档
evidence/                # 证据 / 素材
reasonix-plugin.json     # 插件清单
```

---

## 六、常见操作速查

| 要做的事 | 怎么做 |
|---|---|
| 改一个技能 | 改 `skills/<name>/SKILL.md` → 显式路径提交 → push → `cp` 同步到技能目录 |
| 查两侧差异 | `diff -q --strip-trailing-cr <仓库版> <技能目录版>` |
| 查某技能何时改的 | `git log --format="%h %ad %s" --date=short -- skills/<name>/` |
| 拉开源仓库 | `https_proxy=... gh repo view Linearl/reasonix_skill_repo` |

---

**关联**：技能的实际加载路径与插件四件套见 Reasonix 记忆 `reasonix-plugin-install`；本仓库的迁移历史见 `技能仓库迁移到github-repo-与技能目录同步-20260916`。
