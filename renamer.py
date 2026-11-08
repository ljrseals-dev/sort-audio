"""Build new filenames from a template using extracted audio metrics."""
import re
from pathlib import Path

from metadata import AudioInfo
from quality import Grade


_SAFE_CHARS = re.compile(r"[^\w\-. ]+", re.UNICODE)


def _sanitize(name: str) -> str:
    """Strip characters that are illegal in Windows filenames."""
    cleaned = _SAFE_CHARS.sub("_", name).strip(" .")
    return cleaned or "sample"


def build_name(info: AudioInfo, grade: Grade, index: int, template: str) -> str:
    """Render the rename template for a single sample."""
    original_stem = _sanitize(info.path.stem)
    return template.format(
        index=f"{index:03d}",
        name=original_stem,
        sr=info.sample_rate_khz,
        bd=info.bit_depth_display,
        br=info.bitrate_display,
        grade=grade.value,
        ext=info.format,
    )


def resolve_collision(target: Path) -> Path:
    """Append _1, _2, ... if the target path already exists."""
    if not target.exists():
        return target
    stem, suffix = target.stem, target.suffix
    counter = 1
    while True:
        candidate = target.with_name(f"{stem}_{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1
