#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
任务 C（每台机器，每周）：dist（主力机发布的主版本）→ 本机，按 id/name 合并

合并规则：
- 记忆：dist 有本机无 → 复制（但本机 .archive 里已归档的同 id 事实不复活）；
        dist 与本机都有 → 取 updated_at 较新者，覆盖前备份到 <home>\\sync-backup\\<ts>；
        本机有 dist 无 → 保留（本机独有经验，交给下周 organize 决定是否升全局）。
- 技能：dist 为准覆盖同名技能（先备份）；本机独有技能保留。
- 本机 MEMORY.md 索引不写（reasonix 会在下次写记忆时自动重建）。

用法：
  python sync-pull.py            # 拉取合并
  python sync-pull.py --dry-run  # 演练
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync_common as C


def collect_archived_ids(local_g: Path) -> set:
    """本机 .archive 中已归档事实的 id 集合（用于禁止复活）"""
    ids: set = set()
    arc = local_g / ".archive"
    if arc.is_dir():
        for f in arc.rglob("*.md"):
            fid = C.parse_frontmatter(f.read_text(encoding="utf-8", errors="replace")).get("id")
            if fid:
                ids.add(fid)
    return ids


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = C.sync_root()
    home = Path(C.reasonix_home())
    dist_g = root / "dist" / "memory" / "global"
    dist_skills = root / "dist" / "skills"
    local_g = home / "memory" / "global"
    local_skills = home / "skills"

    if (not dist_g.is_dir() or not any(dist_g.glob("*.md"))) and (not dist_skills.is_dir() or not any(dist_skills.iterdir())):
        print("dist 为空（主力机尚未发布）——跳过")
        return 0

    bk = None  # 惰性创建：仅当确有覆盖时才建备份目录
    pulled_f: list[str] = []
    kept_f: list[str] = []
    skip_archived: list[str] = []
    pulled_s: list[str] = []

    # ---- 记忆合并 ----
    if dist_g.is_dir():
        local_g.mkdir(parents=True, exist_ok=True)
        local_facts = {f.name: f for f in local_g.glob("*.md") if f.name != "MEMORY.md"}
        archived_ids = collect_archived_ids(local_g)
        for f in sorted(dist_g.glob("*.md")):
            if f.name == "MEMORY.md":
                continue
            fm = C.parse_frontmatter(f.read_text(encoding="utf-8", errors="replace"))
            fid = fm.get("id")
            dst = local_g / f.name
            if dst.exists():
                # 本机 active 有同 name → 正常合并（比较 updated_at）
                local_ts = C.fact_ts(dst)
                dist_ts = C.fact_ts(f, fm)
                if dist_ts <= local_ts:
                    kept_f.append(f.name)
                    continue
                if bk is None:
                    bk = C.backup_dir()
                C.copy_file(dst, bk / "memory" / f.name)
            else:
                # 本机无此 name：若 .archive 有同 id → 曾 forget，不复活
                if fid and fid in archived_ids:
                    skip_archived.append(f.name)
                    C.log("pull", f"跳过已归档事实: {f.name} (id={fid})")
                    continue
            if C.copy_file(f, dst):
                pulled_f.append(f.name)
        # 本机有 dist 无 → 保留不动；本机 MEMORY.md 不动

    # ---- 技能合并（dist 为准，覆盖前备份）----
    if dist_skills.is_dir():
        local_skills.mkdir(parents=True, exist_ok=True)
        for e in sorted(dist_skills.iterdir()):
            dst = local_skills / e.name
            if dst.exists():
                if C.tree_sig(e) == C.tree_sig(dst):
                    continue  # 内容一致
                if bk is None:
                    bk = C.backup_dir()
                if dst.is_dir():
                    shutil_copytree = __import__("shutil").copytree
                    shutil_copytree(str(dst), str(bk / "skills" / e.name))
                else:
                    C.copy_file(dst, bk / "skills" / e.name)
            if e.is_dir():
                C.copy_tree(e, dst)
            else:
                # 单文件条目（如 .7z 附件）直接复制——修复台式机反馈 #3：copy_tree 对非目录返回 0 不落盘
                C.copy_file(e, dst)
            pulled_s.append(e.name)

    # ---- credential：dist\credential\<本机名>\ → 本机 global-workspace\credential\ ----
    pulled_c: list[str] = []
    dist_cred = root / "dist" / "credential"
    machine = C.machine_name(C.load_config())
    dc = dist_cred / machine
    if dc.is_dir():
        gw_cred = home / "global-workspace" / "credential"
        gw_cred.mkdir(parents=True, exist_ok=True)
        for f in sorted(dc.rglob("*")):
            if f.is_dir():
                continue
            rel = f.relative_to(dc)
            dst = gw_cred / rel
            if dst.exists():
                if C.file_sha256(dst) == C.file_sha256(f):
                    continue
                if bk is None:
                    bk = C.backup_dir()
                C.copy_file(dst, bk / "credential" / rel.name)
            if C.copy_file(f, dst):
                pulled_c.append(str(rel))

    print("== pull 摘要 ==")
    print(f"  拉取记忆 {len(pulled_f)} 条: {', '.join(pulled_f) or '-'}")
    print(f"  跳过(本机更新) {len(kept_f)} 条")
    print(f"  跳过(本机已归档) {len(skip_archived)} 条: {', '.join(skip_archived) or '-'}")
    print(f"  拉取技能 {len(pulled_s)} 个: {', '.join(pulled_s) or '-'}")
    print(f"  拉取凭据 {len(pulled_c)} 个: {', '.join(pulled_c) or '-'}")
    if bk:
        print(f"  覆盖前备份: {bk}")
    C.log("pull", f"pulled_facts={len(pulled_f)} kept={len(kept_f)} archived_skip={len(skip_archived)} pulled_skills={len(pulled_s)} pulled_cred={len(pulled_c)}")

    # ---- Pull 后自动生成检查/反馈模板（sync-feedback.py，2026-08-16 台式机建议落地）----
    try:
        fb = Path(__file__).resolve().parent / "sync-feedback.py"
        if fb.exists():
            import subprocess
            r = subprocess.run([sys.executable, str(fb)], capture_output=True, text=True, encoding="utf-8")
            if r.returncode == 0 and r.stdout.strip():
                print(r.stdout.strip())
            elif r.stderr.strip():
                C.log("pull", f"feedback stderr: {r.stderr.strip()[:200]}")
    except Exception as e:
        C.log("pull", f"feedback generate skipped: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
