"""CLI entry point for the Audio Sample Quality Organizer."""
import argparse
import sys
from pathlib import Path
from typing import Dict, List

import yaml

from metadata import read_metadata
from organizer import OrganizedItem, ensure_folders, organize_sample
from quality import grade_sample
from renamer import build_name
from scanner import scan_audio_files
from tagger import colorize_all


def load_config(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Organize, rename, and color-code audio samples by quality metrics."
    )
    parser.add_argument("--input", "-i", help="Folder containing raw samples")
    parser.add_argument("--output", "-o", help="Folder for organized output")
    parser.add_argument("--config", "-c", default="config.yaml", help="Config file path")
    parser.add_argument("--dry-run", action="store_true", help="Analyze only, do not write files")
    parser.add_argument("--no-color", action="store_true", help="Skip Windows folder coloring")
    parser.add_argument("--move", action="store_true", help="Move instead of copy (destructive)")
    return parser.parse_args()


def _print_report(items: List[OrganizedItem], dry_run: bool) -> None:
    mode = "[DRY RUN] " if dry_run else ""
    print(f"\n{mode}Organized {len(items)} sample(s):\n")
    for item in items:
        print(f"  {item.grade.value:<9} {item.source.name}")
        print(f"            -> {item.destination}")
        for reason in item.reasons:
            print(f"            - {reason}")
    print()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)

    input_dir = args.input or config.get("input_dir")
    output_dir = args.output or config.get("output_dir", "./organized_samples")

    if not input_dir:
        print("ERROR: no input directory. Pass --input or set input_dir in config.", file=sys.stderr)
        return 2

    thresholds = config.get("thresholds", {})
    folder_names = config.get("folders", {"PASS": "01_PASS", "MARGINAL": "02_MARGINAL", "FAIL": "03_FAIL"})
    folder_icons = config.get("folder_icons", {})
    template = config.get("rename_template", "{index}_{name}_{sr}kHz_{bd}bit_{br}kbps_{grade}.{ext}")
    extensions = config.get("supported_extensions")
    copy = not args.move and config.get("copy_instead_of_move", True)

    try:
        files = scan_audio_files(input_dir, extensions)
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not files:
        print("No audio files found.")
        return 0

    print(f"Found {len(files)} audio file(s) in {input_dir}")

    grade_folders = ensure_folders(Path(output_dir), folder_names)

    items: List[OrganizedItem] = []
    for index, path in enumerate(files, start=1):
        info = read_metadata(path)
        result = grade_sample(info, thresholds)

        if args.dry_run:
            new_name = build_name(info, result.grade, index, template)
            items.append(OrganizedItem(
                source=path,
                destination=grade_folders[result.grade.value] / new_name,
                grade=result.grade,
                reasons=result.reasons,
            ))
            continue

        items.append(organize_sample(
            info=info,
            result=result,
            grade_folders=grade_folders,
            template=template,
            index=index,
            copy=copy,
        ))

    _print_report(items, args.dry_run)

    if not args.dry_run and not args.no_color:
        results = colorize_all(grade_folders, folder_icons)
        for grade_value, ok in results.items():
            status = "colored" if ok else "skipped (non-Windows or failed)"
            print(f"  {grade_value}: {status}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
