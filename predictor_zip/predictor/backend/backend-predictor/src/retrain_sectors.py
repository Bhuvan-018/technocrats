import argparse
import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.config import GROUP_LOOKBACK_WINDOW
from src.build_analytics import build_analytics
from src.group_dataset import refresh_intraday_cache
from src.restructure_legacy_models import archive_legacy_model_root_files
from src.sectors import SECTOR_BANKING, SECTOR_COMPANIES, SECTOR_ENERGY, SECTOR_IT
from src.train_sector_multi import train_sector_model


DEFAULT_CADENCE = {
    SECTOR_BANKING: "daily/weekly",
    SECTOR_ENERGY: "weekly/monthly",
    SECTOR_IT: "daily/weekly",
}


def refresh_sector_data(sector_key: str, interval: str = "5m", period: str = "59d") -> None:
    for company in SECTOR_COMPANIES[sector_key]:
        print(f"[{sector_key}] refreshing {company.ticker}...")
        refresh_intraday_cache(
            ticker=company.ticker,
            interval=interval,
            period=period,
            exchange="NSE",
        )


def run_pipeline(
    target_group: str = "all",
    action: str = "refresh-train",
    epochs: int = 30,
    batch_size: int = 64,
    lookback: int = GROUP_LOOKBACK_WINDOW,
    interval: str = "5m",
    period: str = "59d",
    mse_weight: float = 0.5,
    mae_weight: float = 0.5,
    directional_weight: float = 0.2,
    seed: int = 42,
    min_train_samples: int = 1000,
    min_test_samples: int = 200,
    build_analytics_files: bool = True,
    analytics_days: int = 30,
    archive_legacy_root: bool = False,
    save_checkpoints: bool = True,
    resume_from: str = "none",
    resume_path: str = "",
) -> None:
    sectors = [SECTOR_BANKING, SECTOR_ENERGY, SECTOR_IT] if target_group == "all" else [target_group]

    print(f"Sector pipeline run at {datetime.now().isoformat(timespec='seconds')}")
    if archive_legacy_root:
        moved = archive_legacy_model_root_files(dry_run=False)
        if moved:
            print(f"Archived {len(moved)} legacy root-level file(s) from models/.")
        else:
            print("No legacy root-level files to archive.")

    for sector_key in sectors:
        print(f"\n=== {sector_key} | suggested cadence: {DEFAULT_CADENCE[sector_key]} ===")

        if action in {"refresh", "refresh-train"}:
            refresh_sector_data(sector_key, interval=interval, period=period)

        if action in {"train", "refresh-train"}:
            train_sector_model(
                sector_key=sector_key,
                epochs=epochs,
                batch_size=batch_size,
                lookback=lookback,
                interval=interval,
                period=period,
                refresh_data=False,
                mse_weight=mse_weight,
                mae_weight=mae_weight,
                directional_weight=directional_weight,
                seed=seed,
                min_train_samples=min_train_samples,
                min_test_samples=min_test_samples,
                save_checkpoints=save_checkpoints,
                resume_from=resume_from,
                resume_path=resume_path,
            )

            if build_analytics_files:
                build_analytics(
                    key=sector_key,
                    days=analytics_days,
                    refresh=False,
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Refresh and retrain sector transformer models")
    parser.add_argument("--group", default="all", choices=["all", SECTOR_BANKING, SECTOR_ENERGY, SECTOR_IT])
    parser.add_argument("--action", default="refresh-train", choices=["refresh", "train", "refresh-train"])
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lookback", type=int, default=GROUP_LOOKBACK_WINDOW)
    parser.add_argument("--interval", type=str, default="5m")
    parser.add_argument("--period", type=str, default="59d")
    parser.add_argument("--mse-weight", type=float, default=0.5)
    parser.add_argument("--mae-weight", type=float, default=0.5)
    parser.add_argument("--directional-weight", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-train-samples", type=int, default=1000)
    parser.add_argument("--min-test-samples", type=int, default=200)
    parser.add_argument("--analytics-days", type=int, default=30)
    parser.add_argument("--no-analytics", action="store_true")
    parser.add_argument("--archive-legacy-root", action="store_true")
    parser.add_argument("--no-checkpoints", action="store_true")
    parser.add_argument("--resume-from", type=str, default="none", choices=["none", "best", "last", "path"])
    parser.add_argument("--resume-path", type=str, default="")
    args = parser.parse_args()

    run_pipeline(
        target_group=args.group,
        action=args.action,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lookback=args.lookback,
        interval=args.interval,
        period=args.period,
        mse_weight=args.mse_weight,
        mae_weight=args.mae_weight,
        directional_weight=args.directional_weight,
        seed=args.seed,
        min_train_samples=args.min_train_samples,
        min_test_samples=args.min_test_samples,
        build_analytics_files=not args.no_analytics,
        analytics_days=args.analytics_days,
        archive_legacy_root=args.archive_legacy_root,
        save_checkpoints=not args.no_checkpoints,
        resume_from=args.resume_from,
        resume_path=args.resume_path,
    )
