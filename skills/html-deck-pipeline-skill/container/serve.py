"""启动 HTML Deck 本地服务。

直接从 container/ 目录提供服务，slides-config.json 和 slides/ 路由到目标目录，无需复制骨架文件。
主题和字号配置从 css/config.yaml 读取。
支持多个目标目录，通过页面下拉框切换。

用法:
  python serve.py [target_dir ...] [--theme dark-theme-2] [--port 8080] [--no-browser] [--watch]
"""

import argparse
import json
import os
import re
import threading
import time
import webbrowser
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, HTTPServer
from pathlib import Path

import yaml

CONTAINER = Path(__file__).resolve().parent
CONFIG_PATH = CONTAINER / "css" / "config.yaml"
_CONFIGS_FILE = CONTAINER / ".configs.json"


def load_deck_config() -> dict:
    """读取 css/config.yaml，返回 {themes: [...], fontsizes: [...]}。"""
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def default_theme(config: dict) -> str:
    for t in config.get("themes", []):
        if t.get("default"):
            return t["id"]
    return config["themes"][0]["id"] if config.get("themes") else "dark-theme-2"


def default_fontsize(config: dict) -> str:
    for fs in config.get("fontsizes", []):
        if fs.get("default"):
            return fs["id"]
    return config["fontsizes"][0]["id"] if config.get("fontsizes") else "standard"


def _read_config_title(target: Path) -> str | None:
    """从目录的 slides-config.json 读取 title 字段。"""
    try:
        config = read_slides_config(target)
        return config.get("title") if config else None
    except (json.JSONDecodeError, OSError):
        return None


