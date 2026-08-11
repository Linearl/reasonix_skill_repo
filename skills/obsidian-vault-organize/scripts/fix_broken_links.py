#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 Obsidian vault 中"文件被移动/重命名后断掉的附件引用"。

用法:
  python fix_broken_links.py <vault> [--dirs 优先目录,逗号分隔] [--dry-run]
                              [--exts .pdf,.png] [--exclude 前缀] [--json]

对每个断链引用（wikilink 或 markdown 链接，解析后目标不存在），按文件名
(basename) 在全库查找同名文件：
  - 找到唯一文件 → 改写为嵌入 ![[<路径/名>]]（同名有歧义时用完整相对路径）
  - 在 --dirs 指定目录中找到 → 优先使用
  - 找不到 → 记入缺失清单（不改动）
真缺失的引用保持原样，避免误改。只扫描 .md 与 .canvas（跳过代码块）。

退出码: 0 = 全部修复; 1 = 有缺失/歧义未处理; 2 = 用法错误
"""
import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

WIKILINK_RE = re.compile(r"(!?\[\[)([^\[\]]+)(\]\])")
MDLINK_RE = re.compile(r"(!?\[)([^\]]*)(\]\()([^)]+)(\))")
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")
EXT_RE = re.compile(r"\.[A-Za-z0-9\-]{1,20}$")  # 合法附件扩展名（含连字符，防中文误判）
SKIP_DIRS = {".obsidian", ".claudian", ".trash", ".git"}
TEXT_EXTS = {".md", ".canvas"}


def iter_files(root: Path, exclude_prefixes):
    for p in sorted(Path(root).rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(Path(root)).as_posix()
        if any(part in SKIP_DIRS for part in rel.split("/")):
            continue
        if any(rel.startswith(x) for x in exclude_prefixes):
            continue
        yield p, rel


def build_index(root, exclude_prefixes):
    """返回 (basename -> [vault 相对路径...], 完整路径集合)。"""
    index = {}
    paths = set()
    for p, rel in iter_files(root, exclude_prefixes):
        index.setdefault(os.path.basename(rel), []).append(rel)
        paths.add(rel)
    return index, paths


def wiki_exists(base, index, paths):
    """wikilink 存在性：完整路径（![[dir/file]]）或 basename（shortest path）。"""
    if "/" in base and (base in paths or base + ".md" in paths):
        return True
    return base in index or base + ".md" in index


def md_exists(vr, paths):
    """markdown 链接存在性：精确路径（相对解析结果）。"""
    return vr in paths or vr + ".md" in paths


def resolve_wikilink(raw):
    """wikilink 目标 -> (basename, 是否纯锚点)。"""
    t = raw.strip()
    if t.startswith("#"):
        return None, True
    if "|" in t:
        t = t.split("|", 1)[0]
    t = t.split("#", 1)[0]
    return unquote(t).strip(), False


def resolve_mdlink(target, cur_dir):
    """markdown 链接 -> vault 相对路径或 None（外部/锚点）。"""
    t = unquote(target.strip()).strip()
    if SCHEME_RE.match(t) or t.startswith("#"):
        return None
    if t.startswith("/"):
        return t.lstrip("/")
    return os.path.normpath(os.path.join(cur_dir, t)).replace("\\", "/")


def target_exists(vault_rel, index):
    """按 basename 判断目标是否存在于 vault（shortest path 近似）。"""
    if not vault_rel:
        return True
    base = os.path.basename(vault_rel)
    return base in index

def choose_target(base, index, prio_dirs):
    """选择修复目标路径；优先目录 > 唯一文件 > 最短路；返回 (路径, 歧义?)"""
    cands = index.get(base)
    if not cands:
        return None, False
    for d in prio_dirs:
        for c in cands:
            if c.startswith(d + "/") or c == d:
                return c, False
    if len(cands) == 1:
        return cands[0], False
    # 同名歧义：选路径最短的
    cands = sorted(cands, key=lambda c: (c.count("/"), c))
    return cands[0], True


def render_embed(path):
    """嵌入形式：路径含 / 用完整相对路径，否则 basename。"""
    return "![[%s]]" % path


def process_file(p, rel, index, paths, prio_dirs, exts, dry_run, stats):
    text = p.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines(keepends=True)
    in_code = False
    out = []
    changed = 0
    cur_dir = os.path.dirname(rel)
    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
        if in_code:
            out.append(line)
            continue
        # wikilink
        def wk(m):
            nonlocal changed
            head, raw, tail = m.group(1), m.group(2), m.group(3)
            base, pure = resolve_wikilink(raw)
            if pure or not base:
                return m.group(0)
            me = EXT_RE.search(base)
            ext = me.group(0).lower() if me else ""
            if not ext or ext in (".md", ".canvas"):
                return m.group(0)  # 笔记引用不在此修复
            if exts and ext not in exts:
                return m.group(0)
            if wiki_exists(base, index, paths):
                return m.group(0)  # 未断链
            target, amb = choose_target(base, index, prio_dirs)
            if target is None:
                stats["missing"][base] += 1
                return m.group(0)
            stats["fixed"] += 1
            if amb:
                stats["ambiguous"].append((rel, base, target))
            changed += 1
            return head + render_embed(target) + tail
        line = WIKILINK_RE.sub(wk, line)
        # markdown link
        def md(m):
            nonlocal changed
            vr = resolve_mdlink(m.group(4), cur_dir)
            if vr is None:
                return m.group(0)
            base = os.path.basename(vr)
            me = EXT_RE.search(base)
            ext = me.group(0).lower() if me else ""
            if not ext or ext in (".md", ".canvas"):
                return m.group(0)  # 笔记引用不在此修复
            if exts and ext not in exts:
                return m.group(0)
            if md_exists(vr, paths):
                return m.group(0)  # 未断链
            target, amb = choose_target(base, index, prio_dirs)
            if target is None:
                stats["missing"][base] += 1
                return m.group(0)
            stats["fixed"] += 1
            if amb:
                stats["ambiguous"].append((rel, base, target))
            changed += 1
            # 整体替换为嵌入，保留 alt/文本作别名
            alt = m.group(2)
            embed = "![[%s" % target
            if alt and "|" not in alt and "[" not in alt and "]" not in alt:
                embed += "|" + alt
            return embed + "]]"
        line = MDLINK_RE.sub(md, line)
        out.append(line)
    new_text = "".join(out)
    if changed:
        stats["files"] += 1
        stats["files_list"].append(rel)
        if not dry_run:
            p.write_text(new_text, encoding="utf-8")
    return changed


def main():
    ap = argparse.ArgumentParser(description="按文件名修复断链附件引用")
    ap.add_argument("vault", help="vault 根目录")
    ap.add_argument("--dirs", default="", help="优先查找目录（逗号分隔，vault 相对）")
    ap.add_argument("--dry-run", action="store_true", help="仅预览不落盘")
    ap.add_argument("--exts", default="", help="只处理这些扩展名（逗号分隔，如 .pdf,.png）")
    ap.add_argument("--exclude", action="append", default=[], help="跳过路径前缀（可重复）")
    ap.add_argument("--json", action="store_true", help="输出 JSON 统计")
    args = ap.parse_args()

    root = Path(args.vault)
    if not root.is_dir():
        print("错误: vault 不存在", file=sys.stderr)
        sys.exit(2)
    prio_dirs = [d.strip() for d in args.dirs.split(",") if d.strip()]
    exts = {e.strip().lower() for e in args.exts.split(",") if e.strip()} or None
    exclude = list(args.exclude)

    index, paths = build_index(root, exclude)
    stats = {"files": 0, "fixed": 0, "missing": Counter(), "ambiguous": [],
             "files_list": []}
    for p, rel in iter_files(root, exclude):
        if os.path.splitext(rel)[1].lower() not in TEXT_EXTS:
            continue
        process_file(p, rel, index, paths, prio_dirs, exts, args.dry_run, stats)

    prefix = "[预览] " if args.dry_run else ""
    if args.json:
        print(json.dumps({
            "dry_run": args.dry_run, "files": stats["files"],
            "files_list": stats["files_list"],
            "fixed": stats["fixed"],
            "missing": dict(stats["missing"]),
            "ambiguous": stats["ambiguous"],
        }, ensure_ascii=False, indent=2))
    else:
        print(f"{prefix}修复 {stats['fixed']} 处引用，涉及 {stats['files']} 个文件")
        if stats["missing"]:
            print(f"缺失(未修复) {sum(stats['missing'].values())} 处，去重 {len(stats['missing'])} 个文件名:")
            for name, n in stats["missing"].most_common(20):
                print(f"  {n:4d}  {name}")
            if len(stats["missing"]) > 20:
                print(f"  ... 其余 {len(stats['missing']) - 20} 个")
        if stats["ambiguous"]:
            print(f"歧义 {len(stats['ambiguous'])} 处（同名多文件，已选最短路径）:")
            for rel, base, target in stats["ambiguous"][:10]:
                print(f"  {rel}: {base} -> {target}")
    if stats["missing"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
