"""Quality grading engine based on IASA TC-03 / EBU R128 thresholds."""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from metadata import AudioInfo


class Grade(str, Enum):
    PASS = "PASS"
    MARGINAL = "MARGINAL"
    FAIL = "FAIL"


@dataclass
class GradeResult:
    grade: Grade
    reasons: List[str]


def _grade_metric(value, pass_thr, marginal_thr) -> Grade:
    """Grade a 'higher is better' metric."""
    if value is None:
        return Grade.FAIL
    if value >= pass_thr:
        return Grade.PASS
    if value >= marginal_thr:
        return Grade.MARGINAL
    return Grade.FAIL


def grade_sample(info: AudioInfo, thresholds: Dict) -> GradeResult:
    """Return an overall grade and human-readable reasons."""
    reasons: List[str] = []

    if info.error:
        return GradeResult(Grade.FAIL, [f"read error: {info.error}"])

    sr_cfg = thresholds.get("sample_rate", {})
    bd_cfg = thresholds.get("bit_depth", {})
    br_cfg = thresholds.get("bitrate", {})
    ch_cfg = thresholds.get("channels", {})

    sr_grade = _grade_metric(info.sample_rate_hz,
                             sr_cfg.get("pass", 48000),
                             sr_cfg.get("marginal", 44100))

    # Bit depth is a PCM concept and doesn't meaningfully apply to lossy
    # formats (mp3/aac/m4a/ogg/opus). Grading it there would auto-FAIL
    # every lossy file regardless of actual audio quality, so it's skipped
    # (treated as not-applicable / PASS) for those formats and bitrate
    # carries the weight instead.
    bd_grade: Optional[Grade]
    if info.is_lossless:
        bd_grade = _grade_metric(info.bit_depth,
                                 bd_cfg.get("pass", 24),
                                 bd_cfg.get("marginal", 16))
    else:
        bd_grade = None  # not applicable

    br_grade = _grade_metric(info.bitrate_kbps,
                             br_cfg.get("pass", 192),
                             br_cfg.get("marginal", 128))

    allowed_channels = ch_cfg.get("allowed", [1, 2])
    if info.channels is None:
        ch_grade = Grade.MARGINAL
        reasons.append("channels unknown")
    elif info.channels in allowed_channels:
        ch_grade = Grade.PASS
    else:
        ch_grade = Grade.FAIL
        reasons.append(f"unexpected channel count: {info.channels}")

    if sr_grade != Grade.PASS:
        reasons.append(f"sample rate {info.sample_rate_hz} Hz below pass")
    if bd_grade is not None and bd_grade != Grade.PASS:
        reasons.append(f"bit depth {info.bit_depth} below pass")
    if br_grade != Grade.PASS:
        reasons.append(f"bitrate {info.bitrate_kbps} kbps below pass")

    sub_grades = [sr_grade, br_grade, ch_grade]
    if bd_grade is not None:
        sub_grades.append(bd_grade)

    if all(g == Grade.PASS for g in sub_grades):
        return GradeResult(Grade.PASS, reasons or ["all metrics meet broadcast standard"])
    if any(g == Grade.FAIL for g in sub_grades):
        return GradeResult(Grade.FAIL, reasons)
    return GradeResult(Grade.MARGINAL, reasons)
