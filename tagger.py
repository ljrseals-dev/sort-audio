"""Apply Windows folder colors via desktop.ini using imageres.dll icons."""
import ctypes
import os
from pathlib import Path

FILE_ATTRIBUTE_READONLY = 0x1
FILE_ATTRIBUTE_HIDDEN = 0x2
FILE_ATTRIBUTE_SYSTEM = 0x4

_IMAGERES = r"%SystemRoot%\System32\imageres.dll"

_DESKTOP_INI = """[.ShellClassInfo]
IconResource={icon_path},{icon_index}
[ViewState]
Mode=
Vid=
FolderType=Generic
"""


def _set_attrs(path: Path, attrs: int) -> None:
    ctypes.windll.kernel32.SetFileAttributesW(str(path), attrs)


def colorize_folder(folder: Path, icon_index: str) -> bool:
    """Set a colored folder icon on Windows.

    icon_index is a resource index from imageres.dll (e.g. '-4' = green).
    Returns True on success, False if not on Windows or on error.
    """
    if os.name != "nt":
        return False
    try:
        icon_path = os.path.expandvars(_IMAGERES)
        ini_path = folder / "desktop.ini"
        ini_path.write_text(
            _DESKTOP_INI.format(icon_path=icon_path, icon_index=icon_index),
            encoding="utf-8",
        )
        # desktop.ini must be hidden+system; folder must be readonly+system
        _set_attrs(ini_path, FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)
        _set_attrs(folder, FILE_ATTRIBUTE_READONLY | FILE_ATTRIBUTE_SYSTEM)
        return True
    except Exception:
        return False


def colorize_all(grade_folders: dict, icons: dict) -> dict:
    """Apply colors to each grade folder. Returns grade -> success map."""
    results = {}
    for grade_value, folder in grade_folders.items():
        icon_index = icons.get(grade_value)
        if icon_index is None:
            results[grade_value] = False
            continue
        results[grade_value] = colorize_folder(folder, str(icon_index))
    return results
