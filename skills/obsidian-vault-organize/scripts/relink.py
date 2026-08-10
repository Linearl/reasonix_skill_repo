#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重写 Obsidian vault 中指向已移动/重命名文件（或文件夹）的引用。

用法:
  python relink.py <vault> <old> <new> [--dry-run] [--case-insensitive]

<old>/<new>: vault 相对路径，带不带 .md 均可；new 可以是已存在的目录
（自动拼接原文件名）。old 为目录时整棵子树的前缀引用都会被重写。

覆盖: wikilink / 别名 / 锚点 / 嵌入 / markdown 链接（相对与 / 绝对）/
canvas 的 "file" 与 "link" 字段。只改指向 old 的引用，其他内容不动。

--dry-run  仅预览，不落盘（SKILL 流程要求先预览再执行）
退出码: 0 = 完成; 2 = 无匹配或用法错误
"""
import argparse
import os
import re
import sys
from pathlib import Path
from urllib.parse import quote, unquote

# Windows 控制台/管道下强制 UTF-8，避免 GBK 乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

WIKILINK_RE = re.compile(r"(!?\[\[)([^\[\]]+)(\]\])")
MDLINK_RE = re.compile(r"(\[[^\]]*\]\()([^)]+)(\))")
CANVAS_FILE_RE = re.compile(r'("file"\s*:\s*")([^"]+)(")')
CANVAS_LINK_RE = re.compile(r'("link"\s*:\s*")([^"]+)(")')
SKIP_DIRS = {".obsidian", ".git", ".trash", "node_modules"}
TEXT_EXTS = {".md", ".canvas"}


def norm(s):
    """统一路径形式: 去首尾斜杠、去 .md 扩展名。"""
    s = s.strip().strip("/")
    if s.lower().endswith(".md"):
        s = s[:-3]
    return s


class Rewriter:
    def __init__(self, old_norm, new_norm, case_insensitive):
        self.old = old_norm.lower() if case_insensitive else old_norm
        self.new = new_norm
        self.ci = case_insensitive

    def _norm_for_match(self, t):
        return t.lower() if self.ci else t

    def match(self, t):
        """t 已 norm（去 .md）。精确匹配或子树前缀匹配，返回替换后路径或 None。"""
        tt = self._norm_for_match(t)
        if tt == self.old:
            return self.new
        prefix = self.old + "/"
        if tt.startswith(prefix):
            return self.new + t[len(self.old):]
        return None

    def render_mdlink(self, new_rel, original_target):
        """按原链接风格渲染新目标（相对/绝对、.md 扩展名、%20 编码）。"""
        ext = ".md" if original_target.lower().endswith(".md") else ""
        if original_target.startswith("/"):
            out = "/" + new_rel + ext
        else:
            out = os.path.relpath(new_rel + ext, self._cur_dir or "."
                                  ).replace("\\", "/")
        if "%" in original_target:
            out = quote(out, safe="/")
        else:
            out = out.replace(" ", "%20")
        return out


def rewrite_wikilink_line(line, rw, counter):
    def repl(m):
        head, raw, tail = m.group(1), m.group(2), m.group(3)
        path_part = raw
        suffix = ""
        if "|" in path_part:
            path_part, _, sfx = path_part.partition("|")
            suffix = "|" + sfx
        if "#" in path_part:
            path_part, _, sfx = path_part.partition("#")
            suffix = "#" + sfx + suffix
        t = norm(path_part)
        new_t = rw.match(t)
        if new_t is None:
            return m.group(0)
        counter[0] += 1
        return head + new_t + suffix + tail
    return WIKILINK_RE.sub(repl, line)


def rewrite_mdlink_line(line, rw, cur_dir, counter, force_rel_render=False,
                        parse_dir=None, render_dir=None):
    # 子树内文件：用旧位置解析链接文本，用新位置重新渲染
    rw._cur_dir = render_dir or cur_dir

    def repl(m):
        head, raw, tail = m.group(1), m.group(2), m.group(3)
        t = unquote(raw.strip()).strip()
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:", t):
            return m.group(0)
        is_abs = t.startswith("/")
        if is_abs:
            vault_rel = norm(t.lstrip("/"))
        else:
            base = parse_dir or cur_dir
            vault_rel = norm(os.path.normpath(
                os.path.join(base, t)).replace("\\", "/"))
        new_t = rw.match(vault_rel)
        if new_t is None:
            # 位于被移动子树内：相对链接一律重算（文件位置已变）
            if not (force_rel_render and not is_abs):
                return m.group(0)
            target = vault_rel
        else:
            target = new_t
        counter[0] += 1
        return head + rw.render_mdlink(target, raw.strip()) + tail
    return MDLINK_RE.sub(repl, line)


def rewrite_canvas(text, rw, counter):
    def repl_file(m):
        head, raw, tail = m.group(1), m.group(2), m.group(3)
        t = norm(raw)
        new_t = rw.match(t)
        if new_t is None:
            return m.group(0)
        if raw.lower().endswith(".md") and not new_t.lower().endswith(".md"):
            new_t += ".md"
        counter[0] += 1
        return head + new_t + tail
    text = CANVAS_FILE_RE.sub(repl_file, text)

    def repl_link(m):
        head, raw, tail = m.group(1), m.group(2), m.group(3)
        if raw.startswith("[[") and raw.endswith("]]"):
            inner = raw[2:-2]
            path_part = inner
            suffix = ""
            if "|" in path_part:
                path_part, _, sfx = path_part.partition("|")
                suffix = "|" + sfx
            if "#" in path_part:
                path_part, _, sfx = path_part.partition("#")
                suffix = "#" + sfx + suffix
            new_t = rw.match(norm(path_part))
            if new_t is None:
                return m.group(0)
            counter[0] += 1
            return head + "[[" + new_t + suffix + "]]" + tail
        return m.group(0)
    return CANVAS_LINK_RE.sub(repl_link, text)


def process_file(path, rel, rw, dry_run, in_subtree=False):
    text = path.read_text(encoding="utf-8", errors="replace")
    ext = os.path.splitext(rel)[1].lower()
    cur_dir = os.path.dirname(rel)
    counter = [0]
    new_text = text
    if ext == ".canvas":
        new_text = rewrite_canvas(new_text, rw, counter)
    else:
        lines = new_text.splitlines(keepends=True)
        in_code = False
        out = []
        for line in lines:
            if line.strip().startswith("```"):
                in_code = not in_code
            if not in_code:
                line = rewrite_wikilink_line(line, rw, counter)
                line = rewrite_mdlink_line(line, rw, cur_dir, counter,
                                           force_rel_render=in_subtree,
                                           parse_dir=rw.old if in_subtree else None,
                                           render_dir=rw.new if in_subtree else None)
            out.append(line)
        new_text = "".join(out)
    if counter[0] > 0:
        if not dry_run:
            path.write_text(new_text, encoding="utf-8")
        return rel, counter[0]
    return None


def main():
    ap = argparse.ArgumentParser(description="重写 vault 中指向移动目标的引用")
    ap.add_argument("vault", help="vault 根目录（含 .obsidian/）")
    ap.add_argument("old", help="旧路径（vault 相对，可带 .md；目录则整棵子树）")
    ap.add_argument("new", help="新路径（vault 相对；若为已存在目录则自动拼接原文件名）")
    ap.add_argument("--dry-run", action="store_true", help="仅预览不落盘")
    ap.add_argument("--case-insensitive", action="store_true",
                    help="匹配时忽略大小写（Windows 文件系统场景）")
    args = ap.parse_args()

    root = Path(args.vault)
    if not root.is_dir():
        print(f"错误: vault 不存在: {root}", file=sys.stderr)
        sys.exit(2)

    old_path = root / args.old
    old_base = os.path.basename(args.old.strip("/"))
    new_is_dir = args.new.endswith("/") or (
        (root / args.new).is_dir() and "." in old_base)
    new_norm = norm(args.new if not new_is_dir else norm(args.new) + "/" + old_base)
    new_norm = norm(new_norm)

    old_norm = norm(args.old)
    if old_norm == new_norm:
        print("old 与 new 相同，无需处理", file=sys.stderr)
        sys.exit(2)

    rw = Rewriter(old_norm, new_norm, args.case_insensitive)

    # 收集文本文件
    files = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if any(part in SKIP_DIRS for part in rel.split("/")):
            continue
        if os.path.splitext(rel)[1].lower() not in TEXT_EXTS:
            continue
        files.append((p, rel))

    # 探测文件夹移动：new 位置存在子文件（目录移动），或 vault 中仍有 old 前缀引用
    subtree = None
    if any(rel.startswith(new_norm + "/") for _, rel in files):
        subtree = old_norm
    else:
        old_prefix = old_norm + "/"
        for p, rel in files:
            text = p.read_text(encoding="utf-8", errors="replace")
            cur_dir = os.path.dirname(rel)
            found = False
            for m in WIKILINK_RE.finditer(text):
                raw = m.group(2)
                path_part = raw.split("|", 1)[0].split("#", 1)[0]
                if norm(path_part).startswith(old_prefix):
                    found = True
                    break
            if not found:
                for m in MDLINK_RE.finditer(text):
                    t = unquote(m.group(2).strip()).strip()
                    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:", t):
                        continue
                    vr = norm(t.lstrip("/")) if t.startswith("/") else norm(
                        os.path.normpath(os.path.join(cur_dir, t)).replace("\\", "/"))
                    if vr.startswith(old_prefix):
                        found = True
                        break
            if found:
                subtree = old_norm
                break

    changed = []
    for p, rel in files:
        in_subtree = bool(subtree) and rel.startswith(new_norm + "/")
        r = process_file(p, rel, rw, args.dry_run, in_subtree)
        if r:
            changed.append((rel, abs(r[1])))

    prefix = "[预览] " if args.dry_run else ""
    if not changed:
        print(f"{prefix}没有找到指向 {args.old} 的引用（检查路径与大小写）")
        sys.exit(0 if args.dry_run else 2)
    total = sum(n for _, n in changed)
    if args.dry_run:
        print(f"[预览] 将修改 {len(changed)} 个文件，共 {total} 处引用:")
    else:
        print(f"已重写 {len(changed)} 个文件，共 {total} 处引用:")
    for rel, n in changed:
        print(f"  {rel}: {n} 处")
    sys.exit(0)


if __name__ == "__main__":
    main()
