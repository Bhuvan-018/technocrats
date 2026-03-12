import argparse
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.group_dataset import refresh_intraday_cache
from src.sectors import SECTOR_BANKING, SECTOR_COMPANIES, SECTOR_ENERGY, SECTOR_IT


def collect_sector_data(sector_key: str, interval: str = "5m", period: str = "59d") -> None:
    companies = SECTOR_COMPANIES[sector_key]
    for company in companies:
        print(f"[{sector_key}] Fetching {company.name} ({company.ticker})...")
        df = refresh_intraday_cache(
            ticker=company.ticker,
            interval=interval,
            period=period,
            exchange="NSE",
        )
        print(f"[{sector_key}] {company.ticker}: rows={len(df)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect intraday data for sector training")
    parser.add_argument("--group", default="all", choices=["all", SECTOR_BANKING, SECTOR_ENERGY, SECTOR_IT])
    parser.add_argument("--interval", type=str, default="5m")
    parser.add_argument("--period", type=str, default="59d")
    args = parser.parse_args()

    sectors = [SECTOR_BANKING, SECTOR_ENERGY, SECTOR_IT] if args.group == "all" else [args.group]
    for sector in sectors:
        collect_sector_data(sector_key=sector, interval=args.interval, period=args.period)