class DeckHandler(SimpleHTTPRequestHandler):
    """将 /slides-config.json、/slides/*、/style/* 路由到 target_dir；/css/* 路由到对应目录；其余从 container/ 提供。"""

    target_dir: Path | None = None
    theme_dir: Path | None = None
    deck_config: dict | None = None
    theme_names: set = set()
    fontsize_names: set = set()
    watch_mode: bool = False
    _sse_clients: list = []
    _watch_thread: threading.Thread | None = None
    _watch_mtimes: dict = {}
    configs: dict[str, dict] = {}
    active_config_path: str | None = None

    @classmethod
    def _sync_active(cls) -> None:
        """从 active_config_path 推导 target_dir。"""
        if cls.active_config_path and cls.active_config_path in cls.configs:
            cls.target_dir = Path(cls.configs[cls.active_config_path]["path"]).resolve()
        else:
            cls.target_dir = None

    def do_GET(self) -> None:
        path_raw = self.path
        path = path_raw.split("?")[0]

        if path == "/api/configs":
            self._handle_list_configs()
            return

        if path.startswith("/api/configs/activate"):
            self._handle_activate_config(path_raw)
            return

        if path == "/events" and self.watch_mode:
            self._handle_sse()
            return

        if path.startswith("/css/") and self.theme_dir is not None:
            parts = path[len("/css/"):].split("/", 1)

            if parts[0] == "common":
                self._serve_from(CONTAINER / "css" / "common", path, strip_prefix="css/common/")

            elif parts[0] == "theme" and len(parts) > 1:
                theme_parts = parts[1].split("/", 1)
                if theme_parts[0] in self.theme_names:
                    theme_dir = CONTAINER / "css" / "theme" / theme_parts[0]
                    self._serve_from(theme_dir, path, strip_prefix=f"css/theme/{theme_parts[0]}/")
                else:
                    self.send_error(404)

            elif parts[0] == "fontsize" and len(parts) > 1:
                file = parts[1]
                if file.rsplit(".", 1)[0] in self.fontsize_names:
                    self._serve_from(CONTAINER / "css" / "fontsize", path, strip_prefix="css/fontsize/")
                else:
                    self.send_error(404)

            elif parts[0] in self.theme_names:
                # Legacy: /css/<theme>/<file>
                theme_dir = CONTAINER / "css" / "theme" / parts[0]
                self._serve_from(theme_dir, path, strip_prefix=f"css/{parts[0]}/")

            elif path == "/css/config.yaml":
                self._serve_from(CONTAINER / "css", path, strip_prefix="css/")

            else:
                self._serve_from(self.theme_dir, path, strip_prefix="css/")

        elif path == "/slides-config.json" or path.startswith("/slides/") or path.startswith("/style/"):
            if self.target_dir is not None:
                self._serve_from(self.target_dir, path)
            else:
                self.send_error(404)

        else:
            # Inject config into index.html
            if path in ("/", "/index.html"):
                self._serve_index_with_config()
            else:
                self._serve_from(CONTAINER, path)

    def _serve_index_with_config(self) -> None:
        """Serve index.html with injected __CONFIG from config.json."""
        idx_path = CONTAINER / "index.html"
        if not idx_path.is_file():
            self.send_error(404)
            return
        html = idx_path.read_text(encoding="utf-8")

        config_path = CONTAINER / "config.json"
        if config_path.is_file():
            config_json = config_path.read_text(encoding="utf-8").strip()
            config_script = f"\n  <script>window.__CONFIG = {config_json};</script>\n"
            html = html.replace("</head>", config_script + "</head>")

        # Inject SSE hot-reload script when --watch is active
        if self.watch_mode:
            reload_script = (
                '\n  <script>(()=>{'
                'const s=new EventSource("/events");'
                's.onmessage=()=>{s.close();location.reload()};'
                '})();</script>\n'
            )
            html = html.replace("</head>", reload_script + "</head>")

        data = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "public, max-age=3600")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self) -> None:
        """处理 CORS 预检请求。"""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "3600")
        self.end_headers()

    def do_POST(self) -> None:
        """处理 POST 请求。"""
        if self.path == "/log":
            self._handle_log()
        elif self.path == "/save" and self.target_dir is not None:
            self._handle_save()
        elif self.path == "/api/configs":
            self._handle_register_config()
        elif self.path.startswith("/api/configs/activate"):
            self._handle_activate_config(self.path)
        else:
            self.send_error(404)

    def do_DELETE(self) -> None:
        """处理 DELETE 请求。"""
        path_raw = self.path
        path = path_raw.split("?")[0]
        if path == "/api/configs":
            self._handle_unregister_config(path_raw)
        else:
            self.send_error(404)

    def _handle_log(self) -> None:
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len)
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON"})
            return

        logs_dir = CONTAINER / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        new_entries = payload.get("entries", [])
        is_full = payload.get("full", False)
        max_per_file = 2000

        # Determine target file: use most recent session file, or create new
        if is_full:
            # Full save: always create a new file
            filepath = self._new_log_file(logs_dir)
            all_entries = new_entries
        else:
            # Incremental: append to most recent file, rotating if needed
            filepath, existing = self._find_active_log(logs_dir)
            if existing is not None and len(existing) + len(new_entries) <= max_per_file:
                all_entries = existing + new_entries
            elif existing is not None:
                # Would exceed limit — rotate to new file
                filepath = self._new_log_file(logs_dir)
                all_entries = new_entries
            else:
                all_entries = new_entries

        filepath.write_text(
            json.dumps({"url": payload.get("url", ""), "ua": payload.get("ua", ""), "entries": all_entries},
                       ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        levels = {}
        for e in all_entries:
            lv = e.get("level", "debug")
            levels[lv] = levels.get(lv, 0) + 1

        self._send_json(200, {
            "message": f"已保存 {len(new_entries)} 条日志",
            "file": filepath.name,
            "total": len(all_entries),
            "levels": levels
        })
        print(f"  [log] +{len(new_entries)} → {filepath.name} (total {len(all_entries)}, {', '.join(f'{k}:{v}' for k, v in sorted(levels.items()))})")

    # ---- SSE hot-reload ---- #

    def _handle_sse(self) -> None:
        """SSE endpoint for hot-reload notifications."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b"data: connected\n\n")
        self.wfile.flush()
        DeckHandler._sse_clients.append(self)
        try:
            while True:
                time.sleep(30)
                # Keep-alive
                try:
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
                except Exception:
                    break
        except Exception:
            pass
        finally:
            if self in DeckHandler._sse_clients:
                DeckHandler._sse_clients.remove(self)

    @classmethod
    def _broadcast_reload(cls) -> None:
        """Send reload event to all connected SSE clients."""
        dead = []
        for client in cls._sse_clients:
            try:
                client.wfile.write(b"data: reload\n\n")
                client.wfile.flush()
            except Exception:
                dead.append(client)
        for d in dead:
            if d in cls._sse_clients:
                cls._sse_clients.remove(d)

    @classmethod
    def _start_watcher(cls, target_dir: Path, container_dir: Path) -> None:
        """Start a background thread that watches target_dir and container dirs for file changes."""
        watch_dirs = [target_dir, container_dir / "css", container_dir / "js"]
        watch_dirs = [d for d in watch_dirs if d.exists()]

        def collect_mtimes():
            mtimes = {}
            for wd in watch_dirs:
                for f in wd.rglob("*"):
                    if f.is_file() and f.suffix in (".html", ".css", ".js", ".yaml", ".json"):
                        mtimes[str(f)] = f.stat().st_mtime
            return mtimes

        cls._watch_mtimes = collect_mtimes()

        def watcher_loop():
            while True:
                time.sleep(1)
                try:
                    cur = collect_mtimes()
                    if cur != cls._watch_mtimes:
                        cls._watch_mtimes = cur
                        print("  [watch] 检测到文件变化，通知浏览器刷新…")
                        cls._broadcast_reload()
                except Exception as e:
                    print(f"  [watch] 错误: {e}")

        t = threading.Thread(target=watcher_loop, daemon=True)
        t.start()
        cls._watch_thread = t

    @staticmethod
    def _new_log_file(logs_dir: Path) -> Path:
        ts = __import__("datetime").datetime.now().strftime("%Y%m%d-%H%M%S")
        return logs_dir / f"session-{ts}.json"

    @staticmethod
    def _find_active_log(logs_dir: Path) -> tuple:
        """Return (filepath, entries_list) for the most recent log file, or (new_path, None)."""
        existing = sorted(logs_dir.glob("session-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if existing:
            try:
                data = json.loads(existing[0].read_text(encoding="utf-8"))
                entries = data.get("entries", [])
                return (existing[0], entries)
            except (json.JSONDecodeError, KeyError):
                pass
        # No valid existing file
        ts = __import__("datetime").datetime.now().strftime("%Y%m%d-%H%M%S")
        return (logs_dir / f"session-{ts}.json", None)

    def _handle_save(self) -> None:
        """处理 POST /save — 接收编辑器修改并写入文件。"""
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len)
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON"})
            return

        css_rules = payload.get("cssRules", [])
        dom_changes = payload.get("domChanges", {})
        text_changes = payload.get("textChanges", {})
        deletions = payload.get("deletions", {})

        try:
            # 1. Write CSS overrides
            if css_rules:
                self._write_css_overrides(css_rules)

            # 2. Apply text & DOM changes to slide HTML files
            files_updated = set()
            if dom_changes:
                files_updated.update(self._apply_dom_changes(dom_changes))
            if text_changes:
                files_updated.update(self._apply_text_changes(text_changes))
            if deletions:
                files_updated.update(self._apply_deletions(deletions))

            self._send_json(200, {"message": f"已保存 {len(css_rules)} 条 CSS 规则 + {len(files_updated)} 个文件的结构修改"})
        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def _send_json(self, code: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ── Config management ──

    def _handle_list_configs(self) -> None:
        """GET /api/configs — 返回所有已注册配置 + 当前激活项。自动清理无效目录。"""
        valid = []
        to_remove = []
        for p, info in self.configs.items():
            dir_path = Path(info["path"])
            if dir_path.is_dir() and (dir_path / "slides-config.json").is_file():
                valid.append({"path": p, "title": info.get("title", dir_path.name)})
            else:
                to_remove.append(p)
        for p in to_remove:
            del self.configs[p]
            if DeckHandler.active_config_path == p:
                DeckHandler.active_config_path = None
                DeckHandler._sync_active()
        self._send_json(200, {"configs": valid, "active": DeckHandler.active_config_path})

    def _handle_register_config(self) -> None:
        """POST /api/configs — 注册新目录。body: {"path": "..."}"""
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len)
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON"})
            return

        raw_path = payload.get("path", "").strip()
        if not raw_path:
            self._send_json(400, {"error": "path is required"})
            return

        target = Path(raw_path).resolve()
        if not target.is_dir():
            self._send_json(400, {"error": f"目录不存在: {target}"})
            return

        config_file = target / "slides-config.json"
        if not config_file.is_file():
            self._send_json(400, {"error": f"目录中未找到 slides-config.json: {target}"})
            return

        path_str = str(target)
        if path_str in self.configs:
            self._send_json(409, {"error": "该目录已注册"})
            return

        title = _read_config_title(target) or target.name
        self.configs[path_str] = {"title": title, "path": path_str}
        DeckHandler.active_config_path = path_str
        DeckHandler._sync_active()
        DeckHandler._persist_configs()

        self._send_json(201, {
            "configs": [{"path": p, "title": i["title"]} for p, i in self.configs.items()],
            "active": DeckHandler.active_config_path
        })
        print(f"  [config] 已注册: {title} ({path_str})")

    def _handle_activate_config(self, raw_path: str) -> None:
        """POST /api/configs/activate?path=... — 设置激活配置。"""
        from urllib.parse import parse_qs
        qs = parse_qs(raw_path.split("?")[1] if "?" in raw_path else "")
        paths = qs.get("path", [])
        if not paths:
            self._send_json(400, {"error": "path query parameter is required"})
            return

        path_str = paths[0]
        if path_str not in self.configs:
            self._send_json(404, {"error": "未注册的目录"})
            return

        DeckHandler.active_config_path = path_str
        DeckHandler._sync_active()
        self._send_json(200, {"active": DeckHandler.active_config_path, "title": self.configs[path_str]["title"]})
        print(f"  [config] 已激活: {self.configs[path_str]['title']} ({path_str})")

    def _handle_unregister_config(self, raw_path: str) -> None:
        """DELETE /api/configs?path=... — 从注册表中移除（不删磁盘文件）。"""
        from urllib.parse import parse_qs
        qs = parse_qs(raw_path.split("?")[1] if "?" in raw_path else "")
        paths = qs.get("path", [])
        if not paths:
            self._send_json(400, {"error": "path query parameter is required"})
            return

        path_str = paths[0]
        if path_str not in self.configs:
            self._send_json(404, {"error": "未注册的目录"})
            return

        title = self.configs[path_str].get("title", "")
        del self.configs[path_str]

        if DeckHandler.active_config_path == path_str:
            DeckHandler.active_config_path = next(iter(self.configs), None)
            DeckHandler._sync_active()

        DeckHandler._persist_configs()

        self._send_json(200, {
            "configs": [{"path": p, "title": i["title"]} for p, i in self.configs.items()],
            "active": DeckHandler.active_config_path
        })
        print(f"  [config] 已移除: {title} ({path_str})")

    @classmethod
    def _persist_configs(cls) -> None:
        """保存已注册配置的路径列表到 .configs.json。"""
        paths = list(cls.configs.keys())
        try:
            _CONFIGS_FILE.write_text(json.dumps(paths, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as e:
            print(f"  [config] 持久化失败: {e}")

    @classmethod
    def _load_configs(cls) -> None:
        """从 .configs.json 加载已注册配置，逐一校验目录是否仍存在。"""
        if not _CONFIGS_FILE.is_file():
            return
        try:
            paths = json.loads(_CONFIGS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return

        for raw in paths:
            target = Path(raw).resolve()
            if not target.is_dir():
                print(f"  [config] 跳过不存在的目录: {target}")
                continue
            if not (target / "slides-config.json").is_file():
                print(f"  [config] 跳过缺少 slides-config.json 的目录: {target}")
                continue
            title = _read_config_title(target) or target.name
            path_str = str(target)
            cls.configs[path_str] = {"title": title, "path": path_str}
            print(f"  [config] 已加载: {title} ({path_str})")

        if cls.configs:
            cls.active_config_path = next(iter(cls.configs))
        DeckHandler._sync_active()

    def _write_css_overrides(self, css_rules: list) -> None:
        """将 CSS 规则写入 style/editor-overrides.css，按 slideKey 前缀分组。"""
        # 按 slideKey 分组
        grouped = {}
        for rule in css_rules:
            slide_key = rule.get("slideKey", "")
            selector = rule.get("selector", "")
            props = rule.get("props", {})
            if not slide_key or not selector or not props:
                continue
            grouped.setdefault(slide_key, []).append((selector, props))

        if not grouped:
            return

        style_dir = self.target_dir / "style"
        style_dir.mkdir(parents=True, exist_ok=True)

        css_path = style_dir / "editor-overrides.css"
        lines = ["/* Editor CSS Overrides — auto-generated */"]
        for slide_key, rules in grouped.items():
            lines.append(f"\n/* {slide_key} */")
            for selector, props in rules:
                decls = "".join(f"  {p}: {v} !important;\n" for p, v in props.items())
                lines.append(f'[data-slide-key="{slide_key}"] {selector} {{\n{decls}}}')
        lines.append("")

        css_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"  [save] CSS overrides → {css_path} ({len(grouped)} slides)")

    def _apply_dom_changes(self, dom_changes: dict) -> list:
        """将 DOM 结构修改写回单页 HTML 文件。返回更新的文件路径列表。"""
        slides_dir = self.target_dir / "slides"
        updated = []

        for slide_key, changes in dom_changes.items():
            parts = slide_key.split("/", 1)
            if len(parts) != 2:
                print(f"  [save] 跳过无效的 slideKey: {slide_key}")
                continue
            slide_path = slides_dir / parts[0] / parts[1]
            if not slide_path.is_file():
                print(f"  [save] 跳过不存在的文件: {slide_path}")
                continue

            html = slide_path.read_text(encoding="utf-8")

            # Handle appended elements
            appended = changes.get("appended", [])
            if appended:
                for template in appended:
                    html = self._append_to_slide_body(html, template)

            # Handle reordered elements
            reordered = changes.get("reordered", {})
            if reordered:
                for parent_path, fingerprints in reordered.items():
                    html = self._reorder_children(html, parent_path, fingerprints)

            slide_path.write_text(html, encoding="utf-8")
            updated.append(str(slide_path))
            print(f"  [save] DOM changes → {slide_path}")

        return updated

    def _apply_text_changes(self, text_changes: dict) -> list:
        """将文本修改写回单页 HTML 文件。"""
        slides_dir = self.target_dir / "slides"
        updated = []

        for slide_key, changes in text_changes.items():
            parts = slide_key.split("/", 1)
            if len(parts) != 2:
                continue
            slide_path = slides_dir / parts[0] / parts[1]
            if not slide_path.is_file():
                continue

            html = slide_path.read_text(encoding="utf-8")

            for selector, new_html in changes.items():
                html = self._replace_element_text(html, selector, new_html)

            slide_path.write_text(html, encoding="utf-8")
            updated.append(str(slide_path))
            print(f"  [save] Text changes → {slide_path} ({len(changes)} edits)")

        return updated

    def _apply_deletions(self, deletions: dict) -> list:
        """从 HTML 文件中删除指定选择器匹配的元素。"""
        slides_dir = self.target_dir / "slides"
        updated = []

        for slide_key, selectors in deletions.items():
            parts = slide_key.split("/", 1)
            if len(parts) != 2:
                continue
            slide_path = slides_dir / parts[0] / parts[1]
            if not slide_path.is_file():
                continue

            html = slide_path.read_text(encoding="utf-8")
            modified = False

            for selector in selectors:
                # Walk the selector path to find the parent context
                path_parts = selector.split(" > ")
                last_part = path_parts[-1]
                tag_m = re.match(r'([a-z]+)', last_part)
                if not tag_m:
                    continue
                tag = tag_m.group(1)
                nth_m = re.search(r':nth-of-type\((\d+)\)', selector)
                nth = int(nth_m.group(1)) if nth_m else 1

                # Narrow down to parent scope if path has > 1 part
                scope_html = html
                scope_start = 0
                if len(path_parts) > 1:
                    # Find the parent container by walking path_parts[:-1]
                    for pp in path_parts[:-1]:
                        pp_tag_m = re.match(r'([a-z]+)', pp)
                        if not pp_tag_m:
                            continue
                        pp_tag = pp_tag_m.group(1)
                        pp_nth_m = re.search(r':nth-of-type\((\d+)\)', pp)
                        pp_nth = int(pp_nth_m.group(1)) if pp_nth_m else 1
                        pp_cls_m = re.search(r'\.([a-z_-]+)', pp)
                        pp_cls = pp_cls_m.group(1) if pp_cls_m else None

                        # Find nth <pp_tag> in scope_html
                        found_pp = 0
                        pos = 0
                        while found_pp < pp_nth:
                            m = re.search(r'<' + pp_tag + r'[\s>]', scope_html[pos:], re.IGNORECASE)
                            if not m:
                                break
                            found_pp += 1
                            if found_pp == pp_nth:
                                # Extract this parent's content
                                pp_open = scope_start + pos + m.start()
                                gt = scope_html[scope_start + pos + m.start():].find('>')
                                if gt == -1:
                                    break
                                content_start = scope_start + pos + m.start() + gt + 1
                                # Find matching close tag
                                depth = 1
                                scan = content_start
                                while depth > 0:
                                    no = html.find('<' + pp_tag, scan)
                                    nc = html.find('</' + pp_tag + '>', scan)
                                    if nc == -1:
                                        break
                                    if no != -1 and no < nc:
                                        at = html[no + len(pp_tag) + 1] if no + len(pp_tag) + 1 < len(html) else ''
                                        if at in (' ', '>', '\n', '\r'):
                                            depth += 1
                                        scan = no + len(pp_tag) + 1
                                    else:
                                        depth -= 1
                                        if depth == 0:
                                            scope_html = html[content_start:nc]
                                            scope_start = content_start
                                            break
                                        scan = nc + len(pp_tag) + 3
                                break
                            pos = m.end()

                # Now scope_html contains the parent's content
                # Parse only top-level children (like CSS nth-of-type on direct children)
                top_children = DeckHandler._parse_top_level_tags(scope_html, tag)

                found = 0
                for child_start, child_end in top_children:
                    found += 1
                    if found == nth:
                        # Found! Remove from abs_pos + child_start to abs_pos + child_end
                        abs_pos = scope_start + child_start
                        end = scope_start + child_end
                        while end < len(html) and html[end] in (' ', '\t', '\n', '\r'):
                            end += 1
                        html = html[:abs_pos] + html[end:]
                        modified = True
                        break

            if modified:
                html = re.sub(r'\n\s*\n\s*\n', '\n\n', html)
                slide_path.write_text(html, encoding="utf-8")
                updated.append(str(slide_path))
                print(f"  [save] Deletions → {slide_path} ({len(selectors)} removed)")

        return updated

    def _replace_element_text(self, html: str, selector: str, new_html: str) -> str:
        """在 HTML 中查找匹配选择器的元素并替换其内部 HTML。"""
        # selector 如 "div.card:nth-of-type(2) > p"
        # 简化处理：按标签和 nth-of-type 匹配
        parts = selector.split(" > ")
        last_part = parts[-1]  # 目标元素
        tag_match = re.match(r'([a-z]+)(.*)', last_part)
        if not tag_match:
            return html
        tag = tag_match.group(1)

        # 提取 nth-of-type
        nth_match = re.search(r':nth-of-type\((\d+)\)', selector)
        nth = int(nth_match.group(1)) if nth_match else 1

        # 在 HTML 中找到第 nth 个 <tag> 并替换内容
        pattern = re.compile(r'(<' + tag + r'\b[^>]*>)([\s\S]*?)(</' + tag + r'>)', re.IGNORECASE)

        count = 0
        def replace_nth(m):
            nonlocal count
            count += 1
            if count == nth:
                return m.group(1) + new_html + m.group(3)
            return m.group(0)

        return pattern.sub(replace_nth, html)

    def _append_to_slide_body(self, html: str, template: str) -> str:
        """在 slide HTML 的 .slide-body 末尾（或 </section> 前）追加新元素。"""
        # Strip inline styles from the template (styles go to CSS overrides)
        clean_template = re.sub(r'\s*style="[^"]*"', '', template)

        # Insert before </section>
        pos = html.rfind("</section>")
        if pos > 0:
            html = html[:pos].rstrip() + "\n" + clean_template + "\n" + html[pos:]
        else:
            # Fallback: append to end of HTML
            html = html.rstrip() + "\n" + clean_template + "\n"
        return html

    def _reorder_children(self, html: str, parent_selector: str, fingerprints: list) -> str:
        """根据文本指纹在 HTML 中重排子元素顺序。使用简单的解析器处理嵌套结构。"""
        parent_class = None
        for part in parent_selector.split(" > "):
            if "." in part:
                parent_class = part.split(".")[-1].split(":")[0]
        # Use the LAST (innermost) class in the selector

        if not parent_class:
            print(f"  [save] 无法解析父容器选择器: {parent_selector}")
            return html

        # 定位父容器：找到 class 包含 parent_class 的 div 的起止位置
        start_marker = f'class="{parent_class}"'
        alt_marker = f"class='{parent_class}'"
        # 也匹配 class 列表中包含 parent_class 的情况
        pattern = re.compile(
            r'(<div\s[^>]*\bclass="[^"]*\b' + re.escape(parent_class) + r'\b[^"]*"[^>]*>)',
            re.IGNORECASE
        )
        m = pattern.search(html)
        if not m:
            # 尝试单引号
            pattern_alt = re.compile(
                r"(<div\s[^>]*\bclass='[^']*\b" + re.escape(parent_class) + r"\b[^']*'[^>]*>)",
                re.IGNORECASE
            )
            m = pattern_alt.search(html)
        if not m:
            print(f"  [save] 未找到容器 .{parent_class}")
            return html

        open_tag_start = m.start()
        open_tag = m.group(0)

        # 通过计数匹配的 </div> 找到容器结束位置
        depth = 1
        pos = m.end()
        while depth > 0 and pos < len(html):
            next_open = html.find("<div", pos)
            next_close = html.find("</div>", pos)
            if next_close == -1:
                break
            if next_open != -1 and next_open < next_close:
                depth += 1
                pos = next_open + 4
            else:
                depth -= 1
                if depth == 0:
                    close_tag_end = next_close + len("</div>")
                    break
                pos = next_close + len("</div>")

        if depth != 0:
            print(f"  [save] 无法匹配容器的闭合标签")
            return html

        container_content = html[m.end():close_tag_end - len("</div>")]

        # 解析容器的直接子元素（顶层 div）
        children = self._parse_top_level_divs(container_content)
        if not children or len(children) < 2:
            return html
        if len(children) != len(fingerprints):
            print(f"  [save] 子元素数({len(children)}) ≠ 指纹数({len(fingerprints)})，跳过重排")
            return html

        # 对每个子元素计算文本指纹（模拟 textContent：去标签不加空格，保留源码空白）
        child_by_fp = {}
        for ch in children:
            text = re.sub(r'<[^>]+>', '', ch)
            fp = re.sub(r'\s+', ' ', text).strip()[:60]
            child_by_fp[fp] = ch

        if any(fp not in child_by_fp for fp in fingerprints):
            print(f"  [save] 指纹不匹配，跳过重排")
            return html

        # 按指纹顺序重排
        reordered_content = "\n".join(child_by_fp[fp] for fp in fingerprints)
        html = html[:m.end()] + "\n" + reordered_content + "\n" + html[close_tag_end - len("</div>"):]
        print(f"  [save] 已重排 .{parent_class} 中的 {len(fingerprints)} 个子元素")
        return html

    @staticmethod
    def _parse_top_level_tags(content: str, tag: str) -> list:
        """Parse all top-level occurrences of <tag>...</tag> in content.
        Returns list of (start, end) tuples. Handles nested tags of same type."""
        result = []
        depth = 0
        start = -1
        i = 0
        tag_len = len(tag)
        open_str = '<' + tag
        close_str = '</' + tag + '>'
        while i < len(content):
            if content[i:i+tag_len+1] == open_str and (i + tag_len + 1 >= len(content) or content[i+tag_len+1] in (' ', '>', '\n', '\r')):
                if depth == 0:
                    start = i
                depth += 1
                i += tag_len + 1
                continue
            elif content[i:i+tag_len+3] == close_str:
                depth -= 1
                if depth == 0 and start >= 0:
                    result.append((start, i + tag_len + 3))
                    start = -1
                i += tag_len + 3
                continue
            i += 1
        return result

    @staticmethod
    def _parse_top_level_divs(content: str) -> list:
        """解析 HTML 内容中所有顶层 div 元素。"""
        result = []
        depth = 0
        start = -1
        i = 0
        while i < len(content):
            if content[i:i+4] == "<div" and (i == 0 or depth == 0):
                # Only capture top-level divs (depth == 0)
                if depth > 0:
                    depth += 1
                else:
                    start = i
                    depth = 1
                i += 4
                continue
            elif content[i:i+6] == "</div>":
                depth -= 1
                if depth == 0 and start >= 0:
                    result.append(content[start:i+6])
                    start = -1
                i += 6
                continue
            i += 1
        return result

    def _serve_from(self, root: Path, req_path: str, strip_prefix: str = "") -> None:
        """从指定根目录提供请求路径的文件。可选去除路径前缀。"""
        import mimetypes
        rel = req_path.lstrip("/")
        if strip_prefix and rel.startswith(strip_prefix):
            rel = rel[len(strip_prefix):]
        if not rel:
            rel = "index.html"
        file_path = (root / rel).resolve()
        if not str(file_path).startswith(str(root.resolve())):
            self.send_error(403)
            return
        if file_path.is_dir():
            file_path = (file_path / "index.html").resolve()
        if not file_path.is_file():
            self.send_error(404)
            return

        mime_type, _ = mimetypes.guess_type(str(file_path))
        self.send_response(200)
        self.send_header("Content-Type", mime_type or "application/octet-stream")
        self.send_header("Access-Control-Allow-Origin", "*")
        # Don't cache dynamic content so edits and config-switching appear immediately.
        ext = file_path.suffix.lower()
        if ext in (".html", ".json", ".yaml", ".js", ".css"):
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        else:
            self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        self.wfile.write(file_path.read_bytes())

    def log_message(self, fmt, *args) -> None:
        if args and isinstance(args[0], str):
            p = args[0]
            if "/slides/" in p or p == "/slides-config.json":
                print(f"  [target] {p}")
            elif p.startswith("/css/"):
                print(f"  [css] {p}")
            else:
                print(f"  [container] {p}")


def read_slides_config(target: Path) -> dict | None:
    config_path = target / "slides-config.json"
    if not config_path.exists():
        return None
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    parser = argparse.ArgumentParser(description="启动 HTML Deck 本地服务")
    parser.add_argument("target", nargs="*", default=[], help="目标目录（可多个，每个需包含 slides-config.json 和 slides/）")
    parser.add_argument("--theme", default=None, help="CSS 主题（默认从 config.yaml 读取）")
    parser.add_argument("--port", type=int, default=8080, help="HTTP 端口 (default: 8080)")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    parser.add_argument("--watch", action="store_true", help="监视文件变化并自动刷新浏览器")
    args = parser.parse_args()

    # 读取 CSS 配置
    deck_config = load_deck_config()
    theme_names = {t["id"] for t in deck_config.get("themes", [])}
    fontsize_names = {fs["id"] for fs in deck_config.get("fontsizes", [])}
    theme = args.theme or default_theme(deck_config)

    print(f"容器目录: {CONTAINER}")
    print(f"主题: {theme} (可用: {', '.join(sorted(theme_names))})")
    print(f"字号: {', '.join(sorted(fontsize_names))}")

    # 加载持久化的配置
    DeckHandler._load_configs()

    # 处理 CLI 参数
    if args.target:
        first_from_cli = None
        for i, raw_path in enumerate(args.target):
            target = Path(raw_path).resolve()
            if not target.is_dir():
                print(f"错误：目标目录不存在，已跳过: {target}")
                continue
            if not (target / "slides-config.json").is_file():
                print(f"错误：目录中缺少 slides-config.json，已跳过: {target}")
                continue
            path_str = str(target)
            if path_str not in DeckHandler.configs:
                title = _read_config_title(target) or target.name
                DeckHandler.configs[path_str] = {"title": title, "path": path_str}
                slides_config = read_slides_config(target)
                if slides_config:
                    print(f"讲稿: {title} ({len(slides_config.get('parts', {}))} 章, {len(slides_config.get('slides', []))} 页)")
            if i == 0:
                first_from_cli = path_str
        # 第一个 CLI 参数作为激活配置
        if first_from_cli:
            DeckHandler.active_config_path = first_from_cli
            DeckHandler._sync_active()
            DeckHandler._persist_configs()

    # 确保至少有一个配置
    if not DeckHandler.configs:
        print("错误：没有可用的讲稿目录。请指定至少一个包含 slides-config.json 的目录。")
        return

    active = DeckHandler.configs.get(DeckHandler.active_config_path, {})
    print(f"活动讲稿: {active.get('title', '(无)')}")
    print(f"已注册讲稿: {len(DeckHandler.configs)} 个")

    DeckHandler.theme_dir = CONTAINER / "css" / "theme" / theme
    DeckHandler.deck_config = deck_config
    DeckHandler.theme_names = theme_names
    DeckHandler.fontsize_names = fontsize_names
    DeckHandler.watch_mode = args.watch

    if args.watch:
        watch_dirs = [Path(p) for p in DeckHandler.configs]
        for wd in watch_dirs:
            if wd.exists():
                DeckHandler._start_watcher(wd, CONTAINER)
                break
        print("监视模式: 已启用（文件变化时自动刷新浏览器）")

    if not DeckHandler.theme_dir.exists():
        print(f"警告：主题目录不存在: {DeckHandler.theme_dir}")

    server = HTTPServer(("localhost", args.port), DeckHandler)
    url = f"http://localhost:{args.port}"
    print(f"\n服务已启动: {url}")
    print("按 Ctrl+C 停止")

    if not args.no_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止。")


if __name__ == "__main__":
    main()
