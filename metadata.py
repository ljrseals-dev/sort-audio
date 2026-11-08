"""Extract audio metadata using mutagen."""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import mutagen

# Formats where "bit depth" is a meaningful, measurable property (PCM-based).
# Lossy formats (mp3, aac, m4a, ogg, opus) do not have a bit depth in this
# sense, so quality.py skips that metric for them instead of auto-failing.
LOSSLESS_FORMATS = {"wav", "aiff", "aif", "flac"}


@dataclass
class AudioInfo:
    """Normalized audio metadata."""
    path: Path
    bitrate_kbps: Optional[int]   # None for lossless without a defined bitrate
    sample_rate_hz: Optional[int]
    bit_depth: Optional[int]
    channels: Optional[int]
    duration_sec: Optional[float]
    format: str
    error: Optional[str] = None

    @property
    def is_lossless(self) -> bool:
        return self.format in LOSSLESS_FORMATS

    @property
    def sample_rate_khz(self) -> str:
        if self.sample_rate_hz is None:
            return "unknown"
        return f"{self.sample_rate_hz / 1000:g}"

    @property
    def bitrate_display(self) -> str:
        if self.bitrate_kbps is None:
            return "lossless"
        return str(self.bitrate_kbps)

    @property
    def bit_depth_display(self) -> str:
        return str(self.bit_depth) if self.bit_depth is not None else "unknown"


def _extract_bit_depth(audio) -> Optional[int]:
    """Best-effort bit depth extraction across formats."""
    info = audio.info
    # WAV / AIFF / FLAC expose bits_per_sample
    for attr in ("bits_per_sample", "bits_per_raw_sample"):
        val = getattr(info, attr, None)
        if isinstance(val, int) and val > 0:
            return val
    return None


def read_metadata(path: Path) -> AudioInfo:
    """Read metadata for a single file. Never raises - errors are captured."""
    try:
        audio = mutagen.File(str(path), easy=False)
        if audio is None:
            return AudioInfo(path, None, None, None, None, None,
                             format=path.suffix.lower().lstrip("."),
                             error="Unsupported or unreadable file")

        info = audio.info
        bitrate_bps = getattr(info, "bitrate", None)
        bitrate_kbps = int(bitrate_bps / 1000) if bitrate_bps else None
        sample_rate = getattr(info, "sample_rate", None)
        channels = getattr(info, "channels", None)
        duration = getattr(info, "length", None)
        bit_depth = _extract_bit_depth(audio)

        # For lossless formats mutagen may not report bitrate; estimate from
        # sample_rate * bit_depth * channels when available.
        if bitrate_kbps is None and sample_rate and bit_depth and channels:
            bitrate_kbps = int(sample_rate * bit_depth * channels / 1000)

        return AudioInfo(
            path=path,
            bitrate_kbps=bitrate_kbps,
            sample_rate_hz=sample_rate,
            bit_depth=bit_depth,
            channels=channels,
            duration_sec=duration,
            format=path.suffix.lower().lstrip("."),
        )
    except Exception as exc:  # noqa: BLE001 - we intentionally catch all
        return AudioInfo(path, None, None, None, None, None,
                         format=path.suffix.lower().lstrip("."),
                         error=str(exc))
