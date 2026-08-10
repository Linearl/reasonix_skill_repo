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
    """在 frontmatter 中设置/替换一个字段（无 frontmatter 则补一个）"""
    m = re.match(r"^(---\s*\n)(.*?)(\n---)", content, re.S)
    if not m:
        return f"---\n{field}: {value}\n---\n\n" + content
    head, body, tail = m.group(1), m.group(2), m.group(3)
    if re.search(rf"^{field}:", body, re.M):
        body = re.sub(rf"^{field}:.*$", f"{field}: {value}", body, count=1, flags=re.M)
    else:
        body = body + f"\n{field}: {value}"
    return head + body + tail


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
    print(f"== 种子完成: {n2} 个事实 / {n1} 个技能文件")
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
    print(f"== 发布完成: {n_facts} 个事实, 回收 {len(deleted)} 条, 技能已更新")
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
