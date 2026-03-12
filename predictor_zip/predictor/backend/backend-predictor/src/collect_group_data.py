import argparse
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.group_dataset import refresh_intraday_cache
from src.groups import GROUP_A, GROUP_B, GROUP_COMPANIES


def collect_group_data(group_key: str, interval: str = "5m", period: str = "59d") -> None:
    companies = GROUP_COMPANIES[group_key]
    for company in companies:
        print(f"[{group_key}] Fetching {company.name} ({company.ticker})...")
        df = refresh_intraday_cache(
            ticker=company.ticker,
            interval=interval,
            period=period,
            exchange="NSE",
        )
        print(f"[{group_key}] {company.ticker}: rows={len(df)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect intraday data for grouped training")
    parser.add_argument("--group", default="all", choices=["all", GROUP_A, GROUP_B])
    parser.add_argument("--interval", type=str, default="5m")
    parser.add_argument("--period", type=str, default="59d")
    args = parser.parse_args()

    groups = [GROUP_A, GROUP_B] if args.group == "all" else [args.group]
    for group in groups:
        collect_group_data(group_key=group, interval=args.interval, period=args.period)
