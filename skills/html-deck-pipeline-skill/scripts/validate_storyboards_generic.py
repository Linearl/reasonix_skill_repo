"""分镜稿质量门禁校验。

检查分镜稿 Markdown 文件是否符合 07-quality-gate-patterns.md 定义的规则，
包括禁用模式、必需模式、Frontmatter 完整性、页面结构验证等。

用法：
    python scripts/validate_storyboards_generic.py \
        --workspace-root /path/to/workspace \
        --topic-folder "主题名称" \
        --version v-01 \
        [--glob "*.md"]

改动说明（相对 V1）：
- 新增 Frontmatter 校验（version/updated/style-id/total_pages/owner）
- 新增 style-id 声明检查
- 新增 TODO/TBD/placeholder 禁用检查
- 修复 glob 默认值为 `*-分镜稿.md`，避免把框架文档误判为分镜稿
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

FORBIDDEN_PATTERNS: List[Tuple[str, str]] = [
    ("旧版轻权重标记", r"（轻）"),
    ("旧版重权重标记", r"（重）"),
    ("旧版反面说明", r"这一页不做什么"),
    ("旧版字段名", r"页内主题："),
    ("未完成占位符", r"(?i)\b(TODO|TBD)\b"),
    ("英文占位符", r"(?i)placeholder"),
]

REQUIRED_PATTERNS: List[Tuple[str, str]] = [
    ("页眉主题字段", r"页眉主题："),
    ("演讲备注", r"### 演讲备注"),
    ("过渡句", r"过渡句："),
    ("附录A", r"附录A"),
    ("附录B", r"附录B"),
]

PAGE_HEADING_PATTERN: str = r"^## 第(\d+)页｜(.+)$"

FRONTMATTER_REQUIRED_KEYS: List[str] = [
    "version",
    "updated",
    "style-id",
    "total_pages",
    "owner",
]

SYMBOL_DECLARATION_PATTERN: str = r"(Unicode|Emoji|符号)"
MAIN_SYMBOL_SYSTEM_PATTERN: str = r"主符号体系\s*[：:]"
FALLBACK_SYMBOL_SYSTEM_PATTERN: str = r"替补符号体系\s*[：:]"
STEP_ARABIC_PATTERN: str = r"(?i)\bSTEP\s*[1-9]\b"
EMOJI_DIGIT_STEP_PATTERN: str = r"[1-9]️⃣"
SEMANTIC_STEP_EMOJI_PATTERN: str = r"(🎯|🔍|🛠️|🧪|✅|📍|🚀|🔁)"

SYMBOL_CATEGORIES: Dict[str, str] = {
    "勾选符号": r"[✓✅]",
    "否定符号": r"[✗×]",
    "步骤符号": r"([①②③④⑤⑥⑦⑧⑨]|[1-9]️⃣|🎯|🔍|🛠️|🧪|✅)",
    "箭头符号": r"[→⇒➜⟶]",
    "强调符号": r"[★☆●○•]",
}

STORYBOARD_SUFFIX: str = "-分镜稿.md"


@dataclass
class Issue:
    """单条校验问题。"""

    file: str
    line: int
    level: str
    message: str


@dataclass
class ValidationResult:
    """校验结果汇总。"""

    issues: List[Issue] = field(default_factory=list)
    files_checked: int = 0
    pages_found: int = 0

    @property
    def has_errors(self) -> bool:
        return any(issue.level == "ERROR" for issue in self.issues)

    def add(self, file: str, line: int, level: str, message: str) -> None:
        self.issues.append(Issue(file=file, line=line, level=level, message=message))


def find_first_match_line(content: str, pattern: str) -> int:
    """返回首个正则命中的行号，未命中时返回 0。"""

    match: Optional[re.Match[str]] = re.search(pattern, content, re.MULTILINE)
    if match is None:
        return 0
    return content[: match.start()].count("\n") + 1


def extract_frontmatter(lines: List[str]) -> Optional[Dict[str, str]]:
    """提取 YAML Frontmatter 键值对（简易解析）。"""

    if not lines or lines[0].strip() != "---":
        return None

    frontmatter: Dict[str, str] = {}
    for i, line in enumerate(lines[1:], start=2):
        stripped: str = line.strip()
        if stripped == "---":
            return frontmatter
        if ":" in stripped:
            key, _, value = stripped.partition(":")
            frontmatter[key.strip()] = value.strip().strip('"').strip("'")
    return None


def check_frontmatter(
    lines: List[str], filename: str, result: ValidationResult
) -> None:
    """校验 Frontmatter 完整性。"""

    fm: Optional[Dict[str, str]] = extract_frontmatter(lines)
    if fm is None:
        result.add(filename, 1, "ERROR", "缺少 YAML Frontmatter（文件须以 --- 开头）")
        return

    for key in FRONTMATTER_REQUIRED_KEYS:
        if key not in fm:
            result.add(filename, 1, "ERROR", f"Frontmatter 缺少必需字段: {key}")
        elif not fm[key] or fm[key] in ("YYYY-MM-DD", "待填写"):
            result.add(filename, 1, "WARN", f"Frontmatter 字段 {key} 为占位值")


def check_forbidden(content: str, filename: str, result: ValidationResult) -> None:
    """检查禁用模式。"""

    for name, pattern in FORBIDDEN_PATTERNS:
        matches: list[re.Match[str]] = list(re.finditer(pattern, content, re.MULTILINE))
        for match in matches:
            line_num: int = content[: match.start()].count("\n") + 1
            result.add(
                filename,
                line_num,
                "ERROR",
                f"包含禁用模式 [{name}]: '{match.group(0)}'",
            )


def check_required(content: str, filename: str, result: ValidationResult) -> None:
    """检查必需模式。"""

    for name, pattern in REQUIRED_PATTERNS:
        if not re.search(pattern, content, re.MULTILINE):
            result.add(filename, 0, "ERROR", f"缺少必需模式: {name}")


def check_symbol_consistency(
    content: str, filename: str, result: ValidationResult
) -> None:
    """检查 Emoji/符号规则声明、覆盖类别与同语义混用。"""

    if not re.search(SYMBOL_DECLARATION_PATTERN, content, re.MULTILINE):
        result.add(filename, 0, "ERROR", "缺少 Emoji/符号规则显式声明")

    declaration_patterns: List[Tuple[str, str]] = [
        ("主符号体系", MAIN_SYMBOL_SYSTEM_PATTERN),
        ("替补符号体系", FALLBACK_SYMBOL_SYSTEM_PATTERN),
    ]
    for label, pattern in declaration_patterns:
        if not re.search(pattern, content, re.MULTILINE):
            result.add(filename, 0, "ERROR", f"缺少 {label} 声明")

    detected_categories: List[str] = [
        category
        for category, pattern in SYMBOL_CATEGORIES.items()
        if re.search(pattern, content, re.MULTILINE)
    ]
    if len(detected_categories) < 2:
        category_text: str = (
            "、".join(detected_categories) if detected_categories else "无"
        )
        result.add(
            filename,
            0,
            "ERROR",
            f"Emoji/符号覆盖类别不足 2 类，当前检测到: {category_text}",
        )

    mixed_semantics_checks: List[Tuple[str, str, str]] = [
        (r"✓", r"✅", "同语义混用：同时出现 ✓ 与 ✅"),
        (r"✗", r"×", "同语义混用：同时出现 ✗ 与 ×"),
        (
            r"[①②③④⑤⑥⑦⑧⑨]",
            STEP_ARABIC_PATTERN,
            "同语义混用：同时出现 ①..⑨ 与 STEP 阿拉伯数字编号",
        ),
        (
            EMOJI_DIGIT_STEP_PATTERN,
            SEMANTIC_STEP_EMOJI_PATTERN,
            "同流程混用：同时出现 emoji 数字序号与语义步骤 emoji",
        ),
    ]
    for primary_pattern, secondary_pattern, message in mixed_semantics_checks:
        primary_line: int = find_first_match_line(content, primary_pattern)
        secondary_line: int = find_first_match_line(content, secondary_pattern)
        if primary_line and secondary_line:
            result.add(
                filename,
                min(primary_line, secondary_line),
                "ERROR",
                message,
            )


def check_page_structure(content: str, filename: str, result: ValidationResult) -> None:
    """检查页面结构完整性。"""

    pages: list[re.Match[str]] = list(
        re.finditer(PAGE_HEADING_PATTERN, content, re.MULTILINE)
    )
    if not pages:
        result.add(filename, 0, "ERROR", "未找到任何页面标题（## 第N页｜...）")
        return

    result.pages_found += len(pages)

    prev_num: int = 0
    for page_match in pages:
        page_num: int = int(page_match.group(1))
        page_title: str = page_match.group(2)
        line_num: int = content[: page_match.start()].count("\n") + 1

        if page_num != prev_num + 1:
            result.add(
                filename,
                line_num,
                "ERROR",
                f"页码不连续: 期望 {prev_num + 1}，实际 {page_num}",
            )
        prev_num = page_num

        page_end_match: Optional[re.Match[str]] = re.search(
            r"^## 第\d+页｜",
            content[page_match.end() :],
            re.MULTILINE,
        )
        page_end: int = (
            page_match.end() + page_end_match.start()
            if page_end_match
            else len(content)
        )
        page_content: str = content[page_match.start() : page_end]

        for required_section in ("### 页面目标", "### 页面完整文案", "### 演讲备注"):
            if required_section not in page_content:
                result.add(
                    filename,
                    line_num,
                    "ERROR",
                    f"第{page_num}页缺少: {required_section}",
                )


def check_file(filepath: Path, result: ValidationResult) -> None:
    """校验单个分镜稿文件。"""

    content: str = filepath.read_text(encoding="utf-8")
    lines: List[str] = content.splitlines()
    filename: str = filepath.name

    result.files_checked += 1
    check_frontmatter(lines, filename, result)
    check_forbidden(content, filename, result)
    check_required(content, filename, result)
    check_symbol_consistency(content, filename, result)
    check_page_structure(content, filename, result)


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""

    parser = argparse.ArgumentParser(description="分镜稿质量门禁校验。")
    parser.add_argument(
        "--workspace-root",
        required=True,
        help="工作区根目录（绝对路径）。",
    )
    parser.add_argument(
        "--topic-folder",
        required=True,
        help="主题目录名。",
    )
    parser.add_argument(
        "--version",
        required=True,
        help="版本号（如 v-01）。",
    )
    parser.add_argument(
        "--glob",
        default=f"*{STORYBOARD_SUFFIX}",
        help="分镜稿文件匹配模式（默认 *-分镜稿.md）。",
    )
    return parser.parse_args()


def main() -> None:
    """脚本入口。"""

    args = parse_args()
    root: Path = Path(args.workspace_root).expanduser().resolve()
    storyboard_dir: Path = root / args.topic_folder / "10-storyboards" / args.version

    if not storyboard_dir.exists():
        raise FileNotFoundError(f"分镜目录不存在: {storyboard_dir}")

    files: List[Path] = sorted(
        filepath
        for filepath in storyboard_dir.glob(args.glob)
        if filepath.name.endswith(STORYBOARD_SUFFIX)
    )
    if not files:
        raise FileNotFoundError(f"在 {storyboard_dir} 中未找到匹配 {args.glob} 的文件")

    result = ValidationResult()
    for filepath in files:
        print(f"校验: {filepath.name}")
        check_file(filepath, result)

    print(f"\n校验完成: {result.files_checked} 个文件, {result.pages_found} 个页面")

    if result.issues:
        print(f"\n发现 {len(result.issues)} 个问题:\n")
        for issue in sorted(result.issues, key=lambda i: (i.file, i.line)):
            prefix: str = "❌" if issue.level == "ERROR" else "⚠️"
            loc: str = f"{issue.file}:{issue.line}" if issue.line else issue.file
            print(f"  {prefix} [{issue.level}] {loc}: {issue.message}")

    if result.has_errors:
        print("\n❌ 门禁失败: 存在 ERROR 级别问题。")
        raise SystemExit(1)
    else:
        print("\n✅ 门禁通过。")


if __name__ == "__main__":
    main()
