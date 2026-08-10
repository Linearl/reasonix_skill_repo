#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查 Obsidian vault 中的断链（broken links）。

用法:
  python check_links.py <vault> [--strict] [--exclude <前缀>] [--json]

扫描 .md 与 .canvas 文件，提取 wikilink / 嵌入 / markdown 链接，
对照 vault 实际文件解析目标，报告断链（文件:行:链接 + 原因）。

--strict   只按 vault 相对路径匹配（不按 basename 消歧），更严格
--exclude  跳过路径前缀（可重复），如 --exclude .obsidian
退出码: 0 = 无断链; 1 = 存在断链; 2 = 用法/运行错误
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote

# Windows 控制台/管道下强制 UTF-8，避免 GBK 乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

WIKILINK_RE = re.compile(r"!?\[\[([^\[\]]+)\]\]")
MDLINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
CANVAS_FILE_RE = re.compile(r'"file"\s*:\s*"([^"]+)"')
CANVAS_LINK_RE = re.compile(r'"link"\s*:\s*"([^"]+)"')
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")
SKIP_DIRS = {".obsidian", ".git", ".trash", "node_modules"}
TEXT_EXTS = {".md", ".canvas"}


def iter_files(root: Path):
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if any(part in SKIP_DIRS for part in rel.split("/")):
            continue
        yield p, rel


def build_index(root: Path, exclude_prefixes):
    """返回 (去扩展名全路径集, basename去扩展名集, basename全集, 全路径集)。"""
    stems, base_stems, base_full, all_paths = set(), set(), set(), set()
    for p, rel in iter_files(root):
        if any(rel.startswith(x) for x in exclude_prefixes):
            continue
        all_paths.add(rel)
        stem = os.path.splitext(rel)[0]
        stems.add(stem)
        base_stems.add(os.path.basename(stem))
        base_full.add(os.path.basename(rel))
    return stems, base_stems, base_full, all_paths


def norm_wikilink(raw: str):
    """解析 wikilink 目标 -> (路径部分, 是否纯锚点)。"""
    t = raw.strip()
    if t.startswith("#"):  # 本文件内锚点/块引用
        return None, True
    if "|" in t:
        t = t.split("|", 1)[0]
    t = t.split("#", 1)[0]
    t = unquote(t).strip()
    if t.lower().endswith(".md"):
        t = t[:-3]
    return t, False


def resolve_mdlink(target: str, current_dir: str):
    """markdown 链接 -> vault 相对 stem；外部/无法解析返回 None。"""
    t = unquote(target.strip()).strip()
    if SCHEME_RE.match(t):  # http:, mailto:, obsidian: 等
        return None
    if t.startswith("#"):  # 本文件内锚点 [text](#heading)
        return None
    if t.startswith("/"):
        rel = t.lstrip("/")
    else:
        rel = os.path.normpath(os.path.join(current_dir, t)).replace("\\", "/")
    if rel.lower().endswith(".md"):
        rel = rel[:-3]
    return rel


def check_text(rel, text, stems, base_stems, base_full, all_paths, strict, issues, is_canvas=False):
    lines = text.splitlines()
    in_code = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        for m in WIKILINK_RE.finditer(line):
            target, pure_anchor = norm_wikilink(m.group(1))
            if pure_anchor or not target:
                continue
            if is_valid(target, stems, base_stems, base_full, all_paths, strict):
                continue
            issues.append({"file": rel, "line": i, "kind": "wikilink",
                           "target": m.group(1), "reason": f"未找到: {target}"})
        for m in MDLINK_RE.finditer(line):
            raw = m.group(1)
            resolved = resolve_mdlink(raw, os.path.dirname(rel))
            if resolved is None:
                continue
            if is_valid(resolved, stems, base_stems, base_full, all_paths, strict):
                continue
            issues.append({"file": rel, "line": i, "kind": "markdown",
                           "target": raw, "reason": f"未找到: {resolved}"})


def is_valid(target, stems, base_stems, base_full, all_paths, strict):
    """Obsidian 解析规则近似：路径优先；shortest path 模式按 basename。"""
    if target in stems or target in all_paths:
        return True
    if "/" not in target and not strict:
        base = os.path.basename(target)
        if base in base_stems or target in base_full:
            return True
    return False


def check_canvas(rel, text, stems, base_stems, base_full, all_paths, strict, issues):
    for m in CANVAS_FILE_RE.finditer(text):
        raw = m.group(1)
        stem = raw[:-3] if raw.lower().endswith(".md") else raw
        if not is_valid(stem, stems, base_stems, base_full, all_paths, strict):
            issues.append({"file": rel, "line": 0, "kind": "canvas-file",
                           "target": raw, "reason": f"未找到: {stem}"})
    for m in CANVAS_LINK_RE.finditer(text):
        raw = m.group(1)
        if raw.startswith("[[") and raw.endswith("]]"):
            target, pure_anchor = norm_wikilink(raw[2:-2])
            if not pure_anchor and target and not is_valid(
                    target, stems, base_stems, base_full, all_paths, strict):
                issues.append({"file": rel, "line": 0, "kind": "canvas-link",
                               "target": raw, "reason": f"未找到: {target}"})
        else:
            resolved = resolve_mdlink(raw, os.path.dirname(rel))
            if resolved and not is_valid(resolved, stems, base_stems, base_full,
                                         all_paths, strict):
                issues.append({"file": rel, "line": 0, "kind": "canvas-link",
                               "target": raw, "reason": f"未找到: {resolved}"})


def main():
    ap = argparse.ArgumentParser(description="检查 Obsidian vault 断链")
    ap.add_argument("vault", help="vault 根目录（含 .obsidian/）")
    ap.add_argument("--strict", action="store_true",
                    help="仅按 vault 相对路径匹配，不做 basename 消歧")
    ap.add_argument("--exclude", action="append", default=[],
                    help="跳过路径前缀（可重复）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    root = Path(args.vault)
    if not (root / ".obsidian").is_dir():
        print(f"警告: {root} 下未找到 .obsidian/，可能不是 vault 根（继续扫描）",
              file=sys.stderr)
    stems, base_stems, base_full, all_paths = build_index(root, args.exclude)
    issues = []
    scanned = 0
    for p, rel in iter_files(root):
        if any(rel.startswith(x) for x in args.exclude):
            continue
        ext = os.path.splitext(rel)[1].lower()
        if ext not in TEXT_EXTS:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        scanned += 1
        if ext == ".canvas":
            check_canvas(rel, text, stems, base_stems, base_full, all_paths,
                         args.strict, issues)
        else:
            check_text(rel, text, stems, base_stems, base_full, all_paths,
                       args.strict, issues)

    if args.json:
        print(json.dumps({"scanned": scanned, "broken": len(issues),
                          "issues": issues}, ensure_ascii=False, indent=2))
    else:
        print(f"扫描 {scanned} 个文件，断链 {len(issues)} 处")
        for it in issues:
            loc = f"{it['file']}:{it['line']}" if it["line"] else it["file"]
            print(f"  [{it['kind']}] {loc}  {it['target']}  ->  {it['reason']}")
        if not issues:
            print("✅ 无断链")
    sys.exit(1 if issues else 0)


if __name__ == "__main__":
    main()
