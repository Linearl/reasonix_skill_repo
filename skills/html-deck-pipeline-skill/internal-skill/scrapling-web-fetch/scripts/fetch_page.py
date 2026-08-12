"""Scrapling 网页抓取辅助脚本 — 支持快速/隐身/动态三种模式、滚动加载和批量抓取。"""

import argparse
import json
import subprocess
import sys
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


def ensure_scrapling() -> None:
    """检查 scrapling 是否已安装，若缺失则自动安装并配置浏览器依赖。"""
    try:
        import scrapling  # noqa: F401

        return
    except ImportError:
        pass

    print("[auto-install] scrapling 未安装，正在自动安装...", file=sys.stderr)
    python = sys.executable

    # Step 1: pip install
    print('[auto-install] pip install "scrapling[all]" ...', file=sys.stderr)
    result = subprocess.run(
        [python, "-m", "pip", "install", "scrapling[all]"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"[auto-install] pip install 失败:\n{result.stderr}", file=sys.stderr)
        print(
            "[auto-install] 请参考快速部署指南手动安装: "
            'pip install "scrapling[all]"',
            file=sys.stderr,
        )
        sys.exit(1)
    print("[auto-install] pip install 完成", file=sys.stderr)

    # Step 2: scrapling install (浏览器依赖)
    # scrapling CLI 可能不在 PATH，用 Scripts 目录定位
    scripts_dir = Path(python).parent / "Scripts"
    scrapling_cmd = scripts_dir / "scrapling"
    if not scrapling_cmd.exists() and not (scripts_dir / "scrapling.exe").exists():
        scrapling_cmd = "scrapling"  # fallback to PATH

    print("[auto-install] scrapling install (浏览器依赖) ...", file=sys.stderr)
    result = subprocess.run(
        [str(scrapling_cmd), "install"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(
            f"[auto-install] scrapling install 警告:\n{result.stderr}",
            file=sys.stderr,
        )
        print(
            "[auto-install] 浏览器依赖安装可能不完整，fetcher 模式仍可用，"
            "stealthy/dynamic 可能需要手动执行 scrapling install",
            file=sys.stderr,
        )
    else:
        print("[auto-install] 浏览器依赖安装完成", file=sys.stderr)

    # 验证安装
    try:
        import scrapling  # noqa: F401

        print(
            f"[auto-install] 安装成功，版本: {scrapling.__version__}",
            file=sys.stderr,
        )
    except ImportError:
        print("[auto-install] 安装后仍无法导入 scrapling，请手动检查", file=sys.stderr)
        sys.exit(1)


# 已知站点的文章正文 CSS 选择器
SITE_CONTENT_SELECTORS: dict[str, str] = {
    "zhuanlan.zhihu.com": ".Post-RichTextContainer",
    "www.zhihu.com": ".RichText",
    "mp.weixin.qq.com": "#js_content",
    "juejin.cn": ".article-content",
    "www.jianshu.com": ".article .show-content",
    "blog.csdn.net": "#content_views",
}

# 已知站点的列表项 CSS 选择器
SITE_LIST_SELECTORS: dict[str, str] = {
    "www.zhihu.com/column": "h2.ContentItem-title a",
    "www.zhihu.com/org": ".ContentItem-title a, h2 a",
}


def detect_site_selector(url: str, mode: str = "content") -> Optional[str]:
    """根据 URL 自动匹配已知站点的 CSS 选择器。"""
    parsed = urlparse(url)
    host_path = f"{parsed.hostname}{parsed.path}" if parsed.hostname else ""

    selectors = SITE_LIST_SELECTORS if mode == "list" else SITE_CONTENT_SELECTORS
    for pattern, selector in selectors.items():
        if pattern in host_path or pattern == parsed.hostname:
            return selector
    return None


def html_to_markdown(html: str) -> str:
    """将 HTML 内容转换为简洁的 Markdown 纯文本，自动过滤脚本和样式。"""
    text = html

    # 先移除 script/style/noscript 及其内容（SPA 页面的关键清理）
    text = re.sub(
        r"<script[^>]*>.*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL
    )
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(
        r"<noscript[^>]*>.*?</noscript>", "", text, flags=re.IGNORECASE | re.DOTALL
    )
    text = re.sub(r"<head[^>]*>.*?</head>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<nav[^>]*>.*?</nav>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(
        r"<footer[^>]*>.*?</footer>", "", text, flags=re.IGNORECASE | re.DOTALL
    )

    # <br> → newline
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)

    # <p> → double newline
    text = re.sub(r"</?p[^>]*>", "\n\n", text, flags=re.IGNORECASE)

    # headings
    for level in range(1, 7):
        prefix = "#" * level
        text = re.sub(
            rf"<h{level}[^>]*>(.*?)</h{level}>",
            rf"\n\n{prefix} \1\n\n",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

    # <img> → ![alt](src)
    text = re.sub(
        r'<img[^>]*?src=["\']([^"\']*)["\'][^>]*?(?:alt=["\']([^"\']*)["\'])?[^>]*?>',
        lambda m: f"![{m.group(2) or ''}]({m.group(1)})",
        text,
        flags=re.IGNORECASE,
    )

    # links: <a href="url">text</a> → [text](url)
    text = re.sub(
        r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>',
        r"[\2](\1)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # <strong>/<b> → **text**
    text = re.sub(r"</?(?:strong|b)>", "**", text, flags=re.IGNORECASE)

    # <em>/<i> → *text*
    text = re.sub(r"</?(?:em|i)>", "*", text, flags=re.IGNORECASE)

    # <li> → bullet
    text = re.sub(r"<li[^>]*>", "\n- ", text, flags=re.IGNORECASE)

    # <blockquote>
    text = re.sub(
        r"<blockquote[^>]*>(.*?)</blockquote>",
        lambda m: "\n"
        + "\n".join("> " + line for line in m.group(1).strip().split("\n"))
        + "\n",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # <code> → backtick
    text = re.sub(
        r"<code[^>]*>(.*?)</code>", r"`\1`", text, flags=re.IGNORECASE | re.DOTALL
    )

    # <pre> → code block
    text = re.sub(
        r"<pre[^>]*>(.*?)</pre>",
        r"\n```\n\1\n```\n",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # strip remaining tags
    text = re.sub(r"<[^>]+>", "", text)

    # decode common entities
    for entity, char in [
        ("&amp;", "&"),
        ("&lt;", "<"),
        ("&gt;", ">"),
        ("&quot;", '"'),
        ("&#39;", "'"),
        ("&nbsp;", " "),
        ("&#x27;", "'"),
        ("&apos;", "'"),
        ("&ndash;", "\u2013"),
        ("&mdash;", "\u2014"),
        ("&hellip;", "\u2026"),
    ]:
        text = text.replace(entity, char)

    # collapse excessive whitespace on each line
    text = re.sub(r"[ \t]+", " ", text)
    # collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def fetch_with_fetcher(
    url: str, timeout: int = 30000, css: Optional[str] = None
) -> tuple[int, str, str]:
    """使用 Fetcher（快速 HTTP 请求）抓取页面。"""
    from scrapling.fetchers import Fetcher

    page = Fetcher.get(url, stealthy_headers=True, timeout=timeout)
    status = page.status
    full_html = page.html_content

    if css:
        elements = page.css(css)
        content = "\n".join(el.html_content for el in elements)
    else:
        content = full_html

    return status, content, full_html


def load_cookies(cookies_path: Optional[str] = None) -> Optional[list]:
    """从 JSON 文件加载 cookies。"""
    if not cookies_path:
        # 默认查找技能目录下的 cookies
        default_path = Path(__file__).parent / "zhihu_cookies.json"
        if default_path.exists():
            cookies_path = str(default_path)
        else:
            return None

    path = Path(cookies_path)
    if not path.exists():
        print(f"[warn] Cookies 文件不存在: {path}", file=sys.stderr)
        return None

    cookies = json.loads(path.read_text(encoding="utf-8"))
    print(f"[cookies] 加载了 {len(cookies)} 个 cookie", file=sys.stderr)
    return cookies


def make_scroll_action(scroll_count: int = 5, scroll_pause_ms: int = 2000):
    """创建滚动页面的 page_action 函数，用于加载无限滚动内容。"""

    def scroll_action(page):
        for i in range(scroll_count):
            # 使用 Playwright 的 wait_for_timeout 而非 time.sleep，确保浏览器能处理事件
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(scroll_pause_ms)
            print(f"  [scroll] {i+1}/{scroll_count}", file=sys.stderr)

    return scroll_action


def fetch_with_stealthy(
    url: str,
    timeout: int = 30000,
    css: Optional[str] = None,
    solve_cloudflare: bool = False,
    wait: int = 3000,
    cookies: Optional[list] = None,
    scroll: int = 0,
) -> tuple[int, str, str]:
    """使用 StealthyFetcher（隐身浏览器）抓取页面，可绕过 Cloudflare。"""
    from scrapling.fetchers import StealthyFetcher

    kwargs = dict(
        headless=True,
        timeout=timeout,
        network_idle=True,
        solve_cloudflare=solve_cloudflare,
        wait=wait,
    )
    if cookies:
        kwargs["cookies"] = cookies
    if scroll > 0:
        kwargs["page_action"] = make_scroll_action(scroll_count=scroll)

    page = StealthyFetcher.fetch(url, **kwargs)
    status = page.status
    full_html = page.html_content

    if css:
        elements = page.css(css)
        content = "\n".join(el.html_content for el in elements)
    else:
        content = full_html

    return status, content, full_html


def fetch_with_dynamic(
    url: str,
    timeout: int = 30000,
    css: Optional[str] = None,
    wait: int = 3000,
    cookies: Optional[list] = None,
    scroll: int = 0,
) -> tuple[int, str, str]:
    """使用 DynamicFetcher（Playwright 浏览器）抓取 JS 渲染页面。"""
    from scrapling.fetchers import DynamicFetcher

    kwargs = dict(
        headless=True,
        timeout=timeout,
        network_idle=True,
        wait=wait,
    )
    if cookies:
        kwargs["cookies"] = cookies
    if scroll > 0:
        kwargs["page_action"] = make_scroll_action(scroll_count=scroll)

    page = DynamicFetcher.fetch(url, **kwargs)
    status = page.status
    full_html = page.html_content

    if css:
        elements = page.css(css)
        content = "\n".join(el.html_content for el in elements)
    else:
        content = full_html

    return status, content, full_html


FETCH_METHODS = {
    "fetcher": fetch_with_fetcher,
    "stealthy": fetch_with_stealthy,
    "dynamic": fetch_with_dynamic,
}


def fetch_single(
    url: str,
    method: str = "fetcher",
    css: Optional[str] = None,
    timeout: int = 30000,
    output_format: str = "markdown",
    solve_cloudflare: bool = False,
    cookies_path: Optional[str] = None,
    scroll: int = 0,
    save_html: Optional[str] = None,
    auto_selector: bool = True,
) -> tuple[int, str]:
    """抓取单个 URL 并返回 (状态码, 内容)。"""
    fetch_fn = FETCH_METHODS.get(method)
    if not fetch_fn:
        raise ValueError(f"未知抓取方法: {method}，可选: {list(FETCH_METHODS.keys())}")

    # 若未指定 CSS 选择器，自动检测已知站点
    effective_css = css
    if not effective_css and auto_selector:
        effective_css = detect_site_selector(url)
        if effective_css:
            print(
                f"[auto-css] 检测到已知站点，使用选择器: {effective_css}",
                file=sys.stderr,
            )

    kwargs = {"url": url, "timeout": timeout, "css": effective_css}
    if method in ("stealthy", "dynamic"):
        kwargs["wait"] = 5000
        kwargs["scroll"] = scroll
        cookies = load_cookies(cookies_path)
        if cookies:
            kwargs["cookies"] = cookies
    if method == "stealthy":
        kwargs["solve_cloudflare"] = solve_cloudflare

    status, html, full_html = fetch_fn(**kwargs)

    # 保存完整原始 HTML 作为过程资产（不受 CSS 选择器影响）
    if save_html:
        html_path = Path(save_html)
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(full_html, encoding="utf-8")
        print(
            f"[html] 已保存完整 HTML ({len(full_html)} 字符) → {html_path}",
            file=sys.stderr,
        )

    if output_format == "markdown":
        content = html_to_markdown(html)
    elif output_format == "text":
        # 先清除脚本和样式再去标签
        cleaned = re.sub(
            r"<script[^>]*>.*?</script>", "", html, flags=re.IGNORECASE | re.DOTALL
        )
        cleaned = re.sub(
            r"<style[^>]*>.*?</style>", "", cleaned, flags=re.IGNORECASE | re.DOTALL
        )
        content = re.sub(r"<[^>]+>", "", cleaned).strip()
    else:
        content = html

    return status, content


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="使用 Scrapling 抓取网页内容",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="目标 URL")
    group.add_argument("--batch", help="批量 URL 的 JSON 文件路径")

    parser.add_argument(
        "--method",
        choices=["fetcher", "stealthy", "dynamic"],
        default="fetcher",
        help="抓取方法 (default: fetcher)",
    )
    parser.add_argument("--output", help="输出文件路径（单 URL 模式）")
    parser.add_argument("--output-dir", default=".", help="输出目录（批量模式）")
    parser.add_argument("--css", help="CSS 选择器，仅提取匹配元素")
    parser.add_argument(
        "--timeout", type=int, default=30000, help="超时毫秒数 (default: 30000)"
    )
    parser.add_argument(
        "--solve-cloudflare", action="store_true", help="尝试解决 Cloudflare 挑战"
    )
    parser.add_argument(
        "--cookies", help="Cookies JSON 文件路径（默认自动查找 zhihu_cookies.json）"
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "text", "html"],
        default="markdown",
        help="输出格式 (default: markdown)",
    )
    parser.add_argument(
        "--scroll",
        type=int,
        default=0,
        help="页面滚动次数，用于加载无限滚动内容（每次间隔2秒）",
    )
    parser.add_argument(
        "--save-html",
        dest="save_html",
        help="同时保存原始 HTML 到指定路径（过程资产）",
    )
    parser.add_argument(
        "--no-auto-selector",
        dest="auto_selector",
        action="store_false",
        help="禁用已知站点的自动 CSS 选择器",
    )
    return parser


def main() -> None:
    ensure_scrapling()

    parser = build_parser()
    args = parser.parse_args()

    if args.url:
        print(f"[fetch] {args.method} → {args.url}", file=sys.stderr)
        status, content = fetch_single(
            url=args.url,
            method=args.method,
            css=args.css,
            timeout=args.timeout,
            output_format=args.format,
            solve_cloudflare=args.solve_cloudflare,
            cookies_path=args.cookies,
            scroll=args.scroll,
            save_html=args.save_html,
            auto_selector=args.auto_selector,
        )
        print(f"[status] {status}", file=sys.stderr)

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
            print(f"[saved] {output_path}", file=sys.stderr)
        else:
            print(content)

    elif args.batch:
        batch_path = Path(args.batch)
        urls = json.loads(batch_path.read_text(encoding="utf-8"))
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        ext = (
            ".md"
            if args.format == "markdown"
            else (".txt" if args.format == "text" else ".html")
        )

        for i, item in enumerate(urls):
            url = item if isinstance(item, str) else item.get("url", "")
            name = (
                item.get("name", f"page_{i}") if isinstance(item, dict) else f"page_{i}"
            )

            print(f"[fetch {i+1}/{len(urls)}] {args.method} → {url}", file=sys.stderr)
            try:
                html_save = None
                if args.save_html:
                    html_dir = Path(args.save_html)
                    html_dir.mkdir(parents=True, exist_ok=True)
                    html_save = str(html_dir / f"{name}.html")

                status, content = fetch_single(
                    url=url,
                    method=args.method,
                    css=args.css,
                    timeout=args.timeout,
                    output_format=args.format,
                    solve_cloudflare=args.solve_cloudflare,
                    cookies_path=args.cookies,
                    scroll=args.scroll,
                    save_html=html_save,
                    auto_selector=args.auto_selector,
                )
                print(f"[status] {status}", file=sys.stderr)

                out_file = output_dir / f"{name}{ext}"
                out_file.write_text(content, encoding="utf-8")
                print(f"[saved] {out_file}", file=sys.stderr)
            except Exception as e:
                print(f"[error] {url}: {e}", file=sys.stderr)

        print(f"[done] {len(urls)} URLs processed", file=sys.stderr)


if __name__ == "__main__":
    main()
