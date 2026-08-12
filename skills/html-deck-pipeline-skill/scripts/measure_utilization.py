"""Measure per-slide space utilization of an HTML deck.

Connects to a running deck server (started by serve.py) and measures
each slide's content utilization via Playwright headless Chromium.

Usage:
    python scripts/measure_utilization.py http://localhost:8080 [--threshold 30]
    python scripts/measure_utilization.py http://localhost:8080 --json > report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

DEFAULT_URL = "http://localhost:8080"
DEFAULT_THRESHOLD = 30.0  # slides below this utilization % are flagged as sparse


def build_measure_js() -> str:
    """Return JS IIFE that samples the currently active slide."""
    return """
    (() => {
      const slide = document.querySelector('.slide.active');
      if (!slide) return null;

      const layoutTags = new Set([
        'DIV', 'SECTION', 'MAIN', 'ARTICLE', 'HEADER', 'FOOTER', 'NAV', 'UL', 'OL', 'SPAN'
      ]);

      function isContentEl(el) {
        if (!el || el.nodeType !== 1) return false;
        const tag = el.tagName;
        const cs = getComputedStyle(el);
        const bg = cs.backgroundColor;
        const hasBg = bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent';
        const hasBorder = (parseFloat(cs.borderWidth) || 0) > 0;
        const hasText = el.children.length === 0 && el.textContent.trim().length > 0;
        const contentTags = new Set([
          'H1','H2','H3','H4','H5','H6','P','TABLE','IMG','SVG','CODE','PRE',
          'BLOCKQUOTE','HR','BUTTON','INPUT','TEXTAREA','SELECT','STRONG','EM',
          'A','LI','DT','DD','FIGCAPTION','CANVAS'
        ]);
        return hasBg || hasBorder || (hasText && !layoutTags.has(tag)) || contentTags.has(tag);
      }

      const slideRect = slide.getBoundingClientRect();
      const slideArea = slideRect.width * slideRect.height;
      if (slideArea === 0) {
        return { utilization: 0, slideW: 0, slideH: 0, slideArea: 0, title: '' };
      }

      const gridSize = 40;
      const cellW = slideRect.width / gridSize;
      const cellH = slideRect.height / gridSize;
      let contentPoints = 0;
      let totalPoints = 0;

      for (let row = 0; row < gridSize; row++) {
        for (let col = 0; col < gridSize; col++) {
          const x = slideRect.left + col * cellW + cellW / 2;
          const y = slideRect.top + row * cellH + cellH / 2;
          totalPoints++;
          const el = document.elementFromPoint(x, y);
          let cursor = el;
          let found = false;
          while (cursor && cursor !== slide && cursor !== document.body && cursor !== document.documentElement) {
            if (isContentEl(cursor)) { found = true; break; }
            cursor = cursor.parentElement;
          }
          if (found) contentPoints++;
        }
      }

      const utilization = totalPoints > 0 ? (contentPoints / totalPoints * 100) : 0;
      const h2 = slide.querySelector('h2');
      const title = h2 ? h2.textContent.trim().substring(0, 60) : '';

      return {
        slideW: Math.round(slideRect.width),
        slideH: Math.round(slideRect.height),
        slideArea: Math.round(slideArea),
        utilization: Math.round(utilization * 10) / 10,
        title
      };
    })()
    """


def measure(url: str, threshold: float = DEFAULT_THRESHOLD) -> list[dict[str, Any]]:
    """Open *url* in headless Chromium, navigate slides via deck.js, return per-slide data."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(500)

        # Fetch config to get slide list and part info
        config: dict[str, Any] = page.evaluate(
            "() => fetch('slides-config.json').then(r => r.json())"
        )
        slides: list[dict[str, Any]] = config.get("slides", [])
        parts: dict[str, str] = config.get("parts", {})

        results: list[dict[str, Any]] = []
        js_code = build_measure_js()

        for i, slide_info in enumerate(slides):
            # Navigate via deck.js goToSlide (falls back to direct DOM if unavailable)
            page.evaluate(
                f"""
                () => {{
                  if (typeof goToSlide === 'function') {{
                    goToSlide({i});
                  }}
                }}
                """
            )
            page.wait_for_timeout(200)

            data: dict[str, Any] | None = page.evaluate(js_code)
            if data is None:
                data = {"utilization": 0, "slideW": 0, "slideH": 0, "slideArea": 0, "title": "ERROR"}

            part_id: str = slide_info.get("part", "")
            part_name: str = parts.get(part_id, part_id)

            results.append({
                "index": i,
                "part": part_id,
                "part_name": part_name,
                "file": slide_info.get("file", ""),
                "title": data.get("title") or slide_info.get("title", "untitled"),
                "slideW": data.get("slideW", 0),
                "slideH": data.get("slideH", 0),
                "utilization": data.get("utilization", 0),
                "sparse": data.get("utilization", 0) < threshold,
            })

        browser.close()

    return results


def report(results: list[dict[str, Any]], threshold: float) -> str:
    """Format results as a readable text report."""
    sorted_results = sorted(results, key=lambda r: r["utilization"])

    lines: list[str] = []
    lines.append(f"{'#':>3} | {'Util':>5} | {'Flag':>4} | {'Part':<12} | Slide Title")
    lines.append("-" * 80)

    for r in sorted_results:
        flag = "<<<" if r["sparse"] else ""
        lines.append(
            f" {r['index']:>2} | {r['utilization']:>4.1f}% | {flag:>4} "
            f"| {r['part_name']:<12} | {r['title'][:50]}"
        )

    lines.append("")
    sparse_count = sum(1 for r in sorted_results if r["sparse"])
    total = len(results)
    lines.append(f"Sparse slides (below {threshold:.0f}%): {sparse_count}/{total}")

    # Per-part summary
    lines.append("\n--- By Part ---")
    part_groups: dict[str, list[dict[str, Any]]] = {}
    for r in results:
        part_groups.setdefault(r["part_name"], []).append(r)

    for pn, items in part_groups.items():
        avg_util = sum(r["utilization"] for r in items) / len(items)
        sparse_in_part = sum(1 for r in items if r["sparse"])
        lines.append(f"  {pn}: avg {avg_util:.1f}%, sparse {sparse_in_part}/{len(items)}")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure slide space utilization")
    parser.add_argument(
        "url", nargs="?", default=DEFAULT_URL,
        help="URL of the running deck server (default: http://localhost:8080)"
    )
    parser.add_argument(
        "--threshold", "-t", type=float, default=DEFAULT_THRESHOLD,
        help="Utilization %% threshold for flagging (default: 30)"
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of report")
    args = parser.parse_args()

    try:
        results = measure(args.url, args.threshold)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print(
            "Make sure the deck server is running: "
            "python container/serve.py <target_dir> --theme <theme_name>",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.json:
        json.dump(results, sys.stdout, ensure_ascii=False, indent=2)
    else:
        import io
        if sys.stdout.encoding != "utf-8":
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        print(report(results, args.threshold))


if __name__ == "__main__":
    main()
