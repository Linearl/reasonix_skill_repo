"""Image parser using vision-skill for content recognition.

Uses vision-skill CLI for AI-powered image description.
Falls back to file metadata if vision-skill is unavailable.
No external vision API key needed — vision-skill uses Agent's model.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_VISION_SKILL_DIR = os.path.expanduser(
    os.getenv("VISION_SKILL_PATH", "~/.claude/skills/vision-skill")
)
_VISION_CLI = os.path.join(_VISION_SKILL_DIR, "scripts", "vision_cli.py")


class ImageParser:
    """Parser for image files using vision-skill for content description.

    Supports common formats (jpg, jpeg, png, gif). Uses vision-skill
    for AI-powered image description; falls back to file metadata.
    """

    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def extract_text(self, file_path: Path) -> str:
        """Extract text description from image using vision-skill.

        Falls back to file metadata if vision-skill is unavailable.
        """
        description = self._try_vision_skill(file_path)
        if description:
            return description
        return self._metadata_description(file_path)

    def _try_vision_skill(self, file_path: Path) -> str:
        """Try to describe image using vision-skill CLI."""
        if not os.path.isfile(_VISION_CLI):
            logger.debug("vision-skill not found at %s", _VISION_CLI)
            return ""

        try:
            result = subprocess.run(
                [
                    "python3", _VISION_CLI, "recognize", str(file_path),
                    "--prompt", "Describe this image concisely in 2-3 sentences. "
                               "Include any visible text, main subjects, and context.",
                    "--wait", "--output", "-",
                ],
                capture_output=True, text=True, timeout=60,
                env={**os.environ, "PYTHONPATH": _VISION_SKILL_DIR},
            )
            if result.returncode == 0 and result.stdout.strip():
                try:
                    data = json.loads(result.stdout)
                    if isinstance(data, dict):
                        text = data.get("content") or data.get("text") or ""
                        if text:
                            return f"[Image: {text.strip()[:800]}]"
                except json.JSONDecodeError:
                    return f"[Image: {result.stdout.strip()[:800]}]"
        except subprocess.TimeoutExpired:
            logger.warning("vision-skill timeout for %s", file_path)
        except Exception as e:
            logger.warning("vision-skill error: %s", e)
        return ""

    def _metadata_description(self, file_path: Path) -> str:
        """Return file metadata as text."""
        try:
            size = file_path.stat().st_size if file_path.exists() else 0
            fmt = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif"}.get(
                file_path.suffix.lower().lstrip("."), "unknown"
            )
            if size < 1024:
                s = f"{size} B"
            elif size < 1048576:
                s = f"{size / 1024:.1f} KB"
            else:
                s = f"{size / 1048576:.1f} MB"
            return f"[Image: {file_path.name}, {fmt.upper()}, {s}]"
        except Exception:
            return f"[Image: {file_path.name}]"

    def extract_metadata(self, file_path: Path) -> dict[str, Any]:
        suffix = file_path.suffix.lower()
        return {
            "type": "image",
            "format": {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif"}.get(
                suffix.lstrip("."), "unknown"
            ),
            "size_bytes": file_path.stat().st_size if file_path.exists() else 0,
        }
