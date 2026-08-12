#!/usr/bin/env python3
"""validate_tokens.py — verify theme token completeness and contrast ratios."""

import argparse, re, sys, math
from pathlib import Path

REQUIRED_TOKENS = {
    "背景层": ["--bg", "--surface-1", "--surface-2", "--surface-3"],
    "文字层": ["--text", "--text-sec", "--text-faint"],
    "强调色": ["--accent", "--accent-strong", "--brand"],
    "语义色": ["--ok", "--warn", "--risk", "--info"],
    "边框": ["--border-subtle", "--border-soft"],
    "特效": ["--surface-glass", "--surface-glow", "--surface-hover"],
    "阴影": ["--shadow-soft", "--shadow-strong"],
    "渐变": ["--bg-gradient-body", "--bg-gradient-deck", "--bg-gradient-slide"],
    "排版": ["--font-main", "--font-code"],
    "字号": ["--text-xs", "--text-sm", "--text-md", "--text-lg", "--text-xl"],
    "圆角/过渡": ["--radius-sm", "--radius-md", "--radius-lg", "--transition-fast"],
}

ALL_TOKENS = [t for group in REQUIRED_TOKENS.values() for t in group]

CONTRAST_PAIRS = [
    ("--text", "--bg"),
    ("--text-sec", "--bg"),
    ("--text", "--surface-1"),
    ("--accent", "--bg"),
    ("--brand", "--bg"),
]


def parse_tokens(css_path):
    """Extract custom property definitions from a tokens.css file."""
    text = css_path.read_text(encoding="utf-8")
    # Match: --name: value;
    pattern = re.compile(r'^\s*(--[\w-]+)\s*:\s*(.+?)\s*;', re.MULTILINE)
    tokens = {}
    for m in pattern.finditer(text):
        tokens[m.group(1)] = m.group(2).strip()
    return tokens


def parse_color(value):
    """Parse a CSS color value to (r, g, b) tuple. Returns None if unparseable."""
    value = value.strip().lower()
    # hex
    m = re.match(r'^#([0-9a-f]{3})$', value)
    if m:
        h = m.group(1)
        return tuple(int(c * 2, 16) for c in h)
    m = re.match(r'^#([0-9a-f]{6})$', value)
    if m:
        h = m.group(1)
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    # rgb/rgba
    m = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', value)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    # oklch
    m = re.match(r'oklch\(([\d.]+)\s+([\d.]+)\s+([\d.]+)', value)
    if m:
        L = float(m.group(1))
        C = float(m.group(2)) / 100
        H = float(m.group(3))
        return oklch_to_srgb(L, C, H)
    # named colors
    NAMED = {"white": (255, 255, 255), "black": (0, 0, 0), "transparent": None}
    if value in NAMED:
        return NAMED[value]
    return None


def oklch_to_srgb(L, C, H):
    """Approximate oklch -> sRGB using simplified OKLab pipeline."""
    import math
    a = C * math.cos(H * math.pi / 180)
    b = C * math.sin(H * math.pi / 180)
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l = l_ ** 3
    m = m_ ** 3
    s = s_ ** 3
    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    def clamp(v):
        v = max(0, min(1, v))
        if v <= 0.0031308:
            return round(12.92 * v * 255)
        return round((1.055 * (v ** (1 / 2.4)) - 0.055) * 255)
    return (clamp(r), clamp(g), clamp(bb))


def relative_luminance(rgb):
    """WCAG 2.1 relative luminance."""
    def ch(c):
        s = c / 255.0
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(rgb[0]) + 0.7152 * ch(rgb[1]) + 0.0722 * ch(rgb[2])


def contrast_ratio(rgb1, rgb2):
    """WCAG 2.1 contrast ratio between two sRGB colors."""
    l1 = relative_luminance(rgb1)
    l2 = relative_luminance(rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def validate_theme(css_path):
    """Validate a single tokens.css file. Returns (issues, warnings)."""
    issues = []
    warnings = []

    if not css_path.exists():
        issues.append(f"文件不存在: {css_path}")
        return issues, warnings

    tokens = parse_tokens(css_path)
    if not tokens:
        issues.append("未找到任何 CSS 自定义属性")
        return issues, warnings

    # Check for required tokens
    for group_name, token_list in REQUIRED_TOKENS.items():
        for token in token_list:
            if token not in tokens:
                issues.append(f"缺少 {token} ({group_name})")

    # Check for extra tokens (informational)
    known = set(ALL_TOKENS)
    extra = set(tokens.keys()) - known
    if extra:
        warnings.append(f"额外定义: {', '.join(sorted(extra))}")

    # Check contrast ratios
    for fg_name, bg_name in CONTRAST_PAIRS:
        if fg_name not in tokens or bg_name not in tokens:
            continue
        fg = parse_color(tokens[fg_name])
        bg = parse_color(tokens[bg_name])
        if fg is None or bg is None:
            continue
        ratio = contrast_ratio(fg, bg)
        level = ""
        if ratio < 3.0:
            level = " FAIL"
        elif ratio < 4.5:
            level = " WARN (不足AA)"
        elif ratio < 7.0:
            level = " OK (AA)"
        else:
            level = " OK (AAA)"
        warnings.append(f"{fg_name} / {bg_name}: 对比度 {ratio:.1f}{level}")

    return issues, warnings


def main():
    # Fix encoding on Windows
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Validate theme token completeness")
    parser.add_argument("themes_dir", nargs="?", default=None,
                        help="Path to css/theme/ directory (default: auto-detect)")
    parser.add_argument("--theme", "-t", help="Validate only this theme name")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.themes_dir:
        themes_dir = Path(args.themes_dir)
    else:
        # Auto-detect: look for css/theme/ relative to script or CWD
        script_dir = Path(__file__).resolve().parent.parent
        themes_dir = script_dir / "container" / "css" / "theme"
        if not themes_dir.exists():
            themes_dir = Path.cwd() / "css" / "theme"
        if not themes_dir.exists():
            themes_dir = Path.cwd() / "container" / "css" / "theme"

    if not themes_dir.exists():
        print(f"错误: 找不到主题目录: {themes_dir}", file=sys.stderr)
        sys.exit(1)

    themes = []
    for d in sorted(themes_dir.iterdir()):
        if d.is_dir() and not d.name.startswith("."):
            if args.theme and d.name != args.theme:
                continue
            themes.append(d)

    if not themes:
        print(f"未找到主题目录 (在 {themes_dir})", file=sys.stderr)
        sys.exit(1)

    results = {}
    total_issues = 0
    for theme_dir in themes:
        css_path = theme_dir / "tokens.css"
        issues, warnings = validate_theme(css_path)
        results[theme_dir.name] = {"issues": issues, "warnings": warnings, "path": str(css_path)}
        total_issues += len(issues)

    if args.json:
        import json
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for name, result in results.items():
            print(f"\n{'='*60}")
            print(f"  主题: {name}")
            print(f"  文件: {result['path']}")
            print(f"{'='*60}")
            if result["issues"]:
                print(f"\n  X 问题 ({len(result['issues'])}):")
                for issue in result["issues"]:
                    print(f"     - {issue}")
            else:
                print(f"\n  OK 所有 {len(ALL_TOKENS)} 个必需 Token 均已定义")
            if result["warnings"]:
                print(f"\n  > 备注:")
                for w in result["warnings"]:
                    print(f"     - {w}")

        if total_issues:
            print(f"\nWARN  共 {total_issues} 个问题", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"\nOK 所有主题验证通过")


if __name__ == "__main__":
    main()
