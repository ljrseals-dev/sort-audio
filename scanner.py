"""Recursively scan a directory for supported audio files."""
from pathlib import Path
from typing import List


DEFAULT_EXTENSIONS = {
    ".wav", ".mp3", ".flac", ".aiff", ".aif",
    ".m4a", ".aac", ".ogg", ".opus",
}


def scan_audio_files(root: str, extensions: List[str] | None = None) -> List[Path]:
    """Return a sorted list of audio file paths found under `root`.

    Sorting is case-insensitive alphabetical by filename.
    """
    exts = {e.lower() for e in (extensions or DEFAULT_EXTENSIONS)}
    root_path = Path(root).expanduser().resolve()

    if not root_path.exists():
        raise FileNotFoundError(f"Input directory does not exist: {root_path}")
    if not root_path.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {root_path}")

    found: List[Path] = []
    for path in root_path.rglob("*"):
        if path.is_file() and path.suffix.lower() in exts:
            found.append(path)

    found.sort(key=lambda p: p.name.lower())
    return found
