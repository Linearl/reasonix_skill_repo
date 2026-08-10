# -*- coding: utf-8 -*-
"""
reasonix-sync 公共模块
OneDrive 多机同步：用户级技能 + 全局记忆（经验教训）。
约定：所有文件读写一律 UTF-8；删除一律走 .removed / archive 回收语义。
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import shutil
import socket
import sys
from pathlib import Path

APP_DIR_NAME = "ReasonixSync"


def _setup_stdout_utf8():
    """管道/控制台统一 UTF-8 输出，避免 GBK 乱码"""
    for s in (sys.stdout, sys.stderr):
        try:
            if s and hasattr(s, "reconfigure"):
                s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


_setup_stdout_utf8()


# ---------------------------------------------------------------- 路径定位

def reasonix_home() -> str:
    """reasonix 主目录：REASONIX_HOME 环境变量优先，否则 %APPDATA%\\reasonix"""
    env = os.environ.get("REASONIX_HOME")
    if env:
        return env
    return os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "reasonix")


def find_onedrive() -> str:
    """探测 OneDrive 根目录：先 %USERPROFILE%\\OneDrive，再注册表，再 OneDrive* 通配"""
    home = os.path.expanduser("~")
    cand = os.path.join(home, "OneDrive")
    if os.path.isdir(cand):
        return cand
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\OneDrive\Accounts") as ak:
            i = 0
            while True:
                try:
                    sub = winreg.EnumKey(ak, i)
                    i += 1
                except OSError:
                    break
                try:
                    with winreg.OpenKey(ak, sub) as sk:
                        v, _ = winreg.QueryValueEx(sk, "UserFolder")
                        if v and os.path.isdir(v):
                            return v
                except OSError:
                    pass
    except Exception:
        pass
    for d in sorted(os.listdir(home)):
        if d.startswith("OneDrive") and os.path.isdir(os.path.join(home, d)):
            return os.path.join(home, d)
    return cand  # 最后回退（不存在也返回，由调用方报错）


def sync_root() -> Path:
    return Path(find_onedrive()) / APP_DIR_NAME


def machine_name(cfg: dict) -> str:
    """机器标识：config.machine 优先，否则取真实计算机名（各机自动不同，无需手动配置）"""
    m = str(cfg.get("machine") or "").strip()
    if m:
        return m
    return os.environ.get("COMPUTERNAME") or socket.gethostname()


def load_config() -> dict:
    p = sync_root() / "scripts" / "config.json"
    if not p.exists():
        return {"machine": "", "memory_projects_window_days": 30}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"machine": "", "memory_projects_window_days": 30}


def iso_week(now: datetime.datetime | None = None) -> str:
    """ISO 周目录名，如 2026-W33"""
    d = now or datetime.datetime.now()
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


# ---------------------------------------------------------------- 排除清单

# reasonix home 下永不推送/复制的文件（凭据、桌面状态、各机配置）
EXACT_EXCLUDED = {
    ".env", ".env.bak", "credentials", "nas-credentials.env", "config.toml",
    "install-id", "nas-serve-hash.tmp", "nas-serve-token.txt", "nas-web-password.txt",
    "mcp-global-migration-v1", "desktop-projects-legacy-recovered",
}
PREFIX_EXCLUDED = ("config.toml.", "heartbeat-tasks.json.", "desktop-", ".env.", "nas-")
DIR_EXCLUDED = {
    "sessions", "state", "stats", "cache", "crash-fatal", "repair", "remote",
    "mcp-state", "archive", "global-workspace", "projects", "global",
    ".revisions", ".archive", "__pycache__", ".git", ".removed", "sync-backup",
}


def is_excluded(name: str) -> bool:
    """精确名或前缀命中 → 排除"""
    if name in EXACT_EXCLUDED:
        return True
    return name.startswith(PREFIX_EXCLUDED)


def is_excluded_dir(name: str) -> bool:
    return name in DIR_EXCLUDED or name.startswith(".")


# ---------------------------------------------------------------- frontmatter / 时间

def parse_frontmatter(text: str) -> dict:
    """解析 YAML frontmatter（支持顶层标量 + metadata 下两层嵌套），失败返回 {}"""
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    fm: dict = {}
    cur: str | None = None
    for line in m.group(1).splitlines():
        mm = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*?)\s*$", line)
        if mm:
            cur = mm.group(1)
            fm[cur] = mm.group(2).strip().strip('"')
        elif cur and re.match(r"^\s{2,}[A-Za-z_][A-Za-z0-9_]*:", line):
            kk, _, vv = line.strip().partition(":")
            if not isinstance(fm[cur], dict):
                fm[cur] = {}
            fm[cur][kk] = vv.strip().strip('"')
    return fm


def parse_ts(s) -> datetime.datetime | None:
    if not s:
        return None
    s = str(s).strip().strip('"')
    if not s:
        return None
    try:
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def now_iso() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


# ---------------------------------------------------------------- 文件操作

def file_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_write(path: Path, content: str):
    """原子写：先写 .tmp 再 os.replace，避免读半边文件"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def copy_file(src: Path, dst: Path) -> bool:
    """复制单个文件；内容相同跳过。返回是否实际复制。"""
    if dst.exists() and dst.stat().st_size == src.stat().st_size and file_sha256(dst) == file_sha256(src):
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def copy_tree(src: Path, dst: Path) -> int:
    """复制目录树（跳过 __pycache__/.git/隐藏等），返回复制文件数"""
    n = 0
    if not src.is_dir():
        return 0
    for s in src.rglob("*"):
        if s.is_dir():
            continue
        rel = s.relative_to(src)
        if any(is_excluded_dir(p) for p in rel.parts[:-1]):
            continue
        if is_excluded(rel.name) or is_excluded_dir(rel.name):
            continue
        if copy_file(s, dst / rel):
            n += 1
    return n


