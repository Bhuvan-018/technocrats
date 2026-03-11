import argparse
import os
import shutil
import sys
from datetime import datetime
from typing import List

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.config import LEGACY_ARCHIVE_DIR, MODELS_DIR


def timestamp_tag() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _is_root_file(path: str) -> bool:
    return os.path.isfile(path)


def archive_legacy_model_root_files(dry_run: bool = False) -> List[str]:
    os.makedirs(LEGACY_ARCHIVE_DIR, exist_ok=True)
    root_entries = [os.path.join(MODELS_DIR, name) for name in os.listdir(MODELS_DIR)]
    root_files = [p for p in root_entries if _is_root_file(p)]
    if not root_files:
        return []

    dest_dir = os.path.join(LEGACY_ARCHIVE_DIR, f"root_files_{timestamp_tag()}")
    moved = []
    for src in sorted(root_files):
        dst = os.path.join(dest_dir, os.path.basename(src))
        moved.append(f"{src} -> {dst}")
        if dry_run:
            continue
        os.makedirs(dest_dir, exist_ok=True)
        shutil.move(src, dst)
    return moved


def main() -> None:
    parser = argparse.ArgumentParser(description="Move legacy root-level model files to archive")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    moves = archive_legacy_model_root_files(dry_run=args.dry_run)
    if not moves:
        print("No root-level legacy files found in models/.")
        return

    print("Planned moves:" if args.dry_run else "Moved files:")
    for line in moves:
        print(line)


if __name__ == "__main__":
    main()
