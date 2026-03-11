import argparse
import os
import shutil
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.config import CHECKPOINTS_DIR, SECTOR_MODELS_DIR
from src.sectors import SECTOR_BANKING, SECTOR_ENERGY, SECTOR_IT, get_sector_model_filename


def bootstrap_sector_checkpoints(force: bool = False) -> None:
    sectors = [SECTOR_BANKING, SECTOR_ENERGY, SECTOR_IT]
    for sector_key in sectors:
        src_model = os.path.join(SECTOR_MODELS_DIR, get_sector_model_filename(sector_key))
        if not os.path.exists(src_model):
            print(f"[{sector_key}] skipped: model missing -> {src_model}")
            continue

        dst_dir = os.path.join(CHECKPOINTS_DIR, f"sector_{sector_key}")
        os.makedirs(dst_dir, exist_ok=True)
        best_path = os.path.join(dst_dir, "best.keras")
        last_path = os.path.join(dst_dir, "last.keras")

        for dst in [best_path, last_path]:
            if os.path.exists(dst) and not force:
                print(f"[{sector_key}] kept existing: {dst}")
                continue
            shutil.copy2(src_model, dst)
            print(f"[{sector_key}] created: {dst}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create initial best/last checkpoints from current sector models")
    parser.add_argument("--force", action="store_true", help="Overwrite existing checkpoint files")
    args = parser.parse_args()
    bootstrap_sector_checkpoints(force=args.force)


if __name__ == "__main__":
    main()
