"""知乎登录辅助脚本 — 打开可见浏览器让用户登录，保存 cookies 供后续抓取使用。"""

import json
import sys
import time
from pathlib import Path


COOKIES_PATH = Path(__file__).parent / "zhihu_cookies.json"


def login_and_save_cookies() -> None:
    """打开可见浏览器访问知乎，等待用户登录后保存 cookies。"""
    from scrapling.fetchers import StealthyFetcher

    print("[info] 正在打开知乎登录页面（可见浏览器）...", file=sys.stderr)
    print("[info] 请在浏览器中完成登录操作", file=sys.stderr)
    print("[info] 登录成功后，脚本会自动保存 cookies", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    def wait_for_login(page):
        """等待用户完成登录。"""
        print("[wait] 等待登录... 登录后页面会自动跳转", file=sys.stderr)

        max_wait = 300  # 5 分钟超时
        check_interval = 3
        elapsed = 0

        while elapsed < max_wait:
            time.sleep(check_interval)
            elapsed += check_interval

            current_url = page.url
            print(f"[check] {elapsed}s - 当前页面: {current_url}", file=sys.stderr)

            # 已登录：不再在登录页
            if "signin" not in current_url and "login" not in current_url:
                print("[ok] 检测到登录成功！", file=sys.stderr)
                time.sleep(2)
                return

        print("[timeout] 等待超时，将保存当前状态", file=sys.stderr)

    page = StealthyFetcher.fetch(
        "https://www.zhihu.com/signin",
        headless=False,
        timeout=60000,
        network_idle=True,
        page_action=wait_for_login,
        wait=2000,
    )

    # 提取 cookies
    cookies = page.cookies() if hasattr(page, "cookies") else []

    if not cookies:
        # 如果 Response 对象没有 cookies 方法，尝试从 headers 提取
        print("[warn] 无法直接获取 cookies，尝试备用方案...", file=sys.stderr)
        print("[info] 请使用方案二：手动导出 cookies", file=sys.stderr)
        print_manual_instructions()
        return

    COOKIES_PATH.write_text(
        json.dumps(cookies, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[saved] Cookies 已保存到: {COOKIES_PATH}", file=sys.stderr)
    print(f"[info] 共保存 {len(cookies)} 个 cookie", file=sys.stderr)


def print_manual_instructions() -> None:
    """打印手动导出 cookies 的说明。"""
    print(
        """
╔══════════════════════════════════════════════════╗
║          手动导出 Cookies 方案                     ║
╠══════════════════════════════════════════════════╣
║ 1. 在 Chrome 中打开 https://www.zhihu.com        ║
║ 2. 登录你的知乎账号                               ║
║ 3. 按 F12 打开开发者工具                           ║
║ 4. 切换到 Console 标签                            ║
║ 5. 输入: document.cookie                         ║
║ 6. 复制输出的字符串                                ║
║ 7. 运行本脚本: python zhihu_login.py --import     ║
║    然后粘贴 cookie 字符串                          ║
╚══════════════════════════════════════════════════╝
""",
        file=sys.stderr,
    )


def import_cookie_string(cookie_str: str) -> None:
    """从 document.cookie 导出的字符串导入 cookies。"""
    cookies = []
    for part in cookie_str.strip().split(";"):
        part = part.strip()
        if "=" in part:
            name, value = part.split("=", 1)
            cookies.append(
                {
                    "name": name.strip(),
                    "value": value.strip(),
                    "domain": ".zhihu.com",
                    "path": "/",
                }
            )

    COOKIES_PATH.write_text(
        json.dumps(cookies, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[saved] 从 cookie 字符串导入了 {len(cookies)} 个 cookie", file=sys.stderr)
    print(f"[saved] 保存到: {COOKIES_PATH}", file=sys.stderr)


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--import":
        print("请粘贴 document.cookie 的输出（一行字符串）：", file=sys.stderr)
        cookie_str = input()
        import_cookie_string(cookie_str)
    elif len(sys.argv) > 1 and sys.argv[1] == "--check":
        if COOKIES_PATH.exists():
            cookies = json.loads(COOKIES_PATH.read_text(encoding="utf-8"))
            print(f"[info] 已有 {len(cookies)} 个 cookie", file=sys.stderr)
            for c in cookies[:5]:
                print(
                    f"  - {c.get('name', '?')}: {c.get('value', '?')[:20]}...",
                    file=sys.stderr,
                )
        else:
            print("[info] 尚未保存任何 cookies", file=sys.stderr)
    else:
        login_and_save_cookies()


if __name__ == "__main__":
    main()
