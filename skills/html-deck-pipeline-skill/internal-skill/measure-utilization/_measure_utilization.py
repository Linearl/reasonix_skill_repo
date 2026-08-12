"""Measure per-slide space utilization of a merged deck HTML file.

Uses Playwright headless Chromium to render each slide and grid-sample
via elementFromPoint to determine what fraction of the slide area is
occupied by meaningful content (text, backgrounds, borders, etc.).

Usage:
    python _measure_utilization.py <path/to/deck.html> [--threshold 30] [--parts parts.json] [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

DEFAULT_THRESHOLD = 30.0  # slides below this utilization % are flagged as sparse


def build_measure_js() -> str:
    """Return the JS string (IIFE) that runs inside the browser page."""
    return """
    (async () => {
      const allSlides = document.querySelectorAll('.slide');
      const results = [];

      const layoutTags = new Set(['DIV', 'SECTION', 'MAIN', 'ARTICLE', 'HEADER', 'FOOTER', 'NAV', 'UL', 'OL', 'SPAN']);

      function isContentEl(el) {
        if (!el || el.nodeType !== 1) return false;
        const tag = el.tagName;
        const cs = getComputedStyle(el);

        const bg = cs.backgroundColor;
        const hasBg = bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent';
        const hasBorder = (parseFloat(cs.borderWidth) || 0) > 0;
        const hasText = el.children.length === 0 && el.textContent.trim().length > 0;
        const contentTags = new Set(['H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'P', 'TABLE', 'IMG', 'SVG', 'CODE', 'PRE', 'BLOCKQUOTE', 'HR', 'BUTTON', 'INPUT', 'TEXTAREA', 'SELECT', 'STRONG', 'EM']);
        const isContentTag = contentTags.has(tag);

        return hasBg || hasBorder || (hasText && !layoutTags.has(tag)) || isContentTag;
      }

      for (let i = 0; i < allSlides.length; i++) {
        const slide = allSlides[i];

        // Show only this slide
        allSlides.forEach(s => { s.style.display = 'none'; s.classList.remove('active'); });
        slide.style.display = 'flex';
        slide.classList.add('active');

        // Force reflow + wait for paint
        slide.getBoundingClientRect();
        await new Promise(r => requestAnimationFrame(r));

        const slideRect = slide.getBoundingClientRect();
        const slideArea = slideRect.width * slideRect.height;

        if (slideArea === 0) {
          results.push({ index: i, title: 'EMPTY_RECT', utilization: 0, slideW: 0, slideH: 0, slideArea: 0 });
          continue;
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
            // Walk up the DOM to find the first content-bearing ancestor
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
        const title = h2 ? h2.textContent.trim().substring(0, 60) : (slide.getAttribute('aria-labelledby') || 'no-title');

        results.push({
          index: i,
          title,
          slideW: Math.round(slideRect.width),
          slideH: Math.round(slideRect.height),
          slideArea: Math.round(slideArea),
          utilization: Math.round(utilization * 10) / 10
        });

        // Restore
        slide.style.display = 'none';
        slide.classList.remove('active');
      }

      // Restore first slide as active
      if (allSlides.length > 0) {
        allSlides[0].style.display = 'flex';
        allSlides[0].classList.add('active');
      }

      return results;
    })()
    """


def load_parts(parts_path: str | Path | None) -> list[tuple[str, int, int]]:
    """Load part definitions from a JSON file.

    JSON format: [{"name": "ch01-问题", "start": 0, "end": 2}, ...]
    Returns empty list if parts_path is None.
    """
    if parts_path is None:
        return []
    with open(parts_path, encoding="utf-8") as f:
        raw = json.load(f)
    return [(item["name"], item["start"], item["end"]) for item in raw]


def measure(
    html_path: str | Path,
    threshold: float = DEFAULT_THRESHOLD,
    parts: list[tuple[str, int, int]] | None = None,
) -> list[dict[str, Any]]:
    """Open *html_path* in headless Chromium and return per-slide utilization data."""
    from playwright.sync_api import sync_playwright

    html_path = Path(html_path).resolve()
    if not html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    file_url = html_path.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.goto(file_url, wait_until="networkidle")

        # Wait for JS navigation to initialize
        page.wait_for_timeout(500)

        js_code = build_measure_js()
        raw: list[dict[str, Any]] = page.evaluate(js_code)

        browser.close()

    # Annotate with part info if provided
    if parts:
        for r in raw:
            for part_name, start, end in parts:
                if start <= r["index"] <= end:
                    r["part"] = part_name
                    r["part_slide"] = r["index"] - start
                    break
            else:
                r["part"] = "-"
                r["part_slide"] = -1
    else:
        for r in raw:
            r["part"] = "-"
            r["part_slide"] = -1

    for r in raw:
        r["sparse"] = r["utilization"] < threshold

    return raw


def report(results: list[dict[str, Any]], threshold: float) -> str:
    """Format results as a readable report."""
    sorted_results = sorted(results, key=lambda r: r["utilization"])

    lines: list[str] = []
    has_parts = any(r.get("part") and r["part"] != "-" for r in results)

    if has_parts:
        lines.append(f"{'#':>3} | {'Util':>5} | {'Flag':>4} | {'Part':<18} | Slide Title")
        lines.append("-" * 100)
        for r in sorted_results:
            flag = "<<<" if r["sparse"] else ""
            idx = str(r["index"]).rjust(2)
            util = f"{r['utilization']:.1f}%"
            part_label = f"{r['part']}[{r['part_slide']}]"
            lines.append(f" {idx} | {util:>5} | {flag:>4} | {part_label:<18} | {r['title']}")
    else:
        lines.append(f"{'#':>3} | {'Util':>5} | {'Flag':>4} | Slide Title")
        lines.append("-" * 75)
        for r in sorted_results:
            flag = "<<<" if r["sparse"] else ""
            idx = str(r["index"]).rjust(2)
            util = f"{r['utilization']:.1f}%"
            lines.append(f" {idx} | {util:>5} | {flag:>4} | {r['title']}")

    lines.append("")
    sparse_count = sum(1 for r in sorted_results if r["sparse"])
    lines.append(f"Sparse slides (below {threshold:.0f}%): {sparse_count}/{len(results)}")
    if sparse_count > 0:
        lines.append("Tip: cover/section-divider slides with low utilization are usually by design.")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure slide space utilization")
    parser.add_argument("html", help="Path to merged HTML file")
    parser.add_argument(
        "--threshold", "-t",
        type=float, default=DEFAULT_THRESHOLD,
        help="Utilization %% threshold for flagging (default: 30)",
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of report")
    parser.add_argument(
        "--parts",
        type=str, default=None,
        help="Optional JSON file defining slide parts: [{\"name\": \"...\", \"start\": N, \"end\": M}, ...]",
    )
    args = parser.parse_args()

    parts = load_parts(args.parts) if args.parts else None

    try:
        results = measure(args.html, args.threshold, parts)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        json.dump(results, sys.stdout, ensure_ascii=False, indent=2)
    else:
        # Force UTF-8 output on Windows consoles that default to GBK
        import io
        if sys.stdout.encoding != "utf-8":
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        print(report(results, args.threshold))


if __name__ == "__main__":
    main()