def clean_mirror(mirror: Path, keep: set[str], pattern: str) -> int:
    """镜像清理：把 mirror 中不在 keep 清单的文件移到 .removed/<ts>/（回收语义，不直接删）"""
    moved = 0
    if not mirror.is_dir():
        return 0
    removed = mirror / ".removed" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    for f in mirror.glob(pattern):
        if f.name in keep or f.name.startswith("."):
            continue
        removed.mkdir(parents=True, exist_ok=True)
        shutil.move(str(f), str(removed / f.name))
        moved += 1
    return moved


def clean_mirror_top(mirror: Path, keep: set[str]) -> int:
    """镜像清理（顶层条目版）：把 mirror 中不在 keep 清单的目录/文件移到 .removed/<ts>/"""
    moved = 0
    if not mirror.is_dir():
        return 0
    removed = mirror / ".removed" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    for entry in mirror.iterdir():
        if entry.name in keep or entry.name.startswith("."):
            continue
        removed.mkdir(parents=True, exist_ok=True)
        shutil.move(str(entry), str(removed / entry.name))
        moved += 1
    return moved


# ---------------------------------------------------------------- 日志 / meta / 备份

def log_dir() -> Path:
    d = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))) / "reasonix-sync" / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def log(task: str, msg: str):
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    with open(log_dir() / f"{task}.log", "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


def backup_dir() -> Path:
    """本机备份目录：<reasonix home>\\sync-backup\\<ts>（pull 覆盖前备份）"""
    p = Path(reasonix_home()) / "sync-backup" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    p.mkdir(parents=True, exist_ok=True)
    return p


def meta_path(machine: str) -> Path:
    return sync_root() / "meta" / f"{machine}.json"


def read_meta(machine: str) -> dict:
    p = meta_path(machine)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_meta(machine: str, data: dict):
    atomic_write(meta_path(machine), json.dumps(data, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------- 机器特定内容标记

MACHINE_PATTERNS = [
    (r"[A-Za-z]:[\\/]", "盘符路径"),
    (r"\b\d{1,3}(\.\d{1,3}){3}\b", "IP 地址"),
    (r"(密码|口令|passwd|password|secret|token|凭据|credential|api[_-]?key)", "凭据类"),
    # 端口号：4 位（排除 19xx/20xx 年份）或 5 位 1xxxx-5xxxx
    (r"\b(?!(?:19|20)\d{2}\b)[1-9]\d{3}\b|\b[1-5]\d{4}\b", "端口号"),
]


def mark_machine_specific(text: str, extra_words: list[str] | None = None) -> list[tuple[int, str, str]]:
    """返回 [(1基行号, 模式名, 行内容前120字符)]，供待审清单标红"""
    hits: list[tuple[int, str, str]] = []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        for pat, label in MACHINE_PATTERNS:
            if re.search(pat, line, re.IGNORECASE):
                hits.append((i, label, line.strip()[:120]))
        if extra_words:
            for w in extra_words:
                if w and w in line:
                    hits.append((i, f"机器名[{w}]", line.strip()[:120]))
    return hits


def fact_ts(p: Path, fm: dict | None = None) -> datetime.datetime:
    """fact 时间：frontmatter updated_at 优先，否则文件 mtime"""
    fm = fm if fm is not None else parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
    ts = parse_ts(fm.get("updated_at"))
    if ts is None:
        ts = datetime.datetime.fromtimestamp(p.stat().st_mtime, tz=datetime.timezone.utc)
    return ts


def tree_sig(p: Path) -> dict:
    """目录/文件内容签名：相对路径 -> sha256"""
    sig: dict = {}
    if p.is_dir():
        for f in sorted(p.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(p)
            if any(part.startswith(".") or part == "__pycache__" for part in rel.parts):
                continue
            sig[rel.as_posix()] = file_sha256(f)
    else:
        sig[p.name] = file_sha256(p)
    return sig
