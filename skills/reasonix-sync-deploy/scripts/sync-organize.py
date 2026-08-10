#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
任务 B-1（主力机，每周五，只读）：汇总各机器 inbox 快照 → work\\review\\<周>\\review.md 待审清单

只读：不写 inbox / dist / 本机记忆，只生成审查清单。
机器特定内容（盘符/IP/凭据/端口/机器名）自动标记 ⚠️，供人工审查时净化。

用法：
  python sync-organize.py            # 本周
  python sync-organize.py --week 2026-W33
"""
import argparse
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync_common as C


def inbox_machines() -> list[Path]:
    inbox = C.sync_root() / "inbox"
    if not inbox.is_dir():
        return []
    return [d for d in sorted(inbox.iterdir()) if d.is_dir() and not d.name.startswith(".")]


def read_fact(p: Path) -> tuple[dict, str]:
    text = p.read_text(encoding="utf-8", errors="replace")
    return C.parse_frontmatter(text), text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", default=None)
    args = ap.parse_args()

    week = args.week or C.iso_week()
    root = C.sync_root()
    review_dir = root / "work" / "review" / week
    review_dir.mkdir(parents=True, exist_ok=True)

    machines = inbox_machines()
    machines = [m for m in machines if (m / "memory" / "global").is_dir() or (m / "skills").is_dir()]
    if not machines:
        print("inbox 下没有任何机器快照 —— 请先在每台机器跑一次 sync-push.py")
        return 2

    dist_g = root / "dist" / "memory" / "global"
    dist_skills = root / "dist" / "skills"
    machine_names = [m.name for m in machines]

    # ---- 记忆：聚合各机 global facts（按文件名/name）----
    inbox_facts: dict[str, dict[str, Path]] = {}
    for mdir in machines:
        g = mdir / "memory" / "global"
        if not g.is_dir():
            continue
        for f in g.glob("*.md"):
            inbox_facts.setdefault(f.name, {}).setdefault(mdir.name, f)

    dist_facts = {f.name: f for f in dist_g.glob("*.md") if f.name != "MEMORY.md"} if dist_g.is_dir() else {}

    # 各机 meta 中的 active 清单（判定"某机删除了事实"）
    active_by_machine = {}
    for mdir in machines:
        active_by_machine[mdir.name] = set(C.read_meta(mdir.name).get("active_global_facts", []))

    new_facts: list[tuple[str, dict]] = []
    mod_facts: list[tuple[str, dict, Path]] = []
    del_facts: list[str] = []
    multi_facts: list[str] = []

    for name, srcs in inbox_facts.items():
        if name not in dist_facts:
            new_facts.append((name, srcs))
            if len(srcs) > 1:
                multi_facts.append(name)
        else:
            dist_ts = C.fact_ts(dist_facts[name])
            newest_ts = max(C.fact_ts(p) for p in srcs.values())
            if newest_ts > dist_ts:
                mod_facts.append((name, srcs, dist_facts[name]))
                if len(srcs) > 1:
                    multi_facts.append(name)

    for name in dist_facts:
        if name in inbox_facts:
            continue
        # 没有任何机器的 active 清单包含它 → 删除候选
        if not any(name in active_by_machine[m] for m in active_by_machine):
            del_facts.append(name)

    # ---- 技能 ----
    dist_skill_set = {e.name for e in dist_skills.iterdir()} if dist_skills.is_dir() else set()
    skill_new: list[str] = []
    skill_conflict: list[tuple[str, dict]] = []
    machine_skills: dict[str, set[str]] = {}
    for mdir in machines:
        sd = mdir / "skills"
        names = set()
        if sd.is_dir():
            for e in sd.iterdir():
                if e.name.startswith("."):
                    continue
                names.add(e.name)
        machine_skills[mdir.name] = names
    for mname, names in machine_skills.items():
        for sname in names:
            if sname not in dist_skill_set and sname not in skill_new:
                skill_new.append(sname)
    # 冲突：多机都有同一技能且内容签名不同
    all_names = sorted(set().union(*machine_skills.values())) if machine_skills else []
    for sname in all_names:
        owners = [m for m, names in machine_skills.items() if sname in names]
        if len(owners) < 2:
            continue
        sigs = {}
        for m in owners:
            sigs[m] = C.tree_sig(root / "inbox" / m / "skills" / sname)
        if len({str(sorted(sig.items())) for sig in sigs.values()}) > 1:
            skill_conflict.append((sname, sigs))

    # ---- 项目记忆提炼候选 ----
    proj_cands: list[tuple[str, str, str]] = []  # (machine, project, file)
    for mdir in machines:
        pp = mdir / "memory-projects"
        if not pp.is_dir():
            continue
        for pdir in sorted(pp.iterdir()):
            if not pdir.is_dir():
                continue
            for f in sorted(pdir.glob("*.md")):
                proj_cands.append((mdir.name, pdir.name, f.name))

    # ---- 缺席检测：超过 8 天未推送的机器（快照可能过期）----
    absent: list[tuple[str, str]] = []
    for mdir in machines:
        meta = C.read_meta(mdir.name)
        lp = C.parse_ts(meta.get("last_push"))
        if not lp:
            absent.append((mdir.name, "从未推送"))
        elif (datetime.datetime.now(datetime.timezone.utc) - lp).days > 8:
            absent.append((mdir.name, lp.isoformat()))

    # ---- 生成 review.md ----
    lines: list[str] = []
    lines.append(f"# Reasonix 同步待审清单（{week}）\n")
    lines.append(f"- 生成时间：{C.now_iso()}")
    lines.append(f"- 参与机器：{', '.join(machine_names)}")
    lines.append("- ⚠️ = 疑似机器特定内容（盘符路径/IP/凭据/端口/机器名），发布前必须净化")
    lines.append("- 审查方法：运行 reasonix-sync-review 技能，输出整理稿到本目录 draft/ 后执行 sync-publish.py\n")
    if absent:
        lines.append("### ⚠️ 未推送机器（快照可能过期）\n")
        for mname, last in absent:
            lines.append(f"- `{mname}`：last_push = {last}")
        lines.append("- 处理：在该机器上手动执行 `python sync-push.py` 补推后重新 organize（`python sync-organize.py`）\n")

    lines.append(f"## 一、全局记忆候选\n")
    lines.append(f"### 1. 新增（{len(new_facts)} 条）\n")
    for name, srcs in new_facts:
        src = srcs[max(srcs, key=lambda m: C.fact_ts(srcs[m]))]
        fm, text = read_fact(src)
        hits = C.mark_machine_specific(text, machine_names)
        lines.append(f"#### {name}（来自 {', '.join(sorted(srcs))}）")
        lines.append(f"- updated_at: {fm.get('updated_at') or C.fact_ts(src).isoformat()}")
        if hits:
            for ln, label, content in hits[:8]:
                lines.append(f"- ⚠️ 机器特定: 行{ln} [{label}] `{content}`")
        lines.append("```markdown")
        lines.append(text.rstrip()[:4000])
        lines.append("```\n")

    lines.append(f"### 2. 修改（{len(mod_facts)} 条）\n")
    for name, srcs, dist_p in mod_facts:
        src = srcs[max(srcs, key=lambda m: C.fact_ts(srcs[m]))]
        fm, text = read_fact(src)
        dist_fm, dist_text = read_fact(dist_p)
        hits = C.mark_machine_specific(text, machine_names)
        lines.append(f"#### {name}（来自 {', '.join(sorted(srcs))}；dist 现有 updated_at={dist_fm.get('updated_at')}）")
        if hits:
            for ln, label, content in hits[:8]:
                lines.append(f"- ⚠️ 机器特定: 行{ln} [{label}] `{content}`")
        lines.append("```markdown")
        lines.append(text.rstrip()[:4000])
        lines.append("```\n")

    lines.append(f"### 3. 删除候选（{len(del_facts)} 条，dist 有但已无任何机器在使用）\n")
    for name in del_facts:
        lines.append(f"- `{name}`\n")

    if multi_facts:
        lines.append(f"### 4. 多机同名（{len(multi_facts)} 条，注意合并）\n")
        lines.append(", ".join(f"`{n}`" for n in multi_facts) + "\n")

    lines.append(f"## 二、技能\n")
    lines.append(f"### 1. 新增（{len(skill_new)}）\n")
    for s in skill_new:
        lines.append(f"- `{s}`\n")
    lines.append(f"### 2. 冲突（{len(skill_conflict)}，多机内容不一致）\n")
    for sname, sigs in skill_conflict:
        lines.append(f"- `{sname}`：{', '.join(f'{m}({len(sig)}文件)' for m, sig in sigs.items())}\n")

    lines.append(f"## 三、项目记忆提炼候选（{len(proj_cands)} 个文件，从中提炼可迁移经验）\n")
    for m, proj, f in proj_cands[:50]:
        lines.append(f"- `{m}` / `{proj}` / `{f}`")
    if len(proj_cands) > 50:
        lines.append(f"- …共 {len(proj_cands)} 个\n")
    else:
        lines.append("")

    lines.append("## 四、发布说明\n")
    lines.append("1. 用 reasonix-sync-review 技能逐条审查：净化机器特定内容、提炼经验、去重")
    lines.append("2. 整理稿写入本目录 draft/（每文件一条 fact）+ draft/deleted.txt（删除清单）")
    lines.append("3. 确认后执行：`python sync-publish.py --week {week}`\n")

    review_path = review_dir / "review.md"
    C.atomic_write(review_path, "\n".join(lines))
    print(f"== 待审清单已生成: {review_path}")
    print(f"  新增 {len(new_facts)} / 修改 {len(mod_facts)} / 删除候选 {len(del_facts)} / 技能新增 {len(skill_new)} / 技能冲突 {len(skill_conflict)} / 项目提炼候选 {len(proj_cands)}")
    C.log("organize", f"week={week} new={len(new_facts)} mod={len(mod_facts)} del={len(del_facts)} skill_new={len(skill_new)} skill_conflict={len(skill_conflict)} proj={len(proj_cands)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
