import argparse
import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.build_analytics import build_analytics
from src.config import GROUP_LOOKBACK_WINDOW
from src.group_dataset import refresh_intraday_cache
from src.groups import GROUP_A, GROUP_B, GROUP_COMPANIES
from src.train_group_multi import train_group_model


DEFAULT_CADENCE = {
    GROUP_A: "daily/weekly",
    GROUP_B: "weekly/monthly",
}


def refresh_group_data(group_key: str, interval: str = "5m", period: str = "59d") -> None:
    for company in GROUP_COMPANIES[group_key]:
        print(f"[{group_key}] refreshing {company.ticker}...")
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
) -> None:
    groups = [GROUP_A, GROUP_B] if target_group == "all" else [target_group]

    print(f"Pipeline run at {datetime.now().isoformat(timespec='seconds')}")
    for group_key in groups:
        print(f"\n=== {group_key} | suggested cadence: {DEFAULT_CADENCE[group_key]} ===")

        if action in {"refresh", "refresh-train"}:
            refresh_group_data(group_key, interval=interval, period=period)

        if action in {"train", "refresh-train"}:
            train_group_model(
                group_key=group_key,
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
            )
            if build_analytics_files:
                build_analytics(
                    key=group_key,
                    days=analytics_days,
                    refresh=False,
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Refresh and retrain grouped transformer models")
    parser.add_argument("--group", default="all", choices=["all", GROUP_A, GROUP_B])
    parser.add_argument(
        "--action",
        default="refresh-train",
        choices=["refresh", "train", "refresh-train"],
    )
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
    )
