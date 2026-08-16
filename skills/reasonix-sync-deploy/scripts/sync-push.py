#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
任务 A（每台机器，每周）：本机 reasonix 用户级技能 + 全局记忆 + 近期项目记忆
→ OneDrive\\ReasonixSync\\inbox\\<计算机名>\\

机器名自动探测（COMPUTERNAME），各机器各自创建 inbox 子目录，无需手动配置。
安全：只推 skills 与 memory 的指定部分；删除一律走 .removed 回收；凭据/配置类文件永不触碰。

用法：
  python sync-push.py            # 推送
  python sync-push.py --dry-run  # 演练，不写 meta
"""
import argparse
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync_common as C


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = C.load_config()
    machine = C.machine_name(cfg)
    home = Path(C.reasonix_home())
    root = C.sync_root()
    inbox = root / "inbox" / machine
    window = int(cfg.get("memory_projects_window_days", 30))

    if not home.is_dir():
        print(f"reasonix home 不存在: {home}")
        C.log("push", f"[{machine}] reasonix home 不存在: {home}")
        return 2

    print(f"== push: {machine} -> {inbox}")
    C.log("push", f"start machine={machine} home={home}")

    # ---- 1. 技能（整目录镜像）----
    n_skills = 0
    n_removed_skills = 0
    skills_src = home / "skills"
    if skills_src.is_dir() and any(skills_src.iterdir()):
        n_skills = C.copy_tree(skills_src, inbox / "skills")
        # 本机顶层条目清单（技能目录 + 散文件），镜像中多余的移到 .removed
        keep = set()
        for e in skills_src.iterdir():
            if e.is_dir() and not C.is_excluded_dir(e.name):
                keep.add(e.name)
            elif e.is_file() and not C.is_excluded(e.name):
                keep.add(e.name)
        if not args.dry_run:
            n_removed_skills = C.clean_mirror_top(inbox / "skills", keep)
        print(f"  技能: 复制 {n_skills} 文件, 清理 {n_removed_skills} 项")
    else:
        print(f"  ⚠️ 未发现本机用户级技能（{skills_src} 不存在或为空）——如本机应装有技能，请检查 REASONIX_HOME 与技能安装位置")
        C.log("push", f"[{machine}] 未发现用户级技能目录: {skills_src}")

    # ---- 2. 全局记忆（active facts，不含 MEMORY.md 索引、.archive、.revisions）----
    n_facts = 0
    n_removed_facts = 0
    active: list[str] = []
    mem_g = home / "memory" / "global"
    if mem_g.is_dir():
        for f in sorted(mem_g.glob("*.md")):
            if f.name == "MEMORY.md":
                continue
            active.append(f.name)
            if C.copy_file(f, inbox / "memory" / "global" / f.name):
                n_facts += 1
        if not args.dry_run:
            n_removed_facts = C.clean_mirror(inbox / "memory" / "global", set(active), "*.md")
        print(f"  全局记忆: 复制 {n_facts} 个事实, 清理 {n_removed_facts} 项")

    # ---- 3. 近期项目记忆（供主力机提炼经验，不直接同步）----
    n_proj = 0
    proj_in = inbox / "memory-projects"
    mem_root = home / "memory"
    if mem_root.is_dir():
        now = datetime.datetime.now(datetime.timezone.utc)
        for pdir in sorted(d for d in mem_root.iterdir() if d.is_dir() and d.name != "global" and not C.is_excluded_dir(d.name)):
            keep_proj: set[str] = set()
            for f in sorted(pdir.glob("*.md")):
                fm = C.parse_frontmatter(f.read_text(encoding="utf-8", errors="replace"))
                ts = C.parse_ts(fm.get("updated_at"))
                if ts is None:
                    ts = datetime.datetime.fromtimestamp(f.stat().st_mtime, tz=datetime.timezone.utc)
                if (now - ts).days <= window:
                    keep_proj.add(f.name)
                    if C.copy_file(f, proj_in / pdir.name / f.name):
                        n_proj += 1
            if not args.dry_run:
                C.clean_mirror(proj_in / pdir.name, keep_proj, "*.md")
        print(f"  项目记忆(近{window}天): 复制 {n_proj} 个文件")

    # ---- 4. credential 凭据目录（收口后随本机备份到体系）----
    # 注意：不走 copy_tree（其排除清单含 "nas-" 前缀，会误伤 nas-credentials.md）
    n_cred = 0
    cred_src = home / "global-workspace" / "credential"
    if cred_src.is_dir():
        for f in sorted(cred_src.rglob("*")):
            if f.is_dir():
                continue
            if C.copy_file(f, inbox / "credential" / f.relative_to(cred_src)):
                n_cred += 1
        print(f"  credential: 复制 {n_cred} 文件")
    else:
        print(f"  ⚠️ 未发现本机凭据目录（{cred_src}）——如本机有凭据请先收口到该目录")

    if args.dry_run:
        print("[dry-run] 演练结束，未写 meta")
        return 0

    C.write_meta(machine, {
        "machine": machine,
        "last_push": C.now_iso(),
        "active_global_facts": active,
        "skills": sorted(keep) if skills_src.is_dir() else [],
    })
    print(f"== 完成: {n_facts} 事实 / {n_skills} 技能文件 / {n_proj} 项目记忆文件")
    C.log("push", f"done facts={n_facts} skills={n_skills} proj={n_proj} removed={n_removed_facts + n_removed_skills}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
