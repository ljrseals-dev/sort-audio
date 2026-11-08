"""Create output folders, copy/move files, and rename them."""
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from metadata import AudioInfo
from quality import Grade, GradeResult
from renamer import build_name, resolve_collision


@dataclass
class OrganizedItem:
    source: Path
    destination: Path
    grade: Grade
    reasons: List[str]


def ensure_folders(output_dir: Path, folder_names: Dict[str, str]) -> Dict[str, Path]:
    """Create one folder per grade and return a mapping grade -> path."""
    paths: Dict[str, Path] = {}
    output_dir.mkdir(parents=True, exist_ok=True)
    for grade_value, folder_name in folder_names.items():
        folder = output_dir / folder_name
        folder.mkdir(parents=True, exist_ok=True)
        paths[grade_value] = folder
    return paths


def organize_sample(
    info: AudioInfo,
    result: GradeResult,
    grade_folders: Dict[str, Path],
    template: str,
    index: int,
    copy: bool = True,
) -> OrganizedItem:
    """Place one sample into its grade folder with a new name."""
    grade = result.grade
    folder = grade_folders[grade.value]

    new_name = build_name(info, grade, index, template)
    target = resolve_collision(folder / new_name)

    if copy:
        shutil.copy2(info.path, target)
    else:
        shutil.move(str(info.path), str(target))

    return OrganizedItem(
        source=info.path,
        destination=target,
        grade=grade,
        reasons=result.reasons,
    )
