"""初始化讲稿主题目录结构（模板驱动版）。

要点：
- 使用 templates/init_topic 下的模板文件，避免脚本内嵌大段文本。
- 初始化阶段不自动生成分镜/HTML分片文件，避免模板内容固化风格。
- 沟通记录直接使用真实日期文件名，禁止 YYYYMMDD 占位。
- 当版本为 v-02+ 时，默认复制上一版本分镜与 HTML 作为迭代基线。
"""

from __future__ import annotations

import argparse
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

TEMPLATES_SUBDIR = "templates/init_topic"


@dataclass
class TopicConfig:
    """主题初始化参数。"""

    workspace_root: Path
    topic_folder: str
    topic_code: str
    topic_title: str
    version: str
    style_id: str
    scheme_name: str
    record_date: str
    part_names: List[str]
    copy_previous: bool
    dry_run: bool


@dataclass
class TopicPaths:
    """主题目录路径集合。"""

    skill_root: Path
    topic_root: Path
    input_dir: Path
    comms_dir: Path
    storyboard_root: Path
    storyboard_dir: Path
    html_root: Path
    html_dir: Path
    style_dir: Path
    test_dir: Path
    template_dir: Path


def parse_version_number(version: str) -> int:
    """把 v-XX 转为整数 XX。"""

    match: Optional[re.Match[str]] = re.fullmatch(r"v-(\d{2})", version)
    if match is None:
        raise ValueError("--version 必须是 v-XX 格式，例如 v-01")
    return int(match.group(1))


def previous_version(version: str) -> Optional[str]:
    """返回上一版本名。"""

    current: int = parse_version_number(version)
    if current <= 1:
        return None
    return f"v-{current - 1:02d}"


def validate_record_date(record_date: str) -> None:
    """校验 YYYYMMDD 日期格式。"""

    if re.fullmatch(r"\d{8}", record_date) is None:
        raise ValueError("--record-date 必须是 YYYYMMDD 格式，例如 20260316")


def iso_date(record_date: str) -> str:
    """YYYYMMDD -> YYYY-MM-DD。"""

    return f"{record_date[:4]}-{record_date[4:6]}-{record_date[6:8]}"


def build_paths(config: TopicConfig) -> TopicPaths:
    """构建路径集合。"""

    skill_root: Path = Path(__file__).resolve().parent.parent
    topic_root: Path = config.workspace_root / config.topic_folder
    return TopicPaths(
        skill_root=skill_root,
        topic_root=topic_root,
        input_dir=topic_root / "00-input",
        comms_dir=topic_root / "00-input" / "comms",
        storyboard_root=topic_root / "10-storyboards",
        storyboard_dir=topic_root / "10-storyboards" / config.version,
        html_root=topic_root / "20-html",
        html_dir=topic_root / "20-html" / config.version,
        style_dir=topic_root / "20-html" / config.version / "style",
        test_dir=topic_root / "90-tests",
        template_dir=skill_root / TEMPLATES_SUBDIR,
    )


def read_template(paths: TopicPaths, template_name: str) -> str:
    """读取模板文件。"""

    template_path: Path = paths.template_dir / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"模板文件不存在: {template_path}")
    return template_path.read_text(encoding="utf-8")


def render_template(content: str, context: Dict[str, object]) -> str:
    """执行模板变量替换。"""

    return content.format(**context)


def ensure_directory(path: Path, *, dry_run: bool) -> None:
    """确保目录存在。"""

    if path.exists():
        print(f"  [SKIP DIR] 已存在: {path}")
        return
    if dry_run:
        print(f"  [DRY-RUN] 将创建目录: {path}")
        return
    path.mkdir(parents=True, exist_ok=True)
    print(f"  [CREATE DIR] {path}")


def write_file_if_missing(path: Path, content: str, *, dry_run: bool) -> bool:
    """文件不存在时写入。"""

    if path.exists():
        print(f"  [SKIP] 已存在: {path}")
        return False
    if dry_run:
        print(f"  [DRY-RUN] 将创建: {path}")
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  [CREATE] {path}")
    return True


def copy_if_missing(src: Path, dst: Path, *, dry_run: bool) -> bool:
    """复制文件（目标不存在时）。"""

    if not src.exists() or dst.exists():
        return False
    if dry_run:
        print(f"  [DRY-RUN] 将复制: {src} -> {dst}")
        return True
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  [COPY] {src} -> {dst}")
    return True


def copy_if_missing_or_placeholder(src: Path, dst: Path, *, dry_run: bool) -> bool:
    """目标缺失或为占位内容时复制。"""

    if not src.exists():
        return False

    if dst.exists():
        text: str = dst.read_text(encoding="utf-8")
        if "（待填充）" not in text and "请按分镜稿填充" not in text:
            return False

    if dry_run:
        print(f"  [DRY-RUN] 将复制(覆盖占位): {src} -> {dst}")
        return True

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  [COPY/REPLACE] {src} -> {dst}")
    return True


