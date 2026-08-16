#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
任务 B-2（主力机，人工运行）：发布审查结果 → dist（主版本）

两种模式：
  1. 常规发布：python sync-publish.py --week 2026-W33
     读取 work\\review\\<周>\\draft\\（整理后的 fact + deleted.txt + skills\\）→ 写入 dist
  2. 首次种子：python sync-publish.py --seed <机器名>
     把某机器快照整体作为 dist 初版（首次搭建时用，之后走常规发布）

安全：执行前打印完整操作清单并交互确认；删除一律进 work\\archive 回收，不直接删。
"""
import argparse
import datetime
import json
import re
import shutil
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync_common as C

NAME_RE = re.compile(r"^[\w\-.]{1,80}$")


def sanitize_name(name: str) -> str:
    name = re.sub(r"[^\w\-.]", "-", name).strip("-")
    return name[:80] or "fact"


def set_fm_field(content: str, field: str, value: str) -> str:
    """在 frontmatter 中设置/替换一个字段（无 frontmatter 则补一个）。

    注意保留 `---` 之后的正文（历史 bug：正则未捕获正文导致截断）。
    """
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", content, re.S)
    if not m:
        return f"---\n{field}: {value}\n---\n\n" + content
    head_fm, tail = m.group(1), m.group(2)
    if re.search(rf"^{field}:", head_fm, re.M):
        head_fm = re.sub(rf"^{field}:.*$", f"{field}: {value}", head_fm, count=1, flags=re.M)
    else:
        head_fm = head_fm.rstrip() + f"\n{field}: {value}"
    return f"---\n{head_fm}\n---\n" + tail


def rebuild_memindex(dist_g: Path):
    """重建 dist MEMORY.md 索引（派生索引，由 active facts 生成）"""
    entries = []
    for f in sorted(dist_g.glob("*.md")):
        if f.name == "MEMORY.md":
            continue
        fm = C.parse_frontmatter(f.read_text(encoding="utf-8", errors="replace"))
        title = fm.get("title") or f.stem
        desc = fm.get("description") or ""
        meta = fm.get("metadata")
        scope = meta.get("scope") if isinstance(meta, dict) else ""
        ftype = meta.get("type") if isinstance(meta, dict) else ""
        entries.append(f"- [{title}]({f.name}) — [{scope}/{ftype}] {desc}")
    C.atomic_write(dist_g / "MEMORY.md", "\n".join(entries) + ("\n" if entries else ""))


def build_pull_guide(root: Path) -> Path:
    """生成 dist\\PULL-GUIDE.md：静态指南 + 当次 dist 内容清单 + ⚠️ 机器特定条目标注。

    在每次 publish 完成后调用；内容随 dist 分发，供非主力机 Pull 后参考。
    """
    dist_g = root / "dist" / "memory" / "global"
    dist_skills = root / "dist" / "skills"
    # 机器名单（用于标记）：inbox 下各机目录名
    inbox = root / "inbox"
    machines = sorted(d.name for d in inbox.iterdir()) if inbox.is_dir() else []

    # ---- credential 合并：各机 inbox\\credential → dist\\credential\\<machine>\\ ----
    # 不走 copy_tree（排除清单含 "nas-" 前缀，会误伤 nas-credentials.md）
    if inbox.is_dir():
        for mdir in sorted(inbox.iterdir()):
            if not mdir.is_dir() or mdir.name.startswith("."):
                continue
            src_cred = mdir / "credential"
            if src_cred.is_dir():
                n = 0
                for f in sorted(src_cred.rglob("*")):
                    if f.is_dir():
                        continue
                    if C.copy_file(f, root / "dist" / "credential" / mdir.name / f.relative_to(src_cred)):
                        n += 1
                if n:
                    C.log("publish", f"credential merged from {mdir.name}: {n} files")

    # ---- 记忆条目 + 机器特定标记 ----
    fact_lines: list[str] = []
    warn_lines: list[str] = []
    if dist_g.is_dir():
        for f in sorted(dist_g.glob("*.md")):
            if f.name == "MEMORY.md":
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
            hits = C.mark_machine_specific(text, machines)
            flag = f" ⚠️ 含机器特定内容" if hits else ""
            fact_lines.append(f"- `{f.name}`{flag}")
            if hits:
                kinds = ", ".join(sorted({h[1] for h in hits[:6]}))
                warn_lines.append(f"  - `{f.name}`：疑似 {kinds}（行号: {', '.join(str(h[0]) for h in hits[:6])}）——可能是某台机器的本机事实/凭据，**按需参考，勿照抄**")

    # ---- 技能清单 ----
    skill_lines = []
    if dist_skills.is_dir():
        for e in sorted(dist_skills.iterdir()):
            n = sum(1 for _ in e.rglob("*")) if e.is_dir() else 1
            skill_lines.append(f"- `{e.name}` ({n} 文件)")

    # ---- 各机凭据收口状态检测（待办自动显示/消失）----
    cred_todos: list[str] = []
    secret_pattern = re.compile(r"LiJie|3026625|d27qK9Vh1|123456|admin/[A-Za-z0-9]")
    for mdir in sorted(inbox.iterdir()) if inbox.is_dir() else []:
        if not mdir.is_dir() or mdir.name.startswith("."):
            continue
        mname = mdir.name
        has_cred = (mdir / "credential").is_dir()
        leaked: list[str] = []
        g = mdir / "memory" / "global"
        if g.is_dir():
            for f in g.glob("*.md"):
                try:
                    t = f.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                if secret_pattern.search(t):
                    leaked.append(f.name)
        if has_cred and not leaked:
            continue
        detail = []
        if not has_cred:
            detail.append(f"未建 credential 目录")
        if leaked:
            detail.append(f"{len(leaked)} 个记忆文件含明文凭据: {', '.join(leaked[:3])}")
        cred_todos.append(f"- ⚠️ `{mname}`：{'；'.join(detail)}")

    # ---- 生成指南 ----
    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    lines = [
        "# Reasonix 同步：Pull 指南（非主力机必读）",
        "",
        f"> 本文件由主力机发布 dist 时自动生成（{now}）。随 dist 分发，Pull 方据此处理拉取到的内容。",
        "",
        "## 一、Pull 后会发生什么（内置规则，无需操作）",
        "",
        "- dist 有、本机无 → 拉取（本机曾 forget 过的不复活）",
        "- dist 新、本机旧 → 覆盖（旧版自动备份到 `%APPDATA%\\reasonix\\sync-backup\\`）",
        "- 本机新、dist 旧 → 保留本机版，下轮由主力机裁决",
        "- 本机有、dist 无 → 保留（本机独有）",
        "- 技能同名 → dist 为准覆盖；本机独有技能保留",
        "- **Pull 永不删除本机任何东西**",
        "",
        "## 二、技能与记忆的解耦原则（2026-08-16 起）",
        "",
        "- dist 中的**技能 = 脱敏版**（与 GitHub `Linearl/reasonix_skill_repo` 保持一致）：不含本机路径/IP/凭据/端口，引用本机信息处用占位符（`<local-home>`/`<本地代理端口>`）",
        "- **本机环境细节存本机记忆**（如 `local-env-notes`）或本机凭据文件，**不要**把机器事实写进技能或发布到 dist",
        "- 技能执行需要本机信息时：从本机记忆/凭据取；本机没有对应环境（如该技能源自台式机的 NAS 任务）→ **技能降级使用或跳过**，不要照搬其他机器的凭据",
        "- 某些记忆引用本机专属技能/路径（如 `missav-抓取任务状态与要点` 提到 `skill missav-download`、`V:\\` 盘）：**该技能/路径只存在于来源机器**，Pull 后其他机器没有它，属正常现象",
        "",
        "## 三、本次 dist 内容",
        "",
        f"### 记忆（{len(fact_lines)} 条）",
        *fact_lines,
        "",
        "### ⚠️ 机器特定/含凭据条目（重点阅读）",
        *(warn_lines or ["- （无）"]),
        "",
        f"### 技能（{len(skill_lines)} 个）",
        *skill_lines,
        "",
        "## 四、credential 凭据目录（凭据收口，2026-08-16 起）",
        "",
        "- **凭据一律收口到 `credential` 目录，记忆/技能中不出现明文凭据**（记忆只引用路径）",
        "- 各机器凭据随 Push 备份到 `inbox\\<机器名>\\credential\\`，发布时汇总到 `dist\\credential\\<机器名>\\`",
        "- **Pull 会自动把 `dist\\credential\\<本机计算机名>\\` 复制回本机 `%APPDATA%\\reasonix\\global-workspace\\credential\\`**（覆盖前备份）——即凭据目录应位于 reasonix 的全局工作空间下",
        "- 本机新增/修改凭据 → 放入 `global-workspace\\credential\\` 即可，下次 Push 自动备份",
        "- ⚠️ 对外发布/分享任何内容前，确认不含 `credential\\` 目录与明文凭据",
        "",
        "## 五、各机器凭据收口状态（待办自动检测）",
        "",
        *(cred_todos or ["- ✅ 所有机器均已收口（credential 目录已建、无明文凭据记忆）"]),
        "",
        "### 收口操作步骤（未完成机器的 reasonix 照此执行）",
        "",
        "1. 创建本机凭据目录：`mkdir %APPDATA%\\reasonix\\global-workspace\\credential`",
        "2. 把本机所有明文凭据（密码/令牌/密钥）整理成 md 文件放入该目录（格式参考 `dist\\credential\\<机器名>\\` 下的现有文件）",
        "3. 修改相关记忆：删除明文凭据，改为引用 `credential\\<文件名>.md`（如：`密码：见 credential/nas-credentials.md`）",
        "4. 验证：本机记忆与技能中 grep 不到明文凭据（`LiJie`/`3026625`/`123456` 等）",
        "5. 跑一次 `python sync-push.py`——credential 自动备份到 inbox，记忆快照自动脱敏",
        "",
        "## 六、Pull 后检查、总结与反馈",
        "",
        "1. 技能生效：本机 `%APPDATA%\\reasonix\\skills\\` 出现新技能目录，reasonix 会话中技能索引可见",
        "2. 记忆可 recall：在会话中提及新记忆主题，确认能被检索到",
        "3. 机器特定条目按需处理：参考「三」中的 ⚠️ 条目——本机用不到的可以不管（保留无害）或 `forget` 掉",
        "4. 本机环境记忆（如 `local-env-notes`）若缺失或过时，在本机补充/更新——它不会发布到 dist",
        "5. **检查并反馈（各机约 5 分钟）**：Pull 任务会自动运行 `sync-feedback.py`，在 `feedback\\` 生成模板 `pull-review-<周>-<本机名>.md`；按模板检查清单核对后，填写「检查结果」「发现的问题」「对体系的建议」，保存即成为反馈报告",
        "6. 反馈报告保存于 `feedback\\`（OneDrive 共享），主力机下轮 Organize 时可见并纳入处理",
        "",
    ]
    guide = root / "dist" / "PULL-GUIDE.md"
    C.atomic_write(guide, "\n".join(lines) + "\n")
    C.log("publish", f"pull guide regenerated: {guide}")
    return guide


def seed_mode(root: Path, machine: str) -> int:
    src = root / "inbox" / machine
    if not (src / "skills").is_dir() and not (src / "memory" / "global").is_dir():
        print(f"inbox\\{machine} 没有可种子的内容（先在该机器跑 sync-push.py）")
        return 2
    dist_skills = root / "dist" / "skills"
    dist_g = root / "dist" / "memory" / "global"
    print(f"== 种子模式: inbox\\{machine} -> dist")
    n1 = C.copy_tree(src / "skills", dist_skills) if (src / "skills").is_dir() else 0
    n2 = 0
    if (src / "memory" / "global").is_dir():
        for f in sorted((src / "memory" / "global").glob("*.md")):
            if C.copy_file(f, dist_g / f.name):
                n2 += 1
    if input("以上将覆盖 dist 现有内容，确认？[y/N] ").strip().lower() != "y":
        print("已取消")
        return 1
    rebuild_memindex(dist_g)
    dist_meta = {
        "seed_from": machine,
        "published_at": C.now_iso(),
        "facts": sorted(f.name for f in dist_g.glob("*.md") if f.name != "MEMORY.md"),
        "skills": sorted(e.name for e in dist_skills.iterdir()) if dist_skills.is_dir() else [],
    }
    C.atomic_write(root / "meta" / "dist.json", json.dumps(dist_meta, ensure_ascii=False, indent=2))
    g = build_pull_guide(root)
    print(f"== 种子完成: {n2} 个事实 / {n1} 个技能文件")
    print(f"== Pull 指南已生成: {g}")
    return 0


def normal_mode(root: Path, week: str) -> int:
    review_dir = root / "work" / "review" / week
    draft = review_dir / "draft"
    if not draft.is_dir():
        print(f"未找到 {draft} —— 先运行 reasonix-sync-review 技能生成整理稿")
        return 2

    dist_g = root / "dist" / "memory" / "global"
    dist_g.mkdir(parents=True, exist_ok=True)
    dist_skills = root / "dist" / "skills"

    # ---- 计划 ----
    plan: list[tuple[str, str, str]] = []
    for f in sorted(draft.glob("*.md")):
        plan.append(("新增/更新 fact", f.name, str(f)))
    deleted: list[str] = []
    dl = draft / "deleted.txt"
    if dl.exists():
        for line in dl.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                deleted.append(line)
    for name in deleted:
        plan.append(("删除 fact(回收)", name, "→ work/archive"))
    skill_dir = draft / "skills"
    if skill_dir.is_dir():
        for e in sorted(skill_dir.iterdir()):
            plan.append(("技能", e.name, "→ dist/skills"))

    print("== 待执行操作 ==")
    for kind, a, b in plan:
        print(f"  [{kind}] {a}  {b}")
    if not plan:
        print("（draft 为空，无可发布内容）")
        return 0
    if input("确认发布？[y/N] ").strip().lower() != "y":
        print("已取消")
        return 1

    # ---- 执行 ----
    n_facts = 0
    archive = root / "work" / "archive" / week
    archive.mkdir(parents=True, exist_ok=True)
    for kind, a, _ in plan:
        if kind == "新增/更新 fact":
            src = draft / a
            content = src.read_text(encoding="utf-8")
            fm = C.parse_frontmatter(content)
            fid = fm.get("id") or "mem-" + uuid.uuid4().hex
            name = sanitize_name(fm.get("name") or src.stem)
            if not fm.get("id"):
                content = set_fm_field(content, "id", fid)
            if fm.get("name") != name:
                content = set_fm_field(content, "name", name)
            if not fm.get("scope", ""):
                content = set_fm_field(content, "scope", "global")
            # 完整性校验：frontmatter 后必须有正文（防历史截断类问题静默发布）
            fm_end = content.find("\n---")
            if fm_end < 0 or not content[fm_end + 4:].strip():
                print(f"  ⚠️ 跳过疑似损坏的 fact: {a}（frontmatter 后无正文，请检查 draft 源文件）")
                C.log("publish", f"WARN skip broken fact draft: {a}")
                continue
            C.atomic_write(dist_g / f"{name}.md", content)
            n_facts += 1
            print(f"  ✓ fact: {name}.md (id={fid[:20]}…)")
        elif kind == "删除 fact(回收)":
            src = dist_g / a
            if src.exists():
                shutil.move(str(src), str(archive / a))
                print(f"  ✓ 回收: {a}")
        elif kind == "技能":
            n = C.copy_tree(draft / "skills" / a, dist_skills / a)
            print(f"  ✓ 技能: {a} ({n} 文件)")

    rebuild_memindex(dist_g)
    dist_meta = {
        "publish_week": week,
        "published_at": C.now_iso(),
        "facts": sorted(f.name for f in dist_g.glob("*.md") if f.name != "MEMORY.md"),
        "skills": sorted(e.name for e in dist_skills.iterdir()) if dist_skills.is_dir() else [],
    }
    C.atomic_write(root / "meta" / "dist.json", json.dumps(dist_meta, ensure_ascii=False, indent=2))
    g = build_pull_guide(root)
    print(f"== 发布完成: {n_facts} 个事实, 回收 {len(deleted)} 条, 技能已更新")
    print(f"== Pull 指南已生成: {g}")
    C.log("publish", f"week={week} facts={n_facts} deleted={len(deleted)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", default=None)
    ap.add_argument("--seed", default=None)
    args = ap.parse_args()
    root = C.sync_root()
    if args.seed:
        return seed_mode(root, args.seed)
    return normal_mode(root, args.week or C.iso_week())


if __name__ == "__main__":
    sys.exit(main())
