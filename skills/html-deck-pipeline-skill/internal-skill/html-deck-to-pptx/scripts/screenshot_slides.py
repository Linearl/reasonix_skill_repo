"""
HTML幻灯片逐页截图脚本
用法: python screenshot_slides.py --html <path> --total <N> [options]
"""
import argparse
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


async def screenshot(html_file: str, output_dir: str, total: int,
                     vw: int, vh: int, next_key: str,
                     selector: str, quality: int, wait_ms: int):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(
            viewport={"width": vw, "height": vh},
            device_scale_factor=1,
        )
        page = await ctx.new_page()
        await page.goto(Path(html_file).as_uri(), wait_until="networkidle")

        for i in range(total):
            n = i + 1
            target = page.locator(selector)
            await target.screenshot(path=str(out / f"{n}.jpg"), type="jpeg", quality=quality)
            print(f"已截图：第 {n}/{total} 页")
            if n < total:
                await page.keyboard.press(next_key)
                await page.wait_for_timeout(wait_ms)

        await browser.close()
    print(f"\n完成！共 {total} 张截图 → {out}")


def main():
    ap = argparse.ArgumentParser(description="HTML幻灯片逐页截图")
    ap.add_argument("--html", required=True, help="HTML文件路径")
    ap.add_argument("--output-dir", default=None, help="截图输出目录（默认: <html所在目录>/screenshot）")
    ap.add_argument("--total", type=int, required=True, help="幻灯片总页数")
    ap.add_argument("--viewport-width", type=int, default=1536, help="视口宽度（默认1536）")
    ap.add_argument("--viewport-height", type=int, default=960, help="视口高度（默认960）")
    ap.add_argument("--next-key", default="ArrowRight", help="下一页按键（默认ArrowRight）")
    ap.add_argument("--selector", default=".deck", help="截图目标CSS选择器（默认.deck）")
    ap.add_argument("--quality", type=int, default=95, help="JPEG质量 1-100（默认95）")
    ap.add_argument("--wait-ms", type=int, default=300, help="翻页后等待毫秒数（默认300）")
    args = ap.parse_args()

    if args.output_dir is None:
        args.output_dir = str(Path(args.html).parent / "screenshot")

    asyncio.run(screenshot(
        html_file=args.html,
        output_dir=args.output_dir,
        total=args.total,
        vw=args.viewport_width,
        vh=args.viewport_height,
        next_key=args.next_key,
        selector=args.selector,
        quality=args.quality,
        wait_ms=args.wait_ms,
    ))


if __name__ == "__main__":
    main()