def create_slides_config(paths: TopicPaths, config: TopicConfig) -> None:
    """创建 slides-config.json 模板。"""

    config_path = paths.html_dir / "slides-config.json"
    if config_path.exists():
        return

    import json

    part_entries = {}
    for i, name in enumerate(config.part_names, start=1):
        part_id = f"ch{i:02d}"
        part_entries[part_id] = name

    template = {
        "title": config.topic_title,
        "parts": part_entries,
        "partOrder": list(part_entries.keys()),
        "slides": [],
    }
    if config.dry_run:
        print(f"  [DRY-RUN] 将创建: {config_path}")
        return
    config_path.write_text(
        json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  [CREATE] {config_path}")


def copy_previous_version_assets(config: TopicConfig, paths: TopicPaths) -> None:
    """复制上一版本分镜和 HTML (slides/) 作为迭代基线。"""

    if not config.copy_previous:
        return

    prev: Optional[str] = previous_version(config.version)
    if prev is None:
        return

    prev_storyboard_dir: Path = paths.storyboard_root / prev
    prev_html_dir: Path = paths.html_root / prev

    if not prev_storyboard_dir.exists() and not prev_html_dir.exists():
        return

    print(f"  [INFO] 启用迭代复制：{prev} -> {config.version}")

    if prev_storyboard_dir.exists():
        for file_path in sorted(prev_storyboard_dir.glob("[0-9][0-9]-*.md")):
            copy_if_missing(
                file_path, paths.storyboard_dir / file_path.name, dry_run=config.dry_run
            )

        for index, part_name in enumerate(config.part_names, start=1):
            legacy_name: str = f"{part_name}-分镜稿.md"
            target_name: str = f"{index:02d}-{part_name}-分镜稿.md"
            copy_if_missing_or_placeholder(
                prev_storyboard_dir / legacy_name,
                paths.storyboard_dir / target_name,
                dry_run=config.dry_run,
            )

    if prev_html_dir.exists():
        # Copy slides/ directory
        prev_slides = prev_html_dir / "slides"
        if prev_slides.exists():
            target_slides = paths.html_dir / "slides"
            for part_dir in sorted(prev_slides.iterdir()):
                if not part_dir.is_dir():
                    continue
                for file_path in sorted(part_dir.glob("*.html")):
                    dst = target_slides / part_dir.name / file_path.name
                    copy_if_missing(file_path, dst, dry_run=config.dry_run)

        # Copy optional per-part style/ directory
        prev_style_dir = prev_html_dir / "style"
        if prev_style_dir.exists():
            for file_path in sorted(prev_style_dir.glob("*.css")):
                dst = paths.style_dir / file_path.name
                copy_if_missing(file_path, dst, dry_run=config.dry_run)

        # Copy config
        prev_config = prev_html_dir / "slides-config.json"
        if prev_config.exists():
            copy_if_missing(
                prev_config,
                paths.html_dir / "slides-config.json",
                dry_run=config.dry_run,
            )


def cleanup_legacy_part_files(paths: TopicPaths, config: TopicConfig) -> None:
    """清理当前版本目录中的旧命名分片文件。"""

    for part_name in config.part_names:
        legacy_storyboard: Path = paths.storyboard_dir / f"{part_name}-分镜稿.md"
        legacy_html: Path = paths.html_dir / f"{part_name}.html"

        for legacy in [legacy_storyboard, legacy_html]:
            if not legacy.exists():
                continue
            if config.dry_run:
                print(f"  [DRY-RUN] 将删除旧命名分片: {legacy}")
                continue
            legacy.unlink(missing_ok=True)
            print(f"  [DELETE] 旧命名分片: {legacy}")


def create_style_contract(paths: TopicPaths, config: TopicConfig) -> None:
    """创建或复制 style-contract。"""

    dst_contract: Path = paths.input_dir / f"style-contract-{config.style_id}.md"
    if dst_contract.exists():
        print(f"  [SKIP] 已存在: {dst_contract}")
        return

    src_contract: Path = (
        paths.skill_root
        / "examples"
        / config.style_id
        / f"style-contract-{config.style_id}.md"
    )
    if src_contract.exists():
        copy_if_missing(src_contract, dst_contract, dry_run=config.dry_run)
        return

    placeholder_tpl: str = read_template(paths, "style_contract_placeholder.md")
    content: str = render_template(placeholder_tpl, {"style_id": config.style_id})
    write_file_if_missing(dst_contract, content, dry_run=config.dry_run)


def create_stage_a_records(paths: TopicPaths, config: TopicConfig) -> None:
    """创建阶段 A 沟通与冻结记录。"""

    date_text: str = iso_date(config.record_date)
    context: Dict[str, object] = {
        "round_no": 1,
        "record_date": config.record_date,
        "iso_date": date_text,
        "topic_code": config.topic_code,
        "topic_title": config.topic_title,
        "version": config.version,
        "style_id": config.style_id,
        "part_names_cn": "、".join(config.part_names),
    }

    comms_content: str = render_template(
        read_template(paths, "comms_round.md"), context
    )
    freeze_content: str = render_template(
        read_template(paths, "freeze_snapshot.md"), context
    )
    test_content: str = render_template(
        read_template(paths, "test_record.md"),
        {"topic_code": config.topic_code},
    )

    canonical_name = f"A-round01-{config.record_date}.md"
    for stale_file in sorted(paths.comms_dir.glob("A-*-round*-*.md")):
        if stale_file.name == canonical_name:
            continue
        if config.dry_run:
            print(f"  [DRY-RUN] 将删除旧命名沟通记录: {stale_file}")
            continue
        stale_file.unlink(missing_ok=True)
        print(f"  [DELETE] 旧命名沟通记录: {stale_file}")

    write_file_if_missing(
        paths.comms_dir / canonical_name,
        comms_content,
        dry_run=config.dry_run,
    )
    write_file_if_missing(
        paths.test_dir / f"A-freeze-input-snapshot-{config.record_date}.md",
        freeze_content,
        dry_run=config.dry_run,
    )
    write_file_if_missing(
        paths.test_dir / f"{config.topic_code}-90-技能测试记录_{config.record_date}.md",
        test_content,
        dry_run=config.dry_run,
    )


def init_topic(config: TopicConfig) -> None:
    """执行初始化。"""

    paths: TopicPaths = build_paths(config)

    if not paths.template_dir.exists():
        raise FileNotFoundError(f"模板目录不存在: {paths.template_dir}")

    for directory in [
        paths.input_dir,
        paths.storyboard_dir,
        paths.html_dir,
        paths.style_dir,
        paths.html_dir / "slides",
        paths.test_dir,
        paths.comms_dir,
    ]:
        ensure_directory(directory, dry_run=config.dry_run)

    copy_previous_version_assets(config, paths)
    cleanup_legacy_part_files(paths, config)
    create_style_contract(paths, config)
    create_slides_config(paths, config)
    create_stage_a_records(paths, config)


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""

    parser = argparse.ArgumentParser(
        description="初始化讲稿主题目录结构（模板驱动版）。"
    )
    parser.add_argument("--workspace-root", required=True, help="工作区根目录。")
    parser.add_argument("--topic-folder", required=True, help="主题目录名。")
    parser.add_argument("--topic-code", required=True, help="主题代码，例如 01-00。")
    parser.add_argument("--topic-title", required=True, help="主题标题。")
    parser.add_argument("--version", default="v-01", help="版本号，格式 v-XX。")
    parser.add_argument("--style-id", default="dark-theme", help="风格标识。")
    parser.add_argument(
        "--scheme-name", default="方案A", help="方案代号（用于合并稿命名）。"
    )
    parser.add_argument(
        "--record-date",
        default=datetime.now().strftime("%Y%m%d"),
        help="记录日期，格式 YYYYMMDD。",
    )
    parser.add_argument(
        "--parts",
        nargs="+",
        default=["开头", "基础篇", "进阶篇", "收官篇", "结尾"],
        help="分片名称列表。",
    )
    parser.add_argument(
        "--copy-previous",
        action="store_true",
        default=True,
        help="初始化新版本时复制上一版本资产（默认开启）。",
    )
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不落盘。")
    return parser.parse_args()


def main() -> None:
    """脚本入口。"""

    args = parse_args()
    validate_record_date(args.record_date)
    parse_version_number(args.version)

    config = TopicConfig(
        workspace_root=Path(args.workspace_root).expanduser().resolve(),
        topic_folder=args.topic_folder,
        topic_code=args.topic_code,
        topic_title=args.topic_title,
        version=args.version,
        style_id=args.style_id,
        scheme_name=args.scheme_name,
        record_date=args.record_date,
        part_names=args.parts,
        copy_previous=args.copy_previous,
        dry_run=args.dry_run,
    )

    print(f"初始化主题: {config.topic_title}")
    print(f"工作区: {config.workspace_root}")
    print(f"目标目录: {config.workspace_root / config.topic_folder}")
    print(f"版本: {config.version}")
    print(f"风格: {config.style_id}")
    print(f"方案: {config.scheme_name}")
    print(f"分片: {', '.join(config.part_names)}")
    print(f"日期: {config.record_date}")
    print(f"复制上一版本: {'是' if config.copy_previous else '否'}")
    print(f"模式: {'DRY-RUN' if config.dry_run else 'EXECUTE'}")
    print()

    init_topic(config)
    print("\n初始化完成。")


if __name__ == "__main__":
    main()
